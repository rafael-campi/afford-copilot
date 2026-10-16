"""Run the corpus ingestion: python -m rag [data/rag/documentos]."""

import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from rag.documentos import RepositorioDocumentos
from rag.fontes import FONTES
from rag.ingestao import ingerir_fontes


def baixar(url: str) -> bytes:
    pedido = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; afford-copilot/0.1)"}
    )
    with urllib.request.urlopen(pedido, timeout=120) as resposta:
        conteudo: bytes = resposta.read()
        return conteudo


def main() -> int:
    diretorio = Path(sys.argv[1] if len(sys.argv) > 1 else "data/rag/documentos")
    resultados = ingerir_fontes(baixar, RepositorioDocumentos(diretorio), datetime.now(UTC), FONTES)
    for r in resultados:
        situacao = r.erro or (f"nova versão {r.versao}" if r.nova else f"sem mudança ({r.versao})")
        print(f"{r.fonte_id}: {situacao}")
    return 1 if any(r.erro for r in resultados) else 0


if __name__ == "__main__":
    raise SystemExit(main())
