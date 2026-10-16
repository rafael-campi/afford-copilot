import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from api.contexto import Contexto, Fonte
from simulador import Objetivo, Orcamento, simular


class NovaSimulacao(BaseModel):
    item: str = Field(min_length=1)
    valor_centavos: int = Field(gt=0)
    prazo_meses: int = Field(ge=1)
    entrada_centavos: int = Field(default=0, ge=0)
    duracao_meses: int | None = None
    consorcio_duracao_meses: int | None = None

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


class TaxaOut(BaseModel):
    instituicao: str
    taxa_mensal_percentual: Decimal
    taxa_anual_percentual: Decimal


class FonteOut(BaseModel):
    descricao: str
    inicio_periodo: date
    fim_periodo: date
    url: str


class RessalvaOut(BaseModel):
    codigo: str
    texto: str


class FinanciamentoOut(BaseModel):
    duracao_meses: int
    parcela_centavos: int
    custo_total_centavos: int
    juros_centavos: int
    iof_centavos: int
    tarifas_centavos: int
    cet_mensal_percentual: Decimal
    cet_anual_percentual: Decimal
    taxa_mensal: Decimal
    acima_da_margem: bool
    duracoes_disponiveis: list[int]
    ranking: list[TaxaOut]
    fonte: FonteOut
    ressalvas: list[RessalvaOut]


class JanelaOut(BaseModel):
    melhor_caso_mes: int
    mediana_mes: int
    pior_caso_mes: int
    chance_ate_prazo_percentual: int


class ConsorcioOut(BaseModel):
    carta_credito_centavos: int
    duracao_meses: int
    parcela_centavos: int
    custo_total_centavos: int
    taxa_administracao_centavos: int
    taxa_administracao_percentual: Decimal
    fundo_reserva_centavos: int
    fundo_reserva_percentual: Decimal
    reajuste_anual_percentual: Decimal
    acima_da_margem: bool
    janela: JanelaOut
    duracoes_disponiveis: list[int]
    ressalvas: list[RessalvaOut]


class FonteFocusOut(BaseModel):
    descricao: str
    data_pesquisa: date
    url: str


class JuntarOut(BaseModel):
    deposito_mensal_centavos: int
    mes_compra: int | None
    custo_total_centavos: int | None
    preco_na_compra_centavos: int | None
    entrega_ate_prazo: bool
    rendimento_anual_percentual: Decimal
    ipca_anual_percentual: Decimal
    fonte: FonteFocusOut
    ressalvas: list[RessalvaOut]


class AvaliacaoOut(BaseModel):
    caminho: str
    motivo_codigo: str | None
    motivo_texto: str | None


class AjustesOut(BaseModel):
    entrada_minima_centavos: int | None
    prazo_minimo_meses: int | None
    valor_maximo_centavos: int | None


class RecomendacaoOut(BaseModel):
    caminho: str | None
    avaliacoes: list[AvaliacaoOut]
    ressalvas: list[RessalvaOut]
    ajustes: AjustesOut | None


class SimulacaoOut(BaseModel):
    id: str
    snapshot_id: str
    objetivo: ObjetivoOut
    financiamento: FinanciamentoOut
    consorcio: ConsorcioOut
    juntar: JuntarOut
    recomendacao: RecomendacaoOut


FONTE_BCB = "Banco Central do Brasil: taxas médias de aquisição de veículos (pessoa física)"


def _percentual(fracao: Decimal) -> Decimal:
    return (fracao * 100).quantize(Decimal("0.01"))


