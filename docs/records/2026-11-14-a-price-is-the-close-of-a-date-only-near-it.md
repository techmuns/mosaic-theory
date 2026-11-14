---
id:
status: shipped
date: 2026-11-14
prs: [1075]
supersedes:
superseded-by:
---

# A price is read as the close of a date only when it is near that date: a cohort member with no close within 4 days of either end of its window is refused and counted, never priced as a 180-day move; a comps panel is dated only by a close within 4 days before its export stamp, never by a coincidence a year back — the two defects that held GOOGL's rebuild are fixed in code, at $0; GOOGL now waits on the operator's call on an 11-name Polygon backfill of its cohort

**WHAT.** Two price lookups read a close however far it sat from the date it was read as. Both were found during the 10-page rebuild and recorded as FOUND, NOT FIXED in `docs/records/2026-11-14-rebuild-group-1-ncno-smpl-tjx.md`. The operator ruled "Fix first, build GOOGL later (Recommended)".

1. **The cohort leg** (`vinci/dossier/mechanical.py`, `_window_return`). Each end of the 180-day window read the close on or before its date, with no limit. A cohort member whose stored bars stop in July was priced on its July close and published as its 180-day move.
   - **Now:** each end is read through `_covering_close`. A bar dated more than `_COVERAGE_GAP_DAYS` (4) calendar days before the end it stands for is refused, and the member's return is UNKNOWN (`ret_180d: null`).
   - **The cohort says what it refused.** Its `source_ref`, which both surfaces print, names how many of its members were refused, which ones, and each one's last close. Example: `4 of 12 refused, their latest close more than 4 days before the 2026-10-16 end: EXTR 2026-07-02, NN 2026-07-02, AAPL 2026-06-17, MSFT 2026-06-12`.
   - **The page's own two legs get the same bound.** The name and the benchmark 180-day legs read through the same function. Code review round 0 found that a leg refused at one end still printed "name has no bars over the window" or "benchmark bars unavailable". Each now names the end it was refused at and the bar it would have read. The cohort read no longer says "no price history" when every member was refused.
2. **The comps-date matcher** (`vinci/dossier/freshness.py`, `date_of_close`).
   - **Before:** once the store reached within 4 days of the export stamp, the scan took the latest matching close anywhere before it. A store missing exactly the panel's session passes that precondition.
   - **Now:** a match counts only if it sits within `_COVERAGE_GAP_DAYS` before the stamp. A missing session is refused, never matched elsewhere: the date is None and the header stamp stands.
   - **The reason is true.** `mechanical._uncorrected_reason` names a match it refused further back, with its date. The old "the store carries no bar at that panel's printed close" would be false of a store that holds one.
   - `freshness.matching_closes` is the scan both functions now share.

**WHY.**
- **GOOGL's cohort.** On the 2026-11-11 working store (content sha256 `598a3d2c07f1…`, frontier 2026-11-11), the committed page's 12 cohort names break down as:
  - 1 current: AMZN, to 11-10.
  - 4 stale: EXTR and NN to 07-02, AAPL to 06-17, MSFT to 06-12.
  - 7 absent: T, AVGO, CHKP, PANW, SNX, VZ and ZS have no bars at all.
- **What the stale four read at base.** At the committed page's own 10-16 end: EXTR +65.6% over 04-17 → 07-02, where the page says +20.8%; NN −28.7% (page −58.0%); AAPL +9.5% (page +27.1%); MSFT −7.6% (page +25.1%). At the 11-11 end a rebuild would read, EXTR shows +20.8% over the 48 days 05-15 → 07-02. That is close to the committed figure by coincidence, which is why a stale close is not caught by eye.
- **WERN's comps date.** WERN's 2026-11-12 comps panel prints 27.84, the 2026-11-11 close. On the 2026-11-10 store (content sha256 `a60b31c9…`) the scan took 27.84 on 2025-10-17, and the build refused the panel as 392 days old. IT's 193.00 on the same store matched nothing, so its stamp stood uncorrected.

