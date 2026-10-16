"""Calibrates the judge against a human: how often do they agree?

1. `uv run python evals/calibracao.py gerar` asks the copilot the rule questions and writes
   evals/calibracao/pendentes.jsonl (needs Anthropic credentials).
2. A person fills `"humano": true|false` in each line ("is this answer faithful and useful?")
   and saves the file as evals/calibracao/rotulos.jsonl. About 30 lines are enough.
3. `uv run python evals/calibracao.py concordancia` runs the judge on the labeled answers and
   prints the agreement. Below ~80%, adjust the rubric in juiz.py before trusting its scores.
"""

import json
import sys
from pathlib import Path

from cenarios import GUARDRAILS, REGRAS
from juiz import julgar_fidelidade
from rodar import _sessao

from agentes.anthropic_llm import AnthropicLLM

PASTA = Path(__file__).parent / "calibracao"


def gerar() -> None:
    PASTA.mkdir(exist_ok=True)
    http = _sessao(AnthropicLLM())
    perguntas = [c.pergunta for c in REGRAS] + [
        c.mensagem for c in GUARDRAILS if c.comportamento == "regra"
    ]
    perguntas += [p.replace("?", " e por quê?") for p in perguntas]
    with (PASTA / "pendentes.jsonl").open("w", encoding="utf-8") as saida:
        for pergunta in perguntas[:30]:
            r = http.post("/v1/regras/perguntas", json={"pergunta": pergunta}).json()
            trechos = "\n\n".join(
                f"{c['documento']}, {c['rotulo']}: {c['trecho']}" for c in r["citacoes"]
            )
            linha = {
                "pergunta": pergunta,
                "resposta": r["resposta"],
                "trechos": trechos,
                "humano": None,
            }
            saida.write(json.dumps(linha, ensure_ascii=False) + "\n")
    print(
        f"Escrito {PASTA / 'pendentes.jsonl'}: rotule o campo 'humano' e salve como rotulos.jsonl."
    )


def concordancia() -> int:
    juiz = AnthropicLLM()
    linhas = [json.loads(x) for x in (PASTA / "rotulos.jsonl").read_text("utf-8").splitlines() if x]
    rotuladas = [x for x in linhas if isinstance(x.get("humano"), bool)]
    iguais = 0
    for x in rotuladas:
        julgamento = julgar_fidelidade(juiz, x["pergunta"], x["resposta"], x["trechos"])
        iguais += julgamento.aprovado == x["humano"]
    taxa = iguais / len(rotuladas)
    print(f"concordância juiz vs. humano: {iguais}/{len(rotuladas)} = {taxa:.0%}")
    return 0 if taxa >= 0.8 else 1


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    if comando == "gerar":
        gerar()
    elif comando == "concordancia":
        sys.exit(concordancia())
    else:
        print(__doc__)
