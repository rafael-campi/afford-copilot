# Afford — Project Briefing

> AI copilot for big purchase decisions.

This briefing is the starting context for planning sessions (`/grill-with-docs`, `/to-spec`, `/wayfinder`). It records what has already been decided and what is still open. The clickable prototype in `docs/prototipo/copiloto.html` shows the expected V1 behavior and is the reference for screens, tool names and calculations.

## 1. Why this project exists

- **Author:** Rafael, web and mobile developer with professional experience in real estate, consórcio, insurance and banking.
- **Career goal:** Senior Software Engineer focused on AI, at Brazilian banks and fintechs (Nubank, C6 Bank, Mercado Livre and similar).
- **Purpose:** a portfolio project that proves, with real code and evidence, the skills these postings ask for. Market research on current postings found:
  - Python in production (async), LLM API integration (OpenAI, Anthropic, open-source models)
  - RAG, including advanced techniques: re-ranking, dynamic chunking, context-aware retrieval
  - Agents and multi-agent systems with tool calling / function calling, MCP
  - Evals, observability and cost control
  - AI governance: risk, compliance, security, privacy (LGPD)
  - Docker, Kubernetes, cloud deployment
- **Story for interviews:** a developer who knows the Brazilian financial sector in practice and now applies AI to make its products clearer and safer for customers.

## 2. The problem

People deciding how to pay for a big purchase (car, property, renovation) usually choose between consórcio, financing and saving without knowing the total cost of each option, the hidden fees, or whether the monthly payment really fits their budget.

## 3. V1 flagship: the big-purchase copilot

The user states a goal in natural language, for example *"Quero um carro de 80 mil em até 5 anos"*. The copilot:

1. **Understands the request**: extracts the item, value, term and down payment.
2. **Analyzes the budget**: an agent reads the user's (mock) bank statement, categorizes spending and computes how much is left each month and a safe payment ceiling.
3. **Simulates three paths**: consórcio (administration fee, reserve fund, contemplation by draw or bid), financing (interest, CET, fixed payment), and saving/investing until buying in cash.
4. **Compares and recommends**: total cost, monthly payment and time until the user has the item, side by side, with a recommendation that respects the budget.
5. **Explains the rules**: answers questions with RAG over public documents (Lei 11.795/2008, Banco Central material on consórcio and CET), always citing the source; says it does not know when the documents do not cover the question.
6. **Protects the user**: warns when the payment exceeds the safe share of income (default 30%) and never contracts anything without explicit confirmation.

**Out of scope for V1:** scam/phishing detection, full spending dashboard, real Open Finance integration. These are later versions.

## 4. Screens (see the prototype)

1. **Home**: monthly surplus, income vs. expenses, the "O que você quer conquistar?" input (text or voice), suggestion chips.
2. **Conversation**: parsed request as chips, spending by category, recommended payment ceiling, follow-up questions answered with sources.
3. **Comparison**: the three options as cards, recommended option highlighted, options above the budget flagged.
4. **Review and confirmation**: plan summary, plain-language explanation with source, consent checkbox, confirmation that requires the user's password.

Interfaces: mobile app (main) and web.

## 5. Architecture decisions already made

These should become ADRs.

| Decision | Reason |
|---|---|
| The LLM never does financial math. All calculations live in a deterministic, unit-tested `simulador` package. | Removes hallucinated numbers, which is the first concern of any bank. |
| The orchestrator is an explicit graph (LangGraph), not a free-roaming agent. | Predictable, testable and auditable flow. |
| The model reaches data only through controlled tools, called by the backend with the logged-in user's token and scopes. | The AI never touches the database directly; it sees only what the user authorized. |
| Personal data (CPF, account numbers, names) is masked before reaching the model. | LGPD and least privilege. |
| Any action that moves money requires explicit user confirmation in the UI. | The AI suggests; the user decides. |
| Every tool call is written to an audit log. | Traceability for compliance. |
| RAG answers must cite sources and admit when the answer is not in the documents. | Trust and verifiability. |
| Portfolio data is synthetic (a realistic statement generator). Production would use Open Finance Brasil. | No real personal data in a public repo. |

### Layers

```
App mobile / web
      │
API (FastAPI): auth, masking, audit log
      │
Orchestrator (LangGraph): understands the request, decides the steps
      │
 ┌────────────────┬──────────────────┬──────────────────┐
Budget agent      Simulator          Rules RAG
(categorizes      (deterministic     (answers with
 the statement)    code)              sources)
 │                 │                  │
Postgres (mock)   Rates table        pgvector + BCB docs
```

Cross-cutting: input/output guardrails (prompt injection, out-of-scope requests, no promises of returns, no data leaks), OpenTelemetry tracing (cost, latency and tools per conversation), evals in CI that block merges on quality regressions.

### Initial tool contract (from the prototype)

