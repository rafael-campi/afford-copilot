from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import select

from agentes import LLMClient, ModeloIndisponivel, RecusaDoModelo
from agentes.anthropic_llm import AnthropicLLM
from agentes.categorizacao import categorizar_restantes
from api.auditoria import LLMAuditado
from api.banco import Consentimento, Conta, EventoAuditoria, criar_engine, fabrica_de_sessoes
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


SEM_EXTRATO = "Conecte seu banco ou importe seu extrato."


def _como_utc(momento: datetime) -> datetime:
    """SQLite drops time zones; every stored moment is UTC."""
    return momento if momento.tzinfo else momento.replace(tzinfo=UTC)


@dataclass
class Contexto:
    """What the routes share: configuration, persistence, demo data and caches.

    Accounts and the audit log live in the database; Simulações and conversations are still
    kept in memory, keyed by account.
    """

    config: Config
    personas: dict[str, Persona] = field(default_factory=lambda: {p.id: p for p in PERSONAS})
    simulacoes: dict[str, tuple[str, Any]] = field(default_factory=dict)
    conversas: dict[str, Any] = field(default_factory=dict)
    _llm: LLMClient | None = None
    _categorizados: dict[str, list[TransacaoCategorizada]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.banco = fabrica_de_sessoes(criar_engine(self.config.database_url))

    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = self.config.llm or AnthropicLLM()
        return self._llm

    def llm_da_conta(self, conta_id: str) -> LLMClient:
        return LLMAuditado(self.llm(), lambda tipo: self.auditar(conta_id, tipo))

    def auditar(self, conta_id: str, tipo: str, detalhe: dict[str, Any] | None = None) -> None:
        with self.banco.begin() as db:
            db.add(
                EventoAuditoria(
                    conta_id=conta_id, tipo=tipo, detalhe=detalhe, criado_em=self.config.agora()
                )
            )

    def conta_da_sessao(self, request: Request) -> Conta:
        conta_id = request.session.get("conta_id")
        conta = None
        if conta_id:
            with self.banco() as db:
                conta = db.get(Conta, conta_id)
        if conta is None:
            raise HTTPException(status_code=401, detail="Entre na sua conta primeiro.")
        return conta

    def consentimento_vigente(self, conta_id: str) -> Consentimento | None:
        """The newest Consentimento that was not revoked (it may have expired)."""
        with self.banco() as db:
            return db.scalar(
                select(Consentimento)
                .where(Consentimento.conta_id == conta_id, Consentimento.revogado_em.is_(None))
                .order_by(Consentimento.concedido_em.desc())
            )

    def persona_da_sessao(self, request: Request) -> str:
        """Tool `analisar_orcamento`'s gate: the Extrato the account's Consentimento covers.

        Every successful read is audited against the Consentimento that allowed it.
        """
        conta = self.conta_da_sessao(request)
        consentimento = self.consentimento_vigente(conta.id)
        if consentimento is None:
            raise HTTPException(status_code=409, detail=SEM_EXTRATO)
        if _como_utc(consentimento.expira_em) <= self.config.agora():
            data = consentimento.expira_em.strftime("%d/%m/%Y")
            raise HTTPException(
                status_code=409, detail=f"Seu consentimento expirou em {data}. Conecte de novo."
            )
        if "transacoes" not in consentimento.escopos:
            raise HTTPException(
                status_code=409, detail="Seu consentimento não cobre suas transações."
            )
        self.auditar(conta.id, "consentimento_usado", {"consentimento_id": consentimento.id})
        return consentimento.banco

    def reautenticado(self, request: Request) -> bool:
        marca = request.session.get("reautenticado_em")
        if not marca:
            return False
        janela = timedelta(minutes=self.config.minutos_de_reautenticacao)
        return self.config.agora() - datetime.fromisoformat(marca) <= janela

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

    def extrato_categorizado(
        self, persona_id: str, llm: LLMClient | None = None
    ) -> list[TransacaoCategorizada]:
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
                llm or self.llm(), restantes, [self.personas[persona_id].nome]
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
