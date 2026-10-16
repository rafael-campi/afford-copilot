from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from mercado import RepositorioFocus, ingerir_focus

RESPOSTA_GRAVADA = (Path(__file__).parent / "fixtures" / "focus_anuais.json").read_bytes()
AGORA = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)


def baixar_gravado(url: str) -> bytes:
    assert "ExpectativasMercadoAnuais" in url
    return RESPOSTA_GRAVADA


def test_ingests_the_latest_focus_medians_for_ipca_and_selic(tmp_path: Path) -> None:
    repositorio = RepositorioFocus(tmp_path)

    resultado = ingerir_focus(baixar_gravado, repositorio, AGORA)

    focus = repositorio.mais_recente()
    assert resultado.erro is None
    assert focus is not None
    assert focus.id == "focus-2026-10-09"
    assert focus.data_pesquisa == date(2026, 10, 9)
    assert focus.ipca_anual[2026] == Decimal("5.2245")
    assert focus.ipca_anual[2027] == Decimal("4.3")
    assert focus.selic_anual[2026] == Decimal("13.25")
    assert focus.selic_anual[2027] == Decimal("12.0")


def test_a_failed_focus_download_keeps_the_last_projections(tmp_path: Path) -> None:
    repositorio = RepositorioFocus(tmp_path)
    ingerir_focus(baixar_gravado, repositorio, AGORA)

    def falha(url: str) -> bytes:
        raise TimeoutError("Focus fora do ar")

    resultado = ingerir_focus(falha, repositorio, AGORA)

    assert resultado.erro == "Focus fora do ar"
    focus = repositorio.mais_recente()
    assert focus is not None
    assert focus.id == "focus-2026-10-09"
