export type ResumoOrcamento = {
  entradas_centavos: number
  gastos_centavos: number
  sobra_mensal_centavos: number
  margem_segura_centavos: number
  margem_acima_da_sobra: boolean
}

export type Sugestao = {
  titulo: string
  descricao: string
}

export type HomeData = {
  nome: string
  resumo: ResumoOrcamento
  sugestoes: Sugestao[]
}

export type Persona = {
  id: string
  nome: string
  perfil: string
  descricao: string
}

export type ResultadoHome = { tipo: 'pronto'; dados: HomeData } | { tipo: 'sem-sessao' }

export async function fetchHome(): Promise<ResultadoHome> {
  const response = await fetch('/api/v1/home')
  if (response.status === 401) return { tipo: 'sem-sessao' }
  if (!response.ok) throw new Error(`GET /v1/home failed with ${response.status}`)
  return { tipo: 'pronto', dados: (await response.json()) as HomeData }
}

export async function fetchPersonas(): Promise<Persona[]> {
  const response = await fetch('/api/v1/personas')
  if (!response.ok) throw new Error(`GET /v1/personas failed with ${response.status}`)
  return (await response.json()) as Persona[]
}

export async function entrarComo(personaId: string): Promise<void> {
  const response = await fetch('/api/v1/sessoes/demo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ persona_id: personaId }),
  })
  if (!response.ok) throw new Error(`POST /v1/sessoes/demo failed with ${response.status}`)
}

export type NovaSimulacao = {
  item: string
  valor_centavos: number
  prazo_meses: number
  entrada_centavos: number
  duracao_meses?: number
  consorcio_duracao_meses?: number
}

export type Financiamento = {
  duracao_meses: number
  parcela_centavos: number
  custo_total_centavos: number
  juros_centavos: number
  iof_centavos: number
  tarifas_centavos: number
  cet_mensal_percentual: string
  cet_anual_percentual: string
  taxa_mensal: string
  acima_da_margem: boolean
  duracoes_disponiveis: number[]
  ranking: TaxaInstituicao[]
  fonte: Fonte
  ressalvas: Ressalva[]
}

export type TaxaInstituicao = {
  instituicao: string
  taxa_mensal_percentual: string
  taxa_anual_percentual: string
}

export type Fonte = {
  descricao: string
  inicio_periodo: string
  fim_periodo: string
  url: string
}

export type Ressalva = {
  codigo: string
  texto: string
}

export type JanelaContemplacao = {
  melhor_caso_mes: number
  mediana_mes: number
  pior_caso_mes: number
  chance_ate_prazo_percentual: number
}

export type Consorcio = {
  carta_credito_centavos: number
  duracao_meses: number
  parcela_centavos: number
  custo_total_centavos: number
  taxa_administracao_centavos: number
  taxa_administracao_percentual: string
  fundo_reserva_centavos: number
  fundo_reserva_percentual: string
  reajuste_anual_percentual: string
  acima_da_margem: boolean
  janela: JanelaContemplacao
  duracoes_disponiveis: number[]
  ressalvas: Ressalva[]
}

export type Juntar = {
  deposito_mensal_centavos: number
  mes_compra: number | null
  custo_total_centavos: number | null
  preco_na_compra_centavos: number | null
  entrega_ate_prazo: boolean
  rendimento_anual_percentual: string
  ipca_anual_percentual: string
  fonte: { descricao: string; data_pesquisa: string; url: string }
  ressalvas: Ressalva[]
}

export type Caminho = 'financiamento' | 'consorcio' | 'juntar'

export type Recomendacao = {
  caminho: Caminho | null
  avaliacoes: { caminho: Caminho; motivo_codigo: string | null; motivo_texto: string | null }[]
  ressalvas: Ressalva[]
  ajustes: {
    entrada_minima_centavos: number | null
    prazo_minimo_meses: number | null
    valor_maximo_centavos: number | null
  } | null
}

export type Simulacao = {
  id: string
  snapshot_id: string
  objetivo: Omit<NovaSimulacao, 'duracao_meses' | 'consorcio_duracao_meses'>
  financiamento: Financiamento
  consorcio: Consorcio
  juntar: Juntar
  recomendacao: Recomendacao
}

export class ObjetivoInvalido extends Error {}

export async function criarSimulacao(dados: NovaSimulacao): Promise<Simulacao> {
  const response = await fetch('/api/v1/simulacoes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  })
  if (response.status === 422) throw new ObjetivoInvalido()
  if (!response.ok) throw new Error(`POST /v1/simulacoes failed with ${response.status}`)
  return (await response.json()) as Simulacao
}

export type ObjetivoConversa = {
  item: string | null
  valor_centavos: number | null
  prazo_meses: number | null
  entrada_centavos: number
}

export type RespostaCopiloto = {
  resposta: string
  objetivo: ObjetivoConversa
  faltando: string[]
  novo_objetivo: boolean
  simulacao: Simulacao | null
}

export async function criarConversa(): Promise<string> {
  const response = await fetch('/api/v1/conversas', { method: 'POST' })
  if (!response.ok) throw new Error(`POST /v1/conversas failed with ${response.status}`)
  return ((await response.json()) as { id: string }).id
}

export async function enviarMensagem(conversaId: string, texto: string): Promise<RespostaCopiloto> {
  const response = await fetch(`/api/v1/conversas/${conversaId}/mensagens`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto }),
  })
  if (!response.ok) throw new Error(`POST mensagens failed with ${response.status}`)
  return (await response.json()) as RespostaCopiloto
}
