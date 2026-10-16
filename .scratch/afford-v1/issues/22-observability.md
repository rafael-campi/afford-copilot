# 22: Observability

**What to build:** The operator sees, per conversation, the cost, latency and tools called, with eval scores attached.

**Blocked by:** 09 (Objetivo in natural language)

**Status:** ready-for-agent

- [ ] OpenTelemetry instrumentation across API, graph and tools
- [ ] Traces exported to a self-hosted Langfuse in Docker Compose
- [ ] Cost per conversation and per task is visible
- [ ] Eval runs attach scores to their traces
