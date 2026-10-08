---
id: 2026-10-08-amzn-reassembled-after-the-fixes
status: shipped
date: 2026-10-08
prs: [680]
supersedes:
superseded-by:
---

# AMZN re-assembled on the fixed pipeline — the +71% GAAP-EPS bull point is gone, the R3 recipe held

**WHAT.** AMZN was re-assembled on `9adcf9a3`, the first build carrying all four fixes the 2026-10-07
plan put before it:
- #670 — a rebuild keeps the committed recipe;
- #674 — `horizon_read` reads each metric's own block;
- #673/#676 — the forward-consensus and forward-multiple layers;
- #678 — the GAAP-EPS momentum caveat.

It is stacked on #679, a test-only fix: the full-suite run here found that #674's count-refusal test pinned AMZN's old prose.

Only artifacts changed:
- AMZN's page and its frontend mirror;
- `frontend/dossiers/index.json`;
- the price fixtures the runbook regenerates (below).

**WHY.** Operator instruction, 2026-10-08: "re-assemble AMZN". It was recommended to wait for the Q3
report (~10-29), which will move consensus and add a quarter; the operator chose now.

**PRICES FIRST.** AMZN and IWM/MDY/SPY were refreshed one trading day, to the 2026-10-07 close
(4 bars). The CIQ exports are unchanged since #669.

**WHAT MOVED** (against main's page, #669 plus the #675/#677 layers):

    price              $256.29 (2026-10-06)  ->  $259.92 (2026-10-07)
    comps market cap   $2,764.4B (2026-10-06) — unchanged; it is the comps export's, now a day older than the price
    P/FY26E norm/GAAP  30.8x / 19.9x         ->  31.3x / 20.2x   (EPS unchanged: $8.31 / $12.89)
    P/FY27E norm/GAAP  24.5x / 24.3x         ->  24.8x / 24.7x
    market-relative    unchanged — the window runs to the page's 2026-09-22 reference date, as before
    lean · draws       strongly-bullish 4/1  ->  mixed 4/1 — the proposal is withheld both times
    caveats / qa       8/5                   ->  9/6

**THE FIXES, ON THE PAGE:**
- **Recipe held.** `R3_forward_pe` survived the rebuild. One new caveat says the build's own read
  proposes R1 and that a recipe changes only by hand (#670).
- **The new layers are the builders'.** `horizon_read`, `forward_consensus` and
  `forward_multiple_history` each equal their builder's output on this export. The page now prints
  Net Income's own revision counts, not TEV's.
- **The GAAP-EPS claim is gone.** No claim names GAAP EPS any more. The valuation bear point now
  argues on normalized EPS ("P/FY26E normalized EPS is 31.3x … once below-the-line gains are
  stripped out"). So the #678 check had nothing to fire on, and none of the 9 caveats is that one.
  The only remaining GAAP mention is a key unknown about the leverage basis.

**THE LEAN FLIPPED, AND THAT IS NOT EVIDENCE.** #669 drew 4 strongly-bullish and 1 mixed; this
build drew 4 mixed and 1 strongly-bullish.
- **What changed in the inputs:** a one-day price move, the corrected revision counts, and the
  forward layers. But `forward_consensus` and `forward_multiple_history` sit outside the synthesis
  prompt, so they cannot have moved the lean.
- **What one run cannot do:** separate those input changes from draw variance.
- **The gate withholds the proposal in both builds.**

**THE PRICE FIXTURES CAUGHT UP WITH THE STORE.** Regenerating them (RUNBOOKS i.5) rewrote 21 files,
not just AMZN's:

| change | files |
|---|---|
| +10 bars: 2026-09-23..10-06, already in the store since #668, which never re-ran this step | 19 |
| +11 bars: also gain 2026-10-07 (AMZN, IWM) | 2 |
| `source` relabelled `polygon-aggs` → `polygon-grouped` on bars with identical OHLCV | 6 (NCNO, ORKA, PARR, TECX and WERN 29 bars each; VRRM all 452) |

Not one close or volume changed. The companyfacts fixture rebuilt byte-identically.

**HOW VERIFIED.**
- `vinci refresh` exit 0 (4 bars).
- `dossier --ticker AMZN` exit 0, `1 done · 0 error(s)`, `claude-opus-4-8`, 2026-10-08 11:29–11:38
  IST.
- Every layer equals its builder; the GAAP-EPS check was run on the new page and returned nothing.
- The fixture changes were classified bar by bar against HEAD.
- The first full-suite run went red on one test, #674's count-refusal e2e, which named AMZN's old
  `3↑/0↓` citation. The test is fixed in #679, and this branch is stacked on it.
- ruff clean · `mypy --strict vinci` clean · `pytest -m "not network"` on the freshly-committed
  artifacts, with #679 — counts in the PR.

**BOUNDARY.**
- **Scope:** one page, AMZN, 2026-10-08.
- **Prices:** through the 2026-10-07 close.
- **CIQ:** the 2026-10-06/07 exports already on disk; Financials last close 2026-09-16.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The synthesis prose is fully rewritten**, as every full assembly does.
- **The Q3 report (~10-29) will stale this page**; a re-assembly then is the plan.
- **AORT, CNXC and WERN** still carry stored GAAP-EPS claims the #678 check would caveat (§5.0 row
  10).
