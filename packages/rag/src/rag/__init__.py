"""Ingestion, search and cited answers over the official rules corpus."""

from rag.documentos import Documento, RepositorioDocumentos
from rag.fontes import FONTES
from rag.ingestao import Fonte, ResultadoIngestao, ingerir_fontes

__all__ = [
    "FONTES",
    "Documento",
    "Fonte",
    "RepositorioDocumentos",
    "ResultadoIngestao",
    "ingerir_fontes",
]
