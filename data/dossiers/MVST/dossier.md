# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-07-04 08:56 UTC · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on/after 2026-05-15 (the latest embedded revision event), but the true export date is unknown, so freshness vs the 2026-06-22 reference cannot be confirmed. Re-pull, or corroborate against a dated sibling CIQ export.

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
- **Name 180d return:** -58.1%
  - ↳ `EOD MVST 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -82.2%
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

- **Maturity wall** (deterministic, vs the 2026-06-22 reference):
  - **matured (pre-reference): $25.0M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-05-28 (25d before ref): $13.0M Convertible Loan With Shareholder 
    - 2026-05-28 (25d before ref): $12.0M Convertible Loan With Shareholder 
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
  - **Interest / coupon:** Term SOFR (+3.75% PIK) · Term SOFR + Applicable Margin (9.75% per annum); 3.75% of interest due paid in-kind (PIK Interest); Floor of 3.00% per…
  - **Maturity:** May 28, 2026 · “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026”
  - **Financial maintenance:** not less than $5,000,000 weekly · Minimum Liquidity: not less than $5,000,000, tested as of Friday of each calendar week (Liquidity Testing Date), from t…
  - **Events of default:** no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment; there exists…
- **Covenants — Loan Facilities Agreement** (governing values; full verbatim in appendix):
  - **Interest / coupon:** Floating rate + 115 bps · Floating rate: one-year LPR published by the National Interbank Funding Center Plus 115 bps, reset every 12 months. Def…
  - **Maturity:** December 10, 2026 · December 10, 2026 (5 years in total). Availability Period: from Effective Date to and including 9 June 2023
  - **Financial maintenance:** Financial indicators clause present but left blank ([/]). Related stated covenants: "the Borrower shall ensure that the…
  - **Events of default:** 12 enumerated · Events of Default (Article 15.1): 1. Misrepresentation; 2. Breach of contract or other obligations; 3. Payment default;…

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
| Revenue | 427.5 | FY 2026 | 2026-03-16 | 98d (stale) | actual ≥ floor 10/13 | FY 2025 MISSED |
| Capital Expenditure | '(180.00) - (210.00)' | FY 2023 | 2023-11-10 | 955d (stale) | spend ≤ ceiling 4/4 | FY 2023 MET |
| Gross Margin % | '32.00 - 35.00' | FY 2025 | 2025-11-10 | 224d (stale) | actual ≥ floor 4/4 | FY 2024 MET |

- **Consensus stats (target + ratings):** Target price: mean $5.50, median $5.50, high/low 6.00/5.00, N 2/2; Ratings: Buy 2, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-05-15 · export date unverified]
  - ↳ `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
- **Revision-event log** (47 events · 3 broker-days) — ↳ `CIQ Estimates→Recent Changes (47 broker revision events)  [data ≥ 2026-05-15 · export date unverified]`:
  - **2026-05-15 · H.C. Wainwright & Co.** — Upward Revision×3, Initiation of Coverage×9, Downward Revision×6:
    - Revenue FY 2026: 563.49→438.83 (cons 450.0→444.41)
    - EBITDA FY 2026: 146.5→62.08 (cons -→62.08)
    - EBIT FY 2026: 63.58→21.96 (cons 17.96→19.96)
    - Net Income (GAAP) FY 2026: 47.54→69.84 (cons 70.43→70.13)
    - EBT (GAAP) FY 2026: 59.42→75.69 (cons 70.43→73.06)
    - _+13 more line items in JSON_
  - **2026-05-11 · broker undisclosed** — Upward Revision×5, Downward Revision×8:
    - Net Income (GAAP) FY 2026: 17.63→70.43 (cons 17.63→70.43)
    - EBT (GAAP) FY 2026: 17.63→70.43 (cons 17.63→70.43)
    - Revenue FY 2026: 480.52→450.0 (cons 480.52→450.0)
    - Revenue FQ2 2026: 103.21→95.91 (cons 103.21→95.91)
    - EBIT FY 2026: 22.46→17.96 (cons 22.46→17.96)
    - _+8 more line items in JSON_
  - **2026-03-17 · broker undisclosed** — Downward Revision×16:
    - Net Income (Excl. Excep) FY 2026: 92.58→21.38 (cons -→21.38)
    - Revenue FY 2026: 525.0→480.52 (cons 525.0→480.52)
    - Net Income (Excl. Excep) FQ2 2026: 16.86→0.45 (cons -→0.45)
    - Gross Margin % FY 2026: 34.0→27.9 (cons -→27.9)
    - Gross Margin % FQ2 2026: 33.8→28.0 (cons -→28.0)
    - _+11 more line items in JSON_
- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 +0%; Revenue surprise: FY2021 +3%, FY2022 +2%, FY2023 +3%, FY2024 +6%, FY2025 -8% (GAAP-EPS basis; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`
- **Insider activity (Form 4, 6m):** Open-market buys 0 · sells 7 (net -121.0K sh) · grants 20 · last 2026-06-12 · other C×1
  - ↳ `EDGAR Form 4 (latest 0000947871-26-000620; 18 in 6m)`
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-15): 21.4M → 26.3M sh (+22.9%, rising) · 7.9% of shares out (EDGAR XBRL) · DTC 5.7d · recent: 2026-06-15 26.3M · 2026-05-29 21.4M · 2026-05-15 21.6M · 2026-04-30 21.2M
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,607,454 screen 90d ADV`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Batteries / Battery Systems 428 (100%) of Total 428
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Ashok Leyland Limited (NSEI:ASHOKLEY) — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K; BAIC BluePark New Energy Technology Co., Ltd. (SHSE:600733) — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Cargotec Solutions LLC — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Jbm Electric Vehicles Private Limited — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Kinglong United Automotive Industry (Suzhou) Co., Ltd — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; TREPEL Airport Equipment GmbH — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K
  - ↳ `CIQ Customers&Suppliers Microvast Holdings Inc NasdaqCM MVST Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] China 139 (33%); Other Asia & Pacific 3 (1%); Italy 93 (22%); France 78 (18%); Other Europe 41 (10%); U.S. 39 (9%); India 35 (8%) of Total 428
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

## Synthesis

**Evidence balance:** mixed — a genuine multi-year EBITDA/FCF inflection collides head-on with a -48% revenue collapse, sharp downgrades, and elevated leverage.

### Bull case (overshoot / mean-revert)
- The name is FCF-positive ($39.6M LTM levered FCF) and self-funding, with interest coverage 10.6x, so near-term liquidity does not depend on external capital.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- The $25.0M shareholder convertible loan maturing 2026-05-28 was resolved by conversion to equity (Notice of Conversion for full principal), removing that near-term maturity as a cash claim.
  - ↳ `8-K 0000947871-26-000585 (2026-05-28)`
- On fundamental_deltas the name shows a HIGHER EBITDA margin (14% vs peer-median 6%) and higher EBITDA growth (21% vs 1%), raising whether the discount to the peer-median NTM TEV/EBITDA (7.46x vs 12.9x) is RESIDUAL/overshoot rather than fully EARNED — the human judges, not computed here.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Absolute EBITDA has swung from -$180M (FY21) through breakeven to +$74M (FY25) and +$52M LTM, with EBITDA margin turning positive to 17% (FY25) / 14% (LTM), a genuine multi-year operating inflection rather than a % artefact.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Full-year gross margin held at 36% (FY25) / 35% (LTM) and management attributes the FY25 dip to a one-off $32.5M inventory impairment (7.6pp), a genuine counter to the margin-erosion read — to be verified against the transcript.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Consensus EBITDA is expected to roughly double from FY26E $62.1M to FY27E $147.7M, and forward multiples de-rate sharply (FY27 TEV/EBITDA 4.26x, FY28 3.47x) if that ramp lands — posing whether the trailing cheapness is overshoot on a recovering base.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus EBITDA, latest snapshot)`

### Bear case (terminal / value-trap)
- Leverage is elevated — net-debt/EBITDA 3.9x and comps total-debt/EBITDA 5.8x vs peer-median 2.0x — an EARNED component of the discount, worse than peers on the balance sheet even before growth.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- Q1-26 GAAP net profit of $48.2M was driven by a $63.8M non-cash fair-value gain on warrants/convertible loan; the underlying adjusted result was a net LOSS of $14.6M and YTD adjusted EBITDA of -$5.5M, so the headline profit overstates operating health.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Revenue is contracting hard — Q1-26 $61M vs $116M a year earlier (-48% per the call), LTM revenue $372M down from FY25 $428M, and reported rev growth -10% vs peer-median +1% — the decline is a REAL signal, not an optical artefact, since absolute revenue is falling alongside the %.
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`
- The 14% EBITDA margin fell to 0% in Q1-26 (EBITDA $0M on $61M revenue), and absolute LTM EBITDA slipped to $52M from FY25's $74M — here the margin % AND absolute EBITDA are BOTH deteriorating, so the recent quarter is a genuine setback, not a % that fell while EBITDA rose.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- Forward estimates have been cut sharply: FY26 consensus revenue -27% (609→444) and FY26 EBITDA -52% (129.7→62.1) over the revision path, confirming a real downgrade cycle, not just price weakness.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- The name relies on a single Batteries/Battery-Systems segment (100% of revenue) with meaningful China/Korea regulatory exposure and a 3.5 beta vs peer-median 1.1, amplifying downside sensitivity.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Short interest is rising (21.4M→26.3M shares, +22.9%, 7.9% of float, 5.7d to cover) and insiders show open-market sells 7 / buys 0 (net -121K sh), a negative positioning signal.
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,607,454 screen 90d ADV`
- The stock fell -58% over 180d vs IWM +18% (-82% relative), driven by discrete earnings gap-downs (2026-03-17, 2026-05-12), an idiosyncratic collapse not a market move.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Decisive question
**Is the sharp Q1-26 revenue/EBITDA collapse a temporary volume trough (Phase 3.2 ramp timing + Korea regulatory + EMEA platform delays) that reverses into the FY27 EBITDA doubling consensus expects, or the start of a durable demand/margin deterioration on a levered balance sheet?**

### …evidence for
- Consensus still models EBITDA roughly doubling from FY26E $62.1M to FY27E $147.7M and revenue rising to $591.5M, implying the trough is transitory.
  - ↳ `CIQ Estimates→Trends (FY26/FY27 consensus Revenue, latest snapshot)`
- Management frames the YoY dip as temporary, tied to Phase 3.2 capacity coming online in 2026 and EMEA platform delays beginning to reach SOP.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Gross margin held ~35% in Q1-26 despite low utilization, suggesting pricing/mix strength rather than structural margin loss.
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`

### …evidence against
- Q1-26 revenue fell to $61M (from $116M) and EBITDA to $0M, and FY26 consensus revenue/EBITDA were already cut -27%/-52% on the revision path.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- The most recent resolved revenue guide MISSED (FY2025), and FY25 revenue surprise was -8%, denting the credibility of forward guidance.
  - ↳ `CIQ Estimates→Surprise (annual)`
- Leverage of 3.9x net-debt/EBITDA (5.8x total-debt vs peer 2.0x) leaves little room if the volume recovery slips further.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`

### Key unknowns
- No forward/adjusted EV/EBITDA basis is disclosed — valuation.ev_ebitda is trailing-only, so cheap-overshoot vs cheap-terminal cannot be distinguished from the multiple alone.
- No revised-outlook 99.1 exhibit was parsed for the earnings 8-Ks — revised FY26 guidance is UNKNOWN, an opaque gap where a forward guide is expected (bearish until disclosed).
- Segment-level EBITDA is not disclosed (Segments sheet has no EBITDA section) — profitability by product/geography cannot be assessed.
- Adjusted net-debt/EBITDA and adjusted EPS are not in the revised guidance — true leverage/earnings power on an adjusted basis is unresolved.
- Covenant financial-maintenance terms are partly blank/left open (Loan Facilities Agreement indicators clause blank; convertible minimum-liquidity $5M) — headroom is not fully verifiable.
- Peer set is HETEROGENEOUS (caps $34M–$275B, 8063x span) — every peer multiple is a confidence-gated input, not a clean benchmark; the earned-vs-residual split cannot be cleanly read.
- Only 2 sell-side estimates (both Buy, target $5.50, N=2) and a single initiating broker (H.C. Wainwright) drive consensus — thin coverage limits the reliability of the FY27 ramp anchor.
- Export date of the CIQ estimates pull is unverified (a floor ≥ 2026-05-15) — the true snapshot may be weeks staler than assumed.
- Trailing EV/EBITDA range rests on only 4 closes (<8q) — the 0th-percentile 'floor' read is low-confidence and unreliable.

### Twin reference cases
- **QuantumScape** — went terminal (LLM-claimed — verify)
  - distinguished by: SPAC-era battery-tech name that stayed pre-scale/cash-burning long after de-rating; analogue for a battery story whose technology narrative outran commercial delivery.
  - source: [LLM-suggested, unverified]
- **Amprius Technologies** — recovered
  - distinguished by: US lithium-ion peer in the same roster still at negative EBITDA margin but high revenue growth — analogue for a small battery name where the market pays for a growth ramp despite unprofitability.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Forsee Power S.A.** — went terminal
  - distinguished by: Same-roster European battery-systems maker at negative EBITDA margin and shrinking revenue — analogue for a sub-scale name where a declining top line compounds a weak balance sheet.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Microvast Holdings (own FY21→FY25 arc)** — recovered
  - distinguished by: The name's own resolved trajectory from deeply negative EBITDA through breakeven to positive — analogue for whether the current dip is another leg of a self-improving operating story.
  - source: CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)
