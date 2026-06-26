# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-06-25 18:58 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- PEER-COMP-BARE bear_point: 'On a FORWARD basis the name is not cheap: NTM TEV/EBITDA 17.19 vs…' — presents cheap/rich vs peers as a verdict without the earned-vs-residual decomposition or the peer-set composition; POSE justified-vs-residual, never the bare gap
- HETEROGENEOUS-BENCHMARK bear_point: 'On a FORWARD basis the name is not cheap: NTM TEV/EBITDA 17.19 vs…' — leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every peer stat

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** _UNKNOWN_ — no positive EPS/price
- **P/E percentile (5y):** _UNKNOWN_ — no positive EPS/price
- **EV/EBITDA (GAAP TEV/LTM):** 10.0x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 4 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 10.0x at 0%ile of 4 closes → near-floor
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 39.6
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Margin trend:** EBITDA margin: Dec-31-2021 -118% → Dec-31-2022 (R) -68% → Dec-31-2023 (R) -28% → Dec-31-2024 1% → Dec-31-2025 17% → Mar-31-2026 (LTM) 14%; gross margin: Dec-31-2021 -28% → Dec-31-2022 (R) 4% → Dec-31-2023 (R) 19% → Dec-31-2024 31% → Dec-31-2025 36% → Mar-31-2026 (LTM) 35%; absolute EBITDA: Dec-31-2021 -180 → Dec-31-2022 (R) -140 → Dec-31-2023 (R) -85 → Dec-31-2024 5 → Dec-31-2025 74 → Mar-31-2026 (LTM) 52; absolute revenue: Dec-31-2021 152 → Dec-31-2022 (R) 204 → Dec-31-2023 (R) 307 → Dec-31-2024 380 → Dec-31-2025 428 → Mar-31-2026 (LTM) 372  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA (GAAP):** _UNKNOWN_ — EBITDA<=0 or missing debt/cash
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA UNKNOWN (EBITDA<=0 or missing debt/cash) — solvency risk | FCF-positive → self-funding (no runway constraint) | nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 10.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Share-count trend:** diluting (trailing ~1.7y): 323,815,298 (2024-08-05) → 333,157,384 (2026-05-04), +2.9%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`
- **Liquidity / covenant flags:** Convertible Bond - CNY (Bonds and Notes) 42 @ 3.000% - 4.000%; Convertible Loan With Shareholder - Delayed Draw Term Loan (Term Loans) 13 @ NA; Convertible Loan With Shareholder - Initial Term Loan (Term Loans) 12 @ NA; Loan Facilities Agreement With a Group of Lenders Led by a Bank in China (Term Loans) 43 @ NA; Long-term Loan Agreement With a Chinese Bank (Term Loans) 14 @ 2.700%; Notes Payable (Bonds and Notes) 78 @ NA; Operating Lease Liabilities (Capital Lease) 17 @ 5.000%; Short-term Loan Agreements and Bank Facilities With Chinese Banks (Term Loans) 50 @ 2.400% - 4.850%
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Dec-31-2021 152 → Dec-31-2022 (R) 204 → Dec-31-2023 (R) 307 → Dec-31-2024 380 → Dec-31-2025 428 → Mar-31-2026 (LTM) 372; EBITDA: Dec-31-2021 -180 → Dec-31-2022 (R) -140 → Dec-31-2023 (R) -85 → Dec-31-2024 5 → Dec-31-2025 74 → Mar-31-2026 (LTM) 52; Revenue YoY (latest same-quarter): -25.5% (Q1 Mar-31-2026 vs Q1 Mar-31-2024); ROIC: Dec-31-2021 -24.5% → Dec-31-2022 -12.3% → Dec-31-2023 -8.7% → Dec-31-2024 -2.2% → Dec-31-2025 3.3% → Mar-31-2026 (LTM) 1.5%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Batteries / Battery Systems 428 (100%) of Total 428
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Ashok Leyland Limited (NSEI:ASHOKLEY) — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K; BAIC BluePark New Energy Technology Co., Ltd. (SHSE:600733) — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Cargotec Solutions LLC — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Jbm Electric Vehicles Private Limited — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Kinglong United Automotive Industry (Suzhou) Co., Ltd — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; TREPEL Airport Equipment GmbH — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K
  - ↳ `CIQ Customers&Suppliers Microvast Holdings Inc NasdaqCM MVST Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] China 139 (33%); Other Asia & Pacific 3 (1%); Italy 93 (22%); France 78 (18%); Other Europe 41 (10%); U.S. 39 (9%); India 35 (8%) of Total 428
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 7 peers — Amprius Technologies $2.0B — develops, manufactures, and markets lithium-ion (United States); Forsee Power S.A. $34M — designs, manufactures, and sells battery systems for (France); Cummins Inc. $96.5B — offers various power solutions worldwide. The company (United States); BorgWarner Inc. $14.5B — provides technology solutions for combustion, hybrid, (United States); Contemporary Amperex Technology Co. $275.0B — engages in the research, development, production, and (China); Panasonic Holdings Corporation $64.4B — develops, manufactures, sells, services, and supplies (Japan); Leclanché SA $167M — designs, develops, and manufactures customized turnkey (Switzerland) | the name: $24.8B
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $34M–$275.0B (8063x); the name is $24.8B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 3.7 vs peers Low 0.7 / Median 3.2 / Mean 5.8 / High 22; TEV/EBITDA: name 38.4 vs peers Low 7.9 / Median 14.5 / Mean 18.5 / High 38.4; P/E: name NM vs peers Low 22.6 / Median 39 / Mean 38.9 / High 54.9; NTM TEV/Rev: name 3.07 vs peers Low 1.06 / Median 2.55 / Mean 3.64 / High 13.47; NTM TEV/EBITDA: name 17.19 vs peers Low 7.63 / Median 12.9 / Mean 43.3 / High 198.12; NTM P/E: name 55.1 vs peers Low 13.27 / Median 22.77 / Mean 26.23 / High 55.1  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 4% vs peer-median 9%; rev growth name -9% vs peer-median 2%; EBITDA growth name -66% vs peer-median 2%; Debt/EBITDA name 24.2 vs peer-median 1.8; LT EPS growth name – vs peer-median 18%; beta name 1.5 vs peer-median 1.1  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-03-17 earnings (2.02); 2026-05-12 earnings (2.02); 2026-05-18 no 8-K matched
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-03-17, 2026-05-12, 2026-05-18
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-03-17 → 2026-03-16 [`0001628280-26-018235`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026018235/mvst-20260316.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On March 16, 2026, Microvast Holdings, Inc. issued a press release announcing its consolidated financial results for the fourth quarter and year ended December 31, 2025. A copy of the press release and the slideshow is furnished herewith as Exhibit 99.1 and 99.2, respectively to this Current Report on Form 8-K and each is incorporated herein by refere
  - gap 2026-05-12 → 2026-05-11 [`0001628280-26-033601`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026033601/mvst-20260511.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On May 11, 2026, Microvast Holdings, Inc. (the “Company”) issued a press release announcing its unaudited condensed consolidated financial results for the period ended March 31, 2026. In addition, the Company posted an accompanying slideshow presentation to its website summarizing its results for the same period. The full text of the press release is 
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001628280-26-018235', '0001628280-26-033601']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -58.6%
  - ↳ `EOD MVST 180d to 2026-06-22`
- **Market (IWM) 180d return:** 17.8%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -76.4%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — MVST in graph but no US-listed exposed names to price

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $5.50 / median $5.50
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 +0%; Revenue surprise: FY2021 +3%, FY2022 +2%, FY2023 +3%, FY2024 +6%, FY2025 -8% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** Earnings-call transcript on file — read Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish \u2014 idiosyncratic -76% relative de-rate driven by a real revenue contraction against an order-of-magnitude worse leverage profile.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA has gone from -180 (2021) to +5 (2024) to +74 (2025), and gross margin from -28% to 35%, so the trailing margin %-dip is a story of a real fundamental turnaround, not deterioration — read the % beside the rising absolute.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The name is LTM free-cash-flow positive at +39.6, with a positive FCF sign, meaning operations are currently self-funding with no runway constraint on that leg.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage is 10.6x (EBITDA ÷ interest), indicating LTM earnings comfortably service the interest burden.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- TEV/LTM EBITDA sits at the 0th percentile of its trailing 4 closes (near its own-history floor), which the human must weigh against the turnaround — a possible overshoot if the de-rate has outrun the fundamentals.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 4 quarters (partial last column excluded from the distribution)`

### Bear case (terminal / value-trap)
- The Debt/EBITDA leverage gap is the load-bearing bear signal: name 24.2 vs peer-median 1.8 — an order-of-magnitude worse balance sheet that frames the discount as EARNED rather than residual.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Revenue is contracting hard — -25.5% YoY same-quarter (Q1 2026 vs Q1 2024) and LTM revenue of 372 has rolled back below the 428 FY2025 print — so the top-line ramp narrative is reversing, not the optical artifact of one weak month.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- fundamental_deltas show the discount is largely earned, not residual: rev growth name -9% vs peer-median 2%, EBITDA growth name -66% vs peer-median 2%, EBITDA margin name 4% vs peer-median 9% — worse on every fundamental.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- On a FORWARD basis the name is not cheap: NTM TEV/EBITDA 17.19 vs peer-median 12.9 and NTM P/E 55.1 at the very top of the peer range (High 55.1) — so the 'cheap' read rests only on the trailing multiple, not the forward.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- The drawdown is idiosyncratic, not a market move: name -58.6% over 180d while IWM was +17.8%, a -76.4% relative gap concentrated in discrete earnings gap-downs (2026-03-17, 2026-05-12).
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Both gap-downs trace to 2.02 results-of-operations 8-Ks, tying the de-rate directly to the financial results disclosed, not to a transient external event.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Revenue surprise turned to a -8% miss in FY2025 after years of beats, and the share count is diluting (+2.9% over ~1.7y), eroding per-share value.
  - ↳ `CIQ Estimates→Surprise (annual)`
- Consensus target price is mean/median $5.50 with zero up and zero down EPS or revenue revisions in the last month — no analyst breadth supporting an upgrade.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`

### Twin reference cases
- **Romeo Power** — went terminal
  - distinguished by: US-listed commercial-EV battery maker that de-SPAC'd, ramped revenue then hit volume/utilization shortfalls and customer concentration before failing.
  - source: [LLM-suggested, unverified]
- **Microvast (Plug Power analogue)** — recovered
  - distinguished by: Clean-energy hardware name with deep losses and dilution that survived multiple liquidity scares by repeatedly accessing capital while a turnaround story persisted.
  - source: [LLM-suggested, unverified]
- **Workhorse Group** — went terminal
  - distinguished by: Commercial-EV hardware story with a perennial 'next-product will transform the market' narrative against collapsing revenue and chronic dilution.
  - source: [LLM-suggested, unverified]
- **Enovix** — recovered
  - distinguished by: Battery-technology manufacturer whose valuation hinged on a capacity-ramp execution story that the market repeatedly re-rated on production milestones.
  - source: [LLM-suggested, unverified]
- **Microvast (Ballard analogue)** — went terminal
  - distinguished by: China-exposed clean-energy manufacturer whose end-market subsidy phaseout and geographic concentration eroded the demand base the growth thesis depended on.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the Q1 2026 revenue collapse (-48% YoY per management, -25.5% on the same-quarter facts basis) a TEMPORARY volume/Phase-3.2-timing dip that re-ramps, or the start of a STRUCTURAL demand erosion that makes the trailing turnaround a peak — given an order-of-magnitude worse leverage profile?**

### …evidence for
- Management frames the YoY dip as temporary and driven by Phase 3.2 ramp timing, expecting capacity to contribute to a continued revenue ramp through 2026.
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`
- Gross margin held at 35% LTM and absolute EBITDA remains positive (+52 LTM), so the cost structure has not broken even as volume fell.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- LTM free cash flow is positive (+39.6) and interest coverage is 10.6x, giving the business room to fund a re-ramp without immediate solvency pressure on those legs.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`

### …evidence against
- Same-quarter revenue is down -25.5% YoY and LTM revenue (372) has already fallen below FY2025 (428), evidence the decline is in the realized numbers, not just guidance.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Debt/EBITDA is 24.2 vs peer-median 1.8, so any prolonged revenue/EBITDA shortfall meets a balance sheet with very little cushion.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Both gap-downs were tied to 2.02 results 8-Ks and the FY2025 revenue surprise was a -8% miss — the market is pricing the results, not a transient.
  - ↳ `CIQ Estimates→Surprise (annual)`

### Key unknowns
- net-debt/EBITDA is UNKNOWN (EBITDA<=0 or missing debt/cash) and the nearest refinancing wall / maturity dates are UNPARSED — a solvency leg is opaque, a BEARISH gap not a neutral one, especially against the 24.2 Debt/EBITDA peer delta.
- No revised-outlook 99.1 exhibit was parsed for either gap-down 8-K — forward guidance is absent, leaving the re-ramp claim unquantified.
- Forward (NTM) adjusted EV/EBITDA and adjusted EPS are not in the revised guidance, so cheap-overshoot vs cheap-terminal CANNOT be resolved on a forward basis from the supplied facts.
- Segment EBITDA is unavailable (Segments sheet has no EBITDA section) — 100% Batteries revenue is disclosed but no profitability breakout to test where margin is earned.
- Peer set is HETEROGENEOUS (caps span $34M–$275.0B, 8063x) — every peer multiple and delta is confidence-gated, not a clean benchmark; treat the discount/premium reads with caution.
- EV/EBITDA 10.0x sits at its own-history 0th percentile but is trailing-only — the overshoot-vs-terminal direction of that floor is UNRESOLVED, not a bull or bear point.
- Transcript discloses an adjusted EBITDA swing to negative YTD per management, but no GAAP-reconciled forward adjusted figure exists in the structured facts to corroborate — management posture only.
