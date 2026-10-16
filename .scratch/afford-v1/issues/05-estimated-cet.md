# 05: Estimated CET

**What to build:** The Financiamento card shows an estimated CET and how much of it comes from interest, IOF and fees.

**Blocked by:** 03 (Financing simulation from a structured Objetivo)

**Status:** ready-for-agent

- [ ] The simulador computes IOF per the current credit IOF rule (rule verified and cited at the start of the ticket)
- [ ] Registration and fee parameters have typical values in configuration
- [ ] The card shows the estimated CET and its breakdown, labeled as an estimate
- [ ] Insurance is excluded and a Ressalva says so
- [ ] Simulador tests cover the IOF calculation and the CET breakdown
