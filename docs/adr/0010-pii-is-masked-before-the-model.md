# 0010 — Personal data is masked before reaching the model

**Status:** Accepted (2026-10-15). Recorded from the project briefing.

## Context

LGPD requires data minimization, and model providers are third parties. Statements contain names, CPF numbers, account numbers and PIX keys that the model does not need to categorize spending or explain a simulation.

## Decision

A masking layer in the API replaces names, CPF, account numbers and PIX keys with stable placeholders before any LLM call, and restores them only where the response needs them.

## Consequences

- An API test captures every outgoing LLM request and asserts that no personal data is present.
- Categorization must work on masked descriptions; the merchant name stays, the person's name does not.
- Choosing a model provider does not change what personal data leaves the system.
