# 07: Juntar e comprar à vista Caminho

**What to build:** The comparison shows a saving card with monthly deposit, total cost and projected purchase date, accounting for yield and for the vehicle's price rising with inflation.

**Blocked by:** 04 (Real BCB rates per institution)

**Status:** ready-for-agent

- [ ] An ingestion job fetches Focus projections for Selic/CDI and IPCA into the same snapshot mechanism
- [ ] Monthly deposit is the Margem segura; yield is the Rendimento de referência (100% projected CDI net of income tax)
- [ ] The vehicle price is adjusted by projected IPCA; total cost is the sum of deposits
- [ ] The card shows the assumptions, their source and date, and the 'não é promessa de rendimento' Ressalva
- [ ] No investment product is named anywhere
- [ ] Simulador tests cover the purchase date and totals
