# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 228 · ref 2026-07-06 · assembled 2026-07-07 16:40 UTC · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+0.2s fetch)
- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on/after 2026-05-15 (the latest embedded revision event), so it is up to 52d before the 2026-07-06 reference — beyond the 45d tolerance — and the true export date is unknown, so freshness cannot be confirmed. Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar).

## Mechanical layer

### Drawdown cause & idiosyncrasy — what happened, and did it happen alone?
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
- **Revised guidance (catalyst 8-K Ex-99.1) · Net debt / EBITDA (fwd-adj covenant basis) · EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed — the revised forward guidance is UNKNOWN

_Did it happen alone? (idiosyncratic vs shared — the G2-vs-market compensation):_
- **Name 180d return:** -64.4%
  - ↳ `EOD MVST 180d to 2026-07-06`
- **Market (IWM) 180d return:** 16.5%
  - ↳ `EOD IWM 180d to 2026-07-06`
- **Relative vs market:** -80.9%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read · Graph cohort:** _UNKNOWN_ — MVST is in the graph but has no US-listed exposed names to price — UNKNOWN

### Leverage & survival
- **Net debt / EBITDA (CIQ NET basis):** 3.9x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ EBITDA $52M [LTM 12 months Mar-31-2026]`
- **Total debt / EBITDA (comps — name vs peer median):** name 5.8x vs peer median 2.0x (comps TOTAL-debt/EBITDA basis)
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- **Net debt / OCF:** 4.4x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ OCF $46M [LTM 12 months Mar-31-2026]`
- **Interest coverage:** 10.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Survival (self-funding + nearest wall):** net-debt/EBITDA 3.9x (CIQ) | FCF-positive → self-funding
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign (survival capacity)`
- **Self-funding — two-input read (supersedes the line above):** self-funding: MIXED — latest-Q OCF < 0, LTM FCF > 0 (both must be positive to self-fund)
  - ↳ `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
- **Credit health** — ↳ `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-24`  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 3 | 2.5 |
| Operational | 3 | 2.5 |
| Solvency | 2 | 3 |
| Liquidity | 2 | 3 |

_S&P issuer rating unrated · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 39.6
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Mar-16-2026** — ↳ `CIQ Financials→Capital Structure Details (A 2025 filed Mar-16-2026)`  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Convertible Bond - CNY | Bonds and Notes | $41.7M | 3.000% - 4.000% | NA | 2027-01-31 | Y | Y | CNY |
| Convertible Loan With Shareholder - Delayed Draw Term Loan | Term Loans | $13.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Convertible Loan With Shareholder - Initial Term Loan | Term Loans | $12.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Loan Facilities Agreement With a Group of Lenders Led by a Bank in China | Term Loans | $42.9M | NA | New Benchmark | 2026-12-10 | Y | N | CNY |
| Long-term Loan Agreement With a Chinese Bank | Term Loans | $13.9M | 2.700% | NA | 2027-06-19 | Y | N | CNY |
| Short-term Loan Agreements and Bank Facilities With Chinese Banks | Term Loans | $49.5M | 2.400% - 4.850% | NA | 2027-03-31 | Y | N | USD |

_2 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** (deterministic, vs the 2026-07-06 reference):
  - **matured (pre-reference): $25.0M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-05-28 (39d before ref): $13.0M Convertible Loan With Shareholder 
    - 2026-05-28 (39d before ref): $12.0M Convertible Loan With Shareholder 
  - due ≤12m (through 2026): $42.9M — 2026-12-10 $42.9M
  - due 2027: $105.1M
  - undated (floor — no panel maturity): $95.6M — Notes Payable $78.3M, Operating Lease Liabilitie $17.3M
  - _reconciliation: itemized $268.6M (panel A 2025 filed Mar-16-2026) vs the latest-quarter aggregates below — the gap is unitemized / newer term loans; read the QoQ movement in the aggregates line._
- **Capital-structure aggregates (latest quarter):** term loans 215.2 (131.3→215.2 QoQ); senior bonds 94.0; leases 16.8; total principal 326.0; total debt 326.0 (latest quarter) ($M)
  - ↳ `CIQ Financials→Capital Structure Summary`
