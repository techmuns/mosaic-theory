---
id: 2026-10-07-nflx-onto-fresh-ciq-and-prices
status: shipped
date: 2026-10-07
prs: [668]
supersedes:
superseded-by:
---

# NFLX onto fresh CIQ and fresh prices — and the refresh exposed a hole under eleven pages

**WHAT.** NFLX re-assembled on `13b97034` (caching #665 + credit panels #667) after the operator
re-pulled five CIQ exports on 2026-10-07 — Estimates Report, Comparable Analysis, Credit Health Panel,
Public Company Profile, Key Developments. The other six files were byte-identical; the old folder is
backed up outside the repo and the Drive folder's `.DS_Store` was not copied. Artifacts only.

**PRICES WERE REFRESHED FIRST** (§5.0 row 32 (3)): `vinci refresh`, grouped-daily, the 26 dossier
names + IWM/MDY/SPY, 2026-09-23..2026-10-06 — 10 trading days, 290 bars, all 29 now reach 2026-10-06.
The ~2,111 screening-universe names stay at 2026-09-22 (the refresh writes only the tickers it is
given); nothing in a dossier build compares against them, and the next weekly screen refreshes them.

## The refresh exposed a hole in the benchmark history — under eleven committed pages

**MDY and SPY had stopped at 2026-09-16, not 2026-09-22.** The refresh started at 09-23 — the day after
the STORE-WIDE latest bar — on the assumption that every target ended there. It did not, so the two
benchmarks were left missing 09-17..09-22. `test_the_tolerance_matches_the_market_calendars_own_observed_gaps`
caught it on the artifact gate: MDY's largest bar gap read 7 days against IWM's 4. The four days were
backfilled (8 bars); all three benchmarks are back to a 4-day maximum.

**THE HOLE PRE-DATES THIS WORK, AND IT WAS ALREADY WRONG ON THE PAGES.** A dossier's market-relative
figures run "to 2026-09-22" (the fleet as-of) and take the benchmark's close ON OR BEFORE that date.
With SPY missing 09-17..09-22, that lookup returned **the 09-16 close** — labelled 09-22. SPY rose 2.6%
over those four days (754.05 → 773.38), so every SPY-benchmarked page understates the market's return
by about that much and overstates the name's return relative to it; MDY moved 0.7% (665.88 → 670.49).
The refresh did not cause this; by adding bars AFTER the hole it made the hole measurable.

**Eleven committed pages carry it** — benchmark SPY or MDY, end date inside the hole:

    SPY (~2.6 pts)   AMZN  GOOGL  LLY  NFLX  NKE  ROST  TGT
    MDY (~0.7 pts)   BURL  ORKA  PARR  WLK

The other fifteen benchmark to IWM (complete through 09-22) or carry no benchmark figure. **NFLX is
fixed here — re-assembled a second time on the complete history. The other ten are NOT**: they need a
re-assembly or a deterministic refresh of `idiosyncratic_vs_shared` + `stock_performance`, and
`scripts/refresh_stock_performance.py` covers only the second and writes past the
`moved_cited_claims` check. That is an operator decision, opened in §5.0 row 32 (7), together with
the missing guard: nothing refuses a benchmark close older than the date it is labelled with.

**NFLX, corrected:**

    SPY 180d return       16.89%  ->  19.89%    (main's page carries the same 16.89%)
    NFLX relative to SPY  -39.57% ->  -42.56%   (the lag behind the market was understated by 3.0 pts)

## What moved (against NFLX's #663 page)

    price              $72.16 (2026-09-22)  ->  $68.69 (2026-10-06)
    comps market cap   $305,466.6M (09-21)  ->  $286,021.0M (10-06)
    consensus floor    >=2026-09-18          ->  >=2026-10-06
    P/FY26E norm/GAAP  20.1x / 20.2x         ->  19.1x / 19.2x   (EPS ~unchanged, $3.59 / $3.58)
    P/FY27E norm/GAAP  18.9x / 18.9x         ->  18.0x / 18.1x
    credit health      prose, comps only     ->  BOTH panels: industry (22) 1/1/1/2 · comps (10) 2/1/3/2
    lean · draws       strongly-bullish 4/1  ->  strongly-bullish 4/1 — proposal withheld both times
    caveats / qa       7/8                   ->  6/7  (PRICE STALE AT ASSEMBLY gone)

**The cap and the price share a date again.** The old page paired a 09-21 market cap with a 09-22 price;
here both are 10-06, because the comps panel's data date resolves against a bar the store now holds.
**The multiples moved on PRICE, not on estimates** — FY26E EPS is unchanged to the cent.

**The prompt cache, fourth real run** (the corrected build): ~131.5K tokens written by draw 1 and read
by draws 2–5, gaps under 60s, no miss — synthesis ~$1.61 against ~$3.82 uncached, 57.8% saved.

**HOW VERIFIED.** `vinci refresh` exit 0 twice (10 days / 290 bars; then 4 days / 8 bars for MDY+SPY).
`dossier --ticker NFLX` exit 0 twice; the committed page is the SECOND build. ruff clean ·
`mypy --strict vinci` clean · `pytest -m "not network"` exit 0 on the freshly-committed artifacts —
after the backfill, the gap test that caught the hole passes. The eleven-page list is measured from
every committed `dossier.json`'s benchmark symbol and the end dates in its source refs.

**BOUNDARY.** One page shipped (NFLX, 2026-10-07, `claude-opus-4-8`), five files. Prices through the
2026-10-06 close. The 2.6 / 0.7-point figures are the benchmarks' own 09-16 → 09-22 moves; each page's
exact error depends on its window and is not recomputed here.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **NFLX was assembled twice** (~$6 of API in all); the first build used the holed benchmark.
- **The shared price store moved.** AMZN, BURL, LLY, NKE, ROST and TGT pages still show the 09-22 close
  until re-assembled (row 32 (3)).
- **Ten committed pages still carry the stale benchmark close** (row 32 (7)).
- **Why SPY and MDY stopped at 09-16 is not established** — the refresh that should have carried them
  to 09-22 was not examined.
- **Not CI-validated** — the `gate` workflow has failed on Actions billing since #652.
