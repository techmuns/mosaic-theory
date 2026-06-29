# Dossier — Vital Farms, Inc. (VITL)

_Finalist rank 4 · ref 2026-06-22 · assembled 2026-06-29 17:21 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- TRANSCRIPT-FIGURE '75' in bull_point: 'Management frames 2026 as a deliberate margin 'low watermark' from…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '55' in bear_point: 'Management itself confirmed new-household trial dropped (>55% to 50%…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '55' in decisive.against: 'New-household trial dropped (>55% to 50%) at the price-gap levels…' — from the cited earnings call, not the structured facts; verify against the call
- DIRECTIONAL language 'recommendation' — human review (dossier frames, not concludes)

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 7.8x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 3rd %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 1.5x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 1.5x at 0%ile of 19 closes → near-floor; P/LTM EPS 9.8x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** negative
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** -53.9
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-29-2026]`
- **Margin trend:** EBITDA margin: Dec-26-2021 (R) 1% → Dec-25-2022 (R) 3% → Dec-31-2023 9% → Dec-29-2024 13% → Dec-28-2025 14% → Mar-29-2026 (LTM) 10%; gross margin: Dec-26-2021 (R) 32% → Dec-25-2022 (R) 31% → Dec-31-2023 34% → Dec-29-2024 38% → Dec-28-2025 38% → Mar-29-2026 (LTM) 35%; absolute EBITDA: Dec-26-2021 (R) 4 → Dec-25-2022 (R) 10 → Dec-31-2023 41 → Dec-29-2024 77 → Dec-28-2025 103 → Mar-29-2026 (LTM) 79; absolute revenue: Dec-26-2021 (R) 261 → Dec-25-2022 (R) 362 → Dec-31-2023 472 → Dec-29-2024 606 → Dec-28-2025 759 → Mar-29-2026 (LTM) 784  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA:** 0.0x
  - ↳ `CIQ Net Debt $3M [Q1 Mar-29-2026] ÷ CIQ EBITDA $80M [LTM 12 months Mar-29-2026]`
- **Net debt / OCF:** 0.3x
  - ↳ `CIQ Net Debt $3M [Q1 Mar-29-2026] ÷ CIQ OCF $10M [LTM 12 months Mar-29-2026]`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 0.0x (CIQ) | FCF-negative → burning cash; runway = cash ÷ burn (cash not derived — a risk) | nearest maturity wall: 2029
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 99.4x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-29-2026]`
- **Share-count trend:** flat (trailing ~1.7y): 43,098,946 (2024-08-05) → 42,848,454 (2026-05-04), -0.6%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`
- **Liquidity / covenant flags:** Finance Lease Liabilities (Capital Lease) 11 @ 6.730%; JPMorgan Credit Facility (Revolving Credit) undrawn/– @ NA Due 2029; Operating Lease Liabilities (Capital Lease) 43 @ 4.770%
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Dec-26-2021 (R) 261 → Dec-25-2022 (R) 362 → Dec-31-2023 472 → Dec-29-2024 606 → Dec-28-2025 759 → Mar-29-2026 (LTM) 784; EBITDA: Dec-26-2021 (R) 4 → Dec-25-2022 (R) 10 → Dec-31-2023 41 → Dec-29-2024 77 → Dec-28-2025 103 → Mar-29-2026 (LTM) 79; Revenue YoY (latest same-quarter): +15.4% (Q1 Mar-29-2026 vs Q1 Mar-30-2025); ROIC: Dec-26-2021 0.0% → Dec-25-2022 1.7% → Dec-31-2023 10.8% → Dec-29-2024 15.8% → Dec-28-2025 15.9% → Mar-29-2026 (LTM) 11.6%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Dec-28-2025] Eggs and Butter 759 (100%) of Total 759
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Albertsons Companies, Inc. (NYSE:ACI) — Distributor · Food Retail · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Ben E. Keith Company — Distributor · Food Distributors · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Dot Foods, Inc. — Distributor · Air Freight and Logistics · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Gordon Food Service, Inc. — Distributor · Food Distributors · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Performance Food Group, Inc. — Distributor · Food Distributors · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Publix Super Markets, Inc. — Distributor · Food Retail · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Shamrock Foods Company — Distributor · Packaged Foods and Meats · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Sprouts Farmers Market, Inc. (NasdaqGS:SFM) — Distributor · Food Retail · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Sysco Corporation (NYSE:SYY) — Distributor · Food Distributors · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Target Corporation (NYSE:TGT) — Distributor · Consumer Staples Merchandise Retail · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; The Kroger Co. (NYSE:KR) — Distributor · Food Retail · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; United Natural Foods, Inc. (NYSE:UNFI) — Distributor · Food Distributors · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; US Foods, Inc. — Distributor · Food Distributors · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Walmart Inc. (NasdaqGS:WMT) — Distributor · Consumer Staples Merchandise Retail · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K; Whole Foods Market, Inc. — Distributor · Food Retail · src: Vital Farms, Inc. (NasdaqGM:VITL) 2026 Form 10-K
  - ↳ `CIQ Customers&Suppliers Vital Farms Inc NasdaqGM VITL Customers.rtf`
- **Geographic:** [12 months Dec-28-2025] United States 759 (100%) of Total 759
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — Cal-Maine Foods $3.8B — engages in the production, grading, packaging, (United States); The Simply Good Foods Company $1.2B — engages in the development, marketing, and sale of (United States); Mondelez International $78.0B — manufactures, markets, and sells snack food and (United States); The Kraft Heinz Company $28.1B — manufactures and markets food and beverage products in (United States); Freshpet $2.8B — manufactures, distributes, and markets natural fresh (United States); Utz Brands $683M — manufactures branded salty snacks in the United (United States); Oatly Group AB $281M — provides a range of plant-based dairy products in the (Sweden); BellRing Brands $1.3B — provides various nutrition products in the United (United States); The Hain Celestial Group $50M — manufactures, markets, and sells organic and natural (United States); Post Holdings $4.1B — operates as a consumer packaged goods holding company (United States) | the name: $480M
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $50M–$78.0B (1567x); the name is $480M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 0.6 vs peers Low 0.4 / Median 1.2 / Mean 1.4 / High 2.6; TEV/EBITDA: name 1.2 vs peers Low 2.7 / Median 7.2 / Mean 10.2 / High 23.2; P/E: name 10.7 vs peers Low 5.6 / Median 15.1 / Mean 15.1 / High 30.1; NTM TEV/Rev: name 0.62 vs peers Low 0.52 / Median 1.27 / Mean 1.41 / High 2.43; NTM TEV/EBITDA: name 70.81 vs peers Low 6.8 / Median 8.98 / Mean 10.98 / High 25.99; NTM P/E: name NM vs peers Low 7.85 / Median 11.36 / Mean 16.02 / High 41.44  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 10% vs peer-median 15%; rev growth name 26% vs peer-median 4%; EBITDA growth name 6% vs peer-median -11%; Debt/EBITDA name 0.1 vs peer-median 3.8; LT EPS growth name – vs peer-median 3%; beta name 1.1 vs peer-median 0.5  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-26 earnings (2.02) + management change (5.02) + Reg-FD (7.01) + other event (8.01); 2026-05-07 earnings (2.02) + restructuring (2.05)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-26, 2026-05-07
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-26 → 2026-02-26 [`0001193125-26-073373`](https://www.sec.gov/Archives/edgar/data/1579733/000119312526073373/vitl-20260220.htm)
    - items: 2.02 Results of Operations and Financial Condition, 5.02 Departure/Election of Directors or Certain Officers, 7.01 Regulation FD Disclosure, 8.01 Other Events, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition On February 26, 2026, Vital Farms, Inc. (the “Company”) issued a press release announcing its financial results for the fiscal year ended December 28, 2025. A copy of the earnings press release is furnished as Exhibit 99.1 to this Current Report on Form 8-K (this “Current Report”) and is incorporated herein by reference. The information provided under
    - 5.02 Departure/Election of Directors or Certain Officers: Departure of Directors or Certain Officers; Appointment of Certain Officers; Compensatory Arrangement of Certain Officers. On February 20, 2026, Matthew O’Hayer, the Company’s founder, Executive Chairperson and a member of the Company's Board of Directors (the “Board”) informed the Company and the Board of his resignation as Executive Chairperson, as a member of the Board and as an employee, effec
    - 7.01 Regulation FD Disclosure: Regulation FD Disclosure. A copy of the Company’s press releases announcing the foregoing are attached to this Current Report as Exhibits 99.1 and 99.2 and incorporated herein by reference. The information in this
    - 8.01 Other Events: Other Events. On February 26, 2026, the Company announced that the Board has authorized and approved a plan to repurchase up to $100.0 million of shares (the “Stock Repurchase Program”) of the Company’s outstanding common stock, par value $0.0001 per share (“Common Stock”). Under the Stock Repurchase Program, the Company intends to repurchase shares of Common Stock from time to time, including, wi
  - gap 2026-05-07 → 2026-05-07 [`0001193125-26-210294`](https://www.sec.gov/Archives/edgar/data/1579733/000119312526210294/vitl-20260501.htm)
    - items: 2.02 Results of Operations and Financial Condition, 2.05 Costs Associated with Exit or Disposal Activities, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition On May 7, 2026, Vital Farms, Inc. (the “Company”) issued a press release announcing its financial results for the fiscal quarter ended March 29, 2026. A copy of the press release is furnished as Exhibit 99.1 to this Current Report on Form 8-K (this “Current Report”) and is incorporated herein by reference. The information provided in this Form 8-K, inc
    - 2.05 Costs Associated with Exit or Disposal Activities: Costs Associated with Exit or Disposal Activities. On May 1, 2026, management of the Company elected to wind down and discontinue its butter product offerings to focus on its core egg product categories, with such discontinuation expected to be substantially completed by the end of fiscal 2026. In connection with the discontinuation plan, the Company expects to incur butter inventory-related charg
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001193125-26-073373', '0001193125-26-210294']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -69.2%
  - ↳ `EOD VITL 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -86.8%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — VITL not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $11.67 / median $11.00; Recommendation: Outperform (2.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 +50%, FY2022 -33%, FY2023 +20%, FY2024 +5%, FY2025 -3%; Revenue surprise: FY2021 +2%, FY2022 +2%, FY2023 +1%, FY2024 +1%, FY2025 +0% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Vital Farms, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Vital Farms, Inc., Q4 2025 Earnings Call, Feb 26, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Vital Farms, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Vital Farms, Inc., Q4 2025 Earnings Call, Feb 26, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — near-unlevered balance sheet and still-growing revenue offset by real (dollar-confirmed) margin decline, cash burn, and an unquantified runway.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA scaled ~20x from 4 (Dec-2021) to a peak of 103 (Dec-2025) on revenue rising 261→759, so the margin %, not the dollar engine, is what dipped to LTM 79 — read the reconciler together, not the % alone.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The balance sheet is near-unlevered at net-debt/EBITDA 0.0x with interest coverage 99.4x and the nearest maturity wall only in 2029, so this is not a leverage-driven distress de-rate.
  - ↳ `CIQ Net Debt $3M [Q1 Mar-29-2026] ÷ CIQ EBITDA $80M [LTM 12 months Mar-29-2026]`
- Revenue growth remains positive — +15.4% same-quarter YoY (Q1 Mar-29-2026 vs Q1 Mar-30-2025) — so the top line is still expanding through the de-rate.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- On the fundamental_deltas the discount looks at least partly RESIDUAL not EARNED on growth: name rev growth 26% vs peer-median 4% and Debt/EBITDA 0.1 vs peer-median 3.8 are far BETTER than peers — but this is posed for the human, not computed, and is set against a HETEROGENEOUS peer set spanning $50M–$78.0B caps.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Management frames 2026 as a deliberate margin 'low watermark' from narrowing price gaps with cost actions (ECS staffing, ~10% remote headcount cut, ~$75M CapEx reduction) targeted to flow through in 2027 — a self-described reset of expectations, not ambitions.
  - ↳ `CIQ transcript(s): Vital Farms, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Vital Farms, Inc., Q4 2025 Earnings Call, Feb 26, 2026.rtf`
- Sell-side context is not capitulating: recommendation sits at Outperform (2.00) with mean target $11.67, and a $100M buyback was authorized at the Feb-2026 8-K.
  - ↳ `CIQ Estimates→Consensus`

### Bear case (terminal / value-trap)
- LTM EBITDA margin fell from a 14% peak (Dec-2025) to 10% (Mar-2026) AND absolute EBITDA fell with it (103→79) — here the % decline is the REAL signal, not an optical artifact, because the dollar reconciler moved the same direction.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Levered free cash flow is -53.9 (LTM Mar-2026): the company is burning cash even while near-unlevered, so survival depends on a cash balance not derived here.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-29-2026]`
- The drawdown is idiosyncratic, not market-driven: the name is -69.2% over 180d while IWM is +18.0%, a -86.8% relative gap.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- The gap-downs sit on discrete adverse 8-K events — Feb-2026 earnings plus a founder/Executive-Chair departure (5.02), and May-2026 earnings plus restructuring (2.05) winding down the butter line — not a single noisy print.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- The business is single-segment, single-geography concentrated: Eggs and Butter 100% of revenue and United States 100% of revenue, so there is no diversification cushion against the price-gap/velocity shock management described.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- On fundamental_deltas the discount is at least partly EARNED: name EBITDA margin 10% vs peer-median 15% and a higher beta 1.1 vs peer-median 0.5 — worse profitability and more volatility than the median peer.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Management itself confirmed new-household trial dropped (>55% to 50% of consumers) because price gaps 'reached levels our brand could not sustain,' and said cost-structure benefits land mostly in 2027 — i.e. the margin pressure persists through 2026.
  - ↳ `CIQ transcript(s): Vital Farms, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Vital Farms, Inc., Q4 2025 Earnings Call, Feb 26, 2026.rtf`

### Twin reference cases
- **Freshpet** — recovered
  - distinguished by: Single-category premium-positioned US food brand that endured a sharp growth/margin scare and capex-heavy capacity build before profitability inflected.
  - source: [LLM-suggested, unverified]
- **Beyond Meat** — went terminal
  - distinguished by: Premium single-category food brand whose price-premium thesis broke as the value gap to conventional alternatives widened and trial collapsed.
  - source: [LLM-suggested, unverified]
- **Oatly Group AB** — went terminal
  - distinguished by: Premium-positioned single-category food/beverage name that scaled capacity ahead of demand into a softening, price-sensitive consumer.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **The Hain Celestial Group** — went terminal
  - distinguished by: Natural/organic food brand whose premium positioning compressed amid distribution and margin pressure with management turnover.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Cal-Maine Foods** — recovered
  - distinguished by: US shell-egg producer exposed to the same commodity-egg-price cycle management cited as the driver of price gaps and velocity swings.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)

### Decisive question
**Is the margin/velocity hit a temporary price-gap reset that 2027 cost actions reverse (overshoot), or a structural break in the brand's sustainable price premium that compounds the ongoing cash burn (value trap)?**

### …evidence for
- Management cites a concrete recovery mechanism — narrowing a top-10 customer's gap from ~35% to ~25% lifted volumes 18% in two weeks — and frames 2026 as the cyclical low watermark.
  - ↳ `CIQ transcript(s): Vital Farms, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Vital Farms, Inc., Q4 2025 Earnings Call, Feb 26, 2026.rtf`
- Revenue is still growing +15.4% same-quarter YoY and the balance sheet is near-unlevered (net-debt/EBITDA 0.0x, 2029 maturity wall), giving time for cost actions to land.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### …evidence against
- New-household trial dropped (>55% to 50%) at the price-gap levels seen, and management said the price premium will be 'just not as much' — a possible permanent reset of the premium that anchors the model.
  - ↳ `CIQ transcript(s): Vital Farms, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Vital Farms, Inc., Q4 2025 Earnings Call, Feb 26, 2026.rtf`
- Both absolute EBITDA AND margin % fell together (103→79; 14%→10%) while FCF is -53.9, so the deterioration is real and cash is leaving while the reset plays out.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-29-2026]`

