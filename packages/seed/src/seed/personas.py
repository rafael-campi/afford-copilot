from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    id: str
    nome: str
    perfil: str
    descricao: str


PERSONAS: tuple[Persona, ...] = (
    Persona(
        id="ana",
        nome="Ana",
        perfil="Folgada",
        descricao="Salário fixo, gastos bem abaixo da renda.",
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
    ),
    Persona(
        id="diego",
        nome="Diego",
        perfil="Endividado",
        descricao="Parcelas de empréstimo e juros de cartão consomem quase toda a sobra.",
    ),
)