- **Maturity resolution (8-K verbatim):** On May 28, 2026, Mr. Wu delivered a Notice of Conversion in respect of the full $25.0 million principal amount outstanding under the Loan Agreement. Such principal amount will be converted into shares of common stock of the Company in accordance with the terms of the Loan Agreement.
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`
- **Covenants — Convertible Loan** (governing values; full verbatim in appendix):
  - **Conversion:** ⇒ ~$0.50/sh at 2 sh per $1.00 · "Conversion Price" means at any time an amount equal to $1.00 divided by the applicable Conversion Rate at such time. C…
  - **Interest / coupon:** Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK) · Term SOFR for the applicable Interest Period plus the Applicable Margin (9.75% per annum); provided that 3.75% of the i…
  - **Maturity:** May 28, 2026 · clause (a) of the definition of "Maturity Date": "May 28, 2026" (replacing "November 28, 2025")
  - **Financial maintenance:** Minimum Liquidity: From the Closing Date until the Maturity Date, not permit Liquidity of the Borrower and its Subsidia…
  - **Events of default:** Condition to effectiveness / representation: no Default or Event of Default shall have occurred and be continuing or be…
- **Covenants — Loan Facilities Agreement** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LPR + 115 bps · Floating rate: one-year LPR published by the National Interbank Funding Center plus 115 bps, reset every 12 months
  - **Interest / coupon:** Late Default Interest Rate: 150% of applicable Interest Rate; Misappropriation Default Interest Rate: 200% of applicabl…
  - **Maturity:** December 10, 2026 · December 10, 2026 (Loan Term of 5 years)
  - **Financial maintenance:** Financial indicators clause present but stated value is [/] (left blank). Note: covenant 3) states 'the Borrower shall…
  - **Events of default:** Events of Default (Art. 15.1): Misrepresentation; Breach of contract/other obligations; Payment default; Material payme…

### Primary-source cross-checks (8-K releases + latest 10-Q vs CIQ panel)

- **⚠ Going concern — SUBSTANTIAL DOUBT:** These conditions and events raise substantial doubt about the Company's ability to continue as a going concern.
  - management's plans: plans to alleviate the substantial doubt include 1) obtaining sufficient funding through operations; it is anticipated that the Company will generate cash through operations in the forecasted period in consideration of the existing contract backlog and anticipated market conditions; and 2) refinanci
  - ↳ `10-Q 0001628280-26-033590`
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence — filing cross-validates panel: panel same-window $109.6M (CIQ panel, principal basis) vs filing $111.2M (10-Q, repayment basis) — 1.4% < 5% tol → AGREES. Window [balance, +12m) EXCLUSIVE (filing convention). Convertible: $25.0M panel-principal vs $26.7M filing-repayment (+$1.7M accrued PIK).
  - ↳ `10-Q maturity wall vs CIQ capital panel (same window)`
- **EBITDA-basis triangulation (each leverage basis-labeled):**
  - net debt / EBITDA (CIQ, GAAP basis): 3.9x
  - total debt / EBITDA (CIQ comps, GAAP basis): 5.8x
  - net debt / company-adjusted LTM EBITDA ($10.7M): ~18.7x
  - covenant basis: UNKNOWN (not disclosed)
  - margin: GAAP 28.6% · impairment-excluded 36.2% (CIQ; cross-check 28.6 + 32.5/427.5 = 36.2%)
  - ↳ `CIQ leverage bases + release LTM adj-EBITDA/margins`
- **Guide verification — CIQ guide vs release:** guide verification (revenue): CIQ FY guide 427.516 ≈ prior-FY actual 427.5 (within source-rounding) → VENDOR-ECHO flag (stale carry-forward); release outlook QUALITATIVE-only — render the qualitative growth line
  - ↳ `CIQ revenue guide vs release actual/outlook`
- **Customer concentration (latest 10-Q):**
  - Customer A: 52.0% (prior 31.0%)
  - Customer B: 18.0% (prior 16.0%)
  - order terms: purchase orders or framework supply agreements that are subject to adjustment, cancellation, deferral, or suspension by our customers,
  - ↳ `10-Q 0001628280-26-033590`

### Trajectory (revenue · EBITDA · margins · ROIC)
- **Trajectory ($M · % — per period)** — ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`  <!-- ds-table -->

|  | Dec-2021 | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 | Dec-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|---|
| Revenue ($M) | 152 | 204 | 307 | 380 | 428 | 372 |
| EBITDA ($M) | -180 | -140 | -85 | 5 | 74 | 52 |
| EBITDA margin | -118% | -68% | -28% | 1% | 17% | 14% |
| Gross margin | -28% | 4% | 19% | 31% | 36% | 35% |
| ROIC | -24.5% | -12.3% | -8.7% | -2.2% | 3.3% | 1.5% |

