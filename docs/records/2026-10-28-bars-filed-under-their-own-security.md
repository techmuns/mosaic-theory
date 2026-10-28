---
id: 2026-10-28-bars-filed-under-their-own-security
status: shipped
date: 2026-10-28
prs: [839]
supersedes:
superseded-by:
---

# Each stored bar is filed under its own security: 30 reused tickers' former holders' bars leave the current ids (Polygon's dated record), XPRO and CLBK carry their old filers' history (each new filer's 8-K12B), and the price scorecard holds scoring's 21 Tiingo symbols before it spends the month's cap

**WHAT.** The three price-store defects #835 (wave 2 L7) measured and could not fix in its lane
(`docs/records/2026-10-27-price-flags-checked-against-tiingo.md`), building on #833's alias table
(`docs/records/2026-10-27-rename-alias-and-registered-pool.md`).

1. **Reused tickers: the old holder's bars no longer file under the new holder's id.**
   - **Where the bar was attributed.** `ingest_prices` built `{eod_symbol: internal_id}` from
     TODAY's securities and filed every fetched day by it. A store backfilled across a reuse
     therefore held the former holder's bars under the current id. `ingest_prices_per_symbol`
     and #833's carry read a ticker's aggregates the same way.
   - **The proof, per hole.** The trigger is a hole: a step across more than `GAP_SESSIONS` (10)
     market sessions, by the scorecard's own definition. Polygon's record of the ticker as of the
     last bar before the hole must name another security, in one of three ways
     (`aliases.another_security`):
     - another CIK;
     - another share-class or composite FIGI under the same filer;
     - an exchange-traded fund where the line today is an operating security.

     Holes are read newest first. One whose record does not prove another security moves the walk
     to an earlier hole.
   - **The record.** Each proven reuse is a row in a new committed, accumulate-only table,
     `data/snapshots/ticker_tenure.jsonl` (`TickerTenure`). It says the id's OWN bars begin at
     its first session after the hole.
   - **Why a second table.** A reuse is the NEGATION of an alias: every reader of the alias table
     treats a row as a continuation, so one misread would splice the other company back in.
   - **The repair.** The bars before that session are re-filed, never deleted
     (`Store.refile_bars`). They go to the former holder's own id: `SEC-<its cik>-<ticker>`, or
     `PRIOR-<ticker>-<last date>` when the record names the same filer or none. Prices are
     unchanged, and each bar's source gains `+refiled:<from id>`.
   - **The guard on every later ingest.** `holders()` files each day's bar under the id that held
     the symbol THAT day (`aliases.first_sessions`). It is wired into the weekly screen, the
     monthly scoring refresh, `vinci screen`, and `vinci refresh` in both modes.
2. **Re-domiciles: a history crosses a CIK change only on proof.** `detect_successions` extends
   #833's alias table with an optional `predecessor_cik`. Its conditions:
   - **The pair:** the same ticker and share class under another CIK, with the old filer's bars
     ending before the new id's begin.
   - **The proof:** the same share-class FIGI under both filers, or the new filer's own 8-K12B.
     The 8-K12B must be filed within a year before the boundary, with the old history ending
     within two weeks of it. The shared ticker alone proves nothing.
   - **The carry:** #833's `carry_forward`, with every carried bar tagged
     `polygon-alias:<old id>`. No existing id is re-keyed; the old ids keep their bars untouched.
