"""The V1 corpus: official, in force, verified on 2026-10-15."""

from rag.ingestao import Fonte

_BCB_API = "https://www.bcb.gov.br/api/conteudo/app/normativos/exibenormativo"
_BCB_PUBLICO = "https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo"

FONTES: list[Fonte] = [
    Fonte(
        id="lei-11795-2008",
        titulo="Lei nº 11.795/2008 (Sistema de Consórcio)",
        tipo="planalto",
        url="https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11795.htm",
    ),
    Fonte(
        id="resolucao-bcb-285-2023",
        titulo="Resolução BCB nº 285/2023 (grupos de consórcio)",
        tipo="bcb_normativo",
        url=f"{_BCB_API}?p1=Resolu%C3%A7%C3%A3o%20BCB&p2=285",
        url_publica=f"{_BCB_PUBLICO}?tipo=Resolu%C3%A7%C3%A3o%20BCB&numero=285",
    ),
    Fonte(
        id="resolucao-cmn-4881-2020",
        titulo="Resolução CMN nº 4.881/2020 (Custo Efetivo Total)",
        tipo="bcb_normativo",
        url=f"{_BCB_API}?p1=Resolu%C3%A7%C3%A3o%20CMN&p2=4881",
        url_publica=f"{_BCB_PUBLICO}?tipo=Resolu%C3%A7%C3%A3o%20CMN&numero=4881",
    ),
    Fonte(
        id="decreto-6306-2007",
        titulo="Decreto nº 6.306/2007 (IOF)",
        tipo="planalto",
        url="https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6306.htm",
    ),
]
