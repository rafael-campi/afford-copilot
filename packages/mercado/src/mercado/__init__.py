"""Ingestion of dated, versioned market data snapshots (BCB rates, Focus projections)."""

from mercado.focus import ProjecoesFocus, RepositorioFocus, ingerir_focus
from mercado.ingestao import ResultadoIngestao, ingerir
from mercado.snapshots import RepositorioSnapshots, SnapshotTaxas, TaxaInstituicao

__all__ = [
    "ProjecoesFocus",
    "RepositorioFocus",
    "RepositorioSnapshots",
    "ResultadoIngestao",
    "SnapshotTaxas",
    "TaxaInstituicao",
    "ingerir",
    "ingerir_focus",
]
