---
id:
status: shipped
prs: [529]
date: 2026-08-31
supersedes:
superseded-by:
---

# Period-average shares tier — the filers that publish no instant share count are sized, and say so

**WHAT.** A THIRD tier in the universe's share-count lookup
(`EdgarClient.shares_outstanding_with_provenance`): after `dei:EntityCommonStockSharesOutstanding`
and `us-gaap:CommonStockSharesOutstanding` (both filed INSTANT counts), an OPT-IN
`us-gaap:WeightedAverageNumberOfSharesOutstandingBasic` — a PERIOD AVERAGE, queried as a duration
frame (no `I` suffix). The lookup now returns `(values, tag_by_cik)` from ONE implementation, so a
value and its provenance cannot drift apart; `shares_outstanding_by_cik` remains as the
instant-only façade, so the leaders sweep and the assay basket keep exactly the coverage they were
verified on. `build_universe` opts in, stamps each admitted row's `source` with the tag that sized
it (adding `(PERIOD AVERAGE - approximate share count)` where it applies), and counts
`shares_period_average` in the run's health stats.

**WHY — MEASURED FIRST, BUILT SECOND.** The `no_shares` gate dropped **1,919 ticker-rows / 1,420
unique issuers** at the 2026-08-28 build. Quantified before writing any code:
- **827 of the 1,919 rows are not operating-company equity at all** (SPY/QQQ/DIA and other
  ETFs/funds). The instrument-type allowlist would reject them anyway — `no_shares` merely fires
  first in the gate order. The genuine hole is **1,092 rows**.
- By liquidity the genuine hole is mostly small: 1,383 of the 1,919 trade under $5M/day.
  **142 genuinely-missing operating equities trade above $100M/day** — that is the real cost.
- **This tier recovers 104 of those 142**: META, ACN, MA, CHTR, CMCSA, NKE, REGN, F, EL, RL,
  ABNB, DASH, HOOD, MSTR, CRWV, ASTS and more. Across all 1,420 issuers it recovers 412 (~29%).
- The mechanism, verified per name against live companyfacts: **META publishes NEITHER instant
  tag** (only weighted-average counts), while **GOOGL publishes the us-gaap one** — that single
  difference is why one was admitted and the other vanished. Both drop the dei cover-page tag,
  consistent with multi-class filers reporting share counts per class (dimension-qualified facts
  do not surface in companyfacts/frames).
- The remaining 38 of 142 are a DIFFERENT problem and are NOT addressed here: foreign filers
  (AZN, NVO, SONY, SE, JD, BIDU, ITUB, NU, VALE …) report under `ifrs-full`, and the SEC frames
  endpoint **404s for the `ifrs-full` namespace** (tried CY2026Q1I and CY2025Q4I) — so that fix is
  per-name companyfacts calls plus ADS-ratio handling, i.e. FPI1/FPI4, still parked behind their
  rulings. BRK.A/BRK.B, V, ARES, BN/BAM need per-name investigation. Stated, not started.

**WHY IT IS ACCEPTABLE TO APPROXIMATE HERE — AND WHERE THE APPROXIMATION TRAVELS.** A weighted
average is a count over a period, not a count on a date. `universe.py`'s cap is already declared
coarse ("fine for a coarse band, not a valuation" — the dual-class caveat), and the band's job is
to decide membership. Two properties keep it honest and are pinned: it can never DISPLACE a filed
instant count, and every row it decides — admitted OR dropped out-of-band — carries the tag in its
stamped `source`.

**STATED PRECISELY, because the first draft of this record OVERCLAIMED** (caught at review): the
committed `market_cap` is not read only as a membership gate. `themes/residualize.build_factors`
uses it as the SIZE-FACTOR tercile input and `rank/ranker.py` renders it on the ranked queue —
NEITHER carries the `source` tag alongside. So "no reader can mistake it for a filed figure" was
wrong: the artifact carries the tag; those two derived surfaces do not. The real consequence,
recorded rather than papered over: a name whose period-average cap straddles a tercile boundary
can flip size cohorts and move residuals across the detection window. Accepted for now — the cap
was always coarse, and the dual-class approximation predates this tier — with the honest fix, if
the effect ever matters, being to propagate the tag to those two consumers.

**HOW VERIFIED.**
- 7 pins in `tests/test_shares_period_average.py`, all built on the REAL observed shapes
  (META/GOOGL/MSFT): recovery of a filer with no instant count; precedence (MSFT is in both the
  dei and the average frame — the filed count survives); the tier is opt-in AT THE WIRE (the
  average frame is never even requested on the default path, so existing consumers are untouched);
  the average is queried as a DURATION key, never an instant (an `I` suffix would return nothing —
  the tier would look implemented and recover no one); and the artifact-level provenance stamp.
