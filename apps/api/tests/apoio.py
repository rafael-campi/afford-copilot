from datetime import UTC, date, datetime
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
        "agora": lambda: datetime(2026, 10, 15, 12, 0, tzinfo=UTC),
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


def conceder_consentimento(
    http: object, banco: str, escopos: tuple[str, ...] = ("transacoes",), senha: str = "demo"
) -> dict[str, object]:
    """Runs the whole flow: request, reauthenticate, confirm. Returns the confirmation."""
    from fastapi.testclient import TestClient

    assert isinstance(http, TestClient)
    pedido = http.post(
        "/v1/consentimentos",
        json={"banco": banco, "escopos": list(escopos), "meses_validade": 12},
    )
    assert pedido.status_code == 201, pedido.text
    assert http.post("/v1/sessoes/reautenticar", json={"senha": senha}).status_code == 204
    confirmacao: dict[str, object] = pedido.json()
    resposta = http.post(f"/v1/confirmacoes/{confirmacao['id']}/confirmar")
    assert resposta.status_code == 200, resposta.text
    return confirmacao


def entrar_como(http: object, persona_id: str) -> None:
    """Demo login plus the Consentimento to the Persona's bank, as the screen does it."""
    from fastapi.testclient import TestClient

    assert isinstance(http, TestClient)
    assert http.post("/v1/sessoes/demo", json={"persona_id": persona_id}).status_code == 204
    conceder_consentimento(http, persona_id)
