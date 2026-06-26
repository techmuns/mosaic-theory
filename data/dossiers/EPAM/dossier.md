# Dossier — EPAM Systems, Inc. (EPAM)

_Finalist rank 6 · ref 2026-06-22 · assembled 2026-06-25 18:56 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (-1.5x) is on consolidated GAAP EBITDA; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio). That non-GAAP reconciliation lives in the earnings release/transcript (currently UNAVAILABLE) — do not read -1.5x as the covenant-basis leverage.

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 10.9x
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
- **Net debt / EBITDA (GAAP):** -1.5x
  - ↳ `EDGAR XBRL net-debt/EBITDA (screen data-record)`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA -1.5x (GAAP) | FCF-positive → self-funding (no runway constraint) | nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** _UNKNOWN_ — no period with both EBITDA and Interest Expense
- **Share-count trend:** buying back (trailing ~1.7y): 56,935,370 (2024-07-31) → 52,244,451 (2026-04-30), -8.2%
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-30`
- **Liquidity / covenant flags:** Long Term Debt - Other (Other Borrowings) 0 @ NA; Operating Lease Liabilities (Capital Lease) 119 @ 4.800%; Revolving Credit Facility (Revolving Credit) 25 @ 4.500%
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
- **Name 180d return:** -65.0%
  - ↳ `EOD EPAM 180d to 2026-06-22`
- **Market (IWM) 180d return:** 17.8%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -82.7%
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
- **Earnings call:** Earnings-call transcript on file — read EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — net-cash, FCF-positive, still-growing franchise at its multiple floor, against a real idiosyncratic margin/ROIC erosion and missing forward basis.

### Bull case (overshoot / mean-revert)
- Despite an EBITDA margin sliding from 17% (2021) to 13% (LTM Mar-2026), absolute EBITDA actually ROSE across the same span (628 → 731) on rising revenue (3,758 → 5,555) — the optical margin compression is the consensus MISREAD, not a shrinking profit pool.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The balance sheet is a NET-CASH position at net-debt/EBITDA -1.5x (GAAP), and the business is FCF-positive with ~$692.9M levered FCF, making it self-funding with no runway constraint — not a distressed de-rate.
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- Management is returning capital from a position of strength, reducing share count -8.2% (56.9M → 52.2M) over the trailing ~1.7 years — consistent with self-funded confidence rather than balance-sheet stress.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2026-04-30`
- Revenue is still GROWING, not collapsing: +7.6% YoY (Q1 Mar-2026 vs Q1 Mar-2025) with LTM revenue at an all-time high (5,555), undercutting a pure-terminal reading.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- On the JUSTIFIED-vs-RESIDUAL question, the name's fundamentals are BETTER than the peer median on growth (rev 14% vs 1%, EBITDA 6% vs 2%) and leverage (Debt/EBITDA 0.4 vs 1.5), so the discount may be RESIDUAL/overshoot rather than fully EARNED — though margin (13% vs 17%) and beta (1.4 vs 0.8) cut the other way; the human judges, not computed here.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The forward (NTM) multiples sit BELOW the trailing ones — NTM TEV/EBITDA 3.37 vs LTM 4.1 and NTM P/E 5.76 vs LTM 11 — i.e. consensus models forward earnings growth, posing whether the trailing de-rate is an overshoot; but the peer set is HETEROGENEOUS so treat this as confidence-gated, not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Bear case (terminal / value-trap)
- The margin compression is partly a REAL signal too: gross margin fell 34% → 29% and EBITDA margin 17% → 13% over five years, so the business is converting growing revenue at a structurally lower take rate even as absolute EBITDA edged up — a profitability-quality erosion, not pure optics.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- ROIC has deteriorated from 13.7%/14.9% (2021/2022) to ~10.1% (LTM Mar-2026) — capital is earning materially less, a durable-quality concern beyond optics.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- The de-rate is sharply IDIOSYNCRATIC, not a market move: the name returned -65% over 180d while IWM rose +17.8%, an -82.7% relative gap — the market is pricing a name-specific problem.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Management itself flags rising macro uncertainty, North America underperformance, and lower second-half visibility with expected Q2 impact on larger discretionary programs — a forward-looking caution, not just trailing noise.
  - ↳ `CIQ transcript EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`
