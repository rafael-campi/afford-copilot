"""The copilot's explicit graph (ADR 0008).

entender_pedido -> responder_regra (a question about the rules, answered with citations)
                -> fora_do_escopo (anything else) | so_veiculos (not a vehicle)
                -> perguntar (something is missing)
                -> simular -> explicar (the Recomendação, bounded by the facts)
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agentes.explicacao import SISTEMA_EXPLICAR, Explicacao, Fatos, so_numeros_dos_fatos
from agentes.guardrails import FORA_DO_ESCOPO, SO_VEICULOS, e_veiculo, viola_politica
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


ResponderRegra = Callable[[str], Any]
"""Tool `buscar_regras` + cited answer; returns an object with `resposta` and `citacoes`."""


class Estado(TypedDict, total=False):
    mensagem: str
    intencao: str
    regra: Any
    objetivo: ObjetivoParcial
    novo_objetivo: bool
    resultado: ResultadoSimulacao | None
    resposta: str


def construir_grafo(
    llm: LLMClient,
    simular_opcoes: SimularOpcoes,
    nomes: list[str],
    responder_regra: ResponderRegra | None = None,
) -> Any:
    def entender_pedido(estado: Estado) -> Estado:
        objetivo = estado.get("objetivo", ObjetivoParcial())
        texto = mascarar(
            f"Objetivo atual: {objetivo.descrever()}\nNova mensagem: {estado['mensagem']}", nomes
        )
        extraido = llm.extrair("entender_pedido", SISTEMA_ENTENDER_PEDIDO, texto, ObjetivoExtraido)
        if extraido.intencao == "regra" and responder_regra is not None:
            return {"objetivo": objetivo, "novo_objetivo": False, "intencao": "regra"}
        return {
            "objetivo": objetivo.com(extraido),
            "novo_objetivo": objetivo.muda_de_item(extraido),
            "intencao": extraido.intencao,
        }

    def regra(estado: Estado) -> Estado:
        assert responder_regra is not None
        resposta = responder_regra(estado["mensagem"])
        return {"regra": resposta, "resposta": resposta.resposta, "resultado": None}

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
        confiavel = texto and so_numeros_dos_fatos(texto, fatos) and not viola_politica(texto)
        return {"resposta": texto if confiavel else fatos.padrao}

    def fora_do_escopo(estado: Estado) -> Estado:
        return {"resposta": FORA_DO_ESCOPO, "resultado": None}

    def so_veiculos(estado: Estado) -> Estado:
        return {"resposta": SO_VEICULOS, "resultado": None}

    def depois_de_entender(estado: Estado) -> str:
        intencao = estado.get("intencao")
        if intencao == "regra":
            return "responder_regra"
        if intencao == "outro":
            return "fora_do_escopo"
        item = estado["objetivo"].item
        if item is not None and not e_veiculo(item):
            return "so_veiculos"
        return "perguntar" if estado["objetivo"].faltando else "simular"

    def depois_de_simular(estado: Estado) -> str:
        return "explicar" if isinstance(estado["resultado"], Simulado) else END

    grafo = StateGraph(Estado)
    # LangGraph's add_node overloads don't match a TypedDict state under mypy.
    grafo.add_node("entender_pedido", entender_pedido)  # type: ignore[call-overload]
    grafo.add_node("perguntar", perguntar)  # type: ignore[call-overload]
    grafo.add_node("simular", simular)  # type: ignore[call-overload]
    grafo.add_node("explicar", explicar)  # type: ignore[call-overload]
    grafo.add_node("responder_regra", regra)  # type: ignore[call-overload]
    grafo.add_node("fora_do_escopo", fora_do_escopo)  # type: ignore[call-overload]
    grafo.add_node("so_veiculos", so_veiculos)  # type: ignore[call-overload]
    grafo.add_edge(START, "entender_pedido")
    grafo.add_conditional_edges(
        "entender_pedido",
        depois_de_entender,
        ["responder_regra", "fora_do_escopo", "so_veiculos", "perguntar", "simular"],
    )
    grafo.add_edge("responder_regra", END)
    grafo.add_edge("fora_do_escopo", END)
    grafo.add_edge("so_veiculos", END)
    grafo.add_conditional_edges("simular", depois_de_simular, ["explicar", END])
    grafo.add_edge("perguntar", END)
    grafo.add_edge("explicar", END)
    return grafo.compile()
