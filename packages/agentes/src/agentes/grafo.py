"""The copilot's explicit graph (ADR 0008): understand the Objetivo, then ask or simulate."""

from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agentes.llm import LLMClient
from agentes.mascaramento import mascarar
from agentes.objetivo import (
    SISTEMA_ENTENDER_PEDIDO,
    ObjetivoExtraido,
    ObjetivoParcial,
    pergunta_para,
)


class Estado(TypedDict, total=False):
    mensagem: str
    objetivo: ObjetivoParcial
    resposta: str
    simulacao: Any


SimularOpcoes = Callable[[ObjetivoParcial], Any]
"""Tool `simular_opcoes`: the backend runs the simulador with the person's own budget."""


def construir_grafo(llm: LLMClient, simular_opcoes: SimularOpcoes, nomes: list[str]) -> Any:
    def entender_pedido(estado: Estado) -> Estado:
        objetivo = estado.get("objetivo", ObjetivoParcial())
        texto = mascarar(
            f"Objetivo atual: {objetivo.descrever()}\nNova mensagem: {estado['mensagem']}", nomes
        )
        extraido = llm.extrair("entender_pedido", SISTEMA_ENTENDER_PEDIDO, texto, ObjetivoExtraido)
        return {"objetivo": objetivo.com(extraido)}

    def perguntar(estado: Estado) -> Estado:
        return {"resposta": pergunta_para(estado["objetivo"]) or "", "simulacao": None}

    def simular(estado: Estado) -> Estado:
        return {
            "simulacao": simular_opcoes(estado["objetivo"]),
            "resposta": "Olhei seus gastos e comparei os três caminhos.",
        }

    def proximo(estado: Estado) -> str:
        return "perguntar" if estado["objetivo"].faltando else "simular"

    grafo = StateGraph(Estado)
    # LangGraph's add_node overloads don't match a TypedDict state under mypy.
    grafo.add_node("entender_pedido", entender_pedido)  # type: ignore[call-overload]
    grafo.add_node("perguntar", perguntar)  # type: ignore[call-overload]
    grafo.add_node("simular", simular)  # type: ignore[call-overload]
    grafo.add_edge(START, "entender_pedido")
    grafo.add_conditional_edges("entender_pedido", proximo, ["perguntar", "simular"])
    grafo.add_edge("perguntar", END)
    grafo.add_edge("simular", END)
    return grafo.compile()
