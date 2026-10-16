# 0001 — Afford is an independent advisor, not a bank feature

**Status:** Accepted (2026-10-15)

## Context

Afford could be a feature inside one bank's app that offers that bank's own consórcio and financing, or an independent advisor that compares the three Caminhos without selling any of them. The framing decides what "confirm" means, where rates come from, and how the copilot gets access to the customer's statement.

## Decision

Afford is independent. It sells no financial product and is not paid by any institution. It reads the customer's statement only with their consent, and it recommends a Caminho on the customer's interest alone.

## Consequences

- Statement access comes from a consent the customer grants (Open Finance Brasil in production, a mocked consent flow in the portfolio). Tool scopes map to that consent.
- Rates and fees come from public market data, not from one institution's catalog.
- "Confirm" can no longer mean contracting a product; it must be redefined.
- Impartiality is a product promise: recommendations must be explainable from the customer's numbers, with no institution favored.
- The bank-feature framing that Brazilian banks ship internally is given up; the interview story leans on consent, LGPD and impartial advice instead.
