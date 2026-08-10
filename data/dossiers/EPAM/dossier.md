# Dossier — EPAM Systems, Inc. (NYSE: EPAM)

_August 10, 2026 · extraction 2026-07-28.1_

# Brief — first cut

## At a glance
**Target (base)** $186.76 (+108.9% vs entry-vintage spot) · **Spot** $89.40 (entry-vintage — frozen at underwrite 2026-07-21) · **Reward** $97.36 · **Risk** $15.34 · **Reward : risk** 6.34 : 1 (bar 2 : 1) · **Base IRR** UNDEFINED — no horizon stated — an IRR needs a realisation date · **Gate** UNDEFINED (both tests)

_Spot source: Polygon EOD daily close 2026-07-20 (live; 2026-07-21 has not settled)_

**Underwrite disposition:** PENDING_ANALYST — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

EPAM Systems, Inc. provides digital platform engineering and software development services worldwide.
**Mixed** — a net-cash, still-EBITDA-growing franchise at a valuation floor, against a genuinely deteriorating North American core and persistent margin erosion.
- **Segments:** Americas 58%; Europe 42% [1]
- **Geography:** United States 52%; Other Locations 21%; United Kingdom 11%; Switzerland 8%; Germany 4%; Netherlands 4% [2]
- **Snapshot:** NYSE · CMP $97.43 (2026-08-07) · cap $5.0B (2026-08-10) · 52-wk $73.06–$222.53 · shares 51.6M · book value/sh $68.21 [3]

**The crux — what decides this, and what would change our mind**
**Is the sharp de-rating a temporary overshoot on an FX/M&A-flattered but net-cash, still-growing franchise, or has North American demand and gross-margin erosion permanently reset EPAM's growth-and-margin profile?**
_7 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-11-05 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-02-19 earnings; 2026-06-18 no company filing; 2026-08-06 earnings [4]
- **Price (180d):** -48.8% [5]
- **Market (MDY) 180d:** 8.5% [6]
- **vs market (180d):** -57.3% [7]
- **Net debt / EBITDA:** -0.8x [8]
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
| Screen value / share | $352.35 | spot-independent · EV/EBIT 26.6x |
| Overall confidence | firm |  |

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Pure AI-native revenue is compounding fast — more than $160M in Q2 2026 after exceeding $125M in Q1 (up ~20% sequentially) — a fresh, growing mix element on a $600M full-year target. [10]
- Absolute EBITDA has kept rising through the margin-% compression — from $652M (FY23) to $707M (FY25) to $753M LTM Jun-30-2026 — so the falling margin percentage is not a falling profit dollar. [11]
- Fundamental deltas favor the name over the peer median on growth (rev growth 11% vs 1%; EBITDA growth 5% vs -0%; LT EPS growth 10% vs 8%) and leverage (0.2 vs 2.1), which poses whether the ~24% EV/EBITDA discount is residual overshoot rather than earned — for the human to judge. [12]
_Bear case — the decline is real:_
- The core North American business — the largest market at 52% of revenue — is structurally underperforming: management states it is 'not growing fast enough,' expects it below plan in H2, with demand shifting away from task-based services faster than AI replacement work ramps. [10]
- Organic constant-currency growth is weak and decelerating (3.7% in Q1 2026 to 3.4% in Q2 2026), with reported growth heavily FX/M&A-flattered, so the '11% rev growth vs peer 1%' comp overstates underlying momentum. [10]
- The big-deal pipeline that could inflect growth is unsigned and pushed out — management now expects meaningful revenue contribution only from H1 2027 versus H2 2026, deferring the catalyst. [10]

## Financial snapshot
- **Financial snapshot** — [13]  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 4,825 | 4,691 | 4,728 | 5,457 | 5,617 | 5,658 | 5,865 |
| Revenue growth | — (basis) | -3% | — (basis) | +15% | — (basis) | +4% (vs FY25) | +4% |
| EBITDA ($M) | 799 | 652 | 693 | 707 | 753 | 952 | 992 |
| EBITDA margin | 17% | 14% | 15% | 13% | 13% | 17% | 17% |
| EBIT ($M) | 708 | 562 | 604 | 583 | 628 | 895 | 934 |
| Net income ($M) | 419 | 417 | 455 | 378 | 402 | 436 | 499 |
| EPS (GAAP, dil.) | 7.09 | 7.06 | 7.84 | 6.72 | 7.39 | 8.35 | 9.80 |
| FCF ($M) | 413 | 531 | 667 | 725 | 650 | — | — |

_table shows the last 4 fiscal years · 5 earlier years are in the Appendix_

**Capital allocation — created or destroyed**

- **Impairment headroom — goodwill + intangibles remaining:** $1,576.0M [14]
- **Goodwill:** $1,203.0M [14]
- **Intangibles (net):** $373.0M [15]
- **Impairment:** _NONE IN THE CURRENT PERIOD_ — the last such charge covers 2022-01-01→2022-12-31, 364d, 3.5 years before the balance beside it (as at 2026-06-30), so it measures no current period. Nothing has been written down since
- **Buyback — cash:** $409.0M [16]
- **Buyback — shares repurchased:** 3,538,000 [17]
  - ⚠ **PERIOD MISMATCH** — cash covers 2026-01-01→2026-06-30, 180d and the share count covers 2025-01-01→2025-12-31, 364d; they are not one window and must not be divided into each other
- **Buyback — average cost/share:** $283.69 — **fiscal-period average over 2023-01-01→2023-03-31, 89d; NOT a purchase price** and not evidence of when they bought [18]
  - ⚠ **PERIOD MISMATCH** — this average covers 2023-01-01→2023-03-31, 89d while the repurchase cash beside it covers 2026-01-01→2026-06-30, 180d; they are not two views of one window and must not be divided into each other
- **Acquisition consideration:** $912.2M [19]
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [20]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap | why |
|---|---:|---:|---:|---:|---:|---|
| **EPAM** | **5,026** | **1,576** | **4,574** | **34%** | **31%** | **—** |
| ACN | 107,530 | 27,822 | 68,807 | 40% | 26% | — |
| CTSH | 25,977 | 9,166 | 20,500 | 45% | 35% | — |
| 4307 | 17,646 | — | — | — | — | unresolved |
| IT | 11,720 | 3,033 | 7,194 | 42% | 26% | — |
| 301236 | 6,282 | — | — | — | — | unresolved |
| DOX | 6,216 | 3,006 | 6,386 | 47% | 48% | — |
| SOP | 4,152 | — | — | — | — | unresolved |
| DXC | 1,732 | 2,045 | 12,926 | 16% | 118% | — |
| GLOB | 1,615 | — | — | — | — | no-tag |
| EFOR | 1,318 | 2,876 | 4,024 | 71% | 218% | — |

