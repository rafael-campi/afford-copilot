"""Audit log helpers (ADR 0011): who did what, when, with identifiers only."""

from dataclasses import dataclass
from typing import Any

from agentes import LLMClient
from agentes.llm import Esquema


@dataclass
class LLMAuditado:
    """Records every model call (its task only, never its text) before delegating."""

    interno: LLMClient
    registrar: Any
    """Callable[[str], None] that writes one audit event."""

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[Esquema]) -> Esquema:
        self.registrar(f"modelo:{tarefa}")
        return self.interno.extrair(tarefa, sistema, texto, esquema)
