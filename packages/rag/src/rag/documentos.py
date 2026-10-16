"""Official documents of the rules corpus, kept by version (URL, capture date, hash)."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Documento:
    id: str
    titulo: str
    url: str
    """Public address to cite."""
    capturado_em: datetime
    versao: str
    """First 12 hex digits of the text's SHA-256: the same text is the same version."""
    texto: str


def versao_de(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


class RepositorioDocumentos:
    """One JSON file per document version: <dir>/<id>/<versao>.json. Nothing is overwritten."""

    def __init__(self, diretorio: Path) -> None:
        self.diretorio = diretorio

    def salvar(self, documento: Documento) -> bool:
        """Stores a new version; returns False when that exact text was already stored."""
        caminho = self.diretorio / documento.id / f"{documento.versao}.json"
        if caminho.exists():
            return False
        caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = {
            "ordem": len(list(caminho.parent.glob("*.json"))) + 1,
            "id": documento.id,
            "titulo": documento.titulo,
            "url": documento.url,
            "capturado_em": documento.capturado_em.isoformat(),
            "versao": documento.versao,
            "texto": documento.texto,
        }
        caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), "utf-8")
        return True

    def versoes(self, documento_id: str) -> list[Documento]:
        """All versions of a document, oldest first."""
        arquivos = (self.diretorio / documento_id).glob("*.json")
        lidas = [(json.loads(p.read_text("utf-8")).get("ordem", 0), _ler(p)) for p in arquivos]
        return [d for _, d in sorted(lidas, key=lambda par: (par[1].capturado_em, par[0]))]

    def atuais(self) -> list[Documento]:
        """The newest version of every document."""
        if not self.diretorio.exists():
            return []
        pastas = sorted(p for p in self.diretorio.iterdir() if p.is_dir())
        return [versoes[-1] for p in pastas if (versoes := self.versoes(p.name))]


def _ler(caminho: Path) -> Documento:
    dados = json.loads(caminho.read_text("utf-8"))
    return Documento(
        id=dados["id"],
        titulo=dados["titulo"],
        url=dados["url"],
        capturado_em=datetime.fromisoformat(dados["capturado_em"]),
        versao=dados["versao"],
        texto=dados["texto"],
    )
