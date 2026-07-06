# Dossier — VERRA MOBILITY Corp (VRRM)

_Finalist rank 1 · ref 2026-07-06 · assembled 2026-07-06 15:00 UTC · LLM claude-opus-4-8_

## ⚠ Analyst caveats — verify before the verdict

- primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+0.6s fetch)
- RESOLVED (P/E basis) — trailing GAAP P/E 5.1x is one-time-distorted: latest GAAP EPS 0.85 is ~3.1× the recent median 0.28, so 5.1x is not a meaningful 'cheap' read. Clean read: forward adjusted guide $1.19–$1.25 → ~3.5x at the current price; CIQ P/LTM 16.8x uses a different (lower) trailing EPS basis.
- EV/EBITDA stale-price caveat — CIQ's Financials→Multiples current TEV/LTM 8.5x is priced at its last Close 2026-03-31, 97d before the 2026-07-06 reference; for a since-re-rated name this 'current' multiple AND the own-history range/percentile built on it are stale. The Comparable-Analysis sheet reads 4.7x on a current price — prefer that figure and re-pull the Financials multiple.
- **Distorted-P/E anchor** — On the peer comps the discount is stark (EV/EBITDA 4.7x vs peer median 10.3x; P/E 5.4x vs 15.6x), but the peer set is HETEROGENEOUS ($430M-$15.9B, 37x cap span) so whether the gap is EARNED or RESIDUAL is for the human to judge, not a clean overshoot signal.
  - _where:_ a bull point
  - _why it matters:_ the P/E is distorted (rests on a non-current/non-recurring EPS)
  - _how to verify:_ don't read it as cheap

## Mechanical layer

