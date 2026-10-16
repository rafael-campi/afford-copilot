"""Vector indexes: in memory (tests, dev) and pgvector (the stack)."""

from typing import Any, Protocol

from rag.fragmentacao import Trecho


class IndiceVetorial(Protocol):
    def tem_versao(self, documento_id: str, versao: str) -> bool: ...

    def adicionar(self, trechos: list[Trecho], vetores: list[list[float]]) -> None: ...

    def buscar(self, vetor: list[float], k: int, versoes: set[str]) -> list[Trecho]:
        """The k nearest passages among the given document versions."""
        ...


class IndiceEmMemoria:
    def __init__(self) -> None:
        self.itens: list[tuple[Trecho, list[float]]] = []

    def tem_versao(self, documento_id: str, versao: str) -> bool:
        return any(t.documento_id == documento_id and t.versao == versao for t, _ in self.itens)

    def adicionar(self, trechos: list[Trecho], vetores: list[list[float]]) -> None:
        self.itens.extend(zip(trechos, vetores, strict=True))

    def buscar(self, vetor: list[float], k: int, versoes: set[str]) -> list[Trecho]:
        candidatos = [(t, v) for t, v in self.itens if t.versao in versoes]
        candidatos.sort(key=lambda par: -sum(a * b for a, b in zip(vetor, par[1], strict=True)))
        return [t for t, _ in candidatos[:k]]


class IndicePgVector:
    """Passages and their vectors in Postgres (pgvector), cosine distance."""

    def __init__(self, engine: Any, dimensoes: int) -> None:
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import Column, MetaData, String, Table, Text

        self.engine = engine
        metadata = MetaData()
        self.tabela = Table(
            "trechos",
            metadata,
            Column("id", String(80), primary_key=True),
            Column("documento_id", String(80), index=True),
            Column("titulo", String(200)),
            Column("url", String(400)),
            Column("versao", String(12), index=True),
            Column("capturado_em", String(10)),
            Column("rotulo", String(80)),
            Column("texto", Text),
            Column("embedding", Vector(dimensoes)),
        )
        with engine.begin() as conexao:
            from sqlalchemy import text

            conexao.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        metadata.create_all(engine)

    def tem_versao(self, documento_id: str, versao: str) -> bool:
        from sqlalchemy import select

        with self.engine.connect() as conexao:
            consulta = select(self.tabela.c.id).where(
                self.tabela.c.documento_id == documento_id, self.tabela.c.versao == versao
            )
            return conexao.execute(consulta.limit(1)).first() is not None

    def adicionar(self, trechos: list[Trecho], vetores: list[list[float]]) -> None:
        with self.engine.begin() as conexao:
            conexao.execute(
                self.tabela.insert(),
                [{**vars(t), "embedding": v} for t, v in zip(trechos, vetores, strict=True)],
            )

    def buscar(self, vetor: list[float], k: int, versoes: set[str]) -> list[Trecho]:
        from sqlalchemy import select

        colunas = [c for c in self.tabela.c if c.name != "embedding"]
        consulta = (
            select(*colunas)
            .where(self.tabela.c.versao.in_(versoes))
            .order_by(self.tabela.c.embedding.cosine_distance(vetor))
            .limit(k)
        )
        with self.engine.connect() as conexao:
            return [Trecho(**linha._mapping) for linha in conexao.execute(consulta)]
