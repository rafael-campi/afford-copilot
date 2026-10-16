from apoio import config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app
from seed.gerador import gerar_extrato
from seed.ofx import exportar_ofx

SENHA = "uma senha longa o bastante"


def nova_conta(app: object) -> TestClient:
    http = TestClient(app)  # type: ignore[arg-type]
    http.post("/v1/contas", json={"nome": "Rafa", "email": "rafa@exemplo.com", "senha": SENHA})
    return http


def com_dados(http: TestClient) -> str:
    """Imports an Extrato and simulates once; returns the Simulação id."""
    arquivo = exportar_ofx(gerar_extrato("bruno", 2026).transacoes)
    pedido = http.post("/v1/importacoes", files={"arquivo": ("e.ofx", arquivo)}).json()
    http.post("/v1/sessoes/reautenticar", json={"senha": SENHA})
    http.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")
    simulacao = http.post(
        "/v1/simulacoes", json={"item": "carro", "valor_centavos": 8_000_000, "prazo_meses": 60}
    )
    simulacao_id: str = simulacao.json()["id"]
    http.post("/v1/planos", json={"simulacao_id": simulacao_id, "caminho": "juntar"})
    return simulacao_id


def apagar(http: TestClient) -> None:
    pedido = http.post("/v1/conta/exclusao")
    assert pedido.status_code == 201
    http.post("/v1/sessoes/reautenticar", json={"senha": SENHA})
    assert http.post(f"/v1/confirmacoes/{pedido.json()['id']}/confirmar").status_code == 200


def test_deleting_the_account_asks_for_confirmation_first() -> None:
    app = create_app(config_de_teste())
    http = nova_conta(app)

    pedido = http.post("/v1/conta/exclusao").json()
    sem_senha = http.post(f"/v1/confirmacoes/{pedido['id']}/confirmar")

    assert pedido["acao"] == "apagar_conta"
    assert "consentimentos" in pedido["resumo"]["apaga"]
    assert sem_senha.status_code == 403
    assert http.get("/v1/sessoes").status_code == 200


def test_a_deleted_account_is_logged_out_and_cannot_log_in() -> None:
    app = create_app(config_de_teste())
    http = nova_conta(app)

    apagar(http)

    assert http.get("/v1/sessoes").status_code == 401
    login = TestClient(app).post("/v1/sessoes", json={"email": "rafa@exemplo.com", "senha": SENHA})
    assert login.status_code == 401


def test_nothing_of_the_account_remains_readable() -> None:
    app = create_app(config_de_teste())
    antiga = nova_conta(app)
    simulacao_id = com_dados(antiga)
    apagar(antiga)

    nova = nova_conta(app)

    assert nova.get("/v1/home").status_code == 409
    assert nova.get("/v1/importacoes").json() == []
    assert nova.get("/v1/consentimentos").json() == []
    assert nova.get(f"/v1/simulacoes/{simulacao_id}").status_code == 404
    assert nova.get("/v1/planos").json() == []
    assert [e["tipo"] for e in nova.get("/v1/auditoria").json()["eventos"]] == ["cadastro"]


def test_deleting_requires_being_logged_in() -> None:
    assert TestClient(create_app(config_de_teste())).post("/v1/conta/exclusao").status_code == 401
