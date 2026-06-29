# Dossier — EPAM Systems, Inc. (EPAM)

_Finalist rank 6 · ref 2026-06-22 · assembled 2026-06-29 17:32 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- TRANSCRIPT-FIGURE '125' in bull_point: 'Revenue grew +7.6% YoY in Q1 Mar-31-2026 and management cites pure…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '90' in bear_point: 'Management's own Q1 2026 posture shifted MORE cautious…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '90' in decisive.against: 'Management itself raised caution QoQ — 'more macro uncertainty than…' — from the cited earnings call, not the structured facts; verify against the call

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 12.0x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 0th %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 4.0x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 0th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 4.0x at 0%ile of 19 closes → near-floor; P/LTM EPS 10.9x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 692.9
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Margin trend:** EBITDA margin: Dec-31-2021 17% → Dec-31-2022 (R) 17% → Dec-31-2023 (R) 14% → Dec-31-2024 15% → Dec-31-2025 13% → Mar-31-2026 (LTM) 13%; gross margin: Dec-31-2021 34% → Dec-31-2022 (R) 33% → Dec-31-2023 (R) 31% → Dec-31-2024 31% → Dec-31-2025 29% → Mar-31-2026 (LTM) 29%; absolute EBITDA: Dec-31-2021 628 → Dec-31-2022 (R) 799 → Dec-31-2023 (R) 652 → Dec-31-2024 693 → Dec-31-2025 707 → Mar-31-2026 (LTM) 731; absolute revenue: Dec-31-2021 3,758 → Dec-31-2022 (R) 4,825 → Dec-31-2023 (R) 4,691 → Dec-31-2024 4,728 → Dec-31-2025 5,457 → Mar-31-2026 (LTM) 5,555  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA:** -1.0x
  - ↳ `CIQ Net Debt $-749M [Q1 Mar-31-2026] ÷ CIQ EBITDA $732M [LTM 12 months Mar-31-2026]`