- **Romeo Power** — went terminal (LLM-claimed — verify)
  - distinguished by: EV-battery SPAC that couldn't fund the ramp as demand and customer platforms slipped — analogue for a levered battery name whose capacity build outran realized volume.
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


### Capital-structure provenance (full panel · pointers · terms)
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

|  | Governing value (verbatim, or UNKNOWN) | Source § (base · amended by) |
|---|---|---|
| Conversion price / mechanics | Conversion Price = $1.00 divided by the applicable Conversion Rate at such time. Conversion Rate = two (2) shares of Common Stock (subject to adjustment) per $1.00 principal amount of the Loans. Partial-conversion minimum: $100,000 principal amount, or an integral multiple of $100,000 in excess thereof. Conversion right exercisable at any time prior to the Close of Business on the Scheduled Trading Day immediately preceding the Maturity Date. Restricted Ownership Percentage 9.99% (Section 16 Conversion Blocker). | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Principal / commitment amount | Initial Term Loan Commitment: $12,000,000 (100% Yang Wu per Annex I); Delayed Draw Term Loan Commitment: $13,000,000 (100% Yang Wu per Annex I) | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Interest / coupon rate | Term SOFR + Applicable Margin (9.75% per annum); 3.75% of interest due paid in-kind (PIK Interest); Floor of 3.00% per annum; Default Rate = Applicable Margin increased by 3.00% per annum upon Event of Default | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Maturity date | “November 28, 2025” in clause (a) of the definition of “Maturity Date” is deleted and replaced with “May 28, 2026” | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313 |
| Financial-maintenance covenants | Minimum Liquidity: not less than $5,000,000, tested as of Friday of each calendar week (Liquidity Testing Date), from the Closing Date until the Maturity Date | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm |
| Security / collateral / guarantors | Guarantors: Microvast Holdings, Inc.; Microvast Advanced Materials Inc.; Microvast Advanced Membrane Inc.; Microvast Energy, Inc.; Microvast Power Solutions, Inc.; Microvast GmbH. Liens/rights securing payment of the Obligations ratified and confirmed. Agent: Acquiom Agency Services LLC, as administrative agent and collateral agent. | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313 |
| Mandatory prepayment / events of default | no Default or Event of Default shall have occurred and be continuing or shall be caused by this Amendment; there exists no Default or Event of Default, in each case, after giving effect to this Amendment | 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313 |

