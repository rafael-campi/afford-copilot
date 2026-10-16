"""Embedders: a multilingual model for real use, a deterministic one for tests and offline."""

import hashlib
import math
import re
import unicodedata
from typing import Any, Protocol


class Embedder(Protocol):
    dimensoes: int

    def embutir(self, textos: list[str]) -> list[list[float]]: ...


def _normalizar(vetor: list[float]) -> list[float]:
    norma = math.sqrt(sum(v * v for v in vetor)) or 1.0
    return [v / norma for v in vetor]


class EmbedderDeterministico:
    """Hashed bag of words. No model download, same vector for the same text, enough to
    rank passages that share words with the question."""

    dimensoes = 512

    def embutir(self, textos: list[str]) -> list[list[float]]:
        return [self._um(t) for t in textos]

    def _um(self, texto: str) -> list[float]:
        vetor = [0.0] * self.dimensoes
        sem_acento = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
        for palavra in re.findall(r"[a-z0-9]{3,}", sem_acento):
            indice = int(hashlib.md5(palavra.encode()).hexdigest(), 16) % self.dimensoes
            vetor[indice] += 1.0
        return _normalizar(vetor)


class EmbedderFastEmbed:
    """paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions) via ONNX, loaded on first use."""

    dimensoes = 384
    modelo = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self) -> None:
        self._modelo: Any = None

    def embutir(self, textos: list[str]) -> list[list[float]]:
        if self._modelo is None:
            from fastembed import TextEmbedding

            self._modelo = TextEmbedding(self.modelo)
        return [_normalizar([float(x) for x in v]) for v in self._modelo.embed(textos)]
