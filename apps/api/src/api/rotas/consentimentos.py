from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.banco import Consentimento
from api.confirmacoes import ConfirmacaoOut, executor, solicitar_confirmacao
from api.contexto import Contexto

DIAS_POR_MES = 30
Escopo = Literal["transacoes", "saldos"]


class BancoOut(BaseModel):
    id: str
    nome: str


class PedidoConsentimento(BaseModel):
    banco: str
    escopos: list[Escopo] = Field(min_length=1)
    meses_validade: int = Field(default=12, ge=1, le=12)


class ConsentimentoOut(BaseModel):
    id: str
    banco: str
    escopos: list[str]
    concedido_em: date
    expira_em: date
    situacao: str


def _utc(momento: datetime) -> datetime:
    return momento if momento.tzinfo else momento.replace(tzinfo=UTC)


@executor("conceder_consentimento")
def _conceder(db: Session, conta_id: str, dados: dict[str, Any], agora: datetime) -> str:
    db.add(
        Consentimento(
            conta_id=conta_id,
            banco=dados["banco"],
            escopos=dados["escopos"],
            concedido_em=agora,
            expira_em=datetime.fromisoformat(dados["expira_em"]),
        )
    )
    return "consentimento_concedido"


@executor("revogar_consentimento")
def _revogar(db: Session, conta_id: str, dados: dict[str, Any], agora: datetime) -> str:
    alvo = db.get(Consentimento, dados["consentimento_id"])
    if alvo is not None and alvo.conta_id == conta_id and alvo.revogado_em is None:
        alvo.revogado_em = agora
    return "consentimento_revogado"


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    def nome_do_banco(banco: str) -> str:
        persona = ctx.personas[banco]
        return f"Banco de demonstração d{persona.artigo} {persona.nome}"

    @rotas.get("/v1/bancos")
    def bancos(request: Request) -> list[BancoOut]:
        ctx.conta_da_sessao(request)
        return [BancoOut(id=p, nome=nome_do_banco(p)) for p in ctx.personas]

    @rotas.post("/v1/consentimentos", status_code=201)
    def pedir(pedido: PedidoConsentimento, request: Request) -> ConfirmacaoOut:
        conta = ctx.conta_da_sessao(request)
        if pedido.banco not in ctx.personas:
            raise HTTPException(status_code=404, detail="Banco não encontrado.")
        expira = ctx.config.agora() + timedelta(days=DIAS_POR_MES * pedido.meses_validade)
        resumo = {
            "banco": nome_do_banco(pedido.banco),
            "escopos": list(pedido.escopos),
            "meses_validade": pedido.meses_validade,
            "expira_em": expira.date().isoformat(),
        }
        dados = {
            "banco": pedido.banco,
            "escopos": list(pedido.escopos),
            "expira_em": expira.isoformat(),
        }
        confirmacao = solicitar_confirmacao(ctx, conta.id, "conceder_consentimento", dados)
        return ConfirmacaoOut(id=confirmacao.id, acao=confirmacao.acao, resumo=resumo)

    @rotas.get("/v1/consentimentos")
    def listar(request: Request) -> list[ConsentimentoOut]:
        conta = ctx.conta_da_sessao(request)
        agora = ctx.config.agora()
        with ctx.banco() as db:
            todos = db.scalars(
                select(Consentimento)
                .where(Consentimento.conta_id == conta.id)
                .order_by(Consentimento.concedido_em.desc())
            ).all()
        return [
            ConsentimentoOut(
                id=c.id,
                banco=nome_do_banco(c.banco),
                escopos=c.escopos,
                concedido_em=c.concedido_em.date(),
                expira_em=c.expira_em.date(),
                situacao=(
                    "revogado"
                    if c.revogado_em
                    else "expirado"
                    if _utc(c.expira_em) <= agora
                    else "ativo"
                ),
            )
            for c in todos
        ]

    @rotas.delete("/v1/consentimentos/{consentimento_id}", status_code=201)
    def revogar(consentimento_id: str, request: Request) -> ConfirmacaoOut:
        conta = ctx.conta_da_sessao(request)
        with ctx.banco() as db:
            consentimento = db.get(Consentimento, consentimento_id)
        if consentimento is None or consentimento.conta_id != conta.id:
            raise HTTPException(status_code=404, detail="Consentimento não encontrado.")
        confirmacao = solicitar_confirmacao(
            ctx, conta.id, "revogar_consentimento", {"consentimento_id": consentimento_id}
        )
        resumo = {"banco": nome_do_banco(consentimento.banco)}
        return ConfirmacaoOut(id=confirmacao.id, acao=confirmacao.acao, resumo=resumo)

    return rotas
