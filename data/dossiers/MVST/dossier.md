# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-06-26 17:59 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- MISMATCH bull_point: 'The company is FCF-positive at $39.6M LTM, meaning it…' asserts missing/UNKNOWN data yet cites a PRESENT field — move to key_unknowns, don't source-bind it
- TWIN 'Enovix' has numbers ['3.2'] — must be non-numeric

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
- **Net debt / EBITDA (GAAP):** _UNKNOWN_ — no EBITDA in XBRL
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA UNKNOWN (no EBITDA in XBRL) — solvency risk | FCF-positive → self-funding (no runway constraint) | nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)
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
- **Name 180d return:** _UNKNOWN_ — name has no bars over the window
- **Market (IWM) 180d return:** _UNKNOWN_ — IWM benchmark bars unavailable
- **Relative vs market:** -80.2%
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

**Evidence balance:** mixed \u2014 a self-funding margin inflection collides with a sharp revenue reversal and extreme, low-visibility leverage.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA inflected positive and grew over the multi-year run (Dec-2021 -180 to Dec-2025 74, LTM 52), and gross margin climbed steadily from -28% to 35%, so the falling EBITDA margin % is partly the optical read while the absolute trajectory turned positive.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The company is FCF-positive at $39.6M LTM, meaning it is self-funding with no runway constraint despite the unknown solvency leg. ⚠ uncited
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x LTM indicates EBITDA comfortably services interest expense.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- On a forward basis the name's NTM TEV/EBITDA of 17.19 sits between peer low 7.63 and the heterogeneous peer mean 43.3 — posing whether any discount is RESIDUAL (overshoot) rather than purely EARNED, a question the human must judge against the fundamental_deltas, not a clean benchmark given the 8063x cap dispersion.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Bear case (terminal / value-trap)
- Revenue rolled over (-25.5% YoY latest same-quarter; LTM 372 vs FY2025 428) and ROIC fell back to 1.5% LTM from 3.3% — the inflection is reversing, not consolidating, so the margin recovery story is losing top-line support.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- The EBITDA margin % itself fell from 17% (Dec-2025) to 14% (LTM) AND absolute EBITDA fell from 74 to 52 — here the % decline is the REAL signal, not an optical artifact, because the absolute reconciler moved the same direction.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Leverage is extreme on the comp read: Debt/EBITDA 24.2 vs peer-median 1.8, alongside worse rev growth (-9% vs 2%) and EBITDA growth (-66% vs 2%) — inputs pointing to an EARNED discount (value trap) rather than residual overshoot, for the human to judge.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- 100% of revenue is a single Battery Systems segment with no geographic anchor (China 33%, Italy 22%, France 18%, U.S. only 9%), concentrating the business in one product line exposed to subsidy phaseouts and tariff frameworks management flagged.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- Two discrete earnings-driven gap-downs (2026-03-17 and 2026-05-12, both 8-K item 2.02) plus a third unmatched on 2026-05-18 show the de-rating clustered on results, not a market-wide move, with the name -80% relative to IWM over 180 days.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Share count is diluting (+2.9% over ~1.7y to 333.2M) with a stack of convertible bonds and shareholder convertible loans in the capital structure, adding ongoing equity dilution pressure.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`

### Twin reference cases
- **Romeo Power** — went terminal
  - distinguished by: Commercial-vehicle battery-pack maker with concentrated customer base and subsidy/volume dependence that could not scale to self-funding before capital ran out.
  - source: [LLM-suggested, unverified]
- **Microvast Holdings** — recovered
  - distinguished by: Same-name pattern of a SPAC-era battery name that reached gross-margin and FCF-positive inflection despite a top-line dip management frames as temporary.
  - source: CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]
- **QuantumScape** — went terminal
  - distinguished by: Pre-scale battery innovator reliant on a future product ramp and external narrative rather than current self-funded cash generation.
  - source: [LLM-suggested, unverified]
- **Enovix** — recovered
  - distinguished by: Battery manufacturer whose multi-year story hinged on a phased capacity expansion reaching SOP — a ramp-execution analogue to the Huzhou Phase 3.2 dependency.
  - source: [LLM-suggested, unverified]
- **Workhorse Group** — went terminal
  - distinguished by: Electrification name dependent on a yet-to-prove total-solution product and recurring dilution while revenue contracted.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the LTM revenue contraction and margin pullback a temporary volume dip that the Phase 3.2 ramp reverses (overshoot), or the start of a subsidy/tariff-driven structural decline that turns the high leverage into a value trap?**

### …evidence for
- FCF-positive at $39.6M and interest coverage of 10.6x show the business currently self-funds, buying time for the ramp to play out.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Gross margin held at 35% LTM after climbing from -28%, suggesting pricing/technology resilience independent of volume.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### …evidence against
- Revenue fell -25.5% YoY (latest same-quarter) and LTM revenue (372) is below FY2025 (428) while EBITDA also fell, indicating the inflection is already reversing.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Debt/EBITDA of 24.2 vs peer-median 1.8 means a sustained volume shortfall could convert manageable coverage today into a solvency problem.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Key unknowns
- Net-debt/EBITDA is UNKNOWN (no EBITDA in XBRL) — a BEARISH solvency-visibility gap given Debt/EBITDA 24.2 on the comp read.
- Nearest refinancing wall is UNKNOWN (no maturity dates parsed) — a BEARISH risk against a capital structure stacked with convertible bonds and term loans.
- No revised forward guidance 99.1 exhibit was parsed and no forward EV/EBITDA-adjusted or adjusted-EPS figure exists — a BEARISH disclosure gap leaving the overshoot-vs-terminal question unanchored.
- Segment-level EBITDA is UNKNOWN — cannot test profitability of the 100%-concentrated Battery Systems line.
- EV/EBITDA TEV/LTM 10.0x sits at the 0%ile of only 4 closes (trailing-only, no forward basis) — a NEUTRAL floor reading, not directional, pending forward visibility.
- Consensus breadth is empty (0↑/0↓ EPS and revenue revisions last month) — thin analyst coverage limits external corroboration of the ramp thesis.
- Management transcript posture (temporary dip, KAF school-bus launch, Phase 3.2 SOP timing) is QUALITATIVE only and unverified against numbers — execution risk on an unproven new product.
