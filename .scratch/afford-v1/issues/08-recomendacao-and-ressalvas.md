# 08: Recomendação and Ressalvas

**What to build:** The comparison highlights one recommended Caminho chosen by the fixed rule, shows every Ressalva, explains why each other Caminho was dropped, and suggests adjustments when nothing fits.

**Blocked by:** 05 (Estimated CET), 06 (Consórcio Caminho), 07 (Juntar e comprar à vista Caminho)

**Status:** ready-for-agent

- [ ] The rule follows ADR 0004: delivers by the Prazo, payment ≤ Margem segura, lowest total cost
- [ ] A Recomendação whose payment exceeds the Sobra mensal carries a Ressalva
- [ ] Each non-recommended Caminho carries the reason it was dropped
- [ ] When nothing qualifies, there is no Recomendação and the simulador returns minimum Entrada, minimum Prazo and maximum item value adjustments
- [ ] Same inputs and snapshot always produce the same Recomendação
- [ ] Simulador tests cover every branch of the rule and the Margem segura > Sobra mensal edge case
