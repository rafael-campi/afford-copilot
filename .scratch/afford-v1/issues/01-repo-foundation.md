# 01: Repository foundation

**What to build:** A developer can clone the repo, start the whole stack with one command and see the web Home shell talking to the API. CI runs on every push. The architecture decisions from the briefing are recorded as ADRs alongside 0001–0006.

**Blocked by:** None (can start immediately)

**Status:** done (pending commit)

- [x] Monorepo layout for api, web, simulador, agentes, rag, seed and infra exists, matching the spec's modules
- [x] Docker Compose starts Postgres with pgvector, the API and the web app
- [x] The API exposes a health endpoint, covered by an in-process API test (the pattern for Seam A)
- [x] The web app renders the Home layout from the prototype with placeholder values fetched from the API
- [x] CI runs lint, type checks and tests for Python and web on every push and blocks merge on failure (blocking needs branch protection once the GitHub repo exists)
- [x] ADRs recorded for: no LLM math, explicit LangGraph graph, user-scoped tools, PII masking, audit log, cited RAG, synthetic data
