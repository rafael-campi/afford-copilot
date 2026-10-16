import type { Simulacao } from './api'
import { formatarData, formatarPercentual, formatarReais } from './format'

type Props = {
  simulacao: Simulacao
  margemSeguraCentavos: number
  recalculando: boolean
  onDuracao: (duracaoMeses: number) => void
  onVoltar: () => void
}

export function Comparacao({ simulacao, margemSeguraCentavos, recalculando, onDuracao, onVoltar }: Props) {
  const { objetivo, financiamento: f } = simulacao
  const item = objetivo.item.charAt(0).toUpperCase() + objetivo.item.slice(1)

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">
          {item} de {formatarReais(objetivo.valor_centavos)}
        </h1>
        <p className="tela-texto">
          Até {objetivo.prazo_meses} meses · sua margem: até {formatarReais(margemSeguraCentavos)}
          /mês
        </p>
      </header>

      <article className="caminho" aria-labelledby="caminho-financiamento" aria-busy={recalculando}>
        <div className="caminho-topo">
          <h2 id="caminho-financiamento" className="caminho-titulo">
            Financiamento
          </h2>
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
        {f.ressalvas.length > 0 && (
          <ul className="ressalvas">
            {f.ressalvas.map((r) => (
              <li key={r.codigo} className="ressalva">
                {r.texto}
              </li>
            ))}
          </ul>
        )}
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
      </article>

      <p className="nota">Extrato fictício. Taxas reais publicadas pelo Banco Central.</p>
    </main>
  )
}
