import { useEffect, useState } from 'react'
import {
  criarConversa,
  criarSimulacao,
  enviarMensagem,
  entrarComo,
  fetchHome,
  logout,
  fetchPlano,
  previaPlano,
  salvarPlano,
  ObjetivoInvalido,
  type HomeData,
  type NovaSimulacao,
  type ObjetivoConversa,
  type PlanoInfo,
  type Caminho,
  type Simulacao,
} from './api'
import { ApagarConta } from './ApagarConta'
import { Comparacao } from './Comparacao'
import { Conversa, type Mensagem } from './Conversa'
import { Entrar } from './Entrar'
import { doItem } from './format'
import { Home } from './Home'
import { MeusPlanos } from './MeusPlanos'
import { RevisaoPlano } from './RevisaoPlano'
import { ObjetivoForm } from './ObjetivoForm'
import { Conectar } from './Conectar'
import { Consentimentos } from './Consentimentos'

type Estado =
  | { tipo: 'carregando' }
  | { tipo: 'erro' }
  | { tipo: 'sem-sessao' }
  | { tipo: 'sem-extrato' }
  | { tipo: 'pronto'; dados: HomeData }

type Tela =
  | { nome: 'home' }
  | { nome: 'consentimentos' }
  | { nome: 'apagar-conta' }
  | { nome: 'planos' }
  | { nome: 'plano'; plano: PlanoInfo; modo: 'revisao' | 'salvo' | 'leitura'; simulacaoId?: string; salvando?: boolean; voltar: Tela }
  | { nome: 'objetivo'; erro: string | null; enviando: boolean }
  | { nome: 'comparacao'; pedido: NovaSimulacao; simulacao: Simulacao; recalculando: boolean }
  | {
      nome: 'conversa'
      conversaId: string | null
      mensagens: Mensagem[]
      objetivo: ObjetivoConversa | null
      simulacoes: Simulacao[]
      enviando: boolean
      erro: string | null
    }

const ERRO_OBJETIVO = 'Confira os valores: a Entrada precisa ser menor do que o valor do item.'
const ERRO_GERAL = 'Não foi possível simular agora. Tente de novo em alguns instantes.'

