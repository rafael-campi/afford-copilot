# 19: Guardrails

**What to build:** The copilot ignores instructions hidden in imported data, politely refuses out-of-scope requests (including non-vehicle items and investment product recommendations), and never promises returns or approval.

**Blocked by:** 10 (Explanation and follow-ups), 14 (Importação OFX), 17 (Rules RAG with citations)

**Status:** ready-for-agent

- [ ] Imported descriptions are treated as data; injection attempts in them do not change behavior
- [ ] Out-of-scope requests (personal loans, investing, scams, non-vehicle items) get a refusal explaining what the copilot does
- [ ] No specific investment product or issuer is ever named (ADR 0006)
- [ ] No promise of returns or credit approval appears in outputs
- [ ] Guardrail eval cases cover each of the above
