from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Objetivo:
    item: str
    valor_centavos: int
    prazo_meses: int
    """Latest month, counted from today, by which the person wants the item."""
    entrada_centavos: int = 0


@dataclass(frozen=True)
class Orcamento:
    margem_segura_centavos: int
    sobra_mensal_centavos: int


@dataclass(frozen=True)
class SnapshotMercado:
    id: str
    financiamento_taxa_mensal: Decimal
    financiamento_duracoes_meses: tuple[int, ...] = tuple(range(12, 73, 6))


@dataclass(frozen=True)
class Financiamento:
    duracao_meses: int
    parcela_centavos: int
    custo_total_centavos: int
    juros_centavos: int
    acima_da_margem: bool


@dataclass(frozen=True)
class Simulacao:
    objetivo: Objetivo
    snapshot_id: str
    financiamento: Financiamento
