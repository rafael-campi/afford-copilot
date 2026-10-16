# 20: Eval suite and CI gating

**What to build:** About 50 scenarios run through the API with real models; deterministic checks block merges and judge-graded scores block only beyond a tolerance.

**Blocked by:** 11 (LLM categorization fallback), 18 (Review and save Plano), 19 (Guardrails)

**Status:** ready-for-agent

- [ ] Scenarios cover extraction and Recomendação (exact match), categorization accuracy, RAG and explanations (LLM-as-judge with rubric), and guardrails
- [ ] The judge is calibrated against ~30 answers labeled by hand by the developer
- [ ] CI blocks on deterministic failures and on judge scores dropping more than the tolerance (e.g. −5 points) from the baseline
- [ ] An eval report is produced per run
