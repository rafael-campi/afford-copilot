"""Turns official pages into plain text, dropping what is not in force."""

import json
import re
from html import unescape
from html.parser import HTMLParser

BLOCOS = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "table", "td"}
IGNORAR = {"script", "style", "strike", "s", "del", "head"}
"""Planalto keeps revoked wording struck through; it must never be cited."""


class _Texto(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self.ignorando = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in IGNORAR:
            self.ignorando += 1
        elif tag in BLOCOS:
            self.partes.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in IGNORAR:
            self.ignorando = max(0, self.ignorando - 1)
        elif tag in BLOCOS:
            self.partes.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignorando:
            self.partes.append(data)


def html_para_texto(html: str) -> str:
    leitor = _Texto()
    leitor.feed(html)
    texto = unescape("".join(leitor.partes)).replace("\xa0", " ")
    linhas = (re.sub(r"\s+", " ", linha).strip() for linha in texto.splitlines())
    return "\n".join(linha for linha in linhas if linha)


def decodificar(conteudo: bytes) -> str:
    try:
        return conteudo.decode("utf-8")
    except UnicodeDecodeError:
        return conteudo.decode("cp1252", errors="replace")


def texto_planalto(conteudo: bytes) -> str:
    return html_para_texto(decodificar(conteudo))


def texto_bcb_normativo(conteudo: bytes) -> str:
    """The BCB normativos API returns the consolidated text as HTML inside JSON."""
    normativo = json.loads(conteudo)["conteudo"][0]
    if str(normativo.get("Revogado")).lower() == "true":
        raise ValueError(f"{normativo.get('Titulo')} foi revogado.")
    return html_para_texto(normativo["Texto"])
