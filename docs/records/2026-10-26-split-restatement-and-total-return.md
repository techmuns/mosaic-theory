---
id: 2026-10-26-split-restatement-and-total-return
status: shipped
date: 2026-10-26
prs: [796]
supersedes:
superseded-by:
---

# A split no longer splices the price store, and every return the fund scores is a total return — registered before the first ledger outcome

**WHAT.** Two of #795's findings are fixed in one PR, on the operator's instruction (2026-10-26):
the split-adjustment splice (finding 1) and price return being scored under a total-return name
(finding 5).

**1 — THE SPLICE, FIXED WHERE THE STORE TAKES IT.**

- **The cause.** `RESTATE_WINDOW_DAYS` (#643) re-pulled 30 days and skipped every older held
  session. After a split, the newly pulled bars came back on the new basis (`adjusted=true`), the
  held ones stayed on the old basis, and the series stepped by the split ratio at the boundary
  between pulls. The plan serves two years, so held bars older than that can never be re-pulled.
- **The detector** is the same session, held versus re-fetched (`eod.client.restatement_factor`).
  Measured on 2026-08-05's whole market, re-fetched 2026-10-26:
  - 2,340 of 2,350 names came back identical;
  - the other 10 had all four prices moved by ONE factor (to 1e-6), with volume moving inversely
    to the cent.

  A bar that changed any other way is a correction and restates nothing (`RESTATE_TOL = 0.005`).
  The detector catches a 3-for-2 as readily as a 2-for-1, because it never asks for a whole number.
- **Prevention, at ingest.** Each refresh re-fetches ONE held session it would otherwise skip: the
  latest, its ANCHOR. Any name the source has restated has its older held bars put on the current
  basis by the source's own factor (`restate_held` → `Store.restate_bars`: prices × factor, volume
  ÷ factor, `prices.source` tagged `+restated` once). The anchor costs one call a refresh.
- **The PSTV case.** A name with no bar on the anchor, which then gets new bars in the run, is set
  beside the source at its OWN last held session (one call per distinct date). Measured: PSTV's
  held bars end 2026-07-31, and Polygon now serves its whole history ×0.04.
- **Repair, for a store already spliced.** `vinci restate-prices --through <last session of an older
  pull>` adds the store's latest market session itself and restates each pull by its own factor.
  One factor for all would be wrong: a split after the newest pull needs the newest pull restated
  too.

**2 — TOTAL RETURN (operator ruling B, 2026-10-26).** Total return with dividends is the PRIMARY
basis for every name AND benchmark leg (SPY, MDY, IWM). Price return is printed beside it for
continuity and never enters a spread. The ruling is REGISTERED HERE, before any ledger outcome is
scored (VRRM, 2026-12-14).

- **Definition.** Dividends are reinvested on the ex-date: total return = (exit ÷ entry) ×
  ∏(1 + divCash ÷ close) over the ex-dates in (entry session, exit session]
  (`vinci/eod/dividends.py`). Each yield uses Tiingo's own unadjusted cash and close for that day,
  so it needs no split basis and multiplies onto the fund's own price ratio. The sealed entry price
  stays the entry price.
- **Source and gaps.** Dividends come from Tiingo's `divCash`, through the fund's adapter
  (`TiingoEodClient.daily_rows`, new). Polygon's dividends endpoint is not used.
- **A missing record is UNKNOWN, never zero.** A window counts as read only when Tiingo's rows
  include the entry session and the exit session, with no two neighbouring rows more than 4
  calendar days apart (`MAX_SESSION_GAP_DAYS`: the Friday-to-Tuesday after a Monday holiday).
  Anything less raises `DividendsUnknownError`: no key, a failed request, an unreadable row or a
  hole. A share class is asked for hyphenated (brk-b).
