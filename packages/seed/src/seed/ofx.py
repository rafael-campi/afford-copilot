"""Exports an Extrato as OFX 1.02 (SGML), the format Brazilian banks usually offer."""

from decimal import Decimal

from extrato.orcamento import TransacaoBruta

CABECALHO = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

"""


def exportar_ofx(transacoes: list[TransacaoBruta]) -> bytes:
    linhas = [
        "<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL",
        "<BANKACCTFROM><BANKID>999<ACCTID>DEMO<ACCTTYPE>CHECKING</BANKACCTFROM>",
        "<BANKTRANLIST>",
    ]
    for i, t in enumerate(transacoes):
        valor = Decimal(t.valor_centavos) / 100
        linhas += [
            "<STMTTRN>",
            f"<TRNTYPE>{'CREDIT' if t.valor_centavos > 0 else 'DEBIT'}",
            f"<DTPOSTED>{t.data:%Y%m%d}120000[-3:BRT]",
            f"<TRNAMT>{valor:.2f}",
            f"<FITID>{i:06d}",
            f"<MEMO>{t.descricao}",
            "</STMTTRN>",
        ]
    linhas += ["</BANKTRANLIST>", "</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"]
    return (CABECALHO + "\n".join(linhas) + "\n").encode("cp1252")
