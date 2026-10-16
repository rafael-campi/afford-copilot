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

  it('still offers the structured form', async () => {
    fakeApi({ 'GET /api/v1/home': () => json(homeBruno) })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Prefiro preencher os campos' }))

    expect(screen.getByLabelText('Valor do item (R$)')).toBeInTheDocument()
  })
})
