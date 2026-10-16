import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { fakeApi, homeBruno, json, simulacao } from './test-api'

afterEach(() => {
  vi.unstubAllGlobals()
})

const objetivoCompleto = { item: 'carro', valor_centavos: 8_000_000, prazo_meses: 60, entrada_centavos: 0 }

async function pedir(texto: string) {
  const campo = await screen.findByLabelText('O que você quer conquistar?')
  await userEvent.type(campo, texto)
  await userEvent.click(screen.getByRole('button', { name: 'Analisar minhas opções' }))
}

describe('Conversa', () => {
  it('sends the Objetivo typed on the Home and shows what the copilot understood', async () => {
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/conversas': () => json({ id: 'c1' }, 201),
      'POST /api/v1/conversas/c1/mensagens': () =>
        json({
          resposta: 'Olhei seus gastos e comparei os três caminhos.',
          objetivo: objetivoCompleto,
          faltando: [],
          simulacao: simulacao(72, 199_114, 14_708_518, false),
        }),
    })

    render(<App />)
    await pedir('Quero um carro de 80 mil em até 5 anos')

    expect(await screen.findByText('Quero um carro de 80 mil em até 5 anos')).toBeInTheDocument()
    const entendi = screen.getByRole('list', { name: 'O que entendi' })
    expect(entendi).toHaveTextContent('carro')
    expect(entendi).toHaveTextContent(/R\$\s80\.000/)
    expect(entendi).toHaveTextContent('até 60 meses')
    expect(entendi).toHaveTextContent('sem Entrada')
    expect(screen.getByText('Olhei seus gastos e comparei os três caminhos.')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/conversas/c1/mensagens', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ texto: 'Quero um carro de 80 mil em até 5 anos' }),
    }))

    await userEvent.click(screen.getByRole('button', { name: 'Comparar as 3 opções' }))
    expect(await screen.findByRole('article', { name: 'Financiamento' })).toBeInTheDocument()
  })

  it('asks for what is missing and answers in the same conversation', async () => {
    let chamada = 0
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/conversas': () => json({ id: 'c1' }, 201),
      'POST /api/v1/conversas/c1/mensagens': () =>
        chamada++ === 0
          ? json({
              resposta: 'Até quando você quer ter o carro?',
              objetivo: { ...objetivoCompleto, prazo_meses: null },
              faltando: ['prazo'],
              simulacao: null,
            })
          : json({
              resposta: 'Olhei seus gastos e comparei os três caminhos.',
              objetivo: objetivoCompleto,
              faltando: [],
              simulacao: simulacao(72, 199_114, 14_708_518, false),
            }),
    })

    render(<App />)
    await pedir('Quero um carro de 80 mil')

    expect(await screen.findByText('Até quando você quer ter o carro?')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Comparar as 3 opções' })).not.toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Mensagem'), 'em 5 anos')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByRole('button', { name: 'Comparar as 3 opções' })).toBeInTheDocument()
    expect(screen.getByText('em 5 anos')).toBeInTheDocument()
  })

  it('keeps earlier scenarios to compare and opens any of them', async () => {
    const primeira = { ...simulacao(72, 199_114, 14_708_518, false), id: 's1' }
    const comEntrada = {
      ...simulacao(54, 203_755, 12_002_770, false),
      id: 's2',
      objetivo: { ...objetivoCompleto, entrada_centavos: 1_000_000 },
    }
    let chamada = 0
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/conversas': () => json({ id: 'c1' }, 201),
      'POST /api/v1/conversas/c1/mensagens': () =>
        chamada++ === 0
          ? json({ resposta: 'Recomendo juntar.', objetivo: objetivoCompleto, faltando: [], novo_objetivo: false, simulacao: primeira })
          : json({
              resposta: 'Com a Entrada, recomendo juntar.',
              objetivo: { ...objetivoCompleto, entrada_centavos: 1_000_000 },
              faltando: [],
              novo_objetivo: false,
              simulacao: comEntrada,
            }),
    })

    render(<App />)
    await pedir('Quero um carro de 80 mil em até 5 anos')
    await screen.findByText('Recomendo juntar.')
    await userEvent.type(screen.getByLabelText('Mensagem'), 'E se eu der 10 mil de entrada?')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar' }))

    const cenarios = await screen.findByRole('list', { name: 'Cenários desta conversa' })
    expect(cenarios).toHaveTextContent('Cenário 1: sem Entrada · recomendado: juntar')
    expect(cenarios).toHaveTextContent(/Cenário 2: Entrada de R\$\s10\.000 · recomendado: juntar/)
    await userEvent.click(screen.getByRole('button', { name: 'Ver cenário 1' }))
    const card = await screen.findByRole('article', { name: 'Financiamento' })
    expect(card).toHaveTextContent(/Parcela\s*R\$\s1\.991/)
  })

  it('says when a new Objetivo starts and clears the earlier scenarios', async () => {
    let chamada = 0
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/conversas': () => json({ id: 'c1' }, 201),
      'POST /api/v1/conversas/c1/mensagens': () =>
        chamada++ === 0
          ? json({ resposta: 'Recomendo juntar.', objetivo: objetivoCompleto, faltando: [], novo_objetivo: false, simulacao: simulacao(72, 199_114, 14_708_518, false) })
          : json({
              resposta: 'Até quando você quer ter a moto?',
              objetivo: { item: 'moto', valor_centavos: 2_000_000, prazo_meses: null, entrada_centavos: 0 },
              faltando: ['prazo'],
              novo_objetivo: true,
              simulacao: null,
            }),
    })

    render(<App />)
    await pedir('Quero um carro de 80 mil em até 5 anos')
    await screen.findByText('Recomendo juntar.')
    await userEvent.type(screen.getByLabelText('Mensagem'), 'Quero uma moto de 20 mil')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Novo objetivo: moto. Os cenários do carro ficaram para trás.')).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: 'Cenários desta conversa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Comparar as 3 opções' })).not.toBeInTheDocument()
  })

  it('shows where the money goes and the Margem segura', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/conversas': () => json({ id: 'c1' }, 201),
      'POST /api/v1/conversas/c1/mensagens': () =>
        json({ resposta: 'Recomendo juntar.', objetivo: objetivoCompleto, faltando: [], novo_objetivo: false, simulacao: simulacao(72, 199_114, 14_708_518, false) }),
    })

    render(<App />)
    await pedir('Quero um carro de 80 mil em até 5 anos')

    const gastos = await screen.findByRole('list', { name: 'Para onde vai seu dinheiro' })
    expect(gastos).toHaveTextContent(/Moradia\s*R\$\s2\.000/)
    expect(gastos).toHaveTextContent(/Mercado\s*R\$\s1\.100/)
    expect(gastos).toHaveTextContent(/Delivery\s*R\$\s620/)
    // Everything after the top three is grouped: 400 + 380 + 250 + 150.
    expect(gastos).toHaveTextContent(/Outros\s*R\$\s1\.180/)
    expect(screen.getByText(/Sobram cerca de R\$\s1\.900\/mês\. Sua margem segura é de até R\$\s2\.040/)).toBeInTheDocument()
  })

  it('shows rule answers with their official sources', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/conversas': () => json({ id: 'c1' }, 201),
      'POST /api/v1/conversas/c1/mensagens': () =>
        json({
          resposta: 'A contemplação acontece por sorteio ou por lance.',
          objetivo: { item: null, valor_centavos: null, prazo_meses: null, entrada_centavos: 0 },
          faltando: ['item', 'valor', 'prazo'],
          novo_objetivo: false,
          simulacao: null,
          citacoes: [
            {
              documento: 'Lei nº 11.795/2008 (Sistema de Consórcio)',
              rotulo: 'Art. 22',
              url: 'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11795.htm',
              versao: '8fd6197bc518',
              capturado_em: '2026-10-15',
              trecho: 'Art. 22. A contemplação é a atribuição ao consorciado do crédito...',
            },
          ],
        }),
    })

    render(<App />)
    await pedir('Como funciona o lance?')

    await screen.findByText('A contemplação acontece por sorteio ou por lance.')
    const fonte = screen.getByRole('link', { name: 'Lei nº 11.795/2008 (Sistema de Consórcio), Art. 22' })
    expect(fonte).toHaveAttribute('href', 'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11795.htm')
    await userEvent.click(screen.getByText('Ver trecho'))
    expect(screen.getByText(/A contemplação é a atribuição ao consorciado/)).toBeVisible()
    expect(screen.getByText('Versão consultada em 15/10/2026')).toBeInTheDocument()
  })

  it('still offers the structured form', async () => {
    fakeApi({ 'GET /api/v1/home': () => json(homeBruno) })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Prefiro preencher os campos' }))

    expect(screen.getByLabelText('Valor do item (R$)')).toBeInTheDocument()
  })
})
