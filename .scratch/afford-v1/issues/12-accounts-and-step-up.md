# 12: Accounts and step-up authentication

**What to build:** A person can sign up, log in and log out; Personas become ready-made demo accounts; sensitive actions can require re-authentication; key events are written to the audit log.

**Blocked by:** 02 (Personas and budget on the Home)

**Status:** ready-for-agent

- [ ] Sign up and log in with email and password (or passkey), log out
- [ ] Personas are seeded demo accounts entered with one click
- [ ] A step-up re-authentication primitive is available to other flows
- [ ] Every tool call and auth event is written to the audit log with who, what and when
- [ ] Data is isolated per account; an API test proves one account cannot read another's data
