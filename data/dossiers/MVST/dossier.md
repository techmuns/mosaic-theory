# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-06-29 17:35 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- UNTRACEABLE figure '48' in bear_point: 'The revenue trajectory has rolled over: LTM revenue fell to 372 from…'
- UNTRACEABLE figure '536' in bear_point: 'The revenue trajectory has rolled over: LTM revenue fell to 372 from…'
- TRANSCRIPT-FIGURE '48.2' in bear_point: 'Management's own Q1 2026 disclosure shows YTD adjusted EBITDA swung…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '48' in decisive.for: 'Management attributes the Q1 2026 48% YoY revenue drop to a 'unique…' — from the cited earnings call, not the structured facts; verify against the call
- TWIN 'Microvast (analogue to itself via Korea/EMEA ramp-delay pattern)' has numbers ['3.2'] — must be non-numeric
- UNRECONCILED bear_point: 'The revenue trajectory has rolled over: LTM revenue fell to 372 from…' — cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (5 bull vs 8 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

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
- **Net debt / EBITDA:** 3.9x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ EBITDA $52M [LTM 12 months Mar-31-2026]`
- **Net debt / OCF:** 4.4x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ OCF $46M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 3.9x (CIQ) | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2026
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 10.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Share-count trend:** diluting (trailing ~1.7y): 323,815,298 (2024-08-05) → 333,157,384 (2026-05-04), +2.9%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`
- **Liquidity / covenant flags:** Convertible Bond - CNY (Bonds and Notes) 42 @ 3.000% - 4.000% Due 2027; Convertible Loan With Shareholder - Delayed Draw Term Loan (Term Loans) 13 @ NA Due 2026; Convertible Loan With Shareholder - Initial Term Loan (Term Loans) 12 @ NA Due 2026; Loan Facilities Agreement With a Group of Lenders Led by a Bank in China (Term Loans) 43 @ NA Due 2026; Long-term Loan Agreement With a Chinese Bank (Term Loans) 14 @ 2.700% Due 2027; Notes Payable (Bonds and Notes) 78 @ NA; Operating Lease Liabilities (Capital Lease) 17 @ 5.000%; Short-term Loan Agreements and Bank Facilities With Chinese Banks (Term Loans) 50 @ 2.400% - 4.850% Due 2027
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
- **Relative vs market:** -82.2%
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
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish — revenue and adjusted EBITDA rolled over with worse-than-peer fundamentals on every axis against a 2026 maturity wall.

### Bull case (overshoot / mean-revert)
- The multi-year trajectory shows a genuine operational turn: absolute EBITDA went from -180 (2021) to -85 (2023) to +5 (2024) to +74 (2025), with gross margin climbing from -28% to 36% — a structural inflection, not a single quarter.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The business is FCF-positive at +$39.6M LTM, removing the runway constraint that typically drives a battery-maker's terminal de-rating.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x indicates the LTM EBITDA comfortably services the debt load despite the leverage headline.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- Survival capacity is described as self-funding (no runway constraint) on net-debt/EBITDA 3.9x with FCF positive, a counter to the bankruptcy-thesis read.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- On TEV/Rev the name sits at 3.7 versus a HETEROGENEOUS peer median of 3.2 and on NTM TEV/EBITDA at 17.19 versus peer mean 43.3 — but with caps spanning $34M to $275.0B the human must judge whether any gap is EARNED by worse fundamentals (value trap) or RESIDUAL (overshoot), not read it as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Bear case (terminal / value-trap)
- The revenue trajectory has rolled over: LTM revenue fell to 372 from the 428 full-year-2025 peak, and Q1 2026 revenue dropped 48% YoY on volume falling from ~536 MWh to ~274 MWh — the absolute EBITDA also slipped from 74 (2025) to 52 (LTM), so this is a real deterioration, not just a falling margin %.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Management's own Q1 2026 disclosure shows YTD adjusted EBITDA swung to NEGATIVE $5.5M versus +$28.5M in the prior-year period — the GAAP net profit of $48.2M was driven by a $63.8M non-cash warrant/convertible fair-value change, not operations.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Fundamental deltas are uniformly worse than the peer median across every axis — EBITDA margin 4% vs 9%, revenue growth -9% vs +2%, EBITDA growth -66% vs +2%, Debt/EBITDA 24.2 vs 1.8, beta 1.5 vs 1.1 — pointing toward an EARNED discount (value trap) rather than a residual overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The capital structure is dominated by China-bank term loans and convertibles with a maturity wall in 2026 (multiple Term Loans Due 2026), against a self-funding posture that depends on EBITDA already shrinking.
  - ↳ `CIQ Financials→Capital Structure Details`
- The stock fell -58.1% over 180 days while the small-cap index rose +17.99%, an -82.2% relative underperformance — the de-rating is idiosyncratic, not a shared sector move.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Two discrete earnings gap-downs (2026-03-17 and 2026-05-12, both 2.02 Results of Operations 8-Ks) confirm the drawdown was driven by reported results, not noise.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Revenue surprise turned to -8% in FY2025 after years of beats, and the consensus target price sits at $5.50 mean/median — the estimate trend is no longer supportive.
  - ↳ `CIQ Estimates→Surprise (annual)`
- 100% of revenue is a single Batteries/Battery Systems segment, with no diversification cushion if commercial-EV battery demand stays soft.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`

### Twin reference cases
- **Romeo Power** — went terminal
  - distinguished by: Commercial-EV battery-systems maker that scaled revenue but could not hold operating cash flow as customer-platform ramps slipped, then ran out of independence.
  - source: [LLM-suggested, unverified]
- **Microvast (analogue to itself via Korea/EMEA ramp-delay pattern)** — recovered
  - distinguished by: A name whose top-line dip is framed by management as a temporary capacity/regulatory timing gap pending Phase 3.2 SOP rather than lost demand.
  - source: CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf
- **QuantumScape** — went terminal
  - distinguished by: Battery-technology story heavy on patents and solid-state milestones while commercial revenue and operating cash generation lagged the narrative.
  - source: [LLM-suggested, unverified]
- **Enovix** — recovered
  - distinguished by: Battery manufacturer that survived a sharp de-rate by bringing new cell capacity online and converting trial production into shipped volume.
  - source: [LLM-suggested, unverified]
- **Plug Power** — went terminal
  - distinguished by: Clean-energy hardware name reliant on subsidy-driven demand and serial dilution while leverage built against thin operating cash flow.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the LTM revenue/EBITDA roll-over a temporary Phase 3.2 ramp-and-regulatory timing gap that re-inflects in 2026, or the start of a demand-driven terminal decline that turns the leverage and single-segment concentration into a value trap?**

### …evidence for
- Management attributes the Q1 2026 48% YoY revenue drop to a 'unique set of challenges' it believes 'temporary,' with Phase 3.2 capacity expected to drive a continued revenue ramp through 2026 at SOP.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- The absolute EBITDA trajectory turned positive (5 in 2024, 74 in 2025) and gross margin held at 31.6% in Q1 2026 despite the volume collapse, consistent with a fixed-cost-absorption dip rather than pricing failure.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### …evidence against
- YTD adjusted EBITDA swung to -$5.5M from +$28.5M, and FY2025 revenue already missed (revenue surprise -8%) on Korea regulatory shifts and EMEA platform delays — the 'temporary' delays are recurring across quarters.
  - ↳ `CIQ Estimates→Surprise (annual)`
- Every fundamental delta is worse than the peer median including Debt/EBITDA 24.2 vs 1.8, which would convert a sustained EBITDA decline directly into a leverage problem at the 2026 maturity wall.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Key unknowns
- Revised forward guidance is UNKNOWN — no revised-outlook 99.1 exhibit was parsed for either gap-down 8-K, leaving the post-drawdown forward path undisclosed (a bearish opacity gap given the maturity wall).
- No forward/adjusted EV/EBITDA or adjusted EPS basis is available — the adjusted figures are absent from the 99.1 revised guidance, so the trailing 10.0x at the 0th percentile cannot be distinguished as cheap-overshoot vs cheap-terminal.
- Segment EBITDA is UNKNOWN — the Segments sheet has no EBITDA section, so profitability of the single 100% battery segment cannot be assessed.
- Net-debt/EBITDA on an adjusted basis is UNKNOWN; the reported 3.9x (CIQ) versus the peer-comp Debt/EBITDA of 24.2 is unreconciled and the human must resolve which leverage figure governs the 2026 maturity wall.
- Consensus breadth is empty (0 up / 0 down revisions, single $5.50 target) — analyst coverage may be too thin to confirm or refute the management ramp narrative.
- No cohort of US-listed exposed peers could be priced, so the idiosyncratic-vs-shared read rests only on name-vs-IWM.
