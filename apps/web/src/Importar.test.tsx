import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { fakeApi, homeBruno, json } from './test-api'

const semExtrato = () => json({ detail: 'Conecte seu banco ou importe seu extrato.' }, 409)
const sessao = () => json({ conta: { nome: 'Rafa', email: 'rafa@exemplo.com', demo: false }, reautenticado: false })
const pedido = {
  id: 'imp1',
  acao: 'importar_extrato',
  previa: {
    transacoes: 78,
    inicio: '2026-07-01',
    fim: '2026-09-28',
    exemplos: [
      { data: '2026-07-01', descricao: 'PAO DE ACUCAR 3859', valor_centavos: -15_844 },
      { data: '2026-07-05', descricao: 'CRED SALARIO VERDEMAR', valor_centavos: 680_000 },
    ],
  },
  aviso: 'O arquivo não é guardado. As transações ficam 24 horas e depois são apagadas.',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

async function escolherArquivo() {
  await userEvent.click(await screen.findByRole('button', { name: 'Importar extrato (OFX)' }))
  const arquivo = new File(['<OFX>'], 'extrato.ofx', { type: 'application/x-ofx' })
  await userEvent.upload(screen.getByLabelText('Arquivo OFX'), arquivo)
}

describe('Importar extrato', () => {
  it('previews the file and uses it after confirming with the password', async () => {
    let importado = false
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => (importado ? json(homeBruno) : semExtrato()),
      'GET /api/v1/bancos': () => json([]),
      'GET /api/v1/sessoes': sessao,
      'POST /api/v1/importacoes': () => json(pedido, 201),
      'POST /api/v1/sessoes/reautenticar': () => new Response(null, { status: 204 }),
      'POST /api/v1/confirmacoes/imp1/confirmar': () => {
        importado = true
        return json({ acao: 'importar_extrato', feito: true })
      },
    })

    render(<App />)
    await escolherArquivo()

    const previa = await screen.findByRole('region', { name: 'Prévia do extrato' })
    expect(previa).toHaveTextContent('78 transações de 01/07/2026 a 28/09/2026')
    expect(previa).toHaveTextContent('PAO DE ACUCAR 3859')
    expect(previa).toHaveTextContent('O arquivo não é guardado.')
    const envio = fetchMock.mock.calls.find(([url]) => url === '/api/v1/importacoes')
    expect(envio?.[1]?.body).toBeInstanceOf(FormData)

    await userEvent.click(screen.getByRole('button', { name: 'Usar este extrato' }))
    await screen.findByRole('dialog', { name: 'Confirme a importação' })
    await userEvent.type(screen.getByLabelText('Sua senha'), 'uma senha longa o bastante')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByLabelText('O que você quer conquistar?')).toBeInTheDocument()
  })

  it('explains a file it cannot read', async () => {
    fakeApi({
      'GET /api/v1/home': semExtrato,
      'GET /api/v1/bancos': () => json([]),
      'GET /api/v1/sessoes': sessao,
      'POST /api/v1/importacoes': () =>
        json({ detail: 'Não encontrei transações nesse arquivo. Exporte o extrato em OFX pelo app do seu banco.' }, 422),
    })

    render(<App />)
    await escolherArquivo()

    expect(await screen.findByRole('alert')).toHaveTextContent('Não encontrei transações nesse arquivo.')
  })

  it('offers a sample file to try the import', async () => {
    fakeApi({
      'GET /api/v1/home': semExtrato,
      'GET /api/v1/bancos': () => json([]),
      'GET /api/v1/sessoes': sessao,
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Importar extrato (OFX)' }))

    expect(screen.getByRole('link', { name: 'Baixar um extrato de exemplo' })).toHaveAttribute(
      'href',
      '/api/v1/exemplos/bruno.ofx',
    )
  })
})
