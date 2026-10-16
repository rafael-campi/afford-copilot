from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from api.banco import Plano
from api.contexto import Contexto
from api.rotas.simulacoes import RessalvaOut, SimulacaoOut
from rag.documentos import RepositorioDocumentos
from rag.fragmentacao import trecho_por_rotulo

Caminho = Literal["financiamento", "consorcio", "juntar"]

EXPLICACOES: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "consorcio": (
        "Você entra num grupo de pessoas que pagam juntas. Todo mês alguém recebe a carta de "
        "crédito por sorteio ou por lance. Não há juros, mas há taxa de administração e, em "
        "geral, fundo de reserva. Se você sair do grupo antes de ser contemplado, só recebe de "
        "volta o que pagou quando for sorteado nas assembleias ou quando o grupo terminar, com "
        "os descontos previstos no contrato.",
        [
            ("lei-11795-2008", "Art. 22"),
            ("lei-11795-2008", "Art. 30"),
            ("resolucao-bcb-285-2023", "Art. 22"),
        ],
    ),
    "financiamento": (
        "A instituição paga o carro agora e você devolve em parcelas fixas com juros (Tabela "
        "Price). O CET junta juros, tarifas, IOF e seguros numa taxa anual: é o número certo "
        "para comparar propostas. Sobre o crédito incide IOF de 0,38% na contratação mais "
        "0,0082% ao dia, contando até 365 dias.",
        [("resolucao-cmn-4881-2020", "Art. 2º"), ("decreto-6306-2007", "Art. 7º")],
    ),
    "juntar": (
        "Você guarda sua margem todo mês e compra à vista quando o dinheiro alcança o preço. "
        "Não há juros nem taxas de crédito, mas você espera mais pelo carro e o preço pode "
        "subir. O rendimento usado é uma referência, não uma promessa.",
        [],
    ),
}
AVISOS = {
    "consorcio": (
        "Nada foi contratado. Para seguir, procure uma administradora de consórcio autorizada "
        "pelo Banco Central e compare a proposta com este plano."
    ),
    "financiamento": (
        "Nada foi contratado. Para seguir, peça propostas a instituições financeiras e "
        "compare o CET de cada uma com este plano."
    ),
    "juntar": (
        "Nada foi contratado. Para seguir, separe o depósito mensal assim que receber; "
        "o copiloto não indica onde investir."
    ),
}


class NovoPlano(BaseModel):
    simulacao_id: str
    caminho: Caminho


class FonteOut(BaseModel):
    documento: str
    rotulo: str
    url: str


class ExplicacaoOut(BaseModel):
    texto: str
    fontes: list[FonteOut]


class ResumoPlano(BaseModel):
    item: str
    valor_centavos: int
    parcela_centavos: int
    duracao_meses: int | None
    custo_total_centavos: int | None
    item_em_maos: str


class PlanoOut(BaseModel):
    id: str
    caminho: Caminho
    criado_em: date
    resumo: ResumoPlano
    ressalvas: list[RessalvaOut]
    explicacao: ExplicacaoOut
    snapshot_id: str
    aviso: str


class PlanoResumido(BaseModel):
    id: str
    caminho: Caminho
    item: str
    criado_em: date


