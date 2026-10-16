from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest

from simulador import Objetivo, Orcamento, SnapshotMercado, aplicar_lance, simular

SEM_LIMITE = Orcamento(margem_segura_centavos=10**12, sobra_mensal_centavos=10**12)
BRUNO = Orcamento(margem_segura_centavos=204_000, sobra_mensal_centavos=190_000)


def mercado(**consorcio: Any) -> SnapshotMercado:
    base = SnapshotMercado(
        id="teste",
        financiamento_taxa_mensal=Decimal("0.018"),
        consorcio_taxa_administracao=Decimal("0.15"),
        consorcio_fundo_reserva=Decimal("0.02"),
        consorcio_reajuste_anual=Decimal("0"),
    )
    return replace(base, **consorcio)


def carro(valor: int = 8_000_000, prazo: int = 60, entrada: int = 0) -> Objetivo:
    return Objetivo(item="carro", valor_centavos=valor, prazo_meses=prazo, entrada_centavos=entrada)


def test_payment_spreads_the_carta_plus_fees_over_the_duracao() -> None:
    # 80,000 x (1 + 15% + 2%) / 60 = 1,560.00
    consorcio = simular(carro(), SEM_LIMITE, mercado(), consorcio_duracao_meses=60).consorcio

    assert consorcio.carta_credito_centavos == 8_000_000
    assert consorcio.parcela_centavos == 156_000
    assert consorcio.custo_total_centavos == 60 * 156_000
    assert consorcio.taxa_administracao_centavos == 1_200_000
    assert consorcio.fundo_reserva_centavos == 160_000


def test_the_yearly_carta_adjustment_raises_later_payments() -> None:
    # 12,000 / 24 = 500; year 2 pays 550: 12 x 500 + 12 x 550 = 12,600
    sem_taxas = mercado(
        consorcio_taxa_administracao=Decimal("0"),
        consorcio_fundo_reserva=Decimal("0"),
        consorcio_reajuste_anual=Decimal("0.10"),
    )

    consorcio = simular(
        carro(valor=1_200_000), SEM_LIMITE, sem_taxas, consorcio_duracao_meses=24
    ).consorcio

    assert consorcio.parcela_centavos == 50_000
    assert consorcio.custo_total_centavos == 1_260_000


def test_entrada_reduces_the_carta() -> None:
    consorcio = simular(
        carro(entrada=1_000_000), SEM_LIMITE, mercado(), consorcio_duracao_meses=60
    ).consorcio

    assert consorcio.carta_credito_centavos == 7_000_000
    assert consorcio.custo_total_centavos == 1_000_000 + 60 * 136_500


def test_default_duracao_is_the_shortest_group_that_fits_the_margem_segura() -> None:
    # 93,600 / 36 = 2,600 > 2,040; 93,600 / 48 = 1,950
    consorcio = simular(carro(), BRUNO, mercado()).consorcio

    assert consorcio.duracao_meses == 48
    assert consorcio.parcela_centavos == 195_000
    assert consorcio.acima_da_margem is False


@pytest.mark.parametrize(
    ("duracao", "prazo", "mediana", "chance"),
    [
        # 3 months, 6 members, 1 draw + 1 Lance a month. Without bidding:
        # P(not by 2) = 5/6 x 3/4 = 62.5%, so 37.5% by month 2; everyone left in month 3.
        (3, 2, 3, 38),
        (3, 3, 3, 100),
        # 2 months, 4 members: 1/4 in month 1, the rest in month 2.
        (2, 1, 2, 25),
    ],
)
def test_janela_de_contemplacao_for_someone_who_does_not_bid(
    duracao: int, prazo: int, mediana: int, chance: int
) -> None:
    sem_taxas = mercado(
        consorcio_taxa_administracao=Decimal("0"),
        consorcio_fundo_reserva=Decimal("0"),
        consorcio_duracoes_meses=(duracao,),
    )

    janela = simular(carro(prazo=prazo), SEM_LIMITE, sem_taxas).consorcio.janela

    assert (janela.melhor_caso_mes, janela.mediana_mes, janela.pior_caso_mes) == (
        1,
        mediana,
        duracao,
    )
    assert janela.chance_ate_prazo_percentual == chance


def test_consorcio_warns_about_uncertain_contemplation_and_market_fees() -> None:
    consorcio = simular(carro(), BRUNO, mercado()).consorcio

    assert [r.codigo for r in consorcio.ressalvas] == ["contemplacao_incerta", "faixas_de_mercado"]
    assert "48" in consorcio.ressalvas[0].texto


def test_lance_livre_pays_down_the_balance_and_lowers_the_remaining_payments() -> None:
    # 12,000 in 24 x 500, no fees. After 4 payments (2,000), a 4,000 Lance leaves
    # 6,000 for the remaining 20 months: 300 a month.
    sem_taxas = mercado(
        consorcio_taxa_administracao=Decimal("0"), consorcio_fundo_reserva=Decimal("0")
    )
    consorcio = simular(
        carro(valor=1_200_000), SEM_LIMITE, sem_taxas, consorcio_duracao_meses=24
    ).consorcio

    lance = aplicar_lance(consorcio, lance_centavos=400_000, mes=4, embutido=False)

    assert lance.parcela_restante_centavos == 30_000
    assert lance.carta_liberada_centavos == 1_200_000
    assert lance.dinheiro_proprio_centavos == 400_000


def test_lance_embutido_uses_part_of_the_carta_instead_of_own_money() -> None:
    sem_taxas = mercado(
        consorcio_taxa_administracao=Decimal("0"), consorcio_fundo_reserva=Decimal("0")
    )
    consorcio = simular(
        carro(valor=1_200_000), SEM_LIMITE, sem_taxas, consorcio_duracao_meses=24
    ).consorcio

    lance = aplicar_lance(consorcio, lance_centavos=400_000, mes=4, embutido=True)

    assert lance.parcela_restante_centavos == 30_000
    assert lance.carta_liberada_centavos == 800_000
    assert lance.dinheiro_proprio_centavos == 0
