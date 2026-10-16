from pathlib import Path
from typing import Any

from apoio import config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app

NUMEROS = (
    "duracao_meses",
    "parcela_centavos",
    "juros_centavos",
    "taxa_mensal",
    "acima_da_margem",
    "duracoes_disponiveis",
)

CARRO_80_MIL = {"item": "carro", "valor_centavos": 8_000_000, "prazo_meses": 60}


def sessao(persona_id: str, http: TestClient | None = None) -> TestClient:
    http = http or TestClient(create_app(config_de_teste()))
    http.post("/v1/sessoes/demo", json={"persona_id": persona_id})
    return http


def test_simulates_financing_within_the_personas_margem_segura() -> None:
    http = sessao("bruno")

    response = http.post("/v1/simulacoes", json=CARRO_80_MIL)

    assert response.status_code == 201
    simulacao: dict[str, Any] = response.json()
    assert simulacao["objetivo"] == {**CARRO_80_MIL, "entrada_centavos": 0}
    financiamento = simulacao["financiamento"]
    assert {k: financiamento[k] for k in NUMEROS} == {
        "duracao_meses": 72,
        "parcela_centavos": 199_114,
        "juros_centavos": 6_336_208,
        "taxa_mensal": "0.018",
        "acima_da_margem": False,
        "duracoes_disponiveis": [12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72],
    }
    assert simulacao["snapshot_id"] == "bcb-veiculos-pf-2026-09-24"


def test_a_simulacao_can_be_read_back() -> None:
    http = sessao("bruno")
    criada = http.post("/v1/simulacoes", json=CARRO_80_MIL).json()

    response = http.get(f"/v1/simulacoes/{criada['id']}")

    assert response.status_code == 200
    assert response.json() == criada


def test_the_person_can_choose_the_duracao() -> None:
    http = sessao("bruno")

    response = http.post("/v1/simulacoes", json={**CARRO_80_MIL, "duracao_meses": 60})

    financiamento = response.json()["financiamento"]
    assert financiamento["parcela_centavos"] == 219_136
    assert financiamento["acima_da_margem"] is True


def test_another_session_cannot_read_the_simulacao() -> None:
    app = create_app(config_de_teste())
    criada = sessao("bruno", TestClient(app)).post("/v1/simulacoes", json=CARRO_80_MIL).json()

    response = sessao("ana", TestClient(app)).get(f"/v1/simulacoes/{criada['id']}")

    assert response.status_code == 404


def test_simulating_requires_a_session() -> None:
    response = TestClient(create_app(config_de_teste())).post("/v1/simulacoes", json=CARRO_80_MIL)

    assert response.status_code == 401


def test_rejects_an_entrada_that_covers_the_whole_value() -> None:
    response = sessao("bruno").post(
        "/v1/simulacoes", json={**CARRO_80_MIL, "entrada_centavos": 8_000_000}
    )

    assert response.status_code == 422


def test_rejects_a_duracao_the_market_does_not_offer() -> None:
    response = sessao("bruno").post("/v1/simulacoes", json={**CARRO_80_MIL, "duracao_meses": 61})

    assert response.status_code == 422


def taxa(instituicao: str, mensal: str, anual: str) -> dict[str, str]:
    return {
        "instituicao": instituicao,
        "taxa_mensal_percentual": mensal,
        "taxa_anual_percentual": anual,
    }


def test_financing_shows_the_institutions_ranking_and_its_source() -> None:
    financiamento = (
        sessao("bruno").post("/v1/simulacoes", json=CARRO_80_MIL).json()["financiamento"]
    )

    assert financiamento["ranking"] == [
        {
            "instituicao": "BANCO ALFA",
            "taxa_mensal_percentual": "1.20",
            "taxa_anual_percentual": "15.39",
        },
        {
            "instituicao": "BANCO BETA",
            "taxa_mensal_percentual": "1.80",
            "taxa_anual_percentual": "23.87",
        },
        {
            "instituicao": "BANCO GAMA",
            "taxa_mensal_percentual": "2.40",
            "taxa_anual_percentual": "32.92",
        },
    ]
    assert financiamento["fonte"] == {
        "descricao": (
            "Banco Central do Brasil: taxas médias de aquisição de veículos (pessoa física)"
        ),
        "inicio_periodo": "2026-09-24",
        "fim_periodo": "2026-09-30",
        "url": "https://www.bcb.gov.br/estatisticas/txjuros",
    }
    assert [r["codigo"] for r in financiamento["ressalvas"]] == ["taxa_media", "cet_estimado"]
    assert "perfil de crédito" in financiamento["ressalvas"][0]["texto"]


def test_a_snapshot_older_than_30_days_past_its_period_is_flagged() -> None:
    from datetime import date

    http = sessao("bruno", TestClient(create_app(config_de_teste(hoje=lambda: date(2026, 11, 15)))))

    financiamento = http.post("/v1/simulacoes", json=CARRO_80_MIL).json()["financiamento"]

    assert [r["codigo"] for r in financiamento["ressalvas"]] == [
        "taxa_media",
        "cet_estimado",
        "dados_desatualizados",
    ]


