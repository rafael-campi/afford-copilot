from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request

from api.config import Config
from extrato.orcamento import ResumoOrcamento, resumir_orcamento
from mercado import RepositorioSnapshots, SnapshotTaxas
from seed.gerador import ExtratoGerado, gerar_extrato
from seed.personas import PERSONAS, Persona
from simulador import SnapshotMercado


@dataclass
class Contexto:
    """What the routes share: configuration, demo data and in-memory storage.

    Storage is in memory until accounts and Postgres arrive (ticket 12).
    """

    config: Config
    personas: dict[str, Persona] = field(default_factory=lambda: {p.id: p for p in PERSONAS})
    simulacoes: dict[str, tuple[str, Any]] = field(default_factory=dict)

    def persona_da_sessao(self, request: Request) -> str:
        persona_id = request.session.get("persona_id")
        if persona_id not in self.personas:
            raise HTTPException(status_code=401, detail="Entre como uma Persona primeiro.")
        return str(persona_id)

    def mercado(self) -> tuple[SnapshotTaxas, SnapshotMercado]:
        taxas = RepositorioSnapshots(self.config.diretorio_mercado).mais_recente()
        if taxas is None:
            raise HTTPException(
                status_code=503, detail="Dados de mercado indisponíveis. Tente mais tarde."
            )
        idade = (self.config.hoje() - taxas.fim_periodo).days
        return taxas, SnapshotMercado(
            id=taxas.id,
            financiamento_taxa_mensal=taxas.taxa_mediana_mensal,
            tarifas_centavos=self.config.tarifas_centavos,
            desatualizado=idade > self.config.dias_ate_desatualizar,
        )

    def extrato(self, persona_id: str) -> ExtratoGerado:
        return gerar_extrato(persona_id, self.config.seed)

    def orcamento(self, persona_id: str) -> ResumoOrcamento:
        return resumir_orcamento(
            self.extrato(persona_id).transacoes, self.config.margem_segura_percentual
        )
