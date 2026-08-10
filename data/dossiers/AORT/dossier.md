# Dossier — ARTIVION, INC. (NYSE: AORT)

_July 30, 2026 · extraction 2026-07-28.1_

# Brief — first cut

## At a glance
**Target (base)** $10.34 (-59.2% vs entry-vintage spot) · **Spot** $25.37 (entry-vintage — frozen at underwrite 2026-07-22) · **Reward** $-15.03 · **Risk** $22.28 · **Reward : risk** -0.67 : 1 (bar 2 : 1) · **Base IRR** -8.1% (floor 15%, 4y) · **Gate** FAIL (both tests)

_Spot source: Polygon AORT close 2026-07-20 (live at underwrite)_

**Underwrite disposition:** WATCH (2026-07-22) — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

### Thesis — our rationale
_Prices quoted below are entry-vintage (2026-07-22); the live close is in Snapshot, above._

WATCH at $25.37. The underwrite fails our 2:1 bar with room to spare: the base case is worth about $10 a share in today's terms - under half the market price - and even the optimistic case sits a quarter below it. The market is paying today for margins this company has never printed: breaking even needs roughly 15% operating margins at the stock's own historical floor multiple, against a best-ever year of 10%, margins that moved backwards last year, three-and-a-half turns of debt, and a product recall whose cost is not yet quantified. A real franchise, priced past its delivery. We revisit near $10, or on proof the 2024 cost discipline was structural rather than a one-year event.

### What would reopen this name

- price below about $10.50, roughly the base case in today's terms, then re-run at the new price
- the second-quarter report quantifies the recall as bounded AND valve and stent-graft revenue growth holds double-digit - re-underwrite the optimistic and central cases
- reported operating margin at or above 10% for two consecutive halves with spending growing slower than revenue - the cost model is structural; raise the terminal path

> ⚠ **Verify before the verdict:** Net debt/EBITDA (3.3x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis — full caveats in Analysis.

Artivion, Inc. manufactures, processes, and distributes medical devices and implantable human tissues worldwide.
- **Segments:** Products 78%; Preservation Services 22% [1]
- **Geography:** North America 50%; Europe The Middle East and Africa 34%; Asia Pacific 10%; Latin America 5% [2]
- **Snapshot:** NYSE · CMP $27.01 (2026-07-28) · cap $1.1B · 52-wk $19.16–$48.25 · shares 48.5M · book value/sh $9.29 [3]

**The crux — what decides this, and what would change our mind**
**Is the sharp de-rate a temporary overshoot around a lowered 2026 guide and a contained On-X recall — with On-X/stent-graft/tissue growth and NEXUS restoring the EBITDA trajectory — or the start of an earned, terminal re-rate as recall, leverage and negative LTM FCF impair the franchise?**
_8 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-08-06 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-05-08 material agreement + earnings [4]
- **Price (180d):** -45.3% [5]
- **Market (IWM) 180d:** 17.0% [6]
- **vs market (180d):** -62.3% [7]
- **Net debt / EBITDA:** 3.3x [8]
- **Free cash flow:** positive [9]

## Scenario analysis
_Terminal-margin: value the business in the year it reaches a normal operating margin, then discount that value back at the house waiting charge. Used where no trailing multiple describes the company._

| scenario | revenue $M | margin | multiple | value / sh | vs entry-vintage spot |
| --- | ---: | ---: | ---: | ---: | ---: |
| bear | 590 | 4.5% | 9x | $3.09 | -87.8% |
| base | 638 | 9.5% | 13x | $10.34 | -59.2% |
| bull | 680 | 13.0% | 16x | $18.18 | -28.3% |

- **bear** — the valve recall dents the growth franchise and the FY2024 cost reset proves unsustainable: margin returns toward the 2021-23 structural zone as spending normalizes; a levered, low-margin device business exits well below mature peers.
- **base** — revenue = consensus FY2027 then a stated fade of ~1.5 points a year; margin = partial delivery of the consensus path - above the realized two-year mean (8.83%), below next year's street case (10.80%), respecting that operating leverage ran backwards in the latest year; exit paired to the outcome: mature device businesses at about twice our terminal margin trade near 14x, so 13x for this one.
- **bull** — the FY2024 operating model (10% on falling spend) proves durable and scales past consensus; the recall is bounded at the next print; partial deleveraging earns a step toward - but below - the company's own trading floor.

**Scenario inputs** — every value in the grid recomputes from these.

| input | value | basis | source |
| --- | ---: | --- | --- |
| net debt | 202.393 $M | lease-inclusive net debt, latest quarter: total debt 215 + finance leases 4 + operating leases 39 - cash 56 | EDGAR companyfacts, 10-Q period ended 2026-03-31 |
| diluted shares | 50.20035 shares | Diluted shares outstanding 50,200,350 = basic outstanding 48,543,350 + dilutive increment 1,657,000 (diluted 49,731,000 − basic 48,074,000 weighted average, 2026-01-01→2026-03-31). The dilutive increment is carried from the reporting period to the valuation date, which assumes the dilutive count has not moved since. Excluded from the filer's diluted average: antidilutive instruments (a loss period reports no dilution at all under ASC 260); out-of-the-money options, which contribute nothing under the treasury-stock method; any change in the dilutive count between the reporting period and the valuation date. | EDGAR dei:EntityCommonStockSharesOutstanding + us-gaap:WeightedAverageNumberOf{SharesOutstandingBasic,DilutedSharesOutstanding} — item 24 denominator swap |
| d and a ratio | 0.048961 rate | latest depreciation and amortisation over trailing-twelve-month revenue (22.458 / 458.689) | EDGAR companyfacts dep_amort, FY2025; revenue from the committed financial summary |
| share growth | 0.022516 rate | OVERRIDE. The raw three-year compound rate (5.62%) terminates in a one-off convert-for-stock exchange whose balance-sheet benefit is already banked in net debt; compounding it forward would charge the terminal year twice. Forward rate = the FY2021-FY2024 organic basic-share compound rate. | EDGAR 8-K Item 3.02 accessions 0000784199-25-000080 (2025-05-14) and 0000784199-25-000129 (2025-05-29); share series FY2021-FY2024 |

_Chain (EV/EBITDA):_ EBIT_T = terminal revenue × terminal margin → D&A_T = (latest-FY D&A ÷ latest-FY revenue) × terminal revenue → EBITDA_T = EBIT_T + D&A_T → EV_T = denominator_T × exit multiple   (denominator = EBITDA_T, or EBIT_T on EV/EBIT) → net debt_T = current net debt + cumulative burn to breakeven → equity_T = EV_T − net debt_T → shares_T = current diluted × (1 + share growth)^years + announced-raise shares → value_T = equity_T ÷ shares_T → PV = value_T ÷ (1 + hurdle)^years

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | mid-cycle margin × the median multiple of its own history | applicable |
| Mid-cycle margin | 3.9% | 10y history · firm |
| Median multiple, own history | 32.1x | 42 closes · firm · EV/EBITDA |
| Screen value / share | $21.90 | spot-independent · EV/EBIT 72.7x |
| Overall confidence | firm |  |

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Q1 2026 total revenue reached $116.3M, up 12% constant currency year-over-year, showing the top line is still growing despite the drawdown. [10]
- On-X revenue grew 17% constant currency on further global market-share gains, a mechanism-backed franchise driver rather than a one-off. [10]
- Q1 2026 adjusted EBITDA grew ~26% (from $17.5M to $22.1M) with adjusted EBITDA margin near 19%, a ~130bp year-over-year improvement, evidencing operating leverage. [10]
_Bear case — the decline is real:_
- Leverage is elevated: net-debt/EBITDA 3.3x and total-debt/EBITDA 3.7x vs peer-median 2.1x, with interest coverage only 2.5x — a real EARNED reason for a discount, not an overshoot. [11]
- LTM levered free cash flow is negative (-$7.3M), so the business is not self-funding on a trailing basis despite positive latest-quarter OCF. [12]
- Credit-health panel scores the name weaker than peers (Overall/Operational/Solvency/Liquidity 4/3/3/4 vs peer-median 2.5/2.5/2.5/2.5; 1=strongest…4=weakest), corroborating an earned-risk discount. [13]

## Financial snapshot
- **Financial snapshot** — [14]  <!-- ds-table -->

|  | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 314 | 354 | 389 | 441 | 459 | 486 | 540 |
| Revenue growth | — (basis) | — (basis) | +10% | — (basis) | — (basis) | +10% (vs FY25) | +11% |
| EBITDA ($M) | 20 | 15 | 52 | 54 | 61 | 94 | 116 |
| EBITDA margin | 6% | 4% | 13% | 12% | 13% | 19% | 21% |
| EBIT ($M) | -3 | -8 | 28 | 31 | 38 | 33 | 58 |
| Net income ($M) | -19 | -31 | -13 | 10 | 12 | 4 | 23 |
| EPS (GAAP, dil.) | -0.48 | -0.75 | -0.32 | 0.21 | 0.24 | 0.08 | 0.41 |
| FCF ($M) | 0 | -4 | 0 | -20 | -7 | — | — |

_table shows the last 4 fiscal years · 6 earlier years are in the Appendix_

> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 59 of D&A against 22 in the actuals (2.65x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.


**Capital allocation — created or destroyed**

- **Impairment headroom — goodwill + intangibles remaining:** $471.1M [15]
- **Goodwill:** $349.9M [15]
- **Intangibles (net):** $121.3M [16]
- **Impairment:** _NONE IN THE CURRENT PERIOD_ — the last such charge covers 2012-01-01→2012-12-31, 365d, 13.5 years before the balance beside it (as at 2026-06-30), so it measures no current period. Nothing has been written down since
- **Buyback — cash:** $5.6M [17]
- **Buyback — shares repurchased:** 585,000 [18]
- **Buyback — average cost/share:** _UNKNOWN_ — no TreasuryStockAcquiredAverageCostPerShare, and the only available legs are a CASH-FLOW payment line (EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2014-01-01→2014-12-31, 364d)) and a share COUNT (EDGAR companyfacts TreasuryStockSharesAcquired (2014-01-01→2014-12-31, 364d)). They cover one window but not one BASIS — cash paid includes prior-period excise tax and excludes accrued-unpaid, so the quotient is not a purchase price and does not reproduce the filer's own figure — refused rather than derived (EDGAR XBRL companyfacts). The repurchase CASH and SHARE COUNT above are each sound on their own basis; it is their QUOTIENT that is not a price
- **Acquisition consideration:** $116.7M [19]
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [20]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap | why |
|---|---:|---:|---:|---:|---:|---|
| **AORT** | **1,069** | **471** | **1,072** | **44%** | **44%** | **—** |
| BSX | 66,083 | 25,558 | 45,216 | 57% | 39% | — |
| EW | 51,626 | 3,334 | 13,867 | 24% | 6% | — |
| 688617 | 3,905 | — | — | — | — | unresolved |
| LMAT | 2,108 | 96 | 641 | 15% | 5% | — |
| ATRC | 1,432 | 278 | 677 | 41% | 19% | — |
| PRCT | 1,187 | — | 479 | — | — | no-tag |
| 7575 | 547 | — | — | — | — | unresolved |
| ANGO | 540 | 67 | 267 | 25% | 12% | — |
| CVRX | 137 | — | 92 | — | — | no-tag |
| ARAY | 39 | 58 | 448 | 13% | 147% | — |

- **Median — all peers (n=6):** 25% of assets · 16% of market cap
- **Median — peers ≥ $1,000M market cap (n=4):** 33% of assets · 13% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [21]  <!-- ds-table -->

|  | state | yrs charged | window $M | % acquired | last charge (any date) | live YTD $M |
|---|---|---|---|---:|---:|---|
| **AORT** | **no annual obs.** | **—** | **—** | **—** | **2012-12-31 ($0M)** | **—** |
| BSX | wrote down | 5 of 5 | 992 | 4% | 2025-12-31 ($46M) | — |
| EW | no annual obs. | — | — | — | 2013-12-31 ($6M) | 40 |
| LMAT | wrote down | 1 of 5 | 3 | 4% | 2021-12-31 ($3M) | — |
| ATRC | wrote down | 1 of 3 | 82 | 30% | 2021-12-31 ($82M) | — |
| PRCT | does not tag | — | — | — | never | — |
| ANGO | wrote down | 3 of 5 | 333 | 495% | 2024-05-31 ($159M) | — |
| CVRX | does not tag | — | — | — | never | — |
| ARAY | reports nil | 0 of 5 | — | — | 2013-06-30 ($12M) | — |

- **Base rate — 3 of 3 large peers ASSESSED over the window took a charge**, median 4% of acquired assets among those that did. The denominator counts only peers with an annual observation in the window — a name with none was not measured, and is not a clean year.
- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. `no annual obs.` and `does not tag` are not measurements and must not be read as clean years. The **live YTD** column is excluded from the window total: a year-to-date charge is not an annual one, and the two are different quantities._

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 20.6x as-of 2026-07-17 — trailing range 18.8–75.4x (median 32.1x) over 42 closes → 7%ile → near-floor; P/LTM EPS 104.0x [22]
- **vs peers:** EV/EBITDA 18.4x vs peer median 24.6x (-25%); P/E 91.4x vs peer median 30.7x (+198%) [23]
- **Comparability:** market caps span $39M–$66.1B (1682x); the name is $1.1B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [24]
- **The street, for contrast (target · ratings):** Target price: mean $42.00, median $43.00, high/low 48.00/36.00, N 8/8; Ratings: Buy 6, Outperform 2, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-06-30 · export date unverified] [25]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [4]
  - 2026-05-08 **-28.3%** → material agreement + earnings

