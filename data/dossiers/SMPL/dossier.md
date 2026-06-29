# Dossier — Simply Good Foods Co (SMPL)

_Finalist rank 12 · ref 2026-06-22 · assembled 2026-06-29 16:17 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (1.5x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 1.5x as the covenant-basis leverage.
- TRANSCRIPT-FIGURE '32' in bear_point: 'The cut is guided forward, not just trailing: management lowered…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '213.3' in bear_point: 'A $249M non-cash impairment was taken against the OWYN and Atkins…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '159.7' in bear_point: 'A $249M non-cash impairment was taken against the OWYN and Atkins…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '23.4' in bear_point: 'The deterioration is broad across the portfolio: Atkins consumption…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '-32' in decisive.against: 'The FY2026 adjusted-EBITDA guide of $217–225M is a 22%-to-19% YoY…' — from the cited earnings call, not the structured facts; verify against the call
- UNTRACEABLE figure '23.4' in decisive.against: 'Atkins consumption fell 23.4% on distribution losses and OWYN turned…'
- TWIN 'Medifast' has numbers ['1'] — must be non-numeric
- TWIN 'WW International (Weight Watchers)' has numbers ['1'] — must be non-numeric

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
- **Relative vs market:** -53.9%
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

**Evidence balance:** mixed — a self-funding, FCF-positive balance sheet and floor-level trailing multiple against a guided ~20% forward EBITDA decline, brand impairment, and broad-portfolio deterioration.

### Bull case (overshoot / mean-revert)
- EV/EBITDA sits at 6.0x and at the 0th percentile of 20 trailing quarterly closes, a near-floor on its own history, while P/E sits at the ~4th percentile of its 5-year range.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- The business is FCF-positive at $125.5M LTM with net-debt/EBITDA of 1.5x, interest coverage of 12.3x, and no maturity wall until 2029 — self-funding with no runway constraint, so the de-rate is not a solvency event.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Management is buying back stock aggressively into the de-rate — share count fell 9.6% over ~1.8 years and over 10% of shares were repurchased in the trailing 12 months — signalling that management itself reads the price as discounting the long-term opportunity.
  - ↳ `EDGAR XBRL shares, trailing 2024-06-24..2026-04-07`
- On the fundamental_deltas the name screens better than the heterogeneous peer median on margin (17% vs 14%), leverage (Debt/EBITDA 1.8 vs 3.4), LT EPS growth (3% vs -9%) and beta (0.2 vs 0.4); whether the discount to peers is EARNED or RESIDUAL is for the human to judge — not computed here.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The drawdown shape is a discrete earnings gap-down (8-K item 2.02 on consecutive days), not a structural or distressed-filing pattern — consistent with a guidance-reset overshoot rather than terminal impairment of the franchise.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`

### Bear case (terminal / value-trap)
- The cut is guided forward, not just trailing: management lowered FY2026 to $217–225M adjusted EBITDA (a year-over-year decline of 22% to 19%) with Q3 EBITDA guided down 38% to 32%, so the cheap trailing multiple sits atop a falling forward base — a value-trap risk.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- The EBITDA margin % decline (20%→17% LTM) is corroborated by absolute EBITDA actually FALLING in the most recent LTM (262 → 236) and revenue rolling over (1,451 → 1,416) — so the margin compression is the REAL signal here, not an optical %-only artifact, since the reconciler moves the same direction.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- A $249M non-cash impairment was taken against the OWYN and Atkins brand assets, producing a Q2 GAAP operating loss of $213.3M and net loss of $159.7M — a write-down of two of the three brands' carrying value.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- GAAP-EPS surprises have been chronically negative (FY2021 -42%, FY2024 -9%, FY2025 -36%), and FY2026 Q1 guidance was reaffirmed in January then sharply cut in April — a pattern of management estimates running ahead of delivery.
  - ↳ `CIQ Estimates→Surprise (annual)`
- The deterioration is broad across the portfolio: Atkins consumption down 23.4% on distribution losses, OWYN down 2.4% with further lost distribution coming, and Quest Bars softening — with a CEO change (Tanner out, Scalzo back) mid-de-rate underscoring execution failure.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- The stock fell 40% over 180 days while the IWM small-cap benchmark rose 18%, a 54-point relative underperformance — the drawdown is idiosyncratic to the name, not a market-wide move.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Twin reference cases
- **Medifast** — went terminal
  - distinguished by: Weight-management/nutrition brand whose demand structurally eroded as GLP-1 drugs reshaped the category; an instructive analogue for the Atkins distribution-loss and GLP-1 overhang.
  - source: [LLM-suggested, unverified]
- **BellRing Brands** — recovered
  - distinguished by: A focused high-protein nutritional-shake brand that rode the same category tailwind to durable growth; the bull-case picture of what Quest/OWYN done right looks like.
  - source: [LLM-suggested, unverified]
- **Tupperware Brands** — went terminal
  - distinguished by: A levered single-category consumer brand where a self-funding story unraveled as core demand and execution failed despite buybacks earlier on.
  - source: [LLM-suggested, unverified]
- **Central Garden & Pet** — recovered
  - distinguished by: A branded consumer-staples roll-up that absorbed input-cost and margin compression, then rebuilt margin through productivity programs — the bull pathway management is invoking.
  - source: [LLM-suggested, unverified]
- **WW International (Weight Watchers)** — went terminal
  - distinguished by: Weight-loss brand whose value proposition was disrupted by GLP-1 adoption and lost retail/consumer relevance — the terminal-read mirror to the GLP-1 thesis.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the FY2026 EBITDA guide-down a one-time reset of an over-promised plan that a returning CEO can stabilize via productivity and Quest/OWYN distribution gains (overshoot), or the first leg of a structural demand erosion across all three brands worsened by GLP-1 (terminal)?**

### …evidence for
- Management frames the category as still growing with powerful protein/health tailwinds, predominantly branded with limited private label, and retailers still allocating space — with Quest household penetration up 200bp YoY and Salty growing 14% in Q2.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- A fixed-cost reduction initiative (~$15M one-time) plus locked-in favorable cocoa pricing flowing into late Q4/FY2027 and guided Q4 gross-margin expansion suggest a self-help margin-recovery path.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`

### …evidence against
- The FY2026 adjusted-EBITDA guide of $217–225M is a 22%-to-19% YoY decline with Q3 guided down 38%-32%, and the $249M impairment writes down OWYN and Atkins brand carrying value — a forward and structural deterioration, not a one-quarter blip.
  - ↳ `CIQ transcript(s): The Simply Good Foods Company, Q1 2026 Earnings Call, Jan 08, 2026.rtf; The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf`
- Atkins consumption fell 23.4% on distribution losses and OWYN turned negative with further distribution loss flagged, while absolute EBITDA and revenue both rolled over in the latest LTM — deterioration is reaching the formerly healthy parts of the portfolio.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### Key unknowns
- The revised-guidance 99.1 exhibit was not parsed (revised_guidance status: unknown) — the structured forward outlook beyond what the transcript states is absent; an OPACITY-as-bearish gap given the company just reset guidance.
- Forward EV/EBITDA on an ADJUSTED basis and adjusted EPS are UNKNOWN (not in the 99.1 revised guidance), so the trailing 6.0x cannot be confirmed against the now-lower forward base — the cheap-overshoot vs cheap-terminal distinction is unresolved on the company's own numbers.
- Adjusted net-debt/EBITDA is UNKNOWN; transcript cites ~1.2x while CIQ shows 1.5x — the leverage read shifts with the lower guided EBITDA denominator.
- Segment-level EBITDA is UNKNOWN (Segments sheet has no EBITDA section) and revenue is reported as a single 100% segment — no visibility into whether Quest profit offsets Atkins/OWYN losses, an opacity risk hiding intra-portfolio mix.
- No exposed cross-section cohort (idiosyncratic_vs_shared.cohort/read UNKNOWN) — only the name-vs-IWM relative read is available.
- Peer set is HETEROGENEOUS (caps $54M–$27.2B, 507x span); every peer multiple must be treated as confidence-gated, not a clean benchmark, before judging the discount as earned or residual.
- Durability of the GLP-1 effect on Atkins demand is unresolved — management casts it as a tailwind for protein/muscle-retention but also concedes a consumer segment is shifting to GLP-1 drugs.
