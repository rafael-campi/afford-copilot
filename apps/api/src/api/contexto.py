from dataclasses import dataclass, field
from datetime import date
from typing import Any

from fastapi import HTTPException, Request

from agentes import LLMClient, ModeloIndisponivel, RecusaDoModelo
from agentes.anthropic_llm import AnthropicLLM
from agentes.categorizacao import categorizar_restantes
from api.config import Config
from extrato.categorizacao import OUTROS, pela_regra
from extrato.orcamento import ResumoOrcamento, TransacaoBruta, resumir_orcamento
from mercado import ProjecoesFocus, RepositorioFocus, RepositorioSnapshots, SnapshotTaxas
from seed.gerador import ExtratoGerado, gerar_extrato
from seed.personas import PERSONAS, Persona
from simulador import Projecoes, SnapshotMercado
from simulador.recomendacao import reais


@dataclass(frozen=True)
class TransacaoCategorizada:
    transacao: TransacaoBruta
    categoria: str
    fonte: str
    """regra or llm."""


@dataclass
class Contexto:
    """What the routes share: configuration, demo data and in-memory storage.

    Storage is in memory until accounts and Postgres arrive (ticket 12).
    """

    config: Config
    personas: dict[str, Persona] = field(default_factory=lambda: {p.id: p for p in PERSONAS})
    simulacoes: dict[str, tuple[str, Any]] = field(default_factory=dict)
    conversas: dict[str, Any] = field(default_factory=dict)
    _llm: LLMClient | None = None
    _categorizados: dict[str, list[TransacaoCategorizada]] = field(default_factory=dict)

    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = self.config.llm or AnthropicLLM()
        return self._llm

    def persona_da_sessao(self, request: Request) -> str:
        persona_id = request.session.get("persona_id")
        if persona_id not in self.personas:
            raise HTTPException(status_code=401, detail="Entre como uma Persona primeiro.")
        return str(persona_id)

    def mercado(self) -> tuple[SnapshotTaxas, ProjecoesFocus, SnapshotMercado]:
        taxas = RepositorioSnapshots(self.config.diretorio_mercado).mais_recente()
        focus = RepositorioFocus(self.config.diretorio_focus).mais_recente()
        if taxas is None or focus is None:
            raise HTTPException(
                status_code=503, detail="Dados de mercado indisponíveis. Tente mais tarde."
            )
        hoje = self.config.hoje()
        idade = (hoje - taxas.fim_periodo).days
        projecoes = Projecoes(
            data_base=date(hoje.year, hoje.month, 1),
            selic_anual={ano: v / 100 for ano, v in focus.selic_anual.items()},
            ipca_anual={ano: v / 100 for ano, v in focus.ipca_anual.items()},
            fonte_data=focus.data_pesquisa,
        )
        return (
            taxas,
            focus,
            SnapshotMercado(
                id=taxas.id,
                financiamento_taxa_mensal=taxas.taxa_mediana_mensal,
                tarifas_centavos=self.config.tarifas_centavos,
                consorcio_reajuste_anual=projecoes.ipca(hoje.year),
                projecoes=projecoes,
                desatualizado=idade > self.config.dias_ate_desatualizar,
            ),
        )

    def extrato(self, persona_id: str) -> ExtratoGerado:
        return gerar_extrato(persona_id, self.config.seed)

    def orcamento(self, persona_id: str) -> ResumoOrcamento:
        return resumir_orcamento(
            self.extrato(persona_id).transacoes, self.config.margem_segura_percentual
        )

    def extrato_categorizado(self, persona_id: str) -> list[TransacaoCategorizada]:
        """Rules first; what they miss goes to the model once per Persona.

        When the model is unavailable the rest stays in Outros and nothing is cached,
        so the next request tries again.
        """
        if persona_id in self._categorizados:
            return self._categorizados[persona_id]
        transacoes = self.extrato(persona_id).transacoes
        regras = [pela_regra(t) for t in transacoes]
        restantes = [
            (i, t.descricao, reais(abs(t.valor_centavos)))
            for i, (t, regra) in enumerate(zip(transacoes, regras, strict=True))
            if regra is None
        ]
        try:
            do_modelo = categorizar_restantes(
                self.llm(), restantes, [self.personas[persona_id].nome]
            )
            guardar = True
        except (ModeloIndisponivel, RecusaDoModelo):
            do_modelo, guardar = {}, False
        categorizados = [
            TransacaoCategorizada(
                transacao=t,
                categoria=regra or do_modelo.get(i, OUTROS),
                fonte="llm" if regra is None and i in do_modelo else "regra",
            )
            for i, (t, regra) in enumerate(zip(transacoes, regras, strict=True))
        ]
        if guardar:
            self._categorizados[persona_id] = categorizados
        return categorizados
