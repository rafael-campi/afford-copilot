"""Ingestion of dated, versioned market data snapshots (BCB rates, Focus projections)."""

from mercado.ingestao import ResultadoIngestao, ingerir
from mercado.snapshots import RepositorioSnapshots, SnapshotTaxas, TaxaInstituicao

__all__ = [
    "RepositorioSnapshots",
    "ResultadoIngestao",
    "SnapshotTaxas",
    "TaxaInstituicao",
    "ingerir",
]
