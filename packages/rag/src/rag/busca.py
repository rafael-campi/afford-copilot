"""buscar_regras: vector search for candidates, then the model re-ranks them."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from agentes import LLMClient, ModeloIndisponivel, RecusaDoModelo
from rag.documentos import RepositorioDocumentos
from rag.embeddings import Embedder
from rag.fragmentacao import Trecho, fragmentar
from rag.indice import IndiceVetorial

CANDIDATOS = 16
ESCOLHIDOS = 4
TAMANHO_NA_LISTA = 700

SISTEMA_REORDENAR = """\
Você recebe uma pergunta sobre regras de consórcio, financiamento, CET ou IOF e trechos de
documentos oficiais, cada um com um identificador entre colchetes. Devolva os identificadores
dos trechos que ajudam a responder, do mais útil para o menos útil, no máximo quatro. Se nenhum
ajudar, devolva uma lista vazia.
"""


# How people ask -> how the norms are written. Appended to the question before embedding.
EXPANSOES: dict[str, str] = {
    "desist": "exclusão do consorciado excluído restituição das importâncias pagas",
    "devolv": "restituição",
    "parcela": "prestação",
    "carta": "crédito contemplação",
    "sorteio": "contemplação por sorteio",
    "taxa de administra": "taxa de administração remuneração da administradora",
    "juros": "taxa de juros encargos",
    "atras": "inadimplência",
}


def expandir(pergunta: str) -> str:
    minuscula = pergunta.lower()
    extras = [termos for chave, termos in EXPANSOES.items() if chave in minuscula]
    return " ".join([pergunta, *extras])


class Reordenacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: list[str]


@dataclass
class BaseDeRegras:
    repositorio: RepositorioDocumentos
    embedder: Embedder
    indice: IndiceVetorial

    def versoes_atuais(self) -> set[str]:
        """Indexes what is missing and returns the current version of every document."""
        versoes = set()
        for documento in self.repositorio.atuais():
            versoes.add(documento.versao)
            if not self.indice.tem_versao(documento.id, documento.versao):
                trechos = fragmentar(documento)
                vetores = self.embedder.embutir([t.para_embedding for t in trechos])
                self.indice.adicionar(trechos, vetores)
        return versoes

    def buscar(self, pergunta: str, llm: LLMClient) -> list[Trecho]:
        vetor = self.embedder.embutir([expandir(pergunta)])[0]
        candidatos = self.indice.buscar(vetor, CANDIDATOS, self.versoes_atuais())
        lista = "\n".join(
            f"[{t.id}] {t.titulo}, {t.rotulo}: {t.texto[:TAMANHO_NA_LISTA]}" for t in candidatos
        )
        try:
            ordem = llm.extrair(
                "reordenar_trechos",
                SISTEMA_REORDENAR,
                f"Pergunta: {pergunta}\n\nTrechos:\n{lista}",
                Reordenacao,
            )
        except (ModeloIndisponivel, RecusaDoModelo):
            return candidatos[:ESCOLHIDOS]
        por_id = {t.id: t for t in candidatos}
        return [por_id[i] for i in ordem.ids if i in por_id][:ESCOLHIDOS]
