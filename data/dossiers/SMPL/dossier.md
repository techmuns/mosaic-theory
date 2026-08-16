# Dossier — Simply Good Foods Co (Nasdaq: SMPL)

_August 13, 2026 · extraction 2026-07-28.1_

# Brief — first cut

## At a glance
**Target (base)** $19.64 (+73.4% vs entry-vintage spot) · **Spot** $11.33 (entry-vintage — frozen at underwrite 2026-08-05) · **Reward** $8.31 · **Risk** $3.97 · **Reward : risk** 2.10 : 1 (bar 2 : 1) · **Base IRR** 44.3% (floor 15%, 1.5y) · **Gate** PASS (both tests)

_Spot source: EOD SMPL last close 2026-08-04 (Polygon daily aggregate; store frontier at write)_

**Underwrite disposition:** PENDING_ANALYST (2026-07-27) — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

### What would reopen this name

- Quest revenue growth <= 0% YoY for two consecutive quarters — the growth engine is dead; re-underwrite the bull and base cases.
- FY26 guidance cut at the fiscal Q4 print (~October 2026), or initial FY27 guidance below ~$1.30B — the base revenue path fails.
- Gross margin below ~31% on a full-year basis, or a further decline beyond the ~4 points already absorbed — a margin regime break past what the 14% normal assumes. (The prior instance of this trigger fired on the nine-month decline and was discharged 2026-07-26 by the re-verification that re-set the normal; this is a fresh forward threshold.)

