const brl = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
})

export function formatarReais(centavos: number): string {
  return brl.format(Math.round(centavos / 100))
}

export function saudacao(hora: number): string {
  if (hora >= 5 && hora < 12) return 'Bom dia,'
  if (hora >= 12 && hora < 18) return 'Boa tarde,'
  return 'Boa noite,'
}

/** Reads an amount typed in reais ("80.000", "80000", "1.234,56") as centavos. */
export function lerReais(texto: string): number {
  const limpo = texto.replace(/[^\d,]/g, '')
  const [inteiro = '0', fracao = ''] = limpo.split(',')
  return Number(inteiro || '0') * 100 + Number(fracao.padEnd(2, '0').slice(0, 2))
}