- **Where it applies.**
  - **Scoring** (`vinci/scoring/`):
    - `metrics.total_return` was `exit ÷ entry − 1`. That function is now `price_return`, and
      `total_return` takes the dividend growth.
    - Every `VerdictScore` carries total and price returns. The report prints the basis line and
      the price-return spread beside the primary.
    - The β/α daily returns carry the ex-date yields in both series, so the regression printed
      beside a total-return spread is not a price-return one.
    - `score_ledger(dividends=…)` has NO default, so no caller can drop it by omission. A RESOLVED
      row whose dividends (the name's or its benchmark's) cannot be read raises
      `TotalReturnUnknownError`. An unresolved one is pending, like a row with no forward price
      (the sealed-benchmark precedent).
  - **The follow basket** (`baseline.basket_return`): total return, and refused WITH its reason
    when a member's dividends are unknown, as when a member has no bars.
  - **The monitor.**
    - `position_row` requires each side's dividend growth; total return is primary, and
      `position_price_return`, `benchmark_price_return` and `excess_price` ride beside it. The
      spread carries `spread_price` beside it.
    - `MonitorSnapshot.return_basis` ("price" | "total") defaults to "price" with the old
      `price_basis` text, because EVERY COMMITTED DAY BEFORE 2026-10-26 WAS PRICE RETURN. Those
      days are read as such and never restated.
    - A validator refuses a day that mixes bases.
    - The command sets "total" and stops on a leg whose dividends cannot be read.
    - The terminal table prints `PX-EXC%` beside each row and the price spread beside the headline.

**WHY.** The 2026-10-16 weekly's store (and so its committed screen) carried the splice: SFBS's G1
PASS rested on it (`docs/records/2026-10-24-prices-quality-source.md`). And the spread the fund will
score from 2026-12-14 was a price return labelled total. Both had to be right before the first
outcome.

**THE REAL RUNS, 2026-10-26.**

- **Repair**, on the read-only backup of `research-alpha-audit-bcba59`'s store that #795 scored
  (2,797 names, market sessions to 2026-10-16): `restate-prices --through 2026-08-05` made 2
  grouped-daily calls (2026-08-05 and the added 2026-10-16) and restated 10 names, all through
  2026-08-05: IESC ×0.5, SFBS ×0.5, BYND ×30, AIXI ×7, ETHA ×3, IMMP ×20, LHSW ×8, NVX ×10,
  REAX ×10, SCNI ×10. None needed restating at 2026-10-16. Seven of these splits landed after the
  store's October pull, so they had not spliced yet; the next refresh would have spliced them.
