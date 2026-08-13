# Dossier — ARTIVION, INC. (NYSE: AORT)

_August 13, 2026 · extraction 2026-07-28.1_

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
- **Snapshot:** NYSE · CMP $28.64 (2026-08-12) · cap $1.3B (2026-07-30) ⚠ implies $27.43/sh vs CMP (-4.2%) · 52-wk $19.16–$48.25 · shares 48.8M · book value/sh $9.29 [3]

**The crux — what decides this, and what would change our mind**
**Is the collapsed forward-earnings path a durable impairment of the growth thesis (guidance cut, AMDS/stent-graft shortfall, On-X recall), or a temporary reset around near-floor trailing valuation while the EBITDA base and pipeline keep compounding?**
_8 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-11-05 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-05-08 material agreement + earnings [4]
- **Price (180d):** -21.7% [5]
- **Market (IWM) 180d:** 15.1% [6]
- **vs market (180d):** -36.9% [7]
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
| Screen value / share | $19.79 | spot-independent · EV/EBIT 72.7x |
| Overall confidence | firm |  |

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- Q1 2026 delivered 12% constant-currency revenue growth and ~26% adjusted EBITDA growth year-over-year, EBITDA outgrowing revenue. [10]
- On-X grew 17% year-over-year (constant currency) in Q1 2026 on global share gains plus a new ~$100M U.S. mechanical-valve opportunity, a durable share-taking driver. [10]
- Forward multiples step down steeply on the consensus growth path (NTM TEV/EBITDA 15.66x → FY27 13.33x → FY28 11.03x), so the near-floor trailing multiple sits against a rising earnings base rather than a static one. [11]
_Bear case — the decline is real:_
- Leverage runs above peers — total debt/EBITDA 3.7x vs peer median 2.0x and net-debt/EBITDA 3.3x with interest coverage only 2.5x — a genuine balance-sheet constraint, part of the EARNED discount. [12]
- LTM levered free cash flow is negative (-$7.3M) even as the business grows, so growth is not yet self-funding on that basis. [13]
- Q1 2026 stent-graft growth of only 10% cc fell below expectations on lower-than-expected U.S. AMDS set sales and soft international demand — a mechanism-level miss in the segment framed as foundational to growth. [10]

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
| **AORT** | **1,337** | **471** | **1,072** | **44%** | **35%** | **—** |
| BSX | 68,432 | 25,558 | 45,216 | 57% | 37% | — |
| EW | 49,381 | 3,334 | 13,867 | 24% | 7% | — |
| 688617 | 4,581 | — | — | — | — | unresolved |
| LMAT | 2,367 | 96 | 641 | 15% | 4% | — |
| ATRC | 2,080 | 278 | 677 | 41% | 13% | — |
| PRCT | 1,018 | — | 479 | — | — | no-tag |
| 7575 | 622 | — | — | — | — | unresolved |
| ANGO | 605 | 67 | 267 | 25% | 11% | — |
| CVRX | 131 | — | 92 | — | — | no-tag |
| ARAY | 28 | 58 | 448 | 13% | 210% | — |

- **Median — all peers (n=6):** 25% of assets · 12% of market cap
- **Median — peers ≥ $1,000M market cap (n=4):** 33% of assets · 10% of market cap
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
- **vs peers:** EV/EBITDA 22.3x vs peer median 27.1x (-18%); P/E 114.3x vs peer median 37.0x (+209%) [23]
- **Comparability:** market caps span $28M–$68.4B (2488x); the name is $1.3B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [24]
- **The street, for contrast (target · ratings):** Target price: mean $42.00, median $43.00, high/low 48.00/36.00, N 8/8; Ratings: Buy 6, Outperform 2, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-06-30 · export date unverified] [25]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [4]
  - 2026-05-08 **-28.3%** → material agreement + earnings

_Company-specific or market-wide?_
- **Name 180d return:** -21.7% [5]
- **Market (IWM) 180d return:** 15.1% [6]
- **Relative vs market:** -36.9% [7]
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

**Evidence balance:** mixed — a real EBITDA re-inflection and live pipeline against a guidance cut, an 82% forward-EPS collapse, above-peer leverage and an On-X recall.

### Bull case — the decline is overdone
- Q1 2026 delivered 12% constant-currency revenue growth and ~26% adjusted EBITDA growth year-over-year, EBITDA outgrowing revenue. [10]
- On-X grew 17% year-over-year (constant currency) in Q1 2026 on global share gains plus a new ~$100M U.S. mechanical-valve opportunity, a durable share-taking driver. [10]
- Forward multiples step down steeply on the consensus growth path (NTM TEV/EBITDA 15.66x → FY27 13.33x → FY28 11.03x), so the near-floor trailing multiple sits against a rising earnings base rather than a static one. [11]
- On the comps grid Artivion's revenue growth (17.6%) and EBITDA growth (42.2%) both exceed the peer median (13.4% / 23.2%), a growth profile that argues part of the peer discount may be residual rather than earned — the human judges justified-vs-residual against the fundamental_deltas. [28]
- Absolute EBITDA has re-inflected sharply — from a $15M trough at Dec-31-2023 to $52M/$54M/$61M (LTM) — so the low headline margin masks a real earnings-base recovery, not decline. [29]
- FDA approval of the NEXUS Aortic Arch System (Apr-07-2026) let Artivion exercise its option to acquire Endospan, completing a three-pronged aortic-arch portfolio — a concrete pipeline catalyst. [30]
- Sell-side remains constructive post-derate — target mean $42 / median $43 versus a ~$28.64 price, with 6 Buy / 2 Outperform / 0 Hold and no negative ratings. [31]