def test_without_any_market_snapshot_simulation_is_unavailable(tmp_path: Path) -> None:
    http = sessao("bruno", TestClient(create_app(config_de_teste(diretorio_mercado=tmp_path))))

    response = http.post("/v1/simulacoes", json=CARRO_80_MIL)

    assert response.status_code == 503


def test_financing_shows_the_estimated_cet_and_its_parts() -> None:
    http = sessao("bruno", TestClient(create_app(config_de_teste(tarifas_centavos=105_000))))

    financiamento = http.post("/v1/simulacoes", json=CARRO_80_MIL).json()["financiamento"]

    assert financiamento["tarifas_centavos"] == 105_000
    assert financiamento["iof_centavos"] > 0.0038 * 8_000_000
    assert financiamento["custo_total_centavos"] == (
        72 * 199_114 + financiamento["iof_centavos"] + 105_000
    )
    assert float(financiamento["cet_mensal_percentual"]) > 1.80
    assert (
        float(financiamento["cet_anual_percentual"])
        > float(financiamento["cet_mensal_percentual"]) * 12
    )


def test_simulates_the_consorcio_alongside_financing() -> None:
    consorcio = sessao("bruno").post("/v1/simulacoes", json=CARRO_80_MIL).json()["consorcio"]

    # 80,000 x 1.17 / 48 = 1,950 fits Bruno's 2,040; 36 months (2,600) would not.
    assert consorcio["duracao_meses"] == 48
    assert consorcio["parcela_centavos"] == 195_000
    assert consorcio["carta_credito_centavos"] == 8_000_000
    assert consorcio["acima_da_margem"] is False
    assert consorcio["janela"]["melhor_caso_mes"] == 1
    assert consorcio["janela"]["pior_caso_mes"] == 48
    assert consorcio["janela"]["chance_ate_prazo_percentual"] == 100
    assert consorcio["taxa_administracao_percentual"] == "15.00"
    assert consorcio["duracoes_disponiveis"] == [36, 48, 60, 72, 80]
    assert [r["codigo"] for r in consorcio["ressalvas"]] == [
        "contemplacao_incerta",
        "faixas_de_mercado",
    ]


def test_the_person_can_choose_the_consorcio_duracao() -> None:
    response = sessao("bruno").post(
        "/v1/simulacoes", json={**CARRO_80_MIL, "consorcio_duracao_meses": 60}
    )

    assert response.json()["consorcio"]["parcela_centavos"] == 156_000


def test_rejects_a_consorcio_duracao_the_market_does_not_offer() -> None:
    response = sessao("bruno").post(
        "/v1/simulacoes", json={**CARRO_80_MIL, "consorcio_duracao_meses": 50}
    )

    assert response.status_code == 422


def test_simulates_saving_the_margem_segura_until_buying_in_cash() -> None:
    juntar = sessao("bruno").post("/v1/simulacoes", json=CARRO_80_MIL).json()["juntar"]

    assert juntar["deposito_mensal_centavos"] == 204_000
    # 80,000 / 2,040 is 40 months without yield; the yield beats the 5% price rise.
    assert 30 <= juntar["mes_compra"] < 40
    assert juntar["entrega_ate_prazo"] is True
    assert juntar["custo_total_centavos"] == 204_000 * juntar["mes_compra"]
    assert juntar["rendimento_anual_percentual"] == "13.00"
    assert juntar["ipca_anual_percentual"] == "5.00"
    assert juntar["fonte"]["data_pesquisa"] == "2026-10-09"
    assert [r["codigo"] for r in juntar["ressalvas"]] == [
        "rendimento_de_referencia",
        "preco_projetado",
    ]


def test_the_consorcio_carta_adjusts_by_the_projected_ipca() -> None:
    consorcio = sessao("bruno").post("/v1/simulacoes", json=CARRO_80_MIL).json()["consorcio"]

    assert consorcio["reajuste_anual_percentual"] == "5.00"


def test_without_focus_projections_simulation_is_unavailable(tmp_path: Path) -> None:
    http = sessao("bruno", TestClient(create_app(config_de_teste(diretorio_focus=tmp_path))))

    assert http.post("/v1/simulacoes", json=CARRO_80_MIL).status_code == 503


def test_every_simulacao_carries_a_recomendacao_with_reasons() -> None:
    recomendacao = sessao("bruno").post("/v1/simulacoes", json=CARRO_80_MIL).json()[
        "recomendacao"
    ]

    assert recomendacao["caminho"] == "juntar"
    assert {a["caminho"]: a["motivo_codigo"] for a in recomendacao["avaliacoes"]} == {
        "financiamento": "custo_maior",
        "consorcio": "custo_maior",
        "juntar": None,
    }
    assert [r["codigo"] for r in recomendacao["ressalvas"]] == ["acima_da_sobra"]
    assert recomendacao["ajustes"] is None


def test_when_nothing_fits_the_recomendacao_suggests_adjustments() -> None:
    response = sessao("diego").post("/v1/simulacoes", json={**CARRO_80_MIL, "prazo_meses": 12})

    recomendacao = response.json()["recomendacao"]
    assert recomendacao["caminho"] is None
    ajustes = recomendacao["ajustes"]
    assert ajustes["entrada_minima_centavos"] > 0
    assert ajustes["prazo_minimo_meses"] > 12
    assert 0 < ajustes["valor_maximo_centavos"] < 8_000_000
