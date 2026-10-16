# 15: Importação CSV

**What to build:** A person uploads a CSV from any bank, maps its date, description and amount columns once, and continues through the same preview and confirmation as OFX.

**Blocked by:** 14 (Importação OFX)

**Status:** ready-for-agent

- [ ] A column mapping step handles arbitrary CSV layouts, including Brazilian number and date formats
- [ ] The flow reuses the OFX confirmation, preview, errors and expiry
- [ ] API tests use the Persona CSV exports in at least two column layouts
