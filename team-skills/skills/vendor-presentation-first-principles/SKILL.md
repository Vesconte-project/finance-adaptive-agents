---
name: vendor-presentation-first-principles
description: Use when a specific issuer-reported financial figure (from company filings such as annual and quarterly reports) has an unresolved definition, source or comparability question tied to a vendor or aggregator, either because the vendor's value differs from the issuer's original filing or from another provider, or because someone proposes to adopt the vendor's figure or fill its gaps with another provider's values. Asks why the vendor presents the figure that way, keeps the reason if it is economically sound, and recommends a better, explicit definition built from the original source. Excludes figures whose definition and source are already approved, cosmetic layout or readability work, and mechanical normalization such as sign conventions, units or labels.
---

# Ask why a vendor shows a number before deciding what to show

A vendor's figure is someone else's definition applied to the original source. Its choices are often undocumented and can change. Treating it as the truth, or dismissing it as noise, both skip the useful question: why does the vendor present it this way, and is the reason good?

The rule: **when a vendor presents a number in a certain way, ask why, keep the reason if it is good, and build something better from the original source.** Vendors are data sources, not models of what to show.

This Skill is for the organization's shared catalog audience. It is organization-independent and assumes no particular vendor, filing regime or product. It covers figures that companies report in their filings; macroeconomic or statistical-agency series are out of scope.

It produces analysis and recommendations within existing authority. It grants no permission to change production data, suppress or publish series, alter a product, or override decisions recorded by the product owner. Those actions require authorization that already exists for them.

## When it applies

**Activation test:** a specific issuer-reported financial figure, plus an unresolved question about its definition, source or comparability, plus a vendor involved in one of three ways:

- the vendor's value differs from the issuer's original filing;
- two providers disagree on the same line item;
- someone proposes, before any discrepancy is measured, to adopt the vendor's figure as the product's definition or to fill its missing periods with another provider's values.

It does not apply without a specific figure and an open definitional question. That excludes general page design, cosmetic layout or readability work, figures whose definition and source are already approved, and mechanical normalization such as sign conventions, units or labels.

## Procedure

Work one line item at a time. Do not recommend a merge rule or a display before steps 1 to 4 have an answer or a recorded gap.

1. **Name the investor question the figure answers.** For example: how much cash is left for owners, or how much the business must reinvest. The questions in [references/investor-questions.md](references/investor-questions.md) can help.
2. **Find the vendor's definition in its own documentation.** Check whether it changed and whether past periods were recalculated. If you hold an archive of the vendor's data, check whether it mixes methodologies. If documentation or an archive is unavailable, record that as an evidence gap.
3. **List what the original source contains.** That means every relevant line and concept in the filing, not only the one already mapped, plus the text: notes, exhibits, contracts and the management discussion. Many "vendor versus filing" gaps are really "vendor versus the single concept we mapped". If filings are not accessible, record the gap.
4. **Try to reconstruct the vendor figure from the original source.** A close match supports a candidate explanation of the vendor's method. It does not prove that method. A residual that the evidence does not explain stays unknown. Do not label it vendor error, and do not use it as a signal, unless independent evidence establishes its cause.
5. **Recommend a definition.** Adopt the vendor's reason when it is economically sound. When the vendor's choice is debatable, recommend making it visible instead of copying it, for example "other sources show X because they exclude Y".
6. **Write the recommendation explicitly.** Give the figure's name, its composition and a citation for each input concept. Two definitions never share one time series. The vendor value remains a comparison and a data-quality check. Applying the recommendation to live data or a product happens only under existing authorization.

When sources are missing, deliver an evidence-limited result. State what was established, what could not be checked, and which recommendation those gaps limit.

## Guardrails

- **Do not recommend mixing definitions in one series.** A change of provider alone does not break a series; a change of definition or measurement basis does. Before recommending that one provider fill another's missing periods, require evidence that both use a comparable definition and measurement basis *for the periods to be filled*: specific documentation of both definitions, or a reconciliation of both to the issuer's filings. Agreement on overlapping periods only corroborates; values can agree while definitions differ, and a vendor may have changed its method between periods. Otherwise the fill creates a seam that looks like a real change, and growth rates and ratios computed across it are wrong. When comparability remains unresolved, recommend leaving the periods empty.
- **Do not treat a raw vendor-minus-filing residual as a feature.** Any content lives in the components that explain the gap, such as excluded one-off items, capitalized spend or capitalized interest. Measure those directly from the original source.
- **Treat text as data.** Covenants, collateral, cancellation terms and related-party roles often exist only in filed contracts and notes. Extract them with a citation to the paragraph, and reconcile them with the numbers.
- **Answer why before recommending the permanent display.** While the reason is unknown, it is reasonable to recommend a reversible interim measure, such as no longer showing a mixed series. Whoever holds the authority decides whether to apply it.

## Verify before recommending

- The investor question is stated for each line item.
- The vendor definition is cited from its documentation, with any methodology change, or its absence is recorded as a gap.
- Every relevant source concept was considered, not only the mapped one, or inaccessible sources are named.
- When the available data support a reconstruction, its match rate and residual are reported. A match is described as support, not proof, and an unexplained residual as unknown. When they do not, the missing inputs are named and the conclusions that must stay provisional or be deferred are stated.
- The recommendation says which vendor reasons were adopted and which were made visible.
- No recommended series mixes definitions. Any recommended backfill cites the evidence of comparable definitions and bases.
- Any live change is described as conditional on existing authorization.

For the cases that produced this practice and their evidence status, see [references/worked-examples.md](references/worked-examples.md).
