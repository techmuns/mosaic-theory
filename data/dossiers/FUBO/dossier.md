# Dossier — FuboTV Inc. (FUBO)

_Finalist rank 1 · ref 2026-06-22 · assembled 2026-06-29 16:14 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS -0.54 vs recent median -2.06; verify against normalized/forward EPS (CIQ)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- TRANSCRIPT-FIGURE '95' in bull_point: 'FUBO is FCF-negative at -$131.2M LTM, but management states pro forma…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '95' in decisive.for: 'Management states trailing-12-month pro forma adjusted EBITDA crossed…' — from the cited earnings call, not the structured facts; verify against the call
- DIRECTIONAL language 'buy' — human review (dossier frames, not concludes)
- DIRECTIONAL language 'recommendation' — human review (dossier frames, not concludes)
- HETEROGENEOUS-BENCHMARK bear_point: 'The 22% growth / RESIDUAL-overshoot read is undercut on the SAME…' — leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every peer stat
- HETEROGENEOUS-BENCHMARK decisive.against: 'On forward EBITDA the name is RICH not cheap — NTM TEV/EBITDA 17.77…' — leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every peer stat

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
- **Relative vs market:** -88.1%
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

**Evidence balance:** mixed — deep cash burn and an opaque 2027 runway offset a management-asserted adjusted-EBITDA ramp and contractual carriage step-up.

### Bull case (overshoot / mean-revert)
- FUBO is FCF-negative at -$131.2M LTM, but management states pro forma trailing-12-month adjusted EBITDA crossed $100M in Q2 with a contractual carriage wholesale-fee step-up (95% in 2026 scaling to 99% by 2028) providing visibility toward a stated $300M adjusted-EBITDA target by 2028 and positive FCF guided in 2027-2028.
  - ↳ `CIQ transcript(s): FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf`
- On TEV/Rev the name trades 0.4 (LTM) / 0.36 (NTM) versus a peer Low of 0.7 / 0.62 and Median 1.9 / 2.07 — but the peer set spans $478M-$306.6B (642x) and is flagged HETEROGENEOUS, so the discount must be judged EARNED vs RESIDUAL, not read as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- On the fundamental_deltas the name's revenue growth is 22% vs a peer-median 9% — a faster-growth input that POSES whether the steep TEV/Rev discount is RESIDUAL (overshoot) rather than fully EARNED, though leverage shows Debt/EBITDA NM vs peer-median 3.2 and beta 2.4 vs 1.4 cut the other way.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Gross margin moved 0%→0%→0%→0%→4% (LTM) while absolute revenue rose 3,419→5,304, the reconciler noting margin % can fall while absolute EBITDA RISES — the trajectory is improving, not deteriorating, on the reclassified basis.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- ROIC improved across the multi-year columns from -11.2% to -3.3% (LTM), a narrowing-loss trajectory consistent with the post-Hulu-Live combination scale story.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Consensus carries a Buy recommendation (CIQ score 1.00) with a mean/median target price of $17.00, materially above the implied de-rated level.
  - ↳ `CIQ Estimates→Consensus`

### Bear case (terminal / value-trap)
- The headline P/E of 13.4 is NOT the real signal — it is an optical MISREAD resting on a non-current positive EPS, while the latest annual EPS is negative (-0.54), so the trailing multiple is distorted and not meaningful.
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- The 22% growth / RESIDUAL-overshoot read is undercut on the SAME forward metric: NTM TEV/EBITDA is 17.77 vs a peer Median of 8.19 and Mean 11.64 — on forward EBITDA the name is RICH, not cheap, which weighs toward the discount being EARNED.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- FUBO is structurally cash-consumptive: LTM levered FCF is -$131.2M and operating cash flow is negative ($-489M), so the net-debt/OCF ratio is meaningless and the company is burning cash.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Survival capacity is incompletely evidenced: net debt is $170M, net-debt/EBITDA is N/A, and runway = cash ÷ burn is explicitly NOT derived (flagged a risk), against a nearest maturity wall of 2027.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Shareholders are being diluted: diluted shares rose from 329.3M (2024-07-31) to 342.4M (2025-07-31), +4.0% in roughly one year, with a reverse stock split announced.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2025-07-31`
- Three discrete gap-downs (2026-02-03 earnings, 2026-03-26, 2026-05-06 earnings) drove a 180-day return of -72.6% versus the market's +18.0%, an idiosyncratic underperformance of -88.1% relative to IWM.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Revenue is 100% concentrated in a single Streaming segment and 100% in the United States, with a key content provider (NBCUniversal) having ceased renewal engagement on the Fubo side per management.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- Forward estimate breadth is negative-to-flat: Revenue FY2026 0 up / 1 down and EPS FY2026 0 up / 0 down in the last month, no positive revisions.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`

