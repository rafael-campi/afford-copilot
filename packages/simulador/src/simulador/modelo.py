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
    tarifas_centavos: int = 0
    """Registration and fee costs of a financing, paid up front (estimated values)."""
    consorcio_taxa_administracao: Decimal = Decimal("0.15")
    consorcio_fundo_reserva: Decimal = Decimal("0.02")
    consorcio_reajuste_anual: Decimal = Decimal("0.045")
    consorcio_duracoes_meses: tuple[int, ...] = (36, 48, 60, 72, 80)
    consorcio_sorteios_por_mes: int = 1
    consorcio_lances_por_mes: int = 1
    desatualizado: bool = False
    """True when the newest data available is older than its expected refresh."""


@dataclass(frozen=True)
class Ressalva:
    codigo: str
    texto: str


@dataclass(frozen=True)
class Financiamento:
    duracao_meses: int
    parcela_centavos: int
    custo_total_centavos: int
    """Entrada + all payments + IOF + fees."""
    juros_centavos: int
    iof_centavos: int
    tarifas_centavos: int
    cet_mensal_percentual: Decimal
    cet_anual_percentual: Decimal
    acima_da_margem: bool
    ressalvas: tuple[Ressalva, ...]


@dataclass(frozen=True)
class JanelaContemplacao:
    melhor_caso_mes: int
    """With a winning Lance in the first assembly."""
    mediana_mes: int
    pior_caso_mes: int
    chance_ate_prazo_percentual: int
    """Chance of being awarded by draw, without bidding, by the Prazo."""


@dataclass(frozen=True)
class Consorcio:
    carta_credito_centavos: int
    duracao_meses: int
    parcela_centavos: int
    """First-year payment; it rises with each yearly Carta adjustment."""
    custo_total_centavos: int
    taxa_administracao_centavos: int
    fundo_reserva_centavos: int
    acima_da_margem: bool
    janela: JanelaContemplacao
    ressalvas: tuple[Ressalva, ...]


@dataclass(frozen=True)
class Lance:
    parcela_restante_centavos: int
    carta_liberada_centavos: int
    dinheiro_proprio_centavos: int


@dataclass(frozen=True)
class Simulacao:
    objetivo: Objetivo
    snapshot_id: str
    financiamento: Financiamento
    consorcio: Consorcio