### Drawdown cause & idiosyncrasy — what happened, and did it happen alone?
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-25 earnings (2.02) + Reg-FD (7.01); 2026-05-27 Reg-FD (7.01) + other event (8.01); 2026-06-02 management change (5.02) + Reg-FD (7.01)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-25, 2026-05-27, 2026-06-02
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-25 → 2026-02-24 [`0001193125-26-067015`](https://www.sec.gov/Archives/edgar/data/1682745/000119312526067015/vrrm-20260224.htm)
    - items: 2.02 Results of Operations and Financial Condition, 7.01 Regulation FD Disclosure, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On February 24, 2026, Verra Mobility Corporation (the “ Company ”) issued a press release announcing its financial results for the quarter and fiscal year ended December 31, 2025. A copy of the press release is furnished as Exhibit 99.1 to this Current Report on Form 8-K
    - 7.01 Regulation FD Disclosure: Regulation FD Disclosure. The Company will host a conference call and live webcast to discuss its fourth quarter and full year 2025 financial results on February 24, 2026, at 5:00 p.m. Eastern time. Live and archived webcasts of the presentation will also be available on the Company’s investor relations website at ir.verramobility.com, although the Company reserves the right to discontinue that av
  - gap 2026-05-27 → 2026-05-26 [`0001193125-26-239351`](https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116d8k.htm)
    - items: 7.01 Regulation FD Disclosure, 8.01 Other Events, 9.01 Financial Statements and Exhibits
    - 7.01 Regulation FD Disclosure: Regulation FD Disclosure. On May 26, 2026, Verra Mobility Corporation (the “ Company ”) issued a press release that announced the Company received a termination notice from Avis Budget Group, Inc. (“ Avis Budget ”) regarding Avis Budget’s contract with the Company. The Company also provided revised full-year 2026 guidance. A copy of the press release is furnished as Exhibit 99.1 to this Current Re
    - 8.01 Other Events: Other Events. On May 26, 2026, the Company announced that it received a termination notice from Avis Budget regarding Avis Budget’s contract with the Company. Avis Budget is one of the Company’s significant Commercial Services customers and represented over 10% of the Company’s total revenue for the three months ended March 31, 2026 and year ended December 31, 2025
  - gap 2026-06-02 → 2026-06-01 [`0001193125-26-251522`](https://www.sec.gov/Archives/edgar/data/1682745/000119312526251522/d39754d8k.htm)
    - items: 5.02 Departure/Election of Directors or Certain Officers, 7.01 Regulation FD Disclosure, 9.01 Financial Statements and Exhibits
    - 5.02 Departure/Election of Directors or Certain Officers: Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers. On June 1, 2026, Verra Mobility Corporation (the “Company”) announced that the Board of Directors of the Company (the “Board”) approved the appointment of Jonathan Keyser as the Interim President and Chief Executive Officer of the Company, effective May
    - 7.01 Regulation FD Disclosure: Regulation FD Disclosure. On June 1, 2026, the Company issued a press release announcing the appointment of Jonathan Keyser as Interim President and Chief Executive Officer and related matters. A copy of the press release is furnished as Exhibit 99.1 to this Current Report on Form 8-K and is incorporated by reference herein. The information furnished pursuant to
- **Revised guidance (catalyst 8-K Ex-99.1):** Revised 2026 Full-Year Guidance Based on the Company’s year-to-date 2026 results and outlook for the remainder of the year including the aforementioned termination notice, Verra Mobility is revising its 2026 full-year financial outlook to the following: • Total Revenue of $985 million to $995 million • Adjusted EBITDA of $380 million to $385 million • Adjusted EPS of $1.19 to $1.25 • Free Cash Flow of $140 million to $150 million Underlying Assumptions for 2026 Full-Year Guidance • Weighted average fully diluted share count expected to be approximately 155 million shares for the full-year 2026 • Effective tax rate (including state taxes) is expected to be 28.0% to 29.0%, with approximately $50 million in total cash taxes expected to be paid in 2026. The effective tax rate for non-GAAP adju
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- **Event-impact quantifications (8-K EX-99.1, verbatim-bound):**
  - reduce revenue by $135–145M (2026 annualized) — [`8-K 0001193125-26-239351 EX-99.1`]
  - reduce segment profit by $120–125M (2026 annualized) — [`8-K 0001193125-26-239351 EX-99.1`]

_Did it happen alone? (idiosyncratic vs shared — the G2-vs-market compensation):_
- **Name 180d return:** -80.8%
  - ↳ `EOD VRRM 180d to 2026-07-06`
- **Market (IWM) 180d return:** 16.5%
  - ↳ `EOD IWM 180d to 2026-07-06`
- **Relative vs market:** -97.7%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — VRRM not in graph_coverage.json — no exposed cross-section to compare

### Leverage & survival
- **Net debt / EBITDA (CIQ NET basis):** 2.9x
  - ↳ `CIQ Net Debt $1,046M [Q1 Mar-31-2026] ÷ CIQ EBITDA $358M [LTM 12 months Mar-31-2026]`
- **Total debt / EBITDA (comps — name vs peer median):** name 3.0x vs peer median 1.9x (comps TOTAL-debt/EBITDA basis)
  - ↳ `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
- **Net debt / OCF:** 4.5x
  - ↳ `CIQ Net Debt $1,046M [Q1 Mar-31-2026] ÷ CIQ OCF $234M [LTM 12 months Mar-31-2026]`
- **Net debt / EBITDA (fwd-adj covenant basis):** ~2.6x fwd-adj (net debt $1,009M / FY26 adj-EBITDA $380–$385M)
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm (adj-EBITDA) + EDGAR net debt`
- **Interest coverage:** 5.6x
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- **Survival (self-funding + nearest wall):** net-debt/EBITDA 2.9x (CIQ); ~2.6x fwd-adj (net debt $1,009M / FY26 adj-EBITDA $380–$385M) | FCF-positive → self-funding
  - ↳ `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign (survival capacity)`
- **Self-funding — two-input read (supersedes the line above):** self-funding: YES — latest-Q OCF > 0 AND LTM FCF > 0
  - ↳ `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
- **Credit health** — ↳ `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-24`  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 3 | 2 |
| Operational | 2 | 3 |
| Solvency | 4 | 2 |
| Liquidity | 2 | 3 |

_S&P issuer rating BB- · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** 53.9
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Feb-24-2026** — ↳ `CIQ Financials→Capital Structure Details (A 2025 filed Feb-24-2026)`  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|

_4 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** (deterministic, vs the 2026-07-06 reference):
  - due 2028: $687.1M
  - due 2029: $350.0M
  - due 2030: $0.0M
  - due 2037: $38.1M
  - _reconciliation: itemized $1,075.2M (panel A 2025 filed Feb-24-2026) vs the latest-quarter aggregates below — the gap is unitemized / newer term loans; read the QoQ movement in the aggregates line._
- **Capital-structure aggregates (latest quarter):** term loans 685.4 (687.1→685.4 QoQ); senior bonds 350.0; leases 46.2; total principal 1,110.4; total debt 1,101.8 (latest quarter) ($M)
  - ↳ `CIQ Financials→Capital Structure Summary`

### Primary-source cross-checks (8-K releases + latest 10-Q vs CIQ panel)

- **Going-concern language:** none in latest 10-Q — checked, absent [`10-Q 0001193125-26-209227`]
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure
  - ↳ `10-Q maturity wall vs CIQ capital panel (same window)`
- **EBITDA-basis triangulation (each leverage basis-labeled):**
  - net debt / EBITDA (CIQ, GAAP basis): 2.9x
  - total debt / EBITDA (CIQ comps, GAAP basis): 3.0x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: UNKNOWN (not disclosed)
  - ↳ `CIQ leverage bases + release LTM adj-EBITDA/margins`
- **Guide verification — CIQ guide vs release:** guide verification (revenue): CIQ 985.0–995.0 vs release 985.0–995.0 → cross-source VERIFIED
  - ↳ `CIQ revenue guide vs release actual/outlook`
- **Customer concentration (latest 10-Q):**
  - City of New York Department of Transportation: 15.2% (prior 15.4%)
  - ↳ `10-Q 0001193125-26-209227`

### Trajectory (revenue · EBITDA · margins · ROIC)
- **Trajectory ($M · % — per period)** — ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`  <!-- ds-table -->

|  | Dec-2021 (R) | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 (R) | Dec-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|---|
| Revenue ($M) | 551 | 742 | 817 | 879 | 979 | 979 |
| EBITDA ($M) | 229 | 304 | 306 | 342 | 362 | 358 |
| EBITDA margin | 42% | 41% | 37% | 39% | 37% | 37% |
| Gross margin | 64% | 63% | 62% | 61% | 58% | 57% |
| ROIC | 5.1% | 6.8% | 8.1% | 10.3% | 11.5% | 11.1% |

_Revenue YoY (latest same-quarter): +0.1% (Q1 Mar-31-2026 vs Q1 Mar-31-2025). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** buying back (trailing ~1.7y): 164,658,507 (2024-08-31) → 151,906,653 (2026-05-31), -7.7%
  - ↳ `EDGAR XBRL shares, trailing 2024-08-31..2026-05-31`

### Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 4.7x vs peer median 10.3x (-54%); P/E 5.4x vs peer median 15.6x (-65%)
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _price-implied fundamental levels at stated multiples — the human judges earned vs residual; identity (†): at the name's own multiple the implied level IS consensus._
  - _TEV as-of 2026-06-24 · multiples as-of 2026-06-09_
- **Price-implied levels (at each stated multiple)** — ↳ `TEV = mcap 668.4 + net debt 1046.3 (CIQ Comparable Analysis→Financial Data, Latest, as-of 2026-06-24) — simple-TEV basis`  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **4.7x** | **$364.8M EBITDA †** |
| peer-median NTM TEV/EBITDA | 8.33x | $205.8M EBITDA |
| peer-median LTM TEV/EBITDA | 10.3x | $166.5M EBITDA |
| **name NTM TEV/Rev** | **1.75x** | **$979.8M Revenue †** |
| peer-median NTM TEV/Rev | 1.79x | $957.9M Revenue |
| peer-median LTM TEV/Rev | 2x | $857.3M Revenue |

  - _Reads AGAINST the consensus path anchors below — juxtapose the price-implied level vs consensus per metric; never subtract one from the other._
- **Consensus path anchors (EBITDA — juxtapose, do NOT difference):** FY26E $382.4M · FY27E $333.0M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue — juxtapose, do NOT difference):** FY26E $988.8M · FY27E $947.5M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)
  - _vintage-coherent: derived FY26 $381.0M vs direct consensus $382.4M (residual 0.003 ≤ 0.10 tolerance)_
  - _Fixed multiple set (declared in code, no per-name curation): name NTM + peer-median NTM/LTM, on TEV/EBITDA and TEV/Rev._

