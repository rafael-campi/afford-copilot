# 04: Real BCB rates per institution

**What to build:** The Financiamento card uses real average rates published by the Banco Central for vehicle acquisition by individuals, shows the institutions ranked by rate, and says where the data came from and when.

**Blocked by:** 03 (Financing simulation from a structured Objetivo)

**Status:** ready-for-agent

- [ ] An ingestion job fetches the Olinda taxaJuros series (vehicle acquisition, individuals) and stores a dated, versioned snapshot
- [ ] Simulações record the snapshot id they used
- [ ] The card uses the median rate of reporting institutions and lists the ranking without endorsing any institution
- [ ] The card shows the average-rate Ressalva, source and reference date
- [ ] When the BCB API is unavailable, the latest good snapshot is used and its date shown; a stale-snapshot Ressalva appears past the expected refresh
- [ ] API tests run against a fixed, versioned snapshot fixture; ingestion is tested with recorded responses
