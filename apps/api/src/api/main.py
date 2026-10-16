import os
from dataclasses import dataclass, field
from datetime import date

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from extrato.categorizacao import categorizar
from extrato.orcamento import resumir_orcamento
from seed.gerador import gerar_extrato
from seed.personas import PERSONAS


@dataclass(frozen=True)
class Config:
    margem_segura_percentual: int = 30
    seed: int = 2026
    session_secret: str = field(
        default_factory=lambda: os.environ.get("AFFORD_SESSION_SECRET", "dev-only-secret")
    )


class Health(BaseModel):
    status: str


class PersonaResumo(BaseModel):
    id: str
    nome: str
    perfil: str
    descricao: str


class NovaSessaoDemo(BaseModel):
    persona_id: str


class ResumoOrcamento(BaseModel):
    entradas_centavos: int
    gastos_centavos: int
    sobra_mensal_centavos: int
    margem_segura_centavos: int
    margem_acima_da_sobra: bool


class Transacao(BaseModel):
    data: date
    descricao: str
    valor_centavos: int
    categoria: str


class Extrato(BaseModel):
    transacoes: list[Transacao]


class Sugestao(BaseModel):
    titulo: str
    descricao: str


class Home(BaseModel):
    nome: str
    resumo: ResumoOrcamento
    sugestoes: list[Sugestao]


SUGESTOES = [
    Sugestao(
        titulo="Consórcio ou financiamento?",
        descricao="Compare o custo total para um carro",
    ),
    Sugestao(
        titulo="Quanto posso comprometer por mês?",
        descricao="Calculado a partir dos seus gastos reais",
    ),
]


def create_app(config: Config | None = None) -> FastAPI:
    config = config or Config()
    personas = {p.id: p for p in PERSONAS}
    app = FastAPI(title="Afford API", version="0.1.0")
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.session_secret,
        session_cookie="afford_sessao",
        same_site="lax",
    )

    def persona_da_sessao(request: Request) -> str:
        persona_id = request.session.get("persona_id")
        if persona_id not in personas:
            raise HTTPException(status_code=401, detail="Entre como uma Persona primeiro.")
        return str(persona_id)

    @app.get("/health")
    def health() -> Health:
        return Health(status="ok")

    @app.get("/v1/personas")
    def listar_personas() -> list[PersonaResumo]:
        return [
            PersonaResumo(id=p.id, nome=p.nome, perfil=p.perfil, descricao=p.descricao)
            for p in PERSONAS
        ]

    @app.post("/v1/sessoes/demo", status_code=204)
    def entrar_como_persona(dados: NovaSessaoDemo, request: Request) -> Response:
        if dados.persona_id not in personas:
            raise HTTPException(status_code=404, detail="Persona não encontrada.")
        request.session["persona_id"] = dados.persona_id
        return Response(status_code=204)

    @app.get("/v1/home")
    def home(request: Request) -> Home:
        persona_id = persona_da_sessao(request)
        extrato = gerar_extrato(persona_id, config.seed)
        resumo = resumir_orcamento(extrato.transacoes, config.margem_segura_percentual)
        return Home(
            nome=personas[persona_id].nome,
            resumo=ResumoOrcamento(
                entradas_centavos=resumo.entradas_centavos,
                gastos_centavos=resumo.gastos_centavos,
                sobra_mensal_centavos=resumo.sobra_mensal_centavos,
                margem_segura_centavos=resumo.margem_segura_centavos,
                margem_acima_da_sobra=resumo.margem_acima_da_sobra,
            ),
            sugestoes=SUGESTOES,
        )

    @app.get("/v1/extrato")
    def extrato(request: Request) -> Extrato:
        persona_id = persona_da_sessao(request)
        gerado = gerar_extrato(persona_id, config.seed)
        return Extrato(
            transacoes=[
                Transacao(
                    data=t.data,
                    descricao=t.descricao,
                    valor_centavos=t.valor_centavos,
                    categoria=categorizar(t),
                )
                for t in gerado.transacoes
            ]
        )

    return app


app = create_app()