**THE BOUND, AND WHY IT IS 4 DAYS (face validity, never outcomes).**
- **The existing staleness bounds were searched first.** Vocabularies searched: house terms `_COVERAGE_GAP_DAYS`, `_covering_close`, `MAX_ANCHOR_LAG_DAYS`, `STALE_CLOSE_SESSIONS`, `price_staleness_days`; plain words "stale close", "last close", "trading days". Also `git log -S_COVERAGE_GAP_DAYS`, `git log -S_covering_close`, `git log -S price_staleness_days`, and `git log -i --grep` for "stale close" and "cohort". Four bounds exist:
  - `freshness._COVERAGE_GAP_DAYS` = 4 calendar days: the dossier's own "covering close".
  - `config.price_staleness_days` = 5: the screen's feature staleness and the ledger seal.
  - `features.MAX_ANCHOR_LAG_DAYS` = 10: the screen's G2 start anchor, a gate with six days of margin.
  - `universe.STALE_CLOSE_SESSIONS` = 10 sessions: a trading suspension.
- **4 is the dossier's rule, and #743 set it on the exact analogue** ("A benchmark close older than the date it is labelled with is refused, never read"). `_market_legs` refuses a benchmark that trails the name by more than 4 days, and the cohort is the second comparator in the same block. 4 days is the widest ROUTINE gap between two consecutive trading days (Friday to Tuesday over a Monday holiday). Measured on IWM and MDY, the consecutive-bar gaps are 1d ×994, 2d ×14, 3d ×228, 4d ×37 and nothing beyond (`features.py`'s own comment), so a close further back is a fetch that did not run.
- **The screen's 10 is not adopted at the window start.** The screen's 10 is a GATE's margin over the same measurement. A dossier figure published as a 180-day move has no margin to spend. Any start anchor 5–10 days back is a hole in the series by that same measurement, so refusing it is correct.
- **The known limit is the safe direction.** An unscheduled closure longer than 4 days refuses a figure it could have stated (Hurricane Sandy's five-day gap, stated in the constant's own comment).
- **No forward return was read to set it.**

**HOW VERIFIED.**
- **Pins, built from real data.** Real Polygon bars were cut from the 11-11 store into `tests/fixtures/prices-2026-11-11/`; `SOURCE.json` records the store's content hash, the cut windows, and why the cut cannot move a result. The pins also use the committed `data/graph_coverage.json`, the committed GOOGL page's 12 cohort names, and WERN's export stamp (2026-11-12) and printed close (27.84). Those two were read by `ciq_sheets.comps_export_stamp` / `comps_printed_close` from the 2026-11-12 export: sha256 `54b2114b068d…`, sheet Financial Data, the As-Of Date cell and the subject row's Day Close Price.
  - The cut was checked: on the full store and on the cut, base `date_of_close` gives 2026-11-11 (11-11 bars) and 2025-10-17 (bars to 11-10) on both.
  - The 11-10 WERN series is the 11-11 one less its 11-11 bar, checked identical against the 11-10 store copy.
- **`tests/test_price_date_bounds.py`, twelve pins: six on the defects, five of them red at base; six on the bound's edges (round 1), three of them red at base.** Shown red by running head's tests on main's `vinci/` (the impact check's part 1, below). The defect pins:
  - REJECT: EXTR, NN, AAPL, MSFT refused at an 11-11 end, with the count and dates stated. Red at base: EXTR read 0.2084.
  - ACCEPT: AMZN, one session behind the end, priced on its own two closes; the read rests on 1 name. Red at base only on the read count, which was 5.
  - REJECT: a window-start hole is refused and named (real AMZN bars, with a hole cut — no observed case). Red at base: 0.0811.
  - REJECT: a leg refused at one end names that end, never "no bars". Red at base.
  - REJECT: WERN's 11-10 bars give None, never 2025-10-17, and the reason names 2025-10-17. Red at base: 2025-10-17.
  - ACCEPT: WERN's 11-11 bars give 2026-11-11. Passes at base by design: it pins what must not be refused.
