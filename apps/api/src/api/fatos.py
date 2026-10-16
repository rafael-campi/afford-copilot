"""The facts of a Simulação, worded once, for the explanation and its fallback."""

from agentes import Fatos
from api.rotas.simulacoes import SimulacaoOut
from simulador.recomendacao import reais

NOMES = {
    "financiamento": "o financiamento",
    "consorcio": "o consórcio",
    "juntar": "juntar e comprar à vista",
}
TITULOS = {"financiamento": "Financiamento", "consorcio": "Consórcio", "juntar": "Juntar"}


def _detalhe(s: SimulacaoOut, caminho: str) -> str:
    if caminho == "financiamento":
        f = s.financiamento
        return (
            f"Parcela de {reais(f.parcela_centavos)} em {f.duracao_meses} meses, "
            f"custo total de {reais(f.custo_total_centavos)} e o item na hora."
        )
    if caminho == "consorcio":
        c = s.consorcio
        return (
            f"Parcela de {reais(c.parcela_centavos)} em {c.duracao_meses} meses, custo total de "
            f"{reais(c.custo_total_centavos)}; a carta sai entre o mês "
            f"{c.janela.melhor_caso_mes}, com lance, e o mês {c.janela.pior_caso_mes}."
        )
    j = s.juntar
    return (
        f"Depositando {reais(j.deposito_mensal_centavos)} por mês, você compra no mês "
        f"{j.mes_compra}, com custo total de {reais(j.custo_total_centavos or 0)}."
    )


def fatos_da_simulacao(s: SimulacaoOut) -> Fatos:
    r = s.recomendacao
    outros = [f"{TITULOS[a.caminho]}: {a.motivo_texto}" for a in r.avaliacoes if a.motivo_texto]
    ressalvas = [x.texto for x in r.ressalvas]
    if r.caminho is None:
        ajustes = r.ajustes
        sugestoes = []
        if ajustes and ajustes.entrada_minima_centavos is not None:
            sugestoes.append(f"dar uma Entrada de {reais(ajustes.entrada_minima_centavos)}")
        if ajustes and ajustes.prazo_minimo_meses is not None:
            sugestoes.append(f"aceitar um Prazo de {ajustes.prazo_minimo_meses} meses")
        if ajustes and ajustes.valor_maximo_centavos is not None:
            sugestoes.append(f"escolher um item de até {reais(ajustes.valor_maximo_centavos)}")
        abertura = "Nenhum caminho cabe hoje no seu Prazo e na sua margem."
        linhas = ["Recomendação: nenhuma", abertura, *outros]
        if sugestoes:
            linhas.append("Ajustes possíveis: " + "; ".join(sugestoes) + ".")
        return Fatos(linhas=tuple(linhas), padrao=" ".join(linhas[1:]))
    detalhe = _detalhe(s, r.caminho)
    linhas = [f"Recomendação: {r.caminho}", detalhe, *outros, *ressalvas]
    padrao = " ".join([f"Recomendo {NOMES[r.caminho]}.", detalhe, *outros, *ressalvas])
    return Fatos(linhas=tuple(linhas), padrao=padrao)
