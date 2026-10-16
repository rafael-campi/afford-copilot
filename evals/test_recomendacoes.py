"""Deterministic eval scenarios: they run in CI on every PR and block the merge."""

import pytest
from cenarios import RECOMENDACOES, Recomendacao
from fastapi.testclient import TestClient

from api.config import Config
from api.main import create_app


def entrar(http: TestClient, persona: str) -> None:
    http.post("/v1/sessoes/demo", json={"persona_id": persona})
    pedido = http.post(
        "/v1/consentimentos",
        json={"banco": persona, "escopos": ["transacoes"], "meses_validade": 12},
    ).json()
    http.post("/v1/sessoes/reautenticar", json={"senha": "demo"})
    http.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")


@pytest.mark.parametrize("cenario", RECOMENDACOES, ids=lambda c: c.id)
def test_recomendacao(cenario: Recomendacao) -> None:
    # Real market snapshots from data/, real Personas; no model involved.
    http = TestClient(create_app(Config()))
    entrar(http, cenario.persona)

    simulacao = http.post("/v1/simulacoes", json=cenario.objetivo).json()

    assert simulacao["recomendacao"]["caminho"] == cenario.caminho, cenario.porque
