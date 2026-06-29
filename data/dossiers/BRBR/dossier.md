# Dossier — BELLRING BRANDS, INC. (BRBR)

_Finalist rank 2 · ref 2026-06-22 · assembled 2026-06-29 17:31 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (3.8x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.8x as the covenant-basis leverage.
- TRANSCRIPT-FIGURE '14' in bear_point: 'Management's own posture deteriorated sharply quarter-over-quarter —…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '27' in bear_point: 'Management disclosed the first decline in RTD-shake buy-rate per…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '15' in decisive.for: 'Volumes are growing strongly (Premier shake volumes +12% in Q2,…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '27' in decisive.against: 'Buy-rate per household declined for the first time in 5 years and 27%…' — from the cited earnings call, not the structured facts; verify against the call
- DIRECTIONAL language 'sell' — human review (dossier frames, not concludes)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (6 bull vs 8 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 6.9x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 3rd %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 7.5x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 7.5x at 0%ile of 19 closes → near-floor; P/LTM EPS 7.9x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 182.7
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Margin trend:** EBITDA margin: Sep-30-2021 18% → Sep-30-2022 (R) 17% → Sep-30-2023 (R) 19% → Sep-30-2024 21% → Sep-30-2025 16% → Mar-31-2026 (LTM) 13%; gross margin: Sep-30-2021 31% → Sep-30-2022 (R) 31% → Sep-30-2023 (R) 32% → Sep-30-2024 35% → Sep-30-2025 33% → Mar-31-2026 (LTM) 30%; absolute EBITDA: Sep-30-2021 227 → Sep-30-2022 (R) 234 → Sep-30-2023 (R) 316 → Sep-30-2024 424 → Sep-30-2025 376 → Mar-31-2026 (LTM) 312; absolute revenue: Sep-30-2021 1,247 → Sep-30-2022 (R) 1,372 → Sep-30-2023 (R) 1,667 → Sep-30-2024 1,996 → Sep-30-2025 2,317 → Mar-31-2026 (LTM) 2,332  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA:** 3.8x
  - ↳ `CIQ Net Debt $1,190M [FQ2/CQ1 Mar-31-2026] ÷ CIQ EBITDA $312M [LTM 12 months Mar-31-2026]`
- **Net debt / OCF:** 6.1x
  - ↳ `CIQ Net Debt $1,190M [FQ2/CQ1 Mar-31-2026] ÷ CIQ OCF $195M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 3.8x (CIQ) | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2030
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 4.0x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Share-count trend:** buying back (trailing ~1.7y): 129,242,457 (2024-07-31) → 116,277,850 (2026-04-28), -10.0%
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-28`
- **Liquidity / covenant flags:** 7.00% Senior Notes Maturing in March 2030 (Bonds and Notes) 840 @ 7.000% Due 2030; Operating Lease Liabilities (Capital Lease) 30 @ 7.000%; Revolving Credit Facility (Revolving Credit) 250 @ 5.820% Due 2030
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Sep-30-2021 1,247 → Sep-30-2022 (R) 1,372 → Sep-30-2023 (R) 1,667 → Sep-30-2024 1,996 → Sep-30-2025 2,317 → Mar-31-2026 (LTM) 2,332; EBITDA: Sep-30-2021 227 → Sep-30-2022 (R) 234 → Sep-30-2023 (R) 316 → Sep-30-2024 424 → Sep-30-2025 376 → Mar-31-2026 (LTM) 312; ROIC: Sep-30-2021 23.1% → Sep-30-2022 23.9% → Sep-30-2023 33.4% → Sep-30-2024 43.1% → Sep-30-2025 34.5% → Mar-31-2026 (LTM) 25.6%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Sep-30-2025] Protein-Based Consumer Goods 2,317 (100%) of Total 2,317
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Amazon.com, Inc. (NasdaqGS:AMZN) — Distributor · Broadline Retail · src: BellRing Brands, Inc. (NYSE:BRBR) 2025 Form 10-K; Costco Wholesale Corporation (NasdaqGS:COST) — Distributor · Consumer Staples Merchandise Retail · src: BellRing Brands, Inc. (NYSE:BRBR) 2025 Form 10-K; Post Holdings, Inc. (NYSE:POST) — Licensee · Packaged Foods and Meats · src: BellRing Brands, Inc. (NYSE:BRBR) 2025 Form 10-K; Sam's West, Inc. — Distributor · Broadline Retail · src: BellRing Brands, Inc. (NYSE:BRBR) 2025 Form 10-K; Walmart Inc. (NasdaqGS:WMT) — Distributor · Consumer Staples Merchandise Retail · src: BellRing Brands, Inc. (NYSE:BRBR) 2025 Form 10-K
  - ↳ `CIQ Customers&Suppliers BellRing Brands Inc NYSE BRBR Customers.rtf`
- **Geographic:** [12 months Sep-30-2025] Canada 98 (4%); United States 2,041 (88%); Other Foreign 178 (8%) of Total 2,317
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — The Simply Good Foods Company $1.1B — engages in the development, marketing, and sale of (United States); The Campbell's Company $6.3B — manufactures and markets food and beverage products in (United States); The J. M. Smucker Company $11.8B — manufactures and markets branded food and beverage (United States); The Hershey Company $36.4B — engages in the manufacture and sale of confectionery (United States); Nu Skin Enterprises $250M — engages in the development and distribution of various (United States); Herbalife Ltd. $1.3B — provides health and wellness products in North (United States); USANA Health Sciences $354M — develops, manufactures, and sells science-based (United States); Nature's Sunshine Products $366M — manufactures and sells nutritional and personal care (United States); Kenvue Inc. $35.3B — operates as a consumer health company in the United (United States); FitLife Brands $111M — provides nutritional supplements and wellness products (United States) | the name: $1.3B
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $111M–$36.4B (327x); the name is $1.3B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 1.1 vs peers Low 0.2 / Median 1.2 / Mean 1.4 / High 3.4; TEV/EBITDA: name 7.9 vs peers Low 2.2 / Median 6.2 / Mean 7.8 / High 17.7; P/E: name 8.8 vs peers Low 4.8 / Median 19.3 / Mean 19.3 / High 39.8; NTM TEV/Rev: name 1.05 vs peers Low 0.24 / Median 1.23 / Mean 1.37 / High 3.34; NTM TEV/EBITDA: name 7.78 vs peers Low 2.52 / Median 8.7 / Mean 7.82 / High 13.03; NTM P/E: name 8.78 vs peers Low 4.43 / Median 10.97 / Mean 11.23 / High 20.01  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 13% vs peer-median 16%; rev growth name 6% vs peer-median 4%; EBITDA growth name -31% vs peer-median -6%; Debt/EBITDA name 3.9 vs peer-median 2.5; LT EPS growth name -7% vs peer-median 7%; beta name 0.6 vs peer-median 0.4  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-03 non-narrative items ['5.07']; 2026-05-05 earnings (2.02)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-03, 2026-05-05
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-03 → 2026-02-02 [`0001628280-26-004642`](https://www.sec.gov/Archives/edgar/data/1772016/000162828026004642/brbr-20260128.htm)
    - items: 5.07 Item 5.07
    - 5.07 Item 5.07: Submission of Matters to a Vote of Security Holders. BellRing Brands, Inc. (the “Company”) held its annual meeting of stockholders (the “Annual Meeting”) entirely virtually, conducted via a live audio-only webcast on Wednesday, January 28, 2026. At the Annual Meeting, of the 118,425,407 shares outstanding and entitled to vote, 100,350,223 shares were represented, constituting a 84.74% quorum. The 
  - gap 2026-05-05 → 2026-05-05 [`0001628280-26-030115`](https://www.sec.gov/Archives/edgar/data/1772016/000162828026030115/brbr-20260505.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operation and Financial Condition. On May 5, 2026, BellRing Brands, Inc. (the "Company") issued a press release announcing results for its second fiscal quarter ended March 31, 2026. A copy of the press release is attached hereto as Exhibit 99.1 and incorporated herein by reference. In addition, on May 5, 2026, the Company published to the "Investor Relations" section of its website, ww
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001628280-26-030115']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -66.2%
  - ↳ `EOD BRBR 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -78.6%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — BRBR not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $13.69 / median $13.00; LT growth: mean -7.2% / median -10.2%; Recommendation: Hold (3.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 +0%, FY2022 -20%, FY2023 -5%, FY2024 -1%, FY2025 -8%; Revenue surprise: FY2021 -2%, FY2022 -2%, FY2023 +1%, FY2024 +1%, FY2025 +1% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish — absolute EBITDA fell with the margin amid worsening guidance, earned peer discount, and a 5-year-first buy-rate decline.

### Bull case (overshoot / mean-revert)
- The de-rating is sharply idiosyncratic, not market-driven: BRBR fell ~66% over 180d while the small-cap IWM rose ~18%, leaving room for a mean-revert read IF the bottom-line shock proves cyclical rather than structural.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Absolute revenue still rose to an LTM record (2,332) even as the EBITDA margin collapsed, evidencing demand is intact and the problem is profitability not top-line erosion.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The business is self-funding and not in a runway crisis: FCF-positive at 182.7 with no maturity wall before 2030, so it can absorb a margin trough without forced action.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Management frames the margin shock as competitive-promotional and input-cost-driven (whey/protein inflation, freight, an isolated $11M inventory charge) rather than a category-demand failure, with RTD shakes still cited up 8% — a temporary-overshoot narrative for the human to test.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- On TEV/EBITDA the name screens at 7.9 LTM / 7.78 NTM versus a heterogeneous peer set whose median is 6.2 LTM but 8.7 NTM — POSE for the human whether any forward discount is RESIDUAL (overshoot) or EARNED, recognising the peer set spans $111M–$36.4B and is NOT a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- The company is buying back stock (-10.0% share count over ~1.7y), a capital-return posture inconsistent with a management view of terminal distress — a genuine supporting signal.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-28`

### Bear case (terminal / value-trap)
- The margin collapse is the REAL signal, not an optical %: EBITDA margin fell from 21% (FY24) to 13% LTM AND absolute EBITDA fell with it from 424 to 312 — the reconciler does NOT rescue this, the dollar EBITDA dropped alongside the percentage.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Management's own posture deteriorated sharply quarter-over-quarter — Q1 was a 'solid foundation' with 4-6% sales guidance, by Q2 results 'came in below our expectations,' guidance was cut to flat-to-up-2%, EBITDA margin outlook slashed to 14%, with protein-input inflation set to bite harder in Q3/Q4 — a worsening, not stabilising, trajectory.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- The fundamental discount looks EARNED, not residual: name EBITDA margin 13% vs peer-median 16%, EBITDA growth -31% vs -6%, LT EPS growth -7% vs +7%, and Debt/EBITDA 3.9 vs 2.5 — worse on margin, growth and leverage simultaneously, the signature of a value trap.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Leverage is elevated against a shrinking EBITDA base — net-debt/EBITDA 3.8x and net-debt/OCF 6.1x — so the denominator decay directly worsens the balance-sheet read even though maturities are distant.
  - ↳ `CIQ Net Debt $1,190M [FQ2/CQ1 Mar-31-2026] ÷ CIQ EBITDA $312M [LTM 12 months Mar-31-2026]`
- Management disclosed the first decline in RTD-shake buy-rate per household in 5 years and 27% of category volume now sold on promotion (up 8pts YoY) — evidence the price-sensitive-consumer and promotional pressure may be structural to the category, not a passing event.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- A CEO retirement was announced mid-deterioration, with a national external search and transition by FY-end — leadership uncertainty layered onto a guide-down quarter.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- Consensus posture is unsupportive: Hold (3.00), mean target $13.69, and LT growth mean -7.2% / median -10.2% — the Street is modelling shrinkage, not recovery.
  - ↳ `CIQ Estimates→Consensus`
- The business is single-segment (Protein-Based Consumer Goods 100%) and US-concentrated (88%), with no offsetting diversification to cushion a category-specific competitive shock.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`

### Twin reference cases
- **The Simply Good Foods Company** — recovered
  - distinguished by: Single-category protein/nutrition CPG that weathered competitive and consumer-shift pressure while remaining a focused brand operator — the closest-in-model analogue in the peer roster.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Herbalife Ltd.** — went terminal
  - distinguished by: Levered single-theme wellness name whose multiple compressed as growth stalled and debt loomed against a shrinking base — the leverage-meets-decline pattern.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Beyond Meat** — went terminal
  - distinguished by: Hot protein-trend brand that saw insurgent competition and value-seeking consumers compress margins after a high-growth run — the once-loved category darling losing pricing power.
  - source: [LLM-suggested, unverified]
- **Celsius Holdings** — recovered
  - distinguished by: Functional-beverage growth brand that absorbed a sharp consumption/sell-in scare and re-rated once volume held and the category proved durable.
  - source: [LLM-suggested, unverified]
- **Medifast** — went terminal
  - distinguished by: Single-product weight/nutrition brand whose demand driver eroded faster than management expected, with the de-rate proving structural rather than cyclical.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the margin collapse a temporary promotional/input-cost trough that normalises as insurgent competition moderates, or a structural reset of Premier's category pricing power that permanently lowers the earnings base?**

### …evidence for
- Management states competitive intensity 'would gradually moderate over time' and that current results are 'below the long-term potential of the business,' framing the trough as recoverable.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- Volumes are growing strongly (Premier shake volumes +12% in Q2, consumption outside club +15%) — the brand is gaining units, with the damage concentrated in price/mix not demand.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`

### …evidence against
- Buy-rate per household declined for the first time in 5 years and 27% of category volume is now promoted (up 8pts YoY), pointing to a structurally more value-driven consumer rather than a one-off promotional cycle.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- Protein-driven commodity inflation is running above plan and set to hit harder in Q3 and Q4, meaning the input-cost leg of the margin pressure is escalating, not abating, near-term.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`

### Key unknowns
- Revised forward guidance exhibit (99.1) was NOT parsed for the May 8-K — the actual revised-outlook figures are MISSING; an expected disclosure absent at the guide-down event is a bearish opacity gap, not neutral.
- Forward (NTM) adjusted EV/EBITDA and adjusted EPS are UNKNOWN ('adjusted figure not in the 99.1 revised guidance') — without a forward basis, the EV/EBITDA at 0%ile cannot be adjudicated cheap-overshoot vs cheap-terminal.
- Adjusted net-debt/EBITDA is UNKNOWN — the true leverage on the company's own adjusted basis cannot be confirmed.
- Segment EBITDA is UNKNOWN ('Segments sheet has no EBITDA section as expected') — cannot see profitability split of Premier vs Dymatize; a missing expected breakout is a bearish opacity flag.
- No idiosyncratic cohort comparison available (BRBR not in graph coverage) — cannot benchmark the drawdown against a true peer cross-section.
- Whether the named CEO successor and search outcome resolves the leadership uncertainty before the FY-end transition is unresolved.
- EV/EBITDA at 7.5x sits at the 0%ile of its own 19-quarter history on a TRAILING-ONLY basis — a neutral fact the dossier flags as overshoot-vs-terminal unresolved, belonging here, not in bull or bear.
