from typing import Any

from apoio import config_de_teste, entrar_como
from fastapi.testclient import TestClient

from api.main import create_app

CARRO = {"item": "carro", "valor_centavos": 8_000_000, "prazo_meses": 60}


def sessao(persona_id: str = "bruno", app: object | None = None) -> TestClient:
    http = TestClient(app or create_app(config_de_teste()))  # type: ignore[arg-type]
    entrar_como(http, persona_id)
    return http


def salvar(http: TestClient, caminho: str) -> dict[str, Any]:
    simulacao = http.post("/v1/simulacoes", json=CARRO).json()
    response = http.post("/v1/planos", json={"simulacao_id": simulacao["id"], "caminho": caminho})
    assert response.status_code == 201, response.text
    plano: dict[str, Any] = response.json()
    return plano


def test_saving_a_plano_needs_no_password_and_contracts_nothing() -> None:
    http = sessao()

    plano = salvar(http, "consorcio")

    assert plano["caminho"] == "consorcio"
    assert plano["aviso"] == (
        "Nada foi contratado. Para seguir, procure uma administradora de consórcio autorizada "
        "pelo Banco Central e compare a proposta com este plano."
    )
    resumo = plano["resumo"]
    assert isinstance(resumo, dict)
    assert resumo["parcela_centavos"] == 195_000
    assert resumo["duracao_meses"] == 48
    assert plano["snapshot_id"] == "bcb-veiculos-pf-2026-09-24"
    assert [r["codigo"] for r in plano["ressalvas"]] == [
        "contemplacao_incerta",
        "faixas_de_mercado",
    ]


def test_the_consorcio_explanation_states_the_withdrawal_rule_with_its_source() -> None:
    plano = salvar(sessao(), "consorcio")

    explicacao = plano["explicacao"]
    assert isinstance(explicacao, dict)
    assert "só recebe de volta o que pagou quando for sorteado" in explicacao["texto"]
    fontes = {(f["documento"], f["rotulo"]) for f in explicacao["fontes"]}
    assert ("Lei nº 11.795/2008 (Sistema de Consórcio)", "Art. 30") in fontes
    assert all(f["url"].startswith("https://") for f in explicacao["fontes"])


def test_the_financing_explanation_cites_the_cet_and_iof_rules() -> None:
    plano = salvar(sessao(), "financiamento")

    fontes = {f["rotulo"] for f in plano["explicacao"]["fontes"]}
    assert {"Art. 2º", "Art. 7º"} <= fontes
    assert plano["aviso"] == (
        "Nada foi contratado. Para seguir, peça propostas a instituições financeiras e "
        "compare o CET de cada uma com este plano."
    )


def test_saved_planos_can_be_listed_and_read_again() -> None:
    http = sessao()
    plano = salvar(http, "juntar")

    lista = http.get("/v1/planos").json()
    lido = http.get(f"/v1/planos/{plano['id']}").json()

    assert [p["id"] for p in lista] == [plano["id"]]
    assert lista[0]["caminho"] == "juntar"
    assert lista[0]["criado_em"] == "2026-10-15"
    assert lido == plano


def test_unknown_simulacao_or_caminho_is_refused() -> None:
    http = sessao()
    simulacao = http.post("/v1/simulacoes", json=CARRO).json()

    sem_simulacao = http.post("/v1/planos", json={"simulacao_id": "x", "caminho": "juntar"})
    caminho_errado = http.post(
        "/v1/planos", json={"simulacao_id": simulacao["id"], "caminho": "poupanca"}
    )

    assert sem_simulacao.status_code == 404
    assert caminho_errado.status_code == 422


def test_another_account_cannot_see_or_reuse_my_plano() -> None:
    app = create_app(config_de_teste())
    dono = sessao("bruno", app)
    plano = salvar(dono, "juntar")
    outro = sessao("ana", app)

    assert outro.get(f"/v1/planos/{plano['id']}").status_code == 404
    assert outro.get("/v1/planos").json() == []


def test_saving_a_plano_is_audited() -> None:
    http = sessao()
    salvar(http, "juntar")

    tipos = [e["tipo"] for e in http.get("/v1/auditoria").json()["eventos"]]

    assert tipos[-1] == "plano_salvo"


def test_a_preview_shows_the_plano_without_saving_it() -> None:
    http = sessao()
    simulacao = http.post("/v1/simulacoes", json=CARRO).json()

    previa = http.post(
        "/v1/planos/previa", json={"simulacao_id": simulacao["id"], "caminho": "consorcio"}
    )

    assert previa.status_code == 200
    assert previa.json()["resumo"]["parcela_centavos"] == 195_000
    assert previa.json()["explicacao"]["fontes"]
    assert http.get("/v1/planos").json() == []
