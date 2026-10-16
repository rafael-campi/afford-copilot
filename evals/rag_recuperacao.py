"""Retrieval quality of the rules corpus: does the right article reach the model?

For each question, the expected (document, article) must be among the candidates the vector
search hands to the re-ranker. Runs the real multilingual embedder; no model calls, no key.

    uv run python evals/rag_recuperacao.py
"""

import sys
from pathlib import Path

from rag.busca import CANDIDATOS, expandir
from rag.documentos import RepositorioDocumentos
from rag.embeddings import EmbedderFastEmbed
from rag.fragmentacao import fragmentar
from rag.indice import IndiceEmMemoria

PERGUNTAS: list[tuple[str, str, str]] = [
    ("Como funciona o lance no consórcio?", "resolucao-bcb-285-2023", "Art. 12"),
    ("O que é contemplação?", "lei-11795-2008", "Art. 22"),
    ("Se eu desistir do consórcio recebo o dinheiro de volta?", "lei-11795-2008", "Art. 30"),
    ("Quem administra um grupo de consórcio?", "lei-11795-2008", "Art. 5º"),
    ("O que é o fundo de reserva do consórcio?", "resolucao-bcb-285-2023", "Art. 22"),
    ("O que entra no Custo Efetivo Total?", "resolucao-cmn-4881-2020", "Art. 3º"),
    ("Como o CET deve ser informado ao cliente?", "resolucao-cmn-4881-2020", "Art. 2º"),
    ("Qual a alíquota adicional de IOF no crédito?", "decreto-6306-2007", "Art. 7º"),
]


def avaliar() -> int:
    documentos = RepositorioDocumentos(Path("data/rag/documentos")).atuais()
    trechos = [t for d in documentos for t in fragmentar(d)]
    embedder = EmbedderFastEmbed()
    indice = IndiceEmMemoria()
    indice.adicionar(trechos, embedder.embutir([t.para_embedding for t in trechos]))
    versoes = {d.versao for d in documentos}
    achados, reciproco = 0, 0.0
    for pergunta, documento, rotulo in PERGUNTAS:
        candidatos = indice.buscar(embedder.embutir([expandir(pergunta)])[0], CANDIDATOS, versoes)
        posicoes = [
            i
            for i, t in enumerate(candidatos, 1)
            if t.documento_id == documento and t.rotulo.split(" (")[0] == rotulo
        ]
        posicao = posicoes[0] if posicoes else None
        achados += posicao is not None
        reciproco += 1 / posicao if posicao else 0
        print(f"{'ok ' if posicao else 'NÃO'} {posicao or '-':>3}  {pergunta}  ({rotulo})")
    total = len(PERGUNTAS)
    recall = f"recall@{CANDIDATOS}: {achados}/{total} = {achados / total:.0%}"
    print(f"\n{recall}   MRR: {reciproco / total:.2f}")
    return 0 if achados == total else 1


if __name__ == "__main__":
    sys.exit(avaliar())
