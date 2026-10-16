# 0003 — Strong confirmation guards personal-data actions, not purchases

**Status:** Accepted (2026-10-15)

## Context

The briefing required explicit, password-confirmed consent for any action that moves money. As an independent advisor ([0001](./0001-afford-is-an-independent-advisor.md)), Afford never contracts a product, so no action moves money. The real risks are actions on personal data.

## Decision

Choosing a Caminho only saves a Plano, with no password. The confirmation flow (`solicitar_confirmacao`: explicit consent, step-up authentication, audit log entry) guards granting or revoking a Consentimento, making an Importação, and deleting the customer's data. The copilot can start these flows but never completes them.

## Consequences

- The prototype's screen 4 becomes "review and save plan"; the password step moves to the consent and import flows.
- The audit log is centered on the lifecycle of personal data, which matches what LGPD asks for.
- If a later version hands proposals to institutions, sharing data with them joins the guarded actions.
