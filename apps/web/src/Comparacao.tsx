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
  onVoltar: () => void
}

export function Comparacao({ simulacao, margemSeguraCentavos, recalculando, onMudar, onVoltar }: Props) {
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
        onDuracao={(d) => onMudar({ duracao_meses: d })}
      />

      <CardConsorcio
        consorcio={simulacao.consorcio}
        recalculando={recalculando}
        destaque={destaque('consorcio')}
        onDuracao={(d) => onMudar({ consorcio_duracao_meses: d })}
      />

      <CardJuntar juntar={simulacao.juntar} item={objetivo.item} destaque={destaque('juntar')} />

      <p className="nota">Extrato fictício. Taxas reais publicadas pelo Banco Central.</p>
    </main>
  )
}
