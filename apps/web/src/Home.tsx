import { useEffect, useState } from 'react'
import { fetchHome, type HomeData } from './api'
import { formatarReais, saudacao } from './format'

type Estado =
  | { tipo: 'carregando' }
  | { tipo: 'erro' }
  | { tipo: 'pronto'; dados: HomeData }

export function Home() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' })
  const [pedido, setPedido] = useState('')
  const [hora] = useState(() => new Date().getHours())

  useEffect(() => {
    let ativo = true
    fetchHome()
      .then((dados) => ativo && setEstado({ tipo: 'pronto', dados }))
      .catch(() => ativo && setEstado({ tipo: 'erro' }))
    return () => {
      ativo = false
    }
  }, [])

  return (
    <main className="home">
      <header className="home-header">
        <div className="saudacao">
          <span className="saudacao-texto">{saudacao(hora)}</span>
          <span className="saudacao-nome">
            {estado.tipo === 'pronto' ? estado.dados.nome : ' '}
          </span>
        </div>
        <button type="button" className="icon-button" aria-label="Perfil">
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" />
          </svg>
        </button>
      </header>

      <Resumo estado={estado} />

      <form className="objetivo" onSubmit={(event) => event.preventDefault()}>
        <label htmlFor="pedido" className="objetivo-label">
          O que você quer conquistar?
        </label>
        <div className="objetivo-campo">
          <input
            id="pedido"
            value={pedido}
            onChange={(event) => setPedido(event.target.value)}
            placeholder="Quero um carro de 80 mil em até 5 anos"
          />
          <button type="button" className="mic-button" aria-label="Falar">
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <rect x="9" y="3" width="6" height="11" rx="3" />
              <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
            </svg>
          </button>
        </div>
        <button type="submit" className="primary-button">
          Analisar minhas opções
        </button>
      </form>

      {estado.tipo === 'pronto' && estado.dados.sugestoes.length > 0 && (
        <section className="sugestoes" aria-labelledby="sugestoes-titulo">
          <h2 id="sugestoes-titulo" className="eyebrow">Sugestões para você</h2>
          {estado.dados.sugestoes.map((sugestao) => (
            <button type="button" key={sugestao.titulo} className="sugestao">
              <span className="sugestao-titulo">{sugestao.titulo}</span>
              <span className="sugestao-descricao">{sugestao.descricao}</span>
            </button>
          ))}
        </section>
      )}
    </main>
  )
}

function Resumo({ estado }: { estado: Estado }) {
  if (estado.tipo === 'erro') {
    return (
      <section className="resumo" role="alert">
        <span className="resumo-rotulo">Não foi possível carregar seu resumo.</span>
        <span className="resumo-rotulo">Tente de novo em alguns instantes.</span>
      </section>
    )
  }

  if (estado.tipo === 'carregando') {
    return (
      <section className="resumo" aria-busy="true">
        <span className="resumo-rotulo">Carregando seu resumo…</span>
      </section>
    )
  }

  const { resumo } = estado.dados
  return (
    <section className="resumo" aria-label="Resumo do mês">
      <span className="resumo-rotulo">Quanto sobra por mês (média de 3 meses)</span>
      <span className="resumo-valor">{formatarReais(resumo.sobra_mensal_centavos)}</span>
      <dl className="resumo-linha">
        <div>
          <dt>Entradas</dt>
          <dd>{formatarReais(resumo.entradas_centavos)}</dd>
        </div>
        <div>
          <dt>Gastos</dt>
          <dd>{formatarReais(resumo.gastos_centavos)}</dd>
        </div>
        <div>
          <dt>Margem segura</dt>
          <dd>{formatarReais(resumo.margem_segura_centavos)}</dd>
        </div>
      </dl>
    </section>
  )
}