_Revenue YoY (latest same-quarter): -25.5% (Q1 Mar-31-2026 vs Q1 Mar-31-2024). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** diluting (trailing ~1.7y): 323,815,298 (2024-08-05) → 333,157,384 (2026-05-04), +2.9%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`

### Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 11.1x vs peer median 14.5x (-23%); P/E NM vs peer median 39
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _price-implied fundamental levels at stated multiples — the human judges earned vs residual; identity (†): at the name's own multiple the implied level IS consensus._
  - _TEV as-of 2026-06-24 · multiples as-of 2026-05-15_
- **Price-implied levels (at each stated multiple)** — ↳ `TEV = mcap 423.1 + net debt 199.9 (CIQ Comparable Analysis→Financial Data, Latest, as-of 2026-06-24) — simple-TEV basis`  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **7.54x** | **$82.6M EBITDA †** |
| peer-median NTM TEV/EBITDA | 12.9x | $48.3M EBITDA |
| peer-median LTM TEV/EBITDA | 14.5x | $43.0M EBITDA |
| **name NTM TEV/Rev** | **1.26x** | **$494.4M Revenue †** |
| peer-median NTM TEV/Rev | 2.55x | $244.3M Revenue |
| peer-median LTM TEV/Rev | 3.2x | $194.7M Revenue |

  - _Reads AGAINST the consensus path anchors below — juxtapose the price-implied level vs consensus per metric; never subtract one from the other._
- **Consensus path anchors (EBITDA — juxtapose, do NOT difference):** FY26E $62.1M · FY27E $147.7M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue — juxtapose, do NOT difference):** FY26E $444.4M · FY27E $591.5M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)
  - _vintage-coherent: derived FY26 $61.4M vs direct consensus $62.1M (residual 0.010 ≤ 0.10 tolerance)_
  - _Fixed multiple set (declared in code, no per-name curation): name NTM + peer-median NTM/LTM, on TEV/EBITDA and TEV/Rev._

- **P/E:** _UNKNOWN_ — no positive EPS/price
- **EV/EBITDA (GAAP TEV/LTM):** 10.0x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **Own-history range position:** EV/EBITDA (TEV/LTM) 10.0x as-of 2026-03-31 — trailing range 15.8–66.9x (median 24.9x) over 4 closes → LOW-CONFIDENCE (4 closes < 8q ≈2y) — floor read unreliable
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Peer comps
- **Peer set (roster · caps · business)** — ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Amprius Technologies | $2.0B | develops, manufactures, and markets lithium-ion (United States) |
| Forsee Power S.A. | $34M | designs, manufactures, and sells battery systems for (France) |
| Cummins Inc. | $96.5B | offers various power solutions worldwide. The company (United States) |
| BorgWarner Inc. | $14.5B | provides technology solutions for combustion, hybrid, (United States) |
| Contemporary Amperex Technology Co. | $275.0B | engages in the research, development, production, and (China) |
| Panasonic Holdings Corporation | $64.4B | develops, manufactures, sells, services, and supplies (Japan) |
| Leclanché SA | $167M | designs, develops, and manufactures customized turnkey (Switzerland) |
| Samsung SDI Co. | $24.8B | manufactures and sells batteries in South Korea, (Gyeonggi-do South) |

_the name: $423M_

- **Comparability (confidence gate):** market caps span $34M–$275.0B (8063x); the name is $423M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)** — ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| TEV/Rev | 1.7 | 0.7 | 3.2 | 5.8 | 22 |
| TEV/EBITDA | 11.1 | 7.9 | 14.5 | 18.5 | 38.4 |
| P/E | NM | 22.6 | 39 | 38.9 | 54.9 |
| NTM TEV/Rev | 1.25 | 1.06 | 2.55 | 3.64 | 13.47 |
| NTM TEV/EBITDA | 7.46 | 7.63 | 12.9 | 43.3 | 198.12 |
| NTM P/E | 14.11 | 13.27 | 22.77 | 26.23 | 55.1 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · margin · growth · leverage — name vs peers)** — ↳ `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-24`  <!-- ds-table -->

|  | Cap | EBITDA margin | Rev growth (1y) | EBITDA growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|
| Contemporary Amperex Technology Co. | $275.0B | 24% | 28% | 29% | 1.1 | 42,108 (net cash) |
| Cummins Inc. | $96.5B | 15% | 0% | 0% | 1.6 | 5,058 |
| Panasonic Holdings Corporation | $64.4B | 9% | -5% | 1% | 2.0 | 5,157 |
| Samsung SDI Co. | $24.8B | 4% | -9% | -66% | 24.2 | 6,518 |
| BorgWarner Inc. | $14.5B | 14% | 2% | 2% | 2.0 | 1,963 |
| Amprius Technologies | $2.0B | -19% | 173% | – | NM | 56 (net cash) |
| **Microvast Holdings · the name** | **$423M** | **14%** | **-10%** | **21%** | **5.8** | **200** |
| Leclanché SA | $167M | -265% | 32% | – | NM | 100 |
| Forsee Power S.A. | $34M | -10% | -21% | – | NM | 63 |
| Peer median (peers) | $19.7B | 6% | 1% | 1% | 2.0 | 1,031 |



### Catalyst path (estimates · guidance · revisions) — export date unverified (data ≥ 2026-05-15)
- **Horizon read (FQ — next-2Q revision breadth)** — ↳ `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`:
  - EPS Normalized FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Revenue FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - Revenue FQ3 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBIT FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBIT FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Interest Expense FQ2 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Interest Expense FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - EBT (GAAP) FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBT (GAAP) FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Net Income (GAAP) FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - _no revisions in any window: EPS Normalized FQ2 2026, EPS (GAAP) FQ2 2026, EPS (GAAP) FQ3 2026, EBITDA FQ2 2026, EBITDA FQ3 2026_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 0.24 (12m) → 0.29 (9m) → 0.20 (6m) → 0.06 (3m) → 0.06 (2m) → 0.04 (1m) → 0.04 (latest); net -83% (12m→latest) | FY 2026 EPS (GAAP): 0.09 (12m) → 0.11 (9m) → 0.09 (6m) → 0.05 (3m) → 0.05 (2m) → 0.18 (1m) → 0.18 (latest); net +100% (12m→latest) | FY 2026 Revenue: 609.0 (12m) → 593.9 (9m) → 544.2 (6m) → 480.5 (3m) → 480.5 (2m) → 444.4 (1m) → 444.4 (latest); net -27% (12m→latest) | FY 2026 EBITDA: 129.7 (12m) → 146.5 (9m) → 146.5 (6m) → 62.1 (1m) → 62.1 (latest); net -52% (12m→latest) [3m, 2m n/a] | FY 2026 EBIT: 46.1 (12m) → 52.8 (9m) → 43.4 (6m) → 22.5 (3m) → 22.5 (2m) → 20.0 (1m) → 20.0 (latest); net -57% (12m→latest) | FY 2026 Interest Expense: -13.7 (12m) → -4.61 (9m) → -4.81 (6m) → -5.02 (3m) → -5.02 (2m) → -4.91 (1m) → -4.91 (latest); improving (magnitude toward zero) (12m→latest) | FY 2026 EBT (GAAP): 37.0 (12m) → 59.4 (9m) → 38.8 (6m) → 17.6 (3m) → 17.6 (2m) → 73.1 (1m) → 73.1 (latest); net +98% (12m→latest) | FY 2026 Net Income (Excl. Excep): 92.7 (12m) → 92.6 (9m) → 21.4 (3m) → 21.4 (2m); net -77% (12m→2m) [6m n/a] | FY 2026 Net Income (GAAP): 33.4 (12m) → 42.3 (9m) → 32.9 (6m) → 17.6 (3m) → 17.6 (2m) → 70.1 (1m) → 70.1 (latest); net +110% (12m→latest)  [data ≥ 2026-05-15 · export date unverified]
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- **Cross-name anchor (NTM forward-multiple ladder)** — ↳ `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`:
  - NTM: TEV/REV 1.26 · TEV/EBITDA 7.54 · TEV/EBIT 17.55 · Price/Earnings 14.33 · PEG –
  - FY 2026: TEV/REV 1.42 · TEV/EBITDA 10.14 · TEV/EBIT 31.54 · Price/Earnings 32.25 · PEG –
  - FY 2027: TEV/REV 1.06 · TEV/EBITDA 4.26 · TEV/EBIT 9.17 · Price/Earnings 8.60 · PEG –
  - FY 2028: TEV/REV 0.83 · TEV/EBITDA 3.47 · TEV/EBIT 5.35 · Price/Earnings – · PEG –
  - _+5 later fiscal years in JSON_
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — ↳ `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | 427.5 | FY 2026 | 2026-03-16 | 112d (stale) | actual ≥ floor 10/13 | FY 2025 MISSED |
| Capital Expenditure | '(180.00) - (210.00)' | FY 2023 | 2023-11-10 | 969d (stale) | spend ≤ ceiling 4/4 | FY 2023 MET |
| Gross Margin % | '32.00 - 35.00' | FY 2025 | 2025-11-10 | 238d (stale) | actual ≥ floor 4/4 | FY 2024 MET |