- **P/E:** 5.1x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **EV/EBITDA (GAAP TEV/LTM):** 8.5x
  - ↳ `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
- **EV/EBITDA (adjusted, forward):** ~4.3x (fwd, at current $4.30; EV $1,662M / FY26 adj-EBITDA $380–$385M)
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm (adj-EBITDA) + EDGAR net debt + EOD price × shares`
- **Adjusted EPS (earnings power):** FY26 guide $1.19–$1.25; adj P/E ~3.5x at $4.30 — earnings power above the GAAP basis
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- **Own-history range position:** EV/EBITDA (TEV/LTM) 8.5x as-of 2026-03-31 — trailing range 10.4–23.2x (median 13.6x) over 19 closes → 0%ile → near-floor; P/LTM EPS 16.8x
  - ↳ `CIQ Financials→Multiples (Close; last col = current, excluded from history)`

### Peer comps
- **Peer set (roster · caps · business)** — ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| TaskUs | $430M | provides outsourced digital services for companies in (United States) |
| Tyler Technologies | $11.8B | provides integrated software and technology management (United States) |
| ExlService Holdings | $4.0B | operates as a data and artificial intelligence (“AI”) (United States) |
| SS&C Technologies Holdings | $15.9B | provides software products and software-enabled (United States) |
| Broadridge Financial Solutions | $15.8B | provides investor communications and technology-driven (United States) |
| Concentrix Corporation | $1.5B | designs, builds, and runs integrated customer (United States) |
| Genpact Limited | $4.8B | provides business process outsourcing and information (Hamilton HM 12 ) |

_the name: $668M_

- **Comparability (confidence gate):** market caps span $430M–$15.9B (37x); the name is $668M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)** — ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| TEV/Rev | 1.8 | 0.7 | 2 | 2.2 | 4.8 |
| TEV/EBITDA | 4.7 | 3.4 | 10.3 | 10 | 24.5 |
| P/E | 5.4 | 4.1 | 15.6 | 17.2 | 38.6 |
| NTM TEV/Rev | 1.75 | 0.66 | 1.79 | 2.06 | 4.38 |
| NTM TEV/EBITDA | 4.69 | 3.51 | 8.33 | 7.94 | 14.96 |
| NTM P/E | 5.5 | 2.01 | 9.39 | 9.7 | 21.06 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · margin · growth · leverage — name vs peers)** — ↳ `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-24`  <!-- ds-table -->

