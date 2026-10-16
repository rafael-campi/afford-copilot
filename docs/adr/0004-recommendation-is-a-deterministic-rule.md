# 0004 — The Recomendação is a deterministic rule, not an LLM judgment

**Status:** Accepted (2026-10-15)

## Context

The briefing already keeps all financial math out of the LLM. Choosing which Caminho to recommend could still be left to the model, which would let it weigh soft factors from the conversation. That would make the most consequential output of the product non-reproducible and hard to audit.

## Decision

The Recomendação is computed in the `simulador` package by a fixed, unit-tested rule:

1. Drop Caminhos that cannot deliver the item by the Prazo.
2. Drop Caminhos whose payment exceeds the Margem segura.
3. Pick the lowest total cost among the rest.
4. Attach Ressalvas (payment above the Sobra mensal, uncertain Contemplação, average rather than guaranteed rate).
5. If nothing qualifies, return no Recomendação plus suggested adjustments (Entrada, Prazo, item value).

The LLM only explains the result, and its explanation is built from the reasons each other Caminho was dropped.

## Consequences

- The same Simulação always yields the same Recomendação, so evals assert it exactly and audits can replay it.
- The copilot cannot account for preferences the rule does not encode (for example "I hate debt"); handling them means changing the rule, not the prompt.
- A payment above the Sobra mensal may still be recommended, but never without a Ressalva.
