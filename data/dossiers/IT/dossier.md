# Dossier — GARTNER INC (IT)

_Finalist rank 8 · ref 2026-06-22 · assembled 2026-06-29 17:34 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (1.3x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 1.3x as the covenant-basis leverage.
- UNTRACEABLE figure '126' in bear_point: 'Revenue is heavily concentrated in one segment — Insights is 5,073 of…'

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
- **Relative vs market:** -68.3%
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

**Evidence balance:** mixed — extreme own-history de-rate and durable cash/ROIC against a genuine negative revenue inflection and earned peer-fundamental gap.

### Bull case (overshoot / mean-revert)
- EV/EBITDA sits at 7.5x — the 0th percentile of 20 trailing quarterly closes — and P/LTM EPS at ~13x is at the 1.4th percentile of ~5 years, so on its own history the de-rate is extreme.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- Absolute EBITDA has RISEN through the margin compression — Dec-2021 1,148 → Mar-2026 LTM 1,337 — so the falling margin % is partly an optical read, not collapsing dollar profit.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Levered free cash flow of 1,064.2 (LTM Mar-2026) funds an aggressive buyback that cut shares 13.1% in ~1.8 years (77.06M → 66.95M), evidence the de-rate is being met with capital return rather than distress.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- ROIC remains ~19.4% LTM (and held 18–20% throughout the period), consistent with a high-return subscription model rather than a structurally impaired one.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Leverage is modest at 1.3x net-debt/EBITDA with 10.1x interest coverage and no maturity wall until 2028, so balance-sheet stress is not the driver of the de-rate.
  - ↳ `CIQ Net Debt $1,688M [Q1 Mar-31-2026] ÷ CIQ EBITDA $1,337M [LTM 12 months Mar-31-2026]`
- On a forward NTM basis the gap to peers persists (NTM TEV/EBITDA 6.59 vs peer median 9.66; NTM P/E 9.2 vs median 12.76) — POSE for the human whether this discount is EARNED or RESIDUAL, noting the peer set is HETEROGENEOUS (caps $751M–$119.1B, 159x span) so the median is not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Bear case (terminal / value-trap)
- Revenue growth has stalled and turned negative — same-quarter revenue YoY is -1.5% (Q1 Mar-2026 vs Q1 Mar-2025) and LTM revenue 6,474 sits below FY2025's 6,497 — a genuine top-line deceleration, not merely an optical margin artifact.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- EBITDA margin has compressed every year from 24% (2021) to 20% (2025), and against peers the fundamental gap is wide: name margin 21% vs peer-median 31%, rev growth 2% vs 8%, EBITDA growth 2% vs 7% — suggesting much of the discount may be EARNED rather than residual overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The name has lost ~50% over 180 days while the small-cap market (IWM) gained ~18%, a -68% relative move that is sharply idiosyncratic, not a shared sector swoon.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- The Feb-3-2026 gap-down was an earnings event (8-K items 2.02 + 7.01), and consensus revenue revisions are negative (0↑/3↓ last month) with a Hold (3.00) rating, indicating the Street sees a real fundamental reset.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- Revenue is heavily concentrated in one segment — Insights is 5,073 of 6,497 (78%) — so the CV growth slowdown and U.S. federal CV erosion ($126M, vast majority renewed in 2025) hit the dominant profit engine.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`

### Twin reference cases
- **Moody's Corporation** — recovered
  - distinguished by: High-margin subscription/recurring-revenue franchise that de-rated sharply on a cyclical issuance/demand slowdown, then re-rated as the recurring base proved durable.
  - source: [LLM-suggested, unverified]
- **FactSet Research Systems Inc.** — recovered
  - distinguished by: Subscription information-services model whose multiple compressed on decelerating net-new business amid client budget caution, with retention holding.
  - source: [LLM-suggested, unverified]
- **Cognizant Technology Solutions Corporation** — recovered
  - distinguished by: IT-services name that de-rated on a growth air-pocket from deferred client decision-making, then stabilized as spend normalized.
  - source: [LLM-suggested, unverified]
- **Gartner-style government-exposed services peer (e.g. Maximus)** — went terminal
  - distinguished by: A federal-spend-exposed services book where a sustained government-contraction (DOGE-type) cut compounded into a multi-year top-line impairment rather than a one-off.
  - source: [LLM-suggested, unverified]
- **IHS Markit** — recovered
  - distinguished by: Proprietary-data subscription business that traded at a discount to data-analytics peers until the durability of contract value was recognized.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the revenue deceleration to -1.5% YoY a temporary air-pocket from deferred client decision-making (overshoot, contract value re-accelerates) or the start of a structural top-line impairment in the dominant Insights franchise (earned de-rate, value trap)?**

### …evidence for
- Management states Q1 contract value grew 1% YoY and accelerated from Q4, with ex-federal CV growth of 3.5%, framing the weakness as federal-specific and decision-timing-driven.
  - ↳ `CIQ transcript(s): Gartner, Inc., Q1 2026 Earnings Call, May 05, 2026.rtf; Gartner, Inc., Q4 2025 Earnings Call, Feb 03, 2026.rtf`
- Absolute EBITDA rose to 1,337 LTM and ROIC held ~19.4%, consistent with profit-engine durability through the soft patch.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### …evidence against
- Same-quarter revenue YoY is outright negative at -1.5% and LTM revenue has ceased growing, while consensus revenue revisions run 0↑/3↓.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Fundamental deltas show the name growing far below peers (rev 2% vs 8%, EBITDA 2% vs 7%) with a 10-point margin gap, supporting an EARNED discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Key unknowns
- Forward/adjusted EV/EBITDA and adjusted EPS are UNKNOWN — the adjusted figures were not in the 99.1 revised guidance, so the cheap-overshoot vs cheap-terminal call cannot be resolved on a forward basis (a risk).
- FCF SIGN is UNKNOWN (no OCF/capex parsed) so cash runway is not independently assessable — surface as a bearish opacity gap despite the reported positive levered FCF figure.
- Revised forward guidance was NOT parsed from the Feb-3-2026 8-K 99.1 exhibit — the magnitude of any guide-down driving the gap is unknown (bearish opacity).
- Segment-level EBITDA is UNKNOWN — the Segments sheet has no EBITDA section — so profitability of the 78% Insights concentration cannot be isolated (bearish opacity).
- No exposed cross-section / cohort (IT not in graph coverage) — the idiosyncratic read rests only on name-vs-IWM, with no peer-cohort confirmation.
- Net-debt/EBITDA on an adjusted basis is UNKNOWN; the Digital Markets divestiture's effect on go-forward revenue/leverage is not quantified in the facts.
