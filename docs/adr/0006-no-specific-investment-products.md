# 0006 — The copilot never names a specific investment product

**Status:** Accepted (2026-10-15)

## Context

The Juntar e comprar à vista Caminho has to assume some yield. Recommending a specific investment to an individual is an activity regulated by the CVM (it requires a registered analyst or adviser), and Afford is an independent advisor on how to pay for a purchase, not on where to invest.

## Decision

Simulations use a generic Rendimento de referência (100% of the projected CDI from the BCB Focus survey, net of income tax) shown with a fixed Ressalva. The copilot never names an investment product or issuer, and treats "where should I invest?" as out of scope.

## Consequences

- A guardrail and its eval cases cover attempts to get product recommendations or return promises.
- The saving Caminho is less concrete than "put it in product X", which is the accepted price of staying outside CVM regulation.
