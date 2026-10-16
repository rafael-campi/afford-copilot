# 0008 — The orchestrator is an explicit LangGraph graph

**Status:** Accepted (2026-10-15). Recorded from the project briefing.

## Context

A free-roaming agent that decides its own steps is flexible but unpredictable: the same request can take different paths, which makes testing, auditing and cost control hard. The copilot's flow is well known in advance: parse the Objetivo, ask for missing fields, load the budget, simulate, explain, answer rule questions.

## Decision

The orchestrator is an explicit graph built with LangGraph. Each step is a named node with typed state; the model chooses only among the edges the graph allows.

## Consequences

- Every conversation path can be traced node by node and tested.
- New behavior means adding a node or an edge, which is visible in review.
- Open-ended requests outside the graph's paths are handled by an explicit out-of-scope branch.
