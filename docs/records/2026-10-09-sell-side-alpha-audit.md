---
status: shipped
date: 2026-10-09
prs: [695]
supersedes:
superseded-by:
---

# The sell-side alpha audit runs end to end — 31 Morgan Stanley Overweight signals priced from Polygon, scored in USD; the workbook's "MSCI World Net" benchmark is EUR, not USD

**WHAT.** `python -m vinci.research_audit {fetch,run,qa}` turns the operator's audit workbook
(`Research_Alpha_Historical_Audit_Pilot_CIQ_Validated.xlsx`, sha256 `108e879f…`, never modified)
into: an updated COPY of the workbook (input cells of 'Forward Return Tests' filled with LINKS to
a new 'Polygon Daily Prices' sheet, so the sheet's own formulas compute each return), a raw
daily price CSV, a ticker coverage / unresolved report with CIQ export requests, an
article-company return ledger, author/team and publisher tables, and a provenance + validation
log. Outputs land under the git-ignored `data/research_audit/` (they carry CIQ-derived columns).

What a signal is: a company row with a STATED analyst rating. Only Overweight is scored as a
long; Equal-Weight and Underweight are reported in their own rows; an unrated mention is kept
with its role (thematic beneficiary / risk / contextual) and gets no return. Entry = close of
the first session after the public date; target = EDATE(entry, 6/9/12); exit = first session
on/after the target; nothing carried forward; no incomplete horizon computed.

**THREE FINDINGS THE BUILD HAD TO ACT ON.**
1. *The Polygon plan serves daily bars only from 2024-10-09* (a 2024-01 request answers
   `403 NOT_AUTHORIZED`). Earlier sessions come from the repo's netcache of grouped-daily
   responses (every weekday 2021-07-01 → 2026-08-05; the 2023–2026-02 files all fetched
   2026-08-06), un-adjusted with Polygon's split events. Cache and live agree on raw close for
   every overlapping session of all 49 priced symbols (456 sessions each; PSTG 380): 0 mismatches.
2. *The workbook's CIQ "MSCI World Net" series is not USD.* Converted to USD with Polygon's
   EUR/USD close it tracks URTH (iShares MSCI World, USD) within +0.18%/yr, 21-session RMS gap
   0.36pp; read as USD the gap is 2.18pp, and GBP/CHF/JPY/INR fit worse (1.2–2.3pp). Window
   2024-10-09 → 2026-10-02, n = 495 common sessions. So every excess return is against URTH
   total return, labelled PROXY; the CIQ series is kept only as a reconciliation column.
3. *A SIC-code sector map mis-benchmarks large caps* (BKR and DE land in "Technology"; hotels in
   "Other"; UNH in "Financials"). The sector proxy is instead the Vanguard sector ETF whose SEC
   N-PORT-P holdings contain the stock, as of the last period on/before first entry: 35 of 37
   rated US tickers assigned; ET (MLP) and SPOT (Luxembourg issuer) held by no sector fund and
   left without a sector benchmark.

**HOW VERIFIED.**
- *Pilot reproduction:* the 6 AXP/BKR CIQ pilot horizons recomputed from Polygon on the pilot's
  own sessions and benchmark series: largest stock-return gap 0.03pp (threshold 0.50pp), all six
  outcome labels agree. CIQ's "Dividend Adj" path matches the dividends-reinvested Polygon series
  (max rebased-level gap 0.0009 AXP, 0.0007 BKR over 944 sessions), not price-only (0.11 / 0.19).
- *Workbook:* LibreOffice recalculation — 6,149 formulas, 0 errors; on all 111 filled rows the
  sheet's own R/S/T formulas equal the ledger within 1e-9; the 6 pilot rows A:X unchanged.
- *Pipeline QA:* 11/11 (no carry-forward, exit ≥ target, entry > public date, return = adjClose
  ratio, excess = stock − benchmark, only Overweight is LONG, no non-US listing priced, every
  workbook test row in the ledger, input sha256 unchanged).
- *Tests:* 20 in `tests/test_research_audit.py`, built from real captured bars (NVDA's 2024-06-10
  10:1 split from the grouped cache, AXP's 2024-01-04 ex-dividend, TTD's 2025-02-13 −33%
  session, a real 2024-06→2025-02 session calendar). 11 production mutations: 10 killed on the
  first pass; the survivor (incomplete-horizon guard) exposed a fixture whose calendar stopped at
  `last_session`, so the guard was never the thing refusing — fixed, and all 11 are killed now.
- *A false positive the corpus found:* the first full run blocked TTD as an "unrecorded 0.670x
  split" — its real post-earnings −33.0% session. Ratios 1.5 / 2.5 were dropped from the
  unrecorded-split detector; pinned by the TTD test.

**RESULTS (Overweight only, excess vs URTH TR PROXY; 31 signals, all Morgan Stanley).**

| horizon | n | win rate | median | mean | EW cohort (3 cohorts) | sector-adj. median (n=29) | worst |
|---|---:|---:|---:|---:|---:|---:|---|
| 6M | 31 | 55% | +10.6% | +5.9% | +3.1% | −2.4% | IDXX −24.9% |
| 9M | 31 | 61% | +2.5% | +4.6% | −0.2% | +2.4% | HAL −36.0% |
| 12M | 31 | 45% | −3.3% | +1.1% | −2.9% | −2.2% | HAL −51.9% |

By cohort, 12M median: MS-01 (2024-01, 9 of 16 names priceable) +9.7%; MS-02 (2024-06, 17 of 20)
−0.4%; MS-03 (2025-01, 5 of 11) −28.5%. Equal-Weight (6) 12M median −34.6%; Underweight (DTM,
PLTR) +66.9% (PLTR +137%) — reported separately, never scored as shorts. BofA, Citi, J.P.
Morgan, Goldman Sachs, Nomura: **0 scored observations** — none of their sampled items carries a
rated, dated, priceable company (Nomura's five are month-only dated); no track record is inferred
from that absence.

**BOUNDARY.** Population: the workbook's 26 publications / 97 mention rows / 174 pre-built test
rows as of its 2026-10-08 build — a non-random public-access sample. Window: sessions 2023-01-03
→ 2026-10-08 (last completed session at the 2026-10-09 run). Signals: 58 rated rows = 58
(publication, company) rated signals (the two in-publication duplicates, ServiceNow and Freshworks
in MS-03, are UNRATED rows; the rated row is the one counted); 47 Overweight, of which 31
US-listed and priced, 16 non-US primaries UNAVAILABLE_POLYGON. Unit: excess = stock TR − URTH TR, in USD,
per (signal, horizon); horizons overlap (6M ⊂ 9M ⊂ 12M) and names inside a cohort share one
entry close. Measured at `7408aaaf` (this branch merged with main `ee692651`); the ledger
is byte-identical to the pre-merge run at `dace883f`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *Not a fund input.* This is a historical event study of THIRD-PARTY calls. CLAUDE.md's "validate
  forward, never tune on forward returns" governs the fund's own discriminator; nothing on the
  screen / ranker / ledger / scoring path imports this package, and no parameter may be set from
  it. Falsifier: any decision-path import of `vinci.research_audit`.
- *The world benchmark is a PROXY.* URTH's TR vs the CIQ series converted at EUR/USD differs by
  +0.18%/yr; that comparison is itself DERIVED (Polygon's FX close is not MSCI's 4pm London fix).
  A USD re-export of MSCI World Net from CIQ retires the proxy.
- *Sixteen Overweight signals are unpriced* (UK, Japan, Korea, Germany, Netherlands, Australia,
  Canada, Taiwan, China primaries). Polygon carries US exchanges + US OTC only; ADR/OTC lines are
  listed in the export request, never substituted. The scored set is therefore US-tilted.
- *Unrecorded 3:2 or 5:2 splits are no longer caught* (the 1.5 / 2.5 ratios were dropped); a
  RECORDED one is still applied (PACCAR 2023-02-08).
- *PSTG's bars stop 2026-04-16* (121 later sessions absent — delisting or ticker change, not
  investigated); every PSTG horizon exits by 2026-01-07, so no row is affected.
