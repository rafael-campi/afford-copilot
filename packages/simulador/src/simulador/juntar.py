"""Juntar e comprar à vista: deposit the Margem segura until it covers the projected price."""

from decimal import ROUND_HALF_UP, Decimal

from simulador.modelo import Juntar, Objetivo, Orcamento, Ressalva, SnapshotMercado

MESES_MAXIMOS = 240

RENDIMENTO_DE_REFERENCIA = Ressalva(
    codigo="rendimento_de_referencia",
    texto=(
        "Rendimento de referência: 100% do CDI projetado pela pesquisa Focus do Banco Central, "
        "já descontado o IR. Não é promessa de rendimento nem recomendação de investimento."
    ),
)
PRECO_PROJETADO = Ressalva(
    codigo="preco_projetado",
    texto="O preço do item foi corrigido pelo IPCA projetado pela pesquisa Focus.",
)


def _mensal(anual: Decimal) -> Decimal:
    return (1 + anual) ** (Decimal(1) / 12) - 1


def _ano_do_mes(mercado: SnapshotMercado, mes: int) -> int:
    base = mercado.projecoes.data_base
    return base.year + (base.month - 1 + mes - 1) // 12


def _aliquota_ir(mercado: SnapshotMercado, meses: int) -> Decimal:
    dias = meses * 30
    ate_180, ate_360, ate_720, acima = mercado.ir_aliquotas
    if dias <= 180:
        return ate_180
    if dias <= 360:
        return ate_360
    if dias <= 720:
        return ate_720
    return acima


def _centavos(valor: Decimal) -> int:
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def simular_juntar(objetivo: Objetivo, orcamento: Orcamento, mercado: SnapshotMercado) -> Juntar:
    deposito = orcamento.margem_segura_centavos
    # Each lot: (month deposited, amount deposited, current value).
    lotes: list[tuple[int, Decimal, Decimal]] = []
    if objetivo.entrada_centavos:
        entrada = Decimal(objetivo.entrada_centavos)
        lotes.append((0, entrada, entrada))
    preco = Decimal(objetivo.valor_centavos)
    mes_compra: int | None = None
    for mes in range(1, MESES_MAXIMOS + 1):
        ano = _ano_do_mes(mercado, mes)
        rendimento = _mensal(mercado.projecoes.selic(ano))
        lotes = [(m, aplicado, valor * (1 + rendimento)) for m, aplicado, valor in lotes]
        lotes.append((mes, Decimal(deposito), Decimal(deposito)))
        preco *= 1 + _mensal(mercado.projecoes.ipca(ano))
        liquido = sum(
            valor - _aliquota_ir(mercado, mes - m) * max(valor - aplicado, Decimal(0))
            for m, aplicado, valor in lotes
        )
        if liquido >= preco:
            mes_compra = mes
            break
    primeiro_ano = _ano_do_mes(mercado, 1)
    return Juntar(
        deposito_mensal_centavos=deposito,
        mes_compra=mes_compra,
        custo_total_centavos=(
            None if mes_compra is None else objetivo.entrada_centavos + deposito * mes_compra
        ),
        preco_na_compra_centavos=None if mes_compra is None else _centavos(preco),
        entrega_ate_prazo=mes_compra is not None and mes_compra <= objetivo.prazo_meses,
        rendimento_anual_percentual=(mercado.projecoes.selic(primeiro_ano) * 100).quantize(
            Decimal("0.01")
        ),
        ipca_anual_percentual=(mercado.projecoes.ipca(primeiro_ano) * 100).quantize(
            Decimal("0.01")
        ),
        ressalvas=(RENDIMENTO_DE_REFERENCIA, PRECO_PROJETADO),
    )
