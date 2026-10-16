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
