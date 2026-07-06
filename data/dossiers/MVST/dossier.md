# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 228 · ref 2026-07-06 · assembled 2026-07-06 16:16 UTC · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+0.3s fetch)
- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on/after 2026-05-15 (the latest embedded revision event), so it is up to 52d before the 2026-07-06 reference — beyond the 45d tolerance — and the true export date is unknown, so freshness cannot be confirmed. Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar).
- **Unreconciled margin-compression** — The $74M FY25 EBITDA benefited from a $32.5M inventory impairment structure and non-cash items — gross margin fell 7.6pts on the impairment, and FY25 revenue landed BELOW guidance (MISSED), the most recent resolved guide.
  - _where:_ a bear point
  - _why it matters:_ cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)
- Possible false balance — evidence_balance commits a strong lean but the body is near-symmetric (7 bull vs 10 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case

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
  - **Conversion:** ⇒ ~$0.50/sh at 2 sh per $1.00 · Conversion Price = $1.00 divided by the applicable Conversion Rate. Conversion Rate = two (2) shares of Common Stock pe…
  - **Interest / coupon:** Term SOFR (for applicable Interest Period) plus Applicable Margin. “Applicable Margin” means 9.75% per annum. Floor: 3.…
  - **Maturity:** May 28, 2026 · “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026”
  - **Financial maintenance:** not less than $5,000,000 weekly · Minimum Liquidity: from the Closing Date until the Maturity Date, Liquidity of the Borrower and its Subsidiaries, as of…
  - **Events of default:** “no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment”; “there exi…
- **Covenants — Loan Facilities Agreement** (governing values; full verbatim in appendix):
  - **Interest / coupon:** Floating rate + 115 bps · Floating rate: one-year LPR published by the National Interbank Funding Center Plus 115 bps, reset every 12 months. Lat…
  - **Maturity:** December 10, 2026 · December 10, 2026 (5 years total). Repayment schedule (Ten Thousand Yuan): 6/10/2023 3000; 12/10/2023 7000; 6/10/2024 1…
  - **Financial maintenance:** Article 14.1 Clause 9 (Financial indicator) states: "The Borrower shall meet the following financial indicators: [/]" —…
  - **Events of default:** acceleration · Events of Default (Art. 15.1): 1) Misrepresentation; 2) Breach of covenants/other obligations; 3) Payment default; 4) M…

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

**Evidence balance:** strongly-bearish — a stated going-concern doubt with a ~$111M near-term wall above cash and negative company-adjusted Q1 EBITDA outweighs the margin-repair narrative.

### Bull case (overshoot / mean-revert)
- LTM levered free cash flow is positive at $39.6M, a real reversal from −$136M (2022) / −$117M (2023), indicating the business can partly self-fund at the trailing level.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- LTM interest coverage of 10.6x cushions the leverage, meaning the debt is serviceable on a trailing EBITDA basis despite elevated absolute debt.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- The $25.0M shareholder convertible loan due 2026-05-28 was resolved by conversion into equity rather than a cash call, removing one near-term maturity from the wall (dilutive, not a default).
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`
- Forward consensus EBITDA rebuilds sharply — FY26E $62.1M and FY27E $147.7M against revenue of $444.4M → $591.5M — implying the trailing trough is expected to be transitory.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus EBITDA, latest snapshot)`
- The name shows better fundamentals than the peer median on several axes cited in the comps — EBITDA margin 14% vs 6% and EBITDA growth 21% vs 1% — posing whether any discount is RESIDUAL rather than fully EARNED; but this is a HETEROGENEOUS peer set (caps $34M–$275.0B, 8063x) so the median is not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The Q1-2026 revenue collapse to $60.6M (−48% YoY) is management's framed 'temporary' dip tied to a Phase 3.2 capacity ramp not yet aligned with customer demand, not a demand-loss signal per se.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- The 5-year margin arc is genuine structural repair — EBITDA margin went −118% (2021) → +17% (2025), with absolute EBITDA turning from −$180M to +$74M, so the falling recent margin % is not a collapse in the absolute-EBITDA reconciler beside it.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`

### Bear case (terminal / value-trap)
- The latest 10-Q states SUBSTANTIAL DOUBT about going concern (with plans present) — the single most load-bearing terminal-risk fact, directly qualifying every self-funding and forward-EBITDA claim.
  - ↳ `10-Q 0001628280-26-033590`
- Company-disclosed adjusted EBITDA was NEGATIVE $5.5M in Q1-2026 (vs +$28.5M prior year) and adjusted net loss −$14.6M — the GAAP net profit of $48.2M is a non-cash warrant/convertible fair-value swing of $63.8M, so the reported profit is optical, not operational.
  - ↳ `8-K 0001628280-26-033601 EX-99.1`
