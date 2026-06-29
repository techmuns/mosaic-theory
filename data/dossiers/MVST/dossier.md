# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-06-29 14:50 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- UNTRACEABLE figure '48.2' in bear_point: 'The Q1 GAAP net profit of $48.2M is an accounting artifact:…'
- UNTRACEABLE figure '536' in decisive.against: 'Q1 volume nearly halved (~536 MWh to ~274 MWh) and YTD adjusted…'
- UNRECONCILED bear_point: 'Revenue is rolling over, not just dipping: same-quarter Revenue YoY…' — cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (4 bull vs 7 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

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
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish — a ~48% Q1 volume collapse drove adjusted EBITDA negative while the forward multiple already prices recovery above peers.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA inflected from deeply negative to positive across the trajectory (Dec-2021 -180 to Dec-2025 74, LTM Mar-2026 52), with gross margin climbing from -28% to ~35%, so the falling LTM margin % reads as the optical/consensus MISREAD of a real multi-year operational turn, not a terminal decline.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The name is FCF-positive (Levered FCF +39.6 LTM), making it self-funding with no runway constraint per the survival_capacity read — a genuine signal the franchise is not in cash distress.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x (EBITDA ÷ interest) indicates the LTM earnings base comfortably services the debt, tempering the leverage-distress narrative.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- Management frames the Q1 revenue dip as 'temporary,' tied to Phase 3.2 ramp timing and a Korea regulatory shift, with capacity (up to 2 GWh) expected to contribute a revenue ramp through 2026 — a posture that, if true, supports an overshoot reading rather than secular decline.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

### Bear case (terminal / value-trap)
- Revenue is rolling over, not just dipping: same-quarter Revenue YoY is -25.5% (Q1 Mar-2026 vs Q1 Mar-2024), and LTM revenue (372) has fallen below FY2025 (428) — the top-line is contracting, which is the REAL signal behind the falling LTM margin, not merely a fixed-cost-absorption optical effect.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- On a forward (NTM) basis the name is NOT cheap: NTM TEV/EBITDA 17.19 sits ABOVE the peer median 12.9 and NTM P/E 55.1 is the peer-set HIGH — so the LTM TEV/EBITDA at its own-history 0%ile does not survive as a value signal once the forward basis is read, but POSE whether that NTM premium is EARNED given the peer set is heterogeneous.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- The discount/premium decomposition leans EARNED (value-trap), not residual overshoot: name fundamentals are worse than peer median on every axis — EBITDA margin 4% vs 9%, rev growth -9% vs +2%, EBITDA growth -66% vs +2%, Debt/EBITDA 24.2 vs 1.8, beta 1.5 vs 1.1 — though comparability is HETEROGENEOUS so each peer stat is confidence-gated, not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The Q1 GAAP net profit of $48.2M is an accounting artifact: management's own reconciliation shows it was driven by a $63.8M non-cash fair-value gain on warrant/convertible liabilities, with an underlying adjusted net LOSS of $14.6M and YTD adjusted EBITDA of NEGATIVE $5.5M versus +$28.5M prior year — the real operating economics deteriorated sharply QoQ.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- A near-term refinancing wall: multiple Due-2026 facilities (Delayed Draw + Initial shareholder term loans, China bank-led facility) plus the nearest maturity wall flagged at 2026, against net-debt/EBITDA 3.9x — a structural risk if the operating base keeps shrinking.
  - ↳ `CIQ Financials→Capital Structure Details`
- The stock fell -58.1% over 180d versus IWM +18.0% (relative -81.1%), driven by discrete gap-downs on consecutive earnings (8-K item 2.02 on 2026-03-17 and 2026-05-12) — an idiosyncratic, earnings-driven de-rating, not a market-wide move.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Single-segment concentration (Batteries 100% of revenue) in a sector management itself describes as 'challenging' for near-term profitability — tariff frameworks, raw-material inflation, regional subsidy phase-out — leaves no diversified offset to the volume decline.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`

### Twin reference cases
- **Romeo Power** — went terminal
  - distinguished by: US-listed SPAC-era commercial EV battery-pack maker with customer-ramp/volume shortfalls and chronic operating losses that could not scale before capital ran short.
  - source: [LLM-suggested, unverified]
- **Microvast Holdings (self, 2022-2024 base)** — recovered
  - distinguished by: Same name's own multi-year arc from deeply negative EBITDA to positive on rising gross margin shows an operational turn is on the record, against which a single-year revenue contraction must be read.
  - source: CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)
- **Enovix** — recovered
  - distinguished by: US-listed advanced-battery developer that endured severe de-rating and ramp delays but retained funding and a differentiated technology pipeline through the trough.
  - source: [LLM-suggested, unverified]
- **Microvast Inc. (Chinese-linked supply chain, geo concentration)** — went terminal
  - distinguished by: Battery name with heavy China/EMEA revenue mix exposed to subsidy phase-out and tariff frameworks — the pattern where policy shifts strand a single-product franchise.
  - source: [LLM-suggested, unverified]
- **QuantumScape** — recovered
  - distinguished by: US-listed solid-state battery developer trading on a multi-year technology roadmap (here the all-solid-state milestones) rather than near-term earnings, sustaining valuation through delays.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the LTM revenue/EBITDA contraction a TEMPORARY Phase-3.2-ramp-and-Korea-regulatory timing trough that reverses as 2 GWh capacity comes online, or is it the start of a SECULAR volume decline in a single-segment business facing subsidy phase-out, tariffs and raw-material inflation?**

### …evidence for
- Multi-year arc shows a genuine operational inflection (gross margin -28% to ~35%, absolute EBITDA -180 to +74 before the LTM dip to 52), consistent with a temporary trough on a rising base.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Management attributes the volume drop to Korea regulatory shift and EMEA platform ramp-delays it expects to resolve, with Phase 3.2 capacity to drive a revenue ramp through 2026.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

### …evidence against
- Q1 volume nearly halved (~536 MWh to ~274 MWh) and YTD adjusted EBITDA swung to negative $5.5M from +$28.5M, with same-quarter revenue -25.5% YoY — the deterioration is steep and operating, not cosmetic.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Forward multiples already price recovery: NTM TEV/EBITDA 17.19 exceeds the peer median 12.9 and NTM P/E 55.1 is the peer HIGH, leaving little margin of safety if the ramp slips.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Key unknowns
- Revised forward guidance is UNKNOWN — no revised-outlook 99.1 exhibit was parsed for either gap-down 8-K (0001628280-26-018235, 0001628280-26-033601); the absence of a forward guide on consecutive earnings drops is a BEARISH opacity signal, not neutral.
- Forward/adjusted valuation anchors are UNKNOWN: ev_ebitda_adjusted_fwd and adjusted_eps are not in the 99.1 revised guidance, and P/E is genuinely NM (negative base) — the LTM TEV/EBITDA 10.0x is trailing-only and cannot by itself distinguish cheap-overshoot from cheap-terminal.
- Segment EBITDA is UNKNOWN (Segments sheet has no EBITDA section) — with 100% single-segment revenue there is no profitability breakout to test where the volume decline bites; an expected disclosure gap, BEARISH-leaning.
- net_debt_to_ebitda_adjusted is UNKNOWN — reported 3.9x rests on a depressed LTM EBITDA; the true refinancing-relevant leverage against the Due-2026 wall cannot be confirmed.
- Consensus breadth is empty (FY2026 EPS 0↑/0↓, Revenue 0↑/0↓) and only a single $5.50 mean/median target is on file — thin analyst coverage limits the consensus cross-check.
- Whether the school-bus KAF powertrain and all-solid-state programs are funded, revenue-generating, or still pre-commercial is unresolved — transcripts describe them as launches/dreams/milestones, with no order book in the source-bound facts.
- The idiosyncratic-vs-shared cohort read is UNKNOWN (no US-listed exposed peers to price), so the -81.1% relative move can only be read name-vs-market, not vs a battery cohort.
