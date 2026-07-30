# Dossier — Microvast Holdings, Inc. (Nasdaq: MVST)

_July 10, 2026 · extraction unstamped_

# Brief — first cut

## At a glance
**Target (base)** $0.60 (-34.5% vs entry-vintage spot) · **Spot** $0.92 (entry-vintage — frozen at underwrite 2026-07-22) · **Reward** $-0.32 · **Risk** $0.97 · **Reward : risk** -0.33 : 1 (bar 2 : 1)

_Spot source: Polygon MVST close 2026-07-21 (live at underwrite)_

**Underwrite disposition:** WATCH (2026-07-22) — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

### Thesis — our rationale
_Prices quoted below are entry-vintage (2026-07-22); the live close is in Snapshot, above._

WATCH at $0.92. The underwrite fails our 2:1 bar: the base case is worth roughly the market price in today's terms, so the price pays nothing for the very real chance the equity is worth zero - the company's own filings state substantial doubt it can continue, a debt wall comes due within a year against roughly matching cash, and the share count is compounding double-digit through an open selling programme. The gross-margin turnaround is real engineering - from deeply negative to thirty percent in three years - which is why this stays on the watch list at all. We revisit on a completed refinancing, or on returning growth with cash generation.

### What would reopen this name

- the maturity wall is refinanced or extended (a material-agreement or debt-obligation filing) - re-underwrite survival
- two consecutive quarters of positive revenue growth AND positive operating cash flow - the rollover was a squeeze, not a break; re-underwrite the central and optimistic cases
- going-concern language removed in a periodic filing - re-underwrite in full

> ⚠ **Verify before the verdict:** Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis — full caveats in Analysis.

Microvast Holdings, Inc. engages in the design, development, and manufacturing of battery components and systems primarily for electric commercial vehicles and energy storage systems.
- **Segments:** Batteries / Battery Systems — single segment [1]
- **Geography:** China 33%; Italy 22%; France 18%; Other Europe 10%; U.S. 9%; India 8%; Other Asia & Pacific 1% [2]
- **Customer concentration:** top customer 52% (from 31%) · top-2 ~70% of revenue [3]
- **Snapshot:** Nasdaq · CMP $1.08 (2026-07-08) · cap $423M (2026-05-15) · 52-wk $1.03–$7.12 · shares 333.2M · book value/sh $1.40 [4]

**The crux — what decides this, and what would change our mind**
**Can the near-term maturity wall be refinanced/converted and operating cash generation be restored before the going-concern doubt becomes terminal — i.e. is the collapse a survivable liquidity squeeze on a genuinely profitable business, or a value trap on a business whose profitability was one-off-flattered and is now contracting?**
_8 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-08-11 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-03-17 earnings; 2026-05-12 earnings; 2026-05-18 no 8-K matched [5]
- **Price (180d):** -62.9% [6]
- **vs market (180d):** -80.9% [7]
- **Net debt / EBITDA:** 3.9x [8]
- **Free cash flow:** positive [9]
- **Going concern:** ⚠ SUBSTANTIAL DOUBT stated [3]

## Scenario analysis
_Terminal-margin: value the business in the year it reaches a normal operating margin, then discount that value back at the house waiting charge._

| scenario | revenue $M | margin | multiple | value / sh | vs entry-vintage spot |
| --- | ---: | ---: | ---: | ---: | ---: |
| bear | 550 | 2.0% | 6x | $-0.05 | -105.4% |
| base | 850 | 6.0% | 7.9x | $0.60 | -34.5% |
| bull | 1,000 | 10.0% | 10x | $1.50 | +63.8% |

- **bear** — the contraction proves durable: the largest customer (52% of revenue) wobbles, revenue stabilizes well below the peak run-rate, margins hold barely positive as a marginal producer; a levered, distressed supplier exit.
- **base** — revenue recovers on the consensus path with a haircut for the current -25% quarter; margin reaches levered-auto-supplier economics rather than the street's cut-but-still-hopeful path; exit at the closest economic analogue (a levered auto-parts maker at 7.9x), not the scale leader's multiple.
- **bull** — the gross-margin engineering (-28% to +31% in three years) carries through: revenue re-accelerates, double-digit operating margin arrives, partial deleveraging earns a step above the analogue.

**Scenario inputs** — every value in the grid recomputes from these.

| input | value | basis | source |
| --- | ---: | --- | --- |
| net debt | 199.9 $M | classified total debt less total cash and short-term investments, latest balance sheet [VENDOR BASIS: CIQ workbook; EDGAR has no depreciation tag for this filer] | CIQ Financials->Balance Sheet (vendor basis; EDGAR debt tags under-captured) |
| diluted shares | 385.272 shares | latest-quarter diluted weighted-average count, quarter ended 2026-03-31 | EDGAR WeightedAverageNumberOfDilutedSharesOutstanding |
| d and a ratio | 0.08941 rate | depreciation and amortisation over trailing revenue (33.228 / 371.637) [VENDOR BASIS: CIQ workbook; EDGAR has no depreciation tag for this filer] | CIQ Financials->Cash Flow and Income Statement (vendor basis) |
| share growth | 0.1 rate | OVERRIDE. The organic three-year compound rate (2.30%) cannot see the open $125M at-the-market programme already drawn +19% in two quarters; 10% a year approximates full remaining draw near current prices plus organic issuance. | EDGAR 8-K Item 1.01 accession 0000947871-25-000881 and the 424B5 of 2025-10-03 (Controlled Equity Offering Sales Agreement, up to $125,000,000); share series FY2022-FY2025 |
| burn to breakeven | 307.8 $M | three years at the stated current burn (102.60 x 3) - the survival block's years to breakeven | EDGAR 10-Q accession 0001628280-26-033590, quarter ended 2026-03-31 |

_Chain (EV/EBITDA):_ EBIT_T = terminal revenue × terminal margin → D&A_T = (latest-FY D&A ÷ latest-FY revenue) × terminal revenue → EBITDA_T = EBIT_T + D&A_T → EV_T = denominator_T × exit multiple   (denominator = EBITDA_T, or EBIT_T on EV/EBIT) → net debt_T = current net debt + cumulative burn to breakeven → equity_T = EV_T − net debt_T → shares_T = current diluted × (1 + share growth)^years + announced-raise shares → value_T = equity_T ÷ shares_T → PV = value_T ÷ (1 + hurdle)^years

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | R2_NEEDED | NOT applicable |
| Overall confidence | — |  |