### Key unknowns
- Absolute cash/marketable-securities balance and resulting runway against the -53.9 FCF burn are NOT derived here — survival_capacity flags 'cash not derived — a risk'; an unquantified runway against confirmed burn is a BEARISH gap (the Q4 transcript mentions $113.4M cash at Dec-2025 but no source_ref permits using it).
- No revised forward guidance was parsed from either 8-K (revised_guidance UNKNOWN) — absence of a forward guide after two guide-down events is a BEARISH opacity signal, not a neutral one.
- Adjusted EBITDA, adjusted EPS, and adjusted leverage are all UNKNOWN (not in the 99.1 revised guidance), so the entire forward/adjusted basis the company manages to is missing.
- NTM TEV/EBITDA reads 70.81 vs peer median 8.98 and NTM P/E is NM — the forward multiple is NOT 'cheap'; whether the 1.5x trailing EV/EBITDA at its own 0th percentile is overshoot or terminal is explicitly unresolved (trailing-only, no forward basis) — a neutral fact for the human, not a bull or bear point.
- Segment-level EBITDA is UNKNOWN (Segments sheet has no EBITDA section), so the profitability of the discontinued butter line vs core eggs cannot be isolated.
- Estimate-revision breadth shows 0↑/0↓ for FY2026 EPS and revenue last month — stale/no breadth, so consensus has not visibly repriced post-events.
- No exposed cohort cross-section (VITL not in graph_coverage) to confirm whether peers share the move; only the name-vs-IWM relative read is available.
- Peer set is HETEROGENEOUS ($50M–$78.0B caps, 1567x span) — every peer multiple is a confidence-gated input, not a clean benchmark, and the earned-vs-residual split must be judged against that.
