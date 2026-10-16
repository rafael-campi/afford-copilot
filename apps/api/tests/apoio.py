from datetime import date
from pathlib import Path

from api.config import Config

MERCADO_DE_TESTE = Path(__file__).parent / "fixtures" / "mercado"


def config_de_teste(**mudancas: object) -> Config:
    """Config pinned to a known market snapshot (median 1.80% a.m.) and a fixed date."""
    base: dict[str, object] = {
        "diretorio_mercado": MERCADO_DE_TESTE,
        "hoje": lambda: date(2026, 10, 15),
    }
    return Config(**{**base, **mudancas})  # type: ignore[arg-type]
