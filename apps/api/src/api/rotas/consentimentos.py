from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from api.banco import Confirmacao, Consentimento
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


class ConfirmacaoOut(BaseModel):
    id: str
    acao: str
    resumo: dict[str, Any]


class ConsentimentoOut(BaseModel):
    id: str
    banco: str
    escopos: list[str]
    concedido_em: date
    expira_em: date
    situacao: str


class ResultadoConfirmacao(BaseModel):
    acao: str
    feito: bool


def _utc(momento: datetime) -> datetime:
    return momento if momento.tzinfo else momento.replace(tzinfo=UTC)


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    def nome_do_banco(banco: str) -> str:
        persona = ctx.personas[banco]
        return f"Banco de demonstração d{persona.artigo} {persona.nome}"

    def solicitar_confirmacao(conta_id: str, acao: str, dados: dict[str, Any]) -> Confirmacao:
        """Tool `solicitar_confirmacao`: starts a sensitive action; never completes it."""
        confirmacao = Confirmacao(
            conta_id=conta_id, acao=acao, dados=dados, criada_em=ctx.config.agora()
        )
        with ctx.banco.begin() as db:
            db.add(confirmacao)
        ctx.auditar(conta_id, "ferramenta:solicitar_confirmacao", {"acao": acao})
        return confirmacao

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
        confirmacao = solicitar_confirmacao(conta.id, "conceder_consentimento", dados)
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
            conta.id, "revogar_consentimento", {"consentimento_id": consentimento_id}
        )
        resumo = {"banco": nome_do_banco(consentimento.banco)}
        return ConfirmacaoOut(id=confirmacao.id, acao=confirmacao.acao, resumo=resumo)

    @rotas.post("/v1/confirmacoes/{confirmacao_id}/confirmar")
    def confirmar(confirmacao_id: str, request: Request) -> ResultadoConfirmacao:
        conta = ctx.conta_da_sessao(request)
        agora = ctx.config.agora()
        with ctx.banco.begin() as db:
            confirmacao = db.get(Confirmacao, confirmacao_id)
            if confirmacao is None or confirmacao.conta_id != conta.id:
                raise HTTPException(status_code=404, detail="Confirmação não encontrada.")
            if confirmacao.usada_em is not None:
                raise HTTPException(status_code=409, detail="Essa confirmação já foi usada.")
            if not ctx.reautenticado(request):
                raise HTTPException(status_code=403, detail="Confirme sua senha para continuar.")
            confirmacao.usada_em = agora
            dados = confirmacao.dados
            if confirmacao.acao == "conceder_consentimento":
                db.add(
                    Consentimento(
                        conta_id=conta.id,
                        banco=dados["banco"],
                        escopos=dados["escopos"],
                        concedido_em=agora,
                        expira_em=datetime.fromisoformat(dados["expira_em"]),
                    )
                )
                evento = "consentimento_concedido"
            elif confirmacao.acao == "revogar_consentimento":
                alvo = db.get(Consentimento, dados["consentimento_id"])
                if alvo is not None and alvo.revogado_em is None:
                    alvo.revogado_em = agora
                evento = "consentimento_revogado"
            else:
                raise HTTPException(status_code=422, detail="Ação desconhecida.")
            acao = confirmacao.acao
        ctx.auditar(conta.id, evento)
        return ResultadoConfirmacao(acao=acao, feito=True)

    return rotas
