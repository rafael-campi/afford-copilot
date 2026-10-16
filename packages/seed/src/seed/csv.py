"""Exports an Extrato as CSV in two layouts Brazilian banks commonly use."""

import csv
import io
from decimal import Decimal
from typing import Literal

from extrato.orcamento import TransacaoBruta

Layout = Literal["banco_tradicional", "banco_digital"]


def _brasileiro(centavos: int) -> str:
    valor = f"{Decimal(abs(centavos)) / 100:,.2f}".replace(",", "X").replace(".", ",")
    return ("-" if centavos < 0 else "") + valor.replace("X", ".")


def exportar_csv(transacoes: list[TransacaoBruta], layout: Layout) -> bytes:
    saida = io.StringIO()
    if layout == "banco_tradicional":
        # Semicolons, dd/mm/yyyy, "1.234,56", Windows-1252: the classic internet-banking export.
        escritor = csv.writer(saida, delimiter=";")
        escritor.writerow(["Data", "Histórico", "Valor"])
        for t in transacoes:
            escritor.writerow([f"{t.data:%d/%m/%Y}", t.descricao, _brasileiro(t.valor_centavos)])
        return saida.getvalue().encode("cp1252")
    # Commas, ISO dates, decimal point, UTF-8: the digital-bank export.
    escritor = csv.writer(saida)
    escritor.writerow(["date", "description", "amount"])
    for t in transacoes:
        escritor.writerow(
            [t.data.isoformat(), t.descricao, f"{Decimal(t.valor_centavos) / 100:.2f}"]
        )
    return saida.getvalue().encode("utf-8")
