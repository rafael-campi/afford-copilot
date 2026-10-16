# 16: Delete my account and data

**What to build:** A person deletes their account and all their data after confirming with re-authentication.

**Blocked by:** 13 (Consentimento lifecycle)

**Status:** ready-for-agent

- [ ] Deletion goes through solicitar_confirmacao with step-up
- [ ] Account, Consentimentos, Importações, transactions, Conversas, Simulações and Planos are removed
- [ ] An audit event records the deletion without keeping personal data
- [ ] An API test proves nothing of the account remains readable
