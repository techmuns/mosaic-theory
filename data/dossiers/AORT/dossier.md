# Dossier — ARTIVION, INC. (AORT)

_Finalist rank 9 · ref 2026-06-22 · assembled 2026-06-25 18:18 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS 0.21 vs recent median -0.54; verify against normalized/forward EPS (CIQ)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (2.8x) is on consolidated GAAP EBITDA; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio). That non-GAAP reconciliation lives in the earnings release/transcript (currently UNAVAILABLE) — do not read 2.8x as the covenant-basis leverage.

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 98.1x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 1st %ile
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
- **Name 180d return:** -56.1%
  - ↳ `EOD AORT 180d to 2026-06-22`
- **Market (IWM) 180d return:** 17.8%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -73.8%
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

**Evidence balance:** mixed \u2014 idiosyncratic event-driven de-rate with rising absolute EBITDA, but above-peer leverage, heavy dilution and missing forward/segment disclosure leave the recovery unverified.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA has stepped up sharply on the latest FY2025 GAAP prints (29 → 63 → 56 $M) on rising revenue (354 → 389 → 441 $M), so the optically low single-digit margin % understates a business whose absolute earnings power is expanding.
  - ↳ `EDGAR XBRL companyfacts OperatingIncomeLoss+D&A ÷ RevenueFromContractWithCustomerExcludingAssessedTax [FY2018–FY2025]`
- The drawdown is idiosyncratic, not a sector wash-out: the name is down ~56% over 180d while the small-cap index (IWM) is up ~18%, a ~74-point relative gap that frames a single-name event rather than a macro tide.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Against the fundamental_deltas the discount is not obviously EARNED on growth or margin — rev growth 18% vs peer-median 14%, EBITDA growth 42% vs peer-median 21%, EBITDA margin 13% in-line at peer-median 13% — posing whether the peer gap is RESIDUAL (overshoot) rather than a value trap, though a GAAP-vs-CIQ basis caveat is flagged on the name's fundamentals.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The drawdown traces to a discrete dated 8-K event (Q1 earnings plus a material agreement / Endospan option exercise) rather than a creeping deterioration, consistent with a one-time repricing.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- The business self-funds: FY2025 FCF is positive and the survival read is FCF-positive with no runway constraint, removing the immediate solvency leg of a terminal thesis.
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- Management posture frames Q1 as a timing shortfall (AMDS starter-set stocking lower, reorder patterns within existing accounts encouraging, pending PMA) against an intact long-term growth strategy and a completed Aortic Arch portfolio — a qualitative tone of temporary miss, not structural break.
  - ↳ `CIQ transcript Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`

### Bear case (terminal / value-trap)
- A genuine counter-point: leverage screens worse than peers — Debt/EBITDA name 3.7 vs peer-median 2.1 (GAAP net-debt/EBITDA 2.8x) — a portion of the peer discount may be EARNED by the balance sheet, OUTWEIGHED by the idiosyncratic ~56% drawdown vs a +18% index and the rising absolute-EBITDA trajectory.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- A genuine counter-point: the share count is diluting +15.9% over ~1.7 years (41.9M → 48.5M), eroding per-share claims even as absolute EBITDA rises — OUTWEIGHED by the FCF-positive self-funding survival read and the absolute earnings step-up.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`
- A genuine counter-point: estimate breadth is negative — FY2026 GAAP EPS revisions 0 up / 2 down last month, and the latest FY2025 GAAP-EPS surprise was a 9% miss — OUTWEIGHED by the event-driven discrete repricing and management's timing-shortfall framing.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- A genuine counter-point: the trailing P/E is optically distorted at ~91x — but this is the MISREAD, not the signal: trailing EPS 0.21 is anomalous vs a recent median of -0.54, so the multiple is not a clean read and the percentile sits at its own ~5y floor.
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`

### Twin reference cases
- **Inspire Medical Systems** — recovered
  - distinguished by: Single-product med-device grower sold off on a quarter where stocking/launch timing disappointed, then re-rated as reorder/adoption momentum proved the miss temporary.
  - source: [LLM-suggested, unverified]
