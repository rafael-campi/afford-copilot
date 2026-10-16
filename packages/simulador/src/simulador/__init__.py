"""Deterministic financial calculations for the three Caminhos. No I/O, no LLM."""

from simulador.modelo import (
    Financiamento,
    Objetivo,
    Orcamento,
    Simulacao,
    SnapshotMercado,
)
from simulador.simular import simular

__all__ = [
    "Financiamento",
    "Objetivo",
    "Orcamento",
    "Simulacao",
    "SnapshotMercado",
    "simular",
]
