from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.banco import Confirmacao, Consentimento, Conta, Importacao, TransacaoImportada
from api.confirmacoes import ConfirmacaoOut, executor, solicitar_confirmacao
from api.contexto import Contexto

APAGA = ["conta", "consentimentos", "extratos importados", "simulações", "conversas"]


@executor("apagar_conta")
def _apagar(db: Session, conta_id: str, dados: dict[str, Any], agora: datetime) -> str:
    """Deletes everything that identifies the person. The audit log keeps only bare ids."""
    importacoes = select(Importacao.id).where(Importacao.conta_id == conta_id)
    db.execute(delete(TransacaoImportada).where(TransacaoImportada.importacao_id.in_(importacoes)))
    db.execute(delete(Importacao).where(Importacao.conta_id == conta_id))
    db.execute(delete(Consentimento).where(Consentimento.conta_id == conta_id))
    db.flush()
    db.execute(delete(Confirmacao).where(Confirmacao.conta_id == conta_id))
    db.execute(delete(Conta).where(Conta.id == conta_id))
    return "conta_apagada"


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.post("/v1/conta/exclusao", status_code=201)
    def pedir_exclusao(request: Request) -> ConfirmacaoOut:
        conta = ctx.conta_da_sessao(request)
        confirmacao = solicitar_confirmacao(ctx, conta.id, "apagar_conta", {})
        return ConfirmacaoOut(id=confirmacao.id, acao=confirmacao.acao, resumo={"apaga": APAGA})

    return rotas
