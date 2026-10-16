from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.banco import Importacao, TransacaoImportada
from api.confirmacoes import executor, solicitar_confirmacao
from api.contexto import Contexto
from extrato.ofx import ArquivoInvalido, ler_ofx
from extrato.orcamento import TransacaoBruta
from seed.gerador import gerar_extrato
from seed.ofx import exportar_ofx

TAMANHO_MAXIMO = 2 * 1024 * 1024
DIAS_MINIMOS = 28
EXEMPLOS = 10


class TransacaoPrevia(BaseModel):
    data: date
    descricao: str
    valor_centavos: int


class Previa(BaseModel):
    transacoes: int
    inicio: date
    fim: date
    exemplos: list[TransacaoPrevia]


class PedidoImportacao(BaseModel):
    id: str
    acao: str
    previa: Previa
    aviso: str | None


class ImportacaoOut(BaseModel):
    id: str
    formato: str
    inicio: date
    fim: date
    expira_em: datetime | None


@executor("importar_extrato")
def _importar(db: Session, conta_id: str, dados: dict[str, Any], agora: datetime) -> str:
    horas = dados.get("horas")
    importacao = Importacao(
        conta_id=conta_id,
        formato=dados["formato"],
        inicio=date.fromisoformat(dados["inicio"]),
        fim=date.fromisoformat(dados["fim"]),
        criada_em=agora,
        expira_em=agora + timedelta(hours=horas) if horas else None,
    )
    db.add(importacao)
    db.flush()
    db.add_all(
        TransacaoImportada(
            importacao_id=importacao.id,
            data=date.fromisoformat(quando),
            descricao=descricao[:255],
            valor_centavos=valor,
        )
        for quando, descricao, valor in dados["transacoes"]
    )
    return "importacao_confirmada"


def _serializar(transacoes: list[TransacaoBruta]) -> list[list[Any]]:
    return [[t.data.isoformat(), t.descricao, t.valor_centavos] for t in transacoes]


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.post("/v1/importacoes", status_code=201)
    async def importar(arquivo: UploadFile, request: Request) -> PedidoImportacao:
        conta = ctx.conta_da_sessao(request)
        conteudo = await arquivo.read(TAMANHO_MAXIMO + 1)
        if len(conteudo) > TAMANHO_MAXIMO:
            raise HTTPException(
                status_code=413, detail="O arquivo passa de 2 MB. Exporte só os últimos meses."
            )
        try:
            transacoes = ler_ofx(conteudo)
        except ArquivoInvalido as erro:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Não encontrei transações nesse arquivo. "
                    "Exporte o extrato em OFX pelo app do seu banco."
                ),
            ) from erro
        inicio, fim = transacoes[0].data, transacoes[-1].data
        dias = (fim - inicio).days + 1
        if dias < DIAS_MINIMOS:
            raise HTTPException(
                status_code=422,
                detail=f"O extrato cobre só {dias} dias. Exporte pelo menos os últimos 3 meses.",
            )
        horas = ctx.config.horas_de_importacao
        dados = {
            "formato": "ofx",
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "horas": horas,
            "transacoes": _serializar(transacoes),
        }
        confirmacao = solicitar_confirmacao(ctx, conta.id, "importar_extrato", dados)
        return PedidoImportacao(
            id=confirmacao.id,
            acao=confirmacao.acao,
            previa=Previa(
                transacoes=len(transacoes),
                inicio=inicio,
                fim=fim,
                exemplos=[
                    TransacaoPrevia(
                        data=t.data, descricao=t.descricao, valor_centavos=t.valor_centavos
                    )
                    for t in transacoes[:EXEMPLOS]
                ],
            ),
            aviso=(
                f"O arquivo não é guardado. As transações ficam {horas} horas e depois "
                "são apagadas."
                if horas
                else None
            ),
        )

    @rotas.get("/v1/exemplos/{persona_id}.ofx")
    def exemplo(persona_id: str) -> Response:
        """A Persona's Extrato as OFX, so demo visitors can try the import without real data."""
        if persona_id not in ctx.personas:
            raise HTTPException(status_code=404, detail="Persona não encontrada.")
        conteudo = exportar_ofx(gerar_extrato(persona_id, ctx.config.seed).transacoes)
        return Response(
            content=conteudo,
            media_type="application/x-ofx",
            headers={"Content-Disposition": f'attachment; filename="extrato-{persona_id}.ofx"'},
        )

    @rotas.get("/v1/importacoes")
    def listar(request: Request) -> list[ImportacaoOut]:
        conta = ctx.conta_da_sessao(request)
        ctx.importacao_vigente(conta.id)  # deletes what expired
        with ctx.banco() as db:
            importacoes = db.scalars(
                select(Importacao)
                .where(Importacao.conta_id == conta.id)
                .order_by(Importacao.criada_em.desc())
            ).all()
        return [
            ImportacaoOut(
                id=i.id, formato=i.formato, inicio=i.inicio, fim=i.fim, expira_em=i.expira_em
            )
            for i in importacoes
        ]

    return rotas
