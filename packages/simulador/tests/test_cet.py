from decimal import Decimal

from simulador import Objetivo, Orcamento, SnapshotMercado, simular

SEM_LIMITE = Orcamento(margem_segura_centavos=10**12, sobra_mensal_centavos=10**12)


def mercado(taxa: str, tarifas_centavos: int = 0) -> SnapshotMercado:
    return SnapshotMercado(
        id="teste", financiamento_taxa_mensal=Decimal(taxa), tarifas_centavos=tarifas_centavos
    )


def test_iof_of_a_single_payment_is_the_flat_rate_plus_30_days() -> None:
    # 10,000 x (0.38% + 0.0082% x 30 days) = 38.00 + 24.60
    objetivo = Objetivo(item="carro", valor_centavos=1_000_000, prazo_meses=60)

    financiamento = simular(objetivo, SEM_LIMITE, mercado("0.01"), duracao_meses=1).financiamento

    assert financiamento.iof_centavos == 6_260


def test_iof_counts_at_most_365_days_per_amortization() -> None:
    # 12,000 at 0% in 24 x 500: months 1-12 count 30k days, months 13-24 count 365 days.
    # 500 x 0.0082% x (30 x 78 + 365 x 12) + 0.38% x 12,000 = 275.52 + 45.60
    objetivo = Objetivo(item="carro", valor_centavos=1_200_000, prazo_meses=60)

    financiamento = simular(objetivo, SEM_LIMITE, mercado("0"), duracao_meses=24).financiamento

    assert financiamento.iof_centavos == 32_112


def test_total_cost_adds_entrada_payments_iof_and_fees() -> None:
    objetivo = Objetivo(
        item="carro", valor_centavos=1_300_000, prazo_meses=60, entrada_centavos=100_000
    )

    financiamento = simular(
        objetivo, SEM_LIMITE, mercado("0", tarifas_centavos=105_000), duracao_meses=24
    ).financiamento

    assert financiamento.parcela_centavos == 50_000
    assert financiamento.tarifas_centavos == 105_000
    assert financiamento.custo_total_centavos == 100_000 + 1_200_000 + 32_112 + 105_000


def test_cet_is_the_rate_the_person_really_pays_once_iof_is_counted() -> None:
    # Receives 10,000 - 62.60 now, pays 10,100 in a month: 10,100 / 9,937.40 - 1 = 1.6362% a.m.
    objetivo = Objetivo(item="carro", valor_centavos=1_000_000, prazo_meses=60)

    financiamento = simular(objetivo, SEM_LIMITE, mercado("0.01"), duracao_meses=1).financiamento

    assert financiamento.cet_mensal_percentual == Decimal("1.64")
    assert financiamento.cet_anual_percentual == Decimal("21.50")


def test_financing_says_the_cet_is_an_estimate_without_insurance() -> None:
    objetivo = Objetivo(item="carro", valor_centavos=1_000_000, prazo_meses=60)

    financiamento = simular(objetivo, SEM_LIMITE, mercado("0.01")).financiamento

    assert "cet_estimado" in [r.codigo for r in financiamento.ressalvas]
