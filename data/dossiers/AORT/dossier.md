# Dossier — ARTIVION, INC. (AORT)

_Finalist rank 9 · ref 2026-06-22 · assembled 2026-06-29 16:09 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS 0.21 vs recent median -0.54; verify against normalized/forward EPS (CIQ)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (2.8x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 2.8x as the covenant-basis leverage.
- TRANSCRIPT-FIGURE '-6.8' in bull_point: 'Management reports Q1 2026 constant-currency revenue growth of 12%…' — from the cited earnings call, not the structured facts; verify against the call

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
- **Relative vs market:** -68.3%
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

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — a differentiated, deleveraging double-digit grower de-rated on a discrete guidance-miss, but revised guidance and adjusted-basis valuation are missing.

### Bull case (overshoot / mean-revert)
- The trailing P/E of 112x and 91.4x LTM EPS is a distorted optic — trailing EPS of 0.21 is anomalous vs a recent median of -0.54, so the headline multiple is not a clean read of the business.
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- Absolute EBITDA is rising sharply even as the margin % looks low — FY2025 GAAP EBITDA prints reach 63 and 56 on revenue scaling to 441, so the falling-margin optic masks growing absolute profitability.
  - ↳ `EDGAR XBRL companyfacts OperatingIncomeLoss+D&A ÷ RevenueFromContractWithCustomerExcludingAssessedTax [FY2018–FY2025]`
- On the forward NTM basis the name's TEV/EBITDA of 12.8x sits below the peer median of 17.59x — but the peer set is heterogeneous (caps span $39M–$66.1B), so whether this is an EARNED discount or a RESIDUAL overshoot is the human's call, not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- Fundamentals run AHEAD of peers on growth — rev growth 18% vs peer-median 14% and EBITDA growth 42% vs peer-median 21% with margin matching at 13% — posing whether any discount is RESIDUAL rather than EARNED, though the name is EDGAR-GAAP basis vs peers on CIQ basis so a delta may be definitional.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The business is self-funding — FY2025 FCF positive and net-debt/EBITDA at 2.8x with no runway constraint flagged.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Management reports Q1 2026 constant-currency revenue growth of 12% and adjusted EBITDA growth of 26%, with net leverage falling to 1.8 from 4.0 year-over-year and Q1 FCF improving to -6.8M from -20.6M — a deleveraging, improving-cash trajectory.
  - ↳ `CIQ transcript(s): Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf`
- Consensus mean target price is $42.00 / median $43.00, well above the implied current level given the -57% 180d return.
  - ↳ `CIQ Estimates→Consensus`
- The drawdown is tied to a discrete dual-catalyst 8-K (material agreement 1.01 + Q1 earnings 2.02) — the Endospan option exercise plus a guidance-miss quarter, an event-driven gap rather than a slow secular bleed.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`

### Bear case (terminal / value-trap)
- Q1 2026 stent-graft growth fell below management's own constant-currency expectations, driven by lower-than-expected U.S. AMDS set sales and softer international (notably Middle East) performance — a genuine demand-miss against guidance, OUTWEIGHED by the overall 12% cc revenue / 26% adj-EBITDA growth and 1.8x deleveraging management reported the same quarter.
  - ↳ `CIQ transcript(s): Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf`
- Share count is diluting +15.9% over a trailing ~1.7 years (41.9M → 48.5M), a genuine per-share headwind, OUTWEIGHED by the rising absolute EBITDA and deleveraging trajectory that the dilution partly funded.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`
- EPS revision breadth is negative (0 up / 2 down last month for FY2026 GAAP) — a genuine soft signal, OUTWEIGHED by flat revenue-revision breadth (0/0) and the consensus $42 mean target still standing.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- GAAP-EPS missed by -9% in FY2025, breaking a multi-year run of in-line prints — a genuine execution wobble, OUTWEIGHED by essentially in-line revenue surprises (-0% FY2025) indicating top-line was not the source of the miss.
  - ↳ `CIQ Estimates→Surprise (annual)`

### Twin reference cases
- **Inari Medical** — recovered
  - distinguished by: Single-product medical-device grower that sold off on a guidance/adoption-pace scare, then re-rated as procedure-volume reorder patterns proved the adoption thesis intact.
  - source: [LLM-suggested, unverified]
- **Shockwave Medical** — recovered
  - distinguished by: Differentiated cardiovascular-device platform whose launch-quarter stocking-vs-reorder noise masked a durable adoption curve that later compounded.
  - source: [LLM-suggested, unverified]
- **CryoLife (predecessor to this name)** — recovered
  - distinguished by: Same corporate lineage; an acquisitive aortic/tissue franchise that absorbed integration and leverage cycles before the strategy compounded.
  - source: [LLM-suggested, unverified]
- **NovaBay / small-cap single-catalyst med-device** — went terminal
  - distinguished by: Sub-scale device name where dilution outran adoption and the reorder thesis never materialised into self-funding cash generation.
  - source: [LLM-suggested, unverified]
- **Penumbra** — recovered
  - distinguished by: High-multiple device innovator that absorbed a sharp single-quarter setback then resumed share-gain-driven growth as the differentiated portfolio matured.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the sharp de-rate an event-driven overshoot on a still-compounding, deleveraging aortic-device franchise, or the start of an adoption-pace/dilution value trap where AMDS/NEXUS uptake disappoints against the inventory and dilution already booked?**

### …evidence for
- Management frames the AMDS stocking shortfall as timing — strong reorder patterns within existing accounts, an imminent PMA removing the IRB barrier, and accounts already through the VAC process — alongside 12% cc growth and net leverage cut to 1.8x.
  - ↳ `CIQ transcript(s): Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf`
- Forward NTM TEV/EBITDA of 12.8x sits below the peer median of 17.59x while EBITDA growth (42%) runs roughly double the peer median (21%).
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### …evidence against
- The same quarter delivered a stent-graft miss against management's own expectation on both U.S. AMDS sets and international demand, and EPS revisions skewed down (0 up / 2 down).
  - ↳ `CIQ transcript(s): Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf`
- Share count has diluted +15.9% in ~1.7 years, compounding the per-share cost of any adoption delay.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`

### Key unknowns
- Revised FY2026 guidance is UNKNOWN — no 99.1 revised-outlook exhibit was parsed for the 8-K despite the earnings event; absence of a re-based forward guide after a guidance-miss quarter is a BEARISH opacity, not neutral.
- Adjusted EV/EBITDA (fwd) and adjusted EPS are UNKNOWN — the adjusted figures management speaks to are not in the parsed 99.1, so the cleanest forward valuation leg cannot be built.
- Adjusted net-debt/EBITDA is UNKNOWN; the GAAP 2.8x screen vs management's stated 1.8x net-leverage cannot be reconciled from the facts, and the net-debt screen is flagged as possibly under-capturing scattered debt.
- Interest coverage is UNKNOWN (income statement missing EBITDA or interest-expense row) — a debt-servicing blind spot given 8.41% secured term debt and a $190M facility due 2031.
- Segment and geographic revenue/EBITDA breakouts are UNKNOWN (Segments sheet has no Revenues/EBITDA/Geographic sections) — concentration in stent grafts vs On-X vs tissue cannot be sized; a BEARISH disclosure gap.
- Endospan acquisition economics, financing terms and dilution/closing impact are not quantified in the facts beyond the option-exercise narrative — integration and cash-deployment risk is unsized.
- EV/EBITDA TEV/LTM 18.4x sits at the 0th percentile of its own 20-quarter history (near-floor) but is trailing-only with no forward basis — overshoot-vs-terminal is unresolved and belongs here, not in either directional case.
- No graph cohort exists for the name (not in graph_coverage.json) — the -68% relative-to-market move cannot be triangulated against a peer cross-section.