### Twin reference cases
- **Roku** — recovered
  - distinguished by: US streaming-platform name de-rated hard on growth-to-profitability fears, then stabilized as ad monetization and operating discipline improved.
  - source: [LLM-suggested, unverified]
- **Chewy** — recovered
  - distinguished by: Cash-consumptive high-growth subscription model that crossed into positive adjusted EBITDA and FCF as scale matured, validating a growth-then-profit narrative.
  - source: [LLM-suggested, unverified]
- **Chegg** — went terminal
  - distinguished by: Subscription consumer-media name whose core demand eroded as a dominant content/distribution partner dynamic shifted, leaving a structurally impaired model.
  - source: [LLM-suggested, unverified]
- **WeWork** — went terminal
  - distinguished by: Persistent cash burn against a near-term maturity wall with undisclosed runway eventually overwhelmed a scale-and-synergy growth story.
  - source: [LLM-suggested, unverified]
- **Sirius XM Holdings** — recovered
  - distinguished by: Scaled US subscription-media platform that leaned on a durable distribution moat and content packaging to defend subscribers through churn pressure.
  - source: [LLM-suggested, unverified]

### Decisive question
**Does the Hulu + Live TV combination's contractual carriage step-up and synergy path convert FUBO's cash burn into the guided positive FCF and $300M adjusted EBITDA before the 2027 maturity wall and dilution erode equity value?**

### …evidence for
- Management states trailing-12-month pro forma adjusted EBITDA crossed $100M in Q2 with a contractual wholesale-fee step-up from 95% (2026) to 99% (2028) and positive FCF guided for 2027-2028.
  - ↳ `CIQ transcript(s): FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf`
- ROIC has narrowed from -11.2% to -3.3% and absolute revenue rose to 5,304 (LTM), consistent with improving combined-company economics.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### …evidence against
- The company is still burning cash with LTM levered FCF of -$131.2M against a 2027 maturity wall, and runway = cash ÷ burn is explicitly not derived.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- On forward EBITDA the name is RICH not cheap — NTM TEV/EBITDA 17.77 vs peer Median 8.19 — so the guided EBITDA ramp may already be priced, leaving little RESIDUAL cushion.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Key unknowns
- Cash runway is not derivable: cash ÷ burn is explicitly not computed and flagged a risk, against a 2027 nearest maturity wall — an OPACITY-AS-SIGNAL bearish gap, not a neutral one.
- TEV/LTM EBITDA, its 5y percentile, and range position are all UNKNOWN (<4 quarters of post-combination data), so no through-cycle valuation anchor exists — the headline P/E and its 2.4th-percentile reading are distorted, neither bull nor bear.
- Adjusted EPS, forward adjusted EV/EBITDA, interest coverage, and net-debt/EBITDA are all UNKNOWN (not in the 99.1 revised guidance / missing income-statement rows) — leverage serviceability is opaque, a bearish disclosure gap.
- No revised-guidance 99.1 exhibit was parsed for either gap-down 8-K, so the precise quantitative outlook that drove the discrete gap-downs is unverified from source.
- Segment EBITDA is UNKNOWN (no EBITDA section on the Segments sheet), so profitability inside the 100%-Streaming/100%-US concentration cannot be decomposed.
- No graph cohort is available (FUBO absent from coverage), so idiosyncratic-vs-shared is read only off rel_vs_market with no peer cross-section.
- The durability of the NBCUniversal/Comcast non-renewal on the Fubo side and any future subscriber impact beyond the 'minimal incremental churn' management asserts is unresolved.
- Whether the guided ad-monetization uplift from the Disney ad-server migration is real upside or just stabilization — explicitly raised by an analyst — remains qualitative and unquantified in source.
