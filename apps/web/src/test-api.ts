import { vi } from 'vitest'

export type Rota = (init?: RequestInit) => Response

export function fakeApi(rotas: Record<string, Rota>) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const chave = `${init?.method ?? 'GET'} ${url}`
    const rota = rotas[chave]
    if (!rota) throw new Error(`Unexpected request: ${chave}`)
    return rota(init)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status })

export const homeBruno = {
  nome: 'Bruno',
  resumo: {
    entradas_centavos: 680_000,
    gastos_centavos: 490_000,
    sobra_mensal_centavos: 190_000,
    margem_segura_centavos: 204_000,
    margem_acima_da_sobra: true,
  },
  sugestoes: [],
}

export const consorcio48 = {
  carta_credito_centavos: 8_000_000,
  duracao_meses: 48,
  parcela_centavos: 195_000,
  custo_total_centavos: 9_795_600,
  taxa_administracao_centavos: 1_200_000,
  taxa_administracao_percentual: '15.00',
  fundo_reserva_centavos: 160_000,
  fundo_reserva_percentual: '2.00',
  reajuste_anual_percentual: '4.50',
  acima_da_margem: false,
  janela: { melhor_caso_mes: 1, mediana_mes: 25, pior_caso_mes: 48, chance_ate_prazo_percentual: 100 },
  duracoes_disponiveis: [36, 48, 60],
  ressalvas: [
    {
      codigo: 'contemplacao_incerta',
      texto: 'Sem lance, você pode receber a carta só no mês 48.',
    },
  ],
}

export const juntar35 = {
  deposito_mensal_centavos: 204_000,
  mes_compra: 35,
  custo_total_centavos: 7_140_000,
  preco_na_compra_centavos: 9_190_000,
  entrega_ate_prazo: true,
  rendimento_anual_percentual: '13.00',
  ipca_anual_percentual: '5.00',
  fonte: {
    descricao: 'Banco Central do Brasil: pesquisa Focus (medianas)',
    data_pesquisa: '2026-10-09',
    url: 'https://www.bcb.gov.br/publicacoes/focus',
  },
  ressalvas: [
    { codigo: 'rendimento_de_referencia', texto: 'Não é promessa de rendimento nem recomendação de investimento.' },
  ],
}

export type RecomendacaoFixture = {
  caminho: string | null
  avaliacoes: { caminho: string; motivo_codigo: string | null; motivo_texto: string | null }[]
  ressalvas: { codigo: string; texto: string }[]
  ajustes: {
    entrada_minima_centavos: number | null
    prazo_minimo_meses: number | null
    valor_maximo_centavos: number | null
  } | null
}

export const recomendaJuntar: RecomendacaoFixture = {
  caminho: 'juntar',
  avaliacoes: [
    { caminho: 'financiamento', motivo_codigo: 'custo_maior', motivo_texto: 'Custa R$ 147.085,18 no total, mais do que R$ 71.400,00.' },
    { caminho: 'consorcio', motivo_codigo: 'custo_maior', motivo_texto: 'Custa R$ 97.956,00 no total, mais do que R$ 71.400,00.' },
    { caminho: 'juntar', motivo_codigo: null, motivo_texto: null },
  ],
  ressalvas: [
    { codigo: 'acima_da_sobra', texto: 'A parcela de R$ 2.040,00 cabe na margem, mas passa do que sobra por mês hoje (R$ 1.900,00).' },
  ],
  ajustes: null,
}

export function simulacao(
  duracao: number,
  parcela: number,
  total: number,
  acima: boolean,
  consorcio: typeof consorcio48 = consorcio48,
  juntar: Omit<typeof juntar35, 'mes_compra' | 'custo_total_centavos' | 'preco_na_compra_centavos'> & {
    mes_compra: number | null
    custo_total_centavos: number | null
    preco_na_compra_centavos: number | null
  } = juntar35,
  recomendacao: RecomendacaoFixture = recomendaJuntar,
) {
  return {
    consorcio,
    juntar,
    recomendacao,
    id: `sim-${duracao}`,
    snapshot_id: 'config-taxa-fixa-2026-10',
    objetivo: { item: 'carro', valor_centavos: 8_000_000, prazo_meses: 60, entrada_centavos: 0 },
    financiamento: {
      duracao_meses: duracao,
      parcela_centavos: parcela,
      custo_total_centavos: total,
      juros_centavos: total - 8_000_000,
      iof_centavos: 267_310,
      tarifas_centavos: 105_000,
      cet_mensal_percentual: '1.95',
      cet_anual_percentual: '26.08',
      taxa_mensal: '0.018',
      acima_da_margem: acima,
      duracoes_disponiveis: [48, 60, 72],
      ranking: [
        { instituicao: 'BCO MERCEDES-BENZ S.A.', taxa_mensal_percentual: '0.55', taxa_anual_percentual: '6.85' },
        { instituicao: 'OMNI SA CFI', taxa_mensal_percentual: '3.32', taxa_anual_percentual: '48.0' },
      ],
      fonte: {
        descricao: 'Banco Central do Brasil: taxas médias de aquisição de veículos (pessoa física)',
        inicio_periodo: '2026-09-24',
        fim_periodo: '2026-09-30',
        url: 'https://www.bcb.gov.br/estatisticas/txjuros',
      },
      ressalvas: [
        {
          codigo: 'taxa_media',
          texto: 'A taxa é a média que as instituições informaram ao Banco Central. A sua depende do seu perfil de crédito.',
        },
      ],
    },
  }
}

