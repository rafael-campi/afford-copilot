"""Splits legal texts at article boundaries, so a citation points at the right article."""

import itertools
import re
from dataclasses import dataclass

from rag.documentos import Documento

ARTIGO = re.compile(r"^Art\.\s*(\d+)\s*[º°o]?\s*(-\s*[A-Z])?", re.M)
TAMANHO_MAXIMO = 1800


@dataclass(frozen=True)
class Trecho:
    id: str
    documento_id: str
    titulo: str
    url: str
    versao: str
    capturado_em: str
    rotulo: str
    texto: str

    @property
    def para_embedding(self) -> str:
        """Context-aware chunk: the document and article travel with the text."""
        return f"{self.titulo}. {self.rotulo}. {self.texto}"


def _rotulo(bloco: str) -> str:
    achado = ARTIGO.match(bloco)
    if not achado:
        return "Ementa"
    numero = int(achado.group(1))
    letra = (achado.group(2) or "").replace(" ", "")
    return (f"Art. {numero}º" if numero < 10 else f"Art. {numero}") + letra


def _partes(bloco: str) -> list[str]:
    """Breaks a long article at line ends (paragraphs, items) into pieces that fit."""
    if len(bloco) <= TAMANHO_MAXIMO:
        return [bloco]
    partes, atual = [], ""
    for linha in bloco.splitlines():
        if atual and len(atual) + len(linha) + 1 > TAMANHO_MAXIMO:
            partes.append(atual)
            atual = ""
        atual = f"{atual}\n{linha}" if atual else linha
    return [*partes, atual] if atual else partes


def fragmentar(documento: Documento) -> list[Trecho]:
    inicios = [m.start() for m in ARTIGO.finditer(documento.texto)]
    cortes = [0, *inicios, len(documento.texto)]
    blocos = [documento.texto[a:b].strip() for a, b in itertools.pairwise(cortes)]
    trechos: list[Trecho] = []
    for bloco in blocos:
        if not bloco:
            continue
        rotulo = _rotulo(bloco)
        partes = _partes(bloco)
        for n, parte in enumerate(partes, 1):
            sufixo = f" (parte {n})" if len(partes) > 1 else ""
            trechos.append(
                Trecho(
                    id=f"{documento.id}:{documento.versao}:{len(trechos)}",
                    documento_id=documento.id,
                    titulo=documento.titulo,
                    url=documento.url,
                    versao=documento.versao,
                    capturado_em=documento.capturado_em.date().isoformat(),
                    rotulo=rotulo + sufixo,
                    texto=parte,
                )
            )
    return trechos


def trecho_por_rotulo(documento: Documento, rotulo: str) -> Trecho | None:
    """The passage of an article (its first part when the article was split)."""
    return next(
        (t for t in fragmentar(documento) if t.rotulo.split(" (")[0] == rotulo),
        None,
    )
