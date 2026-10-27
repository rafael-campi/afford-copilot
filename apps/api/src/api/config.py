import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

from argon2 import PasswordHasher

from agentes import LLMClient
from rag.embeddings import Embedder

RAIZ = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Config:
    margem_segura_percentual: int = 30
    seed: int = 2026
    diretorio_mercado: Path = field(
        default_factory=lambda: Path(
            os.environ.get("AFFORD_MERCADO_DIR", RAIZ / "data" / "mercado" / "snapshots")
        )
    )
    diretorio_focus: Path = field(
        default_factory=lambda: Path(
            os.environ.get("AFFORD_FOCUS_DIR", RAIZ / "data" / "mercado" / "focus")
        )
    )
    diretorio_rag: Path = field(
        default_factory=lambda: Path(
            os.environ.get("AFFORD_RAG_DIR", RAIZ / "data" / "rag" / "documentos")
        )
    )
    embedder: Embedder | None = None
    """None loads the multilingual model on the first rule question."""
    tarifas_centavos: int = 105_000
    """Estimated tarifa de cadastro (R$ 800) plus registro de contrato (R$ 250)."""
    dias_ate_desatualizar: int = 30
    """BCB publishes each weekly period with a lag; past this many days it is stale."""
    hoje: Callable[[], date] = date.today
    agora: Callable[[], datetime] = lambda: datetime.now(UTC)
    database_url: str = field(
        default_factory=lambda: os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    )
    minutos_de_reautenticacao: int = 5
    horas_de_importacao: int | None = 24
    """Imported Extratos are deleted after this many hours (None keeps them)."""
    hasher: PasswordHasher = field(default_factory=PasswordHasher)
    """argon2id with the library's recommended parameters."""
    llm: LLMClient | None = None
    """None builds the adapters from `modelos` on first use."""
    modelos: str = field(default_factory=lambda: os.environ.get("AFFORD_MODELOS", ""))
    """Model per task, e.g. `entender_pedido=anthropic:claude-haiku-5-5,*=openai:gpt-x`."""
    session_secret: str = field(
        default_factory=lambda: os.environ.get("AFFORD_SESSION_SECRET", "dev-only-secret")
    )
