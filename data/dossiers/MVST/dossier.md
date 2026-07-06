# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 228 · ref 2026-07-06 · assembled 2026-07-06 14:58 UTC · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+0.3s fetch)
- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on/after 2026-05-15 (the latest embedded revision event), so it is up to 52d before the 2026-07-06 reference — beyond the 45d tolerance — and the true export date is unknown, so freshness cannot be confirmed. Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar).
- Possible false balance — evidence_balance commits a strong lean but the body is near-symmetric (6 bull vs 11 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

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
- **Name 180d return:** -60.5%
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
  - **Conversion:** ⇒ ~$0.50/sh at 2 sh per $1.00 · Conversion Price = $1.00 divided by the applicable Conversion Rate at such time. Conversion Rate = two (2) shares of Co…
  - **Interest / coupon:** Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK) · Term SOFR + Applicable Margin; Applicable Margin = 9.75% per annum; Floor = 3.00% per annum; 3.75% of interest paid in-…
  - **Maturity:** May 28, 2026 · “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026”
  - **Financial maintenance:** not less than $5,000,000 weekly · Minimum Liquidity: not less than $5,000,000, tested as of Friday of each calendar week (Liquidity Testing Date), from t…
  - **Events of default:** “no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment” (condition…
- **Covenants — Loan Facilities Agreement** (governing values; full verbatim in appendix):
  - **Interest / coupon:** Floating rate + 115 bps · Floating rate: one year LPR published by the National Interbank Funding Center Plus 115 bps; reset every 12 months. LPR…
  - **Maturity:** December 10, 2026 · ending on (and including) [December 10, 2026], [5] years in total. Repayment schedule (Ten Thousand Yuan): 6/10/2023 30…
  - **Financial maintenance:** 9. Financial indicator: The Borrower shall meet the following financial indicators: [/] (blank). Also Covenant 3): the…
  - **Events of default:** 12 enumerated; acceleration · Events of Default (Article 15.1): 1. Misrepresentation; 2. Breach of contract or other obligations; 3. Payment default;…

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

**Evidence balance:** strongly-bearish — stated going-concern doubt with a 48% YoY revenue drop and adjusted EBITDA turned negative outweigh the trailing-margin turnaround.

