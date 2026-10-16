import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { fakeApi, homeBruno, json } from './test-api'

const personas = [{ id: 'bruno', nome: 'Bruno', perfil: 'No limite', descricao: 'Sobra pouco.' }]
const semSessao = () => json({ detail: 'Entre na sua conta primeiro.' }, 401)
const semExtrato = () => json({ detail: 'Conecte seu banco ou importe seu extrato.' }, 409)

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Contas', () => {
  it('creates an account and asks to connect a bank', async () => {
    let cadastrado = false
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => (cadastrado ? semExtrato() : semSessao()),
      'GET /api/v1/personas': () => json(personas),
      'POST /api/v1/contas': () => {
        cadastrado = true
        return json({ nome: 'Rafa', email: 'rafa@exemplo.com', demo: false }, 201)
      },
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Criar conta' }))
    await userEvent.type(screen.getByLabelText('Nome'), 'Rafa')
    await userEvent.type(screen.getByLabelText('E-mail'), 'rafa@exemplo.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'uma senha longa o bastante')
    await userEvent.click(screen.getByRole('button', { name: 'Criar minha conta' }))

    expect(await screen.findByRole('heading', { name: 'Conecte seu banco' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/contas', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ nome: 'Rafa', email: 'rafa@exemplo.com', senha: 'uma senha longa o bastante' }),
    }))
  })

  it('logs in with e-mail and shows the Home', async () => {
    let logado = false
    fakeApi({
      'GET /api/v1/home': () => (logado ? json(homeBruno) : semSessao()),
      'GET /api/v1/personas': () => json(personas),
      'POST /api/v1/sessoes': () => {
        logado = true
        return new Response(null, { status: 204 })
      },
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Entrar com e-mail' }))
    await userEvent.type(screen.getByLabelText('E-mail'), 'bruno@exemplo.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'uma senha longa o bastante')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('Bruno')).toBeInTheDocument()
  })

  it('says when the e-mail or password is wrong', async () => {
    fakeApi({
      'GET /api/v1/home': semSessao,
      'GET /api/v1/personas': () => json(personas),
      'POST /api/v1/sessoes': () => json({ detail: 'E-mail ou senha incorretos.' }, 401),
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Entrar com e-mail' }))
    await userEvent.type(screen.getByLabelText('E-mail'), 'bruno@exemplo.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'errada errada')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos.')
  })

  it('logs out from the profile menu', async () => {
    let logado = true
    const fetchMock = fakeApi({
      'GET /api/v1/home': () => (logado ? json(homeBruno) : semSessao()),
      'GET /api/v1/personas': () => json(personas),
      'DELETE /api/v1/sessoes': () => {
        logado = false
        return new Response(null, { status: 204 })
      },
    })

    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Perfil' }))
    await userEvent.click(screen.getByRole('button', { name: 'Sair' }))

    expect(await screen.findByRole('button', { name: /Bruno.*No limite/ })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/sessoes', expect.objectContaining({ method: 'DELETE' }))
  })
})
