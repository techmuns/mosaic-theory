# Dossier — FuboTV Inc. (FUBO)

_Finalist rank 1 · ref 2026-06-22 · assembled 2026-06-30 08:47 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 13.4x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 2nd %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** _UNKNOWN_ — TEV/LTM EBITDA Close has no value
- **EV/EBITDA percentile (5y):** _UNKNOWN_ — TEV/LTM EBITDA Close <4 quarters (0) — no pctile
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** _UNKNOWN_ — TEV/LTM EBITDA Close has <4 quarters — no range position

### Quality / durability
- **FCF sign:** negative
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** -131.2
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Margin trend:** gross margin: Oct-01-2022 0% → Sep-30-2023 0% → Sep-28-2024 0% → Sep-27-2025 0% → Mar-31-2026 (LTM) 4%; absolute revenue: Oct-01-2022 3,419 → Sep-30-2023 3,846 → Sep-28-2024 4,220 → Sep-27-2025 4,413 → Mar-31-2026 (LTM) 5,304  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA:** _UNKNOWN_ — no CIQ Net Debt/EBITDA; EDGAR no net-debt — debt/cash not in XBRL — pull CIQ
- **Net debt / OCF:** _UNKNOWN_ — CIQ OCF $-489M <= 0 — ratio meaningless
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net debt $170M (CIQ); net-debt/EBITDA N/A (no CIQ Net Debt/EBITDA; EDGAR no net-debt — debt/cash not in XBRL — pull CIQ) | FCF-negative → burning cash; runway = cash ÷ burn (cash not derived — a risk) | nearest maturity wall: 2027
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** _UNKNOWN_ — Income Statement missing EBITDA or Interest Expense row
- **Share-count trend:** diluting (trailing ~1.0y): 329,336,621 (2024-07-31) → 342,433,118 (2025-07-31), +4.0%
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2025-07-31`
- **Liquidity / covenant flags:** 2029 Convertible Notes (Bonds and Notes) 178 @ 7.500% Due 2029; Disney Note (Bonds and Notes) 145 @ 4.200% Due 2031; Operating Lease Liabilities (Capital Lease) 33 @ 6.800%; Other Notes (Bonds and Notes) 0 @ 2.250% Due 2027
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Oct-01-2022 3,419 → Sep-30-2023 3,846 → Sep-28-2024 4,220 → Sep-27-2025 4,413 → Mar-31-2026 (LTM) 5,304; ROIC: Sep-30-2023 -11.2% → Sep-28-2024 -10.9% → Sep-27-2025 -10.7% → Mar-31-2026 (LTM) -3.3%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Sep-27-2025] Streaming Business 4,413 (100%) of Total 4,413
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** CBS Corporation (Acquired) — fuboTV Inc. · Customer · src: Broadcasting; Denso Aircool Corporation — fuboTV Inc. · Customer · src: Automotive Parts and Equipment; International Family Entertainment, Inc. — fuboTV Inc. · Customer · src: Movies and Entertainment; NBCUniversal Media, LLC — fuboTV Inc. · Customer · src: Movies and Entertainment; ProBank Austin (Acquired) — fuboTV Inc. · Customer · src: Research and Consulting Services; TEGNA Inc. — fuboTV Inc. · Distributor · src: Broadcasting; Viacom Inc. (Acquired) — fuboTV Inc. · Customer · src: Movies and Entertainment; WideOpenWest, Inc. — fuboTV Inc. · Distributor · src: Cable and Satellite
  - ↳ `CIQ Customers&Suppliers FuboTV Inc NYSE FUBO Customers.rtf`
- **Geographic:** [12 months Sep-27-2025] United States 4,413 (100%) of Total 4,413
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — Roku $19.9B — operates a TV streaming platform in the United States (United States); Netflix $306.6B — provides entertainment services worldwide. The company (United States); Sirius XM Holdings Inc. $9.5B — operates as an audio entertainment company in North (United States); Taboola.com Ltd. $1.3B — operates an artificial intelligence-based algorithmic (United States); Match Group $8.2B — provides digital technologies in the United States and (United States); Reddit $31.9B — operates a digital community in the United States and (United States); People Incorporated $3.1B — operates as a media and internet company worldwide. (United States); Bilibili Inc. $6.6B — provides online entertainment services for the young (China); Paramount Skydance Corporation $10.9B — operates as a media and entertainment company (United States); Starz Entertainment Corp. $478M — provides subscription video programming services to (Canada) | the name: $256M
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $478M–$306.6B (642x); the name is $256M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 0.4 vs peers Low 0.7 / Median 1.9 / Mean 3.2 / High 11.8; TEV/EBITDA: name NM vs peers Low 7.5 / Median 10.6 / Mean 17.6 / High 44.9; P/E: name NM vs peers Low 11.9 / Median 23.7 / Mean 33.6 / High 101.3; NTM TEV/Rev: name 0.36 vs peers Low 0.62 / Median 2.07 / Mean 2.81 / High 8.42; NTM TEV/EBITDA: name 17.77 vs peers Low 5.4 / Median 8.19 / Mean 11.64 / High 24.65; NTM P/E: name NM vs peers Low 7.26 / Median 19.23 / Mean 21.13 / High 51.57  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name – vs peer-median 11%; rev growth name 22% vs peer-median 9%; EBITDA growth name – vs peer-median 18%; Debt/EBITDA name NM vs peer-median 3.2; LT EPS growth name – vs peer-median 17%; beta name 2.4 vs peer-median 1.4  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-03 earnings (2.02); 2026-03-26 no 8-K matched; 2026-05-06 earnings (2.02)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-03, 2026-03-26, 2026-05-06
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-03 → 2026-02-03 [`0001493152-26-004826`](https://www.sec.gov/Archives/edgar/data/1484769/000149315226004826/form8-k.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On February 3, 2026, FuboTV Inc. announced its financial results for the quarter ended December 31, 2025 . The full text of the shareholder letter and press release issued in connection with the announcement are attached as Exhibits 99.1 and 99.2, respectively, to this Current Report on Form 8-K. The information in this
  - gap 2026-05-06 → 2026-05-06 [`0001493152-26-021406`](https://www.sec.gov/Archives/edgar/data/1484769/000149315226021406/form8-k.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On May 6, 2026, FuboTV Inc. announced its financial results for the quarter ended March 31, 2026. The full text of the shareholder letter and press release issued in connection with the announcement are attached as Exhibits 99.1 and 99.2, respectively, to this Current Report on Form 8-K. The information in this
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001493152-26-004826', '0001493152-26-021406']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -72.6%
  - ↳ `EOD FUBO 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -89.0%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — FUBO not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/1↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $17.00 / median $17.00; Recommendation: Buy (1.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** _UNKNOWN_ — Surprise sheet has no fiscal-year header row

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — chronic cash burn and dilution against narrowing losses, a forward-multiple premium, and unverified management profitability guidance pulling opposite directions.

### Bull case (overshoot / mean-revert)
- On the LTM forward revenue multiple the name trades at NTM TEV/Rev 0.36 against a peer Low of 0.62, Median 2.07, and High 8.42 — a steep discount that the human must decompose against fundamentals rather than accept at face value.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- On the decomposition inputs the discount looks partly RESIDUAL rather than fully EARNED: the name's revenue growth is 22% versus a peer-median 9% with a beta of 2.4 versus peer-median 1.4 — superior top-line growth alongside higher risk, the human judges which dominates.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Absolute revenue scaled steadily from 3,419 (Oct-2022) to 5,304 (LTM Mar-2026) while ROIC improved from -11.2% to -3.3%, so the operating loss is narrowing even as the headline stays negative — read the % alongside the rising absolute base.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Management states the post-combination contractual wholesale fee scales from 95% in 2026 to 99% by 2028, framed as visibility into adjusted-EBITDA expansion toward the $300M 2028 target and positive free cash flow in 2027-2028.
  - ↳ `CIQ transcript(s): FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf`
- Sell-side consensus carries a Buy (1.00) recommendation and a mean/median target of $17.00 against the de-rated tape, a genuine counter to the terminal read.
  - ↳ `CIQ Estimates→Consensus`

### Bear case (terminal / value-trap)
- Free cash flow is -131.2 (LTM Mar-2026) with operating cash flow of -489M and the FCF sign negative — the business is burning cash, and on the cash leg this is the REAL signal, not an optical artifact.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- The single positive P/E of 13.4 sits at the 2.4th percentile of its ~5y range but is explicitly a MISREAD: it rests on a non-current positive EPS while latest annual EPS is -0.54, so the low percentile reflects a distorted basis, not cheapness.
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- On the forward EBITDA multiple the name is NOT cheap: NTM TEV/EBITDA is 17.77 versus a peer Median of 8.19 and Mean of 11.64 — a premium, undercutting any blanket 'cheap vs peers' read once the forward earnings leg is used.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- Part of the peer discount is EARNED, not residual: the name's EBITDA margin trails the peer-median by 11 points and Debt/EBITDA is NM against a peer-median 3.2, weaker profitability and unquantifiable leverage that justify some of the gap.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Revenue 100% concentrated in one Streaming segment and 100% in the United States, with no segment-EBITDA breakout — a single undiversified profit pool.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- The decline is idiosyncratic, not a market move: the name returned -72.6% over 180d while IWM returned +18.0%, a relative -89.0% — the market is repricing this name specifically.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Three discrete gap-downs cluster on earnings 8-Ks (2026-02-03 and 2026-05-06 both item 2.02 Results of Operations), so the de-rating is anchored to reported results, not a transient shock.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Share count is diluting +4.0% over ~1y (329.3M to 342.4M), eroding per-share value while the company funds a cash-burning operation.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2025-07-31`

### Twin reference cases
- **Roku** — recovered
  - distinguished by: US streaming platform that ran sustained operating losses while scaling revenue, with the market questioning a path to positive cash generation.
  - source: [LLM-suggested, unverified]
- **Chewy** — recovered
  - distinguished by: Cash-burning subscription-style growth name that re-rated once operating leverage converted top-line scale into positive EBITDA and free cash flow.
  - source: [LLM-suggested, unverified]
- **Blue Apron** — went terminal
  - distinguished by: Single-segment US consumer subscription model whose top-line growth never outran cash burn and chronic dilution.
  - source: [LLM-suggested, unverified]
- **MoviePass / Helios and Matheson** — went terminal
  - distinguished by: Subscription video venture that scaled users while burning cash and diluting shareholders into collapse with no profit pool.
  - source: [LLM-suggested, unverified]
- **fuboTV (pre-Hulu-Live-TV combination)** — recovered
  - distinguished by: Same name's earlier standalone phase whose viability hinged on a transformative content/distribution combination changing the earnings profile.
  - source: [LLM-suggested, unverified]

### Decisive question
**Does the post-combination contractual wholesale step-up and ad-server migration convert revenue scale into the positive free cash flow management guides for 2027-2028 before the cash burn and 2027 maturity force further dilution?**

### …evidence for
- Management guides to positive free cash flow in fiscal 2027 and 2028 and a contractual wholesale fee scaling from 95% to 99% by 2028 underpinning adjusted-EBITDA expansion.
  - ↳ `CIQ transcript(s): FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf`
- ROIC improved from -11.2% (Sep-2023) to -3.3% (LTM Mar-2026) on a rising absolute revenue base, consistent with narrowing losses.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### …evidence against
- LTM free cash flow is still -131.2 with operating cash flow -489M, so the business is currently burning cash, not generating it.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Net debt is $170M with the nearest maturity wall at 2027 and runway uncomputed because cash was not derived — a flagged risk.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`

### Key unknowns
- Cash balance and resulting runway are NOT derived in the facts (survival_capacity flags this as a risk), so days-to-zero against the -131.2 burn cannot be computed — a bearish opacity gap, though the Q2 transcript pointer cites $244M cash / >$200M year-end as management-stated and unverified here.
- TEV/LTM EBITDA and its 5y percentile and range position are all UNKNOWN (<4 quarters of post-combination history), so the trailing valuation leg cannot be benchmarked.
- Net-debt/EBITDA, net-debt/OCF, and interest coverage are all UNKNOWN — leverage and debt-service capacity are unquantifiable from the supplied facts (bearish opacity).
- No revised-guidance 99.1 exhibit was parsed for either earnings 8-K, so the official forward guide is absent from the source-bound facts; only the transcript pointer carries forward targets.
- Segment-EBITDA breakout is absent — the single Streaming segment's profitability is not disclosed.
- Adjusted EPS and adjusted forward EV/EBITDA are not in the supplied facts, so the management adjusted framework cannot be reconciled to GAAP here.
- Peer set is HETEROGENEOUS (caps span $478M to $306.6B, 642x) — every peer multiple is a confidence-gated input, not a clean benchmark, and the earned-vs-residual split of the discount is for the human to judge.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS -0.54 vs recent median -2.06; verify against normalized/forward EPS (CIQ)
- TRANSCRIPT-FIGURE '95' in bull_point: 'Management states the post-combination contractual wholesale fee…' — from the cited earnings call, not the structured facts; verify against the call
- PEER-COMP-BARE bear_point: 'On the forward EBITDA multiple the name is NOT cheap: NTM TEV/EBITDA…' — presents cheap/rich vs peers as a verdict without the earned-vs-residual decomposition or the peer-set composition; POSE justified-vs-residual, never the bare gap
- HETEROGENEOUS-BENCHMARK bear_point: 'On the forward EBITDA multiple the name is NOT cheap: NTM TEV/EBITDA…' — leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every peer stat