3. **Tiingo's monthly cap.** The scorecard's Tiingo reads now go through `TiingoBudget`
   (`vinci/quality/sources/prices.py`).
   - **The reserve** is the symbols scoring and the monitor must read, computed from the committed
     files (`dividends.reserved_symbols`):
     - every ledger name, and any benchmark a ledger row names;
     - the monitor's three benchmarks, and any benchmark its assignments name;
     - every name ever on the follow list.
   - **Rule 1, hold the reserve first.** Before the checks ask any symbol new to the month and
     outside the reserve, each reserve symbol not yet looked up this month is looked up once,
     over a seven-day window. A symbol looked up once is served all month, the cap
     notwithstanding.
   - **Rule 2, stop on the count.** A new non-reserve symbol is asked only while
     500 − (looked up this month) − (reserve not held) ≥ 1.
   - **Kept answers cost nothing.** A kept answer is always read first and never refused.
   - **The printout.** The scorecard's header prints the month's count, the reserve, what is held
     and not held, and what is left.
   - **The count is a FLOOR.** `TiingoEodClient.symbols_asked` reads this checkout's cache only,
     which is why rule 1 exists.
- **New command:** `vinci reattribute-prices` runs items 1–2 over every security in a store
  (`vinci/eod/identity.reconcile`). The weekly build runs the same over its admitted lines,
  before #833's rename detection, and #833's `_first_session` now reads a line's tenure.

**WHY.**
- Prices feed the screens, every page's spot, the monitor and the BUY−AVOID spread.
- #835 measured three defects:
  - 10 hole-steps where Tiingo's series under the ticker is another security's (ACIC, CALY, CBIO,
    CD, CORZ, GOLD, OPI, RCD, TEN, WLTH);
  - 4 securities whose histories broke across two ids (XPRO, CLBK);
  - the key's 500-symbol monthly cap, met on 2026-10-27 at 20:01 IST during #835's run.
- A refusal stops scoring by design (`TotalReturnUnknownError`), and VRRM resolves on 2026-12-14.

**THE STORE (VERIFY-AT-BUILD).**
- **The same store #835 measured.** A read-only SQLite backup of `research-alpha-audit-bcba59`'s
  store, restated through 2026-08-05 by the same command.
  - The restatement moved the same 10 names by the same factors (IESC ×0.5 … SCNI ×10).
  - On main's code (89d37d23) the scorecard gives inputs sha256 **`7f398b3e…`**, #835's
    committed AFTER, with every count equal: 2,797 names and 2,681,540 bars.
- **The repair.** `vinci reattribute-prices`, run on that copy at 2026-10-28 12:50–13:45 IST:
  - **30 reuses** recorded; **11,047 bars re-filed** off 30 ids onto their 30 former holders, 0
    of them with a changed price;
  - **2 successions** recorded; **2,450 bars carried**;
  - **0 bars changed in place**;
  - a second run: `0 reuse(s) and 0 succession(s) newly recorded; 0 bar(s) re-filed, 0 carried`.

**BEFORE → AFTER, `audit quality --source prices` (no `--write`; see COSTS).** BEFORE is #835's
committed AFTER (`data/snapshots/data_quality/prices/2026-10-28.json`, `7f398b3e…`); AFTER is
inputs sha256 **`a7f3aec6…`** at this branch's code.