_Company-specific or market-wide?_
- **Name 180d return:** -45.3% [5]
- **Market (IWM) 180d return:** 17.0% [6]
- **Relative vs market:** -62.3% [7]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-down 2026-05-08 → filed 2026-05-07 [`0001628280-26-032097`](https://www.sec.gov/Archives/edgar/data/784199/000162828026032097/aort-20260507.htm)
    - items: 1.01 Entry into a Material Definitive Agreement, 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj net income Q1 2026 $4.2M; 2026 revenue outlook: $480.0–$496.0M; 2026 adjusted EBITDA outlook: $100.0–$107.0M [26]
    - 1.01 Entry into a Material Definitive Agreement: Securities Purchase Option Agreement As previously disclosed in connection with the announcement of the Exclusive Distribution Agreement, dated September 11, 2019, between JOTEC GmbH, a wholly owned subsidiary of Artivion, Inc., a Delaware corporation formerly known as CryoLife, Inc., and Endospan Ltd., an Israeli corporation, a

## Business quality
- **Segments (revenue share):** Products 78%; Preservation Services 22% [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — reports 2 segments (Products; Preservation Services) but discloses no segment EBITDA — revenue is segmented in the filing and EBITDA is not
- **Customers:** 4 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [27]
- **Geographic:** North America 50%; Europe The Middle East and Africa 34%; Asia Pacific 10%; Latin America 5% [2]

## The argument

**Evidence balance:** mixed — core double-digit growth and a near-floor own-history multiple sit against a lowered guide, a recall, elevated leverage and negative LTM FCF.

### Bull case — the decline is overdone
- Q1 2026 total revenue reached $116.3M, up 12% constant currency year-over-year, showing the top line is still growing despite the drawdown. [10]
- On-X revenue grew 17% constant currency on further global market-share gains, a mechanism-backed franchise driver rather than a one-off. [10]
- Q1 2026 adjusted EBITDA grew ~26% (from $17.5M to $22.1M) with adjusted EBITDA margin near 19%, a ~130bp year-over-year improvement, evidencing operating leverage. [10]
- FDA approval of the Endospan NEXUS Aortic Arch System (Apr-07-2026) and the exercised acquisition option add a platform technology to a claimed complete aortic-arch portfolio, a dated catalyst. [28]
- On the peer grid the name's EBITDA growth of 42% is roughly double the peer-median 21% and its 18% revenue growth exceeds the peer-median 14%, so the discount to peer-median EV/EBITDA (18.4x vs 24.6x) is worth testing as RESIDUAL/overshoot rather than EARNED — but the heterogeneous peer set (caps $39M–$66.1B) gates any clean read. [29]
- Absolute LTM EBITDA has risen to $61M (Mar-31-2026) versus $15M at the FY23 trough, so the mid-teens EBITDA margin masks a genuine and accelerating absolute-profit recovery. [30]
- Consensus target price mean $42.00 / median $43.00 versus a $27.01 close, and the rating panel is Buy 6 / Outperform 2 / Hold 0, indicating sell-side still frames the de-rate as an overshoot. [31]
- EV/EBITDA (TEV/LTM) sits at 20.6x, ~7th percentile of its own 42-quarter range (median 32.1x), a near-floor own-history reading that poses the overshoot question. [32]

### Bear case — the decline is real
- Leverage is elevated: net-debt/EBITDA 3.3x and total-debt/EBITDA 3.7x vs peer-median 2.1x, with interest coverage only 2.5x — a real EARNED reason for a discount, not an overshoot. [11]
- LTM levered free cash flow is negative (-$7.3M), so the business is not self-funding on a trailing basis despite positive latest-quarter OCF. [12]
- Credit-health panel scores the name weaker than peers (Overall/Operational/Solvency/Liquidity 4/3/3/4 vs peer-median 2.5/2.5/2.5/2.5; 1=strongest…4=weakest), corroborating an earned-risk discount. [13]
- The May-07-2026 discrete gap-down was triggered by management LOWERING full-year 2026 earnings guidance, a company-specific negative event, not a market-wide move. [33]
- An On-X Life Technologies voluntary product RECALL (May-23-2026) — heart valves distributed before required testing was complete — hits the very franchise (On-X, 17% growth) the bull case leans on, a genuine mechanism-level risk. [34]
- FY2026 consensus GAAP EPS has been cut ~82% (0.45→0.08 over 12m→latest) and EBT (GAAP) ~79%, a broad, deep, one-directional estimate collapse concentrated after the guide-down. [35]
- The reported P/E of 91.4x vs peer-median 30.7x is NOT the real cheapness signal — it is an optical distortion from an anomalous trailing EPS of 0.21, so the P/E cannot be read as a clean multiple in either direction. [36]
- Near-term forward multiples are extreme on GAAP earnings — NTM P/E 161.63 (peer-median 26.73) and NTM TEV/EBITDA 15.66 — so a forward basis does not obviously validate cheapness on the earnings line. [37]
- Share count is diluting — +15.9% over ~1.7 years (41.9M→48.5M) — eroding per-share value while the Endospan acquisition is financed. [38]
- The name is deeply idiosyncratic-weak: -45.3% over 180d versus IWM +17.0%, a -62.3% relative underperformance not explained by the market. [7]

### Decisive question
**Is the sharp de-rate a temporary overshoot around a lowered 2026 guide and a contained On-X recall — with On-X/stent-graft/tissue growth and NEXUS restoring the EBITDA trajectory — or the start of an earned, terminal re-rate as recall, leverage and negative LTM FCF impair the franchise?**

### …evidence for
- Constant-currency revenue grew 12% and adjusted EBITDA ~26% in Q1 2026, with On-X +17%, stent grafts +10% and tissue processing +23% — the core growth mechanism remained intact through the drawdown. [10]
- NEXUS FDA approval plus the exercised Endospan option is a dated, mechanism-bearing catalyst that management frames as completing a market-leading aortic-arch portfolio. [28]

### …evidence against
- Management LOWERED full-year 2026 earnings guidance on May-07-2026, the direct trigger of the gap-down and the anchor for the ~82% GAAP-EPS consensus cut. [33]
- The May-23-2026 On-X voluntary recall directly threatens the highest-growth franchise, while 3.7x total-debt/EBITDA leverage and negative LTM FCF (-$7.3M) leave little cushion. [34]

### Key unknowns
- Scope, cost and duration of the On-X voluntary recall (May-23-2026) and whether it impairs the 17%-growth valve franchise — no quantified financial impact is disclosed in the facts.
- Company-adjusted LTM EBITDA and adjusted forward EV/EBITDA are UNKNOWN (not in the revised 99.1 guidance), so leverage on the company's own adjusted basis and a clean forward multiple cannot be verified.
- No segment-level EBITDA is disclosed (only revenue split Products 78% / Preservation Services 22%), an opaque profitability gap — a bearish disclosure gap.
- Whether FY2026 revised guidance ($480–496M revenue; $100–107M adjusted EBITDA) fully embeds the recall and lowered outlook, or leaves further downside — the revised-guidance block itself parsed as UNKNOWN.
- Covenant headroom: financial-maintenance covenants referenced (min interest coverage, max leverage) are from stale/older facilities; the governing terms for the 2031 secured loans are not confirmed against current 3.3x–3.7x leverage.
- Reconciliation of the transcript-stated net leverage 1.8x vs the CIQ-computed net-debt/EBITDA 3.3x — the bases differ (company-adjusted vs GAAP LTM) and the true covenant basis is unresolved.
- Timing and terms of the Endospan close and its incremental debt/dilution, given financing is 'in place' but the full-cost and share impact are not quantified in the facts.
- Data vintage: export date is unverified (a floor ≥ 2026-06-30) and TEV as-of (2026-06-25) is vintage-incoherent with multiple pricing (2026-06-30), flagged for a re-pull.

### Twin reference cases
- **AtriCure** — recovered
  - distinguished by: Small-cap cardiac-device peer that traded on revenue growth and market-share gains through years of thin/negative reported margins, with the market underwriting the franchise ahead of GAAP profitability.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **LeMaitre Vascular** — recovered
  - distinguished by: Vascular-device peer of similar model that compounded on steady share gains and margin expansion, illustrating the path AORT bulls assume for On-X and stent grafts.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **AngioDynamics** — went terminal
  - distinguished by: Small-cap device peer stuck at near-zero/negative EBITDA margin and high leverage, where the multiple stayed distressed because the discount was earned rather than an overshoot.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Penumbra** — recovered (LLM-claimed — verify)
  - distinguished by: Device maker that gapped down hard on a product-safety recall tied to a flagship line, then recovered once the recall proved contained and unit growth resumed.
  - source: [LLM-suggested, unverified]
- **Natus Medical** — went terminal (LLM-claimed — verify)
  - distinguished by: Mid-cap device name where recurring quality/recall issues plus a levered balance sheet steadily eroded the equity story until it was taken private at a depressed value.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-08-06 `[cadence-estimate]` — the next reported quarter against the committed trajectory [39]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 18.4x vs peer median 24.6x (-25%); P/E 91.4x vs peer median 30.7x (+198%) [23]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-06-25 · multiples as-of 2026-06-30 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [40]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **15.66x** | **$81.2M EBITDA †** |
| peer-median NTM TEV/EBITDA | 17.59x | $72.3M EBITDA |
| peer-median LTM TEV/EBITDA | 24.5x | $51.9M EBITDA |
| **name NTM TEV/Rev** | **3.08x** | **$412.9M Revenue †** |
| peer-median NTM TEV/Rev | 2.31x | $550.6M Revenue |
| peer-median LTM TEV/Rev | 2.8x | $454.2M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $94.3M · FY27E $115.5M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $486.2M · FY27E $539.8M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)
  - _⚠ multiple-pricing vintage differs from TEV as-of — re-pull comps (derived FY26 $77.9M vs direct $94.3M, residual 0.174 > 0.10)_

### The EV gap — our base case vs the street

_Anchor FY2026 · consensus as-of ≥2026-06-30 (a FLOOR — the export states no as-of, so the true date is on or after this) · TEV as-of 2026-06-25 · form price-implied-only_

- **Total gap:** **0.94x** — our EV against the market's TEV. No consensus enters this figure.

- **Decomposition suppressed:** our margin is a TERMINAL-state assumption and the consensus at this anchor is a NEAR-TERM forecast; a margin RATIO would mix a view difference with a horizon difference in unknown proportion, so the two margins are shown as figures instead

  - _Our EBITDA margin **14.4%** vs consensus **19.4%** at FY2026 — shown as figures, NOT divided: EBITDA margin, ours converted from the recipe's D&A ratio; consensus = median EBITDA / median revenue at the anchor_

- **Bridge:** our EV $1,195M − net debt $202M = equity $993M ÷ 50.200M sh = **$19.77/sh** — against TEV $1,272M.

  - _Revenue dispersion 2.9% (high−low ÷ |median|, FY2026, as-of ≥2026-06-30)_
  - _EBITDA dispersion 5.8% (high−low ÷ |median|, FY2026, as-of ≥2026-06-30)_

  - _D&A convention: ratio of revenue (R2, terminal) — the two recipes differ and the reconciliation is an open analyst question, so it is stated rather than assumed._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 20.6x as-of 2026-07-17 — trailing range 18.8–75.4x (median 32.1x) over 42 closes → 7%ile → near-floor; P/LTM EPS 104.0x [22]

## Peer comps
- **Peer set (roster · caps · business)** — [41]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| AtriCure | $1.4B | engages in the development, manufacture, and sale of devices for surgical ablation of cardiac tissue, exclusion of the left atrial appendage (United States) |
| LeMaitre Vascular | $2.1B | develops, manufactures, and markets medical devices and implants used in the field of vascular surgery in the Americas, Europe, the Middle Esat, Africa (United States) |
| Edwards Lifesciences Corporation | $51.6B | provides products and technologies to treat advanced cardiovascular diseases in the United States, Europe, Japan, and internationally. (United States) |
| AngioDynamics | $540M | designs, manufactures, and sells medical, surgical, and diagnostic devices for the use in treating peripheral vascular disease (United States) |
| Japan Lifeline Co. | $547M | engages in manufacturing and sale of medical device in Japan. (Japan) |
| Boston Scientific Corporation | $66.1B | develops, manufactures, and markets medical devices for use in various interventional medical specialties worldwide. (United States) |
| CVRx | $137M | engages in developing, manufacturing, and commercializing neuromodulation solutions for patients with cardiovascular diseases in the United States, Germany (United States) |
| PROCEPT BioRobotics Corporation | $1.2B | develops transformative solutions in urology in the United States and internationally. (United States) |
| Accuray Incorporated | $39M | engages in the design, development, manufacture, and sale of radiosurgery and radiation therapy systems for the treatment of tumors in the United States (United States) |
| APT Medical Inc. | $3.9B | engages in the research and development, production, and sale of cardiovascular interventional medical devices in China. (China) |

_the name: $1.1B_

- **Comparability (confidence gate):** market caps span $39M–$66.1B (1682x); the name is $1.1B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [24]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [42]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 2.54 | 0.45 | 2.31 | 3.43 | 7.33 |
| NTM TEV/EBITDA | 12.8 | 5.77 | 17.59 | 22.96 | 74.4 |
| NTM P/E | 161.63 | 10.13 | 26.73 | 59.98 | 253.41 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [43]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Boston Scientific Corporation | $66.1B | 13.8 | 3.7 | 18.6 | 27% | 17% | 2.0 | 9,576 |
| Edwards Lifesciences Corporation | $51.6B | 25.2 | 7.7 | 48.6 | 30% | 14% | 0.4 | 2,989 (net cash) |
| APT Medical Inc. | $3.9B | 23.9 | 9.3 | 30.7 | 39% | 25% | 0.0 | 188 (net cash) |
| LeMaitre Vascular | $2.1B | 23.2 | 7.5 | 33.9 | 31% | 13% | 2.3 | 177 (net cash) |
| AtriCure | $1.4B | 68.7 | 2.5 | NM | 3% | 15% | 3.8 | 71 (net cash) |
| PROCEPT BioRobotics Corporation | $1.2B | NM | 3.2 | NM | -32% | 29% | NM | 168 (net cash) |
| **Artivion · the name** | **$1.1B** | **18.4** | **2.8** | **91.4** | **13%** | **18%** | **3.7** | **202** |
| Japan Lifeline Co. | $547M | 5.7 | 1.3 | 9.5 | 24% | 5% | 0.2 | 58 (net cash) |
| AngioDynamics | $540M | 288.9 | 1.6 | NM | 0% | 11% | 6.4 | 26 (net cash) |
| CVRx | $137M | NM | 2.1 | NM | -83% | 12% | NM | 13 (net cash) |
| Accuray Incorporated | $39M | 29.8 | 0.4 | NM | -1% | -8% | 46.2 | 144 |
| Peer median (peers) | $1.3B | 24.6 | 2.9 | 30.7 | 13% | 14% | 2.1 | 65 (net cash) |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [30]  <!-- ds-table -->

|  | Dec-2016 | Dec-2017 | Dec-2018 | Dec-2019 | Dec-2020 | Dec-2021 (R) | Dec-2022 | Dec-2023 (R) | Dec-2024 (R) | Dec-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 68% | 69% | 67% | 66% | 66% | 66% | 65% | 65% | 64% | 64% | 65% |

_Revenue YoY (latest same-quarter): +50.7% (Q1 Mar-31-2026 vs Q1 Mar-31-2022). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** diluting (trailing ~1.7y): 41,893,465 (2024-08-02) → 48,543,350 (2026-05-01), +15.9% [38]
- **Return ratios — per fiscal period** — [44]  <!-- ds-table -->

|  | FY16 | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | 5.9% | 1.5% | -1.0% | 0.6% | -5.4% | -4.7% | -6.6% | -10.8% | -4.8% | 2.7% | 3.1% |
| RoCE % | 4.8% | 1.7% | 1.5% | 2.1% | 0.7% | 0.1% | -0.3% | -0.8% | 2.7% | 2.9% | 3.5% |
| RoA % | 4.2% | 1.5% | 1.3% | 1.8% | 0.6% | 0.1% | -0.2% | -0.7% | 2.2% | 2.3% | 2.8% |
| Total debt/equity | 0.34x | 0.82x | 0.81x | 0.86x | 0.97x | 1.20x | 1.25x | 1.27x | 1.31x | 0.58x | 0.57x |
| Current ratio | 4.89x | 4.18x | 5.19x | 4.15x | 3.88x | 5.51x | 4.98x | 4.85x | 4.34x | 3.53x | 3.86x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-06-30)_
- **Horizon read (FQ — next-2Q revision breadth)** — [45]:
  - EPS (GAAP) FQ2 2026: 1m 0↑/1↓, 2m 0↑/3↓, 3m 0↑/7↓
  - EPS (GAAP) FQ3 2026: 1m 0↑/1↓, 2m 0↑/3↓, 3m 0↑/7↓
  - EPS Normalized FQ2 2026: 1m 0↑/0↓, 2m 0↑/2↓, 3m 0↑/5↓
  - EPS Normalized FQ3 2026: 1m 0↑/0↓, 2m 0↑/2↓, 3m 0↑/5↓
  - Revenue FQ2 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/7↓
  - Revenue FQ3 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/7↓
  - EBITDA FQ2 2026: 1m 0↑/1↓, 2m 0↑/2↓, 3m 0↑/6↓
  - EBITDA FQ3 2026: 1m 0↑/1↓, 2m 0↑/2↓, 3m 0↑/6↓
  - EBIT FQ2 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/6↓
  - EBIT FQ3 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/6↓
  - _+7 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS (GAAP): 0.45 (12m) → 0.40 (9m) → 0.45 (6m) → 0.36 (3m) → 0.14 (2m) → 0.10 (1m) → 0.08 (latest); net -82% (12m→latest) | FY 2026 EPS Normalized: 0.86 (12m) → 0.84 (9m) → 0.84 (6m) → 0.81 (3m) → 0.49 (2m) → 0.44 (1m) → 0.44 (latest); net -49% (12m→latest) | FY 2026 Revenue: 473.0 (12m) → 485.4 (9m) → 490.2 (6m) → 494.1 (3m) → 486.4 (2m) → 486.4 (1m) → 486.2 (latest); net +3% (12m→latest) | FY 2026 EBITDA: 101.9 (12m) → 104.7 (9m) → 106.5 (6m) → 106.1 (3m) → 96.5 (2m) → 95.3 (1m) → 94.3 (latest); net -7% (12m→latest) | FY 2026 EBIT: 50.6 (12m) → 49.5 (9m) → 50.1 (6m) → 44.6 (3m) → 33.7 (2m) → 33.7 (1m) → 32.6 (latest); net -36% (12m→latest) | FY 2026 Interest Expense: -28.6 (12m) → -25.9 (9m) → -25.2 (6m) → -22.7 (3m) → -27.3 (2m) → -28.5 (1m) → -28.4 (latest); improving (magnitude toward zero) (12m→latest) | FY 2026 EBT (GAAP): 25.3 (12m) → 25.5 (9m) → 25.9 (6m) → 23.1 (3m) → 7.59 (2m) → 6.37 (1m) → 5.32 (latest); net -79% (12m→latest) | FY 2026 Net Income (Excl. Excep): 38.6 (12m) → 40.0 (9m) → 42.3 (6m) → 40.5 (3m) → 24.6 (2m) → 22.0 (1m) → 22.0 (latest); net -43% (12m→latest) | FY 2026 Net Income (GAAP): 21.4 (12m) → 20.4 (9m) → 21.7 (6m) → 19.1 (3m) → 6.15 (2m) → 5.11 (1m) → 4.40 (latest); net -79% (12m→latest)  [data ≥ 2026-06-30 · export date unverified] [35]
