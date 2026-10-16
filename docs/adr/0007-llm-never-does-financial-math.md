# 0007 — The LLM never does financial math

**Status:** Accepted (2026-10-15). Recorded from the project briefing.

## Context

The first concern of any bank evaluating an AI copilot is a hallucinated number: a wrong payment, rate or total cost presented with confidence. LLMs are unreliable at arithmetic and cannot be audited the way code can.

## Decision

Every financial number is produced by the `simulador` package: pure, deterministic, unit-tested code with no I/O and no LLM. The LLM extracts inputs and explains outputs; it never computes, rounds or restates a number that did not come from a Simulação.

## Consequences

- Numbers shown in the UI come from structured API fields, never from parsing model text.
- Explanations must be checked against the Simulação; an eval asserts that every number in an explanation exists in the Simulação.
- Adding a new calculation means adding code and tests, not changing a prompt.
