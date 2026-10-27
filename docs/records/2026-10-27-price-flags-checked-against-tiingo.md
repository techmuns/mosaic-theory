---
id: 2026-10-27-price-flags-checked-against-tiingo
status: open
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# Every step and zero-volume bar the price checks flag gets Tiingo's verdict: the 49 old split-like jumps hold 0 unadjusted splits (45 real moves, 1 spin-off splice), the store's own defects are measured and their causes sit in L8's files, and the IESC/SFBS/BYND repair is one operator command

**WHAT.** Wave 2, lane L7, items 13–15. Three checks join the prices scorecard
(`vinci/quality/sources/prices.py`); the core and the command are unchanged, and nothing here writes
a bar.

| check | compares | unit | rule | independence |
|---|---|---|---|---|
| `step_vs_tiingo` | every step `split_shaped_step` or `series_gap` flags, against Tiingo's same two sessions | step | the stored ratio within 0.5% (`CLOSE_TOL`) of Tiingo's raw ratio × the split factors Tiingo reports after the first session and up to the second: confirmed. The stored ratio is Tiingo's RAW ratio instead: differs, STATED (a split held unadjusted). Tiingo serves the later session but nothing on or before the earlier: differs (another security under the ticker). Tiingo lacks the later session, or the earlier one inside a running series: unchecked | independent |
| `zero_volume_vs_tiingo` | every zero-volume bar, against Tiingo's same session | bar | Tiingo also records no trading (volume 0, or no row inside a running series): confirmed; Tiingo records trades: differs; before Tiingo's series under the ticker begins: unchecked | independent |
| `history_across_ids` | a security's span, against every other security carrying its ticker | security | more than `GAP_SESSIONS` (10) market sessions apart: confirmed (two securities in turn); abutting or overlapping: differs (one history across two ids, or two series at once) | internal |

- **One Tiingo request a name.** A flagged name's window runs from two weeks (`FLAGGED_LEAD`) before
  its first flagged session to its last (`flagged_window`). A page name that is also flagged is one
  request, reaching back to that lead. Page names are asked first.
- **Kept once read.** A window that ended 30 days ago (`CLOSED_WINDOW_DAYS`) is cached for good
  (`TiingoEodClient.daily_rows(ttl_seconds=None)`, new keyword; every other caller keeps a day). So
  a flagged name costs a request once, not every run.
- **A plan limit stops the asking.** The first 429, or the first `TiingoRefusedError` (below), ends
  the run's requests; the rest read `not_run` by name ("not asked: hourly rate limit" / "monthly
  symbol limit").
- **A refusal served as 200 is refused** (`vinci/eod/tiingo.py`): a body that is not a list of rows
  raises `TiingoRefusedError` and is dropped from the cache. Before, `daily_rows` returned it as data
  (a dividend read would have failed on an "unreadable Tiingo row", a scorecard read as a TypeError),
  and a closed window would have replayed it for good.

