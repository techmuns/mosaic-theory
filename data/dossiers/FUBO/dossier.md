# Dossier — FuboTV Inc. (NYSE: FUBO)

_July 27, 2026 · extraction unstamped_

> ## ⚠ KNOWN-WRONG — do not read the figures on this page as current
>
> Each item is KNOWN-FALSE, not unknown. A gap is a number we do not have; an error is a number we have and can demonstrate is wrong. This page carries errors, and a reader who treats them as staleness will underestimate them.
>
> **1. The share count is PRE-REVERSE-SPLIT.** `stock_info.shares_out` predates the combination, so every per-share figure and the market cap derived from it are wrong by the split factor.
>     *A stale share count drifts by buybacks. This one is wrong by a corporate action that reprices every per-share line on the page.*
>
> **2. G3 never valued this name.** The dossier carries no multiple-floor verdict. FUBO's admission is not a valuation judgment and must not be read as one.
>     *Absence of a verdict reads as a passed verdict unless said out loud — item 22's visible-absence rule.*
>
> **3. The P/E caveat is text this code no longer produces.** `caveats[4]` asserts the multiple rests on normalized/adjusted earnings. The current code refuses to pick a denominator: it names both candidates and states that the displayed basis does not say which.
>     *The sentence makes a claim about the denominator that the inputs do not support. It is wrong, not old.*
>
> **4. The same caveat contains a grammar defect: "EDGAR P/E 13.1x rest on".** Singular subject, plural verb — the verb was hardcoded while the pronoun switched on the number of multiples shown.
>     *Cosmetic in isolation, but it is the visible marker that this page predates the fix — and it sits inside the sentence whose claim is also wrong.*
>
> **5. The document describes the PRE-COMBINATION entity throughout.** Assembled 2026-07-10 and containing no Hulu, no noncontrolling interest, no Newco, no Class B, and no reverse split — none of the structure that now defines the issuer.
>     *This is not an out-of-date page about the same company. It is an accurate page about a company that no longer exists in that form.*
>
> **Clears when:** A post-combination re-assembly exists. Until then this file stands and `dossier.json` stays sealed.
>

# Brief — first cut

## At a glance
> ⚠ **Verify before the verdict:** EDGAR P/E 13.1x rest on normalized/adjusted earnings; Bare peer-comparison (a bear point): 'The forward NTM TEV/EBITDA of 17.77x sits ABOVE the peer median of 8.19x — full caveats in Analysis.

FuboTV Inc. operates as a live TV streaming platform company in the United States and internationally.
**Strongly-bearish** — idiosyncratic -83% relative collapse, across-the-board FY26 estimate cuts crossing zero, and unfunded cash burn with opaque leverage.
- **Segments:** Streaming Business — single segment [1]
- **Geography:** United States — single geography [2]
- **Snapshot:** NYSE · CMP $8.33 (2026-07-24) · cap $256M · 52-wk $7.95–$56.64 · shares 342.4M · book value/sh $27.58 [3]

**The crux — what decides this, and what would change our mind**
**Does the Hulu Live combination convert scaled revenue into durable, self-funding adjusted-EBITDA/FCF (an overshoot), or does structural cash burn, subscriber attrition and content-supplier loss make the profitability inflection unreachable before the cash runs down (a value trap)?**
_8 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-07-13 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-02-03 earnings; 2026-03-26 no company filing; 2026-05-06 earnings [4]
- **Price (180d):** -65.9% [5]
- **Market (IWM) 180d:** 17.0% [6]
- **vs market (180d):** -82.9% [7]
- **Net debt / EBITDA · Net debt / EBITDA [NET]:** _UNKNOWN_ — no CIQ Net Debt/EBITDA; EDGAR no net-debt — debt/cash not in XBRL — pull CIQ
- **Free cash flow:** negative [8]

## Scenario analysis
_no scenario record for this name_

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | unknown | NOT applicable |
| Overall confidence | — |  |

_own-history multiple missing (valuation.own_history.median absent)_

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Management states trailing-12-month pro forma adjusted EBITDA has now exceeded $100M, a milestone framed against a $300M-by-2028 target — a positive-EBITDA mechanism underlying the forward multiples. [9]
- The forward EBITDA ladder de-rates sharply as consensus EBITDA scales (FY26E $92.3M → FY27E $187.1M), implying a rising-EBITDA glide path the trailing NM multiple cannot capture. [10]
- Trailing revenue growth of 22% far exceeds the peer-median 9%, a residual-vs-earned input the human must judge: the TEV/Rev discount (name 0.4 vs peer median 1.9) may be RESIDUAL rather than earned given superior top-line growth. [11]
_Bear case — the decline is real:_
- The company is FCF-negative (LTM levered FCF -$131.2M) and LTM OCF is -$489M, so it cannot self-fund — a cash-burn risk against net debt of $170M with net-debt/EBITDA unavailable. [12]
- Total North America subscribers fell to 5.7M from 5.9M year-over-year by Q2 2026, a declining user base even as reported revenue rose on the Hulu Live combination. [9]
- The FY26 EBITDA guide of $80–100M is 61 days stale and gross-margin sits at only 4% LTM despite absolute revenue rising to $5,304M, so scale is not yet translating into structural profitability. [13]

