"""Deterministic financial calculations for the three Caminhos. No I/O, no LLM."""

from simulador.modelo import (
    Financiamento,
    Objetivo,
    Orcamento,
    Ressalva,
    Simulacao,
    SnapshotMercado,
)
from simulador.simular import simular

__all__ = [
    "Financiamento",
    "Objetivo",
    "Orcamento",
    "Ressalva",
    "Simulacao",
    "SnapshotMercado",
    "simular",
]
