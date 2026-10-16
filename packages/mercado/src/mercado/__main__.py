"""Run the ingestion job: python -m mercado <snapshots directory>."""

import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from mercado.ingestao import ingerir
from mercado.snapshots import RepositorioSnapshots


def baixar(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as resposta:
        conteudo: bytes = resposta.read()
        return conteudo


def main() -> int:
    diretorio = Path(sys.argv[1] if len(sys.argv) > 1 else "data/mercado/snapshots")
    resultado = ingerir(baixar, RepositorioSnapshots(diretorio), datetime.now(UTC))
    if resultado.erro:
        print(f"Falha na ingestão, último snapshot mantido: {resultado.erro}", file=sys.stderr)
        return 1
    print(f"Snapshot salvo: {resultado.snapshot_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
