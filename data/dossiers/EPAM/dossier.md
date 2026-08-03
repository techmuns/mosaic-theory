# Dossier — EPAM Systems, Inc. (NYSE: EPAM)

_July 30, 2026 · extraction 2026-07-28.1_

# Brief — first cut

## At a glance
**Target (base)** $186.76 (+108.9% vs entry-vintage spot) · **Spot** $89.40 (entry-vintage — frozen at underwrite 2026-07-21) · **Reward** $97.36 · **Risk** $15.34 · **Reward : risk** 6.34 : 1 (bar 2 : 1)

_Spot source: Polygon EOD daily close 2026-07-20 (live; 2026-07-21 has not settled)_

**Underwrite disposition:** PENDING_ANALYST — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

EPAM Systems, Inc. provides digital platform engineering and software development services worldwide.
**Mixed** — a still-growing, net-cash franchise de-rated to trough multiples, but one-sided negative revisions and management-flagged demand softness keep the terminal case live.
- **Segments:** Americas 58%; Europe 42% [1]
- **Geography:** United States 52%; Other Locations 21%; United Kingdom 11%; Switzerland 8%; Germany 4%; Netherlands 4% [2]
- **Snapshot:** NYSE · CMP $100.40 (2026-07-28) · cap $5.2B (2026-07-27) · 52-wk $73.06–$222.53 · shares 52.2M · book value/sh $65.04 [3]

**The crux — what decides this, and what would change our mind**
**Is the sharp de-rating an overshoot on a still-growing, net-cash franchise (mean-revert), or an earned repricing to a permanently lower-growth, lower-margin AI-disrupted services model (value trap)?**
_7 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-08-06 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-02-03 no company filing; 2026-02-19 earnings; 2026-06-18 no company filing [4]
- **Price (180d):** -60.2% [5]
- **Market (MDY) 180d:** 11.7% [6]
- **vs market (180d):** -71.9% [7]
- **Net debt / EBITDA:** -1.0x [8]
- **Free cash flow:** positive [9]

## Scenario analysis
_Mid-cycle underwrite: normalized operating margin on a mid-cycle revenue base, valued at an exit EV/LTM-EBITDA multiple; reward/risk measured at SPOT._

| scenario | revenue $M | margin | multiple | value / sh | vs entry-vintage spot |
| --- | ---: | ---: | ---: | ---: | ---: |
| bear | 5,000 | 8.0% | 6x | $74.06 | -17.2% |
| base | 5,730 | 10.5% | 12.5x | $186.76 | +108.9% |
| bull | 6,075 | 13.0% | 18x | $326.99 | +265.8% |

- **bear** — Secular case: AI substitution erodes the labour-arbitrage model; revenue -10% from the trailing twelve months (carrying the negative forward revision breadth, FQ3 0 up / 14 down, rather than assuming it reverses); margin below the FY25 worst (9.53%) as pricing grinds — floored by the variable-cost model, not collapsed; the multiple holds near the post-2022 trough (range low 4.26x, current 4.87x at the 2.6th percentile) — a secular decline earns no re-rating. [restated for external readability 2026-07-21; substance unchanged]
- **base** — Margin is the post-2022 regime median of 11.10% less a ~60bps trajectory haircut: the regime's most recent year (FY25, 9.53%) is its worst and revision breadth is 0 up / 14 down, so the live-regime median likely overstates the forward mid-cycle. Explicitly not the 10-year blend (11.9%, which straddles the 2022 break), not the pre-war level (13.27%, a regime no longer representative), and not the consensus recovery (~15.6% operating income — the Street's base case is our bull). Revenue is consensus FY26E. The multiple sits below the 15.16x post-2022 median: the AI-substitution question earns a durable discount even at mid-cycle. [restated for external readability 2026-07-21; substance unchanged]
- **bull** — The cyclical air-pocket resolves: the delivery rebuild completes and margin recovers toward but below the pre-war median (13.27%) and well below consensus (~15.6%); revenue is consensus FY27E; the multiple moves toward but stays below the post-2022 75th percentile (20.09x). [restated for external readability 2026-07-21; substance unchanged]

**Scenario inputs** — every value in the grid recomputes from these.

| input | value | basis | source |
| --- | ---: | --- | --- |
| d and a | 124.811 $M | consolidated latest FY (FY2025) | EDGAR companyfacts DepreciationAndAmortization, 10-K accession 0001352010-26-000015 filed 2026-02-26 (CY2025) [amended 2026-07-22 pre-verdict: prior 45.317 was the abandoned combined tag's FY2019 value carried forward by alias ordering (fixed PR #182); filer's split tag FY2025 = 124.811] |
| net debt | -749.016 $M | NET CASH (negative net debt), lease-inclusive, latest 10-Q | EDGAR: total debt 165 + finance leases 0 + operating leases 123 − cash 1,037 ($M) = −749.016; 10-Q acc 0001352010-26-000029. Equity = EV − (−749.016), i.e. the cash is ADDED — reproduced against the committed anchor's $306.05/sh before this run |
| diluted shares | 52.634451 M shares | Diluted shares outstanding 52,634,451 = basic outstanding 52,244,451 + dilutive increment 390,000 (diluted 54,183,000 − basic 53,793,000 weighted average, 2026-01-01→2026-03-31). The dilutive increment is carried from the reporting period to the valuation date, which assumes the dilutive count has not moved since. Excluded from the filer's diluted average: antidilutive instruments (a loss period reports no dilution at all under ASC 260); out-of-the-money options, which contribute nothing under the treasury-stock method; any change in the dilutive count between the reporting period and the valuation date. | EDGAR dei:EntityCommonStockSharesOutstanding + us-gaap:WeightedAverageNumberOf{SharesOutstandingBasic,DilutedSharesOutstanding} — item 24 denominator swap |
| ltm revenue | 5,555.425 $M | LTM revenue | committed financial_summary.annual (LTM) — CIQ Income Statement |
| cash interest | 1.397 $M | FY2025 cash interest PAID (cross-check input only; EPAM is net-cash with $165M total debt, so interest is immaterial) | EDGAR companyfacts us-gaap InterestPaidNet, FY2025 — 10-K acc 0001352010-26-000015 |
| cash tax rate | 0.253 rate | EDGAR-DERIVED FY2025 effective rate (NOT an analyst assumption): income tax expense 127.946 ÷ pretax income 505.624 = 25.30%; cross-check only, does not touch value/share | EDGAR companyfacts IncomeTaxExpenseBenefit ÷ IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest, FY2025 — 10-K acc 0001352010-26-000015 |

