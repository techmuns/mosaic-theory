# Dossier — Concentrix Corp (CNXC)

_Finalist rank 14 · ref 2026-06-22 · assembled 2026-06-29 16:12 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS -20.36 vs recent median 4.71; verify against normalized/forward EPS (CIQ)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- Net debt/EBITDA (4.4x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 4.4x as the covenant-basis leverage.
- UNTRACEABLE figure '21' in bull_point: 'Absolute revenue has risen every year from 5,587 (FY21) to 9,954 LTM,…'
- UNTRACEABLE figure '25' in decisive.for: 'Absolute revenue continues to rise (9,954 LTM vs 9,826 FY25) and the…'
- ANCHORS-ON-DISTORTED-P/E bull_point: 'EV/EBITDA (TEV/LTM) sits at 5.1x at the 11th percentile of 19…' — the P/E is distorted (rests on a non-current/non-recurring EPS); don't read it as cheap
- HETEROGENEOUS-BENCHMARK bear_point: 'The discount to peers is at least partly EARNED: the name's EBITDA…' — leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every peer stat

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 6.7x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 2nd %ile
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
- **Net debt / EBITDA:** 4.4x
  - ↳ `CIQ Net Debt $5,467M [Q1 Feb-28-2026] ÷ CIQ EBITDA $1,231M [LTM 12 months Feb-28-2026]`
- **Net debt / OCF:** 7.6x
  - ↳ `CIQ Net Debt $5,467M [Q1 Feb-28-2026] ÷ CIQ OCF $722M [LTM 12 months Feb-28-2026]`
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA 4.4x (CIQ) | FCF-positive → self-funding (no runway constraint) | nearest maturity wall: 2025
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** 3.4x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Feb-28-2026]`
- **Share-count trend:** buying back (trailing ~1.8y): 65,328,966 (2024-06-30) → 61,004,826 (2026-03-31), -6.6%
  - ↳ `EDGAR XBRL shares, trailing 2024-06-30..2026-03-31`
- **Liquidity / covenant flags:** 6.600% Senior Notes Due 2028 (Bonds and Notes) 800 @ 6.600%; 6.650% Senior Notes Due 2026 (Bonds and Notes) 800 @ 6.650%; 6.850% Senior Notes Due 2033 (Bonds and Notes) 550 @ 6.850%; Credit Facility - Term Loan Component (Term Loans) 1,966 @ NA; Operating Lease (Capital Lease) 898 @ 6.920%; Other Loans (Term Loans) undrawn/– @ NA; Securitization Facility (Other Borrowings) 537 @ NA Due 2028; Sellers Note (Bonds and Notes) undrawn/– @ 2.000% Due 2025; Senior Unsecured Revolving Credit Facility (Revolving Credit) undrawn/– @ NA Due 2030
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
- **Name 180d return:** -42.6%
  - ↳ `EOD CNXC 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -59.7%
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
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Concentrix Corporation, Q1 2026 Earnings Call, Mar 24, 2026.rtf; Concentrix Corporation, Q4 2025 Earnings Call, Jan 13, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Concentrix Corporation, Q1 2026 Earnings Call, Mar 24, 2026.rtf; Concentrix Corporation, Q4 2025 Earnings Call, Jan 13, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — cheap on its own multiple history with rising revenue and positive FCF, but high leverage, falling absolute EBITDA and declining ROIC keep the value-trap read live.

### Bull case (overshoot / mean-revert)
- EV/EBITDA (TEV/LTM) sits at 5.1x at the 11th percentile of 19 quarterly closes — near its own multi-year floor.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 19 quarters (partial last column excluded from the distribution)`
- The business is FCF-positive at $517.1M LTM, making it self-funding with no runway constraint despite the leverage.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Feb-28-2026]`
- Absolute revenue has risen every year from 5,587 (FY21) to 9,954 LTM, with revenue YoY +4.1% latest same-quarter — the top line is growing, not eroding.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Management is buying back stock, reducing share count -6.6% over trailing ~1.8 years (65.3M to 61.0M), a capital-return posture inconsistent with a survival crisis.
  - ↳ `EDGAR XBRL shares, trailing 2024-06-30..2026-03-31`
