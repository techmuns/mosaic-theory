---
id: D7
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D7. THE VOIDED FLEET NUMBERS, REPLACED BY THE CORRECTED RUN — and the premise behind them was
wrong too.** The discarded pass (SMPL 3.83→4.78, EPAM 5.27→6.68, IT 1.29→1.54, MVST −0.33→−0.23)
was described as a BASIC-basis error on both sides. It was not: the **"before" was already the
DILUTED weighted average** — `scenarios.py:725` has read `facts.diluted_shares` all along — so only
the "after" carried the dropped-dilution error, having used the basic cover-page `shares_out`.
Item 24 is therefore **weighted average → outstanding**, not basic → diluted.

MEASURED, engine re-run, nothing written. Three denominators, one change isolated per column:
**A** = committed (diluted WA, mis-periodised on SMPL) · **B** = same basis, correct quarter (the
`_latest_point` fix alone) · **C** = diluted OUTSTANDING at the valuation date (item 24).

| name | A shares | B shares | C shares | A r:r | B r:r | C r:r | A→C |
|------|---------:|---------:|---------:|------:|------:|------:|----:|
| AORT |    49.73 |    49.73 |    50.20 | −0.67 | −0.67 | −0.67 | −0.00 |
| EPAM |    54.18 |    54.18 |    52.63 |  5.27 |  5.27 |  6.34 | +1.07 |
| IT   |    69.97 |    69.97 |    67.12 |  1.29 |  1.29 |  1.52 | +0.23 |
| MVST |   385.27 |   385.27 |   386.07 | −0.33 | −0.33 | −0.33 | −0.00 |
| NCNO |   109.46 |   109.46 |   110.51 | −0.71 | −0.71 | −0.72 | −0.00 |
| SMPL |    93.68 |    89.94 |    88.46 |  3.83 |  4.48 |  4.78 | +0.95 |
| WERN |    59.91 |    59.91 |    59.95 | −0.35 | −0.35 | −0.35 | −0.00 |

**MVST'S TEST PASSES.** The operator's falsifier was "with dilution retained it must FALL, not
rise". It reads −0.33 — back from the erroneous −0.23, unchanged from committed, because its
denominator RISES 385.27→386.07M. The basis is held.
**NO NAME CROSSES 2:1 IN EITHER DIRECTION** — EPAM and SMPL were already PASS, IT stays FAIL at
1.52, the remaining four are negative-reward and structurally unmoved. No re-underwrite trigger.
**THE PERIOD FIX IS THE BIGGER ERROR ON SMPL:** column B moves it 3.83→4.48 on its own, more than
the denominator swap's 4.48→4.78. SMPL is the only name column B touches.
**SMPL'S TWO MOVES MUST BE APPROVED SEPARATELY** — one corrects a mis-dated input, the other
changes a basis; bundling them would seal a single 3.83→4.78 with no way to attribute it.

**WRITTEN 2026-07-31 (item 24 closed).** All seven records now carry diluted shares OUTSTANDING,
written through `refresh_record` with the derivation, the carry-forward assumption and the
exclusions in the fact's own `basis`, then re-rendered. Final: AORT 49.731→50.200 (r:r −0.67
unchanged) · EPAM 54.183→52.634 (5.27→**6.34**) · IT 69.965→67.121 (1.29→**1.52**) · MVST
385.272→386.069 (−0.33 unchanged) · NCNO 109.458→110.509 (−0.71→−0.72) · SMPL 93.678→88.461
(3.83→**4.78**) · WERN 59.910→59.950 (−0.35 unchanged). **NO NAME CROSSES 2:1 in either direction**
— EPAM and SMPL were already PASS, IT stays FAIL at 1.52. No re-underwrite trigger.

**THE 4.78 FALSIFIER MISFIRES, and the reason is D5.** The operator predicted SMPL would land
"nearer 4.5 than 4.8" and that 4.78 would mean the overlay was not being applied. It IS applied —
SMPL is a **zero-dilution** name, so its diluted outstanding equals its basic outstanding
(88,460,545), and that sits **1.65% BELOW** the quarter's weighted average (89,940,680) because the
company is buying back. The prediction assumed diluted outstanding > quarter WA; with no dilution to
add and a shrinking count, the denominator FALLS and the ratio RISES. **The swap is not uniformly
"add dilution":** it is a move from a period AVERAGE to a point-in-time COUNT, then plus the
increment — and for buyback names the first move dominates. EPAM (−2.86%) and IT (−4.07%) show the
same sign; only AORT, MVST, NCNO and WERN rise.

**THE WRITER HAD THE ITEM'S OWN DEFECT.** `refresh_record` moved the VALUE and froze the `basis`, so
swapping the denominator would have left `"diluted weighted-average (latest 10-Q)"` over a number
that is neither weighted nor an average — `Fact.basis` documents itself as naming WHAT the number
is. It now accepts a full `Fact`, logs the basis move as its own `refresh_log` entry (a number that
keeps its value while changing meaning is the move a value-diff cannot show), and **REFUSES a UNIT
change** — basis is prose about the same quantity, unit is its scale, and a silent re-scale of a
denominator is the thousands-blind defect arriving through the writer instead of a parser.

**RE-RENDER SCOPE, per the not-surgical rule.** Six dossiers re-rendered; **FUBO reverted** — it has
no scenario record, so its whole diff was schema-default backfill surfaced by the model round-trip.
MVST's JSON carries **79 added schema-default fields** (`material`, `benchmark_symbol`,
`explanatory`, …) — verified **0 changed, 0 removed** — unavoidable because its denominator moved
and re-rendering forces the round-trip. Disclosed, not hidden.
