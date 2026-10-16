"""Masks personal data before any text reaches a model (ADR 0010)."""

import re

PADROES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"(?:\+?55\s?)?\(?\b\d{2}\)?\s?9?\d{4}-?\d{4}\b"), "[TELEFONE]"),
    (
        re.compile(r"\b(conta(?:\s+corrente)?|c/c)\s*(?:n[º°o]?\.?\s*)?\d[\d.-]*", re.I),
        r"\1 [CONTA]",
    ),
    (re.compile(r"\b(ag[eê]ncia|ag\.)\s*\d[\d-]*", re.I), r"\1 [AGENCIA]"),
)


def mascarar(texto: str, nomes: list[str]) -> str:
    for padrao, troca in PADROES:
        texto = padrao.sub(troca, texto)
    for nome in nomes:
        texto = re.sub(rf"\b{re.escape(nome)}\b", "[NOME]", texto, flags=re.I)
    return texto
