# Dossier — BELLRING BRANDS, INC. (NYSE: BRBR)

_August 13, 2026 · extraction 2026-07-28.1_

# Brief — first cut

## At a glance
**Target (base)** $12.31 (+6.5% vs entry-vintage spot) · **Spot** $11.56 (entry-vintage — frozen at underwrite 2026-08-07) · **Reward** $0.75 · **Risk** $10.97 · **Reward : risk** 0.07 : 1 (bar 2 : 1) · **Base IRR** 4.3% (floor 15%, 1.5y) · **Gate** FAIL (both tests)

_Spot source: EOD BRBR close 2026-08-07. NOTE: only the -sl worktree's store carries a bar that far; this worktree's frontier is 2026-08-04. All three stores agree at 2026-07-29 ($13.29), so the difference is refresh depth, not value._

**Underwrite disposition:** WATCH (2026-08-11) — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

### Thesis — our rationale
_Prices quoted below are entry-vintage (2026-08-07); the live close is in Snapshot, above._

Analysed and not buying at any price near today's. The operating case is alive — promotion normalised at 17% of category volume, cash generation positive, no near-term maturity — but a possible recovery is not a mispricing: at $11.56 the market already gives near-full credit to a $12.31 base case while the equity carries close to total downside if that recovery fails. Only 0.35 turns of the multiple separate the bear case from no equity at all, and the 4.29x low in its trading history predates the current capital structure. No standing limit: a fall to about $4.49 would more likely reflect an event that also lowered the base.

### What would reopen this name

- Price entering roughly $4 to $5 WITHOUT corresponding deterioration in the business.
- Inventory normalising from $480.6M without material write-offs.
- Cash conversion sustained over consecutive quarters.
- Material reduction in net debt.
- Margin recovery that survives the fiscal 2027 price increase.

