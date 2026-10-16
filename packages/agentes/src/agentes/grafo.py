"""The copilot's explicit graph (ADR 0008).

entender_pedido -> perguntar (something is missing)
                -> simular -> explicar (the Recomendação, bounded by the facts)
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agentes.explicacao import SISTEMA_EXPLICAR, Explicacao, Fatos, so_numeros_dos_fatos
from agentes.llm import LLMClient, ModeloIndisponivel, RecusaDoModelo
from agentes.mascaramento import mascarar
from agentes.objetivo import (
    SISTEMA_ENTENDER_PEDIDO,
    ObjetivoExtraido,
    ObjetivoParcial,
    pergunta_para,
)


@dataclass(frozen=True)
class Simulado:
    simulacao: Any
    fatos: Fatos


@dataclass(frozen=True)
class NaoSimulado:
    """The tool could not simulate; `motivo` is said to the person as is."""

    motivo: str


ResultadoSimulacao = Simulado | NaoSimulado
SimularOpcoes = Callable[[ObjetivoParcial], ResultadoSimulacao]
"""Tool `simular_opcoes`: the backend runs the simulador with the person's own budget."""


class Estado(TypedDict, total=False):
    mensagem: str
    objetivo: ObjetivoParcial
    novo_objetivo: bool
    resultado: ResultadoSimulacao | None
    resposta: str


def construir_grafo(llm: LLMClient, simular_opcoes: SimularOpcoes, nomes: list[str]) -> Any:
    def entender_pedido(estado: Estado) -> Estado:
        objetivo = estado.get("objetivo", ObjetivoParcial())
        texto = mascarar(
            f"Objetivo atual: {objetivo.descrever()}\nNova mensagem: {estado['mensagem']}", nomes
        )
        extraido = llm.extrair("entender_pedido", SISTEMA_ENTENDER_PEDIDO, texto, ObjetivoExtraido)
        return {
            "objetivo": objetivo.com(extraido),
            "novo_objetivo": objetivo.muda_de_item(extraido),
        }

    def perguntar(estado: Estado) -> Estado:
        return {"resposta": pergunta_para(estado["objetivo"]) or "", "resultado": None}

    def simular(estado: Estado) -> Estado:
        resultado = simular_opcoes(estado["objetivo"])
        if isinstance(resultado, NaoSimulado):
            return {"resultado": resultado, "resposta": resultado.motivo}
        return {"resultado": resultado}

    def explicar(estado: Estado) -> Estado:
        resultado = estado["resultado"]
        assert isinstance(resultado, Simulado)
        fatos = resultado.fatos
        try:
            explicacao = llm.extrair(
                "explicar_recomendacao", SISTEMA_EXPLICAR, fatos.texto, Explicacao
            )
        except (ModeloIndisponivel, RecusaDoModelo):
            return {"resposta": fatos.padrao}
        texto = explicacao.texto.strip()
        return {"resposta": texto if texto and so_numeros_dos_fatos(texto, fatos) else fatos.padrao}

    def depois_de_entender(estado: Estado) -> str:
        return "perguntar" if estado["objetivo"].faltando else "simular"

    def depois_de_simular(estado: Estado) -> str:
        return "explicar" if isinstance(estado["resultado"], Simulado) else END

    grafo = StateGraph(Estado)
    # LangGraph's add_node overloads don't match a TypedDict state under mypy.
    grafo.add_node("entender_pedido", entender_pedido)  # type: ignore[call-overload]
    grafo.add_node("perguntar", perguntar)  # type: ignore[call-overload]
    grafo.add_node("simular", simular)  # type: ignore[call-overload]
    grafo.add_node("explicar", explicar)  # type: ignore[call-overload]
    grafo.add_edge(START, "entender_pedido")
    grafo.add_conditional_edges("entender_pedido", depois_de_entender, ["perguntar", "simular"])
    grafo.add_conditional_edges("simular", depois_de_simular, ["explicar", END])
    grafo.add_edge("perguntar", END)
    grafo.add_edge("explicar", END)
    return grafo.compile()
