import { useEffect, useState } from 'react'
import { confirmar, fetchSessao, pedirExclusao, reautenticar, type ConfirmacaoPendente } from './api'
import { ConfirmarComSenha } from './ConfirmarComSenha'

type Props = { onVoltar: () => void; onApagada: () => void }

export function ApagarConta({ onVoltar, onApagada }: Props) {
  const [pendente, setPendente] = useState<ConfirmacaoPendente | null>(null)
  const [demo, setDemo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    fetchSessao()
      .then((s) => ativo && setDemo(s.conta.demo))
      .catch(() => undefined)
    return () => {
      ativo = false
    }
  }, [])

  async function pedir() {
    setErro(null)
    try {
      setPendente(await pedirExclusao())
    } catch {
      setErro('Não foi possível pedir a exclusão agora.')
    }
  }

  async function confirmarComSenha(senha: string) {
    if (!pendente) return
    await reautenticar(senha)
    await confirmar(pendente.id)
    onApagada()
  }

  const apaga = (pendente?.resumo.apaga as string[] | undefined) ?? []
  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">Apagar minha conta</h1>
        <p className="tela-texto">
          Apagamos sua conta, seus consentimentos, os extratos importados, as simulações e as
          conversas. O registro de auditoria guarda só que a exclusão aconteceu, sem dados seus.
        </p>
      </header>
      {erro && (
        <p className="aviso" role="alert">
          {erro}
        </p>
      )}
      <button type="button" className="botao-perigo" onClick={pedir}>
        Apagar tudo
      </button>
      {pendente && (
        <ConfirmarComSenha
          titulo="Confirme a exclusão"
          demo={demo}
          onConfirmar={confirmarComSenha}
          onCancelar={() => setPendente(null)}
        >
          <p className="caminho-texto">
            Vamos apagar: {apaga.join(', ')}. Não dá para desfazer.
          </p>
        </ConfirmarComSenha>
      )}
    </main>
  )
}
