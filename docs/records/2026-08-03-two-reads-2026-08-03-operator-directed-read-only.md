---
id: 
status: shipped
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**TWO READS — 2026-08-03 (operator-directed, read-only; NOTHING FIXED). Both were hypotheses about
"a number that doesn't say what it covers." ONE CONFIRMED AND IS BIGGER THAN SCOPED; ONE DOES NOT
EXIST.** Recorded together because the pair is the lesson: a first pass is a hypothesis whichever way
it points, and these went opposite ways.

**READ 1 — INSIDER DATA IS FORM 4 XML, PARSED IN-HOUSE, SO THE COMPOSITION IS RECOVERABLE — AND IT
WAS RECOVERED.** `_insider_activity` + `_form4_codes` (`mechanical.py:1426–1496`) read the raw
ownership XML off EDGAR. Not a vendor aggregate; no caveat-or-drop decision needed.
**THE CODE IS ALREADY RIGHT ON THE THING MOST LIKELY TO BE WRONG.** `F` (shares withheld for tax on
vesting) is NOT netted into the sell side — only `P` and `S` move `net`; `A` renders as "grants";
`M`/`F`/`C` are preserved under "other". The tax-withholding contamination that makes most insider
feeds useless is absent, and it was absent by design (the docstring says so).
**AND F IS SMALL ANYWAY, so the direction of the correction is settled: THE SELLING IS REAL.**
Measured over 24m to 2026-07-30: **F $1.24M against S $24.72M** — ~5% of the disposition dollars.
**10b5-1: THE ELEMENT IS `aff10b5One`, IT IS PRESENT ON EVERY SALE FILING, AND IT READS `'0'` ON ALL
THIRTEEN** — confirmed against the filings we hold rather than assumed, per the operator, and no
footnote mentions a plan either. **So all 17 `S` lines are DISCRETIONARY** — the informative
category, not the scheduled one. The correction runs in the direction that STRENGTHENS N6(b).
**THE AUDIT UNDERSTATED THE SELLING BY ~2×.** It reported ~$12.36M; measured by transaction date over
24m it is **$24.72M across 16 lines and 6 people**. The CEO line the audit named is confirmed present
(SCALZO 147,200 sh @ $36.86 = $5.43M, 2024-11-12). $12.36M does not reconcile to an obvious subset
and NO decomposition is invented here to make it.
**THE WINDOW TABLE IS THE FINDING** (ref 2026-07-30, transaction dates, non-derivative):
· 3m — 1 buy / 1 person / $0.12M · **no sells**
· **6m ← PRODUCTION — 2 buys / 2 people / $1.11M · NO SELLS** (reproduces the page's
  "Open-market buys 2 · sells 0 (net +90.0K sh)" exactly, so the render is CORRECT FOR ITS WINDOW)
· 12m — 4 buys / $1.41M · 1 sell / $0.11M
· 24m — 5 buys / $1.61M · **16 sells / 6 people / $24.72M**
**TWO CORRECTIONS TO THE SCOPING, both operator-relevant.** (i) **THE NETTING HAZARD IS LATENT, NOT
LIVE.** Within the 182-day window there is nothing to net against — zero sales — so the "$1.1M buying
vs $12.36M selling nets to −$11.26M" case cannot arise today. The live defect is purely the window's
SILENCE. (ii) **A 3m/12m PAIR WOULD STILL HAVE MISSED THIS NAME.** The selling episode is Nov 2024,
~21 months back; at 12m it is invisible and at 24m it dominates buys by 15×. So the remedy is not a
better fixed window — it is that **"no sells" and "no sells IN THIS WINDOW" are different claims**,
which is item 22's visible-absence rule applied to a NUMBER rather than a section. Design note
(operator, NOT built): never net; report by transaction code; counts AND dollars AND distinct people;
two windows, with the divergence as the signal.

**READ 2 — THE SPLIT-ADJUSTMENT DEFECT DOES NOT EXIST. `adjusted` IS SET ON BOTH CALL SITES AND THE
STORED SERIES IS INTERNALLY CONSISTENT ACROSS FUBO'S REVERSE SPLIT.** `{"adjusted": "true"}` on
`grouped_daily` (`eod/client.py:212`) and on `daily_bars` (`:229`); there is no unadjusted path.
**PROVEN ON THE DATA, not on the parameter:** FUBO holds 1,254 bars, 2021-07-30 → 2026-07-29, all
`polygon-grouped`. Its **2021 closes read ~$312** — ~11× the ~$28 it actually traded at then — i.e.
the whole history sits on the POST-split basis. **Exactly one single-day close ratio outside
[1/3, 3]** in five years: 2025-01-03 $17.28 → 2025-01-06 $60.72 (3.51×), the Disney/Hulu announcement,
a real event and not a re-basing. **`ret_12m` across the split reads −79.2%** (2025-07-29 $42.48 →
2026-07-29 $8.84), not inflated by 11×. **G2 is not mis-ranking FUBO on a split artifact.**
**BUT THE GUARANTEE IS UNSTATED, and that is the same class as read 1.** Nothing detects a split and
nothing re-fetches history because of one (`grep` for split across `eod/` and `store/`: no handler).
Correctness here rests on two incidental properties: `INSERT OR REPLACE INTO prices`
(`store/store.py:249`) lets a re-ingest overwrite a stale bar, and the HTTP cache EXPIRES
(`netcache.py:145` honours `ttl_seconds`). **AND THE CODE COMMENT CONTRADICTS THE CODE, IN THE
DIRECTION THAT SAVES IT:** `client.py:210` says *"immutable once the day has closed → cache
forever"* while passing `ttl_seconds=_ONE_DAY` (86,400s). **If the comment were true, a bar cached
before a split would be stranded on the old basis permanently.** The comment is wrong and the code is
right; nobody reading the comment would know why this works.
