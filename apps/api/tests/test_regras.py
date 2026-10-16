from apoio import config_de_teste, entrar_como
from fastapi.testclient import TestClient
from pydantic import BaseModel

from agentes import LLMRoteirizado
from api.main import create_app
from rag.busca import Reordenacao
from rag.resposta import RespostaRegra


class Escolher:
    """Re-ranks by picking the passages whose label is in `rotulos`, answers from them."""

    def __init__(self, rotulos: list[str], resposta: str, sabe: bool = True) -> None:
        self.rotulos = rotulos
        self.resposta = resposta
        self.sabe = sabe
        self.textos: dict[str, str] = {}
        self.ids: list[str] = []

    def extrair(self, tarefa: str, sistema: str, texto: str, esquema: type[BaseModel]) -> BaseModel:
        self.textos[tarefa] = texto
        linhas = [linha for linha in texto.splitlines() if linha.startswith("[")]
        if tarefa == "reordenar_trechos":
            escolhidos = [
                linha[1 : linha.index("]")]
                for linha in linhas
                if any(r in linha for r in self.rotulos)
            ]
            self.ids = escolhidos
            return Reordenacao(ids=escolhidos)
        assert tarefa == "responder_regra"
        return RespostaRegra(sabe=self.sabe, resposta=self.resposta, citacoes=self.ids)


def perguntar(llm: object, pergunta: str) -> dict[str, object]:
    http = TestClient(create_app(config_de_teste(llm=llm)))
    entrar_como(http, "bruno")
    response = http.post("/v1/regras/perguntas", json={"pergunta": pergunta})
    assert response.status_code == 200, response.text
    resposta: dict[str, object] = response.json()
    return resposta


def test_answers_a_rule_question_citing_the_official_passage() -> None:
    llm = Escolher(["Art. 22"], "A contemplação acontece por sorteio ou por lance.")

    resposta = perguntar(llm, "Como funciona o lance no consórcio?")

    assert resposta["sabe"] is True
    assert resposta["resposta"] == "A contemplação acontece por sorteio ou por lance."
    citacoes = resposta["citacoes"]
    assert isinstance(citacoes, list)
    assert len(citacoes) == 1
    citacao = citacoes[0]
    assert citacao["documento"] == "Lei nº 11.795/2008 (Sistema de Consórcio)"
    assert citacao["rotulo"] == "Art. 22"
    assert citacao["url"].startswith("https://www.planalto.gov.br/")
    assert "sorteio ou de lance" in citacao["trecho"]
    assert citacao["capturado_em"] == "2026-10-15"


def test_only_the_current_version_of_a_document_is_searched() -> None:
    llm = Escolher(["Art. 22"], "Por sorteio ou lance.")

    perguntar(llm, "Como funciona a contemplação?")

    assert "Redação antiga" not in llm.textos["reordenar_trechos"]


def test_says_it_does_not_know_when_the_documents_do_not_cover_it() -> None:
    llm = Escolher(["Art. 22"], "Talvez sim.", sabe=False)

    resposta = perguntar(llm, "Posso usar o FGTS no consórcio de carro?")

    assert resposta["sabe"] is False
    assert resposta["resposta"] == (
        "Não encontrei isso nos documentos oficiais que consulto. "
        "Vale perguntar à administradora ou ao Banco Central."
    )
    assert resposta["citacoes"] == []


def test_an_answer_without_valid_citations_is_treated_as_not_knowing() -> None:
    class InventaCitacao(Escolher):
        def extrair(
            self, tarefa: str, sistema: str, texto: str, esquema: type[BaseModel]
        ) -> BaseModel:
            resultado = super().extrair(tarefa, sistema, texto, esquema)
            if tarefa == "responder_regra":
                return RespostaRegra(sabe=True, resposta="Inventado.", citacoes=["nao-existe"])
            return resultado

    resposta = perguntar(InventaCitacao(["Art. 22"], ""), "Como funciona o lance?")

    assert resposta["sabe"] is False
    assert resposta["citacoes"] == []


def test_retrieval_brings_the_relevant_passages_to_the_model() -> None:
    llm = Escolher(["Art. 2º"], "O CET é uma taxa anual com todos os encargos.")

    perguntar(llm, "O que entra no Custo Efetivo Total CET?")

    assert "Custo Efetivo Total" in llm.textos["reordenar_trechos"]
    assert "Art. 2º" in llm.textos["responder_regra"]


def test_rule_questions_are_audited() -> None:
    llm = Escolher(["Art. 22"], "Por sorteio ou lance.")
    http = TestClient(create_app(config_de_teste(llm=llm)))
    entrar_como(http, "bruno")
    http.post("/v1/regras/perguntas", json={"pergunta": "Como funciona o lance?"})

    tipos = [e["tipo"] for e in http.get("/v1/auditoria").json()["eventos"]]

    assert tipos[-3:] == [
        "ferramenta:buscar_regras",
        "modelo:reordenar_trechos",
        "modelo:responder_regra",
    ]


def test_without_the_model_the_question_cannot_be_answered() -> None:
    http = TestClient(create_app(config_de_teste()))
    entrar_como(http, "bruno")

    response = http.post("/v1/regras/perguntas", json={"pergunta": "Como funciona o lance?"})

    assert response.status_code == 503


def test_rule_questions_inside_the_conversation_come_back_with_citations() -> None:
    from decimal import Decimal

    from agentes import ObjetivoExtraido

    llm = Escolher(["Art. 22"], "Por sorteio ou por lance, conforme o contrato.")
    roteiro = LLMRoteirizado(
        {"entender_pedido": [ObjetivoExtraido(intencao="regra", valor_reais=Decimal(0))]}
    )

    class Misto:
        def extrair(
            self, tarefa: str, sistema: str, texto: str, esquema: type[BaseModel]
        ) -> BaseModel:
            alvo = roteiro if tarefa == "entender_pedido" else llm
            return alvo.extrair(tarefa, sistema, texto, esquema)

    http = TestClient(create_app(config_de_teste(llm=Misto())))
    entrar_como(http, "bruno")
    conversa = http.post("/v1/conversas").json()["id"]

    resposta = http.post(
        f"/v1/conversas/{conversa}/mensagens", json={"texto": "Como funciona o lance?"}
    ).json()

    assert resposta["resposta"] == "Por sorteio ou por lance, conforme o contrato."
    assert resposta["citacoes"][0]["rotulo"] == "Art. 22"
    assert resposta["objetivo"]["valor_centavos"] is None