_Chain (EV/EBITDA):_ EBIT = revenue × op margin → EBITDA = EBIT + D&A → EV = EBITDA × exit multiple (EV/EBITDA) → equity = EV − net debt → value/share = equity ÷ diluted shares

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | mid-cycle margin × the median multiple of its own history | applicable |
| Mid-cycle margin | 11.9% | 10y history · firm |
| Median multiple, own history | 22.4x | 38 closes · firm · EV/EBITDA |
| Screen value / share | $338.93 | spot-independent · EV/EBIT 26.6x |
| Overall confidence | firm |  |

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Revenue grew +7.6% YoY in Q1 Mar-2026 and the top line is still expanding ($5,457M FY25 → $5,555M LTM), the opposite of the terminal-decline peers whose revenue is shrinking. [10]
- Management reports pure AI revenues exceeded $125M in Q1 up ~20% sequentially with a stated $600M full-year target, a mechanism suggesting a new growth vector rather than structural erosion. [10]
- The trailing EV/EBITDA sits at 4.9x, its 3rd-percentile over 38 quarterly closes (range 4.3–57.2x, median 22.4x), a compression far exceeding the modest EBITDA and revenue trend deterioration. [11]
_Bear case — the decline is real:_
- Management itself flagged rising macro uncertainty, North America underperformance and lower second-half visibility, with expected Q2 impact on larger discretionary programs — a demand-side mechanism behind the guidance caution. [10]
- Consensus estimate breadth is uniformly negative — FY26 GAAP EPS 0 up/4 down and revenue 0 up/6 down last month — confirming analysts are still cutting, so the de-rating tracks a genuine downgrade cycle, not a pure optical overshoot. [12]
- ROIC has fallen from a 14.9% FY22 peak to ~10.1% LTM, a sustained decline in capital efficiency toward the cost of capital, consistent with a lower-quality franchise than the growth-era EPAM. [13]

## Financial snapshot
- **Financial snapshot** — [14]  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 4,825 | 4,691 | 4,728 | 5,457 | 5,555 | 5,724 | 6,055 |
| Revenue growth | — (basis) | -3% | — (basis) | +15% | — (basis) | +5% (vs FY25) | +6% |
| EBITDA ($M) | 799 | 652 | 693 | 707 | 731 | 950 | 1,027 |
| EBITDA margin | 17% | 14% | 15% | 13% | 13% | 17% | 17% |
| EBIT ($M) | 708 | 562 | 604 | 583 | 607 | 891 | 958 |
| Net income ($M) | 419 | 417 | 455 | 378 | 387 | 438 | 505 |
| EPS (GAAP, dil.) | 7.09 | 7.06 | 7.84 | 6.72 | 6.98 | 8.31 | 9.83 |
| FCF ($M) | 413 | 531 | 667 | 725 | 693 | — | — |

_table shows the last 4 fiscal years · 5 earlier years are in the Appendix_

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 4.9x as-of 2026-07-17 — trailing range 4.3–57.2x (median 22.4x) over 38 closes → 3%ile → near-floor; P/LTM EPS 12.7x [15]
- **vs peers:** EV/EBITDA 5.6x vs peer median 6.2x (-9%); P/E 14.4x vs peer median 13.2x (+9%) [16]
- **Comparability:** market caps span $953M–$100.8B (106x); the name is $5.2B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [17]
- **The street, for contrast (target · ratings):** Target price: mean $135.24, median $131.00, high/low 235.00/83.00, N 17/17; Ratings: Buy 8, Outperform 3, Hold 8, Underperform 0, Sell 0, No Opinion 0, Buy 0, Outperform 0, Hold 2, Underperform 0, Sell 0  [data ≥ 2026-07-27 · export date unverified] [18]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [4]
  - 2026-02-03 **-12.9%** → no company filing
  - 2026-02-19 **-17.0%** → earnings
  - 2026-06-18 **-12.6%** → no company filing

