# Dossier — Simply Good Foods Co (SMPL)

_Finalist rank 12 · ref 2026-06-22 · assembled 2026-06-30 08:52 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 12.8x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 4th %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 6.0x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 6.0x at 0%ile of 20 closes → near-floor; P/LTM EPS 16.0x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 125.5
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Feb-28-2026]`
- **Margin trend:** EBITDA margin: Aug-28-2021 (R) 20% → Aug-27-2022 (R) 19% → Aug-26-2023 (R) 18% → Aug-31-2024 19% → Aug-30-2025 18% → Feb-28-2026 (LTM) 17%; gross margin: Aug-28-2021 (R) 41% → Aug-27-2022 (R) 38% → Aug-26-2023 (R) 36% → Aug-31-2024 39% → Aug-30-2025 36% → Feb-28-2026 (LTM) 34%; absolute EBITDA: Aug-28-2021 (R) 196 → Aug-27-2022 (R) 222 → Aug-26-2023 (R) 225 → Aug-31-2024 250 → Aug-30-2025 262 → Feb-28-2026 (LTM) 236; absolute revenue: Aug-28-2021 (R) 1,006 → Aug-27-2022 (R) 1,169 → Aug-26-2023 (R) 1,243 → Aug-31-2024 1,331 → Aug-30-2025 1,451 → Feb-28-2026 (LTM) 1,416  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA:** 1.5x
  - ↳ `CIQ Net Debt $342M [FQ2/CQ1 Feb-28-2026] ÷ CIQ EBITDA $236M [LTM 12 months Feb-28-2026]`
- **Net debt / OCF:** 2.0x
  - ↳ `CIQ Net Debt $342M [FQ2/CQ1 Feb-28-2026] ÷ CIQ OCF $173M [LTM 12 months Feb-28-2026]`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 1.5x (CIQ) | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2029
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 12.3x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Feb-28-2026]`
- **Share-count trend:** buying back (trailing ~1.8y): 100,135,854 (2024-06-24) → 90,489,024 (2026-04-07), -9.6%
  - ↳ `EDGAR XBRL shares, trailing 2024-06-24..2026-04-07`
- **Liquidity / covenant flags:** Credit Agreement With Barclays Bank PLC and Other Parties - Revolving Credit Facility (Revolving Credit) undrawn/– @ 4.200% Due 2029; Credit Agreement With Barclays Bank PLC and Other Parties - Term Loan (Term Loans) 249 @ 5.700% Due 2030; Operating Lease (Capital Lease) 55 @ 6.000%
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Aug-28-2021 (R) 1,006 → Aug-27-2022 (R) 1,169 → Aug-26-2023 (R) 1,243 → Aug-31-2024 1,331 → Aug-30-2025 1,451 → Feb-28-2026 (LTM) 1,416; EBITDA: Aug-28-2021 (R) 196 → Aug-27-2022 (R) 222 → Aug-26-2023 (R) 225 → Aug-31-2024 250 → Aug-30-2025 262 → Feb-28-2026 (LTM) 236; ROIC: Aug-28-2021 6.4% → Aug-27-2022 7.1% → Aug-26-2023 6.8% → Aug-31-2024 7.0% → Aug-30-2025 7.0% → Feb-28-2026 (LTM) 6.5%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Aug-30-2025] Branded Nutritional Foods and Snacking Products 1,451 (100%) of Total 1,451
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Amazon.com, Inc. (NasdaqGS:AMZN) — Distributor · Broadline Retail · src: The Simply Good Foods Company (NasdaqCM:SMPL) 2025 Form 10-K; Only What You Need, Inc. — Distributor · Soft Drinks and Non-alcoholic Beverages · src: The Simply Good Foods Company (NasdaqCM:SMPL) 2025 Form 10-K; Quest Nutrition, LLC — Distributor · Packaged Foods and Meats · src: The Simply Good Foods Company (NasdaqCM:SMPL) 2025 Form 10-K; Simply Good Foods USA, Inc. — Distributor · Packaged Foods and Meats · src: The Simply Good Foods Company (NasdaqCM:SMPL) 2025 Form 10-K; Walmart Inc. (NasdaqGS:WMT) — Distributor · Consumer Staples Merchandise Retail · src: The Simply Good Foods Company (NasdaqCM:SMPL) 2025 Form 10-K
  - ↳ `CIQ Customers&Suppliers The Simply Good Foods Company NasdaqCM SMPL Customers.rtf`
