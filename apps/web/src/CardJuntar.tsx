import type { Juntar } from './api'
import { formatarData, formatarPercentual, formatarReais } from './format'
import { PorQueNao, SeloDestaque, type Destaque } from './Destaque'
import { Ressalvas } from './Ressalvas'

type Props = { juntar: Juntar; item: string; destaque: Destaque; onEscolher: () => void }

export function CardJuntar({ juntar: j, item, destaque, onEscolher }: Props) {
  return (
    <article
      className={destaque.recomendado ? 'caminho caminho-recomendado' : 'caminho'}
      aria-labelledby="caminho-juntar"
    >
      <div className="caminho-topo">
        <h2 id="caminho-juntar" className="caminho-titulo">
          Juntar e comprar à vista
        </h2>
        <SeloDestaque destaque={destaque} />
        {!j.entrega_ate_prazo && <span className="selo selo-alerta">Depois do Prazo</span>}
      </div>
      <dl className="caminho-numeros">
        <div>
          <dt>Por mês</dt>
          <dd>{formatarReais(j.deposito_mensal_centavos)}</dd>
        </div>
        <div>
          <dt>Custo total</dt>
          <dd>{j.custo_total_centavos === null ? '—' : formatarReais(j.custo_total_centavos)}</dd>
        </div>
        <div>
          <dt>Item em mãos</dt>
          <dd>{j.mes_compra === null ? '—' : `mês ${j.mes_compra}`}</dd>
        </div>
      </dl>
      {j.mes_compra === null || j.preco_na_compra_centavos === null ? (
        <p className="caminho-texto">Não alcança o preço em 20 anos</p>
      ) : (
        <p className="caminho-texto">
          O {item} deve custar {formatarReais(j.preco_na_compra_centavos)} quando você comprar.
        </p>
      )}
      <p className="caminho-texto">
        Considera depositar sua margem todo mês, com rendimento de referência de{' '}
        {formatarPercentual(j.rendimento_anual_percentual)} ao ano e IPCA de{' '}
        {formatarPercentual(j.ipca_anual_percentual)} no preço.
      </p>
      <PorQueNao destaque={destaque} />
      <Ressalvas ressalvas={j.ressalvas} />
      <p className="nota">
        Fonte: pesquisa Focus do Banco Central de {formatarData(j.fonte.data_pesquisa)}.{' '}
        <a href={j.fonte.url} target="_blank" rel="noreferrer">
          Ver no site do BCB
        </a>
      </p>
      <button type="button" className="escolher secondary-button" onClick={onEscolher}>
        Escolher este caminho
      </button>
    </article>
  )
}