## Financial snapshot
- **Financial snapshot** — [14]  <!-- ds-table -->

|  | FY22 | FY23 | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 3,419 | 3,846 | 4,220 | 4,413 | 5,304 | 6,226 | 6,533 |
| Revenue growth | — | +12% | +10% | +5% | — (basis) | +41% (vs FY25) | +5% |
| EBITDA ($M) | — | — | — | — | — | 92 | 187 |
| EBITDA margin | — | — | — | — | — | 1% | 3% |
| EBIT ($M) | -180 | -172 | -159 | -156 | -106 | -103 | 0 |
| Net income ($M) | -180 | -172 | -159 | -156 | -85 | -37 | -2 |
| EPS (GAAP, dil.) | — | — | — | — | -2.88 | -1.40 | 0.01 |
| FCF ($M) | — | -31 | -81 | -108 | -131 | — | — |


## Valuation — first cut
- **vs own trading history · Own-history range position:** _UNKNOWN_ — TEV/LTM EBITDA Close has <4 quarters — no range position
- **vs peers:** EV/EBITDA NM vs peer median 10.6; P/E NM vs peer median 23.7 [15]
- **Comparability:** market caps span $478M–$306.6B (642x); the name is $256M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [16]
- **The street, for contrast (target · ratings):** Target price: mean $17.00, median $17.00, high/low 23.00/12.00, N 8/8; Ratings: Buy 5, Outperform 3, Hold 2, Underperform 0, Sell 0, No Opinion 0, Buy 1, Outperform 0, Hold 0, Underperform 0, Sell 0  [data ≥ 2026-06-12 · export date unverified] [17]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [4]
  - 2026-02-03 **-22.0%** → earnings
  - 2026-03-26 **-11.0%** → no company filing
  - 2026-05-06 **-15.9%** → earnings

