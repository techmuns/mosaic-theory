---
id:
status: shipped
date: 2026-10-09
prs: [692]
supersedes:
superseded-by:
---

# AMZN re-assembled onto the bridge build — the stamp catches up, the +71% GAAP-EPS bull point returns under its caveat, and the lean flips back

**WHAT.** AMZN was re-assembled on main @1cdab997. That build carries every change since #680's
build:
- the forward layers' basis (#681/#683);
- the forecast-error cross-check (#682);
- the P/E's EPS basis (#686/#687);
- the bridge (#689/#690);
- the R4 template (#691).

Prices were refreshed first: AMZN and IWM/MDY/SPY by one trading day, to the 2026-10-08 close
(4 bars). The CIQ exports are unchanged since #680. The Drive folder and `data/manual/ciq/AMZN`
hold byte-identical files (11 of 11), with Estimates and comps dated 2026-10-07 and Financials
2026-09-17.

Only artifacts changed:
- AMZN's page and its frontend mirror;
- `frontend/dossiers/index.json`;
- the two price fixtures the runbook regenerates;
- STATE row 10, corrected (below).

**WHY.** Operator instruction, 2026-10-09: "re-assemble AMZN". It was recommended to wait for the
Q3 report (~10-29) and, before the next rebuild, to decide whether the synthesis gets a digest of
the forward layers and the bridge (§5.0 row 30). The operator chose now.

**WHAT MOVED** (against main's page, #680 plus the #683–#690 layers):

    price                 $259.92 (2026-10-07)  ->  $254.06 (2026-10-08)
    extraction stamp      2026-10-07.1          ->  2026-10-08.4
    draws                 mixed 4 / strongly-bullish 1  ->  strongly-bullish 3 / mixed 2 — proposal withheld both times
    caveats / qa          9 / 6                 ->  9 / 5
    recipe                R3_forward_pe         ->  R3_forward_pe (kept by hand tag; this build's own read proposes R1)

**Unchanged, equal to main:**
- `forward_consensus`, `forward_multiple_history`, `historical_forecast_error` and `ev_bridge`;
- `anchor` (only `computed_at`);
- `reference_date` (2026-09-22).

**Redrawn by the LLM-fenced phases:**
- the covenant digest: 16 lines reworded, the same agreement;
- the operating-driver rows: 273 → 270. 23 dropped and 20 added, all `leading_indicator` or
  `competitive_position`, and largely relabels: AWS +28%, the $15bn AI run-rate and Bedrock's
  170% reappear under new metric names.

**THE +71% GAAP-EPS BULL POINT IS BACK, AND THIS TIME IT IS CAVEATED.** #680's build drew no GAAP
EPS claim. This build's bull point reads "FY26 GAAP EPS path moved from 7.56 (12m ago) to 12.9
(latest), +71%". #678's check fired on it: over the same 12 months normalized EPS moved +10%
(7.54 → 8.31), and the gap is items CIQ's normalized figure excludes.
- So the guard did its job on the first build that needed it.
- STATE row 10 said "AMZN … no longer cites GAAP EPS". That was true of #680's page and is false of
  this one, and it is corrected here.

**THE LEAN FLIPPED AGAIN, AND THAT IS NOT EVIDENCE.** Three builds on the same CIQ exports drew:
- 4 strongly-bullish / 1 mixed (#669);
- 4 mixed / 1 strongly-bullish (#680);
- 3 strongly-bullish / 2 mixed (this one).

The inputs moved by two closes of price, and the synthesis reads none of the forward layers or the
bridge (`synthesis.py` has no reference to any of them). One run cannot separate input change from
draw variance. The gate withholds the proposal each time.
- A new caveat flags possible false balance: a strong lean written over a 7-bull / 5-bear body.
- Two bear-point caveats left with the point they flagged: a bare peer comparison and a
  heterogeneous peer benchmark.

**THE PRICE FIXTURES** gained one bar each, AMZN and IWM (2026-10-08). Nothing was removed. The
companyfacts fixture rebuilt byte-identically.

**HOW VERIFIED.**
- `vinci refresh AMZN IWM MDY SPY --aggs` for 2026-10-08: exit 0, 4 bars.
- `dossier --ticker AMZN`: exit 0, `1 done · 0 error(s)`, 2026-10-09 13:20–13:29 IST.
- Each forward layer and the bridge were compared with main's page and found equal. Every moved
  key is itemized above.
- The GAAP-EPS caveat was read on the new page: it names the claim, both moves and the window.
- The fixture diffs were read line by line.
- ruff clean · `mypy --strict vinci` clean · `pytest -m "not network"` on the freshly-committed
  artifacts — counts in the PR.

**BOUNDARY.**
- **Scope:** one page, AMZN, 2026-10-09.
- **Prices:** through the 2026-10-08 close.
- **CIQ:** the exports on disk, unchanged since #680.
- **Draw counts:** five draws per build, three builds.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The synthesis prose is fully rewritten,** as every full assembly does, and it is still blind to
  EV/NTM EBIT, the multiple history, the forecast error and the bridge. That is the open decision
  in §5.0 row 30, the operator's.
- **Amazon's operating-income guidance is still unread** from its release (row 30). Only CIQ's
  FQ3 2026 EBIT range ($22.5–26.5bn) reaches the page.
- **The Q3 report (~10-29) will stale this page.**
