"""Banco Central Olinda `taxaJuros` service: average rates per institution."""

import json
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import quote

from mercado.snapshots import SnapshotTaxas, TaxaInstituicao

SERVICO = (
    "https://olinda.bcb.gov.br/olinda/servico/taxaJuros/versao/v2/odata/"
    "TaxasJurosDiariaPorInicioPeriodo"
)
MODALIDADE_VEICULOS = "Aquisição de veículos - Prefixado"
SEGMENTO_PF = "PESSOA FÍSICA"

Baixar = Callable[[str], bytes]


def url_taxas_veiculos() -> str:
    # Olinda rejects '+' for spaces, so every character is percent-encoded.
    filtro = f"Modalidade eq '{MODALIDADE_VEICULOS}' and Segmento eq '{SEGMENTO_PF}'"
    return f"{SERVICO}?$filter={quote(filtro)}&$format=json&$top=5000"


def buscar_taxas_veiculos(baixar: Baixar, agora: datetime) -> SnapshotTaxas:
    """Downloads the series and keeps only its most recent reference period."""
    linhas = json.loads(baixar(url_taxas_veiculos()))["value"]
    inicio = max(linha["InicioPeriodo"] for linha in linhas)
    periodo = sorted(
        (linha for linha in linhas if linha["InicioPeriodo"] == inicio),
        key=lambda linha: linha["Posicao"],
    )
    return SnapshotTaxas(
        id=f"bcb-veiculos-pf-{inicio}",
        inicio_periodo=date.fromisoformat(inicio),
        fim_periodo=date.fromisoformat(periodo[0]["FimPeriodo"]),
        capturado_em=agora,
        taxas=tuple(
            TaxaInstituicao(
                posicao=linha["Posicao"],
                instituicao=linha["InstituicaoFinanceira"],
                cnpj8=linha["cnpj8"],
                taxa_mensal_percentual=Decimal(str(linha["TaxaJurosAoMes"])),
                taxa_anual_percentual=Decimal(str(linha["TaxaJurosAoAno"])),
            )
            for linha in periodo
        ),
    )