|  | Cap | EBITDA margin | Rev growth (1y) | EBITDA growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|
| SS&C Technologies Holdings | $15.9B | 32% | 7% | 6% | 3.6 | 7,200 |
| Broadridge Financial Solutions | $15.8B | 24% | 8% | 9% | 1.9 | 3,102 |
| Tyler Technologies | $11.8B | 19% | 9% | 13% | 0.1 | 298 (net cash) |
| Genpact Limited | $4.8B | 17% | 6% | 6% | 1.9 | 828 |
| ExlService Holdings | $4.0B | 17% | 13% | 15% | 1.3 | 267 |
| Concentrix Corporation | $1.5B | 12% | 4% | -4% | 3.4 | 5,467 |
| **Verra Mobility Corporation · the name** | **$668M** | **37%** | **10%** | **4%** | **3.0** | **1,046** |
| TaskUs | $430M | 18% | 16% | 23% | 2.2 | 396 |
| Peer median (peers) | $4.8B | 18% | 8% | 9% | 1.9 | 828 |



### Catalyst path (estimates · guidance · revisions) — export date unverified (data ≥ 2026-06-09)
- **Horizon read (FQ — next-2Q revision breadth)** — ↳ `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`:
  - EPS (GAAP) FQ2 2026: 1m 3↑/0↓, 2m 1↑/2↓, 3m 1↑/2↓
  - EPS (GAAP) FQ3 2026: 1m 1↑/5↓, 2m 0↑/6↓, 3m 0↑/6↓
  - Revenue FQ2 2026: 1m 1↑/2↓, 2m 1↑/4↓, 3m 1↑/4↓
  - Revenue FQ3 2026: 1m 0↑/7↓, 2m 0↑/7↓, 3m 0↑/7↓
  - EBITDA FQ2 2026: 1m 1↑/0↓, 2m 1↑/3↓, 3m 1↑/3↓
  - EBITDA FQ3 2026: 1m 0↑/5↓, 2m 0↑/5↓, 3m 0↑/5↓
  - EBIT FQ2 2026: 1m 1↑/0↓, 2m 2↑/2↓, 3m 2↑/2↓
  - EBIT FQ3 2026: 1m 0↑/4↓, 2m 0↑/4↓, 3m 0↑/4↓
  - Interest Expense FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - Interest Expense FQ3 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBT (GAAP) FQ2 2026: 1m 2↑/0↓, 2m 1↑/5↓, 3m 1↑/5↓
  - EBT (GAAP) FQ3 2026: 1m 1↑/5↓, 2m 0↑/6↓, 3m 0↑/6↓
  - Net Income (Excl. Excep) FQ2 2026: 1m 0↑/2↓, 2m 0↑/3↓, 3m 0↑/3↓
  - Net Income (Excl. Excep) FQ3 2026: 1m 0↑/4↓, 2m 0↑/4↓, 3m 0↑/4↓
  - Net Income (GAAP) FQ2 2026: 1m 1↑/6↓, 2m 0↑/6↓, 3m 0↑/6↓
  - Net Income (GAAP) FQ3 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/1↓
- **Acceleration read (monthly consensus path):** FY 2026 EPS (GAAP): 1.11 (12m) → 1.11 (9m) → 0.98 (6m) → 0.96 (3m) → 0.96 (2m) → 0.93 (1m) → 0.85 (latest); net -23% (12m→latest) | FY 2026 EPS Normalized: 1.50 (12m) → 1.49 (9m) → 1.36 (6m) → 1.35 (3m) → 1.35 (2m) → 1.36 (1m) → 1.23 (latest); net -18% (12m→latest) | FY 2026 Revenue: 998.8 (12m) → 1,000.5 (9m) → 1,022.6 (6m) → 1,025.2 (3m) → 1,025.2 (2m) → 1,025.2 (1m) → 988.8 (latest); net -1% (12m→latest) | FY 2026 EBITDA: 453.3 (12m) → 453.4 (9m) → 413.8 (6m) → 409.7 (3m) → 409.7 (2m) → 411.3 (1m) → 382.4 (latest); net -16% (12m→latest) | FY 2026 EBIT: 307.8 (12m) → 307.2 (9m) → 264.9 (6m) → 250.1 (3m) → 250.1 (2m) → 258.1 (1m) → 229.0 (latest); net -26% (12m→latest) | FY 2026 Interest Expense: -67.4 (12m) → -65.3 (9m) → -59.5 (6m) → -59.1 (3m) → -59.1 (2m) → -61.1 (1m) → -61.1 (latest); improving (magnitude toward zero) (12m→latest) | FY 2026 EBT (GAAP): 253.3 (12m) → 251.4 (9m) → 216.1 (6m) → 208.2 (3m) → 208.2 (2m) → 203.8 (1m) → 182.6 (latest); net -28% (12m→latest) | FY 2026 Net Income (Excl. Excep): 243.6 (12m) → 243.8 (9m) → 213.6 (6m) → 207.9 (3m) → 207.9 (2m) → 206.8 (1m) → 186.2 (latest); net -24% (12m→latest) | FY 2026 Net Income (GAAP): 179.7 (12m) → 178.7 (9m) → 153.8 (6m) → 148.9 (3m) → 148.9 (2m) → 147.2 (1m) → 127.7 (latest); net -29% (12m→latest)  [data ≥ 2026-06-09 · export date unverified]
  - ↳ `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
- **Cross-name anchor (NTM forward-multiple ladder)** — ↳ `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`:
  - NTM: TEV/REV 1.75 · TEV/EBITDA 4.70 · TEV/EBIT 8.50 · Price/Earnings 5.55 · PEG 2.94 · P/BV –
  - FY 2026: TEV/REV 1.74 · TEV/EBITDA 4.50 · TEV/EBIT 7.51 · Price/Earnings 5.24 · PEG 2.77 · P/BV 1.84
  - FY 2027: TEV/REV 1.82 · TEV/EBITDA 5.17 · TEV/EBIT 9.39 · Price/Earnings 6.07 · PEG 3.21 · P/BV 1.42
  - FY 2028: TEV/REV 1.79 · TEV/EBITDA 4.85 · TEV/EBIT 7.83 · Price/Earnings 5.36 · PEG 2.83 · P/BV 1.11
  - _+2 later fiscal years in JSON_
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — ↳ `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| EPS Normalized | '1.19 - 1.25' | FY 2026 | 2026-05-26 | fresh | actual ≥ floor 3/3 | FY 2025 MET |
| Revenue | '985.00 - 995.00' | FY 2026 | 2026-05-26 | fresh | actual ≥ floor 8/10 | FY 2025 MET |
| EBITDA | '380.00 - 385.00' | FY 2026 | 2026-05-26 | fresh | actual ≥ floor 8/10 | FY 2025 MET |
| Capital Expenditure | -125.0 | FY 2026 | 2026-05-26 | fresh | spend ≤ ceiling 5/6 | FY 2025 MISSED |

