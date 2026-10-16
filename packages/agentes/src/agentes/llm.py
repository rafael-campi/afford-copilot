"""The LLMClient port: the only way the copilot talks to a language model."""

from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from pydantic import BaseModel

Esquema = TypeVar("Esquema", bound=BaseModel)


class RecusaDoModelo(Exception):
    """The model (and its fallback) declined to answer."""


class ModeloIndisponivel(Exception):
    """The model could not be reached: missing credentials, network or API failure."""


class LLMClient(Protocol):
    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[Esquema]) -> Esquema:
        """Structured extraction: returns an instance of `esquema` validated from the model."""
        ...


@dataclass(frozen=True)
class Chamada:
    tarefa: str
    sistema: str
    texto: str


@dataclass
class LLMRoteirizado:
    """Test double: returns scripted answers per task, in order, and records every call."""

    respostas: dict[str, list[BaseModel]]
    chamadas: list[Chamada] = field(default_factory=list)

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[Esquema]) -> Esquema:
        self.chamadas.append(Chamada(tarefa=tarefa, sistema=sistema, texto=texto))
        roteiro = self.respostas.get(tarefa, [])
        if not roteiro:
            raise AssertionError(f"No scripted answer left for task {tarefa!r}")
        resposta = roteiro.pop(0)
        if not isinstance(resposta, esquema):
            raise AssertionError(f"Scripted {type(resposta).__name__}, expected {esquema.__name__}")
        return resposta
