from decimal import Decimal

from apoio import config_de_teste
from fastapi.testclient import TestClient

from agentes import LLMRoteirizado, ModeloIndisponivel, ObjetivoExtraido
from api.main import create_app


def conversa_com(
    llm: LLMRoteirizado, persona_id: str = "bruno", http: TestClient | None = None
) -> tuple[TestClient, str]:
    http = http or TestClient(create_app(config_de_teste(llm=llm)))
    http.post("/v1/sessoes/demo", json={"persona_id": persona_id})
    response = http.post("/v1/conversas")
    assert response.status_code == 201
    return http, response.json()["id"]


def enviar(http: TestClient, conversa_id: str, texto: str) -> dict[str, object]:
    response = http.post(f"/v1/conversas/{conversa_id}/mensagens", json={"texto": texto})
    assert response.status_code == 200
    resposta: dict[str, object] = response.json()
    return resposta


def extraido(**campos: object) -> ObjetivoExtraido:
    return ObjetivoExtraido(**campos)  # type: ignore[arg-type]


def test_a_complete_request_shows_the_objetivo_and_the_simulacao() -> None:
    llm = LLMRoteirizado(
        {"entender_pedido": [extraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60)]}
    )
    http, conversa = conversa_com(llm)

    resposta = enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    assert resposta["objetivo"] == {
        "item": "carro",
        "valor_centavos": 8_000_000,
        "prazo_meses": 60,
        "entrada_centavos": 0,
    }
    assert resposta["faltando"] == []
    simulacao = resposta["simulacao"]
    assert isinstance(simulacao, dict)
    assert simulacao["recomendacao"]["caminho"] == "juntar"


def test_asks_for_the_prazo_and_simulates_once_it_arrives() -> None:
    llm = LLMRoteirizado(
        {
            "entender_pedido": [
                extraido(item="carro", valor_reais=Decimal(80_000)),
                extraido(prazo_meses=36),
            ]
        }
    )
    http, conversa = conversa_com(llm)

    primeira = enviar(http, conversa, "Quero um carro de 80 mil")
    segunda = enviar(http, conversa, "em 3 anos")

    assert primeira["faltando"] == ["prazo"]
    assert primeira["resposta"] == "Até quando você quer ter o carro?"
    assert primeira["simulacao"] is None
    assert segunda["objetivo"] == {
        "item": "carro",
        "valor_centavos": 8_000_000,
        "prazo_meses": 36,
        "entrada_centavos": 0,
    }
    assert segunda["simulacao"] is not None


def test_asks_for_the_value_when_it_is_missing() -> None:
    llm = LLMRoteirizado({"entender_pedido": [extraido(item="moto", prazo_meses=24)]})
    http, conversa = conversa_com(llm)

    resposta = enviar(http, conversa, "Quero uma moto em 2 anos")

    assert resposta["faltando"] == ["valor"]
    assert resposta["resposta"] == "Quanto custa a moto que você quer?"


def test_a_correction_updates_the_objetivo_without_starting_over() -> None:
    llm = LLMRoteirizado(
        {
            "entender_pedido": [
                extraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60),
                extraido(valor_reais=Decimal(90_000)),
            ]
        }
    )
    http, conversa = conversa_com(llm)
    enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    resposta = enviar(http, conversa, "na verdade são 90 mil")

    objetivo = resposta["objetivo"]
    assert isinstance(objetivo, dict)
    assert objetivo["valor_centavos"] == 9_000_000
    assert objetivo["prazo_meses"] == 60
    simulacao = resposta["simulacao"]
    assert isinstance(simulacao, dict)
    assert simulacao["objetivo"]["valor_centavos"] == 9_000_000


def test_the_model_receives_the_current_objetivo_to_apply_corrections() -> None:
    llm = LLMRoteirizado(
        {
            "entender_pedido": [
                extraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60),
                extraido(valor_reais=Decimal(90_000)),
            ]
        }
    )
    http, conversa = conversa_com(llm)
    enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")
    enviar(http, conversa, "na verdade são 90 mil")

    segunda_chamada = llm.chamadas[1]
    assert "80000" in segunda_chamada.texto
    assert "na verdade são 90 mil" in segunda_chamada.texto


def test_personal_data_never_reaches_the_model() -> None:
    llm = LLMRoteirizado({"entender_pedido": [extraido(item="carro")]})
    http, conversa = conversa_com(llm)

    enviar(
        http,
        conversa,
        "Sou o Bruno, CPF 123.456.789-09, conta 12345-6 agência 0001, quero um carro",
    )

    texto = llm.chamadas[0].texto
    for dado in ["Bruno", "123.456.789-09", "12345-6", "0001"]:
        assert dado not in texto
    assert "quero um carro" in texto


def test_another_session_cannot_post_to_the_conversa() -> None:
    llm = LLMRoteirizado({"entender_pedido": []})
    app = create_app(config_de_teste(llm=llm))
    _, conversa = conversa_com(llm, "bruno", TestClient(app))
    outra = TestClient(app)
    outra.post("/v1/sessoes/demo", json={"persona_id": "ana"})

    response = outra.post(f"/v1/conversas/{conversa}/mensagens", json={"texto": "oi"})

    assert response.status_code == 404


class LLMForaDoAr:
    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type) -> object:
        raise ModeloIndisponivel("sem credenciais")


def test_an_unavailable_model_answers_503_with_a_clear_message() -> None:
    http = TestClient(create_app(config_de_teste(llm=LLMForaDoAr())))
    http.post("/v1/sessoes/demo", json={"persona_id": "bruno"})
    conversa = http.post("/v1/conversas").json()["id"]

    response = http.post(f"/v1/conversas/{conversa}/mensagens", json={"texto": "oi"})

    assert response.status_code == 503
    assert response.json()["detail"] == "O copiloto está indisponível agora. Tente mais tarde."