_Company-specific or market-wide?_
- **Name 180d return:** -65.9% [5]
- **Market (IWM) 180d return:** 17.0% [6]
- **Relative vs market:** -82.9% [7]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-down 2026-02-03 → filed 2026-02-03 [`0001493152-26-004826`](https://www.sec.gov/Archives/edgar/data/1484769/000149315226004826/form8-k.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj EBITDA 2026 $77.9M [18]
- **Other 8-Ks at the gap dates (1):**
  - filed 2026-05-06 · items: 2.02 Results of Operations and Financial Condition [`0001493152-26-021406`](https://www.sec.gov/Archives/edgar/data/1484769/000149315226021406/form8-k.htm)
    - 2.02 Results of Operations and Financial Condition: On May 6, 2026, FuboTV Inc. announced its financial results for the quarter ended March 31, 2026. The full text of the shareholder letter and press release issued in connection with the announcement are attached as Exhibits 99.1 and 99.2, respectively, to this Current Report on Form 8-K. The information in this

## Business quality
- **Segments (revenue share):** Streaming Business — single segment [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** 8 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [19]
- **Geographic:** United States — single geography [2]

## The argument

**Evidence balance:** strongly-bearish — idiosyncratic -83% relative collapse, across-the-board FY26 estimate cuts crossing zero, and unfunded cash burn with opaque leverage.

### Bull case — the decline is overdone
- Management states trailing-12-month pro forma adjusted EBITDA has now exceeded $100M, a milestone framed against a $300M-by-2028 target — a positive-EBITDA mechanism underlying the forward multiples. [9]
- The forward EBITDA ladder de-rates sharply as consensus EBITDA scales (FY26E $92.3M → FY27E $187.1M), implying a rising-EBITDA glide path the trailing NM multiple cannot capture. [10]
- Trailing revenue growth of 22% far exceeds the peer-median 9%, a residual-vs-earned input the human must judge: the TEV/Rev discount (name 0.4 vs peer median 1.9) may be RESIDUAL rather than earned given superior top-line growth. [11]
- Consensus is Buy (1.00) with an $17.00 mean/median target against an $8.33 close, and ratings run 5 Buy / 3 Outperform / 2 Hold with zero sell — a genuinely constructive sell-side posture, though the 6m→latest EBITDA path fell -34%. [20]
- The reported P/E of ~13x rests on a non-current positive EPS and is explicitly flagged distorted — latest annual EPS is negative (-0.54), so the headline 'cheap' multiple is NOT a meaningful signal for either side. [21]

### Bear case — the decline is real
- The company is FCF-negative (LTM levered FCF -$131.2M) and LTM OCF is -$489M, so it cannot self-fund — a cash-burn risk against net debt of $170M with net-debt/EBITDA unavailable. ⚠ uncited [12]
- Total North America subscribers fell to 5.7M from 5.9M year-over-year by Q2 2026, a declining user base even as reported revenue rose on the Hulu Live combination. [9]
- The FY26 EBITDA guide of $80–100M is 61 days stale and gross-margin sits at only 4% LTM despite absolute revenue rising to $5,304M, so scale is not yet translating into structural profitability. [13]
- Return on capital is persistently negative (RoCE Sep-2023 -11.2% → LTM -3.3%) and the share count is diluting +4.0% over ~1 year, compounding a structurally unprofitable base. [22]
- The single anchor client NBCUniversal ceased renewal engagement and NBC content was removed on the Fubo side, a concrete loss of a major programming supplier for a single-segment US streaming business. [23]
- The 180-day return of -65.9% versus IWM +17.0% (relative -82.9%) is deeply idiosyncratic, not a shared-market move, concentrated in discrete earnings gap-downs on 2026-02-03 and 2026-05-06. [7]
- The forward NTM TEV/EBITDA of 17.77x sits ABOVE the peer median of 8.19x — on a forward basis the name is EXPENSIVE, not cheap, so the 'discount to peers' read is a trailing-only artifact that inverts once EBITDA is normalized. [24]
- Consensus FY26 estimates crossed zero across the board 6m→latest — EPS 1.68→-1.40, EBIT +162.0→-103.3, EBITDA -34% — a broad, worsening downgrade cycle, not a single optical timing miss. [25]

### Decisive question
**Does the Hulu Live combination convert scaled revenue into durable, self-funding adjusted-EBITDA/FCF (an overshoot), or does structural cash burn, subscriber attrition and content-supplier loss make the profitability inflection unreachable before the cash runs down (a value trap)?**

### …evidence for
- Management reports trailing-12-month pro forma adjusted EBITDA now exceeds $100M against a stated $300M-by-2028 target, with expected positive free cash flow in FY27 and FY28. [9]
- Consensus FY27E EBITDA of $187.1M roughly doubles FY26E $92.3M, implying a steep near-term profitability ramp the market can underwrite. [10]

### …evidence against
- LTM levered FCF of -$131.2M with LTM OCF -$489M shows the business does not yet self-fund, against only $170M net debt and net-debt/EBITDA unavailable. ⚠ uncited [12]
- Loss of NBCU renewal engagement plus a year-over-year subscriber decline to 5.7M signals content-supplier and user-base erosion at the core. [9]

### Key unknowns
- Net-debt/EBITDA, interest coverage and covenant terms are all UNKNOWN (no CIQ Net Debt/EBITDA, Income Statement missing EBITDA/Interest rows, covenant extraction failed) — leverage-survival is opaque, a bearish gap.
- Cash-runway is not derivable: FCF-negative with cash burn flagged and cash not derived; management asserts >$200M year-end cash but the machine cannot verify runway against burn.
- Segment/geographic EBITDA is UNKNOWN (single Streaming segment, no segment EBITDA section) — no way to isolate profitable vs loss-making product lines.
- The comp set is HETEROGENEOUS (caps $478M–$306.6B, 642x; name $256M) — every peer multiple is a confidence-gated input, not a clean benchmark.
- Comp vintage is incoherent (multiples as-of 2026-06-12 vs TEV as-of 2026-06-24; derived FY26 $17.4M vs direct $92.3M, residual 0.812) — re-pull needed before leaning on any multiple.
- TEV/LTM EBITDA and own-history multiple bands are UNKNOWN (<4 quarterly closes) — no trailing valuation anchor or own-history context.
- Adjusted EBITDA and adjusted leverage figures are not in the revised 99.1 guidance — the company-adjusted profitability basis cannot be reconciled to GAAP.
- A reverse stock split was announced but its execution/effect on the share and multiple picture is not resolved in the data.

### Twin reference cases
- **Chewy** — recovered (LLM-claimed — verify)
  - distinguished by: Loss-making high-growth US subscription/consumer platform that de-rated hard, then reached positive adjusted EBITDA and free cash flow as scale matured.
  - source: [LLM-suggested, unverified]
- **Roku** — recovered
  - distinguished by: US streaming-platform peer that ran negative-to-thin margins through a severe de-rating while top-line growth persisted, later stabilizing on ad monetization.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Paramount Skydance Corporation** — went terminal
  - distinguished by: US media peer carrying heavy leverage and secular Pay-TV pressure whose thin margins and content-cost dependence weighed on the equity despite scale.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Cinedigm** — went terminal (LLM-claimed — verify)
  - distinguished by: Sub-scale US streaming/content name with chronic cash burn and dilution whose growth story never converted to durable free cash flow.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-07-13 `[cadence-estimate]` — the next reported quarter against the committed trajectory [26]
- **Beginning September 2, sports fans will be able to subscribe to Fubo Sports, a standalone plan with 20+ sports and br…** — ~2026-09 `[stated]` — a management-stated dated operating action — the thesis mechanism on a timetable; the following print reads its result [27]
- **Other Notes $0.5M matures** — ~2027-03-31 `[stated]` — refinance / repay / convert before the wall — the survival read [28]
- **Beginning June 20, Fubo Sports Network will stream 16 live games for the duration of Season 9, with t** — ~2027-06 `[stated]` — a management-stated dated operating action — the thesis mechanism on a timetable; the following print reads its result [29]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA NM vs peer median 10.6; P/E NM vs peer median 23.7 [15]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-06-24 · multiples as-of 2026-06-12 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [30]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **17.77x** | **$24.0M EBITDA †** |
| peer-median NTM TEV/EBITDA | 8.19x | $52.1M EBITDA |
| peer-median LTM TEV/EBITDA | 10.6x | $40.3M EBITDA |
| **name NTM TEV/Rev** | **0.36x** | **$1,185.6M Revenue †** |
| peer-median NTM TEV/Rev | 2.07x | $206.2M Revenue |
| peer-median LTM TEV/Rev | 1.9x | $224.6M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $92.3M · FY27E $187.1M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $6226.1M · FY27E $6533.1M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)
  - _⚠ multiple-pricing vintage differs from TEV as-of — re-pull comps (derived FY26 $17.4M vs direct $92.3M, residual 0.812 > 0.10)_

### The EV gap — our base case vs the street

_Not yet computed for this name — the mechanical refresh that writes it has not run here. This is a MISSING REFRESH, not a finding: nothing has been measured and nothing is being withheld._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN

## Peer comps
- **Peer set (roster · caps · business)** — [31]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Roku | $19.9B | operates a TV streaming platform in the United States and internationally. (United States) |
| Netflix | $306.6B | provides entertainment services worldwide. (United States) |
| Sirius XM Holdings Inc. | $9.5B | operates as an audio entertainment company in North America. (United States) |
| Taboola.com Ltd. | $1.3B | operates an artificial intelligence-based algorithmic engine platform in Israel, the United States, the United Kingdom, Germany, and internationally. (United States) |
| Match Group | $8.2B | provides digital technologies in the United States and internationally. (United States) |
| Reddit | $31.9B | operates a digital community in the United States and internationally. (United States) |
| People Incorporated | $3.1B | operates as a media and internet company worldwide. (United States) |
| Bilibili Inc. | $6.6B | provides online entertainment services for the young generations in the People’s Republic of China. (China) |
| Paramount Skydance Corporation | $10.9B | operates as a media and entertainment company worldwide. (United States) |
| Starz Entertainment Corp. | $478M | provides subscription video programming services to consumers in the United States and Canada. (Canada) |

_the name: $256M_

- **Comparability (confidence gate):** market caps span $478M–$306.6B (642x); the name is $256M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [16]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [24]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 0.36 | 0.62 | 2.07 | 2.81 | 8.42 |
| NTM TEV/EBITDA | 17.77 | 5.4 | 8.19 | 11.64 | 24.65 |
| NTM P/E | NM | 7.26 | 19.23 | 21.13 | 51.57 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [32]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Netflix | $306.6B | 20.7 | 6.6 | 23.5 | 31% | 17% | 1.1 | 4,454 |
| Reddit | $31.9B | 44.9 | 11.8 | 47.4 | 26% | 71% | 0.0 | 2,749 (net cash) |
| Roku | $19.9B | 38.9 | 3.6 | 101.3 | 8% | 17% | 1.1 | 1,879 (net cash) |
| Paramount Skydance Corporation | $10.9B | 9.4 | 0.9 | NM | 11% | 1% | 5.4 | 14,654 |
| Sirius XM Holdings Inc. | $9.5B | 8.1 | 2.3 | 11.9 | 29% | 0% | 3.9 | 9,882 |
| Match Group | $8.2B | 10.1 | 3.2 | 13.5 | 31% | 2% | 3.6 | 2,951 |
| Bilibili Inc. | $6.6B | 9.4 | 1.0 | 34.6 | 11% | 9% | 2.9 | 2,155 (net cash) |
| People Incorporated | $3.1B | 16.1 | 1.5 | 23.9 | 7% | -6% | 6.6 | 308 |
| Taboola.com Ltd. | $1.3B | 7.5 | 0.7 | 13.0 | 7% | 10% | 0.9 | 1 |
| Starz Entertainment Corp. | $478M | 11.1 | 0.9 | NM | 8% | – | 7.6 | 696 |
| **FuboTV Inc. · the name** | **$256M** | **NM** | **0.4** | **NM** | **–** | **22%** | **NM** | **170** |
| Peer median (peers) | $8.8B | 10.6 | 1.9 | 23.7 | 11% | 9% | 3.2 | 502 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [13]  <!-- ds-table -->

|  | Oct-2022 | Sep-2023 | Sep-2024 | Sep-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|
| Gross margin | 0% | 0% | 0% | 0% | 4% |

_R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** diluting (trailing ~1.0y): 329,336,621 (2024-07-31) → 342,433,118 (2025-07-31), +4.0% [33]
- **Return ratios — per fiscal period** — [34]  <!-- ds-table -->

|  | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|
| RoE % | — | -17.9% | -17.4% | -17.2% | -5.7% |
| RoCE % | — | -11.2% | -10.9% | -10.7% | -3.3% |
| RoA % | — | -8.3% | -7.7% | -7.5% | -2.5% |
| Total debt/equity | — | — | — | — | 0.15x |
| Current ratio | 0.00x | 0.01x | 0.01x | 0.02x | 0.99x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-06-12)_
- **Horizon read (FQ — next-2Q revision breadth)** — [35]:
  - EPS (GAAP) FQ3 2026: 1m 0↑/0↓, 2m 0↑/5↓, 3m 1↑/3↓
  - EPS (GAAP) FQ4 2026: 1m 0↑/0↓, 2m 0↑/5↓, 3m 0↑/4↓
  - EPS Normalized FQ3 2026: 1m 0↑/0↓, 2m 0↑/3↓, 3m 1↑/1↓
  - EPS Normalized FQ4 2026: 1m 0↑/0↓, 2m 0↑/3↓, 3m 0↑/2↓
  - Revenue FQ3 2026: 1m 0↑/0↓, 2m 2↑/7↓, 3m 2↑/4↓
  - Revenue FQ4 2026: 1m 0↑/1↓, 2m 3↑/5↓, 3m 2↑/4↓
  - EBITDA FQ3 2026: 1m 0↑/0↓, 2m 1↑/6↓, 3m 0↑/3↓
  - EBITDA FQ4 2026: 1m 1↑/0↓, 2m 0↑/7↓, 3m 0↑/3↓
  - EBIT FQ3 2026: 1m 0↑/0↓, 2m 0↑/4↓, 3m 0↑/3↓
  - EBIT FQ4 2026: 1m 0↑/0↓, 2m 0↑/4↓, 3m 0↑/3↓
  - _+7 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS (GAAP): 1.68 (6m) → -0.88 (3m) → -1.21 (2m) → -1.40 (1m) → -1.40 (latest); worsening (crossed zero) (6m→latest) | FY 2026 EPS Normalized: 2.04 (6m) → -0.22 (3m) → -0.35 (2m) → -0.51 (1m) → -0.51 (latest); worsening (crossed zero) (6m→latest) | FY 2026 Revenue: 6,158.7 (6m) → 6,321.6 (3m) → 6,289.6 (2m) → 6,227.9 (1m) → 6,226.1 (latest); net +1% (6m→latest) | FY 2026 EBITDA: 140.7 (6m) → 101.8 (3m) → 89.8 (2m) → 94.2 (1m) → 92.3 (latest); net -34% (6m→latest) | FY 2026 EBIT: 162.0 (6m) → -33.5 (3m) → -98.4 (2m) → -103.3 (1m) → -103.3 (latest); worsening (crossed zero) (6m→latest) | FY 2026 Interest Expense: -13.0 (6m) → -8.95 (3m) → -10.9 (2m) → -10.2 (1m) → -10.2 (latest); improving (magnitude toward zero) (6m→latest) | FY 2026 EBT (GAAP): 150.0 (6m) → -65.1 (3m) → -91.5 (2m) → -101.0 (1m) → -101.1 (latest); worsening (crossed zero) (6m→latest) | FY 2026 Net Income (Excl. Excep): 178.0 (6m) → -10.7 (3m) → -64.0 (2m) → -35.0 (1m) → -49.1 (latest); worsening (crossed zero) (6m→latest) | FY 2026 Net Income (GAAP): 145.0 (6m) → -39.0 (3m) → -36.9 (2m) → -37.3 (1m) → -37.3 (latest); worsening (crossed zero) (6m→latest)  [data ≥ 2026-06-12 · export date unverified] [25]
- **Cross-name anchor (NTM forward-multiple ladder)** — [36]:
  - NTM: TEV/REV 0.36 · TEV/EBITDA 17.77 · TEV/EBIT – · Price/Earnings – · PEG –
  - FY 2026: TEV/REV 0.36 · TEV/EBITDA 24.59 · TEV/EBIT – · Price/Earnings – · PEG –
  - FY 2027: TEV/REV 0.35 · TEV/EBITDA 12.13 · TEV/EBIT – · Price/Earnings – · PEG –
  - FY 2028: TEV/REV 0.33 · TEV/EBITDA 7.01 · TEV/EBIT 15.29 · Price/Earnings 9.14 · PEG –
  - _+2 later fiscal years in JSON_
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [37]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| EBITDA | '80.00 - 100.00' | FY 2026 | 2026-05-06 | 61d (stale) | — | — |

- **Consensus stats (target + ratings):** Target price: mean $17.00, median $17.00, high/low 23.00/12.00, N 8/8; Ratings: Buy 5, Outperform 3, Hold 2, Underperform 0, Sell 0, No Opinion 0, Buy 1, Outperform 0, Hold 0, Underperform 0, Sell 0  [data ≥ 2026-06-12 · export date unverified] [17]
- **Revision-event log (250 events · 18 broker-days)** — [38]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-06-12 | Needham & Company | 4 | 1 | 3 | — | Revenue FY 2026 | 6156.4 | 6137.8 | −18.6 |
| 2026-06-10 | Citizens JMP Securities, LLC | 3 | — | 1 | 2 | Net Income (GAAP) FY 2026 | -28.8 | -28.9 | −0.10 |
| 2026-06-05 | Barrington Research Associates, Inc. | 2 | — | — | 2 | — | — | — | — |
| 2026-05-22 | Needham & Company | 6 | 5 | 1 | — | Gross Margin % FQ3 2026 | 7.0 | 8.0 | +1.0 |
| 2026-05-22 | broker undisclosed | 20 | 10 | 4 | 6 | EBITDA FQ3 2026 | 4.5 | 5.2 | +0.70 |
| 2026-05-07 | Barrington Research Associates, Inc. | 18 | 8 | 10 | — | EBITDA FQ3 2026 | 26.6 | 13.4 | −13.2 |

_+12 more broker-days in JSON_

- **Surprise history (annual beat/miss):** _UNKNOWN_ — Surprise sheet has no fiscal-year header row

## Leverage & survival
- **Total debt / EBITDA vs peers:** name NM vs peer median 3.2x (comps TOTAL-debt/EBITDA basis) [39]
- **Net debt / OCF:** _UNKNOWN_ — CIQ OCF $-489M <= 0 — ratio meaningless
- **Interest coverage:** _UNKNOWN_ — Income Statement missing EBITDA or Interest Expense row
- **Self-funding:** self-funding: MIXED — latest-Q OCF < 0, LTM FCF < 0 (both must be positive to self-fund) [40]
- **Credit health:** _UNKNOWN_ — comps workbook Company Comparable Analysis FuboTV Inc .xls has no 'Credit Health Panel' sheet

- **FCF sign:** negative [8]
- **Free cash flow ($M):** -131.2 [12]
- **Live instruments — near-dated (≤12m + 2027) — panel Q2 2026 filed May-06-2026** — [41]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Other Notes | Bonds and Notes | $0.5M | 2.250% | NA | 2027-03-31 | N | N | USD |

_3 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-07-06 reference:
  - due 2027: $0.5M
  - due 2029: $177.5M
  - due 2031: $145.0M
  - undated (floor — no panel maturity): $33.1M — Operating Lease Liabilities $33.1M
  - _reconciliation: itemized $356.1M (panel Q2 2026 filed May-06-2026) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** senior bonds 323.0; leases 33.1; total principal 356.1; total debt 408.2 (latest quarter) ($M) [42]

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [43]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [44]
  - net debt / EBITDA (CIQ, GAAP basis): UNKNOWN
  - total debt / EBITDA (CIQ comps, GAAP basis): UNKNOWN
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: UNKNOWN (not disclosed)

## ⚠ Analyst caveats — verify before the verdict

_5 to verify._

- P/E may be distorted by non-recurring EPS — latest annual EPS -0.54 vs recent median -2.06; verify against normalized/forward EPS (CIQ)
- EDGAR P/E 13.1x rest on normalized/adjusted earnings — LTM GAAP diluted EPS is NEGATIVE (-2.88); do not read it as a GAAP trailing multiple.
- Possible false balance — the written assessment commits a strong lean but the body is near-symmetric (5 bull vs 8 bear) and the minority bull points aren't qualified-as-outweighed — size the minority against the lean, or it launders a one-sided case
- **Bare peer-comparison** — The forward NTM TEV/EBITDA of 17.77x sits ABOVE the peer median of 8.19x — on a forward basis the name is EXPENSIVE, not cheap, so the 'discount to peers' read is a trailing-only artifact that inverts once EBITDA is normalized.
  - _where:_ a bear point
  - _why it matters:_ presents cheap/rich vs peers as a verdict without the earned-vs-residual decomposition or the peer-set composition
  - _how to verify:_ POSE justified-vs-residual, never the bare gap
- **Heterogeneous-peer benchmark** — The forward NTM TEV/EBITDA of 17.77x sits ABOVE the peer median of 8.19x — on a forward basis the name is EXPENSIVE, not cheap, so the 'discount to peers' read is a trailing-only artifact that inverts once EBITDA is normalized.
  - _where:_ a bear point
  - _why it matters:_ leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS
  - _how to verify:_ confidence-gate every peer stat

# Appendix — data & audit

## How to read this dossier
- The machine assembles and cites; **the analyst decides**. Nothing here is a recommendation — the verdict of record is the human's, logged to an append-only ledger with a frozen entry price.
- The machine's proposed verdict is derived deterministically from its written assessment and stays **sealed until the analyst's verdict is recorded**, so it cannot anchor the decision. A two-sided assessment proposes nothing.
- Citations [n] resolve in the Sources list at the document end. **Cited is not verified** — the reference locates the claim so you can check it.
- Reference values (peer-implied equity, price-implied levels) are shown **beside** the figures they contextualize, never differenced into an upside — the reader judges the gap.
- A value shown as UNKNOWN is honestly absent at the source — nothing is imputed.


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-06-12)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [14]  <!-- ds-table -->

