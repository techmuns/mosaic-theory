# Dossier — EPAM Systems, Inc. (EPAM)

_Finalist rank 6 · ref 2026-06-22 · assembled 2026-06-29 16:13 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (-1.0x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read -1.0x as the covenant-basis leverage.
- TRANSCRIPT-FIGURE '125' in bull_point: 'Q1 FY2026 revenue grew 7.6% YoY with management citing pure AI…' — from the cited earnings call, not the structured facts; verify against the call
- TRANSCRIPT-FIGURE '90' in bear_point: 'Management's own Q1 posture deteriorated quarter-over-quarter: after…' — from the cited earnings call, not the structured facts; verify against the call

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
- **Relative vs market:** -81.1%
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

**Evidence balance:** mixed — net-cash, faster-than-peer growth and rising absolute EBITDA at a floor multiple offset genuine multi-year margin/ROIC erosion and softening guidance.

### Bull case (overshoot / mean-revert)
- EV/EBITDA sits at 4.0x trailing — the 0th percentile of 19 quarterly closes — and the NTM forward multiple is lower still at 3.37x, a forward basis that confirms the de-rate is not merely an artifact of trailing earnings.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- The discount to peers appears partly RESIDUAL rather than EARNED on the growth axis: name revenue growth is 14% vs peer-median 1% and EBITDA growth 6% vs peer-median 2%, so EPAM is growing faster yet trades below median multiples — but this peer set is heterogeneous (caps span $734M–$77.7B), so the human must gate this read, not bank it.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Absolute EBITDA has RISEN through the de-rate — Dec-2021 628 → Mar-2026 LTM 731 — and revenue rose 3,758 → 5,555 over the same span, so the falling margin % masks growing absolute profit dollars.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The balance sheet is net cash (net-debt/EBITDA -1.0x) and FCF-positive ($692.9M LTM), making the company self-funding with no runway constraint and nearest maturity wall not until 2030 — eliminating any forced-sale/solvency overhang.
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- Management is returning capital, reducing share count -8.2% over ~1.7 years (56.9M → 52.2M), consistent with a company deploying excess cash rather than conserving it under distress.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-30`
- Q1 FY2026 revenue grew 7.6% YoY with management citing pure AI revenues exceeding $125M (up ~20% sequentially) and a $600M full-year AI target, indicating a live growth narrative rather than secular collapse.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`

### Bear case (terminal / value-trap)
- The margin trend is genuinely deteriorating and is the REAL signal on the quality axis, not an optical misread: EBITDA margin fell 17% (2021) → 13% (LTM Mar-2026) and gross margin 34% → 29%, a structural compression even though absolute EBITDA dollars rose — the dollars grew because revenue grew, not because the business got more profitable.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Returns on capital have stepped down and stayed down — ROIC 13.7% (2021) → 10.1% (LTM Mar-2026) — consistent with a structurally less profitable business, and this is a per-period level not an optical artifact.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- The de-rate is overwhelmingly idiosyncratic, not market-driven: the name fell -63.6% over 180d while IWM rose +18.0%, a -81.1% relative underperformance pointing to a company-specific deterioration the market is pricing.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Management's own Q1 posture deteriorated quarter-over-quarter: after Q4 described sentiment as 'intact with no material change,' Q1 flagged 'more macro uncertainty today compared to 90 days ago,' North America underperformance and 'lower visibility in the second half,' a concrete softening tied to the 2026-06-18 gap-down.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`
- On margin, the peer discount is partly EARNED, not pure overshoot: name EBITDA margin 13% vs peer-median 17% and beta 1.4 vs peer-median 0.8 — lower profitability and higher volatility justify some of the lower multiple, a genuine value-trap risk the human must weigh against the faster growth.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Twin reference cases
- **Cognizant Technology Solutions** — recovered
  - distinguished by: IT-services peer that de-rated on margin compression and growth fears, then stabilized as absolute profit dollars and cash generation held through the slowdown.
  - source: [LLM-suggested, unverified]
- **Accenture plc** — recovered
  - distinguished by: Large IT-services name that absorbed a discretionary-spend slowdown and AI-transition uncertainty while retaining a self-funding balance sheet and pivoting its offering toward AI.
  - source: [LLM-suggested, unverified]
- **Wipro** — recovered
  - distinguished by: Offshore-heavy services firm whose margins compressed during a demand-soft cycle yet remained net-cash and continued buybacks, eventually re-rating off a depressed multiple.
  - source: [LLM-suggested, unverified]
- **DXC Technology** — went terminal
  - distinguished by: IT-services peer where margin and ROIC erosion proved structural rather than cyclical, and the cheap multiple stayed cheap as the core business kept shrinking — the value-trap analogue.
  - source: [LLM-suggested, unverified]
- **Globant** — went terminal
  - distinguished by: Digital-engineering services name that de-rated sharply when AI-era demand reprioritization and slowing growth converted a premium growth story into a persistent discount.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the margin/ROIC compression a structural, AI-disruption-driven impairment of EPAM's services economics (value trap), or a cyclical trough — masked by rising absolute EBITDA and a growing AI-native book — that mean-reverts as the AI transition matures?**

### …evidence for
- Margin compression is multi-year and consistent (EBITDA 17%→13%, gross 34%→29%) alongside a step-down in ROIC (13.7%→10.1%), suggesting structural rather than one-off pressure.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Q1 management explicitly cited tokenomics as a 'genuinely new and consequential commercial construct' presenting challenges to services pricing and flagged North America underperformance with lower second-half visibility — pointing to AI possibly disrupting the revenue-per-engagement model.
  - ↳ `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`

### …evidence against
- Absolute EBITDA rose 628→731 and revenue 3,758→5,555 while the multiple fell to its own-history floor, and Q1 revenue grew 7.6% YoY — consistent with a cyclical de-rate over a still-growing top line.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- EPAM is growing far faster than peers (rev 14% vs 1%, EBITDA 6% vs 2%) and building a $600M AI-native revenue book with double-digit sequential growth — evidence the franchise is participating in, not being displaced by, the AI transition.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Key unknowns
- Adjusted/forward EBITDA, adjusted EPS, and adjusted net-debt/EBITDA are all UNKNOWN — not in the 99.1 revised guidance — so the trailing 4.0x EV/EBITDA cannot be cleanly distinguished as cheap-overshoot vs cheap-terminal on a forward basis.
- The revised guidance itself was not parsed (no 99.1 revised-outlook exhibit) — the actual magnitude of any FY2026 guide-down behind the 2026-06-18 gap-down is an opaque MISSING disclosure and should be treated as a bearish gap, not neutral.
- Two of the three gap-down dates (2026-02-03 and 2026-06-18) matched NO 8-K item code, so the precise catalyst for those drops is unexplained in the supplied facts.
- Interest coverage is UNKNOWN (no period with both EBITDA and interest expense), though net-cash position blunts the materiality.
- Segment-level EBITDA is UNKNOWN (no EBITDA section on the Segments sheet), so profitability by Americas vs Europe geography cannot be assessed despite North America being flagged as the soft spot.
- Consensus revision breadth shows 0↑/0↓ last month and a Hold (3.00) rating — no directional analyst signal is available to corroborate either case.
- No idiosyncratic cohort comparison exists (EPAM absent from graph coverage), limiting the read to name-vs-IWM only.
