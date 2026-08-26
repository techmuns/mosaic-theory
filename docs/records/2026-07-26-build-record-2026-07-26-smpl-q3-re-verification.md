---
id: 
status: recorded
date: 2026-07-26
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-26 SMPL Q3 RE-VERIFICATION (amend-at-watch; data-only, branch
`data/smpl-q3-reverification`; operator directive, executed after three executor STOPs).**

**(a) VINTAGE VERIFICATION — the operator's staleness alarm, premise-tested.** Every load-bearing
committed number was vintage-mapped against the Q3 10-Q (`0001702744-26-000023`, filed
2026-07-09, period 2026-05-30). RESULT: the alarm was **~80% refuted**. The R1 grid's mechanical
facts are Q3-current **to the dollar** — `ltm_revenue` 1392.235 reproduces EDGAR exactly
(FY2025 − 9mo-2025 + 9mo-2026); `net_debt` 324.582 IS the 2026-05-30 balance sheet (debt 397.0 +
op-leases 51.4 − cash 123.9), and the "342.4 divergence" is the **Q2** figure, correctly not
used; `diluted_shares` 93.678M is the Q3 9-month weighted average. THREE secondary layers were
genuinely stale: `ltm_fcf` (FY2025 157.915 vs true LTM ~119.4, ~32% high), the multiple-leg's
"current multiple 5.65x" reference (a 07-21 read; the fresh panel shows 5.34x), and the
capital-structure detail (FY2025 10-K vintage). **But the deterioration is real and was NOT in
the legs**: a **$369M** nine-month impairment (331 intangible + 38 goodwill) against the single
$60.9M the clean series excluded, gross margin **36.2% → 32.2% (−4.1pp)**, trailing clean
operating margin **~13.8%** vs the 15.5% base leg. Q3 reported operating income −$49.9M.

**(b) RE-VERIFICATION RECORDED.** Base normal margin **0.155 → 0.140** (analyst judgment: set
between the 15.5% seven-year clean median and the ~13.8% trailing clean margin, nearer the
trailing figure — part of the gross-margin reset treated as structural). Revenue and multiple
legs UNCHANGED. Engine on the amended legs at spot **$10.53 (2026-07-22)**: base **$24.2406**,
bear **$6.9540** (unchanged), bull **$40.2135** (unchanged), 2:1 ceiling **$12.7162**, ratio
**3.834:1** vs the 2.0 bar (PASS) — **3.359:1** at the $10.92 entry. Engine == stored verified;
seal CLEAN ×7 (base text byte-identical, 3 legal amendment tags); prose lint 0. STATUS and the
LEDGER are UNTOUCHED — no transition, no new row, close row unchanged.

**(c) FRAGILITY STATED, NOT SMOOTHED.** The entry-recorded boundary cells (recovered from the
LEDGER payload — the record layer had them in prose only): 1,100 × 8% × 6.0x → $3.54 and
1,050 × 7% × 6.0x → $2.62. At $10.53 they clear on the entry-vintage 15.5% normal (≈2.34 /
≈2.07) but read **≈1.96 / ≈1.73 — BELOW the bar — on the re-set 14% normal**. The 2:1 line now
sits between the recorded 10% bear and these stress cells. This flip was caught by the
executor's verify-before-seal pass; the directive as first written would have sealed "both
clear" against a base it was simultaneously cutting.

**(d) GROSS-MARGIN TRIGGER FIRED AND DISCHARGED.** Nine-month GM fell ~4.1pp against the recorded
3.75pp threshold; the re-verification discharges it (base cut to 14%). Full-year basis re-read at
the ~October print. Quest trigger untouched (Q3 printed +1.1% — clock not started); guidance
trigger untouched (arms ~October). The dated September pricing trigger (2027-01-07) stands.

**(e) LEDGER PRESERVED WHAT THE RECORD LOST.** The append-only ledger payload retained the
boundary-cell definition that the scenario record carried only as prose — the append-only rule
paid for itself the first time a number had to be re-derived at a new vintage. (→ queue item 2.)

**(f) BRIEF-DESIGN LESSONS (advisor-attributed), fourth instance logged.** (i) A directive may
not order NOW what it specs as a FUTURE build — the item-2/item-8c contradiction (refresh
`ltm_fcf` now vs. the queued quarterly-refresh build that owns it) was caught by the executor,
not the author. (ii) **Stale-basis quoting** — boundary ratios computed on the PRE-amendment base
were quoted inside the directive that changes that base. **Advisor rule: any number quoted in a
directive is recomputed against the state the directive itself produces.**

**(g) STATUS-PROVENANCE CHECK (gate result).** `verdict.status == "watch"`, set by `d704317`
(2026-07-24, "C3 data: SMPL input-staleness close…", hunk `-"confirmed"` → `+"watch"`), merged
**in-chat** via PR #212; ledger shows **no open BUY** (`V-SMPL-…` closed by `C-SMPL-…` at 10.53).
Provenance explained, not drifted — so the pass ran in amend-at-watch mode rather than the
confirmed-record mode the directive first assumed.
