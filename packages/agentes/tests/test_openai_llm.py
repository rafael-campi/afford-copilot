from types import SimpleNamespace
from typing import Any

import pytest

from agentes import ModeloIndisponivel, ObjetivoExtraido
from agentes.openai_llm import OpenAILLM


def respondendo(conteudo: str) -> Any:
    mensagem = SimpleNamespace(content=conteudo, refusal=None)
    resposta = SimpleNamespace(choices=[SimpleNamespace(message=mensagem)], usage=None)
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: resposta))
    )


def test_an_answer_outside_the_schema_is_a_model_failure() -> None:
    llm = OpenAILLM("qwen3-32b", base_url="http://localhost:11434/v1")
    llm._cliente = respondendo("Claro! Um carro de 80 mil em 5 anos.")

    with pytest.raises(ModeloIndisponivel):
        llm.extrair("entender_pedido", "sistema", "Quero um carro", ObjetivoExtraido)