def criar_simulacao(
    ctx: Contexto, conta_id: str, fonte: Fonte, dados: NovaSimulacao
) -> SimulacaoOut:
    """Tool `simular_opcoes`: runs the simulador with the person's own budget, stores the
    result under their account and audits the call."""
    ctx.auditar(conta_id, "ferramenta:simular_opcoes")
    taxas, focus, mercado = ctx.mercado()
    if (
        dados.duracao_meses is not None
        and dados.duracao_meses not in mercado.financiamento_duracoes_meses
    ):
        raise HTTPException(
            status_code=422,
            detail=f"Duração indisponível. Opções: {mercado.financiamento_duracoes_meses}.",
        )
    if (
        dados.consorcio_duracao_meses is not None
        and dados.consorcio_duracao_meses not in mercado.consorcio_duracoes_meses
    ):
        raise HTTPException(
            status_code=422,
            detail=(f"Duração de grupo indisponível. Opções: {mercado.consorcio_duracoes_meses}."),
        )
    resumo = ctx.orcamento(fonte)
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
        consorcio_duracao_meses=dados.consorcio_duracao_meses,
    )
    c = simulacao.consorcio
    j = simulacao.juntar
    r = simulacao.recomendacao
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
            iof_centavos=f.iof_centavos,
            tarifas_centavos=f.tarifas_centavos,
            cet_mensal_percentual=f.cet_mensal_percentual,
            cet_anual_percentual=f.cet_anual_percentual,
            taxa_mensal=mercado.financiamento_taxa_mensal,
            acima_da_margem=f.acima_da_margem,
            duracoes_disponiveis=sorted(mercado.financiamento_duracoes_meses),
            ranking=[
                TaxaOut(
                    instituicao=t.instituicao,
                    taxa_mensal_percentual=t.taxa_mensal_percentual,
                    taxa_anual_percentual=t.taxa_anual_percentual,
                )
                for t in sorted(taxas.taxas, key=lambda t: t.posicao)
            ],
            fonte=FonteOut(
                descricao=FONTE_BCB,
                inicio_periodo=taxas.inicio_periodo,
                fim_periodo=taxas.fim_periodo,
                url="https://www.bcb.gov.br/estatisticas/txjuros",
            ),
            ressalvas=[RessalvaOut(codigo=r.codigo, texto=r.texto) for r in f.ressalvas],
        ),
        consorcio=ConsorcioOut(
            carta_credito_centavos=c.carta_credito_centavos,
            duracao_meses=c.duracao_meses,
            parcela_centavos=c.parcela_centavos,
            custo_total_centavos=c.custo_total_centavos,
            taxa_administracao_centavos=c.taxa_administracao_centavos,
            taxa_administracao_percentual=_percentual(mercado.consorcio_taxa_administracao),
            fundo_reserva_centavos=c.fundo_reserva_centavos,
            fundo_reserva_percentual=_percentual(mercado.consorcio_fundo_reserva),
            reajuste_anual_percentual=_percentual(mercado.consorcio_reajuste_anual),
            acima_da_margem=c.acima_da_margem,
            janela=JanelaOut(**vars(c.janela)),
            duracoes_disponiveis=sorted(mercado.consorcio_duracoes_meses),
            ressalvas=[RessalvaOut(codigo=r.codigo, texto=r.texto) for r in c.ressalvas],
        ),
        juntar=JuntarOut(
            deposito_mensal_centavos=j.deposito_mensal_centavos,
            mes_compra=j.mes_compra,
            custo_total_centavos=j.custo_total_centavos,
            preco_na_compra_centavos=j.preco_na_compra_centavos,
            entrega_ate_prazo=j.entrega_ate_prazo,
            rendimento_anual_percentual=j.rendimento_anual_percentual,
            ipca_anual_percentual=j.ipca_anual_percentual,
            fonte=FonteFocusOut(
                descricao="Banco Central do Brasil: pesquisa Focus (medianas)",
                data_pesquisa=focus.data_pesquisa,
                url="https://www.bcb.gov.br/publicacoes/focus",
            ),
            ressalvas=[RessalvaOut(codigo=r.codigo, texto=r.texto) for r in j.ressalvas],
        ),
        recomendacao=RecomendacaoOut(
            caminho=r.caminho,
            avaliacoes=[AvaliacaoOut(**vars(a)) for a in r.avaliacoes],
            ressalvas=[RessalvaOut(codigo=x.codigo, texto=x.texto) for x in r.ressalvas],
            ajustes=None if r.ajustes is None else AjustesOut(**vars(r.ajustes)),
        ),
    )
    ctx.simulacoes[saida.id] = (conta_id, saida)
    return saida


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.post("/v1/simulacoes", status_code=201)
    def criar(dados: NovaSimulacao, request: Request) -> SimulacaoOut:
        fonte = ctx.fonte_da_sessao(request)
        return criar_simulacao(ctx, ctx.conta_da_sessao(request).id, fonte, dados)

    @rotas.get("/v1/simulacoes/{simulacao_id}")
    def ler(simulacao_id: str, request: Request) -> SimulacaoOut:
        conta_id = ctx.conta_da_sessao(request).id
        dono, simulacao = ctx.simulacoes.get(simulacao_id, (None, None))
        if dono != conta_id or not isinstance(simulacao, SimulacaoOut):
            raise HTTPException(status_code=404, detail="Simulação não encontrada.")
        return simulacao

    return rotas
