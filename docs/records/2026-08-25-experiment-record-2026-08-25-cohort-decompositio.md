---
id: 
status: recorded
date: 2026-08-25
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**EXPERIMENT RECORD — 2026-08-25 cohort-decomposition falsifier (pre-registered; MEASURE-FIRST,
nothing built).** Operator asked whether the weekly ranker should surface industry co-movement, so a
human stops re-underwriting one de-rating name by name. Measured BEFORE any build, on committed
data only — no API calls, no forward returns touched.

**THE GAP IS REAL AND WAS ALREADY NAMED.** PR #84 (2026-07-06) built the coarse SIC roll-up and its
own message states it: *"G2 strips MARKET beta (name vs IWM) but NOT sector, so a name that fell
with its whole sector still lands in the set looking idiosyncratic."* `sector`/`industry` are on every `ranked_queue.jsonl` row; **industry IS rendered
in the web ranker** (with the committed-dossier CIQ-GICS overlay) and is absent only from
`ranked_queue.md`. So the missing thing is NOT the label — it is the DECOMPOSITION: nothing anywhere
splits a name's fall into its cohort's share and its own. The `Idio (vs mkt)` column asserts
idiosyncrasy as a single number, and that assertion is what this measurement shows is sometimes
false. Separately
`mechanical.idiosyncratic_vs_shared` has a `cohort` slot, a schema and a renderer — and is **null on
16 of 16 dossiers**, because it reaches for `graph_coverage.json` (supply-chain) rather than the SIC
cohort already on the row. `rank/cause.py` likewise exists and never runs: `cause_class` is
`"unclassified"` on all 268 rows.

**METHOD.** `screen_runs/*.jsonl` `grain=candidate` logs `rel_ret_vs_market` for ~1,750 universe
names per run, PASS AND FAIL — so cohort medians are unbiased by admission. Decompose each name into
`cohort median (by SIC industry, n>=6)` + `residual`. Four dated snapshots (07-29, 08-12, 08-14,
08-24) plus two controls: three SAME-DAY runs on 07-29, and the 2-day 08-12→08-14 gap as a noise
floor. **The control reads ~0 as it must** — same-day corr 0.998, median |Δresidual| 0.4%, zero sign
flips. Real intervals move 3–5x the 2-day floor, so the residual is signal, not drift.

**FALSIFIED — RESIDUAL IS NOT A RE-RANKING KEY.** Top-25 set overlap between consecutive runs is
WORSE for the cohort-adjusted order than for the raw one at EVERY interval: 40/72/64% vs 52/88/76%.
Mechanically obvious in hindsight — `residual = name − cohort` subtracts two noisy quantities and
compounds their noise, and the cohort median itself drifts 4.7–8.8% over a real interval. **28% of
the residual top-25 churns in TWO DAYS.** A re-sorted queue would have shipped and rotted. This is
the variant that would have been built without the measurement.

**SURVIVES — THE CLASSIFICATION, CONDITIONED ON MARGIN.** Restricted to the 238 names down >15% vs
IWM in ALL FOUR runs (which removes threshold-crossing churn — the naive 52% figure is dominated by
names stepping over the −15% line, not by the call flipping), the cohort-driven vs idiosyncratic
call holds **78%**, against a 97% 2-day control. Instability is almost entirely NEAR-TIES:

| margin \|cohort\| − \|residual\| | n | stable across all 4 |
|---|--:|--:|
| decisive (>25pt) | 111 | **96%** |
| clear (10–25pt) | 80 | 78% |
| near-tie (<10pt) | 47 | **34%** |

Reliable exactly where it claims strongly, unreliable exactly where it is a coin-flip — so the
remedy is house doctrine already: **a near-tie reports UNRESOLVED, never a forced call** (the same
rule as `mixed` proposing nothing). 48 of the 238 are stably cohort-driven — roughly **1 in 5**
persistent decliners is mostly riding its cohort down.

**THE COHORT TRAJECTORY IS READABLE**, which is the operator's own framing ("is the sector
recovering or de-rating"): cohort medians hold corr 0.92 over 10 days, 0.70 over 14. Food & Kindred
ran −37 → −43 → −43 → −37 — de-rated, then recovered 6 pts.

**THE CONCRETE INSTANCE.** BRBR, SMPL and VITL are three of the sixteen committed dossiers, one
industry cohort, all in the current top 5. Across four snapshots VITL is stably idiosyncratic
(residual −26/−32/−34/−31) and **SMPL stably is not** (−19/−4/−2/−10) — its fall is its cohort's.
VRRM, rank 1, has a POSITIVE cohort (+19/+14/+14/+4) and residual −104/−103/−104/−89: entirely its
own. The queue's raw order cannot express any of that.

**NO BUILD SANCTIONED HERE.** Indicated by the measurement, pending operator ruling: (1) a
cohort/idio flag WITH its margin, abstaining below ~10 pts, fed into the existing null
`idiosyncratic_vs_shared.cohort` slot; (2) the cohort's own trajectory across snapshots. NOT
indicated: any re-ranking by residual. **CAVEATS carried forward** — SIC is a crude cohort and
misses the real solar cluster (ARRY/DQ/SEDG/JKS all land in "Semiconductors"); 10 of the current
top 26 have cohorts under 6 and cannot be assessed at all; four snapshots over 26 days is a thin
panel and this should be re-run at 8–10. Reproduce from committed data alone — no store, no keys.

**A SECOND CORRECTION, RECORDED BECAUSE IT WAS MINE.** I first advised DEFERRING the operator's
no-CIQ triage idea on the grounds that 6 ledger verdicts cannot validate a triage filter. That
reasoning was wrong twice. Factually: 55.3% of the 3,514 mechanical dossier facts are CIQ-sourced,
so a no-CIQ dossier retains ~98 facts per name against ~a dozen decision-relevant ranker fields —
not the overlap I claimed. Methodologically worse: this fund tunes rankers by FACE VALIDITY and
never by outcomes, so the existing ranker was itself built on zero verdicts and tuning a second one
on 6 would be FORBIDDEN, not required. I imported a validation standard the repo explicitly
rejects. What the fact-split actually shows is that CIQ-dependence maps almost exactly onto
triage-vs-underwrite — surviving whole: `capital_allocation`, `idiosyncratic_vs_shared`,
`drawdown_cause`, `sbc`, 91% of `capital_structure` ("why did it fall, does it survive"); lost:
`operating_drivers` (6%), `implied_valuation`/`peer_comps`/`financial_summary` (0%),
`consensus_context` (2%) ("what is it worth vs what is priced"). The remaining caution is COST, not
evidence: `mechanical` and `synthesis` are separate blocks, so a mechanical-only, no-CIQ, no-LLM
second pass gets the triage facts deterministically and at near-zero marginal cost.
