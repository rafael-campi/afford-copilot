import pytest
from fastapi.testclient import TestClient

from api.main import Config, create_app
from seed.gerador import gerar_extrato


def sessao(persona_id: str, seed: int = 2026) -> TestClient:
    http = TestClient(create_app(Config(seed=seed)))
    http.post("/v1/sessoes/demo", json={"persona_id": persona_id})
    return http


def extrato_de(persona_id: str, seed: int = 2026) -> list[dict[str, object]]:
    response = sessao(persona_id, seed).get("/v1/extrato")
    assert response.status_code == 200
    transacoes: list[dict[str, object]] = response.json()["transacoes"]
    return transacoes


@pytest.mark.parametrize("persona_id", ["ana", "bruno", "carla", "diego"])
def test_every_transaction_gets_the_category_of_the_answer_key(persona_id: str) -> None:
    gabarito = gerar_extrato(persona_id, 2026).gabarito

    categorias = [t["categoria"] for t in extrato_de(persona_id)]

    assert categorias == gabarito


def test_transfers_to_people_fall_into_outros() -> None:
    pix = [t for t in extrato_de("bruno") if str(t["descricao"]).startswith("PIX ENVIADO")]

    assert pix
    assert {t["categoria"] for t in pix} == {"Outros"}


def test_the_same_seed_always_generates_the_same_extrato() -> None:
    assert extrato_de("carla", seed=7) == extrato_de("carla", seed=7)


def test_another_seed_changes_the_transactions_but_not_the_budget() -> None:
    assert extrato_de("carla", seed=7) != extrato_de("carla", seed=8)
    assert (
        sessao("carla", seed=7).get("/v1/home").json()["resumo"]
        == sessao("carla", seed=8).get("/v1/home").json()["resumo"]
    )
