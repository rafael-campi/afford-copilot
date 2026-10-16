"""Output and scope guardrails: what the copilot never says and what it does not cover."""

import re
import unicodedata

FORA_DO_ESCOPO = (
    "Eu ajudo a decidir como pagar por um veículo: consórcio, financiamento ou juntar e comprar "
    "à vista, com base no seu extrato. Não indico investimentos, empréstimos pessoais nem "
    "instituições. Quer simular a compra de um carro ou de uma moto?"
)
SO_VEICULOS = (
    "Por enquanto eu comparo caminhos só para veículos, como carro, moto ou caminhonete. "
    "Imóveis e outros bens ficam para uma próxima versão."
)

VEICULOS = {
    "carro",
    "automovel",
    "veiculo",
    "moto",
    "motocicleta",
    "caminhonete",
    "picape",
    "pickup",
    "van",
    "utilitario",
    "suv",
    "scooter",
    "caminhao",
    "seminovo",
    "carro usado",
    "moto usada",
}

# ADR 0006: no investment product or issuer; no promise of returns or credit approval.
PROIBIDOS = [
    r"\bcdbs?\b",
    r"\blci\b",
    r"\blca\b",
    r"\bcri\b",
    r"\bcra\b",
    r"\bdebentures?\b",
    r"\btesouro (direto|selic|ipca|prefixado)\b",
    r"\bfundos? de investimento\b",
    r"\bfundos? imobiliarios?\b",
    r"\bacoes da\b",
    r"\bbitcoin\b",
    r"\bcripto",
    r"\brendimento garantido\b",
    r"\bsem risco\b",
    r"\bgarantid[oa]s?\b",
    r"\b(esta|foi|sera|seu credito) aprovad[oa]\b",
    r"\bcredito aprovado\b",
    r"\baprovacao (garantida|certa)\b",
]
_PROIBIDOS = re.compile("|".join(PROIBIDOS))


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


def viola_politica(texto: str) -> bool:
    """True when model text names an investment product or promises returns or approval."""
    return _PROIBIDOS.search(_sem_acento(texto)) is not None


def e_veiculo(item: str) -> bool:
    return _sem_acento(item).strip() in VEICULOS
