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
}

export type Financiamento = {
  duracao_meses: number
  parcela_centavos: number
  custo_total_centavos: number
  juros_centavos: number
  taxa_mensal: string
  acima_da_margem: boolean
  duracoes_disponiveis: number[]
}

export type Simulacao = {
  id: string
  snapshot_id: string
  objetivo: Omit<NovaSimulacao, 'duracao_meses'>
  financiamento: Financiamento
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
