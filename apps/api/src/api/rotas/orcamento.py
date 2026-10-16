from datetime import date

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.contexto import Contexto
from extrato.categorizacao import categorizar


class ResumoOrcamento(BaseModel):
    entradas_centavos: int
    gastos_centavos: int
    sobra_mensal_centavos: int
    margem_segura_centavos: int
    margem_acima_da_sobra: bool


class Sugestao(BaseModel):
    titulo: str
    descricao: str


class Home(BaseModel):
    nome: str
    resumo: ResumoOrcamento
    sugestoes: list[Sugestao]


class Transacao(BaseModel):
    data: date
    descricao: str
    valor_centavos: int
    categoria: str


class Extrato(BaseModel):
    transacoes: list[Transacao]


SUGESTOES = [
    Sugestao(
        titulo="Consórcio ou financiamento?",
        descricao="Compare o custo total para um carro",
    ),
    Sugestao(
        titulo="Quanto posso comprometer por mês?",
        descricao="Calculado a partir dos seus gastos reais",
    ),
]


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.get("/v1/home")
    def home(request: Request) -> Home:
        persona_id = ctx.persona_da_sessao(request)
        resumo = ctx.orcamento(persona_id)
        return Home(
            nome=ctx.personas[persona_id].nome,
            resumo=ResumoOrcamento(
                entradas_centavos=resumo.entradas_centavos,
                gastos_centavos=resumo.gastos_centavos,
                sobra_mensal_centavos=resumo.sobra_mensal_centavos,
                margem_segura_centavos=resumo.margem_segura_centavos,
                margem_acima_da_sobra=resumo.margem_acima_da_sobra,
            ),
            sugestoes=SUGESTOES,
        )

    @rotas.get("/v1/extrato")
    def extrato(request: Request) -> Extrato:
        persona_id = ctx.persona_da_sessao(request)
        return Extrato(
            transacoes=[
                Transacao(
                    data=t.data,
                    descricao=t.descricao,
                    valor_centavos=t.valor_centavos,
                    categoria=categorizar(t),
                )
                for t in ctx.extrato(persona_id).transacoes
            ]
        )

    return rotas
