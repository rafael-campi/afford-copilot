import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import {
  consorcio48,
  fakeApi,
  homeBruno,
  json,
  juntar35,
  simulacao,
  type RecomendacaoFixture,
} from './test-api'

afterEach(() => {
  vi.unstubAllGlobals()
})

async function preencherObjetivo() {
  await userEvent.click(await screen.findByRole('button', { name: 'Prefiro preencher os campos' }))
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

  it('highlights the Recomendação and says why the others lost', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json(simulacao(72, 199_114, 14_708_518, false), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const juntar = await screen.findByRole('article', { name: /Juntar e comprar à vista/ })
    expect(juntar).toHaveTextContent('Recomendado')
    const financiamento = screen.getByRole('article', { name: 'Financiamento' })
    expect(financiamento).not.toHaveTextContent('Recomendado')
    expect(financiamento).toHaveTextContent('Por que não: Custa R$ 147.085,18 no total')
    expect(screen.getByRole('note', { name: 'Atenção à recomendação' })).toHaveTextContent(
      'passa do que sobra por mês hoje',
    )
  })

  it('suggests adjustments when no Caminho fits', async () => {
    const nenhum: RecomendacaoFixture = {
      caminho: null,
      avaliacoes: [
        { caminho: 'financiamento', motivo_codigo: 'acima_da_margem', motivo_texto: 'A parcela de R$ 1.991,14 passa da sua margem de R$ 1.500,00.' },
        { caminho: 'consorcio', motivo_codigo: 'nao_entrega_no_prazo', motivo_texto: 'Sem lance, a carta pode sair só no mês 72.' },
        { caminho: 'juntar', motivo_codigo: 'nao_entrega_no_prazo', motivo_texto: 'Você só teria o carro no mês 54.' },
      ],
      ressalvas: [],
      ajustes: { entrada_minima_centavos: 1_980_000, prazo_minimo_meses: 54, valor_maximo_centavos: 6_020_000 },
    }
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () =>
        json(simulacao(72, 199_114, 14_708_518, true, consorcio48, juntar35, nenhum), 201),
    })

    render(<App />)
    await preencherObjetivo()

    const painel = await screen.findByRole('region', { name: 'Nenhum caminho cabe hoje' })
    expect(painel).toHaveTextContent('Dar uma Entrada de R$ 19.800')
    expect(painel).toHaveTextContent('Aceitar um Prazo de 54 meses')
    expect(painel).toHaveTextContent('Escolher um carro de até R$ 60.200')
    expect(screen.queryByText('Recomendado')).not.toBeInTheDocument()
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
