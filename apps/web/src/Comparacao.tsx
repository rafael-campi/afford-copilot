import type { Simulacao } from './api'
import { formatarReais } from './format'

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
          Você pagaria cerca de {formatarReais(f.juros_centavos)} só de juros, com taxa de{' '}
          {(Number(f.taxa_mensal) * 100).toLocaleString('pt-BR')}% ao mês.
        </p>
      </article>

      <p className="nota">Simulação com dados fictícios e taxa de referência fixa.</p>
    </main>
  )
}
