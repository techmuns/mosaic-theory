# Dossier — VERRA MOBILITY Corp (VRRM)

_Finalist rank 3 · ref 2026-06-22 · assembled 2026-06-29 16:19 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- RESOLVED (P/E basis) — trailing GAAP P/E 5.3x is one-time-distorted: latest GAAP EPS 0.85 is ~3.1× the recent median 0.28, so 5.3x is not a meaningful 'cheap' read. Clean read: forward adjusted guide $1.19–$1.25 → ~3.7x at the current price; CIQ P/LTM 16.8x uses a different (lower) trailing EPS basis.
- UNTRACEABLE figure '13' in bull_point: 'Government Solutions — the largest revenue segment (47%) — showed…'
- ANCHORS-ON-DISTORTED-P/E bull_point: 'EV/EBITDA sits at 8.5x at the 0th percentile of 19 quarterly closes —…' — the P/E is distorted (rests on a non-current/non-recurring EPS); don't read it as cheap
- ANCHORS-ON-DISTORTED-P/E bull_point: 'On the consensus comp read the name screens well below a…' — the P/E is distorted (rests on a non-current/non-recurring EPS); don't read it as cheap
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (7 bull vs 7 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 5.3x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 1st %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 8.5x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** ~4.4x (fwd, at current $4.50; EV $1,692M / FY26 adj-EBITDA $380–$385M)
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm (adj-EBITDA) + EDGAR net debt + EOD price × shares`
- **Adjusted EPS (earnings power):** FY26 guide $1.19–$1.25; adj P/E ~3.7x at $4.50 — earnings power above the GAAP basis
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
- **Net debt / EBITDA:** 2.9x
  - ↳ `CIQ Net Debt $1,046M [Q1 Mar-31-2026] ÷ CIQ EBITDA $358M [LTM 12 months Mar-31-2026]`
- **Net debt / OCF:** 4.5x
  - ↳ `CIQ Net Debt $1,046M [Q1 Mar-31-2026] ÷ CIQ OCF $234M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj):** ~2.6x fwd-adj (net debt $1,009M / FY26 adj-EBITDA $380–$385M)
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm (adj-EBITDA) + EDGAR net debt`
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 2.9x (CIQ); ~2.6x fwd-adj (net debt $1,009M / FY26 adj-EBITDA $380–$385M) | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2028
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 5.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Share-count trend:** buying back (trailing ~1.7y): 164,658,507 (2024-08-31) → 151,906,653 (2026-05-31), -7.7%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-31..2026-05-31`
- **Liquidity / covenant flags:** 2021 Term Loan Due 2028 (Term Loans) 687 @ 5.700% Due 2028; Operating Lease (Capital Lease) 38 @ 6.500% Due 2037; Revolving Credit Facility (Revolving Credit) undrawn/– @ NA Due 2030; Senior Notes Due 2029 (Bonds and Notes) 350 @ 5.500% Due 2029
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
- **Name 180d return:** -80.0%
  - ↳ `EOD VRRM 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -99.3%
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
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf; Verra Mobility Corporation, Q4 2025 Earnings Call, Feb 24, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf; Verra Mobility Corporation, Q4 2025 Earnings Call, Feb 24, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish — an outright termination of a >10%-revenue customer in the highest-margin segment, amid a CEO change and an idiosyncratic -80% move.

### Bull case (overshoot / mean-revert)
- EV/EBITDA sits at 8.5x at the 0th percentile of 19 quarterly closes — a near-floor on its own history — and the forward adj basis is far cheaper at ~4.4x ($1,692M EV / FY26 adj-EBITDA $380-385M), implying earnings power above the GAAP basis that distorts the headline P/E.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm (adj-EBITDA) + EDGAR net debt + EOD price × shares`
- Absolute EBITDA has RISEN over the trajectory (229→304→306→342→362, 358 LTM) even as the margin % drifted from 42% to 37% — a margin-% decline that masks growing absolute profit, the opposite of secular profit erosion.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The business is self-funding: FCF-positive with $53.9M LTM levered FCF and a FY26 FCF guide of $140-150M, no runway constraint, nearest maturity wall not until 2028, and interest coverage of 5.6x.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Management is buying back stock, reducing share count -7.7% over ~1.7 years (164.7M→151.9M), with the FY26 guide assuming ~155M weighted shares — a buyer at de-rated levels.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-31..2026-05-31`
- Government Solutions — the largest revenue segment (47%) — showed strong booking momentum (~$71M trailing-12-month bookings, ~$13M new Q1 awards) with long-term recurring contracts including the signed $998M 5-year NYC contract, a leg unaffected by the Avis Commercial Services issue.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- On the consensus comp read the name screens well below a heterogeneous peer median on every metric (TEV/EBITDA 4.7 vs median 10.3; P/E 5.4 vs 15.6; NTM TEV/EBITDA 4.69 vs 8.33) — but whether this is RESIDUAL overshoot or EARNED requires decomposing the fundamental_deltas, which show a SUPERIOR margin (37% vs 18%), so the discount is not explained by profitability.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- Sell-side still rates the name a Buy (1.00) with a mean target $9.71 / median $6.00 against the de-rated price, posing the question of whether the market has overshot the analyst base case.
  - ↳ `CIQ Estimates→Consensus`

### Bear case (terminal / value-trap)
- The single most load-bearing fact: Avis Budget — a customer representing OVER 10% of total revenue — issued a contract termination notice (8.01 Other Events, 2026-05-26), a direct revenue loss in the highest-EBITDA-margin segment (Commercial Services is 68% of segment-EBITDA on 45% of revenue), not an optical or timing artifact.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- The drawdown is a sequence of THREE discrete idiosyncratic gap-downs by 8-K item code — Q4 earnings (2026-02-25), the Avis termination + revised guidance (2026-05-27), and a CEO/management change (2026-06-02, item 5.02) — each a real adverse event, not a single overreaction.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- The name fell -80% over 180d while the IWM benchmark rose +18%, a -99% relative underperformance — an entirely idiosyncratic collapse, not a shared/sector drawdown.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- An interim CEO was appointed (Jonathan Keyser, item 5.02, 2026-06-01), and the prior call's framing of Avis as a 'short-term contract extension' with 'ongoing and constructive' negotiations was immediately followed by a termination notice — a leadership void at the moment of the largest customer loss.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Forward fundamentals are weak relative to the peer set the consensus comps against: EBITDA growth 4% vs peer-median 9% and LT EPS growth 2% vs peer-median 10%, so a meaningful part of the discount may be EARNED (worse growth) rather than a pure overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Estimate breadth is sharply negative — Revenue FY2026 revisions 0↑/8↓ and GAAP EPS 1↑/5↓ in the last month — and the GAAP-EPS surprise history is a string of large misses (FY2023 -32%, FY2024 -76%, FY2025 -11%).
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- Leverage is elevated versus the peer set (Debt/EBITDA 3.0 vs peer-median 1.9; CIQ net-debt/EBITDA 2.9x, net-debt/OCF 4.5x), amplifying equity-value sensitivity if the Avis loss compresses EBITDA.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Twin reference cases
- **Sabre Corporation** — went terminal
  - distinguished by: Travel-services provider with rental-car/airline-linked revenue and elevated leverage; demand-and-customer concentration shock compounded by debt left the equity persistently de-rated rather than mean-reverting.
  - source: [LLM-suggested, unverified]
- **Conduent Incorporated** — went terminal
  - distinguished by: Government/commercial outsourced-services mix with large-customer and government-contract dependence; lost-contract and renewal risk drove a durable, not transitory, re-rating.
  - source: [LLM-suggested, unverified]
- **Avis Budget Group** — recovered
  - distinguished by: The named counterparty itself — a cyclical rental-car operator whose own travel-demand cycle drove deep drawdowns that later mean-reverted; relevant as the source of the customer-loss shock.
  - source: CIQ Customers&Suppliers Verra Mobility Corporation NasdaqCM VRRM Customers.rtf
- **Tyler Technologies** — recovered
  - distinguished by: Government-software/enforcement platform business with sticky long-term municipal recurring contracts that supported durable re-rating — the durable-government-revenue analogue to VRRM's Government Solutions leg.
  - source: [LLM-suggested, unverified]
- **Gentherm / Dun & Bradstreet** — went terminal
  - distinguished by: Mid-cap with a single dominant customer/contract concentration where the loss of that anchor was a step-down in earnings power, not a timing dip.
  - source: [LLM-suggested, unverified]

### Decisive question
**Does the Avis termination (a >10%-of-revenue customer in the highest-margin segment) plus a CEO transition represent a permanent step-down in earnings power that justifies the de-rating, or has the -80% idiosyncratic move overshot a business that still guides FY26 adj-EBITDA of $380-385M and remains FCF-positive and self-funding?**

### …evidence for
- Avis represented over 10% of total revenue and issued an outright termination notice in Commercial Services, the segment producing 68% of segment-EBITDA — a concentrated loss in the most profitable leg.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- Forward growth is structurally soft (EBITDA growth 4% vs peer-median 9%; LT EPS growth 2% vs peer-median 10%) and FY26 revenue revisions are 0↑/8↓, consistent with an earned, not transitory, discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### …evidence against
- Management's revised FY26 guidance already incorporates the Avis termination yet still guides $985-995M revenue, $380-385M adj-EBITDA, $1.19-1.25 adj-EPS and $140-150M FCF — implying earnings power well above the price, with adj P/E ~3.7x.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- Government Solutions (47% of revenue) carries a signed $998M 5-year recurring NYC contract and ~$71M trailing bookings, a durable revenue leg untouched by the Commercial Services loss.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`

### Key unknowns
- The Avis termination notice timing and any wind-down/transition period — the input does not disclose when revenue actually stops or whether the contract has a tail; the magnitude/timing of the EBITDA step-down is UNKNOWN.
- The fate of the second concentrated customer relationship: the prior call described a >10% customer on a 'short-term contract extension' under 'ongoing and constructive' negotiations — whether the Avis terminator IS that same relationship, and the status of any other renewals, is not resolvable from the facts (OPACITY — bearish risk).
- Why the CEO departed and whether the management change (item 5.02) is tied to the Avis loss or signals deeper problems — the 8-K names an interim CEO but discloses no reason or permanent-successor timeline.
- No segment-level guidance for the post-Avis Commercial Services run-rate — the revised guide is consolidated only; the EBITDA-margin impact of losing the highest-margin customer is not broken out (OPACITY — bearish risk).
- Peer set is flagged HETEROGENEOUS (caps span $430M-$15.9B, 37x); no clean comparable read, so the residual-vs-earned discount cannot be cleanly benchmarked — every peer multiple is a confidence-gated input only.
- No exposed graph cohort (VRRM absent from graph_coverage) — idiosyncratic-vs-shared can only be read against IWM, not a peer cross-section.
