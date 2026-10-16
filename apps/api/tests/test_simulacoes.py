from typing import Any

from fastapi.testclient import TestClient

from api.main import create_app

CARRO_80_MIL = {"item": "carro", "valor_centavos": 8_000_000, "prazo_meses": 60}


def sessao(persona_id: str, http: TestClient | None = None) -> TestClient:
    http = http or TestClient(create_app())
    http.post("/v1/sessoes/demo", json={"persona_id": persona_id})
    return http


def test_simulates_financing_within_the_personas_margem_segura() -> None:
    http = sessao("bruno")

    response = http.post("/v1/simulacoes", json=CARRO_80_MIL)

    assert response.status_code == 201
    simulacao: dict[str, Any] = response.json()
    assert simulacao["objetivo"] == {**CARRO_80_MIL, "entrada_centavos": 0}
    assert simulacao["financiamento"] == {
        "duracao_meses": 72,
        "parcela_centavos": 199_114,
        "custo_total_centavos": 14_336_208,
        "juros_centavos": 6_336_208,
        "taxa_mensal": "0.018",
        "acima_da_margem": False,
        "duracoes_disponiveis": [12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72],
    }
    assert simulacao["snapshot_id"]


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
    app = create_app()
    criada = sessao("bruno", TestClient(app)).post("/v1/simulacoes", json=CARRO_80_MIL).json()

    response = sessao("ana", TestClient(app)).get(f"/v1/simulacoes/{criada['id']}")

    assert response.status_code == 404


def test_simulating_requires_a_session() -> None:
    response = TestClient(create_app()).post("/v1/simulacoes", json=CARRO_80_MIL)

    assert response.status_code == 401


def test_rejects_an_entrada_that_covers_the_whole_value() -> None:
    response = sessao("bruno").post(
        "/v1/simulacoes", json={**CARRO_80_MIL, "entrada_centavos": 8_000_000}
    )

    assert response.status_code == 422


def test_rejects_a_duracao_the_market_does_not_offer() -> None:
    response = sessao("bruno").post("/v1/simulacoes", json={**CARRO_80_MIL, "duracao_meses": 61})

    assert response.status_code == 422
