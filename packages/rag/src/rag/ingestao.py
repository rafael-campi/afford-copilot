"""Fetches the official sources and stores each new version."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from rag.documentos import Documento, RepositorioDocumentos, versao_de
from rag.extracao import texto_bcb_normativo, texto_planalto

Baixar = Callable[[str], bytes]


@dataclass(frozen=True)
class Fonte:
    id: str
    titulo: str
    tipo: Literal["planalto", "bcb_normativo"]
    url: str
    """Where the text is downloaded from."""
    url_publica: str | None = None
    """Where a person reads it, when different from `url`."""


@dataclass(frozen=True)
class ResultadoIngestao:
    fonte_id: str
    versao: str | None
    nova: bool
    erro: str | None


EXTRATORES = {"planalto": texto_planalto, "bcb_normativo": texto_bcb_normativo}


def ingerir_fontes(
    baixar: Baixar, repositorio: RepositorioDocumentos, agora: datetime, fontes: list[Fonte]
) -> list[ResultadoIngestao]:
    resultados = []
    for fonte in fontes:
        try:
            texto = EXTRATORES[fonte.tipo](baixar(fonte.url))
        except Exception as erro:  # one failing source must not stop the others
            resultados.append(ResultadoIngestao(fonte.id, None, False, str(erro)))
            continue
        documento = Documento(
            id=fonte.id,
            titulo=fonte.titulo,
            url=fonte.url_publica or fonte.url,
            capturado_em=agora,
            versao=versao_de(texto),
            texto=texto,
        )
        nova = repositorio.salvar(documento)
        resultados.append(ResultadoIngestao(fonte.id, documento.versao, nova, None))
    return resultados
