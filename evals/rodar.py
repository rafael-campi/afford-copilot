"""Runs the eval suite through the API and writes a report.

    uv run python evals/rodar.py                 # everything (needs Anthropic credentials)
    uv run python evals/rodar.py --deterministicos
    uv run python evals/rodar.py --comparar evals/baseline.json --tolerancia 5

Every run that reaches the model costs money (about 100 model calls for the full suite).
"""

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cenarios import EXPLICACOES, EXTRACOES, GUARDRAILS, RECOMENDACOES, REGRAS
from fastapi.testclient import TestClient
from juiz import julgar_explicacao, julgar_fidelidade
from test_recomendacoes import entrar

from agentes.anthropic_llm import AnthropicLLM
from agentes.guardrails import FORA_DO_ESCOPO, SO_VEICULOS
from agentes.roteador import montar_llm
from api.config import Config
from api.fatos import fatos_da_simulacao
from api.main import create_app
from api.rotas.simulacoes import SimulacaoOut

RELATORIOS = Path(__file__).parent / "relatorios"


@dataclass
class Resultado:
    id: str
    tipo: str
    passou: bool
    detalhe: str
    extra: dict[str, Any] = field(default_factory=dict)


def _sessao(llm: Any, persona: str = "bruno") -> TestClient:
    http = TestClient(create_app(Config(llm=llm)))
    entrar(http, persona)
    return http


def _mensagem(http: TestClient, texto: str) -> dict[str, Any]:
    conversa = http.post("/v1/conversas").json()["id"]
    resposta: dict[str, Any] = http.post(
        f"/v1/conversas/{conversa}/mensagens", json={"texto": texto}
    ).json()
    return resposta


def _confere(esperado: object, obtido: object, campo: str) -> bool:
    if isinstance(esperado, tuple):
        return isinstance(obtido, int) and esperado[0] <= obtido <= esperado[1]
    if campo == "item":
        return isinstance(obtido, str) and str(esperado) in obtido.lower()
    return obtido == esperado


def recomendacoes() -> list[Resultado]:
    resultados = []
    for c in RECOMENDACOES:
        http = TestClient(create_app(Config()))
        entrar(http, c.persona)
        obtido = http.post("/v1/simulacoes", json=c.objetivo).json()["recomendacao"]["caminho"]
        resultados.append(Resultado(c.id, "recomendacao", obtido == c.caminho, f"obtido {obtido}"))
    return resultados


def extracoes(llm: Any) -> list[Resultado]:
    resultados = []
    for c in EXTRACOES:
        objetivo = _mensagem(_sessao(llm), c.mensagem).get("objetivo") or {}
        errados = [k for k, v in c.esperado.items() if not _confere(v, objetivo.get(k), k)]
        detalhe = "ok" if not errados else f"errados {errados}: {objetivo}"
        resultados.append(Resultado(c.id, "extracao", not errados, detalhe))
    return resultados


def guardrails(llm: Any) -> list[Resultado]:
    resultados = []
    for c in GUARDRAILS:
        r = _mensagem(_sessao(llm), c.mensagem)
        texto = r.get("resposta", r.get("detail", ""))
        obtido = (
            "fora_do_escopo"
            if texto == FORA_DO_ESCOPO
            else "so_veiculos"
            if texto == SO_VEICULOS
            else "regra"
            if r.get("citacoes") or "documentos oficiais" in texto
            else "outro"
        )
        vazou = [p for p in c.nao_pode_conter if p.lower() in texto.lower()]
        passou = obtido == c.comportamento and not vazou
        resultados.append(Resultado(c.id, "guardrail", passou, f"{obtido} {vazou or ''}".strip()))
    return resultados