- **Consensus stats (target + ratings):** Target price: mean $9.71, median $6.00, high/low 28.00/4.00, N 7/7; Ratings: Buy 0, Outperform 1, Hold 6, Underperform 1, Sell 0, No Opinion 0, Buy 1, Outperform 0, Hold 0, Underperform 0, Sell 0  [data ≥ 2026-06-09 · export date unverified]
  - ↳ `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
- **Revision-event log** (250 events · 12 broker-days) — ↳ `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-06-09 · export date unverified]`:
  - **2026-06-09 · CJS Securities, Inc.** · 2↑/0↓ · Target Price Non-periodic 10.0→12.0 · +1 items in JSON
  - **2026-06-01 · broker undisclosed** · 1↑/16↓ · EBITDA FY 2026 410.9→382.1 · +16 items in JSON
  - **2026-05-29 · broker undisclosed** · 13↑/14↓ · EBITDA FY 2026 382.7→383.0 · +26 items in JSON
  - **2026-05-28 · broker undisclosed** · 0↑/0↓ · +29 items in JSON
  - **2026-05-27 · broker undisclosed** · 9↑/46↓ · EBITDA FY 2026 415.2→383.8 · +65 items in JSON
  - **2026-05-27 · CJS Securities, Inc.** · 9↑/10↓ · EBITDA FQ2 2026 90.3→97.4 · +18 items in JSON
  - _+6 more broker-days in JSON_
- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2021 +9%, FY2022 +4%, FY2023 -32%, FY2024 -76%, FY2025 -11%; Revenue surprise: FY2021 +2%, FY2022 +0%, FY2023 +1%, FY2024 +0%, FY2025 +2% (GAAP-EPS basis; +beat / −miss)
  - ↳ `CIQ Estimates→Surprise (annual)`
- **Insider activity (Form 4, 6m):** Open-market buys 0 · sells 0 (net +0.0K sh) · grants 4 · last 2026-06-18 · other F×21/M×23
  - ↳ `EDGAR Form 4 (latest 0001123292-26-000914; 24 in 6m)`
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-15): 5.0M → 7.7M sh (+54.9%, rising) · 5.1% of shares out (EDGAR XBRL) · DTC 1.2d · recent: 2026-06-15 7.7M · 2026-05-29 5.0M · 2026-05-15 3.4M · 2026-04-30 4.0M
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 7,741,661 short ÷ 6,237,412 screen 90d ADV`

### Concentration
- **Segments (revenue share):** [12 months Dec-31-2025] Commercial Services 436 (45%); Parking Solutions 83 (8%); Government Solutions 461 (47%) of Total 979
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** [12 months Dec-31-2025] Commercial Services 283 (68%); Parking Solutions 11 (3%); Government Solutions 122 (29%) of segment-EBITDA sum (pre-corporate) 416; consolidated EBITDA 362 (~54 unallocated corporate)
  - ↳ `CIQ Financials→Segments (EBITDA, latest annual column) + Income Statement (consolidated EBITDA)`
- **Customers:** Avis Budget Group, Inc. (NasdaqGS:CAR) — Customer · Passenger Ground Transportation · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K; Enterprise Holdings, Inc. — Customer · Passenger Ground Transportation · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K; New York City Department of Transportation — Customer · Diversified Support Services · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K; The Hertz Corporation — Customer · Passenger Ground Transportation · src: Verra Mobility Corporation (NasdaqCM:VRRM) 2026 Form 10-K
  - ↳ `CIQ Customers&Suppliers Verra Mobility Corporation NasdaqCM VRRM Customers.rtf`
