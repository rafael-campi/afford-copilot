"""Rule-based categorization: a merchant dictionary first, 'Outros' for the rest.

What no rule recognizes goes to the LLM (agentes.categorizacao), or stays in "Outros".
"""

from extrato.orcamento import TransacaoBruta

OUTROS = "Outros"
RENDA = "Renda"

# Matched against the upper-cased description, in order; the first hit wins.
DICIONARIO: tuple[tuple[str, str], ...] = (
    ("ALUGUEL", "Moradia"),
    ("IMOBILIARIA", "Moradia"),
    ("CONDOMINIO", "Moradia"),
    ("CARREFOUR", "Mercado"),
    ("ASSAI", "Mercado"),
    ("PAO DE ACUCAR", "Mercado"),
    ("IFOOD", "Delivery"),
    ("RAPPI", "Delivery"),
    ("UBER", "Transporte"),
    ("99APP", "Transporte"),
    ("POSTO", "Transporte"),
    ("ENEL", "Contas da casa"),
    ("SABESP", "Contas da casa"),
    ("VIVO", "Contas da casa"),
    ("CLARO", "Contas da casa"),
    ("DROGASIL", "Saúde"),
    ("INGRESSO.COM", "Lazer"),
    ("CINEMARK", "Lazer"),
    ("SYMPLA", "Lazer"),
    ("NETFLIX", "Assinaturas"),
    ("SPOTIFY", "Assinaturas"),
    ("AMAZON PRIME", "Assinaturas"),
    ("DAS SIMPLES", "Impostos e taxas"),
    ("EMPRESTIMO", "Dívidas"),
    ("ROTATIVO", "Dívidas"),
)


def pela_regra(transacao: TransacaoBruta) -> str | None:
    """The rule's category, or None when no rule recognizes the description."""
    if transacao.valor_centavos > 0:
        return RENDA
    descricao = transacao.descricao.upper()
    for trecho, categoria in DICIONARIO:
        if trecho in descricao:
            return categoria
    return None


def categorizar(transacao: TransacaoBruta) -> str:
    return pela_regra(transacao) or OUTROS
