from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from api import confirmacoes
from api.config import Config
from api.contexto import Contexto
from api.rotas import (
    consentimentos,
    contas,
    conversas,
    exclusao,
    importacoes,
    orcamento,
    regras,
    sessao,
    simulacoes,
)


class Health(BaseModel):
    status: str


def create_app(config: Config | None = None) -> FastAPI:
    ctx = Contexto(config=config or Config())
    app = FastAPI(title="Afford API", version="0.1.0")
    app.add_middleware(
        SessionMiddleware,
        secret_key=ctx.config.session_secret,
        session_cookie="afford_sessao",
        same_site="lax",
    )

    @app.get("/health")
    def health() -> Health:
        return Health(status="ok")

    app.include_router(sessao.router(ctx))
    app.include_router(contas.router(ctx))
    app.include_router(consentimentos.router(ctx))
    app.include_router(importacoes.router(ctx))
    app.include_router(exclusao.router(ctx))
    app.include_router(confirmacoes.router(ctx))
    app.include_router(orcamento.router(ctx))
    app.include_router(simulacoes.router(ctx))
    app.include_router(conversas.router(ctx))
    app.include_router(regras.router(ctx))
    return app


app = create_app()
