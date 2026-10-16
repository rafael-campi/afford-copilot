from apoio import config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app
from seed.csv import exportar_csv
from seed.gerador import gerar_extrato

SENHA = "uma senha longa o bastante"
CSV_BRUNO_BANCO = exportar_csv(gerar_extrato("bruno", 2026).transacoes, "banco_tradicional")
CSV_CARLA_DIGITAL = exportar_csv(gerar_extrato("carla", 2026).transacoes, "banco_digital")


def conta() -> TestClient:
    http = TestClient(create_app(config_de_teste()))
    http.post("/v1/contas", json={"nome": "Rafa", "email": "rafa@exemplo.com", "senha": SENHA})
    return http


def enviar(http: TestClient, conteudo: bytes, **mapa: str) -> tuple[int, dict[str, object]]:
    response = http.post("/v1/importacoes", files={"arquivo": ("extrato.csv", conteudo)}, data=mapa)
    corpo: dict[str, object] = response.json()
    return response.status_code, corpo


def confirmar(http: TestClient, confirmacao_id: object) -> None:
    http.post("/v1/sessoes/reautenticar", json={"senha": SENHA})
    assert http.post(f"/v1/confirmacoes/{confirmacao_id}/confirmar").status_code == 200


def test_a_csv_first_asks_which_column_is_which() -> None:
    status, resposta = enviar(conta(), CSV_BRUNO_BANCO)

    assert status == 200
    assert resposta["precisa_mapear"] is True
    assert resposta["colunas"] == ["Data", "Histórico", "Valor"]
    assert resposta["sugestao"] == {"data": "Data", "descricao": "Histórico", "valor": "Valor"}
    amostra = resposta["amostra"]
    assert isinstance(amostra, list)
    assert len(amostra) == 5
    assert amostra[0][0].count("/") == 2


def test_a_mapped_csv_in_brazilian_format_goes_through_preview_and_confirmation() -> None:
    http = conta()

    status, pedido = enviar(
        http,
        CSV_BRUNO_BANCO,
        coluna_data="Data",
        coluna_descricao="Histórico",
        coluna_valor="Valor",
    )
    confirmar(http, pedido["id"])

    assert status == 201
    assert pedido["previa"]["transacoes"] == len(gerar_extrato("bruno", 2026).transacoes)  # type: ignore[index]
    resumo = http.get("/v1/home").json()["resumo"]
    assert resumo["entradas_centavos"] == 680_000
    assert resumo["gastos_centavos"] == 490_000


def test_another_layout_with_iso_dates_and_decimal_points() -> None:
    http = conta()

    _, primeira = enviar(http, CSV_CARLA_DIGITAL)
    sugestao = primeira["sugestao"]
    assert isinstance(sugestao, dict)
    status, pedido = enviar(
        http,
        CSV_CARLA_DIGITAL,
        coluna_data=sugestao["data"],
        coluna_descricao=sugestao["descricao"],
        coluna_valor=sugestao["valor"],
    )
    confirmar(http, pedido["id"])

    assert status == 201
    assert primeira["colunas"] == ["date", "description", "amount"]
    assert http.get("/v1/home").json()["resumo"]["entradas_centavos"] == 650_000


def test_a_mapping_that_points_at_the_wrong_column_is_explained() -> None:
    status, resposta = enviar(
        conta(),
        CSV_BRUNO_BANCO,
        coluna_data="Data",
        coluna_descricao="Valor",
        coluna_valor="Histórico",
    )

    assert status == 422
    assert (
        resposta["detail"] == "Não consegui ler valores na coluna Histórico. Confira o mapeamento."
    )


def test_a_column_that_does_not_exist_is_explained() -> None:
    status, resposta = enviar(
        conta(),
        CSV_BRUNO_BANCO,
        coluna_data="Quando",
        coluna_descricao="Histórico",
        coluna_valor="Valor",
    )

    assert status == 422
    assert resposta["detail"] == "A coluna Quando não existe nesse arquivo."
