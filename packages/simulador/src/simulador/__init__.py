"""Deterministic financial calculations for the three Caminhos. No I/O, no LLM."""

from simulador.consorcio import aplicar_lance
from simulador.modelo import (
    Consorcio,
    Financiamento,
    JanelaContemplacao,
    Juntar,
    Lance,
    Objetivo,
    Orcamento,
    Projecoes,
    Ressalva,
    Simulacao,
    SnapshotMercado,
)
from simulador.simular import simular

__all__ = [
    "Consorcio",
    "Financiamento",
    "JanelaContemplacao",
    "Juntar",
    "Lance",
    "Objetivo",
    "Orcamento",
    "Projecoes",
    "Ressalva",
    "Simulacao",
    "SnapshotMercado",
    "aplicar_lance",
    "simular",
]
