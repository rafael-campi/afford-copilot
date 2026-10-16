from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import delete, select

from agentes import LLMClient, ModeloIndisponivel, RecusaDoModelo
from agentes.anthropic_llm import AnthropicLLM
from agentes.categorizacao import categorizar_restantes
from api.auditoria import LLMAuditado
from api.banco import (
    Consentimento,
    Conta,
    EventoAuditoria,
    Importacao,
    TransacaoImportada,
    criar_engine,
    fabrica_de_sessoes,
)
from api.config import Config
from extrato.categorizacao import OUTROS, pela_regra
from extrato.orcamento import ResumoOrcamento, TransacaoBruta, resumir_orcamento
from mercado import ProjecoesFocus, RepositorioFocus, RepositorioSnapshots, SnapshotTaxas
from seed.gerador import gerar_extrato
from seed.personas import PERSONAS, Persona
from simulador import Projecoes, SnapshotMercado
from simulador.recomendacao import reais

IMPORTACAO_APAGADA = "O extrato importado foi apagado depois de 24 horas. Importe de novo."


@dataclass(frozen=True)
class Fonte:
    """Where an account's Extrato comes from right now: a Consentimento or an Importação."""

    chave: str
    """Cache key: the same source always has the same transactions."""
    transacoes: tuple[TransacaoBruta, ...]
    nomes: tuple[str, ...]
    """Personal names to mask before any model call."""


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

    def importacao_vigente(self, conta_id: str) -> tuple[Importacao | None, bool]:
        """The newest Importação still kept, and whether an older one was just deleted."""
        agora = self.config.agora()
        apagou = False
        with self.banco.begin() as db:
            todas = db.scalars(
                select(Importacao)
                .where(Importacao.conta_id == conta_id)
                .order_by(Importacao.criada_em.desc())
            ).all()
            vigentes = []
            for importacao in todas:
                if importacao.expira_em is not None and _como_utc(importacao.expira_em) <= agora:
                    db.execute(
                        delete(TransacaoImportada).where(
                            TransacaoImportada.importacao_id == importacao.id
                        )
                    )
                    db.delete(importacao)
                    self._categorizados.pop(f"importacao:{conta_id}:{importacao.id}", None)
                    apagou = True
                else:
                    vigentes.append(importacao)
        return (vigentes[0] if vigentes else None), apagou

    def fonte_da_conta(self, conta_id: str, auditar: bool = True) -> Fonte:
        """Tool `analisar_orcamento`'s gate: the Extrato the account may read now.

        The newest of an active Consentimento and a kept Importação wins. Every read is
        audited against the authorization that allowed it.
        """
        with self.banco() as db:
            conta = db.get(Conta, conta_id)
        assert conta is not None
        consentimento = self.consentimento_vigente(conta_id)
        importacao, apagou = self.importacao_vigente(conta_id)
        if importacao is not None and (
            consentimento is None
            or _como_utc(importacao.criada_em) >= _como_utc(consentimento.concedido_em)
        ):
            with self.banco() as db:
                linhas = db.scalars(
                    select(TransacaoImportada)
                    .where(TransacaoImportada.importacao_id == importacao.id)
                    .order_by(TransacaoImportada.data, TransacaoImportada.id)
                ).all()
            if auditar:
                self.auditar(conta_id, "importacao_usada", {"importacao_id": importacao.id})
            return Fonte(
                chave=f"importacao:{conta_id}:{importacao.id}",
                transacoes=tuple(
                    TransacaoBruta(
                        data=t.data, descricao=t.descricao, valor_centavos=t.valor_centavos
                    )
                    for t in linhas
                ),
                nomes=(conta.nome,),
            )
        if consentimento is None:
            raise HTTPException(
                status_code=409, detail=IMPORTACAO_APAGADA if apagou else SEM_EXTRATO
            )
        if _como_utc(consentimento.expira_em) <= self.config.agora():
            data = consentimento.expira_em.strftime("%d/%m/%Y")
            raise HTTPException(
                status_code=409, detail=f"Seu consentimento expirou em {data}. Conecte de novo."
            )
        if "transacoes" not in consentimento.escopos:
            raise HTTPException(
                status_code=409, detail="Seu consentimento não cobre suas transações."
            )
        if auditar:
            self.auditar(conta_id, "consentimento_usado", {"consentimento_id": consentimento.id})
        persona = self.personas[consentimento.banco]
        return Fonte(
            chave=f"persona:{persona.id}",
            transacoes=tuple(gerar_extrato(persona.id, self.config.seed).transacoes),
            nomes=(conta.nome, persona.nome),
        )

    def fonte_da_sessao(self, request: Request, auditar: bool = True) -> Fonte:
        return self.fonte_da_conta(self.conta_da_sessao(request).id, auditar)

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

    def orcamento(self, fonte: Fonte) -> ResumoOrcamento:
        return resumir_orcamento(list(fonte.transacoes), self.config.margem_segura_percentual)

    def extrato_categorizado(
        self, fonte: Fonte, llm: LLMClient | None = None
    ) -> list[TransacaoCategorizada]:
        """Rules first; what they miss goes to the model once per source.

        When the model is unavailable the rest stays in Outros and nothing is cached,
        so the next request tries again.
        """
        if fonte.chave in self._categorizados:
            return self._categorizados[fonte.chave]
        transacoes = fonte.transacoes
        regras = [pela_regra(t) for t in transacoes]
        restantes = [
            (i, t.descricao, reais(abs(t.valor_centavos)))
            for i, (t, regra) in enumerate(zip(transacoes, regras, strict=True))
            if regra is None
        ]
        try:
            do_modelo = categorizar_restantes(llm or self.llm(), restantes, list(fonte.nomes))
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
            self._categorizados[fonte.chave] = categorizados
        return categorizados

    def esquecer_conta(self, conta_id: str) -> None:
        """Drops what is kept in memory for the account: Simulações, conversations and the
        categorization of its imported Extratos."""
        for chave in [c for c in self._categorizados if c.startswith(f"importacao:{conta_id}:")]:
            del self._categorizados[chave]
        for id_, (dono, _) in list(self.simulacoes.items()):
            if dono == conta_id:
                del self.simulacoes[id_]
        for id_, conversa in list(self.conversas.items()):
            if getattr(conversa, "conta_id", None) == conta_id:
                del self.conversas[id_]
