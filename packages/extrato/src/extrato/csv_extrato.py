"""Reads bank CSV exports once the person says which column is which."""

import csv
import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from extrato.orcamento import TransacaoBruta

FORMATOS_DE_DATA = ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y")
NOMES = {
    "data": ("data", "date", "dt", "data lancamento", "data do lancamento"),
    "descricao": (
        "historico",
        "descricao",
        "description",
        "lancamento",
        "memo",
        "title",
        "detalhe",
    ),
    "valor": ("valor", "amount", "quantia", "valor (r$)", "valor r$"),
}


class CsvInvalido(ValueError):
    """Message meant for the person."""


@dataclass(frozen=True)
class Tabela:
    colunas: list[str]
    linhas: list[list[str]]


def _texto(conteudo: bytes) -> str:
    for codificacao in ("utf-8-sig", "cp1252"):
        try:
            return conteudo.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise CsvInvalido("Não consegui ler esse arquivo.")


def ler_tabela(conteudo: bytes) -> Tabela:
    texto = _texto(conteudo)
    try:
        dialeto = csv.Sniffer().sniff(texto[:4096], delimiters=";,\t|")
    except csv.Error as erro:
        raise CsvInvalido("Não reconheci colunas nesse arquivo.") from erro
    linhas = [linha for linha in csv.reader(io.StringIO(texto), dialeto) if any(linha)]
    if len(linhas) < 2:
        raise CsvInvalido("Não reconheci colunas nesse arquivo.")
    return Tabela(colunas=[c.strip() for c in linhas[0]], linhas=linhas[1:])


def _normal(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.strip().lower()


def sugerir_mapa(colunas: list[str]) -> dict[str, str | None]:
    sugestao: dict[str, str | None] = {}
    for campo, nomes in NOMES.items():
        sugestao[campo] = next((c for c in colunas if _normal(c) in nomes), None)
    return sugestao


def ler_data(texto: str) -> date:
    texto = texto.strip()
    for formato in FORMATOS_DE_DATA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(texto)


def ler_valor(texto: str) -> int:
    """Brazilian ("-1.234,56", "R$ 12,30", "(12,30)") or international ("-1234.56")."""
    limpo = texto.strip().replace("R$", "").replace(" ", "")
    negativo = limpo.startswith("-") or (limpo.startswith("(") and limpo.endswith(")"))
    limpo = limpo.strip("-()+")
    if re.fullmatch(r"\d{1,3}(\.\d{3})*(,\d+)?|\d+(,\d+)?", limpo):
        limpo = limpo.replace(".", "").replace(",", ".")
    elif not re.fullmatch(r"\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?", limpo):
        raise ValueError(texto)
    try:
        centavos = int(Decimal(limpo.replace(",", "")) * 100)
    except InvalidOperation as erro:
        raise ValueError(texto) from erro
    return -centavos if negativo else centavos


def ler_csv(
    tabela: Tabela, coluna_data: str, coluna_descricao: str, coluna_valor: str
) -> list[TransacaoBruta]:
    indices = {}
    for nome in (coluna_data, coluna_descricao, coluna_valor):
        if nome not in tabela.colunas:
            raise CsvInvalido(f"A coluna {nome} não existe nesse arquivo.")
        indices[nome] = tabela.colunas.index(nome)
    transacoes = []
    for linha in tabela.linhas:
        if len(linha) < len(tabela.colunas):
            continue
        try:
            data = ler_data(linha[indices[coluna_data]])
        except ValueError as erro:
            raise CsvInvalido(
                f"Não consegui ler datas na coluna {coluna_data}. Confira o mapeamento."
            ) from erro
        try:
            valor = ler_valor(linha[indices[coluna_valor]])
        except ValueError as erro:
            raise CsvInvalido(
                f"Não consegui ler valores na coluna {coluna_valor}. Confira o mapeamento."
            ) from erro
        transacoes.append(
            TransacaoBruta(
                data=data, descricao=linha[indices[coluna_descricao]].strip(), valor_centavos=valor
            )
        )
    if not transacoes:
        raise CsvInvalido("Não encontrei transações nesse arquivo.")
    return sorted(transacoes, key=lambda t: t.data)
