from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    id: str
    nome: str
    perfil: str
    descricao: str
    artigo: str = "o"
    """Portuguese article for the name: "do Bruno", "da Ana"."""


PERSONAS: tuple[Persona, ...] = (
    Persona(
        id="ana",
        nome="Ana",
        perfil="Folgada",
        descricao="Salário fixo, gastos bem abaixo da renda.",
        artigo="a",
    ),
    Persona(
        id="bruno",
        nome="Bruno",
        perfil="No limite",
        descricao="Sobra pouco: 30% da renda passa do que realmente sobra.",
    ),
    Persona(
        id="carla",
        nome="Carla",
        perfil="Renda variável",
        descricao="Freelancer com renda que muda bastante de um mês para o outro.",
        artigo="a",
    ),
    Persona(
        id="diego",
        nome="Diego",
        perfil="Endividado",
        descricao="Parcelas de empréstimo e juros de cartão consomem quase toda a sobra.",
    ),
)
