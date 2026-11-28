# Worked examples and evidence status

Each example separates what was observed, what a public source says, and what remains a hypothesis.

## 1. Vendor normalization against the filing (November 2026)

**Situation.** A company-analysis platform used an aggregator (Yahoo Finance) as its main fundamentals source and added the issuers' own US SEC filings.

**Observed: internal measurement, not reproducible from this text.** The platform's data pipeline compared both sources on about 540 US issuers on 22 November 2026. It reported a difference of 5% or more on:
- 27–28% of operating-income values;
- 23–25% of capital-expenditure values, with 187 cases where the aggregator was at least twice the filing value;
- 11–18% of interest-expense values;
- 7–8% of SG&A, cost-of-revenue and buyback values.

These counts come from the platform's own run log. Use them as an example of scale, not as a benchmark.

**First instinct, which was rejected.** The team designed merge rules: precedence by line item, a divergence guard, and later "fill only where providers agree" or "one source for the whole series". The product owner rejected both final options and asked first to understand why the aggregator shows what it shows.

**Public source: the vendor's own documentation.** Yahoo Help article SLN37694, "Financial statements on Yahoo Finance are changing" (https://help.yahoo.com/kb/SLN37694.html, read 24 November 2026), states:
- the Financials tab uses a new dataset from Morningstar, its financial-statement data provider;
- some figures are calculated differently under the new methodology, including for past reporting periods;
- stock-based compensation is treated as a non-recurring item and sits below the operating income line, so companies with large stock programs show higher operating income;
- normalized earnings use a different method for identifying one-time items;
- EBIT uses interest net of interest earned;
- cash includes restricted cash.

The article does not define capital expenditure.

**Observed: the platform's own mapping.** The platform mapped filing capital expenditure only to `PaymentsToAcquirePropertyPlantAndEquipment`. A concept for intangible-asset purchases existed in its mapping code but was not published. Capitalized software and intangible purchases are separate cash-flow lines in many filings.

**Hypotheses before the reconstruction.**
- The aggregator's capital expenditure is approximately property and equipment, plus capitalized software, plus intangible purchases.
- The aggregator's operating income is approximately reported operating income plus stock-based compensation, plus some one-off items.

**Observed: the reconstruction (internal measurement, 25 November 2026, about 74 issuers with annual pairs).** "Agrees" means a difference below 5%.
- **Capital expenditure.** Property and equipment alone agreed on 240 of 293 pairs. Adding capitalized software and intangible purchases raised that to 264: 25 pairs fixed, 1 broken. This supports the first hypothesis without proving the vendor's method. Only 5 of those issuers reported software, so the overlap between lines could not be measured.
- **Operating income.** The filing figure alone already agreed on 193 of 294 pairs, with a median residual of 1.2%. Adding stock-based compensation made agreement *worse*: 121 pairs with the income-statement amount, 105 with the cash-flow amount. Restructuring and goodwill impairment fixed 20 pairs and broke 6. On this data the vendor's own documentation did not explain the gaps. About 80 pairs remain unexplained and stay unknown.
- **Interest.** The filing figure alone agreed on 152 of 185 pairs. Every variant tested, net of interest income or cash interest paid, made agreement worse.
- **Methodology change.** The platform's archive of vendor data began only months before the measurement and showed no bulk revision, so the change described in the documentation could not be dated.

The lesson for step 2: a vendor's documentation says what its methodology intends. It does not show how that methodology affects a given archive. Test the documented reason; do not assume it.

**Assessment of each vendor reason after the reconstruction.**
- *Reinvestment that includes software and intangibles:* sound for the question "how much the business must reinvest", and supported by the data. Many software companies subtract capitalized software in their own free-cash-flow definition. Recommendation: build it from the filing lines, with the composition visible, and add a line only when it is a separate line on the same cash-flow statement.
- *Stock-based compensation excluded from operating income:* debatable, because it is a real recurring cost, and not what explained the gaps here. Recommendation: show the reported figure, with stock-based compensation, restructuring and impairments beside it as named items.

