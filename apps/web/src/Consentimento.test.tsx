import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { fakeApi, homeBruno, json } from './test-api'

const personas = [{ id: 'bruno', nome: 'Bruno', perfil: 'No limite', descricao: 'Sobra pouco.' }]
const bancos = [
  { id: 'bruno', nome: 'Banco de demonstração do Bruno' },
  { id: 'carla', nome: 'Banco de demonstração da Carla' },
]
const pedido = {
  id: 'cf1',
  acao: 'conceder_consentimento',
  resumo: {
    banco: 'Banco de demonstração do Bruno',
    escopos: ['transacoes'],
    meses_validade: 12,
    expira_em: '2027-10-10',
  },
}
const vazio = () => new Response(null, { status: 204 })
const semSessao = () => json({ detail: 'Entre na sua conta primeiro.' }, 401)
const semExtrato = () => json({ detail: 'Conecte seu banco ou importe seu extrato.' }, 409)
const sessaoDemo = () => json({ conta: { nome: 'Bruno', email: 'bruno@demo.afford', demo: true }, reautenticado: false })

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Consentimento', () => {
  it('connects the Persona bank after choosing a Persona', async () => {
    let fase: 'fora' | 'sem-extrato' | 'conectado' = 'fora'
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => (fase === 'fora' ? semSessao() : fase === 'sem-extrato' ? semExtrato() : json(homeBruno)),
      'GET /api/v1/personas': () => json(personas),
      'GET /api/v1/bancos': () => json(bancos),
      'GET /api/v1/sessoes': sessaoDemo,
      'POST /api/v1/sessoes/demo': () => {
        fase = 'sem-extrato'
        return vazio()
      },
      'POST /api/v1/consentimentos': () => json(pedido, 201),
      'POST /api/v1/sessoes/reautenticar': vazio,
      'POST /api/v1/confirmacoes/cf1/confirmar': () => {
        fase = 'conectado'
        return json({ acao: 'conceder_consentimento', feito: true })
      },
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: /Bruno.*No limite/ }))

    expect(await screen.findByRole('heading', { name: 'Banco de demonstração do Bruno' })).toBeInTheDocument()
    expect(screen.getByLabelText('Transações dos últimos meses')).toBeChecked()
    expect(screen.getByLabelText('Transações dos últimos meses')).toBeDisabled()
    expect(screen.getByLabelText('Saldos')).not.toBeChecked()
    await userEvent.click(screen.getByRole('button', { name: 'Autorizar' }))

    const confirmar = await screen.findByRole('dialog', { name: 'Confirme a autorização' })
    expect(confirmar).toHaveTextContent('Válido até 10/10/2027')
    expect(confirmar).toHaveTextContent('Conta de demonstração: a senha é demo')
    await userEvent.type(screen.getByLabelText('Sua senha'), 'demo')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByLabelText('O que você quer conquistar?')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/consentimentos', expect.objectContaining({
      body: JSON.stringify({ banco: 'bruno', escopos: ['transacoes'], meses_validade: 12 }),
    }))
  })

  it('says when the password is wrong and does not confirm', async () => {
    const fetchMock = fakeApi({
      'GET /api/v1/home': semExtrato,
      'GET /api/v1/bancos': () => json(bancos),
      'GET /api/v1/sessoes': sessaoDemo,
      'POST /api/v1/consentimentos': () => json(pedido, 201),
      'POST /api/v1/sessoes/reautenticar': () => json({ detail: 'Senha incorreta.' }, 401),
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: /Conectar meu banco/ }))
    await userEvent.click(await screen.findByRole('button', { name: 'Banco de demonstração do Bruno' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Autorizar' }))
    await userEvent.type(await screen.findByLabelText('Sua senha'), 'errada')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Senha incorreta.')
    expect(fetchMock).not.toHaveBeenCalledWith('/api/v1/confirmacoes/cf1/confirmar', expect.anything())
  })

  it('lists and revokes consentimentos from the profile menu', async () => {
    let conectado = true
    fakeApi({
      'GET /api/v1/home': () => (conectado ? json(homeBruno) : semExtrato()),
      'GET /api/v1/bancos': () => json(bancos),
      'GET /api/v1/sessoes': sessaoDemo,
      'GET /api/v1/consentimentos': () =>
        json([
          {
            id: 'c1',
            banco: 'Banco de demonstração do Bruno',
            escopos: ['transacoes'],
            concedido_em: '2026-10-15',
            expira_em: '2027-10-10',
            situacao: conectado ? 'ativo' : 'revogado',
          },
        ]),
      'DELETE /api/v1/consentimentos/c1': () =>
        json({ id: 'cf2', acao: 'revogar_consentimento', resumo: { banco: 'Banco de demonstração do Bruno' } }, 201),
      'POST /api/v1/sessoes/reautenticar': vazio,
      'POST /api/v1/confirmacoes/cf2/confirmar': () => {
        conectado = false
        return json({ acao: 'revogar_consentimento', feito: true })
      },
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Perfil' }))
    await userEvent.click(screen.getByRole('button', { name: 'Meus consentimentos' }))
    const item = await screen.findByRole('listitem', { name: 'Banco de demonstração do Bruno' })
    expect(item).toHaveTextContent('Ativo · válido até 10/10/2027')
    await userEvent.click(screen.getByRole('button', { name: 'Revogar' }))
    const confirmar = await screen.findByRole('dialog', { name: 'Confirme a revogação' })
    expect(confirmar).toHaveTextContent('O copiloto deixa de ler seu extrato na hora.')
    await userEvent.type(screen.getByLabelText('Sua senha'), 'demo')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByRole('heading', { name: 'Conecte seu banco' })).toBeInTheDocument()
  })
})
