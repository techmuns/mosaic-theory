---
id: 2026-10-24-prices-quality-source
status: shipped
date: 2026-10-24
prs: [795]
supersedes:
superseded-by:
---

# "Are the prices credible?" has a dated answer: the scorecard's second source reads the EOD store's values, Tiingo agrees on 25,411 of 25,412 closes, and the restatement window's stated cost has already landed in a committed screen

**WHAT.** `vinci audit quality --source prices` scores the Polygon EOD prices. The source is one
new module, `vinci/quality/sources/prices.py`. The core and the command are unchanged:
`tests/test_quality_core.py` holds them to that, and its registry pin now reads `ciq`, `prices`.

- **What it reads.** The working store `data/vinci.db` (`prices` and `securities`), opened
  read-only. Beside it, Tiingo's raw closes and split factors for the names with a committed page
  (`data/dossiers/*`, which covers every ledger name and scenario record). Tiingo is read through
  the fund's adapter (`eod.tiingo`, new method `daily_rows`), and only where `TIINGO_API_KEY` is set.
- **Without a store** (CI, a fresh worktree) the corpus is empty, so the command exits 1 saying the
  store is absent. It never prints a clean card. An existing store with no price rows does the same.
- **Items** are securities, named by ticker. A ticker that two securities carry bars for is named
  by internal id instead, for both of them.
- **Six checks.** Five are internal (the store against itself) and one is independent (Tiingo):

| check | compares | unit | rule | can surface |
|---|---|---|---|---|
| `ohlc_ordering` | a bar's open and close against its own high and low | bar | exact: 0 < low ≤ open, close ≤ high; volume ≥ 0 | wrong cell, wrong unit |
| `stale_bar` | a bar against the name's previous stored bar | bar | an exact copy of the previous bar, or zero volume | wrong file, wrong period |
| `flat_close_run` | a close against its neighbours | bar | inside a run of ≥10 identical closes (`FLAT_RUN_SESSIONS`) | wrong period |
| `split_shaped_step` | a close against the previous close | step | ratio within 3% of a whole number ≥2, either way up (`freshness.whole_number_ratio`) | wrong unit, wrong period |
| `series_gap` | a name's dates against the store's market sessions | step | more than 10 market sessions with no bar (`GAP_SESSIONS`) | wrong file |
| `close_vs_tiingo` | the close against Tiingo's for the same session | bar | within 0.5% (`CLOSE_TOL`) | all five |

