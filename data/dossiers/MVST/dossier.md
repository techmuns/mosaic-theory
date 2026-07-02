# Dossier — Microvast Holdings, Inc. (MVST)

_Finalist rank 272 · ref 2026-06-22 · assembled 2026-07-02 22:38 · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on/after 2026-05-15 (the latest embedded revision event), but the true export date is unknown, so freshness vs the 2026-06-22 reference cannot be confirmed. Re-pull, or corroborate against a dated sibling CIQ export.

## Mechanical layer (source-bound facts — assembles & cites, never concludes)

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
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001628280-26-018235', '0001628280-26-033601']

_Did it happen alone? (idiosyncratic vs shared — the G2-vs-market compensation):_
- **Name 180d return:** -58.1%
  - ↳ `EOD MVST 180d to 2026-06-22`
- **Market (IWM) 180d return:** 18.0%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -82.2%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — MVST in graph but no US-listed exposed names to price

### Leverage & survival (unified — both bases labeled, no net-vs-total mixing)
- **Net debt / EBITDA (CIQ NET basis):** 3.9x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ EBITDA $52M [LTM 12 months Mar-31-2026]`
- **Total debt / EBITDA (comps — name vs peer median):** name 5.8x vs peer median 2.0x (comps TOTAL-debt/EBITDA basis)
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- **Net debt / OCF:** 4.4x
  - ↳ `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ OCF $46M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj covenant basis):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Interest coverage:** 10.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Survival (self-funding + nearest wall):** net-debt/EBITDA 3.9x (CIQ) | FCF-positive → self-funding | nearest maturity wall: 2026
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign + CIQ Capital Structure (survival capacity)`
- **Credit health (S&P-MI scores — scale labeled):** name Overall/Operational/Solvency/Liquidity 3/3/2/2 (S&P issuer rating unrated); peer-median O/Op/S/L 2.5/2.5/3/3; scale 1=strongest … 4=weakest (S&P-MI PD model)
  - ↳ `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-24`

- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 39.6
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Liquidity / covenant flags:** Convertible Bond - CNY (Bonds and Notes) 42 @ 3.000% - 4.000% Due 2027; Convertible Loan With Shareholder - Delayed Draw Term Loan (Term Loans) 13 @ NA Due 2026; Convertible Loan With Shareholder - Initial Term Loan (Term Loans) 12 @ NA Due 2026; Loan Facilities Agreement With a Group of Lenders Led by a Bank in China (Term Loans) 43 @ NA Due 2026; Long-term Loan Agreement With a Chinese Bank (Term Loans) 14 @ 2.700% Due 2027; Notes Payable (Bonds and Notes) 78 @ NA; Operating Lease Liabilities (Capital Lease) 17 @ 5.000%; Short-term Loan Agreements and Bank Facilities With Chinese Banks (Term Loans) 50 @ 2.400% - 4.850% Due 2027
  - ↳ `CIQ Financials→Capital Structure Details`

### Trajectory (revenue · EBITDA · margins · ROIC)
- **Trajectory ($M · % — per period)** — ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`  <!-- ds-table -->

|   | Dec-2021 | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 | Dec-2025 | Mar-2026 (LTM) |
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
- **P/E:** _UNKNOWN_ — no positive EPS/price
- **EV/EBITDA (GAAP TEV/LTM):** 10.0x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Own-history range position:** EV/EBITDA (TEV/LTM) 10.0x as-of 2026-03-31 — trailing range 15.8–66.9x (median 24.9x) over 4 closes → LOW-CONFIDENCE (4 closes < 8q ≈2y) — floor read unreliable
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Peer comps (CIQ Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business)** — ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`  <!-- ds-table -->

|   | Mkt cap | Business |
|---|---|---|
| Amprius Technologies | $2.0B | develops, manufactures, and markets lithium-ion (United States) |
| Forsee Power S.A. | $34M | designs, manufactures, and sells battery systems for (France) |
| Cummins Inc. | $96.5B | offers various power solutions worldwide. The company (United States) |
| BorgWarner Inc. | $14.5B | provides technology solutions for combustion, hybrid, (United States) |
| Contemporary Amperex Technology Co. | $275.0B | engages in the research, development, production, and (China) |
| Panasonic Holdings Corporation | $64.4B | develops, manufactures, sells, services, and supplies (Japan) |
| Leclanché SA | $167M | designs, develops, and manufactures customized turnkey (Switzerland) |
| Samsung SDI Co. | $24.8B | manufactures and sells batteries in South Korea, (Gyeonggi-do  South) |

_the name: $423M_

- **Comparability (confidence gate):** market caps span $34M–$275.0B (8063x); the name is $423M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)** — ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`  <!-- ds-table -->

