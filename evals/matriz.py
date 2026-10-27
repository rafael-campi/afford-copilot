"""Model matrix: the model evals once per candidate, compared by quality and per task.

    uv run python evals/matriz.py anthropic:claude-opus-5-5 openai:gpt-x \\
        openai-compat:qwen3-32b@http://localhost:11434/v1 --precos evals/precos.json

Candidates use the AFFORD_MODELOS syntax (provider:model); each one answers every task.
The judge is always the default Claude model, so the scores stay comparable. Runs on demand
only: every candidate costs a full model run (about 100 calls plus one per Persona).
Writes evals/relatorios/matriz-<timestamp>.md.
"""

import argparse
import json
import math
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from rodar import RELATORIOS, Resultado, explicacoes, extracoes, guardrails, notas, regras
from test_recomendacoes import entrar

from agentes import LLMClient
from agentes.anthropic_llm import AnthropicLLM
from agentes.llm import Esquema
from agentes.roteador import cliente_para
from api.config import Config
from api.main import create_app
from seed.gerador import gerar_extrato
from seed.personas import PERSONAS


@dataclass(frozen=True)
class Medicao:
    tarefa: str
    segundos: float
    entrada: int
    saida: int
    erro: str | None
    """Exception name when the call gave no valid answer (unreachable, refusal, bad schema)."""


@dataclass(frozen=True)
class Preco:
    """US$ per million tokens."""

    entrada: float
    saida: float


@dataclass
class LLMMedido:
    """Measures every call (task, latency, tokens, error) before passing the result on."""

    interno: LLMClient
    relogio: Callable[[], float] = time.perf_counter
    medicoes: list[Medicao] = field(default_factory=list)

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[Esquema]) -> Esquema:
        inicio = self.relogio()
        try:
            resposta = self.interno.extrair(tarefa, sistema, texto, esquema)
        except Exception as erro:
            self.medicoes.append(
                Medicao(tarefa, self.relogio() - inicio, 0, 0, type(erro).__name__)
            )
            raise
        entrada, saida = getattr(self.interno, "ultimo_uso", None) or (0, 0)
        self.medicoes.append(Medicao(tarefa, self.relogio() - inicio, entrada, saida, None))
        return resposta


@dataclass(frozen=True)
class Linha:
    chamadas: int
    p95_segundos: float
    confiabilidade: float
    """Percentage of calls that returned a valid answer."""
    custo_dolares: float | None


def resumir(medicoes: list[Medicao], preco: Preco | None) -> dict[str, Linha]:
    por_tarefa: dict[str, list[Medicao]] = {}
    for m in medicoes:
        por_tarefa.setdefault(m.tarefa, []).append(m)
    linhas = {}
    for tarefa, ms in sorted(por_tarefa.items()):
        tempos = sorted(m.segundos for m in ms)
        custo = (
            sum(m.entrada * preco.entrada + m.saida * preco.saida for m in ms) / 1_000_000
            if preco
            else None
        )
        linhas[tarefa] = Linha(
            chamadas=len(ms),
            p95_segundos=tempos[math.ceil(0.95 * len(tempos)) - 1],
            confiabilidade=round(100 * sum(m.erro is None for m in ms) / len(ms), 1),
            custo_dolares=custo,
        )
    return linhas


def tabela(
    execucoes: dict[str, tuple[list[Resultado], list[Medicao]]], precos: dict[str, Preco]
) -> str:
    tipos = sorted({r.tipo for resultados, _ in execucoes.values() for r in resultados})
    partes = [
        "## Qualidade (% de cenários aprovados)",
        "",
        "| Candidato | " + " | ".join(tipos) + " |",
        "|---" * (len(tipos) + 1) + "|",
    ]
    for candidato, (resultados, _) in execucoes.items():
        nota = notas(resultados)
        partes.append(f"| {candidato} | " + " | ".join(str(nota.get(t, "-")) for t in tipos) + " |")
    partes += [
        "",
        "## Por tarefa",
        "",
        "| Tarefa | Candidato | Chamadas | p95 (s) | Confiável (%) | Custo (US$) |",
        "|---|---|---|---|---|---|",
    ]
    linhas = [
        (tarefa, candidato, linha)
        for candidato, (_, medicoes) in execucoes.items()
        for tarefa, linha in resumir(medicoes, precos.get(candidato)).items()
    ]
    for tarefa, candidato, linha in sorted(linhas, key=lambda x: x[0]):
        custo = "-" if linha.custo_dolares is None else f"{linha.custo_dolares:.4f}"
        partes.append(
            f"| {tarefa} | {candidato} | {linha.chamadas} | {linha.p95_segundos:.2f} "
            f"| {linha.confiabilidade} | {custo} |"
        )
    return "\n".join(partes) + "\n"


def categorizacoes(llm: LLMClient, seed: int = 2026) -> list[Resultado]:
    """One result per transaction the model categorized, checked against the answer key."""
    resultados = []
    for persona in PERSONAS:
        http = TestClient(create_app(Config(llm=llm, seed=seed)))
        entrar(http, persona.id)
        transacoes = http.get("/v1/extrato").json()["transacoes"]
        gabarito = gerar_extrato(persona.id, seed).gabarito
        for i, (t, esperada) in enumerate(zip(transacoes, gabarito, strict=True)):
            if t["categoria_fonte"] == "llm":
                resultados.append(
                    Resultado(
                        f"{persona.id}-{i}",
                        "categorizacao",
                        t["categoria"] == esperada,
                        f"{t['descricao']!r}: {t['categoria']} (esperado {esperada})",
                    )
                )
    return resultados


def rodar_candidato(especificacao: str, juiz: LLMClient) -> tuple[list[Resultado], list[Medicao]]:
    llm = LLMMedido(cliente_para(especificacao))
    resultados = [
        *extracoes(llm),
        *guardrails(llm),
        *regras(llm, juiz),
        *explicacoes(llm, juiz),
        *categorizacoes(llm),
    ]
    return resultados, llm.medicoes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidatos", nargs="+", help="provider:model, as in AFFORD_MODELOS")
    parser.add_argument(
        "--precos",
        type=Path,
        help='JSON {"provider:model": {"entrada": 5.0, "saida": 25.0}}, US$ per million tokens',
    )
    args = parser.parse_args()

    precos = {
        candidato: Preco(**valores)
        for candidato, valores in (
            json.loads(args.precos.read_text("utf-8")) if args.precos else {}
        ).items()
    }
    juiz = AnthropicLLM()
    execucoes = {}
    for candidato in args.candidatos:
        print(f"rodando {candidato}...", flush=True)
        execucoes[candidato] = rodar_candidato(candidato, juiz)
    texto = tabela(execucoes, precos)

    RELATORIOS.mkdir(exist_ok=True)
    carimbo = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (RELATORIOS / f"matriz-{carimbo}.md").write_text(texto, "utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