- **Geographic:** [12 months Dec-31-2025] Australia 66 (7%); United Kingdom 28 (3%); Canada 32 (3%); ALL Other 7 (1%); United States 846 (86%) of Total 979
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

## Synthesis

**Evidence balance:** mixed — a company-quantified permanent loss of a >10% customer plus a CEO exit, against a self-funding, FCF-positive core with a durable Government annuity.

### Bull case (overshoot / mean-revert)
- The business is FCF-positive and self-funding with LTM levered FCF of $53.9M and FY26 guided FCF of $140-150M, so the de-rate is not a solvency event.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Interest coverage is 5.6x and leverage ~2.9x net-debt/EBITDA (~2.6x fwd-adj), with an undrawn revolver and no near-term maturity wall — the capital structure is serviceable.
  - ↳ `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
- Management has met the guided floor on the resolved track record (EPS 3/3, revenue 8/10, EBITDA 8/10; FY2025 MET) and reaffirmed a fresh FY26 guide dated 2026-05-26 that already incorporates the Avis loss.
  - ↳ `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
- On fundamentals the name screens BETTER than the peer median on margin (37% vs 18%), revenue growth (10% vs 8%) and beta (0.4 vs 0.8), inputs that pose whether the peer discount is residual rather than earned.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- Absolute EBITDA has RISEN across the window (229→304→306→342→362, LTM 358) even as the margin % drifted from 42% to 37% — the margin optics mask growing absolute profit dollars.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- On the peer comps the discount is stark (EV/EBITDA 4.7x vs peer median 10.3x; P/E 5.4x vs 15.6x), but the peer set is HETEROGENEOUS ($430M-$15.9B, 37x cap span) so whether the gap is EARNED or RESIDUAL is for the human to judge, not a clean overshoot signal.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
- The name is buying back stock (164.7M→151.9M shares, -7.7% over ~1.7y) and ROIC has climbed 5.1%→11.5% (LTM 11.1%) — capital discipline alongside improving returns.
  - ↳ `EDGAR XBRL shares, trailing 2024-08-31..2026-05-31`
- The name trades at a forward EV/EBITDA of ~4.3x (EV $1,662M / FY26 adj-EBITDA $380-$385M) and adj P/E ~3.5x at $4.30 — earnings power well above the distressed GAAP basis.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`

### Bear case (terminal / value-trap)
- Leverage runs above the peer median (total debt/EBITDA 3.0x vs 1.9x) and S&P issuer rating is BB- with a weaker solvency sub-score (4 vs peer-median 2), and the Avis loss shrinks the EBITDA that services it.
  - ↳ `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-24`
- A significant Commercial Services customer (Avis Budget, >10% of total revenue) issued a contract termination notice, a permanent revenue leg lost rather than a timing wobble.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- The company itself quantified the Avis impact as reducing revenue $135-145M and segment profit $120-125M on a 2026-annualized basis — a material, disclosed permanent hit, not an optical one.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- Guidance was cut hard: FY26 revenue guide fell from $1,020-1,030M to $985-995M and adj-EBITDA from $405-415M to $380-385M between consecutive 8-Ks — the forward earnings base itself re-rated down, so the low multiple sits on a shrinking denominator (real signal, not trailing optics).
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- Consensus revisions are overwhelmingly one-directional: FY26 revenue 0↑/8↓ and EPS 1↑/5↓ last month, with FY26 EBITDA consensus cut -16% and EPS -29% over the 12m-to-latest path.
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- Consensus LT growth was slashed from 9.54% to 1.89% (one broker to -11.22%) and the median target price sits at $6.00 — the Street now models minimal durable growth, an earned-discount reading of the cheap multiple.
  - ↳ `CIQ Estimates→Consensus`
- A CEO departure landed on 2026-06-02 (Interim CEO appointed), an idiosyncratic governance shock stacked on the customer loss.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Short interest is rising sharply (5.0M→7.7M sh, +54.9%; 5.1% of float) — positioning is leaning against the name into the disruption.
  - ↳ `FINRA consolidated short interest (settle 2026-06-15); DTC = 7,741,661 short ÷ 6,237,412 screen 90d ADV`
- The stock is down 80.8% over 180d vs IWM +16.5% (-97.7% relative) — the collapse is idiosyncratic to the name, not a shared-cohort drawdown.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`

### Decisive question
**Does the durable Government Solutions annuity book (long-term recurring enforcement contracts, rising bookings) and stable core offset the permanent loss of the Avis/Commercial Services revenue leg, or does the customer loss plus a leadership vacuum mark the start of secular erosion in the higher-value Commercial franchise?**

### …evidence for
- Government Solutions shows sustained bookings momentum (~$71M trailing-12m new bookings, $13M in Q1) and long-term recurring contracts providing forward revenue visibility per management.
  - ↳ `CIQ transcript(s): Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf; Verra Mobility Corporation, Q4 2025 Earnings Call, Feb 24, 2026.rtf`
- Government Solutions and Commercial Services segment EBITDA both grew or held through the window (Commercial 160→283; Government 108→122), and consolidated absolute EBITDA rose to 362.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- The signed NYC DOT contract carries a $998M total value over five years with a five-year renewal option, anchoring the Government annuity.
  - ↳ `CIQ transcript(s): Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf; Verra Mobility Corporation, Q4 2025 Earnings Call, Feb 24, 2026.rtf`

