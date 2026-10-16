# 0013 — Only synthetic personal data in the repository

**Status:** Accepted (2026-10-15). Recorded from the project briefing.

## Context

The project is a public portfolio. Real bank statements cannot be committed, but realistic data is needed for development, demos and evals.

## Decision

All personal data in the repository comes from a seeded generator of Personas with realistic, uncategorized transaction descriptions and a separate answer key. In production, data would come from Open Finance Brasil or a person's own Importação.

## Consequences

- Demos and evals are reproducible from a seed.
- Categorization accuracy is measurable against the answer key.
- Real data only ever enters through a person's own Consentimento or Importação, which is ephemeral in the public demo.
