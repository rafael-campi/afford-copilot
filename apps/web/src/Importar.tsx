import { useEffect, useState } from 'react'
import {
  RecusaDaApi,
  confirmar,
  fetchSessao,
  importarExtrato,
  reautenticar,
  type PedidoImportacao,
} from './api'
import { ConfirmarComSenha } from './ConfirmarComSenha'
import { formatarData, formatarReais } from './format'

type Props = { onImportado: () => void; onVoltar: () => void }

export function Importar({ onImportado, onVoltar }: Props) {
  const [pedido, setPedido] = useState<PedidoImportacao | null>(null)
  const [confirmando, setConfirmando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [demo, setDemo] = useState(false)

  useEffect(() => {
    let ativo = true
    fetchSessao()
      .then((s) => ativo && setDemo(s.conta.demo))
      .catch(() => undefined)
    return () => {
      ativo = false
    }
  }, [])

  async function escolher(arquivo: File | undefined) {
    if (!arquivo) return
    setErro(null)
    setPedido(null)
    setEnviando(true)
    try {
      setPedido(await importarExtrato(arquivo))
    } catch (e) {
      setErro(e instanceof RecusaDaApi ? e.message : 'Não foi possível ler o arquivo agora.')
    } finally {
      setEnviando(false)
    }
  }

  async function confirmarComSenha(senha: string) {
    if (!pedido) return
    await reautenticar(senha)
    await confirmar(pedido.id)
    onImportado()
  }

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">Importar extrato</h1>
        <p className="tela-texto">
          Exporte o extrato em OFX pelo app ou site do seu banco, com pelo menos os últimos 3
          meses.
        </p>
      </header>

      <label className="campo">
        <span>Arquivo OFX</span>
        <input type="file" accept=".ofx,application/x-ofx" disabled={enviando}
          onChange={(e) => escolher(e.target.files?.[0])} />
      </label>
      <a className="link-button" href="/api/v1/exemplos/bruno.ofx" download>
        Baixar um extrato de exemplo
      </a>

      {erro && (
        <p className="aviso" role="alert">
          {erro}
        </p>
      )}

      {pedido && (
        <section className="orcamento-conversa" aria-labelledby="previa-titulo">
          <h2 id="previa-titulo" className="painel-titulo">
            Prévia do extrato
          </h2>
          <p className="caminho-texto">
            {pedido.previa.transacoes} transações de {formatarData(pedido.previa.inicio)} a{' '}
            {formatarData(pedido.previa.fim)}
          </p>
          <ul className="gastos">
            {pedido.previa.exemplos.map((t, i) => (
              <li key={i}>
                <span>
                  {formatarData(t.data)} {t.descricao}
                </span>
                <span>{formatarReais(t.valor_centavos)}</span>
              </li>
            ))}
          </ul>
          {pedido.aviso && <p className="nota">{pedido.aviso}</p>}
          <button type="button" className="primary-button" onClick={() => setConfirmando(true)}>
            Usar este extrato
          </button>
        </section>
      )}

      {pedido && confirmando && (
        <ConfirmarComSenha
          titulo="Confirme a importação"
          demo={demo}
          onConfirmar={confirmarComSenha}
          onCancelar={() => setConfirmando(false)}
        >
          <p className="caminho-texto">
            O copiloto vai usar estas {pedido.previa.transacoes} transações para calcular seu
            orçamento.
          </p>
        </ConfirmarComSenha>
      )}
    </main>
  )
}
