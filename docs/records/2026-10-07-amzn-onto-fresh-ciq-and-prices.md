---
id: 2026-10-07-amzn-onto-fresh-ciq-and-prices
status: shipped
date: 2026-10-07
prs: [669]
supersedes:
superseded-by:
---

# AMZN onto fresh CIQ and fresh prices — and off the stale benchmark close

**WHAT.** AMZN re-assembled on `f8dab003` after the operator re-pulled four CIQ exports on 2026-10-07 —
Estimates Report, Comparable Analysis, Public Company Profile, Key Developments. The other seven files
were byte-identical (the Credit Health export is the 2026-10-05 one, already held); the old folder is
backed up outside the repo. Artifacts only.

**NO PRICE REFRESH WAS NEEDED.** #668 had already carried AMZN and IWM/MDY/SPY to the 2026-10-06 close
and backfilled SPY's 09-17..09-22 hole; at build time (03:59 US/Eastern, 2026-10-07) no later close
existed.

**WHAT MOVED** (against AMZN's #666 page):

    price              $254.98 (2026-09-22)   ->  $256.29 (2026-10-06)
    comps market cap   $2,653,001.7M (09-16)  ->  $2,764,424.3M (10-06)
    consensus floor    >=2026-10-01           ->  >=2026-10-06
    SPY 180d return    16.89%                 ->  19.89%
    AMZN vs SPY        +5.97%                 ->  +2.97%
    P/FY26E norm/GAAP  30.7x / 19.8x          ->  30.8x / 19.9x
    P/FY27E norm/GAAP  24.4x / 24.3x          ->  24.5x / 24.3x
    credit health      industry (21) 1/1/1/2 · comps (11) 2/3/2/4 — unchanged
    lean · draws       mixed 3/2              ->  strongly-bullish 4/1 — proposal withheld both times
    caveats / qa       7/6                    ->  8/5

**AMZN IS OFF THE STALE BENCHMARK.** #666's page was one of the eleven #668 found comparing against
SPY's 2026-09-16 close under a 2026-09-22 label. On the complete history the market's 180-day return
is 19.89%, and **AMZN's lead over it falls from +5.97% to +2.97%** — #666 overstated it by 3.0 points.
Nine pages still carry the stale close.

**THE CAP AND THE PRICE SHARE A DATE.** #666 paired a 2026-09-16 comps market cap with a 2026-09-22
price; both are now 2026-10-06. The forward multiples barely move — the price is up 0.5% and the
estimates are unchanged to the cent — and the normalized FY26E basis (30.8x on $8.31, the GAAP
consensus still carrying the non-operating gain #666 documented) is as before.

**THE LEAN FLIPPED BACK, AND THAT IS NOT EVIDENCE.** #666 drew 3 mixed / 2 strongly-bullish; this build
4 strongly-bullish / 1 mixed. The inputs moved (fresh estimates, a corrected benchmark that makes the
relative return LESS flattering), but one run cannot separate that from draw variance — and the gate
withholds the proposal in both. Two new caveats flag the synthesis leaning on the heterogeneous peer
median for its forward-premium bear point.

**THE PROMPT CACHE, on the fleet's largest prompt yet** (225,020 tokens): written once, read four
times, gaps under 60s, no miss — synthesis ~$2.36 against ~$6.13 uncached, 61.5% saved.

**HOW VERIFIED.** `dossier --ticker AMZN` exit 0, `1 done · 0 error(s)`, 13:29–13:38 IST. ruff clean ·
`mypy --strict vinci` clean · `pytest -m "not network"` exit 0 on the freshly-committed artifacts.

**BOUNDARY.** One page, AMZN, 2026-10-07, `claude-opus-4-8`. Five files
(`data/dossiers/AMZN/dossier.{json,md}`, `frontend/dossiers/AMZN.{json,md}`,
`frontend/dossiers/index.json`). Prices through the 2026-10-06 close.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The synthesis prose is fully rewritten**, as every full assembly does.
- **Row 32 updated:** AMZN leaves the stale-close list (3), the credit backfill (6, now 17 pages) and
  the stale-benchmark list (7, now nine pages).
- **Not CI-validated** — the `gate` workflow has failed on Actions billing since #652.
