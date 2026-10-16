# Afford

Independent AI copilot that helps a person decide how to pay for a vehicle: consórcio, financing, or saving until buying in cash. It reads the person's own statement with their consent, simulates the three Caminhos with deterministic code and public Banco Central data, and recommends one by a fixed rule.

Status: early development (ticket 01 of 25). See the [V1 spec](docs/spec/v1-copiloto.md).

## Run it

Requirements: Docker with Compose.

```sh
docker compose up --build
```

- Web: http://localhost:8080
- API: http://localhost:8000 (docs at `/docs`)
- Postgres with pgvector: `localhost:5432` (user, password and database: `afford`)

## Develop

Requirements: [uv](https://docs.astral.sh/uv/) and Node 24.

```sh
# Python (API and packages)
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run uvicorn api.main:app --reload

# Web (proxies /api to localhost:8000)
cd apps/web
npm install
npm run dev
npm test && npm run lint && npm run typecheck
```

## Layout

| Path | What it holds |
|---|---|
| `apps/api` | FastAPI: accounts, consent, masking, audit, conversations |
| `apps/web` | Mobile-first React app following the prototype |
| `packages/simulador` | Pure financial calculations and the Recomendação rule (no I/O, no LLM) |
| `packages/mercado` | Dated snapshots of BCB rates and Focus projections |
| `packages/extrato` | Statement import, categorization and budget summary |
| `packages/rag` | Official rules corpus, search and cited answers |
| `packages/agentes` | LangGraph orchestrator, tools and the LLM port |
| `packages/seed` | Seeded synthetic Personas |
| `infra` | Dockerfiles, database init, later Helm charts |
| `docs` | Briefing, spec, ADRs and prototype |

## Read more

- [CONTEXT.md](CONTEXT.md): domain glossary
- [docs/adr](docs/adr): architecture decisions
- [docs/spec/v1-copiloto.md](docs/spec/v1-copiloto.md): V1 spec
