"""Banco Central Focus survey: annual market expectations for IPCA and Selic."""

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

from mercado.bcb import Baixar
from mercado.ingestao import ResultadoIngestao

SERVICO = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
    "ExpectativasMercadoAnuais"
)


@dataclass(frozen=True)
class ProjecoesFocus:
    """Median expectations by calendar year, in percent."""

    id: str
    data_pesquisa: date
    capturado_em: datetime
    ipca_anual: dict[int, Decimal]
    selic_anual: dict[int, Decimal]

    def para_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "data_pesquisa": self.data_pesquisa.isoformat(),
                "capturado_em": self.capturado_em.isoformat(),
                "ipca_anual": {str(a): str(v) for a, v in self.ipca_anual.items()},
                "selic_anual": {str(a): str(v) for a, v in self.selic_anual.items()},
            },
            indent=1,
        )

    @staticmethod
    def de_json(texto: str) -> "ProjecoesFocus":
        dados = json.loads(texto)
        return ProjecoesFocus(
            id=dados["id"],
            data_pesquisa=date.fromisoformat(dados["data_pesquisa"]),
            capturado_em=datetime.fromisoformat(dados["capturado_em"]),
            ipca_anual={int(a): Decimal(v) for a, v in dados["ipca_anual"].items()},
            selic_anual={int(a): Decimal(v) for a, v in dados["selic_anual"].items()},
        )


class RepositorioFocus:
    def __init__(self, diretorio: Path) -> None:
        self.diretorio = diretorio

    def salvar(self, projecoes: ProjecoesFocus) -> None:
        self.diretorio.mkdir(parents=True, exist_ok=True)
        (self.diretorio / f"{projecoes.id}.json").write_text(projecoes.para_json(), "utf-8")

    def mais_recente(self) -> ProjecoesFocus | None:
        todas = [
            ProjecoesFocus.de_json(p.read_text("utf-8")) for p in self.diretorio.glob("*.json")
        ]
        return max(todas, key=lambda p: (p.data_pesquisa, p.capturado_em), default=None)


def url_focus() -> str:
    filtro = "(Indicador eq 'IPCA' or Indicador eq 'Selic') and baseCalculo eq 0"
    return f"{SERVICO}?$filter={quote(filtro)}&$orderby={quote('Data desc')}&$top=40&$format=json"


def buscar_focus(baixar: Baixar, agora: datetime) -> ProjecoesFocus:
    linhas = [r for r in json.loads(baixar(url_focus()))["value"] if r["baseCalculo"] == 0]
    data = max(r["Data"] for r in linhas)
    do_dia = [r for r in linhas if r["Data"] == data]

    def medianas(indicador: str) -> dict[int, Decimal]:
        return {
            int(r["DataReferencia"]): Decimal(str(r["Mediana"]))
            for r in do_dia
            if r["Indicador"] == indicador
        }

    return ProjecoesFocus(
        id=f"focus-{data}",
        data_pesquisa=date.fromisoformat(data),
        capturado_em=agora,
        ipca_anual=medianas("IPCA"),
        selic_anual=medianas("Selic"),
    )


def ingerir_focus(
    baixar: Baixar, repositorio: RepositorioFocus, agora: datetime
) -> ResultadoIngestao:
    try:
        projecoes = buscar_focus(baixar, agora)
    except Exception as erro:  # any failure must leave the previous projections in place
        return ResultadoIngestao(snapshot_id=None, erro=str(erro))
    repositorio.salvar(projecoes)
    return ResultadoIngestao(snapshot_id=projecoes.id, erro=None)
