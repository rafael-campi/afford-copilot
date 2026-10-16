from datetime import UTC, datetime, timedelta

from apoio import config_de_teste
from fastapi.testclient import TestClient

from api.main import create_app
from seed.gerador import gerar_extrato
from seed.ofx import exportar_ofx

SENHA = "uma senha longa o bastante"
OFX_BRUNO = exportar_ofx(gerar_extrato("bruno", 2026).transacoes)

OFX_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<?OFX OFXHEADER="200" VERSION="211"?>
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN><TRNTYPE>CREDIT</TRNTYPE><DTPOSTED>20260705120000[-3:BRT]</DTPOSTED>
<TRNAMT>5000.00</TRNAMT><MEMO>CRED SALARIO EMPRESA</MEMO></STMTTRN>
<STMTTRN><TRNTYPE>DEBIT</TRNTYPE><DTPOSTED>20260710</DTPOSTED>
<TRNAMT>-1500.00</TRNAMT><MEMO>PAG BOLETO ALUGUEL</MEMO></STMTTRN>
<STMTTRN><TRNTYPE>CREDIT</TRNTYPE><DTPOSTED>20260905</DTPOSTED>
<TRNAMT>5000.00</TRNAMT><MEMO>CRED SALARIO EMPRESA</MEMO></STMTTRN>
<STMTTRN><TRNTYPE>DEBIT</TRNTYPE><DTPOSTED>20260910</DTPOSTED>
<TRNAMT>-1500.00</TRNAMT><MEMO>PAG BOLETO ALUGUEL</MEMO></STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""


class Relogio:
    def __init__(self) -> None:
        self.agora = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.agora


def conta(relogio: Relogio | None = None) -> TestClient:
    config = config_de_teste(agora=relogio) if relogio else config_de_teste()
    http = TestClient(create_app(config))
    http.post("/v1/contas", json={"nome": "Rafa", "email": "rafa@exemplo.com", "senha": SENHA})
    return http


def enviar(http: TestClient, conteudo: bytes, nome: str = "extrato.ofx") -> dict[str, object]:
    response = http.post("/v1/importacoes", files={"arquivo": (nome, conteudo)})
    resposta: dict[str, object] = {"status": response.status_code, **response.json()}
    return resposta


def confirmar(http: TestClient, confirmacao_id: object) -> None:
    http.post("/v1/sessoes/reautenticar", json={"senha": SENHA})
    assert http.post(f"/v1/confirmacoes/{confirmacao_id}/confirmar").status_code == 200


def test_an_imported_ofx_is_previewed_and_only_used_after_confirmation() -> None:
    http = conta()

    pedido = enviar(http, OFX_BRUNO)
    antes = http.get("/v1/home").status_code
    confirmar(http, pedido["id"])

    assert pedido["status"] == 201
    assert pedido["acao"] == "importar_extrato"
    previa = pedido["previa"]
    assert isinstance(previa, dict)
    assert previa["transacoes"] == len(gerar_extrato("bruno", 2026).transacoes)
    datas = [t.data for t in gerar_extrato("bruno", 2026).transacoes]
    assert (previa["inicio"], previa["fim"]) == (min(datas).isoformat(), max(datas).isoformat())
    assert len(previa["exemplos"]) == 10
    assert antes == 409
    home = http.get("/v1/home").json()
    assert home["nome"] == "Rafa"
    assert home["resumo"]["entradas_centavos"] == 680_000
    assert home["resumo"]["gastos_centavos"] == 490_000


def test_ofx_2_xml_files_are_read_too() -> None:
    http = conta()

    pedido = enviar(http, OFX_XML)
    confirmar(http, pedido["id"])

    resumo = http.get("/v1/home").json()["resumo"]
    assert pedido["previa"]["transacoes"] == 4  # type: ignore[index]
    assert resumo["entradas_centavos"] == 500_000
    assert resumo["gastos_centavos"] == 150_000


def test_a_file_without_transactions_is_explained() -> None:
    resposta = enviar(conta(), b"isto nao e um extrato")

    assert resposta["status"] == 422
    assert resposta["detail"] == (
        "Não encontrei transações nesse arquivo. Exporte o extrato em OFX pelo app do seu banco."
    )


def test_a_file_that_is_too_large_is_refused() -> None:
    resposta = enviar(conta(), b"x" * (2 * 1024 * 1024 + 1))

    assert resposta["status"] == 413
    assert resposta["detail"] == "O arquivo passa de 2 MB. Exporte só os últimos meses."


def test_a_period_shorter_than_a_month_is_refused() -> None:
    um_mes = [t for t in gerar_extrato("bruno", 2026).transacoes if t.data.month == 7][:5]

    resposta = enviar(conta(), exportar_ofx(um_mes))

    assert resposta["status"] == 422
    assert str(resposta["detail"]).startswith("O extrato cobre só ")


def test_the_uploaded_file_is_never_kept_and_imports_vanish_after_24_hours() -> None:
    relogio = Relogio()
    http = conta(relogio)
    pedido = enviar(http, OFX_BRUNO)
    confirmar(http, pedido["id"])

    relogio.agora += timedelta(hours=25)
    response = http.get("/v1/home")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "O extrato importado foi apagado depois de 24 horas. Importe de novo."
    )
    assert http.get("/v1/importacoes").json() == []


def test_the_newest_source_wins_over_a_consentimento() -> None:
    from apoio import conceder_consentimento

    http = conta()
    conceder_consentimento(http, "ana", senha=SENHA)
    pedido = enviar(http, OFX_BRUNO)
    confirmar(http, pedido["id"])

    assert http.get("/v1/home").json()["resumo"]["entradas_centavos"] == 680_000


def test_importing_is_audited() -> None:
    http = conta()
    pedido = enviar(http, OFX_BRUNO)
    confirmar(http, pedido["id"])

    tipos = [e["tipo"] for e in http.get("/v1/auditoria").json()["eventos"]]

    assert tipos == [
        "cadastro",
        "ferramenta:solicitar_confirmacao",
        "reautenticacao",
        "importacao_confirmada",
    ]


def test_a_personas_sample_ofx_can_be_downloaded_and_imported() -> None:
    http = conta()

    arquivo = http.get("/v1/exemplos/diego.ofx")
    pedido = enviar(http, arquivo.content)
    confirmar(http, pedido["id"])

    assert arquivo.headers["content-type"] == "application/x-ofx"
    assert http.get("/v1/home").json()["resumo"]["entradas_centavos"] == 520_000
