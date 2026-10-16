"""Sensitive actions on personal data wait here for explicit confirmation (ADR 0003).

`solicitar_confirmacao` is the copilot's tool: it records what would happen and returns a
summary; it never performs the action. The person confirms with a fresh reauthentication.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.banco import Confirmacao
from api.contexto import Contexto

Executor = Callable[[Session, str, dict[str, Any], datetime], str]
"""Performs a confirmed action inside the transaction; returns the audit event name."""

EXECUTORES: dict[str, Executor] = {}


def executor(acao: str) -> Callable[[Executor], Executor]:
    def registrar(funcao: Executor) -> Executor:
        EXECUTORES[acao] = funcao
        return funcao

    return registrar


class ConfirmacaoOut(BaseModel):
    id: str
    acao: str
    resumo: dict[str, Any]


class ResultadoConfirmacao(BaseModel):
    acao: str
    feito: bool


def solicitar_confirmacao(
    ctx: Contexto, conta_id: str, acao: str, dados: dict[str, Any]
) -> Confirmacao:
    confirmacao = Confirmacao(
        conta_id=conta_id, acao=acao, dados=dados, criada_em=ctx.config.agora()
    )
    with ctx.banco.begin() as db:
        db.add(confirmacao)
    ctx.auditar(conta_id, "ferramenta:solicitar_confirmacao", {"acao": acao})
    return confirmacao


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

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
            executar = EXECUTORES.get(confirmacao.acao)
            if executar is None:
                raise HTTPException(status_code=422, detail="Ação desconhecida.")
            confirmacao.usada_em = agora
            evento = executar(db, conta.id, confirmacao.dados, agora)
            acao = confirmacao.acao
        ctx.auditar(conta.id, evento)
        return ResultadoConfirmacao(acao=acao, feito=True)

    return rotas
