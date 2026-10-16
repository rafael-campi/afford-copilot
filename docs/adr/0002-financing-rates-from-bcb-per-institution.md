# 0002 — Financing rates come from real BCB data per institution

**Status:** Accepted (2026-10-15)

## Context

As an independent advisor ([0001](./0001-afford-is-an-independent-advisor.md)), Afford has no product catalog of its own. The options were one market-average offer per Caminho, fictional institutions calibrated on public data, or real per-institution data.

## Decision

Financing simulations use the average rates that the Banco Central publishes weekly for each institution and credit modality (Olinda `taxaJuros` service, aquisição de veículos PF). Every rate shown carries the institution name, the reference period and the source.

## Consequences

- Recommendations name real institutions, so the copilot must say that the published rate is the institution's average, not the rate the customer will get, which depends on their credit profile.
- An ingestion job keeps a dated, versioned snapshot of the data; simulations record which snapshot they used, so evals and audits are reproducible.
- No equivalent official per-administradora dataset for consórcio fees was confirmed; consórcio parameters may have to fall back to market ranges.
- Stale or missing data (the BCB API is down, an institution stops reporting) becomes a failure mode to handle and test.