- **Consensus stats (target + ratings):** Target price: mean $5.50, median $5.50, high/low 6.00/5.00, N 2/2; Ratings: Buy 2, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-05-15 · export date unverified]
  - ↳ `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
- **Revision-event log** (47 events · 3 broker-days) — ↳ `CIQ Estimates→Recent Changes (47 broker revision events)  [data ≥ 2026-05-15 · export date unverified]`:
  - **2026-05-15 · H.C. Wainwright & Co.** · 3↑/6↓, 9 initiations · EBITDA FY 2026 146.5→62.1 · +17 items in JSON
  - **2026-05-11 · broker undisclosed** · 5↑/8↓ · Revenue FQ2 2026 103.2→95.9 · +12 items in JSON
  - **2026-03-17 · broker undisclosed** · 0↑/16↓ · Revenue FY 2026 525.0→480.5 · +15 items in JSON
- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 +0%; Revenue surprise: FY2021 +3%, FY2022 +2%, FY2023 +3%, FY2024 +6%, FY2025 -8% (GAAP-EPS basis; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`
- **Insider activity (Form 4, 6m):** Open-market buys 0 · sells 7 (net -121.0K sh) · grants 20 · last 2026-06-12 · other C×1
  - ↳ `EDGAR Form 4 (latest 0000947871-26-000620; 18 in 6m)`
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-15): 21.4M → 26.3M sh (+22.9%, rising) · 7.9% of shares out (EDGAR XBRL) · DTC 5.8d · recent: 2026-06-15 26.3M · 2026-05-29 21.4M · 2026-05-15 21.6M · 2026-04-30 21.2M
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,571,432 screen 90d ADV`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Batteries / Battery Systems 428 (100%) of Total 428
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Ashok Leyland Limited (NSEI:ASHOKLEY) — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K; BAIC BluePark New Energy Technology Co., Ltd. (SHSE:600733) — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Cargotec Solutions LLC — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Jbm Electric Vehicles Private Limited — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Kinglong United Automotive Industry (Suzhou) Co., Ltd — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; TREPEL Airport Equipment GmbH — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K
  - ↳ `CIQ Customers&Suppliers Microvast Holdings Inc NasdaqCM MVST Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] China 139 (33%); Other Asia & Pacific 3 (1%); Italy 93 (22%); France 78 (18%); Other Europe 41 (10%); U.S. 39 (9%); India 35 (8%) of Total 428
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

