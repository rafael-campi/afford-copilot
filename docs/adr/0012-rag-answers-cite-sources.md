# 0012 — RAG answers cite their sources and admit when they do not know

**Status:** Accepted (2026-10-15). Recorded from the project briefing.

## Context

Questions about consórcio rules, CET or IOF have legally defined answers. An invented or outdated rule stated with confidence would mislead the person and destroy trust in the product.

## Decision

Rule answers are generated only from passages retrieved from the official corpus, always cite the source document, version and link, and say plainly when the corpus does not cover the question.

## Consequences

- A faithfulness eval checks that every claim is supported by a cited passage.
- "I don't know" is a tested, expected outcome, not a failure.
- The corpus is versioned (see the spec); answers record which document version they used.