- **Cross-name anchor (NTM forward-multiple ladder)** — [37]:
  - NTM: TEV/REV 3.08 · TEV/EBITDA 15.66 · TEV/EBIT 39.58 · Price/Earnings 222.54 · PEG –
  - FY 2026: TEV/REV 3.17 · TEV/EBITDA 16.33 · TEV/EBIT 47.27 · Price/Earnings – · PEG –
  - FY 2027: TEV/REV 2.85 · TEV/EBITDA 13.33 · TEV/EBIT 26.42 · Price/Earnings 67.61 · PEG –
  - FY 2028: TEV/REV 2.56 · TEV/EBITDA 11.03 · TEV/EBIT 19.17 · Price/Earnings 34.87 · PEG –
  - _+2 later fiscal years in JSON_
- **Current guide (latest results filing):** revenue 2026: 480.0–496.0 $M; adjusted ebitda 2026: 100.0–107.0 $M [46]
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [47]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| EPS Normalized | '0.28 - 0.32' | FY 2019 | 2019-10-30 | 2441d (stale) | actual ≥ floor 5/7 | FY 2019 MET |
| Revenue | '480.00 - 496.00' | FY 2026 | 2026-05-07 | 60d (stale) | actual ≥ floor 28/41 | FY 2025 MET |
| EBITDA | '100.00 - 107.00' | FY 2026 | 2026-05-07 | 60d (stale) | actual ≥ floor 3/4 | FY 2025 MET |
| Capital Expenditure | -50.0 | FY 2026 | 2026-02-12 | 144d (stale) | — | — |
| Gross Margin % | 64.9 | FY 2026 | 2026-02-12 | 144d (stale) | actual ≥ floor 3/6 | FY 2024 MISSED |