| check | unit | BEFORE confirmed · stated · unexplained · unchecked | AFTER |
|---|---|---|---|
| ohlc_ordering · flat_close_run | bar | 2,681,540 · 0 · 0 · 0 | 2,683,990 · 0 · 0 · 0 |
| stale_bar | bar | 2,681,465 · 0 · 75 · 0 | 2,683,915 · 0 · 75 · 0 (31 of the 75 now sit on the former holders' ids) |
| split_shaped_step | step | 2,678,582 · 0 · 109 · 0 (52 excluded) | 2,681,032 · 0 · 109 · 0 (22 excluded) |
| **series_gap** | step | 2,678,691 · 0 · **52** · 0 | 2,681,141 · 0 · **22** · 0 |
| close_vs_tiingo | bar | 25,411 · 0 · 1 · 0 | unchanged |
| **step_vs_tiingo** | step | 65 · 0 · **13** · 6 (84 steps, 73 names; 52 not run) | 65 · 0 · **3** · 2 (70 steps, 61 names; 34 not run) |
| zero_volume_vs_tiingo | bar | 20 · 0 · 44 · 8 (8 names; 1 not run) | 20 · 0 · 22 · 0 (6 names; 3 not run) |
| **history_across_ids** | security | 0 · 0 · **4** · 0 (4 names) | **60** · **4** · 0 · 0 (64 names) |

- **The 10 measured reuses are all gone.**
- **step_vs_tiingo's 3 left unexplained** are the split-shaped identity steps with no hole,
  outside this rule: BHVN 2022-10-04, WOLF 2025-09-29, SRXH 2026-07-06.
- **series_gap's 22 left** are holes inside one security:
  - 12 that Polygon confirms are one security across the hole: BANFP 1, ILLR 1, INHD 1, NESR 1,
    PCTTU 8;
  - 10 that moved with the SPACs' re-filed bars: Lionheart III 2, Corner Growth 2 8.
- **history_across_ids:**
  - 60 confirmed: 30 current holders and 30 former holders, two securities in turn;
  - 4 stated: the XPRO and CLBK pairs, one line by a recorded succession.
- **zero_volume_vs_tiingo's 3 not run** are the ETF former holders (CALY's 22 bars, WLTH's 8,
  HHH's 1). Tiingo's series under those tickers is the current holder's, so it has none to give
  them. Before, CALY's 22 bars were compared with Callaway's volume, which was meaningless.

**THE 30 REUSES, BY PROOF** (each row's evidence names the record):
- **Another CIK (22):** ACIC, AKTS, ARIS, BBBY, CAI, CALY, CBIO, CD, CNR, GOLD, LION, MNR, MRLN,
  NIQ, NP, RCD, SAIL, SI, TACO, TEN, TRON, VELO.
- **Another FIGI under the same filer (5), each equity issued at a reorganisation:**
  - CORZ and CORZW (Core Scientific, 2024-01-24);
  - DBD (Diebold Nixdorf, 2023-08-14);
  - OPI (Office Properties, 2026-06-22);
  - SEZL (its Nasdaq class, 2023-09-14).
- **An ETF record (3):** WLTH and LUXE, whose ETF records carry no CIK and no FIGI; HHH's
  carries a FIGI.
- **Ten of the 30 are #835's measured ten.** The other twenty are among the 39 holes Tiingo's cap
  left not run, and the 2 it left unchecked (BBBY, DBD).

**THE 2 SUCCESSIONS, BOTH PROVEN BY THE 8-K12B.**
- **XPRO:** Expro Ltd, CIK 2126198, accession 0001104659-26-083106, filed 2026-07-13. Polygon
  carries no FIGI for XPRO on any date read.
- **CLBK:** Columbia Financial, CIK 2115119, accession 0001193125-26-309602, filed 2026-07-21.
  - The old class's FIGI is BBG003222R95 (as of 2026-06-12) and the new one's BBG023TM45X9. A
    second-step conversion issues a new class, so the FIGI rule correctly refuses it.
  - The conversion exchanged **2.2 new shares for each old one.** Polygon's own bars carry that
    ratio, and the carry put the old id's copies older than Polygon's window on the same basis by
    Polygon's own factor (×0.454545, measured on 2024-10-28; 793 bars tagged `+restated`).
  - So the successor's series runs continuously through 2026-07-21: 11.1364 → 11.08.

**NO LEDGER OR BENCHMARK BAR MOVES.** Bar for bar against the backup:
- IT 1,287, SMPL 1,287, VRRM 1,287 and GOOGL 470 bars, all identical;
- IWM 1,287, MDY 1,287 and SPY 368 bars, all identical.

The only ids whose bars change are the 30 current holders (bars taken off), their 30 former
holders (the same bars, put on) and the 2 successors (bars carried).

**WHAT THE SCREEN SEES, MEASURED (`compute_price_features`, reference 2026-10-16).**
- **12 of the 32 changed ids** have their 52-week drawdown, 12-month or 6-month return move:
  - AKTS's 12-month return was **+40,384%** (Akoustis's bankrupt equity spliced to Aktis) and OPI's
    **+9,400%**; both now read UNKNOWN;
  - GOLD's was +108.6% (Barrick spliced to Gold.com) and CALY's −72.6% (the ETF spliced to
    Callaway); both now UNKNOWN;
  - XPRO and CLBK were unevaluable on 51 bars. Now: XPRO drawdown −16.0% and 12-month +27.7%;
    CLBK −11.1% and +70.5%.
- **18 of the 32** are members of the 2026-10-16 primary population, and **0** are in the ranked
  queue.
- Whether any passes G1 is the next weekly's call; nothing here re-runs the screen.

**THE TIINGO BUDGET, REAL RUN.**
- **The header, on the repaired store:**
  > Tiingo budget 2026-10 (UTC month; 500 distinct symbols a key): 110 looked up this month through
  > this checkout's cache — a floor … scoring and the monitor reserve 21 symbols (3 benchmark, 15
  > followed, 4 ledger), 21 of them held this month; … left for the checks: 0 — Tiingo refused a new
  > symbol this run: the key's cap is met, and nothing new is asked until 2026-11-01