- Consensus is lukewarm at Hold (3.00) with a mean target of $144.06 and no positive estimate breadth — a genuine counter-point, OUTWEIGHED by the net-cash self-funding balance sheet and still-growing revenue, but a real overhang on the overshoot thesis.
  - ↳ `CIQ Estimates→Consensus`

### Twin reference cases
- **Cognizant Technology Solutions** — recovered
  - distinguished by: Large IT-services provider that de-rated on growth/margin worries yet remained FCF-positive and grew through the cycle as demand normalised.
  - source: [LLM-suggested, unverified]
- **Accenture plc** — recovered
  - distinguished by: Consulting/IT-services leader that absorbed discretionary-spend air-pockets and repositioned around the AI build cycle while sustaining profitability.
  - source: [LLM-suggested, unverified]
- **DXC Technology** — went terminal
  - distinguished by: Legacy IT-services name where margin/ROIC erosion proved structural and the 'cheap multiple' was an earned value trap, not an overshoot.
  - source: [LLM-suggested, unverified]
- **Wipro** — recovered
  - distinguished by: Offshore-heavy services firm whose cyclical demand slump and margin dip mean-reverted without balance-sheet distress.
  - source: [LLM-suggested, unverified]
- **Globant S.A.** — went terminal
  - distinguished by: Digital-engineering peer where a sharp idiosyncratic de-rate reflected genuine deceleration as AI reshaped the services pricing model.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the 4.0x trailing EV/EBITDA (0th percentile of its own 5y history) a temporary OVERSHOOT on a still-growing, net-cash, FCF-positive franchise — or does it price an EARNED, durable erosion of services economics (margin/ROIC) as AI/tokenomics resets pricing and North America demand stalls?**

### …evidence for
- Absolute EBITDA rose (628 → 731) and revenue hit an all-time high (5,555) with +7.6% YoY growth, so the cash-earning engine is intact while the multiple sits at its own-history floor.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Net-cash (-1.5x net-debt/EBITDA) and ~$692.9M levered FCF mean no forced-seller dynamic, giving time for any overshoot to mean-revert.
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`

### …evidence against
- Gross margin (34% → 29%), EBITDA margin (17% → 13%) and ROIC (13.7% → 10.1%) all trend down over five years — consistent with a structural take-rate reset rather than a one-off dip.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Management cites lower second-half visibility, North America underperformance, and an evolving AI tokenomics pricing construct 'for some quarters to come' — forward signals the cheapness may be earned.
  - ↳ `CIQ transcript EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`

### Key unknowns
- No forward/adjusted EV/EBITDA or adjusted EPS in the revised guidance (both UNKNOWN) — the trailing 4.0x cannot be tested against a forward basis, leaving overshoot-vs-terminal unresolved (a bearish opacity gap).
- Nearest refinancing/maturity wall UNKNOWN (no maturity dates parsed) — flagged as a risk even within a net-cash position.
- Interest coverage UNKNOWN (no period with both EBITDA and interest expense).
- No revised-guidance 99.1 exhibit was parsed for the Feb-2026 earnings 8-K — the actual revised outlook driving the gap-downs is not in evidence (bearish opacity).
- Segment EBITDA is UNKNOWN (Segments sheet has no EBITDA breakout) — cannot see where profitability is eroding (Americas vs Europe).
- Two of three gap-down dates (2026-02-03, 2026-06-18) had NO matching 8-K — the catalyst behind those discrete drops is unexplained.
- No exposed graph cohort (EPAM not in coverage) — cannot place the idiosyncratic move against a peer cross-section beyond the name-vs-IWM read.
- Estimate-revision breadth is 0↑/0↓ (no fresh analyst movement) — consensus has not re-marked to the new posture.
- Peer set is HETEROGENEOUS (caps $734M–$77.7B, 106x span) — every peer multiple is a confidence-gated input, not a clean benchmark for residual-vs-earned.
