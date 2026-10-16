export type ResumoOrcamento = {
  entradas_centavos: number
  gastos_centavos: number
  sobra_mensal_centavos: number
  margem_segura_centavos: number
}

export type Sugestao = {
  titulo: string
  descricao: string
}

export type HomeData = {
  placeholder: boolean
  nome: string
  resumo: ResumoOrcamento
  sugestoes: Sugestao[]
}

export async function fetchHome(): Promise<HomeData> {
  const response = await fetch('/api/v1/home')
  if (!response.ok) {
    throw new Error(`GET /v1/home failed with ${response.status}`)
  }
  return (await response.json()) as HomeData
}