def _resumo(s: SimulacaoOut, caminho: str) -> tuple[ResumoPlano, list[RessalvaOut]]:
    item, valor = s.objetivo.item, s.objetivo.valor_centavos
    if caminho == "financiamento":
        f = s.financiamento
        return ResumoPlano(
            item=item,
            valor_centavos=valor,
            parcela_centavos=f.parcela_centavos,
            duracao_meses=f.duracao_meses,
            custo_total_centavos=f.custo_total_centavos,
            item_em_maos="na hora",
        ), f.ressalvas
    if caminho == "consorcio":
        c = s.consorcio
        return ResumoPlano(
            item=item,
            valor_centavos=valor,
            parcela_centavos=c.parcela_centavos,
            duracao_meses=c.duracao_meses,
            custo_total_centavos=c.custo_total_centavos,
            item_em_maos=f"entre o mês {c.janela.melhor_caso_mes} e o mês {c.janela.pior_caso_mes}",
        ), c.ressalvas
    j = s.juntar
    return ResumoPlano(
        item=item,
        valor_centavos=valor,
        parcela_centavos=j.deposito_mensal_centavos,
        duracao_meses=j.mes_compra,
        custo_total_centavos=j.custo_total_centavos,
        item_em_maos=f"no mês {j.mes_compra}" if j.mes_compra else "fora de alcance em 20 anos",
    ), j.ressalvas


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    def explicacao(caminho: str) -> ExplicacaoOut:
        texto, referencias = EXPLICACOES[caminho]
        documentos = {d.id: d for d in RepositorioDocumentos(ctx.config.diretorio_rag).atuais()}
        fontes = []
        for documento_id, rotulo in referencias:
            documento = documentos.get(documento_id)
            trecho = trecho_por_rotulo(documento, rotulo) if documento else None
            if trecho:
                fontes.append(FonteOut(documento=trecho.titulo, rotulo=rotulo, url=trecho.url))
        return ExplicacaoOut(texto=texto, fontes=fontes)

    def montar(dados: NovoPlano, conta_id: str) -> PlanoOut:
        dono, simulacao = ctx.simulacoes.get(dados.simulacao_id, (None, None))
        if dono != conta_id or not isinstance(simulacao, SimulacaoOut):
            raise HTTPException(status_code=404, detail="Simulação não encontrada.")
        resumo, ressalvas = _resumo(simulacao, dados.caminho)
        return PlanoOut(
            id="",
            caminho=dados.caminho,
            criado_em=ctx.config.agora().date(),
            resumo=resumo,
            ressalvas=ressalvas,
            explicacao=explicacao(dados.caminho),
            snapshot_id=simulacao.snapshot_id,
            aviso=AVISOS[dados.caminho],
        )

    @rotas.post("/v1/planos/previa")
    def previa(dados: NovoPlano, request: Request) -> PlanoOut:
        """What the review screen shows; nothing is stored."""
        return montar(dados, ctx.conta_da_sessao(request).id)

    @rotas.post("/v1/planos", status_code=201)
    def salvar(dados: NovoPlano, request: Request) -> PlanoOut:
        conta = ctx.conta_da_sessao(request)
        saida = montar(dados, conta.id)
        plano = Plano(
            conta_id=conta.id, caminho=dados.caminho, dados={}, criado_em=ctx.config.agora()
        )
        with ctx.banco.begin() as db:
            db.add(plano)
            db.flush()
            saida.id = plano.id
            plano.dados = saida.model_dump(mode="json")
        ctx.auditar(conta.id, "plano_salvo", {"caminho": dados.caminho})
        return saida

    @rotas.get("/v1/planos")
    def listar(request: Request) -> list[PlanoResumido]:
        conta = ctx.conta_da_sessao(request)
        with ctx.banco() as db:
            planos = db.scalars(
                select(Plano).where(Plano.conta_id == conta.id).order_by(Plano.criado_em.desc())
            ).all()
        return [
            PlanoResumido(
                id=p.id,
                caminho=p.dados["caminho"],
                item=p.dados["resumo"]["item"],
                criado_em=date.fromisoformat(p.dados["criado_em"]),
            )
            for p in planos
        ]

    @rotas.get("/v1/planos/{plano_id}")
    def ler(plano_id: str, request: Request) -> PlanoOut:
        conta = ctx.conta_da_sessao(request)
        with ctx.banco() as db:
            plano = db.get(Plano, plano_id)
        if plano is None or plano.conta_id != conta.id:
            raise HTTPException(status_code=404, detail="Plano não encontrado.")
        dados: dict[str, Any] = plano.dados
        return PlanoOut.model_validate(dados)

    return rotas
