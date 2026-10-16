from apoio import config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app


def test_lists_the_demo_personas() -> None:
    response = TestClient(create_app(config_de_teste())).get("/v1/personas")

    assert response.status_code == 200
    personas = response.json()
    assert [p["id"] for p in personas] == ["ana", "bruno", "carla", "diego"]
    assert all(p["nome"] and p["perfil"] and p["descricao"] for p in personas)
