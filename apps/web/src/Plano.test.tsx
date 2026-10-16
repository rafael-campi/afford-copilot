import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { fakeApi, homeBruno, json, simulacao } from './test-api'

const plano = {
  id: '',
  caminho: 'consorcio',
  criado_em: '2026-10-15',
  resumo: {
    item: 'carro',
    valor_centavos: 8_000_000,
    parcela_centavos: 195_000,
    duracao_meses: 48,
    custo_total_centavos: 9_795_600,
    item_em_maos: 'entre o mês 1 e o mês 48',
  },
  ressalvas: [{ codigo: 'contemplacao_incerta', texto: 'Sem lance, você pode receber a carta só no mês 48.' }],
  explicacao: {
    texto: 'Se você sair do grupo antes de ser contemplado, só recebe de volta o que pagou quando for sorteado.',
    fontes: [
      {
        documento: 'Lei nº 11.795/2008 (Sistema de Consórcio)',
        rotulo: 'Art. 30',
        url: 'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11795.htm',
      },
    ],
  },
  snapshot_id: 'bcb-veiculos-pf-2026-09-24',
  aviso: 'Nada foi contratado. Para seguir, procure uma administradora de consórcio autorizada pelo Banco Central.',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

async function abrirComparacao() {
  await userEvent.click(await screen.findByRole('button', { name: 'Prefiro preencher os campos' }))
  await userEvent.type(screen.getByLabelText('O que você quer comprar?'), 'carro')
  await userEvent.type(screen.getByLabelText('Valor do item (R$)'), '80.000')
  await userEvent.type(screen.getByLabelText('Prazo para ter o item (meses)'), '60')
  await userEvent.click(screen.getByRole('button', { name: 'Simular' }))
}

describe('Plano', () => {
  it('reviews the chosen Caminho and saves it without a password', async () => {
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'POST /api/v1/simulacoes': () => json({ ...simulacao(72, 199_114, 14_708_518, false), id: 's1' }, 201),
      'POST /api/v1/planos/previa': () => json(plano),
      'POST /api/v1/planos': () => json({ ...plano, id: 'p1' }, 201),
    })

    render(<App />)
    await abrirComparacao()
    const consorcio = await screen.findByRole('article', { name: /Consórcio/ })
    await userEvent.click(consorcio.querySelector('button.escolher') as HTMLButtonElement)

    expect(await screen.findByRole('heading', { name: 'Revise antes de salvar' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Seu plano' })).toHaveTextContent(/Parcela\s*R\$\s1\.950/)
    expect(screen.getByText(/só recebe de volta o que pagou quando for sorteado/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Lei nº 11.795/2008 (Sistema de Consórcio), Art. 30' })).toHaveAttribute(
      'href',
      'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11795.htm',
    )
    const salvar = screen.getByRole('button', { name: 'Salvar plano' })
    expect(salvar).toBeDisabled()
    await userEvent.click(screen.getByLabelText('Entendi que nada é contratado'))
    await userEvent.click(salvar)

    expect(await screen.findByRole('heading', { name: 'Plano salvo' })).toBeInTheDocument()
    expect(screen.getByText(/Nada foi contratado/)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/planos', expect.objectContaining({
      body: JSON.stringify({ simulacao_id: 's1', caminho: 'consorcio' }),
    }))
    expect(fetchMock).not.toHaveBeenCalledWith('/api/v1/sessoes/reautenticar', expect.anything())
  })

  it('lists saved Planos from the profile menu', async () => {
    fakeApi({
      'GET /api/v1/home': () => json(homeBruno),
      'GET /api/v1/planos': () => json([{ id: 'p1', caminho: 'consorcio', item: 'carro', criado_em: '2026-10-15' }]),
      'GET /api/v1/planos/p1': () => json({ ...plano, id: 'p1' }),
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Perfil' }))
    await userEvent.click(screen.getByRole('button', { name: 'Meus planos' }))
    await userEvent.click(await screen.findByRole('button', { name: /carro · Consórcio · 15\/10\/2026/ }))

    expect(await screen.findByRole('region', { name: 'Seu plano' })).toHaveTextContent('entre o mês 1 e o mês 48')
    expect(screen.getByText('Simulado com os dados de mercado bcb-veiculos-pf-2026-09-24.')).toBeInTheDocument()
  })
})
