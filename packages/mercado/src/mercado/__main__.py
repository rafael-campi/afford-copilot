"""Run the ingestion jobs: python -m mercado [data/mercado]."""

import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from mercado.focus import RepositorioFocus, ingerir_focus
from mercado.ingestao import ingerir
from mercado.snapshots import RepositorioSnapshots


def baixar(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as resposta:
        conteudo: bytes = resposta.read()
        return conteudo


def main() -> int:
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "data/mercado")
    agora = datetime.now(UTC)
    resultados = {
        "Taxas BCB": ingerir(baixar, RepositorioSnapshots(raiz / "snapshots"), agora),
        "Focus": ingerir_focus(baixar, RepositorioFocus(raiz / "focus"), agora),
    }
    for nome, resultado in resultados.items():
        if resultado.erro:
            print(f"{nome}: falha, último dado mantido: {resultado.erro}", file=sys.stderr)
        else:
            print(f"{nome}: salvo {resultado.snapshot_id}")
    return 1 if any(r.erro for r in resultados.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
