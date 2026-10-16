from fastapi import FastAPI
from pydantic import BaseModel

MARGEM_SEGURA_PERCENTUAL = 30


class Health(BaseModel):
    status: str


class ResumoOrcamento(BaseModel):
    entradas_centavos: int
    gastos_centavos: int
    sobra_mensal_centavos: int
    margem_segura_centavos: int


class Sugestao(BaseModel):
    titulo: str
    descricao: str


class Home(BaseModel):
    placeholder: bool
    nome: str
    resumo: ResumoOrcamento
    sugestoes: list[Sugestao]


def _resumo_placeholder() -> ResumoOrcamento:
    # Prototype values until Personas land (ticket 02).
    entradas = 680_000
    gastos = 490_000
    return ResumoOrcamento(
        entradas_centavos=entradas,
        gastos_centavos=gastos,
        sobra_mensal_centavos=entradas - gastos,
        margem_segura_centavos=entradas * MARGEM_SEGURA_PERCENTUAL // 100,
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Afford API", version="0.1.0")

    @app.get("/health")
    def health() -> Health:
        return Health(status="ok")

    @app.get("/v1/home")
    def home() -> Home:
        return Home(
            placeholder=True,
            nome="Rafael",
            resumo=_resumo_placeholder(),
            sugestoes=[
                Sugestao(
                    titulo="Consórcio ou financiamento?",
                    descricao="Compare o custo total para um carro",
                ),
                Sugestao(
                    titulo="Quanto posso comprometer por mês?",
                    descricao="Calculado a partir dos seus gastos reais",
                ),
            ],
        )

    return app


app = create_app()