### Bull case (overshoot / mean-revert)
- The margin trajectory is a genuine multi-year turnaround, not an optical print: GAAP gross margin climbed -28%→4%→19%→31%→36% (2021→2025) and EBITDA margin swung from -118% to +17% while absolute EBITDA moved from -$180M to +$74M — the real signal is an inflection to positive operating cash generation, not a fading percentage.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- LTM free cash flow is positive at $39.6M and FCF sign is +1, a structural break from the -$136M/-$117M/-$65M capex-heavy burn of 2021-2024, evidencing the ramp capex has passed its peak.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x (LTM EBITDA / interest) indicates the debt is currently serviceable out of operating earnings despite the leverage headline.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- The $25.0M shareholder convertible loan maturing 2026-05-28 was resolved by conversion to equity (Mr. Wu's full-principal Notice of Conversion), removing a near-term cash maturity rather than requiring a cash repayment.
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`
- The peer discount (name TEV/EBITDA 11.1x vs peer median 14.5x, -23%) sits against a HETEROGENEOUS peer set spanning $34M–$275.0B caps (8063x), so the question for the human is whether the discount is EARNED or RESIDUAL — and the fundamental_deltas show the name's EBITDA margin (14%) and EBITDA growth (21%) exceed the peer medians (6%, 1%), which cuts against a purely earned discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The FY25 gross-margin decline is largely a one-off: a $32.5M ESS inventory impairment cut reported margin by 7.6 points, so the underlying 2025 gross margin was ~36.2% vs the 28.6% GAAP print — a value-obscuring charge, not a demand collapse.
  - ↳ `8-K 0001628280-26-018235 EX-99.1`

### Bear case (terminal / value-trap)
- The latest 10-Q states SUBSTANTIAL DOUBT about going concern with plans present — an explicit survival flag that outweighs the trailing-margin recovery narrative.
  - ↳ `10-Q 0001628280-26-033590`
- The FY25 adjusted-EBITDA recovery reversed in Q1-26: adjusted EBITDA was -$5.5M vs +$28.5M a year earlier and adjusted net income was -$14.6M vs +$19.3M — the profitability that anchors the trailing multiple has gone negative on a company-adjusted basis.
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- On the company-adjusted LTM EBITDA basis (~$10.7M), net-debt/EBITDA is ~18.7x — far worse than the 3.9x CIQ GAAP-basis figure — meaning the headline leverage understates the strain once impairment/one-offs are stripped correctly.
  - ↳ `CIQ leverage bases + release LTM adj-EBITDA/margins`
- Total-debt/EBITDA of 5.8x is nearly triple the peer median of 2.0x, and credit-health solvency/liquidity scores (2/2) are weaker than the peer-median (3/3 scale where lower=stronger reverses) — leverage is a genuinely worse-than-peer fundamental partly earning the discount.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- Q1-26 revenue collapsed to $60.6M, down 48% YoY (volume ~536MWh→~274MWh), and LTM revenue has rolled from the $428M FY25 peak to $372M — the top line is contracting sharply, not ramping.
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- Customer concentration is intensifying and dangerous: Customer A rose to 52.0% of revenue (from 31.0%) and Customer B to 18.0% (from 16.0%), so two customers now drive ~70% of a single 100%-battery-segment business.
  - ↳ `10-Q 0001628280-26-033590`
- Consensus forward estimates have been cut hard: FY26 revenue -27% (609→444), FY26 EBITDA -52% (129.7→62.1), FY26 EPS-Normalized -83% (12m→latest), and the target price was cut $7→$6→$5 — the forward path is deteriorating, not stabilizing.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- Guidance credibility is impaired: most-recent resolved revenue guide was MISSED (FY25) and the CIQ FY26 revenue guide (427.5) is a stale vendor-echo of prior-FY actual, with 2026 revenue outlook stated only QUALITATIVELY (no number).
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- Short interest is rising (+22.9% to 26.3M sh, 7.9% of shares out) while insiders show 0 open-market buys against 7 sells — positioning signals reinforce the bearish tape.
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,571,432 screen 90d ADV`
- The trailing TEV/LTM EBITDA of 10.0x is trailing-only with no forward basis and sits at the 0th percentile of a 4-close (<8q) window, so the 'cheap' read cannot distinguish cheap-overshoot from cheap-terminal — this optical multiple is a MISREAD, not a clean signal.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- The stock fell -60% over 180d vs IWM +16% (-81% relative), driven by discrete earnings gap-downs (2026-03-17, 2026-05-12) — an idiosyncratic, filing-tied de-rating rather than a market-wide drawdown.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Decisive question
**Is the Q1-26 revenue-and-adjusted-EBITDA collapse a temporary Phase-3.2-ramp/Korea/EMEA air-pocket that reverses as new capacity comes online, or the start of a demand-and-liquidity decline that the going-concern doubt makes terminal?**

### …evidence for
- Management frames the YoY dip as temporary, tied to Phase 3.2 ramp timing and customer-platform delays, with capacity expected to contribute to a continued 2026 revenue ramp.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- LTM FCF is positive ($39.6M) and interest coverage is 10.6x, giving some self-funding capacity to bridge a ramp gap.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- The near-term $25.0M shareholder convertible maturity was resolved by conversion to equity rather than cash repayment.
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`

### …evidence against
- The 10-Q states SUBSTANTIAL DOUBT about going concern, and latest-quarter OCF turned negative even as LTM FCF stayed positive, so the self-funding read is MIXED — not clean.
  - ↳ `10-Q 0001628280-26-033590`
- Adjusted EBITDA flipped to -$5.5M in Q1-26 from +$28.5M a year earlier while revenue fell 48% YoY, and consensus FY26 EBITDA was cut 52% — the deterioration is broad and forward-looking, not a single soft quarter.
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- Customer A concentration jumped to 52% of revenue, so the revenue base now hinges on one customer's ordering pattern.
  - ↳ `10-Q 0001628280-26-033590`

### Key unknowns
- Cash-runway visibility is opaque: no forward cash-runway disclosure and going-concern doubt is stated with 'plans present' but the plans' adequacy is undisclosed — a BEARISH gap, not neutral.
- No forward/adjusted EV/EBITDA or adjusted EPS is available (not in the 99.1 revised guidance), so overshoot-vs-terminal on a forward basis cannot be adjudicated from the data.
- TEV/LTM EBITDA is trailing-only at the 0th percentile of a <8q (4-close) window — the floor read is explicitly low-confidence and belongs unresolved, not counted as bull or bear.
- FY26 revenue outlook is QUALITATIVE only (no number stated); the CIQ 427.5 guide is a flagged stale vendor-echo of prior-FY actual — true management revenue guidance is unknown.
- No segment-level EBITDA breakout exists (Segments sheet lacks an EBITDA section) — profitability by product/region is undisclosed.
- Covenant basis for leverage is UNKNOWN (not disclosed); the $5M minimum-liquidity covenant on the converted shareholder loan and financial-indicator covenants on the China facility exist but current headroom is not quantified.
- The $111.2M maturity wall due ≤12m (filing basis) — how it is refinanced/repaid given going-concern doubt and negative latest-Q OCF is unresolved.
- Peer set is HETEROGENEOUS (caps 8063x span); whether the -23% TEV/EBITDA discount is EARNED (worse leverage/growth) or RESIDUAL (overshoot) is for the human to judge, not computed here.

### Twin reference cases
- **Romeo Power** — went terminal (LLM-claimed — verify)
  - distinguished by: US SPAC-listed EV/commercial battery-systems maker with heavy customer concentration and mounting cash strain that could not scale to self-funding before the balance sheet forced resolution.
  - source: [LLM-suggested, unverified]
- **Microvast Holdings (FY25 inventory-impairment episode)** — recovered
  - distinguished by: The name's own prior optical-margin shock — a discrete non-cash inventory impairment obscured an otherwise-improving underlying gross margin, illustrating how one-offs can misprice a trailing metric.
  - source: 8-K 0001628280-26-018235 EX-99.1
- **Amprius Technologies** — recovered
  - distinguished by: A same-roster US lithium-ion peer carrying negative EBITDA margin yet a far larger market cap, showing this cohort can trade on future-capacity narrative rather than current profitability.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Leclanché SA** — went terminal
  - distinguished by: A same-roster small-cap battery-systems maker with deeply negative EBITDA margin and net debt on a small cap — the value-trap end of the exposed-peer distribution.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)


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
| Conversion price / mechanics | ⇒ ~$0.50/sh at 2 sh per $1.00 · Conversion Price = $1.00 divided by the applicable Conversion Rate at such time. Conversion Rate = two (2) shares of Common Stock (subject to adjustment) per $1.00 principal amount of the Loans. Part… — full verbatim in JSON | base (footer) |
| Principal / commitment amount | Initial Term Loan Commitment: $12,000,000. Delayed Draw Term Loan Commitment: $13,000,000. | base (footer) |
| Interest / coupon rate | Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK) · Term SOFR + Applicable Margin; Applicable Margin = 9.75% per annum; Floor = 3.00% per annum; 3.75% of interest paid in-kind (PIK) on each interest payment date; Default Rate = Applicable Margin incre… — full verbatim in JSON | base (footer) |
| Maturity date | May 28, 2026 · “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026” | amended by 0000947871-25-000313 |
| Financial-maintenance covenants | not less than $5,000,000 weekly · Minimum Liquidity: not less than $5,000,000, tested as of Friday of each calendar week (Liquidity Testing Date), from the Closing Date until the Maturity Date. | base (footer) |
| Security / collateral / guarantors | Guarantors: Microvast Holdings, Inc. (as Holdings and a Guarantor), Microvast Advanced Materials Inc., Microvast Advanced Membrane Inc., Microvast Energy, Inc., Microvast Power Solutions, Inc., Micro… — full verbatim in JSON | amended by 0000947871-25-000313 |
| Mandatory prepayment / events of default | “no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment” (condition to effectiveness); and “there exists no Default or Event of Default, in each cas… — full verbatim in JSON | amended by 0000947871-25-000313 |

_Source §: 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313_

- **Covenant terms — Loan Facilities Agreement (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Principal / commitment amount | aggregate amount up to RMB [800,000,000.00] yuan (In words: RMB [Eight hundred million] yuan). Annex I Lenders' Initial Commitment: Bank of China, Huzhou Branch 250 million; China Construction Bank,… — full verbatim in JSON | base (footer) |
| Interest / coupon rate | Floating rate + 115 bps · Floating rate: one year LPR published by the National Interbank Funding Center Plus 115 bps; reset every 12 months. LPR means the one-year RMB Loan Prime Rate. Default Interest Rate: Late Default Int… — full verbatim in JSON | base (footer) |
| Maturity date | December 10, 2026 · ending on (and including) [December 10, 2026], [5] years in total. Repayment schedule (Ten Thousand Yuan): 6/10/2023 3000; 12/10/2023 7000; 6/10/2024 10000; 12/10/2024 10000; 6/10/2025 10000; 12/10/2… — full verbatim in JSON | base (footer) |
| Financial-maintenance covenants | 9. Financial indicator: The Borrower shall meet the following financial indicators: [/] (blank). Also Covenant 3): the Borrower shall ensure that the final total financing balance for the Project doe… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Mortgagor / Pledgor = Microvast Power Systems Co., Ltd. Mortgage Contract = three mortgage contracts (# HuKai 2022 C113, #HuKai 2022 C114, #HuKai 2022 C115) signed by the Mortgagor and the Agent on 1… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | 12 enumerated; acceleration · Events of Default (Article 15.1): 1. Misrepresentation; 2. Breach of contract or other obligations; 3. Payment default; 4. Material payment default (two consecutive times or three times in total); 5.… — full verbatim in JSON | base (footer) |

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
| Vesting schedule (RSUs) | Vesting Dates: First anniversary of the Grant Date; Second anniversary of the Grant Date; Third anniversary of the Grant Date; one-third vests on each | base (footer) |
| Settlement mechanics | One Share per vested RSU (or cash value equal to Fair Market Value of a Share on the applicable Vesting Date); settled by Settlement Date, no later than March 15 of the year following the Vesting Dat… — full verbatim in JSON | base (footer) |
| Forfeiture on termination | Unvested RSUs forfeited on any Termination of Employment; all RSUs (vested-unsettled or unvested) forfeited on Termination for Cause | base (footer) |
| Change in Control | Unvested RSUs treated per Plan; vested-unsettled RSUs settled immediately prior to Change in Control | base (footer) |
| Dividend Equivalents | Dividend Equivalents credited; cash dividends converted into additional RSUs at Fair Market Value on dividend payment date; share dividends converted one-for-one; same vesting/settlement terms as und… — full verbatim in JSON | base (footer) |
| Transfer restrictions | Non-transferable except by will or laws of descent and distribution | base (footer) |
| Clawback | Subject to clawback/recoupment per applicable law and Company policy | base (footer) |
| Governing law | State of Delaware | base (footer) |

_Source §: latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm_


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