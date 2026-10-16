from fastapi.testclient import TestClient

from api.main import create_app


def client() -> TestClient:
    return TestClient(create_app())


def test_health_reports_ok() -> None:
    response = client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_returns_placeholder_budget_summary() -> None:
    response = client().get("/v1/home")

    assert response.status_code == 200
    body = response.json()
    assert body["placeholder"] is True
    resumo = body["resumo"]
    assert resumo["sobra_mensal_centavos"] == (
        resumo["entradas_centavos"] - resumo["gastos_centavos"]
    )
    assert resumo["margem_segura_centavos"] == resumo["entradas_centavos"] * 30 // 100
    assert len(body["sugestoes"]) >= 1