### Bear case — the decline is real
- Leverage runs above peers — total debt/EBITDA 3.7x vs peer median 2.0x and net-debt/EBITDA 3.3x with interest coverage only 2.5x — a genuine balance-sheet constraint, part of the EARNED discount. [12]
- LTM levered free cash flow is negative (-$7.3M) even as the business grows, so growth is not yet self-funding on that basis. [13]
- Q1 2026 stent-graft growth of only 10% cc fell below expectations on lower-than-expected U.S. AMDS set sales and soft international demand — a mechanism-level miss in the segment framed as foundational to growth. [10]
- On-X Life Technologies issued a voluntary product recall on May-23-2026 (heart valves distributed before all required testing complete), a live operational/regulatory risk to a core growth line. [32]
- Management LOWERED full-year 2026 earnings guidance on May-07-2026, and the current guide (adj EBITDA $92–99M) has been cut again from the prior $100–107M — a genuine downshift, not optical. [33]
- The FY26 GAAP EPS consensus path collapsed -82% (0.45 → 0.08 latest) and GAAP net income -79%, so the earnings the stock is priced on have been materially marked down; this is the REAL signal, not a stale trailing artifact. [34]
- Estimate breadth is uniformly negative — EBITDA FQ2/FQ3 2026 3-month revisions 0 up / 6 down, EPS 0 up / 7 down — confirming a broad-based downgrade cycle, not a single broker's cut. [35]
- Shares diluted +16.3% over ~1.7 years (41.9M → 48.8M), steadily eroding per-share claims on the recovering EBITDA base. [36]
- The trailing P/E of 114.3x is a distorted, near-meaningless multiple because trailing EPS $0.21 is anomalous — the OPTICAL headline; the load-bearing bear read is the collapsed forward path (NTM P/E 222.54x on cut estimates), not the trailing figure. [37]
- The stock fell ~37% relative to its small-cap benchmark over 180 days (name -21.7% vs IWM +15.1%), an idiosyncratic de-rate, not a market move. [7]

### Decisive question
**Is the collapsed forward-earnings path a durable impairment of the growth thesis (guidance cut, AMDS/stent-graft shortfall, On-X recall), or a temporary reset around near-floor trailing valuation while the EBITDA base and pipeline keep compounding?**

### …evidence for
- Guidance was lowered and cut again to adj EBITDA $92–99M, and the FY26 GAAP EPS path fell -82%, marking down the very earnings the equity is priced on. [34]
- The core stent-graft line grew only 10% cc in Q1, below expectations on weak U.S. AMDS set sales and soft Middle East demand — the load-bearing driver disappointing. [10]
- An On-X voluntary recall (May-23-2026) directly threatens the second growth engine the bull case relies on. [32]

### …evidence against
- Absolute EBITDA still re-inflected to $61M LTM from a $15M trough, and Q1 adjusted EBITDA rose ~26% — the earnings base is expanding despite the guidance cut. [10]
- On-X still grew 17% cc in Q1 on share gains and a new ~$100M U.S. opportunity, and NEXUS FDA approval completed the aortic-arch portfolio — the pipeline drivers remain live. [30]
- Forward multiples fall steeply on the consensus path (NTM 15.66x → FY28 11.03x), consistent with a base that keeps compounding rather than a permanent impairment. [11]

### Key unknowns
- Adjusted/forward EV/EBITDA and adjusted EPS are not in the revised 99.1 guidance, so a clean forward multiple on the company's own adjusted basis cannot be struck (ev_ebitda_adjusted_fwd and adjusted_eps both UNKNOWN).
- Segment EBITDA is not disclosed — only segment revenue (Products 78% / Preservation 22%) — an expected-disclosure gap that hides where profitability actually sits; treat as a bearish opacity risk.
- The actual/estimate EBITDA basis diverges (estimate columns imply 2.65x the D&A of actuals), so trailing-vs-forward multiples are part definitional and not directly comparable — the human must reconcile before leaning on either.
- Self-funding is MIXED: latest-quarter OCF is positive but LTM levered FCF is negative; whether the business self-funds through the Endospan integration is unresolved.
- The debt schedule is 175 days old and no structured covenant-basis leverage figure exists for this vintage; headroom against the 3.00:1 interest-coverage / max-leverage covenants on the credit facilities is not verifiable from the supplied facts.
- The Endospan acquisition consideration/financing terms and integration cost trajectory are only partially visible; the $116.7M acquisition-consideration line and its impact on leverage and FCF are not fully specified.
- The peer set is HETEROGENEOUS (caps $28M–$68.4B, 2488x span), so every peer-median multiple is a confidence-gated input, not a clean benchmark for a $1.3B name.
- Magnitude and duration of the On-X recall's revenue/margin impact are not quantified in the supplied facts.

### Twin reference cases
- **AtriCure** — recovered
  - distinguished by: In-roster cardiac-device peer that traded on optically extreme earnings multiples through a thin-margin ramp while revenue compounded; the human can weigh whether Artivion's distorted trailing P/E is a similar early-profitability artifact.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **LeMaitre Vascular** — recovered
  - distinguished by: In-roster small-cap vascular-device peer that sustained premium multiples on steady share-gain-driven growth and margin expansion — the pattern Artivion's bull case leans on if the EBITDA re-inflection holds.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **AngioDynamics** — went terminal
  - distinguished by: In-roster device peer whose acquired-growth strategy produced repeated goodwill/intangible write-downs and stalled revenue — the value-trap pattern if Artivion's Endospan and prior deal goodwill fails to earn its keep.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Boston Scientific Corporation** — recovered
  - distinguished by: Large-cap device compounder that levered up for M&A and grew into the balance sheet; an analogue for whether Artivion's above-peer leverage is a temporary funding of a growth platform rather than distress.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **NuVasive** — recovered (LLM-claimed — verify)
  - distinguished by: Mid-cap specialty implant/device maker that carried elevated leverage and thin GAAP earnings while product launches drove share gains before re-rating — a qualitative analogue for a growth-plus-debt device name.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-11-05 `[cadence-estimate]` — the next reported quarter against the committed trajectory [38]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 22.3x vs peer median 27.1x (-18%); P/E 114.3x vs peer median 37.0x (+209%) [23]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-07-29 · multiples as-of 2026-06-30 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [39]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **15.66x** | **$98.3M EBITDA †** |
