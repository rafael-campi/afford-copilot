import uuid
from dataclasses import dataclass, field, replace
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ValidationError

from agentes import (
    ModeloIndisponivel,
    NaoSimulado,
    ObjetivoParcial,
    RecusaDoModelo,
    Simulado,
    construir_grafo,
)
from api.contexto import Contexto
from api.fatos import fatos_da_simulacao
from api.rotas.simulacoes import NovaSimulacao, SimulacaoOut, criar_simulacao


@dataclass
class EstadoConversa:
    persona_id: str
    objetivo: ObjetivoParcial = field(default_factory=ObjetivoParcial)
    simulacoes: list[SimulacaoOut] = field(default_factory=list)


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
    novo_objetivo: bool
    simulacao: SimulacaoOut | None


class ConversaOut(BaseModel):
    objetivo: ObjetivoOut
    simulacoes: list[SimulacaoOut]


def _objetivo_out(objetivo: ObjetivoParcial) -> ObjetivoOut:
    return ObjetivoOut(
        item=objetivo.item,
        valor_centavos=objetivo.valor_centavos,
        prazo_meses=objetivo.prazo_meses,
        entrada_centavos=objetivo.entrada_centavos,
    )


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    def conversa_da_sessao(conversa_id: str, request: Request) -> EstadoConversa:
        persona_id = ctx.persona_da_sessao(request)
        conversa = ctx.conversas.get(conversa_id)
        if not isinstance(conversa, EstadoConversa) or conversa.persona_id != persona_id:
            raise HTTPException(status_code=404, detail="Conversa não encontrada.")
        return conversa

    @rotas.post("/v1/conversas", status_code=201)
    def criar(request: Request) -> NovaConversa:
        conversa_id = str(uuid.uuid4())
        ctx.conversas[conversa_id] = EstadoConversa(persona_id=ctx.persona_da_sessao(request))
        return NovaConversa(id=conversa_id)

    @rotas.get("/v1/conversas/{conversa_id}")
    def ler(conversa_id: str, request: Request) -> ConversaOut:
        conversa = conversa_da_sessao(conversa_id, request)
        return ConversaOut(
            objetivo=_objetivo_out(conversa.objetivo), simulacoes=conversa.simulacoes
        )

    @rotas.post("/v1/conversas/{conversa_id}/mensagens")
    def enviar(conversa_id: str, mensagem: NovaMensagem, request: Request) -> RespostaCopiloto:
        conversa = conversa_da_sessao(conversa_id, request)
        persona_id = conversa.persona_id

        def simular_opcoes(objetivo: ObjetivoParcial) -> Simulado | NaoSimulado:
            try:
                dados = NovaSimulacao(
                    item=objetivo.item or "",
                    valor_centavos=objetivo.valor_centavos or 0,
                    prazo_meses=objetivo.prazo_meses or 0,
                    entrada_centavos=objetivo.entrada_centavos,
                    duracao_meses=objetivo.duracao_meses,
                )
            except ValidationError:
                return NaoSimulado(
                    "A Entrada precisa ser menor do que o valor do item. Pode conferir?"
                )
            try:
                simulacao = criar_simulacao(ctx, persona_id, dados)
            except HTTPException as erro:
                if erro.status_code != 422:
                    raise
                duracoes = ctx.mercado()[2].financiamento_duracoes_meses
                return NaoSimulado(
                    f"Um financiamento em {objetivo.duracao_meses} meses não existe. As durações "
                    f"oferecidas vão de {min(duracoes)} a {max(duracoes)} meses."
                )
            return Simulado(simulacao=simulacao, fatos=fatos_da_simulacao(simulacao))

        grafo = construir_grafo(ctx.llm(), simular_opcoes, [ctx.personas[persona_id].nome])
        try:
            entrada = {"mensagem": mensagem.texto, "objetivo": conversa.objetivo}
            estado: dict[str, Any] = grafo.invoke(entrada)
        except ModeloIndisponivel as erro:
            raise HTTPException(
                status_code=503, detail="O copiloto está indisponível agora. Tente mais tarde."
            ) from erro
        except RecusaDoModelo as erro:
            raise HTTPException(
                status_code=502, detail="Não consegui entender agora. Pode reformular?"
            ) from erro

        objetivo: ObjetivoParcial = estado["objetivo"]
        resultado = estado.get("resultado")
        simulacao = resultado.simulacao if isinstance(resultado, Simulado) else None
        if isinstance(resultado, NaoSimulado):
            # Keep what the market does not offer out of the next simulations.
            objetivo = replace(objetivo, duracao_meses=conversa.objetivo.duracao_meses)
        if estado.get("novo_objetivo"):
            conversa.simulacoes.clear()
        if simulacao is not None:
            conversa.simulacoes.append(simulacao)
        conversa.objetivo = objetivo
        return RespostaCopiloto(
            resposta=estado.get("resposta", ""),
            objetivo=_objetivo_out(objetivo),
            faltando=objetivo.faltando,
            novo_objetivo=bool(estado.get("novo_objetivo")),
            simulacao=simulacao,
        )

    return rotas
