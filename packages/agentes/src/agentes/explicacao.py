"""Explaining the Recomendação: the model words it, the facts bound it (ADR 0007)."""

import re
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

SISTEMA_EXPLICAR = """\
Você explica para uma pessoa, em português simples, por que o copiloto recomendou um caminho
para a compra dela. Use no máximo três frases curtas, fale direto com ela ("você").

Use apenas os fatos recebidos. Não faça contas, não arredonde e não escreva nenhum número que
não esteja nos fatos, exatamente como está escrito neles. Não recomende produtos de investimento
nem instituições. Se houver ressalvas, mencione a mais importante.
"""


class Explicacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str


@dataclass(frozen=True)
class Fatos:
    """What the explanation may say, already worded with the Simulação's own numbers."""

    linhas: tuple[str, ...]
    padrao: str
    """Deterministic explanation used when the model's text cannot be trusted."""

    @property
    def texto(self) -> str:
        return "\n".join(self.linhas)


NUMERO = re.compile(r"\d+(?:[.,]\d+)*")


def so_numeros_dos_fatos(texto: str, fatos: Fatos) -> bool:
    permitidos = set(NUMERO.findall(fatos.texto))
    return all(numero in permitidos for numero in NUMERO.findall(texto))