**Illustrative candidate for "how much cash is left for owners", pending reconciliation.** Operating cash flow, minus reinvestment (property and equipment, capitalized software, intangible purchases), with stock-based compensation shown as an economic cost. It is not a universal formula. Before adopting it for an issuer:
- **Check for overlap between the reinvestment lines.** Some filers already include capitalized software in the property-and-equipment purchases line, and adding it again would count it twice.
- **State the rationale for the stock-based compensation adjustment.** It is not a cash outflow; operating cash flow adds it back. Subtracting it measures the economic cost of dilution, not cash spent. The alternative is to keep cash flow as reported and show dilution per share next to it. Name which one is used and why.
- **Build it from filing concepts**, with the composition and these choices shown.

**Integrity issue found on the way (observed in code).** A merge rule let the filing fill the periods the vendor lacked, even for pairs flagged as persistently divergent. Older years used one definition and recent years another. Year-over-year growth was computed across that seam and shown to users. That is the source of the "do not mix definitions in one series" guardrail.

## 2. A vendor "total debt" figure that hides what an investor needs

**Figure and discrepancy (observed in the platform's data inventory, 23 November 2026).** The aggregator supplied one "total debt" figure, plus "current debt" and debt "and lease obligations". The filing supplied separate concepts: non-current long-term debt, commercial paper and operating-lease liabilities. The open questions were whether the product's "debt" should include leases, and why the vendor's total differs from the sum of the filing lines. That meets the activation test.

**Step 1: the investor question.** "What can go wrong in the balance sheet?" A single total answers it badly. The investor needs to know:
- who lends, how much, at what rate and when it falls due;
- what the lenders take as collateral or guarantees;
- the covenants and what happens if they are breached;
- what triggers acceleration;
- which obligations behave like debt without being reported as debt, such as non-cancellable purchase commitments for compute, energy or capacity, and whether they depend on conditions such as available capacity;
- which counterparties have more than one role, for example a supplier that is also an investor or a customer.

**Steps 2–3: vendor reason against the original source.** The vendor's documentation for this figure was not checked, so its rationale is unknown. A *possible* rationale is quick comparison across companies: one number, with leases optionally included. Treat that as a hypothesis until the vendor's definition is found or the total is reconstructed. Either way, the filing holds far more:
- **Numbers:** debt-instrument facts with dimensions (`DebtInstrumentAxis`), credit-line capacity, unconditional purchase obligations by year, related-party amounts.
- **Text:**
  - credit agreements filed as exhibits;
  - current-report items 1.01 (material definitive agreement), 2.03 (direct financial obligation) and 2.04 (triggering events that accelerate an obligation);
  - the commitments and related-party notes;
  - the liquidity discussion;
  - the IPO registration statement, before the first annual report.

**Steps 4–6: recommendation (illustrative; not reconstructed on data).**
- Keep the vendor's total only as a comparison.
- Recommend explicit components: borrowings by instrument, leases and debt-like commitments, each named and cited.
- Recommend a reconciliation of the numbers with the contract text.
- Possible product views, subject to authorization:
  - a counterparty map with multi-role flags;
  - a timeline of maturities and commitments against cash;
  - the distance to each covenant, with the clause quoted;
  - alerts on the relevant current-report items.

No specific registration statement, credit agreement or annual report was analysed for this example. The reconstruction of the vendor's total from the filing lines was not run.

## Limits of this practice

- It slows down a decision that looks like plumbing. A reversible interim measure can limit harm while the "why" is investigated, if whoever holds the authority applies it.
- Vendor documentation can be thin or missing. The reconstruction is then the main evidence, and an unexplained residual stays unknown.
- Some differences are presentation conventions, such as the sign of outflows or labels. Those need normalization, not this procedure.
