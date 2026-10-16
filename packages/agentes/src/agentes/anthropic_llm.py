"""LLMClient adapter for the Claude API."""

from typing import Any

import anthropic
from anthropic.types.beta import BetaMessage, BetaMessageParam, BetaOutputConfigParam
from pydantic import BaseModel

from agentes.llm import Esquema, ModeloIndisponivel, RecusaDoModelo

MODELO_PADRAO = "claude-opus-5-5"


def esquema_estrito(modelo: type[BaseModel]) -> dict[str, Any]:
    """Pydantic schema as structured outputs expects it: every property required, no defaults.

    Optional fields stay nullable, so "not mentioned" is an explicit null.
    """
    esquema = modelo.model_json_schema()
    propriedades: dict[str, Any] = esquema["properties"]
    for definicao in propriedades.values():
        definicao.pop("default", None)
    esquema["required"] = list(propriedades)
    esquema["additionalProperties"] = False
    return esquema


class AnthropicLLM:
    def __init__(
        self,
        modelos: dict[str, str] | None = None,
        esforco: dict[str, str] | None = None,
        cliente: anthropic.Anthropic | None = None,
    ) -> None:
        self.modelos = modelos or {}
        self.esforco = esforco or {}
        self._cliente = cliente

    @property
    def cliente(self) -> anthropic.Anthropic:
        if self._cliente is None:
            try:
                self._cliente = anthropic.Anthropic()
            except anthropic.AnthropicError as erro:
                raise ModeloIndisponivel(str(erro)) from erro
        return self._cliente

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[Esquema]) -> Esquema:
        mensagens: list[BetaMessageParam] = [{"role": "user", "content": texto}]
        saida: BetaOutputConfigParam = {
            "effort": self.esforco.get(tarefa, "low"),  # type: ignore[typeddict-item]
            "format": {"type": "json_schema", "schema": esquema_estrito(esquema)},
        }
        try:
            resposta = self._criar(tarefa, sistema, mensagens, saida)
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as erro:
            raise ModeloIndisponivel(str(erro)) from erro
        except TypeError as erro:
            # The SDK reports missing credentials as a TypeError at request time.
            if "Could not resolve authentication method" not in str(erro):
                raise
            raise ModeloIndisponivel("Sem credenciais da Anthropic.") from erro
        if resposta.stop_reason == "refusal":
            raise RecusaDoModelo(tarefa)
        conteudo = next(b.text for b in resposta.content if b.type == "text")
        return esquema.model_validate_json(conteudo)

    def _criar(
        self,
        tarefa: str,
        sistema: str,
        mensagens: list[BetaMessageParam],
        saida: BetaOutputConfigParam,
    ) -> BetaMessage:
        return self.cliente.beta.messages.create(
            model=self.modelos.get(tarefa, MODELO_PADRAO),
            max_tokens=4096,
            system=sistema,
            messages=mensagens,
            output_config=saida,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
