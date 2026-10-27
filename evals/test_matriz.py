"""The model matrix's measuring and reporting, without any model."""

from decimal import Decimal

import pytest
from matriz import LLMMedido, Medicao, Preco, resumir, tabela
from rodar import Resultado

from agentes import ModeloIndisponivel, ObjetivoExtraido


class LLMFalso:
    def __init__(self, uso: tuple[int, int], erro: Exception | None = None) -> None:
        self.uso = uso
        self.erro = erro
        self.ultimo_uso: tuple[int, int] | None = None

    def extrair(self, tarefa, sistema, texto, esquema):  # type: ignore[no-untyped-def]
        if self.erro:
            raise self.erro
        self.ultimo_uso = self.uso
        return ObjetivoExtraido(item="carro", valor_reais=Decimal(80_000), prazo_meses=60)


def relogio(*momentos: float):  # type: ignore[no-untyped-def]
    restantes = list(momentos)
    return lambda: restantes.pop(0)


def test_each_call_is_measured_with_its_task_latency_and_tokens() -> None:
    llm = LLMMedido(LLMFalso(uso=(1200, 80)), relogio=relogio(10.0, 10.5))

    llm.extrair("entender_pedido", "sistema", "Quero um carro", ObjetivoExtraido)

    assert llm.medicoes == [Medicao("entender_pedido", 0.5, 1200, 80, None)]


def test_a_failed_call_is_measured_and_still_raised() -> None:
    llm = LLMMedido(LLMFalso((0, 0), ModeloIndisponivel("fora")), relogio=relogio(1.0, 3.0))

    with pytest.raises(ModeloIndisponivel):
        llm.extrair("categorizar", "sistema", "texto", ObjetivoExtraido)

    assert llm.medicoes == [Medicao("categorizar", 2.0, 0, 0, "ModeloIndisponivel")]


def test_the_summary_per_task_has_p95_reliability_and_cost() -> None:
    medicoes = [Medicao("entender_pedido", s / 10, 1_000_000, 100_000, None) for s in range(1, 20)]
    medicoes.append(Medicao("entender_pedido", 9.0, 0, 0, "ValidationError"))

    linha = resumir(medicoes, Preco(entrada=3.0, saida=15.0))["entender_pedido"]

    assert linha.chamadas == 20
    assert linha.p95_segundos == 1.9
    assert linha.confiabilidade == 95.0
    assert linha.custo_dolares == pytest.approx(19 * 3.0 + 19 * 1.5)


def test_without_a_price_the_cost_is_unknown() -> None:
    linha = resumir([Medicao("categorizar", 1.0, 500, 50, None)], None)["categorizar"]

    assert linha.custo_dolares is None


def test_the_table_compares_candidates_by_quality_and_by_task() -> None:
    texto = tabela(
        {
            "anthropic:claude-opus-5-5": (
                [Resultado("x1", "extracao", True, ""), Resultado("x2", "extracao", False, "")],
                [Medicao("entender_pedido", 1.0, 1000, 100, None)],
            ),
            "openai-compat:qwen3-32b@http://localhost:11434/v1": (
                [Resultado("x1", "extracao", True, ""), Resultado("x2", "extracao", True, "")],
                [Medicao("entender_pedido", 2.0, 1000, 100, "ValidationError")],
            ),
        },
        precos={"anthropic:claude-opus-5-5": Preco(entrada=5.0, saida=25.0)},
    )

    assert "| anthropic:claude-opus-5-5 | 50.0 |" in texto
    assert "| openai-compat:qwen3-32b@http://localhost:11434/v1 | 100.0 |" in texto
    assert "| entender_pedido | anthropic:claude-opus-5-5 | 1 | 1.00 | 100.0 | 0.0075 |" in texto
    qwen = "openai-compat:qwen3-32b@http://localhost:11434/v1"
    assert f"| entender_pedido | {qwen} | 1 | 2.00 | 0.0 | - |" in texto
