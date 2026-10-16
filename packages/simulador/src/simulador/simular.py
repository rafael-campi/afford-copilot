from decimal import ROUND_HALF_UP, Decimal

from simulador.modelo import (
    Financiamento,
    Objetivo,
    Orcamento,
    Ressalva,
    Simulacao,
    SnapshotMercado,
)

TAXA_MEDIA = Ressalva(
    codigo="taxa_media",
    texto=(
        "A taxa é a média que as instituições informaram ao Banco Central. "
        "A sua depende do seu perfil de crédito."
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


def _ressalvas(mercado: SnapshotMercado) -> tuple[Ressalva, ...]:
    if mercado.desatualizado:
        return (TAXA_MEDIA, DADOS_DESATUALIZADOS)
    return (TAXA_MEDIA,)


def simular(
    objetivo: Objetivo,
    orcamento: Orcamento,
    mercado: SnapshotMercado,
    duracao_meses: int | None = None,
) -> Simulacao:
    financiado = objetivo.valor_centavos - objetivo.entrada_centavos
    taxa = mercado.financiamento_taxa_mensal
    if duracao_meses is None:
        duracao_meses = _menor_duracao_que_cabe(
            financiado, taxa, mercado.financiamento_duracoes_meses, orcamento
        )
    parcela = parcela_price(financiado, taxa, duracao_meses)
    return Simulacao(
        objetivo=objetivo,
        snapshot_id=mercado.id,
        financiamento=Financiamento(
            duracao_meses=duracao_meses,
            parcela_centavos=parcela,
            custo_total_centavos=objetivo.entrada_centavos + parcela * duracao_meses,
            juros_centavos=parcela * duracao_meses - financiado,
            acima_da_margem=parcela > orcamento.margem_segura_centavos,
            ressalvas=(TAXA_MEDIA, DADOS_DESATUALIZADOS)
            if mercado.desatualizado
            else (TAXA_MEDIA,),
        ),
    )