| peer-median NTM TEV/EBITDA | 21.51x | $71.6M EBITDA |
| peer-median LTM TEV/EBITDA | 27.1x | $56.8M EBITDA |
| **name NTM TEV/Rev** | **3.08x** | **$499.9M Revenue †** |
| peer-median NTM TEV/Rev | 2.56x | $601.5M Revenue |
| peer-median LTM TEV/Rev | 3.1x | $496.7M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $94.3M · FY27E $115.5M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $486.2M · FY27E $539.8M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

### The EV gap — our base case vs the street

_Anchor FY2026 · consensus as-of ≥2026-06-30 (a FLOOR — the export states no as-of, so the true date is on or after this) · TEV as-of 2026-07-29 · form price-implied-only_

- **Total gap:** **0.78x** — our EV against the market's TEV. No consensus enters this figure.

- **Decomposition suppressed:** our margin is a TERMINAL-state assumption and the consensus at this anchor is a NEAR-TERM forecast; a margin RATIO would mix a view difference with a horizon difference in unknown proportion, so the two margins are shown as figures instead

  - _Our EBITDA margin **14.4%** vs consensus **19.4%** at FY2026 — shown as figures, NOT divided: EBITDA margin, ours converted from the recipe's D&A ratio; consensus = median EBITDA / median revenue at the anchor_

- **Bridge:** our EV $1,195M − net debt $202M = equity $993M ÷ 50.200M sh = **$19.77/sh** — against TEV $1,540M.

  - _Revenue dispersion 2.9% (high−low ÷ |median|, FY2026, as-of ≥2026-06-30)_
  - _EBITDA dispersion 5.8% (high−low ÷ |median|, FY2026, as-of ≥2026-06-30)_

  - _D&A convention: ratio of revenue (R2, terminal) — the two recipes differ and the reconciliation is an open analyst question, so it is stated rather than assumed._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 20.6x as-of 2026-07-17 — trailing range 18.8–75.4x (median 32.1x) over 42 closes → 7%ile → near-floor; P/LTM EPS 104.0x [22]

## Peer comps
- **Peer set (roster · caps · business)** — [40]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| AtriCure | $2.1B | engages in the development, manufacture, and sale of devices for surgical ablation of cardiac tissue, exclusion of the left atrial appendage (United States) |
| LeMaitre Vascular | $2.4B | develops, manufactures, and markets medical devices and implants used in the field of vascular surgery in the Americas, Europe, the Middle Esat, Africa (United States) |
| Edwards Lifesciences Corporation | $49.4B | provides products and technologies to treat advanced cardiovascular diseases in the United States, Europe, Japan, and internationally. (United States) |
| AngioDynamics | $605M | designs, manufactures, and sells products for the treatment of cardiovascular disease and cancer diagnoses in the United States and internationally. (United States) |
| Japan Lifeline Co. | $622M | engages in manufacturing and sale of medical device in Japan. (Japan) |
| Boston Scientific Corporation | $68.4B | develops, manufactures, and markets medical devices for use in various interventional medical specialties worldwide. (United States) |
| CVRx | $131M | engages in developing, manufacturing, and commercializing neuromodulation solutions for patients with cardiovascular diseases in the United States, Germany (United States) |
| PROCEPT BioRobotics Corporation | $1.0B | develops transformative solutions in urology in the United States and internationally. (United States) |
| Accuray Incorporated | $28M | engages in the design, development, manufacture, and sale of radiosurgery and radiation therapy systems for the treatment of tumors in the United States (United States) |
| APT Medical Inc. | $4.6B | engages in the research and development, production, and sale of cardiovascular interventional medical devices in China. (China) |

_the name: $1.3B_

- **Comparability (confidence gate):** market caps span $28M–$68.4B (2488x); the name is $1.3B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [24]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [37]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 3.08 | 0.42 | 2.56 | 3.73 | 9.05 |
| NTM TEV/EBITDA | 15.66 | 6.75 | 21.51 | 20.03 | 43.21 |
| NTM P/E | 222.54 | 12.16 | 29.26 | 47.41 | 166.29 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [41]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Boston Scientific Corporation | $68.4B | 13.3 | 3.7 | 18.7 | 28% | 14% | 1.9 | 9,576 |
| Edwards Lifesciences Corporation | $49.4B | 23.3 | 7.1 | 51.2 | 31% | 15% | 0.4 | 2,989 (net cash) |
| APT Medical Inc. | $4.6B | 28.1 | 10.9 | 35.9 | 39% | 25% | 0.0 | 188 (net cash) |
| LeMaitre Vascular | $2.4B | 26.3 | 8.5 | 38.1 | 31% | 13% | 2.3 | 177 (net cash) |
| AtriCure | $2.1B | 55.5 | 3.5 | 193.9 | 6% | 14% | 2.1 | 94 (net cash) |
| **Artivion · the name** | **$1.3B** | **22.3** | **3.4** | **114.3** | **13%** | **18%** | **3.7** | **202** |
| PROCEPT BioRobotics Corporation | $1.0B | NM | 2.6 | NM | -32% | 29% | NM | 168 (net cash) |
| Japan Lifeline Co. | $622M | 6.4 | 1.6 | 10.9 | 25% | 5% | 0.2 | 58 (net cash) |
| AngioDynamics | $605M | 221.8 | 1.8 | NM | 0% | 9% | 4.3 | 43 (net cash) |
| CVRx | $131M | NM | 2.0 | NM | -83% | 12% | NM | 13 (net cash) |
| Accuray Incorporated | $28M | 27.9 | 0.4 | NM | -1% | -8% | 46.2 | 144 |
| Peer median (peers) | $1.5B | 27.1 | 3.1 | 37.0 | 15% | 13% | 2.0 | 76 (net cash) |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [29]  <!-- ds-table -->