- **Covenant terms — Loan Facilities Agreement (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (verbatim, or UNKNOWN) | Source § (base · amended by) |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Principal / commitment amount | aggregate amount up to RMB 800,000,000.00 yuan (RMB Eight hundred million yuan). Initial Commitments (Annex I): Bank of China, Huzhou Branch RMB 250 million; China Construction Bank, Huzhou Branch RMB 250 million; Bank of Huzhou, Co. RMB 150 million; China Zheshang Bank, Huzhou Branch RMB 150 million | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Interest / coupon rate | Floating rate: one-year LPR published by the National Interbank Funding Center Plus 115 bps, reset every 12 months. Default Interest: Late Default Interest Rate = 150% of applicable Interest Rate; Misappropriation Default Interest Rate = 200% of applicable Interest Rate. Interest calculated on daily basis, daily interest rate = corresponding annual rate/360 | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Maturity date | December 10, 2026 (5 years in total). Availability Period: from Effective Date to and including 9 June 2023 | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Financial-maintenance covenants | Financial indicators clause present but left blank ([/]). Related stated covenants: "the Borrower shall ensure that the final total financing balance for the Project does not exceed RMB 800 million, and the final proportion of equity funds is not less than 45%"; "The Borrower shall ensure that the equity fund of the Project in an amount of RMB 500 million is in place before the disbursement of Loans" | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Security / collateral / guarantors | Mortgage Contract means three mortgage contracts (with contract NO. of # HuKai 2022 C113, #HuKai 2022 C114, #HuKai 2022 C115 respectively) signed by the Mortgagor and the Agent on 1 September 2022. Mortgagor means Microvast Power Systems Co., Ltd. Pledgor means Microvast Power Systems Co., Ltd. Guarantor means [/] (blank); Guarantee Contract means a [/] guarantee contract signed between the Guarantor and the Agent on [/]. Covenant: "The property and equipment of the Project will be mortgaged to the syndicate when they are available for the mortgage" | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Mandatory prepayment / events of default | Events of Default (Article 15.1): 1. Misrepresentation; 2. Breach of contract or other obligations; 3. Payment default; 4. Material payment default (two consecutive times or three times in total); 5. Misappropriation of loans; 6. Cross default (RMB 1000 yuan or more); 7. Insolvency (RMB 1,000,000 Yuan or more); 8. Liquidation and bankruptcy events; 9. Enforcement events (RMB 30,000,000 yuan or more, not released within 90 Business Days); 10. Financial indicators failure; 11. Material Adverse Effects; 12. Invalidity of Finance Documents. Mandatory prepayment/compulsory cancellation: change of control (Art 7.4): "The Agent (acting on instructions of all Lenders ) shall, after giving at least 10 Business Days' prior notice to the Borrower , require the Borrower to prepay the loans and cancel the Total Commitments"; Change in law (Art 11): "The Borrower shall, within [10] Business Days after receiving a request from Lenders Affected by Change in Law , prepay to Lenders Affected by Change in Law its participation in any Outstanding Loans and the interests accrued thereon." Covenant 10: "the Lenders have the right to require the Borrower to prepay all the syndicated loan." | 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |

- **Covenant terms — material contracts (10-K exhibit index) (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (verbatim, or UNKNOWN) | Source § (base · amended by) |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Principal / commitment amount | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Interest / coupon rate | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Maturity date | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Security / collateral / guarantors | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Mandatory prepayment / events of default | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Instrument type | Restricted Stock Unit Award Agreement under the Microvast Holdings, Inc. 2021 Equity Incentive Plan | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Vesting schedule | One-third of the RSUs vest on each of the first, second and third anniversaries of the Grant Date, subject to continued employment | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Settlement | One Share per vested RSU, or at Company's option the cash value (Fair Market Value of a Share on the applicable Vesting Date); settled no later than March 15 of the year following vesting | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Forfeiture on termination | Unvested RSUs forfeited on any termination; all RSUs (vested-unsettled and unvested) forfeited on termination for Cause | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Change in Control | Unvested RSUs treated per the Plan; vested unsettled RSUs settled immediately prior to the Change in Control | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Dividend Equivalents | Dividend Equivalents credited and converted into additional RSUs; subject to same vesting/settlement terms as the corresponding Award | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Transfer restrictions | Non-transferable except by will or laws of descent and distribution | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Clawback | Subject to clawback/recoupment per applicable law or Company policy | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Governing law | State of Delaware | latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |


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