export function App() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' })
  const [tela, setTela] = useState<Tela>({ nome: 'home' })
  const [bancoSugerido, setBancoSugerido] = useState<string | null>(null)

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
    setBancoSugerido(personaId)
    try {
      await entrarComo(personaId)
      setEstado(await fetchHome())
    } catch {
      setEstado({ tipo: 'erro' })
    }
  }

  async function recarregar() {
    setTela({ nome: 'home' })
    setEstado({ tipo: 'carregando' })
    try {
      setEstado(await fetchHome())
    } catch {
      setEstado({ tipo: 'erro' })
    }
  }

  async function sair() {
    setBancoSugerido(null)
    await logout()
    await recarregar()
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

  async function conversar(texto: string) {
    const atual =
      tela.nome === 'conversa'
        ? tela
        : {
            nome: 'conversa' as const,
            conversaId: null,
            mensagens: [],
            objetivo: null,
            simulacoes: [],
            enviando: false,
            erro: null,
          }
    const mensagens: Mensagem[] = [...atual.mensagens, { autor: 'pessoa', texto }]
    setTela({ ...atual, mensagens, enviando: true, erro: null })
    try {
      const conversaId = atual.conversaId ?? (await criarConversa())
      const resposta = await enviarMensagem(conversaId, texto)
      const respostas: Mensagem[] = []
      if (resposta.novo_objetivo && atual.objetivo?.item && resposta.objetivo.item) {
        respostas.push({
          autor: 'copiloto',
          texto: `Novo objetivo: ${resposta.objetivo.item}. Os cenários ${doItem(atual.objetivo.item)} ficaram para trás.`,
        })
      }
      respostas.push({ autor: 'copiloto', texto: resposta.resposta, citacoes: resposta.citacoes })
      const anteriores = resposta.novo_objetivo ? [] : atual.simulacoes
      setTela({
        ...atual,
        conversaId,
        mensagens: [...mensagens, ...respostas],
        objetivo: resposta.objetivo,
        simulacoes: resposta.simulacao ? [...anteriores, resposta.simulacao] : anteriores,
        enviando: false,
        erro: null,
      })
    } catch {
      setTela({
        ...atual,
        mensagens,
        enviando: false,
        erro: 'Não consegui responder agora. Tente de novo em alguns instantes.',
      })
    }
  }

  function compararDaConversa(indice?: number) {
    if (tela.nome !== 'conversa' || tela.simulacoes.length === 0) return
    const simulacao = tela.simulacoes[indice ?? tela.simulacoes.length - 1]
    setTela({
      nome: 'comparacao',
      pedido: { ...simulacao.objetivo },
      simulacao,
      recalculando: false,
    })
  }

  async function escolherCaminho(caminho: Caminho) {
    if (tela.nome !== 'comparacao') return
    const plano = await previaPlano(tela.simulacao.id, caminho)
    setTela({ nome: 'plano', plano, modo: 'revisao', simulacaoId: tela.simulacao.id, voltar: tela })
  }

  async function salvar() {
    if (tela.nome !== 'plano' || !tela.simulacaoId) return
    setTela({ ...tela, salvando: true })
    const plano = await salvarPlano(tela.simulacaoId, tela.plano.caminho)
    setTela({ nome: 'plano', plano, modo: 'salvo', voltar: { nome: 'home' } })
  }

  async function abrirPlano(id: string) {
    const plano = await fetchPlano(id)
    setTela({ nome: 'plano', plano, modo: 'leitura', voltar: { nome: 'planos' } })
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

  if (estado.tipo === 'sem-sessao') {
    return <Entrar onEscolherPersona={escolher} onEntrou={recarregar} />
  }
  if (tela.nome === 'plano') {
    return (
      <RevisaoPlano
        plano={tela.plano}
        modo={tela.modo}
        salvando={tela.salvando}
        onSalvar={salvar}
        onVoltar={() => setTela(tela.voltar)}
      />
    )
  }
  if (tela.nome === 'planos') {
    return <MeusPlanos onAbrir={abrirPlano} onVoltar={() => setTela({ nome: 'home' })} />
  }
  if (tela.nome === 'apagar-conta') {
    return <ApagarConta onVoltar={recarregar} onApagada={recarregar} />
  }
  if (tela.nome === 'consentimentos') {
    return <Consentimentos onVoltar={recarregar} onMudou={recarregar} />
  }
  if (estado.tipo === 'sem-extrato') {
    return <Conectar bancoInicial={bancoSugerido} onConectado={recarregar} onSair={sair} />
  }

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

  if (estado.tipo === 'pronto' && tela.nome === 'conversa') {
    return (
      <Conversa
        mensagens={tela.mensagens}
        objetivo={tela.objetivo}
        cenarios={tela.simulacoes}
        resumo={estado.dados.resumo}
        gastos={estado.dados.gastos_por_categoria ?? []}
        enviando={tela.enviando}
        erro={tela.erro}
        onEnviar={conversar}
        onComparar={() => compararDaConversa()}
        onVerCenario={(i) => compararDaConversa(i)}
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
        onEscolher={escolherCaminho}
        onVoltar={() => setTela({ nome: 'objetivo', erro: null, enviando: false })}
      />
    )
  }

  return (
    <Home
      estado={estado}
      onEnviar={conversar}
      onFormulario={() => setTela({ nome: 'objetivo', erro: null, enviando: false })}
      onSair={sair}
      onConsentimentos={() => setTela({ nome: 'consentimentos' })}
      onApagarConta={() => setTela({ nome: 'apagar-conta' })}
      onPlanos={() => setTela({ nome: 'planos' })}
    />
  )
}
