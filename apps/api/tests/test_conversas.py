from decimal import Decimal

from apoio import config_de_teste
from fastapi.testclient import TestClient

from agentes import Explicacao, LLMRoteirizado, ModeloIndisponivel, ObjetivoExtraido
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


def explicacao(texto: str = "O caminho recomendado cabe no seu orçamento.") -> Explicacao:
    return Explicacao(texto=texto)


def roteiro(*extracoes: ObjetivoExtraido, explicacoes: int = 5) -> LLMRoteirizado:
    """Scripted model: the given extractions in order, and generic explanations."""
    return LLMRoteirizado(
        {
            "entender_pedido": list(extracoes),
            "explicar_recomendacao": [explicacao() for _ in range(explicacoes)],
        }
    )


def test_a_complete_request_shows_the_objetivo_and_the_simulacao() -> None:
    llm = roteiro(extraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60))
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
    llm = roteiro(extraido(item="carro", valor_reais=Decimal(80_000)), extraido(prazo_meses=36))
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
    llm = roteiro(extraido(item="moto", prazo_meses=24))
    http, conversa = conversa_com(llm)

    resposta = enviar(http, conversa, "Quero uma moto em 2 anos")

    assert resposta["faltando"] == ["valor"]
    assert resposta["resposta"] == "Quanto custa a moto que você quer?"


def test_a_correction_updates_the_objetivo_without_starting_over() -> None:
    llm = roteiro(
        extraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60),
        extraido(valor_reais=Decimal(90_000)),
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
    llm = roteiro(
        extraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60),
        extraido(valor_reais=Decimal(90_000)),
    )
    http, conversa = conversa_com(llm)
    enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")
    enviar(http, conversa, "na verdade são 90 mil")

    segunda_chamada = [c for c in llm.chamadas if c.tarefa == "entender_pedido"][1]
    assert "80000" in segunda_chamada.texto
    assert "na verdade são 90 mil" in segunda_chamada.texto


def test_personal_data_never_reaches_the_model() -> None:
    llm = roteiro(extraido(item="carro"))
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
    llm = roteiro()
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


CARRO = extraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60)


def test_the_copilot_explains_the_recomendacao_in_its_own_words() -> None:
    llm = LLMRoteirizado(
        {
            "entender_pedido": [CARRO],
            "explicar_recomendacao": [
                explicacao("Juntar R$ 2.040,00 por mês sai mais barato que financiar.")
            ],
        }
    )
    http, conversa = conversa_com(llm)

    resposta = enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    assert resposta["resposta"] == "Juntar R$ 2.040,00 por mês sai mais barato que financiar."
    fatos = next(c.texto for c in llm.chamadas if c.tarefa == "explicar_recomendacao")
    assert "Recomendação: juntar" in fatos
    assert "R$ 2.040,00" in fatos


def test_an_explanation_with_an_invented_number_is_replaced_by_the_facts() -> None:
    llm = LLMRoteirizado(
        {
            "entender_pedido": [CARRO],
            "explicar_recomendacao": [explicacao("Você economiza R$ 12.345,00 juntando.")],
        }
    )
    http, conversa = conversa_com(llm)

    resposta = enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    texto = str(resposta["resposta"])
    assert "12.345" not in texto
    assert texto.startswith("Recomendo juntar e comprar à vista.")
    assert "Financiamento: Custa" in texto


def test_without_the_model_the_explanation_comes_from_the_facts() -> None:
    class SoExtrai:
        def __init__(self) -> None:
            self.extracoes = [CARRO]

        def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type) -> object:
            if tarefa == "explicar_recomendacao":
                raise ModeloIndisponivel("fora do ar")
            return self.extracoes.pop(0)

    http, conversa = conversa_com(SoExtrai())  # type: ignore[arg-type]

    resposta = enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    assert str(resposta["resposta"]).startswith("Recomendo juntar e comprar à vista.")


def test_a_follow_up_with_an_entrada_creates_a_new_simulacao_and_keeps_the_first() -> None:
    llm = roteiro(CARRO, extraido(entrada_reais=Decimal(10_000)))
    http, conversa = conversa_com(llm)
    primeira = enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    segunda = enviar(http, conversa, "E se eu der uma entrada de 10 mil?")

    simulacao = segunda["simulacao"]
    assert isinstance(simulacao, dict)
    assert simulacao["objetivo"]["entrada_centavos"] == 1_000_000
    historico = http.get(f"/v1/conversas/{conversa}").json()["simulacoes"]
    assert [s["id"] for s in historico] == [
        primeira["simulacao"]["id"],  # type: ignore[index]
        simulacao["id"],
    ]
    assert historico[1]["objetivo"]["entrada_centavos"] == 1_000_000


def test_a_follow_up_can_choose_the_financing_duracao() -> None:
    llm = roteiro(CARRO, extraido(duracao_meses=48))
    http, conversa = conversa_com(llm)
    enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    resposta = enviar(http, conversa, "e em 48x?")

    simulacao = resposta["simulacao"]
    assert isinstance(simulacao, dict)
    assert simulacao["financiamento"]["duracao_meses"] == 48


def test_a_duracao_the_market_does_not_offer_is_explained_not_simulated() -> None:
    llm = roteiro(CARRO, extraido(duracao_meses=50))
    http, conversa = conversa_com(llm)
    enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    resposta = enviar(http, conversa, "e em 50x?")

    assert resposta["simulacao"] is None
    assert "50 meses não existe" in str(resposta["resposta"])


def test_changing_the_item_starts_a_new_objetivo() -> None:
    llm = roteiro(CARRO, extraido(item="moto", valor_reais=Decimal(20_000)))
    http, conversa = conversa_com(llm)
    enviar(http, conversa, "Quero um carro de 80 mil em até 5 anos")

    resposta = enviar(http, conversa, "Pensando melhor, quero uma moto de 20 mil")

    assert resposta["novo_objetivo"] is True
    assert resposta["objetivo"] == {
        "item": "moto",
        "valor_centavos": 2_000_000,
        "prazo_meses": None,
        "entrada_centavos": 0,
    }
    assert resposta["faltando"] == ["prazo"]
