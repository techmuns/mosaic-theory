---
status: open
date: 2026-11-10
prs: [943]
supersedes:
superseded-by:
---

# Fix request 2, group F, the scoring path (RF-D1, RF-D2, RF-D3, RF-D13): a split is read only when Polygon's reference and Tiingo's splitFactor agree, the realized view is a total return, and a pending row says why. On the committed ledger every score, mark, excess and realized number reads as before

**WHAT.**
- **RF-D1. A split Polygon reports late on both feeds was scored −50%.**
  - The fault: `entry_on_basis` reads one record, Polygon's splits reference. When Polygon serves
    the bars as traded (100, then 50) and lists no split, the sealed 100 equals the store's
    unrestated entry close. So f = 1, no split is recorded, and the return divides across a ×0.5
    step. A flat 2-for-1 scored −0.5000, RESOLVED, with no note. The basket read −0.5 and the
    monitor marked −0.5000.
  - The fix: every production split source is now `vinci.eod.splits.ConfirmedSplits`, Polygon's
    reference CONFIRMED by Tiingo's `splitFactor` rows over the span the run reads.
    - Tiingo puts the factor on the execution date. On GOOGL's real rows it serves 20.0 on
      2022-07-18, the date Polygon records. The rows are committed as
      `tests/fixtures/splits_reference/tiingo_googl_2022-07.json`.
    - The two records must hold the same splits, on the same dates, at ratios within 0.5%.
      Anything else raises `SplitsUnconfirmedError`. It is a `SplitsUnknownError`, so every caller
      that refused an unread reference refuses it.
    - Where that lands: a resolved row raises `SplitsUnreadError`; an interim row is pending and
      named; the basket is refused, with the reason; the monitor stops; close-position refuses.
  - Every Tiingo session in the span needs a row. A missing row makes the record unknown, never
    "no split". Tiingo may trail the calendar's newest session by one market closure (four days),
    because Polygon posts first.
  - Ratios of two STORED closes now get the check too: each row's benchmark leg in scoring and in
    the monitor, and each basket member. Before, these had no split check at all.
    - With no split in the window, the ratio stands as before.
    - Across a confirmed split, the store's first close is held to Tiingo's unadjusted close for
      that session (`leg_on_basis`). It must be ×the split, which means the store was restated.
      ×1, or anything else, refuses.
  - Tiingo's rows are the ones the dividend read already fetched. `default_splits` asks for the
    span `default_dividends` asks for (`TIINGO_LEAD`), so no symbol is added to the plan's monthly
    lookups.
- **RF-D2. With the reference late alone, `close-position` printed "−50.00% realized" and wrote
  the close.**
  - The fix: the same confirmed record. Every vendor read now runs inside
    `ledger.close_position(check=…)`: after the ledger's own guards and before the append. A
    record that cannot be confirmed refuses, and nothing is written.
- **RF-D3. The realized view was a price return inside a day declaring "TOTAL return both
  sides".**
  - A flat stock that paid a $20 special dividend read −20% realized beside a mark of 0%.
  - The fix: `monitor.pair_closes` reads the dividends for (entry, exit] and reinvests them on the
    ex-date, as every mark does. `realized_price_return` rides beside it; it is None on a day
    written before it existed. `close-position` prints "= X% realized, total return (price return
    Y%)".
  - `--as-of` must now be a session the name traded whose bar has posted. The total return is
    read through that session, so a weekend, a holiday, or today before the close is refused in
    words.
- **RF-D13. A pending row carried no reason.** The interim branch with unreadable dividends and
  the no-forward-price branch now each add a note naming the row and the cause. On the
  committed ledger, the primary's store holds no GOOGL bars; that is now said under the pending
  count.

**WHY.** These are TeamNostra's fix request 2 (document 15, 2026-11-09), order 3 (RF-D1, RF-D2)
and order 4's prices (RF-D3, RF-D13). Order 3's done-when reads "a split that cannot be confirmed
on one basis fails loudly in every surface: cross-check Tiingo's splitFactor, which the price
scorecard already reads". The scoring path is VRRM's: its rehearsal is due 2026-12-07 and it is
scored 2026-12-14 (STATE §5.0 row 38). Two other choices were considered and not taken:
- a split-shaped-step test on the stored series, because it would refuse a real crash. VRRM is
  an AVOID_TERMINAL, and a crash is the event it predicts;
- per-window confirmation, because a surface that forgot to call it would be silently
  unchecked. The span check runs inside the source, so no caller can skip it.

**HOW VERIFIED.**
- **The defects, reproduced first** at `7c87164a` on the real paths, every vendor faked at
  `CachedHttp.get_json`: `score_ledger` as `run_monthly` wires it, `vinci monitor --out`, and
  `close-position`. The script and its output are in this build's scratchpad; the summary:

  | Scenario | `main` | This branch |
  |---|---|---|
  | D: 2-for-1, both Polygon feeds late | score −0.5000, resolved, basket −0.5, 0 notes; monitor −0.5000, 0 split notes | `SplitsUnreadError` naming Tiingo's 2-for-1 on 2026-04-01; monitor stops, "splits UNCONFIRMED" |
  | E: reference late, close at 50 | "−50.00% realized"; ledger 1 → 2 rows | "REFUSED: splits UNCONFIRMED …"; ledger 1 → 1 |
  | A: everything on time (control) | 0.0000, basket 0.0, split named | the same |
  | C: $20 special dividend, close at 80 | "−20.00% realized"; monitor realized −0.2000 | "+0.00% realized, total return (price return −20.00%)"; realized 0.0 beside −0.2 |
  | Interim row, dividends unread | n_pending 1, 0 notes | n_pending 1, the row named |
