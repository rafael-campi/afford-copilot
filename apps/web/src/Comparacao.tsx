import type { Caminho, NovaSimulacao, Simulacao } from './api'
import { CardFinanciamento } from './CardFinanciamento'
import type { Destaque } from './Destaque'
import { PainelRecomendacao } from './PainelRecomendacao'
import { CardConsorcio } from './CardConsorcio'
import { CardJuntar } from './CardJuntar'
import { formatarReais } from './format'

type Props = {
  simulacao: Simulacao
  margemSeguraCentavos: number
  recalculando: boolean
  onMudar: (mudanca: Partial<NovaSimulacao>) => void
  onEscolher: (caminho: Caminho) => void
  onVoltar: () => void
}

export function Comparacao(props: Props) {
  const { simulacao, margemSeguraCentavos, recalculando, onMudar, onEscolher, onVoltar } = props
  const { objetivo, financiamento: f, recomendacao } = simulacao
  const item = objetivo.item.charAt(0).toUpperCase() + objetivo.item.slice(1)
  const destaque = (caminho: Caminho): Destaque => ({
    recomendado: recomendacao.caminho === caminho,
    porQueNao: recomendacao.avaliacoes.find((a) => a.caminho === caminho)?.motivo_texto ?? null,
  })

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

      <PainelRecomendacao recomendacao={recomendacao} item={objetivo.item} />

      <CardFinanciamento
        financiamento={f}
        recalculando={recalculando}
        destaque={destaque('financiamento')}
        onEscolher={() => onEscolher('financiamento')}
        onDuracao={(d) => onMudar({ duracao_meses: d })}
      />

      <CardConsorcio
        consorcio={simulacao.consorcio}
        recalculando={recalculando}
        destaque={destaque('consorcio')}
        onEscolher={() => onEscolher('consorcio')}
        onDuracao={(d) => onMudar({ consorcio_duracao_meses: d })}
      />

      <CardJuntar
        juntar={simulacao.juntar}
        item={objetivo.item}
        destaque={destaque('juntar')}
        onEscolher={() => onEscolher('juntar')}
      />

      <p className="nota">Extrato fictício. Taxas reais publicadas pelo Banco Central.</p>
    </main>
  )
}
