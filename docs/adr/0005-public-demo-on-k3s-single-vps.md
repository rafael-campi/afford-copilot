# 0005 — Public demo runs on k3s on a single VPS

**Status:** Accepted (2026-10-15)

## Context

The project should show Kubernetes deployment, but it is a self-funded portfolio. A managed cluster (GKE, EKS) costs more than US$ 70/month before any workload; a PaaS is cheap but would leave the Kubernetes manifests tested only locally.

## Decision

The public demo runs on k3s on one VPS, deployed with real Helm charts from CI. Total monthly spend is capped at about US$ 50, with a hard LLM budget enforced in the API: a daily message limit per user, rate limiting on the demo, and a kill switch that disables the copilot when the month's spend reaches the cap.

## Consequences

- Real Kubernetes manifests, rollouts and secrets are exercised in production at VPS cost.
- One node means no high availability; downtime during upgrades is accepted and documented.
- The budget kill switch is a product behavior that needs a clear message in the UI and its own test.
- Moving to a managed cluster later only changes infrastructure; the Helm charts carry over.
