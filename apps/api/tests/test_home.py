import apoio
import pytest
from apoio import config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app


def client() -> TestClient:
    return TestClient(create_app(config_de_teste()))


def entrar_como(persona_id: str, http: TestClient | None = None) -> TestClient:
    http = http or client()
    apoio.entrar_como(http, persona_id)
    return http


def test_health_reports_ok() -> None:
    response = client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("persona_id", "nome", "entradas", "gastos", "sobra", "margem", "margem_acima_da_sobra"),
    [
        ("ana", "Ana", 950_000, 610_000, 340_000, 285_000, False),
        ("bruno", "Bruno", 680_000, 490_000, 190_000, 204_000, True),
        ("carla", "Carla", 650_000, 430_000, 220_000, 195_000, False),
        ("diego", "Diego", 520_000, 490_000, 30_000, 156_000, True),
    ],
)
def test_home_shows_the_personas_three_month_budget(
    persona_id: str,
    nome: str,
    entradas: int,
    gastos: int,
    sobra: int,
    margem: int,
    margem_acima_da_sobra: bool,
) -> None:
    response = entrar_como(persona_id).get("/v1/home")

    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == nome
    assert body["resumo"] == {
        "entradas_centavos": entradas,
        "gastos_centavos": gastos,
        "sobra_mensal_centavos": sobra,
        "margem_segura_centavos": margem,
        "margem_acima_da_sobra": margem_acima_da_sobra,
    }
    assert len(body["sugestoes"]) >= 1


def test_home_requires_a_session() -> None:
    assert client().get("/v1/home").status_code == 401


def test_entering_as_an_unknown_persona_is_rejected() -> None:
    response = client().post("/v1/sessoes/demo", json={"persona_id": "zeca"})

    assert response.status_code == 404


def test_margem_segura_percentual_is_configurable() -> None:
    http = TestClient(create_app(config_de_teste(margem_segura_percentual=25)))

    resumo = entrar_como("bruno", http).get("/v1/home").json()["resumo"]

    assert resumo["margem_segura_centavos"] == 170_000
    assert resumo["margem_acima_da_sobra"] is False
