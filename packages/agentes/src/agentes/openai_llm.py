"""LLMClient adapter for OpenAI and for OpenAI-compatible servers (open-weights models)."""

from typing import Any

import openai
from pydantic import ValidationError

from agentes.anthropic_llm import esquema_estrito
from agentes.llm import Esquema, ModeloIndisponivel, RecusaDoModelo


class OpenAILLM:
    """Chat Completions with a strict JSON schema. With `base_url`, the same code talks to an
    OpenAI-compatible server (vLLM, Ollama, hosted open-weights providers)."""

    def __init__(
        self, modelo: str, base_url: str | None = None, api_key: str | None = None
    ) -> None:
        self.modelo = modelo
        self.base_url = base_url
        self.api_key = api_key
        self._cliente: openai.OpenAI | None = None
        self.ultimo_uso: tuple[int, int] | None = None

    @property
    def cliente(self) -> openai.OpenAI:
        if self._cliente is None:
            try:
                # Local OpenAI-compatible servers usually accept any key.
                chave = self.api_key or (None if self.base_url is None else "sem-chave")
                self._cliente = openai.OpenAI(base_url=self.base_url, api_key=chave)
            except openai.OpenAIError as erro:
                raise ModeloIndisponivel(str(erro)) from erro
        return self._cliente

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[Esquema]) -> Esquema:
        formato: Any = {
            "type": "json_schema",
            "json_schema": {
                "name": esquema.__name__,
                "schema": esquema_estrito(esquema),
                "strict": True,
            },
        }
        try:
            resposta = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": texto},
                ],
                response_format=formato,
            )
        except (openai.APIConnectionError, openai.APIStatusError) as erro:
            raise ModeloIndisponivel(str(erro)) from erro
        escolha = resposta.choices[0]
        if getattr(escolha.message, "refusal", None):
            raise RecusaDoModelo(tarefa)
        if resposta.usage is not None:
            self.ultimo_uso = (resposta.usage.prompt_tokens, resposta.usage.completion_tokens)
        try:
            return esquema.model_validate_json(escolha.message.content or "")
        except ValidationError as erro:
            # Open-weights servers may ignore the strict schema.
            raise ModeloIndisponivel(f"Resposta fora do esquema {esquema.__name__}") from erro
