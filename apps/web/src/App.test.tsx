import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

const personas = [
  { id: 'ana', nome: 'Ana', perfil: 'Folgada', descricao: 'Salário fixo, gastos bem abaixo da renda.' },
  { id: 'bruno', nome: 'Bruno', perfil: 'No limite', descricao: 'Sobra pouco.' },
]

const homeAna = {
  nome: 'Ana',
  resumo: {
    entradas_centavos: 950_000,
    gastos_centavos: 610_000,
    sobra_mensal_centavos: 340_000,
    margem_segura_centavos: 285_000,
    margem_acima_da_sobra: false,
  },
  sugestoes: [
    { titulo: 'Consórcio ou financiamento?', descricao: 'Compare o custo total para um carro' },
  ],
}

const homeBruno = {
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

type Rota = (init?: RequestInit) => Response

function fakeApi(rotas: Record<string, Rota>) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const chave = `${init?.method ?? 'GET'} ${url}`
    const rota = rotas[chave]
    if (!rota) throw new Error(`Unexpected request: ${chave}`)
    return rota(init)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('asks the visitor to pick a Persona when there is no session', async () => {
    fakeApi({
      'GET /api/v1/home': () => json({ detail: 'Entre como uma Persona primeiro.' }, 401),
      'GET /api/v1/personas': () => json(personas),
    })

    render(<App />)

    expect(await screen.findByRole('button', { name: /Ana.*Folgada/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Bruno.*No limite/ })).toBeInTheDocument()
  })

  it('enters as the chosen Persona and shows her budget', async () => {
    let logado = false
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => (logado ? json(homeAna) : json({}, 401)),
      'GET /api/v1/personas': () => json(personas),
      'POST /api/v1/sessoes/demo': () => {
        logado = true
        return new Response(null, { status: 204 })
      },
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: /Ana.*Folgada/ }))

    expect(await screen.findByText(/R\$\s3\.400/)).toBeInTheDocument()
    expect(screen.getByText('Ana')).toBeInTheDocument()
    expect(screen.getByText(/R\$\s9\.500/)).toBeInTheDocument()
    expect(screen.getByText(/R\$\s6\.100/)).toBeInTheDocument()
    expect(screen.getByText(/R\$\s2\.850/)).toBeInTheDocument()
    expect(screen.getByLabelText('O que você quer conquistar?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Consórcio ou financiamento\?/ })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/sessoes/demo', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ persona_id: 'ana' }),
    }))
  })

  it('warns when the Margem segura is larger than the Sobra mensal', async () => {
    fakeApi({ 'GET /api/v1/home': () => json(homeBruno) })

    render(<App />)

    expect(await screen.findByRole('note')).toHaveTextContent(
      'A margem de R$ 2.040 é maior do que sobra por mês (R$ 1.900)',
    )
  })

  it('does not warn when the Margem segura fits the Sobra mensal', async () => {
    fakeApi({ 'GET /api/v1/home': () => json(homeAna) })

    render(<App />)

    await screen.findByText(/R\$\s3\.400/)
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  it('says when the summary cannot be loaded', async () => {
    fakeApi({ 'GET /api/v1/home': () => new Response('', { status: 503 }) })

    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível carregar seu resumo')
  })
})