- **Tests that fail first.**
  - Disabling the Tiingo comparison in-process (`_agree → True`) reddens exactly the six RF-D1 and
    RF-D2 pins in `tests/test_split_confirmed_by_tiingo.py`. The controls and negative pins stay
    green.
  - Dropping the dividends from the realized view reddens the three RF-D3 pins in
    `tests/test_realized_total_return.py`.
  - `tests/test_scoring_pending_reasons.py` fails 2 of 3 on a clean `main` checkout; the negative
    pin passes on both.
  - The Tiingo-lag fix from the code review: restoring the whole-span reading reddens its three
    pins.
- **On the committed ledger, as a dry run, never written.** The data was a `.backup` copy of the
  primary's `data/vinci.db`, its ledger rebuilt from `data/snapshots/` as `run_monthly` does.
  Vendor reads were held to the ledger's names and benchmarks. `main` (`6fbbb4a2`) and this
  branch read alike:
  - **Scoring as of 2026-11-09:** VRRM −0.0870, SMPL −0.0055 and −0.0415 (all interim), IWM
    +0.0266. The same two pending notes: IT and GOOGL, MDY and SPY absent from the copy.
  - **`vinci monitor --out`, the 2026-11-06 session:** every row's mark, excess and the spread
    (+0.71545) are identical. The realized rows read IT +0.0000 and SMPL −0.0357, now with the
    price return beside them (equal, because neither paid a dividend). No split notes.
  - **`close-position` on a scratch copy,** SMPL's open decision at 12.05 on 2026-11-06: main
    printed "= +6.35% realized", and this branch "= +6.35% realized, total return (price return
    +6.35%)".
- **Live reads,** all within the ledger's names and benchmarks:
  - Tiingo: 7 symbols, GOOGL, IT, SMPL, VRRM, IWM, MDY and SPY, all already in this month's
    lookups. One more request was GOOGL's 2022-07-13 → 07-20 rows, for the fixture. The
    confirmation added no Tiingo lookup: in the second dry run it read 0 symbols live.
  - Polygon: 2 splits references before (VRRM, SMPL) and 4 after (adding IWM, MDY, SPY), plus the
    monitor's grouped-daily days and aggregates.
- ruff and `mypy --strict vinci` are clean. The gate (`bin/commit`, after review round 0) passed:
  9,654 passed, 567 skipped and 8 xfailed. Its first run failed one test,
  `tests/test_sec_pacing.py::test_two_processes_on_one_machine_share_one_budget` (#854's
  cross-process SEC timing: a 0.080s gap against 0.1s), while three suites shared the CPU. It
  passed 3 of 3 alone and on the rerun. It is not this change's: reported, not fixed.

**BOUNDARY.**
- **Ledger:** `data/snapshots/decision_ledger.jsonl` at `6fbbb4a2`: 7 rows, 5 decisions and 2
  closes.
- **Store copy:** taken 2026-11-09 23:32 IST. Its IWM, IT and VRRM bars end 2026-07-02 and SMPL's
  2026-08-11. It holds no GOOGL, MDY or SPY bars.
- **The monitor dry run** read the 2026-11-06 session, the latest posted when it ran on
  2026-11-10.
- **Reproductions:** the constructed name SPLT. The world, its dates and its prices are in the
  script header.
- **Suite counts:** `pytest -m "not network"` on this branch, rebased on `6fbbb4a2`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A split NO vendor records** (both Polygon feeds and Tiingo late together) is still read as no
  split. Nothing here can confirm against anything then. The price scorecard
  (`quality.sources.prices`) is what flags the step. Falsifier: a scorecard split-shaped step on a
  ledger name inside its window.
- **A Tiingo hole anywhere in the span refuses every row of that symbol,** not only the rows
  whose windows hold the hole. The check runs per symbol, inside the source, so no caller can skip
  it. The span starts a week before the book's earliest entry.
- **A stored ratio across a confirmed split is held to Tiingo's close within 0.5%** (the
  scorecard's own `CLOSE_TOL` band). Where the two vendors' closes differ by more on that one
  session, the benchmark or basket refuses.
- **`close-position` needs both keys,** and its `--as-of` must be a posted session. A close typed
  before the day's session posts is refused until it has. Every past close was recorded after its
  exit date.
- **`realized_return` changes meaning on new monitor days,** to the total return the day declares.
  Days written before this keep their price returns, with `realized_price_return` None.
- **Row 38's rehearsal** surfaces one more refusal: `SplitsUnreadError`, saying "cannot be
  confirmed" when the two vendors disagree, or "cannot be read" when Tiingo or the reference
  cannot be read. Tiingo's key, which the run already needed for dividends, is now needed for the
  split basis too.
- **No page changes,** so there is no extraction-version bump. Monitor days written from now on
  carry `realized_price_return`.
