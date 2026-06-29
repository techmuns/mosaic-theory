# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-06-29 13:33 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.

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
- **Net debt / OCF (GAAP):** _UNKNOWN_ — no net-debt — debt/cash not in XBRL
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 3.9x (CIQ) | FCF-positive → self-funding (no runway constraint) | nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
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
- **Earnings call:** Earnings-call transcript on file — read Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed \u2014 a real multi-year margin/FCF turn collides with a sharp latest-quarter revenue/EBITDA reversal and unresolved forward basis.

### Bull case (overshoot / mean-revert)
- Absolute EBITDA went from -180 (2021) to +5 (2024) to +74 (2025), and gross margin climbed from -28% to 36% over the same span, evidencing a genuine multi-year operational turn rather than a one-off.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The company is FCF-positive with $39.6M levered free cash flow, indicating self-funding with no near-term runway constraint.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x suggests the debt load is comfortably serviced by current EBITDA.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- On a forward basis the name's NTM TEV/EBITDA of 17.19 sits well below the peer mean of 43.3 and only modestly above the peer median of 12.9 — a far less stretched picture than the LTM 38.4 figure; the human must judge whether this forward gap is RESIDUAL overshoot or EARNED, given the peer set is HETEROGENEOUS (caps span $34M–$275.0B).
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Bear case (terminal / value-trap)
- The headline EV/EBITDA of 10.0x is trailing-only with no forward basis disclosed, so on its own it cannot distinguish a cheap-overshoot from a cheap-terminal name — this is the consensus optical read, not a clean signal.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- The latest quarter shows a sharp deterioration: same-quarter revenue YoY of -25.5% and LTM EBITDA falling from the 74 full-year-2025 print to 52, so the margin-percent improvement masks an absolute EBITDA decline that is the REAL signal here.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Against peers the fundamentals are worse on nearly every axis — EBITDA margin 4% vs 9%, revenue growth -9% vs +2%, EBITDA growth -66% vs +2%, beta 1.5 vs 1.1 — pointing toward an EARNED discount (value trap) rather than a residual overshoot; the human adjudicates.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Revenue is 100% concentrated in a single Battery Systems segment with no segment-EBITDA visibility, leaving no diversification cushion against the battery-sector pressures management itself cites.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- The stock fell -58.1% over 180 days while the small-cap market (IWM) rose +18.0%, an -81.1% relative underperformance that is idiosyncratic, not market-driven.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Net debt/EBITDA of 3.9x (CIQ) is elevated, and the capital structure leans heavily on Chinese bank term loans and convertible instruments — a refinancing-sensitive mix.
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ EBITDA $52M [LTM 12 months Mar-31-2026]`
- Consensus target price is just $5.50 mean/median with zero upward EPS or revenue revisions in the last month, signaling no analyst momentum behind a rebound.
  - ↳ `CIQ Estimates→Consensus`

### Twin reference cases
- **QuantumScape** — went terminal
  - distinguished by: Pre-revenue/early-commercialization battery technology story sustained by patent count and roadmap narrative while burning toward dilution.
  - source: [LLM-suggested, unverified]
- **Romeo Power** — went terminal
  - distinguished by: Commercial-vehicle battery-pack maker with customer-concentration and single-product exposure that could not scale capacity profitably before liquidity ran short.
  - source: [LLM-suggested, unverified]
- **Plug Power** — went terminal
  - distinguished by: Clean-energy hardware ramp dependent on subsidies and continuing equity dilution while top-line momentum reversed.
  - source: [LLM-suggested, unverified]
- **Enovix** — recovered
  - distinguished by: Battery-cell manufacturer whose multi-year capacity ramp eventually converted into commercial volume after a deep de-rate, despite a heterogeneous comp set.
  - source: [LLM-suggested, unverified]
- **Ballard Power Systems** — went terminal
  - distinguished by: China-exposed clean-power hardware name whose regional demand and subsidy phaseout stalled the revenue ramp despite a long technology pedigree.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the latest-quarter revenue and absolute-EBITDA decline a temporary, Phase-3.2-ramp-driven dip that reverses as new capacity comes online, or the start of a structural top-line contraction that makes the peer discount EARNED?**

### …evidence for
- Absolute EBITDA built consistently from -180 (2021) to +74 (2025) and gross margin held at 31.6% even on sharply lower Q1 volumes, consistent with management's 'temporary dip' framing.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Management posture on the Q1 2026 call frames the YoY dip as temporary and tied to Phase 3.2 ramp timing with expected revenue ramp through 2026.
  - ↳ `CIQ transcript Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf`

### …evidence against
- Same-quarter revenue fell -25.5% YoY and LTM EBITDA slipped from 74 to 52, and peer-relative growth is -9% vs +2% — a deterioration broader than a clean one-quarter timing blip.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Revenue surprise turned to -8% in FY2025 after years of beats, and there are zero upward revisions in the last month, suggesting the weakness is not yet seen as transient by estimators.
  - ↳ `CIQ Estimates→Surprise (annual)`

### Key unknowns
- No forward (adjusted) EV/EBITDA or adjusted EPS in the revised guidance — the overshoot-vs-terminal distinction on the trailing 10.0x multiple cannot be resolved without it.
- The 0%ile EV/EBITDA on a 4-close history is a near-floor trailing-only fact, neither bull nor bear until the forward basis is known.
- Nearest refinancing/maturity wall is UNKNOWN — no maturity dates parsed; with a China-bank/convertible-heavy structure this is a BEARISH opacity risk, not a neutral gap.
- No revised-guidance 99.1 exhibit was parsed for either gap-down 8-K, so the magnitude of any outlook cut is undisclosed — a BEARISH disclosure gap.
- No segment-EBITDA breakout despite 100% single-segment revenue — profitability composition is opaque, a BEARISH visibility gap.
- Customer concentration depth is unquantified (named customers only, no revenue share) — cannot size dependency risk.
- Idiosyncratic-vs-shared cohort and read are UNKNOWN (no exposed US-listed cohort to price), limiting attribution of the de-rate beyond the name-vs-market figure.
- Net-debt/EBITDA is shown as 3.9x (CIQ) yet peer-comp Debt/EBITDA is 24.2 vs peer-median 1.8 — the basis discrepancy must be reconciled before leaning on either leverage figure.
