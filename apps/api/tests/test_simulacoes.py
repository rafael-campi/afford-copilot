from pathlib import Path
from typing import Any

from apoio import config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app

NUMEROS = (
    "duracao_meses",
    "parcela_centavos",
    "custo_total_centavos",
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
        "custo_total_centavos": 14_336_208,
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
    assert [r["codigo"] for r in financiamento["ressalvas"]] == ["taxa_media"]
    assert "perfil de crédito" in financiamento["ressalvas"][0]["texto"]


def test_a_snapshot_older_than_30_days_past_its_period_is_flagged() -> None:
    from datetime import date

    http = sessao("bruno", TestClient(create_app(config_de_teste(hoje=lambda: date(2026, 11, 15)))))

    financiamento = http.post("/v1/simulacoes", json=CARRO_80_MIL).json()["financiamento"]

    assert [r["codigo"] for r in financiamento["ressalvas"]] == [
        "taxa_media",
        "dados_desatualizados",
    ]


def test_without_any_market_snapshot_simulation_is_unavailable(tmp_path: Path) -> None:
    http = sessao("bruno", TestClient(create_app(config_de_teste(diretorio_mercado=tmp_path))))

    response = http.post("/v1/simulacoes", json=CARRO_80_MIL)

    assert response.status_code == 503
