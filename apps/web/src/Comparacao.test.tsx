import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { fakeApi, homeBruno, json } from './test-api'

const consorcio48 = {
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

const juntar35 = {
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

function simulacao(
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
) {
  return {
    consorcio,
    juntar,
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

afterEach(() => {
  vi.unstubAllGlobals()
})

async function preencherObjetivo() {
  await userEvent.click(await screen.findByRole('button', { name: 'Analisar minhas opções' }))
  await userEvent.type(screen.getByLabelText('O que você quer comprar?'), 'carro')
  await userEvent.type(screen.getByLabelText('Valor do item (R$)'), '80.000')
  await userEvent.type(screen.getByLabelText('Prazo para ter o item (meses)'), '60')
  await userEvent.click(screen.getByRole('button', { name: 'Simular' }))
}

describe('Comparação', () => {
  it('simulates financing from the structured Objetivo', async () => {
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json(simulacao(72, 199_114, 14_336_208, false), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const card = await screen.findByRole('article', { name: 'Financiamento' })
    expect(card).toHaveTextContent(/Parcela\s*R\$\s1\.991/)
    expect(card).toHaveTextContent(/Custo total\s*R\$\s143\.362/)
    expect(card).toHaveTextContent(/R\$\s63\.362 só de juros/)
    expect(screen.getByLabelText('Duração')).toHaveValue('72')
    expect(card).not.toHaveTextContent('Acima da margem')
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/simulacoes', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        item: 'carro',
        valor_centavos: 8_000_000,
        prazo_meses: 60,
        entrada_centavos: 0,
      }),
    }))
  })

  it('re-simulates with the Duração the person picks and flags it above the margem', async () => {
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': (init) =>
        JSON.parse(String(init?.body)).duracao_meses === 60
          ? json(simulacao(60, 219_136, 13_148_160, true), 201)
          : json(simulacao(72, 199_114, 14_336_208, false), 201),
    })

    render(<App />)
    await preencherObjetivo()
    await userEvent.selectOptions(await screen.findByLabelText('Duração'), '60')

    const card = await screen.findByRole('article', { name: 'Financiamento' })
    expect(await screen.findByText('Acima da margem')).toBeInTheDocument()
    expect(card).toHaveTextContent(/Parcela\s*R\$\s2\.191/)
    expect(fetchMock).toHaveBeenLastCalledWith('/api/v1/simulacoes', expect.objectContaining({
      body: expect.stringContaining('"duracao_meses":60'),
    }))
  })

  it('shows the Ressalvas, the source period and the institutions ranking', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json(simulacao(72, 199_114, 14_336_208, false), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const card = await screen.findByRole('article', { name: 'Financiamento' })
    expect(card).toHaveTextContent('A sua depende do seu perfil de crédito.')
    expect(card).toHaveTextContent('Fonte: Banco Central do Brasil, 24/09/2026 a 30/09/2026')
    await userEvent.click(screen.getByText('Ver taxas de 2 instituições'))
    expect(screen.getByRole('row', { name: /BCO MERCEDES-BENZ S\.A\.\s*0,55%/ })).toBeVisible()
    expect(screen.getByRole('row', { name: /OMNI SA CFI\s*3,32%/ })).toBeVisible()
  })

  it('shows the estimated CET and what it is made of', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json(simulacao(72, 199_114, 14_708_518, false), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const card = await screen.findByRole('article', { name: 'Financiamento' })
    expect(card).toHaveTextContent('CET estimado: 26,08% ao ano (1,95% ao mês)')
    expect(screen.getByRole('row', { name: /Juros\s*R\$\s67\.085/ })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /IOF\s*R\$\s2\.673/ })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Tarifas\s*R\$\s1\.050/ })).toBeInTheDocument()
  })

  it('shows the Consórcio with its Janela de contemplação', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json(simulacao(72, 199_114, 14_708_518, false), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const card = await screen.findByRole('article', { name: 'Consórcio' })
    expect(card).toHaveTextContent(/Parcela\s*R\$\s1\.950/)
    expect(card).toHaveTextContent(/Custo total\s*R\$\s97\.956/)
    expect(card).toHaveTextContent('mês 1 com lance')
    expect(card).toHaveTextContent('mês 25 na mediana')
    expect(card).toHaveTextContent('até o mês 48')
    expect(card).toHaveTextContent('100% de chance de sair por sorteio até o seu Prazo')
    expect(card).toHaveTextContent('Taxa de administração de 15,00%, fundo de reserva de 2,00%')
    expect(card).toHaveTextContent('Sem lance, você pode receber a carta só no mês 48.')
  })

  it('re-simulates the Consórcio with another group Duração', async () => {
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json(simulacao(72, 199_114, 14_708_518, false), 201),
    })

    render(<App />)
    await preencherObjetivo()
    await userEvent.selectOptions(await screen.findByLabelText('Duração do grupo'), '60')

    expect(fetchMock).toHaveBeenLastCalledWith('/api/v1/simulacoes', expect.objectContaining({
      body: expect.stringContaining('"consorcio_duracao_meses":60'),
    }))
  })

  it('shows saving the Margem segura until buying in cash', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json(simulacao(72, 199_114, 14_708_518, false), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const card = await screen.findByRole('article', { name: 'Juntar e comprar à vista' })
    expect(card).toHaveTextContent(/Por mês\s*R\$\s2\.040/)
    expect(card).toHaveTextContent(/Custo total\s*R\$\s71\.400/)
    expect(card).toHaveTextContent(/Item em mãos\s*mês 35/)
    expect(card).toHaveTextContent('O carro deve custar R$ 91.900 quando você comprar.')
    expect(card).toHaveTextContent('rendimento de referência de 13,00% ao ano e IPCA de 5,00%')
    expect(card).toHaveTextContent('Fonte: pesquisa Focus do Banco Central de 09/10/2026')
    expect(card).toHaveTextContent('Não é promessa de rendimento nem recomendação de investimento.')
    expect(card).not.toHaveTextContent('Depois do Prazo')
  })

  it('flags saving that ends after the Prazo or never reaches the price', async () => {
    const depois = { ...juntar35, mes_compra: 70, custo_total_centavos: 14_280_000, entrega_ate_prazo: false }
    const nunca = { ...juntar35, mes_compra: null, custo_total_centavos: null, preco_na_compra_centavos: null, entrega_ate_prazo: false }
    let chamada = 0
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () =>
        json(simulacao(72, 199_114, 14_708_518, false, consorcio48, chamada++ === 0 ? depois : nunca), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const card = await screen.findByRole('article', { name: 'Juntar e comprar à vista' })
    expect(card).toHaveTextContent('Depois do Prazo')
    await userEvent.selectOptions(screen.getByLabelText('Duração'), '60')
    expect(await screen.findByText('Não alcança o preço em 20 anos')).toBeInTheDocument()
  })

  it('explains when the API rejects the Objetivo', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json({ detail: 'inválido' }, 422),
    })

    render(<App />)
    await preencherObjetivo()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Confira os valores: a Entrada precisa ser menor do que o valor do item.',
    )
  })
})
