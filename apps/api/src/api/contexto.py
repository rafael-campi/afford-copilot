from dataclasses import dataclass, field
from datetime import date
from typing import Any

from fastapi import HTTPException, Request

from agentes import LLMClient
from agentes.anthropic_llm import AnthropicLLM
from api.config import Config
from extrato.orcamento import ResumoOrcamento, resumir_orcamento
from mercado import ProjecoesFocus, RepositorioFocus, RepositorioSnapshots, SnapshotTaxas
from seed.gerador import ExtratoGerado, gerar_extrato
from seed.personas import PERSONAS, Persona
from simulador import Projecoes, SnapshotMercado


@dataclass
class Contexto:
    """What the routes share: configuration, demo data and in-memory storage.

    Storage is in memory until accounts and Postgres arrive (ticket 12).
    """

    config: Config
    personas: dict[str, Persona] = field(default_factory=lambda: {p.id: p for p in PERSONAS})
    simulacoes: dict[str, tuple[str, Any]] = field(default_factory=dict)
    conversas: dict[str, tuple[str, Any]] = field(default_factory=dict)
    _llm: LLMClient | None = None

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