- **Net debt / OCF:** -1.3x
  - ↳ `CIQ Net Debt $-749M [Q1 Mar-31-2026] ÷ CIQ OCF $594M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA -1.0x (CIQ) → net cash | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2030
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** _UNKNOWN_ — no period with both EBITDA and Interest Expense
- **Share-count trend:** buying back (trailing ~1.7y): 56,935,370 (2024-07-31) → 52,244,451 (2026-04-30), -8.2%
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-30`
- **Liquidity / covenant flags:** Long Term Debt - Other (Other Borrowings) 0 @ NA; Operating Lease Liabilities (Capital Lease) 119 @ 4.800%; Revolving Credit Facility (Revolving Credit) 25 @ 4.500% Due 2030
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Dec-31-2021 3,758 → Dec-31-2022 (R) 4,825 → Dec-31-2023 (R) 4,691 → Dec-31-2024 4,728 → Dec-31-2025 5,457 → Mar-31-2026 (LTM) 5,555; EBITDA: Dec-31-2021 628 → Dec-31-2022 (R) 799 → Dec-31-2023 (R) 652 → Dec-31-2024 693 → Dec-31-2025 707 → Mar-31-2026 (LTM) 731; Revenue YoY (latest same-quarter): +7.6% (Q1 Mar-31-2026 vs Q1 Mar-31-2025); ROIC: Dec-31-2021 13.7% → Dec-31-2022 14.9% → Dec-31-2023 10.3% → Dec-31-2024 10.2% → Dec-31-2025 9.6% → Mar-31-2026 (LTM) 10.1%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Americas 3,166 (58%); Europe 2,291 (42%) of Total 5,457
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** AB Electrolux (publ) (OM:ELUX B) — Your Agency SA · Customer · src: Household Appliances; Actiris — Emakina Group SA · Customer · src: Human Resource and Employment Services; AG Insurance SA/NV — Emakina Group SA · Customer · src: Property and Casualty Insurance; Air Canada (TSX:AC) — Emakina Group SA · Customer · src: Passenger Airlines; Al Tayer Group — Emakina Group SA · Customer · src: Industrial Conglomerates; Alès Groupe S.A. — Emakina Group SA · Customer · src: Personal Care Products; Ansell Healthcare Europe N.V. — The Reference N.V. · Customer · src: Health Care Supplies; Ansell Limited (ASX:ANN) — Emakina Group SA · Customer · src: Health Care Supplies; Aquafin NV — Emakina Group SA · Customer · src: Environmental and Facilities Services; Arçelik Anonim Sirketi (IBSE:ARCLK) — Emakina Group SA · Customer · src: Household Appliances; Austrian Standards Plus GmbH — Emakina Group SA · Customer · src: Diversified Support Services; Automobiles Citroen SA — Your Agency SA · Customer · src: Automobile Manufacturers; AXA SA (ENXTPA:CS) — Emakina Group SA · Customer · src: Multi-line Insurance; Banca Monte dei Paschi di Siena S.p.A. (BIT:BMPS) — Emakina Group SA · Customer · src: Diversified Banks; Banque Stellantis France — Your Agency SA · Customer · src: Specialized Finance; Barilla Holding S.p.A. — Emakina Group SA · Customer · src: Packaged Foods and Meats; Basic Fit International B.V. — Emakina Group SA · Customer · src: Multi-Sector Holdings; Basic Fit International B.V. — Emakina.NL BV · Customer · src: Multi-Sector Holdings; Bayerische Motoren Werke Aktiengesellschaft (XTRA:BMW) — Emakina Group SA · Customer · src: Automobile Manufacturers; Beiersdorf Aktiengesellschaft (XTRA:BEI) — Emakina Group SA · Customer · src: Personal Care Products; Biotherm — Your Agency SA · Customer · src: Personal Care Products; Blocket AB — Doe Blomberg Gottberg Aktiebolag · Customer · src: Application Software; Blocket AB — Emakina Group SA · Customer · src: Application Software; Blue Band Group — Emakina Group SA · Customer · src: Hotels, Resorts and Cruise Lines; Blue Stores S.A. — Emakina Group SA · Customer · src: Apparel, Accessories and Luxury Goods; BNP Paribas Fortis SA (ENXTBR:017250539) — Emakina Belgique SA · Customer · src: Diversified Banks; BNP Paribas Fortis SA (ENXTBR:017250539) — Emakina Group SA · Customer · src: Diversified Banks; Bonduelle SCA (ENXTPA:BON) — Emakina.NL BV · Customer · src: Packaged Foods and Meats; Boucheron Holding S.A. — EMAKINA.FR SA · Customer · src: Multi-Sector Holdings; Boucheron S.A.S. — Emakina Group SA · Customer · src: Apparel, Accessories and Luxury Goods; …(+151 more)
  - ↳ `CIQ Customers&Suppliers EPAM Systems Inc NYSE EPAM Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] United States 2,834 (52%); United Kingdom 597 (11%); Switzerland 438 (8%); Netherlands 230 (4%); Germany 233 (4%); Other Locations 1,124 (21%) of Total 5,457
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — Amdocs Limited $5.6B — provides software and services to communications, (United States); Cognizant Technology Solutions Corporation $19.4B — provides consulting and technology, and outsourcing (United States); DXC Technology Company $1.4B — provides information technology services and solutions (United States); Globant S.A. $1.3B — provides technology services in the United States, (Luxembourg); Sopra Steria Group SA $3.0B — provides consulting, digital, and software development (France); Everforth $734M — provides information technology solutions for (United States); Nomura Research Institute $15.1B — engages in the provision of consulting, financial (Japan); Gartner $8.6B — provides business and technology insights for (United States); Accenture plc $77.7B — provides strategy and consulting, industry X, song, (D02 P820  Ireland); iSoftStone Information Technology $5.8B — provides information technology services in China and (China) | the name: $4.0B
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $734M–$77.7B (106x); the name is $4.0B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 0.6 vs peers Low 0.3 / Median 1 / Mean 1.1 / High 3.1; TEV/EBITDA: name 4.1 vs peers Low 2.3 / Median 5.5 / Mean 25.2 / High 199.3; P/E: name 11 vs peers Low 7.9 / Median 10.5 / Mean 35.5 / High 164.1; NTM TEV/Rev: name 0.56 vs peers Low 0.34 / Median 0.93 / Mean 1.09 / High 2.97; NTM TEV/EBITDA: name 3.37 vs peers Low 2.65 / Median 5.26 / Mean 8.42 / High 35.37; NTM P/E: name 5.76 vs peers Low 3.27 / Median 7.47 / Mean 14.74 / High 74.86  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 13% vs peer-median 17%; rev growth name 14% vs peer-median 1%; EBITDA growth name 6% vs peer-median 2%; Debt/EBITDA name 0.4 vs peer-median 1.5; LT EPS growth name 10% vs peer-median 8%; beta name 1.4 vs peer-median 0.8  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-03 no 8-K matched; 2026-02-19 earnings (2.02); 2026-06-18 no 8-K matched
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-03, 2026-02-19, 2026-06-18
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-19 → 2026-02-19 [`0001352010-26-000010`](https://www.sec.gov/Archives/edgar/data/1352010/000135201026000010/epam-20260219.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On February 19, 2026, EPAM Systems, Inc. (the “Company” or “EPAM”) issued a press release discussing its results of operations for the fourth quarter and the year ended December 31, 2025. A copy of the press release is attached as Exhibit 99.1 to this report and is incorporated by reference into this
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001352010-26-000010']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -63.6%
  - ↳ `EOD EPAM 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -82.4%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — EPAM not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $144.06 / median $139.00; LT growth: mean 10.5% / median 10.5%; Recommendation: Hold (3.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 +2%, FY2022 +7%, FY2023 -4%, FY2024 -0%, FY2025 -2%; Revenue surprise: FY2021 +1%, FY2022 +0%, FY2023 +0%, FY2024 +1%, FY2025 +0% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — multi-year margin/ROIC erosion and a self-flagged H2-visibility cut offset a net-cash, FCF-positive, still-growing franchise at a trailing-multiple floor.

### Bull case (overshoot / mean-revert)
- EV/EBITDA sits at 4.0x trailing — the absolute 0th-percentile floor across 19 quarterly closes — while the NTM TEV/EBITDA of 3.37x sits ABOVE that low, posing whether the de-rate is a mean-revertible overshoot rather than a permanent re-rating.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- P/E at 12.0x is at the 0.5-percentile of its own ~5-year range, a compression that POSES the overshoot reading against the trailing record.
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- Absolute EBITDA RISES across the window (628→799→652→693→707→731 LTM) and revenue rises to 5,555 LTM even as the margin % compresses, so the margin-% decline is partly an OPTICAL misread — the dollar earnings base is growing, not shrinking.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The balance sheet is net cash at -1.0x net-debt/EBITDA with positive FCF of 692.9 and no maturity wall before 2030 — self-funding, no runway constraint that would force a terminal outcome.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Management is buying back stock through the de-rate (-8.2% shares over trailing ~1.7y), a capital-return action inconsistent with a self-assessed terminal trajectory.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-30`
- On the fundamental_deltas the name shows superior revenue growth (14% vs peer-median 1%), faster EBITDA growth (6% vs 2%) and far lower leverage (Debt/EBITDA 0.4 vs 1.5) — POSING whether the discount to peers is RESIDUAL (overshoot) rather than EARNED, though only against a heterogeneous peer set.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Revenue grew +7.6% YoY in Q1 Mar-31-2026 and management cites pure AI-native revenue exceeding $125M in Q1 (up ~20% sequentially) with a $600M FY target, framing the demand backdrop as growing, not collapsing.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`

### Bear case (terminal / value-trap)
- EBITDA margin compressed from 17% (2021) to 13% (LTM Mar-31-2026) and gross margin from 34% to 29% — a multi-year structural erosion that, while absolute EBITDA still rose, signals the business is converting growth at a falling rate; this is a REAL signal of margin pressure, not purely optical.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- ROIC declined from 13.7%/14.9% (2021-22) to ~10.1% (LTM), indicating the capital-efficiency of the franchise has stepped down and not recovered — a durable quality deterioration, not a timing artifact.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- The stock fell -63.6% over 180d against IWM's +18.0% (-82.4% relative) — an idiosyncratic collapse, not a market-wide drawdown, indicating the market is pricing a company-specific deterioration.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Management's own Q1 2026 posture shifted MORE cautious quarter-over-quarter: from 'sentiment intact, no material change' in Q4 to 'more macro uncertainty than 90 days ago,' North America underperformance, 'lower visibility in the second half,' and expected Q2 impact — a self-flagged deceleration.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`
- The EBITDA-margin gap to peers is EARNED-leaning: the name's 13% EBITDA margin trails the peer-median 17%, so part of the discount reflects genuinely lower profitability — a value-trap input that must be weighed against the growth/leverage advantages, against a heterogeneous peer set.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Management flags 'tokenomics' and a 'genuinely new commercial construct' for AI engagements as a challenge to the services billing model, posing a structural revenue-model risk that the AI pivot could compress, not expand, the per-engagement economics.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`

### Twin reference cases
- **Cognizant Technology Solutions** — recovered
  - distinguished by: IT-services provider that de-rated on margin compression and growth slowdown fears, then stabilized as demand normalized and cost discipline returned — analogue for a services name whose margin % fell while the franchise endured.
  - source: [LLM-suggested, unverified]
- **Accenture plc** — recovered
  - distinguished by: Large consulting/services peer that absorbed discretionary-spend pullbacks and a technology-transition cycle without structural impairment — pattern for a services leader re-rating through a demand-timing trough.
  - source: [LLM-suggested, unverified]
- **DXC Technology** — went terminal
  - distinguished by: IT-services name where persistent margin erosion and revenue stagnation proved structural rather than cyclical, validating the value-trap reading for a cheap services multiple — analogue for the bear case.
  - source: [LLM-suggested, unverified]
- **Gartner** — recovered
  - distinguished by: Advisory/technology-insight provider that weathered a demand-visibility scare and re-rated as recurring engagement strength reasserted — pattern for a name whose pipeline endured a confidence dip.
  - source: [LLM-suggested, unverified]
- **Globant** — went terminal
  - distinguished by: Digital-engineering services name where an AI-disruption narrative and decelerating growth fed a sustained de-rate without recovery — analogue for the AI-cannibalization-of-services-billing risk.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the second-half visibility shortfall a temporary, macro-driven timing pause in client decision-making (overshoot, mean-revert) or the leading edge of a structural impairment of EPAM's services-billing economics as AI/tokenomics reshape engagement value (value trap)?**

### …evidence for
- Management frames the slowdown as 'a temporary shift in timing and direction' while the 'AI program pipeline and funding remains strong' and large-deal pipeline is accelerating beyond historical norms.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`
- Absolute EBITDA and revenue are still rising into the LTM (731 EBITDA, 5,555 revenue) and the balance sheet is net cash with positive FCF — no forced-outcome pressure during the pause.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### …evidence against
- Management itself raised caution QoQ — 'more macro uncertainty than 90 days ago,' North America underperformance and 'lower visibility in the second half' — and flags tokenomics as an unresolved commercial-model challenge.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`
- Multi-year margin (17%→13%) and ROIC (13.7%→10.1%) erosion predate the AI-timing scare, suggesting a structural component independent of the macro pause.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Key unknowns
- No forward/adjusted EV/EBITDA or adjusted EPS is in the revised 99.1 guidance — the trailing 4.0x cannot distinguish cheap-overshoot from cheap-terminal (note flags this explicitly).
- No revised-guidance 99.1 exhibit was parsed for the Feb-2026 8-K, so the actual revised outlook driving the de-rate is UNDISCLOSED here — a missing expected disclosure to be treated as a bearish opacity risk.
- Two of three gap-down dates (2026-02-03, 2026-06-18) had NO matching 8-K — the cause of those discrete drops is unexplained in the source set.
- No segment-level EBITDA is disclosed (Segments sheet lacks an EBITDA section), so where margin erosion concentrates (Americas vs Europe) is opaque — a bearish disclosure gap.
- Interest coverage is UNKNOWN (no period with both EBITDA and interest expense), though net-cash status reduces its weight.
- No exposed graph cohort exists for EPAM, so the idiosyncratic-vs-shared read rests only on the name-vs-IWM relative.
- Consensus revision breadth shows 0 up / 0 down last month for both EPS and revenue — no fresh analyst directional signal post-de-rate.
- Peer set is HETEROGENEOUS (caps span $734M–$77.7B, 106x) so the EARNED-vs-RESIDUAL decomposition of the discount is confidence-gated, not a clean benchmark.