- **Median — all peers (n=6):** 43% of assets · 42% of market cap
- **Median — peers ≥ $1,000M market cap (n=6):** 43% of assets · 42% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [21]  <!-- ds-table -->

|  | state | yrs charged | window $M | % acquired | last charge (any date) | live YTD $M |
|---|---|---|---|---:|---:|---|
| **EPAM** | **wrote down** | **1 of 1** | **1** | **0%** | **2022-12-31 ($1M)** | **—** |
| ACN | reports nil | 0 of 5 | — | — | never | — |
| CTSH | no annual obs. | — | — | — | never | — |
| IT | wrote down | 1 of 5 | 150 | 5% | 2025-12-31 ($150M) | — |
| DOX | reports nil | 0 of 5 | — | — | never | — |
| DXC | wrote down | 1 of 5 | 14 | 1% | 2026-03-31 ($14M) | — |
| EFOR | no annual obs. | — | — | — | 2010-12-31 ($15M) | — |

- **Base rate — 2 of 4 large peers ASSESSED over the window took a charge**, median 3% of acquired assets among those that did. The denominator counts only peers with an annual observation in the window — a name with none was not measured, and is not a clean year.
- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. `no annual obs.` and `does not tag` are not measurements and must not be read as clean years. The **live YTD** column is excluded from the window total: a year-to-date charge is not an annual one, and the two are different quantities._

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 5.4x as-of 2026-08-07 — trailing range 4.3–57.2x (median 22.4x) over 38 closes → 3%ile → near-floor; P/LTM EPS 13.2x [22]
- **vs peers:** EV/EBITDA 5.4x vs peer median 7.1x (-24%); P/E 13.2x vs peer median 15.3x (-14%) [23]
- **Comparability:** market caps span $1.3B–$107.5B (82x); the name is $5.0B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [24]
- **The street, for contrast (target · ratings):** Target price: mean $122.24, median $120.00, high/low 200.00/85.00, N 17/17; Ratings: Buy 7, Outperform 3, Hold 9, Underperform 0, Sell 0, No Opinion 0, Buy 0, Outperform 0, Hold 2, Underperform 0, Sell 0  [data ≥ 2026-08-09 · export date unverified] [25]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [4]
  - 2026-02-19 **-17.0%** → earnings
  - 2026-06-18 **-12.6%** → no company filing
  - 2026-08-06 → earnings

