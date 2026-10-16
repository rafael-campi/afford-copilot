import type { Financiamento } from './api'
import { PorQueNao, SeloDestaque, type Destaque } from './Destaque'
import { formatarData, formatarPercentual, formatarReais } from './format'
import { Ressalvas } from './Ressalvas'

type Props = {
  financiamento: Financiamento
  recalculando: boolean
  destaque: Destaque
  onEscolher: () => void
  onDuracao: (duracaoMeses: number) => void
}

export function CardFinanciamento({ financiamento: f, recalculando, destaque, onDuracao, onEscolher }: Props) {
  return (
    <article
      className={destaque.recomendado ? 'caminho caminho-recomendado' : 'caminho'}
      aria-labelledby="caminho-financiamento"
      aria-busy={recalculando}
    >
      <div className="caminho-topo">
        <h2 id="caminho-financiamento" className="caminho-titulo">
          Financiamento
        </h2>
        <SeloDestaque destaque={destaque} />
        {f.acima_da_margem && <span className="selo selo-alerta">Acima da margem</span>}
      </div>
      <dl className="caminho-numeros">
        <div>
          <dt>Parcela</dt>
          <dd>{formatarReais(f.parcela_centavos)}</dd>
        </div>
        <div>
          <dt>Custo total</dt>
          <dd>{formatarReais(f.custo_total_centavos)}</dd>
        </div>
        <div>
          <dt>Item em mãos</dt>
          <dd>Imediato</dd>
        </div>
      </dl>
      <label className="caminho-duracao">
        <span>Duração</span>
        <select
          value={String(f.duracao_meses)}
          onChange={(e) => onDuracao(Number(e.target.value))}
          disabled={recalculando}
        >
          {f.duracoes_disponiveis.map((d) => (
            <option key={d} value={String(d)}>
              {d} meses
            </option>
          ))}
        </select>
      </label>
      <p className="caminho-texto">
        Você pagaria cerca de {formatarReais(f.juros_centavos)} só de juros, com a taxa mediana
        do mercado de {formatarPercentual(String(Number(f.taxa_mensal) * 100))} ao mês.
      </p>
      <div className="cet">
        <p className="cet-titulo">
          CET estimado: {formatarPercentual(f.cet_anual_percentual)} ao ano (
          {formatarPercentual(f.cet_mensal_percentual)} ao mês)
        </p>
        <table className="cet-partes">
          <caption>Quanto você paga além do valor financiado</caption>
          <tbody>
            <tr>
              <th scope="row">Juros</th>
              <td>{formatarReais(f.juros_centavos)}</td>
            </tr>
            <tr>
              <th scope="row">IOF</th>
              <td>{formatarReais(f.iof_centavos)}</td>
            </tr>
            <tr>
              <th scope="row">Tarifas</th>
              <td>{formatarReais(f.tarifas_centavos)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <PorQueNao destaque={destaque} />
      <Ressalvas ressalvas={f.ressalvas} />
      <details className="ranking">
        <summary>Ver taxas de {f.ranking.length} instituições</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">Instituição</th>
              <th scope="col">Taxa ao mês</th>
            </tr>
          </thead>
          <tbody>
            {f.ranking.map((t) => (
              <tr key={t.instituicao}>
                <td>{t.instituicao}</td>
                <td>{formatarPercentual(t.taxa_mensal_percentual)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      <p className="nota">
        Fonte: Banco Central do Brasil, {formatarData(f.fonte.inicio_periodo)} a{' '}
        {formatarData(f.fonte.fim_periodo)}.{' '}
        <a href={f.fonte.url} target="_blank" rel="noreferrer">
          Ver no site do BCB
        </a>
      </p>
      <button type="button" className="escolher secondary-button" onClick={onEscolher}>
        Escolher este caminho
      </button>
    </article>
  )
}