### …evidence against
- Avis represented over 10% of total revenue and its loss is company-quantified at $135-145M revenue and $120-125M segment profit annualized — a large, high-margin permanent removal.
  - ↳ `EDGAR 8-K 0001193125-26-239351 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1682745/000119312526239351/d123116dex991.htm`
- Commercial Services revenue already declined ~4% YoY in Q1 on prior-period fleet-management churn before the Avis loss, and management flagged cautious 2-year travel-volume assumptions.
  - ↳ `CIQ transcript(s): Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf; Verra Mobility Corporation, Q4 2025 Earnings Call, Feb 24, 2026.rtf`
- Customer concentration remains high with City of New York DOT at 15.2% of revenue, so the annuity offset itself rests on a single large public counterparty.
  - ↳ `10-Q 0001193125-26-209227`

### Key unknowns
- Whether the interim CEO becomes permanent and what strategic direction a new leader takes — the 5.02 leadership change leaves succession and posture unresolved (an opaque governance gap, bearish until resolved).
- The covenant basis and any leverage covenant headroom is explicitly UNKNOWN/not disclosed — an expected disclosure gap that matters more now that Avis shrinks EBITDA.
- Whether the >10%-of-revenue relationship discussed as under 'short-term extension / constructive negotiation' in the Q1 call is the same Avis contract subsequently terminated, and whether any further Commercial customer is at risk.
- FY26 CFO/capex/FCF are shown only as guide ranges; actual post-Avis run-rate FCF and its trajectory into FY27 (EBITDA consensus $333M) are not yet resolved.
- No graph cohort exists for the name (cohort/read UNKNOWN) — the idiosyncratic-vs-shared read rests only on the name-vs-IWM relative, with no peer cross-section to confirm.
- Whether the peer discount is EARNED or RESIDUAL cannot be cleanly read: the peer set is HETEROGENEOUS (37x cap span) so every peer multiple is a confidence-gated input, not a benchmark.

### Twin reference cases
- **Sabre Corporation** — went terminal (LLM-claimed — verify)
  - distinguished by: Travel-linked, levered services name where a structural demand/customer-mix hit compounded balance-sheet strain and the multiple stayed depressed as estimates kept falling.
  - source: [LLM-suggested, unverified]
- **Conduent** — went terminal (LLM-claimed — verify)
  - distinguished by: Government/commercial BPO with heavy customer concentration where contract losses and leadership churn kept the de-rate from reverting despite an optically cheap multiple.
  - source: [LLM-suggested, unverified]
- **Cardlytics** — went terminal (LLM-claimed — verify)
  - distinguished by: Single large-customer dependence turned a cheap-looking multiple into a value trap when the anchor relationship deteriorated.
  - source: [LLM-suggested, unverified]
- **Concentrix Corporation** — went terminal
  - distinguished by: In-roster peer, similarly levered outsourced-services model whose EBITDA-growth has already turned negative, illustrating how a low multiple can be earned rather than an overshoot.
  - source: CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-24
- **Iron Mountain** — recovered (LLM-claimed — verify)
  - distinguished by: Durable recurring-contract cash generator that traded at a distressed multiple during a growth scare but self-funded through it as the core annuity book held.
  - source: [LLM-suggested, unverified]


