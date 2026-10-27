"""Categorization accuracy against the Personas' answer key, with the real model.

Runs every Persona's Extrato through the API (rules first, the model for the rest) and
compares each category with the answer key. Needs Anthropic credentials; each run makes one
model call per Persona.

    uv run python evals/categorizacao.py
"""

import sys
from collections import Counter

from fastapi.testclient import TestClient
from test_recomendacoes import entrar

from api.config import Config
from api.main import create_app
from seed.gerador import gerar_extrato
from seed.personas import PERSONAS


def avaliar(seed: int = 2026) -> int:
    total_acertos = total = 0
    print(f"{'Persona':<8} {'acertos':>8} {'total':>6} {'acurácia':>9}   pelo modelo")
    for persona in PERSONAS:
        http = TestClient(create_app(Config(seed=seed)))
        entrar(http, persona.id)
        transacoes = http.get("/v1/extrato").json()["transacoes"]
        gabarito = gerar_extrato(persona.id, seed).gabarito
        acertos = sum(t["categoria"] == g for t, g in zip(transacoes, gabarito, strict=True))
        do_modelo = [
            (t, g)
            for t, g in zip(transacoes, gabarito, strict=True)
            if t["categoria_fonte"] == "llm"
        ]
        acertos_modelo = sum(t["categoria"] == g for t, g in do_modelo)
        print(
            f"{persona.id:<8} {acertos:>8} {len(gabarito):>6} {acertos / len(gabarito):>9.1%}"
            f"   {acertos_modelo}/{len(do_modelo)}"
        )
        erros = Counter(
            (t["descricao"], t["categoria"], g)
            for t, g in zip(transacoes, gabarito, strict=True)
            if t["categoria"] != g
        )
        for (descricao, obtida, esperada), n in erros.most_common(5):
            print(f"    {descricao!r}: {obtida} (esperado {esperada}) x{n}")
        total_acertos += acertos
        total += len(gabarito)
    print(f"{'total':<8} {total_acertos:>8} {total:>6} {total_acertos / total:>9.1%}")
    return 0 if total_acertos == total else 1


if __name__ == "__main__":
    sys.exit(avaliar())
