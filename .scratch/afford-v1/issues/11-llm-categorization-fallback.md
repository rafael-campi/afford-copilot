# 11: LLM categorization fallback

**What to build:** Transactions the rules cannot categorize are categorized by the LLM, the Conversa shows spending by category, and categorization accuracy is measured against the Persona answer keys.

**Blocked by:** 02 (Personas and budget on the Home), 09 (Objetivo in natural language)

**Status:** ready-for-agent

- [ ] Uncategorized transactions go to the LLM in batches; each transaction records whether its category came from a rule or the LLM
- [ ] Spending by category appears in the Conversa, as in the prototype
- [ ] An eval reports accuracy against each Persona's answer key, measured by importing Persona data through the API
- [ ] Descriptions are masked before reaching the LLM
