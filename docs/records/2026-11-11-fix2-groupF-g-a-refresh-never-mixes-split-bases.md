---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, group F, order 5 (prices): a partial refresh restates the held bars on both sides of its window across a split (RF-D5, both paths); price features read nothing after the reference date (RF-D10); Tiingo bars carry splits only, never dividends (RF-D11); a refusal inside the plan's window raises (RF-D12)

**WHAT.**
- **RF-D5, left edge, `vinci/eod/client.py` `ingest_prices_per_symbol`.** A partial aggregates
  refresh rewrote only `[start, end]` on the source's current split basis. After a split, the held
  bars before `start` stayed on the old basis: a ×0.5 step on a day with no corporate action, read
  by the screen's G1 drawdown and G2 relative return, and named nowhere.
  - Each name's one call now reaches back to its **anchor**, the latest held session before
    `start`, and sets the held anchor beside the served one.
  - A restatement (`restatement_factor`: all four prices by one factor, volume by its inverse) puts
    every held bar through the anchor on the current basis (`Store.restate_bars`, tagged
    `+restated`). That is the grouped path's rule (`restate_held`) applied here.
  - A move in price alone restates nothing and is named (`price_only`). An anchor beyond the plan's
    window cannot be fetched, and an anchor the source does not return cannot be compared, so the
    name is named as `unanchored` (the second case is from code review round 0).
- **RF-D5, right edge, both paths (`restate_after`, `Store.first_bar_after`).** The coordinator
  counted this in scope on 2026-11-11 ("Fix both edges in order 5's PR, behind a test that fails
  first on each"). A name that also held bars AFTER `end` kept them on the basis they were pulled
  on, so a split since left the same step at `end`'s next session. This happened on the aggregates
  path and on the grouped one; a screen replay at an earlier reference date is a grouped case.
  - Each name this run wrote that holds bars after `end` is set beside the source at its FIRST and
    LAST held sessions after `end`.
  - Only one restatement read at both ends restates: every held bar after `end` is then put on the
    current basis.
  - Two bases there restate nothing. That is a pull made after the split, whose ex-date and later
    bars the split leaves as they were, so one factor over all of them would make a step rather
    than remove one. An end the source did not serve also restates nothing. Both are named
    `unanchored`.
  - Aggregates path: still one call per name, now reaching through the last held bar. Grouped
    path: one call per distinct date, mostly two.
  - A refresh ending on the latest session holds nothing after `end` and costs nothing. That is
    the routine weekly and monthly refresh.
  - Only `[start, end]` is written; the anchors either side are read.
- **The summaries.** Both paths now carry `restated`, `price_only` and `unanchored`, a list of
  factors per symbol. The grouped path's `unanchored` covers its right edge only (see the
  found-not-fixed item below).
- **RF-D10, `vinci/eod/features.py` `compute_price_features`.** With no `frontier`, the reference
  date bounded only the staleness and the window starts, so bars after it were read as the latest
  close and stamped PRESENT (a lookahead). Without a frontier, nothing after the reference date is
  read now. A frontier still bounds at itself: a page's price date may run past its reference date.
- **RF-D11, `vinci/eod/tiingo.py` `parse_tiingo_prices`.** The bars came from Tiingo's `adj*`
  fields, which take out dividends as well as splits. Every total return here adds Tiingo's
  `divCash` on top of the price ratio, so a dividend would have been counted twice.
  - The bars are now the unadjusted open, high, low and close divided, and the volume multiplied,
    by every `splitFactor` dated after the row. That is the split-only basis of the last row given.
  - `price_history` reads rows through today, so the basis is Polygon's current one.
  - A row missing a field raises. Nothing writes these bars today (latent).
- **RF-D12, `vinci/eod/client.py` `grouped_daily`.** Any 403 NOT_AUTHORIZED read as "before the
  plan's window", so a lapsed plan or key read every refused session as a holiday. Now only a date
  past the window, within a margin of its edge, reads as no data. A refusal on a date certainly
  inside the window raises `EodError`.
  - One exception (code review round 0): the plan also refuses "today's data before end of day"
    until midnight ET, which is local tomorrow in IST (2026-10-28 was refused at 03:38 UTC on
    10-29, `docs/records/2026-10-29-monitor-day-2026-10-28.md`). So a refusal of today or yesterday
    still reads as no data, and `last_completed_session` steps back past it as it always did.
  - The window is named once (`PLAN_HISTORY_DAYS` = 730, `PLAN_EDGE_MARGIN_DAYS` = 14,
    `inside_plan_window`).
  - It was measured live on 2026-11-11: grouped-daily served 2024-11-20 (721 days back, 10,731
    results) and refused 2024-11-01 (740 days back) with "Attempted to request data past historical
    entitlements".
- **Also changed.**
  - Two comments that described `compute_price_features` as never filtering
    (`dossier/assemble.py`, `dossier/freshness.py`) now say what it does.
  - `tests/test_extraction_version_drift.py` is re-pinned for `vinci/eod/features.py`, with no
    version row: no page moves (below).
  - Two `tests/test_eod.py` expectations that encoded the old behaviour are updated: the Tiingo row
    shape and the per-symbol summary.

