# Evals

Fifty scenarios that check the copilot end to end, through the API.

| Type | Scenarios | Checked by | Needs the model |
|---|---|---|---|
| `recomendacao` | 10 | exact match of the recommended Caminho | no |
| `extracao` | 15 | exact match of the parsed Objetivo (ranges where the text is fuzzy) | yes |
| `guardrail` | 10 | expected behavior: out of scope, vehicles only, rule question; forbidden words absent | yes |
| `regra` | 10 | the expected article is cited **and** the judge finds the answer faithful (score ≥ 4) | yes |
| `explicacao` | 5 | the judge finds the explanation faithful to the facts and clear (score ≥ 4) | yes |

Expected values were reasoned by hand from the rules (`cenarios.py` says why for each
recommendation), never copied from the code's output.

## Run

```sh
uv run python evals/rodar.py --deterministicos   # free: recommendations only
uv run python evals/rodar.py                      # full suite, needs Anthropic credentials
uv run python evals/rodar.py --modelo entender_pedido=anthropic:claude-sonnet-5-5   # per-task model
```

The full suite makes about 100 model calls (50 scenarios, some with a judge call). Every run
writes `evals/relatorios/<timestamp>.json` (ignored by git).

Other evals that need no model:

```sh
uv run python evals/rag_recuperacao.py   # retrieval recall/MRR on the real corpus
uv run python evals/categorizacao.py     # categorization accuracy (rules only without a key)
```

## Model matrix

`matriz.py` runs the model evals plus categorization once per candidate, each candidate
answering every task, and writes a comparison to `evals/relatorios/matriz-<timestamp>.md`:
quality per eval type, and per task the number of calls, p95 latency, reliability (calls that
returned a valid answer) and cost. It runs on demand only, never in CI.

```sh
uv run python evals/matriz.py \
    anthropic:claude-opus-5-5 \
    openai:<model> \
    openai-compat:qwen3-32b@http://localhost:11434/v1 \
    --precos precos.json
```

Candidates use the `AFFORD_MODELOS` syntax. It needs `ANTHROPIC_API_KEY` (the judge is always
the default Claude model) and `OPENAI_API_KEY` for `openai:` candidates. Prices are not kept in
the repository; copy them from each provider's pricing page into a file like
`{"<candidate>": {"entrada": <input price>, "saida": <output price>}}` (US$ per million tokens).
Without one, the cost column shows `-`.

Pick a model per task from the table and set it with `AFFORD_MODELOS`, e.g.
`entender_pedido=anthropic:claude-haiku-5-5,categorizar=openai-compat:qwen3-32b@http://...`.
Tasks: `entender_pedido`, `categorizar`, `reordenar_trechos`, `responder_regra`,
`explicar_recomendacao`. Tasks left out use `*`, or Claude Opus 5.5 without it.

## CI

- The 10 recommendation scenarios run in the `python` job on every PR (`test_recomendacoes.py`)
  and block the merge.
- `evals-modelo` runs the full suite only when the repository has an `ANTHROPIC_API_KEY`
  secret and `evals/baseline.json` exists. Deterministic types (`recomendacao`, `extracao`,
  `guardrail`) may not drop at all; judged types (`regra`, `explicacao`) may drop up to 5
  points before the job fails.

## Baseline

After the first full run you have reviewed, copy its scores into `evals/baseline.json`, e.g.
`{"recomendacao": 100.0, "extracao": 93.3, "guardrail": 100.0, "regra": 90.0, "explicacao": 80.0}`,
and commit it. Raise it when the suite improves.

## Judge calibration

The judge is only trusted after it agrees with a person. `calibracao.py gerar` writes 30
answers to label, a person marks each `"humano": true|false`, and `calibracao.py concordancia`
reports the agreement (target ≥ 80%). See the docstring in `calibracao.py`.