- **The repo's own rules, where one exists.**
  - The split shape is the rule that already names a corporate action between CIQ panels. It is
    extracted from `freshness.reconcile_cap` as `whole_number_ratio`, and `reconcile_cap` now calls
    it; its behaviour is unchanged.
  - A market session reuses `eod.client._SESSION_PRESENT_FRACTION`: a day holding bars for at least
    half as many names as the store's fullest day. Any other day is partial (a few names'
    backfill). Glossary line added.
  - Tiingo's closes go onto Polygon's basis by dividing each raw close by every split factor Tiingo
    reports on a later day. Polygon's `adjusted=true` restates splits only, and Tiingo's `adj*`
    fields also remove dividends, so they are not used.
  - Theme intelligence holds the same split adjustment (`market.split_adjusted`) and the same band
    (`market.OVERLAP_TOLERANCE`). A fund module may not import it
    (`tests/test_theme_intelligence_isolation.py`, which failed on this build's first draft), so
    both stand in the source on their own.
- **Three new constants, chosen by face validity:**
  - `GAP_SESSIONS = 10`: the longest trading suspension the SEC may order (Exchange Act
    §12(k)(1)(A), 10 business days).
  - `FLAT_RUN_SESSIONS = 10`: two trading weeks.
  - `CLOSE_TOL = 0.005`: the band `freshness.date_of_close` accepts as one price.
- **Coverage map, three families.** `bars.close` is independent, on the Tiingo sample only.
  `bars.range` (open, high, low) and `bars.volume` are internal. Two checks that exist elsewhere
  are listed UNSCORED:
  - the CIQ printed-close match (`freshness.date_of_close`), which dates the comps panel, so it
    agrees by construction wherever it matches;
  - the row-COUNT floor at ingest.
- **Snapshot.** `data/snapshots/data_quality/prices/2026-10-24.json` holds counts and statuses only.
  No price, volume or ratio is in it; dates and counts are.

**WHY.** Prices feed the screens, every page's spot, the monitor and the scoring of the BUY−AVOID
spread, whose first ledger outcome is VRRM on 2026-12-14 (operator, 2026-10-23). Their only guard
was a row COUNT at ingest (`parse_grouped_daily`), which never reads a value. CLAUDE.md: "a count
test catches sparse corruption and cannot catch dense".

**THE ANSWER, 2026-10-24.** The store read is a read-only SQLite backup of the
`research-alpha-audit-bcba59` worktree's store, which is the primary's store plus the 2026-10-16
weekly's refresh. It holds 2,797 names and 2,681,540 bars, over 1,287 market sessions from
2021-09-01 to 2026-10-16, plus 43 partial days. Inputs sha256 `af7deee3…`. The run was at
`909d0808`.

| check | unit | confirmed | differs, unexplained | other |
|---|---|--:|--:|---|
| OHLC ordering | bar | 2,681,540 | 0 | — |
| stale bar | bar | 2,681,465 | 75, on 10 names | — |
| flat close run | bar | 2,681,540 | 0 | — |
| split-shaped step | step | 2,678,579 | 112, on 97 names | 52 steps excluded (across a gap) |
| series gap | step | 2,678,691 | 52, on 35 names | — |
| close vs Tiingo | bar | 25,411 | 1 (FUBO, 2023-05-30) | 26 names run; 2,771 not in the sample |

- **Tiingo agrees with Polygon on every sampled close but one.** That is 25,411 of 25,412 bars,
  across all 26 page names that have bars here, with 0 sessions missing on either side. On a 27-name
  probe earlier the same day (`-ta` store), 22,214 of 23,450 shared closes were EQUAL, and 1,234
  more were within 1e-4. That residue is split-adjustment rounding on FUBO (1,155) and NFLX (79).
- **The one miss is FUBO, 2023-05-30.** It is 0.66% apart, about 1.1 cents on the pre-split price.
  FUBO's later 1-for-12 split puts that day before it.
- **Coverage.** 1 family is independent and 2 are internal. Per failure class (independent /
  internal only / nothing):

| failure class | independent | internal only | nothing |
|---|--:|--:|--:|
| wrong file | 1 | 2 | 0 |
| wrong cell | 1 | 1 | 1 |
| wrong unit | 1 | 1 | 1 |
| wrong period | 1 | 2 | 0 |
| different definition | 1 | 0 | 2 |

  Read it with the boundary: the "independent" row is the close, on 26 of 2,797 names.
- **The second store** (`mosaic-theory-ta`, which the committed pages were assembled from; internal
  checks only): 2,265 names, 2,138,681 bars, 1,282 market sessions from 2021-08-13 to 2026-09-22,
  plus 20 partial days (its latest bar is 2026-10-20). OHLC 0, stale 32 on 3 names, flat 0,
  split-shaped 88 on 79 names (28 excluded), gaps 28 on 26 names.

**FINDINGS — reported, not fixed (hold scope).**

1. **THE RESTATEMENT WINDOW'S STATED COST HAS LANDED, AND IT REACHED A COMMITTED SCREEN.**
   `eod.client.RESTATE_WINDOW_DAYS` (#643) skips held sessions older than 30 days, and its own
   comment names the cost: "a split older than this window leaves the bars before it on the
   pre-split basis until something re-pulls them".
   - **Three names in the store above.** IESC, SFBS and BYND step by a whole number at 2026-08-06,
     the first session pulled after the store's August copy (its earlier bars end 2026-08-05).
   - **Tiingo confirms the splits.** It reports IESC 2-for-1 on 2026-08-24, SFBS 2-for-1 on
     2026-08-21, and BYND 1-for-30 on 2026-08-14. So every IESC, SFBS and BYND bar before
     2026-08-06 is on the pre-split basis.
   - **The `-ta` store has the same splice** for IESC and SFBS, at 2026-08-12.
   - **IESC and SFBS are band-A candidate records** in the committed 2026-10-16 screen run
     (`data/snapshots/candidate_records.jsonl`). Both passed G1, whose drawdown is taken from the
     52-week maximum high. Recomputed from the store's bars, with the pre-2026-08-06 highs divided
     by Tiingo's factor:
     - IESC's drawdown is −68.7% as stored and −38.3% on one basis. It passes G1 either way, but
       the magnitude is wrong.
     - **SFBS's is −57.1% as stored and −14.5% on one basis, which is outside G1's −30%.** Its
       admission rests on the splice.
   - **The primary store will take the same splice at its next refresh.** Its bars end 2026-08-05
     on the old basis, and they are older than the window.
   - The window exists because the Polygon plan serves about 5 requests a minute (STATE.md §5.0
     row 31, where this is noted).
2. **A REUSED TICKER FILES TWO SECURITIES' BARS UNDER ONE ID.** `ingest_prices` maps each day's
   grouped bars by TODAY's `eod_symbol`. So a historical day's bars go to whoever holds the ticker
   now, and the old holder's history is lost.
   - 35 names have a gap of more than 10 market sessions (26 in `-ta`). Most of them are this:
     - BBBY: the old Bed Bath & Beyond's bars, ending 2023-05-02, sit under Beyond Inc's id,
       CIK 1130713;
     - TEN: 2022 bars under Tsakos Energy Navigation's id;
     - NIQ, SAIL, CAI, NP, MRLN, CALY and others.
   - The gap check sees a reuse only when the old security stopped trading more than 10 sessions
     before the new one took the ticker. WOLF's re-listing on consecutive sessions (×18.3 in one
     step) shows only because, from about 17× up, every ratio sits within 3% of some whole number.
3. **TWO HISTORIES BREAK AT A RE-DOMICILE.** XPRO (Expro N.V. → Expro Ltd) and CLBK (Columbia
   Financial's new holding company) each sit under two securities, with no overlap.
   - The new ids carry 51 bars, from 2026-08-06; the old ids end 2026-08-05.
   - Any feature that needs more history reads short for the new id.
4. **ZERO-VOLUME BARS: 75 ON 10 NAMES.** Most are thin BMO ETNs (CARD, JETD, WTID, SHNY) and
   CALY's 2023 bars, which are a different security under today's ticker (finding 2). Two are
   exact copies of the bar before (GEGGL 2023-06-13, HHH 2022-07-14).
5. **THE STORE IS PRICE RETURN.** Polygon's closes equal Tiingo's raw closes ÷ split factors,
   dividend payers included, back to 2021. So every return read from the store excludes
   dividends. The monitor already says so. `vinci/scoring/baseline.py` calls its basket return a
   "total return" while it reads the same closes. That is a wording defect, in a protected file.
6. **STORES DIFFER BY CHECKOUT, AND ONE PAGE NAME IS MISSING FROM THE FRESHEST.**
   - The primary's store ends 2026-08-05.
   - The `-ta` store's whole-market days end 2026-09-22; its 20 later days hold 4–30 names each.
   - The research-alpha copy reaches 2026-10-16. It holds no TJX bars (TJX came into `-ta` by
     a per-name backfill).
7. **THE SPLIT CHECK IS A SCREEN, NOT A VERDICT.** Of its 112 differences, 106 traded at least 3×
   their 20-bar median volume, which looks like news. The other six include the three splices of
   finding 1.
   - Dollar volume, which a split leaves unchanged, gives no clean break: 3 steps sit below 1.5×
     normal, 7 below 3× and 14 below 5×, with spin-offs such as BHVN and CTVA in the low tail.
   - So no news-day exemption is built. A difference here means "look", and the Tiingo check
     decides it on its sample.

**HOW VERIFIED.**

- **Real run** on the store above (output summarized in THE ANSWER). It took 16 s: about 10 s to
  load, about 1 s to score, and the rest on Tiingo.
- **Corpus before synthetic.** OHLC ordering and flat runs read 0 on both stores. So
  `test_the_all_clear_checks_fire_on_a_perturbed_live_series` takes the live store's longest series
  and plants five shapes in memory. A high below the low, a zero volume, a ten-bar frozen close and
  an unrestated 2-for-1 each fire their check, and so does a gap over 10 sessions. The untouched
  series stays quiet. That test runs wherever `data/vinci.db` exists and skips in CI.
- **Frozen fixture** through the real types (`Store`, `Identity`, `PriceBar`), with synthetic
  values, and Tiingo rows in the served shape (its field set was measured live).
  - Every status of every check is pinned, with these edges: a run of exactly 10 against one of 9;
    ×2.05 (2.5% from 2) against ×2.07 (3.5%); 11 missed sessions against 10; and a close exactly
    on the 0.5% band.
  - A partial Saturday inside a 10-session gap must not make it 11.
  - Also pinned: a 2:1 split inside the Tiingo series; a session Tiingo lacks; a 404, a symbol
    with no rows, and a share class sent hyphenated (NNN.B is asked for as NNN-B); a high below the
    low and a negative volume written past `PriceBar`; one ticker on two securities; an absent store
    and an empty one, through the command.
- **No-leak guard.** A sentinel price and volume sit in every bar, and neither reaches the card.
  Every number in the card and in the committed snapshot is an integer (56,193 of them).
- **Mutation:** 31 of 31 mutants killed, with stale bytecode off. Two survived the first pass:
  M2 (close below low) and M4 (open below low). The plants were overlapping, so the fixture was
  separated.
- **Isolation.** The first draft imported theme intelligence's Tiingo reader and helpers. The full
  suite caught it (`test_no_fund_module_imports_theme_intelligence`), and it was rewritten onto the
  fund's adapter.
- **Splits confirmed independently** of the store, by Tiingo's split factors (finding 1), with 3
  requests.
- **Suite.** `pytest -m "not network"`: 6,496 passed, 527 skipped, 0 failed (before review). The
  `bin/commit` gate was green on `64f15580` and `909d0808`.
- **Review.** `/code-review high --fix`, round 0, 7 findings:
  - Four fixed: share-class symbols reach Tiingo hyphenated; a failed request keeps its status; the
    live test calls the source's calendar helpers; its gap-free-step search cannot index past the
    end.
  - Two skipped: the Tiingo cache follows the cwd (the command always passes cwd as root), and
    per-row date parsing (2 s of a 9.6 s load).
  - One no-change: a collided ticker is fetched twice, but no page name is collided.

**BOUNDARY.**

- **The scorecard.** Every security with at least one bar in the store named in THE ANSWER: 2,797
  names, measured 2026-10-24 at `909d0808`. Units are per check (bar or step), as in the table.
  Market sessions are store days holding ≥50% of the most names any day holds.
- **The Tiingo sample.** The 27 committed pages at `909d0808`, of which 26 have bars in that
  store. Spans run from each name's first to its last stored bar.
- **The equal-close count** (22,214 of 23,450). The 27 page names against the `-ta` store, over
  each name's stored span, measured 2026-10-24 with a scratch script.
- **The drawdowns.** IESC and SFBS, the 2025-10-16 → 2026-10-16 window (252 bars), maximum high,
  from the research-alpha copy.
- **The volume characterization.** The 112 split-shaped steps, against each name's previous 20
  stored bars.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: the scorecard judges whichever store sits at `data/vinci.db`.** Stores differ by
  checkout, so the boundary line names the store's span, its partial days and its latest bar, and
  the sha256 names what was read. Nothing names WHICH checkout's store it was. Falsifier: two
  snapshots with the same date range and different sha256 that nobody can attribute.
- **ACCEPTED: the independent check covers the close on the page names only** (26 of 2,797).
  Tiingo is one request a name, and its plan allows 50 an hour. Highs, lows and volume are not
  compared. Every other name relies on the internal checks.
- **ACCEPTED: the split check misses a 3-for-2 or 5-for-4** (ratios 1.5 and 1.25 are not whole
  numbers). It also flags genuine halvings and doublings (finding 7). The Tiingo check catches any
  basis error on its sample.
- **ACCEPTED: `FLAT_RUN_SESSIONS` sits above the longest real run measured** (8 bars, CCO, pinned at
  a pending cash deal). It reads 0 on both stores. It was set by face validity, not outcomes, and
  is shown to fire on a live series.
- **COST: the snapshot is 2.1 MB** (98,394 lines; 97 KB gzipped). The core writes every name for
  every check, and the core was not to change in this build. A compact form that writes only the
  names with a non-confirmed unit would be a core change, and it is the operator's call.
- **COST: two copies across the isolation wall.** The split adjustment and the 0.5% band exist in
  theme intelligence and here. That is the wall's price.
- **Extracted:** `freshness.whole_number_ratio`, with `reconcile_cap`'s behaviour unchanged, and
  `TiingoEodClient.daily_rows`, which `price_history` now parses, also unchanged.
