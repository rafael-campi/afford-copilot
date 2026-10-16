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
