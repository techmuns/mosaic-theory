---
status: shipped
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
  - **Aggregates path:** still one call per name, now reaching through the name's last held bar.
    EVERY held bar after `end` is set beside the served one. A held session there that the source
    did not serve cannot be read, so it makes the name `unanchored` and is never inferred from the
    bars around it (Codex round 1 on #991).
  - **Grouped path:** every name this run wrote that holds bars after `end` is read at its FIRST
    held session after `end`, which is where a splice at `end`'s next session shows. Only a name
    that reads a restatement there is read at its LAST held session too. That costs one
    whole-market call per distinct date.
  - Only one restatement across everything read restates: every held bar after `end` is then put
    on the current basis.
  - Two bases there restate nothing. That is a pull made after the split, whose ex-date and later
    bars the split leaves as they were, so one factor over all of them would make a step rather
    than remove one. An end the source did not serve also restates nothing. Both are named
    `unanchored`.
  - **A name whose window writes nothing has neither edge restated.** Its held window keeps its
    basis, so restating the bars either side of it would make the two steps the anchors exist to
    remove (code review 0b, finding 3).
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
    10-29, `docs/records/2026-10-29-monitor-day-2026-10-28.md`). So a refusal of the ET date still
    open, or a later one (`et_today()`, America/New_York), still reads as no data, and
    `last_completed_session` steps back past it as it always did.
  - Codex round 2 on #991: the first cut exempted local today and yesterday for the whole IST
    day. A refused session that had already closed in ET therefore read as a holiday after
    midnight ET, so a revoked key on a one-day ingest wrote and raised nothing. Only the ET date
    still open is exempt now (`test_a_refusal_of_a_session_already_closed_in_et_raises`, red on
    `c94dd27a`; the negative pin keeps the early-hours case at no data).
  - It is pinned at the real instants, both with Polygon's real 403 text. 2026-10-29T03:38Z is
    23:38 EDT on 10-28, so 10-28's refusal is no data. 04:30Z is 00:30 EDT on 10-29, just after
    midnight, so the same refusal raises.
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
- **Fail first.** `tests/test_prices_order5.py` has 26 tests.
  - The first 10: 8 fail on `2b9b766c`, and the 2 negative pins pass there, as they should.
  - Review 0a's 2 (a day not yet closed in ET; an anchor the source did not serve): each fails
    with its fix reverted.
  - The right edge's 5: 4 fail on the left-edge-only code (`ba5c6707`), being one positive pin per
    path and the two-bases negative pin on each path. The routine-refresh pin passes there, as it
    should.
  - Review 0b's 5: 3 fail on `8d7040bc` with that review's two applied refactors only. They are a current
    bar between two stale ones, a window that writes nothing, and a grouped replay with no split
    reading only the first session. The other 2 pin shipped behaviour: an unserved grouped right
    edge, and a price-only move after `end`.
  - Codex round 1's 1 (a held session after `end` the source did not serve): fails on
    `0135392d`.
  - Codex round 2's 1 fails on `c94dd27a`.
  - All 26 pass on head.
- **The real data in those tests:**
  - IESC's real 2026-08-05 restatement pair, from the primary store and Polygon;
  - GOOGL's committed Polygon bars;
  - SPY's real Tiingo rows over its 2026-09-18 ex-date, cut from the response cache into
    `tests/fixtures/tiingo/spy_2026-09-18_exdate.json`;
  - GOOGL's real 2022-07 Tiingo rows;
  - Polygon's real 403 text.
- **Both edges, live, on a `.backup` of the primary's store** (a scratch script, not committed;
  no Tiingo). The ledger names the store holds were VRRM, SMPL and IT.
  - Final code, 10 Polygon requests:
    - Per-symbol over 2026-06-01..06-12: 3 calls, each reaching through the name's last held bar
      (07-02, 08-11, 07-02).
    - Grouped over 2026-06-08..06-12: 7 calls, being 5 window days, the left check at 06-05, and
      the right edge's first session 06-15. No name read a restatement there, so no last session
      was read.
  - Neither path restated anything, and 0 of the 66 held bars after `end` changed. No split fell
    in the window, so no false restatement was made on real data.
  - The same run before review 0b's fixes made 12 requests; its grouped path also read 07-02 and
    08-11, with the same result.
  - The primary's sha256 (`b237f3a0…`) was the same before and after both runs.