- **Consensus stats (target + ratings):** Target price: mean $42.00, median $43.00, high/low 48.00/36.00, N 8/8; Ratings: Buy 6, Outperform 2, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-06-30 · export date unverified] [25]
- **Revision-event log (250 events · 17 broker-days)** — [48]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-06-30 | Ladenburg Thalmann & Company | 20 | 1 | 17 | 2 | EBITDA FQ2 2026 | 25.6 | 22.5 | −3.0 |
| 2026-06-23 | Needham & Company | 13 | — | 13 | — | EBITDA FY 2026 | 100.3 | 91.8 | −8.5 |
| 2026-06-09 | Lake Street Capital Markets, LLC | 12 | — | 12 | — | EPS Normalized FQ2 2026 | 0.1 | 0.1 | −0.05 |
| 2026-05-20 | Freedom Capital Markets | 29 | — | 29 | — | EBITDA FQ2 2026 | 29.4 | 24.1 | −5.3 |
| 2026-05-08 | Citizens JMP Securities, LLC | 21 | — | 21 | — | EBITDA FQ2 2026 | 26.4 | 22.0 | −4.4 |
| 2026-05-08 | Freedom Capital Markets | 9 | — | — | 9 | — | — | — | — |

_+11 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2004 +0%, FY2005 +0%, FY2006 +0%, FY2007 +24%, FY2008 +152%, FY2009 +3%, FY2010 +0%, FY2011 +0%, FY2012 +4%, FY2013 -5%, FY2014 +4%, FY2015 +56%, FY2016 +7%, FY2017 -62%, FY2018 +0%, FY2019 -44%, FY2020 +0%, FY2021 +0%, FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 -9%; Revenue surprise: FY2000 -3%, FY2001 -1%, FY2002 -2%, FY2003 -1%, FY2004 +0%, FY2005 +0%, FY2006 +0%, FY2007 +0%, FY2008 -2%, FY2009 -0%, FY2010 -0%, FY2011 -1%, FY2012 -0%, FY2013 +0%, FY2014 -0%, FY2015 -0%, FY2016 -1%, FY2017 +2%, FY2018 +0%, FY2019 -0%, FY2020 +1%, FY2021 +1%, FY2022 -0%, FY2023 +1%, FY2024 -1%, FY2025 -0% (GAAP-EPS basis; +beat / −miss) [49]

