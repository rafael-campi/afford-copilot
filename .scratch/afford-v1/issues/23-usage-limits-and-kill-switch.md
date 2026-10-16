# 23: Usage limits and kill switch

**What to build:** The demo cannot exceed its budget: each user has a daily message limit, requests are rate limited, and the copilot is disabled with a clear message when the month's LLM spend reaches the cap.

**Blocked by:** 12 (Accounts and step-up authentication), 22 (Observability)

**Status:** ready-for-agent

- [ ] Per-user daily message limit and demo rate limiting, both configurable
- [ ] Monthly LLM spend is tracked; reaching the cap (about US$ 50 total budget) disables the copilot
- [ ] The web app shows a clear message when a limit or the kill switch is hit
- [ ] API tests cover each limit and the kill switch