- **The edge pins (round 1 of the review).** Every defect pin lands at most 1 day from its close, so a bound narrowed to 1, 2 or 3 days passed them all (the review's mutation run: 348 related tests green at a 1-, 2- or 3-day `_window_return` bound, and `date_of_close` at 3 survived; only the drift guard fired). These six sit on the edge, on the real AMZN and WERN bars:
  - ACCEPT, window start: 05-12..05-15 cut, an 11-11 end's start reads Mon 05-11, 4 days back.
  - REJECT, window start: 05-11..05-13 cut, an 11-09 end's start would read Fri 05-08, 5 days back.
  - ACCEPT, window end: a Fri 11-06 last bar under a Mon 11-09 end (3 days) and a Tue 11-10 end (4 days).
  - REJECT, window end: the same last bar under a Wed 11-11 end, 5 days back.
  - ACCEPT, comps date, WERN's real Labor Day: a panel stamped Tue 2026-09-08 is dated by the Fri 09-04 close (40.04), 4 days back.
  - REJECT, comps date: stamped Wed 09-09 with 09-08 cut, the 09-04 close is 5 days back.
  - The three REJECT pins are red at base; the three ACCEPT pins pass there, since base refuses nothing.
- **Mutation check of the edges.** Each end of each bound was set to 3 days and then to 5, in a scratch copy, with the twelve pins run against each mutant. Each of the six mutants fails exactly one pin, the one on its own edge:
  - start at 3 → the start ACCEPT pin; end at 3 → the end ACCEPT pin; `date_of_close` at 3 → the Labor Day pin;
  - start at 5 → the start REJECT pin; end at 5 → the end REJECT pin; `date_of_close` at 5 → the 5-day comps REJECT pin.
- **Two existing tests changed.** `tests/test_benchmark_bar_guard.py` and `tests/test_benchmark_figures_refresh.py` used `_window_return` itself as their picture of "the old, unbounded lookup". That oracle is the code changed here, so both now spell out the old reads with `eod.features._close_on_or_before`.
- **Cross-setup validation (`python -m vinci.impact run`).** First run: base `e17ceee9` vs head `3c033df6`. Re-run after round 1 and one merge of main: base `4fc47c88` vs head `ed933185`. The re-run has the same page moves, row for row on the 11-11 store and with the same counts on the 11-10 store; its fail-first shows 9 of 33 nodes red at base, 0 red at head. `vinci.impact verify` reads VALID on both stores:
  - **On the 11-11 store:** 3 of 25 pages move, all in the cohort.
    - AMZN: 10 of 21 refused — CRSR, EXTR, NN, SPB, TRNS, AAPL, INTC, MSFT, NVDA and WMT, their last closes 06-12 to 07-02. The read now rests on 1 name, not 11.
    - GOOGL: 4 of 12 refused; the read rests on 1 name, not 5.
    - WLK: 1 of 6 refused (CLF, 07-02). In the base $0 build on this store, WLK's read, "moved ALONE (idiosyncratic): name -44% vs cohort median -1%", rested on CLF alone; at head it reads UNKNOWN. The COMMITTED WLK page carries no stale read: it priced CLF at +21.9% on its own store, so nothing is owed for it.
    - **ATKR, WLK's sixth name, is a resolver miss, not a refusal.** The store holds `SEC-0001666138-ATKR` to 2026-07-02 (1,264 bars), so had it resolved it would be refused, and WLK would count 2 of 6. But ATKR is absent from SEC's `company_tickers.json` and `company_tickers_exchange.json` as cached 2026-11-11T03:52Z, by ticker and by CIK 1666138. `EntityResolver.resolve_ticker("ATKR")` on that index raises `UnknownSymbolError` ("no US issuer for ticker 'ATKR' (renamed/delisted?)"), which `_cohort` catches as a `ResolutionError` and reads as no bars. The committed page's null for ATKR is consistent with this; its build-time index is not cached, so that is not shown. Nothing here changes it: a resolver question, outside this PR.
    - PARR is not built at either side (its mislabelled quarterly export).
    - 0 committed pages re-render differently from their JSON.
    - Synthesis requests differ on the same 3 pages, in FACTS only. The 6 frozen panel pages' requests are byte-identical, so the row-53 panel check is not owed. The request moves off the panel; measuring it is the operator's call.
    - No downstream consumer (screen, ledger, scoring, monitor, theme desk, frontend) is reached.
  - **On the 11-10 store** (`--skip-fail-first`): 4 of 25 move.
    - The same three cohorts (AMZN, GOOGL, WLK).
    - **WERN:** every comps-dated field goes 2025-10-17 → 2026-11-12, the export stamp, uncorrected because the store lacks the 11-11 bar the panel names. Those fields are `market_cap_as_of`, `tev_as_of`, `valuation_snapshot_as_of`, and the `as-of` of the bridge, credit-health, leverage, peer-grid and market-cap cites. `price_days_after_valuation_snapshot` goes 389 → −2. The panel-freshness caveat that named the old snapshot is gone.
    - **WERN's TEV cite** now reads: "export stamp 2026-11-12 — NOT date-corrected: the store's latest bar at that panel's printed close is 2025-10-17, more than 4 days before the 2026-11-12 export stamp — not the panel's session, so it is never read as its date; no bar in those 4 days carries that close".
    - **WERN's oldest export panel by the gate's own reading** (`freshness.panel_age`, kind `export`, on each side's $0 build, assembled 2026-11-14): 393 days (`valuation.implied_expectations.tev_as_of`, 2025-10-17, refused against the 45-day ceiling) → 4 days (`stock_info.as_of`, 2026-11-10).
    - IT does not move: its 193.00 matches no bar at either side, and its stamp stands at both.
    - 0 live fetches.
- **Gate:**
  - Round 0: ruff, `mypy --strict vinci` and `pytest -m "not network"` were green on the merged tree `1daacb4f` (11,376 passed, 661 skipped, 11 xfailed, 0 failed).
  - Round 1: `5c278374` was committed through `bin/commit`, and its full offline gate was green.
  - The merged head `ed933185`: CI `gate` passes.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **LEFT OPEN (comps date).** A store missing the panel's session, in which another bar INSIDE the 4-day window happens to print the missing close (within half a cent), still dates the panel by that bar. The date is then at most 4 days too old: the gate reads it older, the safe direction. No market calendar is available inside `date_of_close` to tell the two apart. Falsifier: a corrected comps date that sits on a session for which the store holds the symbol's bar but not the market's.
- **REPORTED, NOT FIXED** (renderer changes, under the preview rule):
  - The Markdown cohort list prints "no bars" for every member with no return (`vinci/dossier/render.py:4185`). For a refused member that names the wrong cause; the cohort's `source_ref`, printed on the line above, names the refusal. 1 committed Markdown page carries the label today (`frontend/dossiers/WLK.md`, on ATKR — the resolver miss above, where "no bars" is also not the cause); AMZN and WLK are watch pages with no rebuild planned, and GOOGL's will carry no refusal once its cohort is back-filled.
  - The web's idiosyncratic block prints a fixed "benchmark bars unavailable — relative read UNKNOWN" whenever the market leg is UNKNOWN (`frontend/views/shared/dossier.js:3920`). That was already the wrong cause for #743's stale-benchmark refusal.
- **NOT DONE HERE:** no Polygon or Tiingo pull, no page rebuilt or re-rendered, and GOOGL not built.
- **WHAT GOOGL NEEDS BACK-FILLED.** For its cohort to read all 12 names at an 11-11 end:
  - EXTR, NN, AAPL and MSFT, from their last bar (06-12 to 07-02) to 11-11.
  - T, AVGO, CHKP, PANW, SNX, VZ and ZS, of which the store holds no bar. A 180-day window needs at least 2026-05-11 → 11-11.
  - That is 11 names. AMZN (to 11-10) is inside the bound and needs none.
  - A later price date moves every end with it.
  - The pull is the operator's call.

**BOUNDARY.**
- **Code:** on `claude/price-date-bounds`. The first run was base main `e17ceee9`, head `3c033df6`. Round 1 is base main `4fc47c88`, head `ed933185`; later commits are docs only.
- **Stores** (`vinci.impact.run.store_digest`: every table but `meta`):
  - The 2026-11-11 working copy: content `598a3d2c07f1…`, 2,543,246 rows, frontier 2026-11-11.
  - The 2026-11-10 copy: content `a60b31c9…`, 2,543,233 rows, frontier 2026-11-10.
  - Both are `.backup` copies of the rebuild session's files, opened read-only.
- **Pages:** the 26 committed `data/dossiers/*/dossier.json` at head, each built at $0 at its own reference date by the impact check. That date is 2026-10-16 for GOOGL's, AMZN's and WLK's cohort end.
- **CIQ:** the operator's Drive `manual/ciq` as of 2026-11-14: 277 exports on 26 pages, each by sha256 in the run's JSON, unchanged during either run.
- **Cache:** the primary's `data/cache`, served frozen. 13 SEC full-text-search responses were fetched live on the 11-11 run; there were 0 Polygon or Tiingo fetches.
