"""Reads OFX statements: 1.x (SGML, tags without closing) and 2.x (XML)."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from extrato.orcamento import TransacaoBruta

BLOCO = re.compile(r"<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|(?=</BANKTRANLIST>))", re.S | re.I)


class ArquivoInvalido(ValueError):
    """The file has no readable transactions."""


def _campo(bloco: str, nome: str) -> str | None:
    achado = re.search(rf"<{nome}>([^<\r\n]*)", bloco, re.I)
    return achado.group(1).strip() if achado else None


def _decodificar(conteudo: bytes) -> str:
    try:
        return conteudo.decode("utf-8")
    except UnicodeDecodeError:
        return conteudo.decode("cp1252", errors="replace")


def ler_ofx(conteudo: bytes) -> list[TransacaoBruta]:
    texto = _decodificar(conteudo)
    transacoes = []
    for bloco in BLOCO.findall(texto):
        quando = _campo(bloco, "DTPOSTED")
        valor = _campo(bloco, "TRNAMT")
        descricao = _campo(bloco, "MEMO") or _campo(bloco, "NAME") or ""
        if not quando or not valor:
            continue
        try:
            data = date(int(quando[:4]), int(quando[4:6]), int(quando[6:8]))
            centavos = int(Decimal(valor.replace(",", ".")) * 100)
        except (ValueError, InvalidOperation):
            continue
        transacoes.append(TransacaoBruta(data=data, descricao=descricao, valor_centavos=centavos))
    if not transacoes:
        raise ArquivoInvalido
    return sorted(transacoes, key=lambda t: t.data)
