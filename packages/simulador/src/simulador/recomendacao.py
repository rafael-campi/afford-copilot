"""The Recomendação rule (ADR 0004): delivers by the Prazo, fits the Margem segura, cheapest."""

from collections.abc import Callable
from dataclasses import dataclass

from simulador.modelo import (
    Ajustes,
    Avaliacao,
    Consorcio,
    Financiamento,
    Juntar,
    Objetivo,
    Orcamento,
    Recomendacao,
    Ressalva,
)

PASSO_CENTAVOS = 10_000  # adjustments move in steps of R$ 100
PRAZO_MAXIMO = 240


def reais(centavos: int) -> str:
    inteiro, fracao = divmod(centavos, 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{fracao:02d}"


@dataclass(frozen=True)
class _Candidato:
    caminho: str
    entrega_mes: int | None
    """Month the item is guaranteed in hand: 0 for financing, worst case for the consórcio."""
    parcela_centavos: int
    acima_da_margem: bool
    custo_total_centavos: int | None


def candidatos(f: Financiamento, c: Consorcio, j: Juntar) -> list[_Candidato]:
    return [
        _Candidato(
            "financiamento", 0, f.parcela_centavos, f.acima_da_margem, f.custo_total_centavos
        ),
        _Candidato(
            "consorcio",
            c.duracao_meses,
            c.parcela_centavos,
            c.acima_da_margem,
            c.custo_total_centavos,
        ),
        _Candidato(
            "juntar", j.mes_compra, j.deposito_mensal_centavos, False, j.custo_total_centavos
        ),
    ]


def _entrega(candidato: _Candidato, prazo: int) -> bool:
    return candidato.entrega_mes is not None and candidato.entrega_mes <= prazo


def _escolher(candidatos: list[_Candidato], prazo: int) -> _Candidato | None:
    elegiveis = [c for c in candidatos if _entrega(c, prazo) and not c.acima_da_margem]
    return min(
        elegiveis,
        key=lambda c: (c.custo_total_centavos or 0, c.entrega_mes or 0),
        default=None,
    )


def _motivo(
    candidato: _Candidato,
    escolhido: _Candidato | None,
    objetivo: Objetivo,
    orcamento: Orcamento,
) -> tuple[str | None, str | None]:
    prazo = objetivo.prazo_meses
    if not _entrega(candidato, prazo):
        if candidato.caminho == "consorcio":
            return (
                "nao_entrega_no_prazo",
                f"Sem lance, a carta pode sair só no mês {candidato.entrega_mes}, "
                f"depois do seu Prazo de {prazo} meses.",
            )
        if candidato.entrega_mes is None:
            return (
                "nao_entrega_no_prazo",
                "Juntando sua margem, o preço não é alcançado em 20 anos.",
            )
        return (
            "nao_entrega_no_prazo",
            f"Você só teria o {objetivo.item} no mês {candidato.entrega_mes}, "
            f"depois do seu Prazo de {prazo} meses.",
        )
    if candidato.acima_da_margem:
        return (
            "acima_da_margem",
            f"A parcela de {reais(candidato.parcela_centavos)} passa da sua margem de "
            f"{reais(orcamento.margem_segura_centavos)}.",
        )
    if escolhido is not None and candidato is not escolhido:
        return (
            "custo_maior",
            f"Custa {reais(candidato.custo_total_centavos or 0)} no total, mais do que "
            f"{reais(escolhido.custo_total_centavos or 0)}.",
        )
    return (None, None)


def recomendar(
    objetivo: Objetivo,
    orcamento: Orcamento,
    financiamento: Financiamento,
    consorcio: Consorcio,
    juntar: Juntar,
    ajustes: Callable[[], Ajustes],
) -> Recomendacao:
    todos = candidatos(financiamento, consorcio, juntar)
    escolhido = _escolher(todos, objetivo.prazo_meses)
    avaliacoes = tuple(
        Avaliacao(c.caminho, *_motivo(c, escolhido, objetivo, orcamento)) for c in todos
    )
    ressalvas: tuple[Ressalva, ...] = ()
    if escolhido is not None and escolhido.parcela_centavos > orcamento.sobra_mensal_centavos:
        ressalvas = (
            Ressalva(
                codigo="acima_da_sobra",
                texto=(
                    f"A parcela de {reais(escolhido.parcela_centavos)} cabe na margem, mas passa "
                    f"do que sobra por mês hoje ({reais(orcamento.sobra_mensal_centavos)}). "
                    "Seu orçamento ficaria no vermelho."
                ),
            ),
        )
    return Recomendacao(
        caminho=escolhido.caminho if escolhido else None,
        avaliacoes=avaliacoes,
        ressalvas=ressalvas,
        ajustes=None if escolhido else ajustes(),
    )


def algum_serve(f: Financiamento, c: Consorcio, j: Juntar, prazo: int) -> bool:
    return _escolher(candidatos(f, c, j), prazo) is not None


def prazo_minimo(f: Financiamento, c: Consorcio, j: Juntar) -> int | None:
    """Earliest Prazo at which some Caminho that fits the margem delivers."""
    meses = [
        x.entrega_mes
        for x in candidatos(f, c, j)
        if not x.acima_da_margem and x.entrega_mes is not None
    ]
    menor = min(meses, default=None)
    return None if menor is None or menor > PRAZO_MAXIMO else max(menor, 1)


def menor_que_serve(inicio: int, fim: int, serve: Callable[[int], bool]) -> int | None:
    """Smallest value in [inicio, fim], in R$ 100 steps, for which serve() holds.

    serve() must be monotonic: once it holds, it holds for every larger value.
    """
    passos = (fim - inicio) // PASSO_CENTAVOS
    if passos < 0 or not serve(inicio + passos * PASSO_CENTAVOS):
        return None
    baixo, alto = 0, passos
    while baixo < alto:
        meio = (baixo + alto) // 2
        if serve(inicio + meio * PASSO_CENTAVOS):
            alto = meio
        else:
            baixo = meio + 1
    return inicio + baixo * PASSO_CENTAVOS
