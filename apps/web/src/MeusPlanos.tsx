import { useEffect, useState } from 'react'
import { fetchPlanos, type PlanoResumido } from './api'
import { formatarData } from './format'
import { NOME_CAMINHO } from './nomes'

type Props = { onAbrir: (id: string) => void; onVoltar: () => void }

export function MeusPlanos({ onAbrir, onVoltar }: Props) {
  const [planos, setPlanos] = useState<PlanoResumido[] | null>(null)

  useEffect(() => {
    let ativo = true
    fetchPlanos()
      .then((lista) => ativo && setPlanos(lista))
      .catch(() => ativo && setPlanos([]))
    return () => {
      ativo = false
    }
  }, [])

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">Meus planos</h1>
      </header>
      {planos && planos.length === 0 && <p className="tela-texto">Você ainda não salvou nenhum plano.</p>}
      <ul className="personas">
        {(planos ?? []).map((p) => (
          <li key={p.id}>
            <button type="button" className="persona" onClick={() => onAbrir(p.id)}>
              <span className="persona-nome">
                {p.item} · {NOME_CAMINHO[p.caminho]} · {formatarData(p.criado_em)}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </main>
  )
}
