---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 What-broke chart: one shared "true 1-day move" rule (pre-window
detector consistency).** The chart drew two kinds of markers off DIFFERENT definitions of a 1-day
drop: the numbered gap markers + the ledger used the #197 tightened rule (spacing==1, or ==3 with
the prior point a Friday), but the **pre-window HOLLOW-drop detector** (`dossier.js` ~1473) still
used a **loose `sp2>=1 && sp2<=4`** — so on a downsampled step-2 series (a weekday skipped) it would
mark a 2-trading-day slide as a 1-day crash. Fix (JS-only; the md/PDF ledger has no pre-window
markers): extracted the rule into ONE shared, exported helper **`isNextTradingDay(aDate, bDate)`**
and routed BOTH `gapPctFromPerf` AND the pre-window loop through it — the two can't drift again.
`gapPctFromPerf`'s refactor is behavior-preserving (its py-twin equivalence test still green).
NO committed-artifact change: a scan of every committed series found ZERO consecutive ≤-threshold
pairs where the loose and strict rules disagree, so every current (daily) chart renders
byte-identical — the fix only bites a downsampled series (e.g. MVST's back-compat weekly). This is
why a browser preview is uninformative here (nothing visible changes on committed JSON); the
behavioral change is pinned synthetically instead. INVARIANT:
`test_prewindow_hollow_drop_uses_the_shared_trading_day_rule` (a step-2 pre-window pair is EXCLUDED,
a true 1-day control INCLUDED, + the shared rule's 6 spacing/weekday cases) — would fail on the old
loose check. Gate: ruff + `mypy --strict` clean · 1050 passed.

**OPERATOR NOTE — worktree stores are separate + need the benchmark ETFs.** `db_path=data/vinci.db`
is CWD-relative, so `../mosaic-theory-wb` has its OWN `data/vinci.db` (started empty). Re-assembling
a name IN a worktree needs its bars AND the IWM/MDY benchmark bars in THAT store, else the
stock-performance benchmark line is empty. Backfill both with `refresh <NAME> IWM MDY --aggs` from
the worktree, or re-assemble in the main checkout (full store) and copy the artifact. The worktree
also needs a `.env` symlink for the ANTHROPIC/POLYGON keys (synthesis + EOD).
