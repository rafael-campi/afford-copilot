from dataclasses import dataclass
from datetime import datetime

from mercado.bcb import Baixar, buscar_taxas_veiculos
from mercado.snapshots import RepositorioSnapshots


@dataclass(frozen=True)
class ResultadoIngestao:
    snapshot_id: str | None
    erro: str | None


def ingerir(
    baixar: Baixar, repositorio: RepositorioSnapshots, agora: datetime
) -> ResultadoIngestao:
    """Fetches the newest BCB period and stores it. On failure, the last snapshot stays."""
    try:
        snapshot = buscar_taxas_veiculos(baixar, agora)
    except Exception as erro:  # any failure must leave the previous snapshot in place
        return ResultadoIngestao(snapshot_id=None, erro=str(erro))
    repositorio.salvar(snapshot)
    return ResultadoIngestao(snapshot_id=snapshot.id, erro=None)