**WHY.** These are TeamNostra's fix request 2 (document 15), order 5, group F: RF-D5, RF-D10,
RF-D11 and RF-D12, all latent per the audit (group F notes, F-D5 and F-D10 to F-D12). The right
edge is this build's own finding 1, counted in scope by the coordinator.

**HOW VERIFIED.** See the PR's "Cross-setup validation (deterministic)".
- **Fail first.** `tests/test_prices_order5.py` has 17 tests.
  - First 10: 8 fail on `2b9b766c`; the 2 negative pins pass there, as they should.
  - The review's 2 (a day not yet closed in ET; an anchor the source did not serve): each fails
    with its fix reverted.
  - The right edge's 5: 4 fail on the left-edge-only code (`ba5c6707`), one positive pin per path
    and the two-bases negative pin on each path. The routine-refresh pin passes there, as it should.
  - All 17 pass on head.
- **The real data in those tests:**
  - IESC's real 2026-08-05 restatement pair, from the primary store and Polygon;
  - GOOGL's committed Polygon bars;
  - SPY's real Tiingo rows over its 2026-09-18 ex-date, cut from the response cache into
    `tests/fixtures/tiingo/spy_2026-09-18_exdate.json`;
  - GOOGL's real 2022-07 Tiingo rows;
  - Polygon's real 403 text.
- **Both edges, live, on a `.backup` of the primary's store** (a scratch script, not committed;
  12 Polygon requests in all, no Tiingo). The ledger names the store holds were VRRM, SMPL and IT.
  - Per-symbol over 2026-06-01..06-12: 3 calls, each reaching through the name's last held bar
    (07-02, 08-11, 07-02).
  - Grouped over 2026-06-08..06-12: 9 calls, being 5 window days, the left check at 06-05, and the
    right edge at 06-15, 07-02 and 08-11.
  - Neither path restated anything, and 0 of the 66 held bars after `end` changed. No split fell
    in the window, so no false restatement was made on real data.
  - The primary's sha256 (`b237f3a0…`) was the same before and after.
- **RF-D10 on the screen's committed inputs.** The screen's own `build_price_record` was run on the
  24 names with committed real bars:
  - as the weekly `2026-10-16-01` ran it (bars cut at its reference date): 0 of 24 names and 0
    fields move;
  - in a replay without that cut at 2026-06-30: 24 of 24 names and 288 fields move (base read the
    2026-10-16 bars).
  - 0 of the 4,456 dated price fields in the 343 committed candidate records is dated after
    2026-10-16.
- PAGES_PLACEHOLDER

**FOUND, NOT FIXED** (reported, not built: scope freeze, rule C).
- **`scripts/build_price_fixture.py` drops `ingest_prices_per_symbol`'s summary** (finding 2).
  This is the coordinator's instruction: record it, do not fix it. The weekly job runs the script
  unattended, and its call (line 140) discards the return value. So a name the refresh restated,
  or found `price_only` or `unanchored`, is never printed by that job.
- **The grouped path's left edge skips a held name the source did not serve, unnamed.**
  `restate_held` `continue`s when a boundary session has no fresh bar for the name. That name's
  older bars go unchecked and appear in no summary list. The right edge here names the same case
  (`unanchored`).
- **The primary's store holds no GOOGL or SPY identity, and most of its bars end 2026-07-02.**
  This was observed while choosing the live run's names; IT and VRRM end on that date and SMPL on
  2026-08-11. STATE row 38 (VRRM's rehearsal) already owns the refresh that `run-monthly` does.

**BOUNDARY.**
- Fail first: base `2b9b766c` with the tests copied in. The import of the new constant and the new
  `today=` argument are shimmed so each test fails on base's behaviour rather than at import. The
  right edge's fail-first ran against `ba5c6707`, the branch before it.
- Live run: 2026-11-11, on a `.backup` of the primary's `data/vinci.db` (sha256 `b237f3a0…`), with
  a fresh response cache. Names: VRRM, SMPL and IT, the ledger names the store holds.
  "Held after `end`" counts each name's bars dated after its run's `end`: 13 + 40 + 13 = 66 for
  each path.
- Screen inputs: `tests/fixtures/prices/*.jsonl`, 24 names plus IWM, real Polygon bars through
  2026-10-16. The candidate scan covers all 343 rows of `data/snapshots/candidate_records.jsonl`
  at `2b9b766c`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The plan window's edge is not measured to the day.** A refusal within 14 days of it reads as
  no data, as before, so a lapse there is not caught. Falsifier: a refusal on a date the plan
  served the same week.
- **An anchor beyond the plan window cannot be checked.** It is named in the summary as
  `unanchored`, never assumed.
- **The right edge reads two sessions, not every one.** The held bars between the first and last
  are taken to share their pull, the rule `restate_held` already states for the left. A store
  already spliced between those two sessions (by a refresh before this fix) is not repaired here;
  `vinci restate-prices` and the scorecard's split-step check are what catch it. Falsifier: a
  whole-number step between two held bars after a refresh's `end`, on a name that refresh restated.
- **A screen replay at an earlier reference date now costs one or two grouped calls more**
  (about 12–24 s at 5 a minute).