- **RF-D10 on the screen's committed inputs.** The screen's own `build_price_record` was run on the
  24 names with committed real bars:
  - as the weekly `2026-10-16-01` ran it (bars cut at its reference date): 0 of 24 names and 0
    fields move;
  - in a replay without that cut at 2026-06-30: 24 of 24 names and 288 fields move (base read the
    2026-10-16 bars).
  - 0 of the 4,456 dated price fields in the 343 committed candidate records is dated after
    2026-10-16.
- **Pages.** The $0 build of every committed page, on base and head from one store copy, is in the PR's part 2, with the frontend render diff (part 4) and the six-page request compare (part 3: 6 of 6 identical, no paid check owed).

**FOUND, NOT FIXED** (reported, not built: scope freeze, rule C).
- **The unattended paths discard the ingest summary.** This is finding 2, which the coordinator
  directed be recorded and not fixed. Review 0b found the same at two more callers.
  - `scripts/build_price_fixture.py:140` (run by the weekly job) discards
    `ingest_prices_per_symbol`'s summary.
  - `vinci/screens/run.py:119,123` and `vinci/orchestrator.py:456,466` discard `ingest_prices`'
    summary.
  - So a name a refresh restated, or found `price_only` or `unanchored`, is never shown there. A
    screen replay's right edge, the case this build adds, is one of them. Only `vinci refresh`
    prints it.
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
- Replay cost: a read-only query of the same backup, per `end` above, over the names with a bar
  in the 30 days before it (the grouped path's restatement window, which it rewrites). That is
  2,332, 2,313 and 2,272 names, of which 2,328, 2,313 and 2,272 hold bars after `end`.
- Screen inputs: `tests/fixtures/prices/*.jsonl`, 24 names plus IWM, real Polygon bars through
  2026-10-16. The candidate scan covers all 343 rows of `data/snapshots/candidate_records.jsonl`
  at `2b9b766c`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The plan window's edge is not measured to the day.** A refusal within 14 days of it reads as
  no data, as before, so a lapse there is not caught. Falsifier: a refusal on a date the plan
  served the same week.
- **An anchor beyond the plan window cannot be checked.** It is named in the summary as
  `unanchored`, never assumed.
- **The grouped right edge reads two sessions, not every one.** The aggregates path reads every
  held bar after `end`, because its one call already carries them. The grouped path reads the
  first and last, and the bars between are taken to share their pull, the rule `restate_held`
  already states for the left edge.
  - So a store already spliced between those two sessions, by a refresh before this fix, can have
    its current-basis middle rescaled a second time (code review 0b, finding 2).
  - `vinci restate-prices` and the scorecard's split-step check are what catch that.
  - Falsifier: a whole-number step between two held bars after a grouped refresh's `end`, on a
    name that refresh restated.
- **A screen replay at an earlier reference date now costs more whole-market calls.** It pays one
  per distinct first held date after `end`, plus one per distinct last date among the names that
  read a restatement.
  - On the backed-up primary store, replays at 2026-05-29, 2026-03-31 and 2025-12-31 have 4, 6 and
    6 distinct first dates, so they cost about a minute or more at 5 a minute.
  - Reading every name's last date as well would have cost 18, 23 and 24 calls.
  - The ~4,600 lookups that find those dates (~2,300 names) took 147–236 ms.
## Amendments

- **2026-11-11 — `status: open` → `shipped`** (the record-status sweep, `docs/records/2026-11-11-record-status-sweep.md`). This record's change merged to `main` as `87f763d3` (#991) on 2026-11-11. `prs:` was left empty at merge; the front matter stays as merged, so this entry names the PR.
