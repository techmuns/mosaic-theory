---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# The P/E percentiles are demoted to context — retroactively — and EV/NTM EBIT replaces them

**BOUNDARY.** Source: operator's CIQ exports read 2026-09-03 through `CiqBundle`. Multiple series =
`Financials→Multiples` Close, settled quarters, n=38, current excluded. Consensus drift =
`Estimates→Trends`. USD. No raw CIQ committed. 24-month anchors are the settled quarter nearest
730 days before the current close.

## The ruling, and it reaches backwards

GOOGL's memo records `CURRENT-vs-HISTORY BASIS MATCH: LIMITED` — the current Estimates P/E is
explicitly **normalized NTM EPS**, the historical Financials row is labelled only **`P/NTM EPS`**, and
the workbook does not establish they share a denominator. Therefore *"the P/E quartiles are valuation
context, not load-bearing evidence."*

**That is structural to the workbook, so it applies to all four names — and retroactively to every
percentile computed in this thread.** WST's 37th/40th, WAT's 63rd/66th, MCK's 95th and BDX's 13th were
context all along. They were reported here as reference distributions with the LIMITED caveat
attached, but the caveat was carried as a footnote while the numbers did the work. **Demoted
explicitly: none of them may anchor a multiple leg.**

## What replaces them — EV/NTM EBIT, the GOOGL cross-check

EBIT is a **reported line**, not a proprietary normalized figure, so this basis does not carry the
LIMITED problem. Same sheet, same Close convention, same 38 settled quarters:

| | n | min | P25 | med | P75 | max | current | rank | 24m ago | 24m change |
|---|---|---|---|---|---|---|---|---|---|---|
| WST | 38 | 20.6 | 26.7 | 33.1 | 36.0 | 49.4 | 30.9 | 42% | 35.5 | **−13.0%** |
| WAT | 38 | 16.7 | 18.8 | 20.3 | 24.0 | 28.8 | 22.7 | 68% | 24.5 | −7.2% |
| MCK | 38 | 8.2 | 9.3 | 11.1 | 13.1 | 16.4 | 16.2 | **95%** | 12.6 | **+28.6%** |

**It corroborates rather than overturns.** Ranks agree closely with the demoted P/E ranks (WST 42 vs
37, WAT 68 vs 63, MCK 95 vs 95), so the earlier readings were not misleading — they were merely not
admissible as evidence. Now there is a basis that is.

*EV-based measures carry their own sensitivity: EV includes net debt, so a leverage change moves the
multiple without the business moving. That is live for MCK (net debt +39%, shares −46% over the
window) and should be stated wherever its +28.6% is used.*

## The within-series evidence, which survives the ruling

A change measured **inside one row** is internally consistent regardless of what the row's denominator
is — the basis question cancels. Over 24 months, against consensus that rose:

| | P/NTM EPS 24m | EV/NTM EBIT 24m | FY27E consensus 18m |
|---|---|---|---|
| **WST** | **−18.4%** | **−13.0%** | **+24.2%** |
| WAT | — | −7.2% | +5.9% |
| MCK | — | +28.6% | +7.9% |

**WST took the earnings and the multiple compressed.** Earnings arriving without a re-rating is direct
evidence against a theme premium, and it holds on the basis that survives the ruling. That is the
answer five comp bases could not produce.

### Anchor sensitivity — the 18-month window flips sign

At **18 months** the same comparison is fragile: the daily series gives 37.38 → 36.94 (**−1.2%**), the
quarterly close gives 36.51 → 36.94 (**+1.2%**). Both are correct; they differ by a four-week anchor,
because WST's multiple fell ~10 points inside one quarter (45.90 Dec-24 → 36.51 Mar-25 → 34.40
Jun-25 → 37.42 Sep-25). **The 24-month window is the one to quote** — −18.4% / −13.0% is unambiguous
and the conclusion is stronger there. An 18-month figure should not be cited without its anchor.

## Momentum is not dispersion — state which leg it sets

**+24.2% is directional momentum, not a dispersion estimate.** Momentum-derived widths are widest at
the top of a revision cycle, which is exactly where WST sits. Two uses, and they assume opposite
things:

- **Bull leg from the drift** — extrapolates the revision trend forward.
- **Symmetric ±24.2%** — assumes the drift fully reverses.

Neither is neutral, and the underwrite must **say which and why**. The same figure for BDX (−21.0%)
would set a bear leg by extrapolation or a bull leg by reversal, which is the tell that direction is
an assumption and not a property of the number.

## BDX — a screen finding worth keeping

**BDX drops. Three names: WST, WAT, MCK.**

Recorded as its own case, because it is the one the screen exists to catch: **the premium half was
satisfied and the materiality half never arrived.** BDX was cheap on every basis — 13th percentile,
−18% to peers — and its GLP-1 exposure was named in prose beside two names carrying figures. The
figure never came: its own transcripts give **agreement counts** (*"approximately 100 agreements
signed across novel and biosimilar GLP-1 programs"*) inside a segment that **declined 1%** then grew
5%. Meanwhile FY27 consensus was cut **16.82 → 13.29 (−21%)**, shares rose 27% and net debt 245%.

**The cheapness and the estimate collapse are one event.** A screen for materiality *without* premium
will always admit names that are cheap for reasons unrelated to the driver; the materiality prong is
what excludes them, and it only works if it requires a figure.

## Landed out of order

`#585` carried the 0.00% cross-source reconciliation, the split-date sensitivity and the MCK
mechanical check — and both `#586` and `#588` merged **on top of findings recorded in it** while it
sat open. The evidence was sound and nothing depended on the sequence, but the ledger now reads as
though the conclusions preceded their support. Noted so the order is not mistaken for provenance.
