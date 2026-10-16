import { useState, type FormEvent } from 'react'
import { RecusaDaApi, cadastrar, login } from './api'
import { EscolherPersona } from './EscolherPersona'

type Modo = 'personas' | 'login' | 'cadastro'

type Props = {
  onEscolherPersona: (personaId: string) => void
  onEntrou: () => void
}

export function Entrar({ onEscolherPersona, onEntrou }: Props) {
  const [modo, setModo] = useState<Modo>('personas')
  if (modo === 'personas') {
    return (
      <EscolherPersona onEscolher={onEscolherPersona}>
        <div className="entrar-alternativas">
          <button type="button" className="link-button" onClick={() => setModo('login')}>
            Entrar com e-mail
          </button>
          <button type="button" className="link-button" onClick={() => setModo('cadastro')}>
            Criar conta
          </button>
        </div>
      </EscolherPersona>
    )
  }
  return <FormConta modo={modo} onVoltar={() => setModo('personas')} onEntrou={onEntrou} />
}

function FormConta({
  modo,
  onVoltar,
  onEntrou,
}: {
  modo: 'login' | 'cadastro'
  onVoltar: () => void
  onEntrou: () => void
}) {
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const cadastro = modo === 'cadastro'

  async function enviar(event: FormEvent) {
    event.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      if (cadastro) await cadastrar(nome.trim(), email.trim(), senha)
      else await login(email.trim(), senha)
      onEntrou()
    } catch (e) {
      setErro(e instanceof RecusaDaApi ? e.message : 'Algo deu errado. Tente de novo.')
      setEnviando(false)
    }
  }

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">{cadastro ? 'Criar conta' : 'Entrar'}</h1>
      </header>
      <form className="formulario" onSubmit={enviar}>
        {cadastro && (
          <label className="campo">
            <span>Nome</span>
            <input id="nome" required value={nome} onChange={(e) => setNome(e.target.value)} />
          </label>
        )}
        <label className="campo">
          <span>E-mail</span>
          <input id="email" type="email" required autoComplete="email" value={email}
            onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="campo">
          <span>Senha</span>
          <input id="senha" type="password" required minLength={cadastro ? 12 : undefined}
            autoComplete={cadastro ? 'new-password' : 'current-password'} value={senha}
            onChange={(e) => setSenha(e.target.value)} />
        </label>
        {erro && (
          <p className="aviso" role="alert">
            {erro}
          </p>
        )}
        <button type="submit" className="primary-button" disabled={enviando}>
          {cadastro ? 'Criar minha conta' : 'Entrar'}
        </button>
      </form>
    </main>
  )
}
