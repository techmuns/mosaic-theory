# Dossier — ARTIVION, INC. (AORT)

_Finalist rank 9 · ref 2026-06-22 · assembled 2026-06-30 08:47 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 112.4x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 3rd %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 18.4x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 18.4x at 0%ile of 20 closes → near-floor; P/LTM EPS 91.4x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 0.8
  - ↳ `EDGAR XBRL companyfacts NetCashProvidedByUsedInOperatingActivities − PaymentsToAcquirePropertyPlantAndEquipment [FY2025] ($M)`
- **Margin trend:** EBITDA margin: FY2018 17% → FY2019 9% → FY2020 10% → FY2021 13% → FY2022 9% → FY2023 11% → FY2024 9% → FY2025 8% → FY2025 16% → FY2025 13%; absolute EBITDA: FY2011 19 → FY2012 14 → FY2013 17 → FY2014 18 → FY2015 20 → FY2016 15 → FY2017 11 → FY2018 30 → FY2019 18 → FY2020 27 → FY2021 35 → FY2022 23 → FY2023 32 → FY2024 29 → FY2025 29 → FY2025 63 → FY2025 56; absolute revenue: FY2018 180 → FY2019 190 → FY2020 263 → FY2021 276 → FY2022 253 → FY2023 299 → FY2024 314 → FY2025 354 → FY2025 389 → FY2025 441  [EDGAR GAAP basis, $M; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `EDGAR XBRL companyfacts OperatingIncomeLoss+D&A ÷ RevenueFromContractWithCustomerExcludingAssessedTax [FY2018–FY2025]`
- **Net debt / EBITDA:** 2.8x
  - ↳ `EDGAR XBRL net-debt/EBITDA (screen data-record); breadth estimate — may under-capture scattered debt; pull CIQ`
- **Net debt / OCF:** 4.0x
  - ↳ `EDGAR XBRL net-debt/OCF (screen data-record) — OCF basis, not EBITDA; breadth estimate — may under-capture scattered debt; pull CIQ`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 2.8x (CIQ) | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2025
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** _UNKNOWN_ — Income Statement missing EBITDA or Interest Expense row
- **Share-count trend:** diluting (trailing ~1.7y): 41,893,465 (2024-08-02) → 48,543,350 (2026-05-01), +15.9%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`
- **Liquidity / covenant flags:** 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank (Term Loans) undrawn/– @ 1.400%; Convertible Senior Notes (Bonds and Notes) undrawn/– @ 4.250% Due 2025; Finance Lease Obligation (Capital Lease) 3 @ 2.400%; New Delayed Draw Term Loan Facility (Term Loans) undrawn/– @ NA Due 2031; Notes Payable (Bonds and Notes) 1 @ 6.050% Due 2026; Operating Lease Liabilities (Capital Lease) 39 @ 5.900%; Secured Revolving Credit Facility (Revolving Credit) 30 @ 7.160% Due 2031; Secured Term Loan Facility (Term Loans) 190 @ 8.410% Due 2031
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: FY2018 180 → FY2019 190 → FY2020 263 → FY2021 276 → FY2022 253 → FY2023 299 → FY2024 314 → FY2025 354 → FY2025 389 → FY2025 441; EBITDA: FY2011 19 → FY2012 14 → FY2013 17 → FY2014 18 → FY2015 20 → FY2016 15 → FY2017 11 → FY2018 30 → FY2019 18 → FY2020 27 → FY2021 35 → FY2022 23 → FY2023 32 → FY2024 29 → FY2025 29 → FY2025 63 → FY2025 56; FCF: FY2011 15 → FY2012 19 → FY2012 14 → FY2012 16 → FY2017 8 → FY2018 14 → FY2019 4 → FY2020 4 → FY2021 8 → FY2022 5 → FY2023 -16 → FY2024 -16 → FY2025 9 → FY2025 11 → FY2025 1  [EDGAR XBRL GAAP basis, $M; per-period values, never YoY'd]
  - ↳ `EDGAR XBRL companyfacts revenue / operating_income+D&A / operating_cash_flow−capex (annual)`

### Concentration
- **Segments (revenue share):** _UNKNOWN_ — Segments sheet has no 'Revenues' section as expected
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Artivion, Inc. (NYSE:AORT) — Endospan Ltd. · Distributor · src: Health Care Equipment; Baxter International Inc. (NYSE:BAX) — Artivion, Inc. (NYSE:AORT) · Customer · src: Health Care Equipment; Endospan Ltd. — Artivion, Inc. (NYSE:AORT) · Borrower · src: Health Care Equipment; Japan Lifeline Co., Ltd. (TSE:7575) — Endospan Ltd. · Distributor · src: Health Care Equipment
  - ↳ `CIQ Customers&Suppliers Artivion Inc NYSE AORT Customers.rtf`
- **Geographic:** _UNKNOWN_ — Segments sheet has no 'Geographic Segment' section

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — AtriCure $1.4B — engages in the development, manufacture, and sale of (United States); LeMaitre Vascular $2.1B — develops, manufactures, and markets medical devices (United States); Edwards Lifesciences Corporation $51.6B — provides products and technologies to treat advanced (United States); AngioDynamics $540M — designs, manufactures, and sells medical, surgical, (United States); Japan Lifeline Co. $547M — engages in manufacturing and sale of medical device in (Japan); Boston Scientific Corporation $66.1B — develops, manufactures, and markets medical devices (United States); CVRx $137M — engages in developing, manufacturing, and (United States); PROCEPT BioRobotics Corporation $1.2B — develops transformative solutions in urology in the (United States); Accuray Incorporated $39M — engages in the design, development, manufacture, and (United States); APT Medical Inc. $3.9B — engages in the research and development, production, (China) | the name: $1.1B
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $39M–$66.1B (1682x); the name is $1.1B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 2.8 vs peers Low 0.4 / Median 2.8 / Mean 3.9 / High 9.3; TEV/EBITDA: name 18.4 vs peers Low 5.7 / Median 24.5 / Mean 59.9 / High 288.9; P/E: name 91.4 vs peers Low 9.5 / Median 30.7 / Mean 28.3 / High 48.6; NTM TEV/Rev: name 2.54 vs peers Low 0.45 / Median 2.31 / Mean 3.43 / High 7.33; NTM TEV/EBITDA: name 12.8 vs peers Low 5.77 / Median 17.59 / Mean 22.96 / High 74.4; NTM P/E: name 161.63 vs peers Low 10.13 / Median 26.73 / Mean 59.98 / High 253.41  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 13% vs peer-median 13%; rev growth name 18% vs peer-median 14%; EBITDA growth name 42% vs peer-median 21%; Debt/EBITDA name 3.7 vs peer-median 2.1; LT EPS growth name – vs peer-median 13%; beta name 1.3 vs peer-median 0.7  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]  [⚠ name fundamentals are EDGAR-GAAP basis (CIQ fundamentals empty) vs peers on CIQ basis — a delta may be definitional, not a real gap]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-05-08 material agreement (1.01) + earnings (2.02)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-05-08
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-05-08 → 2026-05-07 [`0001628280-26-032097`](https://www.sec.gov/Archives/edgar/data/784199/000162828026032097/aort-20260507.htm)
    - items: 1.01 Entry into a Material Definitive Agreement, 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 1.01 Entry into a Material Definitive Agreement: Entry into a Material Definitive Agreement. Securities Purchase Option Agreement As previously disclosed in connection with the announcement of the Exclusive Distribution Agreement, dated September 11, 2019, between JOTEC GmbH, a wholly owned subsidiary of Artivion, Inc., a Delaware corporation formerly known as CryoLife, Inc. (“Artivion”), and Endospan Ltd., an Israeli corporation (“Endospan”), a
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On May 7, 2026, Artivion issued a press release announcing its financial results for the first quarter ended March 31, 2026 and the exercise of the Option. Artivion hereby incorporates by reference herein the information set forth in its press release dated May 7, 2026, a copy of which is attached hereto as Exhibit 99.1. Except as otherwise provided i
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001628280-26-032097']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -57.1%
  - ↳ `EOD AORT 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -70.0%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — AORT not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/2↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $42.00 / median $43.00
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 +0%, FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 -9%; Revenue surprise: FY2021 +1%, FY2022 -0%, FY2023 +1%, FY2024 -1%, FY2025 -0% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf`

## Synthesis
_Not produced (see flags)._

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS 0.21 vs recent median -0.54; verify against normalized/forward EPS (CIQ)
- Net debt/EBITDA (2.8x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 2.8x as the covenant-basis leverage.
- LLM synthesis UNAVAILABLE — synthesis tool returned incomplete output — missing required field(s) ['bear_points'] (likely truncated)
