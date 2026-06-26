# Dossier — VERRA MOBILITY Corp (VRRM)

_Finalist rank 3 · ref 2026-06-22 · assembled 2026-06-25 18:58 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- RESOLVED (P/E basis) — trailing GAAP P/E 5.2x is one-time-distorted: latest GAAP EPS 0.85 is ~3.1× the recent median 0.28, so 5.2x is not a meaningful 'cheap' read. Clean read: forward adjusted guide $1.19–$1.25 → ~3.6x at the current price; CIQ P/LTM 16.8x uses a different (lower) trailing EPS basis.
- MISMATCH bear_point: 'GAAP-EPS surprises have been deeply negative (FY2023…' asserts missing/UNKNOWN data yet cites a PRESENT field — move to key_unknowns, don't source-bind it
- DIRECTIONAL language 'fair value' — human review (dossier frames, not concludes)

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 5.2x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 1st %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 8.5x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** ~4.4x (fwd, at current $4.42; EV $1,679M / FY26 adj-EBITDA $380–$385M)
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm (adj-EBITDA) + EDGAR net debt + EOD price × shares`
- **Adjusted EPS (earnings power):** FY26 guide $1.19–$1.25; adj P/E ~3.6x at $4.42 — earnings power above the GAAP basis
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- **Range position:** EV/EBITDA (TEV/LTM) 8.5x at 0%ile of 19 closes → near-floor; P/LTM EPS 16.8x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 53.9
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Margin trend:** EBITDA margin: Dec-31-2021 (R) 42% → Dec-31-2022 (R) 41% → Dec-31-2023 (R) 37% → Dec-31-2024 (R) 39% → Dec-31-2025 37% → Mar-31-2026 (LTM) 37%; gross margin: Dec-31-2021 (R) 64% → Dec-31-2022 (R) 63% → Dec-31-2023 (R) 62% → Dec-31-2024 (R) 61% → Dec-31-2025 58% → Mar-31-2026 (LTM) 57%; absolute EBITDA: Dec-31-2021 (R) 229 → Dec-31-2022 (R) 304 → Dec-31-2023 (R) 306 → Dec-31-2024 (R) 342 → Dec-31-2025 362 → Mar-31-2026 (LTM) 358; absolute revenue: Dec-31-2021 (R) 551 → Dec-31-2022 (R) 742 → Dec-31-2023 (R) 817 → Dec-31-2024 (R) 879 → Dec-31-2025 979 → Mar-31-2026 (LTM) 979  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA (GAAP):** 2.9x
  - ↳ `EDGAR XBRL net-debt/EBITDA (screen data-record)`
- **Net debt / EBITDA (fwd-adj):** ~2.6x fwd-adj (net debt $1,009M / FY26 adj-EBITDA $380–$385M)
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm (adj-EBITDA) + EDGAR net debt`
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 2.9x (GAAP); ~2.6x fwd-adj (net debt $1,009M / FY26 adj-EBITDA $380–$385M) | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2028
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 5.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Share-count trend:** buying back (trailing ~1.7y): 164,658,507 (2024-08-31) → 151,906,653 (2026-05-31), -7.7%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-31..2026-05-31`
- **Liquidity / covenant flags:** 2021 Term Loan Due 2028 (Term Loans) 687 @ 5.700%; Operating Lease (Capital Lease) 38 @ 6.500%; Revolving Credit Facility (Revolving Credit) undrawn/– @ NA; Senior Notes Due 2029 (Bonds and Notes) 350 @ 5.500%
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Dec-31-2021 (R) 551 → Dec-31-2022 (R) 742 → Dec-31-2023 (R) 817 → Dec-31-2024 (R) 879 → Dec-31-2025 979 → Mar-31-2026 (LTM) 979; EBITDA: Dec-31-2021 (R) 229 → Dec-31-2022 (R) 304 → Dec-31-2023 (R) 306 → Dec-31-2024 (R) 342 → Dec-31-2025 362 → Mar-31-2026 (LTM) 358; Revenue YoY (latest same-quarter): +0.1% (Q1 Mar-31-2026 vs Q1 Mar-31-2025); Commercial Services EBITDA: Dec-31-2021 (R) 160 → Dec-31-2022 (R) 209 → Dec-31-2023 (R) 242 → Dec-31-2024 (R) 268 → Dec-31-2025 283; Parking Solutions EBITDA: Dec-31-2021 (R) 3 → Dec-31-2022 (R) 14 → Dec-31-2023 (R) 15 → Dec-31-2024 (R) 12 → Dec-31-2025 11; Government Solutions EBITDA: Dec-31-2021 (R) 108 → Dec-31-2022 (R) 116 → Dec-31-2023 (R) 114 → Dec-31-2024 (R) 122 → Dec-31-2025 122; ROIC: Dec-31-2021 5.1% → Dec-31-2022 6.8% → Dec-31-2023 8.1% → Dec-31-2024 10.3% → Dec-31-2025 11.5% → Mar-31-2026 (LTM) 11.1%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Commercial Services 436 (45%); Parking Solutions 83 (8%); Government Solutions 461 (47%) of Total 979
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** [12 months Dec-31-2025] Commercial Services 283 (68%); Parking Solutions 11 (3%); Government Solutions 122 (29%) of segment-EBITDA sum (pre-corporate) 416; consolidated EBITDA 362 (~54 unallocated corporate)
  - ↳ `CIQ Financials→Segments (EBITDA, latest annual column) + Income Statement (consolidated EBITDA)`
- **Customers:** Avis Budget Group, Inc. (NasdaqGS:CAR) — Customer · Passenger Ground Transportation · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K; Enterprise Holdings, Inc. — Customer · Passenger Ground Transportation · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K; New York City Department of Transportation — Customer · Diversified Support Services · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K; The Hertz Corporation — Customer · Passenger Ground Transportation · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K
  - ↳ `CIQ Customers&Suppliers Verra Mobility Corporation NasdaqCM VRRM Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] Australia 66 (7%); United Kingdom 28 (3%); Canada 32 (3%); ALL Other 7 (1%); United States 846 (86%) of Total 979
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 7 peers — TaskUs $430M — provides outsourced digital services for companies in (United States); Tyler Technologies $11.8B — provides integrated software and technology management (United States); ExlService Holdings $4.0B — operates as a data and artificial intelligence (“AI”) (United States); SS&C Technologies Holdings $15.9B — provides software products and software-enabled (United States); Broadridge Financial Solutions $15.8B — provides investor communications and technology-driven (United States); Concentrix Corporation $1.5B — designs, builds, and runs integrated customer (United States); Genpact Limited $4.8B — provides business process outsourcing and information (Hamilton  HM 12   ) | the name: $668M
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $430M–$15.9B (37x); the name is $668M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 1.8 vs peers Low 0.7 / Median 2 / Mean 2.2 / High 4.8; TEV/EBITDA: name 4.7 vs peers Low 3.4 / Median 10.3 / Mean 10 / High 24.5; P/E: name 5.4 vs peers Low 4.1 / Median 15.6 / Mean 17.2 / High 38.6; NTM TEV/Rev: name 1.75 vs peers Low 0.66 / Median 1.79 / Mean 2.06 / High 4.38; NTM TEV/EBITDA: name 4.69 vs peers Low 3.51 / Median 8.33 / Mean 7.94 / High 14.96; NTM P/E: name 5.5 vs peers Low 2.01 / Median 9.39 / Mean 9.7 / High 21.06  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 37% vs peer-median 18%; rev growth name 10% vs peer-median 8%; EBITDA growth name 4% vs peer-median 9%; Debt/EBITDA name 3.0 vs peer-median 1.9; LT EPS growth name 2% vs peer-median 10%; beta name 0.4 vs peer-median 0.8  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-25 earnings (2.02) + Reg-FD (7.01); 2026-05-27 Reg-FD (7.01) + other event (8.01); 2026-06-02 management change (5.02) + Reg-FD (7.01)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-25, 2026-05-27, 2026-06-02
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-25 → 2026-02-24 [`0001193125-26-067015`](https://www.sec.gov/Archives/edgar/data/1682745/000119312526067015/vrrm-20260224.htm)
    - items: 2.02 Results of Operations and Financial Condition, 7.01 Regulation FD Disclosure, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On February 24, 2026, Verra Mobility Corporation (the “ Company ”) issued a press release announcing its financial results for the quarter and fiscal year ended December 31, 2025. A copy of the press release is furnished as Exhibit 99.1 to this Current Report on Form 8-K
    - 7.01 Regulation FD Disclosure: Regulation FD Disclosure. The Company will host a conference call and live webcast to discuss its fourth quarter and full year 2025 financial results on February 24, 2026, at 5:00 p.m. Eastern time. Live and archived webcasts of the presentation will also be available on the Company’s investor relations website at ir.verramobility.com, although the Company reserves the right to discontinue that av
  - gap 2026-05-27 → 2026-05-26 [`0001193125-26-239351`](https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116d8k.htm)
    - items: 7.01 Regulation FD Disclosure, 8.01 Other Events, 9.01 Financial Statements and Exhibits
    - 7.01 Regulation FD Disclosure: Regulation FD Disclosure. On May 26, 2026, Verra Mobility Corporation (the “ Company ”) issued a press release that announced the Company received a termination notice from Avis Budget Group, Inc. (“ Avis Budget ”) regarding Avis Budget’s contract with the Company. The Company also provided revised full-year 2026 guidance. A copy of the press release is furnished as Exhibit 99.1 to this Current Re
    - 8.01 Other Events: Other Events. On May 26, 2026, the Company announced that it received a termination notice from Avis Budget regarding Avis Budget’s contract with the Company. Avis Budget is one of the Company’s significant Commercial Services customers and represented over 10% of the Company’s total revenue for the three months ended March 31, 2026 and year ended December 31, 2025
  - gap 2026-06-02 → 2026-06-01 [`0001193125-26-251522`](https://www.sec.gov/Archives/edgar/data/1682745/000119312526251522/d39754d8k.htm)
    - items: 5.02 Departure/Election of Directors or Certain Officers, 7.01 Regulation FD Disclosure, 9.01 Financial Statements and Exhibits
    - 5.02 Departure/Election of Directors or Certain Officers: Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers. On June 1, 2026, Verra Mobility Corporation (the “Company”) announced that the Board of Directors of the Company (the “Board”) approved the appointment of Jonathan Keyser as the Interim President and Chief Executive Officer of the Company, effective May
    - 7.01 Regulation FD Disclosure: Regulation FD Disclosure. On June 1, 2026, the Company issued a press release announcing the appointment of Jonathan Keyser as Interim President and Chief Executive Officer and related matters. A copy of the press release is furnished as Exhibit 99.1 to this Current Report on Form 8-K and is incorporated by reference herein. The information furnished pursuant to
- **Revised guidance (catalyst 8-K Ex-99.1):** Revised 2026 Full-Year Guidance Based on the Company’s year-to-date 2026 results and outlook for the remainder of the year including the aforementioned termination notice, Verra Mobility is revising its 2026 full-year financial outlook to the following: • Total Revenue of $985 million to $995 million • Adjusted EBITDA of $380 million to $385 million • Adjusted EPS of $1.19 to $1.25 • Free Cash Flow of $140 million to $150 million Underlying Assumptions for 2026 Full-Year Guidance • Weighted average fully diluted share count expected to be approximately 155 million shares for the full-year 2026 • Effective tax rate (including state taxes) is expected to be 28.0% to 29.0%, with approximately $50 million in total cash taxes expected to be paid in 2026. The effective tax rate for non-GAAP adju
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -80.2%
  - ↳ `EOD VRRM 180d to 2026-06-22`
- **Market (IWM) 180d return:** 17.8%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -98.0%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — VRRM not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 1↑/5↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/8↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $9.71 / median $6.00; LT growth: mean 1.9% / median 1.9%; Recommendation: Buy (1.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 +9%, FY2022 +4%, FY2023 -32%, FY2024 -76%, FY2025 -11%; Revenue surprise: FY2021 +2%, FY2022 +0%, FY2023 +1%, FY2024 +0%, FY2025 +2% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** Earnings-call transcript on file — read Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed \u2014 a real >10%-customer loss plus CEO exit and stalled growth offset durable FCF, rising absolute EBITDA and a possibly-residual discount.

### Bull case (overshoot / mean-revert)
- On forward adjusted economics the name trades ~4.4x EV/FY26-adj-EBITDA and ~3.6x adj-P/E at $4.42, materially below the GAAP optics that anchor consensus.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- The business is FCF-positive (LTM levered FCF $53.9M) and self-funding with no runway constraint and nearest maturity wall not until 2028 — there is no solvency clock forcing a terminal outcome.
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- Absolute EBITDA has risen across the window (229→304→306→342→362, LTM 358) on rising revenue (551→979), so the falling EBITDA-margin % masks growing absolute profit — the headline margin compression is the OPTICAL read, not contracting dollars.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- ROIC has improved every year (5.1%→11.5%, LTM 11.1%) — capital efficiency is rising, not deteriorating.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Management is buying back stock (164.7M→151.9M shares, -7.7% over ~1.7y), a capital-return posture inconsistent with a distressed terminal name.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-31..2026-05-31`
- Revised post-Avis FY26 guidance still holds revenue $985–995M, adj-EBITDA $380–385M and FCF $140–150M — the company's own forward outlook does not depict collapse.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- On the peer table the name shows a far higher EBITDA margin (37% vs peer-median 18%) and higher revenue growth (10% vs 8%) than the median, so its TEV/EBITDA discount (NTM 4.69 vs peer-median 8.33) is not obviously EARNED on those axes — POSE whether it is RESIDUAL overshoot; but the peer set is HETEROGENEOUS, so treat as a confidence-gated input, not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Bear case (terminal / value-trap)
- A significant Commercial Services customer (Avis Budget, >10% of total revenue) issued a contract termination notice — a discrete, structural revenue loss, not a timing or optical artifact: this is a REAL signal.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- The CEO departed with an interim CEO appointed (5.02) immediately after the Avis shock, compounding execution/leadership uncertainty at the worst moment.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- The name has materially lagged the market (-80% 180d vs IWM +18%, -98% relative) — the drawdown is overwhelmingly idiosyncratic, not a shared-cohort selloff.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Forward fundamentals are weak on the axes that justify a discount: LT EPS growth name 2% vs peer-median 10% and EBITDA growth 4% vs peer-median 9%, with higher leverage (Debt/EBITDA 3.0 vs 1.9) — inputs consistent with an EARNED discount / value-trap reading.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Revision breadth is sharply negative — Revenue FY26 0↑/8↓ and EPS FY26 1↑/5↓ last month — analysts are cutting, the post-Avis cut not yet stabilized.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- GAAP-EPS surprises have been deeply negative (FY2023 -32%, FY2024 -76%, FY2025 -11%), a multi-year pattern of missing the GAAP bar that undercuts reliance on the adjusted guide. ⚠ uncited
  - ↳ `CIQ Estimates→Surprise (annual)`
- Same-quarter revenue growth has stalled to +0.1% YoY (Q1 Mar-31-2026), and LTM EBITDA (358) has ticked below FY25 (362) — the growth engine was flattening even before the Avis loss flows through.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Twin reference cases
- **Cimpress / Vistaprint** — recovered
  - distinguished by: Sharp idiosyncratic de-rate on customer/margin fears while remaining FCF-positive and buying back stock; recovered as cash generation proved durable.
  - source: [LLM-suggested, unverified]
- **Conduent** — went terminal
  - distinguished by: BPO/government-services contractor where customer-contract losses and stalled growth compounded into a persistent value-trap re-rate.
  - source: [LLM-suggested, unverified]
- **Sabre Corporation** — went terminal
  - distinguished by: Levered travel-linked services name where a key customer/volume shock plus weak forward growth kept the multiple compressed despite optical cheapness.
  - source: [LLM-suggested, unverified]
- **Genpact** — recovered
  - distinguished by: Outsourcing-services peer that traded at a low multiple yet held margins and re-rated as recurring revenue visibility was confirmed.
  - source: [LLM-suggested, unverified]
- **Avis Budget Group** — went terminal
  - distinguished by: The terminating counterparty itself — cyclical travel/fleet exposure illustrates how concentrated customer dependence transmits demand shocks.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the Avis termination a one-customer, ring-fenced revenue loss the durable Government Solutions and FCF base absorbs (overshoot), or the first crack in a flattening-growth, leadership-vacant franchise that justifies an EARNED discount (value trap)?**

### …evidence for
- Avis is identified as a single Commercial Services customer at >10% of revenue, while Government Solutions (47% of revenue, recurring long-term enforcement contracts) and the FCF-positive, self-funding balance sheet remain intact.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- Revised FY26 guidance — issued WITH the Avis termination known — still projects $985–995M revenue and $140–150M FCF, implying management sizes the loss as absorbable.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`

### …evidence against
- Revenue growth had already stalled to +0.1% YoY and forward LT EPS growth (2%) trails peers (10%) — the Avis loss lands on an already-decelerating base.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- An abrupt CEO departure / interim appointment landed days after the Avis disclosure, removing execution stability precisely when renewal/transformation depends on it.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`

### Key unknowns
- Quantified revenue/EBITDA impact of the Avis termination beyond the '>10% of revenue' tag — timing of roll-off and whether other Commercial Services rental customers (Hertz, Enterprise) are at similar renewal risk is NOT disclosed (opacity = bearish risk).
- Permanent CEO succession outcome and strategy continuity — only an interim CEO is named; the durability of the transformation/MOSAIC plan under new leadership is unknown.
- Status of the unnamed '>10% customer operating under a short-term contract extension' referenced on the call vs the terminating Avis contract — whether these are the same relationship is unclear.
- GAAP P/E (5.2x) rests on one-time-distorted EPS flagged as not a clean multiple; the trailing TEV/EBITDA at 0%ile is a near-floor optical reading whose overshoot-vs-terminal resolution is unresolved — belongs here, not as a directional point.
- Peer set is HETEROGENEOUS (caps $430M–$15.9B, 37x span) — every peer multiple is a confidence-gated input, so the residual-vs-earned discount cannot be cleanly benchmarked.
- Wide consensus target dispersion (mean $9.71 / median $6.00) signals unresolved disagreement on fair value post-Avis.