**WHY.** #796 left 49 split-shaped steps unexplained because they predate Polygon's two-year window,
and #795 named three defects in the store itself — reused tickers, re-domiciles, zero-volume bars —
that no check measured. Prices feed the screens, every page's spot, the monitor and the scoring of
the BUY−AVOID spread (#820).

**THE STORE AND THE BEFORE (VERIFY-AT-BUILD).** The 2026-10-26 snapshot was the BEFORE. It was
measured on a backup of `research-alpha-audit-bcba59`'s store after `restate-prices --through
2026-08-05`. That state was rebuilt here: a read-only SQLite backup of the same store, then the same
command, which restated the same 10 names by the same factors as #796. `origin/main`'s own code on
that copy, with today's Tiingo reads, gives inputs sha256 **`80ed8324…`**, the committed BEFORE's
hash, and every count equals it: 2,797 names, 2,681,540 bars, stale 75, split-shaped 109, gaps 52,
Tiingo 25,411 of 25,412.

**THE AFTER (measured 2026-10-28 01:00 IST at 1d3809d4, `data/snapshots/data_quality/prices/2026-10-28.json`).** Same store; the six
old checks read exactly as before.

| check | unit | confirmed | differs, stated | differs, unexplained | unchecked | not run | other |
|---|---|--:|--:|--:|--:|--:|---|
| OHLC ordering · stale bar · flat close run | bar | 2,681,540 · 2,681,465 · 2,681,540 | 0 | 0 · 75 · 0 | 0 | 0 | as BEFORE |
| split-shaped step · series gap | step | 2,678,582 · 2,678,691 | 0 | 109 · 52 | 0 | 0 | 52 steps excluded (across a gap) |
| close vs Tiingo | bar | 25,411 | 0 | 1 (FUBO 2023-05-30) | 0 | 0 | 26 names run, as BEFORE |
| **step vs Tiingo** | step | **65** | **0** | **13** | **6** | 52 names | 84 steps on 73 names read; 2,672 names have no flagged step |
| **zero volume vs Tiingo** | bar | **20** | 0 | **44** | **8** | 1 name (HHH) | 72 bars on 8 names read |
| **history across ids** | security | 0 | 0 | **4** (XPRO ×2, CLBK ×2) | 0 | 0 | 2,793 names carry a ticker no other security does |

Inputs sha256 `7f398b3e…`; it differs from the BEFORE's because the hash now also covers the flagged
names' Tiingo rows and each security's distance from another carrier of its ticker. Every not-run
name reads Tiingo's monthly cap: WVE was refused, and the 51 after it were not asked.

**ITEM 13 — THE 49 SPLIT-LIKE JUMPS OLDER THAN POLYGON'S WINDOW.** These are the split-shaped steps
whose earlier session is before 2024-10-28 (49 steps, 45 names), as #796 counted them. One Tiingo
request a name:

| verdict | steps | names |
|---|--:|---|
| real price move: Tiingo's split-adjusted ratio agrees within 0.5% (all 45 to 4 decimals) | 45 | 41 names (AKBA, APEI, APLD, … MNPR ×4, CCCC ×2) |
| unadjusted real split (the stored ratio is Tiingo's RAW ratio across a split) | **0** | — |
| data error: two securities under one id | 1 | BHVN 2022-10-04: the store steps ×0.05 from the old Biohaven (acquired by Pfizer) to the spun-off one; Tiingo's series rises 19% that day |
| unchecked: Tiingo serves nothing under today's ticker for those sessions | 2 | BBBY 2023-02-07, CORZ 2022-12-21 (each ticker now names a later security) |
| not run: refused by Tiingo's monthly cap | 1 | LION 2023-02-28 (an earlier probe the same day showed Tiingo's LION begins 2025-05-05: a reused ticker) |

So the store holds **no unadjusted split** among them. 44 of the 45 real moves traded 10× to 5,427× their
previous 20 stored bars' median volume (ZJYL's 1.6× is the one below); most are biotech readouts. The four that are not real moves are all identity: another security's bars under today's
id, which is item 14's defect.

**ITEM 14 — THE STORE'S OWN DEFECTS, MEASURED; NONE IS FIXED IN L7's FILES, BECAUSE NONE IS CAUSED
THERE.**

1. **Reused tickers file two companies' bars under one id.**
   - The cause is in `vinci/eod/client.py::ingest_prices` (L8's file). It builds `sym_to_id` from
     TODAY's `eod_symbol` and applies it to every fetched day, so a former holder's bars go to the
     current holder's id.
   - `step_vs_tiingo` on `series_gap`'s 52 steps (35 names), measured:
     - 10 differ: Tiingo's security under the ticker is another across the hole. They are ACIC, CALY,
       CBIO, CD, CORZ, GOLD, OPI, RCD, TEN, WLTH.
     - 1 confirmed: BANFP, one security with a hole in the store.
     - 2 unchecked: BBBY and DBD.
     - 39 not run: the monthly cap.
   - Inside Polygon's window two split-shaped steps differ the same way: WOLF 2025-09-29 (the
     restructured equity) and SRXH 2026-07-06.
   - Reported to L8 (shared notes `l7-price-store-defects.md`), with the key it is building for
     renames: share-class FIGI plus a validity window.
2. **Re-domiciles break a history.** `history_across_ids` differs on 4 securities: XPRO and CLBK,
   each an old filer whose bars end 2026-08-05 and a new one whose bars begin 2026-08-06, 0 market
   sessions apart. It confirms none and is not applicable to the other 2,793. Fixing it means
   succession in identity: the resolver, L8's.
   - **The twin, found and not scored: renames.** One CIK on two tickers with spans at most 10
     sessions apart gives 9 pairs on the same store: 7 renames (IA/ISSC, SCVL/SHOE, DMC/FDP,
     HAPN/LC, ODV/OGG, STLN/TOI, VSCO/VSXY) and 2 common/preferred line swaps (UMBF/UMBFO,
     WTFC/WTFCN). A CIK rule would read the swaps as one history, so it is not built. L8 has the
     rename bridge.
3. **Zero-volume bars.** `stale_bar`'s 75 are 73 zero-volume bars plus 2 exact repeats (GEGGL
   2023-06-13, HHH 2022-07-14), on 10 names.
   - **42 are on ETNs/ETPs** (CARD 17, JETD 11, WTID 10, YCL 2, SHNY 1, DZZ 1). Tiingo confirms no
     trading on 20 and records 1 to 17,098 shares on 22.
     - On 41 of the 42 Tiingo's raw close equals the stored close exactly. These are thin sessions
       with the price right and the volume under-reported by Polygon's grouped feed, not wrong
       prices.
     - SHNY's one bar sits at a tenth of Tiingo's raw close, a split basis; its volume verdict is
       unaffected.
   - **31 are on reused-ticker securities** (CALY 22, WLTH 8, HHH 1). CALY's 2023 bars differ:
     Tiingo's CALY trades millions of shares a day then, at about 2.5× the stored close.
   - Nothing to repair in the store: no second volume is substituted. Removing the ETNs from the
     screened population is L8's security typing.

**ITEM 15 — THE IESC, SFBS AND BYND SPLICE IN THE PRIMARY'S STORE.** Rehearsed on read-only backups
of the primary's store (2,572,227 bars, ending 2026-08-05), never on the store itself.

- **`restate-prices --through 2026-08-05`**, the store's last market session and so its one
  boundary. It made 1 grouped-daily call and restated 10 names, every bar through 2026-08-05: IESC,
  SFBS and BYND (1,236 bars each), AIXI 855, ETHA 511, IMMP 1,227, LHSW 336, NVX 1,125, REAX 1,236,
  SCNI 730 — 9,728 bars in all. The factors are IESC ×0.5, SFBS ×0.5, BYND ×30, AIXI ×7, ETHA ×3,
  IMMP ×20, LHSW ×8, NVX ×10, REAX ×10, SCNI ×10. No other bar moved: IT, SMPL, VRRM, IWM, MDY and
  SPY are unchanged, and GOOGL has no bars in that store.
- **The next refresh instead**, run-monthly's own price step (`ingest_prices` over every security
  to 2026-10-26, then IWM). Its anchor is 2026-08-05, it restates the same 10 by the same factors,
  and it adds 57 bars to each name. `restate-prices` after it prints `0 name(s) restated`.
- **Both orders leave identical stores**: 2,704,807 bars, 0 differing beyond 1e-9.
- **PSTV**, which #796 found ×0.04 behind Polygon in the research-alpha copy, is already on Polygon's
  current basis in the primary's store (factor 1.0 at its last bar, 2026-07-31).
- The command and its expected effect are STATE.md §5.0 row 32 item (22), as an operator action. No
  primary store was written.

**FOUND BUILDING IT — TIINGO'S MONTHLY SYMBOL CAP.**

- From 2026-10-27 20:01 IST, during this build's second batch, Tiingo answered HTTP 200 with
  `{"detail": "You have run over your 500 symbol look up for this month..."}` for new symbols.
- The cap is 500 distinct symbols a calendar month for the whole key. Theme intelligence, CI, the
  monitor and scoring share it. The fund's cache saw 153 distinct symbols in October; the rest of
  the count is outside it.
- `daily_rows` cast that body to rows, so a dividend read would have failed on an "unreadable
  Tiingo row". A closed window would have replayed the body for good: 45 such bodies had been
  cached by this build's own warm-up runs, and were removed.
- **Incident → invariant (shipped Y):** a non-list body raises `TiingoRefusedError`, is dropped from
  the cache, and stops the scorecard asking. Pinned by
  `test_a_refusal_served_as_200_is_raised_and_never_kept`.
- **It refuses only NEW symbols.** On 2026-10-28 at 00:45 IST, VRRM, already looked up this month,
  was served (5 rows). The monitor's and scoring's names and benchmarks are all such symbols, so
  they are unaffected. A name new to the key this month is refused until 2026-11-01.

**NO LEDGER NAME'S BARS CHANGE.** This build writes no bar. The operator command restates 10 names,
none of them a ledger name or benchmark (rehearsal above).

**HOW VERIFIED.**

- **Corpus first.** Each new check fires on the live store copy before any fixture:
  - `history_across_ids` differs on XPRO and CLBK.
  - `step_vs_tiingo` differs on BHVN and the 10 reuses.
  - `zero_volume_vs_tiingo` differs on 44 bars and confirms 20.
- **Frozen fixture** through the real types (`Store`, `Identity`, `PriceBar`). It plants the live
  failure SHAPES, with synthetic price levels because the repo is public:
  - a real fall of half (AKBA-shaped), and a split held unadjusted;
  - a split on the earlier session, which is not the step's;
  - the BHVN spin-off, a reuse across a hole (CORZ/LION), and one security's hole;
  - both unchecked shapes, and both sides of the 0.5% band;
  - CARD-shaped no-trade sessions, including one before Tiingo's series begins;
  - XPRO's abutting ids, two securities exactly `GAP_SESSIONS` apart and one session further;
  - a page name with a flag, a 404, no key, five unreadable row shapes;
  - both plan limits, and a 200 refusal.

  Each check has a positive and a negative pin.
- **The real run caught one defect the fixture had not.** The first final run stopped asking after
  the cap, and then refused even names whose answers were already kept. BHVN, CORZ, CCCC and others
  read not_run though cached. After a stop, a kept answer is now still read (`cached_rows`, never a
  request), pinned in the plan-limit test, and the snapshot is from the re-run.
- **Mutation: 41 of 41 killed**, stale bytecode off, on a baseline proven green with the
  snapshot-ids pin deselected (that pin is red until this commit's snapshot exists). The first pass
  was invalid: every mutant "died" on that pin, which was caught and re-run. The second pass left 4
  survivors. Three were missing pins (no rows at all ×2, a negative volume), now added; the fourth
  was a redundant guard, now removed.
- **Pins moved deliberately:**
  - Tiingo is now asked for flagged names, not only page names
    (`test_tiingo_is_asked_for_once_and_only_when_a_sampled_or_flagged_name_has_bars`).
  - `bars.volume` is independent, through `zero_volume_vs_tiingo`.
- **Suite.** `pytest -m "not network"` on the final tree: 7,346 passed, 526 skipped, 0 failed (2026-10-28, at 1d3809d4 plus this artifact commit, with the store copy linked so the store-dependent tests ran).
- **Review.** `/code-review high --fix`, round 0, 5 findings:
  - 1 fixed: a not-run reason cut at 40 characters.
  - 3 skipped: renames, as above; a recomputed flag scan (about 1–2 s on a 16 s run); two row
    validators that read different fields.
  - 1 no change: a missing Tiingo row read as no trade is the stated rule.
  - A second pass over the refusal code added after it found 1 more, fixed behind a pin: any
    200 refusal stopped the run labelled "monthly symbol limit". Only the cap stops it now
    (`TiingoRefusedError.monthly_cap`). The snapshot, measured at 1d3809d4 just before this fix,
    is unaffected: its one refusal was the cap.

**BOUNDARY.**

- **The store.** A read-only backup of `research-alpha-audit-bcba59`'s store, restated through
  2026-08-05: 2,797 names, 2,681,540 bars, 1,287 market sessions from 2021-09-01 to 2026-10-16 (+43
  partial). Measured 2026-10-28 01:00 IST at 1d3809d4 (this branch's code commit).
- **"Older than Polygon's window."** Earlier session before 2024-10-28, #796's cut.
- **Tiingo.** Read 2026-10-27 18:22–23:38 IST, plus the final run. All 26 page names and 79 of the
  131 flagged names were read; the other 52 were refused or not asked, all after the cap. Each window runs from 14 days before a name's
  first flagged session to its last.
- **Renames.** Same CIK, different tickers, spans 0–10 market sessions apart, on the same store.
- **The rehearsal.** Two backups of the primary's store (ending 2026-08-05) as found on 2026-10-27,
  with Polygon's cache fresh for 2026-08-05 → 2026-10-26.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: a closed window is kept for good.** A Tiingo correction to a session more than 30 days
  old is never re-read on this machine. Falsifier: deleting such a cache entry and re-reading it
  gives a different raw close, volume or split factor.
- **ACCEPTED: 52 flagged names read `not_run` until Tiingo's month resets (2026-11-01).** After that,
  the next scorecard run asks for them. Every other run costs about the page names.
- **COST: the first pass spends Tiingo's monthly symbols.** It used 157 symbols, against 500 a month
  shared with theme intelligence, CI, the monitor and scoring. Steady state is the page names plus
  any newly flagged name. **The key's October cap is met**: until 2026-11-01 no new symbol can be
  read by anyone using the key (theme intelligence's market step included). Symbols already read
  this month still are.
- **ACCEPTED: "no row inside a running series" confirms a zero volume.** It cannot tell a no-trade
  session from a Tiingo data hole. Falsifier: a confirmed zero on a session Polygon's aggregates
  later serve with volume.
- **NOT BUILT: renames, the reuse fix, ETN typing** — all L8's.
- **The Tiingo hourly window is not established.** One reading looked like a clock hour (54 accepted
  in a trailing hour), the next did not (a 00:00 request refused 22 minutes after 50 others).
  RUNBOOKS §k says so.