## Synthesis

**Evidence balance:** strongly-bearish — a stated going-concern doubt plus a sub-12-month maturity wall and a negative current-quarter run-rate outweigh the trailing turnaround.

### Bull case (overshoot / mean-revert)
- The name is FCF-positive on an LTM basis ($39.6M levered FCF) and interest coverage is 10.6x, indicating the business self-funds and services its debt from operations on a trailing basis.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- On the fundamental_deltas, the name shows a HIGHER EBITDA margin (14% vs peer-median 6%) and faster EBITDA growth (21% vs 1%), posing whether the discount to the heterogeneous peer set is RESIDUAL (overshoot) rather than fully EARNED — the human must judge, since the peer set is not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Multi-year structural turnaround: EBITDA margin swung from -118% (Dec-2021) to +17% (Dec-2025), with gross margin climbing -28%→36% and absolute EBITDA moving from -$180M to +$74M over the same span — the % improvement is corroborated by rising absolute EBITDA, so this is a real signal, not an optical artifact.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The FY2025 gross-margin compression was primarily a one-off: a $32.5M non-cash inventory impairment cut reported gross margin by 7.6 points, with management framing underlying margin at 36.2% impairment-excluded.
  - ↳ `CIQ leverage bases + release LTM adj-EBITDA/margins`
- Consensus GAAP earnings revisions turned upward at the latest print: FY26 EPS (GAAP) net +100% (12m→latest) and Net Income (GAAP) net +110%, with H.C. Wainwright raising FY26 EBT and Net Income on 2026-05-15.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`

### Bear case (terminal / value-trap)
- The self-funding thesis fails the two-input test: latest-quarter OCF is NEGATIVE even though LTM FCF is positive — both must be positive to self-fund, so the trailing FCF-positive read is a lagging optical signal, not the current-run-rate reality.
  - ↳ `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
- Q1-2026 collapsed: revenue $60.6M (-48% YoY) on volume falling from ~536MWh to ~274MWh, adjusted EBITDA -$5.5M (vs +$28.5M prior-year) and adjusted net loss -$14.6M — the trailing +17% FY25 EBITDA margin is stale; the current run-rate turned negative.
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- The company-adjusted leverage is far worse than the headline: net debt / company-adjusted LTM EBITDA ($10.7M) is ~18.7x versus the 3.9x CIQ GAAP-basis figure — the low headline multiple is the optical MISREAD, the adjusted ~18.7x is the real signal.
  - ↳ `CIQ leverage bases + release LTM adj-EBITDA/margins`
- A $111.2M maturity wall is due within 12 months (filing basis), against only $126M cash — a near-term refinancing/repayment cliff.
  - ↳ `10-Q 0001628280-26-033590`
- The name carries the second-weakest credit profile on the panel (Solvency/Liquidity 2/2, S&P-MI PD model, issuer unrated) with total-debt/EBITDA 5.8x vs peer-median 2.0x and a beta of 3.5 vs 1.1.
  - ↳ `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-24`