|  | FY22 | FY23 | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|
| Revenue ($M) | 3,419 | 3,846 | 4,220 | 4,413 | 5,304 | 6,226 | 6,533 |
| Revenue growth | — | +12% | +10% | +5% | — (basis) | +41% (vs FY25) | +5% |
| EBITDA ($M) | — | — | — | — | — | 92 | 187 |
| EBITDA margin | — | — | — | — | — | 1% | 3% |
| EBIT ($M) | -180 | -172 | -159 | -156 | -106 | -103 | 0 |
| Net income ($M) | -180 | -172 | -159 | -156 | -85 | -37 | -2 |
| EPS (GAAP, dil.) | — | — | — | — | -2.88 | -1.40 | 0.01 |
| EPS (Normalized) | — | — | — | — | -1.57 | -0.51 | 0.47 |
| CFO ($M) | -167 | -96 | -140 | -166 | -489 | — | — |
| Capex ($M) | — | — | — | — | -1 | — | — |
| FCF (levered, CIQ) | — | -31 | -81 | -108 | -131 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-06-12; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Quarterly — every exported quarter
- **Quarterly financials** — [45]  <!-- ds-table -->

|  | FY23 | FY24 | FY24 | FY24 | FY24 | FY25 (R) | FY25 | FY25 | FY25 | FY26 |
|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 1,051 | 1,076 | 1,058 | 1,058 | 1,106 | 1,125 | 1,091 | 1,091 | 1,549 | 1,574 |
| Gross margin | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 7% | 8% |
| EBITDA ($M) | — | — | — | — | — | — | — | — | -4 | 34 |
| EBITDA margin | — | — | — | — | — | — | — | — | -0% | 2% |
| Revenue QoQ | — | +2% | -2% | +0% | +4% | — (basis) | — (basis) | +0% | +42% | +2% |
| Revenue YoY | — | — | — | — | — | — | — | — | — | — |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of FY26 ($M): cash & ST inv 238; total debt 408; net debt 170; equity 812; net working capital -6; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [46]
- **Coherence — BS vs implied-valuation bridge:** cash BS $238M / bridge $238M; debt BS $408M / bridge $408M — reconcile with the implied-valuation bridge. [47]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel Q2 2026 filed May-06-2026** — [41]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 2029 Convertible Notes | Bonds and Notes | $177.5M | 7.500% | NA | 2029-02-15 | Y | Y | USD |
| Disney Note | Bonds and Notes | $145.0M | 4.200% | NA | 2031-01-05 | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $33.1M | 6.800% | NA | undated | Y | N | USD |
| Other Notes | Bonds and Notes | $0.5M | 2.250% | NA | 2027-03-31 | N | N | USD |