| Tool | Does |
|---|---|
| `entender_pedido` | Structured extraction: item, value, term, down payment |
| `analisar_orcamento` | Income, expenses by category, monthly surplus, safe payment ceiling |
| `simular_opcoes` | Consórcio, financing and saving, with the parameters used and the recommended option |
| `buscar_regras` | RAG search with re-ranking; returns passages and sources |
| `solicitar_confirmacao` | Starts the confirmation flow for a sensitive action; never executes it |

## 6. Suggested stack

Python 3.12, FastAPI, LangGraph, an LLM API (provider kept behind an interface), Postgres + pgvector, OpenTelemetry, Docker, Kubernetes, GitHub Actions. React for web and React Native for mobile (open to keeping the mobile framework already used at work).

## 7. Senior-level deliverables

- Public GitHub repo with a strong README, diagrams and ADRs
- Eval suite (~50 scenarios): correct math, real cited sources, sensible recommendations; runs in CI
- Metrics dashboard: quality, cost and latency per conversation
- Public demo (web and mobile) and a short demo video
- At least one postmortem of a real problem found while building
- A README section describing how the project was built with AI agents and how generated code was reviewed

## 8. Suggested repository layout

```
afford-copilot/
├── apps/
│   ├── api/            # FastAPI: auth, masking, audit
│   ├── web/            # React
│   └── mobile/         # React Native
├── packages/
│   ├── simulador/      # pure calculations + tests (no LLM)
│   ├── agentes/        # LangGraph graph and tools
│   └── rag/            # ingestion, chunking, search, re-ranking
├── data/
│   ├── seed/           # synthetic statement generator
│   └── docs/           # public BCB documents
├── evals/              # scenarios and reports
├── infra/              # Docker, Kubernetes, OpenTelemetry
└── docs/
    ├── adr/
    ├── postmortems/
    └── prototipo/      # copiloto.html
```

## 9. Build order (about 10–12 h/week)

| Weeks | Phase | Done when |
|---|---|---|
| 1–2 | Foundation | Repo, Docker Compose, CI, synthetic statement generator, first ADRs |
| 3–4 | Simulator | Consórcio, financing and saving computed with tests, checked against public simulators |
| 5–6 | Budget agent | Statement categorization, monthly surplus, first evals |
| 7–8 | RAG | BCB documents ingested, search with re-ranking, cited answers, faithfulness eval |
| 9–10 | Orchestrator | LangGraph graph wiring everything, guardrails, ~50 eval scenarios in CI |
| 11–12 | API and security | Auth, masking, audit log, confirmation of sensitive actions |
| 13–15 | Interfaces | Mobile and web apps following the prototype |
| 16 | Production and showcase | Public deploy, metrics dashboard, README with demo video, postmortem |

Résumé milestones: week 4 (tested simulator), week 10 (working copilot in the terminal with evals in CI), week 16 (full product with public demo).

## 10. Domain glossary (seed for GLOSSARY.md)

- **Consórcio**: a group of people paying monthly into a common fund; each month members are awarded a credit letter by draw or bid. No interest, but an administration fee.
- **Carta de crédito**: the credit amount a consórcio member receives when awarded.
- **Contemplação**: being awarded the credit letter, by **sorteio** (draw) or **lance** (bid).
- **Lance**: an offer to prepay installments in order to be awarded earlier.
- **Taxa de administração**: the consórcio administrator's fee, a percentage of the credit letter spread over the term.
- **Fundo de reserva**: an additional percentage that covers group shortfalls.
- **CET (Custo Efetivo Total)**: the total effective cost of a loan, combining interest, fees, taxes and insurance into one rate.
- **Tabela Price**: fixed-payment amortization schedule.
- **Margem segura**: the payment ceiling the copilot recommends for this user.

## 11. Open questions for the planning session

- Which LLM provider(s) for V1, and how to keep the provider swappable?
- Which consórcio rules to model now (annual credit-letter adjustment, insurance, bid types) and which to defer?
- Financing: model Tabela Price only, or SAC as well? How to estimate CET from the parameters?
- Source documents for the RAG corpus: exact list and how to keep them versioned.
- Eval design: who writes the expected answers, and how to grade explanations versus numbers?
- Mobile framework: React Native or the one already used at work?
- Hosting for the public demo, and a monthly cost ceiling.

## 12. How this project is being built

Development uses AI agents with the skills from [mattpocock/skills](https://github.com/mattpocock/skills):

1. `/setup-matt-pocock-skills` once per repo
2. `/grill-with-docs` with this briefing to produce ADRs and `GLOSSARY.md`
3. `/to-spec` for the V1 spec, then `/wayfinder` (large work) or `/to-tickets`
4. `/implement` with `tdd`, starting with the simulator
5. `code-review` and `pr` before merging; `/retro` after sessions