def regras(llm: Any, juiz: Any) -> list[Resultado]:
    resultados = []
    http = _sessao(llm)
    for c in REGRAS:
        r = http.post("/v1/regras/perguntas", json={"pergunta": c.pergunta}).json()
        citou = any(
            x["documento"].startswith(_titulo(c.documento))
            and x["rotulo"].split(" (")[0] == c.rotulo
            for x in r.get("citacoes", [])
        )
        trechos = "\n\n".join(
            f"{x['documento']}, {x['rotulo']}: {x['trecho']}" for x in r.get("citacoes", [])
        )
        julgamento = (
            julgar_fidelidade(juiz, c.pergunta, r["resposta"], trechos) if r.get("sabe") else None
        )
        fiel = bool(julgamento and julgamento.aprovado)
        resultados.append(
            Resultado(
                c.id,
                "regra",
                citou and fiel,
                f"citou={citou} nota={julgamento.nota if julgamento else '-'}",
                {
                    "resposta": r.get("resposta", r.get("detail")),
                    "julgamento": julgamento.model_dump() if julgamento else None,
                },
            )
        )
    return resultados


def _titulo(documento_id: str) -> str:
    return {
        "lei-11795-2008": "Lei nº 11.795/2008",
        "resolucao-bcb-285-2023": "Resolução BCB nº 285/2023",
        "resolucao-cmn-4881-2020": "Resolução CMN nº 4.881/2020",
        "decreto-6306-2007": "Decreto nº 6.306/2007",
    }[documento_id]


def explicacoes(llm: Any, juiz: Any) -> list[Resultado]:
    resultados = []
    for c in EXPLICACOES:
        r = _mensagem(_sessao(llm, c.persona), c.mensagem)
        if not r.get("simulacao"):
            resultados.append(Resultado(c.id, "explicacao", False, "sem simulação"))
            continue
        fatos = fatos_da_simulacao(SimulacaoOut.model_validate(r["simulacao"])).texto
        julgamento = julgar_explicacao(juiz, fatos, r["resposta"])
        resultados.append(
            Resultado(
                c.id,
                "explicacao",
                julgamento.aprovado,
                f"nota={julgamento.nota}",
                {"resposta": r["resposta"], "julgamento": julgamento.model_dump()},
            )
        )
    return resultados


def notas(resultados: list[Resultado]) -> dict[str, float]:
    por_tipo: dict[str, list[bool]] = {}
    for r in resultados:
        por_tipo.setdefault(r.tipo, []).append(r.passou)
    return {t: round(100 * sum(v) / len(v), 1) for t, v in por_tipo.items()}


def comparar(atual: dict[str, float], baseline: dict[str, float], tolerancia: float) -> list[str]:
    """Deterministic types may not drop at all; judged types may drop up to `tolerancia`."""
    quedas = []
    for tipo, nota in baseline.items():
        limite = 0.0 if tipo in {"recomendacao", "extracao", "guardrail"} else tolerancia
        if tipo in atual and atual[tipo] < nota - limite:
            quedas.append(f"{tipo}: {atual[tipo]} < {nota} (tolerância {limite})")
    return quedas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deterministicos", action="store_true")
    parser.add_argument("--comparar", type=Path)
    parser.add_argument("--tolerancia", type=float, default=5.0)
    parser.add_argument(
        "--modelo", help="AFFORD_MODELOS syntax, e.g. entender_pedido=anthropic:claude-sonnet-5-5"
    )
    args = parser.parse_args()

    etapas: list[Callable[[], list[Resultado]]] = [recomendacoes]
    if not args.deterministicos:
        llm, juiz = montar_llm(args.modelo or ""), AnthropicLLM()
        etapas += [
            lambda: extracoes(llm),
            lambda: guardrails(llm),
            lambda: regras(llm, juiz),
            lambda: explicacoes(llm, juiz),
        ]
    resultados = [r for etapa in etapas for r in etapa()]
    atual = notas(resultados)

    RELATORIOS.mkdir(exist_ok=True)
    carimbo = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (RELATORIOS / f"{carimbo}.json").write_text(
        json.dumps(
            {"notas": atual, "resultados": [vars(r) for r in resultados]},
            ensure_ascii=False,
            indent=1,
        ),
        "utf-8",
    )
    for r in resultados:
        print(f"{'ok ' if r.passou else 'FALHOU'} {r.id:<8} {r.detalhe}")
    print("\nnotas:", atual)

    if args.comparar:
        quedas = comparar(atual, json.loads(args.comparar.read_text("utf-8")), args.tolerancia)
        for q in quedas:
            print("QUEDA:", q)
        return 1 if quedas else 0
    return 0 if all(r.passou for r in resultados if r.tipo == "recomendacao") else 1


if __name__ == "__main__":
    sys.exit(main())
