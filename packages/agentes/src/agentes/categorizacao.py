"""Categorizes what the rules could not place, in one batch per Extrato."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from agentes.llm import LLMClient
from agentes.mascaramento import mascarar

Categoria = Literal[
    "Moradia",
    "Mercado",
    "Delivery",
    "Transporte",
    "Contas da casa",
    "Saúde",
    "Lazer",
    "Assinaturas",
    "Impostos e taxas",
    "Dívidas",
    "Outros",
]

SISTEMA_CATEGORIZAR = """\
Você classifica transações de um extrato bancário brasileiro em uma categoria de gasto.
Cada linha tem um índice, a descrição como o banco a exporta e o valor.

Use só as categorias permitidas. Transferências para pessoas e qualquer coisa que você não
consiga identificar com segurança vão para "Outros". Devolva um item para cada índice recebido.
"""


class ItemCategorizado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indice: int
    categoria: Categoria


class Categorizacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    itens: list[ItemCategorizado]


def categorizar_restantes(
    llm: LLMClient, transacoes: list[tuple[int, str, str]], nomes: list[str]
) -> dict[int, str]:
    """`transacoes` are (index, description, formatted amount); returns index -> category."""
    if not transacoes:
        return {}
    texto = "\n".join(
        f"{indice}: {mascarar(descricao, nomes)} ({valor})"
        for indice, descricao, valor in transacoes
    )
    resposta = llm.extrair("categorizar", SISTEMA_CATEGORIZAR, texto, Categorizacao)
    pedidos = {indice for indice, _, _ in transacoes}
    return {item.indice: item.categoria for item in resposta.itens if item.indice in pedidos}
