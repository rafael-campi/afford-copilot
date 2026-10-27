"""Which model answers which task, set by configuration only (AFFORD_MODELOS)."""

from dataclasses import dataclass, field

from agentes.anthropic_llm import MODELO_PADRAO, AnthropicLLM
from agentes.llm import Esquema, LLMClient
from agentes.openai_llm import OpenAILLM


@dataclass
class RoteadorLLM:
    rotas: dict[str, LLMClient]
    padrao: LLMClient
    nomes: dict[str, str] = field(default_factory=dict)

    def para(self, tarefa: str) -> LLMClient:
        return self.rotas.get(tarefa, self.padrao)

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[Esquema]) -> Esquema:
        return self.para(tarefa).extrair(tarefa, sistema, texto, esquema)

    def descrever(self) -> dict[str, str]:
        return self.nomes


def cliente_para(especificacao: str) -> LLMClient:
    """`anthropic:<model>`, `openai:<model>` or `openai-compat:<model>@<base url>`."""
    provedor, _, modelo = especificacao.partition(":")
    if provedor == "anthropic":
        return AnthropicLLM(modelo_padrao=modelo)
    if provedor == "openai":
        return OpenAILLM(modelo)
    if provedor == "openai-compat":
        nome, _, endereco = modelo.partition("@")
        return OpenAILLM(nome, base_url=endereco)
    raise ValueError(f"Provedor desconhecido: {provedor!r}")


def montar_llm(configuracao: str) -> RoteadorLLM:
    """`task=provider:model,...,*=provider:model`. Without `*`, every other task goes to Claude."""
    nomes: dict[str, str] = {}
    for par in filter(None, (p.strip() for p in configuracao.split(","))):
        tarefa, _, especificacao = par.partition("=")
        nomes[tarefa.strip()] = especificacao.strip()
    padrao = nomes.get("*", f"anthropic:{MODELO_PADRAO}")
    clientes = {tarefa: cliente_para(espec) for tarefa, espec in nomes.items() if tarefa != "*"}
    return RoteadorLLM(rotas=clientes, padrao=cliente_para(padrao), nomes=nomes)