- Customer concentration is severe and worsening: Customer A rose to 52.0% of revenue (from 31.0%) and Customer B to 18.0% (from 16.0%), leaving the top two at ~70% of a shrinking top line.
  - ↳ `10-Q 0001628280-26-033590`
- The apparent Q1-2026 GAAP net profit of $48.2M is a non-operating artifact of a $63.8M fair-value gain on warrant/convertible liabilities, not operating performance — the reconciled adjusted result was a loss.
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- The latest 10-Q states SUBSTANTIAL DOUBT about going-concern (with plans present) — a primary-source disclosure that is the load-bearing terminal-risk signal, not an optical metric.
  - ↳ `10-Q 0001628280-26-033590`
- The $25.0M shareholder convertible term loans maturing 2026-05-28 were resolved by Mr. Wu converting the full principal into common stock — deleveraging via dilution of an insider-priced (~$0.50/sh) convertible, not cash repayment.
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`
- The stock fell 64% over 180 days while the small-cap benchmark rose 16% (rel -81%), and short interest is rising (+22.9% to 26.3M sh, 7.9% of float) — the drawdown is idiosyncratic, not a market-wide de-rate.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Decisive question
**Is the Q1-2026 revenue/volume collapse a temporary trough during the Phase 3.2 capacity ramp (supporting an overshoot read), or the start of a demand deterioration that, combined with the going-concern doubt and the 12-month maturity wall, makes the discount an earned value trap?**

### …evidence for
- Management frames the YoY revenue dip as temporary and tied to Phase 3.2 production timing, expecting capacity to contribute to a continued revenue ramp through 2026.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Consensus FY27 revenue is set to reaccelerate to $591.5M with EBITDA of $147.7M, implying the trough is expected to reverse.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus Revenue, latest snapshot)`
- Multi-year gross margin held in the 31-38% quarterly band even as revenue fell, supporting management's 'resilient margin' framing.
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`

### …evidence against
- The latest 10-Q carries an explicit going-concern substantial-doubt statement, indicating the funding gap is not yet resolved by the ramp narrative.
  - ↳ `10-Q 0001628280-26-033590`
- Q1-2026 volume nearly halved (~536MWh to ~274MWh) and adjusted EBITDA turned negative (-$5.5M), so the trough is already draining rather than generating cash.
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- FY25 revenue landed just below guidance on Korea regulatory shifts and EMEA platform delays, and top-customer dependence rose to 52% — demand is concentrated and externally exposed, not diversified.
  - ↳ `10-Q 0001628280-26-033590`

### Key unknowns
- Cash-runway visibility against the $111.2M sub-12-month maturity wall is not disclosed as a resolved plan — the going-concern 'plans present' are not quantified (bearish opacity).
- The covenant basis for leverage is UNKNOWN/not disclosed; minimum-liquidity and other financial-maintenance covenant headroom cannot be tested (bearish opacity).
- No forward adjusted EBITDA/EPS in the revised guidance and FY26 revenue guide is a stale vendor-echo of prior-year actual ($427.5M) — no quantified forward outlook (bearish opacity).
- TEV/LTM EBITDA sits at the 0th percentile of a 4-close (<2y) history flagged LOW-CONFIDENCE; the floor read is unreliable and cannot resolve overshoot-vs-terminal — a neutral fact, not directional.
- No segment-level EBITDA breakout is disclosed (single 100% Batteries segment), so profitability by product/region is unverifiable (bearish opacity).
- Peer set is HETEROGENEOUS (market caps span 8063x); every peer multiple and the residual-vs-earned discount question are confidence-gated, not clean benchmarks.
- Whether the Phase 3.2 SOP and the KAF school-bus powertrain convert to actual orders/revenue is unquantified narrative only.
- Q1-2026 GAAP net profit is inflated by a $63.8M non-cash fair-value swing; the recurring quality of interest coverage and FCF under the negative current-quarter OCF is unresolved.

### Twin reference cases
- **Romeo Power** — went terminal (LLM-claimed — verify)
  - distinguished by: US-listed SPAC-era EV battery/pack maker with extreme single-customer concentration and a cash runway that ran out before scale economics arrived.
  - source: [LLM-suggested, unverified]
- **Leclanché SA** — went terminal
  - distinguished by: A sub-scale battery-systems maker on the same peer roster with deeply negative EBITDA margin and chronic reliance on shareholder/convertible financing.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **QuantumScape** — recovered (LLM-claimed — verify)
  - distinguished by: US-listed battery innovator that survived on a solid-state technology narrative and repeated equity issuance while pre-scale — analogue for a dilution-funded runway extension rather than cash-flow self-funding.
  - source: [LLM-suggested, unverified]


## APPENDIX — FINANCIAL SUMMARY (actuals + consensus estimates) — export date unverified (data ≥ 2026-05-15)
### Annual (last-4-FY + LTM + FY26E/FY27E consensus)
- **Annual financials ($M; E = consensus)** — ↳ `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|
| Revenue ($M) | 204 | 307 | 380 | 428 | 372 | 444 | 592 |
| Revenue growth | — | +50% | — (basis) | +13% | — (basis) | +4% (vs FY25) | +33% |
| EBITDA ($M) | -140 | -85 | 5 | 74 | 52 | 62 | 148 |
| EBITDA margin | -68% | -28% | 1% | 17% | 14% | 14% | 25% |
| EBIT ($M) | -160 | -108 | -26 | 40 | 19 | 20 | 69 |
| Net income ($M) | -158 | -106 | -196 | -29 | -43 | 70 | 56 |
| EPS (GAAP, dil.) | -0.52 | -0.34 | -0.61 | -0.09 | -0.19 | 0.18 | 0.17 |
| EPS (Normalized) | -0.33 | -0.21 | -0.22 | 0.00 | -0.03 | 0.04 | 0.15 |
| CFO ($M) | -54 | -75 | 3 | 76 | 46 | — | — |
| Capex ($M) | -151 | -187 | -28 | -20 | -20 | — | — |
| FCF (levered, CIQ) | -136 | -117 | -65 | 18 | 40 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-05-15; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Trailing 8 quarters (the recent-quarter trajectory)
- **Quarterly financials** — ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`  <!-- ds-table -->

|  | Q2-24 | Q3-24 (R) | Q4-24 (R) | Q1-25 (R) | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 84 | 101 | 113 | 116 | 91 | 123 | 96 | 61 |
| Gross margin | 33% | 33% | 37% | 37% | 35% | 38% | 35% | 32% |
| EBITDA ($M) | -4 | 12 | 12 | 22 | 18 | 23 | 11 | 0 |
| EBITDA margin | -5% | 12% | 11% | 19% | 19% | 19% | 11% | 0% |
| Revenue QoQ | — | — (basis) | +12% | +3% | — (basis) | +35% | -22% | -37% |
| Revenue YoY | — | — | — | — | +9% | — (basis) | — (basis) | — (basis) |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q1-26 ($M): cash & ST inv 126; total debt 326; net debt 200; equity 466; net working capital -18; net-debt/EBITDA → see the Leverage & survival block (not recomputed)
  - ↳ `CIQ Financials→Balance Sheet (quarterly, Q1-26)`
- **Coherence — BS vs implied-valuation bridge:** cash BS $126M / bridge $126M; debt BS $326M / bridge $326M — reconcile with the implied-valuation bridge.
  - ↳ `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`


### Capital-structure provenance — on-demand (web collapsed · print-excluded · JSON) — full panel · pointers · terms
- **Capital structure — full instrument panel A 2025 filed Mar-16-2026** — ↳ `CIQ Financials→Capital Structure Details (A 2025 filed Mar-16-2026)`  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Convertible Bond - CNY | Bonds and Notes | $41.7M | 3.000% - 4.000% | NA | 2027-01-31 | Y | Y | CNY |
| Convertible Loan With Shareholder - Delayed Draw Term Loan | Term Loans | $13.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Convertible Loan With Shareholder - Initial Term Loan | Term Loans | $12.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Loan Facilities Agreement With a Group of Lenders Led by a Bank in China | Term Loans | $42.9M | NA | New Benchmark | 2026-12-10 | Y | N | CNY |
| Long-term Loan Agreement With a Chinese Bank | Term Loans | $13.9M | 2.700% | NA | 2027-06-19 | Y | N | CNY |
| Notes Payable | Bonds and Notes | $78.3M | NA | NA | undated | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $17.3M | 5.000% | NA | undated | Y | N | USD |
| Short-term Loan Agreements and Bank Facilities With Chinese Banks | Term Loans | $49.5M | 2.400% - 4.850% | NA | 2027-03-31 | Y | N | USD |

- **8-Ks at instrument maturities:** 8-K at maturity 2026-05-28: filed 2026-05-28 [0000947871-26-000585] 5.02 Departure/Election of Directors or Certain Officers, 8.01 Other Events, 9.01 Financial Statements and Exhibits — read for resolution
  - ↳ `EDGAR 8-K submissions (±10d of instrument maturities)`
- **Covenant / contract pointers (CIK-verified execution filings)** — ↳ `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| material contracts (10-K exhibit index) | latest 10-K | 2026-03-16 | 0001628280-26-018264 — mvst20251231-ex1013.htm, mvst20251231-ex1021.htm |
| Convertible Loan | 8-K | 2025-03-17 | 0000947871-25-000313 — ss4588423_ex1001.htm |
| Convertible Loan | 8-K | 2024-06-04 | 0001760689-24-000021 — wu_microvast-guarantyagree.htm, wu_microvast-loanandsecuri.htm, wu_microvast-pledgeagreeme.htm |
| Loan Facilities Agreement | 8-K | 2022-09-29 | 0001760689-22-000094 — exhibit101-syndicatedloana.htm |
| Notes Payable | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Convertible Loan (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | ⇒ ~$0.50/sh at 2 sh per $1.00 · "Conversion Price" means at any time an amount equal to $1.00 divided by the applicable Conversion Rate at such time. Conversion Rate: two (2) shares of Common Stock (subject to adjustment) per $1.00… — full verbatim in JSON | base (footer) |
| Principal / commitment amount | Initial Term Loan Commitment: $12,000,000. Delayed Draw Term Loan Commitment: $13,000,000. (Annex I: YANG WU $12,000,000.00 / $13,000,000.00; Totals $12,000,000 / $13,000,000) | base (footer) |
| Interest / coupon rate | Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK) · Term SOFR for the applicable Interest Period plus the Applicable Margin (9.75% per annum); provided that 3.75% of the interest due on each Loan shall be paid in-kind (PIK Interest). Floor: Term SOFR… — full verbatim in JSON | base (footer) |
| Maturity date | May 28, 2026 · clause (a) of the definition of "Maturity Date": "May 28, 2026" (replacing "November 28, 2025") | amended by 0000947871-25-000313 |
| Financial-maintenance covenants | Minimum Liquidity: From the Closing Date until the Maturity Date, not permit Liquidity of the Borrower and its Subsidiaries, as of Friday of each calendar week (each, a "Liquidity Testing Date"), to… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Guarantors: Microvast Holdings, Inc.; Microvast Advanced Materials Inc.; Microvast Advanced Membrane Inc.; Microvast Energy, Inc.; Microvast Power Solutions, Inc.; Microvast GmbH. Liens and rights se… — full verbatim in JSON | amended by 0000947871-25-000313 |
| Mandatory prepayment / events of default | Condition to effectiveness / representation: no Default or Event of Default shall have occurred and be continuing or be caused by this Amendment (terms as defined in Loan Agreement; not otherwise def… — full verbatim in JSON | amended by 0000947871-25-000313 |

_Source §: 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313_

- **Covenant terms — Loan Facilities Agreement (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Principal / commitment amount | RMB 800,000,000.00 yuan (Eight hundred million). Initial Commitments per Annex I: Bank of China, Huzhou Branch RMB 250 million; China Construction Bank, Huzhou Branch RMB 250 million; Bank of Huzhou,… — full verbatim in JSON | base (footer) |
| Interest / coupon rate | LPR + 115 bps · Floating rate: one-year LPR published by the National Interbank Funding Center plus 115 bps, reset every 12 months | base (footer) |
| Default Interest Rate | Late Default Interest Rate: 150% of applicable Interest Rate; Misappropriation Default Interest Rate: 200% of applicable Interest Rate | base (footer) |
| Maturity date | December 10, 2026 · December 10, 2026 (Loan Term of 5 years) | base (footer) |
| Financial-maintenance covenants | Financial indicators clause present but stated value is [/] (left blank). Note: covenant 3) states 'the Borrower shall ensure that the final total financing balance for the Project does not exceed RM… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Security Documents = Guarantee Contract/Maximum Guarantee Contract, Mortgage Contract/Maximum Mortgage Contract and/or Pledge Contract/Maximum Pledge Contract. Mortgagor = Microvast Power Systems Co.… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | Events of Default (Art. 15.1): Misrepresentation; Breach of contract/other obligations; Payment default; Material payment default (two consecutive/three total); Misappropriation of loans; Cross defau… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm_

- **Covenant terms — material contracts (10-K exhibit index) (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Principal / commitment amount | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Interest / coupon rate | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Maturity date | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Security / collateral / guarantors | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Mandatory prepayment / events of default | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |

_Source §: fenced Tier-2 extraction (verbatim, source-bound)_


### Reference: CIQ implied equity at peer-median multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 423.1
  - ↳ `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-24`
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $126.10M, − total debt $326.00M
  - ↳ `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-06-24`
- **Implied equity at peer-median ($M, CIQ)** — ↳ `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-06-24`  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 550.7 |
| NTM Revenue (Capital IQ) | 1,070.4 |
| NTM EBITDA (Capital IQ) | 877.0 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

---
> **No BUY/AVOID here — this dossier only assembles and cites.** The verdict is the human's, logged separately via the ledger with a frozen entry price.