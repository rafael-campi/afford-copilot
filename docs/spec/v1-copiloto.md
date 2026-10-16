# Spec — Afford V1: big-purchase copilot (vehicles)

> Status: `ready-for-agent` (to be published as an issue once the tracker exists)
> Vocabulary: [CONTEXT.md](../../CONTEXT.md). Decisions: [docs/adr](../adr/). Prototype: `docs/Copiloto de Grandes Compras.html` (see "Prototype changes" below).

## Problem Statement

A person who wants to buy a vehicle has to choose between a consórcio, a financing and saving until buying in cash, and usually cannot tell which one is cheapest, which one actually fits their monthly budget, or when each one puts the vehicle in their hands. Fees are hidden behind jargon (Taxa de administração, Fundo de reserva, CET, Contemplação), bank and administrator sites push their own products, and nobody checks the payment against what the person really spends each month. People end up with a payment that squeezes their budget, a consórcio that delivers years after they needed the car, or a loan whose interest costs half the car.

## Solution

Afford is an independent copilot that sells nothing. The person connects their bank through a Consentimento, or imports their Extrato, and types an Objetivo in plain Portuguese ("Quero um carro de 80 mil em até 5 anos"). The copilot:

- parses the Objetivo (item, value, Prazo, Entrada) and asks only for what is missing;
- reads the Extrato, categorizes spending and computes the Sobra mensal and the Margem segura (30% of net income);
- simulates the three Caminhos with deterministic code and public market data: Consórcio (with its Janela de contemplação), Financiamento (with real per-institution average rates from the Banco Central and an estimated CET) and Juntar e comprar à vista (with the Focus survey's projected CDI and IPCA);
- picks a Recomendação by a fixed rule, shows every Ressalva, and explains why the other Caminhos lost;
- answers questions about the rules with cited passages from official documents, and says when the documents do not cover the question;
- lets the person save the chosen Caminho as a Plano. Nothing is ever contracted.

Personal data is masked before reaching any model, every tool call is audited, and actions on personal data (granting or revoking a Consentimento, importing, deleting data) require explicit, re-authenticated confirmation.

## User Stories

### Access and accounts

1. As a recruiter visiting the public demo, I want to enter as a ready-made Persona with one click, so that I can see the copilot working without creating an account or sharing my data.
2. As a visitor, I want to see a short description of each Persona (income profile, spending pattern), so that I can pick the scenario I want to explore.
3. As a person, I want to create an account with email and password (or passkey), so that my Consentimento, Plano and history belong to me.
4. As a person, I want to log in and log out, so that nobody else using my device sees my finances.
5. As a person, I want to be asked to re-authenticate before sensitive actions on my data, so that someone with my unlocked session cannot grant access or delete my data.
6. As a person, I want to delete my account and all my data, so that I can exercise my LGPD rights.

### Consentimento

7. As a person, I want to connect my bank through a Consentimento screen that lists exactly what Afford will read (accounts, transactions, how many months) and for how long, so that I authorize knowingly.
8. As a person, I want to confirm the Consentimento explicitly with re-authentication, so that access is never granted by accident.
9. As a person, I want to see my active Consentimentos with their scopes and expiry, so that I know what Afford can read.
10. As a person, I want to revoke a Consentimento at any time, so that Afford stops reading my data immediately.
11. As a person, I want the copilot to tell me when it cannot answer because my Consentimento does not cover the needed data or has expired, so that I understand why and how to fix it.
12. As a demo visitor using a Persona, I want choosing the Persona to go through the same Consentimento screen as a "connected bank", so that I see how consent works.

### Importação

13. As a person whose bank is not connected, I want to import my Extrato as an OFX file, so that I can use the copilot with my real spending.
14. As a person, I want to import my Extrato as a CSV file and map its columns (date, description, amount) once, so that files from any bank work.
15. As a person, I want to see the imported transactions and their period before they are used, so that I can catch a wrong file.
16. As a person, I want clear errors when a file is unreadable, empty, too large or covers too short a period, so that I know what to export instead.
17. As a person using the public demo, I want to be told that my imported file is processed and discarded and that its transactions are deleted after 24 hours, so that I feel safe trying it with real data.
18. As a person, I want the Importação to require explicit confirmation like a Consentimento, so that my data is never ingested without my decision.

### Budget

19. As a person, I want to see my average monthly income, spending and Sobra mensal over the last 3 months on the home screen, so that I know my starting point.
20. As a person, I want to see my spending grouped by category, so that I understand where my money goes.
21. As a person, I want my transactions categorized correctly even when descriptions are cryptic ("PAG*IFOOD 8821"), so that the budget reflects reality.
22. As a person, I want to see my Margem segura and how it was computed (30% of net income), so that I trust the payment ceiling.
23. As a person whose Margem segura is larger than my Sobra mensal, I want the copilot to point that out, so that I do not mistake the rule for room I do not have.
24. As a person with irregular income, I want the copilot to tell me when my income varies a lot across months, so that I treat the average with care.

### Objetivo

25. As a person, I want to type my Objetivo in plain Portuguese on the home screen, so that I do not have to fill a form.
26. As a person, I want to start from suggestion chips, so that I see what kind of question the copilot answers.
27. As a person, I want the copilot to show what it understood (item, value, Prazo, Entrada) as chips, so that I can spot a misunderstanding immediately.
28. As a person, I want the copilot to ask for the value or the Prazo when I did not give them, so that it never simulates on guessed numbers.
29. As a person, I want "em até 5 anos" understood as the date by which I want the vehicle, so that the comparison answers my real question.
30. As a person, I want to correct any parsed field by saying so ("na verdade são 90 mil"), so that I do not have to start over.
31. As a person asking about something other than a vehicle (a house, a trip), I want to be told that V1 covers vehicles only, so that I am not given a wrong simulation.

### Simulation and comparison

32. As a person, I want to see the three Caminhos side by side with monthly payment, total cost and when I get the vehicle, so that I can compare them at a glance.
33. As a person, I want each Caminho's Duração to default to the smallest one whose payment fits my Margem segura, so that the first answer is already realistic.
34. As a person, I want Caminhos above my Margem segura flagged, so that I see which ones do not fit.
35. As a person, I want to see the consórcio's Janela de contemplação (best case with a Lance, median, worst case) instead of "sorteio/lance", so that I understand the uncertainty.
36. As a person, I want to see my chance of Contemplação by my Prazo, so that I know how likely the consórcio is to deliver in time.
37. As a person, I want the consórcio cost to include the Taxa de administração, the Fundo de reserva and the yearly Carta de crédito adjustment, so that I am not surprised later.
38. As a person, I want the consórcio's fee parameters labeled as market ranges, not a specific administrator's offer, so that I know they are estimates.
39. As a person, I want the financing simulation to use real average rates published by the Banco Central per institution, so that the numbers come from the market.
40. As a person, I want to see a ranking of institutions by average rate inside the Financiamento card, so that I know where to look, without the copilot endorsing one.
41. As a person, I want a Ressalva saying the published rate is the institution's average and my rate depends on my credit profile, so that I do not treat it as an offer.
42. As a person, I want an estimated CET with its parts (interest, IOF, fees), so that I see what the loan really costs.
43. As a person, I want to see how much of the financing total is interest, so that the cost of borrowing is concrete.
44. As a person, I want the saving Caminho to account for the yield on my deposits and for the vehicle's price rising with inflation, so that its time and cost are honest.
45. As a person, I want the saving Caminho to show the assumptions used (Rendimento de referência, projected IPCA, their source and date) and state that it is not a promise of return, so that I am not misled.
46. As a person, I want every rate and projection to show its source and reference date, so that I can verify it.
47. As a person, I want a "parameters used" view for each Caminho, so that I can check how each number was produced.

### Recomendação

48. As a person, I want one Caminho recommended by a clear rule (delivers by my Prazo, fits my Margem segura, lowest total cost), so that the advice is consistent and explainable.
49. As a person, I want to read why each other Caminho was not recommended, so that I understand the trade-off.
50. As a person, I want a Recomendação whose payment exceeds my Sobra mensal to come with a visible Ressalva, so that I know the risk before choosing it.
51. As a person, I want to be told when no Caminho fits, with concrete adjustments (an Entrada of X, a later Prazo, a cheaper vehicle), so that I have a way forward.
52. As a person, I want the same question with the same data to always give the same Recomendação, so that I can trust it.

### Follow-ups

53. As a person, I want to ask "e se eu der uma entrada de 10 mil?" and get a new Simulação, so that I can explore scenarios.
54. As a person, I want to ask "e em 48x?" and see the Caminhos with that Duração, so that I can tune the plan.
55. As a person, I want earlier Simulações in the conversation kept so I can compare them, so that I do not lose a better scenario.
56. As a person, I want changing the item to start a new Objetivo, so that simulations are not mixed up.

### Rules (RAG)

57. As a person, I want to ask how a Lance works and get an answer based on the official rules, so that I learn without reading the law.
58. As a person, I want every rule answer to cite its source with a link to the passage, so that I can verify it.
59. As a person, I want the copilot to say it does not know when the documents do not cover my question, so that I am never given an invented rule.
60. As a person, I want plain-language explanations of consórcio, CET and IOF on the review screen, each linked to its official source, so that I understand what I am choosing.
61. As a person, I want rule answers to reflect the current version of each document, and to see which version was used, so that outdated rules are visible.

### Plano

62. As a person, I want to review the chosen Caminho with its parameters, Ressalvas and plain-language explanation before saving, so that I decide consciously.
63. As a person, I want to save it as a Plano without a password, since saving contracts nothing, so that saving is easy.
64. As a person, I want to see my saved Planos later, with the market data snapshot they were computed on, so that I can come back to my decision.
65. As a person, I want to be told clearly that Afford contracts nothing and that I must go to an institution to proceed, so that I know the next step.

### Safety and scope

66. As a person, I want the copilot to refuse to recommend specific investment products, so that I am not given regulated advice it is not entitled to give.
67. As a person, I want out-of-scope requests (personal loans, investing, scams) answered with a polite explanation of what the copilot does, so that I am not confused.
68. As a person, I want instructions hidden in my imported file's descriptions to be ignored, so that a malicious file cannot steer the copilot.
69. As a person, I want my name, CPF and account numbers never sent to the AI model, so that my identity is protected.
70. As a person, I want the copilot never to promise returns or guaranteed approval, so that I am not misled.
71. As a demo visitor, I want a clear message when the demo's daily or monthly usage limit is reached, so that I know it is a limit and not a bug.

### Operator and engineering (portfolio owner)

72. As the operator, I want every tool call recorded in an audit log with who, what, when, and which Consentimento authorized it, so that I can trace any answer.
73. As the operator, I want Consentimento grants, uses and revocations, Importações and deletions in the audit log, so that the lifecycle of personal data is traceable.
74. As the operator, I want traces with cost, latency and tools per conversation, so that I can watch quality and spend.
75. As the operator, I want a hard monthly LLM budget with a kill switch and per-user daily limits, so that the public demo cannot exceed about US$ 50/month.
76. As the operator, I want market data ingested on a schedule into dated, versioned snapshots, so that simulations are reproducible and the source date is known.
77. As the operator, I want the copilot to keep working on the last good snapshot and show its date when the BCB API is unavailable, so that an outage does not break the product.
78. As the developer, I want deterministic checks (simulador, extraction, Recomendação, guardrails) to block merges, so that regressions never ship.
79. As the developer, I want judge-graded quality scores (RAG faithfulness, citations, explanations) to block merges only when they fall beyond a tolerance, so that noise does not block PRs.
80. As the developer, I want to run the eval suite against several model providers per task and compare quality, cost, p95 latency and tool-calling reliability, so that model choice is evidence-based.
81. As the developer, I want to switch the model used for each task through configuration, so that the evidence can be acted on without code changes.
82. As the developer, I want the synthetic Persona generator to produce realistic, uncategorized transaction descriptions with a separate answer key, so that categorization accuracy can be measured.
83. As a recruiter reading the repo, I want a README with diagrams, ADRs, the model comparison table and a demo video, so that I can assess the engineering quickly.

## Implementation Decisions

### Modules

- **simulador** (pure, no I/O, no LLM): builds a Simulação from an Objetivo, a budget summary and a market data snapshot. Contains the three Caminho calculators, the Duração search, the Janela de contemplação model, the CET estimate and the Recomendação rule. This is the only place financial numbers are produced (briefing decision; ADR 0004).
- **mercado** (ingestion): fetches and stores dated, versioned snapshots of (a) BCB per-institution average rates for vehicle acquisition by individuals (Olinda `taxaJuros` service, weekly), (b) Focus survey projections for Selic/CDI and IPCA, (c) consórcio parameter ranges maintained as versioned configuration (no official per-administrator dataset was confirmed). Exposes "latest good snapshot" and "snapshot by id".
- **extrato**: normalizes transactions from a Consentimento (mocked Open Finance bank backed by Persona data) or an Importação (OFX parser; CSV parser with column mapping). Categorizes with rules and a merchant dictionary first, LLM only for the remainder. Produces the budget summary: average income, spending by category, Sobra mensal, Margem segura, income variability flag.
- **rag**: ingestion of the official corpus (Lei 11.795/2008, Resolução BCB 285/2023, the CET rule, the credit IOF rule, BCB citizen pages on consórcio, financing and CET), chunking, pgvector search with re-ranking, and cited answers. Each document is stored with URL, capture date and content hash; changed documents are re-indexed and old versions kept.
- **agentes**: the LangGraph graph and tools. The graph is explicit: parse Objetivo → (ask for missing fields) → load budget → simulate → explain; plus branches for rule questions, follow-ups and out-of-scope. Holds the `LLMClient` port with one adapter per provider, and per-task model configuration.
- **api** (FastAPI): accounts and step-up authentication, Consentimento lifecycle, Importação, conversations, Planos, PII masking before any model call, audit log, usage limits and budget kill switch, tracing.
- **web**: mobile-first React app following the prototype's visual language.
- **seed**: Persona generator (3–5 fixed, seeded Personas, such as comfortable, at-the-limit, variable income, indebted) producing realistic uncategorized descriptions plus an answer key, exportable as OFX/CSV.

### Domain rules

- **Margem segura** = 30% of average net monthly income (parameter). It does not depend on the Sobra mensal.
- **Prazo** is the latest date to have the item. **Duração** is the number of payments; default is the smallest Duração whose payment ≤ Margem segura, capped by the Caminho's allowed range; the person can override it.
- **Recomendação rule** (ADR 0004): drop Caminhos that cannot deliver by the Prazo (consórcio: group Duração ends after the Prazo; saving: projected purchase date after the Prazo); drop Caminhos with payment > Margem segura; pick lowest total cost; attach Ressalvas; if none qualifies, return no Recomendação plus suggested adjustments computed by the simulador (minimum Entrada, minimum Prazo, maximum item value that would make some Caminho qualify).
- **Ressalvas** (at least): payment above Sobra mensal; consórcio Contemplação uncertain with chance by Prazo; financing rate is an institution average; consórcio fees are market ranges; saving yield is a reference, not a promise; market snapshot older than its expected refresh.
- **Consórcio**: Taxa de administração and Fundo de reserva spread over the Duração; yearly Carta de crédito adjustment by a configurable index; Lance livre and Lance embutido for follow-up questions; Contemplação by draw with a configurable number of awards per assembly, giving best case / median / worst case and P(Contemplação ≤ Prazo). Out: seguro prestamista, Lance fixo, joining groups in progress, withdrawal refunds (explained by RAG only).
- **Financiamento**: Tabela Price only (vehicles). Rate from the snapshot per institution; the simulation uses a representative rate (median of reporting institutions) for the card, and lists the ranking. Estimated CET = interest + IOF per the current rule + registration/fee parameters with typical values; insurance excluded with a Ressalva.
- **Juntar e comprar à vista**: monthly deposit = Margem segura; yield = Rendimento de referência (100% projected CDI net of income tax, from Focus); vehicle price adjusted by projected IPCA; total cost = sum of deposits. Never names an investment product (ADR 0006).

### Tool contract (backend-called, user-scoped)

| Tool | Does |
|---|---|
| `entender_pedido` | Structured extraction of the Objetivo (item, value, Prazo, Entrada) and list of missing fields |
| `analisar_orcamento` | Budget summary from the Extrato covered by the active Consentimento or Importação |
| `simular_opcoes` | Calls the simulador with the Objetivo, budget summary and latest good snapshot; returns the Simulação with Recomendação, Ressalvas, parameters used and snapshot id |
| `buscar_regras` | RAG search with re-ranking; returns passages with source, document version and link |
| `solicitar_confirmacao` | Starts a confirmation flow for granting/revoking a Consentimento, an Importação or a data deletion; never completes it (ADR 0003) |

Tools run in the backend with the logged-in person's identity and the scopes of their Consentimento; the model never touches storage directly. Tool inputs and outputs pass through masking and are written to the audit log.

### Data and API shape

- Main entities: Account, Persona, Consentimento (scopes, granted_at, expires_at, revoked_at), Importação (format, period, status, expires_at for demo), Transaction (normalized, category, category_source rule|llm), Conversa (one Objetivo), Simulação (inputs, outputs, snapshot id), Plano (Simulação reference, chosen Caminho), MarketSnapshot, RagDocumentVersion, AuditEvent.
- Demo Importações and their transactions are deleted 24 h after creation; the uploaded file itself is never persisted.
- A conversation endpoint returns structured responses (text, parsed Objetivo chips, budget summary, Simulação, citations, pending confirmation) so that the web app renders cards instead of parsing prose.

### Cross-cutting

- PII masking (names, CPF, account numbers, keys in PIX descriptions) before any LLM call; unmasking only in the API response layer where needed.
- Input/output guardrails: prompt injection (including inside imported descriptions, treated as data), out-of-scope, no investment product recommendations, no promises of returns or approval, no data leakage across accounts.
- OpenTelemetry tracing exported to self-hosted Langfuse: cost, latency and tools per conversation; eval scores attached.
- Usage control: per-user daily message limit, demo rate limiting, monthly budget kill switch with a user-facing message.
- Deployment: Docker; k3s on a single VPS with Helm charts deployed from GitHub Actions (ADR 0005).

### Prototype changes

- Margem segura shown as 30% of income (R$ 2.040 for the prototype numbers), with the "above Sobra mensal" Ressalva when applicable.
- Consórcio card shows the Janela de contemplação and the chance by Prazo instead of "Sorteio/lance".
- Saving card shows yield and inflation assumptions; numbers recomputed.
- Financing card gains the institution ranking and the average-rate Ressalva.
- Screen 4 becomes "Revisar e salvar plano" (no password); the withdrawal sentence is corrected (a withdrawing member is refunded only upon draw or at group end).
- New screens: Persona selection, Consentimento (grant, list, revoke), Importação (upload, CSV column mapping, preview), saved Planos.
- Remove the property suggestion chip.

## Testing Decisions

- **Good tests exercise external behavior only**: requests in, responses and persisted effects out. They do not assert graph node names, prompts, chunk sizes or internal calls, so the orchestration, RAG and categorization internals can change freely.
- **Seam A: the HTTP API**, run in-process. Covers accounts and step-up auth, Consentimento lifecycle, Importação (OFX/CSV, errors, demo expiry), conversations end to end (Objetivo → Simulação → Recomendação → citations), Planos, masking (no PII in any captured LLM request), audit events, usage limits and kill switch, snapshot fallback. Boundaries replaced with fakes:
  - `LLMClient`: scripted fake in CI tests; real provider adapters in eval and model-matrix runs through the same API.
  - Market data: a fixed, versioned snapshot of BCB and Focus series.
  - Extratos: Persona OFX/CSV files with their category answer key; categorization accuracy is measured by importing them through the API.
- **Seam B: the simulador**, as a pure function. Hundreds of cheap exact cases: reference cases checked by hand against the BCB Calculadora do Cidadão, every branch of the Recomendação rule, Duração search, Janela de contemplação probabilities, CET components, and edge cases around Prazo, Margem segura and Sobra mensal (for example Margem segura > Sobra mensal).
- **Eval suite (~50 scenarios)** on Seam A with real models: extraction and Recomendação by exact match; categorization accuracy against the answer key; RAG and explanations by LLM-as-judge with a rubric (faithful to the passage, cites the source, admits not knowing), calibrated on ~30 answers labeled by hand by the developer; guardrail cases (injection in CSV descriptions, out-of-scope, investment product requests, return promises).
- **CI gating**: deterministic checks block merges; judge scores block only when they drop beyond a tolerance (e.g. −5 points) from the baseline.
- **Model matrix**: 3 providers (Anthropic, OpenAI, one open-weights model) × 4 tasks (extraction, categorization fallback, RAG answer, explanation), scored on eval score, cost per conversation, p95 latency and tool-calling reliability. Run on demand, not on every PR; results go to the README and to an ADR recording the per-task choice.
- **Prior art**: none yet, as the repository is empty. The simulador tests set the pattern for pure-function tests and the first API test sets the pattern for in-process API tests with fakes.

## Out of Scope

- Native mobile app (V1.1; framework decision deferred).
- PDF import (V1.1, with LLM extraction and a transaction review screen).
- Property and any non-vehicle item, including SAC, SFH, FGTS, TR and property insurance (V2).
- Recommending a specific institution or administrator; per-administrator consórcio fees.
- Contracting anything, sending proposals or sharing data with institutions.
- Real Open Finance integration (mocked consent flow only).
- Scam/phishing detection and a full spending dashboard.
- Credit scoring or personalized rates.
- Consórcio seguro prestamista, Lance fixo, joining groups in progress, withdrawal refund calculations.
- Investment product recommendations of any kind.
- High availability for the demo.

## Further Notes

- Build order (16 weeks, about 10–12 h/week): 1–2 foundation, Persona generator, ADRs; 3–5 simulador and BCB/Focus ingestion; 6–7 extrato (categorization, OFX/CSV import); 8–9 RAG and faithfulness evals; 10–11 orchestrator, guardrails, ~50 scenarios in CI, model matrix; 12–13 API: accounts, Consentimento, masking, audit, confirmation; 14–15 web; 16 deploy on k3s, Langfuse, README, video, postmortem. Résumé milestones: week 5 (simulador on real BCB data), week 11 (terminal copilot with evals and model matrix), week 16 (public demo).
- The exact RAG corpus links, the current IOF rule and the existence of any official per-administrator consórcio dataset are to be verified at the start of their phases.
- The architecture decisions in section 5 of the briefing (no LLM math, explicit graph, user-scoped tools, masking, audit log, cited RAG, synthetic data) are not yet recorded as ADRs.
