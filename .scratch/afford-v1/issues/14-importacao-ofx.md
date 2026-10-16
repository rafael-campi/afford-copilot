# 14: Importação OFX

**What to build:** A person uploads an OFX file, confirms the Importação, previews the transactions and period, and the copilot uses them as the Extrato.

**Blocked by:** 13 (Consentimento lifecycle)

**Status:** ready-for-agent

- [ ] Upload goes through solicitar_confirmacao with step-up
- [ ] The preview shows transactions and period before use
- [ ] Clear errors for unreadable, empty, oversized or too-short files
- [ ] The uploaded file is never persisted; in the demo, imported transactions are deleted 24 h after creation and the person is told so
- [ ] Importações are audit events
- [ ] API tests use the Persona OFX exports
