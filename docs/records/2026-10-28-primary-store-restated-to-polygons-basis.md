---
id: 2026-10-28-primary-store-restated-to-polygons-basis
status: shipped
date: 2026-10-28
prs: [846]
supersedes:
superseded-by:
---

# The primary's price store is restated to Polygon's basis through 2026-08-05: IESC, SFBS, BYND and seven more, 9,728 bars, exactly as rehearsed — STATE.md §5.0 row 32 item (22, `restate-prices`) closed

**WHAT.** The operator ran row 32's `restate-prices` item, from #835
(`docs/records/2026-10-27-price-flags-checked-against-tiingo.md`), in the primary checkout on
2026-10-28, at `main` `68da34ae`:

```
.venv/bin/python -m vinci.cli restate-prices --through 2026-08-05
```

It printed `restating against Polygon's current basis at 2026-08-05 (1 grouped-daily call(s))…`,
one line per name, then:

> done: 10 name(s) restated; every other held bar at those sessions matched

- **The ten, by Polygon's factor:** AIXI ×7, BYND ×30, ETHA ×3, IESC ×0.5, IMMP ×20, LHSW ×8,
  NVX ×10, REAX ×10, SCNI ×10, SFBS ×0.5. These are row 32's expected names and factors.
- **Their bars:** 9,728 through 2026-08-05, one security id each. By name: AIXI 855, BYND 1,236,
  ETHA 511, IESC 1,236, IMMP 1,227, LHSW 336, NVX 1,125, REAX 1,236, SCNI 730, SFBS 1,236. That is
  row 32's expected 9,728.

**WHY.** These ten names split or reverse-split after the store last read them. The store kept
their old basis while Polygon serves the new one, so each series broke at the store's boundary.
Any reader of their history read across that break, the screen's drawdown among them. No ledger
or benchmark name is among the ten, so scoring was never exposed. The ingest guard
(`eod.client.restate_held`) restates held bars only when it next ingests a name, so this store's
next refresh would have done the same. This run does it now.

**HOW VERIFIED.**
- **Rehearsed before the run,** on copies, in both orders with a refresh. Both left identical
  stores: 2,704,807 bars to 2026-10-26, 0 differing (#835's record).
- **The live run's names and factors equal the rehearsal's.**
- **The bar count above was read after the run,** read-only (`mode=ro`), from the primary's
  `data/vinci.db`.
- **The store's shape is unchanged** from #842's record of the same store earlier the same day:
  - 2,572,227 bars in all, the latest 2026-08-05;
  - the ledger and benchmark names: IT, SMPL and VRRM 1,236 each; IWM 1,236, MDY 1,236 and SPY
    307; GOOGL has none here.

  None of those names is among the ten. The command reports every other held bar at the anchor
  sessions as matched.

**BOUNDARY.**
- **Store:** the primary checkout's `data/vinci.db` on 2026-10-28, after #842's re-filing.
- **Run:** by the operator, in the primary checkout's terminal, on 2026-10-28, at `68da34ae`.
- **Counts:** read after the run, by ticker over each name's one security id, for bars dated on
  or before 2026-08-05.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No per-bar before/after was kept for this run.** The value check rests on the rehearsal and
  on the command's own anchor comparison; the counts above check only shape.
- **Still open on this store:** its latest bar is 2026-08-05, so it is ~12 weeks behind the
  market. XPRO and CLBK are carried at its next weekly build (#842's record).
- **Found while closing it:** row 32 had two items numbered (22), LLY's quarterly CIQ misfile and
  this one. The STATE identifier test (`tests/test_state_identifiers.py`) does not catch a
  duplicate item number inside a row. The closed list therefore names this one
  "(22, `restate-prices`)", and LLY's (22) stays open under its own text.