- **8-Ks at instrument maturities:** _UNKNOWN_ — no trailing-12m instrument maturity to anchor an 8-K
- **Covenant exhibit pointers:** _UNKNOWN_ — no CIK-scoped agreement exhibit located across the filing history
- **Covenant terms (from the filed agreement):** COVENANT DIGEST — extraction failed: no covenant terms extracted from located exhibits (terms UNKNOWN, not pending). [48]

### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 256.4 [49]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $237.80M, − total debt $408.20M [50]
- **Implied equity at peer-median ($M, CIQ)** — [51]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| NTM Revenue (Capital IQ) | 11,250.9 |
| NTM EBITDA (Capital IQ) | -966.8 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [52]

### Ownership & positioning
- **Insider activity (Form 4, 6m):** Open-market buys 0 · sells 2 (net -311.4K sh) · grants 0 · last 2026-07-13 · other filings 2 [53]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-30): 6.9M → 7.0M sh (+1.2%, rising) · 2.0% of shares out (EDGAR XBRL) · DTC 4.7d · recent: 2026-06-30 7.0M · 2026-06-15 6.9M · 2026-05-29 7.0M · 2026-05-15 7.3M [54]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [55]
- **Guide verification — CIQ guide vs release:** revenue: CIQ guide UNKNOWN — not cross-checked [56]

