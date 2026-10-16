export function SemExtrato({ onSair }: { onSair: () => void }) {
  return (
    <main className="tela">
      <header className="tela-cabecalho">
        <h1 className="tela-titulo">Conecte seu banco</h1>
        <p className="tela-texto">
          Para calcular quanto cabe no seu orçamento, o copiloto precisa do seu extrato. Em breve
          você poderá conectar seu banco ou importar um arquivo do extrato.
        </p>
      </header>
      <button type="button" className="link-button" onClick={onSair}>
        Sair
      </button>
    </main>
  )
}