- **The hold, live.** The first AFTER run held SPY and MDY: 2 lookups this cache had not counted.
  The monitor rehearsals of 10-26/27 had already looked both up this month, so Tiingo served them.
  WVE, the one new symbol, was refused, and the run stopped asking.
- **The reserve (21):** IT, SMPL, GOOGL, VRRM; IWM, MDY, SPY; AMZN, BURL, GOOGL, LLY, NFLX, NKE,
  ORKA, PARR, ROST, TECX, TGT, TJX, UBER, V, WLK.
  - All but the three benchmarks are page names, which the scorecard now asks first.
  - So a normal month's hold costs at most 3 lookups.

**HOW VERIFIED.**
- **Corpus first.** Every rule was set against Polygon's records for all 35 hole-ids on the live
  store copy before any fixture existed: 52 holes, and 13 after-records where the CIK could not
  decide. The real run above is that corpus.
- **Frozen REAL fixtures.** `tests/fixtures/ticker_identity.json` holds:
  - 15 Polygon records;
  - EDGAR's filing lists for the four filers;
  - Polygon's carry bars for XPRO and CLBK;
  - real stored bars cut around each hole, on the store's real session calendar. Only the twelve
    names that make it a calendar carry synthetic prices.

  `tests/fixtures/tiingo_reserve/` is a copy of the committed ledger fields, follow list and
  monitor assignments as of 2026-10-28.
- **A positive and a negative pin per rule**, from real records unless named as a counterfactual:
  - CIK: CALY / BANFP;
  - FIGI: CORZ / INHD;
  - fund type: WLTH / WLTH with the line counterfactually a fund;
  - 8-K12B: XPRO / the old filer's list;
  - window: a stale filing, a 15-day gap and an overlap, all counterfactual;
  - FIGI succession: a counterfactual match / CLBK's real mismatch;
  - share class;
  - hold: before a new symbol / not for a reserve or counted one;
  - count stop: 499 / 500;
  - kept answer;
  - cap met mid-hold;
  - the reserve on the frozen files / an invariant on the live ones.
- **End to end:**
  - real bars → `reconcile` → `prices.read_store` → the checks (`series_gap`,
    `history_across_ids`), before and after;
  - the real builder (`build_universe`): a reuse inside Polygon's window hides HOS's rename
    without the tenure row and not with it;
  - `prices.load` holds the reserve and prints the budget;
  - a second checkout re-files from the committed table without asking Polygon;
  - AST pins hold every refresh call site to `first_sessions`.
- **Mutation: 48 of 48 killed on the final code**, stale bytecode off, baseline green. The first
  pass killed 45 of 47:
  - "the tenure table rewritten" and "reserve page names not first" survived, and each got a pin;
  - a third mutant had been killed by malformed SQL, not by its test; it was rewritten and
    re-run;
  - review round 0 added the 48th: carried bars re-filed.
