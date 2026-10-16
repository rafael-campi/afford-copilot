import { useEffect, useState } from 'react'
import { entrarComo, fetchHome, type HomeData } from './api'
import { EscolherPersona } from './EscolherPersona'
import { Home } from './Home'

type Estado =
  | { tipo: 'carregando' }
  | { tipo: 'erro' }
  | { tipo: 'sem-sessao' }
  | { tipo: 'pronto'; dados: HomeData }

export function App() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' })

  useEffect(() => {
    let ativo = true
    fetchHome()
      .then((resultado) => ativo && setEstado(resultado))
      .catch(() => ativo && setEstado({ tipo: 'erro' }))
    return () => {
      ativo = false
    }
  }, [])

  async function escolher(personaId: string) {
    setEstado({ tipo: 'carregando' })
    try {
      await entrarComo(personaId)
      setEstado(await fetchHome())
    } catch {
      setEstado({ tipo: 'erro' })
    }
  }

  if (estado.tipo === 'sem-sessao') return <EscolherPersona onEscolher={escolher} />
  return <Home estado={estado} />
}
