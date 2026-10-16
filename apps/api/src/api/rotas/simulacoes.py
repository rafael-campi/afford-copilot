import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from api.contexto import Contexto
from simulador import Objetivo, Orcamento, simular


class NovaSimulacao(BaseModel):
    item: str = Field(min_length=1)
    valor_centavos: int = Field(gt=0)
    prazo_meses: int = Field(ge=1)
    entrada_centavos: int = Field(default=0, ge=0)
    duracao_meses: int | None = None

    @model_validator(mode="after")
    def entrada_menor_que_valor(self) -> "NovaSimulacao":
        if self.entrada_centavos >= self.valor_centavos:
            raise ValueError("A Entrada precisa ser menor do que o valor do item.")
        return self


class ObjetivoOut(BaseModel):
    item: str
    valor_centavos: int
    prazo_meses: int
    entrada_centavos: int


class FinanciamentoOut(BaseModel):
    duracao_meses: int
    parcela_centavos: int
    custo_total_centavos: int
    juros_centavos: int
    taxa_mensal: Decimal
    acima_da_margem: bool
    duracoes_disponiveis: list[int]


class SimulacaoOut(BaseModel):
    id: str
    snapshot_id: str
    objetivo: ObjetivoOut
    financiamento: FinanciamentoOut


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.post("/v1/simulacoes", status_code=201)
    def criar(dados: NovaSimulacao, request: Request) -> SimulacaoOut:
        persona_id = ctx.persona_da_sessao(request)
        mercado = ctx.config.mercado
        if (
            dados.duracao_meses is not None
            and dados.duracao_meses not in mercado.financiamento_duracoes_meses
        ):
            raise HTTPException(
                status_code=422,
                detail=f"Duração indisponível. Opções: {mercado.financiamento_duracoes_meses}.",
            )
        resumo = ctx.orcamento(persona_id)
        objetivo = Objetivo(
            item=dados.item,
            valor_centavos=dados.valor_centavos,
            prazo_meses=dados.prazo_meses,
            entrada_centavos=dados.entrada_centavos,
        )
        simulacao = simular(
            objetivo,
            Orcamento(
                margem_segura_centavos=resumo.margem_segura_centavos,
                sobra_mensal_centavos=resumo.sobra_mensal_centavos,
            ),
            mercado,
            duracao_meses=dados.duracao_meses,
        )
        f = simulacao.financiamento
        saida = SimulacaoOut(
            id=str(uuid.uuid4()),
            snapshot_id=simulacao.snapshot_id,
            objetivo=ObjetivoOut(**vars(objetivo)),
            financiamento=FinanciamentoOut(
                duracao_meses=f.duracao_meses,
                parcela_centavos=f.parcela_centavos,
                custo_total_centavos=f.custo_total_centavos,
                juros_centavos=f.juros_centavos,
                taxa_mensal=mercado.financiamento_taxa_mensal,
                acima_da_margem=f.acima_da_margem,
                duracoes_disponiveis=sorted(mercado.financiamento_duracoes_meses),
            ),
        )
        ctx.simulacoes[saida.id] = (persona_id, saida)
        return saida

    @rotas.get("/v1/simulacoes/{simulacao_id}")
    def ler(simulacao_id: str, request: Request) -> SimulacaoOut:
        persona_id = ctx.persona_da_sessao(request)
        dono, simulacao = ctx.simulacoes.get(simulacao_id, (None, None))
        if dono != persona_id or not isinstance(simulacao, SimulacaoOut):
            raise HTTPException(status_code=404, detail="Simulação não encontrada.")
        return simulacao

    return rotas
