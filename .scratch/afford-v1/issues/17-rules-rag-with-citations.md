# 17: Rules RAG with citations

**What to build:** The person asks rule questions in the Conversa ('como funciona o lance?') and gets answers grounded in official documents, each citing its source with a link, or a clear 'não sei' when the documents do not cover it.

**Blocked by:** 09 (Objetivo in natural language)

**Status:** ready-for-agent

- [ ] The corpus list is verified and documented: Lei 11.795/2008, Resolução BCB 285/2023, the CET rule, the credit IOF rule, BCB citizen pages
- [ ] Each document is stored with URL, capture date and content hash; changed documents are re-indexed and old versions kept
- [ ] buscar_regras searches pgvector with re-ranking and returns passages with source and document version
- [ ] Answers cite sources with links and admit when the answer is not in the documents
- [ ] A faithfulness eval runs on a starter set of questions
