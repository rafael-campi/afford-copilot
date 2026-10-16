# 03: Financing simulation from a structured Objetivo

**What to build:** The person enters item, value, Prazo and Entrada in fields and sees a comparison screen with a Financiamento card: payment, total cost, interest paid, Duração and whether it fits the Margem segura.

**Blocked by:** 02 (Personas and budget on the Home)

**Status:** ready-for-agent

- [ ] The simulador is a pure function from Objetivo + budget summary + market snapshot to a Simulação (Seam B)
- [ ] Financing uses Tabela Price with a rate from configuration (stand-in snapshot)
- [ ] Default Duração is the smallest one whose payment fits the Margem segura, within the allowed range; the person can override it
- [ ] The card shows payment, total cost, interest paid, Duração and an 'acima da margem' flag
- [ ] Simulador unit tests include reference cases checked by hand against the BCB Calculadora do Cidadão
- [ ] An API test covers Objetivo in, Simulação out, persisted
