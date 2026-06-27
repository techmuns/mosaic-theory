# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-06-27 19:41 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (5 bull vs 9 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

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
- **Net debt / OCF (GAAP):** -1.5x
  - ↳ `EDGAR XBRL net-debt/OCF (screen data-record) — OCF basis, not EBITDA`
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
- **Name 180d return:** -58.1%
  - ↳ `EOD MVST 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -81.1%
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

**Evidence balance:** strongly-bearish — realized -25.5% revenue decline, negative adjusted EBITDA, and 24.2x leverage outweigh a temporary-ramp narrative and trailing positives.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA has swung from -180 in 2021 to positive 5 in 2024, 74 in 2025 and 52 LTM — the falling LTM margin % (17%→14%) is the optical read, not the real signal, since the multi-year turn from deep losses to positive EBITDA is genuine.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Gross margin held at 35% LTM and climbed every year from -28% (2021) to 36% (2025), a structural unit-economics improvement rather than a one-off.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The name is FCF-positive at +39.6 LTM, meaning it is self-funding with no runway constraint despite the de-rate.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x indicates EBITDA comfortably services interest, easing the solvency fear behind the drawdown.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- On the peer comp the name's discount must be tested as EARNED vs RESIDUAL, but the peer set is HETEROGENEOUS (caps span $34M–$275.0B, 8063x) so no single peer multiple is a clean benchmark — the human must judge whether the gap is overshoot.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`

### Bear case (terminal / value-trap)
- Revenue is rolling over — LTM 372 is below FY2025's 428, with Q1 same-quarter revenue down -25.5% YoY, so the top-line growth story has reversed.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- On the consensus comp the name's fundamentals are WORSE on every operating leg: EBITDA margin 4% vs peer-median 9%, rev growth -9% vs +2%, EBITDA growth -66% vs +2%, supporting an EARNED (value-trap) discount rather than an overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Debt/EBITDA of 24.2 vs peer-median 1.8 flags extreme leverage on the consensus comp, a load-bearing solvency concern.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The GAAP net profit driving the period was overwhelmingly a non-cash warrant/convertible fair-value swing of 63.8, with management itself stating adjusted EBITDA was NEGATIVE 5.5 vs positive 28.5 a year prior — the headline profitability is optical, the underlying adjusted result deteriorated.
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`
- Two discrete earnings-driven gap-downs (2026-03-17 and 2026-05-12, both 8-K item 2.02) show the de-rate was a direct reaction to reported results, not a market-wide move.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- The name fell -58.1% over 180 days while the small-cap market rose +18.0% (-81.1% relative), confirming the decline is idiosyncratic, not shared.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Revenue is 100% concentrated in a single Battery Systems segment, leaving no diversification cushion against the volume collapse.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- Consensus target price is $5.50 mean/median, an external low anchor with zero upward EPS or revenue revisions in the last month.
  - ↳ `CIQ Estimates→Consensus`
- Share count is diluting, +2.9% over a trailing ~1.7 years, eroding per-share value during the stress period.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`

### Twin reference cases
- **Romeo Power** — went terminal
  - distinguished by: Commercial-EV battery maker with thin customer base and a collapsing volume ramp despite a differentiated-tech narrative.
  - source: [LLM-suggested, unverified]
- **Microvast (SPAC-era cohort context)** — went terminal
  - distinguished by: Pre-revenue/early-revenue SPAC EV-supplier de-SPACs that diluted into a falling top line while promoting a next-gen product roadmap.
  - source: [LLM-suggested, unverified]
- **Plug Power** — recovered
  - distinguished by: Loss-making clean-energy hardware name that survived through repeated capital raises while pivoting to a new application vertical.
  - source: [LLM-suggested, unverified]
- **Enovix** — recovered
  - distinguished by: Battery-technology developer whose narrative hinged on bringing new manufacturing capacity online to an as-yet-unproven demand ramp.
  - source: [LLM-suggested, unverified]
- **Workhorse Group** — went terminal
  - distinguished by: Commercial electrification name leaning on a new flagship product launch to offset a sharply declining core revenue line.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the LTM revenue/volume collapse a temporary Phase-3.2 ramp gap that re-inflects as new capacity meets demand, or the onset of a terminal demand decline that turns the leverage and negative adjusted EBITDA into a solvency spiral?**

### …evidence for
- Management frames the YoY revenue dip as temporary and tied to Phase 3.2 capacity timing aligning with customer demand, expecting a continued ramp through 2026.
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`
- Absolute EBITDA and gross margin both inflected positive and held (LTM EBITDA 52, gross margin 35%), evidence the cost structure improved even as volume dropped.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- FCF-positive +39.6 means the business can self-fund through a ramp gap without a forced raise.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`

### …evidence against
- Same-quarter revenue fell -25.5% YoY and LTM revenue (372) is already below FY2025 (428), so the decline is realized, not hypothetical.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Management disclosed adjusted EBITDA turned NEGATIVE 5.5 from positive 28.5 a year earlier, showing underlying earnings power eroded as volumes fell.
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`
- Debt/EBITDA of 24.2 vs peer-median 1.8 means any prolonged shortfall compounds quickly against a heavy debt load.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Key unknowns
- Forward/adjusted EV/EBITDA and adjusted EPS are UNKNOWN — the revised 99.1 guidance was not parsed, so the trailing 10.0x cannot be tested against a forward basis (overshoot-vs-terminal unresolved).
- Nearest refinancing/maturity wall is UNKNOWN — no maturity dates parsed; a missing solvency disclosure against a heavy debt load is a BEARISH gap, not neutral.
- Net-debt/EBITDA is UNKNOWN (no EBITDA in XBRL) — a core solvency leg is missing; only an OCF-basis figure exists.
- Segment EBITDA is UNKNOWN — no profitability breakout beneath the 100%-battery revenue line, so the quality of the single segment's earnings is opaque.
- Revised guidance content is UNKNOWN — no forward outlook exhibit parsed for either gap-down 8-K, leaving the management ramp claim unverified by numbers.
- Whether the on-call adjusted-EBITDA-negative and warrant-driven GAAP-profit figures are sustained or one-off cannot be judged from supplied facts (transcript is qualitative only).
- China exposure (33% of revenue) plus China-bank and shareholder convertible facilities — refinancing terms and counterparty risk are not disclosed.
