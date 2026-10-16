from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

from simulador import Objetivo, Orcamento, Projecoes, SnapshotMercado, simular

# Annual rate whose monthly equivalent is 1%: 1.01 ** 12 - 1.
UM_POR_CENTO_AO_MES = Decimal("0.12682503013196972")
SEM_IR = (Decimal(0), Decimal(0), Decimal(0), Decimal(0))


def mercado(
    selic: Decimal = Decimal(0), ipca: Decimal = Decimal(0), **mudancas: Any
) -> SnapshotMercado:
    base = SnapshotMercado(
        id="teste",
        financiamento_taxa_mensal=Decimal("0.018"),
        projecoes=Projecoes(
            data_base=date(2026, 10, 1),
            selic_anual={2026: selic},
            ipca_anual={2026: ipca},
            fonte_data=date(2026, 10, 9),
        ),
        ir_aliquotas=SEM_IR,
    )
    return replace(base, **mudancas)


def orcamento(margem: int) -> Orcamento:
    return Orcamento(margem_segura_centavos=margem, sobra_mensal_centavos=margem)


def item(valor: int, entrada: int = 0, prazo: int = 60) -> Objetivo:
    return Objetivo(item="carro", valor_centavos=valor, prazo_meses=prazo, entrada_centavos=entrada)


def test_without_yield_or_inflation_it_takes_price_over_deposit_months() -> None:
    juntar = simular(item(1_200_000), orcamento(100_000), mercado()).juntar

    assert juntar.deposito_mensal_centavos == 100_000
    assert juntar.mes_compra == 12
    assert juntar.custo_total_centavos == 1_200_000


def test_yield_on_deposits_shortens_the_wait() -> None:
    # 1,000 a month at 1%: 1,000; 2,010; 3,030.10 >= 3,020 in month 3 (month 4 without yield).
    sem_rendimento = simular(item(302_000), orcamento(100_000), mercado()).juntar
    com_rendimento = simular(
        item(302_000), orcamento(100_000), mercado(selic=UM_POR_CENTO_AO_MES)
    ).juntar

    assert sem_rendimento.mes_compra == 4
    assert com_rendimento.mes_compra == 3
    assert com_rendimento.custo_total_centavos == 300_000


def test_inflation_raises_the_price_and_delays_the_purchase() -> None:
    # Price 1,000 rising 1% a month: 1,010; 1,020.10; 1,030.30. Deposits of 500 reach it in month 3.
    juntar = simular(item(100_000), orcamento(50_000), mercado(ipca=UM_POR_CENTO_AO_MES)).juntar

    assert juntar.mes_compra == 3
    assert juntar.preco_na_compra_centavos == 103_030


def test_income_tax_on_the_gains_can_delay_the_purchase() -> None:
    # 10,000 of Entrada at 1% a month. Month 5: gross 10,510.10, net of 22.5% IR 10,395.33 < 10,470.
    # Month 6: gross 10,615.20, net 10,476.78 >= 10,470. Without IR it would be month 5.
    com_ir = mercado(
        selic=UM_POR_CENTO_AO_MES,
        ir_aliquotas=(Decimal("0.225"), Decimal("0.20"), Decimal("0.175"), Decimal("0.15")),
    )

    sem_imposto = simular(
        item(1_047_000, entrada=1_000_000), orcamento(1), mercado(selic=UM_POR_CENTO_AO_MES)
    )
    com_imposto = simular(item(1_047_000, entrada=1_000_000), orcamento(1), com_ir)

    assert sem_imposto.juntar.mes_compra == 5
    assert com_imposto.juntar.mes_compra == 6


def test_it_says_whether_the_purchase_happens_by_the_prazo() -> None:
    juntar = simular(item(1_200_000, prazo=10), orcamento(100_000), mercado()).juntar

    assert juntar.entrega_ate_prazo is False


def test_a_goal_out_of_reach_has_no_purchase_month() -> None:
    juntar = simular(item(100_000_000), orcamento(1_000), mercado()).juntar

    assert juntar.mes_compra is None
    assert juntar.entrega_ate_prazo is False


def test_saving_names_no_product_and_promises_no_return() -> None:
    juntar = simular(item(1_200_000), orcamento(100_000), mercado()).juntar

    assert [r.codigo for r in juntar.ressalvas] == ["rendimento_de_referencia", "preco_projetado"]
    assert "não é promessa de rendimento" in juntar.ressalvas[0].texto.lower()