|   | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| TEV/Rev | 1.7 | 0.7 | 3.2 | 5.8 | 22 |
| TEV/EBITDA | 11.1 | 7.9 | 14.5 | 18.5 | 38.4 |
| P/E | NM | 22.6 | 39 | 38.9 | 54.9 |
| NTM TEV/Rev | 1.25 | 1.06 | 2.55 | 3.64 | 13.47 |
| NTM TEV/EBITDA | 7.46 | 7.63 | 12.9 | 43.3 | 198.12 |
| NTM P/E | 14.11 | 13.27 | 22.77 | 26.23 | 55.1 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · margin · growth · leverage — name vs peers)** — ↳ `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-24`  <!-- ds-table -->

|   | Cap | EBITDA margin | Rev growth (1y) | EBITDA growth (1y) | Total debt/EBITDA | Net debt ($M) |
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


### Implied valuation (CIQ-computed at peer multiples — POSED, not concluded)
> **Comparability gate:** market caps span $34M–$275.0B (8063x); the name is $423M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
> _Composition first — the human judges earned vs residual (not a machine upside)._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 423.1
  - ↳ `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-24`
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $126.10M, − total debt $326.00M
  - ↳ `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-06-24`
- **Implied EQUITY value ($M, CIQ)** — ↳ `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-06-24`  <!-- ds-table -->

|   | Low | Median | Mean | High |
|---|---|---|---|---|
| LTM Total Revenue | 64.3 | 1,004.4 | 1,963.7 | 7,962.6 |
| LTM EBITDA | 212.5 | 550.7 | 760.2 | 1,794.7 |
| LTM EBIT | 21.8 | 193.9 | 163.1 | 242.9 |
| NTM Revenue (Capital IQ) | 329.6 | 1,070.4 | 1,616.4 | 6,521.1 |
| NTM EBITDA (Capital IQ) | 437.0 | 877.0 | 3,415.6 | 16,341.2 |
| NTM EPS (Capital IQ) | 397.9 | 682.6 | 786.5 | 1,652.1 |
| LTM Tangible Book Value/Share | 385.1 | 2,139.1 | 2,972.4 | 8,131.3 |



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
- **Guidance bridge (latest guide + track-record):** Revenue: latest guide 427.5 for FY 2026 (dated 2026-03-16) (stale — 98d old); actual ≥ guided floor 10/13 resolved; most recent resolved: FY 2025 MISSED; Capital Expenditure: latest guide '(180.00) - (210.00)' for FY 2023 (dated 2023-11-10) (stale — 955d old); spend ≤ guided ceiling 4/4 resolved; most recent resolved: FY 2023 MET; Gross Margin %: latest guide '32.00 - 35.00' for FY 2025 (dated 2025-11-10) (stale — 224d old); actual ≥ guided floor 4/4 resolved; most recent resolved: FY 2024 MET  [data ≥ 2026-05-15 · export date unverified]
  - ↳ `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
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

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Batteries / Battery Systems 428 (100%) of Total 428
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** Ashok Leyland Limited (NSEI:ASHOKLEY) — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K; BAIC BluePark New Energy Technology Co., Ltd. (SHSE:600733) — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Cargotec Solutions LLC — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Jbm Electric Vehicles Private Limited — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; Kinglong United Automotive Industry (Suzhou) Co., Ltd — Customer · Automobile Manufacturers · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2026 Form 10-K; TREPEL Airport Equipment GmbH — Customer · Construction Machinery and Heavy Transportation Equipment · src: Microvast Holdings, Inc. (NasdaqCM:MVST) 2025 Form 10-K
  - ↳ `CIQ Customers&Suppliers Microvast Holdings Inc NasdaqCM MVST Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] China 139 (33%); Other Asia & Pacific 3 (1%); Italy 93 (22%); France 78 (18%); Other Europe 41 (10%); U.S. 39 (9%); India 35 (8%) of Total 428
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** mixed — a real multi-year margin/FCF turnaround now colliding with a 48% YoY revenue collapse, high leverage, and a 2026 maturity wall.

