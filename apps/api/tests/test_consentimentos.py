from datetime import UTC, datetime, timedelta

from apoio import conceder_consentimento, config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app


class Relogio:
    def __init__(self) -> None:
        self.agora = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.agora


def demo(persona_id: str = "bruno", relogio: Relogio | None = None) -> TestClient:
    config = config_de_teste(agora=relogio) if relogio else config_de_teste()
    http = TestClient(create_app(config))
    http.post("/v1/sessoes/demo", json={"persona_id": persona_id})
    return http


def pedir(http: TestClient, escopos: list[str] | None = None) -> dict[str, object]:
    response = http.post(
        "/v1/consentimentos",
        json={"banco": "bruno", "escopos": escopos or ["transacoes"], "meses_validade": 12},
    )
    assert response.status_code == 201
    pedido: dict[str, object] = response.json()
    return pedido


def test_the_extrato_needs_a_consentimento() -> None:
    response = demo().get("/v1/home")

    assert response.status_code == 409
    assert response.json()["detail"] == "Conecte seu banco ou importe seu extrato."


def test_lists_the_banks_that_can_be_connected() -> None:
    bancos = demo().get("/v1/bancos").json()

    assert [b["id"] for b in bancos] == ["ana", "bruno", "carla", "diego"]
    assert bancos[1]["nome"] == "Banco de demonstração do Bruno"


def test_requesting_a_consentimento_only_creates_a_pending_confirmation() -> None:
    http = demo()

    pedido = pedir(http)

    assert pedido["acao"] == "conceder_consentimento"
    assert pedido["resumo"] == {
        "banco": "Banco de demonstração do Bruno",
        "escopos": ["transacoes"],
        "meses_validade": 12,
        "expira_em": "2027-10-10",
    }
    assert http.get("/v1/home").status_code == 409


def test_confirming_requires_a_recent_reauthentication() -> None:
    http = demo()
    pedido = pedir(http)

    sem = http.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")
    http.post("/v1/sessoes/reautenticar", json={"senha": "demo"})
    com = http.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")

    assert sem.status_code == 403
    assert sem.json()["detail"] == "Confirme sua senha para continuar."
    assert com.status_code == 200
    assert http.get("/v1/home").status_code == 200


def test_a_confirmation_cannot_be_used_twice() -> None:
    http = demo()
    pedido = conceder_consentimento(http, "bruno")

    response = http.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")

    assert response.status_code == 409


def test_active_consentimentos_show_scopes_and_expiry() -> None:
    http = demo()
    conceder_consentimento(http, "bruno", ("transacoes", "saldos"))

    consentimentos = http.get("/v1/consentimentos").json()

    assert len(consentimentos) == 1
    assert consentimentos[0]["banco"] == "Banco de demonstração do Bruno"
    assert consentimentos[0]["escopos"] == ["transacoes", "saldos"]
    assert consentimentos[0]["concedido_em"] == "2026-10-15"
    assert consentimentos[0]["expira_em"] == "2027-10-10"
    assert consentimentos[0]["situacao"] == "ativo"


def test_revoking_goes_through_confirmation_and_takes_effect_at_once() -> None:
    http = demo()
    conceder_consentimento(http, "bruno")
    consentimento = http.get("/v1/consentimentos").json()[0]

    pedido = http.delete(f"/v1/consentimentos/{consentimento['id']}")
    ainda = http.get("/v1/home").status_code
    http.post(f"/v1/confirmacoes/{pedido.json()['id']}/confirmar")

    assert pedido.status_code == 201
    assert pedido.json()["acao"] == "revogar_consentimento"
    assert ainda == 200
    assert http.get("/v1/home").status_code == 409
    assert http.get("/v1/consentimentos").json()[0]["situacao"] == "revogado"


def test_an_expired_consentimento_stops_the_reading() -> None:
    relogio = Relogio()
    http = demo(relogio=relogio)
    conceder_consentimento(http, "bruno")

    relogio.agora += timedelta(days=361)
    response = http.get("/v1/home")

    assert response.status_code == 409
    assert response.json()["detail"] == "Seu consentimento expirou em 10/10/2027. Conecte de novo."
    assert http.get("/v1/consentimentos").json()[0]["situacao"] == "expirado"


def test_a_consentimento_without_transactions_does_not_cover_the_budget() -> None:
    http = demo()
    conceder_consentimento(http, "bruno", ("saldos",))

    response = http.get("/v1/home")

    assert response.status_code == 409
    assert response.json()["detail"] == "Seu consentimento não cobre suas transações."


def test_a_real_account_can_connect_a_demo_bank() -> None:
    http = TestClient(create_app(config_de_teste()))
    senha = "uma senha longa o bastante"
    http.post("/v1/contas", json={"nome": "Rafa", "email": "rafa@exemplo.com", "senha": senha})

    conceder_consentimento(http, "carla", senha=senha)

    assert http.get("/v1/home").json()["nome"] == "Rafa"
    assert http.get("/v1/home").json()["resumo"]["entradas_centavos"] == 650_000


def test_another_account_cannot_confirm_my_request() -> None:
    app = create_app(config_de_teste())
    dono = TestClient(app)
    dono.post("/v1/sessoes/demo", json={"persona_id": "bruno"})
    pedido = pedir(dono)
    intruso = TestClient(app)
    intruso.post("/v1/sessoes/demo", json={"persona_id": "ana"})
    intruso.post("/v1/sessoes/reautenticar", json={"senha": "demo"})

    response = intruso.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")

    assert response.status_code == 404


def test_the_consentimento_lifecycle_is_audited() -> None:
    http = demo()
    conceder_consentimento(http, "bruno")
    http.get("/v1/home")
    consentimento = http.get("/v1/consentimentos").json()[0]
    pedido = http.delete(f"/v1/consentimentos/{consentimento['id']}").json()
    http.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")

    tipos = [e["tipo"] for e in http.get("/v1/auditoria").json()["eventos"]]

    assert tipos == [
        "sessao_demo",
        "ferramenta:solicitar_confirmacao",
        "reautenticacao",
        "consentimento_concedido",
        "consentimento_usado",
        "modelo:categorizar",
        "ferramenta:solicitar_confirmacao",
        "consentimento_revogado",
    ]