- **Geographic:** [12 months Aug-30-2025] North America 1,421 (98%); International 29 (2%) of Total 1,451
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — Utz Brands $651M — manufactures branded salty snacks in the United (United States); The Hain Celestial Group $54M — manufactures, markets, and sells organic and natural (United States); J&J Snack Foods Corp. $1.4B — manufactures, markets, and distributes nutritional (United States); The Marzetti Company $3.1B — engages in manufacturing and marketing of specialty (United States); BellRing Brands $1.4B — provides various nutrition products in the United (United States); The Campbell's Company $6.6B — manufactures and markets food and beverage products in (United States); John B. Sanfilippo & Son $985M — distributes tree nuts and peanuts in the United (United States); Conagra Brands $6.5B — operates as a consumer packaged goods food company (United States); Freshpet $2.6B — manufactures, distributes, and markets natural fresh (United States); The Kraft Heinz Company $27.2B — manufactures and markets food and beverage products in (United States) | the name: $1.1B
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $54M–$27.2B (507x); the name is $1.1B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 1 vs peers Low 0.4 / Median 1.3 / Mean 1.3 / High 2.4; TEV/EBITDA: name 6 vs peers Low 6.2 / Median 7.8 / Mean 9.7 / High 22.9; P/E: name NM vs peers Low 9.3 / Median 14.6 / Mean 15.3 / High 24.9; NTM TEV/Rev: name 1.13 vs peers Low 0.53 / Median 1.31 / Mean 1.31 / High 2.19; NTM TEV/EBITDA: name 6.81 vs peers Low 6.85 / Median 8.7 / Mean 8.78 / High 12.04; NTM P/E: name 7.59 vs peers Low 8.42 / Median 11.41 / Mean 14.62 / High 38.06  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 17% vs peer-median 14%; rev growth name 0% vs peer-median 0%; EBITDA growth name -11% vs peer-median -9%; Debt/EBITDA name 1.8 vs peer-median 3.4; LT EPS growth name 3% vs peer-median -9%; beta name 0.2 vs peer-median 0.4  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-04-09 earnings (2.02); 2026-04-10 earnings (2.02)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-04-09, 2026-04-10
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-04-09 → 2026-04-09 [`0001702744-26-000010`](https://www.sec.gov/Archives/edgar/data/1702744/000170274426000010/atk-20260409.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On April 9, 2026, The Simply Good Foods Company, a Delaware corporation (the “Company”), reported its results for the fiscal second quarter ended February 28, 2026. The results are discussed in detail in the press release attached hereto as Exhibit 99.1. In addition, the Company has posted an investor presentation at www.thesimplygoodfoodscompany.com.
  - gap 2026-04-10 → 2026-04-09 [`0001702744-26-000010`](https://www.sec.gov/Archives/edgar/data/1702744/000170274426000010/atk-20260409.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On April 9, 2026, The Simply Good Foods Company, a Delaware corporation (the “Company”), reported its results for the fiscal second quarter ended February 28, 2026. The results are discussed in detail in the press release attached hereto as Exhibit 99.1. In addition, the Company has posted an investor presentation at www.thesimplygoodfoodscompany.com.
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001702744-26-000010', '0001702744-26-000010']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -40.0%
  - ↳ `EOD SMPL 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -56.8%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — SMPL not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/1↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $17.33 / median $14.00; LT growth: mean 2.9% / median 4.3%; Recommendation: Hold (3.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 -42%, FY2022 +0%, FY2023 -3%, FY2024 -9%, FY2025 -36%; Revenue surprise: FY2021 +0%, FY2022 +1%, FY2023 +0%, FY2024 +0%, FY2025 +0% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish — a hard guidance cut to a ~20% EBITDA decline plus a $249M brand impairment confirm real deterioration, not an optical overshoot.

### Bull case (overshoot / mean-revert)
- The balance sheet is self-funding — net-debt/EBITDA 1.5x, FCF-positive, nearest maturity wall not until 2029 — so this is not a runway-constrained survival story.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Interest coverage is a comfortable 12.3x, leaving no near-term solvency pressure even after the EBITDA decline.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Feb-28-2026]`
- On the leverage fundamental_delta the name screens materially LESS levered than peers (Debt/EBITDA 1.8 vs peer-median 3.4), arguing the peer discount on this leg is not earned by a worse balance sheet.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- On margin and forward growth fundamentals the name screens BETTER than peers (EBITDA margin 17% vs 14%; LT EPS growth 3% vs peer-median -9%), posing whether the peer-multiple discount is RESIDUAL/overshoot rather than EARNED — the human judges.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Management is buying the discount aggressively — repurchasing over 10% of shares in the past 12 months and borrowing $150M to accelerate buybacks, with -9.6% share count over ~1.8y, signalling insider conviction the price discounts the long-term opportunity.
  - ↳ `EDGAR XBRL shares, trailing 2024-06-24..2026-04-07`
- Absolute EBITDA has compounded over the multi-year window (196→262 to FY25) even as margin % drifted, a reconciler showing the margin-compression narrative is not the whole picture.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### Bear case (terminal / value-trap)
- Management cut FY26 guidance hard at Q2 to adjusted EBITDA $217–225M, a 22–19% year-over-year DECLINE, and the absolute EBITDA reconciler confirms the turn is real — LTM EBITDA already fell to 236 from FY25's 262, so the trailing-EBITDA strength is now rolling over, not optical.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- The EV/EBITDA at 6.0x sitting at the 0th percentile of its own 5y range is a REAL signal of a regime break — but it is trailing-only, so it cannot by itself distinguish cheap-overshoot from cheap-terminal (flagged in the fact itself).
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`
- The falling margin trend is now a GENUINE signal not just an optical %: Q2 gross margin fell 460bps to 31.6% on cocoa/whey/tariff inflation, and LTM EBITDA margin slipped to 17% as absolute EBITDA turned DOWN to 236 — the % and the absolute now move the same direction.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- A $249M non-cash impairment on the OWYN and Atkins brand assets was taken in Q2 — management's own write-down of the acquired growth brands, a real signal of impaired underlying value.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- The decline is idiosyncratic, not market-driven: the name is down ~40% over 180d while IWM rose ~18%, a -57% relative gap, isolating the problem to SMPL's fundamentals.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- The drawdown was a discrete gap-down on the Q2 earnings 8-K (item 2.02), pinning the de-rate to the reported results, not a transient macro move.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Demand is deteriorating across the portfolio per the latest call: Q2 retail takeaway -6.4% YoY, OWYN consumption -2.4% (now facing lost distribution), Atkins -23.4%, and a CEO change with the new chief stating they are 'not pleased' and citing strategy/execution failures.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- Consensus posture confirms the weakness: a chronic GAAP-EPS miss history (FY2024 -9%, FY2025 -36%), a Hold rating, and revenue revisions running 0 up / 1 down last month.
  - ↳ `CIQ Estimates→Surprise (annual)`

### Twin reference cases
- **BellRing Brands** — recovered
  - distinguished by: Protein/nutritional-snacking pure-play that sustained category-tailwind growth and re-rated as branded high-protein demand mainstreamed.
  - source: [LLM-suggested, unverified]
- **Hain Celestial Group** — went terminal
  - distinguished by: Natural/better-for-you portfolio that suffered repeated brand impairments, distribution losses and management turnover after acquired brands underperformed.
  - source: [LLM-suggested, unverified]
- **Utz Brands** — recovered
  - distinguished by: Single-category branded-snack roll-up that worked through input-cost margin compression and leverage while protecting core brand velocity.
  - source: [LLM-suggested, unverified]
- **Tupperware Brands** — went terminal
  - distinguished by: Single-brand consumer franchise where a CEO return and turnaround framing could not arrest structural demand erosion.
  - source: [LLM-suggested, unverified]
- **WW International (Weight Watchers)** — went terminal
  - distinguished by: Weight-management brand whose core proposition was disrupted by the rise of GLP-1 drugs — directly relevant to the Atkins weight-loss positioning here.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the sub-floor de-rate an overshoot on a still-self-funding, category-tailwind franchise, or the early innings of a structural demand/margin decline that the guidance cut and brand impairment have only begun to price?**

### …evidence for
- Leverage screens far below peers (1.8 vs 3.4) and coverage is 12.3x, so the discount is not earned by balance-sheet risk and the name can self-fund a turnaround.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Management is acting on its overshoot view with 10%+ of shares repurchased in 12 months, signalling the price discounts the long-term opportunity.
  - ↳ `EDGAR XBRL shares, trailing 2024-06-24..2026-04-07`
- Forward LT EPS growth screens positive vs a negative peer median (3% vs -9%), posing the discount as potentially residual.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### …evidence against
- Guidance was cut to a 22–19% YoY adjusted EBITDA DECLINE with Q3 EBITDA guided down 38–32%, and a $249M brand impairment booked — management is confirming, not denying, deterioration.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- Demand is softening across all four brands with Atkins -23.4% and OWYN now facing lost distribution, amid a CEO change framed around strategy/execution failures.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- Trailing EV/EBITDA at the 0th percentile is trailing-only and cannot, by itself, separate overshoot from terminal — the cheapness is not self-validating.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`

### Key unknowns
- No forward adjusted EV/EBITDA or adjusted EPS in the revised 99.1 guidance — the adjusted (management-basis) valuation anchor the company itself guides on is MISSING, an opacity gap that blunts overshoot-vs-terminal adjudication.
- No revised-outlook 99.1 exhibit was parsed for the Q2 8-K, so the exact revised guidance text is unverified beyond the transcript figures.
- Segment EBITDA is UNKNOWN — single reported segment (100%) with no profitability split across Quest / Atkins / OWYN, so the market cannot see which brand carries the margin or whether the impaired brands are loss-making, a bearish disclosure gap.
- Net-debt/EBITDA on an ADJUSTED basis is UNKNOWN; the transcript cites ~1.2x adjusted vs 1.5x on the CIQ trailing basis — the leverage read differs by basis.
- No cohort / cross-section in graph_coverage, so the idiosyncratic-vs-shared read rests only on the name-vs-IWM relative, not a peer-group dispersion.
- Durability of the GLP-1 thesis is unresolved: management frames protein as a beneficiary, but the Atkins weight-loss core may be a structural casualty — the pilot study result is not quantified.
- Whether the Q2 takeaway slowdown (-6.4%) stabilises or accelerates into H2 is unknown; Q3 guide already implies a 14–11% sales decline.

## ⚠ Flags (human review)
- Net debt/EBITDA (1.5x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 1.5x as the covenant-basis leverage.
- UNTRACEABLE figure '460' in bear_point: 'The falling margin trend is now a GENUINE signal not just an optical…'
- TRANSCRIPT-FIGURE '-23.4' in bear_point: 'Demand is deteriorating across the portfolio per the latest call: Q2…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '32' in decisive.against: 'Guidance was cut to a 22–19% YoY adjusted EBITDA DECLINE with Q3…' — from the cited earnings call, not the structured facts; verify against the call
- DIRECTIONAL language 'conviction' — human review (dossier frames, not concludes)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (6 bull vs 8 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case
