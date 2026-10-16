"""Seeded generator of synthetic Extratos.

Each Persona has a fixed monthly profile (amount per category per month). The seed only
decides how each amount is split into transactions, on which days, and with which
realistic description, so the budget is known in advance and independent of the seed.
"""

import random
from dataclasses import dataclass
from datetime import date

from extrato.orcamento import TransacaoBruta

MESES: tuple[tuple[int, int], ...] = ((2026, 7), (2026, 8), (2026, 9))


@dataclass(frozen=True)
class Linha:
    categoria: str
    reais_por_mes: tuple[int, int, int]
    descricoes: tuple[str, ...]
    transacoes_por_mes: int = 1
    dia: int | None = None
    credito: bool = False


def fixo(reais: int) -> tuple[int, int, int]:
    return (reais, reais, reais)


MERCADO = (
    "COMPRA CARTAO CARREFOUR {n}",
    "PAG*ASSAI ATACADISTA",
    "PAO DE ACUCAR {n}",
    "HORTIFRUTI BOA VISTA",
)
DELIVERY = ("PAG*IFOOD", "IFD*IFOOD.COM AGENCIA", "RAPPI*BRASIL", "ZE DELIVERY BEBIDAS")
TRANSPORTE = ("UBER *TRIP", "99APP *CORRIDA", "POSTO SHELL {n}", "IPIRANGA POSTO {n}")
CONTAS = ("DEB AUT ENEL SP", "SABESP DEB AUT", "VIVO FIBRA", "CLARO CELULAR")
SAUDE = ("DROGASIL {n}", "RAIA DROGASIL {n}", "CLINICA SORRISO {n}")
LAZER = ("INGRESSO.COM", "CINEMARK {n}", "SYMPLA*EVENTO", "BAR DO ZE")
ASSINATURAS = ("NETFLIX.COM", "SPOTIFY", "AMAZON PRIME BR")
PIX_PESSOAS = ("PIX ENVIADO JOAO S", "PIX ENVIADO MARIA F", "PIX ENVIADO PEDRO L")

PERFIS: dict[str, tuple[Linha, ...]] = {
    "ana": (
        Linha("Renda", fixo(9_500), ("CRED SALARIO ORBITA SOFTWARE LTDA",), dia=5, credito=True),
        Linha("Moradia", fixo(2_400), ("PAG BOLETO IMOBILIARIA LAR IDEAL",), dia=10),
        Linha("Mercado", fixo(1_300), MERCADO, 6),
        Linha("Delivery", fixo(600), DELIVERY, 5),
        Linha("Transporte", fixo(500), TRANSPORTE, 6),
        Linha("Contas da casa", fixo(450), CONTAS, 4),
        Linha("Saúde", fixo(350), SAUDE, 2),
        Linha("Lazer", fixo(400), LAZER, 3),
        Linha("Assinaturas", fixo(100), ASSINATURAS, 2),
    ),
    "bruno": (
        Linha("Renda", fixo(6_800), ("CRED SALARIO VERDEMAR COMERCIO SA",), dia=5, credito=True),
        Linha("Moradia", fixo(2_000), ("PAG BOLETO ALUGUEL RESIDENCIAL",), dia=10),
        Linha("Mercado", fixo(1_100), MERCADO, 5),
        Linha("Delivery", fixo(620), DELIVERY, 6),
        Linha("Transporte", fixo(400), TRANSPORTE, 5),
        Linha("Contas da casa", fixo(380), CONTAS, 4),
        Linha("Lazer", fixo(250), LAZER, 2),
        Linha("Outros", fixo(150), PIX_PESSOAS, 2),
    ),
    "carla": (
        Linha(
            "Renda",
            (4_800, 8_400, 6_300),
            ("PIX RECEBIDO STUDIO ALFA LTDA", "PIX RECEBIDO AGENCIA NORTE ME"),
            2,
            credito=True,
        ),
        Linha("Moradia", fixo(1_800), ("PAG BOLETO CONDOMINIO ED AURORA",), dia=8),
        Linha("Mercado", fixo(900), MERCADO, 4),
        Linha("Delivery", fixo(300), DELIVERY, 3),
        Linha("Transporte", fixo(350), TRANSPORTE, 4),
        Linha("Contas da casa", fixo(400), CONTAS, 4),
        Linha("Saúde", fixo(250), SAUDE, 2),
        Linha("Lazer", fixo(225), LAZER, 2),
        Linha("Impostos e taxas", fixo(75), ("DAS SIMPLES NACIONAL",), dia=20),
    ),
    "diego": (
        Linha("Renda", fixo(5_200), ("CRED SALARIO LOGIX TRANSPORTES LTDA",), dia=5, credito=True),
        Linha("Dívidas", fixo(1_100), ("PARCELA EMPRESTIMO PESSOAL",), dia=12),
        Linha("Dívidas", fixo(180), ("JUROS ROTATIVO CARTAO",), dia=15),
        Linha("Moradia", fixo(1_500), ("PAG BOLETO ALUGUEL RESIDENCIAL",), dia=10),
        Linha("Mercado", fixo(950), MERCADO, 5),
        Linha("Delivery", fixo(250), DELIVERY, 3),
        Linha("Transporte", fixo(450), TRANSPORTE, 5),
        Linha("Contas da casa", fixo(320), CONTAS, 3),
        Linha("Outros", fixo(150), PIX_PESSOAS, 2),
    ),
}


@dataclass(frozen=True)
class ExtratoGerado:
    transacoes: list[TransacaoBruta]
    gabarito: list[str]
    """Expected category of each transaction, by position. For evals only, never for the
    product at runtime."""


def _dividir(total_centavos: int, partes: int, rng: random.Random) -> list[int]:
    if partes == 1:
        return [total_centavos]
    pesos = [rng.uniform(0.5, 1.5) for _ in range(partes)]
    soma = sum(pesos)
    valores = [int(total_centavos * p / soma) for p in pesos]
    valores[-1] += total_centavos - sum(valores)
    return valores


def gerar_extrato(persona_id: str, seed: int) -> ExtratoGerado:
    rng = random.Random(f"{seed}:{persona_id}")
    linhas: list[tuple[TransacaoBruta, str]] = []
    for indice_mes, (ano, mes) in enumerate(MESES):
        for linha in PERFIS[persona_id]:
            total = linha.reais_por_mes[indice_mes] * 100
            for valor in _dividir(total, linha.transacoes_por_mes, rng):
                dia = linha.dia or rng.randint(1, 28)
                descricao = rng.choice(linha.descricoes).format(n=rng.randint(100, 9999))
                transacao = TransacaoBruta(
                    data=date(ano, mes, dia),
                    descricao=descricao,
                    valor_centavos=valor if linha.credito else -valor,
                )
                linhas.append((transacao, linha.categoria))
    linhas.sort(key=lambda par: (par[0].data, par[0].descricao))
    return ExtratoGerado(
        transacoes=[t for t, _ in linhas],
        gabarito=[categoria for _, categoria in linhas],
    )
