import { useEffect, useState } from 'react'
import {
  confirmar,
  fetchBancos,
  fetchSessao,
  pedirConsentimento,
  reautenticar,
  type Banco,
  type ConfirmacaoPendente,
} from './api'
import { ConfirmarComSenha } from './ConfirmarComSenha'
import { formatarData } from './format'
import { Importar } from './Importar'

type Props = {
  bancoInicial: string | null
  onConectado: () => void
  onSair: () => void
}

type Passo = 'inicio' | 'bancos' | 'autorizar' | 'importar'

const ESCOPOS = [
  { id: 'transacoes', rotulo: 'Transações dos últimos meses', obrigatorio: true },
  { id: 'saldos', rotulo: 'Saldos', obrigatorio: false },
]

export function Conectar({ bancoInicial, onConectado, onSair }: Props) {
  const [bancos, setBancos] = useState<Banco[]>([])
  const [demo, setDemo] = useState(false)
  const [banco, setBanco] = useState<string | null>(bancoInicial)
  const [passo, setPasso] = useState<Passo>(bancoInicial ? 'autorizar' : 'inicio')
  const [saldos, setSaldos] = useState(false)
  const [meses, setMeses] = useState(12)
  const [pendente, setPendente] = useState<ConfirmacaoPendente | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    fetchBancos()
      .then((lista) => ativo && setBancos(lista))
      .catch(() => ativo && setErro('Não foi possível listar os bancos.'))
    fetchSessao()
      .then((s) => ativo && setDemo(s.conta.demo))
      .catch(() => undefined)
    return () => {
      ativo = false
    }
  }, [])

  async function autorizar() {
    if (!banco) return
    setErro(null)
    try {
      const escopos = saldos ? ['transacoes', 'saldos'] : ['transacoes']
      setPendente(await pedirConsentimento(banco, escopos, meses))
    } catch {
      setErro('Não foi possível pedir a autorização agora.')
    }
  }

  async function confirmarComSenha(senha: string) {
    if (!pendente) return
    await reautenticar(senha)
    await confirmar(pendente.id)
    onConectado()
  }

  if (passo === 'importar') {
    return <Importar onImportado={onConectado} onVoltar={() => setPasso('inicio')} />
  }

  if (passo === 'inicio') {
    return (
      <main className="tela">
        <header className="tela-cabecalho">
          <h1 className="tela-titulo">Conecte seu banco</h1>
          <p className="tela-texto">
            Para calcular quanto cabe no seu orçamento, o copiloto precisa ler seu extrato. Você
            escolhe o que ele pode ver e por quanto tempo, e pode revogar quando quiser.
          </p>
        </header>
        <button type="button" className="primary-button" onClick={() => setPasso('bancos')}>
          Conectar meu banco
        </button>
        <button type="button" className="secondary-button" onClick={() => setPasso('importar')}>
          Importar extrato (OFX ou CSV)
        </button>
        <button type="button" className="link-button" onClick={onSair}>
          Sair
        </button>
      </main>
    )
  }

  if (passo === 'bancos') {
    return (
      <main className="tela">
        <header className="tela-cabecalho">
          <button type="button" className="voltar" onClick={() => setPasso('inicio')}>
            Voltar
          </button>
          <h1 className="tela-titulo">Escolha o banco</h1>
        </header>
        {erro && <p className="aviso" role="alert">{erro}</p>}
        <ul className="personas">
          {bancos.map((b) => (
            <li key={b.id}>
              <button type="button" className="persona" onClick={() => {
                setBanco(b.id)
                setPasso('autorizar')
              }}>
                <span className="persona-nome">{b.nome}</span>
              </button>
            </li>
          ))}
        </ul>
      </main>
    )
  }

  const nome = bancos.find((b) => b.id === banco)?.nome ?? ''
  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <span className="eyebrow">Autorizar acesso</span>
        <h1 className="tela-titulo">{nome}</h1>
        <p className="tela-texto">O copiloto vai poder ler só o que você marcar.</p>
      </header>
      <fieldset className="escopos">
        <legend className="eyebrow">O que o copiloto pode ver</legend>
        {ESCOPOS.map((e) => (
          <label key={e.id} className="escopo">
            <input
              type="checkbox"
              checked={e.obrigatorio || saldos}
              disabled={e.obrigatorio}
              onChange={(ev) => setSaldos(ev.target.checked)}
            />
            <span>{e.rotulo}</span>
          </label>
        ))}
      </fieldset>
      <label className="campo">
        <span>Válido por</span>
        <select value={meses} onChange={(e) => setMeses(Number(e.target.value))}>
          {[3, 6, 12].map((m) => (
            <option key={m} value={m}>
              {m} meses
            </option>
          ))}
        </select>
      </label>
      {erro && <p className="aviso" role="alert">{erro}</p>}
      <button type="button" className="primary-button" onClick={autorizar}>
        Autorizar
      </button>
      <button type="button" className="link-button" onClick={onSair}>
        Agora não
      </button>
      {pendente && (
        <ConfirmarComSenha
          titulo="Confirme a autorização"
          demo={demo}
          onConfirmar={confirmarComSenha}
          onCancelar={() => setPendente(null)}
        >
          <p className="caminho-texto">
            {String(pendente.resumo.banco)} · Válido até{' '}
            {formatarData(String(pendente.resumo.expira_em))}
          </p>
        </ConfirmarComSenha>
      )}
    </main>
  )
}