_no positive operating margin over available history — needs revenue-anchored recipe_

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Gross margin has climbed a full multi-year arc from -28% (FY21) to 35-36% (FY25/LTM) and absolute EBITDA turned from -$180M (FY21) to +$74M (FY25), showing the model reached genuine operating profitability, not just an optical improvement. [10]
- The name is FCF-positive on an LTM basis (+$39.6M levered FCF) after years of deep cash burn, a material inflection in cash generation. [11]
- The $25.0M shareholder convertible maturing 2026-05-28 was resolved by conversion to equity rather than a cash default, removing a near-term maturity from the wall. [12]
_Bear case — the decline is real:_
- The latest 10-Q states SUBSTANTIAL DOUBT about going concern (with plans present), the single most load-bearing terminal-risk fact in the file. [3]
- The reported EBITDA margin improvement is heavily flattered by one-offs: a $32.5M inventory impairment sits inside the numbers and company-adjusted LTM EBITDA is only ~$10.7M, pushing net-debt/adjusted-EBITDA to ~18.7x — the 3.9x GAAP-basis leverage is the optical MISREAD, the adjusted ~18.7x is closer to the real signal. [13]
- A $111.2M maturity wall is due within 12 months on a filing basis against only $126M cash, a tight liquidity bridge for a going-concern name. [3]

## Financial snapshot
- **Financial snapshot** — [14]  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 204 | 307 | 380 | 428 | 372 | 444 | 592 |
| Revenue growth | — (basis) | +50% | — (basis) | +13% | — (basis) | +4% (vs FY25) | +33% |
| EBITDA ($M) | -140 | -85 | 5 | 74 | 52 | 62 | 148 |
| EBITDA margin | -68% | -28% | 1% | 17% | 14% | 14% | 25% |
| EBIT ($M) | -160 | -108 | -26 | 40 | 19 | 20 | 69 |
| Net income ($M) | -158 | -106 | -196 | -29 | -43 | 70 | 56 |
| EPS (GAAP, dil.) | -0.52 | -0.34 | -0.61 | -0.09 | -0.19 | 0.18 | 0.17 |
| FCF ($M) | -136 | -117 | -65 | 18 | 40 | — | — |

_table shows the last 4 fiscal years · 4 earlier years are in the Appendix_

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 9.0x as-of 2026-07-17 — trailing range 10.0–66.9x (median 19.3x) over 6 closes → LOW-CONFIDENCE (6 closes < 8q ≈2y) — floor read unreliable [15]
- **vs peers:** EV/EBITDA 11.1x vs peer median 14.5x (-23%); P/E NM vs peer median 39 [16]
- **Comparability:** market caps span $34M–$275.0B (8063x); the name is $423M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [17]
- **The street, for contrast (target · ratings):** Target price: mean $5.50, median $5.50, high/low 6.00/5.00, N 2/2; Ratings: Buy 2, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-05-15 · export date unverified] [18]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [5]
  - 2026-03-17 → earnings
  - 2026-05-12 → earnings
  - 2026-05-18 → no 8-K matched

