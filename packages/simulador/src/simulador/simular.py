from dataclasses import replace
from decimal import ROUND_HALF_UP, Decimal

from simulador.consorcio import simular_consorcio
from simulador.juntar import simular_juntar
from simulador.modelo import (
    Ajustes,
    Financiamento,
    Objetivo,
    Orcamento,
    Ressalva,
    Simulacao,
    SnapshotMercado,
)
from simulador.recomendacao import (
    PASSO_CENTAVOS,
    algum_serve,
    menor_que_serve,
    prazo_minimo,
    recomendar,
)

TAXA_MEDIA = Ressalva(
    codigo="taxa_media",
    texto=(
        "A taxa é a média que as instituições informaram ao Banco Central. "
        "A sua depende do seu perfil de crédito."
    ),
)
CET_ESTIMADO = Ressalva(
    codigo="cet_estimado",
    texto=(
        "O CET é uma estimativa com IOF e tarifas típicas pagos na contratação. "
        "Seguros não estão incluídos."
    ),
)
DADOS_DESATUALIZADOS = Ressalva(
    codigo="dados_desatualizados",
    texto="Os dados de mercado mais recentes disponíveis estão desatualizados.",
)


def parcela_price(valor_centavos: int, taxa_mensal: Decimal, duracao_meses: int) -> int:
    """Fixed payment of the Tabela Price, rounded to the centavo."""
    valor = Decimal(valor_centavos)
    if taxa_mensal == 0:
        parcela = valor / duracao_meses
    else:
        parcela = valor * taxa_mensal / (1 - (1 + taxa_mensal) ** -duracao_meses)
    return int(parcela.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _menor_duracao_que_cabe(
    financiado: int, taxa: Decimal, duracoes: tuple[int, ...], orcamento: Orcamento
) -> int:
    """Shortest Duração whose payment fits the Margem segura, else the longest one."""
    for duracao in sorted(duracoes):
        if parcela_price(financiado, taxa, duracao) <= orcamento.margem_segura_centavos:
            return duracao
    return max(duracoes)


# IOF on credit for individuals (Decreto 6.306/2007): 0.38% flat plus 0.0082% a day on
# each amortized amount, counting at most 365 days.
IOF_ADICIONAL = Decimal("0.0038")
IOF_DIARIO = Decimal("0.000082")
IOF_DIAS_MAXIMOS = 365
DIAS_POR_MES = 30


def _centavos(valor: Decimal) -> int:
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def iof_financiamento(financiado: int, taxa: Decimal, parcela: int, duracao: int) -> int:
    saldo = Decimal(financiado)
    iof = Decimal(financiado) * IOF_ADICIONAL
    for mes in range(1, duracao + 1):
        amortizacao = saldo if mes == duracao else parcela - saldo * taxa
        dias = min(mes * DIAS_POR_MES, IOF_DIAS_MAXIMOS)
        iof += amortizacao * IOF_DIARIO * dias
        saldo -= amortizacao
    return _centavos(iof)


def taxa_interna_mensal(liquido_recebido: int, parcela: int, duracao: int) -> float:
    """Monthly rate that discounts all payments back to the amount actually received."""

    def valor_presente(taxa: float) -> float:
        return sum(parcela / (1 + taxa) ** mes for mes in range(1, duracao + 1))

    baixa, alta = 0.0, 1.0
    for _ in range(200):
        meio = (baixa + alta) / 2
        if valor_presente(meio) > liquido_recebido:
            baixa = meio
        else:
            alta = meio
    return (baixa + alta) / 2


def _percentual(fracao: float) -> Decimal:
    return Decimal(str(fracao * 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ressalvas(mercado: SnapshotMercado) -> tuple[Ressalva, ...]:
    if mercado.desatualizado:
        return (TAXA_MEDIA, CET_ESTIMADO, DADOS_DESATUALIZADOS)
    return (TAXA_MEDIA, CET_ESTIMADO)


def _financiamento(
    objetivo: Objetivo,
    orcamento: Orcamento,
    mercado: SnapshotMercado,
    duracao_meses: int | None,
) -> Financiamento:
    financiado = objetivo.valor_centavos - objetivo.entrada_centavos
    taxa = mercado.financiamento_taxa_mensal
    if duracao_meses is None:
        duracao_meses = _menor_duracao_que_cabe(
            financiado, taxa, mercado.financiamento_duracoes_meses, orcamento
        )
    parcela = parcela_price(financiado, taxa, duracao_meses)
    iof = iof_financiamento(financiado, taxa, parcela, duracao_meses)
    tarifas = mercado.tarifas_centavos
    cet = taxa_interna_mensal(financiado - iof - tarifas, parcela, duracao_meses)
    return Financiamento(
        duracao_meses=duracao_meses,
        parcela_centavos=parcela,
        custo_total_centavos=objetivo.entrada_centavos + parcela * duracao_meses + iof + tarifas,
        juros_centavos=parcela * duracao_meses - financiado,
        iof_centavos=iof,
        tarifas_centavos=tarifas,
        cet_mensal_percentual=_percentual(cet),
        cet_anual_percentual=_percentual((1 + cet) ** 12 - 1),
        acima_da_margem=parcela > orcamento.margem_segura_centavos,
        ressalvas=_ressalvas(mercado),
    )


def _algum_serve(objetivo: Objetivo, orcamento: Orcamento, mercado: SnapshotMercado) -> bool:
    return algum_serve(
        _financiamento(objetivo, orcamento, mercado, None),
        simular_consorcio(objetivo, orcamento, mercado, None),
        simular_juntar(objetivo, orcamento, mercado),
        objetivo.prazo_meses,
    )


def _ajustes(objetivo: Objetivo, orcamento: Orcamento, mercado: SnapshotMercado) -> Ajustes:
    """Each adjustment on its own, with every other input unchanged and default Durações."""
    valor = objetivo.valor_centavos
    entrada = menor_que_serve(
        objetivo.entrada_centavos + PASSO_CENTAVOS,
        valor - PASSO_CENTAVOS,
        lambda e: _algum_serve(replace(objetivo, entrada_centavos=e), orcamento, mercado),
    )
    # A cheaper item helps monotonically, so search the discount instead of the value.
    desconto = menor_que_serve(
        PASSO_CENTAVOS,
        valor - objetivo.entrada_centavos - PASSO_CENTAVOS,
        lambda d: _algum_serve(replace(objetivo, valor_centavos=valor - d), orcamento, mercado),
    )
    return Ajustes(
        entrada_minima_centavos=entrada,
        prazo_minimo_meses=prazo_minimo(
            _financiamento(objetivo, orcamento, mercado, None),
            simular_consorcio(objetivo, orcamento, mercado, None),
            simular_juntar(objetivo, orcamento, mercado),
        ),
        valor_maximo_centavos=None if desconto is None else valor - desconto,
    )


def simular(
    objetivo: Objetivo,
    orcamento: Orcamento,
    mercado: SnapshotMercado,
    duracao_meses: int | None = None,
    consorcio_duracao_meses: int | None = None,
) -> Simulacao:
    financiamento = _financiamento(objetivo, orcamento, mercado, duracao_meses)
    consorcio = simular_consorcio(objetivo, orcamento, mercado, consorcio_duracao_meses)
    juntar = simular_juntar(objetivo, orcamento, mercado)
    return Simulacao(
        objetivo=objetivo,
        snapshot_id=mercado.id,
        financiamento=financiamento,
        consorcio=consorcio,
        juntar=juntar,
        recomendacao=recomendar(
            objetivo,
            orcamento,
            financiamento,
            consorcio,
            juntar,
            lambda: _ajustes(objetivo, orcamento, mercado),
        ),
    )
