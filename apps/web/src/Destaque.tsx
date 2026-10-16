export type Destaque = {
  recomendado: boolean
  porQueNao: string | null
}

export function SeloDestaque({ destaque }: { destaque: Destaque }) {
  return destaque.recomendado ? <span className="selo selo-ok">Recomendado</span> : null
}

export function PorQueNao({ destaque }: { destaque: Destaque }) {
  if (destaque.recomendado || !destaque.porQueNao) return null
  return <p className="por-que-nao">Por que não: {destaque.porQueNao}</p>
}
