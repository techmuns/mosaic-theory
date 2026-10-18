---
id: 2026-10-17-benchmark-bar-guard
status: recorded
date: 2026-10-17
prs: [743]
supersedes:
superseded-by:
---

# A benchmark close older than the date it is labelled with is refused, never read

**WHAT.** STATE §5.0 row 32 (7), the guard half: "add the missing guard (refuse a benchmark bar
older than its label)". Operator instruction, 2026-10-17: "build the benchmark guard".

**THE DEFECT.** The dossier's market-relative figures (`mechanical._idiosyncratic_vs_shared`: the
name's 180-day move, the benchmark's, and the difference) and the 52-week chart
(`_stock_performance`) read every benchmark close through `_close_on_or_before`. That returns the
latest close at or before a date, however far back it is. On 2026-10-07 SPY and MDY had stopped
at 2026-09-16, so on pages dated 2026-09-22 the 09-16 close went out as the 09-22 close.
- SPY rose 2.6% in those four days, so seven SPY pages understated the market's move by that much;
  MDY's four pages by 0.7% (`docs/records/2026-10-07-nflx-onto-fresh-ciq-and-prices.md`).
- **The screen had already fixed this exact defect on 2026-07-30.** `vinci.eod.features.relative_return`
  ends both legs on the COMMON last bar and stamps it. The dossier never adopted that rule.

**THE FIX.**
- **`_market_legs`** (new, in `vinci/dossier/mechanical.py`) builds the three figures, and
  `_idiosyncratic_vs_shared` calls it.
  - Both legs end on the common last bar, as the screen's do, and every figure is stamped with
    that date ("to 2026-09-21"), not the page's date.
  - **A benchmark whose latest close is more than `_COVERAGE_GAP_DAYS` (4) days before the page's
    date is refused.** Four days is the calendar's longest gap between two trading days (a long
    weekend plus a holiday), the repo's existing constant in `vinci/dossier/freshness.py`.
  - When refused, the benchmark's move and the difference are UNKNOWN, and the note names the
    benchmark's latest close, how many days it trails, and `vinci refresh <symbol>`. The name's
    own move still stands.
- **`_covering_close`** is the bounded form of `_close_on_or_before`. The 52-week chart reads the
  benchmark through it: a stale series STOPS its line rather than carrying an old close flat to
  the page's date. Its window return is not stated, and the exhibit's source names where the line
  stopped.
- **`vinci.eod.features.frontier`**, a series' latest bar at or before a date, was the screen's
  nested helper. It is now module-level and shared by both surfaces. The screen's behaviour is
  unchanged (below).

**DOES THIS SELECT ON FORM?** No. No gate, rank or threshold reads these figures. They are context
on the page, and the change refuses a mislabelled value; it does not alter how any value is
judged.

**HOW VERIFIED.**
- **Real run, every committed page.** All 26 dossiers, on this machine's store (IWM through
  2026-10-16, MDY through 2026-08-05, SPY through 2026-07-22), at each page's own date and at
  2026-10-16, old lookup against new. That is 52 cases:
  - **IWM pages, 11 names, 22 cases: every figure identical.**
  - **SPY pages, 9 names, and MDY pages, 6 names, 30 cases: every one refused by the new code.**
    The old lookup had stamped a July or early-August close with the page's date. GOOGL's market
    return read +15.86% "to 2026-09-22" off a July close.
  - The 52-week chart's benchmark return is refused in the same 30 cases and unchanged in the 22.
- **The screen is unchanged.** G2 recomputed with the shared `frontier` for every candidate of
  run `2026-10-16-01` that carries a value: **1,671 of 1,671 identical** to the committed values.
- **Pins:** `tests/test_benchmark_bar_guard.py`, on the committed price fixtures (real Polygon bars,
  GOOGL against IWM), through the real `_idiosyncratic_vs_shared` and `_stock_performance`:
  - the incident's shape (IWM missing 09-17..09-22, page 09-22): refused, both dates and the
    command named, the name's move kept;
  - one missing session (09-22 alone): both legs end on 09-21 and say so;
  - NEGATIVE: complete bars read exactly as before, every value equal to the old lookup's;
  - the chart: the line stops and the return is refused; NEGATIVE: on complete bars every point
    and the return equal the old as-of reading;
  - the screen and the dossier share one `frontier`.
- **Mutation.** 7 mutants, all killed:
  - no refusal;
  - no common end;
  - an unbounded covering close;
  - the stamp reading the page's date;
  - the call site bypassing the legs;
  - `frontier` taking the earliest bar;
  - the refusal note dropped.
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"` with the store moved aside,
  as the weekly workflow runs it: 5868 passed, 512 skipped.

**BOUNDARY.**
- Measured 2026-10-17 on this branch over main 987d2b4e.
- Store: this machine's `data/vinci.db` after the weekly run of 2026-10-17; its benchmark coverage
  is as stated above.
- Population: the 26 committed dossiers; run `2026-10-16-01`'s candidates with a G2 value.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The nine committed pages are NOT changed here.** GOOGL, LLY, NKE, ROST and TGT on SPY; BURL,
  ORKA, PARR and WLK on MDY. They still carry the 2026-09-16 close as 09-22. The guard stops it
  recurring; correcting them is row 32 (7)'s other half, re-assembly or a deterministic refresh,
  still the operator's decision.
- **On this machine, a local assembly of any SPY or MDY page now refuses its market figures** until
  `vinci refresh SPY MDY` runs. That is the guard working: its store holds SPY only to 2026-07-22.
- **Seen, not changed:**
  - A benchmark gap at the window's START (an old anchor) is still read unbounded. The screen
    bounds it (`MAX_ANCHOR_LAG_DAYS`); the dossier's start is not bounded here.
  - The cohort peers' 180-day moves (`_cohort`) read each peer through the same unbounded lookup.
  - Neither was the incident; both are the same family.