### Bull case (overshoot / mean-revert)
- The name is self-funding: LTM levered free cash flow is +$39.6M and FCF sign is positive, a real inflection from years of cash burn (FY22 -136, FY23 -117).
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage of 10.6x indicates the current debt load is comfortably serviced out of LTM EBITDA despite the elevated leverage ratio.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- The multi-year arc is a genuine turnaround: EBITDA margin swung from -118% (2021) to +14% LTM while absolute EBITDA moved from -180 to +52, so the falling margin % from the 17% FY25 peak is a mix/volume optical dip against a still-positive absolute base, not a return to losses.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- On the fundamental_deltas the name screens BETTER than the peer median on the profitability and growth axes that matter — EBITDA margin 14% vs 6%, EBITDA growth 21% vs 1% — posing whether the discount to peers is RESIDUAL (overshoot) rather than fully earned; but the HETEROGENEOUS peer set (caps $34M–$275B) gates this as a confidence-limited input, not a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Both covering brokers rate the name Buy with a $5.50 mean target, and the recent H.C. Wainwright revisions lifted FY26 GAAP net income to $70.1M (+110% vs 12m ago), a bullish earnings-path signal.
  - ↳ `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
- The forward multiple ladder collapses steeply (FY26 TEV/EBITDA 10.1x → FY27 4.3x → FY28 3.5x), consistent with consensus modelling a sharp EBITDA re-acceleration off the trough rather than a terminal fade.
  - ↳ `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`

### Bear case (terminal / value-trap)
- Leverage is high and above peers: net-debt/EBITDA 3.9x, and on the comps TOTAL-debt/EBITDA basis 5.8x vs peer median 2.0x — this is an EARNED leg of any discount, a value-trap input, not an overshoot.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- Revenue is contracting sharply at the trough: Q1-26 revenue $61M is down 48% YoY (management: volume 536MWh→274MWh), and LTM revenue $372M has already rolled below FY25's $428M — the top-line direction is DOWN, not merely a soft print.
  - ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`
- EBITDA margin has retraced from the 17% FY25 peak to 14% LTM and hit 0% in Q1-26; read WITH the reconciler this is the REAL signal at the quarterly frequency — absolute quarterly EBITDA fell to ~$0M in Q1-26 — not merely an optical percentage dip, so the deceleration is genuine even though the multi-year absolute base remains positive.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- The GAAP net profit is an accounting artifact: reported Q1-26 GAAP net profit of $48.2M rested on a $63.8M non-cash fair-value gain on warrant/convertible liabilities, beneath which management disclosed an adjusted net LOSS of $14.6M and YTD adjusted EBITDA of NEGATIVE $5.5M vs +$28.5M a year prior.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- The stock fell on discrete earnings gap-downs (2026-03-17 and 2026-05-12, both 8-K item 2.02 results), i.e. the de-rating is idiosyncratic and reaction to reported numbers, not a market-wide drawdown — name -58% vs IWM +18% over 180d (rel -82%).
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- The trailing TEV/LTM EBITDA sits at its own-history floor (10.0x, 0th percentile of a 4-close window), but this is trailing-only with no forward basis and cannot on its own distinguish cheap-overshoot from cheap-terminal.
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`

### Decisive question
**Is the Q1-26 revenue collapse (-48% YoY, $61M) and the drop of quarterly EBITDA to ~$0 a TEMPORARY Phase-3.2 ramp/tariff air-pocket that re-accelerates on new capacity and the KAF/school-bus program, or the start of a structural volume decline that leaves 5.8x total-debt leverage stranded against a 2026 maturity wall?**

### …evidence for
- Management frames the YoY dip as temporary, tied to Phase-3.2 capacity timing aligning with customer demand and expecting a continued revenue ramp through 2026, with SOP expected in 2026.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- Consensus models a sharp forward recovery — FY27E revenue $592M (+33%) and FY27E EBITDA $148M (25% margin) — well above the LTM trough.
  - ↳ `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
