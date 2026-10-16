"""Answers rule questions only from the retrieved passages, always citing them (ADR 0012)."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from agentes import LLMClient
from rag.fragmentacao import Trecho

NAO_SEI = (
    "Não encontrei isso nos documentos oficiais que consulto. "
    "Vale perguntar à administradora ou ao Banco Central."
)

SISTEMA_RESPONDER = """\
Você responde perguntas sobre regras de consórcio, financiamento, CET e IOF usando apenas os
trechos de documentos oficiais recebidos, cada um com um identificador entre colchetes.

Responda em português simples, em até quatro frases, para alguém que não é especialista.
Cite em `citacoes` os identificadores dos trechos que sustentam a resposta. Se os trechos não
respondem à pergunta, devolva sabe=false. Não use conhecimento de fora dos trechos, não dê
conselho de investimento e não recomende instituições.
"""


class RespostaRegra(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sabe: bool
    resposta: str
    citacoes: list[str]


@dataclass(frozen=True)
class RespostaCitada:
    sabe: bool
    resposta: str
    citacoes: tuple[Trecho, ...]


def responder(pergunta: str, trechos: list[Trecho], llm: LLMClient) -> RespostaCitada:
    if not trechos:
        return RespostaCitada(sabe=False, resposta=NAO_SEI, citacoes=())
    contexto = "\n\n".join(f"[{t.id}] {t.titulo}, {t.rotulo}:\n{t.texto}" for t in trechos)
    gerada = llm.extrair(
        "responder_regra",
        SISTEMA_RESPONDER,
        f"Pergunta: {pergunta}\n\nTrechos:\n{contexto}",
        RespostaRegra,
    )
    por_id = {t.id: t for t in trechos}
    citados = tuple(por_id[i] for i in dict.fromkeys(gerada.citacoes) if i in por_id)
    if not gerada.sabe or not citados or len(citados) != len(set(gerada.citacoes)):
        return RespostaCitada(sabe=False, resposta=NAO_SEI, citacoes=())
    return RespostaCitada(sabe=True, resposta=gerada.resposta.strip(), citacoes=citados)
