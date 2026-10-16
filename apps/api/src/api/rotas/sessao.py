from fastapi import APIRouter
from pydantic import BaseModel

from api.contexto import Contexto


class PersonaResumo(BaseModel):
    id: str
    nome: str
    perfil: str
    descricao: str


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.get("/v1/personas")
    def listar_personas() -> list[PersonaResumo]:
        return [
            PersonaResumo(id=p.id, nome=p.nome, perfil=p.perfil, descricao=p.descricao)
            for p in ctx.personas.values()
        ]

    return rotas