|  | Dec-2016 | Dec-2017 | Dec-2018 | Dec-2019 | Dec-2020 | Dec-2021 (R) | Dec-2022 | Dec-2023 (R) | Dec-2024 (R) | Dec-2025 | Mar-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 68% | 69% | 67% | 66% | 66% | 66% | 65% | 65% | 64% | 64% | 65% |

_Revenue YoY (latest same-quarter): +50.7% (Q1 Mar-31-2026 vs Q1 Mar-31-2022). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** diluting (trailing ~1.7y): 41,919,896 (2024-11-01) → 48,756,221 (2026-07-31), +16.3% [36]
- **Non-operating earnings:** no material non-operating item in the four quarters to 2026-06-30 — in the latest, $-3M against $-12M pre-tax [42]
- **Return ratios — per fiscal period** — [43]  <!-- ds-table -->

|  | FY16 | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | 5.9% | 1.5% | -1.0% | 0.6% | -5.4% | -4.7% | -6.6% | -10.8% | -4.8% | 2.7% | 3.1% |
| RoCE % | 4.8% | 1.7% | 1.5% | 2.1% | 0.7% | 0.1% | -0.3% | -0.8% | 2.7% | 2.9% | 3.5% |
| RoA % | 4.2% | 1.5% | 1.3% | 1.8% | 0.6% | 0.1% | -0.2% | -0.7% | 2.2% | 2.3% | 2.8% |
| Total debt/equity | 0.34x | 0.82x | 0.81x | 0.86x | 0.97x | 1.20x | 1.25x | 1.27x | 1.31x | 0.58x | 0.57x |
| Current ratio | 4.89x | 4.18x | 5.19x | 4.15x | 3.88x | 5.51x | 4.98x | 4.85x | 4.34x | 3.53x | 3.86x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-06-30)_
- **Horizon read (FQ — next-2Q revision breadth)** — [35]:
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
- **Acceleration read (monthly consensus path):** FY 2026 EPS (GAAP): 0.45 (12m) → 0.40 (9m) → 0.45 (6m) → 0.36 (3m) → 0.14 (2m) → 0.10 (1m) → 0.08 (latest); net -82% (12m→latest) | FY 2026 EPS Normalized: 0.86 (12m) → 0.84 (9m) → 0.84 (6m) → 0.81 (3m) → 0.49 (2m) → 0.44 (1m) → 0.44 (latest); net -49% (12m→latest) | FY 2026 Revenue: 473.0 (12m) → 485.4 (9m) → 490.2 (6m) → 494.1 (3m) → 486.4 (2m) → 486.4 (1m) → 486.2 (latest); net +3% (12m→latest) | FY 2026 EBITDA: 101.9 (12m) → 104.7 (9m) → 106.5 (6m) → 106.1 (3m) → 96.5 (2m) → 95.3 (1m) → 94.3 (latest); net -7% (12m→latest) | FY 2026 EBIT: 50.6 (12m) → 49.5 (9m) → 50.1 (6m) → 44.6 (3m) → 33.7 (2m) → 33.7 (1m) → 32.6 (latest); net -36% (12m→latest) | FY 2026 Interest Expense: -28.6 (12m) → -25.9 (9m) → -25.2 (6m) → -22.7 (3m) → -27.3 (2m) → -28.5 (1m) → -28.4 (latest); improving (magnitude toward zero) (12m→latest) | FY 2026 EBT (GAAP): 25.3 (12m) → 25.5 (9m) → 25.9 (6m) → 23.1 (3m) → 7.59 (2m) → 6.37 (1m) → 5.32 (latest); net -79% (12m→latest) | FY 2026 Net Income (Excl. Excep): 38.6 (12m) → 40.0 (9m) → 42.3 (6m) → 40.5 (3m) → 24.6 (2m) → 22.0 (1m) → 22.0 (latest); net -43% (12m→latest) | FY 2026 Net Income (GAAP): 21.4 (12m) → 20.4 (9m) → 21.7 (6m) → 19.1 (3m) → 6.15 (2m) → 5.11 (1m) → 4.40 (latest); net -79% (12m→latest)  [data ≥ 2026-06-30 · export date unverified] [34]
- **Cross-name anchor (NTM forward-multiple ladder)** — [11]:
  - NTM: TEV/REV 3.08 · TEV/EBITDA 15.66 · TEV/EBIT 39.58 · Price/Earnings 222.54 · PEG –
  - FY 2026: TEV/REV 3.17 · TEV/EBITDA 16.33 · TEV/EBIT 47.27 · Price/Earnings – · PEG –
  - FY 2027: TEV/REV 2.85 · TEV/EBITDA 13.33 · TEV/EBIT 26.42 · Price/Earnings 67.61 · PEG –
  - FY 2028: TEV/REV 2.56 · TEV/EBITDA 11.03 · TEV/EBIT 19.17 · Price/Earnings 34.87 · PEG –
  - _+2 later fiscal years in JSON_
