# Dossier — ARTIVION, INC. (AORT)

_Finalist rank 9 · ref 2026-06-22 · assembled 2026-06-26 18:04 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS 0.21 vs recent median -0.54; verify against normalized/forward EPS (CIQ)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (2.8x) is on consolidated GAAP EBITDA; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio). That non-GAAP reconciliation lives in the earnings release/transcript (currently UNAVAILABLE) — do not read 2.8x as the covenant-basis leverage.
- ANCHORS-ON-DISTORTED-P/E bull_point: 'The name's TEV/LTM EBITDA sits at the 0th percentile of 20 quarterly…' — the P/E is distorted (rests on a non-current/non-recurring EPS); don't read it as cheap

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 107.9x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 2nd %ile
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
- **Net debt / EBITDA (GAAP):** 2.8x
  - ↳ `EDGAR XBRL net-debt/EBITDA (screen data-record)`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 2.8x (GAAP) | FCF-positive → self-funding (no runway constraint) | nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** _UNKNOWN_ — Income Statement missing EBITDA or Interest Expense row
- **Share-count trend:** diluting (trailing ~1.7y): 41,893,465 (2024-08-02) → 48,543,350 (2026-05-01), +15.9%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`
- **Liquidity / covenant flags:** 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank (Term Loans) undrawn/– @ 1.400%; Convertible Senior Notes (Bonds and Notes) undrawn/– @ 4.250%; Finance Lease Obligation (Capital Lease) 3 @ 2.400%; New Delayed Draw Term Loan Facility (Term Loans) undrawn/– @ NA; Notes Payable (Bonds and Notes) 1 @ 6.050%; Operating Lease Liabilities (Capital Lease) 39 @ 5.900%; Secured Revolving Credit Facility (Revolving Credit) 30 @ 7.160%; Secured Term Loan Facility (Term Loans) 190 @ 8.410%
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
- **Name 180d return:** _UNKNOWN_ — name has no bars over the window
- **Market (IWM) 180d return:** _UNKNOWN_ — IWM benchmark bars unavailable
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
- **Earnings call:** Earnings-call transcript on file — read Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — an event-driven near-floor multiple with above-peer growth set against above-peer leverage, dilution, negative revisions and an opaque revised guide.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA has risen sharply on the latest FY2025 prints (to 63 then 56 from 29), and revenue stepped up to 441 — so the optically soft 8% margin coincides with rising, not falling, absolute EBITDA, which the consensus margin read misses.
  - ↳ `EDGAR XBRL companyfacts OperatingIncomeLoss+D&A ÷ RevenueFromContractWithCustomerExcludingAssessedTax [FY2018–FY2025]`
- The name's TEV/LTM EBITDA sits at the 0th percentile of 20 quarterly closes (near-floor at 18.4x), evidencing a sharp de-rate off its own history rather than steady erosion.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`
- On the forward basis the name's NTM TEV/EBITDA is 12.8 vs peer median 17.59 — a discount that the human must decompose as EARNED vs RESIDUAL, given the name's EBITDA growth 42% vs peer-median 21% and revenue growth 18% vs 14% run ahead of peers, though comparability is HETEROGENEOUS and the name's fundamentals are EDGAR-GAAP vs peers on CIQ basis so a delta may be definitional.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- The business is FCF-positive (FY2025 FCF +0.8M, positive sign) and self-funding with no runway constraint per survival capacity.
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- The drawdown is a discrete single gap-down (2026-05-08) tied to a material-agreement plus earnings 8-K — an event-driven re-rate, not a slow secular bleed.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`

### Bear case (terminal / value-trap)
- Trailing leverage at net-debt/EBITDA 2.8x (GAAP) sits above the peer-median Debt/EBITDA of 2.1, and on the comp sheet the name's 3.7 vs 2.1 marks it as more levered than peers — a genuine load-bearing risk.
  - ↳ `EDGAR XBRL net-debt/EBITDA (screen data-record)`
- Share count is diluting +15.9% over a trailing ~1.7y (41.9M to 48.5M shares), structurally pressuring per-share value — outweighed in the lean only if the Endospan deal and growth deliver, but a real signal now.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`
- The trailing P/E is optically distorted at ~108x (range note 91.4x) because trailing EPS 0.21 is anomalous vs a recent median of -0.54 — a misread, not a clean richness signal, but it flags fragile/erratic GAAP earnings beneath.
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- FY2026 GAAP EPS revision breadth is negative (0 up / 2 down last month) and the FY2025 GAAP-EPS surprise was -9%, indicating estimates are being cut into the print.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- The name has materially lagged the market, with a 180d relative return of -70% vs IWM — a deep, genuine underperformance.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Twin reference cases
- **Inari Medical** — recovered
  - distinguished by: Med-device single-category growth name de-rated on a soft quarter and decelerating new-account stocking, then re-rated as reorder/utilization patterns confirmed adoption.
  - source: [LLM-suggested, unverified]
