from decimal import Decimal

import pytest
from apoio import config_de_teste, entrar_como
from fastapi.testclient import TestClient

from agentes import Explicacao, LLMRoteirizado, ObjetivoExtraido
from agentes.roteador import RoteadorLLM, montar_llm
from api.contexto import Contexto
from api.main import create_app


def test_each_task_goes_to_the_model_configured_for_it() -> None:
    extrator = LLMRoteirizado(
        {
            "entender_pedido": [
                ObjetivoExtraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60)
            ]
        }
    )
    explicador = LLMRoteirizado({"explicar_recomendacao": [Explicacao(texto="Juntar cabe.")]})
    llm = RoteadorLLM({"entender_pedido": extrator}, padrao=explicador)
    http = TestClient(create_app(config_de_teste(llm=llm)))
    entrar_como(http, "bruno")
    conversa = http.post("/v1/conversas").json()["id"]

    http.post(f"/v1/conversas/{conversa}/mensagens", json={"texto": "Quero um carro"})

    assert [c.tarefa for c in extrator.chamadas] == ["entender_pedido"]
    assert [c.tarefa for c in explicador.chamadas] == ["explicar_recomendacao"]


def test_the_routing_comes_from_a_configuration_string() -> None:
    llm = montar_llm(
        "entender_pedido=anthropic:claude-haiku-5-5,"
        "categorizar=openai:modelo-x,"
        "*=anthropic:claude-opus-5-5"
    )

    assert llm.descrever() == {
        "entender_pedido": "anthropic:claude-haiku-5-5",
        "categorizar": "openai:modelo-x",
        "*": "anthropic:claude-opus-5-5",
    }


def test_an_openai_compatible_server_is_configured_with_its_address() -> None:
    llm = montar_llm("*=openai-compat:qwen3-32b@http://localhost:11434/v1")

    assert llm.descrever() == {"*": "openai-compat:qwen3-32b@http://localhost:11434/v1"}


def test_the_api_reads_the_routing_from_afford_modelos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFFORD_MODELOS", "entender_pedido=openai:modelo-x")

    llm = Contexto(config_de_teste(llm=None)).llm()

    assert isinstance(llm, RoteadorLLM)
    assert llm.descrever() == {"entender_pedido": "openai:modelo-x"}
