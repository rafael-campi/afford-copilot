import type { Recomendacao } from './api'
import { formatarReais } from './format'

export function PainelRecomendacao({ recomendacao, item }: { recomendacao: Recomendacao; item: string }) {
  if (recomendacao.caminho === null) {
    const ajustes = recomendacao.ajustes
    return (
      <section className="painel-sem-caminho" aria-labelledby="sem-caminho">
        <h2 id="sem-caminho" className="painel-titulo">
          Nenhum caminho cabe hoje
        </h2>
        <p className="caminho-texto">
          Nenhuma opção entrega o {item} no seu Prazo com uma parcela dentro da sua margem. Uma
          destas mudanças resolveria:
        </p>
        {ajustes && (
          <ul className="ajustes">
            {ajustes.entrada_minima_centavos !== null && (
              <li>Dar uma Entrada de {formatarReais(ajustes.entrada_minima_centavos)}</li>
            )}
            {ajustes.prazo_minimo_meses !== null && (
              <li>Aceitar um Prazo de {ajustes.prazo_minimo_meses} meses</li>
            )}
            {ajustes.valor_maximo_centavos !== null && (
              <li>
                Escolher um {item} de até {formatarReais(ajustes.valor_maximo_centavos)}
              </li>
            )}
          </ul>
        )}
      </section>
    )
  }

  if (recomendacao.ressalvas.length === 0) return null
  return (
    <aside className="ressalva" role="note" aria-label="Atenção à recomendação">
      {recomendacao.ressalvas.map((r) => (
        <p key={r.codigo}>{r.texto}</p>
      ))}
    </aside>
  )
}
