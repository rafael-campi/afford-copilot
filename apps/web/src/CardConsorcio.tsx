import type { Consorcio } from './api'
import { PorQueNao, SeloDestaque, type Destaque } from './Destaque'
import { Ressalvas } from './Ressalvas'
import { formatarPercentual, formatarReais } from './format'

type Props = {
  consorcio: Consorcio
  recalculando: boolean
  destaque: Destaque
  onDuracao: (duracaoMeses: number) => void
}

export function CardConsorcio({ consorcio: c, recalculando, destaque, onDuracao }: Props) {
  const { janela } = c
  const posicao = (mes: number) =>
    `${((mes - 1) / Math.max(janela.pior_caso_mes - 1, 1)) * 100}%`

  return (
    <article
      className={destaque.recomendado ? 'caminho caminho-recomendado' : 'caminho'}
      aria-labelledby="caminho-consorcio"
      aria-busy={recalculando}
    >
      <div className="caminho-topo">
        <h2 id="caminho-consorcio" className="caminho-titulo">
          Consórcio
        </h2>
        <SeloDestaque destaque={destaque} />
        {c.acima_da_margem && <span className="selo selo-alerta">Acima da margem</span>}
      </div>
      <dl className="caminho-numeros">
        <div>
          <dt>Parcela</dt>
          <dd>{formatarReais(c.parcela_centavos)}</dd>
        </div>
        <div>
          <dt>Custo total</dt>
          <dd>{formatarReais(c.custo_total_centavos)}</dd>
        </div>
        <div>
          <dt>Item em mãos</dt>
          <dd>Sorteio ou lance</dd>
        </div>
      </dl>

      <div className="janela">
        <p className="janela-titulo">Janela de contemplação</p>
        <div className="janela-trilho" aria-hidden="true">
          <i style={{ left: posicao(janela.melhor_caso_mes) }} />
          <i style={{ left: posicao(janela.mediana_mes) }} />
          <i style={{ left: posicao(janela.pior_caso_mes) }} />
        </div>
        <p className="janela-marcos">
          <span>mês {janela.melhor_caso_mes} com lance</span>
          <span>mês {janela.mediana_mes} na mediana</span>
          <span>até o mês {janela.pior_caso_mes}</span>
        </p>
        <p className="caminho-texto">
          {janela.chance_ate_prazo_percentual}% de chance de sair por sorteio até o seu Prazo.
        </p>
      </div>

      <label className="caminho-duracao">
        <span>Duração do grupo</span>
        <select
          value={String(c.duracao_meses)}
          onChange={(e) => onDuracao(Number(e.target.value))}
          disabled={recalculando}
        >
          {c.duracoes_disponiveis.map((d) => (
            <option key={d} value={String(d)}>
              {d} meses
            </option>
          ))}
        </select>
      </label>
      <p className="caminho-texto">
        Taxa de administração de {formatarPercentual(c.taxa_administracao_percentual)}, fundo de
        reserva de {formatarPercentual(c.fundo_reserva_percentual)} e reajuste anual estimado de{' '}
        {formatarPercentual(c.reajuste_anual_percentual)} na carta e nas parcelas.
      </p>
      <PorQueNao destaque={destaque} />
      <Ressalvas ressalvas={c.ressalvas} />
    </article>
  )
}
