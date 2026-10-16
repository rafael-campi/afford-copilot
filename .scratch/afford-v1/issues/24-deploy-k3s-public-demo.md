# 24: Deploy on k3s and public demo

**What to build:** The product runs publicly on k3s on a single VPS, deployed by CI with Helm, with market data ingested on a schedule.

**Blocked by:** 23 (Usage limits and kill switch)

**Status:** ready-for-agent

- [ ] Helm charts for API, web, Postgres, Langfuse and ingestion jobs
- [ ] GitHub Actions deploys to the VPS on merge to main
- [ ] BCB and Focus ingestion run as scheduled jobs
- [ ] Secrets are managed outside the repo
- [ ] The public URL serves the demo with Personas and limits active
- [ ] Single-node limitations are documented (ADR 0005)
