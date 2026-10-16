import json
import statistics
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class TaxaInstituicao:
    posicao: int
    instituicao: str
    cnpj8: str
    taxa_mensal_percentual: Decimal
    taxa_anual_percentual: Decimal


@dataclass(frozen=True)
class SnapshotTaxas:
    """BCB average rates per institution for one reference period."""

    id: str
    inicio_periodo: date
    fim_periodo: date
    capturado_em: datetime
    taxas: tuple[TaxaInstituicao, ...]

    @property
    def taxa_mediana_mensal(self) -> Decimal:
        """Median monthly rate across institutions, as a fraction (1.8% -> 0.018)."""
        mediana = statistics.median(t.taxa_mensal_percentual for t in self.taxas)
        return Decimal(mediana) / 100

    def para_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "inicio_periodo": self.inicio_periodo.isoformat(),
                "fim_periodo": self.fim_periodo.isoformat(),
                "capturado_em": self.capturado_em.isoformat(),
                "taxas": [
                    {
                        "posicao": t.posicao,
                        "instituicao": t.instituicao,
                        "cnpj8": t.cnpj8,
                        "taxa_mensal_percentual": str(t.taxa_mensal_percentual),
                        "taxa_anual_percentual": str(t.taxa_anual_percentual),
                    }
                    for t in self.taxas
                ],
            },
            ensure_ascii=False,
            indent=1,
        )

    @staticmethod
    def de_json(texto: str) -> "SnapshotTaxas":
        dados = json.loads(texto)
        return SnapshotTaxas(
            id=dados["id"],
            inicio_periodo=date.fromisoformat(dados["inicio_periodo"]),
            fim_periodo=date.fromisoformat(dados["fim_periodo"]),
            capturado_em=datetime.fromisoformat(dados["capturado_em"]),
            taxas=tuple(
                TaxaInstituicao(
                    posicao=t["posicao"],
                    instituicao=t["instituicao"],
                    cnpj8=t["cnpj8"],
                    taxa_mensal_percentual=Decimal(t["taxa_mensal_percentual"]),
                    taxa_anual_percentual=Decimal(t["taxa_anual_percentual"]),
                )
                for t in dados["taxas"]
            ),
        )


class RepositorioSnapshots:
    """Dated snapshots stored as one JSON file each, never overwritten by a different period."""

    def __init__(self, diretorio: Path) -> None:
        self.diretorio = diretorio

    def salvar(self, snapshot: SnapshotTaxas) -> None:
        self.diretorio.mkdir(parents=True, exist_ok=True)
        (self.diretorio / f"{snapshot.id}.json").write_text(snapshot.para_json(), "utf-8")

    def por_id(self, snapshot_id: str) -> SnapshotTaxas | None:
        caminho = self.diretorio / f"{snapshot_id}.json"
        if not caminho.is_file():
            return None
        return SnapshotTaxas.de_json(caminho.read_text("utf-8"))

    def mais_recente(self) -> SnapshotTaxas | None:
        snapshots = [
            SnapshotTaxas.de_json(p.read_text("utf-8")) for p in self.diretorio.glob("*.json")
        ]
        if not snapshots:
            return None
        return max(snapshots, key=lambda s: (s.fim_periodo, s.capturado_em))