_Company-specific or market-wide?_
- **Name 180d return:** -60.2% [5]
- **Market (MDY) 180d return:** 11.7% [6]
- **Relative vs market:** -71.9% [7]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-down 2026-02-19 → filed 2026-02-19 [`0001352010-26-000010`](https://www.sec.gov/Archives/edgar/data/1352010/000135201026000010/epam-20260219.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj operating income Q4 2025 $230.0M (+$21.8 million); adj EPS Q4 2025 $3.26 (+14.8%); 2026 revenue outlook: 4.5–7.5% growth [19]

## Business quality
- **Segments (revenue share):** Americas 58%; Europe 42% [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — reports 2 segments (Americas; Europe) but discloses no segment EBITDA — revenue is segmented in the filing and EBITDA is not
- **Customers:** 31 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [20]
- **Geographic:** United States 52%; Other Locations 21%; United Kingdom 11%; Switzerland 8%; Germany 4%; Netherlands 4% [2]

## The argument

**Evidence balance:** mixed — a still-growing, net-cash franchise de-rated to trough multiples, but one-sided negative revisions and management-flagged demand softness keep the terminal case live.

### Bull case — the decline is overdone
- Revenue grew +7.6% YoY in Q1 Mar-2026 and the top line is still expanding ($5,457M FY25 → $5,555M LTM), the opposite of the terminal-decline peers whose revenue is shrinking. [10]
- Management reports pure AI revenues exceeded $125M in Q1 up ~20% sequentially with a stated $600M full-year target, a mechanism suggesting a new growth vector rather than structural erosion. [10]
- The trailing EV/EBITDA sits at 4.9x, its 3rd-percentile over 38 quarterly closes (range 4.3–57.2x, median 22.4x), a compression far exceeding the modest EBITDA and revenue trend deterioration. [11]
- The stock fell ~60% over 180 days versus the mid-cap benchmark up ~12%, a ~72pp idiosyncratic underperformance far exceeding any operational deterioration, consistent with an overshoot rather than a broken business. [7]
- Absolute EBITDA is still rising — $707M FY25 → $731M LTM Mar-2026 — even as the EBITDA margin % compressed to 13%, so the trailing-margin decline overstates deterioration; the absolute reconciler is the real signal here and it is up. [21]
- The balance sheet is net cash at net-debt/EBITDA -1.0x with positive LTM FCF of $692.9M, so the company is self-funding and faces no solvency or refinancing forcing-function. [22]
- The company is buying back stock (-8.2% share count over ~1.7 years) and credit-health scores are stronger than peers (2/2/2/1 vs peer-median 3/3/3/3), indicating capital-return capacity and financial strength, not distress. [23]

### Bear case — the decline is real
- Management itself flagged rising macro uncertainty, North America underperformance and lower second-half visibility, with expected Q2 impact on larger discretionary programs — a demand-side mechanism behind the guidance caution. [10]
- Consensus estimate breadth is uniformly negative — FY26 GAAP EPS 0 up/4 down and revenue 0 up/6 down last month — confirming analysts are still cutting, so the de-rating tracks a genuine downgrade cycle, not a pure optical overshoot. [12]
- ROIC has fallen from a 14.9% FY22 peak to ~10.1% LTM, a sustained decline in capital efficiency toward the cost of capital, consistent with a lower-quality franchise than the growth-era EPAM. [13]
- Structural profitability has eroded: gross margin fell from 36% (FY17) to 29% (LTM) and EBITDA margin to 13% — the % decline is the REAL signal on unit economics even though absolute EBITDA still rose, because the margin trend has been multi-year and directional. [21]
- The drawdown came in three discrete earnings-linked gap-downs (2026-02-03, 2026-02-19 earnings, 2026-06-18), an event-driven repricing to information, not indiscriminate selling. [4]
- Rising short interest (10.3M → 11.3M shares, +9.5%, ~21.6% of shares out) shows conviction bearish positioning is building, not covering. [24]

### Decisive question
**Is the sharp de-rating an overshoot on a still-growing, net-cash franchise (mean-revert), or an earned repricing to a permanently lower-growth, lower-margin AI-disrupted services model (value trap)?**

### …evidence for
- Revenue still grew +7.6% YoY in Q1 and absolute EBITDA rose to $731M LTM, with pure-AI revenue up ~20% sequentially toward a $600M target — an operating base inconsistent with terminal decline. [10]
- The trailing EV/EBITDA at 4.9x sits near its 3rd-percentile of a 38-quarter range whose median is 22.4x, a compression magnitude that outruns the fundamental deterioration on record. [11]

### …evidence against
- Management flagged North America underperformance, rising macro uncertainty and lower second-half visibility with expected Q2 impact on discretionary programs — the demand mechanism that could make lower growth durable. [10]
- Estimate breadth is one-sided down (FY26 revenue 0 up/6 down, EPS 0 up/4 down last month) and multi-year gross margin has fallen from 36% to 29%, signalling an earned, not optical, decline. [12]

### Key unknowns
- Adjusted/forward EBITDA and adjusted EPS in the revised guidance are UNKNOWN, so a clean forward multiple and forward leverage cannot be built — a disclosure gap that weakens the cheap-vs-terminal test.
- Segment EBITDA is not disclosed (only Americas/Europe revenue), so the profitability mix behind the North America weakness and the margin compression cannot be isolated — an opacity risk that should be read cautiously, not neutrally.
- Interest coverage is UNKNOWN (no period with both EBITDA and interest expense), though net-cash status makes this less load-bearing.
- The primary-source cross-check flags a MISMATCH between the CIQ revenue guide (1,400–1,415) and the release outlook (4.0–6.5% growth), and self-funding reads MIXED (latest-Q OCF negative while LTM FCF positive) — both need reconciliation before leaning on the self-funding thesis.
- The peer set is HETEROGENEOUS (market caps $953M–$100.8B, 106x span), so the peer median is not a clean benchmark and any earned-vs-residual discount read is confidence-gated.
- Whether the tokenomics/AI-pricing shift management describes is margin-accretive or margin-dilutive over time is unresolved — the commercial-model transition could cut either way.
- Data vintage is a floor (≥2026-07-27, export date unverified) against a stock price of $100.4 as-of 2026-07-28 that has recovered off the ~$42 June low — the current setup may already differ from the trailing series.

### Twin reference cases
- **Cognizant Technology Solutions Corporation** — recovered
  - distinguished by: A large IT-services peer that de-rated on growth-deceleration fears yet held revenue and margin, then re-rated as growth stabilized — the mean-revert analogue for a services franchise still growing.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **DXC Technology Company** — went terminal
  - distinguished by: An IT-services name whose revenue and EBITDA are structurally shrinking and leverage is elevated — the value-trap analogue where a low multiple reflected earned decline, not overshoot.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Globant S.A.** — went terminal
  - distinguished by: A digital-engineering peer that lost its premium growth rate as AI reshaped demand, seeing multiple and estimates compress together — the analogue for growth-model disruption in the same vertical.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Accenture plc** — recovered
  - distinguished by: The scaled consulting/technology leader that navigated an AI-demand transition while defending margin and cash generation — the analogue for a franchise using AI as a tailwind rather than a threat.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-08-06 `[cadence-estimate]` — the next reported quarter against the committed trajectory [25]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 5.6x vs peer median 6.2x (-9%); P/E 14.4x vs peer median 13.2x (+9%) [16]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-07-29 · multiples as-of 2026-07-27 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [26]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **5x** | **$899.3M EBITDA †** |
| peer-median NTM TEV/EBITDA | 5.61x | $801.5M EBITDA |
| peer-median LTM TEV/EBITDA | 6.1x | $737.1M EBITDA |
| **name NTM TEV/Rev** | **0.83x** | **$5,417.2M Revenue †** |
| peer-median NTM TEV/Rev | 1.04x | $4,323.4M Revenue |
| peer-median LTM TEV/Rev | 1.1x | $4,087.5M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $949.7M · FY27E $1027.3M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $5724.1M · FY27E $6054.6M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 4.9x as-of 2026-07-17 — trailing range 4.3–57.2x (median 22.4x) over 38 closes → 3%ile → near-floor; P/LTM EPS 12.7x [15]

## Peer comps
- **Peer set (roster · caps · business)** — [27]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Cognizant Technology Solutions Corporation | $23.8B | provides consulting and technology, and outsourcing services in North America, Europe, and internationally. (United States) |
| Amdocs Limited | $5.8B | provides software and services to communications, entertainment, media, and other service providers worldwide. (United States) |
| DXC Technology Company | $1.8B | provides information technology services and solutions in the United States, the United Kingdom, the Rest of Europe, Australia, and internationally. (United States) |
| Globant S.A. | $1.5B | provides technology services in the United States, rest of North America, Latin America, Europe, and internationally. (Luxembourg) |
| Sopra Steria Group SA | $3.6B | provides consulting, digital, and software development services in France and internationally. (France) |
| Everforth | $953M | provides information technology solutions for commercial and government sectors in the United States, Canada, and Europe. (United States) |
| Nomura Research Institute | $18.1B | engages in the provision of consulting, financial information technology (IT) solutions, Industrial IT solutions (Japan) |
| Gartner | $10.4B | provides business and technology insights to support decision-making and performance on an organization’s mission-critical priorities in the United States (United States) |
| Accenture plc | $100.8B | provides strategy and consulting, industry X, song, and technology and operation services in the Americas, Europe, the Middle East, Africa (D02 P820 Ireland) |
| iSoftStone Information Technology | $5.4B | provides information technology services in China and internationally. (China) |

_the name: $5.2B_

- **Comparability (confidence gate):** market caps span $953M–$100.8B (106x); the name is $5.2B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [17]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [28]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 0.78 | 0.37 | 1.04 | 1.29 | 3.57 |
| NTM TEV/EBITDA | 4.65 | 2.9 | 5.61 | 6.33 | 13.38 |
| NTM P/E | 7.53 | 4.24 | 8.69 | 16.54 | 76.93 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [29]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Accenture plc | $100.8B | 7.2 | 1.4 | 13.2 | 18% | 7% | 0.6 | 1,783 (net cash) |
| Cognizant Technology Solutions Corporation | $23.8B | 5.7 | 1.1 | 10.9 | 18% | 7% | 0.3 | 425 (net cash) |
| Nomura Research Institute | $18.1B | 14.8 | 3.8 | 206.4 | 25% | 7% | 1.1 | 632 |
| Gartner | $10.4B | 8.7 | 1.9 | 15.5 | 21% | 2% | 2.4 | 1,688 |
| Amdocs Limited | $5.8B | 6.2 | 1.5 | 11.0 | 22% | -3% | 1.0 | 853 |
| iSoftStone Information Technology | $5.4B | 185.2 | 1.1 | NM | 0% | 10% | 44.6 | 179 |
| **EPAM Systems · the name** | **$5.2B** | **5.6** | **0.8** | **14.4** | **13%** | **14%** | **0.4** | **749 (net cash)** |
| Sopra Steria Group SA | $3.6B | 6.1 | 0.7 | 11.4 | 10% | -2% | 1.8 | 768 |
| DXC Technology Company | $1.8B | 2.5 | 0.4 | 108.7 | 12% | -2% | 2.3 | 2,510 |
| Globant S.A. | $1.5B | 4.3 | 0.8 | 14.3 | 16% | 0% | 1.1 | 262 |
| Everforth | $953M | 6.0 | 0.6 | 10.2 | 9% | -1% | 3.9 | 1,388 |
| Peer median (peers) | $5.6B | 6.2 | 1.1 | 13.2 | 17% | 1% | 1.5 | 700 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [21]  <!-- ds-table -->

|  | Dec-2017 (R) | Dec-2018 | Dec-2019 | Dec-2020 | Dec-2021 | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 | Dec-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 36% | 36% | 35% | 35% | 34% | 33% | 31% | 31% | 29% | 29% |

_Revenue YoY (latest same-quarter): +7.6% (Q1 Mar-31-2026 vs Q1 Mar-31-2025). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** buying back (trailing ~1.7y): 56,935,370 (2024-07-31) → 52,244,451 (2026-04-30), -8.2% [23]
- **Return ratios — per fiscal period** — [30]  <!-- ds-table -->

|  | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | 8.3% | 21.5% | 18.3% | 18.3% | 21.5% | 15.3% | 12.9% | 12.8% | 10.3% | 10.9% |
| RoCE % | 12.0% | 13.4% | 12.0% | 11.5% | 13.7% | 14.9% | 10.3% | 10.2% | 9.6% | 10.1% |
| RoA % | 9.9% | 10.7% | 9.8% | 9.5% | 10.9% | 11.7% | 8.4% | 8.3% | 7.5% | 8.0% |
| Total debt/equity | 0.03x | 0.02x | 0.17x | 0.13x | 0.10x | 0.06x | 0.05x | 0.04x | 0.04x | 0.08x |
| Current ratio | 5.31x | 4.56x | 3.81x | 4.11x | 2.97x | 3.69x | 4.79x | 2.96x | 2.59x | 2.67x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-07-27)_
- **Horizon read (FQ — next-2Q revision breadth)** — [31]:
  - EPS Normalized FQ2 2026: 1m 0↑/2↓, 2m 0↑/2↓, 3m 11↑/5↓
  - EPS Normalized FQ3 2026: 1m 0↑/5↓, 2m 0↑/5↓, 3m 10↑/4↓
  - Revenue FQ2 2026: 1m 1↑/3↓, 2m 1↑/3↓, 3m 1↑/15↓
  - Revenue FQ3 2026: 1m 0↑/5↓, 2m 0↑/5↓, 3m 1↑/13↓
  - EBITDA FQ2 2026: 1m 1↑/2↓, 2m 1↑/2↓, 3m 0↑/6↓
  - EBITDA FQ3 2026: 1m 0↑/3↓, 2m 0↑/3↓, 3m 2↑/3↓
  - EBIT FQ2 2026: 1m 1↑/3↓, 2m 1↑/3↓, 3m 4↑/9↓
  - EBIT FQ3 2026: 1m 0↑/5↓, 2m 0↑/5↓, 3m 1↑/12↓
  - _+8 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 12.1 (12m) → 12.2 (9m) → 12.5 (6m) → 12.8 (3m) → 13.1 (2m) → 13.1 (1m) → 13.1 (latest); net +8% (12m→latest) | FY 2026 EPS (GAAP): 8.49 (12m) → 8.46 (9m) → 8.60 (6m) → 8.14 (3m) → 8.32 (2m) → 8.32 (1m) → 8.31 (latest); net -2% (12m→latest) | FY 2026 Revenue: 5,748.3 (12m) → 5,794.9 (9m) → 5,823.4 (6m) → 5,780.8 (3m) → 5,729.8 (2m) → 5,730.4 (1m) → 5,724.1 (latest); net -0% (12m→latest) | FY 2026 EBITDA: 964.5 (12m) → 953.2 (9m) → 967.3 (6m) → 966.3 (3m) → 963.0 (2m) → 963.0 (1m) → 949.7 (latest); net -2% (12m→latest) | FY 2026 EBIT: 883.3 (12m) → 894.0 (9m) → 900.6 (6m) → 898.4 (3m) → 891.5 (2m) → 892.1 (1m) → 891.1 (latest); net +1% (12m→latest) | FY 2026 Interest Expense: -9.00 (3m) → -2.00 (2m) → -3.41 (1m) → -3.41 (latest); improving (magnitude toward zero) (3m→latest) | FY 2026 EBT (GAAP): 623.8 (12m) → 629.4 (9m) → 627.7 (6m) → 593.1 (3m) → 595.8 (2m) → 596.1 (1m) → 599.2 (latest); net -4% (12m→latest) | FY 2026 Net Income (Excl. Excep): 681.0 (12m) → 682.4 (9m) → 687.4 (6m) → 692.6 (3m) → 687.5 (2m) → 687.6 (1m) → 687.0 (latest); net +1% (12m→latest) | FY 2026 Net Income (GAAP): 476.7 (12m) → 475.3 (9m) → 476.3 (6m) → 441.2 (3m) → 438.8 (2m) → 438.7 (1m) → 438.0 (latest); net -8% (12m→latest)  [data ≥ 2026-07-27 · export date unverified] [32]
- **Cross-name anchor (NTM forward-multiple ladder)** — [33]:
  - NTM: TEV/REV 0.83 · TEV/EBITDA 5.00 · TEV/EBIT 5.36 · Price/Earnings 8.01 · PEG 0.79 · P/BV –
  - FY 2026: TEV/REV 0.84 · TEV/EBITDA 5.09 · TEV/EBIT 5.43 · Price/Earnings 8.19 · PEG 0.81 · P/BV 1.47
  - FY 2027: TEV/REV 0.80 · TEV/EBITDA 4.71 · TEV/EBIT 5.05 · Price/Earnings 7.56 · PEG 0.75 · P/BV 1.26
  - FY 2028: TEV/REV 0.75 · TEV/EBITDA 4.34 · TEV/EBIT 4.66 · Price/Earnings 7.00 · PEG 0.69 · P/BV 1.06
  - _+2 later fiscal years in JSON_
- **Current guide (latest results filing):** revenue next-fy: 4.0–6.5 % [34]
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [35]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| EPS Normalized | '3.10 - 3.18' | FQ2 2026 | 2026-05-07 | 60d (stale) | actual ≥ floor 63/64 | FQ1 2026 MET |
| Revenue | '1,400.00 - 1,415.00' | FQ2 2026 | 2026-05-07 | 60d (stale) | actual ≥ floor 66/67 | FQ1 2026 MET |
| Capital Expenditure | '(19.00) - (20.00)' | FY 2016 | 2016-02-18 | 3791d (stale) | spend ≤ ceiling 1/2 | FY 2016 MISSED |

- **Consensus stats (target + ratings):** Target price: mean $135.24, median $131.00, high/low 235.00/83.00, N 17/17; Ratings: Buy 8, Outperform 3, Hold 8, Underperform 0, Sell 0, No Opinion 0, Buy 0, Outperform 0, Hold 2, Underperform 0, Sell 0  [data ≥ 2026-07-27 · export date unverified] [18]
- **Revision-event log (250 events · 15 broker-days)** — [36]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Withheld | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-07-27 | broker undisclosed | 1 | — | — | — | 1 | — | — | — | — |
| 2026-07-21 | broker undisclosed | 22 | — | — | — | 22 | — | — | — | — |
| 2026-07-15 | broker undisclosed | 18 | — | 18 | — | — | EBITDA FY 2026 | 961.6 | 957.1 | −4.5 |
| 2026-07-13 | broker undisclosed | 21 | — | 21 | — | — | EBITDA FY 2026 | 957.2 | 954.4 | −2.8 |
| 2026-07-10 | broker undisclosed | 20 | 3 | 16 | 1 | — | Revenue FY 2026 | 5743.4 | 5728.0 | −15.4 |
| 2026-07-09 | broker undisclosed | 20 | 7 | 11 | 2 | — | EBITDA FQ2 2026 | 235.2 | 231.9 | −3.3 |

_+9 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2011 -34%, FY2012 -4%, FY2013 +2%, FY2014 -1%, FY2015 +4%, FY2016 -4%, FY2017 -51%, FY2018 +1%, FY2019 +2%, FY2020 -1%, FY2021 +2%, FY2022 +7%, FY2023 -4%, FY2024 -0%, FY2025 -2%; Revenue surprise: FY2011 +2%, FY2012 +2%, FY2013 +2%, FY2014 +0%, FY2015 +1%, FY2016 +0%, FY2017 +0%, FY2018 +0%, FY2019 +1%, FY2020 +1%, FY2021 +1%, FY2022 +0%, FY2023 +0%, FY2024 +1%, FY2025 +0% (GAAP-EPS basis; +beat / −miss) [37]

## Leverage & survival
- **Net debt / EBITDA [NET]:** -1.0x [8]
- **Total debt / EBITDA vs peers:** name 0.4x vs peer median 1.5x (comps TOTAL-debt/EBITDA basis) [38]
- **Net debt / OCF:** -1.3x [39]
- **Interest coverage:** _UNKNOWN_ — no period with both EBITDA and Interest Expense
- **Self-funding:** self-funding: MIXED — latest-Q OCF < 0, LTM FCF > 0 (both must be positive to self-fund) [40]
- **Credit health** — [41]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 2 | 3 |
| Operational | 2 | 3 |
| Solvency | 2 | 3 |
| Liquidity | 1 | 3 |

_S&P issuer rating unrated · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [9]
- **Free cash flow ($M):** 692.9 [42]
- **Live instruments — near-dated (≤12m + 2027):** none due in the window — 3 undated / later aggregate line item(s) in the appendix panel [43]
- **Maturity wall** · vs the 2026-07-06 reference:
  - due 2030: $25.0M
  - undated (floor — no panel maturity): $118.7M — Long Term Debt - Other $0.0M, Operating Lease Liabilities $118.7M
  - _reconciliation: itemized $143.7M (panel A 2025 filed Feb-26-2026) vs the latest-quarter aggregates below — the gap is unitemized / newer term loans; read the QoQ movement in the aggregates line._
- **Capital-structure aggregates (latest quarter):** leases 122.9; total principal 287.9; total debt 287.9 (latest quarter) ($M) [44]
- **Covenants — Revolving Credit Facility** (governing values; full verbatim in appendix):
  - **Interest / coupon:** Base Rate + Applicable Margin (Base Rate spread 0.000%–1.000%); or Adjusted Eurocurrency Rate + Applicable Margin (Euro…
  - **Maturity:** October 21, 2026 · October 21, 2026 (Expiration Date), subject to extension
  - **Financial maintenance:** Maximum Consolidated Leverage Ratio 3.50 to 1.00 (temporarily 4.00 to 1.00 for four fiscal quarters following a Materia…
  - **Events of default:** Mandatory prepayment (Section 5.3): (a),(b) Reserved; (d) if Alternative Currency Loans/LC Obligations exceed 105% of t…

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [45]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [46]
  - net debt / EBITDA (CIQ, GAAP basis): -1.0x
  - total debt / EBITDA (CIQ comps, GAAP basis): 0.4x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage

## ⚠ Analyst caveats — verify before the verdict

_1 to verify._

- **Unreconciled margin-compression** — Estimate breadth is one-sided down (FY26 revenue 0 up/6 down, EPS 0 up/4 down last month) and multi-year gross margin has fallen from 36% to 29%, signalling an earned, not optical, decline.
  - _where:_ a decisive-against point
  - _why it matters:_ cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)

# Appendix — data & audit

## How to read this dossier
- The machine assembles and cites; **the analyst decides**. Nothing here is a recommendation — the verdict of record is the human's, logged to an append-only ledger with a frozen entry price.
- The machine's proposed verdict is derived deterministically from its written assessment and stays **sealed until the analyst's verdict is recorded**, so it cannot anchor the decision. A two-sided assessment proposes nothing.
- Citations [n] resolve in the Sources list at the document end. **Cited is not verified** — the reference locates the claim so you can check it.
- Reference values (peer-implied equity, price-implied levels) are shown **beside** the figures they contextualize, never differenced into an upside — the reader judges the gap.
- A value shown as UNKNOWN is honestly absent at the source — nothing is imputed.

## How these numbers were set

_Per-axis methodology from the underwrite record — the reference frame each leg was chosen against, not a re-derivation._

### Revenue · **DRAFT — not ratified by the analyst**

Legs are set on the consensus path: base is consensus FY26E, bull is consensus FY27E, and bear is the trailing twelve months less ~10%, carrying the negative forward revision breadth (FQ3 0 up / 14 down) forward rather than assuming it reverses. [restated for external readability 2026-07-21; substance unchanged]

| reference | value |
| --- | ---: |
| consensus FY26E revenue | $5,730.43M [47] |
| consensus FY27E revenue | $6,074.52M [48] |
| LTM revenue | $5,555.425M [49] |

### Margin · **DRAFT — not ratified by the analyst**

Modelled on regime-split operating-margin statistics (post-2022 window; operating income divided by the ASC-606 revenue tag, with annual filing points filtered to 350-380 day durations so no quarter is mistaken for a year): base is the post-2022 median of 11.10% less a ~60bps trajectory haircut; bear sits below the regime's worst year (FY25, 9.53%); bull recovers toward but below the pre-war median (13.27%, a regime no longer representative). The 10-year blend (11.90%) is explicitly not used — it straddles the 2022 break and describes neither regime. [restated for external readability 2026-07-21; substance unchanged]

| reference | value |
| --- | ---: |
| post-2022 regime median operating margin (FY2022-2025) | 11.1% [50] |
| post-2022 worst year (FY2025) | 9.53% [51] |
| post-2022 best year (FY2022) | 11.88% [52] |
| _pre-war median operating margin (FY2016-2021) — excluded: the pre-war margin structure no longer obtains_ | _13.27%_ [53] |
| _10-FY blended median (FY2016-2025) — excluded: blends across the structural break_ | _11.9%_ [54] |

### Multiple · **DRAFT — not ratified by the analyst**

Chosen against the regime-split TEV/LTM-EBITDA trading range (38 quarterly closes): base sits below the post-2022 median (15.16x) as an analyst discount for the unresolved AI-substitution question; bear near the post-2022 trough; bull toward but below the post-2022 75th percentile (20.09x). The full-blend median (22.41x) is not used — it is a pre-2022 bubble-era statistic. [restated for external readability 2026-07-21; substance unchanged]

| reference | value |
| --- | ---: |
| post-2022 band 25th percentile | 11.83x [55] |
| post-2022 band median | 15.16x [55] |
| post-2022 band 75th percentile | 20.09x [55] |
| full-band minimum (9.5y history) | 4.26x [56] |
| current TEV/LTM-EBITDA (2.6th percentile of the full band) | 4.87x [57] |
| band multiples are vendor TEV/LTM-EBITDA computed on the filer's actual depreciation - the corrected fact aligns the grid's EBITDA basis with the band's | $124.811M [58] |


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-07-27)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [14]  <!-- ds-table -->

|  | FY17 (R) | FY18 | FY19 | FY20 | FY21 | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 1,450 | 1,843 | 2,294 | 2,659 | 3,758 | 4,825 | 4,691 | 4,728 | 5,457 | 5,555 | 5,724 | 6,055 |
| Revenue growth | — | — (basis) | +24% | +16% | +41% | — (basis) | -3% | — (basis) | +15% | — (basis) | +5% (vs FY25) | +6% |
| EBITDA ($M) | 202 | 283 | 348 | 441 | 628 | 799 | 652 | 693 | 707 | 731 | 950 | 1,027 |
| EBITDA margin | 14% | 15% | 15% | 17% | 17% | 17% | 14% | 15% | 13% | 13% | 17% | 17% |
| EBIT ($M) | 173 | 246 | 303 | 379 | 546 | 708 | 562 | 604 | 583 | 607 | 891 | 958 |
| Net income ($M) | 73 | 240 | 261 | 327 | 482 | 419 | 417 | 455 | 378 | 387 | 438 | 505 |
| EPS (GAAP, dil.) | 1.32 | 4.24 | 4.53 | 5.60 | 8.15 | 7.09 | 7.06 | 7.84 | 6.72 | 6.98 | 8.31 | 9.83 |
| EPS (Normalized) | 1.98 | 2.74 | 3.27 | 4.07 | 5.78 | 6.91 | 6.35 | 7.01 | 6.35 | 6.83 | 13.05 | 14.13 |
| Restructuring Charges ($M) | — | — | — | — | — | -17 | — | -31 | -48 | -56 | — | — |
| Merger & Related Restruct. Charges ($M) | — | — | — | — | -4 | — | — | -14 | — | — | — | — |
| Impairment of Goodwill ($M) | — | — | — | — | — | -1 | — | — | — | — | — | — |
| Gain (Loss) On Sale Of Invest. ($M) | — | — | — | — | — | -1 | — | — | — | — | — | — |
| Gain (Loss) On Sale Of Assets ($M) | — | — | — | — | — | — | -26 | — | — | — | — | — |
| Asset Writedown ($M) | — | — | — | — | — | -19 | -6 | -0 | -0 | -0 | — | — |
| Other Unusual Items ($M) | — | 1 | -2 | -2 | -9 | -109 | -31 | -20 | -18 | -18 | — | — |
| CFO ($M) | 193 | 292 | 287 | 544 | 572 | 464 | 563 | 559 | 655 | 594 | — | — |
| Capex ($M) | -30 | -38 | -99 | -69 | -112 | -82 | -28 | -32 | -42 | -51 | — | — |
| FCF (levered, CIQ) | 131 | 243 | 221 | 456 | 486 | 413 | 531 | 667 | 725 | 693 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-07-27; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Quarterly — every exported quarter
- **Quarterly financials** — [59]  <!-- ds-table -->

|  | Q1-17 | Q2-17 (R) | Q3-17 (R) | Q4-17 (R) | Q1-18 (R) | Q2-18 (R) | Q3-18 (R) | Q4-18 (R) | Q1-19 | Q2-19 | Q3-19 | Q4-19 | Q1-20 | Q2-20 | Q3-20 | Q4-20 | Q1-21 | Q2-21 (R) | Q3-21 (R) | Q4-21 (R) | Q1-22 (R) | Q2-22 (R) | Q3-22 (R) | Q4-22 (R) | Q1-23 (R) | Q2-23 | Q3-23 | Q4-23 (R) | Q1-24 (R) | Q2-24 (R) | Q3-24 | Q4-24 (R) | Q1-25 | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 325 | 349 | 378 | 399 | 424 | 446 | 468 | 505 | 521 | 552 | 588 | 633 | 651 | 632 | 652 | 723 | 781 | 881 | 989 | 1,107 | 1,172 | 1,195 | 1,227 | 1,231 | 1,211 | 1,170 | 1,152 | 1,157 | 1,165 | 1,147 | 1,168 | 1,248 | 1,302 | 1,353 | 1,394 | 1,408 | 1,400 |
| Gross margin | 36% | 37% | 37% | 36% | 35% | 35% | 36% | 37% | 34% | 35% | 36% | 35% | 35% | 34% | 35% | 36% | 33% | 34% | 34% | 34% | 35% | 30% | 33% | 35% | 30% | 31% | 31% | 31% | 28% | 29% | 35% | 30% | 27% | 29% | 30% | 30% | 28% |
| EBITDA ($M) | 42 | 48 | 56 | 60 | 57 | 63 | 74 | 89 | 75 | 84 | 92 | 97 | 102 | 99 | 112 | 128 | 125 | 146 | 166 | 192 | 229 | 148 | 213 | 223 | 157 | 173 | 167 | 184 | 143 | 144 | 200 | 186 | 140 | 162 | 180 | 197 | 165 |
| EBITDA margin | 13% | 14% | 15% | 15% | 13% | 14% | 16% | 18% | 14% | 15% | 16% | 15% | 16% | 16% | 17% | 18% | 16% | 17% | 17% | 17% | 20% | 12% | 17% | 18% | 13% | 15% | 14% | 16% | 12% | 13% | 17% | 15% | 11% | 12% | 13% | 14% | 12% |
| Revenue QoQ | — | — (basis) | +8% | +6% | +6% | +5% | +5% | +8% | — (basis) | +6% | +7% | +8% | +3% | -3% | +3% | +11% | +8% | — (basis) | +12% | +12% | +6% | +2% | +3% | +0% | -2% | — (basis) | -2% | — (basis) | +1% | -2% | — (basis) | — (basis) | — (basis) | +4% | +3% | +1% | -1% |
| Revenue YoY | — | — | — | — | — (basis) | +28% | +24% | +26% | — (basis) | — (basis) | — (basis) | — (basis) | +25% | +15% | +11% | +14% | +20% | — (basis) | — (basis) | — (basis) | — (basis) | +36% | +24% | +11% | +3% | — (basis) | — (basis) | -6% | -4% | — (basis) | +1% | +8% | — (basis) | — (basis) | +19% | — (basis) | +8% |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q1-26 ($M): cash & ST inv 1,037; total debt 288; net debt -749; equity 3,431; net working capital 1,473; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [60]
- **Coherence — BS vs implied-valuation bridge:** cash BS $1,037M / bridge $1,037M; debt BS $288M / bridge $288M — reconcile with the implied-valuation bridge. [61]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Feb-26-2026** — [43]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Long Term Debt - Other | Other Borrowings | $0.0M | NA | NA | undated | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $118.7M | 4.800% | NA | undated | Y | N | USD |
| Revolving Credit Facility | Revolving Credit | $25.0M | 4.500% | Benchmark | 2030-10-03 | N | N |  |

- **8-Ks at instrument maturities:** _UNKNOWN_ — no trailing-12m instrument maturity to anchor an 8-K
- **Covenant / contract pointers (CIK-verified execution filings)** — [62]  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| Revolving Credit Facility | 8-K | 2017-05-26 | 0001352010-17-000022 — exhibit10-1epamcreditagree.htm |
| Revolving Credit Facility | 8-K | 2021-10-25 | 0001352010-21-000039 — exhibit101-arcreditagreeme.htm |
| Long Term Debt | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Revolving Credit Facility (governing agreement)** — [63]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001352010-21-000039 · exhibit101-arcreditagreeme.htm |
| Principal / commitment amount | $700,000,000 revolving credit facility; Swingline Loan Commitment up to $50,000,000; Letter of Credit Sublimit $100,000,000; Alternative Currency Sublimit lesser of $150,000,000 and the total Revolvi… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Interest / coupon rate | Base Rate + Applicable Margin (Base Rate spread 0.000%–1.000%); or Adjusted Eurocurrency Rate + Applicable Margin (Eurocurrency Rate spread 0.875%–2.000%), based on Consolidated Leverage Ratio (Level… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Maturity date | October 21, 2026 · October 21, 2026 (Expiration Date), subject to extension | amended by 0001352010-21-000039 |
| Financial-maintenance covenants | Maximum Consolidated Leverage Ratio 3.50 to 1.00 (temporarily 4.00 to 1.00 for four fiscal quarters following a Material Permitted Acquisition, requestable not more than twice); Minimum Consolidated… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Security / collateral / guarantors | Guarantors: each direct or indirect Subsidiary of the Borrower (other than Excluded Subsidiaries), per the Continuing Agreement of Guaranty and Suretyship. Signatory Guarantors include Vested Develop… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Mandatory prepayment / events of default | Mandatory prepayment (Section 5.3): (a),(b) Reserved; (d) if Alternative Currency Loans/LC Obligations exceed 105% of the Alternative Currency Sublimit, prepay/Cash Collateralize within 5 Business Da… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Letter of Credit Sublimit | $50,000,000.00 | base (footer) |
| Incremental Loan Commitment | Incremental Loan Commitments up to $100,000,000.00 aggregate; minimum $25,000,000.00 each | base (footer) |
| Commitment Fee | Applicable Commitment Fee Rate (based on Leverage Ratio per pricing grid on Schedule 1.1(A)) multiplied by average daily unused difference | base (footer) |
| Permitted Acquisition Leverage Ratio condition | 2.75 to 1.00 | base (footer) |
| Use of Proceeds | Working capital and general corporate needs (including Letters of Credit); refinance existing Indebtedness; finance ongoing capital expenditures and Permitted Acquisitions | base (footer) |
| Governing Law | Section 10.11.1 Governing Law [specific state not stated in exhibit text; heading references CHOICE OF LAW] | base (footer) |

_Source §: 8-K 0001352010-17-000022 · exhibit10-1epamcreditagree.htm · amended by 0001352010-21-000039_


### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 5245.3 [64]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $1,037.00M, − total debt $287.90M [65]
- **Implied equity at peer-median ($M, CIQ)** — [66]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 5,216.2 |
| NTM Revenue (Capital IQ) | 6,765.0 |
| NTM EBITDA (Capital IQ) | 6,177.5 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [67]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 6 · sells 0 (net +0.5K sh) · grants 18 · last 2026-05-22 · other filings 36 [68]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-30): 10.3M → 11.3M sh (+9.5%, rising) · 21.6% of shares out (EDGAR XBRL) · DTC 5.7d · recent: 2026-06-30 11.3M · 2026-06-15 10.3M · 2026-05-29 9.6M · 2026-05-15 9.3M [24]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [69]
- **Guide verification — CIQ guide vs release:** revenue: CIQ 1400.0–1415.0 vs release 4.0–6.5 → MISMATCH flag [70]

## Record & reproduce
- **Data window:** screened as of 2026-07-06 · assembled 2026-07-30 11:39 UTC
- **Extraction:** 2026-07-28.1 — unusual-items surfacing in the financial summary (#238) · multiples read from the latest close, NM rather than a stale figure (#241)
- **Panel age:** oldest panel 2d old — 2026-07-28 (stock_info.as_of), against a 2026-07-30 build
- **Consensus age:** consensus 3d old (2026-07-27, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001352010` · NYSE : EPAM
- **Assembly log:** primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+1.1s fetch)
- **Re-run:** `python -m vinci dossier --ticker EPAM` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[5] `EOD EPAM 180d to 2026-07-06`
[6] `EOD MDY 180d to 2026-07-06 (cap-band: $5.2B @ 2026-07-06 → mid ($4–25B) → MDY)`
[7] `EOD EPAM−MDY 180d to 2026-07-06 (assembly, cap-band)`
[8] `CIQ Net Debt $-749M [Q1 Mar-31-2026] ÷ CIQ EBITDA $732M [LTM 12 months Mar-31-2026]`
[9] `EDGAR XBRL FCF sign (screen data-record)`
[10] `CIQ transcript: EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`
[11] `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 38 quarters (partial last column excluded from the distribution)`
[12] `CIQ Estimates→Revisions (Last-Month breadth, FY)`
[13] `CIQ Financials→Ratios (Return on Capital %, multi-year columns)`
[14] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[15] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[16] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[17] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[18] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[19] `8-K 0001352010-26-000010 EX-99.1`
[20] `CIQ Customers&Suppliers EPAM Systems Inc NYSE EPAM Customers.rtf`
[21] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[22] `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign (survival capacity)`
[23] `EDGAR XBRL shares, trailing 2024-07-31..2026-04-30`
[24] `FINRA consolidated short interest (settle 2026-06-30); DTC = 11,288,524 short ÷ 1,968,147 screen 90d ADV`
[25] `cadence: EDGAR submissions (median 91d gap over 52 results 8-Ks; last print 2026-05-07)`
[26] `TEV = mcap 5245.3 + net debt -749.0 (CIQ Comparable Analysis→Financial Data, Latest, as-of 2026-07-29) — simple-TEV basis`
[27] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[28] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[29] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-07-29`
[30] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[31] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[32] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[33] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[34] `8-K 0001352010-26-000026 EX-99.1 (filed 2026-05-07)`
[35] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
[36] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-07-27 · export date unverified]`
[37] `CIQ Estimates→Surprise (annual)`
[38] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-07-29`
[39] `CIQ Net Debt $-749M [Q1 Mar-31-2026] ÷ CIQ OCF $594M [LTM 12 months Mar-31-2026]`
[40] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[41] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-07-29`
[42] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
[43] `CIQ Financials→Capital Structure Details (A 2025 filed Feb-26-2026)`
[44] `CIQ Financials→Capital Structure Summary`
[45] `10-Q 0001352010-26-000029`
[46] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[47] `committed financial_summary.annual FY26E — CIQ Estimates→Trends 'Current', as-of ≥2026-06-18`
[48] `committed financial_summary.annual FY27E — CIQ Estimates→Trends 'Current', as-of ≥2026-06-18`
[49] `committed financial_summary.annual (LTM) — CIQ Income Statement`
[50] `EDGAR companyfacts OperatingIncomeLoss ÷ RevenueFromContractWithCustomerExcludingAssessedTax, 10-K 365d points — regime-split basis pull 2026-07-21`
[51] `EDGAR companyfacts — same basis, FY2025 (520 EBIT / 5,457 revenue)`
[52] `EDGAR companyfacts — same basis, FY2022 (573 EBIT / 4,825 revenue); GAAP carries the war-year charges, so a cleaned FY22 would sit higher`
[53] `EDGAR companyfacts — same basis, pre-2022 window; shown for reference ONLY (the pre-invasion cost structure no longer exists)`
[54] `EDGAR companyfacts — same basis, 10 FY; equals the committed anchor's margin, which averages across the 2022 regime break and describes neither regime`
[55] `committed valuation.own_history series, 2022Q1 onward (n=18) — refreshed band sha 9614730c9e`
[56] `committed valuation.own_history — refreshed band sha 9614730c9e`
[57] `committed valuation.own_history current, as-of 2026-07-17 — refreshed band sha 9614730c9e`
[58] `EDGAR companyfacts DepreciationAndAmortization FY2025 (accession 0001352010-26-000015)`
[59] `CIQ Financials→Income Statement (quarterly, full exported history)`
[60] `CIQ Financials→Balance Sheet (quarterly, Q1-26)`
[61] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[62] `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`
[63] `fenced Tier-2 extraction (verbatim, source-bound)`
[64] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-07-29`
[65] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-07-29`
[66] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-07-29`
[67] `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q4 2025 Earnings Call, Feb 19, 2026.rtf`
[68] `EDGAR Form 4 (latest 0001355666-26-000002; 25 in 6m)`
[69] `10-Q maturity wall vs CIQ capital panel (same window)`
[70] `CIQ revenue guide vs release actual/outlook`