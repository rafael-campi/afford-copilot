import pytest
from apoio import CategorizadorPerfeito, config_de_teste, entrar_como
from fastapi.testclient import TestClient

from api.main import create_app
from seed.gerador import gerar_extrato


def sessao(persona_id: str, seed: int = 2026, llm: object | None = None) -> TestClient:
    mudancas: dict[str, object] = {"seed": seed}
    if llm is not None:
        mudancas["llm"] = llm
    http = TestClient(create_app(config_de_teste(**mudancas)))
    entrar_como(http, persona_id)
    return http


def extrato_de(
    persona_id: str, seed: int = 2026, llm: object | None = None
) -> list[dict[str, object]]:
    response = sessao(persona_id, seed, llm).get("/v1/extrato")
    assert response.status_code == 200
    transacoes: list[dict[str, object]] = response.json()["transacoes"]
    return transacoes


@pytest.mark.parametrize("persona_id", ["ana", "bruno", "carla", "diego"])
def test_rules_and_the_model_together_match_the_answer_key(persona_id: str) -> None:
    gabarito = gerar_extrato(persona_id, 2026).gabarito

    categorias = [t["categoria"] for t in extrato_de(persona_id, llm=CategorizadorPerfeito())]

    assert categorias == gabarito


def test_the_model_only_sees_what_the_rules_could_not_place() -> None:
    llm = CategorizadorPerfeito()

    transacoes = extrato_de("ana", llm=llm)

    fontes = {str(t["descricao"]): t["categoria_fonte"] for t in transacoes}
    assert fontes["NETFLIX.COM"] == "regra"
    assert any(f == "llm" for f in fontes.values())
    enviados = llm.textos[0]
    assert "NETFLIX" not in enviados
    assert "CRED SALARIO" not in enviados


def test_without_the_model_unknown_merchants_stay_in_outros() -> None:
    transacoes = extrato_de("ana")

    desconhecidos = [t for t in transacoes if "BAR DO ZE" in str(t["descricao"])]
    assert desconhecidos
    assert {(t["categoria"], t["categoria_fonte"]) for t in desconhecidos} == {("Outros", "regra")}


def test_names_in_transfers_are_masked_before_the_model() -> None:
    llm = CategorizadorPerfeito()

    extrato_de("bruno", llm=llm)

    enviados = llm.textos[0]
    assert "PIX ENVIADO [NOME]" in enviados
    for nome in ["JOAO", "MARIA", "PEDRO"]:
        assert nome not in enviados


def test_the_model_categorizes_a_personas_extrato_only_once() -> None:
    llm = CategorizadorPerfeito()
    http = sessao("ana", llm=llm)

    http.get("/v1/extrato")
    http.get("/v1/extrato")
    http.get("/v1/home")

    assert len(llm.textos) == 1


def test_home_shows_monthly_spending_by_category() -> None:
    http = sessao("bruno", llm=CategorizadorPerfeito())

    home = http.get("/v1/home").json()

    gastos = home["gastos_por_categoria"]
    assert gastos[0] == {"categoria": "Moradia", "centavos": 200_000}
    assert {g["categoria"]: g["centavos"] for g in gastos}["Delivery"] == 62_000
    assert sum(g["centavos"] for g in gastos) == home["resumo"]["gastos_centavos"]


def test_transfers_to_people_fall_into_outros() -> None:
    pix = [t for t in extrato_de("bruno") if str(t["descricao"]).startswith("PIX ENVIADO")]

    assert pix
    assert {t["categoria"] for t in pix} == {"Outros"}


def test_the_same_seed_always_generates_the_same_extrato() -> None:
    assert extrato_de("carla", seed=7) == extrato_de("carla", seed=7)


def test_another_seed_changes_the_transactions_but_not_the_budget() -> None:
    assert extrato_de("carla", seed=7) != extrato_de("carla", seed=8)
    assert (
        sessao("carla", seed=7).get("/v1/home").json()["resumo"]
        == sessao("carla", seed=8).get("/v1/home").json()["resumo"]
    )
