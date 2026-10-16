"""LLM-as-judge with a rubric, for what exact match cannot check: faithfulness and clarity."""

from pydantic import BaseModel, ConfigDict, Field

from agentes import LLMClient

SISTEMA_FIDELIDADE = """\
Você avalia a resposta de um copiloto financeiro a uma pergunta sobre regras, dados os trechos
oficiais que ele recebeu. Critérios:
- fiel: toda afirmação da resposta está sustentada pelos trechos (nada inventado).
- responde: a resposta trata da pergunta feita.
- nota de 1 a 5: 5 = fiel, completa e clara para leigos; 3 = fiel mas incompleta ou confusa;
  1 = afirma algo que os trechos não sustentam.
Seja rigoroso: na dúvida sobre uma afirmação, considere-a não sustentada.
"""

SISTEMA_EXPLICACAO = """\
Você avalia a explicação que um copiloto financeiro deu para a recomendação de um caminho de
compra (consórcio, financiamento ou juntar e comprar à vista), dados os fatos da simulação.
Critérios:
- fiel: a explicação é coerente com os fatos e não contradiz nenhum número ou motivo.
- responde: explica por que aquele caminho foi recomendado (ou por que nenhum coube).
- nota de 1 a 5: 5 = fiel, clara para leigos, menciona a ressalva mais importante quando há;
  3 = fiel mas vaga; 1 = contradiz os fatos ou recomenda produtos ou instituições.
"""


class Julgamento(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fiel: bool
    responde: bool
    nota: int = Field(ge=1, le=5)
    justificativa: str

    @property
    def aprovado(self) -> bool:
        return self.fiel and self.responde and self.nota >= 4


def julgar_fidelidade(juiz: LLMClient, pergunta: str, resposta: str, trechos: str) -> Julgamento:
    texto = (
        f"Pergunta: {pergunta}\n\nTrechos oficiais:\n{trechos}\n\nResposta do copiloto:\n{resposta}"
    )
    return juiz.extrair("julgar_fidelidade", SISTEMA_FIDELIDADE, texto, Julgamento)


def julgar_explicacao(juiz: LLMClient, fatos: str, explicacao: str) -> Julgamento:
    texto = f"Fatos da simulação:\n{fatos}\n\nExplicação do copiloto:\n{explicacao}"
    return juiz.extrair("julgar_explicacao", SISTEMA_EXPLICACAO, texto, Julgamento)