> ⚠ **Verify before the verdict:** EDGAR P/E 10.7x does not rest on LTM GAAP earnings; Net debt/EBITDA (1.5x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis — full caveats in Analysis.

The Simply Good Foods Company, a consumer-packaged food and beverage company, engages in the development, marketing, and sale of snacks and meal replacements, and other products in North America and internationally.
**Mixed** — a self-funding, durably profitable franchise with a growing Quest core, offset by secular Atkins erosion, ongoing impairments and still-falling estimates.
- **Segments:** Branded Nutritional Foods and Snacking Products — single segment [1]
- **Geography:** North America 98%; International 2% [2]
- **Snapshot:** Nasdaq · CMP $10.94 (2026-08-12) · cap $961M · 52-wk $9.88–$30.36 · shares 88.5M · book value/sh $16.03 [3]

**The crux — what decides this, and what would change our mind**
**Is the de-rating an overshoot on a durably profitable, self-funding franchise whose growth engine (Quest) plus pricing can rebuild margins — or a terminal re-rating as legacy Atkins demand secularly erodes, OWYN distribution unwinds, and cost inflation permanently resets margins lower?**
_7 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-10-08 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-04-09 earnings; 2026-04-10 earnings [4]
- **Price (180d):** -31.4% [5]
- **Market (IWM) 180d:** 15.1% [6]
- **vs market (180d):** -46.5% [7]
- **Net debt / EBITDA:** 1.5x [8]
- **Free cash flow:** positive [9]

## Scenario analysis
_Mid-cycle underwrite: normalized operating margin on a mid-cycle revenue base, valued at an exit EV/LTM-EBITDA multiple; reward/risk measured at SPOT._

| scenario | revenue $M | margin | multiple | value / sh | vs entry-vintage spot |
| --- | ---: | ---: | ---: | ---: | ---: |
| bear | 1,200 | 13.0% | 5.5x | $7.36 | -35.0% |
| base | 1,340 | 15.5% | 9x | $19.64 | +73.4% |
| bull | 1,410 | 17.0% | 12x | $31.75 | +180.3% |

- **bear** — Revenue 1,200 approximates the lowest FY2027 forecast on the street, 1,203.2 — a downside taken from the bottom of the analyst distribution rather than invented. Margin 13.0% sits roughly 0.9pp below the trailing twelve-month margin: further deterioration on top of what has already happened. The 5.5x multiple is below the lowest close in the company's own eight-and-a-half-year trading range, 6.11x, and is deliberately not 5.0x — pushing it lower would count the same deterioration twice, once in the revenue and margin legs and again in the multiple.
- **base** — Revenue 1,340 is the median FY2028 street forecast, read at the eighteen-month horizon this record states rather than at the nearest fiscal year. Margin 15.5% matches the median operating margin of the last eight fiscal years, 15.45%, and the street agrees forward: FY2027 consensus is about 15.5% and FY2028 implies 15.7%. The 9.0x multiple is roughly half the 17.85x median close of the company's own trading history, because that history spans a growth era the business has left; it stood at 9.54x as recently as September 2025, and comparable companies trade at 8.72x on next-twelve-month earnings.
- **bull** — Revenue 1,410 is the highest FY2028 street forecast. Margin 17.0% is held below the 17.18% the business actually earned in FY2024, so the upside leg claims only a margin already demonstrated rather than an extrapolation. The 12.0x multiple sits near the 12.89x that the most expensive comparable company trades at on next-twelve-month earnings, so the re-rating is bounded by what peers fetch today.

**Scenario inputs** — every value in the grid recomputes from these.

| input | value | basis | source |
| --- | ---: | --- | --- |
| d and a | 21.431 $M | consolidated latest FY | EDGAR companyfacts dep_amort (combined) — via committed dossier anchor block (#158/#160/#162-verified) |
| net debt | 324.582 $M | lease-inclusive net debt (latest 10-Q) | EDGAR: total debt 397 + finance leases 0 + operating leases 51 − cash 124 ($M) — via committed dossier anchor block (#158/#160/#162-verified) |
| diluted shares | 88.460545 M shares | The filer reports NO dilutive difference for 2026-03-01→2026-05-30 (basic and diluted weighted averages are equal at 89,940,680), so the diluted denominator equals the basic outstanding count of 88,460,545. This is a reported zero, not an unchecked one. Excluded from the filer's diluted average: antidilutive instruments (a loss period reports no dilution at all under ASC 260); out-of-the-money options, which contribute nothing under the treasury-stock method; any change in the dilutive count between the reporting period and the valuation date. | EDGAR dei:EntityCommonStockSharesOutstanding + us-gaap:WeightedAverageNumberOf{SharesOutstandingBasic,DilutedSharesOutstanding} — item 24 denominator swap |
| ltm revenue | 1,392.235 $M | LTM revenue | committed financial_summary.annual (LTM) — via committed dossier anchor block (#158/#160/#162-verified) |
| cash interest | 23.249 $M | FY2025 non-operating interest expense (FCF cross-check only) | EDGAR companyfacts InterestExpenseNonoperating FY2025 |
| cash tax rate | 0.2376 rate | FY2025 effective rate = tax expense / pre-tax income (FCF cross-check only; does not touch value/share) | EDGAR companyfacts IncomeTaxExpenseBenefit 32.289 / pre-tax 135.903 (FY2025) |

_Chain (EV/EBITDA):_ EBIT = revenue × op margin → EBITDA = EBIT + D&A → EV = EBITDA × exit multiple (EV/EBITDA) → equity = EV − net debt → value/share = equity ÷ diluted shares

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | mid-cycle margin × the median multiple of its own history | applicable |
| Mid-cycle margin | 15.4% | 8y history · firm |
| Median multiple, own history | 17.9x | 35 closes · firm · EV/EBITDA |
| Screen value / share | $43.33 | spot-independent · EV/EBIT 19.6x |
| Overall confidence | firm |  |

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Quest — the largest brand — grew retail takeaway 1.4% with household penetration up 120bps to 20.5%, and Quest chips consumption grew over 17% and milkshakes ~50%, evidence the core growth engine is still recruiting consumers within a purposeful-nutrition category that grew 10%. [10]
- Q3 came in ahead of the company's own expectations — net sales declined 6.3% to $357M and adjusted EBITDA declined 22.5% to $57.2M, both better than the Q2-guided Q3 range — an early inflection versus a bleaker prior guide. [10]
- Management announced a high single-digit price increase across most of the portfolio effective September to offset input inflation, a concrete margin-rebuild mechanism on a timetable rather than a hope. [10]
_Bear case — the decline is real:_
- Revenue and EBITDA growth are negative and worse than peers on fundamental_deltas (rev growth -4% vs peer 0%; EBITDA growth -19% vs peer -14%), so part of the peer discount is EARNED by inferior top-line and EBITDA momentum — a value-trap risk the human must weigh. [11]
- Forward estimate breadth is sharply negative: FQ4 2026 and FQ1 2027 revisions run 0↑ against 4–7↓ across EPS, EBITDA, revenue and net income at the 2m/3m horizons, and the FY26 EBITDA path fell -22% (285.6 → 222.1) over 12 months — a still-deteriorating consensus. [12]
- Gross margin has compressed hard — 33% LTM vs 39% in FY24 — driven by inflationary cocoa, whey and tariff costs, and management guides a further 375bps next-fy gross-margin decline, so the margin damage is ongoing and cost-driven, not one-off. [13]

## Financial snapshot
- **Financial snapshot** — [14]  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 1,169 | 1,243 | 1,331 | 1,451 | 1,392 | 1,352 | 1,285 |
| Revenue growth | +16% | +6% | — (basis) | +9% | — (basis) | -7% (vs FY25) | -5% |
| EBITDA ($M) | 222 | 225 | 250 | 262 | 217 | 222 | 221 |
| EBITDA margin | 19% | 18% | 19% | 18% | 16% | 16% | 17% |
| EBIT ($M) | 203 | 205 | 229 | 241 | 193 | 199 | 200 |
| Net income ($M) | 109 | 134 | 139 | 104 | -199 | -154 | 126 |
| EPS (GAAP, dil.) | 1.08 | 1.32 | 1.38 | 1.02 | -2.08 | -1.70 | 1.61 |
| Asset Writedown ($M) | — | — | — | -61 | -392 | — | — |
| FCF ($M) | 73 | 128 | 166 | 127 | 107 | — | — |

_table shows the last 4 fiscal years · 6 earlier years are in the Appendix_

**Capital allocation — created or destroyed**

- **Impairment headroom — goodwill + intangibles remaining:** $1,508.9M [15]
- **Goodwill:** $552.0M [15]
- **Intangibles (net):** $956.9M [16]
- **Goodwill impairment:** $38.0M [17]
- **Intangible impairment:** $331.0M [18]
- **Buyback — cash:** $213.2M [19]
- **Buyback — shares repurchased:** 11,651,767 [20]
- **Buyback — average cost/share:** $18.29 — **fiscal-period average over 2025-08-31→2026-05-30, 272d; NOT a purchase price** and not evidence of when they bought [21]
- **Acquisition consideration:** $280.4M [22]
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [23]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap | why |
|---|---:|---:|---:|---:|---:|---|
| **SMPL** | **961** | **1,509** | **2,062** | **73%** | **157%** | **—** |
| KHC | 29,231 | 52,086 | 73,065 | 71% | 178% | — |
| CAG | 7,145 | 9,950 | 17,274 | 58% | 139% | — |
| CPB | 6,775 | 9,318 | 15,142 | 62% | 138% | — |
| FRPT | 3,448 | — | 1,812 | — | — | no-tag |
| MZTI | 3,154 | 274 | 1,356 | 20% | 9% | — |
| JJSF | 1,684 | 229 | 1,356 | 17% | 14% | — |
| BRBR | 1,343 | 178 | 1,052 | 17% | 13% | — |
| UTZ | 1,250 | 1,814 | 2,776 | 65% | 145% | — |
| JBSS | 978 | 15 | 651 | 2% | 2% | — |
| HAIN | 49 | 467 | 1,163 | 40% | 956% | — |

- **Median — all peers (n=9):** 40% of assets · 138% of market cap
- **Median — peers ≥ $1,000M market cap (n=7):** 58% of assets · 138% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [24]  <!-- ds-table -->

|  | state | yrs charged | window $M | % acquired | last charge (any date) | live YTD $M |
|---|---|---|---|---:|---:|---|
| **SMPL** | **wrote down** | **1 of 5** | **61** | **4%** | **2025-08-30 ($61M)** | **369** |
| KHC | wrote down | 5 of 5 | 16,184 | 31% | 2025-12-27 ($6,734M) | 7,365 |
| CAG | wrote down | 4 of 4 | 4,689 | 47% | 2026-05-31 ($2,382M) | — |
| CPB | no annual obs. | — | — | — | 2018-07-29 ($540M) | 176 |
| FRPT | does not tag | — | — | — | never | — |
| MZTI | wrote down | 2 of 2 | 6 | 2% | 2024-06-30 ($4M) | — |
| JJSF | reports nil | 0 of 5 | — | — | never | — |
| BRBR | does not tag | — | — | — | never | — |
| UTZ | does not tag | — | — | — | never | — |
| JBSS | wrote down | 1 of 5 | 9 | 57% | 2023-06-29 ($9M) | — |
| HAIN | wrote down | 5 of 5 | 746 | 160% | 2025-06-30 ($429M) | 151 |

- **Base rate — 3 of 4 large peers ASSESSED over the window took a charge**, median 31% of acquired assets among those that did. The denominator counts only peers with an annual observation in the window — a name with none was not measured, and is not a clean year.
- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. `no annual obs.` and `does not tag` are not measurements and must not be read as clean years. The **live YTD** column is excluded from the window total: a year-to-date charge is not an annual one, and the two are different quantities._

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 5.6x as-of 2026-08-11 — trailing range 6.1–28.9x (median 17.9x) over 35 closes → 0%ile → near-floor; P/LTM EPS NM (no meaningful trailing P/E at this close) [25]
- **vs peers:** EV/EBITDA 5.6x vs peer median 8.8x (-36%); P/E NM vs peer median 16.35 [26]
- **Comparability:** market caps span $49M–$29.2B (599x); the name is $961M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [27]
- **The street, for contrast (target · ratings):** Target price: mean $14.88, median $14.00, high/low 20.00/12.00, N 8/8; Ratings: Buy 4, Outperform 0, Hold 7, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-07-21 · export date unverified] [28]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [4]
  - 2026-04-09 **-18.1%** → earnings
  - 2026-04-10 **-11.5%** → earnings

_Company-specific or market-wide?_
- **Name 180d return:** -31.4% [5]
- **Market (IWM) 180d return:** 15.1% [6]
- **Relative vs market:** -46.5% [7]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-downs 2026-04-09 and 2026-04-10 → filed 2026-04-09 [`0001702744-26-000010`](https://www.sec.gov/Archives/edgar/data/1702744/000170274426000010/atk-20260409.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj EBITDA Q2 2026 $55.5M (-18.4%); adj EPS Q2 2026 $0.45; $3.9M one-time OWYN integration expenses; $4.5M restructuring costs; 2026 net sales outlook: $1,310.0–$1,350.0M; next-fy adjusted EBITDA outlook: $217.0–$225.0M; next-fy gross margin outlook: $-350.0–$-300.0M [29]

## Business quality
- **Segments (revenue share):** Branded Nutritional Foods and Snacking Products — single segment [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — single-segment reporting (Branded Nutritional Foods and Snacking Products) — no segment EBITDA to break out; the consolidated EBITDA is the whole business
- **Customers:** 5 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [30]
- **Geographic:** North America 98%; International 2% [2]

## The argument

**Evidence balance:** mixed — a self-funding, durably profitable franchise with a growing Quest core, offset by secular Atkins erosion, ongoing impairments and still-falling estimates.

### Bull case — the decline is overdone
- Quest — the largest brand — grew retail takeaway 1.4% with household penetration up 120bps to 20.5%, and Quest chips consumption grew over 17% and milkshakes ~50%, evidence the core growth engine is still recruiting consumers within a purposeful-nutrition category that grew 10%. [10]
- Q3 came in ahead of the company's own expectations — net sales declined 6.3% to $357M and adjusted EBITDA declined 22.5% to $57.2M, both better than the Q2-guided Q3 range — an early inflection versus a bleaker prior guide. [10]
- Management announced a high single-digit price increase across most of the portfolio effective September to offset input inflation, a concrete margin-rebuild mechanism on a timetable rather than a hope. [10]
- The business is FCF-positive and self-funding (LTM levered FCF $107.2M) with net-debt/EBITDA of 1.5x and interest coverage of 10.9x, so it can fund its own turnaround without forced dilution or refinancing distress. [31]
- On the fundamental_deltas, the name carries LOWER leverage (Debt/EBITDA 1.9x vs peer-median 3.3x), a lower beta (0.1 vs 0.4) and a HIGHER LT EPS growth estimate (2% vs peer-median -8%) than the peer set, so the discount is not explained by worse balance-sheet or growth fundamentals across the board — the human must judge earned vs residual against a heterogeneous roster. [11]
- Absolute EBITDA has stepped up the entire history (FY21 196 → FY22 222 → FY24 250 → FY25 262) with only a modest LTM dip to 217, so the enterprise is a durably profitable cash generator, not a melting asset — the margin-percent softening sits against a much larger absolute base than five years ago. [13]
- The trailing EV/EBITDA sits at 5.6x against a peer median of 8.8x (-36%), but the paired fundamental deltas show the discount is not obviously earned on profitability — the name's EBITDA margin is 16% vs a peer median of 13% — posing whether the gap is residual overshoot rather than a value trap. [26]
- Insiders were net buyers on the open market (2 buys, ~$1.11M, zero sells in the last 182 days, largest a $0.99M director purchase 2026-04-23) around the drawdown lows, a directional signal from those closest to the business. [32]

### Bear case — the decline is real
- Revenue and EBITDA growth are negative and worse than peers on fundamental_deltas (rev growth -4% vs peer 0%; EBITDA growth -19% vs peer -14%), so part of the peer discount is EARNED by inferior top-line and EBITDA momentum — a value-trap risk the human must weigh. [11]
- Forward estimate breadth is sharply negative: FQ4 2026 and FQ1 2027 revisions run 0↑ against 4–7↓ across EPS, EBITDA, revenue and net income at the 2m/3m horizons, and the FY26 EBITDA path fell -22% (285.6 → 222.1) over 12 months — a still-deteriorating consensus. [12]
- Gross margin has compressed hard — 33% LTM vs 39% in FY24 — driven by inflationary cocoa, whey and tariff costs, and management guides a further 375bps next-fy gross-margin decline, so the margin damage is ongoing and cost-driven, not one-off. [13]
- Atkins — a core legacy brand — is in secular decline: retail takeaway fell 23.9% in Q3 with household penetration down 220bps to 8.5%, a real signal of demand erosion, not an optical artifact. [10]
- OWYN — the recent acquisition — still faces expected distribution losses over the next 6–12 months from a product-quality issue and poor marketplace performance, a forward drag on top line, not a healed problem. [10]
- The company took $391.9M of asset writedowns (goodwill + intangible impairment across Atkins and OWYN) in the trailing period, driving a GAAP net loss of -$199M and confirming acquired brand value was permanently destroyed, not merely re-timed. [18]
- The de-rating is idiosyncratic, not market-driven: SMPL returned -31.4% over 180d while its small-cap benchmark IWM rose +15.1%, a -46.5% relative gap that points to a company-specific impairment of the thesis, not a beta washout. [7]
- The trailing 5.6x is at its own 0th percentile over 8.5 years (range 6.1–28.9x, median 17.9x) and the forward NTM basis is barely higher at 5.9x — so this is NOT merely a trailing optical low; consensus is pricing a durably lower multiple, consistent with the terminal-impairment read rather than a timing dip. [33]

### Decisive question
**Is the de-rating an overshoot on a durably profitable, self-funding franchise whose growth engine (Quest) plus pricing can rebuild margins — or a terminal re-rating as legacy Atkins demand secularly erodes, OWYN distribution unwinds, and cost inflation permanently resets margins lower?**

### …evidence for
- Quest retail takeaway grew 1.4% with household penetration up 120bps to 20.5% and Quest chips up over 17%, showing the core engine still recruits consumers in a category that grew 10%. [10]
- A high single-digit portfolio-wide price increase effective September is a committed mechanism to offset the protein/packaging inflation that drove margin compression. [10]
- The franchise is self-funding — LTM FCF +$107.2M, net-debt/EBITDA 1.5x, interest coverage 10.9x — giving it runway to execute a turnaround without distress. [31]

### …evidence against
- Atkins takeaway fell 23.9% with penetration down 220bps to 8.5%, and management ties it to lost household penetration and distribution — a secular demand drain on a core brand. [10]
- $391.9M of Atkins/OWYN brand impairment confirms acquired value was permanently written down, and OWYN faces further 6–12 month distribution losses. [18]
- Forward estimate breadth remains one-sidedly negative (0↑ vs 4–7↓) and the FY26 EBITDA consensus path fell -22% over 12 months, with the NTM multiple (5.9x) barely above trailing — consensus is pricing a durably lower level. [12]

### Key unknowns
- No forward/adjusted EV/EBITDA or adjusted EPS in the revised guidance, and no company-adjusted LTM EBITDA — the overshoot-vs-terminal multiple read cannot be cleanly gated on a forward adjusted basis (opacity to surface, not fill).
- No segment-level EBITDA (single-segment reporting) and no XBRL per-brand split of the $391.9M impairment across Atkins vs OWYN — the profitability and value destruction by brand is footnote-prose only, obscuring which brand is dragging.
- Whether the September high-single-digit price increase holds without accelerating volume/distribution losses — elasticity in a declining-takeaway environment is untested in the data provided.
- How much of Atkins' decline is GLP-1-driven secular versus fixable marketing under-investment — management asserts execution-driven, but provides no data separating the two.
- The peer set is HETEROGENEOUS (caps $49M–$29.2B, 599x span; name $961M) — every peer-median stat is a confidence-gated input, not a clean benchmark, so the -36% EV/EBITDA discount cannot be read as clean mispricing.
- The next results print (~2026-10-08) is the checkpoint that confirms or refutes the committed revised outlook and the early Q3 inflection — unresolved until then.
- The 5.6x trailing multiple sits at its own 0th percentile over 8.5y — a floor reading that is itself neutral (overshoot-vs-terminal unresolved) and must be judged against the mechanism, not read directionally on its own.

### Twin reference cases
- **BellRing Brands** — recovered
  - distinguished by: Same purposeful-nutrition/protein aisle and in the peer set; a focused single-category nutrition player that compounded on brand momentum — the pattern SMPL's Quest engine would need to reassert.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **The Hain Celestial Group** — went terminal
  - distinguished by: In-peer natural/better-for-you brand company whose acquired brand portfolio impaired repeatedly over years with eroding takeaway — the terminal analogue for SMPL's Atkins/OWYN writedown path.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **The Kraft Heinz Company** — went terminal
  - distinguished by: In-peer packaged-food acquirer that took massive multi-year goodwill/intangible impairments on over-paid brands and de-rated persistently — the 'acquired brand value permanently destroyed' pattern.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Utz Brands** — recovered
  - distinguished by: In-peer salty-snacks player that carried heavy leverage and depressed margins through an operational reset while retaining brand relevance — a turnaround-execution analogue.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Medifast** — went terminal (LLM-claimed — verify)
  - distinguished by: Weight-management brand whose demand base eroded sharply amid GLP-1 adoption and a lost core consumer — the demand-erosion analogue most relevant to Atkins.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-10-08 `[cadence-estimate]` — the committed revised outlook (see Revised guidance — the print is the checkpoint that confirms or refutes it) [34]
- **Mexican Street Corn will be available exclusively at Target beginning in January, and Pizza, now exclusively at Walma…** — ~2027-01 `[stated]` — a management-stated dated operating action — the thesis mechanism on a timetable; the following print reads its result [35]
- **Re-underwrite trigger: September portfolio-wide price increase fails to stick (elasticity / share loss)** — ~2027-01-07 `[trigger-deadline]` — the analyst's own falsifier — unresolved by this date, the monitor flags re-underwrite due [36]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 5.6x vs peer median 8.8x (-36%); P/E NM vs peer median 16.35 [26]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-08-11 · multiples as-of 2026-07-21 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [37]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **5.9x** | **$217.8M EBITDA †** |
| peer-median NTM TEV/EBITDA | 9.2x | $139.7M EBITDA |
| peer-median LTM TEV/EBITDA | 8.7x | $147.7M EBITDA |
| **name NTM TEV/Rev** | **0.99x** | **$1,298.3M Revenue †** |
| peer-median NTM TEV/Rev | 1.37x | $938.2M Revenue |
| peer-median LTM TEV/Rev | 1.3x | $988.7M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $222.1M · FY27E $220.9M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $1351.8M · FY27E $1284.6M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

### The EV gap — our base case vs the street

_Anchor FY2026 · consensus as-of ≥2026-07-21 (a FLOOR — the export states no as-of, so the true date is on or after this) · TEV as-of 2026-08-11 · form three-ratio_

- **The gap, decomposed (ours / consensus, at the anchor year)**  <!-- ds-table -->

|  | ratio | consensus dispersion |
|---|---|---:|
| revenue | 0.99x | sigma 3.62 on n=9 |
| EBITDA margin | 1.04x | sigma 2.80 on n=10 |
| exit multiple | 1.56x | street 5.76x at FY2026 |
| **product = the EV gap** | **1.60x** |  |

_the three ratios multiply to the gap by IDENTITY — this is a decomposition, never an attribution of cause_

- **Shape:** **multiple-dominant** at FY2026, and FY2027 gives the same shape — the label does not move with the year.

  _The record does not state which fiscal year its base leg is struck at, so this label is reported on FY2026's basis and is unverified against the leg. The total gap above carries no year and is unaffected._

- **Bridge:** our EV $2,062M − net debt $325M = equity $1,738M ÷ 88.461M sh = **$19.64/sh** — against TEV $1,285M.

  - _Revenue dispersion 0.9% (high−low ÷ |median|, FY2026, as-of ≥2026-07-21)_
  - _EBITDA dispersion 4.7% (high−low ÷ |median|, FY2026, as-of ≥2026-07-21)_

  - _D&A convention: fixed $M anchor (R1, mid-cycle) — the two recipes differ and the reconciliation is an open analyst question, so it is stated rather than assumed._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 5.6x as-of 2026-08-11 — trailing range 6.1–28.9x (median 17.9x) over 35 closes → 0%ile → near-floor; P/LTM EPS NM (no meaningful trailing P/E at this close) [25]

## Peer comps
- **Peer set (roster · caps · business)** — [38]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Utz Brands | $1.3B | manufactures branded salty snacks in the United States. (United States) |
| J&J Snack Foods Corp. | $1.7B | manufactures, markets, and distributes nutritional snack food and beverages to the food service and retail supermarket industries in the United States, Mexico (United States) |
| The Hain Celestial Group | $49M | manufactures, markets, and sells organic and natural products in the United States, United Kingdom, Europe, and internationally. (United States) |
| The Campbell's Company | $6.8B | manufactures and markets food and beverage products in the United States and internationally. (United States) |
| The Marzetti Company | $3.2B | engages in manufacturing and marketing of specialty food products for the retail and foodservice channels in the United States. (United States) |
| Freshpet | $3.4B | manufactures, distributes, and markets natural fresh meals and treats for dogs and cats in the United States, Canada, and Europe. (United States) |
| BellRing Brands | $1.3B | provides various nutrition products in the United States. (United States) |
| Conagra Brands | $7.1B | operates as a branded consumer packaged goods food company primarily in the United States. (United States) |
| John B. Sanfilippo & Son | $978M | distributes tree nuts and peanuts in the United States. (United States) |
| The Kraft Heinz Company | $29.2B | manufactures and markets food and beverage products in North America and internationally. (United States) |

_the name: $961M_

- **Comparability (confidence gate):** market caps span $49M–$29.2B (599x); the name is $961M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [27]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [39]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 0.99 | 0.52 | 1.37 | 1.44 | 2.82 |
| NTM TEV/EBITDA | 5.9 | 6.78 | 9.2 | 9.62 | 14.91 |
| NTM P/E | 6.49 | 9.44 | 13.26 | 16.82 | 45.27 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [40]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| The Kraft Heinz Company | $29.2B | 7.6 | 1.8 | NM | 22% | -2% | 3.2 | 16,320 |
| Conagra Brands | $7.1B | 7.4 | 1.3 | NM | 15% | -3% | 4.2 | 7,257 |
| The Campbell's Company | $6.8B | 6.3 | 1.4 | 11.1 | 17% | -3% | 3.4 | 6,934 |
| Freshpet | $3.4B | 17.7 | 3.1 | 19.5 | 17% | 13% | 2.4 | 143 |
| The Marzetti Company | $3.2B | 9.3 | 1.5 | 18.0 | 15% | 3% | 0.1 | 181 (net cash) |
| J&J Snack Foods Corp. | $1.7B | 9.6 | 1.2 | 35.0 | 10% | -5% | 1.0 | 129 |
| BellRing Brands | $1.3B | 9.2 | 1.0 | 8.1 | 11% | 6% | 4.4 | 1,123 |
| Utz Brands | $1.3B | 32.6 | 2.0 | NM | 6% | 2% | 11.8 | 974 |
| John B. Sanfilippo & Son | $978M | 8.3 | 0.9 | 14.7 | 10% | 5% | 0.8 | 102 |
| **The Simply Good Foods Company · the name** | **$961M** | **5.6** | **0.9** | **NM** | **16%** | **-4%** | **1.9** | **325** |
| The Hain Celestial Group | $49M | 6.1 | 0.4 | NM | 6% | -10% | 6.1 | 550 |
| Peer median (peers) | $2.4B | 8.8 | 1.4 | 16.4 | 13% | 0% | 3.3 | 762 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [13]  <!-- ds-table -->

|  | Aug-2016 (R) | Aug-2017 (R) | Aug-2018 | Aug-2019 | Aug-2020 | Aug-2021 (R) | Aug-2022 (R) | Aug-2023 (R) | Aug-2024 | Aug-2025 | May-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 42% | 41% | 42% | 42% | 40% | 41% | 38% | 36% | 39% | 36% | 33% |

_R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** buying back (trailing ~1.7y): 100,221,529 (2024-10-18) → 88,460,545 (2026-07-02), -11.7% [41]
- **Non-operating earnings:** no material non-operating item in the four quarters to 2026-02-28 — in the latest, $-5M against $-218M pre-tax [42]
- **Return ratios — per fiscal period** — [43]  <!-- ds-table -->

|  | FY16 | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | — | -0.7% | 5.9% | -3.6% | 7.1% | 3.5% | 8.3% | 8.9% | 8.4% | 5.9% | -12.2% |
| RoCE % | — | 6.5% | 5.0% | 5.9% | 5.3% | 6.4% | 7.1% | 6.8% | 7.0% | 7.0% | 6.0% |
| RoA % | — | 5.4% | 4.4% | 5.0% | 4.5% | 5.5% | 6.1% | 6.1% | 6.3% | 6.2% | 5.4% |
| Total debt/equity | — | 0.32x | 0.28x | 0.27x | 0.55x | 0.42x | 0.32x | 0.21x | 0.25x | 0.17x | 0.32x |
| Current ratio | 3.13x | 4.03x | 6.07x | 7.45x | 3.64x | 2.63x | 3.44x | 4.14x | 4.05x | 3.64x | 4.80x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-07-21)_
- **Horizon read (FQ — next-2Q revision breadth)** — [12]:
  - EPS Normalized FQ4 2026: 1m 0↑/0↓, 2m 1↑/6↓, 3m 0↑/7↓
  - EPS Normalized FQ1 2027: 1m 0↑/1↓, 2m 0↑/4↓, 3m 0↑/4↓
  - Revenue FQ4 2026: 1m 0↑/0↓, 2m 2↑/6↓, 3m 2↑/6↓
  - Revenue FQ1 2027: 1m 0↑/2↓, 2m 1↑/4↓, 3m 1↑/4↓
  - EBITDA FQ4 2026: 1m 0↑/0↓, 2m 0↑/6↓, 3m 0↑/6↓
  - EBITDA FQ1 2027: 1m 0↑/1↓, 2m 0↑/4↓, 3m 0↑/4↓
  - EBIT FQ4 2026: 1m 0↑/0↓, 2m 0↑/5↓, 3m 0↑/5↓
  - EBIT FQ1 2027: 1m 0↑/0↓, 2m 0↑/3↓, 3m 0↑/3↓
  - _+7 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 2.02 (12m) → 1.89 (9m) → 1.95 (6m) → 1.61 (3m) → 1.65 (2m) → 1.64 (1m) → 1.65 (latest); net -18% (12m→latest) | FY 2026 EPS (GAAP): 1.70 (12m) → 1.64 (9m) → 1.65 (6m) → -0.06 (3m) → 0.35 (2m) → -1.70 (1m) → -1.70 (latest); worsening (crossed zero) (12m→latest) | FY 2026 Revenue: 1,497.8 (12m) → 1,448.9 (9m) → 1,447.0 (6m) → 1,335.1 (3m) → 1,333.9 (2m) → 1,350.9 (1m) → 1,351.8 (latest); net -10% (12m→latest) | FY 2026 EBITDA: 285.6 (12m) → 269.1 (9m) → 271.1 (6m) → 220.0 (3m) → 219.8 (2m) → 221.9 (1m) → 222.1 (latest); net -22% (12m→latest) | FY 2026 EBIT: 262.4 (12m) → 242.1 (9m) → 242.2 (6m) → 194.0 (3m) → 196.3 (2m) → 198.5 (1m) → 198.7 (latest); net -24% (12m→latest) | FY 2026 Interest Expense: -15.2 (12m) → -15.2 (9m) → -19.7 (6m) → -19.5 (3m) → -19.5 (2m) → -19.7 (1m) → -19.7 (latest); worsening (magnitude away from zero) (12m→latest) | FY 2026 EBT (GAAP): 248.3 (12m) → 232.7 (9m) → 225.6 (6m) → 171.1 (3m) → 171.1 (2m) → 180.9 (1m) → 180.9 (latest); net -27% (12m→latest) | FY 2026 Net Income (Excl. Excep): 195.5 (12m) → 184.0 (9m) → 181.6 (6m) → 148.6 (3m) → 148.8 (2m) → 151.8 (1m) → 152.0 (latest); net -22% (12m→latest) | FY 2026 Net Income (GAAP): 172.6 (12m) → 164.8 (9m) → 161.7 (6m) → -27.6 (3m) → -9.73 (2m) → -153.5 (1m) → -153.5 (latest); worsening (crossed zero) (12m→latest)  [data ≥ 2026-07-21 · export date unverified] [44]
- **Cross-name anchor (NTM forward-multiple ladder)** — [45]:
  - NTM: TEV/REV 0.99 · TEV/EBITDA 5.90 · TEV/EBIT 6.47 · Price/Earnings 6.49 · PEG 2.72 · P/BV –
  - FY 2026: TEV/REV 0.95 · TEV/EBITDA 5.79 · TEV/EBIT 6.47 · Price/Earnings 6.60 · PEG 2.76 · P/BV 0.69
  - FY 2027: TEV/REV 1.00 · TEV/EBITDA 5.82 · TEV/EBIT 6.44 · Price/Earnings 6.36 · PEG 2.66 · P/BV 0.60
  - FY 2028: TEV/REV 0.97 · TEV/EBITDA 5.52 · TEV/EBIT 6.06 · Price/Earnings 5.84 · PEG 2.45 · P/BV 0.55
  - _+5 later fiscal years in JSON_
- **Guidance at the drawdown (8-K 99.1):** Updating Fiscal Year 2026 (4) Outlook: • Net sales expected to range between $1.31 and $1.35 billion, or -10% to -7% year-over-year • Gross margins expected to decline between 300 and 350 basis points year-over-year • Adjusted EBITDA expected to range between $217 and $225 million, or -22% to -19% year-over-year “I want to make it quite clear that we are not satisfied with our current performance,” said Joe Scalzo, President and Chief Executive Officer of Simply Good Foods. "Our recent results have not met our expectations, and we have taken immediate and fundamental actions to turnaround both our financial performance and our in-market performance." Scalzo continued, “The long-term fundamentals of our category, our portfolio and our company capabilities are compelling, but in the near-ter [46]
- **Current guide (latest results filing):** net sales 2026: 1,345.0–1,355.0 $M; adjusted ebitda next-fy: 220.0–225.0 $M; gross margin next-fy: -375.0–-375.0 bps [47]
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [48]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | '322.00 - 332.00' | FQ4 2026 | 2026-07-09 | fresh | actual ≥ floor 8/9 · 2 at-guide (±0.5% of a point, not adjudicated) | FQ3 2026 MET |
| EBITDA | '52.00 - 57.00' | FQ4 2026 | 2026-07-09 | fresh | actual ≥ floor 6/9 · 1 at-guide (±0.5% of a point, not adjudicated) | FQ3 2026 MET |
| Capital Expenditure | '(20.00) - (25.00)' | FY 2026 | 2026-07-09 | fresh | spend ≤ ceiling 6/8 | FY 2025 MISSED |
| Gross Margin % | 32.5 | FY 2026 | 2026-07-09 | fresh | actual ≥ floor 4/9 · 1 at-guide (±0.5% of a point, not adjudicated) | FQ2 2026 MISSED |
| Effective Tax Rate % | 25.0 | FQ4 2026 | 2026-07-09 | fresh | spend ≤ ceiling 2/5 | FY 2025 MISSED |
| Interest Expense | '(19.00) - (21.00)' | FY 2026 | 2026-07-09 | fresh | spend ≤ ceiling 1/6 | FY 2025 MISSED |
| EPS Normalized | none current (last: 1.69) | FY 2023 | 2023-06-29 | 1140d (stale) | actual ≥ floor 2/3 | FY 2023 MISSED |
| Cash From Operations | none current (last: 110.6) | FY 2023 | 2023-01-05 | 1315d (stale) | actual ≥ floor 1/2 | FY 2023 MET |

_CIQ states every guide as a LEVEL in the metric's own units. Where management guided a RATE, the level is CIQ's arithmetic on its own base, not a figure the company published — check the release before quoting one as guidance._

- **Consensus stats (target + ratings):** Target price: mean $14.88, median $14.00, high/low 20.00/12.00, N 8/8; Ratings: Buy 4, Outperform 0, Hold 7, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-07-21 · export date unverified] [28]
- **Revision-event log (250 events · 10 broker-days)** — [49]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Withheld | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-07-21 | broker undisclosed | 4 | 2 | 2 | — | — | EBITDA FY 2026 | 222.9 | 223.0 | +0.14 |
| 2026-07-15 | broker undisclosed | 5 | 1 | 3 | 1 | — | Capital Expenditure FY 2026 | -8.0 | -22.5 | −14.5 |
| 2026-07-13 | BTIG | 3 | — | — | 3 | — | — | — | — | — |
| 2026-07-13 | broker undisclosed | 18 | 12 | 6 | — | — | EBITDA FQ4 2026 | 59.1 | 53.7 | −5.4 |
| 2026-07-10 | BTIG | 3 | — | — | 3 | — | — | — | — | — |
| 2026-07-10 | broker undisclosed | 88 | 30 | 33 | — | 25 | EBITDA FQ4 2026 | 74.8 | 54.2 | −20.6 |

_+4 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2017 +25%, FY2018 +30%, FY2019 -11%, FY2020 -3%, FY2021 -42%, FY2022 +0%, FY2023 -3%, FY2024 -9%, FY2025 -36%; Revenue surprise: FY2017 +0%, FY2018 -1%, FY2019 +1%, FY2020 +2%, FY2021 +0%, FY2022 +1%, FY2023 +0%, FY2024 +0%, FY2025 +0% (GAAP-EPS basis; +beat / −miss) [50]

## Leverage & survival
- **Net debt / EBITDA [NET]:** 1.5x [8]
- **Total debt / EBITDA vs peers:** name 1.9x vs peer median 3.3x (comps TOTAL-debt/EBITDA basis) [51]
- **Net debt / OCF:** 2.2x [52]
- **Interest coverage:** 10.9x [53]
- **Self-funding:** self-funding: YES — latest-Q OCF > 0 AND LTM FCF > 0 [54]
- **Credit health** — [55]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 1 | 3 |
| Operational | 3 | 2.5 |
| Solvency | 2 | 3 |
| Liquidity | 2 | 3 |

_S&P issuer rating BB- · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [9]
- **Free cash flow ($M):** 107.2 — basis: CIQ 'Levered Free Cash Flow', NOT CFO − capex: on the same sheet and period [LTM 12 months May-30-2026], CFO $147.5M − capex $28.1M = $119.4M — 0.90x apart. Company-defined FCF is usually the second; a per-share or self-funding read should say which it used. [31]
- **Debt schedule vintage:** the debt schedule is 288d old (source filed 2025-10-28); no Item 1.02 (termination of a material agreement) has been filed since [56]
- **Live instruments — near-dated (≤12m + 2027):** none due in the window — 3 undated / later aggregate line item(s) in the appendix panel [57]
- **Maturity wall** · vs the 2026-08-12 reference:
  - due 2029: $0.0M
  - due 2030: $249.1M
  - undated (floor — no panel maturity): $55.4M — Operating Lease $55.4M
  - _reconciliation: itemized $304.5M (panel A 2025 filed Oct-28-2025) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** term loans 397.0 (3 months FQ2/CQ1 Feb-28-2026 396.9 → 3 months FQ3/CQ2 May-30-2026 397.0); leases 51.4; total principal 448.5; total debt 448.5 (3 months FQ3/CQ2 May-30-2026) ($M) [58]
- **Covenants — Credit Agreement** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LIBO Rate / ABR + 3.75% · On and after Amendment No. 2 Effective Date: ABR Loan 2.75% per annum; Eurodollar Loan 3.75% per annum (prior: ABR 2.50…
  - **Maturity:** July 7, 2024 · July 7, 2024
  - **Financial maintenance:** Total Net Leverage Ratio no greater than 5.00 to 1.00 (as an Investment condition under Section 6.04(bb)); Investment b…
  - **Events of default:** Voluntary prepayment permitted without premium/penalty; within 12 months of Amendment No. 2 Effective Date a Repricing…

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [59]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [60]
  - net debt / EBITDA (CIQ, GAAP basis): 1.5x
  - total debt / EBITDA (CIQ comps, GAAP basis): 1.9x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage

## ⚠ Analyst caveats — verify before the verdict

_3 to verify._

- EDGAR P/E 10.7x does not rest on LTM GAAP earnings — LTM GAAP diluted EPS is NEGATIVE (-2.08), so a positive multiple must use some other denominator (an EPS from a non-current period, or a normalized/adjusted figure — the displayed basis does not say which). Do not read it as a GAAP trailing multiple.
- Net debt/EBITDA (1.5x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 1.5x as the covenant-basis leverage.
- **Unreconciled margin-compression** — Gross margin has compressed hard — 33% LTM vs 39% in FY24 — driven by inflationary cocoa, whey and tariff costs, and management guides a further 375bps next-fy gross-margin decline, so the margin damage is ongoing and cost-driven, not one-off.
  - _where:_ a bear point
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

### Revenue · ratified 2026-08-05

All three legs are read off the street's forecast distribution AT THIS RECORD'S EIGHTEEN-MONTH HORIZON rather than at the nearest fiscal year: base 1,340 is the median FY2028 estimate, bull 1,410 the highest, and bear 1,200 approximates the lowest FY2027 estimate of 1,203.2. Taking all three from one distribution keeps a single horizon across the legs. The computed default of 1,351.7 is the FY2026 median and therefore describes a different moment, which is why base sits below it.

| reference | value |
| --- | ---: |
| FY2025 reported revenue | $1,450.9M [61] |
| LTM revenue | $1,416.208M [62] |
| consensus FY26E revenue `base` | $1,334M [63] |

### Margin · ratified 2026-08-05

Base 15.5% matches the median operating margin of the last eight fiscal years, 15.45%, and is corroborated forward rather than extrapolated from a depressed present — the street carries about 15.5% for FY2027 and an implied 15.7% for FY2028. Bear 13.0% is roughly 0.9pp below the trailing twelve-month margin: deterioration from a level already impaired. Bull 17.0% is held below the 17.18% actually earned in FY2024, so the upside claims only what the business has already done. Stated on operating income, not EBITDA.

| reference | value |
| --- | ---: |
| screening median (naive, 8 FY) | 15.45% [64] |
| 7yr clean median (FY2025 adjusted) `base` | 15.51% [65] |
| FY2020 worst clean year `bear` | 9.58% [66] |
| FY2022 best clean year `bull` | 17.35% [67] |
| FY2025 adjusted ex $60.9M impairment | 15.01% [68] |

### Multiple · ratified 2026-08-05

Base 9.0x is roughly half the 17.85x median close of the company's own eight-and-a-half-year trading history, and that gap IS the judgment: the history spans a growth era the business has left, so a median drawn across it describes a company that no longer exists. The leg follows the company's own de-rating instead — it traded at 9.54x as recently as September 2025 — and is cross-checked against the 8.72x median that comparable companies fetch on next-twelve-month earnings, which it sits slightly above. Bear 5.5x is below the 6.11x lowest close in that same history, deliberately not 5.0x, because a lower multiple would count deterioration the revenue and margin legs already carry. Bull 12.0x is near the 12.89x the most expensive comparable fetches.

| reference | value |
| --- | ---: |
| this company's trading-range low `bear` | 6.11x [69] |
| this company's trailing 25th percentile | 15.2x [69] |
| this company's trailing median `base` | 17.85x [69] |
| this company's trailing 75th percentile | 20.88x [69] |
| current multiple (0th pctile) | 5.65x [69] |
| entry-boundary cell A (1,100 × 8% × 6.0x) | 1.96:1 [70] |
| entry-boundary cell B (1,050 × 7% × 6.0x) | 1.73:1 [70] |

_2026-07-26 — entry-boundary cells: 1,100 × 8% × 6.0x → $3.54; 1,050 × 7% × 6.0x → $2.62 (from the sealed entry rationale, preserved in the ledger payload). At the verification price ($10.53, 2026-07-22 close) both clear on the entry-vintage 15.5% normal (≈2.34 / ≈2.07); on the re-set 14% normal they read ≈1.96 / ≈1.73 — below the bar. The boundary tightened with the cut: the 2:1 line now sits between the recorded 10% bear and these stress cells._ [70]


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-07-21)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [14]  <!-- ds-table -->

|  | FY16 (R) | FY17 (R) | FY18 | FY19 | FY20 | FY21 (R) | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 428 | 396 | 438 | 524 | 817 | 1,006 | 1,169 | 1,243 | 1,331 | 1,451 | 1,392 | 1,352 | 1,285 |
| Revenue growth | — | -7% | — (basis) | +20% | +56% | — (basis) | +16% | +6% | — (basis) | +9% | — (basis) | -7% (vs FY25) | -5% |
| EBITDA ($M) | 57 | 67 | 74 | 91 | 130 | 196 | 222 | 225 | 250 | 262 | 217 | 222 | 221 |
| EBITDA margin | 13% | 17% | 17% | 17% | 16% | 20% | 19% | 18% | 19% | 18% | 16% | 16% | 17% |
| EBIT ($M) | 48 | 57 | 67 | 84 | 114 | 178 | 203 | 205 | 229 | 241 | 193 | 199 | 200 |
| Net income ($M) | 10 | -2 | 37 | -25 | 66 | 41 | 109 | 134 | 139 | 104 | -199 | -154 | 126 |
| EPS (GAAP, dil.) | — | 0.01 | 0.51 | -0.31 | 0.35 | 0.42 | 1.08 | 1.32 | 1.38 | 1.02 | -2.08 | -1.70 | 1.61 |
| EPS (Normalized) | — | 0.30 | 0.18 | 0.01 | 0.73 | 0.51 | 0.94 | 1.09 | 1.29 | 1.35 | 1.15 | 1.65 | 1.71 |
| Restructuring Charges ($M) | -2 | — | — | — | -6 | -4 | -0 | — | — | — | -18 | — | — |
| Merger & Related Restruct. Charges ($M) | — | -32 | -2 | -7 | -27 | — | — | — | -18 | -23 | -21 | — | — |
| Asset Writedown ($M) | — | — | — | — | -3 | — | — | — | — | -61 | -392 | — | — |
| Legal Settlements ($M) | — | — | — | -4 | — | 5 | — | — | — | — | — | — | — |
| Other Unusual Items ($M) | — | — | 3 | 1 | — | — | — | — | -4 | — | — | — | — |
| CFO ($M) | 29 | -5 | 61 | 73 | 59 | 132 | 111 | 171 | 216 | 178 | 148 | 196 | 165 |
| Capex ($M) | -1 | -1 | -2 | -1 | -2 | -6 | -5 | -12 | -6 | -20 | -28 | -24 | -22 |
| FCF (levered, CIQ) | — | 31 | 46 | 57 | 25 | 105 | 73 | 128 | 166 | 127 | 107 | — | — |
| D&A ($M) | 10 | 10 | 8 | 8 | 20 | 23 | 26 | 27 | 28 | 28 | 30 | — | — |
| FCF (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | — | 162 | 151 |
| D&A (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | — | 20 | 19 |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-07-21; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

### Quarterly — every exported quarter
- **Quarterly financials** — [71]  <!-- ds-table -->

|  | FY16 | FY17 | FY17 | FY17 | FY17 | FY18 | FY18 | FY18 (R) | FY18 (R) | FY19 (R) | FY19 (R) | FY19 | FY19 | FY20 | FY20 | FY20 | FY20 | FY21 | FY21 | FY21 | FY21 | FY22 | FY22 | FY22 (R) | FY22 | FY23 | FY23 | FY23 | FY23 | FY24 | FY24 | FY24 | FY24 (R) | FY25 (R) | FY25 | FY25 | FY25 | FY26 | FY26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 100 | 102 | 97 | 98 | 107 | 109 | 107 | 108 | 121 | 124 | 139 | 140 | 152 | 227 | 215 | 222 | 231 | 231 | 284 | 260 | 281 | 297 | 317 | 274 | 301 | 297 | 325 | 320 | 309 | 312 | 335 | 376 | 341 | 360 | 381 | 369 | 340 | 326 | 357 |
| Gross margin | 49% | 46% | 45% | 49% | 49% | 46% | 48% | 24% | 43% | 40% | 41% | 43% | 42% | 40% | 41% | 40% | 41% | 39% | 43% | 40% | 41% | 37% | 37% | 37% | 37% | 35% | 37% | 38% | 37% | 37% | 40% | 40% | 39% | 36% | 36% | 34% | 32% | 32% | 34% |
| EBITDA ($M) | 21 | 16 | 13 | 17 | 22 | 17 | 16 | 16 | 25 | 21 | 23 | 22 | 30 | 40 | 41 | 38 | 47 | 40 | 65 | 46 | 63 | 51 | 60 | 48 | 57 | 48 | 60 | 63 | 58 | 53 | 67 | 72 | 66 | 62 | 70 | 64 | 50 | 51 | 52 |
| EBITDA margin | 21% | 15% | 14% | 17% | 21% | 16% | 15% | 15% | 20% | 17% | 17% | 16% | 20% | 17% | 19% | 17% | 21% | 17% | 23% | 18% | 22% | 17% | 19% | 18% | 19% | 16% | 18% | 20% | 19% | 17% | 20% | 19% | 19% | 17% | 18% | 17% | 15% | 16% | 14% |
| Revenue QoQ | — | +3% | -6% | +1% | +9% | +3% | -2% | — (basis) | +12% | +2% | +13% | — (basis) | +9% | +49% | -5% | +3% | +4% | -0% | +23% | -9% | +8% | +5% | +7% | — (basis) | — (basis) | -1% | +10% | -1% | -4% | +1% | +7% | +12% | — (basis) | +5% | — (basis) | -3% | -8% | -4% | +9% |
| Revenue YoY | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of FY26 ($M): cash & ST inv 124; total debt 448; net debt 325; equity 1,418; net working capital 367; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [72]
- **Coherence — BS vs implied-valuation bridge:** cash BS $124M / bridge $124M; debt BS $448M / bridge $448M — reconcile with the implied-valuation bridge. [73]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Oct-28-2025** — [57]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Credit Agreement With Barclays Bank PLC and Other Parties - Revolving Credit Facility | Revolving Credit | – | 4.200% | Benchmark | 2029-12-16 | Y | N | USD |
| Credit Agreement With Barclays Bank PLC and Other Parties - Term Loan | Term Loans | $249.1M | 5.700% | Benchmark | 2030-03-17 | Y | N | USD |
| Operating Lease | Capital Lease | $55.4M | 6.000% | NA | undated | Y | N | USD |

- **8-Ks at instrument maturities:** _UNKNOWN_ — no trailing-12m instrument maturity to anchor an 8-K
- **Covenant / contract pointers (CIK-verified execution filings)** — [74]  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| Credit Agreement | 8-K | 2018-03-20 | 0001213900-18-003172 — f8k032018ex10-1_simplygood.htm |
| Credit Agreement | 8-K | 2019-11-07 | 0001104659-19-060856 — a19-22146_1ex10d1.htm, a19-22146_1ex10d2.htm |
| Operating Lease | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Credit Agreement (governing agreement)** — [75]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001104659-19-060856 · a19-22146_1ex10d1.htm |
| Principal / commitment amount | $460,000,000 (2019 Incremental Term Loan Commitment; Barclays Bank PLC / Total) | base (footer) |
| Interest / coupon rate | LIBO Rate / ABR + 3.75% · On and after Amendment No. 2 Effective Date: ABR Loan 2.75% per annum; Eurodollar Loan 3.75% per annum (prior: ABR 2.50%, Eurodollar 3.50%) | 8-K 0001213900-18-003172 · f8k032018ex10-1_simplygood.htm |
| Maturity date | July 7, 2024 · July 7, 2024 | base (footer) |
| Financial-maintenance covenants | Total Net Leverage Ratio no greater than 5.00 to 1.00 (as an Investment condition under Section 6.04(bb)); Investment basket the greater of $100,000,000 and 66% of Consolidated EBITDA under Section 6… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | 2019 Incremental Term Loans rank equal in right of payment and security with Initial Term Loans; Holdings and Borrowers shall have satisfied the Collateral and Guarantee Requirement, and substantiall… — full verbatim in JSON | 8-K 0001213900-18-003172 · f8k032018ex10-1_simplygood.htm |
| Mandatory prepayment / events of default | Voluntary prepayment permitted without premium/penalty; within 12 months of Amendment No. 2 Effective Date a Repricing Transaction (incl. mandatory prepayment under Section 2.11(c) in connection with… — full verbatim in JSON | 8-K 0001213900-18-003172 · f8k032018ex10-1_simplygood.htm |
| 2018 Amendment Effective Date | March 16, 2018 | 8-K 0001213900-18-003172 · f8k032018ex10-1_simplygood.htm |
| Governing law | State of New York | 8-K 0001213900-18-003172 · f8k032018ex10-1_simplygood.htm |
| Scheduled amortization | $1,676,470.59 per quarter, commencing March 31, 2020 through June 30, 2024 | base (footer) |
| Closing fee | 0.50% of stated principal amount of the 2019 Incremental Term Loan | base (footer) |

_Source §: 8-K 0001104659-19-060856 · a19-22146_1ex10d1.htm · amended by 0001104659-19-060856_


### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 960.7 [76]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $123.90M, − total debt $448.50M [77]
- **Implied equity at peer-median ($M, CIQ)** — [78]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 1,576.0 |
| NTM Revenue (Capital IQ) | 1,447.6 |
| NTM EBITDA (Capital IQ) | 1,680.0 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf; The Simply Good Foods Company, Q3 2026 Earnings Call, Jul 09, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [79]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 2 (2 insiders, $1.11M) · sells 0 — in the last 182 days · last purchase $0.12M, director, 2026-05-14 (~3mo ago) · largest purchase $0.99M, director, 2026-04-23 (~4mo ago) · last sale $0.11M, VP, Controller and CAO, 2025-11-11 (~9mo ago) · largest sale $8.06M, director, 2024-11-07 (~21mo ago) · grants 78 · last filing 2026-07-24 · other filings 44 [32]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-07-31): 6.9M → 7.4M sh (+6.8%, rising) · 8.3% of shares out (EDGAR XBRL) · DTC 3.1d · recent: 2026-07-31 7.4M · 2026-07-15 6.9M · 2026-06-30 7.2M · 2026-06-15 6.5M [80]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [81]
- **Guide verification — CIQ guide vs release:** revenue: CIQ guides a QUARTER (FQ4 2026: 322.0–332.0) and the release guides a YEAR (2026: 1345.0–1355.0) — NOT CROSS-CHECKED. Different periods; annualising one to match the other would manufacture the base the comparison is supposed to verify. [82]

## Record & reproduce
- **Data window:** screened as of 2026-08-12 · assembled 2026-08-13 17:10 UTC
- **Extraction:** 2026-07-28.1 — unusual-items surfacing in the financial summary (#238) · multiples read from the latest close, NM rather than a stale figure (#241)
- **Price store:** `mosaic-theory-pg → mosaic-theory-wb` · reaching 2026-08-12
- **Panel age:** oldest panel 2d old — 2026-08-11 (valuation.implied_expectations.tev_as_of), against a 2026-08-13 build
- **Consensus age:** consensus 23d old (2026-07-21, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001702744` · Nasdaq : SMPL
- **Assembly log:** primary-source: 5 EX-99.1 release(s) + 1 10-Q parsed (+0.5s fetch)
- **Re-run:** `python -m vinci dossier --ticker SMPL` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Aug-30-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Aug-30-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[5] `EOD SMPL 180d to 2026-08-12`
[6] `EOD IWM 180d to 2026-08-12 (cap-band: $1.0B @ 2026-08-12 → small (<$4B) → IWM)`
[7] `EOD SMPL−IWM 180d to 2026-08-12 (assembly, cap-band)`
[8] `CIQ Net Debt $325M [FQ3/CQ2 May-30-2026] ÷ CIQ EBITDA $218M [LTM 12 months May-30-2026]`
[9] `EDGAR XBRL FCF sign (screen data-record)`
[10] `CIQ transcript: The Simply Good Foods Company, Q3 2026 Earnings Call, Jul 09, 2026.rtf`
[11] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[12] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[13] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[14] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[15] `EDGAR companyfacts Goodwill (as at 2026-05-30)`
[16] `EDGAR companyfacts IntangibleAssetsNetExcludingGoodwill (as at 2026-05-30)`
[17] `EDGAR companyfacts GoodwillImpairmentLoss (2025-08-31→2026-05-30, 272d)`
[18] `EDGAR companyfacts ImpairmentOfIntangibleAssetsExcludingGoodwill (2025-08-31→2026-05-30, 272d)`
[19] `EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2025-08-31→2026-05-30, 272d)`
[20] `EDGAR companyfacts TreasuryStockSharesAcquired (2025-08-31→2026-05-30, 272d)`
[21] `EDGAR companyfacts TreasuryStockAcquiredAverageCostPerShare (2025-08-31→2026-05-30, 272d)`
[22] `EDGAR companyfacts PaymentsToAcquireBusinessesNetOfCashAcquired (2023-08-27→2024-08-31, 370d)`
[23] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[24] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[25] `CIQ Financials→Multiples (Close; latest close = current, excluded from history)`
[26] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[27] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[28] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[29] `8-K 0001702744-26-000010 EX-99.1`
[30] `CIQ Customers&Suppliers The Simply Good Foods Company NasdaqCM SMPL Customers.rtf`
[31] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months May-30-2026]`
[32] `EDGAR Form 4 (latest 0002076611-26-000003; 110 filings in the 1095d scanned; counts over 182d)`
[33] `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 35 quarters spanning 2017-12-29..2026-06-30 (8.5y) (partial last column excluded from the distribution)`
[34] `cadence: EDGAR submissions (median 91d gap over 36 results 8-Ks; last print 2026-07-09) · guide: EDGAR 8-K 0001702744-26-000010 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1702744/000170274426000010/a991_pressreleasexq2x2026.htm`
[35] `CIQ Key Developments: The Simply Good Foods Company NasdaqCM SMPL Key Developments.rtf · Jan-05-2026`
[36] `underwrite record (analyst-typed (second print after the September action — the Q1-FY27 print reveals elasticity; operator-confirmed 2026-07-24))`
[37] `TEV = mcap 960.7 + net debt 324.6 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-08-11, exported 2026-08-12) — simple-TEV basis`
[38] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[39] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[40] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-08-12`
[41] `EDGAR XBRL shares, trailing 2024-10-18..2026-07-02`
[42] `EDGAR XBRL pre-tax − operating, quarters 2025-03-01..2026-02-28`
[43] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[44] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[45] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[46] `EDGAR 8-K 0001702744-26-000010 Ex-99.1 — https://www.sec.gov/Archives/edgar/data/1702744/000170274426000010/a991_pressreleasexq2x2026.htm`
[47] `8-K 0001702744-26-000021 EX-99.1 (filed 2026-07-09)`
[48] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record) — CIQ states every guide as a LEVEL; where management guided a RATE, the level is CIQ's arithmetic, not the company's published figure`
[49] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-07-21 · export date unverified]`
[50] `CIQ Estimates→Surprise (annual)`
[51] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-08-12`
[52] `CIQ Net Debt $325M [FQ3/CQ2 May-30-2026] ÷ CIQ OCF $148M [LTM 12 months May-30-2026]`
[53] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months May-30-2026]`
[54] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[55] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-08-12`
[56] `CIQ Capital Structure Details — A 2025 filed Oct-28-2025`
[57] `CIQ Financials→Capital Structure Details (A 2025 filed Oct-28-2025)`
[58] `CIQ Financials→Capital Structure Summary`
[59] `10-Q 0001702744-26-000023`
[60] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[61] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2025)`
[62] `committed dossier anchor block (#158/#160/#162-verified)`
[63] `committed dossier financial_summary (E cols = consensus)`
[64] `committed dossier anchor block (#158/#160/#162-verified) anchor.margin.value`
[65] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax FY2019-FY2025, FY2025 ex the $60.9M impairment`
[66] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2020)`
[67] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2022)`
[68] `EDGAR companyfacts OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax (FY2025) + 10-K 0001702744-25-000046 (FY2025, Note 5 Goodwill and Intangibles)`
[69] `committed dossier valuation.own_history (CIQ Financials→Multiples 'TEV/LTM EBITDA' Close, 35 closes, 8.55y span, as-of 2026-07-17, sha 7bd83a1103)`
[70] `entry rationale cells preserved in the ledger payload; re-verified 2026-07-26 at the 2026-07-22 close ($10.53)`
[71] `CIQ Financials→Income Statement (quarterly, full exported history)`
[72] `CIQ Financials→Balance Sheet (quarterly, FY26)`
[73] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[74] `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`
[75] `fenced Tier-2 extraction (verbatim, source-bound)`
[76] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-08-12`
[77] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-08-12`
[78] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-08-12`
[79] `CIQ transcript(s): The Simply Good Foods Company, Q2 2026 Earnings Call, Apr 09, 2026.rtf; The Simply Good Foods Company, Q3 2026 Earnings Call, Jul 09, 2026.rtf`
[80] `FINRA consolidated short interest (settle 2026-07-31); DTC = 7,383,061 short ÷ 2,385,558 screen 90d ADV`
[81] `10-Q maturity wall vs CIQ capital panel (same window)`
[82] `CIQ revenue guide vs release actual/outlook`