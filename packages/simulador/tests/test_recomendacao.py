from datetime import date
from decimal import Decimal

from simulador import Objetivo, Orcamento, Projecoes, SnapshotMercado, simular

# Zero yield, inflation and income tax keep every Caminho hand-checkable:
# Juntar costs exactly the item value, the Consórcio 1.17 x the Carta.
MERCADO = SnapshotMercado(
    id="teste",
    financiamento_taxa_mensal=Decimal("0.018"),
    consorcio_reajuste_anual=Decimal(0),
    projecoes=Projecoes(
        data_base=date(2026, 10, 1),
        selic_anual={2026: Decimal(0)},
        ipca_anual={2026: Decimal(0)},
        fonte_data=date(2026, 10, 9),
    ),
    ir_aliquotas=(Decimal(0), Decimal(0), Decimal(0), Decimal(0)),
)
BRUNO = Orcamento(margem_segura_centavos=204_000, sobra_mensal_centavos=190_000)
APERTADO = Orcamento(margem_segura_centavos=150_000, sobra_mensal_centavos=150_000)


def carro(prazo: int, valor: int = 8_000_000) -> Objetivo:
    return Objetivo(item="carro", valor_centavos=valor, prazo_meses=prazo)


def motivos(simulacao_recomendacao: object) -> dict[str, str | None]:
    return {a.caminho: a.motivo_codigo for a in simulacao_recomendacao.avaliacoes}  # type: ignore[attr-defined]


def test_among_caminhos_that_deliver_and_fit_the_cheapest_wins() -> None:
    # Juntar: 40 months, 80,000. Consórcio: 48 months, 93,600. Financing: 72 x 1,991.14.
    recomendacao = simular(carro(prazo=60), BRUNO, MERCADO).recomendacao

    assert recomendacao.caminho == "juntar"
    assert motivos(recomendacao) == {
        "juntar": None,
        "consorcio": "custo_maior",
        "financiamento": "custo_maior",
    }
    assert recomendacao.ajustes is None


def test_caminhos_that_cannot_deliver_by_the_prazo_are_dropped() -> None:
    # Prazo 24: Juntar needs 40 months and the shortest fitting group is 48.
    recomendacao = simular(carro(prazo=24), BRUNO, MERCADO).recomendacao

    assert recomendacao.caminho == "financiamento"
    assert motivos(recomendacao) == {
        "juntar": "nao_entrega_no_prazo",
        "consorcio": "nao_entrega_no_prazo",
        "financiamento": None,
    }


def test_a_recomendacao_above_the_sobra_mensal_carries_a_ressalva() -> None:
    # Financing at 1,991.14 fits Bruno's margem (2,040) but not his sobra (1,900).
    recomendacao = simular(carro(prazo=24), BRUNO, MERCADO).recomendacao

    assert [r.codigo for r in recomendacao.ressalvas] == ["acima_da_sobra"]


def test_no_ressalva_when_the_payment_fits_the_sobra() -> None:
    folgado = Orcamento(margem_segura_centavos=204_000, sobra_mensal_centavos=300_000)

    recomendacao = simular(carro(prazo=60), folgado, MERCADO).recomendacao

    assert recomendacao.caminho == "juntar"
    assert recomendacao.ressalvas == ()


def test_saving_the_margem_above_the_sobra_also_carries_the_ressalva() -> None:
    # Bruno would deposit his 2,040 margem, more than the 1,900 he has left each month.
    recomendacao = simular(carro(prazo=60), BRUNO, MERCADO).recomendacao

    assert recomendacao.caminho == "juntar"
    assert [r.codigo for r in recomendacao.ressalvas] == ["acima_da_sobra"]


def test_when_nothing_fits_there_is_no_recomendacao_but_adjustments() -> None:
    # Margem 1,500, Prazo 24. Financing needs 1,991.14 even in 72 months; Juntar needs
    # 54 months; the shortest fitting group is 72. Financing fits once the financed
    # amount is at most PV(1,500; 1.8%; 72) = 60,267.
    recomendacao = simular(carro(prazo=24), APERTADO, MERCADO).recomendacao

    assert recomendacao.caminho is None
    assert motivos(recomendacao) == {
        "juntar": "nao_entrega_no_prazo",
        "consorcio": "nao_entrega_no_prazo",
        "financiamento": "acima_da_margem",
    }
    assert recomendacao.ajustes is not None
    assert recomendacao.ajustes.entrada_minima_centavos == 1_980_000
    assert recomendacao.ajustes.prazo_minimo_meses == 54
    assert recomendacao.ajustes.valor_maximo_centavos == 6_020_000


def test_every_dropped_caminho_explains_why_in_plain_language() -> None:
    recomendacao = simular(carro(prazo=24), APERTADO, MERCADO).recomendacao

    textos = {a.caminho: a.motivo_texto for a in recomendacao.avaliacoes}
    assert textos["juntar"] == "Você só teria o carro no mês 54, depois do seu Prazo de 24 meses."
    assert textos["financiamento"] == "A parcela de R$ 1.991,14 passa da sua margem de R$ 1.500,00."
