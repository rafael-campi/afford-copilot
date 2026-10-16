from decimal import Decimal

import pytest

from simulador import Objetivo, Orcamento, SnapshotMercado, simular

SEM_LIMITE = Orcamento(margem_segura_centavos=10**12, sobra_mensal_centavos=10**12)


def mercado(taxa_mensal: str) -> SnapshotMercado:
    return SnapshotMercado(id="teste", financiamento_taxa_mensal=Decimal(taxa_mensal))


@pytest.mark.parametrize(
    ("valor", "taxa", "duracao", "parcela"),
    [
        # Classic Tabela Price textbook cases.
        (1_000_000, "0.01", 12, 88_849),
        (100_000, "0.10", 5, 26_380),
    ],
)
def test_payment_follows_tabela_price(valor: int, taxa: str, duracao: int, parcela: int) -> None:
    objetivo = Objetivo(item="carro", valor_centavos=valor, prazo_meses=60)

    simulacao = simular(objetivo, SEM_LIMITE, mercado(taxa), duracao_meses=duracao)

    assert simulacao.financiamento.parcela_centavos == parcela
    assert simulacao.financiamento.duracao_meses == duracao


def test_interest_is_all_payments_minus_the_financed_amount() -> None:
    objetivo = Objetivo(
        item="carro", valor_centavos=1_100_000, prazo_meses=60, entrada_centavos=100_000
    )

    financiamento = simular(objetivo, SEM_LIMITE, mercado("0.01"), duracao_meses=12).financiamento

    assert financiamento.parcela_centavos == 88_849
    assert financiamento.juros_centavos == 66_188


BRUNO = Orcamento(margem_segura_centavos=204_000, sobra_mensal_centavos=190_000)


@pytest.mark.parametrize(
    ("entrada", "duracao", "parcela"),
    [
        (0, 72, 199_114),  # 66 months would cost 2,081.13 > 2,040
        (1_000_000, 54, 203_755),  # 48 months would cost 2,190.25 > 2,040
    ],
)
def test_default_duracao_is_the_shortest_that_fits_the_margem_segura(
    entrada: int, duracao: int, parcela: int
) -> None:
    objetivo = Objetivo(
        item="carro", valor_centavos=8_000_000, prazo_meses=60, entrada_centavos=entrada
    )

    financiamento = simular(objetivo, BRUNO, mercado("0.018")).financiamento

    assert financiamento.duracao_meses == duracao
    assert financiamento.parcela_centavos == parcela
    assert financiamento.acima_da_margem is False


def test_when_no_duracao_fits_it_uses_the_longest_and_flags_it() -> None:
    apertado = Orcamento(margem_segura_centavos=150_000, sobra_mensal_centavos=100_000)
    objetivo = Objetivo(item="carro", valor_centavos=8_000_000, prazo_meses=60)

    financiamento = simular(objetivo, apertado, mercado("0.018")).financiamento

    assert financiamento.duracao_meses == 72
    assert financiamento.parcela_centavos == 199_114
    assert financiamento.acima_da_margem is True


def test_an_overridden_duracao_above_the_margem_is_flagged() -> None:
    objetivo = Objetivo(item="carro", valor_centavos=8_000_000, prazo_meses=60)

    financiamento = simular(objetivo, BRUNO, mercado("0.018"), duracao_meses=60).financiamento

    assert financiamento.parcela_centavos == 219_136
    assert financiamento.acima_da_margem is True


def test_financing_always_warns_that_the_rate_is_an_average() -> None:
    objetivo = Objetivo(item="carro", valor_centavos=8_000_000, prazo_meses=60)

    financiamento = simular(objetivo, BRUNO, mercado("0.018")).financiamento

    assert [r.codigo for r in financiamento.ressalvas] == ["taxa_media", "cet_estimado"]


def test_a_stale_market_snapshot_adds_a_ressalva() -> None:
    objetivo = Objetivo(item="carro", valor_centavos=8_000_000, prazo_meses=60)
    antigo = SnapshotMercado(
        id="antigo", financiamento_taxa_mensal=Decimal("0.018"), desatualizado=True
    )

    financiamento = simular(objetivo, BRUNO, antigo).financiamento

    assert [r.codigo for r in financiamento.ressalvas] == [
        "taxa_media",
        "cet_estimado",
        "dados_desatualizados",
    ]
