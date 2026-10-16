"""Understanding the Objetivo: what the model extracts and how the copilot completes it."""

from dataclasses import dataclass, replace
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

SISTEMA_ENTENDER_PEDIDO = """\
Você extrai o Objetivo de compra de uma pessoa a partir da mensagem dela, em português.

Campos:
- item: o bem que ela quer comprar, em uma ou duas palavras minúsculas (ex.: "carro", "moto").
- valor_reais: preço do item em reais ("80 mil" = 80000).
- prazo_meses: até quando ela quer ter o item, em meses a partir de hoje. "Em até 5 anos" = 60.
  É uma data-limite para ter o item, não o número de parcelas.
- entrada_reais: quanto ela pode pagar à vista de início, em reais.
- duracao_meses: número de parcelas do financiamento, quando ela pedir ("em 48x" = 48).

Você recebe o Objetivo atual da conversa e a nova mensagem. Devolva só o que a nova mensagem
informa ou corrige; campos que ela não menciona ficam null. Não invente valores.
"""


class ObjetivoExtraido(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: str | None = Field(default=None)
    valor_reais: Decimal | None = Field(default=None)
    prazo_meses: int | None = Field(default=None)
    entrada_reais: Decimal | None = Field(default=None)
    duracao_meses: int | None = Field(default=None)


@dataclass(frozen=True)
class ObjetivoParcial:
    item: str | None = None
    valor_centavos: int | None = None
    prazo_meses: int | None = None
    entrada_centavos: int = 0
    duracao_meses: int | None = None
    """Financing Duração the person asked for; None lets the simulador choose."""

    def muda_de_item(self, extraido: ObjetivoExtraido) -> bool:
        novo = (extraido.item or "").strip().lower()
        return bool(novo) and self.item is not None and novo != self.item

    def com(self, extraido: ObjetivoExtraido) -> "ObjetivoParcial":
        """Applies what the new message says; anything it does not mention stays.

        A different item starts a new Objetivo: nothing from the old one carries over.
        """
        novo = ObjetivoParcial() if self.muda_de_item(extraido) else self
        if extraido.item:
            novo = replace(novo, item=extraido.item.strip().lower())
        if extraido.valor_reais is not None:
            novo = replace(novo, valor_centavos=int(extraido.valor_reais * 100))
        if extraido.prazo_meses is not None:
            novo = replace(novo, prazo_meses=extraido.prazo_meses)
        if extraido.entrada_reais is not None:
            novo = replace(novo, entrada_centavos=int(extraido.entrada_reais * 100))
        if extraido.duracao_meses is not None:
            novo = replace(novo, duracao_meses=extraido.duracao_meses)
        return novo

    @property
    def faltando(self) -> list[str]:
        campos = {"item": self.item, "valor": self.valor_centavos, "prazo": self.prazo_meses}
        return [nome for nome, valor in campos.items() if valor is None]

    def descrever(self) -> str:
        return (
            f"item={self.item}, valor_reais={_reais(self.valor_centavos)}, "
            f"prazo_meses={self.prazo_meses}, entrada_reais={_reais(self.entrada_centavos)}, "
            f"duracao_meses={self.duracao_meses}"
        )


def _reais(centavos: int | None) -> str | None:
    return None if centavos is None else str(centavos // 100)


FEMININOS = {"moto", "motocicleta", "caminhonete", "picape", "van", "bicicleta", "scooter"}


def _artigo(item: str) -> str:
    return "a" if item in FEMININOS else "o"


def pergunta_para(objetivo: ObjetivoParcial) -> str | None:
    """The one question that unblocks the simulation, or None when nothing is missing."""
    if objetivo.item is None:
        return "O que você quer comprar?"
    artigo = _artigo(objetivo.item)
    if objetivo.valor_centavos is None:
        return f"Quanto custa {artigo} {objetivo.item} que você quer?"
    if objetivo.prazo_meses is None:
        return f"Até quando você quer ter {artigo} {objetivo.item}?"
    return None
