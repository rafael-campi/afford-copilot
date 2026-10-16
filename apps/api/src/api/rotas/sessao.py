from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from api.contexto import Contexto


class PersonaResumo(BaseModel):
    id: str
    nome: str
    perfil: str
    descricao: str


class NovaSessaoDemo(BaseModel):
    persona_id: str


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()

    @rotas.get("/v1/personas")
    def listar_personas() -> list[PersonaResumo]:
        return [
            PersonaResumo(id=p.id, nome=p.nome, perfil=p.perfil, descricao=p.descricao)
            for p in ctx.personas.values()
        ]

    @rotas.post("/v1/sessoes/demo", status_code=204)
    def entrar_como_persona(dados: NovaSessaoDemo, request: Request) -> Response:
        if dados.persona_id not in ctx.personas:
            raise HTTPException(status_code=404, detail="Persona não encontrada.")
        request.session["persona_id"] = dados.persona_id
        return Response(status_code=204)

    return rotas
