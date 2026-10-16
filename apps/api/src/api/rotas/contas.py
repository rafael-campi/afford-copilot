from argon2.exceptions import VerificationError
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from api.banco import Conta, EventoAuditoria
from api.contexto import Contexto

SENHA_DEMO = "demo"
"""Shown on screen: demo accounts reauthenticate with it."""


class NovaConta(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=12, max_length=200)


class Credenciais(BaseModel):
    email: EmailStr
    senha: str


class Reautenticacao(BaseModel):
    senha: str


class NovaSessaoDemo(BaseModel):
    persona_id: str


class ContaOut(BaseModel):
    nome: str
    email: str
    demo: bool


class SessaoOut(BaseModel):
    conta: ContaOut
    reautenticado: bool


class EventoOut(BaseModel):
    tipo: str
    detalhe: dict[str, object] | None
    criado_em: str


class AuditoriaOut(BaseModel):
    eventos: list[EventoOut]


def router(ctx: Contexto) -> APIRouter:
    rotas = APIRouter()
    hasher = ctx.config.hasher

    def _confere(conta: Conta, senha: str) -> bool:
        try:
            return hasher.verify(conta.senha_hash, senha)
        except VerificationError:
            return False

    def entrar(request: Request, conta: Conta) -> None:
        request.session.clear()
        request.session["conta_id"] = conta.id

    def por_email(email: str) -> Conta | None:
        with ctx.banco() as db:
            return db.scalar(select(Conta).where(Conta.email == email.lower()))

    @rotas.post("/v1/contas", status_code=201)
    def cadastrar(dados: NovaConta, request: Request) -> ContaOut:
        if por_email(dados.email) is not None:
            raise HTTPException(status_code=409, detail="Já existe uma conta com esse e-mail.")
        conta = Conta(
            email=dados.email.lower(),
            nome=dados.nome.strip(),
            senha_hash=hasher.hash(dados.senha),
            criada_em=ctx.config.agora(),
        )
        with ctx.banco.begin() as db:
            db.add(conta)
        ctx.auditar(conta.id, "cadastro")
        entrar(request, conta)
        return ContaOut(nome=conta.nome, email=conta.email, demo=False)

    @rotas.post("/v1/sessoes", status_code=204)
    def login(dados: Credenciais, request: Request) -> Response:
        conta = por_email(dados.email)
        if conta is None or not _confere(conta, dados.senha):
            if conta is not None:
                ctx.auditar(conta.id, "login_falhou")
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
        entrar(request, conta)
        ctx.auditar(conta.id, "login")
        return Response(status_code=204)

    @rotas.post("/v1/sessoes/demo", status_code=204)
    def entrar_como_persona(dados: NovaSessaoDemo, request: Request) -> Response:
        persona = ctx.personas.get(dados.persona_id)
        if persona is None:
            raise HTTPException(status_code=404, detail="Persona não encontrada.")
        conta = por_email(f"{persona.id}@demo.afford")
        if conta is None:
            conta = Conta(
                email=f"{persona.id}@demo.afford",
                nome=persona.nome,
                senha_hash=hasher.hash(SENHA_DEMO),
                persona_id=persona.id,
                criada_em=ctx.config.agora(),
            )
            with ctx.banco.begin() as db:
                db.add(conta)
        entrar(request, conta)
        ctx.auditar(conta.id, "sessao_demo")
        return Response(status_code=204)

    @rotas.get("/v1/sessoes")
    def sessao_atual(request: Request) -> SessaoOut:
        conta = ctx.conta_da_sessao(request)
        return SessaoOut(
            conta=ContaOut(nome=conta.nome, email=conta.email, demo=conta.persona_id is not None),
            reautenticado=ctx.reautenticado(request),
        )

    @rotas.delete("/v1/sessoes", status_code=204)
    def logout(request: Request) -> Response:
        conta_id = request.session.get("conta_id")
        request.session.clear()
        if conta_id:
            ctx.auditar(conta_id, "logout")
        return Response(status_code=204)

    @rotas.post("/v1/sessoes/reautenticar", status_code=204)
    def reautenticar(dados: Reautenticacao, request: Request) -> Response:
        conta = ctx.conta_da_sessao(request)
        if not _confere(conta, dados.senha):
            ctx.auditar(conta.id, "reautenticacao_falhou")
            raise HTTPException(status_code=401, detail="Senha incorreta.")
        request.session["reautenticado_em"] = ctx.config.agora().isoformat()
        ctx.auditar(conta.id, "reautenticacao")
        return Response(status_code=204)

    @rotas.get("/v1/auditoria")
    def auditoria(request: Request) -> AuditoriaOut:
        conta = ctx.conta_da_sessao(request)
        with ctx.banco() as db:
            eventos = db.scalars(
                select(EventoAuditoria)
                .where(EventoAuditoria.conta_id == conta.id)
                .order_by(EventoAuditoria.id)
            ).all()
        return AuditoriaOut(
            eventos=[
                EventoOut(tipo=e.tipo, detalhe=e.detalhe, criado_em=e.criado_em.isoformat())
                for e in eventos
            ]
        )

    return rotas
