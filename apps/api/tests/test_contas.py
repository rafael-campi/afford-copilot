from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apoio import config_de_teste, entrar_como
from fastapi.testclient import TestClient

from agentes import Explicacao, LLMRoteirizado, ObjetivoExtraido
from api.main import create_app

SENHA = "uma senha longa o bastante"


class Relogio:
    def __init__(self) -> None:
        self.agora = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.agora


def cliente(**config: object) -> TestClient:
    return TestClient(create_app(config_de_teste(**config)))


def cadastrar(http: TestClient, email: str = "rafa@exemplo.com") -> None:
    response = http.post("/v1/contas", json={"nome": "Rafa", "email": email, "senha": SENHA})
    assert response.status_code == 201


def eventos(http: TestClient) -> list[str]:
    return [e["tipo"] for e in http.get("/v1/auditoria").json()["eventos"]]


def test_signing_up_logs_the_person_in() -> None:
    http = cliente()

    cadastrar(http)

    sessao = http.get("/v1/sessoes").json()
    assert sessao["conta"] == {"nome": "Rafa", "email": "rafa@exemplo.com", "demo": False}


def test_an_email_can_only_sign_up_once() -> None:
    http = cliente()
    cadastrar(http)

    response = http.post(
        "/v1/contas", json={"nome": "Outra", "email": "RAFA@exemplo.com", "senha": SENHA}
    )

    assert response.status_code == 409


def test_short_passwords_are_rejected() -> None:
    response = cliente().post(
        "/v1/contas", json={"nome": "Rafa", "email": "rafa@exemplo.com", "senha": "curta"}
    )

    assert response.status_code == 422


def test_logging_in_and_out() -> None:
    app = create_app(config_de_teste())
    cadastrar(TestClient(app))
    http = TestClient(app)

    errado = http.post("/v1/sessoes", json={"email": "rafa@exemplo.com", "senha": "errada!!"})
    certo = http.post("/v1/sessoes", json={"email": "rafa@exemplo.com", "senha": SENHA})
    logado = http.get("/v1/sessoes").status_code
    http.delete("/v1/sessoes")

    assert errado.status_code == 401
    assert certo.status_code == 204
    assert logado == 200
    assert http.get("/v1/sessoes").status_code == 401


def test_personas_are_ready_made_demo_accounts() -> None:
    http = cliente()

    entrar_como(http, "bruno")

    assert http.get("/v1/sessoes").json()["conta"] == {
        "nome": "Bruno",
        "email": "bruno@demo.afford",
        "demo": True,
    }
    assert http.get("/v1/home").status_code == 200


def test_an_account_without_an_extrato_is_asked_to_connect_a_bank() -> None:
    http = cliente()
    cadastrar(http)

    response = http.get("/v1/home")

    assert response.status_code == 409
    assert response.json()["detail"] == "Conecte seu banco ou importe seu extrato."


def test_reauthentication_lasts_five_minutes() -> None:
    relogio = Relogio()
    http = cliente(agora=relogio)
    cadastrar(http)

    antes = http.get("/v1/sessoes").json()["reautenticado"]
    errada = http.post("/v1/sessoes/reautenticar", json={"senha": "errada!!"})
    certa = http.post("/v1/sessoes/reautenticar", json={"senha": SENHA})
    depois = http.get("/v1/sessoes").json()["reautenticado"]
    relogio.agora += timedelta(minutes=6)
    expirado = http.get("/v1/sessoes").json()["reautenticado"]

    assert (antes, depois, expirado) == (False, True, False)
    assert errada.status_code == 401
    assert certa.status_code == 204


def test_demo_accounts_reauthenticate_with_the_shown_password() -> None:
    http = cliente()
    entrar_como(http, "ana")

    response = http.post("/v1/sessoes/reautenticar", json={"senha": "demo"})

    assert response.status_code == 204


def test_auth_events_are_audited() -> None:
    app = create_app(config_de_teste())
    cadastrar(TestClient(app))
    http = TestClient(app)
    http.post("/v1/sessoes", json={"email": "rafa@exemplo.com", "senha": "errada!!"})
    http.post("/v1/sessoes", json={"email": "rafa@exemplo.com", "senha": SENHA})
    http.post("/v1/sessoes/reautenticar", json={"senha": SENHA})

    assert eventos(http) == ["cadastro", "login_falhou", "login", "reautenticacao"]


def test_tool_and_model_calls_are_audited_without_their_content() -> None:
    llm = LLMRoteirizado(
        {
            "entender_pedido": [
                ObjetivoExtraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60)
            ],
            "explicar_recomendacao": [Explicacao(texto="Juntar cabe no seu orçamento.")],
        }
    )
    http = cliente(llm=llm)
    entrar_como(http, "bruno")
    conversa = http.post("/v1/conversas").json()["id"]
    http.post(f"/v1/conversas/{conversa}/mensagens", json={"texto": "Quero um carro de 80 mil"})

    registro = http.get("/v1/auditoria").json()["eventos"]

    assert [e["tipo"] for e in registro] == [
        "sessao_demo",
        "ferramenta:solicitar_confirmacao",
        "reautenticacao",
        "consentimento_concedido",
        "consentimento_usado",
        "modelo:entender_pedido",
        "ferramenta:simular_opcoes",
        "modelo:explicar_recomendacao",
    ]
    assert all("80 mil" not in str(e) for e in registro)


def test_an_account_sees_only_its_own_audit_log() -> None:
    app = create_app(config_de_teste())
    rafa = TestClient(app)
    cadastrar(rafa)
    outra = TestClient(app)
    cadastrar(outra, "outra@exemplo.com")

    assert eventos(rafa) == ["cadastro"]
    assert eventos(outra) == ["cadastro"]
