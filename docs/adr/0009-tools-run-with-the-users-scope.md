# 0009 — Tools run in the backend with the user's identity and Consentimento scope

**Status:** Accepted (2026-10-15). Recorded from the project briefing.

## Context

Giving the model direct access to the database, or tools that act with service-level privileges, would let a prompt injection or a model error read other people's data or data the person never authorized.

## Decision

The model reaches data only through a fixed set of tools that the backend executes on its behalf, with the logged-in person's identity and the scopes of their active Consentimento. The model never sees credentials or connection strings.

## Consequences

- A tool call can never return data outside the person's account or outside what their Consentimento covers; API tests prove it.
- When the Consentimento does not cover a request, the tool returns an explicit refusal the copilot can explain.
- Adding a tool requires defining its scope, which keeps the attack surface reviewable.