- On the company's own adjusted LTM EBITDA (~$10.7M), net-debt/EBITDA is ~18.7x — far above the 3.9x GAAP-basis headline — so the 'self-funding' leverage read is a basis artifact and the real leverage may be distress-level.
  - ↳ `CIQ leverage bases + release LTM adj-EBITDA/margins`
- A $111.2M maturity wall falls due within 12 months (filing basis), against only $126M cash — a near-term refinancing/liquidity squeeze, not a comfortable runway.
  - ↳ `10-Q 0001628280-26-033590`
- Customer concentration jumped sharply — Customer A now 52.0% of revenue (prior 31.0%) and Customer B 18.0% (prior 16.0%) — a fragile single-customer dependence on a shrinking top line.
  - ↳ `10-Q 0001628280-26-033590`
- Revenue is decelerating hard: Q1-26 $61M is −37% QoQ and −48% YoY by volume (274 MWh vs 536 MWh), and the LTM revenue trend (372) has rolled over from the FY25 peak (428).
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`
- Forward FY26 consensus has been cut aggressively — EBITDA −52% (129.7→62.1) and revenue −27% (609→444.4) over the 12m→latest path — so the 'rebound' anchor is itself a marked-down number, and the FY26 revenue guide echoes prior-year actual (vendor-echo/stale carry-forward).
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- The $74M FY25 EBITDA benefited from a $32.5M inventory impairment structure and non-cash items — gross margin fell 7.6pts on the impairment, and FY25 revenue landed BELOW guidance (MISSED), the most recent resolved guide.
  - ↳ `8-K 0001628280-26-018235 EX-99.1`
- The name is heavily China-anchored operationally (China 33% of revenue; multiple Chinese-bank term loans and a CNY convertible) with a shareholder-conversion capital structure, adding governance/geopolitical fragility.
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`
- Short interest is rising (+22.9% to 26.3M sh, 7.9% of float) and insiders are net sellers (0 buys, 7 sells) — positioning and insider signal both lean negative.
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,571,432 screen 90d ADV`

### Decisive question
**Can the company refinance/clear its ~$111M near-term maturity wall and re-accelerate revenue off the Phase 3.2 ramp before cash and dilution exhaust the equity — i.e., is the trough temporary (overshoot) or the start of the going-concern spiral (terminal)?**

### …evidence for
- LTM FCF is positive $39.6M and interest coverage 10.6x, and the near-term shareholder convertible was cleared by equity conversion rather than cash.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Forward consensus rebuilds EBITDA to $62.1M (FY26E) then $147.7M (FY27E) as Phase 3.2 capacity comes online, supporting a transitory-trough reading.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus EBITDA, latest snapshot)`

### …evidence against
- The 10-Q itself states SUBSTANTIAL DOUBT about going concern, and Q1-26 company-adjusted EBITDA was negative $5.5M with an adjusted net loss.
  - ↳ `10-Q 0001628280-26-033590`
- The $111.2M maturity wall due within 12 months exceeds the $126M cash balance while revenue fell −48% YoY, so the runway is thin against a falling top line.
  - ↳ `10-Q 0001628280-26-033590`

### Key unknowns
- The revised-guidance 99.1 exhibit was not parsed and the 2026 revenue outlook is QUALITATIVE-only (no number stated) — no forward number to test the ramp against (opacity = bearish risk).
- No forward/adjusted EV/EBITDA or adjusted EPS in the revised guidance — the trailing 10.0x multiple cannot distinguish cheap-overshoot from cheap-terminal.
- Covenant basis for leverage is UNKNOWN (not disclosed); minimum-liquidity covenants exist on the convertible loan but headroom vs the ~$111M wall is not visible — a missing survival-capacity leg.
- No segment-level EBITDA disclosure (Segments sheet has no EBITDA section) — profitability of the single 100% battery segment is opaque.
- Self-funding is MIXED: latest-Q OCF is negative while LTM FCF is positive — the two-input read does not confirm self-funding at the current quarterly run-rate.
- Peer set is HETEROGENEOUS (caps $34M–$275.0B); every peer multiple is a confidence-gated input, so the discount cannot be read as a clean overshoot.
- The full text of both earnings-call transcripts and the specifics of the going-concern 'plans' are not synthesized here and must be read for management's mitigation credibility.
- CIQ export date is unverified (a floor ≥2026-05-15); the true snapshot may be weeks newer, so consensus/positioning figures may be stale.

### Twin reference cases
- **Romeo Power** — went terminal (LLM-claimed — verify)
  - distinguished by: US SPAC-era commercial-EV battery pack maker with customer-concentration and ramp/liquidity dependence that could not bridge to scale before cash ran short.
  - source: [LLM-suggested, unverified]
