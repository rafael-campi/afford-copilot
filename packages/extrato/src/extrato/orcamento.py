from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TransacaoBruta:
    """A statement line as the bank exports it: no category."""

    data: date
    descricao: str
    valor_centavos: int  # positive is a credit, negative a debit


@dataclass(frozen=True)
class ResumoOrcamento:
    entradas_centavos: int
    gastos_centavos: int
    sobra_mensal_centavos: int
    margem_segura_centavos: int

    @property
    def margem_acima_da_sobra(self) -> bool:
        return self.margem_segura_centavos > self.sobra_mensal_centavos


def resumir_orcamento(
    transacoes: list[TransacaoBruta], margem_segura_percentual: int
) -> ResumoOrcamento:
    """Monthly averages over the months present in the Extrato."""
    meses = len({(t.data.year, t.data.month) for t in transacoes}) or 1
    entradas = sum(t.valor_centavos for t in transacoes if t.valor_centavos > 0) // meses
    gastos = -sum(t.valor_centavos for t in transacoes if t.valor_centavos < 0) // meses
    return ResumoOrcamento(
        entradas_centavos=entradas,
        gastos_centavos=gastos,
        sobra_mensal_centavos=entradas - gastos,
        margem_segura_centavos=entradas * margem_segura_percentual // 100,
    )
