# Dossier — Concentrix Corp (CNXC)

_Finalist rank 14 · ref 2026-06-22 · assembled 2026-06-26 18:00 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS -20.36 vs recent median 4.71; verify against normalized/forward EPS (CIQ)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- MISMATCH bull_point: 'The business is self-funding: LTM levered free cash…' asserts missing/UNKNOWN data yet cites a PRESENT field — move to key_unknowns, don't source-bind it
- UNTRACEABLE figure '630' in decisive.against: 'LTM free cash flow is positive at 517.1 and management reaffirmed…'

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 6.1x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 0th %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** 5.1x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA percentile (5y):** 10th %ile
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** EV/EBITDA (TEV/LTM) 5.1x at 11%ile of 19 closes → near-floor; P/LTM EPS 8.8x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Quality / durability
- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 517.1
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Feb-28-2026]`
- **Margin trend:** EBITDA margin: Nov-30-2021 (R) 15% → Nov-30-2022 16% → Nov-30-2023 (R) 15% → Nov-30-2024 (R) 13% → Nov-30-2025 13% → Feb-28-2026 (LTM) 12%; gross margin: Nov-30-2021 (R) 35% → Nov-30-2022 36% → Nov-30-2023 (R) 36% → Nov-30-2024 (R) 36% → Nov-30-2025 35% → Feb-28-2026 (LTM) 34%; absolute EBITDA: Nov-30-2021 (R) 832 → Nov-30-2022 981 → Nov-30-2023 (R) 1,045 → Nov-30-2024 (R) 1,295 → Nov-30-2025 1,266 → Feb-28-2026 (LTM) 1,231; absolute revenue: Nov-30-2021 (R) 5,587 → Nov-30-2022 6,324 → Nov-30-2023 (R) 7,115 → Nov-30-2024 (R) 9,619 → Nov-30-2025 9,826 → Feb-28-2026 (LTM) 9,954  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA (GAAP):** _UNKNOWN_ — no EBITDA in XBRL
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA UNKNOWN (no EBITDA in XBRL) — solvency risk | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2026
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 3.4x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Feb-28-2026]`
- **Share-count trend:** buying back (trailing ~1.8y): 65,328,966 (2024-06-30) → 61,004,826 (2026-03-31), -6.6%
  - ↳ `EDGAR XBRL shares, trailing 2024-06-30..2026-03-31`
- **Liquidity / covenant flags:** 6.600% Senior Notes Due 2028 (Bonds and Notes) 800 @ 6.600%; 6.650% Senior Notes Due 2026 (Bonds and Notes) 800 @ 6.650%; 6.850% Senior Notes Due 2033 (Bonds and Notes) 550 @ 6.850%; Credit Facility - Term Loan Component (Term Loans) 1,966 @ NA; Operating Lease (Capital Lease) 898 @ 6.920%; Other Loans (Term Loans) undrawn/– @ NA; Securitization Facility (Other Borrowings) 537 @ NA; Sellers Note (Bonds and Notes) undrawn/– @ 2.000%; Senior Unsecured Revolving Credit Facility (Revolving Credit) undrawn/– @ NA
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Nov-30-2021 (R) 5,587 → Nov-30-2022 6,324 → Nov-30-2023 (R) 7,115 → Nov-30-2024 (R) 9,619 → Nov-30-2025 9,826 → Feb-28-2026 (LTM) 9,954; EBITDA: Nov-30-2021 (R) 832 → Nov-30-2022 981 → Nov-30-2023 (R) 1,045 → Nov-30-2024 (R) 1,295 → Nov-30-2025 1,266 → Feb-28-2026 (LTM) 1,231; Revenue YoY (latest same-quarter): +4.1% (Q1 Feb-28-2026 vs Q1 Feb-29-2024); ROIC: Nov-30-2021 8.8% → Nov-30-2022 9.0% → Nov-30-2023 5.3% → Nov-30-2024 3.8% → Nov-30-2025 4.2% → Feb-28-2026 (LTM) 3.9%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Nov-30-2025] Software & Programming 9,826 (100%) of Total 9,826
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** MakeMyTrip Limited (NasdaqGS:MMYT) — Concentrix Daksh Services India Private Limited · Client Services · src: Hotels, Resorts and Cruise Lines; R Systems International Limited (NSEI:RSYSTEMS) — Sento Europe B.V. · Customer · src: IT Consulting and Other Services; SRP Groupe S.A. (ENXTPA:SRP) — Webhelp SAS · Client Services · src: Apparel Retail
  - ↳ `CIQ Customers&Suppliers Concentrix Corporation NasdaqGS CNXC Customers.rtf`