- **Current guide (latest results filing):** revenue 2026: 480.0–496.0 $M; adjusted ebitda 2026: 92.0–99.0 $M [44]
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [45]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | '480.00 - 496.00' | FY 2026 | 2026-05-07 | 97d (stale) | actual ≥ floor 28/39 · 2 at-guide (±0.5% of a point, not adjudicated) | FY 2025 MET |
| EBITDA | '100.00 - 107.00' | FY 2026 | 2026-05-07 | 97d (stale) | actual ≥ floor 3/4 | FY 2025 MET |
| Capital Expenditure | -50.0 | FY 2026 | 2026-02-12 | 181d (stale) | — | — |
| Gross Margin % | 64.9 | FY 2026 | 2026-02-12 | 181d (stale) | actual ≥ floor 3/6 | FY 2024 MISSED |
| Free Cash Flow | 0.00 | FY 2026 | 2026-02-12 | 181d (stale) | — | — |
| EPS Normalized | none current (last: '0.28 - 0.32') | FY 2019 | 2019-10-30 | 2478d (stale) | actual ≥ floor 5/7 | FY 2019 MET |
| EPS (GAAP) | none current (last: '0.09 - 0.11') | FY 2015 | 2015-10-27 | 3942d (stale) | actual ≥ floor 5/8 | FY 2015 MET |
| EBIT | none current (last: 13.7) | FY 2009 | 2009-07-30 | 6222d (stale) | actual ≥ floor 1/1 | FY 2009 MET |
| Effective Tax Rate % | none current (last: 20.0) | FY 2018 | 2018-10-31 | 2842d (stale) | spend ≤ ceiling 7/10 | FY 2018 MISSED |

_CIQ states every guide as a LEVEL in the metric's own units. Where management guided a RATE, the level is CIQ's arithmetic on its own base, not a figure the company published — check the release before quoting one as guidance._

- **Consensus stats (target + ratings):** Target price: mean $42.00, median $43.00, high/low 48.00/36.00, N 8/8; Ratings: Buy 6, Outperform 2, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-06-30 · export date unverified] [25]
- **Revision-event log (250 events · 17 broker-days)** — [46]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-06-30 | Ladenburg Thalmann & Company | 20 | 1 | 17 | 2 | EBITDA FQ2 2026 | 25.6 | 22.5 | −3.0 |
| 2026-06-23 | Needham & Company | 13 | — | 13 | — | EBITDA FY 2026 | 100.3 | 91.8 | −8.5 |
| 2026-06-09 | Lake Street Capital Markets, LLC | 12 | — | 12 | — | EPS Normalized FQ2 2026 | 0.1 | 0.1 | −0.05 |
| 2026-05-20 | Freedom Capital Markets | 29 | — | 29 | — | EBITDA FQ2 2026 | 29.4 | 24.1 | −5.3 |
| 2026-05-08 | Citizens JMP Securities, LLC | 21 | — | 21 | — | EBITDA FQ2 2026 | 26.4 | 22.0 | −4.4 |
| 2026-05-08 | Freedom Capital Markets | 9 | — | — | 9 | — | — | — | — |

_+11 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2004 +0%, FY2005 +0%, FY2006 +0%, FY2007 +24%, FY2008 +152%, FY2009 +3%, FY2010 +0%, FY2011 +0%, FY2012 +4%, FY2013 -5%, FY2014 +4%, FY2015 +56%, FY2016 +7%, FY2017 -62%, FY2018 +0%, FY2019 -44%, FY2020 +0%, FY2021 +0%, FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 -9%; Revenue surprise: FY2000 -3%, FY2001 -1%, FY2002 -2%, FY2003 -1%, FY2004 +0%, FY2005 +0%, FY2006 +0%, FY2007 +0%, FY2008 -2%, FY2009 -0%, FY2010 -0%, FY2011 -1%, FY2012 -0%, FY2013 +0%, FY2014 -0%, FY2015 -0%, FY2016 -1%, FY2017 +2%, FY2018 +0%, FY2019 -0%, FY2020 +1%, FY2021 +1%, FY2022 -0%, FY2023 +1%, FY2024 -1%, FY2025 -0% (GAAP-EPS basis; +beat / −miss) [47]

## Leverage & survival
- **Net debt / EBITDA [NET]:** 3.3x [8]
- **Total debt / EBITDA vs peers:** name 3.7x vs peer median 2.0x (comps TOTAL-debt/EBITDA basis) [12]
- **Net debt / OCF:** 3.5x [48]
- **Interest coverage:** 2.5x [49]
- **Self-funding:** self-funding: MIXED — latest-Q OCF > 0, LTM FCF < 0 (both must be positive to self-fund) [50]
- **Credit health** — [51]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 4 | 2.5 |
| Operational | 3 | 2.5 |
| Solvency | 3 | 2.5 |
| Liquidity | 4 | 2.5 |

_S&P issuer rating NR · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [9]
- **Free cash flow ($M):** -7.3 — basis: CIQ 'Levered Free Cash Flow', NOT CFO − capex — and the two carry OPPOSITE SIGNS: on the same sheet and period [LTM 12 months Mar-31-2026], CFO $58.0M − capex $43.4M = $14.6M. One says the business generated cash this period and the other says it consumed it; the basis decides which, so name it before quoting either. [13]
- **Debt schedule vintage:** the debt schedule is 175d old (source filed 2026-02-18); no Item 1.02 (termination of a material agreement) has been filed since [52]
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Feb-18-2026** — [53]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Convertible Senior Notes | Bonds and Notes | – | 4.250% | NA | 2025-07-01 | N | Y | USD |
| Notes Payable | Bonds and Notes | $0.9M | 6.050% | NA | 2026-04-01 | N | N | USD |

_6 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-08-12 reference:
  - **matured (pre-reference): $0.9M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2025-07-01 (407d before ref): – Convertible Senior Notes
    - 2026-04-01 (133d before ref): $0.9M Notes Payable
  - due 2031: $220.0M
  - undated (floor — no panel maturity): $42.5M — 1.40% Sparkasse Zollernalb KFW… –, Finance Lease Obligation $3.4M, Operating Lease Liabilities $39.1M
  - _reconciliation: itemized $263.4M (panel A 2025 filed Feb-18-2026) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** term loans 190.0 (3 months Q4 Dec-31-2025 190.0 → 3 months Q1 Mar-31-2026 190.0); leases 42.8; total principal 262.8; total debt 258.2 (3 months Q1 Mar-31-2026) ($M) [54]
