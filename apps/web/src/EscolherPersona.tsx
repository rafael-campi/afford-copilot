import { useEffect, useState, type ReactNode } from 'react'
import { fetchPersonas, type Persona } from './api'

type Props = { onEscolher: (personaId: string) => void; children?: ReactNode }

export function EscolherPersona({ onEscolher, children }: Props) {
  const [personas, setPersonas] = useState<Persona[] | null>(null)
  const [erro, setErro] = useState(false)

  useEffect(() => {
    let ativo = true
    fetchPersonas()
      .then((lista) => ativo && setPersonas(lista))
      .catch(() => ativo && setErro(true))
    return () => {
      ativo = false
    }
  }, [])

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <h1 className="tela-titulo">Escolha uma Persona</h1>
        <p className="tela-texto">
          Cada Persona é um cliente fictício com um extrato de 3 meses. Escolha uma para ver o
          copiloto trabalhando com os números dela.
        </p>
      </header>

      {erro && (
        <p className="aviso" role="alert">
          Não foi possível carregar as Personas. Tente de novo em alguns instantes.
        </p>
      )}

      {personas && (
        <ul className="personas">
          {personas.map((persona) => (
            <li key={persona.id}>
              <button type="button" className="persona" onClick={() => onEscolher(persona.id)}>
                <span className="persona-topo">
                  <span className="persona-nome">{persona.nome}</span>
                  <span className="persona-perfil">{persona.perfil}</span>
                </span>
                <span className="persona-descricao">{persona.descricao}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {children}
    </main>
  )
}
