"""Consórcio: payment, yearly Carta adjustment, Janela de contemplação and Lance."""

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from simulador.modelo import (
    Consorcio,
    JanelaContemplacao,
    Lance,
    Objetivo,
    Orcamento,
    Ressalva,
    SnapshotMercado,
)

FAIXAS_DE_MERCADO = Ressalva(
    codigo="faixas_de_mercado",
    texto=(
        "Taxa de administração e fundo de reserva são faixas típicas de mercado, "
        "não a oferta de uma administradora."
    ),
)


def _centavos(valor: Decimal) -> int:
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _total_devido(carta: int, mercado: SnapshotMercado) -> Decimal:
    taxas = mercado.consorcio_taxa_administracao + mercado.consorcio_fundo_reserva
    return Decimal(carta) * (1 + taxas)


def _parcela(carta: int, duracao: int, mercado: SnapshotMercado) -> int:
    return _centavos(_total_devido(carta, mercado) / duracao)


def janela_contemplacao(duracao: int, prazo: int, mercado: SnapshotMercado) -> JanelaContemplacao:
    sorteios = mercado.consorcio_sorteios_por_mes
    por_mes = sorteios + mercado.consorcio_lances_por_mes
    membros = duracao * por_mes
    nao_contemplado = Fraction(1)
    contemplado_ate: list[Fraction] = []
    for mes in range(1, duracao + 1):
        if mes == duracao:
            nao_contemplado = Fraction(0)
        else:
            restantes = membros - por_mes * (mes - 1)
            nao_contemplado *= 1 - Fraction(sorteios, restantes)
        contemplado_ate.append(1 - nao_contemplado)
    mediana = next(mes for mes, p in enumerate(contemplado_ate, 1) if p >= Fraction(1, 2))
    chance = contemplado_ate[min(prazo, duracao) - 1] * 100
    return JanelaContemplacao(
        melhor_caso_mes=1,
        mediana_mes=mediana,
        pior_caso_mes=duracao,
        chance_ate_prazo_percentual=_centavos(Decimal(chance.numerator) / chance.denominator),
    )


def simular_consorcio(
    objetivo: Objetivo,
    orcamento: Orcamento,
    mercado: SnapshotMercado,
    duracao_meses: int | None,
) -> Consorcio:
    carta = objetivo.valor_centavos - objetivo.entrada_centavos
    if duracao_meses is None:
        duracoes = sorted(mercado.consorcio_duracoes_meses)
        duracao_meses = next(
            (
                d
                for d in duracoes
                if _parcela(carta, d, mercado) <= orcamento.margem_segura_centavos
            ),
            duracoes[-1],
        )
    parcela = _parcela(carta, duracao_meses, mercado)
    reajuste = 1 + mercado.consorcio_reajuste_anual
    pago = sum(
        _centavos(parcela * reajuste ** ((mes - 1) // 12)) for mes in range(1, duracao_meses + 1)
    )
    janela = janela_contemplacao(duracao_meses, objetivo.prazo_meses, mercado)
    incerta = Ressalva(
        codigo="contemplacao_incerta",
        texto=(
            f"Sem lance, você pode receber a carta só no mês {duracao_meses}. "
            f"A chance de ser contemplado por sorteio até o seu Prazo é de "
            f"{janela.chance_ate_prazo_percentual}%."
        ),
    )
    return Consorcio(
        carta_credito_centavos=carta,
        duracao_meses=duracao_meses,
        parcela_centavos=parcela,
        custo_total_centavos=objetivo.entrada_centavos + pago,
        taxa_administracao_centavos=_centavos(carta * mercado.consorcio_taxa_administracao),
        fundo_reserva_centavos=_centavos(carta * mercado.consorcio_fundo_reserva),
        acima_da_margem=parcela > orcamento.margem_segura_centavos,
        janela=janela,
        ressalvas=(incerta, FAIXAS_DE_MERCADO),
    )


def aplicar_lance(consorcio: Consorcio, lance_centavos: int, mes: int, embutido: bool) -> Lance:
    """A Lance offered after `mes` payments pays down the balance; the rest is re-spread.

    A Lance embutido comes out of the Carta itself instead of the person's own money.
    """
    devido = consorcio.parcela_centavos * consorcio.duracao_meses
    saldo = devido - consorcio.parcela_centavos * mes - lance_centavos
    if saldo < 0 or mes >= consorcio.duracao_meses:
        raise ValueError("O lance não pode passar do saldo devedor.")
    return Lance(
        parcela_restante_centavos=_centavos(Decimal(saldo) / (consorcio.duracao_meses - mes)),
        carta_liberada_centavos=consorcio.carta_credito_centavos
        - (lance_centavos if embutido else 0),
        dinheiro_proprio_centavos=0 if embutido else lance_centavos,
    )