_Company-specific or market-wide?_
- **Name 180d return:** -62.9% [6]
- **Relative vs market:** -80.9% [7]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-down 2026-03-17 → filed 2026-03-16 [`0001628280-26-018235`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026018235/mvst-20260316.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj EBITDA 2025 $44.7M (vs -$44.8M 2024); adj net income 2025 $13.0M (vs -$84.6M 2024); adj EPS 2025 -$0.11 (vs -$0.27 2024); $32.5M inventory impairment charge related to; 2026 revenue outlook: qualitative [19]
  - gap-down 2026-05-12 → filed 2026-05-11 [`0001628280-26-033601`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026033601/mvst-20260511.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj EBITDA Q1 2026 -$5.5M (vs $28.5M Q1 2025); adj net income Q1 2026 -$14.6M (vs $19.3M Q1 2025); adj EPS Q1 2026 -$0.04; 2026 revenue outlook: qualitative [20]

## Business quality
- **Segments (revenue share):** Batteries / Battery Systems — single segment [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** 6 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [21]
- **Geographic:** China 33%; Italy 22%; France 18%; Other Europe 10%; U.S. 9%; India 8%; Other Asia & Pacific 1% [2]

## The argument

**Evidence balance:** strongly-bearish — stated going-concern doubt with a near-term maturity wall against thin cash while adjusted EBITDA has turned negative and revenue is contracting.

### Bull case — the decline is overdone
- Gross margin has climbed a full multi-year arc from -28% (FY21) to 35-36% (FY25/LTM) and absolute EBITDA turned from -$180M (FY21) to +$74M (FY25), showing the model reached genuine operating profitability, not just an optical improvement. [10]
- The name is FCF-positive on an LTM basis (+$39.6M levered FCF) after years of deep cash burn, a material inflection in cash generation. [11]
- The $25.0M shareholder convertible maturing 2026-05-28 was resolved by conversion to equity rather than a cash default, removing a near-term maturity from the wall. [12]
- On fundamental_deltas the name shows a HIGHER EBITDA margin (14% vs peer-median 6%) and faster EBITDA growth (21% vs 1%), so the discount to the peer-median EV/EBITDA is at least partly RESIDUAL rather than fully earned — but the human must judge this against the HETEROGENEOUS peer set before treating it as a clean overshoot signal. [22]
- Interest coverage of 10.6x (LTM EBITDA ÷ interest) indicates the current debt load is serviceable out of operating earnings. [23]

### Bear case — the decline is real
- The latest 10-Q states SUBSTANTIAL DOUBT about going concern (with plans present), the single most load-bearing terminal-risk fact in the file. [3]
- The reported EBITDA margin improvement is heavily flattered by one-offs: a $32.5M inventory impairment sits inside the numbers and company-adjusted LTM EBITDA is only ~$10.7M, pushing net-debt/adjusted-EBITDA to ~18.7x — the 3.9x GAAP-basis leverage is the optical MISREAD, the adjusted ~18.7x is closer to the real signal. [13]
- A $111.2M maturity wall is due within 12 months on a filing basis against only $126M cash, a tight liquidity bridge for a going-concern name. [3]
- The most recent quarter reversed the profitability story: Q1 2026 adjusted EBITDA was -$5.5M (vs +$28.5M Q1 2025) and adjusted net income -$14.6M (vs +$19.3M), so the trailing margin recovery is already rolling over. [20]
- The self-funding read is MIXED, not clean: latest-quarter OCF is negative even though LTM FCF is positive — both must be positive to self-fund, so recent cash generation has turned. [24]
- Customer concentration spiked to 52.0% for Customer A (from 31.0% prior), a severe single-customer dependency that amplifies revenue fragility. [3]
- Revenue is contracting sharply — Q1-26 revenue $61M vs $116M in Q1-25, a -37% QoQ and a -25.5% same-quarter YoY decline — the top line is deteriorating, not mean-reverting up. [25]
- Consensus estimates have been cut hard — FY26 EBITDA -52% and FY26 revenue -27% (12m→latest) — confirming a deteriorating forward path, not a temporary overshoot. [26]

### Decisive question
**Can the near-term maturity wall be refinanced/converted and operating cash generation be restored before the going-concern doubt becomes terminal — i.e. is the collapse a survivable liquidity squeeze on a genuinely profitable business, or a value trap on a business whose profitability was one-off-flattered and is now contracting?**

### …evidence for
- LTM FCF is positive (+$39.6M) and interest coverage is 10.6x, consistent with a business that can service debt from operations. [11]
- The $25.0M shareholder convertible maturing in May 2026 was resolved by conversion to equity rather than a cash outflow, evidence a friendly capital source is willing to convert rather than force repayment. [12]
- Gross margin and absolute EBITDA rose across a multi-year arc, indicating underlying unit economics that improved rather than a purely accounting move. [10]

### …evidence against
- The 10-Q states SUBSTANTIAL DOUBT about going concern. [3]
- Company-adjusted LTM EBITDA is only ~$10.7M implying ~18.7x net leverage once one-offs are stripped, and Q1-26 adjusted EBITDA already turned negative (-$5.5M). [13]
- A $111.2M wall is due within 12 months against $126M cash while latest-quarter OCF is negative. [3]

### Key unknowns
- Covenant basis leverage and the minimum-liquidity covenant threshold are UNKNOWN/undisclosed — whether the name is in or near breach cannot be judged (bearish opacity given going-concern status).
- No numeric FY26 revenue guidance was given — the outlook is QUALITATIVE-only, and the CIQ 427.5 'guide' is a stale vendor-echo of prior-year actual, leaving no verified forward guide (bearish disclosure gap).
- Adjusted forward EV/EBITDA, adjusted EPS and net-debt/adjusted-EBITDA are not in the revised 99.1 guidance — the forward valuation basis is missing.
- Segment-level EBITDA is not disclosed (single reported segment); profitability by product/geography cannot be assessed.
- The refinancing/repayment plan for the $111.2M near-term wall is not quantified in the supplied facts beyond the resolved $25M conversion.
- The trailing EV/EBITDA multiple (10.0x at the 0th percentile of a 4-close, <2y history) is flagged low-confidence and trailing-only — it cannot distinguish cheap-overshoot from cheap-terminal and is treated as neutral, not directional.
- Peer set is HETEROGENEOUS (market caps span $34M–$275.0B, 8063x); every peer multiple and the residual-vs-earned discount read is confidence-gated, not a clean benchmark.
- IWM/market 180d benchmark and exposed-cohort returns are unavailable — idiosyncratic-vs-shared drawdown attribution is incomplete.

### Twin reference cases
- **Romeo Power** — went terminal (LLM-claimed — verify)
  - distinguished by: EV/commercial-vehicle battery maker that reached going-concern doubt with heavy customer concentration and a cash wall it could not clear.
  - source: [LLM-suggested, unverified]
- **Proterra** — went terminal (LLM-claimed — verify)
  - distinguished by: Commercial-EV battery/powertrain supplier that showed improving gross margins yet filed for bankruptcy under a liquidity wall it could not refinance.
  - source: [LLM-suggested, unverified]
- **Plug Power** — recovered (LLM-claimed — verify)
  - distinguished by: Clean-energy hardware name that carried going-concern-style doubt and dilution yet remained a going concern by repeatedly accessing equity/refinancing capital.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-08-11 `[cadence-estimate]` — the next reported quarter against the committed trajectory [27]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 11.1x vs peer median 14.5x (-23%); P/E NM vs peer median 39 [16]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-06-24 · multiples as-of 2026-05-15 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [28]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **7.54x** | **$82.6M EBITDA †** |
| peer-median NTM TEV/EBITDA | 12.9x | $48.3M EBITDA |
| peer-median LTM TEV/EBITDA | 14.5x | $43.0M EBITDA |
| **name NTM TEV/Rev** | **1.26x** | **$494.4M Revenue †** |
| peer-median NTM TEV/Rev | 2.55x | $244.3M Revenue |
| peer-median LTM TEV/Rev | 3.2x | $194.7M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $62.1M · FY27E $147.7M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $444.4M · FY27E $591.5M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 9.0x as-of 2026-07-17 — trailing range 10.0–66.9x (median 19.3x) over 6 closes → LOW-CONFIDENCE (6 closes < 8q ≈2y) — floor read unreliable [15]

## Peer comps
- **Peer set (roster · caps · business)** — [29]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Amprius Technologies | $2.0B | develops, manufactures, and markets lithium-ion batteries for mobility applications. (United States) |
| Forsee Power S.A. | $34M | designs, manufactures, and sells battery systems for electromobility in France, res of Europe, Asia, the United States, and internationally. (France) |
| Cummins Inc. | $96.5B | offers various power solutions worldwide. (United States) |
| BorgWarner Inc. | $14.5B | provides technology solutions for combustion, hybrid, and electric vehicles worldwide. (United States) |
| Contemporary Amperex Technology Co. | $275.0B | engages in the research, development, production, and sale of electric vehicle and energy storage system batteries in China and internationally. (China) |
| Panasonic Holdings Corporation | $64.4B | develops, manufactures, sells, services, and supplies various electrical and electronic equipment and related products in Japan, the Americas (Japan) |
| Leclanché SA | $167M | designs, develops, and manufactures customized turnkey energy storage solutions for electricity generation and transmission, mass transportation (Switzerland) |
| Samsung SDI Co. | $24.8B | manufactures and sells batteries in South Korea, Europe, China, North America, Southeast Asia, and internationally. (Gyeonggi-do South) |

_the name: $423M_

- **Comparability (confidence gate):** market caps span $34M–$275.0B (8063x); the name is $423M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [17]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [30]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 1.25 | 1.06 | 2.55 | 3.64 | 13.47 |
| NTM TEV/EBITDA | 7.46 | 7.63 | 12.9 | 43.3 | 198.12 |
| NTM P/E | 14.11 | 13.27 | 22.77 | 26.23 | 55.1 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [31]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Contemporary Amperex Technology Co. | $275.0B | 14.5 | 3.5 | 22.6 | 24% | 28% | 1.1 | 42,108 (net cash) |
| Cummins Inc. | $96.5B | 17.9 | 3.0 | 36.3 | 15% | 0% | 1.6 | 5,058 |
| Panasonic Holdings Corporation | $64.4B | 13.7 | 1.4 | 54.9 | 9% | -5% | 2.0 | 5,157 |
| Samsung SDI Co. | $24.8B | 38.4 | 3.7 | NM | 4% | -9% | 24.2 | 6,518 |
| BorgWarner Inc. | $14.5B | 7.9 | 1.2 | 41.7 | 14% | 2% | 2.0 | 1,963 |
| Amprius Technologies | $2.0B | NM | 22.0 | NM | -19% | 173% | NM | 56 (net cash) |
| **Microvast Holdings · the name** | **$423M** | **11.1** | **1.7** | **NM** | **14%** | **-10%** | **5.8** | **200** |
| Leclanché SA | $167M | NM | 11.2 | NM | -265% | 32% | NM | 100 |
| Forsee Power S.A. | $34M | NM | 0.7 | NM | -10% | -21% | NM | 63 |
| Peer median (peers) | $19.7B | 14.5 | 3.3 | 39.0 | 6% | 1% | 2.0 | 1,031 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [10]  <!-- ds-table -->

|  | Dec-2021 | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 | Dec-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|---|
| Gross margin | -28% | 4% | 19% | 31% | 36% | 35% |

_Revenue YoY (latest same-quarter): -25.5% (Q1 Mar-31-2026 vs Q1 Mar-31-2024). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** diluting (trailing ~1.7y): 323,815,298 (2024-08-05) → 333,157,384 (2026-05-04), +2.9% [32]
- **Return ratios — per fiscal period** — [33]  <!-- ds-table -->

|  | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|
| RoE % | -57.1% | -24.3% | -18.1% | -41.1% | -7.3% | -9.3% |
| RoCE % | -24.5% | -12.3% | -8.7% | -2.2% | 3.3% | 1.5% |
| RoA % | -17.9% | -10.1% | -6.5% | -1.6% | 2.6% | 1.2% |
| Total debt/equity | 0.21x | 0.29x | 0.36x | 0.85x | 0.94x | 0.70x |
| Current ratio | 4.02x | 2.16x | 1.06x | 1.30x | 0.92x | 0.96x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-05-15)_
- **Horizon read (FQ — next-2Q revision breadth)** — [34]:
  - EPS Normalized FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Revenue FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - Revenue FQ3 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBIT FQ2 2026: 1m 0↑/0↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EBIT FQ3 2026: 1m 0↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - _no revisions in any window: EPS Normalized FQ2 2026, EPS (GAAP) FQ2 2026, EPS (GAAP) FQ3 2026, EBITDA FQ2 2026, EBITDA FQ3 2026_
  - _+5 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 0.24 (12m) → 0.29 (9m) → 0.20 (6m) → 0.06 (3m) → 0.06 (2m) → 0.04 (1m) → 0.04 (latest); net -83% (12m→latest) | FY 2026 EPS (GAAP): 0.09 (12m) → 0.11 (9m) → 0.09 (6m) → 0.05 (3m) → 0.05 (2m) → 0.18 (1m) → 0.18 (latest); net +100% (12m→latest) | FY 2026 Revenue: 609.0 (12m) → 593.9 (9m) → 544.2 (6m) → 480.5 (3m) → 480.5 (2m) → 444.4 (1m) → 444.4 (latest); net -27% (12m→latest) | FY 2026 EBITDA: 129.7 (12m) → 146.5 (9m) → 146.5 (6m) → 62.1 (1m) → 62.1 (latest); net -52% (12m→latest) [3m, 2m n/a] | FY 2026 EBIT: 46.1 (12m) → 52.8 (9m) → 43.4 (6m) → 22.5 (3m) → 22.5 (2m) → 20.0 (1m) → 20.0 (latest); net -57% (12m→latest) | FY 2026 Interest Expense: -13.7 (12m) → -4.61 (9m) → -4.81 (6m) → -5.02 (3m) → -5.02 (2m) → -4.91 (1m) → -4.91 (latest); improving (magnitude toward zero) (12m→latest) | FY 2026 EBT (GAAP): 37.0 (12m) → 59.4 (9m) → 38.8 (6m) → 17.6 (3m) → 17.6 (2m) → 73.1 (1m) → 73.1 (latest); net +98% (12m→latest) | FY 2026 Net Income (Excl. Excep): 92.7 (12m) → 92.6 (9m) → 21.4 (3m) → 21.4 (2m); net -77% (12m→2m) [6m n/a] | FY 2026 Net Income (GAAP): 33.4 (12m) → 42.3 (9m) → 32.9 (6m) → 17.6 (3m) → 17.6 (2m) → 70.1 (1m) → 70.1 (latest); net +110% (12m→latest)  [data ≥ 2026-05-15 · export date unverified] [26]
- **Cross-name anchor (NTM forward-multiple ladder)** — [35]:
  - NTM: TEV/REV 1.26 · TEV/EBITDA 7.54 · TEV/EBIT 17.55 · Price/Earnings 14.33 · PEG –
  - FY 2026: TEV/REV 1.42 · TEV/EBITDA 10.14 · TEV/EBIT 31.54 · Price/Earnings 32.25 · PEG –
  - FY 2027: TEV/REV 1.06 · TEV/EBITDA 4.26 · TEV/EBIT 9.17 · Price/Earnings 8.60 · PEG –
  - FY 2028: TEV/REV 0.83 · TEV/EBITDA 3.47 · TEV/EBIT 5.35 · Price/Earnings – · PEG –
  - _+5 later fiscal years in JSON_
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [36]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | 427.5 | FY 2026 | 2026-03-16 | 112d (stale) | actual ≥ floor 10/13 | FY 2025 MISSED |
| Capital Expenditure | '(180.00) - (210.00)' | FY 2023 | 2023-11-10 | 969d (stale) | spend ≤ ceiling 4/4 | FY 2023 MET |
| Gross Margin % | '32.00 - 35.00' | FY 2025 | 2025-11-10 | 238d (stale) | actual ≥ floor 4/4 | FY 2024 MET |

- **Consensus stats (target + ratings):** Target price: mean $5.50, median $5.50, high/low 6.00/5.00, N 2/2; Ratings: Buy 2, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-05-15 · export date unverified] [18]
- **Revision-event log (47 events · 3 broker-days)** — [37]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-05-15 | H.C. Wainwright & Co. | 18 | 3 | 6 | 9 | EBITDA FY 2026 | 146.5 | 62.1 | −84.4 |
| 2026-05-11 | broker undisclosed | 13 | 5 | 8 | — | Revenue FQ2 2026 | 103.2 | 95.9 | −7.3 |
| 2026-03-17 | broker undisclosed | 16 | — | 16 | — | Revenue FY 2026 | 525.0 | 480.5 | −44.5 |

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 +0%; Revenue surprise: FY2021 +3%, FY2022 +2%, FY2023 +3%, FY2024 +6%, FY2025 -8% (GAAP-EPS basis; +beat / −miss) [38]

## Leverage & survival
- **Net debt / EBITDA [NET]:** 3.9x [8]
- **Total debt / EBITDA vs peers:** name 5.8x vs peer median 2.0x (comps TOTAL-debt/EBITDA basis) [39]
- **Net debt / OCF:** 4.4x [40]
- **Interest coverage:** 10.6x [23]
- **Self-funding:** self-funding: MIXED — latest-Q OCF < 0, LTM FCF > 0 (both must be positive to self-fund) [24]
- **Credit health** — [41]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 3 | 2.5 |
| Operational | 3 | 2.5 |
| Solvency | 2 | 3 |
| Liquidity | 2 | 3 |

_S&P issuer rating unrated · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [9]
- **Free cash flow ($M):** 39.6 [11]
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Mar-16-2026** — [42]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Convertible Bond - CNY | Bonds and Notes | $41.7M | 3.000% - 4.000% | NA | 2027-01-31 | Y | Y | CNY |
| Convertible Loan With Shareholder - Delayed Draw Term Loan | Term Loans | $13.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Convertible Loan With Shareholder - Initial Term Loan | Term Loans | $12.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Loan Facilities Agreement With a Group of Lenders Led by a Bank in China | Term Loans | $42.9M | NA | New Benchmark | 2026-12-10 | Y | N | CNY |
| Long-term Loan Agreement With a Chinese Bank | Term Loans | $13.9M | 2.700% | NA | 2027-06-19 | Y | N | CNY |
| Short-term Loan Agreements and Bank Facilities With Chinese Banks | Term Loans | $49.5M | 2.400% - 4.850% | NA | 2027-03-31 | Y | N | USD |

_2 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-07-06 reference:
  - **matured (pre-reference): $25.0M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-05-28 (39d before ref): $13.0M Convertible Loan With Shareholder 
    - 2026-05-28 (39d before ref): $12.0M Convertible Loan With Shareholder 
  - due ≤12m (through 2026): $42.9M — 2026-12-10 $42.9M
  - due 2027: $105.1M
  - undated (floor — no panel maturity): $95.6M — Notes Payable $78.3M, Operating Lease Liabilities $17.3M
  - _reconciliation: itemized $268.6M (panel A 2025 filed Mar-16-2026) vs the latest-quarter aggregates below — the gap is unitemized / newer term loans; read the QoQ movement in the aggregates line._
- **Capital-structure aggregates (latest quarter):** term loans 215.2 (131.3→215.2 QoQ); senior bonds 94.0; leases 16.8; total principal 326.0; total debt 326.0 (latest quarter) ($M) [43]
- **Maturity resolution (8-K verbatim):** On May 28, 2026, Mr. Wu delivered a Notice of Conversion in respect of the full $25.0 million principal amount outstanding under the Loan Agreement. Such principal amount will be converted into shares of common stock of the Company in accordance with the terms of the Loan Agreement. [12]
- **Covenants — Convertible Loan** (governing values; full verbatim in appendix):
  - **Conversion:** “Conversion Price” means at any time an amount equal to $1.00 divided by the applicable Conversion Rate at such time. C…
  - **Interest / coupon:** Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK) · Term SOFR for the applicable Interest Period plus the Applicable Margin (9.75% per annum), with 3.75% paid in-kind (PIK…
  - **Maturity:** May 28, 2026 · clause (a) of the definition of “Maturity Date” amended to “May 28, 2026” (previously “November 28, 2025”)
  - **Financial maintenance:** Minimum Liquidity: not permit Liquidity of Borrower and its Subsidiaries, as of Friday of each calendar week (Liquidity…
  - **Events of default:** Effectiveness/representation condition that no Default or Event of Default has occurred or is continuing; no mandatory…
- **Covenants — Loan Facilities Agreement** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LPR + 115 bps · Floating rate: one-year LPR published by the National Interbank Funding Center plus 115 bps
  - **Interest / coupon:** Late Default Interest Rate: 150% of applicable Interest Rate; Misappropriation Default Interest Rate: 200% of applicabl…
  - **Maturity:** December 10, 2026 · December 10, 2026 (5 years total)
  - **Financial maintenance:** Financial indicator covenant present but specific indicators not stated (field marked [/]); Borrower undertakes final t…
  - **Events of default:** acceleration · Events of Default listed in Article 15.1 (misrepresentation, breach, payment default, misappropriation, cross default,…

### Filing cross-checks — going concern · leverage basis

- **⚠ Going concern — SUBSTANTIAL DOUBT:** These conditions and events raise substantial doubt about the Company's ability to continue as a going concern. [3]
  - management's plans: plans to alleviate the substantial doubt include 1) obtaining sufficient funding through operations; it is anticipated that the Company will generate cash through operations in the forecasted period in consideration of the existing contract backlog and anticipated market conditions; and 2) refinanci
- **EBITDA-basis triangulation (each leverage basis-labeled):** [13]
  - net debt / EBITDA (CIQ, GAAP basis): 3.9x
  - total debt / EBITDA (CIQ comps, GAAP basis): 5.8x
  - net debt / company-adjusted LTM EBITDA ($10.7M): ~18.7x
  - covenant basis: UNKNOWN (not disclosed)
  - margin: GAAP 28.6% · impairment-excluded 36.2% (CIQ; cross-check 28.6 + 32.5/427.5 = 36.2%)
- **Customer concentration (latest 10-Q):** [3]
  - Customer A: 52.0% (prior 31.0%)
  - Customer B: 18.0% (prior 16.0%)
  - order terms: purchase orders or framework supply agreements that are subject to adjustment, cancellation, deferral, or suspension by our customers,

## ⚠ Analyst caveats — verify before the verdict

_3 to verify._

- Net debt/EBITDA (3.9x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.9x as the covenant-basis leverage.
- Estimates data up to 52d stale (beyond the 45d tolerance) — freshness UNVERIFIABLE: the CIQ Estimates export has no as-of stamp, and its data is on/after 2026-05-15 (its latest embedded revision event — a worst-case floor on the true export date). Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar).
- Possible false balance — the written assessment commits a strong lean but the body is near-symmetric (5 bull vs 8 bear) and the minority bull points aren't qualified-as-outweighed — size the minority against the lean, or it launders a one-sided case

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

Terminal revenue starts from the street path and is cut for what the latest quarter actually did: revenue fell about a quarter year on year, so the central case sits well below the street's own two-year figure. Everything past the street's second year is our extrapolation.

| reference | value |
| --- | ---: |
| street revenue, FY2026 | $444.4M [44] |
| street revenue, FY2027 | $591.5M [44] |
| reported revenue, FY2025 | $427.5M [45] |
| latest-quarter revenue decline, year on year | -25.5% [46] |
| street revenue cut over twelve months | -27% [44] |

### Margin · **DRAFT — not ratified by the analyst**

Reported accounting basis throughout, and the depreciation assumption is vendor-sourced because this filer tags none at all in its own machine-readable filings - stated here so the basis is never mistaken for a primary figure. The gross-margin arc is real: minus twenty-eight per cent to plus thirty-one in three years. The operating margin turned positive for the first time in the latest full year and has already rolled over - the most recent quarter's adjusted operating profit is negative against a strongly positive comparison. The central case therefore takes levered auto-supplier economics rather than the street's cut-but-still-hopeful path, and the leverage read that matters is the company-adjusted one, not the headline.

| reference | value |
| --- | ---: |
| gross margin, FY2021 | -28.1% [47] |
| gross margin, FY2024 - the arc's peak | 31.5% [47] |
| gross margin, FY2025 | 28.6% [47] |
| reported operating margin, FY2025 - first positive year | 1.6% [48] |
| street operating margin, FY2026 - stated | 4.5% [49] |
| street operating margin, FY2027 - stated | 11.6% [49] |
| street earnings cut over twelve months | -52% [44] |
| leverage on company-adjusted earnings | 18.7x [50] |
| depreciation and amortisation - vendor basis | $33.228M [51] |

### Multiple · **DRAFT — not ratified by the analyst**

The exit is set at the closest economic analogue - a levered auto-parts maker - rather than at the scale leader, whose multiple belongs to a business with tens of billions of net cash and none of this balance sheet. This company's own trading history is unusable as an exit: six closes over one and a third years, with the current reading below its own trailing low, which the range read itself calls low-confidence. The peer median spans thirty-four million to two hundred and seventy-five billion of market value, so it is a number rather than a comparison.

| reference | value |
| --- | ---: |
| closest economic analogue, enterprise value to EBITDA `base` | 7.9x [52] |
| _scale leader, enterprise value to EBITDA — excluded: the scale leader's multiple belongs to a different business model (see method)_ | _14.5x_ [53] |
| peer median, heterogeneous nine-name set | 14.5x [54] |
| _this company's trailing median — excluded: six closes over 1.3 years — too short a series to stand on_ | _19.3x_ [55] |
| this company's current reading - below its own trailing low | 9x [56] |

### Horizon · **DRAFT — not ratified by the analyst**

Four years, matching the other records on this recipe so the three are comparable. The survival block sets breakeven three years out, so the terminal year sits one year past the point the business is assumed to fund itself.

| reference | value |
| --- | ---: |
| years to the terminal year | 4years [57] |
| waiting charge applied over the horizon | 74.9% [58] |


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-05-15)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [14]  <!-- ds-table -->

|  | FY18 (R) | FY19 (R) | FY20 (R) | FY21 | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 174 | 76 | 108 | 152 | 204 | 307 | 380 | 428 | 372 | 444 | 592 |
| Revenue growth | — | -56% | +41% | — (basis) | — (basis) | +50% | — (basis) | +13% | — (basis) | +4% (vs FY25) | +33% |
| EBITDA ($M) | -45 | -39 | -15 | -180 | -140 | -85 | 5 | 74 | 52 | 62 | 148 |
| EBITDA margin | -26% | -51% | -14% | -118% | -68% | -28% | 1% | 17% | 14% | 14% | 25% |
| EBIT ($M) | -58 | -54 | -32 | -200 | -160 | -108 | -26 | 40 | 19 | 20 | 69 |
| Net income ($M) | -55 | -58 | -34 | -206 | -158 | -106 | -196 | -29 | -43 | 70 | 56 |
| EPS (GAAP, dil.) | -161.90 | -1.17 | -0.82 | -1.26 | -0.52 | -0.34 | -0.61 | -0.09 | -0.19 | 0.18 | 0.17 |
| EPS (Normalized) | -52.68 | -0.36 | -0.23 | -0.68 | -0.33 | -0.21 | -0.22 | 0.00 | -0.03 | 0.04 | 0.15 |
| CFO ($M) | -6 | 13 | 16 | -45 | -54 | -75 | 3 | 76 | 46 | — | — |
| Capex ($M) | -30 | -20 | -19 | -88 | -151 | -187 | -28 | -20 | -20 | — | — |
| FCF (levered, CIQ) | — | — | 16 | -175 | -136 | -117 | -65 | 18 | 40 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ?; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Quarterly — every exported quarter
- **Quarterly financials** — [59]  <!-- ds-table -->

|  | Q4-19 (R) | Q1-20 | Q2-20 | Q3-20 | Q4-20 (R) | Q1-21 (R) | Q2-21 | Q3-21 | Q4-21 | Q1-22 | Q2-22 | Q3-22 | Q4-22 | Q1-23 | Q2-23 (R) | Q3-23 (R) | Q4-23 (R) | Q1-24 | Q2-24 | Q3-24 (R) | Q4-24 (R) | Q1-25 (R) | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 31 | 7 | 22 | 31 | 48 | 15 | 33 | 37 | 67 | 37 | 64 | 39 | 65 | 47 | 75 | 80 | 105 | 81 | 84 | 101 | 113 | 116 | 91 | 123 | 96 | 61 |
| Gross margin | -21% | 27% | 16% | 12% | 18% | -8% | -20% | -97% | 2% | 0% | 8% | 5% | 3% | 10% | 15% | 22% | 22% | 21% | 33% | 33% | 37% | 37% | 35% | 38% | 35% | 32% |
| EBITDA ($M) | -12 | -6 | -4 | -5 | -1 | -8 | -18 | -109 | -45 | -38 | -40 | -33 | -30 | -26 | -22 | -21 | -15 | -16 | -4 | 12 | 12 | 22 | 18 | 23 | 11 | 0 |
| EBITDA margin | -40% | -88% | -16% | -15% | -2% | -53% | -53% | -295% | -68% | -103% | -63% | -85% | -47% | -56% | -30% | -27% | -15% | -20% | -5% | 12% | 11% | 19% | 19% | 19% | 11% | 0% |
| Revenue QoQ | — | — (basis) | +212% | +42% | — (basis) | -69% | — (basis) | +11% | +81% | -45% | +76% | -40% | +68% | -28% | — (basis) | +7% | +31% | — (basis) | +3% | — (basis) | +12% | +3% | — (basis) | +35% | -22% | -37% |
| Revenue YoY | — | — | — | — | +56% | — (basis) | +54% | +20% | — (basis) | — (basis) | +93% | +5% | -3% | +28% | — (basis) | — (basis) | — (basis) | +73% | — (basis) | +27% | +8% | — (basis) | +9% | — (basis) | — (basis) | — (basis) |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q1-26 ($M): cash & ST inv 126; total debt 326; net debt 200; equity 466; net working capital -18; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [60]
- **Coherence — BS vs implied-valuation bridge:** cash BS $126M / bridge $126M; debt BS $326M / bridge $326M — reconcile with the implied-valuation bridge. [61]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Mar-16-2026** — [42]  <!-- ds-table -->

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

- **8-Ks at instrument maturities:** 8-K at maturity 2026-05-28: filed 2026-05-28 [0000947871-26-000585] 5.02 Departure/Election of Directors or Certain Officers, 8.01 Other Events, 9.01 Financial Statements and Exhibits — read for resolution [62]
- **Covenant / contract pointers (CIK-verified execution filings)** — [63]  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| material contracts (10-K exhibit index) | latest 10-K | 2026-03-16 | 0001628280-26-018264 — mvst20251231-ex1013.htm, mvst20251231-ex1021.htm |
| Convertible Loan | 8-K | 2025-03-17 | 0000947871-25-000313 — ss4588423_ex1001.htm |
| Convertible Loan | 8-K | 2024-06-04 | 0001760689-24-000021 — wu_microvast-guarantyagree.htm, wu_microvast-loanandsecuri.htm, wu_microvast-pledgeagreeme.htm |
| Loan Facilities Agreement | 8-K | 2022-09-29 | 0001760689-22-000094 — exhibit101-syndicatedloana.htm |
| Notes Payable | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Convertible Loan (governing agreement)** — [64]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | “Conversion Price” means at any time an amount equal to $1.00 divided by the applicable Conversion Rate at such time. Conversion Rate: two (2) shares of Common Stock (subject to adjustment by the Bor… — full verbatim in JSON | base (footer) |
| Principal / commitment amount | Initial Term Loan Commitments: $12,000,000; Delayed Draw Term Loan Commitments: $13,000,000 (aggregate $25,000,000 per Annex I) | base (footer) |
| Interest / coupon rate | Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK) · Term SOFR for the applicable Interest Period plus the Applicable Margin (9.75% per annum), with 3.75% paid in-kind (PIK Interest); Floor of 3.00% per annum; Default Rate = Applicable Margin increased… — full verbatim in JSON | base (footer) |
| Maturity date | May 28, 2026 · clause (a) of the definition of “Maturity Date” amended to “May 28, 2026” (previously “November 28, 2025”) | amended by 0000947871-25-000313 |
| Financial-maintenance covenants | Minimum Liquidity: not permit Liquidity of Borrower and its Subsidiaries, as of Friday of each calendar week (Liquidity Testing Date), to be less than $5,000,000 (from Closing Date until Maturity Dat… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Liens securing the Obligations ratified and confirmed; ACQUIOM AGENCY SERVICES LLC as collateral agent; Guarantors: Microvast Holdings, Inc.; Microvast Advanced Materials Inc.; Microvast Advanced Mem… — full verbatim in JSON | amended by 0000947871-25-000313 |
| Mandatory prepayment / events of default | Effectiveness/representation condition that no Default or Event of Default has occurred or is continuing; no mandatory prepayment terms stated (Events of Default otherwise defined in the underlying L… — full verbatim in JSON | amended by 0000947871-25-000313 |

_Source §: 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by 0000947871-25-000313_

- **Covenant terms — Loan Facilities Agreement (governing agreement)** — [64]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Principal / commitment amount | RMB 800,000,000.00 yuan (Eight hundred million yuan) | base (footer) |
| Interest / coupon rate | LPR + 115 bps · Floating rate: one-year LPR published by the National Interbank Funding Center plus 115 bps | base (footer) |
| Default interest rate | Late Default Interest Rate: 150% of applicable Interest Rate; Misappropriation Default Interest Rate: 200% of applicable Interest Rate | base (footer) |
| Maturity date | December 10, 2026 · December 10, 2026 (5 years total) | base (footer) |
| Financial-maintenance covenants | Financial indicator covenant present but specific indicators not stated (field marked [/]); Borrower undertakes final total financing balance for the Project does not exceed RMB 800 million and final… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Mortgage under three Mortgage Contracts (#HuKai 2022 C113, C114, C115 dated 1 September 2022); Mortgagor and Pledgor = Microvast Power Systems Co., Ltd.; Guarantor = [/] (not stated); Security Docume… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | acceleration · Events of Default listed in Article 15.1 (misrepresentation, breach, payment default, misappropriation, cross default, insolvency, bankruptcy, enforcement events, financial indicators, Material Adver… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm_

- **Covenant terms — material contracts (10-K exhibit index) (governing agreement)** — [64]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Principal / commitment amount | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Interest / coupon rate | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Maturity date | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Security / collateral / guarantors | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Mandatory prepayment / events of default | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Vesting schedule | One-third on each of the first, second, and third anniversaries of the Grant Date | base (footer) |
| Settlement | One Share per vested RSU (or cash equal to Fair Market Value of a Share on the applicable Vesting Date), by the Settlement Date (no later than March 15 of the year following vesting) | base (footer) |
| Forfeiture on termination | Unvested RSUs forfeited on any termination; all RSUs (vested-unsettled and unvested) forfeited on termination for Cause | base (footer) |
| Change in Control | Unvested RSUs treated per the Plan; vested-unsettled RSUs settled immediately prior to the Change in Control | base (footer) |
| Dividend Equivalents | Credited with Dividend Equivalents, converted into additional RSUs; subject to same vesting/settlement terms as the corresponding Award | base (footer) |
| Transfer restrictions | Non-transferable except by will or laws of descent and distribution | base (footer) |
| Clawback | Subject to clawback/recoupment per applicable law and Company policy | base (footer) |
| Governing law | State of Delaware | base (footer) |

_Source §: latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm_


### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 423.1 [65]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $126.10M, − total debt $326.00M [66]
- **Implied equity at peer-median ($M, CIQ)** — [67]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 550.7 |
| NTM Revenue (Capital IQ) | 1,070.4 |
| NTM EBITDA (Capital IQ) | 877.0 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [68]

### Ownership & positioning
- **Insider activity (Form 4, 6m):** Open-market buys 0 · sells 7 (net -121.0K sh) · grants 20 · last 2026-06-12 · other filings 1 [69]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-15): 21.4M → 26.3M sh (+22.9%, rising) · 7.9% of shares out (EDGAR XBRL) · DTC 5.8d · recent: 2026-06-15 26.3M · 2026-05-29 21.4M · 2026-05-15 21.6M · 2026-04-30 21.2M [70]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence — filing cross-validates panel: panel same-window $109.6M (CIQ panel, principal basis) vs filing $111.2M (10-Q, repayment basis) — 1.4% < 5% tol → AGREES. Window [balance, +12m) EXCLUSIVE (filing convention). Convertible: $25.0M panel-principal vs $26.7M filing-repayment (+$1.7M accrued PIK). [71]
- **Guide verification — CIQ guide vs release:** revenue: CIQ FY guide 427.516 ≈ prior-FY actual 427.5 (within source-rounding) → VENDOR-ECHO flag (stale carry-forward); release outlook QUALITATIVE-only — render the qualitative growth line [72]

## Record & reproduce
- **Data window:** screened as of 2026-07-06 · assembled 2026-07-10 07:06 UTC
- **Extraction:** unstamped — assembled before extraction versions were declared; vintage unknown
- **Panel age:** oldest panel 16d old — 2026-06-24 (valuation.implied_expectations.tev_as_of), against a 2026-07-10 build
- **Consensus age:** consensus is 56d old (2026-05-15, valuation.implied_expectations.multiples_as_of) — beyond the 45d ceiling. No analyst has revised this name in that window; a re-export will NOT move it. Treat as a neglect signal, not a stale pull.
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001760689` · Nasdaq : MVST
- **Assembly log:** primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+0.3s fetch)
- **Re-run:** `python -m vinci dossier --ticker MVST` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `10-Q 0001628280-26-033590`
[4] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[5] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[6] `EOD MVST 180d to 2026-07-06`
[7] `EOD name−IWM 180d (screen data-record, G2)`
[8] `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ EBITDA $52M [LTM 12 months Mar-31-2026]`
[9] `EDGAR XBRL FCF sign (screen data-record)`
[10] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[11] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
[12] `8-K 0000947871-26-000585 (2026-05-28)`
[13] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[14] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[15] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[16] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[17] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[18] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[19] `8-K 0001628280-26-018235 EX-99.1`
[20] `8-K 0001628280-26-033601 EX-99.1`
[21] `CIQ Customers&Suppliers Microvast Holdings Inc NasdaqCM MVST Customers.rtf`
[22] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[23] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
[24] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[25] `CIQ Financials→Income Statement (quarterly, trailing 8Q)`
[26] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[27] `cadence: EDGAR submissions (median 92d gap over 19 results 8-Ks; last print 2026-05-11)`
[28] `TEV = mcap 423.1 + net debt 199.9 (CIQ Comparable Analysis→Financial Data, Latest, as-of 2026-06-24) — simple-TEV basis`
[29] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[30] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[31] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-24`
[32] `EDGAR XBRL shares, trailing 2024-08-05..2026-05-04`
[33] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[34] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[35] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[36] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
[37] `CIQ Estimates→Recent Changes (47 broker revision events)  [data ≥ 2026-05-15 · export date unverified]`
[38] `CIQ Estimates→Surprise (annual)`
[39] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
[40] `CIQ Net Debt $200M [Q1 Mar-31-2026] ÷ CIQ OCF $46M [LTM 12 months Mar-31-2026]`
[41] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-24`
[42] `CIQ Financials→Capital Structure Details (A 2025 filed Mar-16-2026)`
[43] `CIQ Financials→Capital Structure Summary`
[44] `CIQ Estimates->Trends`
[45] `EDGAR Revenues`
[46] `CIQ transcript and quarterly income statement`
[47] `EDGAR GrossProfit / Revenues`
[48] `EDGAR OperatingIncomeLoss / Revenues`
[49] `CIQ Estimates->Trends (EBIT row)`
[50] `company-adjusted trailing figure, vs the 3.9x headline optic`
[51] `CIQ Financials->Cash Flow (no EDGAR tag exists)`
[52] `CIQ Comparable Analysis (BorgWarner, 13.9% EBITDA margin, levered)`
[53] `CIQ Comparable Analysis (CATL, 23.8% margin, large net cash)`
[54] `CIQ Comparable Analysis (set spans $34M to $275bn; several members not meaningful)`
[55] `CIQ Financials->Multiples`
[56] `CIQ Financials->Multiples (low-confidence range read)`
[57] `analyst judgement`
[58] `house rate of 15% a year compounded over four years`
[59] `CIQ Financials→Income Statement (quarterly, full exported history)`
[60] `CIQ Financials→Balance Sheet (quarterly, Q1-26)`
[61] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[62] `EDGAR 8-K submissions (±10d of instrument maturities)`
[63] `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`
[64] `fenced Tier-2 extraction (verbatim, source-bound)`
[65] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-24`
[66] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-06-24`
[67] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-06-24`
[68] `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q4 2025 Earnings Call, Mar 16, 2026.rtf`
[69] `EDGAR Form 4 (latest 0000947871-26-000620; 18 in 6m)`
[70] `FINRA consolidated short interest (settle 2026-06-15); DTC = 26,323,600 short ÷ 4,571,432 screen 90d ADV`
[71] `10-Q maturity wall vs CIQ capital panel (same window)`
[72] `CIQ revenue guide vs release actual/outlook`