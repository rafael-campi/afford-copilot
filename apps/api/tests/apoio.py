from datetime import date
from pathlib import Path

from argon2 import PasswordHasher

from agentes import ModeloIndisponivel
from agentes.categorizacao import Categorizacao, ItemCategorizado
from agentes.mascaramento import mascarar
from api.config import Config
from seed.gerador import gerar_extrato
from seed.personas import PERSONAS

MERCADO_DE_TESTE = Path(__file__).parent / "fixtures" / "mercado"
FOCUS_DE_TESTE = Path(__file__).parent / "fixtures" / "focus"


def config_de_teste(**mudancas: object) -> Config:
    """Config pinned to a known market snapshot (median 1.80% a.m.) and a fixed date."""
    base: dict[str, object] = {
        "diretorio_mercado": MERCADO_DE_TESTE,
        "diretorio_focus": FOCUS_DE_TESTE,
        "hoje": lambda: date(2026, 10, 15),
        "llm": LLMIndisponivel(),
        # Cheap argon2 parameters: tests check behavior, not hashing cost.
        "hasher": PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1),
    }
    return Config(**{**base, **mudancas})  # type: ignore[arg-type]


class LLMIndisponivel:
    """Every call fails as if the model were down."""

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type) -> object:
        raise ModeloIndisponivel("modelo de teste indisponível")


class CategorizadorPerfeito:
    """Answers `categorizar` from the Personas' answer key; records what it received."""

    def __init__(self, seed: int = 2026) -> None:
        self.textos: list[str] = []
        self.gabarito: dict[str, str] = {}
        for persona in PERSONAS:
            extrato = gerar_extrato(persona.id, seed)
            for transacao, categoria in zip(extrato.transacoes, extrato.gabarito, strict=True):
                self.gabarito[mascarar(transacao.descricao, [])] = categoria

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type) -> object:
        assert tarefa == "categorizar"
        self.textos.append(texto)
        itens = []
        for linha in texto.splitlines():
            indice, descricao = linha.split(": ", 1)
            categoria = self.gabarito.get(descricao.rsplit(" (", 1)[0], "Outros")
            itens.append(ItemCategorizado(indice=int(indice), categoria=categoria))  # type: ignore[arg-type]
        return Categorizacao(itens=itens)