- On the discount-to-peers question: the name trades at TEV/EBITDA 4.1x vs a heterogeneous peer median of 5.3x — but the human must judge whether that gap is EARNED (name's EBITDA margin 12% vs peer-median 17%, EBITDA growth -4% vs 0%, Debt/EBITDA 3.4 vs 2.0) or RESIDUAL/overshoot, since the fundamental deltas point to several worse metrics.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Bear case (terminal / value-trap)
- EBITDA margin has compressed from 16% (FY22) to 12% LTM, but the paired reconciler shows absolute EBITDA also fell from a 1,295 peak (FY24) to 1,231 LTM — so this is a GENUINE signal, not merely an optical %-decline: both the ratio AND the absolute dollar figure are declining off the peak.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Net-debt/EBITDA is 4.4x and net-debt/OCF is 7.6x with interest coverage of only 3.4x — a heavily levered balance sheet against a declining EBITDA base.
  - ↳ `CIQ Net Debt $5,467M [Q1 Feb-28-2026] ÷ CIQ EBITDA $1,231M [LTM 12 months Feb-28-2026]`
- ROIC has structurally deteriorated from 9.0% (FY22) to 3.9% LTM despite the revenue build — capital is generating progressively less return, signalling the growth is being bought, not earned.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- The name has fallen -42.6% over 180 days while the IWM benchmark rose +18.0%, a -59.7% relative underperformance — the de-rating is sharply idiosyncratic, not a market-wide move.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- The discount to peers is at least partly EARNED: the name's EBITDA margin (12%) trails the peer median (17%) and its EBITDA growth (-4%) trails the peer median (0%) with higher leverage (3.4 vs 2.0) — fundamental deltas consistent with a value trap rather than a clean overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Twin reference cases
- **Teleperformance SE** — went terminal
  - distinguished by: Same-industry CX/BPO incumbent de-rated on the secular fear that generative AI structurally shrinks the human-agent revenue pool; analogue for the bear AI-disruption thesis.
  - source: [LLM-suggested, unverified]
- **Genpact Limited** — recovered
  - distinguished by: BPO peer that repositioned toward higher-value AI-and-analytics-led work and held its multiple as the human-seat narrative reset; analogue for the bull transformation thesis.
  - source: [LLM-suggested, unverified]
- **Cognizant Technology Solutions** — recovered
  - distinguished by: IT-services name that de-rated on growth and margin worries yet kept generating cash and buying back stock through the trough; analogue for self-funded mean-reversion.
  - source: [LLM-suggested, unverified]
- **DXC Technology** — went terminal
  - distinguished by: Levered services roll-up where a leveraged balance sheet and structurally falling returns on capital persisted through repeated 'transformation' framing; analogue for the value-trap read.
  - source: [LLM-suggested, unverified]
- **Conduent** — went terminal
  - distinguished by: BPO spinoff that stayed cheap for years as leverage and weak organic growth offset cost actions; analogue for cheap-but-terminal.
  - source: [LLM-suggested, unverified]

### Decisive question
**Is the AI/iX-Suite shift a genuine margin-accretive growth engine that reverses the EBITDA and ROIC decline, or is it cover for a CX/BPO model whose human-agent revenue base is structurally eroding while leverage stays high?**

### …evidence for
- Management states Technology wins are up >61% YoY, signed annual contract value for AI solutions more than doubled QoQ, and >40% of new business now includes their own technology, with exited-2025 AI revenue of over $60M reaching breakeven.
  - ↳ `CIQ transcript(s): Concentrix Corporation, Q1 2026 Earnings Call, Mar 24, 2026.rtf; Concentrix Corporation, Q4 2025 Earnings Call, Jan 13, 2026.rtf`
- Absolute revenue continues to rise (9,954 LTM vs 9,826 FY25) and the name remains FCF-positive at $517.1M, giving room to fund the transition without external capital.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Feb-28-2026]`

### …evidence against
- Despite the revenue build, both EBITDA margin (16%→12%) and absolute EBITDA (1,295→1,231) are off their peaks and ROIC has fallen to 3.9%, so the 'accretive-at-scale' transition has not yet shown up in the consolidated numbers.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Management's own framing concedes the transformative AI deals 'might initially compress some existing revenue and margin' — an acknowledged near-term drag whose payoff timing is unverified.
  - ↳ `CIQ transcript(s): Concentrix Corporation, Q1 2026 Earnings Call, Mar 24, 2026.rtf; Concentrix Corporation, Q4 2025 Earnings Call, Jan 13, 2026.rtf`

### Key unknowns
- No adjusted forward EV/EBITDA, adjusted EPS, or adjusted net-debt/EBITDA in the revised 99.1 guidance — the forward-leverage and forward-margin picture is undisclosed (a bearish opacity gap given the 4.4x leverage).
- No revised-guidance 99.1 exhibit was parsed for the gap-down 8-Ks, so the precise content/cause that drove the discrete gap-downs is not in the facts.
- Segment EBITDA is UNKNOWN (Segments sheet has no EBITDA section) and revenue is reported as a single 100% 'Software & Programming' segment — no profitability breakout to test where margin erosion sits (bearish disclosure gap).
- The drawdown shape is discrete gap-downs tied to a debt offering (8.01) and a securitization-facility amendment (1.01/2.03), not a labelled earnings miss — the market's specific objection is not pinned down in the facts.
- No exposed graph cohort (CNXC absent from coverage) — cannot place the idiosyncratic move against a sector cross-section beyond the IWM relative read.
- Whether the planned net-leverage reduction to below 2.6x adjusted EBITDA by end-FY2026 (management target) is on track cannot be verified from the supplied facts.
