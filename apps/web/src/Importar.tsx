import { useEffect, useState } from 'react'
import {
  RecusaDaApi,
  confirmar,
  fetchSessao,
  importarExtrato,
  reautenticar,
  type MapaColunas,
  type PedidoImportacao,
  type PedidoMapeamento,
} from './api'
import { ConfirmarComSenha } from './ConfirmarComSenha'
import { formatarData, formatarReais } from './format'

type Props = { onImportado: () => void; onVoltar: () => void }

export function Importar({ onImportado, onVoltar }: Props) {
  const [pedido, setPedido] = useState<PedidoImportacao | null>(null)
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [mapeamento, setMapeamento] = useState<PedidoMapeamento | null>(null)
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

  async function enviar(escolhido: File, mapa?: MapaColunas) {
    setErro(null)
    setPedido(null)
    setEnviando(true)
    try {
      const resposta = await importarExtrato(escolhido, mapa)
      if ('precisa_mapear' in resposta) {
        setMapeamento(resposta)
      } else {
        setMapeamento(null)
        setPedido(resposta)
      }
    } catch (e) {
      setErro(e instanceof RecusaDaApi ? e.message : 'Não foi possível ler o arquivo agora.')
    } finally {
      setEnviando(false)
    }
  }

  function escolher(escolhido: File | undefined) {
    if (!escolhido) return
    setArquivo(escolhido)
    setMapeamento(null)
    void enviar(escolhido)
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
          Exporte o extrato em OFX ou CSV pelo app ou site do seu banco, com pelo menos os
          últimos 3 meses.
        </p>
      </header>

      <label className="campo">
        <span>Arquivo do extrato</span>
        <input type="file" accept=".ofx,.csv,application/x-ofx,text/csv" disabled={enviando}
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

      {mapeamento && arquivo && (
        <MapearColunas
          mapeamento={mapeamento}
          enviando={enviando}
          onContinuar={(mapa) => enviar(arquivo, mapa)}
        />
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

const CAMPOS: { campo: keyof MapaColunas; rotulo: string }[] = [
  { campo: 'data', rotulo: 'Coluna da data' },
  { campo: 'descricao', rotulo: 'Coluna da descrição' },
  { campo: 'valor', rotulo: 'Coluna do valor' },
]

function MapearColunas({
  mapeamento,
  enviando,
  onContinuar,
}: {
  mapeamento: PedidoMapeamento
  enviando: boolean
  onContinuar: (mapa: MapaColunas) => void
}) {
  const primeira = mapeamento.colunas[0] ?? ''
  const [mapa, setMapa] = useState<MapaColunas>({
    data: mapeamento.sugestao.data ?? primeira,
    descricao: mapeamento.sugestao.descricao ?? primeira,
    valor: mapeamento.sugestao.valor ?? primeira,
  })

  return (
    <section className="orcamento-conversa" aria-labelledby="mapa-titulo">
      <h2 id="mapa-titulo" className="painel-titulo">
        Qual coluna é qual?
      </h2>
      <div className="tabela-rolagem">
        <table className="amostra">
          <thead>
            <tr>
              {mapeamento.colunas.map((c) => (
                <th key={c} scope="col">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mapeamento.amostra.map((linha, i) => (
              <tr key={i}>
                {linha.map((celula, j) => (
                  <td key={j}>{celula}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {CAMPOS.map(({ campo, rotulo }) => (
        <label key={campo} className="campo">
          <span>{rotulo}</span>
          <select value={mapa[campo]} onChange={(e) => setMapa({ ...mapa, [campo]: e.target.value })}>
            {mapeamento.colunas.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      ))}
      <button type="button" className="primary-button" disabled={enviando} onClick={() => onContinuar(mapa)}>
        Continuar
      </button>
    </section>
  )
}