- **The restated history equals what Polygon serves today.** 2026-07-15 was re-fetched and set
  beside every held bar:
  - 2,356 of the 2,357 untouched names were identical;
  - of the 10 restated, 2 were identical, 6 within 1e-6, and 2 within 1e-3 (worst 4.7e-6, the
    source's 4-decimal rounding).

  The one untouched difference is CLBK's old security, which Polygon now serves restated by the
  conversion's exchange ratio. It sits under its own internal id, so it makes no step inside a
  series (finding 3 of #795).
- **The scorecard.** Split-shaped steps went from 112 to 109: IESC's, SFBS's and BYND's 2026-08-06
  steps are gone. Every other count is unchanged (stale 75, gaps 52, Tiingo 25,411 of 25,412).
  Snapshot `data/snapshots/data_quality/prices/2026-10-26.json`, inputs sha256 `80ed8324…`.
- **The remaining 109, explained where they can be.** Of the 60 whose sessions Polygon still serves
  (both re-fetched, 102 calls):
  - 59 come back identical on both sessions. The step is in Polygon's own current series: a real
    move, not a splice.
  - 1 is PSTV, both sessions restated ×0.04. Its whole held series is on the old basis, one
    vintage, so it has no step. The PSTV case above now covers it.

  The other 49 (on 45 names) predate Polygon's window. They were NOT re-checked; Tiingo could do it
  at one request a name, which is a follow-up.
- **WHAT THE CORRECTED DATA DOES TO THE COMMITTED SCREEN — decision surface, shown, not
  rewritten.** IESC and SFBS are band-A candidate records in the 2026-10-16 run. Through the
  screen's own `build_price_record` and gates, at reference 2026-10-16 against IWM:

| | as committed (and reproduced on the pre-repair copy) | on the repaired bars |
|---|---|---|
| IESC | drawdown −68.7% G1 PASS · relative return −51.2% G2 PASS | −38.3% G1 PASS · −4.3% **G2 FAIL** |
| SFBS | −57.1% G1 PASS · −47.5% G2 PASS | **−14.5% G1 FAIL** · **+3.0% G2 FAIL** |

  So neither name would be a candidate. Nothing committed was rewritten. The operator's choice is
  recorded as §5.0 row 32 item (16).
- **The primary store's next refresh, on a copy, through the real `ingest_prices`.** The primary's
  store ends 2026-08-05. The run covered a 21-name universe (the 10 names above, PSTV and 10
  controls) from 2026-07-01 to the 2026-10-23 close, with 59 grouped calls.
  - **New code.** Anchor 2026-08-05; the same 10 names restated by the same factors. No
    split-shaped step since 2026-07-01 except LHSW's at 2026-09-22 (×2.05), which lies inside
    freshly pulled bars, so it is in Polygon's current series.
  - **`main`'s old ingest, on a second copy from the same cache.** The splice at 2026-08-06 for 7
    names: IESC ×0.49, SFBS ×0.49, BYND ×25.9, AIXI ×6.8, ETHA ×2.98, IMMP ×19.1, NVX ×10.1.
    REAX's and SCNI's ×10 splices are there too, but they miss the scorecard's whole-number band;
    the new code restates them all the same.
  - PSTV gets no bar after 2026-07-31 in either run, so the late-name check has nothing to do for
    it yet.
- **Scoring on total return**, on the store copy as of its frontier 2026-10-16, with live Tiingo
  dividends. No row has resolved, so this is the mechanism shown, not a result:
  - VRRM, IT and SMPL read the same total and price return (no dividend in their windows);
  - GOOGL's total return sits above its price return by its own dividend (−1.47% against −1.54%);
  - IWM's total return exceeds its price return in every window (for example −6.46% against
    −6.71%).

  The report prints the basis line and "on price return: BUY−AVOID n/a".
- **The monitor on total return.** `vinci monitor --out <scratch>` ran live (Polygon, EDGAR,
  Tiingo) to the 2026-10-23 close: rc 0, `return_basis: total`, the new `price_basis` text, and
  `PX-EXC%` on all 5 rows. GOOGL reads −7.37% total against −7.43% price, and its SPY benchmark
  −1.87% against −2.11%. IT, SMPL and VRRM read the same on both bases. The interim spread prints
  on both bases as a diagnostic (§7): nothing was chosen on it, and its effect was not computed to
  choose anything.
- **Dividends in the window**, Tiingo 2026-06-01 → 10-23: VRRM, IT and SMPL paid none; GOOGL paid
  (06-08, 09-04); IWM, MDY and SPY each went ex-dividend twice.

**HOW VERIFIED.**

- **Pins that fail first.**
  - On `main`'s ingest, `test_a_split_since_the_held_pull_leaves_no_step` fails on a ×0.5 step at
    the boundary (`assert not True`).
  - `test_a_name_with_no_bar_on_the_anchor_is_checked_at_its_own_last_bar` fails the same way with
    the late-name check off.
  - The total-return pins cannot run on `main`, whose harness takes no dividends and whose
    "total_return" is a price return.
- **Mutation: 34 of 34 killed**, with stale bytecode off:
  - 26 on the total-return code: the window bounds, both coverage ends, the gap rule, yield as
    cash, an unreadable cash read as 0, per-window re-reads, the share class, a missing key read as
    no dividends, each growth dropped, an unknown resolved row priced, β without dividends, price
    beside reading total, the basket ignoring an unknown member or dropping growth, the monitor's
    growths, the one-basis validator, the price spread from total, the command's basis and its
    fail-loud, and the report's price means;
  - 7 on the splice: the factor band, the one-factor rule, the segment bound, the anchor choice,
    the repair's latest session and its refusal, and the `+restated` tag;
  - the late-name check.
- **Test layer.** End to end through the real monitor command over the committed ledger and
  assignments, the written day declares total, carries price beside every row, a dividend-paying
  leg reads above its price return, and an unreadable leg stops the run with nothing written. All
  committed monitor days still load as price basis, and none prints `PX-EXC%`.
- **No live Tiingo in the suite.** The scoring, monitor, prices and ingest suites pass with a
  deliberately invalid `TIINGO_API_KEY` (214 passed). `main()` loads `.env`, so a test that reached
  Tiingo would have failed on a 401.
- **Pins updated deliberately:**
  - 44 call sites in 8 suites now state their dividend source (`tests/dividend_support.no_dividends`
    for synthetic stores, which pay nothing; it lives in tests so no production module offers a
    way back to price return);
  - `test_total_return` became `test_price_return_and_total_return`;
  - the anchor makes `test_a_session_the_store_already_holds_is_not_re_pulled` re-pull exactly one
    held session.
- **The decision-path guard asked once for each scoring file** edited through the Edit tool. One
  early edit to `vinci/scoring/__init__.py` was made by script; it was reverted and re-made through
  the Edit tool so the guard asked. Later edits to `metrics.py` by script came after its approved
  Edit, inside the guard's once-per-file approval.
- **Suite and gate.** `pytest -m "not network"` on the final tree: 6,550 passed, 526 skipped, 0 failed. Ruff and `mypy --strict` are clean. The `bin/commit` gate runs again on every commit.

**BOUNDARY.**

- **Re-fetch comparisons.** The whole market on 2026-08-05 and 2026-07-15, re-fetched 2026-10-26,
  against the research-alpha store copy (2,350 and 2,367 names with bars on those days).
- **The 60 re-checked steps.** Those whose prior session is on or after 2024-10-28 (inside the
  plan's two-year window), counted on the repaired copy.
- **The screen recompute.** Reference 2026-10-16, IWM benchmark, `Screen2Thresholds()` defaults
  (G1 ≤ −30%, G2 ≤ −15%).
- **Dividend presence.** Tiingo, 2026-06-01 → 2026-10-23, ex-dates only (no amounts quoted).
- **Interim returns.** As of 2026-10-16 (scoring, store frontier) and 2026-10-23 (monitor).

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **OPERATOR ITEM — the CI secret** (§5.0 row 32 item 15). `monthly-score.yml` has no
  `TIINGO_API_KEY`, so once a row resolves the monthly run stops with `TotalReturnUnknownError`.
  The change is to add `TIINGO_API_KEY: ${{ secrets.TIINGO_API_KEY }}` to the *Run monthly scoring*
  step's `env` and create the secret. NOT made here, per the ruling. It meets item (14), the
  refused direct push, at the same run.
- **OPERATOR ITEM — the committed screen** (§5.0 row 32 item 16): annotate, re-run, or let the next
  weekly supersede.
- **ACCEPTED: a restated bar is this repo's arithmetic on the source's factor, not a bar the source
  served**, and it says so (`+restated`). The 2026-07-15 comparison shows it equals today's serving
  to 5e-6. Falsifier: a re-fetched restated bar that differs beyond `RESTATE_TOL`.
- **ACCEPTED: restatement assumes a pull is one vintage.** A refresh writes every session it fetches
  in one pass, so this holds by construction going forward. A store stitched from several copies
  needs each boundary named to `restate-prices`.
- **ACCEPTED: the 49 older remaining steps are not re-checked**, because the plan cannot re-fetch
  them. A Tiingo pass over their 45 names is the follow-up.
- **ACCEPTED: Tiingo is the only dividend source.** If Tiingo misses a dividend while still serving
  the row (divCash 0 on an ex-date), it reads as none. Falsifier: a Polygon dividends-endpoint
  ex-date in a window Tiingo reads as clean.
- **NOT CHANGED: the frontend.** It shows the latest monitor day's figures under its own basis line,
  so the next committed day shows total return labelled as such. Showing price beside it on the page
  is a render change, which needs the preview rule. The theme priced-check (RUNBOOKS §c) is a
  research surface and stays labelled dividend-blind.
- **The monitor's history is not restated**: the five committed days stay price return, by their
  own stated basis.
