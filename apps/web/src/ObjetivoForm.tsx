import { useState, type FormEvent } from 'react'
import type { NovaSimulacao } from './api'
import { lerReais } from './format'

type Props = {
  erro: string | null
  enviando: boolean
  onSimular: (dados: NovaSimulacao) => void
  onVoltar: () => void
}

export function ObjetivoForm({ erro, enviando, onSimular, onVoltar }: Props) {
  const [item, setItem] = useState('')
  const [valor, setValor] = useState('')
  const [prazo, setPrazo] = useState('')
  const [entrada, setEntrada] = useState('')

  function enviar(event: FormEvent) {
    event.preventDefault()
    onSimular({
      item: item.trim(),
      valor_centavos: lerReais(valor),
      prazo_meses: Number(prazo),
      entrada_centavos: lerReais(entrada),
    })
  }

  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <button type="button" className="voltar" onClick={onVoltar}>
          Voltar
        </button>
        <h1 className="tela-titulo">Seu objetivo</h1>
        <p className="tela-texto">Conte o que você quer comprar e até quando quer ter o item.</p>
      </header>

      <form className="formulario" onSubmit={enviar}>
        <label className="campo">
          <span>O que você quer comprar?</span>
          <input id="item" required value={item} onChange={(e) => setItem(e.target.value)}
            placeholder="carro" />
        </label>
        <label className="campo">
          <span>Valor do item (R$)</span>
          <input id="valor" required inputMode="decimal" value={valor}
            onChange={(e) => setValor(e.target.value)} placeholder="80.000" />
        </label>
        <label className="campo">
          <span>Prazo para ter o item (meses)</span>
          <input id="prazo" required inputMode="numeric" value={prazo}
            onChange={(e) => setPrazo(e.target.value.replace(/\D/g, ''))} placeholder="60" />
        </label>
        <label className="campo">
          <span>Entrada (R$, opcional)</span>
          <input id="entrada" inputMode="decimal" value={entrada}
            onChange={(e) => setEntrada(e.target.value)} placeholder="0" />
        </label>

        {erro && (
          <p className="aviso" role="alert">
            {erro}
          </p>
        )}

        <button type="submit" className="primary-button" disabled={enviando}>
          {enviando ? 'Simulando…' : 'Simular'}
        </button>
      </form>
    </main>
  )
}