## Record & reproduce
- **Data window:** screened as of 2026-07-06 · assembled 2026-07-27 10:05 UTC
- **Extraction:** unstamped — assembled before extraction versions were declared; vintage unknown
- **Price store:** unstamped — this dossier predates the store stamp
- **Panel age:** oldest panel 33d old — 2026-06-24 (valuation.implied_expectations.tev_as_of), against a 2026-07-27 build
- **Consensus age:** consensus 45d old (2026-06-12, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001484769` · NYSE : FUBO
- **Assembly log:** primary-source: 8-K 0001493152-26-011823 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 8-K 0001493152-26-003429 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 3 EX-99.1 release(s) + 1 10-Q parsed (+2.4s fetch)
- **Re-run:** `python -m vinci dossier --ticker FUBO` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Sep-27-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Sep-27-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[5] `EOD FUBO 180d to 2026-07-06`
[6] `EOD IWM 180d to 2026-07-06 (cap-band: $0.3B @ 2026-07-06 → small (<$4B) → IWM)`
[7] `EOD FUBO−IWM 180d to 2026-07-06 (assembly, cap-band)`
[8] `EDGAR XBRL FCF sign (screen data-record)`
[9] `CIQ transcript: FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf`
[10] `CIQ Estimates→Trends (FY26/FY27 consensus EBITDA, latest snapshot)`
[11] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[12] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
[13] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[14] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[15] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[16] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[17] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[18] `8-K 0001493152-26-004826 EX-99.1`
[19] `CIQ Customers&Suppliers FuboTV Inc NYSE FUBO Customers.rtf`
[20] `CIQ Estimates→Consensus`
[21] `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
[22] `CIQ Financials→Ratios (Return on Capital %, multi-year columns)`
[23] `CIQ transcript: FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf`
[24] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[25] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[26] `cadence: EDGAR submissions (median 68d gap over 33 results 8-Ks; last print 2026-05-06)`
[27] `CIQ Key Developments: FuboTV Inc NYSE FUBO Key Developments.rtf · Aug-28-2025`
[28] `CIQ capital-structure panel (maturity_date)`
[29] `CIQ Key Developments: FuboTV Inc NYSE FUBO Key Developments.rtf · Jun-18-2026`
[30] `TEV = mcap 256.4 + net debt 170.4 (CIQ Comparable Analysis→Financial Data, Latest, as-of 2026-06-24) — simple-TEV basis`
[31] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[32] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-24`
[33] `EDGAR XBRL shares, trailing 2024-07-31..2025-07-31`
[34] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[35] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[36] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[37] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
[38] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-06-12 · export date unverified]`
[39] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-24`
[40] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[41] `CIQ Financials→Capital Structure Details (Q2 2026 filed May-06-2026)`
[42] `CIQ Financials→Capital Structure Summary`
[43] `10-Q 0001628280-26-031265`
[44] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[45] `CIQ Financials→Income Statement (quarterly, full exported history)`
[46] `CIQ Financials→Balance Sheet (quarterly, FY26)`
[47] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[48] `fenced Tier-2 digest (P1)`
[49] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-24`
[50] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-06-24`
[51] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-06-24`
[52] `CIQ transcript(s): FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf; FuboTV Inc., Q2 2026 Earnings Call, May 06, 2026.rtf`
[53] `EDGAR Form 4 (latest 0001493152-26-033082; 3 in 6m)`
[54] `FINRA consolidated short interest (settle 2026-06-30); DTC = 7,001,210 short ÷ 1,482,863 screen 90d ADV`
[55] `10-Q maturity wall vs CIQ capital panel (same window)`
[56] `CIQ revenue guide vs release actual/outlook`