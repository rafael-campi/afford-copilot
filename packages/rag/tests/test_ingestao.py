from datetime import UTC, datetime
from pathlib import Path

from rag import Fonte, RepositorioDocumentos, ingerir_fontes

FIXTURES = Path(__file__).parent / "fixtures"
AGORA = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

LEI = Fonte(
    id="lei-11795-2008",
    titulo="Lei nº 11.795/2008 (Sistema de Consórcio)",
    tipo="planalto",
    url="https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11795.htm",
)
CET = Fonte(
    id="resolucao-cmn-4881-2020",
    titulo="Resolução CMN nº 4.881/2020 (CET)",
    tipo="bcb_normativo",
    url="https://www.bcb.gov.br/api/conteudo/app/normativos/exibenormativo?p1=Resolu%C3%A7%C3%A3o%20CMN&p2=4881",
    url_publica="https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolu%C3%A7%C3%A3o%20CMN&numero=4881",
)
RESPOSTAS = {
    LEI.url: (FIXTURES / "planalto_lei_11795.htm").read_bytes(),
    CET.url: (FIXTURES / "bcb_resolucao_cmn_4881.json").read_bytes(),
}


def baixar(url: str) -> bytes:
    return RESPOSTAS[url]


def test_reads_planalto_pages_without_revoked_text_or_scripts(tmp_path: Path) -> None:
    repositorio = RepositorioDocumentos(tmp_path)

    ingerir_fontes(baixar, repositorio, AGORA, [LEI])

    documento = repositorio.atuais()[0]
    assert documento.id == "lei-11795-2008"
    assert documento.url == LEI.url
    assert "Art. 22" in documento.texto
    assert "Texto revogado" not in documento.texto
    assert "var x" not in documento.texto
    assert documento.capturado_em == AGORA
    assert len(documento.versao) == 12


def test_reads_the_official_text_from_the_bcb_normativos_api(tmp_path: Path) -> None:
    repositorio = RepositorioDocumentos(tmp_path)

    ingerir_fontes(baixar, repositorio, AGORA, [CET])

    documento = repositorio.atuais()[0]
    assert "Custo Efetivo Total" in documento.texto
    assert "&quot;" not in documento.texto
    assert documento.url == CET.url_publica


def test_a_changed_text_becomes_a_new_version_and_the_old_one_is_kept(tmp_path: Path) -> None:
    repositorio = RepositorioDocumentos(tmp_path)
    ingerir_fontes(baixar, repositorio, AGORA, [LEI])
    ingerir_fontes(baixar, repositorio, AGORA, [LEI])
    primeira = repositorio.atuais()[0].versao

    alterada = RESPOSTAS[LEI.url].replace(b"Art. 22", b"Art. 22 (redacao nova)")
    ingerir_fontes(lambda url: alterada, repositorio, AGORA, [LEI])

    assert next(v.versao for v in repositorio.versoes("lei-11795-2008")) == primeira
    assert len(repositorio.versoes("lei-11795-2008")) == 2
    assert repositorio.atuais()[0].versao != primeira


def test_a_failed_download_keeps_the_previous_version(tmp_path: Path) -> None:
    repositorio = RepositorioDocumentos(tmp_path)
    ingerir_fontes(baixar, repositorio, AGORA, [LEI])

    def falha(url: str) -> bytes:
        raise TimeoutError("Planalto fora do ar")

    resultados = ingerir_fontes(falha, repositorio, AGORA, [LEI])

    assert resultados[0].erro == "Planalto fora do ar"
    assert len(repositorio.atuais()) == 1
