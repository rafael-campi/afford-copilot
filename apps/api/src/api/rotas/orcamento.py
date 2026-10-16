from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.contexto import Contexto


class ResumoOrcamento(BaseModel):
    entradas_centavos: int
    gastos_centavos: int
    sobra_mensal_centavos: int
    margem_segura_centavos: int
    margem_acima_da_sobra: bool


class Sugestao(BaseModel):
    titulo: str
    descricao: str


class GastoCategoria(BaseModel):
    categoria: str
    centavos: int


class Home(BaseModel):
    nome: str
    resumo: ResumoOrcamento
    gastos_por_categoria: list[GastoCategoria]
    sugestoes: list[Sugestao]


class Transacao(BaseModel):
    data: date
    descricao: str
    valor_centavos: int
    categoria: str
    categoria_fonte: str


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


def _gastos_por_categoria(ctx: Contexto, persona_id: str, conta_id: str) -> list[GastoCategoria]:
    """Monthly average spending per category, largest first."""
    categorizados = ctx.extrato_categorizado(persona_id, ctx.llm_da_conta(conta_id))
    meses = len({(c.transacao.data.year, c.transacao.data.month) for c in categorizados}) or 1
    totais: dict[str, int] = defaultdict(int)
    for c in categorizados:
        if c.transacao.valor_centavos < 0:
            totais[c.categoria] -= c.transacao.valor_centavos
    return sorted(
        (GastoCategoria(categoria=k, centavos=v // meses) for k, v in totais.items()),
        key=lambda g: (-g.centavos, g.categoria),
    )


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
            gastos_por_categoria=_gastos_por_categoria(
                ctx, persona_id, ctx.conta_da_sessao(request).id
            ),
            sugestoes=SUGESTOES,
        )

    @rotas.get("/v1/extrato")
    def extrato(request: Request) -> Extrato:
        persona_id = ctx.persona_da_sessao(request)
        return Extrato(
            transacoes=[
                Transacao(
                    data=c.transacao.data,
                    descricao=c.transacao.descricao,
                    valor_centavos=c.transacao.valor_centavos,
                    categoria=c.categoria,
                    categoria_fonte=c.fonte,
                )
                for c in ctx.extrato_categorizado(
                    persona_id, ctx.llm_da_conta(ctx.conta_da_sessao(request).id)
                )
            ]
        )

    return rotas