- **Covenants — Convertible Senior Notes** (governing values; full verbatim in appendix):
  - **Conversion:** ⇒ ~$23.46/sh at 42.6203 sh per $1,000 · Initial Conversion Rate: 42.6203 shares of the Issuer's common stock per $1,000 principal amount of Notes. Initial Conv…
  - **Interest / coupon:** Fixed + 4.25% · 4.250% per year
  - **Maturity:** July 1, 2025 · July 1, 2025
  - **Conversion:** in no event will the conversion rate per $1,000 principal amount of Notes exceed 57.5373 shares
- **Covenants — New Delayed Draw Term Loan Facility** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LIBOR + 3.50% · At Borrowers' option: Base Rate + Applicable Margin, or LIBOR + Applicable Margin. Initial Applicable Margin: 2.50% (Ba…
  - **Maturity:** Term Loan: term of five years from the Closing Date. Revolving Credit Facility: until the fifth anniversary of the Clos…
  - **Financial maintenance:** Minimum interest coverage of 3.00:1.00; and maximum total leverage multiple (levels to be agreed, reflecting a cushion…
  - **Events of default:** Mandatory prepayments (per Section 2.8 of Negotiated Credit Agreement): (a) Excess Cash Flow – 50% (reducing to 25% at…
- **Covenants — Secured Revolving Credit Facility** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LIBOR or Base Rate plus Applicable Margin. Initial Applicable Margin: Base Rate Loan 2.50%, LIBOR Rate Loan 3.50%; ther…
  - **Maturity:** January 20, 2021 · Revolving Termination Date: January 20, 2021; final Term Loan installment due January 20, 2021 ($56,250,000.00)
  - **Financial maintenance:** Leverage Ratio (max 3.50:1.00 stepping down to 2.75:1.00 by 12/31/2017); Interest Coverage Ratio (min 3.00:1.00); Equit…
  - **Events of default:** Mandatory prepayments: scheduled Term Loan amortization (Sec 2.8(a)); Revolving overadvance; Asset Dispositions/Events…

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
- Panel-freshness caveat — 2 CIQ valuation panel(s) predate the latest earnings print (2026-08-06, EDGAR 8-K item 2.02), the oldest by 37d: valuation multiples as-of 2026-06-30; implied-TEV inputs as-of 2026-07-29. The valuation read may rest on a pre-print P&L — re-pull CIQ after the print before relying on it.

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
| CFO ($M) | 20 | 11 | 10 | 16 | 12 | -3 | -5 | 19 | 22 | 40 | 58 | 37 | 61 |
| Capex ($M) | -6 | -7 | -6 | -8 | -7 | -13 | -11 | -10 | -11 | -39 | -43 | -28 | -42 |
| FCF (levered, CIQ) | 4 | -18 | 9 | -4 | 5 | -21 | 0 | -4 | 0 | -20 | -7 | — | — |
| D&A ($M) | 8 | 10 | 18 | 18 | 21 | 24 | 22 | 23 | 24 | 22 | 23 | — | — |
| FCF (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | — | -19 | 19 |
| D&A (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | — | 27 | 30 |

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
| material contracts (10-K exhibit index) | latest 10-K | 2026-02-18 | 0001628280-26-009046 — aort-20251231xexx1032.htm |
| 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank | 8-K | 2026-05-18 | 0001628280-26-035798 — aort-2026x8k03312026ex101.htm, aort-2026x8k03312026ex102.htm, aort-2026x8k03312026ex103.htm |
| 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank | 8-K | 2026-05-07 | 0001628280-26-032097 — aort-2026x8k033126ex101.htm, aort-2026x8k033126ex102.htm, aort-2026x8k033126ex103.htm |
| Convertible Senior Notes | 8-K | 2020-06-23 | 0001193125-20-176533 — d946474dex101.htm |
| Convertible Senior Notes | 8-K | 2025-09-29 | 0001628280-25-043099 — ex-101.htm, ex-102.htm |
| New Delayed Draw Term Loan Facility | 8-K | 2015-12-23 | 0000784199-15-000171 — c199-20151222ex101949499.htm |
| New Delayed Draw Term Loan Facility | 8-K | 2024-01-18 | 0000950157-24-000061 — ex10-1.htm |
| Secured Revolving Credit Facility | 8-K | 2016-01-25 | 0000784199-16-000175 — c199-20160125ex101fad737.htm, c199-20160125ex1021c6f6c.htm |
| Secured Revolving Credit Facility | 8-K | 2017-12-01 | 0001398344-17-015456 — fp0029473_ex101.htm |
| Secured Term Loan Facility | 8-K | 2025-09-15 | 0000784199-25-000145 — ex101.htm |
| Finance Lease Obligation | — | — | no contract-level filing expected (aggregate line item) |
| Notes Payable | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — 1.40% Sparkasse Zollernalb KFW Loan 2 with Kreditanstalt fur Wiederaufbau Bank (governing agreement)** — [78]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Principal / commitment amount | up to $15 million (the “Buyer Loan”); initial tranche of $5,000,000 (“Initial Loan Tranche”) | base (footer) |
| Interest / coupon rate | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Maturity date | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Security / collateral / guarantors | Debenture granting Buyer a perfected security interest in all of the Company's assets (other than the Horizon Assets), junior in priority to the charge granted to JLL under the JLL Loan | base (footer) |
| Mandatory prepayment / events of default | UNKNOWN | not stated in 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm |
| Option Fee | $1,000,000 payable within fourteen (14) Business Days of the Effective Time | base (footer) |
| Acquisition Consideration / Base Amount | Base Amount = $250,000,000 in cash | base (footer) |
| Additional Consideration Amount | Greater of Additional Consideration Minimum Amount ($100,000,000) or 5x the specified revenue increase; capped at $200,000,000 | base (footer) |
| Indemnity Escrow Amount | $23,500,000 plus Additional Indemnity Escrow Amount | base (footer) |
| Adjustment Escrow Amount | $1,000,000 | base (footer) |
| Governing law | State of Delaware | base (footer) |
| Termination / Option Period | Option Period beginning as of Effective Time and ending 90 days following the Company's receipt of FDA Approval | base (footer) |

_Source §: 8-K 0001628280-26-035798 · aort-2026x8k03312026ex101.htm_

- **Covenant terms — Convertible Senior Notes (governing agreement)** — [78]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | ⇒ ~$23.46/sh at 42.6203 sh per $1,000 · Initial Conversion Rate: 42.6203 shares of the Issuer's common stock per $1,000 principal amount of Notes. Initial Conversion Price: Approximately $23.46 per share of the Issuer's common stock. Conve… — full verbatim in JSON | base (footer) |
| Principal / commitment amount | $100,000,000, plus up to an additional $15,000,000 principal amount pursuant to the initial purchaser's option to purchase additional Notes | base (footer) |
| Interest / coupon rate | Fixed + 4.25% · 4.250% per year | base (footer) |
| Maturity date | July 1, 2025 · July 1, 2025 | base (footer) |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0001193125-20-176533 · d946474dex101.htm |
| Security / collateral / guarantors | UNKNOWN | not stated in 8-K 0001193125-20-176533 · d946474dex101.htm |
| Mandatory prepayment / events of default | UNKNOWN | not stated in 8-K 0001193125-20-176533 · d946474dex101.htm |
| Optional redemption | The Issuer may not redeem the Notes prior to July 5, 2023. The Issuer may redeem for cash all or part of the Notes ... on or after July 5, 2023 if the last reported sale price ... has been at least 1… — full verbatim in JSON | base (footer) |
| Ranking / seniority | 4.250% Convertible Senior Notes due 2025 | base (footer) |
| Purchase price / discount | 97.00% of the principal amount thereof (the "Purchase Price") plus accrued interest | base (footer) |
| Make-whole fundamental change conversion rate increase | in no event will the conversion rate per $1,000 principal amount of Notes exceed 57.5373 shares | base (footer) |
| Sinking fund | No "sinking fund" is provided for the Notes | base (footer) |
| Denominations | $1,000 and multiples of $1,000 in excess thereof | base (footer) |

_Source §: 8-K 0001193125-20-176533 · d946474dex101.htm_

- **Covenant terms — New Delayed Draw Term Loan Facility (governing agreement)** — [78]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0000784199-15-000171 · c199-20151222ex101949499.htm |
| Principal / commitment amount | $95,000,000 total ($75,000,000 Term Loan Facility; $20,000,000 Revolving Credit Facility; $4,000,000 Letter of Credit sub-facility; $3,000,000 Swing Line sub-facility). Initial Lender commitments: HF… — full verbatim in JSON | base (footer) |
| Interest / coupon rate | LIBOR + 3.50% · At Borrowers' option: Base Rate + Applicable Margin, or LIBOR + Applicable Margin. Initial Applicable Margin: 2.50% (Base Rate) / 3.50% (LIBOR) for both Term Loan and Revolving. Thereafter set per Pr… — full verbatim in JSON | base (footer) |
| Maturity date | Term Loan: term of five years from the Closing Date. Revolving Credit Facility: until the fifth anniversary of the Closing Date. (No calendar date stated.) | base (footer) |
| Financial-maintenance covenants | Minimum interest coverage of 3.00:1.00; and maximum total leverage multiple (levels to be agreed, reflecting a cushion to the financial model of 25% to 30%). Cure right per Section 7.3 of the Negotia… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Collateral: first priority perfected security interests (subject to permitted liens) in substantially all existing and after-acquired real and personal property of Borrowers and each Guarantor, inclu… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | Mandatory prepayments (per Section 2.8 of Negotiated Credit Agreement): (a) Excess Cash Flow – 50% (reducing to 25% at total leverage 2.50x and 0% at 1.50x), less voluntary prepayments; (b) Debt Issu… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0000784199-15-000171 · c199-20151222ex101949499.htm_

- **Covenant terms — Secured Revolving Credit Facility (governing agreement)** — [78]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0000784199-16-000175 · c199-20160125ex101fad737.htm |
| Principal / commitment amount | $95,000,000 Credit Facility; Aggregate Term Loan Commitment $75,000,000; Aggregate Revolving Loan Commitment $20,000,000; Swingline Commitment $3,000,000; L/C Sublimit $4,000,000 | base (footer) |
| Interest / coupon rate | LIBOR or Base Rate plus Applicable Margin. Initial Applicable Margin: Base Rate Loan 2.50%, LIBOR Rate Loan 3.50%; thereafter grid based on Leverage Ratio (LIBOR Margin 2.75%–3.75%; Base Rate Margin… — full verbatim in JSON — ⚠ QA: rate component 0 not stated in the clause — lead suppressed | base (footer) |
| Maturity date | January 20, 2021 · Revolving Termination Date: January 20, 2021; final Term Loan installment due January 20, 2021 ($56,250,000.00) | base (footer) |
| Financial-maintenance covenants | Leverage Ratio (max 3.50:1.00 stepping down to 2.75:1.00 by 12/31/2017); Interest Coverage Ratio (min 3.00:1.00); Equity Cure (Section 7.3) | base (footer) |
| Security / collateral / guarantors | Secured by Liens on substantially all assets of the Credit Parties (Guaranty and Security Agreement, Mortgages, Control Agreements); guaranteed by Borrowers and Domestic Subsidiary Credit Parties; pl… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | Mandatory prepayments: scheduled Term Loan amortization (Sec 2.8(a)); Revolving overadvance; Asset Dispositions/Events of Loss (>$1,500,000, subject to reinvestment); Incurrence of Debt/Specified Equ… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0000784199-16-000175 · c199-20160125ex101fad737.htm_

- _6 located agreement exhibit(s) not extracted this run (cost bound / fetch fail) — see the pointer table: 0000784199-25-000145, 0000950157-24-000061, 0001398344-17-015456, 0001628280-25-043099, 0001628280-26-009046, 0001628280-26-032097_

### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 1337.4 [79]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $55.80M, − total debt $258.20M [80]
- **Implied equity at peer-median ($M, CIQ)** — [81]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 1,462.3 |
| NTM Revenue (Capital IQ) | 1,078.7 |
| NTM EBITDA (Capital IQ) | 1,912.6 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [82]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 0 · sells 28 (7 insiders, $5.92M) — in the last 182 days · last purchase $0.04M, director, 2025-03-05 (~17mo ago) · last sale $0.03M, SVP, General Counsel, 2026-08-12 (~0mo ago) · largest sale $1.75M, President & CEO, 2025-03-06 (~17mo ago) · grants 84 · last filing 2026-08-12 · other filings 31 [83]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-07-31): 2.5M → 2.7M sh (+8.3%, rising) · 5.5% of shares out (EDGAR XBRL) · DTC 3.6d · recent: 2026-07-31 2.7M · 2026-07-15 2.5M · 2026-06-30 2.2M · 2026-06-15 1.9M [84]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [85]
- **Guide verification — CIQ guide vs release:** revenue: CIQ 480.0–496.0 vs release 480.0–496.0 → cross-source VERIFIED [86]

## Record & reproduce
- **Data window:** screened as of 2026-08-12 · assembled 2026-08-13 15:17 UTC
- **Extraction:** 2026-07-28.1 — unusual-items surfacing in the financial summary (#238) · multiples read from the latest close, NM rather than a stale figure (#241)
- **Price store:** `mosaic-theory-pg → mosaic-theory-wb` · reaching 2026-08-12
- **Panel age:** oldest panel 15d old — 2026-07-29 (valuation.implied_expectations.tev_as_of), against a 2026-08-13 build
- **Consensus age:** consensus 44d old (2026-06-30, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0000784199` · NYSE : AORT
- **Assembly log:** primary-source: 6 EX-99.1 release(s) + 1 10-Q parsed (+0.6s fetch)
- **Re-run:** `python -m vinci dossier --ticker AORT` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[5] `EOD AORT 180d to 2026-08-12`
[6] `EOD IWM 180d to 2026-08-12 (cap-band: $1.3B @ 2026-08-12 → small (<$4B) → IWM)`
[7] `EOD AORT−IWM 180d to 2026-08-12 (assembly, cap-band)`
[8] `CIQ Net Debt $202M [Q1 Mar-31-2026] ÷ CIQ EBITDA $61M [LTM 12 months Mar-31-2026]`
[9] `EDGAR XBRL FCF sign (screen data-record)`
[10] `CIQ transcript: Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf`
[11] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[12] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-07-30`
[13] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
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
[28] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[29] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[30] `CIQ Key Developments: Artivion Inc NYSE AORT Key Developments.rtf · Apr-07-2026`
[31] `CIQ Estimates→Consensus`
[32] `CIQ Key Developments: Artivion Inc NYSE AORT Key Developments.rtf · May-23-2026`
[33] `8-K 0001628280-26-054294 EX-99.1`
[34] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[35] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[36] `EDGAR XBRL shares, trailing 2024-11-01..2026-07-31`
[37] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[38] `cadence: EDGAR submissions (median 91d gap over 43 results 8-Ks; last print 2026-08-06)`
[39] `TEV = mcap 1337.4 + net debt 202.4 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-07-29, exported 2026-07-30) — simple-TEV basis`
[40] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[41] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-07-30`
[42] `EDGAR XBRL pre-tax − operating, quarters 2025-06-30..2026-06-30`
[43] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[44] `8-K 0001628280-26-054294 EX-99.1 (filed 2026-08-06)`
[45] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record) — CIQ states every guide as a LEVEL; where management guided a RATE, the level is CIQ's arithmetic, not the company's published figure`
[46] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-06-30 · export date unverified]`
[47] `CIQ Estimates→Surprise (annual)`
[48] `CIQ Net Debt $202M [Q1 Mar-31-2026] ÷ CIQ OCF $58M [LTM 12 months Mar-31-2026]`
[49] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Mar-31-2026]`
[50] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[51] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-07-30`
[52] `CIQ Capital Structure Details — A 2025 filed Feb-18-2026`
[53] `CIQ Financials→Capital Structure Details (A 2025 filed Feb-18-2026)`
[54] `CIQ Financials→Capital Structure Summary`
[55] `10-Q 0001628280-26-054746`
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
[79] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-07-30`
[80] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-07-30`
[81] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-07-30`
[82] `CIQ transcript(s): Artivion, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf; Artivion, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf`
[83] `EDGAR Form 4 (latest 0001628280-26-056381; 166 filings in the 1095d scanned; counts over 182d)`
[84] `FINRA consolidated short interest (settle 2026-07-31); DTC = 2,705,501 short ÷ 752,868 screen 90d ADV`
[85] `10-Q maturity wall vs CIQ capital panel (same window)`
[86] `CIQ revenue guide vs release actual/outlook`