## Leverage & survival
- **Net debt / EBITDA [NET]:** 3.3x [8]
- **Total debt / EBITDA vs peers:** name 3.7x vs peer median 2.1x (comps TOTAL-debt/EBITDA basis) [11]
- **Net debt / OCF:** 3.5x [50]
- **Interest coverage:** 2.5x [51]
- **Self-funding:** self-funding: MIXED — latest-Q OCF > 0, LTM FCF < 0 (both must be positive to self-fund) [52]
- **Credit health** — [13]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 4 | 2.5 |
| Operational | 3 | 2.5 |
| Solvency | 3 | 2.5 |
| Liquidity | 4 | 2.5 |

_S&P issuer rating NR · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [9]
- **Free cash flow ($M):** -7.3 [12]
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Feb-18-2026** — [53]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Convertible Senior Notes | Bonds and Notes | – | 4.250% | NA | 2025-07-01 | N | Y | USD |
| Notes Payable | Bonds and Notes | $0.9M | 6.050% | NA | 2026-04-01 | N | N | USD |

_6 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-07-06 reference:
  - **matured (pre-reference): $0.9M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2025-07-01 (370d before ref): – Convertible Senior Notes
    - 2026-04-01 (96d before ref): $0.9M Notes Payable
  - due 2031: $220.0M
  - undated (floor — no panel maturity): $42.5M — 1.40% Sparkasse Zollernalb KFW… –, Finance Lease Obligation $3.4M, Operating Lease Liabilities $39.1M
  - _reconciliation: itemized $263.4M (panel A 2025 filed Feb-18-2026) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** term loans 190.0 (190.0→190.0 QoQ); leases 42.8; total principal 262.8; total debt 258.2 (latest quarter) ($M) [54]
