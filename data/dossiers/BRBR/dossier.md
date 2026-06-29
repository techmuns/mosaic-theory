# Dossier — BELLRING BRANDS, INC. (BRBR)

_Finalist rank 2 · ref 2026-06-22 · assembled 2026-06-29 16:10 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (3.8x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.8x as the covenant-basis leverage.
- MISMATCH bear_point: 'Q2 FY2026 adjusted EBITDA margin of 9% came in 400bps…' asserts missing/UNKNOWN data yet cites a PRESENT field — move to key_unknowns, don't source-bind it
- TRANSCRIPT-FIGURE '14' in bear_point: 'Management cut full-year FY2026 outlook to flat-to-+2% net sales and…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '27' in decisive.against: 'Management reported the first decline in RTD-shake buy-rate per…' — from the cited earnings call, not the structured facts; verify against the call
- TWIN 'Medifast, Inc.' has numbers ['1'] — must be non-numeric
- DIRECTIONAL language 'buy' — human review (dossier frames, not concludes)
- UNRECONCILED bear_point: 'EBITDA margin has collapsed from 21% (Sep-2024) to 13% LTM and…' — cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)
- UNRECONCILED bear_point: 'Q2 FY2026 adjusted EBITDA margin of 9% came in 400bps below the…' — cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (5 bull vs 8 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

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
- **Relative vs market:** -81.0%
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

**Evidence balance:** strongly-bearish — both margin % and absolute EBITDA are falling on company-confirmed structural promotional, consumer-trade-down and commodity-inflation headwinds.

### Bull case (overshoot / mean-revert)
- Despite EBITDA margin compressing to 13% LTM, absolute revenue has continued rising to $2,332M and the category itself remains one of the fastest-growing in CPG, suggesting the multiple compression may be cyclical-promotional rather than a terminal demand failure — the consensus margin read may overstate the case.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The business is FCF-positive ($182.7M LTM) and self-funding with no runway constraint and a nearest maturity wall at 2030, so the de-rating is not a solvency story.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Management is buying back stock through the drawdown (share count -10.0% over ~1.7y), a capital-allocation signal consistent with a self-funding overshoot rather than a distressed name.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-28`
- On TEV/EBITDA the name trades 7.9 LTM vs a peer median of 6.2 (and 7.78 NTM vs peer median 8.7) — but the peer set spans $111M–$36.4B (327x) and is flagged HETEROGENEOUS, so whether the discount is EARNED by worse fundamentals or RESIDUAL overshoot is for the human to judge, not a clean 'cheap' read.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- On fundamentals the name shows faster revenue growth (6% vs peer-median 4%) and only modestly higher leverage (Debt/EBITDA 3.9 vs 2.5), posing whether part of the discount is unexplained by fundamental_deltas — a residual the human must adjudicate.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Bear case (terminal / value-trap)
- EBITDA margin has collapsed from 21% (Sep-2024) to 13% LTM and absolute EBITDA has FALLEN with it — $424M to $312M — so this is NOT the optical case where a % falls while EBITDA rises; both the rate AND the dollars are declining, confirming the margin signal is REAL, not a consensus misread.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Q2 FY2026 adjusted EBITDA margin of 9% came in 400bps below the company's own 13% guide and adjusted gross margin fell to 22.7% from 34.5% a year ago, indicating the deterioration is accelerating and management is missing its own near-term targets. ⚠ uncited
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- Management cut full-year FY2026 outlook to flat-to-+2% net sales and a 14% adjusted EBITDA margin, citing structural pressures — intensifying insurgent-brand promotion, a value-shifting consumer (first buy-rate decline in 5 years), freight and protein-driven commodity inflation worsening into Q4 — pointing to persistent, not one-off, headwinds.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- Fundamental_deltas show the name is materially worse than peers on the metrics that justify a discount: EBITDA margin 13% vs 16%, EBITDA growth -31% vs -6%, LT EPS growth -7% vs +7%, and leverage 3.9 vs 2.5 — supporting an EARNED discount (value-trap) reading rather than pure overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The name massively underperformed its market over 180 days (-66.2% vs IWM +18.0%, -81.0% relative), an idiosyncratic collapse not explained by broad market conditions.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Net-debt/EBITDA of 3.8x and net-debt/OCF of 6.1x, with interest coverage of only 4.0x, mean falling EBITDA directly erodes the leverage and coverage cushion against 7.00% senior notes.
  - ↳ `CIQ Net Debt $1,190M [FQ2/CQ1 Mar-31-2026] ÷ CIQ EBITDA $312M [LTM 12 months Mar-31-2026]`
- 100% single-segment, single-category concentration (Protein-Based Consumer Goods) leaves no diversification offset to the RTD-shake promotional war pressuring the entire business.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- Consensus is unsupportive: Hold rating (3.00), mean target $13.69, and negative LT growth (mean -7.2% / median -10.2%), with a CEO retirement announced mid-deterioration adding leadership-transition uncertainty.
  - ↳ `CIQ Estimates→Consensus`

### Twin reference cases
- **Medifast, Inc.** — went terminal
  - distinguished by: Single-category branded nutrition leader that de-rated hard as a demand/competitive shift (GLP-1, channel) eroded its core franchise without diversification to offset.
  - source: [LLM-suggested, unverified]
- **Beyond Meat, Inc.** — went terminal
  - distinguished by: High-growth protein-adjacent insurgent whose category enthusiasm reversed into a margin and competitive-intensity collapse once novelty faded.
  - source: [LLM-suggested, unverified]
- **The Simply Good Foods Company** — recovered
  - distinguished by: Single-focus nutrition/protein brand that weathered category competition and re-rated as volume and distribution held — also a named peer in this set.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Herbalife Ltd.** — went terminal
  - distinguished by: Levered single-vertical wellness name whose multiple stayed depressed as debt cushion and growth both eroded — a value-trap pattern on leverage; also a named peer.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **e.l.f. Beauty, Inc.** — recovered
  - distinguished by: Fast-growing consumer brand that absorbed a sharp growth-scare de-rating and recovered when household-penetration and distribution momentum proved intact through the soft patch.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the margin/EBITDA collapse a cyclical promotional-war-plus-input-inflation overshoot that normalizes as competition moderates and innovation/distribution ramps, or a structural reset to a permanently lower-margin, more price-competitive RTD-shake category?**

### …evidence for
- Management frames the promotional intensity as competition it expects to 'gradually moderate over time' as retailers consolidate shelf behind scaled leaders, and points to record consumption events and double-digit out-of-club volume growth.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- Revenue is still growing (6% vs peer-median 4%) and the name remains FCF-positive and self-funding, consistent with a temporary profitability dip rather than demand destruction.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### …evidence against
- Management reported the first decline in RTD-shake buy-rate per household in 5 years and 27% of category volume sold on promotion (up 8pts YoY), alongside worsening protein-commodity inflation into Q4 — structural, not transient, pressures.
  - ↳ `CIQ transcript(s): BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
- EBITDA growth of -31% vs peer-median -6% and LT EPS growth of -7% vs +7% show the deterioration is name-specific and severe relative to the peer group.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Key unknowns
- Revised forward guidance: no revised-outlook 99.1 exhibit was parsed, so the explicit FY2026 guidance figures are only available via transcript narrative, not a structured source-bound fact.
- Forward valuation: adjusted forward EV/EBITDA and adjusted EPS are UNKNOWN (not in the 99.1 revised guidance) — the TEV/LTM 7.5x at the 0th percentile is trailing-only and cannot distinguish cheap-overshoot from cheap-terminal; this is unresolved, not directional.
- Segment EBITDA is UNKNOWN (no EBITDA section on the Segments sheet) — a MISSING expected disclosure that obscures whether Premier vs Dymatize profitability is diverging; treat as a bearish opacity risk.
- Customer concentration magnitude: top customers (Walmart, Costco, Amazon, Sam's) are named but no revenue-percentage breakout is given — the degree of buyer-power exposure to the promotional war is undisclosed; bearish opacity.
- Cohort/idiosyncratic-vs-shared read is UNKNOWN (BRBR not in graph coverage) — only the name-vs-market relative is available.
- Estimate revision breadth shows 0 up / 0 down last month for both EPS and revenue — stale or uncovered, so consensus may not yet reflect the Q2 cut.
- CEO succession: a national external CEO search is underway with transition by end of FY2026 — leadership and strategic continuity through the deterioration is unresolved.