- **Amprius Technologies** — recovered
  - distinguished by: A source-roster small-cap battery peer still pre-profit (negative EBITDA margin) yet market-supported on growth optionality — the overshoot-vs-terminal question turns on funding access.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Leclanché SA** — went terminal
  - distinguished by: A source-roster small-cap battery-systems peer with deeply negative EBITDA and chronic financing dependence — the value-trap analogue where perpetual capital needs erode equity.
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
| Conversion price / mechanics | ⇒ ~$0.50/sh at 2 sh per $1.00 · Conversion Price = $1.00 divided by the applicable Conversion Rate. Conversion Rate = two (2) shares of Common Stock per $1.00 principal amount of the Loans (subject to adjustment). Partial-conversio… — full verbatim in JSON | base (footer) |
| Principal / commitment amount | Initial Term Loan Commitment: $12,000,000 (Closing Date). Delayed Draw Term Loan Commitment: $13,000,000 (Closing Date). Annex I: YANG WU — Initial Term Loan Commitment $12,000,000.00 (100.00%); Dela… — full verbatim in JSON | base (footer) |
| Interest / coupon rate | Term SOFR (for applicable Interest Period) plus Applicable Margin. “Applicable Margin” means 9.75% per annum. Floor: 3.00% per annum (Term SOFR deemed the Floor if lower). PIK Interest: 3.75% of the… — full verbatim in JSON | base (footer) |
| Maturity date | May 28, 2026 · “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026” | amended by 0000947871-25-000313 |
| Financial-maintenance covenants | not less than $5,000,000 weekly · Minimum Liquidity: from the Closing Date until the Maturity Date, Liquidity of the Borrower and its Subsidiaries, as of Friday of each calendar week (each a “Liquidity Testing Date”), not less than $… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Guarantors: Microvast Holdings, Inc. (as Holdings and a Guarantor), Microvast Advanced Materials Inc., Microvast Advanced Membrane Inc., Microvast Energy, Inc., Microvast Power Solutions, Inc., Micro… — full verbatim in JSON | amended by 0000947871-25-000313 |
| Mandatory prepayment / events of default | “no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment”; “there exists no Default or Event of Default, in each case, after giving effect to this Am… — full verbatim in JSON | amended by 0000947871-25-000313 |
| Governing law | State of New York (including Section 5-1401 of the General Obligations Law of the State of New York), without regard to conflict of laws principles | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Underlying agreement / date | First Amendment to Loan and Security Agreement dated March 17, 2025, amending the Loan and Security Agreement dated May 28, 2024 | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Lender | Yang Wu (Initial Lender); Acquiom Agency Services LLC as Agent | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Fees and expenses | Borrower to pay all reasonable and documented out-of-pocket expenses of Agent and Lenders in accordance with Section 10.4 of the Loan Agreement | 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |

_Source §: 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313_

- **Covenant terms — Loan Facilities Agreement (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Principal / commitment amount | RMB 800,000,000.00 yuan (Eight hundred million yuan). Annex I Initial Commitments: Bank of China, Huzhou Branch RMB 250 million; China Construction Bank, Huzhou Branch RMB 250 million; Bank of Huzhou… — full verbatim in JSON | base (footer) |
| Interest / coupon rate | Floating rate + 115 bps · Floating rate: one-year LPR published by the National Interbank Funding Center Plus 115 bps, reset every 12 months. Late Default Interest Rate = 150% of applicable Interest Rate; Misappropriation Def… — full verbatim in JSON | base (footer) |
| Maturity date | December 10, 2026 · December 10, 2026 (5 years total). Repayment schedule (Ten Thousand Yuan): 6/10/2023 3000; 12/10/2023 7000; 6/10/2024 10000; 12/10/2024 10000; 6/10/2025 10000; 12/10/2025 10000; 6/10/2026 15000; 12/1… — full verbatim in JSON | base (footer) |
| Financial-maintenance covenants | Article 14.1 Clause 9 (Financial indicator) states: "The Borrower shall meet the following financial indicators: [/]" — the specific indicators are left blank ([/]). Related Article 14 undertakings s… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Mortgagor / Pledgor: Microvast Power Systems Co., Ltd. Mortgage Contract: three mortgage contracts (# HuKai 2022 C113, #HuKai 2022 C114, #HuKai 2022 C115) signed 1 September 2022. Guarantor: [/] (lef… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | acceleration · Events of Default (Art. 15.1): 1) Misrepresentation; 2) Breach of covenants/other obligations; 3) Payment default; 4) Material payment default (fails to pay two consecutive times or three times in to… — full verbatim in JSON | base (footer) |

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