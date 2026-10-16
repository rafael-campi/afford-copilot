"""Deterministic financial calculations for the three Caminhos. No I/O, no LLM."""

from simulador.consorcio import aplicar_lance
from simulador.modelo import (
    Ajustes,
    Avaliacao,
    Consorcio,
    Financiamento,
    JanelaContemplacao,
    Juntar,
    Lance,
    Objetivo,
    Orcamento,
    Projecoes,
    Recomendacao,
    Ressalva,
    Simulacao,
    SnapshotMercado,
)
from simulador.simular import simular

__all__ = [
    "Ajustes",
    "Avaliacao",
    "Consorcio",
    "Financiamento",
    "JanelaContemplacao",
    "Juntar",
    "Lance",
    "Objetivo",
    "Orcamento",
    "Projecoes",
    "Recomendacao",
    "Ressalva",
    "Simulacao",
    "SnapshotMercado",
    "aplicar_lance",
    "simular",
]
