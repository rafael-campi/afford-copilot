import os
from dataclasses import dataclass, field
from decimal import Decimal

from simulador import SnapshotMercado

# Stand-in until real BCB snapshots land (ticket 04).
MERCADO_PADRAO = SnapshotMercado(
    id="config-taxa-fixa-2026-10", financiamento_taxa_mensal=Decimal("0.018")
)


@dataclass(frozen=True)
class Config:
    margem_segura_percentual: int = 30
    seed: int = 2026
    mercado: SnapshotMercado = MERCADO_PADRAO
    session_secret: str = field(
        default_factory=lambda: os.environ.get("AFFORD_SESSION_SECRET", "dev-only-secret")
    )
