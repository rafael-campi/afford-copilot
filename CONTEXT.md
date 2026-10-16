# Afford

An independent AI copilot that helps a person decide how to pay for a big purchase (consórcio, financing, or saving until buying in cash) from their own statement, without selling any financial product.

## Language

### The request

**Objetivo**:
What the customer wants to acquire, as stated in natural language and parsed into item, value, Prazo and Entrada.
_Avoid_: Goal, meta, pedido (use "pedido" only for the raw text the customer typed)

**Prazo**:
The latest date by which the customer wants the item in hand ("em até 5 anos"). It is a deadline for having the item, not the number of payments.
_Avoid_: Term, urgência, número de parcelas

**Entrada**:
The amount the customer pays up front from their own money.
_Avoid_: Down payment, sinal

**Duração**:
The number of monthly payments in a Caminho; by default the smallest one whose payment fits the Margem segura.
_Avoid_: Prazo, term, número de parcelas

### The budget

**Extrato**:
The customer's account transactions the copilot analyzes, obtained through a Consentimento or an Importação.
_Avoid_: Statement data, histórico

**Consentimento**:
The customer's explicit, scoped, time-limited and revocable authorization for Afford to read their Extrato from a bank, in the style of Open Finance Brasil.
_Avoid_: Permission, login, conexão

**Importação**:
The customer uploading an Extrato file exported from their bank, as an alternative to a Consentimento.
_Avoid_: Upload, integração

**Persona**:
One of a small fixed set of synthetic customers, each with a reproducible bank statement, chosen at login in the public demo.
_Avoid_: Test user, mock user

**Sobra mensal**:
Average monthly income minus average monthly spending over the last 3 months.
_Avoid_: Surplus, saldo, folga

**Margem segura**:
The highest monthly payment the copilot considers safe for this customer: a fixed share of net monthly income (default 30%).
_Avoid_: Limite, teto, budget

### The paths

**Caminho**:
One of the three ways to pay for an Objetivo: Consórcio, Financiamento or Juntar e comprar à vista.
_Avoid_: Option, modalidade, produto

**Consórcio**:
A group of people paying monthly into a common fund; each month members are awarded a Carta de crédito by Sorteio or Lance. No interest, but a Taxa de administração.

**Carta de crédito**:
The credit amount a consórcio member receives when awarded.

**Contemplação**:
Being awarded the Carta de crédito, by Sorteio (draw) or Lance (bid).

**Janela de contemplação**:
The range of months in which a consórcio member may be awarded: best case, median and worst case, plus the chance of being awarded by the Prazo.
_Avoid_: "Sorteio/lance" as a delivery time

**Lance**:
An offer to prepay installments in order to be awarded earlier.

**Taxa de administração**:
The consórcio administrator's fee, a percentage of the Carta de crédito spread over the Prazo.

**Fundo de reserva**:
An additional percentage that covers group shortfalls.

**CET (Custo Efetivo Total)**:
The total effective cost of a loan, combining interest, fees, taxes and insurance into one rate.

**Tabela Price**:
Fixed-payment amortization schedule.

**Simulação**:
One computation of all three Caminhos for an Objetivo's current parameters. A follow-up that changes a parameter produces a new Simulação; earlier ones are kept for comparison.

**Recomendação**:
The single Caminho chosen by a fixed rule from a Simulação: delivers by the Prazo, fits the Margem segura, lowest total cost. When no Caminho qualifies there is no Recomendação, only suggested adjustments.
_Avoid_: Sugestão, melhor opção

**Ressalva**:
A warning attached to a Caminho or recommendation that the customer must see, such as a payment above the Sobra mensal, an uncertain Contemplação, or a rate that is only an institution's average.
_Avoid_: Disclaimer, aviso legal

**Plano**:
The Caminho the customer chose, with the parameters and Ressalvas of its simulation, saved for later. Saving a Plano contracts nothing.
_Avoid_: Contrato, proposta, pedido

**Juntar e comprar à vista**:
The Caminho where the customer deposits the Margem segura monthly at the Rendimento de referência until it covers the item's projected price.
_Avoid_: Poupança (that is a specific product), investir

**Rendimento de referência**:
The generic yield assumed for Juntar e comprar à vista (100% of the projected CDI, net of income tax). It stands for no specific investment product.
_Avoid_: Investimento recomendado, CDB, Tesouro