- REAL RUN on the primary band at the committed snapshot's OWN vintage,
  `vinci build-universe --ref 2026-08-24`, from a cold DB over main's entity master:
  `{'considered': 7663, 'in_universe': 2000, 'no_shares': 1366, 'shares_period_average': 189,
  'out_of_band_period_average': 323, ...}` — **`no_shares` fell 1,919 → 1,366**, membership
  1,812 → 2,000, of which **189 admitted rows carry the period-average tag in their committed
  `source`** and **323 out-of-band drops are attributed to it**. The rebuilt snapshot IS
  committed (leaving it out would leave the committed population contradicting the code that
  builds it), and building at the primary vintage keeps every new identity `first_seen`
  on-or-before it: `identities_first_seen_after(2026-08-24)` returns **0**, and every in-universe
  name resolves in the committed entity master (0 missing).
- FOUR EXISTING TESTS REDDENED, which is the evidence the change binds the real path, not a
  parallel one: two builder stubs did not implement the provenance method (updated — one now
  returns a FILED tag, so the row it stamps must carry no approximation warning), and the
  retention guard correctly refused a new stat incremented outside `_drop` (its allowlist now
  names `shares_period_average` with the reason: it counts an ADMITTED name's quality, not a
  drop, so it has no retention row to emit — its evidence is the row's own stamped `source`).
- ONE DESIGN CORRECTION found by that reddening: the tags were class attributes, and
  `build_universe` read `EdgarClient.SHARES_TAG_WAVG` — which a test substituting its own client
  SHADOWS, silently changing what "approximate" means at the stamping site. They are module-level
  constants now, imported directly.

**REVIEW ROUND (2026-08-31, medium code-review — three findings applied, one refuted, one noted).**
1. **The drop side had no provenance.** The tier newly SIZES names that then fall out of band —
   324 of them on the real run — and their retention rows still named a filed EDGAR count as the
   deciding input, so an operator auditing drops could not attribute an exclusion to the
   approximation. The `out_of_band` `StampedInput` now carries the tag, and those decisions are
   counted separately (`out_of_band_period_average`). The retention guard's allowlist names both
   counters with the reason they are not drop STAGES.
2. **The provenance pins were `inspect.getsource` string matches** — they would have stayed green
   through a plausible refactor keying the tag lookup on the TICKER instead of the CIK (every name
   tagged `""`, never approximate, the stat always 0, every row stamped with a bare prefix), and
   reddened on a harmless reflow. Replaced with BEHAVIOURAL tests that run the real
   `build_universe` against a fake filer and assert the EXPORTED ROW: approximate row stamped and
   counted, filed row tagged without a warning and not counted, out-of-band drop counted.
   (Pin the artifact, not the helper.)
3. The "coarse cap band and nothing else" claim was **wrong** — see the corrected paragraph above.
   REFUTED: the `_merge` precedence logic (verified correct across tiers and periods; the reviewer
   fuzzed old-vs-new equivalence over 200k randomized cases with 0 mismatches, so the
   instant-only façade is exactly the previous behaviour) and `period.rstrip("I")` (no reachable
   frame key ends in a non-suffix `I`).
   NOTED, NOT FIXED: `shares_period_average` is written to `universe_stats.json` but the frontend
   ingestion dashboard renders a fixed gate list and does not display it — the counter is in the
   artifact, not yet on that surface.

**BOTH BANDS REBUILT TOGETHER (post-#527 rebase).** The theme band's committed snapshot had been
built before this tier, so it lagged the code that now builds it. Rebuilt at the same vintage from
the same cold DB: **theme 826 → 907 admitted** (81 sized by the period average, 463 out-of-band
decisions attributed to it), primary 2,000. **META is now in the scanned population**, alongside
MSFT/GOOGL/AMZN/NVDA/LLY/CRM/NOW/VEEV/SAP — the whole point of the two changes together, and the
first time the exposure scan can reach the centre of the operator's two declared theses rather
than their mid-cap periphery. `identities_first_seen_after(2026-08-24)` is 0 for both bands and
every in-universe name across both resolves in the committed entity master.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A cap sized from a period average can differ from a same-day filed count — most for a filer
  mid-buyback or post-issuance. Accepted for a COARSE band; the row says so, and any consumer
  needing a filed count reads the tag rather than the number.
- One extra frame call per period per build (~5 calls). Negligible beside the per-name SIC pass.
- **Universe membership GREW: +188 net on the primary band (1,812 → 2,000).** That is a coverage
  repair, not a redefinition — the precedent is #525 (SIC holes filled, membership moved). Ledger
  rows already logged are unaffected: the spread accumulates per decision, not per population.
  The screen/queue artifacts are NOT regenerated here; the next weekly run screens the larger
  population, which is the normal cadence.
- The THEME band's committed snapshot (PR #527, 816 names) was built before this tier and does
  not include META. Once both are on main a `--band theme` rebuild picks up the ~104 recovered
  names. Noted, not done here — this branch is deliberately independent of #527.
