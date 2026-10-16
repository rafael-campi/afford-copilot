import { useState, type FormEvent } from 'react'
import type { GastoCategoria, ObjetivoConversa, ResumoOrcamento, Simulacao } from './api'
import { formatarReais } from './format'

export type Mensagem = { autor: 'pessoa' | 'copiloto'; texto: string }

type Props = {
  mensagens: Mensagem[]
  objetivo: ObjetivoConversa | null
  cenarios: Simulacao[]
  resumo: ResumoOrcamento
  gastos: GastoCategoria[]
  enviando: boolean
  erro: string | null
  onEnviar: (texto: string) => void
  onComparar: () => void
  onVerCenario: (indice: number) => void
  onVoltar: () => void
}

export function Conversa(props: Props) {
  const { mensagens, objetivo, cenarios, resumo, gastos, enviando, erro } = props
  const { onEnviar, onComparar, onVerCenario, onVoltar } = props
  const [texto, setTexto] = useState('')

  function enviar(event: FormEvent) {
    event.preventDefault()
    const limpo = texto.trim()
    if (!limpo) return
    setTexto('')
    onEnviar(limpo)
  }

  return (
    <main className="tela conversa">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">Copiloto</h1>
      </header>

      <ol className="mensagens" aria-live="polite">
        {mensagens.map((m, i) => (
          <li key={i} className={`mensagem mensagem-${m.autor}`}>
            {m.texto}
          </li>
        ))}
        {enviando && <li className="mensagem mensagem-copiloto">Pensando…</li>}
      </ol>

      {objetivo && objetivo.item && <ChipsObjetivo objetivo={objetivo} />}

      {objetivo && objetivo.item && gastos.length > 0 && (
        <Orcamento resumo={resumo} gastos={gastos} />
      )}

      {erro && (
        <p className="aviso" role="alert">
          {erro}
        </p>
      )}

      {cenarios.length > 1 && <Cenarios cenarios={cenarios} onVer={onVerCenario} />}

      {cenarios.length > 0 && (
        <button type="button" className="primary-button" onClick={onComparar}>
          Comparar as 3 opções
        </button>
      )}

      <form className="conversa-campo" onSubmit={enviar}>
        <input
          id="mensagem"
          aria-label="Mensagem"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="E se eu der uma entrada?"
        />
        <button type="submit" className="enviar" disabled={enviando}>
          Enviar
        </button>
      </form>
    </main>
  )
}

function ChipsObjetivo({ objetivo }: { objetivo: ObjetivoConversa }) {
  return (
    <ul className="chips" aria-label="O que entendi">
      <li className="chip">{objetivo.item}</li>
      {objetivo.valor_centavos !== null && (
        <li className="chip">{formatarReais(objetivo.valor_centavos)}</li>
      )}
      {objetivo.prazo_meses !== null && <li className="chip">até {objetivo.prazo_meses} meses</li>}
      <li className="chip">
        {objetivo.entrada_centavos > 0
          ? `Entrada de ${formatarReais(objetivo.entrada_centavos)}`
          : 'sem Entrada'}
      </li>
    </ul>
  )
}

const NOMES_CAMINHO: Record<string, string> = {
  financiamento: 'financiamento',
  consorcio: 'consórcio',
  juntar: 'juntar',
}

function Cenarios({ cenarios, onVer }: { cenarios: Simulacao[]; onVer: (indice: number) => void }) {
  return (
    <ul className="cenarios" aria-label="Cenários desta conversa">
      {cenarios.map((s, i) => {
        const entrada =
          s.objetivo.entrada_centavos > 0
            ? `Entrada de ${formatarReais(s.objetivo.entrada_centavos)}`
            : 'sem Entrada'
        const caminho = s.recomendacao.caminho
        return (
          <li key={s.id} className="cenario">
            <span>
              Cenário {i + 1}: {entrada} · recomendado:{' '}
              {caminho ? NOMES_CAMINHO[caminho] : 'nenhum'}
            </span>
            <button type="button" className="link-button" onClick={() => onVer(i)}>
              <span className="visualmente-oculto">Ver cenário {i + 1}</span>
              <span aria-hidden="true">Ver</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}

const PRINCIPAIS = 3

function Orcamento({ resumo, gastos }: { resumo: ResumoOrcamento; gastos: GastoCategoria[] }) {
  const principais = gastos.filter((g) => g.categoria !== 'Outros').slice(0, PRINCIPAIS)
  const resto = gastos
    .filter((g) => !principais.includes(g))
    .reduce((total, g) => total + g.centavos, 0)
  const linhas = resto > 0 ? [...principais, { categoria: 'Outros', centavos: resto }] : principais
  return (
    <section className="orcamento-conversa">
      <ul className="gastos" aria-label="Para onde vai seu dinheiro">
        {linhas.map((g) => (
          <li key={g.categoria}>
            <span>{g.categoria}</span>
            <span>{formatarReais(g.centavos)}</span>
          </li>
        ))}
      </ul>
      <p className="caminho-texto">
        Sobram cerca de {formatarReais(resumo.sobra_mensal_centavos)}/mês. Sua margem segura é de
        até {formatarReais(resumo.margem_segura_centavos)} por mês.
      </p>
    </section>
  )
}
