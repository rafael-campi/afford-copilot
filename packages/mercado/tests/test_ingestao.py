from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from mercado import RepositorioSnapshots, SnapshotTaxas, TaxaInstituicao, ingerir

RESPOSTA_GRAVADA = (Path(__file__).parent / "fixtures" / "olinda_veiculos_pf.json").read_bytes()
AGORA = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)


def baixar_gravado(url: str) -> bytes:
    assert "Aquisi%C3%A7%C3%A3o%20de%20ve%C3%ADculos%20-%20Prefixado" in url
    return RESPOSTA_GRAVADA


def baixar_com_falha(url: str) -> bytes:
    raise TimeoutError("BCB fora do ar")


def test_ingests_the_latest_period_of_the_recorded_response(tmp_path: Path) -> None:
    repositorio = RepositorioSnapshots(tmp_path)

    resultado = ingerir(baixar_gravado, repositorio, AGORA)

    snapshot = repositorio.mais_recente()
    assert resultado.erro is None
    assert snapshot is not None
    assert snapshot.id == resultado.snapshot_id == "bcb-veiculos-pf-2026-09-24"
    assert (snapshot.inicio_periodo.isoformat(), snapshot.fim_periodo.isoformat()) == (
        "2026-09-24",
        "2026-09-30",
    )
    assert len(snapshot.taxas) == 42
    assert snapshot.taxas[0] == TaxaInstituicao(
        posicao=1,
        instituicao="BCO MERCEDES-BENZ S.A.",
        cnpj8="60814191",
        taxa_mensal_percentual=Decimal("0.55"),
        taxa_anual_percentual=Decimal("6.85"),
    )
    assert snapshot.taxas[-1].instituicao == "OMNI SA CFI"
    assert snapshot.capturado_em == AGORA


def test_a_failed_download_keeps_the_last_good_snapshot(tmp_path: Path) -> None:
    repositorio = RepositorioSnapshots(tmp_path)
    ingerir(baixar_gravado, repositorio, AGORA)

    resultado = ingerir(baixar_com_falha, repositorio, AGORA)

    assert resultado.erro == "BCB fora do ar"
    snapshot = repositorio.mais_recente()
    assert snapshot is not None
    assert snapshot.id == "bcb-veiculos-pf-2026-09-24"


def test_snapshots_survive_a_new_repository_instance(tmp_path: Path) -> None:
    ingerir(baixar_gravado, RepositorioSnapshots(tmp_path), AGORA)

    snapshot = RepositorioSnapshots(tmp_path).por_id("bcb-veiculos-pf-2026-09-24")

    assert snapshot is not None
    assert len(snapshot.taxas) == 42


def taxa(percentual: str) -> TaxaInstituicao:
    return TaxaInstituicao(0, "X", "0", Decimal(percentual), Decimal(0))


@pytest.mark.parametrize(
    ("percentuais", "mediana"),
    [
        (["3.32", "0.55", "1.20", "0.94", "1.50"], Decimal("0.012")),
        (["1.00", "2.00", "1.50", "3.00"], Decimal("0.0175")),
    ],
)
def test_median_monthly_rate_as_a_fraction(percentuais: list[str], mediana: Decimal) -> None:
    snapshot = SnapshotTaxas(
        id="s",
        inicio_periodo=AGORA.date(),
        fim_periodo=AGORA.date(),
        capturado_em=AGORA,
        taxas=tuple(taxa(p) for p in percentuais),
    )

    assert snapshot.taxa_mediana_mensal == mediana
