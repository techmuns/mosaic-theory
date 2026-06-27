# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-06-27 18:48 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- MISMATCH bull_point: 'Interest coverage is 10.6x (EBITDA ÷ interest),…' asserts missing/UNKNOWN data yet cites a PRESENT field — move to key_unknowns, don't source-bind it
- MISMATCH bear_point: 'Debt/EBITDA at 24.2 (vs peer-median 1.8) signals an…' asserts missing/UNKNOWN data yet cites a PRESENT field — move to key_unknowns, don't source-bind it
- VERIFICATION-CLAIM bear_point: 'Revenue contracted -25.5% YoY (latest same-quarter) and LTM revenue…' — the dossier cites, it does not verify; confirm against the source (cited ≠ verified)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (4 bull vs 7 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case
- HETEROGENEOUS-BENCHMARK bear_point: 'On a forward basis the name screens RICH, not cheap: NTM P/E 55.1…' — leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every peer stat

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
- **Net debt / OCF (GAAP):** _UNKNOWN_ — not in snapshot (pre-OCF-leverage screen)
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

**Evidence balance:** strongly-bearish — sharper-than-peer revenue/EBITDA contraction, earned discount on every fundamental axis, rich forward multiples, and missing solvency/guidance disclosures.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA inflected from -180 in 2021 to +74 in 2025 and +52 LTM, with gross margin climbing from -28% to 35% — a genuine turnaround in unit economics, not just an optical margin-% read.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The name is FCF-positive (+$39.6M levered FCF LTM), meaning it is self-funding with no immediate runway constraint.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage is 10.6x (EBITDA ÷ interest), indicating servicing capacity on current debt despite an unknown leverage ratio. ⚠ uncited
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- ROIC turned positive in 2025 (3.3%) after years of deeply negative returns (-24.5% in 2021), evidencing a real operating-quality improvement.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Bear case (terminal / value-trap)
- Revenue contracted -25.5% YoY (latest same-quarter) and LTM revenue fell to 372 from 428 FY2025, with EBITDA slipping from 74 to 52 LTM — the absolute reconciler confirms this is a REAL deterioration in the top line and EBITDA, not merely a margin-% optical effect.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- On fundamentals the discount-to-peers looks EARNED rather than residual: name EBITDA margin 4% vs peer-median 9%, rev growth -9% vs +2%, EBITDA growth -66% vs +2%, and Debt/EBITDA 24.2 vs peer-median 1.8 — far worse on every axis, pointing to a value trap.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Debt/EBITDA at 24.2 (vs peer-median 1.8) signals an extreme leverage profile relative to comparables, even though the XBRL net-debt/EBITDA itself is unavailable. ⚠ uncited
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- On a forward basis the name screens RICH, not cheap: NTM P/E 55.1 sits at the peer HIGH (vs median 22.77) and NTM TEV/EBITDA 17.19 is above peer-median 12.9 — the forward read undercuts any overshoot thesis.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- The stock fell -58.1% over 180d while IWM rose +18.0%, an -80.2% relative underperformance driven by discrete earnings gap-downs (8-K item 2.02 on 2026-03-17 and 2026-05-12) — idiosyncratic, name-specific damage.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Two of three drawdowns trace to earnings results filings (item 2.02), confirming the de-rate is anchored to disclosed fundamentals rather than market-wide pressure.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Share count is diluting (+2.9% over ~1.7y to 333.2M), a persistent drag on per-share value.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`

### Twin reference cases
- **Romeo Power** — went terminal
  - distinguished by: US commercial-EV battery-systems maker with concentrated customer base and revenue that stalled before scale; cash burn and leverage overwhelmed a margin story.
  - source: [LLM-suggested, unverified]
- **Microvast Holdings (post-SPAC)** — went terminal
  - distinguished by: Same name's own SPAC-era de-rate pattern: heavy China manufacturing exposure, capacity-expansion capex ahead of demand, and subsidy/tariff sensitivity.
  - source: [LLM-suggested, unverified]
- **QuantumScape** — recovered
  - distinguished by: Pre-scale battery developer that sustained equity value on a patent/technology narrative and roadmap milestones despite weak current revenue.
  - source: [LLM-suggested, unverified]
- **Enovix** — recovered
  - distinguished by: Battery manufacturer whose story turned on a capacity-ramp (new-line SOP) executing on schedule into rising demand rather than slipping.
  - source: [LLM-suggested, unverified]
- **Lordstown Motors** — went terminal
  - distinguished by: US electrification name reliant on a future flagship program and partner-sourced components, where the gap between announced roadmap and shipped volume proved fatal.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the LTM revenue/EBITDA decline a temporary trough tied to the Phase 3.2 capacity ramp that reverses into 2026, or the start of a structural demand/subsidy-driven contraction against an already heavily-levered balance sheet?**

### …evidence for
- Management frames the Q1 revenue dip as temporary, tied to Phase 3.2 ramp timing aligning with customer demand and a continued revenue ramp expected through 2026.
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`
- Gross margin held at 35% LTM and absolute EBITDA remains positive (+52), showing the cost structure did not collapse with the volume drop.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### …evidence against
- Revenue fell -25.5% YoY (latest same-quarter) and EBITDA growth is -66% vs a +2% peer median, with rev growth -9% vs +2% — the contraction is sharper than peers experiencing the same sector.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Management cites subsidy phaseout, new tariff frameworks, and raw-material/logistics inflation as ongoing pressures on near-term profitability across the sector.
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`

### Key unknowns
- No revised forward guidance was parsed from either earnings 8-K (99.1 exhibit absent) — no forward revenue/EBITDA basis to test the overshoot-vs-terminal question. (BEARISH opacity: an expected disclosure is missing.)
- Net-debt/EBITDA and net-debt/OCF are UNKNOWN (no EBITDA in XBRL); against a peer-comp Debt/EBITDA of 24.2 this missing solvency leg is a bearish gap, not neutral.
- Nearest refinancing/maturity wall is UNKNOWN (no maturity dates parsed) despite a complex capital structure of Chinese bank term loans, convertible bonds, and shareholder convertible loans — a survival-capacity blind spot.
- Trailing TEV/LTM EBITDA of 10.0x sits at the 0%ile of only 4 closes (trailing-only, no forward basis) — neither bull nor bear; it cannot distinguish cheap-overshoot from cheap-terminal.
- Segment EBITDA is unavailable (Segments sheet has no EBITDA section); the 100%-batteries revenue concentration cannot be tested for profitability mix.
- Consensus breadth is empty (0↑/0↓ EPS and revenue revisions last month) and the only target ($5.50 mean/median) lacks a current price for context — thin analyst coverage.
- KAF powertrain / 290Ah pack and school-bus TAM are roadmap/aspirational per the transcript — no shipped-volume or order facts supplied to corroborate.
- Peer set is HETEROGENEOUS (caps $34M–$275.0B, 8063x span) — every peer multiple and delta is a confidence-gated input, not a clean benchmark; the earned-vs-residual judgment rests on a noisy comp.
