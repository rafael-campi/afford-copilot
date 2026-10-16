import { useState, type FormEvent, type ReactNode } from 'react'
import { RecusaDaApi } from './api'

type Props = {
  titulo: string
  demo: boolean
  children: ReactNode
  onConfirmar: (senha: string) => Promise<void>
  onCancelar: () => void
}

/** The step every sensitive action goes through: summary, password, confirm (ADR 0003). */
export function ConfirmarComSenha({ titulo, demo, children, onConfirmar, onCancelar }: Props) {
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(event: FormEvent) {
    event.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      await onConfirmar(senha)
    } catch (e) {
      setErro(e instanceof RecusaDaApi ? e.message : 'Não foi possível confirmar agora.')
      setEnviando(false)
    }
  }

  return (
    <div className="dialogo-fundo">
      <div className="dialogo" role="dialog" aria-modal="true" aria-labelledby="dialogo-titulo">
        <h2 id="dialogo-titulo" className="painel-titulo">
          {titulo}
        </h2>
        {children}
        <form className="formulario" onSubmit={enviar}>
          <label className="campo">
            <span>Sua senha</span>
            <input id="senha-confirmacao" type="password" required autoComplete="current-password"
              value={senha} onChange={(e) => setSenha(e.target.value)} />
          </label>
          {demo && <p className="nota">Conta de demonstração: a senha é demo</p>}
          {erro && (
            <p className="aviso" role="alert">
              {erro}
            </p>
          )}
          <button type="submit" className="primary-button" disabled={enviando}>
            Confirmar
          </button>
          <button type="button" className="link-button" onClick={onCancelar}>
            Cancelar
          </button>
        </form>
      </div>
    </div>
  )
}
