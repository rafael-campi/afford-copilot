import { useCallback, useEffect, useState } from 'react'
import {
  confirmar,
  fetchConsentimentos,
  fetchSessao,
  reautenticar,
  revogarConsentimento,
  type ConfirmacaoPendente,
  type ConsentimentoInfo,
} from './api'
import { ConfirmarComSenha } from './ConfirmarComSenha'
import { formatarData } from './format'

const SITUACAO = { ativo: 'Ativo', revogado: 'Revogado', expirado: 'Expirado' }

export function Consentimentos({ onVoltar, onMudou }: { onVoltar: () => void; onMudou: () => void }) {
  const [lista, setLista] = useState<ConsentimentoInfo[] | null>(null)
  const [demo, setDemo] = useState(false)
  const [pendente, setPendente] = useState<ConfirmacaoPendente | null>(null)

  const carregar = useCallback(() => {
    fetchConsentimentos().then(setLista).catch(() => setLista([]))
  }, [])

  useEffect(() => {
    let ativo = true
    fetchConsentimentos()
      .then((itens) => ativo && setLista(itens))
      .catch(() => ativo && setLista([]))
    fetchSessao()
      .then((s) => ativo && setDemo(s.conta.demo))
      .catch(() => undefined)
    return () => {
      ativo = false
    }
  }, [])

  async function confirmarRevogacao(senha: string) {
    if (!pendente) return
    await reautenticar(senha)
    await confirmar(pendente.id)
    setPendente(null)
    carregar()
    onMudou()
  }

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">Meus consentimentos</h1>
      </header>
      {lista && lista.length === 0 && <p className="tela-texto">Nenhum banco conectado.</p>}
      <ul className="personas">
        {(lista ?? []).map((c) => (
          <li key={c.id} className="persona" aria-label={c.banco}>
            <span className="persona-nome">{c.banco}</span>
            <span className="persona-descricao">
              {SITUACAO[c.situacao]} · válido até {formatarData(c.expira_em)}
            </span>
            {c.situacao === 'ativo' && (
              <button
                type="button"
                className="link-button"
                onClick={async () => setPendente(await revogarConsentimento(c.id))}
              >
                Revogar
              </button>
            )}
          </li>
        ))}
      </ul>
      {pendente && (
        <ConfirmarComSenha
          titulo="Confirme a revogação"
          demo={demo}
          onConfirmar={confirmarRevogacao}
          onCancelar={() => setPendente(null)}
        >
          <p className="caminho-texto">
            {String(pendente.resumo.banco)}. O copiloto deixa de ler seu extrato na hora.
          </p>
        </ConfirmarComSenha>
      )}
    </main>
  )
}