- **Shockwave Medical** — recovered
  - distinguished by: Differentiated cardiovascular platform whose launch-phase set/stocking dynamics masked underlying procedure adoption until utilization compounded.
  - source: [LLM-suggested, unverified]
- **Nevro** — went terminal
  - distinguished by: Med-device grower that kept diluting and missing into negative estimate revisions while a single product franchise stalled, with no margin inflection arriving.
  - source: [LLM-suggested, unverified]
- **Establishment Labs** — went terminal
  - distinguished by: Levered single-vertical device maker reliant on distributor/international stocking that whipsawed on quarter-to-quarter ordering and dilution without de-leveraging.
  - source: [LLM-suggested, unverified]
- **AngioDynamics** — went terminal
  - distinguished by: Mid-cap vascular device peer that traded at depressed multiples for years as flat franchises and weak FCF kept it a value trap rather than an overshoot.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)

### Decisive question
**Is the depressed multiple a temporary overshoot off a launch-timing miss (RESIDUAL discount that mean-reverts as AMDS/On-X adoption and the Endospan/NEXUS portfolio compound), or an EARNED value-trap discount given above-peer leverage, persistent dilution and negative EPS revisions?**

### …evidence for
- NTM TEV/EBITDA 12.8 sits below peer median 17.59 while the name shows EBITDA growth 42% vs peer-median 21% and revenue growth 18% vs 14% — a possible residual/overshoot the human must adjudicate, gated by heterogeneous comparability and GAAP-vs-CIQ basis.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- TEV/LTM EBITDA at the 0th percentile of 20 closes with absolute EBITDA stepping up on the latest FY2025 prints frames the de-rate as event-driven rather than fundamental decay.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`

### …evidence against
- Above-peer leverage (name vs peer-median 3.7 vs 2.1; GAAP net-debt/EBITDA 2.8x) plus +15.9% dilution and 0-up/2-down EPS revisions are the hallmarks of an EARNED discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The peer set is HETEROGENEOUS (caps span $39M–$66.1B, 1682x) so the median is anchored by differing scale/model — every peer multiple is a confidence-gated input, not a clean benchmark for declaring an overshoot.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`

### Key unknowns
- Revised 2026 guidance: no revised-outlook 99.1 exhibit was parsed for the 8-K, so the forward guide is opaque — a BEARISH disclosure gap given the quarter missed CC expectations.
- Adjusted EPS, adjusted EV/EBITDA-fwd and adjusted net-debt/EBITDA are all UNKNOWN (not in the 99.1 revised guidance) — the management-favoured basis is unavailable, a BEARISH opacity.
- Interest coverage is UNKNOWN (Income Statement missing EBITDA or Interest Expense row) — coverage adequacy against the 8.41% term loan and 7.16% revolver cannot be assessed; a BEARISH gap.
- Nearest refinancing/maturity wall is UNKNOWN (no maturity dates parsed) — a survival-capacity leg left open, a BEARISH risk despite FCF-positive self-funding.
- Segment, segment-EBITDA and geographic breakouts are all UNKNOWN (Segments sheet missing sections) — concentration and product-line economics are not disclosed in the facts; a BEARISH opacity.
- Endospan acquisition terms, financing draw and closing certainty are not quantified in the source-bound facts beyond the transcript pointer — economics and incremental leverage unresolved.
- Idiosyncratic-vs-shared read is incomplete: name and market 180d absolute returns and the cohort cross-section are UNKNOWN; only the name-vs-market relative is available.
