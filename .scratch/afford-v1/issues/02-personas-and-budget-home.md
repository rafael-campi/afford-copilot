# 02: Personas and budget on the Home

**What to build:** A demo visitor picks a Persona and lands on a Home showing that Persona's average income, spending, Sobra mensal and Margem segura over the last 3 months.

**Blocked by:** 01 (Repository foundation)

**Status:** ready-for-agent

- [ ] The seed generator produces 3–5 fixed, seeded Personas (e.g. comfortable, at-the-limit, variable income, indebted) with realistic, uncategorized transaction descriptions
- [ ] Each Persona has a separate category answer key that is never used by the product at runtime
- [ ] Running the generator twice with the same seed yields identical data
- [ ] A Persona picker lets the visitor enter a demo session with one click
- [ ] Transactions are categorized by rules and a merchant dictionary; uncategorized ones fall into 'Outros'
- [ ] Home shows average income, spending, Sobra mensal and Margem segura (30% of average net income, configurable)
- [ ] Home flags when Margem segura is larger than Sobra mensal
- [ ] API tests cover the budget summary for each Persona
