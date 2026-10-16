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

  it('still offers the structured form', async () => {
    fakeApi({ 'GET /api/v1/home': () => json(homeBruno) })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Prefiro preencher os campos' }))

    expect(screen.getByLabelText('Valor do item (R$)')).toBeInTheDocument()
  })
})
