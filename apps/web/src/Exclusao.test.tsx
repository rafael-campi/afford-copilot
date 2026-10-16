import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { fakeApi, homeBruno, json } from './test-api'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Apagar minha conta', () => {
  it('lists what goes away and deletes after the password', async () => {
    let existe = true
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => (existe ? json(homeBruno) : json({ detail: 'Entre na sua conta primeiro.' }, 401)),
      'GET /api/v1/personas': () => json([{ id: 'bruno', nome: 'Bruno', perfil: 'No limite', descricao: 'Sobra pouco.' }]),
      'GET /api/v1/sessoes': () => json({ conta: { nome: 'Bruno', email: 'bruno@demo.afford', demo: true }, reautenticado: false }),
      'POST /api/v1/conta/exclusao': () =>
        json({ id: 'ex1', acao: 'apagar_conta', resumo: { apaga: ['conta', 'consentimentos', 'extratos importados'] } }, 201),
      'POST /api/v1/sessoes/reautenticar': () => new Response(null, { status: 204 }),
      'POST /api/v1/confirmacoes/ex1/confirmar': () => {
        existe = false
        return json({ acao: 'apagar_conta', feito: true })
      },
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Perfil' }))
    await userEvent.click(screen.getByRole('button', { name: 'Apagar minha conta' }))
    expect(await screen.findByRole('heading', { name: 'Apagar minha conta' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Apagar tudo' }))

    const dialogo = await screen.findByRole('dialog', { name: 'Confirme a exclusão' })
    expect(dialogo).toHaveTextContent('conta, consentimentos, extratos importados')
    expect(dialogo).toHaveTextContent('Não dá para desfazer.')
    await userEvent.type(screen.getByLabelText('Sua senha'), 'demo')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByRole('button', { name: /Bruno.*No limite/ })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/confirmacoes/ex1/confirmar', expect.anything())
  })
})
