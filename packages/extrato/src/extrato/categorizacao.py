"""Rule-based categorization: a merchant dictionary first, 'Outros' for the rest.

The LLM fallback for what the rules cannot place comes later (ticket 11).
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


def categorizar(transacao: TransacaoBruta) -> str:
    if transacao.valor_centavos > 0:
        return RENDA
    descricao = transacao.descricao.upper()
    for trecho, categoria in DICIONARIO:
        if trecho in descricao:
            return categoria
    return OUTROS
