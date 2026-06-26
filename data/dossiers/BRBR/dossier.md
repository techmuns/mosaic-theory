# Dossier — BELLRING BRANDS, INC. (BRBR)

_Finalist rank 2 · ref 2026-06-22 · assembled 2026-06-25 18:55 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (3.1x) is on consolidated GAAP EBITDA; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio). That non-GAAP reconciliation lives in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.1x as the covenant-basis leverage.
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (6 bull vs 8 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 5.8x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 2nd %ile
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
- **Net debt / EBITDA (GAAP):** 3.1x
  - ↳ `EDGAR XBRL net-debt/EBITDA (screen data-record)`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 3.1x (GAAP) | FCF-positive → self-funding (no runway constraint) | nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 4.0x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Share-count trend:** buying back (trailing ~1.7y): 129,242,457 (2024-07-31) → 116,277,850 (2026-04-28), -10.0%
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-28`
- **Liquidity / covenant flags:** 7.00% Senior Notes Maturing in March 2030 (Bonds and Notes) 840 @ 7.000%; Operating Lease Liabilities (Capital Lease) 30 @ 7.000%; Revolving Credit Facility (Revolving Credit) 250 @ 5.820%
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
- **Name 180d return:** -67.7%
  - ↳ `EOD BRBR 180d to 2026-06-22`
- **Market (IWM) 180d return:** 17.8%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -85.5%
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
- **Earnings call:** Earnings-call transcript on file — read BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish — margin %, absolute EBITDA and ROIC all falling together with a partly-earned peer discount and -85% idiosyncratic underperformance.

### Bull case (overshoot / mean-revert)
- BRBR trades at 7.5x TEV/LTM EBITDA, sitting at the 0th percentile of 19 quarterly closes and a P/LTM-EPS of ~7.9x — a near-floor of its own trading history.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- The business is self-funding: levered FCF is positive at $182.7M (LTM Mar-31-2026) with no runway constraint, so the de-rate is not a solvency story on the cash leg.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Absolute revenue has compounded through the period (1,247 → 2,332 LTM) even as the EBITDA margin % fell, so the top line is not in secular decline.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Management is returning capital — share count fell ~10% (129.2M → 116.3M) over trailing ~1.7y — consistent with a company treating the price as cheap, not distressed.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-28`
- On peer comps the discount question is open not closed: vs a HETEROGENEOUS 10-peer set ($111M–$36.4B caps) the name's NTM P/E 8.78 sits below peer median 10.97 and NTM TEV/EBITDA 7.78 below median 8.7 — POSE whether that gap is EARNED or RESIDUAL, since the name also shows faster rev growth (6% vs 4%) and a comparable beta, which is not the profile of a pure value trap.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The deepest gap-down (2026-02-03) was filed under 8-K item 5.07 (an annual-meeting vote), NOT an earnings/guidance item, so part of the drawdown shape is not a fundamental-miss event.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`

### Bear case (terminal / value-trap)
- The EBITDA margin trajectory is the real signal here, not an optical artifact: the reconciler shows absolute EBITDA ALSO falling (424 at Sep-2024 → 376 Sep-2025 → 312 LTM Mar-2026) alongside the margin slide (21% → 16% → 13%) — both the % and the dollars are deteriorating together.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Profitability quality is rolling over: ROIC fell from 43.1% (Sep-2024) to 25.6% (LTM Mar-2026), confirming the earnings erosion is structural rather than a single-quarter blip.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- On fundamentals the discount looks at least partly EARNED, not residual: name EBITDA margin 13% trails peer-median 16%, EBITDA growth -31% vs peer-median -6%, LT EPS growth -7% vs +7%, and Debt/EBITDA 3.9 vs 2.5 — worse on margin, growth and leverage simultaneously.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Leverage is elevated at 3.1x net-debt/EBITDA (GAAP) with interest coverage of only ~4.0x, thinning the margin for further EBITDA erosion.
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- Consensus carries a structurally negative LT view — target-price mean $13.69, LT growth mean -7.2% / median -10.2%, Hold (3.00) — i.e. the Street already embeds shrinking long-term earnings.
  - ↳ `CIQ Estimates→Consensus`
- The name is overwhelmingly idiosyncratic: -67.7% over 180d while IWM rose +17.8%, a -85.5% relative move, so this is company-specific damage not a market drawdown.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Per management's own posture, insurgent-brand promotional events are running ahead of expectations and were factored into a balance-of-year outlook, signalling competitive pressure on the core Premier franchise.
  - ↳ `CIQ transcript BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf`
- A CEO retirement/leadership transition was announced for on-or-before fiscal year-end with an external search still open, adding execution uncertainty during the de-rate.
  - ↳ `CIQ transcript BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf`

### Twin reference cases
- **The Simply Good Foods Company** — recovered
  - distinguished by: Branded better-for-you nutrition/snack player that absorbed competitive entrants while leaning on brand equity and distribution gains — the closest model for a single-category protein brand defending share.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Herbalife Ltd.** — went terminal
  - distinguished by: Wellness/nutrition brand that de-rated hard amid leverage and demand-durability doubts — the analogue for when a levered single-theme nutrition name's discount proves earned.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **The J. M. Smucker Company** — recovered
  - distinguished by: Branded packaged-food incumbent that traded through input-cost and promotional pressure episodes by holding shelf and pricing over time.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **USANA Health Sciences** — went terminal
  - distinguished by: Nutrition/wellness brand whose growth and margin faded as category competition and demand softened, a cautionary analogue for eroding repeat economics.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Monster Beverage** — recovered
  - distinguished by: Single-category consumables leader that defended a high-velocity, high-repeat franchise against insurgent entrants by out-innovating on flavor/format — pattern for category-leader durability.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the collapse in EBITDA margin and ROIC a temporary cost/promotional-cycle overshoot in a still-growing RTD-shake category, or the start of structural margin compression as insurgent brands permanently re-set the economics of the Premier franchise?**

### …evidence for
- Revenue kept growing through the de-rate (1,247 → 2,332 LTM) and management cites a healthy high-single-digit category with retailers expanding shelf — consistent with a temporary margin dip on whey costs and promo timing.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Management frames Q1 as ahead of expectations with consumption ramping and growth strategies expected to contribute more in 2H — a transitional, not terminal, posture.
  - ↳ `CIQ transcript BellRing Brands, Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf`

### …evidence against
- Both margin % AND absolute EBITDA are falling together (21%/424 → 13%/312) and ROIC dropped from 43.1% to 25.6%, with EBITDA growth -31% vs peer-median -6% — a structurally worse profile.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Consensus LT growth is -7.2% mean / -10.2% median with a $13.69 mean target, indicating the Street models persistent decline rather than a one-year reset.
  - ↳ `CIQ Estimates→Consensus`

### Key unknowns
- Forward/adjusted basis is missing: ev_ebitda_adjusted_fwd and adjusted_eps are UNKNOWN (not in the 99.1 revised guidance), so the 7.5x trailing multiple cannot be tested as cheap-overshoot vs cheap-terminal — a bearish opacity gap.
- The May-5-2026 8-K revised_guidance / 99.1 exhibit was not parsed, so the magnitude of any guidance cut at the second gap-down is undisclosed here — surface as a bearish missing-disclosure.
- Nearest refinancing wall is UNKNOWN (no maturity dates parsed) against $840M 7.00% notes due 2030 and a $250M revolver — a survival-capacity leg left open and treated as a risk, not neutral.
- Segment-level EBITDA is UNKNOWN (no EBITDA section on the Segments sheet) and revenue is 100% one Protein-Based segment, so Premier-vs-Dymatize profitability mix cannot be inspected — a bearish opacity gap.
- Estimate-revision breadth shows 0↑/0↓ last month on both EPS and revenue, so there is no fresh directional confirmation of where consensus is moving post-de-rate.
- No graph cohort exists for BRBR (not in graph_coverage.json), so the idiosyncratic read rests only on name-vs-IWM, with no peer cross-section.
- Whether the peer discount is EARNED or RESIDUAL is unresolved against a HETEROGENEOUS peer set (caps span 327x), so every peer multiple is a confidence-gated input, not a clean benchmark, for the human to adjudicate.