## APPENDIX — FINANCIAL SUMMARY (actuals + consensus estimates) — export date unverified (data ≥ 2026-06-09)
### Annual (last-4-FY + LTM + FY26E/FY27E consensus)
- **Annual financials ($M; E = consensus)** — ↳ `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|
| Revenue ($M) | 742 | 817 | 879 | 979 | 979 | 989 | 948 |
| Revenue growth | — | +10% | +8% | — (basis) | — (basis) | +1% (vs FY25) | -4% |
| EBITDA ($M) | 304 | 306 | 342 | 362 | 358 | 382 | 333 |
| EBITDA margin | 41% | 37% | 39% | 37% | 37% | 39% | 35% |
| EBIT ($M) | 165 | 193 | 233 | 248 | 242 | 229 | 183 |
| Net income ($M) | 92 | 57 | 31 | 137 | 131 | 128 | 107 |
| EPS (GAAP, dil.) | 0.50 | 0.36 | 0.19 | 0.85 | 0.82 | 0.85 | 0.73 |
| EPS (Normalized) | 0.49 | 0.37 | 0.66 | 0.80 | 0.79 | 1.23 | 1.03 |
| CFO ($M) | 218 | 206 | 224 | 256 | 234 | — | — |
| Capex ($M) | -48 | -57 | -71 | -119 | -129 | — | — |
| FCF (levered, CIQ) | 183 | 139 | 146 | 83 | 54 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-06-09; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Trailing 8 quarters (the recent-quarter trajectory)
- **Quarterly financials** — ↳ `CIQ Financials→Income Statement (quarterly, trailing 8Q)`  <!-- ds-table -->

|  | Q2-24 | Q3-24 | Q4-24 (R) | Q1-25 | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 222 | 226 | 222 | 223 | 236 | 262 | 258 | 224 |
| Gross margin | 61% | 61% | 61% | 61% | 60% | 58% | 55% | 55% |
| EBITDA ($M) | 89 | 91 | 81 | 85 | 92 | 103 | 81 | 81 |
| EBITDA margin | 40% | 40% | 37% | 38% | 39% | 39% | 32% | 36% |
| Revenue QoQ | — | +1% | — (basis) | — (basis) | +6% | +11% | -2% | -13% |
| Revenue YoY | — | — | — | — | +6% | +16% | — (basis) | +0% |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q1-26 ($M): cash & ST inv 56; total debt 1,102; net debt 1,046; equity 272; net working capital 207; net-debt/EBITDA → see the Leverage & survival block (not recomputed)
  - ↳ `CIQ Financials→Balance Sheet (quarterly, Q1-26)`
- **Coherence — BS vs implied-valuation bridge:** cash BS $56M / bridge $56M; debt BS $1,102M / bridge $1,102M — reconcile with the implied-valuation bridge.
  - ↳ `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`


### Capital-structure provenance — on-demand (web collapsed · print-excluded · JSON) — full panel · pointers · terms
- **Capital structure — full instrument panel A 2025 filed Feb-24-2026** — ↳ `CIQ Financials→Capital Structure Details (A 2025 filed Feb-24-2026)`  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 2021 Term Loan Due 2028 | Term Loans | $687.1M | 5.700% | Benchmark | 2028-03-24 | Y | N | USD |
| Operating Lease | Capital Lease | $38.1M | 6.500% | NA | 2037-01-01 | Y | N | USD |
| Revolving Credit Facility | Revolving Credit | – | NA | Benchmark | 2030-10-17 | Y | N | USD |
| Senior Notes Due 2029 | Bonds and Notes | $350.0M | 5.500% | NA | 2029-04-15 | N | N | USD |

- **8-Ks at instrument maturities:** _UNKNOWN_ — no trailing-12m instrument maturity to anchor an 8-K
- **Covenant / contract pointers (CIK-verified execution filings)** — ↳ `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| 2021 Term Loan Due 2028 | 8-K | 2018-10-22 | 0001564590-18-024644 — vrrm-ex1010_20.htm, vrrm-ex1011_16.htm, vrrm-ex1012_17.htm |
| 2021 Term Loan Due 2028 | 8-K | 2021-03-29 | 0001564590-21-015880 — vrrm-ex101_62.htm |
| Revolving Credit Facility | 8-K | 2020-02-25 | 0001564590-20-006447 — vrrm-ex101_6.htm |
| Operating Lease | — | — | no contract-level filing expected (aggregate line item) |
| Senior Notes Due 2029 | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — 2021 Term Loan Due 2028 (governing; Tier-2 fenced)** — ↳ `fenced Tier-2 extraction (verbatim, source-bound)`  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm |
| Principal / commitment amount | UNKNOWN | not stated in 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm |
| Interest / coupon rate | UNKNOWN | not stated in 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm |
| Maturity date | UNKNOWN | not stated in 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm |
| Security / collateral / guarantors | UNKNOWN | not stated in 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm |
| Mandatory prepayment / events of default | UNKNOWN | not stated in 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm |
| Document type | Letter Amendment to Offer Letter (executive employment offer letter revision) | base (footer) |
| Annual salary | $400,000.00 annual salary, effective December 22, 2014 | base (footer) |
| Target bonus | Target bonus 100% | base (footer) |
| LTIP grant | 400,000 additional LTIP Grants, currently valued at $2.78 per share | base (footer) |
| Severance | Termination without cause or resignation for Good Reason: base salary plus medical benefits for up to 24 months (Good Reason: until alternate employment, whichever first) | base (footer) |
| Good Reason definition | a change in authority, duties, responsibilities, reporting lines, or other action by the Company resulting in a diminution of, or a material alteration to, your position | base (footer) |
| Transition/cooperation period | 60 day working/cooperation period after resignation | base (footer) |
| Title | President & Chief Operating Officer | base (footer) |

_Source §: 8-K 0001564590-18-024644 · vrrm-ex1010_20.htm_

- _2 located agreement exhibit(s) not extracted this run (cost bound / fetch fail) — see the pointer table: 0001564590-20-006447, 0001564590-21-015880_

### Reference: CIQ implied equity at peer-median multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 668.4
  - ↳ `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-24`
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $55.60M, − total debt $1,101.80M
  - ↳ `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-06-24`
- **Implied equity at peer-median ($M, CIQ)** — ↳ `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-06-24`  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 2,626.0 |
| NTM Revenue (Capital IQ) | 713.0 |
| NTM EBITDA (Capital IQ) | 2,001.8 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf; Verra Mobility Corporation, Q4 2025 Earnings Call, Feb 24, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt)
  - ↳ `CIQ transcript(s): Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf; Verra Mobility Corporation, Q4 2025 Earnings Call, Feb 24, 2026.rtf`

---
> **No BUY/AVOID here — this dossier only assembles and cites.** The verdict is the human's, logged separately via the ledger with a frozen entry price.