> ⚠ **Verify before the verdict:** Net debt/EBITDA (4.3x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis — full caveats in Analysis.

BellRing Brands, Inc., together with its subsidiaries, provides various nutrition products in the United States.
- **Segments:** Protein-Based Consumer Goods — single segment [1]
- **Geography:** United States 88%; Other Foreign 8%; Canada 4% [2]
- **Snapshot:** NYSE · CMP $10.85 (2026-08-12) · cap $1.3B (2026-08-09) ⚠ implies $11.56/sh vs CMP (+6.5%) · 52-wk $7.82–$43.02 · shares 116.3M · book value/sh $-4.02 [3]

**The crux — what decides this, and what would change our mind**
**Is the margin collapse a transitory input-cost/promotional overshoot that the announced FY27 double-digit price increase and cost actions will reverse, or a structural re-set of a single-category franchise now facing permanent competitive-promotion intensity?**
_7 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-11-03 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-05-05 earnings [4]
- **Price (180d):** -39.3% [5]
- **Market (IWM) 180d:** 15.1% [6]
- **vs market (180d):** -54.4% [7]
- **Net debt / EBITDA:** 4.3x [8]
- **Free cash flow:** positive [9]

## Scenario analysis
_Mid-cycle underwrite: normalized operating margin on a mid-cycle revenue base, valued at an exit EV/LTM-EBITDA multiple; reward/risk measured at SPOT._

| scenario | revenue $M | margin | multiple | value / sh | vs entry-vintage spot |
| --- | ---: | ---: | ---: | ---: | ---: |
| bear | 2,250 | 8.0% | 6x | $0.59 | -94.9% |
| base | 2,385 | 11.8% | 8.5x | $12.31 | +6.5% |
| bull | 2,500 | 15.5% | 12x | $32.20 | +178.5% |

- **bear** — Promotional intensity persists and the price increase does not hold, so revenue falls back and margin compresses to 8.0%. The multiple sits at 6.0x. The equity is thin enough here that the residual is close to nothing.
- **base** — Promotion normalises — the third quarter ran at 17% of category volume, down sequentially — cash generation stays positive and there is no near-term maturity. Margin recovers to 11.83% and the multiple to 8.5x.
- **bull** — The price increase holds through the elasticity, distribution gains carry, and margin reaches 15.5% against a 12.0x multiple.

**Scenario inputs** — every value in the grid recomputes from these.

| input | value | basis | source |
| --- | ---: | --- | --- |
| net debt | 1,122.7 $M | net debt, latest 10-Q | CIQ Financials/EDGAR — carried from the completed stage-2 underwrite |
| d and a | 18.6 $M | FROZEN — no clean FY27 figure exists, so the latest reported annual charge is carried forward unchanged rather than forecast | carried from the completed stage-2 underwrite |
| diluted shares | 116.478194 M shares | Diluted shares outstanding 116,478,194 = basic shares outstanding 116,278,194 (cover of the 10-Q filed 2026-08-04, as of 2026-07-28) + a dilutive increment of 200,000 (diluted weighted average 116,600,000 less basic weighted average 116,400,000, 2026-04-01 to 2026-06-30). BOTH LEGS COME FROM THE SAME FILING, which is what makes the construction sound. The underwrite's 116,600,000 is NOT used: it is the latest-quarter diluted weighted average, a period average over a quarter in which the count was falling, and a period average is the mislabel the denominator convention exists to remove. Excluded from the filer's diluted average: antidilutive instruments (a loss period reports no dilution at all under ASC 260); out-of-the-money options, which contribute nothing under the treasury-stock method; and any change in the dilutive count between the reporting period end and the valuation date. | EDGAR dei:EntityCommonStockSharesOutstanding + us-gaap:WeightedAverageNumberOf{SharesOutstandingBasic,DilutedSharesOutstanding} — item 24 denominator swap |
| ltm revenue | 1,392.235 $M | LTM revenue | committed financial_summary.annual (LTM) — via committed dossier anchor block (#158/#160/#162-verified) |

_Chain (EV/EBITDA):_ EBIT = revenue × op margin → EBITDA = EBIT + D&A → EV = EBITDA × exit multiple (EV/EBITDA) → equity = EV − net debt → value/share = equity ÷ diluted shares

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | mid-cycle margin × the median multiple of its own history | applicable |
| Mid-cycle margin | 16.0% | 8y history · firm |
| Median multiple, own history | 19.8x | 27 closes · firm · EV/EBITDA |
| Screen value / share | $57.61 | spot-independent · EV/EBIT 20.7x |
| Overall confidence | firm |  |

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Q3 net sales rose 4% with both brands ahead of expectations, and Q3 adjusted EBITDA of $78.3M was well above the depressed Q2 $53.8M print — the top-line demand engine has not broken. [10]
- Management announced a double-digit price increase on Premier shakes plus additional powder pricing effective Q1 FY27, with expected elasticity slightly greater than 1 — a concrete margin-recovery lever aimed at the input-cost problem that crushed the margin. [10]
- The RTD shake category is up 8% and among the fastest-growing in CPG, with Premier household penetration at almost 23% and the highest shake repeat rate in the category — a share-defensible franchise, not a structurally declining one. [10]
_Bear case — the decline is real:_
- Leverage is elevated at net-debt/EBITDA 4.3x (total-debt/EBITDA 4.4x vs peer-median 2.4x) with interest coverage only 3.3x, so a further EBITDA leg down would strain the capital structure. [8]
- The guidance arc itself is a repeated cut: FY26 net-sales growth guided 4-8% (Nov-2025) → 4-6% (Feb-2026) → 0-2% (May-2026) → 1-3% (Aug-2026), showing management repeatedly overestimated the year. [11]
- Competitive intensity is structural, not one-off: 70% of RTD category volumes were sold on price promotion in Q3 (up from 27% in Q2) and buy-rate per household saw its first decline in 5 years, forcing rising promotional cost to defend share. [10]

## Financial snapshot
- **Financial snapshot** — [12]  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 1,372 | 1,667 | 1,996 | 2,317 | 2,355 | 2,356 | 2,385 |
| Revenue growth | — (basis) | +22% | — (basis) | +16% | — (basis) | +2% (vs FY25) | +1% |
| EBITDA ($M) | 234 | 316 | 424 | 376 | 263 | 288 | 323 |
| EBITDA margin | 17% | 19% | 21% | 16% | 11% | 12% | 14% |
| EBIT ($M) | 212 | 294 | 405 | 357 | 243 | 246 | 282 |
| Net income ($M) | 82 | 166 | 246 | 216 | 171 | 138 | 153 |
| EPS (GAAP, dil.) | 0.88 | 1.23 | 1.86 | 1.68 | 1.43 | 1.18 | 1.34 |
| FCF ($M) | -5 | 192 | 162 | 224 | 158 | — | — |

_table shows the last 4 fiscal years · 6 earlier years are in the Appendix_

**Capital allocation — created or destroyed**

- **Impairment headroom — goodwill + intangibles remaining:** $178.1M [13]
- **Goodwill:** $65.9M [13]
- **Intangibles (net):** $112.2M [14]
- **Impairment:** _NONE IN THE CURRENT PERIOD_ — the filer records no impairment under any tag tried
- **Buyback — cash:** $137.2M [15]
- **Buyback — shares repurchased:** 4,860,000 [16]
- **Buyback — average cost/share:** $29.18 — **fiscal-period average over 2025-10-01→2026-03-31, 181d; NOT a purchase price** and not evidence of when they bought [17]
  - ⚠ **PERIOD MISMATCH** — this average covers 2025-10-01→2026-03-31, 181d while the repurchase cash beside it covers 2025-10-01→2026-06-30, 272d; they are not two views of one window and must not be divided into each other
- **Acquisition consideration:** _UNKNOWN_ — no acquisition consideration under any of BusinessCombinationConsiderationTransferred1, BusinessCombinationConsiderationTransferred, PaymentsToAcquireBusinessesNetOfCashAcquired — EDGAR XBRL companyfacts
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [18]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap |
|---|---:|---:|---:|---:|---:|
| **BRBR** | **1,344** | **178** | **1,052** | **17%** | **13%** |
| KVUE | 36,936 | 17,671 | 26,735 | 66% | 48% |
| HSY | 36,639 | 5,411 | 13,973 | 39% | 15% |
| SJM | 12,843 | 10,889 | 16,219 | 67% | 85% |
| CAG | 7,231 | 9,950 | 17,274 | 58% | 138% |
| HLF | 1,294 | 459 | 2,858 | 16% | 35% |
| SMPL | 982 | 1,509 | 2,062 | 73% | 154% |
| NATR | 288 | 0 | 260 | 0% | 0% |
| USNA | 286 | 267 | 739 | 36% | 93% |
| NUS | 266 | 43 | 1,122 | 4% | 16% |
| FTLF | 94 | 71 | 104 | 68% | 75% |

- **Median — all peers (n=10):** 48% of assets · 61% of market cap
- **Median — peers ≥ $1,000M market cap (n=5):** 58% of assets · 48% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [19]  <!-- ds-table -->

|  | state | yrs charged | window $M | % acquired | last charge (any date) | live YTD $M |
|---|---|---|---|---:|---:|---|
| **BRBR** | **does not tag** | **—** | **—** | **—** | **never** | **—** |
| KVUE | wrote down | 1 of 5 | 479 | 3% | 2024-12-29 ($479M) | — |
| HSY | wrote down | 1 of 5 | 6 | 0% | 2025-12-31 ($6M) | — |
| SJM | wrote down | 2 of 5 | 2,169 | 20% | 2026-04-30 ($508M) | — |
| CAG | wrote down | 4 of 4 | 4,689 | 47% | 2026-05-31 ($2,382M) | — |
| HLF | reports nil | 0 of 1 | — | — | never | — |
| SMPL | wrote down | 1 of 5 | 61 | 4% | 2025-08-30 ($61M) | 369 |
| NATR | does not tag | — | — | — | never | — |
| USNA | wrote down | 1 of 5 | 7 | 2% | 2026-01-03 ($7M) | — |
| NUS | reports nil | 0 of 1 | — | — | never | 79 |
| FTLF | reports nil | 0 of 2 | — | — | 2017-12-31 ($6M) | — |

- **Base rate — 4 of 5 large peers ASSESSED over the window took a charge**, median 11% of acquired assets among those that did. The denominator counts only peers with an annual observation in the window — a name with none was not measured, and is not a clean year.
- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. `no annual obs.` and `does not tag` are not measurements and must not be read as clean years. The **live YTD** column is excluded from the window total: a year-to-date charge is not an annual one, and the two are different quantities._

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 9.2x as-of 2026-08-07 — trailing range 4.3–27.9x (median 19.8x) over 27 closes → 11%ile → near-floor; P/LTM EPS 8.1x [20]
- **vs peers:** EV/EBITDA 9.2x vs peer median 6.6x (+39%); P/E 8.1x vs peer median 16.6x (-51%) [21]
- **Comparability:** market caps span $94M–$36.9B (392x); the name is $1.3B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [22]
- **The street, for contrast (target · ratings):** Target price: mean $14.71, median $14.50, high/low 20.00/10.00, N 12/12; Ratings: Buy 6, Outperform 2, Hold 5, Underperform 1, Sell 0, No Opinion 1, Buy 0, Outperform 0, Hold 1, Underperform 0, Sell 0  [data ≥ 2026-08-06 · export date unverified] [23]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [4]
  - 2026-05-05 **-38.8%** → earnings

_Company-specific or market-wide?_
- **Name 180d return:** -39.3% [5]
- **Market (IWM) 180d return:** 15.1% [6]
- **Relative vs market:** -54.4% [7]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-down 2026-05-05 → filed 2026-05-05 [`0001628280-26-030115`](https://www.sec.gov/Archives/edgar/data/1772016/000162828026030115/brbr-20260505.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj EBITDA Q2 2026 $53.8M; $11.3M inventory-related charge; 2026 net sales outlook: $2,325.0–$2,365.0M [24]

## Business quality
- **Segments (revenue share):** Protein-Based Consumer Goods — single segment [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — single-segment reporting (Protein-Based Consumer Goods) — no segment EBITDA to break out; the consolidated EBITDA is the whole business
- **Customers:** 5 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [25]
- **Geographic:** United States 88%; Other Foreign 8%; Canada 4% [2]

## The argument

**Evidence balance:** strongly-bearish — absolute EBITDA down ~40% on structural promotional intensity and still-falling consensus, with margin recovery unproven and unquantified.

### Bull case — the decline is overdone
- Q3 net sales rose 4% with both brands ahead of expectations, and Q3 adjusted EBITDA of $78.3M was well above the depressed Q2 $53.8M print — the top-line demand engine has not broken. [10]
- Management announced a double-digit price increase on Premier shakes plus additional powder pricing effective Q1 FY27, with expected elasticity slightly greater than 1 — a concrete margin-recovery lever aimed at the input-cost problem that crushed the margin. [10]
- The RTD shake category is up 8% and among the fastest-growing in CPG, with Premier household penetration at almost 23% and the highest shake repeat rate in the category — a share-defensible franchise, not a structurally declining one. [10]
- The absolute-EBITDA reconciler shows the margin collapse is partly optical: EBITDA % fell to 11% LTM, but the drop reflects transitory input-cost inflation, freight and one-off inventory charges rather than lost revenue, which still grew to $2,355M LTM. [26]
- The company is FCF-positive on an LTM basis ($158M) and actively buying back stock (share count -9.7% over ~1.7y), consistent with a self-funding rather than distressed posture. [27]
- On the peer grid BRBR trades at P/E 8.1x vs peer median 16.5x, but comparability is flagged HETEROGENEOUS (caps span $94M-$36.9B, 392x) so whether that discount is earned or residual overshoot is the human's judgment, not a clean benchmark read. [28]
- The forward multiple ladder shows EBITDA recovering (FY26E $288M → FY27E $323M), so the NTM TEV/EBITDA of 7.99x sits below the peer-median NTM 8.3x on a recovering base rather than a permanently impaired one. [29]

### Bear case — the decline is real
- Leverage is elevated at net-debt/EBITDA 4.3x (total-debt/EBITDA 4.4x vs peer-median 2.4x) with interest coverage only 3.3x, so a further EBITDA leg down would strain the capital structure. [8]
- The guidance arc itself is a repeated cut: FY26 net-sales growth guided 4-8% (Nov-2025) → 4-6% (Feb-2026) → 0-2% (May-2026) → 1-3% (Aug-2026), showing management repeatedly overestimated the year. [11]
- Competitive intensity is structural, not one-off: 70% of RTD category volumes were sold on price promotion in Q3 (up from 27% in Q2) and buy-rate per household saw its first decline in 5 years, forcing rising promotional cost to defend share. [10]
- EBITDA collapsed from $424M (FY24) to $376M (FY25) to $263M LTM and EBITDA growth is -42% vs peer-median -3%, so the margin % fall is the REAL signal, not an optical artifact — absolute EBITDA fell alongside the percentage. [30]
- Book equity is negative (-$4.02/share) and a new CEO is only seven days in with FY27 guidance not yet issued, so the turnaround plan is unproven and unquantified. [31]
- The gross-margin destruction is mechanism-driven and severe: Q2 adjusted gross margin was 22.7% vs 34.5% a year prior, driven by input-cost inflation, tariffs, unfavorable price/mix and freight — and management says protein-commodity inflation runs above initial assumptions into the back half. [32]
- Consensus is cutting hard: FY26 EBITDA has been revised from $512M (12m ago) to $288M latest (-44%) and normalized EPS -56%, with 4 downward / 0 upward GAAP-EPS revisions last month — the estimate trend is still falling, not stabilizing. [33]
- The stock is an idiosyncratic loss, down 39% over 180d while IWM rose 15% (-54% relative), with a discrete earnings gap-down on 2026-05-05 — the market is repricing the name specifically, not a sector. [7]

### Decisive question
**Is the margin collapse a transitory input-cost/promotional overshoot that the announced FY27 double-digit price increase and cost actions will reverse, or a structural re-set of a single-category franchise now facing permanent competitive-promotion intensity?**

### …evidence for
- Management announced a double-digit Premier shake price increase plus powder pricing effective Q1 FY27 with expected elasticity slightly greater than 1, explicitly to offset inflation and rebuild margin over time. [10]
- Q3 net sales grew 4% with both brands ahead and category demand remains strong (RTD shakes up 8%, Premier penetration ~23%), suggesting the demand engine is intact and the problem is cost/mix rather than volume. [10]

### …evidence against
- Promotional intensity jumped to 70% of category volumes on promotion in Q3 with the first household buy-rate decline in 5 years, and management flags rising cost to defend leadership — a structural competitive shift, not a one-quarter blip. [32]
- Consensus FY26 EBITDA has been cut -44% (from $512M to $288M) and is still being revised down (4 down / 0 up GAAP-EPS last month), indicating analysts do not yet see the deterioration bottoming. [33]

### Key unknowns
- FY27 guidance is not yet issued (new CEO seven days in), so the quantified margin-recovery path from the announced price increase is unknown.
- No company-adjusted LTM EBITDA is disclosed in the revised guidance, so net-debt/adjusted-EBITDA and covenant headroom cannot be computed (adjusted figures UNKNOWN).
- Whether the announced double-digit price increase holds without triggering elasticity worse than the assumed ~1 — the elasticity outcome is a management assumption, not a resolved fact.
- The financial-summary EBITDA-basis check flags GAAP-actual vs possibly-ADJUSTED-estimate mismatch (1.73x implied D&A ratio, unresolved) — cross-basis EBITDA comparisons are not verified.
- The peer set is flagged HETEROGENEOUS (caps span 392x), so whether the P/E and EV/EBITDA discounts to peer median are earned or residual is unresolved and not computable here.
- BRBR does not tag impairment concepts in XBRL ('does not tag', not zero), so goodwill/intangible impairment risk on the single Protein segment is opaque.
- Covenant terms on the revolver and 2030 senior notes are only partially digested; actual leverage/coverage covenant thresholds are not stated.

### Twin reference cases
- **The Simply Good Foods Company** — went terminal
  - distinguished by: Direct nutrition/meal-replacement peer facing the same promotional-intensity and category-competition pressures, with a pending impairment flagged — the closest read-across for whether the category dynamic is transitory or structural.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Conagra Brands** — went terminal
  - distinguished by: Levered branded-food peer that took repeated goodwill/intangible write-downs across four years as input-cost and demand pressures ground down earnings — the value-trap template where cheap stayed cheap.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Herbalife Ltd.** — went terminal
  - distinguished by: Similarly-sized wellness-products name trading at a low multiple with heavy leverage and stagnant EBITDA growth — a comparable on whether a small-cap protein/wellness brand re-rates or stays depressed.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Medifast** — went terminal (LLM-claimed — verify)
  - distinguished by: Weight-management/nutrition brand whose single-category demand engine reversed sharply when competitive and consumer dynamics shifted, showing how fast a fast-growing wellness franchise can de-rate.
  - source: [LLM-suggested, unverified]
- **e.l.f. Beauty** — recovered (LLM-claimed — verify)
  - distinguished by: Fast-growing single-category consumer brand that absorbed a sharp margin/estimate scare and re-rated once pricing and distribution actions restored the growth-plus-margin narrative.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-11-03 `[cadence-estimate]` — the committed revised outlook (see Revised guidance — the print is the checkpoint that confirms or refutes it) [34]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 9.2x vs peer median 6.6x (+39%); P/E 8.1x vs peer median 16.6x (-51%) [21]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-08-07 · multiples as-of 2026-08-06 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [35]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **7.99x** | **$308.7M EBITDA †** |
| peer-median NTM TEV/EBITDA | 8.3x | $297.2M EBITDA |
| peer-median LTM TEV/EBITDA | 6.6x | $373.8M EBITDA |
| **name NTM TEV/Rev** | **1.04x** | **$2,372.0M Revenue †** |
| peer-median NTM TEV/Rev | 1.13x | $2,183.1M Revenue |
| peer-median LTM TEV/Rev | 1.1x | $2,242.6M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $288.1M · FY27E $322.7M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $2356.2M · FY27E $2385.5M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

### The EV gap — our base case vs the street

_Anchor FY2026 · consensus as-of ≥2026-08-06 (a FLOOR — the export states no as-of, so the true date is on or after this) · TEV as-of 2026-08-07 · form three-ratio_

- **The gap, decomposed (ours / consensus, at the anchor year)**  <!-- ds-table -->

|  | ratio | consensus dispersion |
|---|---|---:|
| revenue | 1.01x | sigma 8.83 on n=13 |
| EBITDA margin | 1.03x | sigma 2.43 on n=13 |
| exit multiple | 0.99x | street 8.57x at FY2026 |
| **product = the EV gap** | **1.04x** |  |

_the three ratios multiply to the gap by IDENTITY — this is a decomposition, never an attribution of cause_

- **Shape:** **earnings** at FY2026, but FY2027 gives **multiple** — the shape MOVES between years, so neither is the answer on its own.

  _The record does not state which fiscal year its base leg is struck at, so this label is reported on FY2026's basis and is unverified against the leg. The total gap above carries no year and is unaffected._

- **Bridge:** our EV $2,557M − net debt $1,123M = equity $1,434M ÷ 116.478M sh = **$12.31/sh** — against TEV $2,467M.

  - _Revenue dispersion 1.4% (high−low ÷ |median|, FY2026, as-of ≥2026-08-06)_
  - _EBITDA dispersion 3.7% (high−low ÷ |median|, FY2026, as-of ≥2026-08-06)_

  - _D&A convention: fixed $M anchor (R1, mid-cycle) — the two recipes differ and the reconciliation is an open analyst question, so it is stated rather than assumed._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 9.2x as-of 2026-08-07 — trailing range 4.3–27.9x (median 19.8x) over 27 closes → 11%ile → near-floor; P/LTM EPS 8.1x [20]

## Peer comps
- **Peer set (roster · caps · business)** — [36]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| The Simply Good Foods Company | $982M | engages in the development, marketing, and sale of snacks and meal replacements, and other products in North America and internationally. (United States) |
| The J. M. Smucker Company | $12.8B | manufactures and markets branded food and beverage products worldwide. (United States) |
| Conagra Brands | $7.2B | operates as a branded consumer packaged goods food company primarily in the United States. (United States) |
| The Hershey Company | $36.6B | engages in the manufacture and sale of confectionery products and pantry items in the United States and internationally. (United States) |
| Nu Skin Enterprises | $266M | engages in the development and distribution of various beauty and wellness products worldwide. (United States) |
| Herbalife Ltd. | $1.3B | provides health and wellness products in North America, Mexico, South and Central America, Europe, the Middle East, Africa, China, and the Asia Pacific. (United States) |
| USANA Health Sciences | $286M | develops, manufactures, and sells science-based nutritional, personal care, and skincare products in the Asia Pacific, the Americas, and Europe. (United States) |
| Kenvue Inc. | $36.9B | operates as a consumer health company in the United States, rest of North America, Europe, the Middle East, Africa, the Asia-Pacific, and Latin America. (United States) |
| Nature's Sunshine Products | $288M | manufactures and sells nutritional and personal care products in Asia, Europe, North America, Latin America, and internationally. (United States) |
| FitLife Brands | $94M | provides nutritional supplements and wellness products for health-conscious consumers in the United States and internationally. (United States) |

_the name: $1.3B_

- **Comparability (confidence gate):** market caps span $94M–$36.9B (392x); the name is $1.3B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [22]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [28]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 1.04 | 0.18 | 1.13 | 1.35 | 3.36 |
| NTM TEV/EBITDA | 7.99 | 2.2 | 8.3 | 7.61 | 12.86 |
| NTM P/E | 9.45 | 4.63 | 11.38 | 11.53 | 19.65 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [37]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Kenvue Inc. | $36.9B | 12.6 | 2.9 | 22.6 | 23% | 2% | 2.4 | 7,503 |
| The Hershey Company | $36.6B | 15.0 | 3.4 | 24.9 | 22% | 8% | 2.1 | 5,132 |
| The J. M. Smucker Company | $12.8B | 9.8 | 2.2 | NM | 21% | 4% | 3.5 | 7,071 |
| Conagra Brands | $7.2B | 7.5 | 1.3 | NM | 15% | -3% | 4.2 | 7,257 |
| **BellRing Brands · the name** | **$1.3B** | **9.2** | **1.0** | **8.1** | **11%** | **6%** | **4.4** | **1,123** |
| Herbalife Ltd. | $1.3B | 4.5 | 0.6 | 8.0 | 12% | 6% | 3.2 | 1,833 |
| The Simply Good Foods Company | $982M | 5.7 | 0.9 | NM | 16% | -4% | 1.9 | 325 |
| Nature's Sunshine Products | $288M | 4.7 | 0.5 | 16.4 | 9% | 7% | 0.4 | 61 (net cash) |
| USANA Health Sciences | $286M | 2.2 | 0.2 | NM | 8% | 2% | – | 169 (net cash) |
| Nu Skin Enterprises | $266M | 2.3 | 0.3 | 5.1 | 9% | -14% | 1.9 | 103 |
| FitLife Brands | $94M | 9.9 | 1.5 | 16.7 | 15% | 42% | 3.1 | 41 |
| Peer median (peers) | $1.1B | 6.6 | 1.1 | 16.6 | 15% | 3% | 2.4 | 1,079 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [26]  <!-- ds-table -->

|  | Sep-2016 | Sep-2017 (R) | Sep-2018 | Sep-2019 | Sep-2020 | Sep-2021 | Sep-2022 (R) | Sep-2023 (R) | Sep-2024 | Sep-2025 | Jun-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 31% | 34% | 34% | 36% | 34% | 31% | 31% | 32% | 35% | 33% | 29% |

_R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** buying back (trailing ~1.7y): 128,782,398 (2024-11-12) → 116,278,194 (2026-07-28), -9.7% [38]
- **Non-operating earnings:** no material non-operating item in the four quarters to 2026-06-30 — in the latest, $-20M against $46M pre-tax [39]
- **Return ratios — per fiscal period** — [40]  <!-- ds-table -->

|  | FY16 | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | — | — | 20.5% | 26.2% | 61.5% | — | — | — | — | — | — |
| RoCE % | — | — | 16.0% | 22.5% | 20.0% | 23.1% | 23.9% | 33.4% | 43.1% | 34.5% | 21.6% |
| RoA % | — | — | 13.1% | 18.3% | 16.6% | 18.8% | 18.9% | 26.3% | 33.1% | 25.1% | 14.9% |
| Current ratio | — | 2.16x | 1.74x | 2.37x | 1.90x | 1.54x | 2.94x | 2.82x | 2.91x | 2.35x | 2.25x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-08-06)_
- **Horizon read (FQ — next-2Q revision breadth)** — [41]:
  - EPS Normalized FQ4 2026: 1m 0↑/13↓, 2m 0↑/13↓, 3m 0↑/12↓
  - EPS Normalized FQ1 2027: 1m 6↑/3↓, 2m 6↑/3↓, 3m 6↑/3↓
  - EPS (GAAP) FQ4 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EPS (GAAP) FQ1 2027: 1m 1↑/0↓, 2m 1↑/0↓, 3m 1↑/0↓
  - Revenue FQ4 2026: 1m 5↑/6↓, 2m 5↑/6↓, 3m 4↑/6↓
  - Revenue FQ1 2027: 1m 2↑/6↓, 2m 2↑/6↓, 3m 2↑/6↓
  - EBITDA FQ4 2026: 1m 0↑/11↓, 2m 0↑/11↓, 3m 0↑/10↓
  - EBITDA FQ1 2027: 1m 4↑/3↓, 2m 4↑/3↓, 3m 4↑/3↓
  - EBIT FQ4 2026: 1m 0↑/11↓, 2m 0↑/11↓, 3m 0↑/10↓
  - EBIT FQ1 2027: 1m 4↑/3↓, 2m 4↑/3↓, 3m 4↑/3↓
  - _+7 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 2.37 (12m) → 2.31 (9m) → 1.92 (6m) → 1.25 (3m) → 1.25 (2m) → 1.24 (1m) → 1.04 (latest); net -56% (12m→latest) | FY 2026 EPS (GAAP): 2.34 (12m) → 2.25 (9m) → 1.93 (6m) → 1.42 (3m) → 1.40 (2m) → 1.38 (1m) → 1.18 (latest); net -50% (12m→latest) | FY 2026 Revenue: 2,534.5 (12m) → 2,520.1 (9m) → 2,417.2 (6m) → 2,333.9 (3m) → 2,333.5 (2m) → 2,331.9 (1m) → 2,356.2 (latest); net -7% (12m→latest) | FY 2026 EBITDA: 512.3 (12m) → 499.9 (9m) → 424.5 (6m) → 318.8 (3m) → 318.6 (2m) → 317.4 (1m) → 288.1 (latest); net -44% (12m→latest) | FY 2026 EBIT: 469.1 (12m) → 458.2 (9m) → 384.4 (6m) → 279.7 (3m) → 278.8 (2m) → 277.6 (1m) → 246.3 (latest); net -47% (12m→latest) | FY 2026 Interest Expense: -65.1 (12m) → -68.8 (9m) → -79.9 (6m) → -80.5 (3m) → -79.9 (2m) → -80.2 (1m) → -79.7 (latest); worsening (magnitude away from zero) (12m→latest) | FY 2026 EBT (GAAP): 395.5 (12m) → 381.8 (9m) → 317.1 (6m) → 223.0 (3m) → 223.0 (2m) → 217.5 (1m) → 184.7 (latest); net -53% (12m→latest) | FY 2026 Net Income (Excl. Excep): 303.3 (12m) → 293.1 (9m) → 229.1 (6m) → 148.8 (3m) → 148.4 (2m) → 147.3 (1m) → 123.0 (latest); net -59% (12m→latest) | FY 2026 Net Income (GAAP): 297.7 (12m) → 287.1 (9m) → 234.3 (6m) → 165.8 (3m) → 164.8 (2m) → 163.2 (1m) → 138.2 (latest); net -54% (12m→latest)  [data ≥ 2026-08-06 · export date unverified] [33]
- **Cross-name anchor (NTM forward-multiple ladder)** — [29]:
  - NTM: TEV/REV 1.04 · TEV/EBITDA 7.99 · TEV/EBIT 9.26 · Price/Earnings 9.45 · PEG – · P/BV –
  - FY 2026: TEV/REV 1.05 · TEV/EBITDA 8.56 · TEV/EBIT 10.01 · Price/Earnings 11.07 · PEG – · P/BV –
  - FY 2027: TEV/REV 1.03 · TEV/EBITDA 7.64 · TEV/EBIT 8.74 · Price/Earnings 8.75 · PEG – · P/BV –
  - FY 2028: TEV/REV 1.00 · TEV/EBITDA 7.15 · TEV/EBIT 8.12 · Price/Earnings 7.56 · PEG – · P/BV –
  - _+2 later fiscal years in JSON_
- **Guidance at the drawdown (8-K 99.1):** Updates Fiscal Year 2026 Outlook St. Louis - May 5, 2026 - BellRing Brands, Inc. (NYSE:BRBR) (“BellRing”), a holding company operating in the global proactive wellness category, today reported results for the second fiscal quarter ended March 31, 2026. Highlights: • Second quarter net sales of $598.7 million, up 2% year-over-year • Operating profit of $66.0 million, net earnings of $33.9 million and Adjusted EBITDA* of $53.8 million, each of which were impacted by a pre-tax $11 million inventory-related charge • Updated fiscal year 2026 net sales outlook of $2.325-$2.365 billion and Adjusted EBITDA* outlook of $315-$335 million *Adjusted EBITDA is a non-GAAP measure. For additional information regarding non-GAAP measures, see the related explanations presented under “Use of Non-GAAP Measur [42]
- **Current guide (latest results filing):** net sales 2026: 2,335.0–2,375.0 $M [43]
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [44]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | '2,335.00 - 2,375.00' | FY 2026 | 2026-08-04 | fresh | actual ≥ floor 9/11 | FY 2025 MET |
| EBITDA | '275.00 - 295.00' | FY 2026 | 2026-08-04 | fresh | actual ≥ floor 7/7 | FY 2025 MET |
| Capital Expenditure | -10.0 | FY 2026 | 2026-08-04 | fresh | spend ≤ ceiling 6/6 | FY 2025 MET |
| Gross Margin % | none current (last: '28.20 - 32.40') | FQ4 2022 | 2022-08-05 | 1468d (stale) | actual ≥ floor 1/1 | FQ4 2022 MET |
| Interest Expense | none current (last: -47.0) | FY 2020 | 2020-02-07 | 2378d (stale) | spend ≤ ceiling 0/1 | FY 2020 MISSED |

_CIQ states every guide as a LEVEL in the metric's own units. Where management guided a RATE, the level is CIQ's arithmetic on its own base, not a figure the company published — check the release before quoting one as guidance._

- **Consensus stats (target + ratings):** Target price: mean $14.71, median $14.50, high/low 20.00/10.00, N 12/12; Ratings: Buy 6, Outperform 2, Hold 5, Underperform 1, Sell 0, No Opinion 1, Buy 0, Outperform 0, Hold 1, Underperform 0, Sell 0  [data ≥ 2026-08-06 · export date unverified] [23]
- **Revision-event log (250 events · 5 broker-days)** — [45]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Withheld | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-08-06 | broker undisclosed | 23 | — | — | 23 | — | — | — | — |
| 2026-08-05 | broker undisclosed | 55 | 9 | 46 | — | EBITDA FQ4 2026 | 89.3 | 65.5 | −23.8 |
| 2026-08-04 | BTIG | 20 | 6 | 14 | — | EBITDA FQ4 2026 | 96.0 | 65.4 | −30.6 |
| 2026-08-04 | William Blair & Company L.L.C. | 16 | 2 | 14 | — | EBITDA FQ4 2026 | 88.7 | 61.6 | −27.1 |
| 2026-08-04 | broker undisclosed | 136 | 34 | 100 | 2 | EBITDA FQ4 2026 | 91.0 | 66.0 | −25.0 |

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2019 +259%, FY2020 +13%, FY2021 +0%, FY2022 -20%, FY2023 -5%, FY2024 -1%, FY2025 -8%; Revenue surprise: FY2019 -0%, FY2020 +2%, FY2021 -2%, FY2022 -2%, FY2023 +1%, FY2024 +1%, FY2025 +1% (GAAP-EPS basis; +beat / −miss) [46]

## Leverage & survival
- **Net debt / EBITDA [NET]:** 4.3x [8]
- **Total debt / EBITDA vs peers:** name 4.4x vs peer median 2.4x (comps TOTAL-debt/EBITDA basis) [47]
- **Net debt / OCF:** 4.8x [48]
- **Interest coverage:** 3.3x [49]
- **Self-funding:** self-funding: MIXED — latest-Q OCF < 0, LTM FCF > 0 (both must be positive to self-fund) [50]
- **Credit health:** _UNKNOWN_ — credit-health panel scale is ambiguous in the export

- **FCF sign:** positive [9]
- **Free cash flow ($M):** 158.0 — basis: CIQ 'Levered Free Cash Flow', NOT CFO − capex: on the same sheet and period [LTM 12 months Jun-30-2026], CFO $234.1M − capex $9.1M = $225.0M — 0.70x apart. Company-defined FCF is usually the second; a per-share or self-funding read should say which it used. [27]
- **Debt schedule vintage:** the debt schedule is 267d old (source filed 2025-11-18); no Item 1.02 (termination of a material agreement) has been filed since [51]
- **Live instruments — near-dated (≤12m + 2027):** none due in the window — 3 undated / later aggregate line item(s) in the appendix panel [52]
- **Maturity wall** · vs the 2026-08-12 reference:
  - due 2030: $1,090.0M
  - undated (floor — no panel maturity): $29.5M — Operating Lease Liabilities $29.5M
  - _reconciliation: itemized $1,119.5M (panel A 2025 filed Nov-18-2025) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** senior bonds 840.0; total principal 1,177.8; total debt 1,173.1 (3 months Jun-30-2026) ($M) [53]
- **Covenants — Revolving Credit Facility** (governing values; full verbatim in appendix):
  - **Interest / coupon:** in respect of Term B Loans, 3.00% per annum for Base Rate Loans and 4.00% per annum for Eurodollar Rate Loans
  - **Interest / coupon:** Eurodollar Rate floor: Revolving Credit Loans not less than 1.00% per annum; Term Loans not less than 0.75% per annum
  - **Events of default:** Repricing Event premium of 1.00% of aggregate principal amount of Term B Loans repriced/refinanced or subject to amendm…
  - **Interest / coupon:** Prime Rate + 2.00% · Prime Rate plus 2.0% per annum

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [54]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [55]
  - net debt / EBITDA (CIQ, GAAP basis): 4.3x
  - total debt / EBITDA (CIQ comps, GAAP basis): 4.4x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage

## ⚠ Analyst caveats — verify before the verdict

_7 to verify._

- Guidance stated but not attributable — one range is shared by 2 metrics (adjusted ebitda, net sales), so which it governs cannot be read from the sentence; verify against the filing: "Updated fiscal year 2026 net sales outlook of $2.335-$2.375 billion and Adjusted EBITDA* outlook of $275-$295 million" (8-K 0001628280-26-052137 EX-99.1)
- Guidance stated but not attributable — one range is shared by 2 metrics (adjusted ebitda, net sales), so which it governs cannot be read from the sentence; verify against the filing: "Updated fiscal year 2026 net sales outlook of $2.325-$2.365 billion and Adjusted EBITDA* outlook of $315-$335 million" (8-K 0001628280-26-030115 EX-99.1)
- Guidance stated but not attributable — one range is shared by 2 metrics (adjusted ebitda, net sales), so which it governs cannot be read from the sentence; verify against the filing: "Narrowed fiscal year 2026 net sales outlook of $2.41-$2.46 billion and Adjusted EBITDA* outlook of $425-$440 million" (8-K 0001628280-26-004789 EX-99.1)
- Guidance stated but not attributable — one range is shared by 2 metrics (adjusted ebitda, net sales), so which it governs cannot be read from the sentence; verify against the filing: "Fiscal year 2026 net sales and Adjusted EBITDA* expected to range between $2.41-$2.49 billion" (8-K 0001628280-25-052773 EX-99.1)
- Guidance stated but not attributable — one range is shared by 2 metrics (adjusted ebitda, net sales), so which it governs cannot be read from the sentence; verify against the filing: "Adjusted EBITDA as a percentage of net sales of 18% to 20%" (8-K 0001628280-25-052773 EX-99.1)
- Net debt/EBITDA (4.3x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 4.3x as the covenant-basis leverage.
- Possible false balance — the written assessment commits a strong lean but the body is near-symmetric (7 bull vs 8 bear) and the minority bull points aren't qualified-as-outweighed — size the minority against the lean, or it launders a one-sided case

# Appendix — data & audit

## How to read this dossier
- The machine assembles and cites; **the analyst decides**. Nothing here is a recommendation — the verdict of record is the human's, logged to an append-only ledger with a frozen entry price.
- The machine's proposed verdict is derived deterministically from its written assessment and stays **sealed until the analyst's verdict is recorded**, so it cannot anchor the decision. A two-sided assessment proposes nothing.
- Citations [n] resolve in the Sources list at the document end. **Cited is not verified** — the reference locates the claim so you can check it.
- Reference values (peer-implied equity, price-implied levels) are shown **beside** the figures they contextualize, never differenced into an upside — the reader judges the gap.
- A value shown as UNKNOWN is honestly absent at the source — nothing is imputed.

## How these numbers were set

_Per-axis methodology from the underwrite record — the reference frame each leg was chosen against, not a re-derivation._

### Revenue · ratified 2026-08-05

All three legs are read off the street's forecast distribution AT THIS RECORD'S EIGHTEEN-MONTH HORIZON rather than at the nearest fiscal year: base 1,340 is the median FY2028 estimate, bull 1,410 the highest, and bear 1,200 approximates the lowest FY2027 estimate of 1,203.2. Taking all three from one distribution keeps a single horizon across the legs. The computed default of 1,351.7 is the FY2026 median and therefore describes a different moment, which is why base sits below it.

| reference | value |
| --- | ---: |
| FY2025 reported revenue | $1,450.9M [56] |
| LTM revenue | $1,416.208M [57] |
| consensus FY26E revenue `base` | $1,334M [58] |

### Margin · ratified 2026-08-05

Base 15.5% matches the median operating margin of the last eight fiscal years, 15.45%, and is corroborated forward rather than extrapolated from a depressed present — the street carries about 15.5% for FY2027 and an implied 15.7% for FY2028. Bear 13.0% is roughly 0.9pp below the trailing twelve-month margin: deterioration from a level already impaired. Bull 17.0% is held below the 17.18% actually earned in FY2024, so the upside claims only what the business has already done. Stated on operating income, not EBITDA.

| reference | value |
| --- | ---: |
| screening median (naive, 8 FY) | 15.45% [59] |
| 7yr clean median (FY2025 adjusted) `base` | 15.51% [60] |
| FY2020 worst clean year `bear` | 9.58% [61] |
| FY2022 best clean year `bull` | 17.35% [62] |
| FY2025 adjusted ex $60.9M impairment | 15.01% [63] |

### Multiple · ratified 2026-08-05

Base 9.0x is roughly half the 17.85x median close of the company's own eight-and-a-half-year trading history, and that gap IS the judgment: the history spans a growth era the business has left, so a median drawn across it describes a company that no longer exists. The leg follows the company's own de-rating instead — it traded at 9.54x as recently as September 2025 — and is cross-checked against the 8.72x median that comparable companies fetch on next-twelve-month earnings, which it sits slightly above. Bear 5.5x is below the 6.11x lowest close in that same history, deliberately not 5.0x, because a lower multiple would count deterioration the revenue and margin legs already carry. Bull 12.0x is near the 12.89x the most expensive comparable fetches.

| reference | value |
| --- | ---: |
| this company's trading-range low `bear` | 6.11x [64] |
| this company's trailing 25th percentile | 15.2x [64] |
| this company's trailing median `base` | 17.85x [64] |
| this company's trailing 75th percentile | 20.88x [64] |
| current multiple (0th pctile) | 5.65x [64] |
| entry-boundary cell A (1,100 × 8% × 6.0x) | 1.96:1 [65] |
| entry-boundary cell B (1,050 × 7% × 6.0x) | 1.73:1 [65] |

_2026-07-26 — entry-boundary cells: 1,100 × 8% × 6.0x → $3.54; 1,050 × 7% × 6.0x → $2.62 (from the sealed entry rationale, preserved in the ledger payload). At the verification price ($10.53, 2026-07-22 close) both clear on the entry-vintage 15.5% normal (≈2.34 / ≈2.07); on the re-set 14% normal they read ≈1.96 / ≈1.73 — below the bar. The boundary tightened with the cut: the 2:1 line now sits between the recorded 10% bear and these stress cells._ [65]


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-08-06)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [12]  <!-- ds-table -->

|  | FY16 | FY17 (R) | FY18 | FY19 | FY20 | FY21 | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 575 | 713 | 828 | 854 | 988 | 1,247 | 1,372 | 1,667 | 1,996 | 2,317 | 2,355 | 2,356 | 2,385 |
| Revenue growth | — | — (basis) | — (basis) | +3% | +16% | +26% | — (basis) | +22% | — (basis) | +16% | — (basis) | +2% (vs FY25) | +1% |
| EBITDA ($M) | 67 | 117 | 146 | 194 | 191 | 227 | 234 | 316 | 424 | 376 | 263 | 288 | 323 |
| EBITDA margin | 12% | 16% | 18% | 23% | 19% | 18% | 17% | 19% | 21% | 16% | 11% | 12% | 14% |
| EBIT ($M) | 42 | 92 | 120 | 169 | 166 | 203 | 212 | 294 | 405 | 357 | 243 | 246 | 282 |
| Net income ($M) | 20 | 35 | 0 | 0 | 24 | 28 | 82 | 166 | 246 | 216 | 171 | 138 | 153 |
| EPS (GAAP, dil.) | — | — | — | — | 0.60 | 0.70 | 0.88 | 1.23 | 1.86 | 1.68 | 1.43 | 1.18 | 1.34 |
| EPS (Normalized) | — | — | -0.62 | -0.44 | -0.18 | 0.33 | 0.73 | 1.06 | 1.64 | 1.41 | 0.86 | 1.04 | 1.32 |
| Restructuring Charges ($M) | — | — | — | — | — | -5 | — | -7 | -17 | — | — | — | — |
| Impairment of Goodwill ($M) | — | -26 | — | — | — | — | — | — | — | — | — | — | — |
| Gain (Loss) On Sale Of Assets ($M) | -4 | — | — | — | — | — | — | — | — | — | — | — | — |
| Asset Writedown ($M) | — | — | — | — | — | -30 | — | — | — | — | — | — | — |
| Legal Settlements ($M) | -6 | — | — | — | — | — | — | — | — | — | 69 | — | — |
| Other Unusual Items ($M) | — | — | — | -7 | -2 | -2 | -18 | — | — | — | — | — | — |
| CFO ($M) | 41 | 80 | 141 | 98 | 97 | 226 | 21 | 216 | 200 | 261 | 234 | 111 | 164 |
| Capex ($M) | -4 | -4 | -5 | -3 | -2 | -2 | -2 | -2 | -2 | -5 | -9 | -10 | -8 |
| FCF (levered, CIQ) | — | — | 121 | 69 | 61 | 178 | -5 | 192 | 162 | 224 | 158 | — | — |
| D&A ($M) | 25 | 25 | 26 | 25 | 25 | 24 | 21 | 21 | 19 | 19 | 20 | — | — |
| FCF (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | — | 165 | 195 |
| D&A (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | — | 20 | 21 |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-08-06; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Quarterly — every exported quarter
- **Quarterly financials** — [66]  <!-- ds-table -->

|  | FY17 | FY18 | FY18 | FY18 | FY18 | FY19 | FY19 | FY19 | FY19 | FY20 (R) | FY20 (R) | FY20 (R) | FY20 (R) | FY21 (R) | FY21 (R) | FY21 (R) | FY21 | FY22 | FY22 | FY22 | FY22 (R) | FY23 (R) | FY23 (R) | FY23 | FY23 | FY24 | FY24 | FY24 | FY24 | FY25 | FY25 (R) | FY25 | FY25 | FY26 | FY26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 196 | 205 | 216 | 220 | 186 | 216 | 238 | 214 | 244 | 258 | 204 | 283 | 282 | 282 | 343 | 340 | 306 | 315 | 371 | 379 | 363 | 386 | 446 | 473 | 430 | 495 | 515 | 556 | 533 | 588 | 548 | 648 | 537 | 599 | 570 |
| Gross margin | 33% | 31% | 35% | 34% | 35% | 36% | 38% | 36% | 37% | 34% | 34% | 32% | 33% | 31% | 32% | 28% | 30% | 28% | 32% | 32% | 34% | 30% | 31% | 33% | 34% | 33% | 37% | 37% | 37% | 32% | 35% | 29% | 30% | 27% | 29% |
| EBITDA ($M) | 28 | 31 | 46 | 44 | 39 | 49 | 60 | 45 | 56 | 42 | 37 | 57 | 54 | 39 | 69 | 63 | 58 | 49 | 74 | 68 | 80 | 63 | 81 | 91 | 96 | 96 | 116 | 117 | 120 | 100 | 118 | 107 | 83 | 72 | 71 |
| EBITDA margin | 14% | 15% | 21% | 20% | 21% | 23% | 25% | 21% | 23% | 16% | 18% | 20% | 19% | 14% | 20% | 19% | 19% | 15% | 20% | 18% | 22% | 16% | 18% | 19% | 22% | 19% | 23% | 21% | 22% | 17% | 21% | 17% | 16% | 12% | 12% |
| Revenue QoQ | — | +5% | +5% | +2% | -16% | +17% | +10% | -10% | +14% | — (basis) | -21% | +38% | -0% | -0% | +21% | -1% | — (basis) | +3% | +18% | +2% | — (basis) | +6% | +16% | — (basis) | -9% | +15% | +4% | +8% | -4% | +10% | — (basis) | — (basis) | -17% | +11% | -5% |
| Revenue YoY | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of FY26 ($M): cash & ST inv 50; total debt 1,173; net debt 1,123; equity -467; net working capital 434; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [67]
- **Coherence — BS vs implied-valuation bridge:** cash BS $50M / bridge $50M; debt BS $1,173M / bridge $1,173M — reconcile with the implied-valuation bridge. [68]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Nov-18-2025** — [52]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 7.00% Senior Notes Maturing in March 2030 | Bonds and Notes | $840.0M | 7.000% | NA | 2030-03-15 | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $29.5M | 7.000% | NA | undated | Y | N | USD |
| Revolving Credit Facility | Revolving Credit | $250.0M | 5.620% | Various Benchmarks | 2030-08-22 | Y | N |  |

- **8-Ks at instrument maturities:** _UNKNOWN_ — no trailing-12m instrument maturity to anchor an 8-K
- **Covenant / contract pointers (CIK-verified execution filings)** — [69]  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| Revolving Credit Facility | 8-K | 2021-02-26 | 0001772016-21-000029 — ex10-1_amend2creditagmt.htm, ex991-termloanbrepricing02.htm |
| Revolving Credit Facility | 8-K | 2019-10-21 | 0001193125-19-270862 — d812149dex101.htm, d812149dex102.htm, d812149dex103.htm |
| 7.00% Senior Notes Maturing in March 2030 | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Revolving Credit Facility (governing agreement)** — [70]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001772016-21-000029 · ex10-1_amend2creditagmt.htm |
| Principal / commitment amount | aggregate principal amount up to $636,200,000 (2021 Refinancing Term Loans); Schedule I: Credit Suisse AG, Cayman Islands Branch $636,200,000; Total $636,200,000 | base (footer) |
| Interest / coupon rate | in respect of Term B Loans, 3.00% per annum for Base Rate Loans and 4.00% per annum for Eurodollar Rate Loans — ⚠ QA: rate component 0.75 not stated in the clause — lead suppressed | base (footer) |
| Interest / coupon rate — Eurodollar Rate floor | Eurodollar Rate floor: Revolving Credit Loans not less than 1.00% per annum; Term Loans not less than 0.75% per annum | base (footer) |
| Maturity date | UNKNOWN | not stated in 8-K 0001772016-21-000029 · ex10-1_amend2creditagmt.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0001772016-21-000029 · ex10-1_amend2creditagmt.htm |
| Security / collateral / guarantors | 2021 Refinancing Term Loans constitute Obligations, are secured by the Collateral Documents, and are guaranteed pursuant to the Loan Documents; Loan Parties reaffirm pledges, grants of security inter… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | Repricing Event premium of 1.00% of aggregate principal amount of Term B Loans repriced/refinanced or subject to amendment, if occurring on or before 6 months after Amendment No. 2 Effective Date (Se… — full verbatim in JSON | base (footer) |
| Redemption Right / Share Settlement mechanics (LLC unit exchange) | Share Settlement = a number of shares of Class A Common Stock equal to the number of Redeemed Units, subject to adjustment as set forth in Section 9.01(e); Cash Settlement = immediately available fun… — full verbatim in JSON | 8-K 0001193125-19-270862 · d812149dex101.htm |
| Common Unit Redemption Price | arithmetic average of the volume weighted average prices for a share of Class A Common Stock for each of the five (5) consecutive full Trading Days ending on and including the last full Trading Day i… — full verbatim in JSON | 8-K 0001193125-19-270862 · d812149dex101.htm |
| Units issued / reclassified | 97,474,180 Nonvoting Common Units (reclassified to Holdings); 39,428,571 Nonvoting Common Units issued to Pubco; one Voting Common Unit issued to Pubco | 8-K 0001193125-19-270862 · d812149dex101.htm |
| Term / duration | perpetual existence unless sooner dissolved | 8-K 0001193125-19-270862 · d812149dex101.htm |
| Withholding Advance interest rate | Prime Rate + 2.00% · Prime Rate plus 2.0% per annum | 8-K 0001193125-19-270862 · d812149dex101.htm |

_Source §: 8-K 0001772016-21-000029 · ex10-1_amend2creditagmt.htm_


### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 1344.2 [71]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $50.40M, − total debt $1,173.10M [72]
- **Implied equity at peer-median ($M, CIQ)** — [73]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 601.9 |
| NTM Revenue (Capital IQ) | 1,562.1 |
| NTM EBITDA (Capital IQ) | 1,439.6 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf; BellRing Brands, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [74]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 2 (1 insider, $0.07M) · sells 0 — in the last 182 days · last purchase $0.04M, director, 2026-05-13 (~3mo ago) · largest purchase $65.82M, director, 2025-08-14 (~12mo ago) · last sale $0.12M, CHIEF GROWTH OFFICER, 2025-12-01 (~8mo ago) · largest sale $5.90M, director, 2025-02-14 (~18mo ago) · grants 51 · last filing 2026-07-31 · other filings 41 [75]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-07-31): 14.7M → 14.3M sh (-2.8%, falling) · 12.3% of shares out (EDGAR XBRL) · DTC 2.7d · recent: 2026-07-31 14.3M · 2026-07-15 14.7M · 2026-06-30 17.7M · 2026-06-15 15.8M [76]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [77]
- **Guide verification — CIQ guide vs release:** revenue: CIQ 2335.0–2375.0 vs release 2335.0–2375.0 → cross-source VERIFIED [78]

## Record & reproduce
- **Data window:** screened as of 2026-08-12 · assembled 2026-08-13 05:30 UTC
- **Extraction:** 2026-07-28.1 — unusual-items surfacing in the financial summary (#238) · multiples read from the latest close, NM rather than a stale figure (#241)
- **Price store:** `mosaic-theory-pg → mosaic-theory-wb` · reaching 2026-08-12
- **Panel age:** oldest panel 6d old — 2026-08-07 (valuation.implied_expectations.tev_as_of), against a 2026-08-13 build
- **Consensus age:** consensus 7d old (2026-08-06, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001772016` · NYSE : BRBR
- **Assembly log:** primary-source: 8-K 0001628280-26-045287 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 5 EX-99.1 release(s) + 1 10-Q parsed (+0.5s fetch)
- **Re-run:** `python -m vinci dossier --ticker BRBR` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Sep-30-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Sep-30-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[5] `EOD BRBR 180d to 2026-08-12`
[6] `EOD IWM 180d to 2026-08-12 (cap-band: $1.3B @ 2026-08-12 → small (<$4B) → IWM)`
[7] `EOD BRBR−IWM 180d to 2026-08-12 (assembly, cap-band)`
[8] `CIQ Net Debt $1,123M [FQ3/CQ2 Jun-30-2026] ÷ CIQ EBITDA $263M [LTM 12 months Jun-30-2026]`
[9] `EDGAR XBRL FCF sign (screen data-record)`
[10] `CIQ transcript: BellRing Brands, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf`
[11] `CIQ Key Developments: BellRing Brands Inc NYSE BRBR Key Developments.rtf · Aug-04-2026`
[12] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[13] `EDGAR companyfacts Goodwill (as at 2026-06-30)`
[14] `EDGAR companyfacts FiniteLivedIntangibleAssetsNet (as at 2026-06-30)`
[15] `EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2025-10-01→2026-06-30, 272d)`
[16] `EDGAR companyfacts TreasuryStockSharesAcquired (2025-10-01→2026-06-30, 272d)`
[17] `EDGAR companyfacts TreasuryStockAcquiredAverageCostPerShare (2025-10-01→2026-03-31, 181d)`
[18] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[19] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[20] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[21] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[22] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[23] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[24] `8-K 0001628280-26-030115 EX-99.1`
[25] `CIQ Customers&Suppliers BellRing Brands Inc NYSE BRBR Customers.rtf`
[26] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[27] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Jun-30-2026]`
[28] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[29] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[30] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[31] `CIQ Financials→Balance Sheet→Book Value/Share (latest)`
[32] `CIQ transcript: BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf`
[33] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[34] `cadence: EDGAR submissions (median 91d gap over 28 results 8-Ks; last print 2026-08-04) · guide: EDGAR 8-K 0001628280-26-030115 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1772016/000162828026030115/brbrexh991-q22026earningsr.htm`
[35] `TEV = mcap 1344.2 + net debt 1122.7 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-08-07, exported 2026-08-09) — simple-TEV basis`
[36] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[37] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-08-09`
[38] `EDGAR XBRL shares, trailing 2024-11-12..2026-07-28`
[39] `EDGAR XBRL pre-tax − operating, quarters 2025-06-30..2026-06-30`
[40] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[41] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[42] `EDGAR 8-K 0001628280-26-030115 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1772016/000162828026030115/brbrexh991-q22026earningsr.htm`
[43] `8-K 0001628280-26-052137 EX-99.1 (filed 2026-08-04)`
[44] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record) — CIQ states every guide as a LEVEL; where management guided a RATE, the level is CIQ's arithmetic, not the company's published figure`
[45] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-08-06 · export date unverified]`
[46] `CIQ Estimates→Surprise (annual)`
[47] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-08-09`
[48] `CIQ Net Debt $1,123M [FQ3/CQ2 Jun-30-2026] ÷ CIQ OCF $234M [LTM 12 months Jun-30-2026]`
[49] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Jun-30-2026]`
[50] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[51] `CIQ Capital Structure Details — A 2025 filed Nov-18-2025`
[52] `CIQ Financials→Capital Structure Details (A 2025 filed Nov-18-2025)`
[53] `CIQ Financials→Capital Structure Summary`
[54] `10-Q 0001772016-26-000022`
[55] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[56] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2025)`
[57] `committed dossier anchor block (#158/#160/#162-verified)`
[58] `committed dossier financial_summary (E cols = consensus)`
[59] `committed dossier anchor block (#158/#160/#162-verified) anchor.margin.value`
[60] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax FY2019-FY2025, FY2025 ex the $60.9M impairment`
[61] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2020)`
[62] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2022)`
[63] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2025) + 10-K 0001702744-25-000046 (FY2025, Note 5 Goodwill and Intangibles)`
[64] `committed dossier valuation.own_history (CIQ Financials→Multiples 'TEV/LTM EBITDA' Close, 35 closes, 8.55y span, as-of 2026-07-17, sha 7bd83a1103)`
[65] `entry rationale cells preserved in the ledger payload; re-verified 2026-07-26 at the 2026-07-22 close ($10.53)`
[66] `CIQ Financials→Income Statement (quarterly, full exported history)`
[67] `CIQ Financials→Balance Sheet (quarterly, FY26)`
[68] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[69] `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`
[70] `fenced Tier-2 extraction (verbatim, source-bound)`
[71] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-08-09`
[72] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-08-09`
[73] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-08-09`
[74] `CIQ transcript(s): BellRing Brands, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf; BellRing Brands, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf`
[75] `EDGAR Form 4 (latest 0001628280-26-051505; 161 filings in the 1095d scanned; counts over 182d)`
[76] `FINRA consolidated short interest (settle 2026-07-31); DTC = 14,310,982 short ÷ 5,287,731 screen 90d ADV`
[77] `10-Q maturity wall vs CIQ capital panel (same window)`
[78] `CIQ revenue guide vs release actual/outlook`