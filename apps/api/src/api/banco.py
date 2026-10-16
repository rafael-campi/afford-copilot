"""Persistence: accounts and the audit log (SQLAlchemy; Postgres in the stack, SQLite in tests)."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def _id() -> str:
    return str(uuid.uuid4())


class Conta(Base):
    __tablename__ = "contas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    nome: Mapped[str] = mapped_column(String(120))
    senha_hash: Mapped[str] = mapped_column(String(255))
    persona_id: Mapped[str | None] = mapped_column(String(40), default=None)
    """Set for demo accounts: their Extrato is the Persona's."""
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EventoAuditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """Insertion order: the log reads in the order things happened."""
    conta_id: Mapped[str] = mapped_column(String(36), index=True)
    """Not a foreign key: the log outlives a deleted account, pointing at an id that no
    longer resolves to anyone."""
    tipo: Mapped[str] = mapped_column(String(80))
    detalhe: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    """Never personal data: identifiers and outcomes only."""
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def criar_engine(url: str) -> Engine:
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("sqlite") and ":memory:" in url:
        engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


def fabrica_de_sessoes(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


class Consentimento(Base):
    """Scoped, time-limited, revocable authorization to read a bank's Extrato."""

    __tablename__ = "consentimentos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    conta_id: Mapped[str] = mapped_column(ForeignKey("contas.id"), index=True)
    banco: Mapped[str] = mapped_column(String(40))
    escopos: Mapped[list[str]] = mapped_column(JSON)
    concedido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class Confirmacao(Base):
    """A sensitive action waiting for the person's explicit, reauthenticated confirmation."""

    __tablename__ = "confirmacoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    conta_id: Mapped[str] = mapped_column(ForeignKey("contas.id"), index=True)
    acao: Mapped[str] = mapped_column(String(60))
    dados: Mapped[dict[str, Any]] = mapped_column(JSON)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class Importacao(Base):
    """An Extrato the person uploaded. The file itself is never stored, only its transactions."""

    __tablename__ = "importacoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    conta_id: Mapped[str] = mapped_column(ForeignKey("contas.id"), index=True)
    formato: Mapped[str] = mapped_column(String(10))
    inicio: Mapped[date] = mapped_column(Date)
    fim: Mapped[date] = mapped_column(Date)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    """Set in the public demo: transactions are deleted when it passes."""


class TransacaoImportada(Base):
    __tablename__ = "transacoes_importadas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    importacao_id: Mapped[str] = mapped_column(
        ForeignKey("importacoes.id", ondelete="CASCADE"), index=True
    )
    data: Mapped[date] = mapped_column(Date)
    descricao: Mapped[str] = mapped_column(String(255))
    valor_centavos: Mapped[int] = mapped_column(Integer)


class Plano(Base):
    """The Caminho the person chose, frozen with the numbers and sources it was shown."""

    __tablename__ = "planos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    conta_id: Mapped[str] = mapped_column(ForeignKey("contas.id"), index=True)
    caminho: Mapped[str] = mapped_column(String(20))
    dados: Mapped[dict[str, Any]] = mapped_column(JSON)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
