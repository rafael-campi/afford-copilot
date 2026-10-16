from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agentes import ModeloIndisponivel, RecusaDoModelo
from api.contexto import Contexto
from rag.resposta import RespostaCitada, responder


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500)


class CitacaoOut(BaseModel):
    documento: str
    rotulo: str
    url: str
    versao: str
    capturado_em: str
    trecho: str


class RespostaRegraOut(BaseModel):
    sabe: bool
    resposta: str
    citacoes: list[CitacaoOut]


def citacoes_out(resposta: RespostaCitada) -> list[CitacaoOut]:
    return [
        CitacaoOut(
            documento=t.titulo,
            rotulo=t.rotulo,
            url=t.url,
            versao=t.versao,
            capturado_em=t.capturado_em,
            trecho=t.texto,
        )
        for t in resposta.citacoes
    ]


def responder_regra(ctx: Contexto, conta_id: str, pergunta: str) -> RespostaCitada:
    """Tool `buscar_regras` followed by the cited answer."""
    ctx.auditar(conta_id, "ferramenta:buscar_regras")
    llm = ctx.llm_da_conta(conta_id)
    trechos = ctx.regras().buscar(pergunta, llm)
    return responder(pergunta, trechos, llm)


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.post("/v1/regras/perguntas")
    def perguntar(dados: Pergunta, request: Request) -> RespostaRegraOut:
        conta = ctx.conta_da_sessao(request)
        try:
            resposta = responder_regra(ctx, conta.id, dados.pergunta)
        except (ModeloIndisponivel, RecusaDoModelo) as erro:
            raise HTTPException(
                status_code=503, detail="O copiloto está indisponível agora. Tente mais tarde."
            ) from erro
        return RespostaRegraOut(
            sabe=resposta.sabe, resposta=resposta.resposta, citacoes=citacoes_out(resposta)
        )

    return rotas
