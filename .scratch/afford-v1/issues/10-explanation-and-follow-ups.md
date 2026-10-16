# 10: Explanation and follow-ups

**What to build:** The copilot explains the Recomendação in plain language, and the person can ask 'e se eu der uma entrada de 10 mil?' or 'e em 48x?' to get new Simulações while earlier ones stay available for comparison.

**Blocked by:** 08 (Recomendação and Ressalvas), 09 (Objetivo in natural language)

**Status:** ready-for-agent

- [ ] Explanations are built from the rule's reasons and contain only numbers taken from the Simulação
- [ ] Follow-ups that change Entrada, Duração or value create a new Simulação in the same Conversa
- [ ] Earlier Simulações in the Conversa can be viewed and compared
- [ ] Changing the item starts a new Objetivo
- [ ] API tests with a scripted fake LLMClient cover follow-ups and the new-Objetivo branch
