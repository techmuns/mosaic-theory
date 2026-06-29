# Dossier — GARTNER INC (IT)

_Finalist rank 8 · ref 2026-06-22 · assembled 2026-06-29 16:15 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (1.3x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 1.3x as the covenant-basis leverage.
- DIRECTIONAL language 'recommendation' — human review (dossier frames, not concludes)
- UNRECONCILED bear_point: 'Top-line growth has stalled into a decline — revenue YoY -1.5% (Q1…' — cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 14.0x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 1st %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 7.5x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 7.5x at 0%ile of 20 closes → near-floor; P/LTM EPS 13.0x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** _UNKNOWN_ — no OCF/capex
- **Free cash flow ($M):** 1064.2
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Margin trend:** EBITDA margin: Dec-31-2021 24% → Dec-31-2022 24% → Dec-31-2023 22% → Dec-31-2024 21% → Dec-31-2025 20% → Mar-31-2026 (LTM) 21%; gross margin: Dec-31-2021 69% → Dec-31-2022 69% → Dec-31-2023 68% → Dec-31-2024 68% → Dec-31-2025 68% → Mar-31-2026 (LTM) 69%; absolute EBITDA: Dec-31-2021 1,148 → Dec-31-2022 1,314 → Dec-31-2023 1,274 → Dec-31-2024 1,309 → Dec-31-2025 1,311 → Mar-31-2026 (LTM) 1,337; absolute revenue: Dec-31-2021 4,734 → Dec-31-2022 5,476 → Dec-31-2023 5,907 → Dec-31-2024 6,267 → Dec-31-2025 6,497 → Mar-31-2026 (LTM) 6,474  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA:** 1.3x
  - ↳ `CIQ Net Debt $1,688M [Q1 Mar-31-2026] ÷ CIQ EBITDA $1,337M [LTM 12 months Mar-31-2026]`
- **Net debt / OCF:** 1.2x
  - ↳ `CIQ Net Debt $1,688M [Q1 Mar-31-2026] ÷ CIQ OCF $1,368M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 1.3x (CIQ) | FCF sign UNKNOWN — runway not assessable (a risk) | nearest maturity wall: 2028
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 10.1x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Share-count trend:** buying back (trailing ~1.8y): 77,059,514 (2024-07-26) → 66,951,889 (2026-05-01), -13.1%
  - ↳ `EDGAR XBRL shares, trailing 2024-07-26..2026-05-01`
- **Liquidity / covenant flags:** 24 Credit Agreement - Revolving Credit Facility (Revolving Credit) undrawn/– @ 5.230% Due 2029; 3.625% Senior Notes Due 2029 (Bonds and Notes) 600 @ 3.625% Due 2029; 3.75% Senior Notes Due 2030 (Bonds and Notes) 800 @ 3.750% Due 2030; 4.50% Senior Notes Due 2028 (Bonds and Notes) 800 @ 4.500% Due 2028; 4.95% Senior Notes Due 2031 (Bonds and Notes) 350 @ 4.950% Due 2031; 5.60% Senior Notes Due 2035 (Bonds and Notes) 450 @ 5.600% Due 2035; Operating Lease Liabilities (Capital Lease) 366 @ 5.600%; State of Connecticut Economic Development Loan (Term Loans) 5 @ 1.750%
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Dec-31-2021 4,734 → Dec-31-2022 5,476 → Dec-31-2023 5,907 → Dec-31-2024 6,267 → Dec-31-2025 6,497 → Mar-31-2026 (LTM) 6,474; EBITDA: Dec-31-2021 1,148 → Dec-31-2022 1,314 → Dec-31-2023 1,274 → Dec-31-2024 1,309 → Dec-31-2025 1,311 → Mar-31-2026 (LTM) 1,337; Revenue YoY (latest same-quarter): -1.5% (Q1 Mar-31-2026 vs Q1 Mar-31-2025); ROIC: Dec-31-2021 15.7% → Dec-31-2022 20.6% → Dec-31-2023 19.8% → Dec-31-2024 18.2% → Dec-31-2025 18.6% → Mar-31-2026 (LTM) 19.4%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Conferences 645 (10%); Other 227 (4%); Insights 5,073 (78%); Consulting 552 (9%) of Total 6,497
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** JB Financial Group Co., Ltd. (KOSE:A175330) — Gartner, Inc. (NYSE:IT) · Client Services · src: Diversified Banks; Kafein Yazilim Hizmetleri Ticaret A.S. (IBSE:KFEIN) — Gartner Turkey Teknoloji Arastirma ve Danismanlik Hizmetleri Limited Sirketi · Client Services · src: IT Consulting and Other Services; PT Global Sukses Solusi Tbk (IDX:RUNS) — Gartner Ireland Ltd. · Customer · src: Systems Software; Qatar National Bank (Q.P.S.C.) (DSM:QNBK) — Gartner, Inc. (NYSE:IT) · Client Services · src: Diversified Banks; United States — Gartner, Inc. (NYSE:IT) · Customer · src: Diversified Support Services
  - ↳ `CIQ Customers&Suppliers Gartner Inc NYSE IT Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] United States and Canada 4,033 (62%); Europe, Middle East and Africa 1,694 (26%); Other International 771 (12%) of Total 6,497
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — Equifax Inc. $18.8B — operates as a data, analytics, and technology company. (United States); Moody's Corporation $78.6B — operates as an integrated risk assessment firm in the (United States); TransUnion $13.1B — operates as a global consumer credit reporting agency (United States); EPAM Systems $4.1B — provides digital platform engineering and software (United States); Verisk Analytics $23.6B — engages in the provision of data analytics and (United States); S&P Global Inc. $119.1B — provides benchmarks, data, analytics, and workflow (United States); FactSet Research Systems Inc. $7.9B — operates as a financial digital platform and (United States); Amdocs Limited $5.5B — provides software and services to communications, (United States); Everforth $751M — provides information technology solutions for (United States); Cognizant Technology Solutions Corporation $19.6B — provides consulting and technology, and outsourcing (United States) | the name: $8.7B
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $751M–$119.1B (159x); the name is $8.7B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 1.6 vs peers Low 0.5 / Median 3.8 / Mean 4.3 / High 10.7; TEV/EBITDA: name 7.5 vs peers Low 4.2 / Median 10.8 / Mean 11.1 / High 21.5; P/E: name 13 vs peers Low 8.1 / Median 16.4 / Mean 18.4 / High 32.3; NTM TEV/Rev: name 1.61 vs peers Low 0.54 / Median 3.48 / Mean 4.05 / High 10.1; NTM TEV/EBITDA: name 6.59 vs peers Low 3.45 / Median 9.66 / Mean 9.91 / High 19.21; NTM P/E: name 9.2 vs peers Low 4.96 / Median 12.76 / Mean 13.66 / High 26.3  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 21% vs peer-median 31%; rev growth name 2% vs peer-median 8%; EBITDA growth name 2% vs peer-median 7%; Debt/EBITDA name 2.4 vs peer-median 1.8; LT EPS growth name 14% vs peer-median 12%; beta name 0.9 vs peer-median 0.9  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-03 earnings (2.02) + Reg-FD (7.01)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-03
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-03 → 2026-02-03 [`0000749251-26-000028`](https://www.sec.gov/Archives/edgar/data/749251/000074925126000028/it-20260129.htm)
    - items: 2.02 Results of Operations and Financial Condition, 7.01 Regulation FD Disclosure, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: RESULTS OF OPERATIONS AND FINANCIAL CONDITION. On February 3, 2026, Gartner, Inc. (the “Company” or “Gartner”) announced financial results for the three months and year ended December 31, 2025. A copy of the Company’s Press Release is furnished herein as Exhibit 99.1. In accordance with General Instruction B.2 of Form 8-K, the information in this
    - 7.01 Regulation FD Disclosure: REGULATION FD DISCLOSURES. Financial Results Gartner has scheduled a webcast call at 8:00 a.m. Eastern time on Tuesday, February 3, 2026 to discuss the Company’s financial results for the three months and year ended December 31, 2025. An earnings supplement will also be available via the Internet by accessing the Company’s website at https://investor.gartner.com. An audio replay of the webcast wil
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0000749251-26-000028']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -49.9%
  - ↳ `EOD IT 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -65.8%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — IT not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 1↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/3↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $165.00 / median $164.00; LT growth: mean 14.1% / median 15.0%; Recommendation: Hold (3.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 +5%, FY2022 +10%, FY2023 +2%, FY2024 +16%, FY2025 +1%; Revenue surprise: FY2021 +1%, FY2022 +1%, FY2023 -0%, FY2024 +1%, FY2025 +0% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Gartner, Inc., Q1 2026 Earnings Call, May 05, 2026.rtf; Gartner, Inc., Q4 2025 Earnings Call, Feb 03, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Gartner, Inc., Q1 2026 Earnings Call, May 05, 2026.rtf; Gartner, Inc., Q4 2025 Earnings Call, Feb 03, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — a high-ROIC cash-generative franchise at its own valuation floor, but with revenue now contracting and fundamentals materially below peers.

### Bull case (overshoot / mean-revert)
- At 7.5x TEV/LTM EBITDA the name sits at the 0th percentile of its own 20-quarter history and P/E sits at the 1.4th percentile of ~5y — a multiple at its own-history floor that POSES (not answers) whether this is overshoot.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 20 quarters (partial last column excluded from the distribution)`
- Absolute EBITDA has RISEN through the margin compression — Dec-31-2021 1,148 → Mar-31-2026 (LTM) 1,337 — so the falling margin % is not a falling EBITDA dollar; the % is the optical read, the rising dollar is the reconciler.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The business throws off $1,064.2M levered FCF (LTM Mar-31-2026), consistent with a capital-light subscription model.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Leverage is modest at 1.3x net-debt/EBITDA with 10.1x interest coverage and no maturity before 2028, indicating no near-term solvency pressure.
  - ↳ `CIQ Net Debt $1,688M [Q1 Mar-31-2026] ÷ CIQ EBITDA $1,337M [LTM 12 months Mar-31-2026]`
- Management is shrinking the share count aggressively — 77.06M (2024-07-26) → 66.95M (2026-05-01), -13.1% — concentrating per-share economics.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-26..2026-05-01`
- ROIC has stayed high and even firmed — Dec-31-2024 18.2% → Mar-31-2026 (LTM) 19.4% — inconsistent with a structurally impaired franchise.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- On the peer-comp consensus read the name trades below the heterogeneous peer median on every line (TEV/EBITDA 7.5 vs median 10.8; NTM TEV/EBITDA 6.59 vs 9.66; P/E 13 vs 16.4; NTM P/E 9.2 vs 12.76) — but whether that gap is EARNED or RESIDUAL must be decomposed against fundamental_deltas, not read as cheap.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- On the fundamental_deltas the name's LT EPS growth (14% vs peer-median 12%) and beta (0.9 vs 0.9) are AT OR ABOVE peers, posing whether the full discount is fully earned by the weaker growth/margin legs or partly residual — the human judges.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Bear case (terminal / value-trap)
- The de-rate is sharply idiosyncratic, not a market move: the name returned -49.9% over 180d while IWM returned +18.0%, a -65.8% relative gap concentrated on the name.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Top-line growth has stalled into a decline — revenue YoY -1.5% (Q1 Mar-31-2026 vs Q1 Mar-31-2025) — and LTM revenue 6,474 has slipped below FY2025's 6,497, so this is not merely margin optics: the dollar base is now contracting.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- The EBITDA-margin slide is real and multi-year — 24% (2021) → 20% (2025) — and on growth/margin fundamentals the name is materially worse than peers (EBITDA margin 21% vs peer-median 31%; rev growth 2% vs 8%; EBITDA growth 2% vs 7%), so much of the peer discount is EARNED, not a clean overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Revenue estimate breadth is negative — FY2026 Revenue 0 up / 3 down last month — and the gap traces to a discrete 2026-02-03 earnings+Reg-FD 8-K, consistent with a fundamentals-driven reset rather than noise.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- Revenue is heavily concentrated in one segment — Insights 5,073 (78%) of 6,497 — so any deceleration in the subscription/CV engine drives the whole result.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- On the fundamental_deltas leverage is also worse than peers (Debt/EBITDA 2.4 vs peer-median 1.8), partly justifying the discount on the balance-sheet leg.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Twin reference cases
- **Moody's Corporation** — recovered
  - distinguished by: High-retention subscription/recurring-data franchise that de-rated on a cyclical demand pause yet held pricing power and re-rated as growth resumed.
  - source: [LLM-suggested, unverified]
- **Verisk Analytics** — recovered
  - distinguished by: Recurring-revenue analytics moat that absorbed a growth scare without structural erosion of its subscription base.
  - source: [LLM-suggested, unverified]
- **Gartner Inc** — recovered
  - distinguished by: Same name previously de-rated on a federal/government and macro demand shock, then re-accelerated contract value as decision-making normalized.
  - source: [LLM-suggested, unverified]
- **FactSet Research Systems** — recovered
  - distinguished by: Subscription financial-data provider that saw decelerating net new business and multiple compression but retained sticky customers.
  - source: [LLM-suggested, unverified]
- **Nielsen Holdings** — went terminal
  - distinguished by: Information/measurement franchise whose stalled organic growth and rising leverage led to a prolonged de-rate and eventual take-private rather than a re-rate.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the contract-value/revenue stall a temporary geopolitical- and federal-driven deferral that re-accelerates (overshoot), or the start of a structural deceleration of the Insights subscription engine that earns the peer discount (value trap)?**

### …evidence for
- Management frames the slowdown as client decisions slowing 'somewhat in March' due to the geopolitical environment, with CV growth said to have ACCELERATED in Q1 and expected to accelerate further.
  - ↳ `CIQ transcript(s): Gartner, Inc., Q1 2026 Earnings Call, May 05, 2026.rtf; Gartner, Inc., Q4 2025 Earnings Call, Feb 03, 2026.rtf`
- ROIC firmed to 19.4% LTM and absolute EBITDA rose to 1,337 LTM, inconsistent with a franchise in structural decay.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- LT EPS growth at 14% is above the peer median of 12%, suggesting the long-run earnings trajectory the market is pricing may exceed the implied discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### …evidence against
- Revenue is already YoY -1.5% and LTM revenue has slipped below FY2025, so the deceleration has crossed into outright contraction at the reporting line.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Forward revenue revisions are negative (FY2026 0 up / 3 down), and the consensus recommendation is a Hold (3.00), with management itself describing a 'much tougher selling environment' of deferred decision-making.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- Margin and growth fundamentals are materially below peers (margin 21% vs 31%; rev growth 2% vs 8%), indicating much of the discount is earned.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Key unknowns
- FCF SIGN is UNKNOWN (no OCF/capex parsed) — although a positive levered FCF figure of 1,064.2 is reported, the survival_capacity leg flags runway as not formally assessable; treat the disclosure gap as a bearish risk, not a neutral one.
- Forward/adjusted EV/EBITDA and adjusted EPS are UNKNOWN — the adjusted figure was not in the 99.1 revised guidance, so the trailing 7.5x cannot be cleanly tested against a forward basis to separate cheap-overshoot from cheap-terminal.
- Revised guidance is UNKNOWN — no revised-outlook 99.1 exhibit was parsed for the 2026-02-03 8-K, so the magnitude of any forward cut behind the gap-down is not in the facts.
- Segment EBITDA is UNKNOWN — no per-segment profitability, so the margin contribution of the 78% Insights concentration cannot be isolated.
- No graph cohort/cross-section (IT not in graph_coverage) — the idiosyncratic read rests on name-vs-IWM only, with no peer-cohort comparison.
- The EV/EBITDA at its own-history 0th percentile is explicitly trailing-only with overshoot-vs-terminal unresolved — a neutral fact for the human to resolve, not directional evidence.