- **AngioDynamics** — went terminal
  - distinguished by: Med-device name where chronic margin pressure and dilution outran a portfolio-transformation narrative, leaving a low absolute earnings base that never inflected.
  - source: [LLM-suggested, unverified]
- **Tandem Diabetes Care** — recovered
  - distinguished by: Device maker that gapped down on a launch/inventory-timing quarter but whose underlying installed-base reorder dynamics reasserted growth.
  - source: [LLM-suggested, unverified]
- **Accuray** — went terminal
  - distinguished by: Capital-intensive device firm that grew revenue yet never converted scale into durable FCF, with leverage and a thin earnings base capping any re-rate.
  - source: [LLM-suggested, unverified]
- **Penumbra** — recovered
  - distinguished by: High-beta med-device grower punished hard on a single guidance/timing reset, then recovered as the differentiated portfolio kept taking share.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the post-event de-rate a temporary repricing of an AMDS/stent-graft stocking-and-timing miss in a business whose absolute EBITDA is genuinely inflecting upward, or does the dilution-plus-leverage profile mean the per-share/balance-sheet reality justifies the discount as EARNED?**

### …evidence for
- Latest FY2025 absolute EBITDA stepped to 63 then 56 $M on revenue rising to 389 then 441 $M, a real expansion in earnings power behind a low optical margin %.
  - ↳ `EDGAR XBRL companyfacts OperatingIncomeLoss+D&A ÷ RevenueFromContractWithCustomerExcludingAssessedTax [FY2018–FY2025]`
- Forward (NTM) peer multiples sit below the name's trailing prints — NTM TEV/EBITDA name 12.8 vs LTM 18.4 and below peer-median 17.59 — consistent with consensus modelling earnings recovery.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- On rev growth (18% vs 14%) and EBITDA growth (42% vs 21%) the name screens ahead of peers, so the discount is not obviously earned on growth.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### …evidence against
- Leverage runs above peers — Debt/EBITDA 3.7 vs peer-median 2.1 — a real fundamental that can justify part of the discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Share count diluted +15.9% over ~1.7 years, so absolute EBITDA gains accrue to a wider base.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`
- FY2026 GAAP EPS revision breadth is negative (0 up / 2 down) with a recent 9% GAAP-EPS miss, pressure on the recovery view.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`

### Key unknowns
- Adjusted/forward EV/EBITDA and adjusted EPS are UNKNOWN — not in the 99.1 revised guidance — so the cheap-overshoot vs cheap-terminal question cannot be settled on a forward earnings basis (the trailing EV/EBITDA at 0%ile of its own history is a neutral, unresolved fact, not a directional one).
- Revised FY2026 guidance is UNKNOWN — no revised-outlook 99.1 exhibit parsed — a missing forward guide post-miss; treat as a BEARISH opacity risk, not a neutral gap.
- Segment, segment-EBITDA and geographic breakouts are all UNKNOWN (Segments sheet missing the expected sections) — a missing expected disclosure that masks where the AMDS/stent-graft miss concentrates; surface as a BEARISH opacity risk.
- The nearest refinancing/maturity wall is UNKNOWN (no maturity dates parsed) while a Secured Term Loan of ~190 @ 8.41% and a Revolver of ~30 @ 7.16% sit in the structure — an unresolved survival-capacity leg, BEARISH until dated.
- Interest coverage is UNKNOWN (Income Statement missing EBITDA or Interest Expense row), leaving the debt-service cushion unquantified.
- Name fundamentals are EDGAR-GAAP basis while peers are CIQ basis — deltas (esp. margin/leverage) may be definitional rather than real, so every peer-comp lean is confidence-gated.
- Peer set is HETEROGENEOUS (caps span $39M–$66.1B, 1682x) — the peer median is not a clean benchmark and no peer multiple should be read as one.
- The Endospan option-exercise/acquisition terms, financing impact and dilution/leverage consequences are not quantified in the supplied facts — the transcript is a pointer only.
