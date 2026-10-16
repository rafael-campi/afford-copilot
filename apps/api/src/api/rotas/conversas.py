import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ValidationError

from agentes import ModeloIndisponivel, ObjetivoParcial, RecusaDoModelo, construir_grafo
from api.contexto import Contexto
from api.rotas.simulacoes import NovaSimulacao, SimulacaoOut, criar_simulacao


class NovaConversa(BaseModel):
    id: str


class NovaMensagem(BaseModel):
    texto: str


class ObjetivoOut(BaseModel):
    item: str | None
    valor_centavos: int | None
    prazo_meses: int | None
    entrada_centavos: int


class RespostaCopiloto(BaseModel):
    resposta: str
    objetivo: ObjetivoOut
    faltando: list[str]
    simulacao: SimulacaoOut | None


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    def conversa_da_sessao(conversa_id: str, request: Request) -> tuple[str, ObjetivoParcial]:
        persona_id = ctx.persona_da_sessao(request)
        dono, objetivo = ctx.conversas.get(conversa_id, (None, None))
        if dono != persona_id or not isinstance(objetivo, ObjetivoParcial):
            raise HTTPException(status_code=404, detail="Conversa não encontrada.")
        return persona_id, objetivo

    @rotas.post("/v1/conversas", status_code=201)
    def criar(request: Request) -> NovaConversa:
        persona_id = ctx.persona_da_sessao(request)
        conversa_id = str(uuid.uuid4())
        ctx.conversas[conversa_id] = (persona_id, ObjetivoParcial())
        return NovaConversa(id=conversa_id)

    @rotas.post("/v1/conversas/{conversa_id}/mensagens")
    def enviar(conversa_id: str, mensagem: NovaMensagem, request: Request) -> RespostaCopiloto:
        persona_id, objetivo = conversa_da_sessao(conversa_id, request)

        def simular_opcoes(completo: ObjetivoParcial) -> SimulacaoOut | str:
            try:
                dados = NovaSimulacao(
                    item=completo.item or "",
                    valor_centavos=completo.valor_centavos or 0,
                    prazo_meses=completo.prazo_meses or 0,
                    entrada_centavos=completo.entrada_centavos,
                )
            except ValidationError:
                return "A Entrada precisa ser menor do que o valor do item. Pode conferir?"
            return criar_simulacao(ctx, persona_id, dados)

        grafo = construir_grafo(ctx.llm(), simular_opcoes, [ctx.personas[persona_id].nome])
        try:
            estado: dict[str, Any] = grafo.invoke(
                {"mensagem": mensagem.texto, "objetivo": objetivo}
            )
        except ModeloIndisponivel as erro:
            raise HTTPException(
                status_code=503, detail="O copiloto está indisponível agora. Tente mais tarde."
            ) from erro
        except RecusaDoModelo as erro:
            raise HTTPException(
                status_code=502, detail="Não consegui entender agora. Pode reformular?"
            ) from erro
        novo: ObjetivoParcial = estado["objetivo"]
        ctx.conversas[conversa_id] = (persona_id, novo)
        simulacao = estado.get("simulacao")
        resposta = estado.get("resposta", "")
        if isinstance(simulacao, str):
            resposta, simulacao = simulacao, None
        return RespostaCopiloto(
            resposta=resposta,
            objetivo=ObjetivoOut(
                item=novo.item,
                valor_centavos=novo.valor_centavos,
                prazo_meses=novo.prazo_meses,
                entrada_centavos=novo.entrada_centavos,
            ),
            faltando=novo.faltando,
            simulacao=simulacao,
        )

    return rotas