- **The real run caught one defect the fixture had not.** The reserve read the monitor's
  assignments through `read_assignments(data_dir.parent)`, which appends `data/monitor`. Under any
  folder not named `data` it read nothing, quietly. It now reads beside `data_dir`, pinned with
  counterfactual XLK and QQQ benchmarks.
- **The outcome fence caught the first cut.** It reached `vinci.monitor` from `vinci.screens`
  through `universe` → `eod.identity` → the scorecard (`quality.sources.prices`, for its hole
  definition) → `eod.dividends`. `GAP_SESSIONS`, `market_sessions` and `missed_sessions` now live
  in `eod.client`, and the scorecard and the repair both import that one definition
  (`tests/test_outcome_import_fences.py`, green).
- **Review, round 1 (Codex P2, #839): the fund-type proof needs the line's type STATED.**
  - The first cut read a line record Polygon could not serve after the hole, or one with no
    `type`, as "not a fund". A fund-type record before the hole then "proved" another security,
    and a fund's own history would have left it.
  - The type must now be present and not a fund. Pinned by
    `test_a_line_whose_own_type_is_unknown_is_not_proven_by_type`, red on the PR head.
  - The real run is unchanged: re-run from the backup, the same 30 + 2 rows and identical tables.
    WLTH's and LUXE's own records state CS and ADRC.
- **Incident → invariant (shipped Y, twice):**
  - a bar filed under today's holder of its ticker → `holders()` plus the committed tenure and
    alias tables, pinned by `test_a_reused_tickers_former_bars_are_never_filed_under_the_current_id`
    and `test_every_refresh_files_by_the_committed_tables`;
  - a scorecard that can spend scoring's Tiingo symbols → `TiingoBudget`, pinned by
    `test_the_reserve_is_held_before_any_new_symbol_is_asked` and
    `test_the_checks_stop_when_the_count_leaves_no_room`.
- **Pins moved deliberately:** the two fake Tiingo clients in `test_quality_prices_flags.py`
  gained `symbols_asked` (an empty month) and `cached_rows` (nothing kept), the two calls the
  budget adds.
- **Review, round 0 (`/code-review high --fix`): 5 findings, all fixed.**
  1. **Fixed behind a pin that fails first:** `refile_bars` would have moved bars an alias had
     CARRIED to the line (`polygon-alias:`). For a line that is both a reuse's holder and a
     rename's successor, that strips the carry every build, and the carry re-runs: a cycle. Pinned
     by `test_a_carried_history_is_never_refiled_off_its_line`, red on the pre-fix query.
  2. **Fixed:** the hole scan built every line's full bar history. It now reads dates only
     (`Store.bar_dates`), and the whole-store pass fell from 1 min 44 s to 4 s.
  3. **Fixed:** the hole calendar counted securities' ids only. It now counts every stored row,
     as the scorecard does (`Store.bars_per_session`), re-filed former holders included.
  4. **Fixed:** the FIGI succession probe is skipped when the line carries no FIGI (XPRO).
  5. **Fixed:** an unreadable EDGAR filing list (a `ValueError`) ends no build. As before, it
     proves nothing.

  The real run was repeated from the backup after the fixes: identical tables and the same 30 + 2
  rows, 11,047 bars re-filed and 2,450 carried; a second run moves nothing.
- **Suite:** `pytest -m "not network"`: 7,581 passed, 529 skipped, 0 failed (2026-10-28, this branch's final tree with the store copy linked). The full run reported 7,580 passed and 1 failed: the records test refusing this record's empty `prs:` trail, green once the number was written

**BOUNDARY.**
- **Store:** the read-only backup above. 2,797 → 2,827 names, 2,681,540 → 2,683,990 bars, 1,287
  market sessions from 2021-09-01 to 2026-10-16 (+43 partial). Measured 2026-10-28 between 11:00
  and 14:00 IST, at main 89d37d23 (BEFORE) and this branch (AFTER).
- **Holes:** steps across more than 10 market sessions on that store's calendar: 52 on 35 ids
  before, 22 on 7 ids after.
- **Polygon:** `/v3/reference/tickers/<T>?date=` as of each hole's last bar (and its first after,
  where the CIK could not decide), read 2026-10-28; about 110 calls, each kept for good.
- **EDGAR:** submissions for CIKs 2126198, 1575828, 2115119 and 1723596, read 2026-10-28.
- **Tiingo:** the October count is the distinct symbols in the URLs of entries in this checkout's
  linked cache (the primary's `data/cache/tiingo`) fetched in October UTC: 108 before this build,
  110 after.
  - Machine-wide, the caches held 112 distinct symbols looked up in October, against the 500 the
    key met.
  - Requests this build made: 2 served (SPY, MDY), and WVE refused on each of 3 scorecard runs.
- **Population:** the committed 2026-10-16 primary snapshot.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **ACCEPTED: Polygon's dated record decides.** A record Polygon dates wrongly would file a
  segment under the wrong security.
  - The 13 after-records read here all name today's line.
  - FALSIFIER: a re-filed segment whose Tiingo series under the current holder runs through it.
- **ACCEPTED: the bars before an earlier hole go with the newest proven one.** All bars before
  the tenure go to the holder named at the newest proven hole.
  - On the two multi-hole reuses (TRON's 9 holes, LION's 3), every hole's record names the same
    filer.
  - FALSIFIER: an earlier hole whose record names a third filer.
- **ACCEPTED: a new FIGI under one filer is another security** (DBD, OPI, SEZL, CORZ, CORZW: each
  the equity issued at a reorganisation; Tiingo starts a new series at CORZ's and OPI's).
  - FALSIFIER: a class Polygon re-FIGIs with no corporate event.
- **COST: a successor's boundary is its first held bar.** A successor holding none is left for
  the next build, so it is screened on its own short history once.
- **COST: unproven holes re-read their records every run.** These are the 22 left, and each record
  is kept for good, so it is a cache read, not a request.
- **COST: the hold looks up reserve symbols this cache has not counted.** In October that was 2,
  both already held on the key.
- **NOT PROTECTED: a month whose cap is met before the scorecard's first run.** That can happen
  through CI or theme intelligence; the hold then fails, by name, in the header.
  - The paid plan is the operator's option (STATE.md §5.0 row 32 item 24).
- **ACCEPTED: the month turns on UTC.** Tiingo does not say which clock it uses.
- **NOT WRITTEN: today's prices snapshot.**
  - `data_quality/prices/2026-10-28.json` is #835's AFTER, and its record cites that path and
    sha. Overwriting it would make that record false, and `--write` refuses any date but today.
  - The next dated run records this state.
- **FOUND, NOT FIXED:**
  - **The old CLBK id keeps an unrestated step.** Its own series steps 24.50 → 11.08 on
    2026-07-21, the 2.2 exchange held unrestated. `split_shaped_step` cannot see it (2.2 is not a
    whole number), and the old id is never rewritten. The successor carries the restated series,
    and the old id has left the population.
  - **BHVN, WOLF and SRXH:** identity steps with no hole, which this rule does not trigger on.
  - **`refresh --aggs`:** a name whose every aggregate falls before its first session now raises
    "returned NO bars" (fail loud).
- **OPERATOR:** run `vinci reattribute-prices` on the primary's store (STATE.md §5.0 row 32 item
  25). Rehearsed on a read-only backup of the primary's store as found on 2026-10-28 (2,572,227
  bars, ending 2026-08-05), with this branch's two tables, never on the store itself:
  - **11,047 bars re-filed** off the same 30 ids, no new reuse found, 0 bars changed in place;
  - **no succession:** that store holds no new XPRO or CLBK id yet; its next weekly build
    records the pair and carries it;
  - **ledger and benchmarks identical:** IT, SMPL and VRRM 1,236 bars each; IWM 1,236, MDY 1,236
    and SPY 307; GOOGL has no bars there.