- The forward TEV/EBITDA ladder steps down hard (FY26 10.1x → FY27 4.3x), consistent with a modelled earnings re-acceleration off the trough.
  - ↳ `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`

### …evidence against
- The nearest maturity wall is 2026 and the capital structure carries multiple Chinese term loans and shareholder convertible loans due 2026, against only $126M cash — a refinancing/liquidity risk if the volume trough persists.
  - ↳ `CIQ Financials→Capital Structure Details`
- Underlying profitability inverted at the trough: YTD adjusted EBITDA is negative $5.5M vs +$28.5M a year prior and adjusted net loss $14.6M, so the recovery has not yet begun in the cash-relevant figures.
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
- FY26 consensus revenue has been cut 27% over 12 months (609 → 444) and FY26 EBITDA cut 52% (130 → 62), so the forward recovery estimates themselves are being marked down, not held.
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`

### Key unknowns
- The 2026 maturity-wall refinancing plan is not disclosed: multiple term loans and shareholder convertible loans are due 2026 against $126M cash, and no cash-runway/refinancing visibility is provided — an opaque, bearish-leaning gap.
- No forward/adjusted EV-EBITDA basis and no adjusted EPS are in the revised 99.1 guidance, so the trailing 10.0x floor cannot be resolved into cheap-overshoot vs cheap-terminal.
- No revised-outlook 99.1 exhibit was parsed for either gap-down 8-K, so the specific guidance revision that drove the de-rating is not in evidence.
- Segment EBITDA is not disclosed (100% single Battery Systems segment reported for revenue only), so profitability by product/region — including the loss-making vs profitable mix inside the volume drop — is invisible.
- The KAF school-bus/290Ah program and Phase-3.2 SOP are pre-revenue narrative with no order book, timeline-to-revenue, or capex funding quantified — execution risk unquantified.
- Peer set is HETEROGENEOUS (caps span 8063x), so every peer multiple and delta is a confidence-gated input; the earned-vs-residual split of the discount cannot be cleanly read off this roster.
- Revenue YoY comparability is muddied by reclassified (R) periods; the true same-basis trajectory through the trough is partly obscured.
- Export date is unverified (a floor ≥2026-05-15), so consensus and revision figures may be staler than the true pull.

### Twin reference cases
- **Enovix** — recovered
  - distinguished by: Advanced-battery developer that swung through a capacity-ramp trough with volatile quarterly volumes before demand for its differentiated cell technology re-accelerated the top line.
  - source: [LLM-suggested, unverified]
- **Romeo Power** — went terminal
  - distinguished by: Commercial-vehicle battery-pack integrator with heavy customer/platform concentration whose ramp costs and funding needs overwhelmed a thin cash position when volumes disappointed.
  - source: [LLM-suggested, unverified]
- **Microvast Holdings** — recovered
  - distinguished by: The name's OWN prior arc: years of deep negative EBITDA and cash burn (2021–2023) inflected to positive absolute EBITDA and positive FCF by 2025 — evidence the current dip follows an earlier successful margin/cash turn.
  - source: CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)
- **Leclanché SA** — went terminal
  - distinguished by: A same-roster small-cap battery-systems peer carrying negative EBITDA margins and NM leverage — the value-trap end-state the leverage-and-volume-trough case warns against for sub-scale battery names.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)


## APPENDIX — FINANCIAL SUMMARY (actuals + consensus estimates) — export date unverified (data ≥ 2026-05-15)
### Annual (last-4-FY + LTM + FY26E/FY27E consensus)
- **Annual financials ($M; E = consensus)** — ↳ `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`  <!-- ds-table -->

|   | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
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

|   | Q2-24 | Q3-24 (R) | Q4-24 (R) | Q1-25 (R) | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
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

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** 2 earnings-call transcript(s) on file — read in full for management posture: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`

---
> **No BUY/AVOID here — this dossier only assembles and cites.** The verdict is the human's, logged separately via the ledger with a frozen entry price.