_Company-specific or market-wide?_
- **Name 180d return:** -48.8% [5]
- **Market (MDY) 180d return:** 8.5% [6]
- **Relative vs market:** -57.3% [7]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-down 2026-02-19 → filed 2026-02-19 [`0001352010-26-000010`](https://www.sec.gov/Archives/edgar/data/1352010/000135201026000010/epam-20260219.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj operating income Q4 2025 $230.0M (+$21.8 million); adj EPS Q4 2025 $3.26 (+14.8%); 2026 revenue outlook: 4.5–7.5% growth [26]
  - gap-down 2026-08-06 → filed 2026-08-06 [`0001352010-26-000043`](https://www.sec.gov/Archives/edgar/data/1352010/000135201026000043/epam-20260806.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj operating income Q2 2026 $232.7M (+$29.8 million); adj EPS Q2 2026 $3.38 (+$0.61,); next-fy revenue outlook: 3.2–4.2% growth [27]

## Business quality
- **Segments (revenue share):** Americas 58%; Europe 42% [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — reports 2 segments (Americas; Europe) but discloses no segment EBITDA — revenue is segmented in the filing and EBITDA is not
- **Customers:** 31 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [28]
- **Geographic:** United States 52%; Other Locations 21%; United Kingdom 11%; Switzerland 8%; Germany 4%; Netherlands 4% [2]

## The argument

**Evidence balance:** mixed — a net-cash, still-EBITDA-growing franchise at a valuation floor, against a genuinely deteriorating North American core and persistent margin erosion.

### Bull case — the decline is overdone
- Pure AI-native revenue is compounding fast — more than $160M in Q2 2026 after exceeding $125M in Q1 (up ~20% sequentially) — a fresh, growing mix element on a $600M full-year target. [10]
- Absolute EBITDA has kept rising through the margin-% compression — from $652M (FY23) to $707M (FY25) to $753M LTM Jun-30-2026 — so the falling margin percentage is not a falling profit dollar. [11]
- Fundamental deltas favor the name over the peer median on growth (rev growth 11% vs 1%; EBITDA growth 5% vs -0%; LT EPS growth 10% vs 8%) and leverage (0.2 vs 2.1), which poses whether the ~24% EV/EBITDA discount is residual overshoot rather than earned — for the human to judge. [12]
- Guidance delivery is strong — actual ≥ guided revenue floor 67/68 times and ≥ EPS floor 64/65, with the most recent quarter (FQ2 2026) MET — a credible track record behind the fresh 2026-08-06 guide. [29]
- The balance sheet is net-cash (net-debt/EBITDA -0.8x, total debt/EBITDA 0.2x vs peer-median 2.1x) and FCF-positive ($650.2M LTM), so the name is self-funding and under no survival pressure. [30]
- Credit-health scores are better than peers (Overall/Operational/Solvency/Liquidity 2/2/2/1 vs peer-median 3/3/3/3), consistent with a stronger-than-average balance sheet. [31]
- The stock now trades at 5.4x trailing EV/EBITDA and 13.2x P/LTM EPS, both at roughly the 3rd percentile of their own ~9-year history (median 22.4x EV/EBITDA and 41.9x P/E), a near-floor de-rating from a company still growing absolute EBITDA. [22]
- The company is buying back stock — shares fell 9.4% over ~2 years (56.9M → 51.6M) — shrinking the base while the multiple is at a floor. [32]

### Bear case — the decline is real
- The core North American business — the largest market at 52% of revenue — is structurally underperforming: management states it is 'not growing fast enough,' expects it below plan in H2, with demand shifting away from task-based services faster than AI replacement work ramps. [10]
- Organic constant-currency growth is weak and decelerating (3.7% in Q1 2026 to 3.4% in Q2 2026), with reported growth heavily FX/M&A-flattered, so the '11% rev growth vs peer 1%' comp overstates underlying momentum. [10]
- The big-deal pipeline that could inflect growth is unsigned and pushed out — management now expects meaningful revenue contribution only from H1 2027 versus H2 2026, deferring the catalyst. [10]
- Gross margin has eroded persistently — 36% (FY17) → 31% (FY24) → 29% (FY25) → 29% LTM — and unlike EBITDA dollars this is a real, sustained quality decline, not just an optical percentage; it is the REAL signal of pricing/mix pressure, corroborated by softening organic growth. [11]
- The de-rating is idiosyncratic, not shared — the name fell ~48.8% over 180d while the mid-cap benchmark rose ~8.5% (a ~57pt relative shortfall), driven by discrete earnings gap-downs (2026-02-19 and 2026-08-06 8-K item 2.02), signalling company-specific deterioration rather than a market-wide overshoot. [7]
- Forward revisions are overwhelmingly negative — Revenue FY2026 breadth 0↑/16↓ last month, and near-term quarter breadth is near-uniformly downward (e.g. Revenue FQ3 0↑/14↓) — consensus is still cutting. [33]
- The 13.2x P/E discount to the 15.3x peer median is only 14% and the peer set is deeply heterogeneous, and the name carries a higher beta (1.4 vs 0.8) and lower EBITDA margin (13% vs 15%), so part of the discount is plausibly EARNED rather than a clean overshoot. [12]

### Decisive question
**Is the sharp de-rating a temporary overshoot on an FX/M&A-flattered but net-cash, still-growing franchise, or has North American demand and gross-margin erosion permanently reset EPAM's growth-and-margin profile?**

### …evidence for
- Absolute EBITDA keeps rising ($652M FY23 → $753M LTM) despite the margin-% slide, and the name is net-cash and FCF-positive — the fundamentals a temporary-overshoot thesis needs. [11]
- Pure AI-native revenue accelerated to more than $160M in Q2 2026, evidencing a growing mix component that could refill the demand gap over time. [10]

### …evidence against
- Management concedes North America — 52% of revenue — is 'not growing fast enough' and will be below plan in H2, with task-based demand eroding faster than AI work replaces it. [10]
- Gross margin has fallen persistently to 29% LTM from 36% in FY17, and consensus revenue revisions are still uniformly downward (0↑/16↓ last month). [11]

### Key unknowns
- No forward/adjusted EV/EBITDA or adjusted-EPS figure in the revised 99.1 guidance — the trailing 5.4x cannot be distinguished as a temporarily depressed vs permanently impaired level (a bearish disclosure gap).
- No segment-level EBITDA is disclosed (2 revenue segments only), so the profitability of the underperforming North America/Americas book is opaque — a bearish visibility gap given that region is the cited weakness.
- Interest coverage is UNKNOWN (no period with both EBITDA and interest expense) — though net-cash status limits the concern.
- The size, close-probability and ramp of the unsigned multiyear AI 'big-deal' pipeline are unquantified; management explicitly excludes them from the outlook and pushed contribution to H1 2027.
- Whether the FX/M&A gap between reported (~4.5%) and organic constant-currency (~3.4%) growth widens or narrows — the peer comp leans on the reported figure.
- The revolving-credit facility's stated expiration is October 21, 2026 (near-term); refinancing/extension terms and any covenant step-up not resolved in the supplied facts.
- Peer set is HETEROGENEOUS (market caps $1.3B–$107.5B, 82x span); the peer median is not a clean benchmark and every peer multiple must be confidence-gated before use.

### Twin reference cases
- **Cognizant Technology Solutions Corporation** — recovered
  - distinguished by: IT-services peer that de-rated on decelerating growth and margin worries, then stabilised as it repositioned toward digital/AI work while remaining consistently cash-generative.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Globant S.A.** — went terminal
  - distinguished by: Digital-engineering peer whose growth premium collapsed as demand normalised, showing how a growth-services name can lose its multiple when organic momentum fades — the same organic-deceleration risk in view here.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **DXC Technology Company** — went terminal
  - distinguished by: IT-services name where secular demand shift away from legacy/task-based work drove sustained revenue decline and a permanently compressed multiple — the value-trap analogue for a task-to-AI transition that ramps too slowly.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Accenture plc** — recovered
  - distinguished by: Consulting/IT-services leader that navigated a discretionary-spend slowdown by leaning into AI/GenAI offerings and reinvesting in go-to-market, illustrating the path a services franchise can take through a demand air-pocket.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Infosys** — recovered (LLM-claimed — verify)
  - distinguished by: Offshore-heavy IT-services franchise that saw growth stall on client caution yet defended its position through delivery scale and steady cash generation before demand re-accelerated.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-11-05 `[cadence-estimate]` — the next reported quarter against the committed trajectory [34]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 5.4x vs peer median 7.1x (-24%); P/E 13.2x vs peer median 15.3x (-14%) [23]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-08-07 · multiples as-of 2026-08-09 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [35]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **4.58x** | **$958.3M EBITDA †** |
| peer-median NTM TEV/EBITDA | 6.49x | $676.3M EBITDA |
| peer-median LTM TEV/EBITDA | 7.1x | $618.2M EBITDA |
| **name NTM TEV/Rev** | **0.76x** | **$5,774.9M Revenue †** |
| peer-median NTM TEV/Rev | 1.19x | $3,688.2M Revenue |
| peer-median LTM TEV/Rev | 1.2x | $3,657.4M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $951.8M · FY27E $992.4M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $5658.3M · FY27E $5864.8M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

### The EV gap — our base case vs the street

_Anchor FY2026 · consensus as-of ≥2026-08-09 (a FLOOR — the export states no as-of, so the true date is on or after this) · TEV as-of 2026-08-07 · form three-ratio_

- **The gap, decomposed (ours / consensus, at the anchor year)**  <!-- ds-table -->

|  | ratio | consensus dispersion |
|---|---|---:|
| revenue | 1.01x | sigma 12.50 on n=17 |
| EBITDA margin | 0.76x | sigma 5.06 on n=7 |
| exit multiple | 2.70x | street 4.62x at FY2026 |
| **product = the EV gap** | **2.07x** |  |

_the three ratios multiply to the gap by IDENTITY — this is a decomposition, never an attribution of cause_

- **Shape:** **multiple-dominant** at FY2026, and FY2027 gives the same shape — the label does not move with the year.

  _The record does not state which fiscal year its base leg is struck at, so this label is reported on FY2026's basis and is unverified against the leg. The total gap above carries no year and is unaffected._

- **Bridge:** our EV $9,081M − net debt $-637M = equity $9,718M ÷ 52.634M sh = **$184.63/sh** — against TEV $4,389M.

  - _Revenue dispersion 1.1% (high−low ÷ |median|, FY2026, as-of ≥2026-08-09)_
  - _EBITDA dispersion 1.5% (high−low ÷ |median|, FY2026, as-of ≥2026-08-09)_

  - _D&A convention: fixed $M anchor (R1, mid-cycle) — the two recipes differ and the reconciliation is an open analyst question, so it is stated rather than assumed._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 5.4x as-of 2026-08-07 — trailing range 4.3–57.2x (median 22.4x) over 38 closes → 3%ile → near-floor; P/LTM EPS 13.2x [22]

## Peer comps
- **Peer set (roster · caps · business)** — [36]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Cognizant Technology Solutions Corporation | $26.0B | provides consulting and technology, and outsourcing services in North America, Europe, and internationally. (United States) |
| Amdocs Limited | $6.2B | provides software and services to communications, entertainment, media, and other service providers worldwide. (United States) |
| DXC Technology Company | $1.7B | provides information technology services and solutions in the United States, the United Kingdom, the Rest of Europe, Australia, and internationally. (United States) |
| Globant S.A. | $1.6B | provides technology services in the United States, rest of North America, Latin America, Europe, and internationally. (Luxembourg) |
| Sopra Steria Group SA | $4.2B | provides consulting, digital, and software development services in France and internationally. (France) |
| Nomura Research Institute | $17.6B | engages in the provision of consulting, financial information technology (IT) solutions, Industrial IT solutions (Japan) |
| Everforth | $1.3B | provides information technology solutions for commercial and government sectors in the United States, Canada, and Europe. (United States) |
| Gartner | $11.7B | provides business and technology insights to support decision-making and performance on an organization’s mission-critical priorities in the United States (United States) |
| Accenture plc | $107.5B | provides strategy and consulting, industry X, song, and technology and operation services in the Americas, Europe, the Middle East, Africa (D02 P820 Ireland) |
| iSoftStone Information Technology | $6.3B | provides information technology services in China and internationally. (China) |

_the name: $5.0B_

- **Comparability (confidence gate):** market caps span $1.3B–$107.5B (82x); the name is $5.0B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [24]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [37]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 0.76 | 0.35 | 1.19 | 1.34 | 3.32 |
| NTM TEV/EBITDA | 4.58 | 2.7 | 6.49 | 6.64 | 12.29 |
| NTM P/E | 7.18 | 3.97 | 9.52 | 10.13 | 22.07 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [38]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Accenture plc | $107.5B | 7.7 | 1.5 | 14.1 | 18% | 7% | 0.6 | 1,783 (net cash) |
| Cognizant Technology Solutions Corporation | $26.0B | 6.4 | 1.2 | 12.4 | 19% | 6% | 0.5 | 1,043 |
| Nomura Research Institute | $17.6B | 25.2 | 3.5 | 154.0 | 14% | 7% | 2.1 | 654 |
| Gartner | $11.7B | 9.5 | 2.1 | 17.0 | 21% | 1% | 2.3 | 1,841 |
| iSoftStone Information Technology | $6.3B | 213.2 | 1.2 | NM | 0% | 10% | 44.6 | 180 |
| Amdocs Limited | $6.2B | 6.4 | 1.5 | 13.9 | 22% | 0% | 1.0 | 881 |
| **EPAM Systems · the name** | **$5.0B** | **5.4** | **0.8** | **13.2** | **13%** | **11%** | **0.2** | **637 (net cash)** |
| Sopra Steria Group SA | $4.2B | 7.1 | 0.8 | 12.1 | 10% | 2% | 2.1 | 1,298 |
| DXC Technology Company | $1.7B | 2.4 | 0.3 | 15.4 | 11% | -2% | 2.4 | 2,217 |
| Globant S.A. | $1.6B | 4.6 | 0.8 | 15.3 | 16% | 0% | 1.1 | 262 |
| Everforth | $1.3B | 7.1 | 0.7 | 16.4 | 9% | -1% | 4.0 | 1,344 |
| Peer median (peers) | $6.2B | 7.1 | 1.2 | 15.3 | 15% | 1% | 2.1 | 962 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [11]  <!-- ds-table -->

|  | Dec-2017 (R) | Dec-2018 | Dec-2019 | Dec-2020 | Dec-2021 | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 | Dec-2025 | Jun-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 36% | 36% | 35% | 35% | 34% | 33% | 31% | 31% | 29% | 29% |

_Revenue YoY (latest same-quarter): +20.9% (Q2 Jun-30-2026 vs Q2 Jun-30-2023). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** buying back (trailing ~2.0y): 56,935,370 (2024-07-31) → 51,586,981 (2026-07-31), -9.4% [32]
- **Return ratios — per fiscal period** — [39]  <!-- ds-table -->

|  | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | 8.3% | 21.5% | 18.3% | 18.3% | 21.5% | 15.3% | 12.9% | 12.8% | 10.3% | 11.2% |
| RoCE % | 12.0% | 13.4% | 12.0% | 11.5% | 13.7% | 14.9% | 10.3% | 10.2% | 9.6% | 10.5% |
| RoA % | 9.9% | 10.7% | 9.8% | 9.5% | 10.9% | 11.7% | 8.4% | 8.3% | 7.5% | 8.5% |
| Total debt/equity | 0.03x | 0.02x | 0.17x | 0.13x | 0.10x | 0.06x | 0.05x | 0.04x | 0.04x | 0.04x |
| Current ratio | 5.31x | 4.56x | 3.81x | 4.11x | 2.97x | 3.69x | 4.79x | 2.96x | 2.59x | 2.75x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-08-09)_
- **Horizon read (FQ — next-2Q revision breadth)** — [40]:
  - EPS Normalized FQ3 2026: 1m 1↑/12↓, 2m 1↑/12↓, 3m 1↑/11↓
  - EPS Normalized FQ4 2026: 1m 0↑/14↓, 2m 0↑/15↓, 3m 0↑/14↓
  - Revenue FQ3 2026: 1m 0↑/14↓, 2m 0↑/13↓, 3m 0↑/13↓
  - Revenue FQ4 2026: 1m 0↑/14↓, 2m 0↑/13↓, 3m 0↑/13↓
  - EBITDA FQ3 2026: 1m 1↑/4↓, 2m 0↑/5↓, 3m 0↑/5↓
  - EBITDA FQ4 2026: 1m 0↑/5↓, 2m 0↑/5↓, 3m 0↑/5↓
  - EBIT FQ3 2026: 1m 1↑/10↓, 2m 1↑/10↓, 3m 1↑/10↓
  - EBIT FQ4 2026: 1m 1↑/11↓, 2m 1↑/11↓, 3m 1↑/11↓
  - _+8 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 12.1 (12m) → 12.4 (9m) → 12.6 (6m) → 13.1 (3m) → 13.1 (2m) → 13.1 (1m) → 13.2 (latest); net +8% (12m→latest) | FY 2026 EPS (GAAP): 8.49 (12m) → 8.62 (9m) → 8.63 (6m) → 8.32 (3m) → 8.32 (2m) → 8.32 (1m) → 8.35 (latest); net -2% (12m→latest) | FY 2026 Revenue: 5,801.3 (12m) → 5,822.3 (9m) → 5,829.3 (6m) → 5,733.2 (3m) → 5,731.3 (2m) → 5,729.1 (1m) → 5,658.3 (latest); net -2% (12m→latest) | FY 2026 EBITDA: 961.6 (12m) → 968.2 (9m) → 967.3 (6m) → 963.0 (3m) → 963.0 (2m) → 950.7 (1m) → 951.8 (latest); net -1% (12m→latest) | FY 2026 EBIT: 892.1 (12m) → 902.3 (9m) → 901.7 (6m) → 891.5 (3m) → 891.5 (2m) → 891.6 (1m) → 894.5 (latest); net +0% (12m→latest) | FY 2026 Interest Expense: -2.00 (3m) → -2.00 (2m) → -3.41 (1m) → -8.00 (latest); worsening (magnitude away from zero) (3m→latest) | FY 2026 EBT (GAAP): 631.4 (12m) → 629.2 (9m) → 627.7 (6m) → 596.0 (3m) → 595.8 (2m) → 595.6 (1m) → 595.2 (latest); net -6% (12m→latest) | FY 2026 Net Income (Excl. Excep): 684.8 (12m) → 687.5 (9m) → 690.4 (6m) → 687.1 (3m) → 687.7 (2m) → 687.5 (1m) → 686.2 (latest); net +0% (12m→latest) | FY 2026 Net Income (GAAP): 479.6 (12m) → 477.1 (9m) → 478.4 (6m) → 438.7 (3m) → 438.8 (2m) → 438.4 (1m) → 436.3 (latest); net -9% (12m→latest)  [data ≥ 2026-08-09 · export date unverified] [41]
- **Cross-name anchor (NTM forward-multiple ladder)** — [42]:
  - NTM: TEV/REV 0.76 · TEV/EBITDA 4.58 · TEV/EBIT 4.89 · Price/Earnings 7.18 · PEG 0.71 · P/BV –
  - FY 2026: TEV/REV 0.78 · TEV/EBITDA 4.61 · TEV/EBIT 4.91 · Price/Earnings 7.41 · PEG 0.73 · P/BV 1.37
  - FY 2027: TEV/REV 0.75 · TEV/EBITDA 4.42 · TEV/EBIT 4.70 · Price/Earnings 6.93 · PEG 0.68 · P/BV 1.14
  - FY 2028: TEV/REV 0.71 · TEV/EBITDA 4.16 · TEV/EBIT 4.42 · Price/Earnings 6.53 · PEG 0.65 · P/BV 0.99
  - _+2 later fiscal years in JSON_
- **Current guide (latest results filing):** revenue next-fy: 3.2–4.2 % [43]
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [29]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | '1,410.00 - 1,425.00' | FQ3 2026 | 2026-08-06 | fresh | actual ≥ floor 67/68 | FQ2 2026 MET |
| Capital Expenditure | '(19.00) - (20.00)' | FY 2016 | 2016-02-18 | 3814d (stale) | spend ≤ ceiling 1/2 | FY 2016 MISSED |
| EPS Normalized | '3.38 - 3.46' | FQ3 2026 | 2026-08-06 | fresh | actual ≥ floor 64/65 | FQ2 2026 MET |

- **Consensus stats (target + ratings):** Target price: mean $122.24, median $120.00, high/low 200.00/85.00, N 17/17; Ratings: Buy 7, Outperform 3, Hold 9, Underperform 0, Sell 0, No Opinion 0, Buy 0, Outperform 0, Hold 2, Underperform 0, Sell 0  [data ≥ 2026-08-09 · export date unverified] [25]
- **Revision-event log (250 events · 11 broker-days)** — [44]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-08-09 | Mizuho Securities USA LLC | 16 | 5 | 11 | — | Revenue FQ3 2026 | 1455.0 | 1421.0 | −34.0 |
| 2026-08-09 | broker undisclosed | 2 | — | — | 2 | — | — | — | — |
| 2026-08-07 | Guggenheim Securities, LLC | 25 | 11 | 14 | — | Revenue FQ3 2026 | 1446.6 | 1417.4 | −29.2 |
| 2026-08-07 | Mizuho Securities USA LLC | 1 | 1 | — | — | Capital Expenditure FQ3 2026 | -11.0 | -9.0 | +2.0 |
| 2026-08-07 | Morningstar Inc. | 13 | 9 | 4 | — | Revenue FQ3 2026 | 1436.0 | 1429.0 | −7.0 |
| 2026-08-07 | Wedbush Securities Inc. | 27 | 7 | 16 | 4 | Revenue FQ3 2026 | 1457.1 | 1421.4 | −35.7 |

_+5 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2011 -34%, FY2012 -4%, FY2013 +2%, FY2014 -1%, FY2015 +4%, FY2016 -4%, FY2017 -51%, FY2018 +1%, FY2019 +2%, FY2020 -1%, FY2021 +2%, FY2022 +7%, FY2023 -4%, FY2024 -0%, FY2025 -2%; Revenue surprise: FY2011 +2%, FY2012 +2%, FY2013 +2%, FY2014 +0%, FY2015 +1%, FY2016 +0%, FY2017 +0%, FY2018 +0%, FY2019 +1%, FY2020 +1%, FY2021 +1%, FY2022 +0%, FY2023 +0%, FY2024 +1%, FY2025 +0% (GAAP-EPS basis; +beat / −miss) [45]

## Leverage & survival
- **Net debt / EBITDA [NET]:** -0.8x [8]
- **Total debt / EBITDA vs peers:** name 0.2x vs peer median 2.1x (comps TOTAL-debt/EBITDA basis) [46]
- **Net debt / OCF:** -1.2x [47]
- **Interest coverage:** _UNKNOWN_ — no period with both EBITDA and Interest Expense
- **Self-funding:** self-funding: MIXED — latest-Q OCF < 0, LTM FCF > 0 (both must be positive to self-fund) [48]
- **Credit health** — [31]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 2 | 3 |
| Operational | 2 | 3 |
| Solvency | 2 | 3 |
| Liquidity | 1 | 3 |

_S&P issuer rating unrated · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [9]
- **Free cash flow ($M):** 650.2 [49]
- **Live instruments — near-dated (≤12m + 2027):** none due in the window — 3 undated / later aggregate line item(s) in the appendix panel [50]
- **Maturity wall** · vs the 2026-07-29 reference:
  - due 2030: $25.0M
  - undated (floor — no panel maturity): $118.7M — Long Term Debt - Other $0.0M, Operating Lease Liabilities $118.7M
  - _reconciliation: itemized $143.7M (panel A 2025 filed Feb-26-2026) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** leases 127.2; total principal 152.2; total debt 152.2 (3 months Jun-30-2026) ($M) [51]
- **Covenants — Revolving Credit Facility** (governing values; full verbatim in appendix):
  - **Interest / coupon:** Adjusted Eurocurrency Rate + 0.875% (Floor 0.00%) · Base Rate Option: Base Rate plus Applicable Margin; Eurocurrency Rate Option: Adjusted Eurocurrency Rate plus Applicabl…
  - **Maturity:** October 21, 2026 · Expiration Date: October 21, 2026 (as may be extended)
  - **Financial maintenance:** Maximum Consolidated Leverage Ratio: not to exceed 3.50 to 1.00 (temporary step-up to 4.00 to 1.00 for a four fiscal qu…
  - **Events of default:** Mandatory Prepayments (Section 5.3): (a)-(b) [Reserved]; (d) Alternative Currencies – if Loans and LC Obligations in Al…

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [52]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [53]
  - net debt / EBITDA (CIQ, GAAP basis): -0.8x
  - total debt / EBITDA (CIQ comps, GAAP basis): 0.2x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage

## ⚠ Analyst caveats — verify before the verdict

_1 to verify._

- **Unreconciled margin-compression** — Gross margin has fallen persistently to 29% LTM from 36% in FY17, and consensus revenue revisions are still uniformly downward (0↑/16↓ last month).
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
| consensus FY26E revenue | $5,730.43M [54] |
| consensus FY27E revenue | $6,074.52M [55] |
| LTM revenue | $5,555.425M [56] |

### Margin · **DRAFT — not ratified by the analyst**

Modelled on regime-split operating-margin statistics (post-2022 window; operating income divided by the ASC-606 revenue tag, with annual filing points filtered to 350-380 day durations so no quarter is mistaken for a year): base is the post-2022 median of 11.10% less a ~60bps trajectory haircut; bear sits below the regime's worst year (FY25, 9.53%); bull recovers toward but below the pre-war median (13.27%, a regime no longer representative). The 10-year blend (11.90%) is explicitly not used — it straddles the 2022 break and describes neither regime. [restated for external readability 2026-07-21; substance unchanged]

| reference | value |
| --- | ---: |
| post-2022 regime median operating margin (FY2022-2025) | 11.1% [57] |
| post-2022 worst year (FY2025) | 9.53% [58] |
| post-2022 best year (FY2022) | 11.88% [59] |
| _pre-war median operating margin (FY2016-2021) — excluded: the pre-war margin structure no longer obtains_ | _13.27%_ [60] |
| _10-FY blended median (FY2016-2025) — excluded: blends across the structural break_ | _11.9%_ [61] |

### Multiple · **DRAFT — not ratified by the analyst**

Chosen against the regime-split TEV/LTM-EBITDA trading range (38 quarterly closes): base sits below the post-2022 median (15.16x) as an analyst discount for the unresolved AI-substitution question; bear near the post-2022 trough; bull toward but below the post-2022 75th percentile (20.09x). The full-blend median (22.41x) is not used — it is a pre-2022 bubble-era statistic. [restated for external readability 2026-07-21; substance unchanged]

| reference | value |
| --- | ---: |
| post-2022 band 25th percentile | 11.83x [62] |
| post-2022 band median | 15.16x [62] |
| post-2022 band 75th percentile | 20.09x [62] |
| full-band minimum (9.5y history) | 4.26x [63] |
| current TEV/LTM-EBITDA (2.6th percentile of the full band) | 4.87x [64] |
| band multiples are vendor TEV/LTM-EBITDA computed on the filer's actual depreciation - the corrected fact aligns the grid's EBITDA basis with the band's | $124.811M [65] |


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-08-09)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [13]  <!-- ds-table -->

|  | FY17 (R) | FY18 | FY19 | FY20 | FY21 | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 1,450 | 1,843 | 2,294 | 2,659 | 3,758 | 4,825 | 4,691 | 4,728 | 5,457 | 5,617 | 5,658 | 5,865 |
| Revenue growth | — | — (basis) | +24% | +16% | +41% | — (basis) | -3% | — (basis) | +15% | — (basis) | +4% (vs FY25) | +4% |
| EBITDA ($M) | 202 | 283 | 348 | 441 | 628 | 799 | 652 | 693 | 707 | 753 | 952 | 992 |
| EBITDA margin | 14% | 15% | 15% | 17% | 17% | 17% | 14% | 15% | 13% | 13% | 17% | 17% |
| EBIT ($M) | 173 | 246 | 303 | 379 | 546 | 708 | 562 | 604 | 583 | 628 | 895 | 934 |
| Net income ($M) | 73 | 240 | 261 | 327 | 482 | 419 | 417 | 455 | 378 | 402 | 436 | 499 |
| EPS (GAAP, dil.) | 1.32 | 4.24 | 4.53 | 5.60 | 8.15 | 7.09 | 7.06 | 7.84 | 6.72 | 7.39 | 8.35 | 9.80 |
| EPS (Normalized) | 1.98 | 2.74 | 3.27 | 4.07 | 5.78 | 6.91 | 6.35 | 7.01 | 6.35 | 7.11 | 13.15 | 14.05 |
| Restructuring Charges ($M) | — | — | — | — | — | -17 | — | -31 | -48 | -54 | — | — |
| Merger & Related Restruct. Charges ($M) | — | — | — | — | -4 | — | — | -14 | — | 1 | — | — |
| Impairment of Goodwill ($M) | — | — | — | — | — | -1 | — | — | — | — | — | — |
| Gain (Loss) On Sale Of Invest. ($M) | — | — | — | — | — | -1 | — | — | — | — | — | — |
| Gain (Loss) On Sale Of Assets ($M) | — | — | — | — | — | — | -26 | — | — | — | — | — |
| Asset Writedown ($M) | — | — | — | — | — | -19 | -6 | -0 | -0 | -0 | — | — |
| Other Unusual Items ($M) | — | 1 | -2 | -2 | -9 | -109 | -31 | -20 | -18 | -18 | — | — |
| CFO ($M) | 193 | 292 | 287 | 544 | 572 | 464 | 563 | 559 | 655 | 539 | — | — |
| Capex ($M) | -30 | -38 | -99 | -69 | -112 | -82 | -28 | -32 | -42 | -56 | — | — |
| FCF (levered, CIQ) | 131 | 243 | 221 | 456 | 486 | 413 | 531 | 667 | 725 | 650 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-08-09; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Quarterly — every exported quarter
- **Quarterly financials** — [66]  <!-- ds-table -->

|  | Q1-17 | Q2-17 (R) | Q3-17 (R) | Q4-17 (R) | Q1-18 (R) | Q2-18 (R) | Q3-18 (R) | Q4-18 (R) | Q1-19 | Q2-19 | Q3-19 | Q4-19 | Q1-20 | Q2-20 | Q3-20 | Q4-20 | Q1-21 | Q2-21 (R) | Q3-21 (R) | Q4-21 (R) | Q1-22 (R) | Q2-22 (R) | Q3-22 (R) | Q4-22 (R) | Q1-23 (R) | Q2-23 | Q3-23 | Q4-23 (R) | Q1-24 (R) | Q2-24 (R) | Q3-24 | Q4-24 (R) | Q1-25 | Q2-25 (R) | Q3-25 | Q4-25 | Q1-26 | Q2-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 325 | 349 | 378 | 399 | 424 | 446 | 468 | 505 | 521 | 552 | 588 | 633 | 651 | 632 | 652 | 723 | 781 | 881 | 989 | 1,107 | 1,172 | 1,195 | 1,227 | 1,231 | 1,211 | 1,170 | 1,152 | 1,157 | 1,165 | 1,147 | 1,168 | 1,248 | 1,302 | 1,353 | 1,394 | 1,408 | 1,400 | 1,415 |
| Gross margin | 36% | 37% | 37% | 36% | 35% | 35% | 36% | 37% | 34% | 35% | 36% | 35% | 35% | 34% | 35% | 36% | 33% | 34% | 34% | 34% | 35% | 30% | 33% | 35% | 30% | 31% | 31% | 31% | 28% | 29% | 35% | 30% | 27% | 29% | 30% | 30% | 28% | 30% |
| EBITDA ($M) | 42 | 48 | 56 | 60 | 57 | 63 | 74 | 89 | 75 | 84 | 92 | 97 | 102 | 99 | 112 | 128 | 125 | 146 | 166 | 192 | 229 | 148 | 213 | 223 | 157 | 173 | 167 | 184 | 143 | 144 | 200 | 186 | 140 | 162 | 180 | 197 | 165 | 187 |
| EBITDA margin | 13% | 14% | 15% | 15% | 13% | 14% | 16% | 18% | 14% | 15% | 16% | 15% | 16% | 16% | 17% | 18% | 16% | 17% | 17% | 17% | 20% | 12% | 17% | 18% | 13% | 15% | 14% | 16% | 12% | 13% | 17% | 15% | 11% | 12% | 13% | 14% | 12% | 13% |
| Revenue QoQ | — | — (basis) | +8% | +6% | +6% | +5% | +5% | +8% | — (basis) | +6% | +7% | +8% | +3% | -3% | +3% | +11% | +8% | — (basis) | +12% | +12% | +6% | +2% | +3% | +0% | -2% | — (basis) | -2% | — (basis) | +1% | -2% | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | +1% | -1% | +1% |
| Revenue YoY | — | — | — | — | — (basis) | +28% | +24% | +26% | — (basis) | — (basis) | — (basis) | — (basis) | +25% | +15% | +11% | +14% | +20% | — (basis) | — (basis) | — (basis) | — (basis) | +36% | +24% | +11% | +3% | — (basis) | — (basis) | -6% | -4% | — (basis) | +1% | +8% | — (basis) | +18% | +19% | — (basis) | +8% | — (basis) |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q2-26 ($M): cash & ST inv 789; total debt 152; net debt -637; equity 3,519; net working capital 1,412; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [67]
- **Coherence — BS vs implied-valuation bridge:** cash BS $789M / bridge $789M; debt BS $152M / bridge $152M — reconcile with the implied-valuation bridge. [68]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Feb-26-2026** — [50]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Long Term Debt - Other | Other Borrowings | $0.0M | NA | NA | undated | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $118.7M | 4.800% | NA | undated | Y | N | USD |
| Revolving Credit Facility | Revolving Credit | $25.0M | 4.500% | Benchmark | 2030-10-03 | N | N |  |

- **8-Ks at instrument maturities:** _UNKNOWN_ — no trailing-12m instrument maturity to anchor an 8-K
- **Covenant / contract pointers (CIK-verified execution filings)** — [69]  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| Revolving Credit Facility | 8-K | 2017-05-26 | 0001352010-17-000022 — exhibit10-1epamcreditagree.htm |
| Revolving Credit Facility | 8-K | 2021-10-25 | 0001352010-21-000039 — exhibit101-arcreditagreeme.htm |
| Long Term Debt | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Revolving Credit Facility (governing agreement)** — [70]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001352010-21-000039 · exhibit101-arcreditagreeme.htm |
| Principal / commitment amount | $700,000,000 REVOLVING CREDIT FACILITY; Swingline Loan Commitment aggregate principal amount up to $50,000,000; Letter of Credit Sublimit $100,000,000; Alternative Currency Sublimit lesser of $150,00… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Incremental Loan Commitment | Incremental Loan Commitments not to exceed $100,000,000.00 in aggregate; each not less than $25,000,000.00 | base (footer) |
| Letter of Credit Sublimit | $50,000,000.00 | base (footer) |
| Interest / coupon rate | Adjusted Eurocurrency Rate + 0.875% (Floor 0.00%) · Base Rate Option: Base Rate plus Applicable Margin; Eurocurrency Rate Option: Adjusted Eurocurrency Rate plus Applicable Margin. Applicable Margin (Revolving Credit Eurocurrency Rate Spread) ranges 0… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Base Rate definition | highest of (a) Overnight Bank Funding Rate plus 0.5%, (b) Prime Rate, and (c) Daily LIBOR Rate plus 1.00% | base (footer) |
| Maturity date | October 21, 2026 · Expiration Date: October 21, 2026 (as may be extended) | amended by 0001352010-21-000039 |
| Financial-maintenance covenants | Maximum Consolidated Leverage Ratio: not to exceed 3.50 to 1.00 (temporary step-up to 4.00 to 1.00 for a four fiscal quarter period following a Material Permitted Acquisition, not more than twice dur… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Security / collateral / guarantors | Guarantors: each direct or indirect Subsidiary of the Borrower (other than Excluded Subsidiaries), pursuant to Continuing Agreement of Guaranty and Suretyship. Signatory Guarantors include Vested Dev… — full verbatim in JSON | amended by 0001352010-21-000039 |
| Mandatory prepayment / events of default | Mandatory Prepayments (Section 5.3): (a)-(b) [Reserved]; (d) Alternative Currencies – if Loans and LC Obligations in Alternative Currencies exceed 105% of Alternative Currency Sublimit, prepay/Cash C… — full verbatim in JSON | amended by 0001352010-21-000039 |

_Source §: 8-K 0001352010-17-000022 · exhibit10-1epamcreditagree.htm · amended by 0001352010-21-000039_


### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 5026.1 [71]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $789.40M, − total debt $152.20M [72]
- **Implied equity at peer-median ($M, CIQ)** — [73]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 5,997.4 |
| NTM Revenue (Capital IQ) | 7,455.2 |
| NTM EBITDA (Capital IQ) | 6,854.1 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q2 2026 Earnings Call, Aug 06, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [74]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 6 (6 insiders, $0.04M) · sells 0 — in the last 182 days · last purchase $0.01M, CEO, President, Director, 2026-04-30 (~3mo ago) · last sale $1.03M, SVP/Co-Head of Global Business, 2025-12-10 (~8mo ago) · largest sale $5.69M, CEO, President, Chairman, 2024-03-14 (~28mo ago) · grants 58 · last filing 2026-05-22 · other filings 153 [75]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-07-15): 11.3M → 9.5M sh (-15.4%, falling) · 18.5% of shares out (EDGAR XBRL) · DTC 4.7d · recent: 2026-07-15 9.5M · 2026-06-30 11.3M · 2026-06-15 10.3M · 2026-05-29 9.6M [76]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [77]
- **Guide verification — CIQ guide vs release:** revenue: CIQ guides a LEVEL (1410.0–1425.0) and the release guides a CHANGE (3.2–4.2) — NOT CROSS-CHECKED. Deriving a level from the prior period would compare a filing-derived guide against a vendor-derived base; the two need not share a definition. [78]

## Record & reproduce
- **Data window:** screened as of 2026-07-29 · assembled 2026-08-10 11:26 UTC
- **Extraction:** 2026-07-28.1 — unusual-items surfacing in the financial summary (#238) · multiples read from the latest close, NM rather than a stale figure (#241)
- **Panel age:** oldest panel 3d old — 2026-08-07 (valuation.implied_expectations.tev_as_of), against a 2026-08-10 build
- **Consensus age:** consensus 1d old (2026-08-09, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001352010` · NYSE : EPAM
- **Assembly log:** primary-source: 5 EX-99.1 release(s) + 1 10-Q parsed (+0.6s fetch)
- **Re-run:** `python -m vinci dossier --ticker EPAM` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[5] `EOD EPAM 180d to 2026-07-29`
[6] `EOD MDY 180d to 2026-07-29 (cap-band: $5.0B @ 2026-07-29 → mid ($4–25B) → MDY)`
[7] `EOD EPAM−MDY 180d to 2026-07-29 (assembly, cap-band)`
[8] `CIQ Net Debt $-637M [Q2 Jun-30-2026] ÷ CIQ EBITDA $753M [LTM 12 months Jun-30-2026]`
[9] `EDGAR XBRL FCF sign (screen data-record)`
[10] `CIQ transcript: EPAM Systems, Inc., Q2 2026 Earnings Call, Aug 06, 2026.rtf`
[11] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[12] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[13] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[14] `EDGAR companyfacts Goodwill (as at 2026-06-30)`
[15] `EDGAR companyfacts IntangibleAssetsNetExcludingGoodwill (as at 2026-06-30)`
[16] `EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2026-01-01→2026-06-30, 180d)`
[17] `EDGAR companyfacts TreasuryStockSharesAcquired (2025-01-01→2025-12-31, 364d)`
[18] `EDGAR companyfacts TreasuryStockAcquiredAverageCostPerShare (2023-01-01→2023-03-31, 89d)`
[19] `EDGAR companyfacts PaymentsToAcquireBusinessesNetOfCashAcquired (2024-01-01→2024-12-31, 365d)`
[20] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[21] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[22] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[23] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[24] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[25] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[26] `8-K 0001352010-26-000010 EX-99.1`
[27] `8-K 0001352010-26-000043 EX-99.1`
[28] `CIQ Customers&Suppliers EPAM Systems Inc NYSE EPAM Customers.rtf`
[29] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
[30] `CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign (survival capacity)`
[31] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-08-10`
[32] `EDGAR XBRL shares, trailing 2024-07-31..2026-07-31`
[33] `CIQ Estimates→Revisions (Last-Month breadth, FY)`
[34] `cadence: EDGAR submissions (median 91d gap over 52 results 8-Ks; last print 2026-08-06)`
[35] `TEV = mcap 5026.1 + net debt -637.2 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-08-07, exported 2026-08-10) — simple-TEV basis`
[36] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[37] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[38] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-08-10`
[39] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[40] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[41] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[42] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[43] `8-K 0001352010-26-000043 EX-99.1 (filed 2026-08-06)`
[44] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-08-09 · export date unverified]`
[45] `CIQ Estimates→Surprise (annual)`
[46] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-08-10`
[47] `CIQ Net Debt $-637M [Q2 Jun-30-2026] ÷ CIQ OCF $539M [LTM 12 months Jun-30-2026]`
[48] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[49] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Jun-30-2026]`
[50] `CIQ Financials→Capital Structure Details (A 2025 filed Feb-26-2026)`
[51] `CIQ Financials→Capital Structure Summary`
[52] `10-Q 0001352010-26-000046`
[53] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[54] `committed financial_summary.annual FY26E — CIQ Estimates→Trends 'Current', as-of ≥2026-06-18`
[55] `committed financial_summary.annual FY27E — CIQ Estimates→Trends 'Current', as-of ≥2026-06-18`
[56] `committed financial_summary.annual (LTM) — CIQ Income Statement`
[57] `EDGAR companyfacts OperatingIncomeLoss ÷ RevenueFromContractWithCustomerExcludingAssessedTax, 10-K 365d points — regime-split basis pull 2026-07-21`
[58] `EDGAR companyfacts — same basis, FY2025 (520 EBIT / 5,457 revenue)`
[59] `EDGAR companyfacts — same basis, FY2022 (573 EBIT / 4,825 revenue); GAAP carries the war-year charges, so a cleaned FY22 would sit higher`
[60] `EDGAR companyfacts — same basis, pre-2022 window; shown for reference ONLY (the pre-invasion cost structure no longer exists)`
[61] `EDGAR companyfacts — same basis, 10 FY; equals the committed anchor's margin, which averages across the 2022 regime break and describes neither regime`
[62] `committed valuation.own_history series, 2022Q1 onward (n=18) — refreshed band sha 9614730c9e`
[63] `committed valuation.own_history — refreshed band sha 9614730c9e`
[64] `committed valuation.own_history current, as-of 2026-07-17 — refreshed band sha 9614730c9e`
[65] `EDGAR companyfacts DepreciationAndAmortization FY2025 (accession 0001352010-26-000015)`
[66] `CIQ Financials→Income Statement (quarterly, full exported history)`
[67] `CIQ Financials→Balance Sheet (quarterly, Q2-26)`
[68] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[69] `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`
[70] `fenced Tier-2 extraction (verbatim, source-bound)`
[71] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-08-10`
[72] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-08-10`
[73] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-08-10`
[74] `CIQ transcript(s): EPAM Systems, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; EPAM Systems, Inc., Q2 2026 Earnings Call, Aug 06, 2026.rtf`
[75] `EDGAR Form 4 (latest 0001355666-26-000002; 118 filings in the 1095d scanned; counts over 182d)`
[76] `FINRA consolidated short interest (settle 2026-07-15); DTC = 9,546,920 short ÷ 2,046,697 screen 90d ADV`
[77] `10-Q maturity wall vs CIQ capital panel (same window)`
[78] `CIQ revenue guide vs release actual/outlook`