import { vi } from 'vitest'

export type Rota = (init?: RequestInit) => Response

export function fakeApi(rotas: Record<string, Rota>) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const chave = `${init?.method ?? 'GET'} ${url}`
    const rota = rotas[chave]
    if (!rota) throw new Error(`Unexpected request: ${chave}`)
    return rota(init)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status })

export const homeBruno = {
  nome: 'Bruno',
  resumo: {
    entradas_centavos: 680_000,
    gastos_centavos: 490_000,
    sobra_mensal_centavos: 190_000,
    margem_segura_centavos: 204_000,
    margem_acima_da_sobra: true,
  },
  sugestoes: [],
}
