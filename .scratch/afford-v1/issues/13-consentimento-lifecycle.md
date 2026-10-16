# 13: Consentimento lifecycle

**What to build:** A person connects their (mocked) bank through a Consentimento screen showing scopes and expiry, confirms with re-authentication, sees active Consentimentos, and revokes them; the copilot only reads what an active Consentimento covers.

**Blocked by:** 12 (Accounts and step-up authentication)

**Status:** ready-for-agent

- [ ] The grant screen lists scopes (accounts, transactions, months) and expiry; granting goes through solicitar_confirmacao and step-up
- [ ] Active Consentimentos are listed with scopes and expiry; revocation takes effect immediately
- [ ] analisar_orcamento only reads data covered by an active Consentimento and says so when it cannot
- [ ] Choosing a Persona goes through the same Consentimento screen
- [ ] Grants, uses and revocations are audit events
- [ ] API tests cover grant, use, expiry and revocation
