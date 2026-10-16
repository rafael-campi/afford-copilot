# 0011 — Every tool call is written to an audit log

**Status:** Accepted (2026-10-15). Recorded from the project briefing.

## Context

In a financial product, compliance needs to answer who saw what, when and under which authorization. Without a log, an answer cannot be traced back to the data and consent that produced it.

## Decision

Every tool call is recorded with the person, the tool, a summary of inputs and outputs (masked), the time and the Consentimento that authorized it. The lifecycle of personal data (Consentimento granted, used, revoked; Importação; deletion) is recorded too (see ADR 0003).

## Consequences

- Audit events never store raw personal data.
- The audit log is append-only from the application's point of view.
- Deleting an account keeps a record that the deletion happened, without the deleted data.
