import { useEffect, useState } from 'react'
import {
  criarSimulacao,
  entrarComo,
  fetchHome,
  ObjetivoInvalido,
  type HomeData,
  type NovaSimulacao,
  type Simulacao,
} from './api'
import { Comparacao } from './Comparacao'
import { EscolherPersona } from './EscolherPersona'
import { Home } from './Home'
import { ObjetivoForm } from './ObjetivoForm'

type Estado =
  | { tipo: 'carregando' }
  | { tipo: 'erro' }
  | { tipo: 'sem-sessao' }
  | { tipo: 'pronto'; dados: HomeData }

type Tela =
  | { nome: 'home' }
  | { nome: 'objetivo'; erro: string | null; enviando: boolean }
  | { nome: 'comparacao'; pedido: NovaSimulacao; simulacao: Simulacao; recalculando: boolean }

const ERRO_OBJETIVO = 'Confira os valores: a Entrada precisa ser menor do que o valor do item.'
const ERRO_GERAL = 'Não foi possível simular agora. Tente de novo em alguns instantes.'

export function App() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' })
  const [tela, setTela] = useState<Tela>({ nome: 'home' })

  useEffect(() => {
    let ativo = true
    fetchHome()
      .then((resultado) => ativo && setEstado(resultado))
      .catch(() => ativo && setEstado({ tipo: 'erro' }))
    return () => {
      ativo = false
    }
  }, [])

  async function escolher(personaId: string) {
    setEstado({ tipo: 'carregando' })
    try {
      await entrarComo(personaId)
      setEstado(await fetchHome())
    } catch {
      setEstado({ tipo: 'erro' })
    }
  }

  async function simularObjetivo(pedido: NovaSimulacao) {
    setTela({ nome: 'objetivo', erro: null, enviando: true })
    try {
      const simulacao = await criarSimulacao(pedido)
      setTela({ nome: 'comparacao', pedido, simulacao, recalculando: false })
    } catch (erro) {
      const mensagem = erro instanceof ObjetivoInvalido ? ERRO_OBJETIVO : ERRO_GERAL
      setTela({ nome: 'objetivo', erro: mensagem, enviando: false })
    }
  }

  async function mudarPedido(mudanca: Partial<NovaSimulacao>) {
    if (tela.nome !== 'comparacao') return
    const pedido = { ...tela.pedido, ...mudanca }
    setTela({ ...tela, recalculando: true })
    try {
      const simulacao = await criarSimulacao(pedido)
      setTela({ nome: 'comparacao', pedido, simulacao, recalculando: false })
    } catch {
      setTela({ ...tela, recalculando: false })
    }
  }

  if (estado.tipo === 'sem-sessao') return <EscolherPersona onEscolher={escolher} />

  if (estado.tipo === 'pronto' && tela.nome === 'objetivo') {
    return (
      <ObjetivoForm
        erro={tela.erro}
        enviando={tela.enviando}
        onSimular={simularObjetivo}
        onVoltar={() => setTela({ nome: 'home' })}
      />
    )
  }

  if (estado.tipo === 'pronto' && tela.nome === 'comparacao') {
    return (
      <Comparacao
        simulacao={tela.simulacao}
        margemSeguraCentavos={estado.dados.resumo.margem_segura_centavos}
        recalculando={tela.recalculando}
        onMudar={mudarPedido}
        onVoltar={() => setTela({ nome: 'objetivo', erro: null, enviando: false })}
      />
    )
  }

  return (
    <Home estado={estado} onAnalisar={() => setTela({ nome: 'objetivo', erro: null, enviando: false })} />
  )
}
