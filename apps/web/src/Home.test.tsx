import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Home } from './Home'

const homeResponse = {
  placeholder: true,
  nome: 'Rafael',
  resumo: {
    entradas_centavos: 680_000,
    gastos_centavos: 490_000,
    sobra_mensal_centavos: 190_000,
    margem_segura_centavos: 204_000,
  },
  sugestoes: [
    { titulo: 'Consórcio ou financiamento?', descricao: 'Compare o custo total para um carro' },
  ],
}

function mockFetch(response: Response) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Home', () => {
  it('shows the budget summary fetched from the API', async () => {
    mockFetch(new Response(JSON.stringify(homeResponse)))

    render(<Home />)

    expect(await screen.findByText(/R\$\s1\.900/)).toBeInTheDocument()
    expect(screen.getByText('Rafael')).toBeInTheDocument()
    expect(screen.getByText(/R\$\s6\.800/)).toBeInTheDocument()
    expect(screen.getByText(/R\$\s4\.900/)).toBeInTheDocument()
    expect(screen.getByText(/R\$\s2\.040/)).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith('/api/v1/home')
  })

  it('offers the Objetivo input and the suggestions', async () => {
    mockFetch(new Response(JSON.stringify(homeResponse)))

    render(<Home />)

    expect(await screen.findByLabelText('O que você quer conquistar?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Consórcio ou financiamento\?/ })).toBeInTheDocument()
  })

  it('says when the summary cannot be loaded', async () => {
    mockFetch(new Response('', { status: 503 }))

    render(<Home />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Não foi possível carregar seu resumo',
    )
  })
})