- **Covenants — Convertible Senior Notes** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LIBOR + 3.50% · Base Rate + Applicable Margin, or LIBOR + Applicable Margin; Term Loan and Revolving: 2.50% (Base Rate Loans) / 3.50% (…
  - **Maturity:** Term Loan: term of five years; Revolving Credit Facility: fifth anniversary of the Closing Date
  - **Financial maintenance:** Minimum interest coverage of 3.00:1.00; and maximum total leverage multiple (levels to be agreed, reflecting cushion to…
  - **Events of default:** Mandatory prepayments: (a) 50% of Excess Cash Flow (25% at total leverage 2.50x, 0% at 1.50x); (b) 100% of net cash pro…
- **Covenants — Secured Revolving Credit Facility** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LIBOR or Base Rate plus the Applicable Margin. "Applicable Margin" means: (a) for the period commencing on the Closing…
  - **Maturity:** January 20, 2021 · Revolving Termination Date: earlier of (a) January 20, 2021 and (b) date Aggregate Revolving Loan Commitment terminates…
  - **Financial maintenance:** Maximum Leverage Ratio (stepping down from 3.50:1.00 to 2.75:1.00); Minimum Interest Coverage Ratio of 3.00:1.00; Equit…
  - **Events of default:** Mandatory prepayments from asset dispositions/events of loss (Net Proceeds over $1,500,000/Fiscal Year), incurrence of…

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [55]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [56]
  - net debt / EBITDA (CIQ, GAAP basis): 3.3x
  - total debt / EBITDA (CIQ comps, GAAP basis): 3.7x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage

## ⚠ Analyst caveats — verify before the verdict

_3 to verify._

- P/E may be distorted by non-recurring EPS — latest annual EPS 0.21 vs recent median -0.54; verify against normalized/forward EPS (CIQ)
- Net debt/EBITDA (3.3x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 3.3x as the covenant-basis leverage.
- **Distorted-P/E anchor** — EV/EBITDA (TEV/LTM) sits at 20.6x, ~7th percentile of its own 42-quarter range (median 32.1x), a near-floor own-history reading that poses the overshoot question.
  - _where:_ a bull point
  - _why it matters:_ the P/E is distorted (rests on a non-current/non-recurring EPS)
  - _how to verify:_ don't read it as cheap

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

Terminal revenue starts from the street's FY2027 figure and then fades at a stated rate of about 1.5 points of growth a year in the central case. Only FY2026 and FY2027 are street figures; everything beyond is our own extrapolation, and the realized growth record is lumpy rather than a smooth curve because acquisitions and the 2020 shutdown both sit inside it.

| reference | value |
| --- | ---: |
| street revenue, FY2026 | $486.4M [57] |
| street revenue, FY2027 | $540M [57] |
| reported revenue, FY2025 | $441.3M [58] |
| company revenue guidance, FY2026 low end | $480M [59] |
| company revenue guidance, FY2026 high end | $496M [59] |

### Margin · **DRAFT — not ratified by the analyst**

Every margin here is on a reported accounting basis, and so is the depreciation assumption, because the two must sit in the same layer. The street's 'EBITDA' figures are not: they imply about $62M of depreciation for a year in which the company reported about $22M, so converting them at our depreciation rate would overstate the operating margin by roughly eight points. The honest street references are its own stated operating-profit rows, 6.93% for FY2026 and 10.80% for FY2027. The realized record is the harder evidence: the best year on file, FY2024 at 10.01%, came from spending FALLING 11.7% in absolute dollars, and the following year gave 2.4 points back as spending grew 22.7% against 13.6% revenue. Operating leverage ran backwards in the latest year, which is why the central case sits below next year's street figure rather than on it.

| reference | value |
| --- | ---: |
| reported operating margin, FY2024 - best year on file | 10.01% [60] |
| operating expenses, FY2024 - the reason for that year | -11.7% [61] |
| reported operating margin, FY2025 | 7.65% [60] |
| operating expenses, FY2025 - leverage running backwards | 22.7% [61] |
| realized two-year mean operating margin | 8.83% [62] |
| street operating margin, FY2026 - stated, not derived | 6.93% [63] |
| street operating margin, FY2027 - stated, not derived | 10.8% [63] |
| depreciation implied by the street layer, FY2026 | $61.6M [64] |
| depreciation reported, FY2025 | $22.458M [65] |
| earnings revision breadth, next two quarters | -7count [66] |
| street full-year earnings revision over twelve months | -78% [67] |

### Multiple · **DRAFT — not ratified by the analyst**

The exit multiple is paired to the margin the leg actually reaches, not taken from a peer whose economics the leg does not model. Mature device businesses earning about twice our terminal margin trade near 14x, and every one of them carries net cash while this company carries three and a half turns of debt - so the central case exits just below that level and the pessimistic case well below it. This company's own trading history is the longest series available and both data-quality checks pass on it, but its median spans years when earnings were near zero, which inflates a multiple without saying anything about value; the current and low readings are the usable part. For orientation: breaking even against the price would need roughly 15 to 17 percent operating margins at that historical floor multiple.

| reference | value |
| --- | ---: |
| mature device business, enterprise value to EBITDA | 13.8x [68] |
| mature device business, closest in size, net cash | 23.2x [69] |
| this company's trailing current reading, seventh percentile | 20.6x [70] |
| this company's trailing low | 18.8x [70] |
| this company's trailing median - spans near-zero-earnings years | 32.1x [70] |
| peer median, heterogeneous ten-name set | 24.6x [71] |

### Horizon · **DRAFT — not ratified by the analyst**

Four years to the terminal year, matching the first record on this recipe so the two are comparable. Three years would require the margin recovery to complete almost immediately after a recall and a guidance cut; five would let the waiting charge halve the answer, leaving the exit multiple rather than the operating case to carry it.

| reference | value |
| --- | ---: |
| years to the terminal year | 4years [72] |
| waiting charge applied over the horizon | 74.9% [73] |


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-06-30)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [14]  <!-- ds-table -->

|  | FY16 | FY17 | FY18 | FY19 | FY20 | FY21 (R) | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 180 | 190 | 263 | 276 | 253 | 299 | 314 | 354 | 389 | 441 | 459 | 486 | 540 |
| Revenue growth | — | +5% | +39% | +5% | -8% | — (basis) | — (basis) | — (basis) | +10% | — (basis) | — (basis) | +10% (vs FY25) | +11% |
| EBITDA ($M) | 25 | 20 | 30 | 35 | 28 | 25 | 20 | 15 | 52 | 54 | 61 | 94 | 116 |
| EBITDA margin | 14% | 11% | 11% | 13% | 11% | 8% | 6% | 4% | 13% | 12% | 13% | 19% | 21% |
| EBIT ($M) | 17 | 11 | 12 | 17 | 7 | 1 | -3 | -8 | 28 | 31 | 38 | 33 | 58 |
| Net income ($M) | 11 | 4 | -3 | 2 | -17 | -15 | -19 | -31 | -13 | 10 | 12 | 4 | 23 |
| EPS (GAAP, dil.) | 0.32 | 0.11 | -0.08 | 0.05 | -0.44 | -0.38 | -0.48 | -0.75 | -0.32 | 0.21 | 0.24 | 0.08 | 0.41 |
| EPS (Normalized) | 0.26 | 0.11 | -0.06 | 0.03 | -0.21 | -0.35 | -0.37 | -0.55 | -0.22 | 0.20 | 0.26 | 0.44 | 0.72 |
| Merger & Related Restruct. Charges ($M) | -3 | -3 | -3 | — | — | — | — | — | — | — | — | — | — |
| Gain (Loss) On Sale Of Assets ($M) | 8 | — | — | — | — | 16 | — | 14 | — | 7 | 7 | — | — |
| Insurance Settlements ($M) | — | — | — | — | — | — | — | — | — | 3 | 5 | — | — |
| Other Unusual Items ($M) | — | — | — | — | -4 | -9 | 9 | — | 7 | -10 | -15 | — | — |
| CFO ($M) | 20 | 11 | 10 | 16 | 12 | -3 | -5 | 19 | 22 | 40 | 58 | — | — |
| Capex ($M) | -6 | -7 | -6 | -8 | -7 | -13 | -11 | -10 | -11 | -39 | -43 | — | — |
| FCF (levered, CIQ) | 4 | -18 | 9 | -4 | 5 | -21 | 0 | -4 | 0 | -20 | -7 | — | — |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-06-30; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_


> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 59 of D&A against 22 in the actuals (2.65x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.

### Quarterly — every exported quarter
- **Quarterly financials** — [74]  <!-- ds-table -->

|  | Q1-16 | Q2-16 | Q3-16 | Q4-16 | Q1-17 | Q2-17 (R) | Q3-17 (R) | Q4-17 (R) | Q1-18 | Q2-18 | Q3-18 (R) | Q4-18 (R) | Q1-19 | Q2-19 | Q3-19 (R) | Q4-19 (R) | Q1-20 | Q2-20 | Q3-20 | Q4-20 | Q1-21 | Q2-21 | Q3-21 (R) | Q4-21 (R) | Q1-22 | Q2-22 | Q3-22 (R) | Q4-22 (R) | Q1-23 (R) | Q2-23 | Q3-23 (R) | Q4-23 (R) | Q1-24 (R) | Q2-24 | Q3-24 (R) | Q4-24 (R) | Q1-25 (R) | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 43 | 47 | 45 | 45 | 45 | 48 | 44 | 53 | 62 | 68 | 65 | 68 | 68 | 71 | 68 | 70 | 66 | 54 | 65 | 68 | 71 | 76 | 72 | 79 | 77 | 80 | 77 | 79 | 83 | 89 | 88 | 94 | 97 | 98 | 96 | 97 | 99 | 113 | 113 | 116 | 116 |
| Gross margin | 66% | 66% | 67% | 71% | 70% | 69% | 68% | 74% | 66% | 69% | 66% | 67% | 66% | 66% | 67% | 67% | 66% | 67% | 66% | 66% | 67% | 66% | 66% | 65% | 66% | 65% | 63% | 64% | 65% | 65% | 64% | 65% | 65% | 65% | 64% | 63% | 64% | 65% | 66% | 63% | 65% |
| EBITDA ($M) | 7 | 9 | 9 | 1 | 7 | 7 | 3 | 6 | 2 | 11 | 11 | 0 | 7 | 11 | 9 | 9 | 4 | 3 | 9 | 12 | 8 | 11 | 6 | 1 | 6 | 7 | 2 | 5 | 7 | 10 | 11 | 11 | 14 | 14 | 14 | 10 | 5 | 17 | 17 | 15 | 12 |
| EBITDA margin | 16% | 19% | 19% | 2% | 15% | 15% | 7% | 11% | 4% | 17% | 17% | 0% | 10% | 15% | 14% | 12% | 6% | 5% | 14% | 18% | 12% | 14% | 8% | 1% | 7% | 9% | 2% | 7% | 8% | 11% | 12% | 11% | 14% | 14% | 15% | 11% | 5% | 15% | 15% | 13% | 11% |
| Revenue QoQ | — | +9% | -4% | -0% | +0% | — (basis) | -8% | +20% | — (basis) | +11% | — (basis) | +5% | — (basis) | +5% | — (basis) | +3% | — (basis) | -19% | +21% | +4% | +5% | +7% | — (basis) | +10% | — (basis) | +4% | — (basis) | +3% | +5% | — (basis) | — (basis) | +7% | +4% | — (basis) | — (basis) | +2% | +2% | — (basis) | +0% | +2% | +0% |
| Revenue YoY | — | — | — | — | +5% | — (basis) | — (basis) | — (basis) | +37% | — (basis) | +47% | +28% | +9% | +4% | +5% | +3% | -2% | -24% | — (basis) | — (basis) | +7% | +42% | — (basis) | — (basis) | +9% | +6% | +6% | +0% | — (basis) | +11% | +14% | +18% | +17% | +10% | +9% | +4% | +2% | +15% | — (basis) | — (basis) | — (basis) |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q1-26 ($M): cash & ST inv 56; total debt 258; net debt 202; equity 450; net working capital 265; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [75]
- **Coherence — BS vs implied-valuation bridge:** cash BS $56M / bridge $56M; debt BS $258M / bridge $258M — reconcile with the implied-valuation bridge. [76]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Feb-18-2026** — [53]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank | Term Loans | – | 1.400% | NA | undated | N | N | USD |
| Convertible Senior Notes | Bonds and Notes | – | 4.250% | NA | 2025-07-01 | N | Y | USD |
| Finance Lease Obligation | Capital Lease | $3.4M | 2.400% | NA | undated | Y | N | USD |
| New Delayed Draw Term Loan Facility | Term Loans | – | NA | SOFR + 4.750% | 2031-01-18 | Y | N | USD |
| Notes Payable | Bonds and Notes | $0.9M | 6.050% | NA | 2026-04-01 | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $39.1M | 5.900% | NA | undated | Y | N | USD |
| Secured Revolving Credit Facility | Revolving Credit | $30.0M | 7.160% | SOFR + 3.500% | 2031-01-18 | Y | N | USD |
| Secured Term Loan Facility | Term Loans | $190.0M | 8.410% | SOFR + 4.750% | 2031-01-18 | Y | N | USD |

- **8-Ks at instrument maturities:** _UNKNOWN_ — no 8-K within ±10d of a trailing-12m maturity (2026-04-01)
- **Covenant / contract pointers (CIK-verified execution filings)** — [77]  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank | 8-K | 2026-05-18 | 0001628280-26-035798 — aort-2026x8k03312026ex101.htm, aort-2026x8k03312026ex102.htm, aort-2026x8k03312026ex103.htm |
| 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank | 8-K | 2026-05-07 | 0001628280-26-032097 — aort-2026x8k033126ex101.htm, aort-2026x8k033126ex102.htm, aort-2026x8k033126ex103.htm |
| Convertible Senior Notes | 8-K | 2015-12-23 | 0000784199-15-000171 — c199-20151222ex101949499.htm |
| Convertible Senior Notes | 8-K | 2025-09-15 | 0000784199-25-000145 — ex101.htm |
| New Delayed Draw Term Loan Facility | 8-K | 2017-12-01 | 0001398344-17-015456 — fp0029473_ex101.htm |
| Secured Revolving Credit Facility | 8-K | 2016-01-25 | 0000784199-16-000175 — c199-20160125ex101fad737.htm, c199-20160125ex1021c6f6c.htm |
| Finance Lease Obligation | — | — | no contract-level filing expected (aggregate line item) |
| Notes Payable | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank (governing agreement)** — [78]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Principal / commitment amount | Buyer Loan up to $15 million, funded in tranches; Initial Loan Tranche of $5,000,000 | amended by 0001628280-26-035798 |
| Interest / coupon rate | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Maturity date | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Security / collateral / guarantors | Debenture granting Buyer a perfected security interest in all of the Company's assets (other than the Horizon Assets), junior in priority to JLL's charge under the JLL Loan | amended by 0001628280-26-035798 |
| Mandatory prepayment / events of default | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Buyer Option / purchase right | Buyer Option to purchase 100% (but not less than 100%) of the Company Securities or the Acquired Assets | 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Option Fee | $1,000,000 payable within fourteen (14) Business Days of the Effective Time | 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Base Amount / Closing Consideration | Base Amount = $250,000,000 in cash | 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Additional Consideration Amount | Greater of Additional Consideration Minimum Amount ($100,000,000) or 5x revenue growth; capped at $200,000,000 | amended by 0001628280-26-035798 |
| Indemnity Escrow Amount | $23,500,000 plus Additional Indemnity Escrow Amount | amended by 0001628280-26-035798 |
| Adjustment Escrow Amount | $1,000,000 | amended by 0001628280-26-035798 |
| Governing law | State of Delaware | amended by 0001628280-26-035798 |
| Closing timing | 12:01 a.m. Eastern Time ninety (90) days following delivery of the Exercise Notice | 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Buyer Option Fee | $1,000,000 payable within fourteen (14) Business Days of the Effective Time | base (footer) |
| Acquisition Consideration / Base Amount | Base Amount of $250,000,000 in cash | base (footer) |
| Termination provisions | Termination by mutual consent; by Company or Buyer for breach; upon Governmental Authority Restriction; expiration/termination of Distribution Agreement; failure to fund loan tranches; and other cond… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0001628280-26-032097 · aort-2026x8k033126ex101.htm · amended by 0001628280-26-035798_

- **Covenant terms — Convertible Senior Notes (governing agreement)** — [78]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0000784199-15-000171 · c199-20151222ex101949499.htm |
| Principal / commitment amount | $95,000,000 total (Term Loan Facility $75,000,000; Revolving Credit Facility $20,000,000; commitments: HFS $40,000,000, Fifth Third $40,000,000, Citizens $15,000,000) | base (footer) |
| Interest / coupon rate | LIBOR + 3.50% · Base Rate + Applicable Margin, or LIBOR + Applicable Margin; Term Loan and Revolving: 2.50% (Base Rate Loans) / 3.50% (LIBOR Loans), subject to Pricing Grid | base (footer) |
| Maturity date | Term Loan: term of five years; Revolving Credit Facility: fifth anniversary of the Closing Date | base (footer) |
| Financial-maintenance covenants | Minimum interest coverage of 3.00:1.00; and maximum total leverage multiple (levels to be agreed, reflecting cushion to financial model of 25% to 30%) | base (footer) |
| Security / collateral / guarantors | First priority perfected security interests in substantially all existing and after-acquired real and personal property of Borrowers and each Guarantor, including 100% of outstanding equity interests… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | Mandatory prepayments: (a) 50% of Excess Cash Flow (25% at total leverage 2.50x, 0% at 1.50x); (b) 100% of net cash proceeds of debt issuances; (c) 100% of net cash proceeds of asset sales. Events of… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0000784199-15-000171 · c199-20151222ex101949499.htm_

- **Covenant terms — Secured Revolving Credit Facility (governing agreement)** — [78]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0000784199-16-000175 · c199-20160125ex101fad737.htm |
| Principal / commitment amount | $95,000,000 credit facility, consisting of Aggregate Term Loan Commitment of $75,000,000 and Aggregate Revolving Loan Commitment of $20,000,000 (as of the Closing Date) | base (footer) |
| Interest / coupon rate | LIBOR or Base Rate plus the Applicable Margin. "Applicable Margin" means: (a) for the period commencing on the Closing Date through the ... First Grid Calculation Date ...: (i) if a Base Rate Loan, t… — full verbatim in JSON — ⚠ QA: rate component 0 not stated in the clause — lead suppressed | base (footer) |
| Maturity date | January 20, 2021 · Revolving Termination Date: earlier of (a) January 20, 2021 and (b) date Aggregate Revolving Loan Commitment terminates. Term Loan final scheduled installment of $56,250,000.00 due January 20, 2021 | base (footer) |
| Financial-maintenance covenants | Maximum Leverage Ratio (stepping down from 3.50:1.00 to 2.75:1.00); Minimum Interest Coverage Ratio of 3.00:1.00; Equity Cure right (Section 7.3) | base (footer) |
| Security / collateral / guarantors | Secured by Liens on Collateral (all Property of Credit Parties) pursuant to the Guaranty and Security Agreement and Collateral Documents; guaranteed by Credit Parties (Domestic Subsidiaries other tha… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | Mandatory prepayments from asset dispositions/events of loss (Net Proceeds over $1,500,000/Fiscal Year), incurrence of debt/specified equity raises, and Excess Cash Flow (50%/25%/0% based on Leverage… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0000784199-16-000175 · c199-20160125ex101fad737.htm_

- _2 located agreement exhibit(s) not extracted this run (cost bound / fetch fail) — see the pointer table: 0000784199-25-000145, 0001398344-17-015456_

### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 1069.4 [79]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $55.80M, − total debt $258.20M [80]
- **Implied equity at peer-median ($M, CIQ)** — [81]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 1,303.9 |
| NTM Revenue (Capital IQ) | 951.5 |
| NTM EBITDA (Capital IQ) | 1,545.3 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [82]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 0 · sells 27 (7 insiders, $5.89M) — in the last 182 days · last purchase $0.04M, director, 2025-03-05 (~17mo ago) · last sale $0.29M, SVP, Regulatory and Quality, 2026-06-11 (~2mo ago) · largest sale $1.75M, President & CEO, 2025-03-06 (~17mo ago) · grants 85 · last filing 2026-06-15 · other filings 31 [83]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-06-30): 1.9M → 2.2M sh (+15.4%, rising) · 4.5% of shares out (EDGAR XBRL) · DTC 2.7d · recent: 2026-06-30 2.2M · 2026-06-15 1.9M · 2026-05-29 1.9M · 2026-05-15 1.9M [84]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [85]
- **Guide verification — CIQ guide vs release:** revenue: CIQ 480.0–496.0 vs release 480.0–496.0 → cross-source VERIFIED [86]

## Record & reproduce
- **Data window:** screened as of 2026-07-06 · assembled 2026-07-30 11:36 UTC
- **Extraction:** 2026-07-28.1 — unusual-items surfacing in the financial summary (#238) · multiples read from the latest close, NM rather than a stale figure (#241)
- **Panel age:** oldest panel 35d old — 2026-06-25 (valuation.implied_expectations.tev_as_of), against a 2026-07-30 build
- **Consensus age:** consensus 30d old (2026-06-30, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0000784199` · NYSE : AORT
- **Assembly log:** primary-source: 6 EX-99.1 release(s) + 1 10-Q parsed (+1.1s fetch)
- **Re-run:** `python -m vinci dossier --ticker AORT` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[5] `EOD AORT 180d to 2026-07-06`
[6] `EOD IWM 180d to 2026-07-06 (cap-band: $1.1B @ 2026-07-06 → small (<$4B) → IWM)`
[7] `EOD AORT−IWM 180d to 2026-07-06 (assembly, cap-band)`
[8] `CIQ Net Debt $202M [Q1 Mar-31-2026] ÷ CIQ EBITDA $61M [LTM 12 months Mar-31-2026]`
[9] `EDGAR XBRL FCF sign (screen data-record)`
[10] `CIQ transcript: Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`
[11] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-06-25`
[12] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
[13] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-06-25`
[14] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[15] `EDGAR companyfacts Goodwill (as at 2026-06-30)`
[16] `EDGAR companyfacts IntangibleAssetsNetExcludingGoodwill (as at 2018-09-30)`
[17] `EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2014-01-01→2014-12-31, 364d)`
[18] `EDGAR companyfacts TreasuryStockSharesAcquired (2014-01-01→2014-12-31, 364d)`
[19] `EDGAR companyfacts PaymentsToAcquireBusinessesNetOfCashAcquired (2026-01-01→2026-06-30, 180d)`
[20] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[21] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[22] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[23] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[24] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[25] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[26] `8-K 0001628280-26-032097 EX-99.1`
[27] `CIQ Customers&Suppliers Artivion Inc NYSE AORT Customers.rtf`
[28] `CIQ Key Developments: Artivion Inc NYSE AORT Key Developments.rtf · Apr-07-2026`
[29] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[30] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[31] `CIQ Estimates→Consensus`
[32] `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 42 quarters (partial last column excluded from the distribution)`
[33] `CIQ Key Developments: Artivion Inc NYSE AORT Key Developments.rtf · May-07-2026`
[34] `CIQ Key Developments: Artivion Inc NYSE AORT Key Developments.rtf · May-23-2026`
[35] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[36] `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
[37] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[38] `EDGAR XBRL shares, trailing 2024-08-02..2026-05-01`
[39] `cadence: EDGAR submissions (median 91d gap over 42 results 8-Ks; last print 2026-05-07)`
[40] `TEV = mcap 1069.4 + net debt 202.4 (CIQ Comparable Analysis→Financial Data, Latest, as-of 2026-06-25) — simple-TEV basis`
[41] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[42] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[43] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-06-25`
[44] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[45] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[46] `8-K 0001628280-26-032097 EX-99.1 (filed 2026-05-07)`
[47] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record)`
[48] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-06-30 · export date unverified]`
[49] `CIQ Estimates→Surprise (annual)`
[50] `CIQ Net Debt $202M [Q1 Mar-31-2026] ÷ CIQ OCF $58M [LTM 12 months Mar-31-2026]`
[51] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
[52] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[53] `CIQ Financials→Capital Structure Details (A 2025 filed Feb-18-2026)`
[54] `CIQ Financials→Capital Structure Summary`
[55] `10-Q 0001628280-26-032620`
[56] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[57] `CIQ Estimates->Trends`
[58] `EDGAR RevenueFromContractWithCustomerExcludingAssessedTax`
[59] `CIQ guidance bridge, dated 2026-05-07`
[60] `EDGAR OperatingIncomeLoss / revenue`
[61] `EDGAR OperatingExpenses, year on year`
[62] `EDGAR, FY2024 and FY2025`
[63] `CIQ Estimates->Trends (EBIT row)`
[64] `CIQ Estimates->Trends (EBITDA less EBIT)`
[65] `EDGAR companyfacts dep_amort`
[66] `CIQ Estimates->Revisions (0 upward / 7 downward)`
[67] `CIQ Estimates->Trends (FY2026 reported EPS path)`
[68] `CIQ Comparable Analysis (Boston Scientific, 26.7% EBITDA margin)`
[69] `CIQ Comparable Analysis (LeMaitre Vascular, 30.7% EBITDA margin)`
[70] `CIQ Financials->Multiples (42 closes; both checks pass)`
[71] `CIQ Comparable Analysis (set spans $39M to $66.1B)`
[72] `analyst judgement`
[73] `house rate of 15% a year compounded over four years`
[74] `CIQ Financials→Income Statement (quarterly, full exported history)`
[75] `CIQ Financials→Balance Sheet (quarterly, Q1-26)`
[76] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[77] `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`
[78] `fenced Tier-2 extraction (verbatim, source-bound)`
[79] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-25`
[80] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-06-25`
[81] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-06-25`
[82] `CIQ transcript(s): Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf`
[83] `EDGAR Form 4 (latest 0001628280-26-043059; 166 filings in the 1095d scanned; counts over 182d)`
[84] `FINRA consolidated short interest (settle 2026-06-30); DTC = 2,179,918 short ÷ 795,826 screen 90d ADV`
[85] `10-Q maturity wall vs CIQ capital panel (same window)`
[86] `CIQ revenue guide vs release actual/outlook`