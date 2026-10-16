import { useState } from 'react'
import type { PlanoInfo } from './api'
import { formatarReais } from './format'
import { NOME_CAMINHO } from './nomes'
import { Ressalvas } from './Ressalvas'

type Props = {
  plano: PlanoInfo
  modo: 'revisao' | 'salvo' | 'leitura'
  salvando?: boolean
  onSalvar?: () => void
  onVoltar: () => void
}

export function RevisaoPlano({ plano, modo, salvando, onSalvar, onVoltar }: Props) {
  const [entendi, setEntendi] = useState(false)
  const r = plano.resumo
  const titulo =
    modo === 'revisao' ? 'Revise antes de salvar' : modo === 'salvo' ? 'Plano salvo' : 'Seu plano'

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">{titulo}</h1>
      </header>

      <section className="caminho caminho-recomendado" aria-labelledby="plano-titulo">
        <h2 id="plano-titulo" className="caminho-titulo">
          Seu plano
        </h2>
        <p className="caminho-texto">
          {NOME_CAMINHO[plano.caminho]} · {r.item} de {formatarReais(r.valor_centavos)}
        </p>
        <dl className="caminho-numeros">
          <div>
            <dt>{plano.caminho === 'juntar' ? 'Por mês' : 'Parcela'}</dt>
            <dd>{formatarReais(r.parcela_centavos)}</dd>
          </div>
          <div>
            <dt>Custo total</dt>
            <dd>{r.custo_total_centavos === null ? '—' : formatarReais(r.custo_total_centavos)}</dd>
          </div>
          <div>
            <dt>Item em mãos</dt>
            <dd>{r.item_em_maos}</dd>
          </div>
        </dl>
        <Ressalvas ressalvas={plano.ressalvas} />
      </section>

      <section className="orcamento-conversa" aria-labelledby="simples-titulo">
        <h2 id="simples-titulo" className="painel-titulo">
          Em linguagem simples
        </h2>
        <p className="caminho-texto">{plano.explicacao.texto}</p>
        {plano.explicacao.fontes.length > 0 && (
          <ul className="citacoes" aria-label="Regras na fonte oficial">
            {plano.explicacao.fontes.map((f) => (
              <li key={`${f.documento}-${f.rotulo}`}>
                <a href={f.url} target="_blank" rel="noreferrer">
                  {f.documento}, {f.rotulo}
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>

      {modo === 'revisao' ? (
        <>
          <label className="escopo">
            <input type="checkbox" checked={entendi} onChange={(e) => setEntendi(e.target.checked)} />
            <span>Entendi que nada é contratado</span>
          </label>
          <button
            type="button"
            className="primary-button"
            disabled={!entendi || salvando}
            onClick={onSalvar}
          >
            Salvar plano
          </button>
        </>
      ) : (
        <p className="aviso">{plano.aviso}</p>
      )}
      <p className="nota">Simulado com os dados de mercado {plano.snapshot_id}.</p>
    </main>
  )
}
