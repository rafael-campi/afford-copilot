# 09: Objetivo in natural language

**What to build:** The person types 'Quero um carro de 80 mil em até 5 anos' on the Home and, on the Conversa screen, sees the parsed Objetivo as chips, is asked for anything missing, can correct any field, and gets the comparison.

**Blocked by:** 03 (Financing simulation from a structured Objetivo)

**Status:** ready-for-agent

- [ ] An LLMClient port with one provider adapter; the model per task comes from configuration
- [ ] A minimal explicit LangGraph graph: parse Objetivo → ask for missing fields → load budget → simulate
- [ ] entender_pedido extracts item, value, Prazo (as a deadline) and Entrada, and lists missing fields
- [ ] Corrections ('na verdade são 90 mil') update the Objetivo without restarting
- [ ] Names, CPF and account numbers are masked before any LLM call; a test asserts no PII in captured LLM requests
- [ ] API tests use a scripted fake LLMClient