- **Geographic:** [12 months Nov-30-2025] Philippines 1,595 (16%); United States 1,052 (11%); India 1,126 (11%); Others 5,061 (52%); Great Britain 356 (4%); Germany 334 (3%); Canada 302 (3%) of Total 9,826
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — ExlService Holdings $4.0B — operates as a data and artificial intelligence (“AI”) (United States); Teleperformance SE $3.4B — operates as a digital business services company in (France); Fiserv $25.7B — provides payments and financial services technology (United States); TaskUs $447M — provides outsourced digital services for companies in (United States); Wipro Limited $19.4B — operates as an information technology (IT), (560035    India); TTEC Holdings $103M — operates as a customer experience (CX) company that (United States); Genpact Limited $4.8B — provides business process outsourcing and information (Hamilton  HM 12   ); IBEX Limited $401M — provides end-to-end technology-enabled customer (United States); Capita plc $478M — operates as an outsourcer that supports clients across (United Kingdom); HCL Technologies Limited $32.0B — provides IT and business services, engineering, (India) | the name: $1.5B
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $103M–$32.0B (311x); the name is $1.5B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 0.7 vs peers Low 0.4 / Median 0.9 / Mean 1.2 / High 2.6; TEV/EBITDA: name 4.1 vs peers Low 3.4 / Median 5.3 / Mean 6.1 / High 10.6; P/E: name NM vs peers Low 4.3 / Median 9 / Mean 10.6 / High 17.2; NTM TEV/Rev: name 0.68 vs peers Low 0.43 / Median 0.86 / Mean 1.19 / High 2.68; NTM TEV/EBITDA: name 4.54 vs peers Low 3.55 / Median 5.26 / Mean 5.81 / High 9.27; NTM P/E: name 2 vs peers Low 1.64 / Median 6.88 / Mean 7.69 / High 15.41  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name 12% vs peer-median 17%; rev growth name 4% vs peer-median 5%; EBITDA growth name -4% vs peer-median 0%; Debt/EBITDA name 3.4 vs peer-median 2.0; LT EPS growth name 8% vs peer-median 7%; beta name 0.4 vs peer-median 0.8  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-01-28 no 8-K matched; 2026-02-11 other event (8.01); 2026-02-12 other event (8.01); 2026-03-24 material agreement (1.01)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-01-28, 2026-02-11, 2026-02-12, 2026-03-24
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-11 → 2026-02-13 [`0001803599-26-000068`](https://www.sec.gov/Archives/edgar/data/1803599/000180359926000068/cnxc-20260212.htm)
    - items: 8.01 Other Events, 9.01 Financial Statements and Exhibits
    - 8.01 Other Events: Other Events. On February 12, 2026, Concentrix Corporation (the “Company”) entered into an underwriting agreement (the “Underwriting Agreement”) with BofA Securities, Inc. and J.P. Morgan Securities LLC, as representatives of the several underwriters named in Schedule 1 thereto, to issue and sell (the “Offering”) $600 million principal amount of its 6.500% Senior Notes due 2029 (the “Notes”). The 
  - gap 2026-02-12 → 2026-02-13 [`0001803599-26-000068`](https://www.sec.gov/Archives/edgar/data/1803599/000180359926000068/cnxc-20260212.htm)
    - items: 8.01 Other Events, 9.01 Financial Statements and Exhibits
    - 8.01 Other Events: Other Events. On February 12, 2026, Concentrix Corporation (the “Company”) entered into an underwriting agreement (the “Underwriting Agreement”) with BofA Securities, Inc. and J.P. Morgan Securities LLC, as representatives of the several underwriters named in Schedule 1 thereto, to issue and sell (the “Offering”) $600 million principal amount of its 6.500% Senior Notes due 2029 (the “Notes”). The 
  - gap 2026-03-24 → 2026-03-23 [`0001803599-26-000080`](https://www.sec.gov/Archives/edgar/data/1803599/000180359926000080/cnxc-20260320.htm)
    - items: 1.01 Entry into a Material Definitive Agreement, 2.03 Item 2.03, 9.01 Financial Statements and Exhibits
    - 1.01 Entry into a Material Definitive Agreement: Entry into a Material Definitive Agreement. On March 20, 2026, Concentrix Corporation (the “Company”), as servicer, entered into an amendment (the “Amendment”) to its accounts receivable securitization facility (as amended, the “Securitization Facility”) by and among Concentrix Receivables, Inc., a subsidiary of the Company, as borrower, PNC Bank, National Association, as administrative agent, and
    - 2.03 Item 2.03: Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant. The information set forth in
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001803599-26-000068', '0001803599-26-000068']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** _UNKNOWN_ — name has no bars over the window
- **Market (IWM) 180d return:** _UNKNOWN_ — IWM benchmark bars unavailable
- **Relative vs market:** -65.2%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — CNXC not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/1↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $41.25 / median $39.00; LT growth: mean 7.7% / median 7.7%
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** GAAP-EPS surprise: FY2021 +5%, FY2022 -3%, FY2023 -13%, FY2024 +24%, FY2025 +0%; Revenue surprise: FY2021 +0%, FY2022 -1%, FY2023 +0%, FY2024 +0%, FY2025 +0% (fiscal-year, GAAP-EPS basis — adjusted basis is the 99.1 guide; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** Earnings-call transcript on file — read Concentrix Corporation, Q1 2026 Earnings Call, Mar 24, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript Concentrix Corporation, Q1 2026 Earnings Call, Mar 24, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed \u2014 a real margin/ROIC/leverage deterioration sits against a self-funding FCF-positive business whose de-rate was financing-driven, not a guidance cut.

### Bull case (overshoot / mean-revert)
- The de-rate is not an earnings collapse but a financing/balance-sheet event: the gap-down filings are a refinancing 8-K ($600M 6.500% notes due 2029 to retire 6.65% notes) and a securitization-facility amendment, not a guidance cut.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Absolute EBITDA and revenue both grew across the multi-year window (revenue 5,587→9,954, EBITDA 832→1,231), so the falling margin % rests on a rising absolute base, not shrinking dollars.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The business is self-funding: LTM levered free cash flow is positive at 517.1, removing a near-term runway constraint despite the unknown net-debt/EBITDA. ⚠ uncited
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Feb-28-2026]`
- Management is actively de-risking the nearest maturity wall, having refinanced $600M of 2026 notes with 2029 notes and committing to repay the residual with free cash flow.
  - ↳ `CIQ transcript Concentrix Corporation, Q1 2026 Earnings Call, Mar 24, 2026.rtf`
- The company is returning capital, having reduced share count ~6.6% over a trailing ~1.8 years (65.3M→61.0M).
  - ↳ `EDGAR XBRL shares, trailing 2024-06-30..2026-03-31`
- On a forward NTM basis the name's TEV/EBITDA 4.54 sits below the peer median 5.26 — POSE for the human whether that gap is EARNED by worse fundamentals or RESIDUAL overshoot, NOT a clean cheap-vs-peers conclusion given the heterogeneous set.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`

### Bear case (terminal / value-trap)
- The margin trend is genuinely deteriorating on BOTH ratio and dollars at the latest reads: EBITDA margin slid 16%→12% and absolute EBITDA has now turned down (1,295→1,266→1,231 LTM) even as revenue rose — so this is the REAL signal at the recent margin, not merely an optical %-falls-while-dollars-rise misread.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Returns on capital have structurally halved over the window (ROIC 8.8%→3.9% LTM), a deterioration in capital productivity not explained away by any reconciler.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Leverage is heavier than peers (Debt/EBITDA 3.4 vs peer-median 2.0) and the margin gap is wide (12% vs 17%), so much of the peer discount appears EARNED by worse fundamentals — a value-trap reading, not a clean overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Interest coverage is thin at 3.4x against a high-coupon debt stack (6.50%–6.85% senior notes plus a 1,966 term loan), leaving limited cushion if EBITDA keeps eroding.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Feb-28-2026]`
- EBITDA growth is negative versus a flat peer median (name -4% vs 0%), confirming the recent absolute-dollar EBITDA decline is name-specific, not a sector tide.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The name has materially underperformed the market (rel-vs-IWM -65% over 180d), an idiosyncratic drawdown not shared by the broad small-cap index.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Twin reference cases
- **Teleperformance SE** — went terminal
  - distinguished by: Same customer-experience/BPO model facing the AI-displacement narrative that compressed the whole human-agent outsourcing cohort's multiples.
  - source: [LLM-suggested, unverified]
- **Conduent** — went terminal
  - distinguished by: Levered business-process outsourcer where eroding margins and a heavy debt load fed a persistent value-trap de-rate rather than mean-reversion.
  - source: [LLM-suggested, unverified]
- **Genpact Limited** — recovered
  - distinguished by: BPO peer that repositioned toward higher-value AI/analytics services and re-rated as the mix shift earned credibility.
  - source: [LLM-suggested, unverified]
- **DXC Technology** — went terminal
  - distinguished by: Roll-up IT-services name carrying acquisition leverage where declining returns on capital persisted despite a low headline multiple.
  - source: [LLM-suggested, unverified]
- **Cognizant Technology Solutions** — recovered
  - distinguished by: IT/BPO services provider that defended margins and grew free cash flow through a demand soft patch, re-rating off trough sentiment.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the peer/own-history discount EARNED by a genuine structural margin-and-returns decline (value trap), or RESIDUAL overshoot around a refinancing event in a self-funding, FCF-positive business?**

### …evidence for
- Margin %, absolute EBITDA dollars, and ROIC are all rolling over at the latest reads (EBITDA margin 16%→12%, absolute EBITDA 1,295→1,231, ROIC 8.8%→3.9%) — a real, not optical, deterioration.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Fundamentals are worse than peers across margin, EBITDA growth, and leverage (12% vs 17%, -4% vs 0%, 3.4 vs 2.0), supporting an EARNED discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### …evidence against
- LTM free cash flow is positive at 517.1 and management reaffirmed $630–$650M adjusted FCF guidance, with the Q1 negative print explained as collected-timing seasonality — consistent with a financing-driven overshoot rather than a cash-burn terminal case.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Feb-28-2026]`
- The gap-down catalysts were refinancing and securitization filings, not a guidance cut — the maturity wall was actively termed out.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`

### Key unknowns
- Net-debt/EBITDA is UNKNOWN (no EBITDA in XBRL) — a missing solvency leg; surface as a bearish opacity risk given the 3.4 Debt/EBITDA peer-comp and the 2026 maturity wall.
- Adjusted (non-GAAP) forward EBITDA and adjusted EPS are not in the revised 99.1 guidance — the forward earnings basis management itself guides on is absent, an opacity gap.
- No revised-outlook 99.1 exhibit was parsed for the financing 8-Ks — the actual revised guidance text underlying the de-rate is missing.
- Segment-level EBITDA is UNKNOWN (Segments sheet has no EBITDA section) and revenue is reported as a single 100% 'Software & Programming' bucket — no margin breakout by line of business, an opacity risk.
- Headline GAAP P/E (6.07) rests on a non-current positive EPS while latest annual EPS is negative (-20.36); the trailing EV/EBITDA is trailing-only with no forward basis — the cheap-overshoot vs cheap-terminal question is unresolved and belongs here, not as a directional point.
- Name 180d absolute return and IWM benchmark bars are UNKNOWN, and there is no graph cohort — only the name-minus-IWM relative read exists.
- Durability and margin profile of the AI/iX-Suite mix shift (management says near-term margin compression, eventual accretion) is unverified from numbers — transcript is posture only.
