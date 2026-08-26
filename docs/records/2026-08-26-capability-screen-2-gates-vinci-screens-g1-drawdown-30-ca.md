---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier and is dated in the body. The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **Screen 2 + gates** (`vinci/screens`) — G1 drawdown ≤−30% (capped at −85% terminal floor) / G2

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **Re-screen accretion bug — FIXED 2026-06-23 (root cause + regression-pinned).** The first weekly
    re-run produced a DOUBLED candidate set (618 = last week's 301 + this week's 317, 287 tickers
    twice) and the ranker faithfully ranked the duplicates. **Root cause = the screen WRITE path, not
    just `run_weekly`:** `screen_universe` cleared only the *current* run's `screen_run_at`
    (`clear_candidates(run_at)`), so a re-screen on a NEW reference date layered on top of prior
    generations instead of replacing them — any caller accretes (the `screen` CLI too); `run_weekly`
    merely triggers it by `rebuild_from_snapshots`-ing last week's set first. The writer
    (`save_candidate`, INSERT-OR-REPLACE by id) was never at fault. **Fix:** `clear_candidates()` is
    now a FULL replace (`DELETE FROM candidate_records`), matching its own docstring — a re-screen is a
    clean snapshot. **Regression-pinned:** `test_rescreen_replaces_not_accretes` runs the screen TWICE
    consecutively and asserts the stored set is the SECOND run's only (week-1 ids gone), NOT the union
    — it FAILS on the old run-scoped clear, passes on the fix (both shown). *Cleaned: dropped the 618,
    re-ran the fixed screen → 317 single-generation candidates (no dup ids), re-ranked → 47/317
    structurally sunk, top-15 unique.* (Side effect: the `ev_ebitda` legacy-float compat test was
    decoupled from the live snapshot — the current producer defers all `ev_ebitda` to UNKNOWN, so the
    legacy present-float shape is now guarded by a synthetic record, not the live snapshot's contents.)
  - **G2 "idiosyncratic" is name-vs-IWM, NOT name-vs-SIC-sector (verified 2026-06-19; the field was
    then renamed `rel_ret_vs_sector` → `rel_ret_vs_market`, the old name being a lie — it compares to
    IWM, not a sector).** `assemble.build_price_record` sets it to
    `relative_return(name_bars, benchmark_bars, lookback_days=180)` = **name 180d trailing return − IWM
    180d trailing return** (`eod/features.relative_return`; `run.py` passes `benchmark="IWM"`). It is a
    *trailing return*, not peak-to-current drawdown. The SIC peer-cohort was **deferred and never built**
    (`features.py:135` leaves the field UNKNOWN, note "needs SIC peers (step 5)"; **no SIC-cohort /
    peer-aggregation code exists anywhere in `vinci/`** — so the Part-1 sub-questions on SIC
    source/granularity/aggregate/thin-cohort are all moot). So G2 removes **market** beta only — a name
    that fell *with its sector* (sector-wide derate) still PASSES G2 if it merely lagged IWM. *Re-derived
    FUBO from raw bars: depth −84.3% (=snapshot, close 8.90 / 52w high-of-highs 56.64); idio −88.2%
    (=snapshot) = FUBO −72.6% − IWM **+15.6%** over 180d — the "−88% vs market" is FUBO's fall minus the
    small-cap market's RISE, no sector comparison at all.*
