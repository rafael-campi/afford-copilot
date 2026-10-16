# 21: Model matrix

**What to build:** The developer runs the eval suite across three providers for each task and gets a comparison of quality, cost, p95 latency and tool-calling reliability, then switches models per task by configuration.

**Blocked by:** 20 (Eval suite and CI gating)

**Status:** ready-for-agent

- [ ] Adapters exist for Anthropic, OpenAI and one open-weights model behind the LLMClient port
- [ ] Per-task model selection (extraction, categorization fallback, RAG answer, explanation) is configuration only
- [ ] The matrix runs on demand, not on every PR, and produces a comparison table
- [ ] An ADR records the per-task choice with the evidence
