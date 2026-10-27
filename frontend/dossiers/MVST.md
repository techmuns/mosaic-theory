# Dossier — Microvast Holdings, Inc. (Nasdaq: MVST)

_September 17, 2026 · extraction 2026-08-16.1 · layers refreshed to 2026-10-09.3_

# Brief — first cut

## At a glance
**Target (base)** $0.60 (-34.7% vs entry-vintage spot) · **Spot** $0.92 (entry-vintage — frozen at underwrite 2026-07-22) · **Reward** $-0.32 · **Risk** $0.97 · **Reward : risk** -0.33 : 1 (bar 2 : 1) · **Base IRR** 3.4% (floor 15%, 4y) · **Gate** FAIL (both tests)

_judged under the 2:1 / 15% regime (pre-2026-08-21; tiers not applied)_

_Spot source: Polygon MVST close 2026-07-21 (live at underwrite)_

**Underwrite disposition:** WATCH (2026-07-22) — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

### Thesis — our rationale
_Prices quoted below are entry-vintage (2026-07-21); the live close is in Snapshot, above._

WATCH at $0.92. The underwrite fails our 2:1 bar: the base case is worth roughly the market price in today's terms, so the price pays nothing for the very real chance the equity is worth zero - the company's own filings state substantial doubt it can continue, a debt wall comes due within a year against roughly matching cash, and the share count is compounding double-digit through an open selling programme. The gross-margin turnaround is real engineering - from deeply negative to thirty percent in three years - which is why this stays on the watch list at all. We revisit on a completed refinancing, or on returning growth with cash generation.

### What would reopen this name

- the maturity wall is refinanced or extended (a material-agreement or debt-obligation filing) - re-underwrite survival
- two consecutive quarters of positive revenue growth AND positive operating cash flow - the rollover was a squeeze, not a break; re-underwrite the central and optimistic cases
- going-concern language removed in a periodic filing - re-underwrite in full

> ⚠ **Verify before the verdict:** wall coherence: divergence with an instrument maturing within ±7d of the +12m boundary (Short-term Loan Agreements an…; Net debt/EBITDA (1.6x) is on CIQ's EBITDA (vendor-normalised, not the reported GAAP figure), not the covenant basis — full caveats in Analysis.

Microvast Holdings, Inc. engages in the design, development, and manufacturing of battery components and systems primarily for electric commercial vehicles and energy storage systems.
- **Segments:** Batteries / Battery Systems — single segment [1]
- **Geography:** China 33%; Italy 22%; France 18%; Other Europe 10%; U.S. 9%; India 8%; Other Asia & Pacific 1% [2]
- **Customer concentration:** top customer 46% (from 18%) · top-2 ~57% of revenue [3]
- **Snapshot:** Nasdaq · CMP $0.59 (2026-09-16) · cap $354M (2026-08-12) ⚠ implies $0.92/sh vs CMP (+57.1%) · 52-wk $0.56–$7.12 · shares 384.5M · book value/sh $1.41 [4]

**The crux — what decides this, and what would change our mind**
**Can Microvast clear the ~$104M twelve-month maturity wall (refinance/repay/convert) and re-accelerate sales volume before the going-concern doubt resolves against it — i.e. is the de-rating a fundable overshoot or a terminal liquidity/demand spiral?**
_7 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-11-11 `[cadence-estimate]` — calendar in Analysis

## What happened — and can it survive?
- **Shape:** discrete gap-downs — 2026-03-17 earnings; 2026-05-12 earnings; 2026-05-18 no company filing [5]
- **Price (180d):** -66.7% [6]
- **Market (IWM) 180d:** 12.6% [7]
- **vs market (180d):** -79.3% [8]
- **Net debt / EBITDA:** 1.6x [9]
- **Free cash flow:** positive [10]
- **Going concern:** ⚠ SUBSTANTIAL DOUBT stated [3]

## Scenario analysis
_Terminal-margin: value the business in the year it reaches a normal operating margin, then discount that value back at the house waiting charge._

| scenario | revenue $M | margin | multiple | value / sh | vs entry-vintage spot |
| --- | ---: | ---: | ---: | ---: | ---: |
| bear | 550 | 2.0% | 6x | $-0.05 | -105.4% |
| base | 850 | 6.0% | 7.9x | $0.60 | -34.7% |
| bull | 1,000 | 10.0% | 10x | $1.50 | +63.4% |

- **bear** — the contraction proves durable: the largest customer (52% of revenue) wobbles, revenue stabilizes well below the peak run-rate, margins hold barely positive as a marginal producer; a levered, distressed supplier exit.
- **base** — revenue recovers on the consensus path with a haircut for the current -25% quarter; margin reaches levered-auto-supplier economics rather than the street's cut-but-still-hopeful path; exit at the closest economic analogue (a levered auto-parts maker at 7.9x), not the scale leader's multiple.
- **bull** — the gross-margin engineering (-28% to +31% in three years) carries through: revenue re-accelerates, double-digit operating margin arrives, partial deleveraging earns a step above the analogue.

**Scenario inputs** — every value in the grid recomputes from these.

| input | value | basis | source |
| --- | ---: | --- | --- |
| net debt | 199.9 $M | classified total debt less total cash and short-term investments, latest balance sheet [VENDOR BASIS: CIQ workbook; EDGAR has no depreciation tag for this filer] | CIQ Financials->Balance Sheet (vendor basis; EDGAR debt tags under-captured) |
| diluted shares | 386.069384 shares | Diluted shares outstanding 386,069,384 = basic outstanding 333,157,384 + dilutive increment 52,912,000 (diluted 385,272,000 − basic 332,360,000 weighted average, 2026-01-01→2026-03-31). The dilutive increment is carried from the reporting period to the valuation date, which assumes the dilutive count has not moved since. Excluded from the filer's diluted average: antidilutive instruments (a loss period reports no dilution at all under ASC 260); out-of-the-money options, which contribute nothing under the treasury-stock method; any change in the dilutive count between the reporting period and the valuation date. | EDGAR dei:EntityCommonStockSharesOutstanding + us-gaap:WeightedAverageNumberOf{SharesOutstandingBasic,DilutedSharesOutstanding} — item 24 denominator swap |
| d and a ratio | 0.08941 rate | depreciation and amortisation over trailing revenue (33.228 / 371.637) [VENDOR BASIS: CIQ workbook; EDGAR has no depreciation tag for this filer] | CIQ Financials->Cash Flow and Income Statement (vendor basis) |
| share growth | 0.1 rate | OVERRIDE. The organic three-year compound rate (2.30%) cannot see the open $125M at-the-market programme already drawn +19% in two quarters; 10% a year approximates full remaining draw near current prices plus organic issuance. | EDGAR 8-K Item 1.01 accession 0000947871-25-000881 and the 424B5 of 2025-10-03 (Controlled Equity Offering Sales Agreement, up to $125,000,000); share series FY2022-FY2025 |
| burn to breakeven | 307.8 $M | three years at the stated current burn (102.60 x 3) - the survival block's years to breakeven | EDGAR 10-Q accession 0001628280-26-033590, quarter ended 2026-03-31 |

_Chain (EV/EBITDA):_ EBIT_T = terminal revenue × terminal margin → D&A_T = (latest-FY D&A ÷ latest-FY revenue) × terminal revenue → EBITDA_T = EBIT_T + D&A_T → EV_T = denominator_T × exit multiple   (denominator = EBITDA_T, or EBIT_T on EV/EBIT) → net debt_T = current net debt + cumulative burn to breakeven → equity_T = EV_T − net debt_T → shares_T = current diluted × (1 + share growth)^years + announced-raise shares → value_T = equity_T ÷ shares_T → PV = value_T ÷ (1 + hurdle)^years

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | R2_NEEDED | R1 screen: NOT applicable |
| Overall confidence | — |  |

_no positive operating margin over available history — needs revenue-anchored recipe_

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the decline is overdone:_
- The European franchise is inflecting up — European sales rose 35% year-over-year in Q2 2026 and reached 61% of quarterly revenue (from 43%), a mechanism-level offset to the APAC decline, though its continuation line notes year-to-date Europe was still down 3% on prior platform-rollout delays. [11]
- Consensus models a forward recovery — FY26E EBITDA $62.1M rising to FY27E $147.7M and revenue $444.4M to $591.5M — with both covering analysts rating Buy and a $5.50 mean target, well above the $0.59 close. [12]
- The multi-year arc shows a genuine operating turn: absolute EBITDA swung from −$85M (FY23) to +$5M (FY24) to +$74M (FY25), and gross margin climbed from 19% (FY23) to 36% (FY25) — a real structural improvement, not merely a margin-percentage optic. [13]
_Bear case — the decline is real:_
- The latest 10-Q states SUBSTANTIAL DOUBT (going concern) — a filed disclosure that is the single load-bearing terminal signal and outweighs any peer-relative cheapness. [3]
- A near-term maturity wall of $104.2M is due within twelve months on the filing basis, against $128M cash — the survival crux, and the filing figure DIVERGES from the CIQ panel's same-window $98.5M by more than tolerance, so the exact wall itself is uncertain. [3]
- Comps-basis total-debt/EBITDA is 4.3x versus a peer median of 1.6x, and the name is diluting (+18.8% shares over ~1.7y) with a $25.0M shareholder loan converted to stock in May 2026 — a heavier balance sheet and ongoing equity issuance. [14]

## Financial snapshot
- **Financial snapshot** — [15]  <!-- ds-table -->

|  | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 204 | 307 | 380 | 428 | 368 | 444 | 592 |
| Revenue growth | — (basis) | +50% | — (basis) | +13% | — (basis) | +4% (vs FY25) | +33% |
| EBITDA ($M) | -140 | -85 | 5 | 74 | 41 | 62 | 148 |
| EBITDA margin | -68% | -28% | 1% | 17% | 11% | 14% | 25% |
| EBIT ($M) | -160 | -108 | -26 | 40 | 8 | 20 | 69 |
| Net income ($M) | -158 | -106 | -196 | -29 | 51 | 70 | 56 |
| EPS (GAAP, dil.) | -0.52 | -0.34 | -0.61 | -0.09 | -0.02 | 0.18 | 0.17 |
| FCF (levered, CIQ) | -136 | -117 | -65 | 18 | 63 | — | — |

_FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

_table shows the last 4 fiscal years · 4 earlier years are in the Appendix_

> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 61 of D&A against 21 in the actuals (2.93x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.


**Capital allocation — created or destroyed**

- **Impairment headroom — intangibles remaining:** $2.0M [16]
- **Goodwill:** _UNKNOWN_ — no goodwill balance under any of Goodwill — EDGAR XBRL companyfacts
- **Intangibles (net):** $2.0M [16]
- **Impairment:** _NONE IN THE CURRENT PERIOD_ — the filer records no impairment under any tag tried
- **Buyback — cash:** _UNKNOWN_ — no share-repurchase cash under any of PaymentsForRepurchaseOfCommonStock — EDGAR XBRL companyfacts
- **Buyback — shares repurchased:** _UNKNOWN_ — no annual repurchased-share count under TreasuryStockSharesAcquired — EDGAR XBRL companyfacts
- **Buyback — average cost/share:** _UNKNOWN_ — no TreasuryStockAcquiredAverageCostPerShare, and the cash leg is absent — refused rather than derived (EDGAR XBRL companyfacts). The repurchase CASH and SHARE COUNT above are each sound on their own basis; it is their QUOTIENT that is not a price
- **Acquisition consideration:** _UNKNOWN_ — no acquisition consideration under any of BusinessCombinationConsiderationTransferred1, BusinessCombinationConsiderationTransferred, PaymentsToAcquireBusinessesNetOfCashAcquired — EDGAR XBRL companyfacts
- **Registered offering pipeline (equity/debt not distinguished):** shelf registrations 2 (S-3/S-3/A, last 2025-04-28); prospectus supplements 1 (424B5, last 2025-10-03) — 3y window to 2026-08-24 [17]
- **Schedule 13D/G filing activity:** Schedule 13D filings 1 (SC 13D/A, last 2024-11-21) · Schedule 13G filings 3 (SC 13G/SC 13G/A/SCHEDULE 13G/A, last 2026-02-13) — 3y window to 2026-08-24 [18]
- **Stock-based compensation:** stock-based compensation $3.1M = 0.7% of revenue ($427.5M, FY 2025-01-01→2025-12-31) [19]
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [20]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap | why |
|---|---:|---:|---:|---:|---:|---|
| **MVST** | **354** | **2** | **952** | **0%** | **1%** | **—** |
| 300750 | 274,050 | — | — | — | — | unresolved |
| CMI | 87,809 | 4,390 | 35,630 | 12% | 5% | — |
| 6752 | 67,066 | — | — | — | — | unresolved |
| A006400 | 26,687 | — | — | — | — | unresolved |
| BWA | 14,022 | 2,402 | 13,934 | 17% | 17% | — |
| AMPX | 1,788 | — | 149 | — | — | no-tag |
| LECN | 166 | — | — | — | — | unresolved |
| ALFOR | 32 | — | — | — | — | unresolved |

- **Median — all peers (n=2):** 15% of assets · 11% of market cap
- **Median — peers ≥ $1,000M market cap (n=2):** 15% of assets · 11% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [21]  <!-- ds-table -->

|  | state | yrs charged | window $M | % acquired | last charge (any date) | live YTD $M |
|---|---|---|---|---:|---:|---|
| **MVST** | **reports nil** | **0 of 5** | **—** | **—** | **never** | **—** |
| CMI | wrote down | 2 of 2 | 111 | 3% | 2025-12-31 ($27M) | — |
| BWA | wrote down | 2 of 2 | 1,027 | 43% | 2025-12-31 ($423M) | — |
| AMPX | does not tag | — | — | — | never | — |

- **Base rate — 2 of 2 large peers ASSESSED over the window took a charge**, median 23% of acquired assets among those that did. The denominator counts only peers with an annual observation in the window — a name with none was not measured, and is not a clean year.
- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. `no annual obs.` and `does not tag` are not measurements and must not be read as clean years. The **live YTD** column is excluded from the window total: a year-to-date charge is not an annual one, and the two are different quantities._

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 9.4x as-of 2026-08-12 — trailing range 10.0–66.9x (median 19.3x) over 6 closes → LOW-CONFIDENCE (6 closes < 8q ≈2y) — floor read unreliable; P/LTM EPS NM (no meaningful trailing P/E at this close) [22]
- **vs peers:** EV/EBITDA 9.4x vs peer median 12.6x (-25%); P/E NM vs peer median 33.85 [23]
- **Multiple basis — read before the level:** rent is 5.4% of EBITDA (FY ending 2025-12-31). Since ASC 842 CIQ's TEV carries the operating leases and before it did not, so CIQ's EV/EBITDA (TEV/LTM) history is not on one basis; its latest close implies a 12.2% EBITDA margin against 11.1% reported. The ex-lease history could not be built (only 6 ex-lease quarter(s) of history (≥8 needed)), so R1 does not price this name on either series. [24]
- **What CIQ's EV/EBITDA divides:** CIQ's 9.4x divides TEV $419M (comps, 2026-08-12) by $45M: reported LTM EBITDA $41M + rent $4M (FY ending 2025-12-31) = $45M (0.4% apart) — TEV WITH the operating leases over EBITDA WITH rent added back, consistent on its own basis. It is NOT a multiple of reported EBITDA ($41M, 8.5% below the denominator).
- **Comparability:** market caps span $32M–$274.1B (8591x); the name is $354M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [25]
- **The street, for contrast (target · ratings):** Target price: mean $5.50, median $5.50, high/low 6.00/5.00, N 2/2; Ratings: Buy 2, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-05-15 · export date unverified] [26]

# Analysis — full dossier

## What broke — and did it fall alone?
- **Read — what broke** · discrete gap-downs: [5]
  - 2026-03-17 **-34.2%** → earnings
  - 2026-05-12 **-30.2%** → earnings
  - 2026-05-18 **-12.0%** → no company filing

_Company-specific or market-wide?_
- **Name 180d return:** -66.7% [6]
- **Market (IWM) 180d return:** 12.6% [7]
- **Relative vs market:** -79.3% [8]
_no supplier/customer cohort mapped for this name — the comparison is vs the market only_
- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**
  - gap-down 2026-03-17 → filed 2026-03-16 [`0001628280-26-018235`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026018235/mvst-20260316.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj EBITDA Q4 2025 -$31.6M (vs $8.6M Q4 2024); adj net income Q4 2025 -$34.5M (vs -$0.6M Q4 2024); adj EPS Q4 2025 -$0.11 (vs -$0.01 Q4 2024); $32.5M inventory impairment charge; 2026 revenue outlook: stated, no number given [27]
  - gap-down 2026-05-12 → filed 2026-05-11 [`0001628280-26-033601`](https://www.sec.gov/Archives/edgar/data/1760689/000162828026033601/mvst-20260511.htm)
    - items: 2.02 Results of Operations and Financial Condition
    - **what the results showed:** adj EBITDA Q1 2026 -$5.5M (vs $28.5M Q1 2025); adj net income Q1 2026 -$14.6M (vs $19.3M Q1 2025); adj EPS Q1 2026 -$0.04; 2026 revenue outlook: stated, no number given [28]

## Business quality
- **Segments (revenue share):** Batteries / Battery Systems — single segment [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — single-segment reporting (Batteries / Battery Systems) — no segment EBITDA to break out; the consolidated EBITDA is the whole business
- **Customers:** 6 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [29]
- **Geographic:** China 33%; Italy 22%; France 18%; Other Europe 10%; U.S. 9%; India 8%; Other Asia & Pacific 1% [2]

## The argument

**Evidence balance:** strongly-bearish — a filed going-concern doubt plus a ~$104M near-term maturity wall against shrinking volume outweighs peer-relative optical cheapness.

### Bull case — the decline is overdone
- The European franchise is inflecting up — European sales rose 35% year-over-year in Q2 2026 and reached 61% of quarterly revenue (from 43%), a mechanism-level offset to the APAC decline, though its continuation line notes year-to-date Europe was still down 3% on prior platform-rollout delays. [11]
- Consensus models a forward recovery — FY26E EBITDA $62.1M rising to FY27E $147.7M and revenue $444.4M to $591.5M — with both covering analysts rating Buy and a $5.50 mean target, well above the $0.59 close. [12]
- The multi-year arc shows a genuine operating turn: absolute EBITDA swung from −$85M (FY23) to +$5M (FY24) to +$74M (FY25), and gross margin climbed from 19% (FY23) to 36% (FY25) — a real structural improvement, not merely a margin-percentage optic. [13]
- On the fundamental deltas, the name's EBITDA margin (11%) actually EXCEEDS the peer median (10%), so the discount to peers is not obviously earned on a margin basis — posing whether the gap is RESIDUAL rather than a value trap; but this must be read against the HETEROGENEOUS peer set (caps span $32M–$274.1B) where no single peer stat is a clean benchmark. [30]
- The trailing EV/EBITDA of 9.4x sits below the peer median of 12.6x (-25%), and its own history places today's multiple at the 0th percentile of a 6-close range floor of 10.0x — a compression versus the name's own recent past. [23]

### Bear case — the decline is real
- The latest 10-Q states SUBSTANTIAL DOUBT (going concern) — a filed disclosure that is the single load-bearing terminal signal and outweighs any peer-relative cheapness. [3]
- A near-term maturity wall of $104.2M is due within twelve months on the filing basis, against $128M cash — the survival crux, and the filing figure DIVERGES from the CIQ panel's same-window $98.5M by more than tolerance, so the exact wall itself is uncertain. [3]
- Comps-basis total-debt/EBITDA is 4.3x versus a peer median of 1.6x, and the name is diluting (+18.8% shares over ~1.7y) with a $25.0M shareholder loan converted to stock in May 2026 — a heavier balance sheet and ongoing equity issuance. [14]
- The recent operating turn is reversing: six-month 2026 revenue fell $60.0M (−28.8%) driven by a 24.3% sales-volume reduction (947.2 MWh to 717.2 MWh), the causal mechanism behind the de-rating — volume, not a one-off. [3]
- Customer concentration spiked sharply — Customer A is 46.0% of revenue (from 18.0% prior) — a single-customer dependence that magnifies the revenue-volume risk. [3]
- The margin optic masks deterioration confirmed by absolute figures: adjusted EBITDA collapsed to $3.6M in Q2 2026 from $25.9M a year earlier, so the falling margin % is here the REAL signal, not a reclassification artefact. [31]
- GAAP net income is dominated by below-the-line items — four trailing quarters carry material non-operating blocks netting −$87M (including a −$122M Q2 2025 swing at 134% of revenue) — so any trailing EPS or P/E spanning them is not an operating anchor and the name shows P/E NM. [32]
- The trailing EV/EBITDA of 9.4x is a trailing-only optic with no forward basis, and its own-history 'floor' read is explicitly LOW-CONFIDENCE (6 closes < 8q); it cannot distinguish a temporarily depressed level from a permanently impaired one — so the apparent cheapness is not a reliable signal. [33]

### Decisive question
**Can Microvast clear the ~$104M twelve-month maturity wall (refinance/repay/convert) and re-accelerate sales volume before the going-concern doubt resolves against it — i.e. is the de-rating a fundable overshoot or a terminal liquidity/demand spiral?**

### …evidence for
- Consensus models EBITDA recovering to FY27E $147.7M from FY26E $62.1M with a Buy rating and $5.50 target, implying analysts expect the ramp and refinancing to hold. [12]
- A precedent for clearing near-term obligations without cash exists: on May 28, 2026 the full $25.0M shareholder loan was converted to common stock rather than repaid — a conversion path off the wall. [34]
- The European franchise is a live growth mechanism — European sales +35% YoY and 61% of Q2 2026 revenue — that could re-accelerate consolidated volume, though the same line flags year-to-date Europe still −3%. [11]

### …evidence against
- The 10-Q itself states SUBSTANTIAL DOUBT about going concern — management's own filed judgment that survival is in question. [3]
- The load-bearing operating driver is deteriorating: six-month revenue fell 28.8% on a 24.3% volume drop (947.2 to 717.2 MWh), so the cash-generating base is shrinking as the wall approaches. [3]
- Conversion off the wall is dilutive to a shareholder base already up 18.8% in ~1.7y, and 46% single-customer concentration makes the volume recovery fragile. [35]

### Key unknowns
- Refinancing/repayment plan for the ~$104M twelve-month maturity wall is not disclosed; the filing ($104.2M) and CIQ panel ($98.5M) figures diverge >5%, so even the size of the wall is unresolved — a bearish opacity gap given the going-concern flag.
- Self-funding is MIXED, not established: latest-quarter OCF is negative (−$1.7M / −$33.3M six-month) while LTM 'Levered Free Cash Flow' is positive $63.4M — the two legs carry opposite signs and the basis decides which; true cash self-sufficiency is unknown.
- No forward/adjusted EV/EBITDA on a consistent basis is available, and the actual-vs-estimate EBITDA rows are NOT the same basis (estimate implies 2.93x the D&A add-back) — trailing 9.4x and forward multiples cannot be cleanly compared.
- The peer set is HETEROGENEOUS (caps $32M–$274.1B, 8591x); whether the discount to the 12.6x median is EARNED or RESIDUAL cannot be read off the peer stat and is left for the human.
- 2026 revenue guidance is QUALITATIVE only (no number stated) and the CIQ level appears to be a stale vendor-echo of prior-year actual — no firm forward revenue anchor from management.
- Durability of the Customer A 46% concentration (from 18%) and whether the APAC decline (−45% YTD) continues are unresolved demand-side questions.
- Covenant-compliance status on the Chinese bank facilities (financial-maintenance covenant referenced) is not disclosed for the current vintage.

### Twin reference cases
- **Forsee Power S.A.** — went terminal
  - distinguished by: In-roster peer battery-systems maker of small scale with negative EBITDA margin and shrinking revenue — the same electromobility demand-and-scale squeeze the name faces.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Leclanché SA** — went terminal
  - distinguished by: In-roster micro-cap energy-storage battery maker running deeply negative EBITDA with net debt on the balance sheet — the analogue for a sub-scale battery franchise unable to self-fund.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Amprius Technologies** — recovered
  - distinguished by: In-roster small-cap lithium-ion maker with fast revenue growth and negative EBITDA that the market has continued to fund — the analogue for a pre-profit battery name whose ramp story was believed.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **A123 Systems** — went terminal (LLM-claimed — verify)
  - distinguished by: US-listed advanced-battery maker with a technology story and customer wins that hit a liquidity/maturity wall before demand scaled — the going-concern-into-default pattern.
  - source: [LLM-suggested, unverified]
- **Enovix** — recovered (LLM-claimed — verify)
  - distinguished by: Advanced-battery developer with a capacity-ramp narrative and dilution that the equity market kept funding through the pre-profit valley — the survive-to-the-ramp pattern.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-11-11 `[cadence-estimate]` — the next reported quarter against the committed trajectory [36]
- **Loan Facilities Agreement With a Group of Lenders Led by a Bank in China $42.9M matures** — ~2026-12-10 `[stated]` — refinance / repay / convert before the wall — the survival read [37]
- **effective January 7, 2026** — ~2027-01 `[stated]` — a management-stated dated operating action — the thesis mechanism on a timetable; the following print reads its result [38]
- **Convertible Bond - CNY $41.7M matures** — ~2027-01-31 `[stated]` — refinance / repay / convert before the wall — the survival read [37]
- **Long-term Loan Agreement With a Chinese Bank $13.9M matures** — ~2027-06-19 `[stated]` — refinance / repay / convert before the wall — the survival read [37]
- **Short-term Loan Agreements and Bank Facilities With Chinese Banks $49.5M matures** — ~2027-06-30 `[stated]` — refinance / repay / convert before the wall — the survival read [37]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 9.4x vs peer median 12.6x (-25%); P/E NM vs peer median 33.85 [23]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-08-12 · multiples as-of 2026-05-15 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [39]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **3.99x** | **$105.0M EBITDA †** |
| peer-median NTM TEV/EBITDA | 11.52x | $36.4M EBITDA |
| peer-median LTM TEV/EBITDA | 12.6x | $33.3M EBITDA |
| **name NTM TEV/Rev** | **0.79x** | **$530.4M Revenue †** |
| peer-median NTM TEV/Rev | 2.34x | $179.1M Revenue |
| peer-median LTM TEV/Rev | 2.9x | $144.5M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $62.1M · FY27E $147.7M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $444.4M · FY27E $591.5M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

### The EV gap — our base case vs the street

_Anchor FY2026 · consensus as-of ≥2026-05-15 (a FLOOR — the export states no as-of, so the true date is on or after this) · TEV as-of 2026-08-12 · form price-implied-only_

- **Total gap:** **2.39x** — our EV against the market's TEV. No consensus enters this figure.

- **Decomposition suppressed:** consensus coverage at this anchor is below the floor, so no consensus-side comparison is struck — the total gap stands on our leg and the market price alone

  - _Our EBITDA margin **14.9%** vs consensus **14.0%** at FY2026 — shown as figures, NOT divided: EBITDA margin, ours converted from the recipe's D&A ratio; consensus = median EBITDA / median revenue at the anchor_

- **Bridge:** our EV $1,003M − net debt $65M = equity $938M ÷ 386.069M sh = **$2.43/sh** — against TEV $419M.

  - _D&A convention: ratio of revenue (R2, terminal) — the two recipes differ and the reconciliation is an open analyst question, so it is stated rather than assumed._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 9.4x as-of 2026-08-12 — trailing range 10.0–66.9x (median 19.3x) over 6 closes → LOW-CONFIDENCE (6 closes < 8q ≈2y) — floor read unreliable; P/LTM EPS NM (no meaningful trailing P/E at this close) [22]

## Peer comps
- **Peer set (roster · caps · business)** — [40]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Amprius Technologies | $1.8B | develops, manufactures, and markets lithium-ion batteries for mobility applications. (United States) |
| Forsee Power S.A. | $32M | designs, manufactures, and sells battery systems for electromobility in France, res of Europe, Asia, the United States, and internationally. (France) |
| Cummins Inc. | $87.8B | offers various power solutions worldwide. (United States) |
| BorgWarner Inc. | $14.0B | provides technology solutions for combustion, hybrid, and electric vehicles worldwide. (United States) |
| Contemporary Amperex Technology Co. | $274.1B | engages in the research, development, production, and sale of electric vehicle and energy storage system batteries in China and internationally. (China) |
| Panasonic Holdings Corporation | $67.1B | develops, manufactures, sells, services, and supplies various electrical and electronic equipment and related products in Japan, the Americas (Japan) |
| Leclanché SA | $166M | designs, develops, and manufactures customized turnkey energy storage solutions for electricity generation and transmission, mass transportation (Switzerland) |
| Samsung SDI Co. | $26.7B | manufactures and sells batteries in South Korea, Europe, China, North America, Southeast Asia, and internationally. (Gyeonggi-do South) |

_the name: $354M_

- **Comparability (confidence gate):** market caps span $32M–$274.1B (8591x); the name is $354M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [25]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [41]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 0.79 | 1.1 | 2.34 | 3.01 | 10.02 |
| NTM TEV/EBITDA | 3.99 | 7.2 | 11.52 | 32.02 | 137.85 |
| NTM P/E | 7.67 | 12.69 | 19.2 | 21.44 | 37.35 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [42]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| Contemporary Amperex Technology Co. | $274.1B | 13.1 | 3.1 | 21.1 | 23% | 39% | 1.2 | 43,182 (net cash) |
| Cummins Inc. | $87.8B | 16.2 | 2.7 | 32.6 | 14% | 3% | 1.6 | 4,362 |
| Panasonic Holdings Corporation | $67.1B | 12.1 | 1.4 | 42.2 | 10% | -1% | 1.7 | 2,742 |
| Samsung SDI Co. | $26.7B | – | 3.4 | NM | – | – | – | 7,485 |
| BorgWarner Inc. | $14.0B | 7.4 | 1.1 | 35.1 | 14% | 2% | 1.9 | 1,617 |
| Amprius Technologies | $1.8B | NM | 15.7 | NM | -13% | 144% | NM | 68 (net cash) |
| **Microvast Holdings · the name** | **$354M** | **9.4** | **1.1** | **NM** | **11%** | **-13%** | **4.3** | **65** |
| Leclanché SA | $166M | NM | 11.2 | NM | -265% | 32% | NM | 99 |
| Forsee Power S.A. | $32M | NM | 0.7 | NM | -10% | -21% | NM | 64 |
| Peer median (peers) | $20.4B | 12.6 | 2.9 | 33.9 | 10% | 3% | 1.6 | 858 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [13]  <!-- ds-table -->

|  | Dec-2018 (R) | Dec-2019 (R) | Dec-2020 (R) | Dec-2021 | Dec-2022 (R) | Dec-2023 (R) | Dec-2024 | Dec-2025 | Jun-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 12% | -0% | 16% | -28% | 4% | 19% | 31% | 36% | 34% |

_Revenue YoY (latest same-quarter): -4.5% (Q2 Jun-30-2026 vs Q2 Jun-30-2025). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** diluting (trailing ~1.7y): 323,815,298 (2024-11-08) → 384,534,486 (2026-08-03), +18.8% [35]
- **Non-operating earnings:** 4 of the trailing four quarters carry a material block from BELOW the operating line — 2024-09-30 +$6M (46% of pre-tax · 6% of revenue) · 2025-03-31 +$43M (69% of pre-tax · 37% of revenue) · 2025-06-30 −$122M (115% of pre-tax · 134% of revenue) · 2025-09-30 −$14M (exceeds pre-tax · 11% of revenue) — netting −$87M across the four. A trailing EPS or P/E spanning them is not an operating anchor, and the LTM figure carries the SUM, not the largest of them. [32]
- **Return ratios — per fiscal period** — [43]  <!-- ds-table -->

|  | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|
| RoE % | — | — | -69.4% | -57.1% | -24.3% | -18.1% | -41.1% | -7.3% | 11.4% |
| RoCE % | — | — | -10.1% | -24.5% | -12.3% | -8.7% | -2.2% | 3.3% | 0.6% |
| RoA % | — | — | -4.9% | -17.9% | -10.1% | -6.5% | -1.6% | 2.6% | 0.5% |
| Total debt/equity | — | 2.51x | 4.07x | 0.21x | 0.29x | 0.36x | 0.85x | 0.94x | 0.36x |
| Current ratio | — | 1.06x | 1.03x | 4.02x | 2.16x | 1.06x | 1.30x | 0.92x | 1.09x |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-05-15)_
- **Horizon read (FQ — next-2Q revision breadth)** — [44]:
  - _no revisions in any window: EPS Normalized FQ3 2026, EPS Normalized FQ4 2026, EPS (GAAP) FQ3 2026, EPS (GAAP) FQ4 2026, Revenue FQ3 2026, Revenue FQ4 2026, EBITDA FQ3 2026, EBITDA FQ4 2026, EBIT FQ3 2026, EBIT FQ4 2026_
  - _+6 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 0.29 (12m) → 0.20 (9m) → 0.20 (6m) → 0.04 (3m) → 0.04 (2m) → 0.04 (1m) → 0.04 (latest); net -86% (12m→latest) | FY 2026 EPS (GAAP): 0.09 (12m) → 0.09 (9m) → 0.09 (6m) → 0.18 (2m) → 0.18 (1m) → 0.18 (latest); net +100% (12m→latest) [3m n/a] | FY 2026 Revenue: 593.9 (12m) → 544.2 (9m) → 544.2 (6m) → 450.0 (3m) → 444.4 (2m) → 444.4 (1m) → 444.4 (latest); net -25% (12m→latest) | FY 2026 EBITDA: 133.3 (12m) → 146.5 (9m) → 146.5 (6m) → 62.1 (2m) → 62.1 (1m) → 62.1 (latest); net -53% (12m→latest) [3m n/a] | FY 2026 EBIT: 46.2 (12m) → 43.4 (9m) → 43.4 (6m) → 18.0 (3m) → 20.0 (2m) → 20.0 (1m) → 20.0 (latest); net -57% (12m→latest) | FY 2026 Interest Expense: -13.7 (12m) → -4.81 (9m) → -4.81 (6m) → -4.91 (3m) → -4.91 (2m) → -4.91 (1m) → -4.91 (latest); improving (magnitude toward zero) (12m→latest) | FY 2026 EBT (GAAP): 37.0 (12m) → 38.8 (9m) → 38.8 (6m) → 70.4 (3m) → 73.1 (2m) → 73.1 (1m) → 73.1 (latest); net +98% (12m→latest) | FY 2026 Net Income (Excl. Excep): 92.6 (12m) — level only | FY 2026 Net Income (GAAP): 33.3 (12m) → 32.9 (9m) → 32.9 (6m) → 70.4 (3m) → 70.1 (2m) → 70.1 (1m) → 70.1 (latest); net +110% (12m→latest)  [data ≥ 2026-05-15 · export date unverified] [45]
- **Cross-name anchor (NTM forward-multiple ladder)** — [46]:
  - NTM: TEV/REV 0.79 · TEV/EBITDA 3.99 · TEV/EBIT 8.90 · Price/Earnings 7.67 · PEG –
  - FY 2026: TEV/REV 0.94 · TEV/EBITDA 6.75 · TEV/EBIT 20.99 · Price/Earnings 23.00 · PEG –
  - FY 2027: TEV/REV 0.71 · TEV/EBITDA 2.84 · TEV/EBIT 6.11 · Price/Earnings 6.13 · PEG –
  - FY 2028: TEV/REV 0.55 · TEV/EBITDA 2.31 · TEV/EBIT 3.56 · Price/Earnings – · PEG –
  - _+5 later fiscal years in JSON_
- **Current guide (latest results filing):** revenue 2026: 2026 Outlook & Forward-Looking Information • While we continue to navigate evolving tariff structures and shif… (full text in the release record) [47]
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [48]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Revenue | 427.5 | FY 2026 | 2026-03-16 | 161d (stale) | actual ≥ floor 10/13 | FY 2025 MISSED |
| Capital Expenditure | none current (last: '(180.00) - (210.00)') | FY 2023 | 2023-11-10 | 1018d (stale) | spend ≤ ceiling 4/4 | FY 2023 MET |
| Gross Margin % | none current (last: '32.00 - 35.00') | FY 2025 | 2025-11-10 | 287d (stale) | actual ≥ floor 4/4 | FY 2024 MET |

_CIQ states every guide as a LEVEL in the metric's own units. Where management guided a RATE, the level is CIQ's arithmetic on its own base, not a figure the company published — check the release before quoting one as guidance._

- **Consensus stats (target + ratings):** Target price: mean $5.50, median $5.50, high/low 6.00/5.00, N 2/2; Ratings: Buy 2, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0  [data ≥ 2026-05-15 · export date unverified] [26]
- **Revision-event log (31 events · 2 broker-days)** — [49]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-05-15 | H.C. Wainwright & Co. | 17 | 3 | 6 | 8 | EBITDA FY 2026 | 146.5 | 62.1 | −84.4 |
| 2026-05-11 | broker undisclosed | 14 | 9 | 5 | — | Revenue FY 2026 | 480.5 | 450.0 | −30.5 |

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2022 +0%, FY2023 +0%, FY2024 +0%, FY2025 +0%; Revenue surprise: FY2021 +3%, FY2022 +2%, FY2023 +3%, FY2024 +6%, FY2025 -8% (GAAP-EPS basis; +beat / −miss) [50]

## Leverage & survival
- **Net debt / EBITDA [NET]:** 1.6x [9]
- **Total debt / EBITDA vs peers:** name 4.3x vs peer median 1.6x (comps TOTAL-debt/EBITDA basis) [14]
- **Net debt / OCF:** _UNKNOWN_ — CIQ OCF $-2M <= 0 — ratio meaningless
- **Interest coverage:** 8.2x [51]
- **Self-funding:** self-funding: MIXED — latest-Q OCF < 0, LTM FCF > 0 (both must be positive to self-fund) [52]
- **Credit health** — [53]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 3 | 2.5 |
| Operational | 4 | 2.5 |
| Solvency | 3 | 2.5 |
| Liquidity | 2 | 3 |

_S&P issuer rating unrated · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [10]
- **Free cash flow ($M):** 63.4 — basis: CIQ 'Levered Free Cash Flow', NOT CFO − capex — and the two carry OPPOSITE SIGNS: on the same sheet and period [LTM 12 months Jun-30-2026], CFO $-1.7M − capex $28.8M = $-30.5M. One says the business generated cash this period and the other says it consumed it; the basis decides which, so name it before quoting either. [54]
- **Debt schedule vintage:** the debt schedule is 161d old (source filed 2026-03-16); no Item 1.02 (termination of a material agreement) has been filed since [55]
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Mar-16-2026** — [56]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Convertible Bond - CNY | Bonds and Notes | $41.7M | 3.000% - 4.000% | NA | 2027-01-31 | Y | Y | CNY |
| Convertible Loan With Shareholder - Delayed Draw Term Loan | Term Loans | $13.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Convertible Loan With Shareholder - Initial Term Loan | Term Loans | $12.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Loan Facilities Agreement With a Group of Lenders Led by a Bank in China | Term Loans | $42.9M | NA | New Benchmark | 2026-12-10 | Y | N | CNY |
| Long-term Loan Agreement With a Chinese Bank | Term Loans | $13.9M | 2.700% | NA | 2027-06-19 | Y | N | CNY |
| Short-term Loan Agreements and Bank Facilities With Chinese Banks | Term Loans | $49.5M | 2.400% - 4.850% | NA | 2027-06-30 | Y | N | USD |

_2 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-08-24 reference:
  - **matured (pre-reference): $25.0M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-05-28 (88d before ref): $13.0M Convertible Loan With Shareholder 
    - 2026-05-28 (88d before ref): $12.0M Convertible Loan With Shareholder 
  - due ≤12m (through 2026): $42.9M — 2026-12-10 $42.9M
  - due 2027: $105.1M
  - undated (floor — no panel maturity): $95.6M — Notes Payable $78.3M, Operating Lease Liabilities $17.3M
  - _reconciliation: itemized $268.6M (panel A 2025 filed Mar-16-2026) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** term loans 118.5 (3 months Q1 Mar-31-2026 215.2 → 3 months Q2 Jun-30-2026 118.5); senior bonds 56.9; leases 17.5; total principal 192.9; total debt 193.0 (3 months Q2 Jun-30-2026) ($M) [57]
- **Maturity resolution (8-K verbatim):** On May 28, 2026, Mr. Wu delivered a Notice of Conversion in respect of the full $25.0 million principal amount outstanding under the Loan Agreement. Such principal amount will be converted into shares of common stock of the Company in accordance with the terms of the Loan Agreement. [34]
- **Covenants — Convertible Bond** (governing values; full verbatim in appendix):
  - **Conversion:** any conversion of the Convertible Loans into Conversion Shares pursuant to Section 3.2(c)(iii) will only occur in conne… — per an 8-K filed 2021-02-05
  - **Interest / coupon:** non-interest bearing term loan facility — per an 8-K filed 2021-02-05
  - **Events of default:** As soon as practicable following the receipt by a CL Investor of the applicable Required Approvals, but in any event wi… — per an 8-K filed 2021-02-05
- **Covenants — Convertible Loan** (governing values; full verbatim in appendix):
  - **Maturity:** November 28, 2025 · clause (a) of the definition of “Maturity Date” changed from “November 28, 2025” to “May 28, 2026” — per an 8-K filed 2025-03-17
  - **Events of default:** references to “Default or Event of Default” as a condition to effectiveness and as a representation; no mandatory prepa… — per an 8-K filed 2025-03-17
- **Covenants — Loan Facilities Agreement** (governing values; full verbatim in appendix):
  - **Interest / coupon:** LPR + 115 bps · Floating rate: one year LPR published by the National Interbank Funding Center plus 115 bps (reset every 12 months) — per an 8-K filed 2022-09-29
  - **Interest / coupon:** Late Default Interest Rate: 150% of applicable Interest Rate; Misappropriation Default Interest Rate: 200% of applicabl… — per an 8-K filed 2022-09-29
  - **Maturity:** December 10, 2026 · December 10, 2026 (5 years in total) — per an 8-K filed 2022-09-29
  - **Financial maintenance:** Article 14.1(9) Financial indicator: 'The Borrower shall meet the following financial indicators: [/]' — the specific i… — per an 8-K filed 2022-09-29
  - **Events of default:** 12 enumerated · Events of Default (Art. 15.1): 1. Misrepresentation; 2. Breach of covenants/obligations; 3. Payment default; 4. Materia… — per an 8-K filed 2022-09-29

### Filing cross-checks — going concern · leverage basis

- **⚠ Going concern — SUBSTANTIAL DOUBT:** These conditions and events raise substantial doubt about the Company's ability to continue as a going concern within one year after the date that these consolidated financial statements are issued. [3]
  - management's plans: — none stated
- **EBITDA-basis triangulation (each leverage basis-labeled):** [58]
  - net debt / EBITDA (CIQ's EBITDA, vendor-normalised): 1.6x
  - total debt / EBITDA (CIQ comps EBITDA, vendor-normalised): 4.3x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage
  - margin: GAAP 28.6% · impairment-excluded 36.2% (CIQ; cross-check 28.6 + 32.5/427.5 = 36.2%)
- **Customer concentration (latest 10-Q):** [3]
  - Customer A: 46.0% (prior 18.0%)
  - Customer B: 11.0%
  - Customer C: 10.0%
  - order terms: purchase orders or framework supply agreements that are subject to adjustment, cancellation, deferral, or suspension by our customers,

## ⚠ Analyst caveats — verify before the verdict

_8 to verify._

- NOT A CURRENT SCREEN CANDIDATE — assembled because the name carries a committed dossier. The cap band decides where the fund HUNTS, not what it may hold or follow, so absence from it is not a rejection — read the verdict, not the absence: last evaluated 2026-08-14-01: FAIL (g1_drawdown FAIL).
- wall coherence: divergence with an instrument maturing within ±7d of the +12m boundary (Short-term Loan Agreements and Bank Facilities With Chinese Banks) — possible window-convention artifact, not a true divergence
- Net debt/EBITDA (1.6x) is on CIQ's EBITDA (vendor-normalised, not the reported GAAP figure), not the covenant basis; management and credit covenants typically define leverage on adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings release/transcript (currently UNAVAILABLE) — do not read 1.6x as the covenant-basis leverage.
- Estimates data up to 101d stale (beyond the 45d tolerance) — freshness UNVERIFIABLE: the CIQ Estimates export has no as-of stamp, and its data is on/after 2026-05-15 (its latest embedded revision event — a worst-case floor on the true export date). Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar).
- Panel-freshness caveat — 1 CIQ valuation panel(s) predate the latest earnings print (2026-08-11, EDGAR 8-K item 2.02), the oldest by 88d: valuation multiples as-of 2026-05-15. The valuation read may rest on a pre-print P&L — re-pull CIQ after the print before relying on it.
- former registrant name: this CIK filed as "Tuscan Holdings Corp." (2018-12-07 → 2021-07-21) — multi-year series on this page may span a different underlying business; verify continuity across the change (SEC submissions formerNames, CIK 0001760689)
- **Unreconciled margin-compression** — The margin optic masks deterioration confirmed by absolute figures: adjusted EBITDA collapsed to $3.6M in Q2 2026 from $25.9M a year earlier, so the falling margin % is here the REAL signal, not a reclassification artefact.
  - _where:_ a bear point
  - _why it matters:_ cites margin compression without the absolute-EBITDA reconciliation (margin % can fall while EBITDA rises)
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
| street revenue, FY2026 | $444.4M [59] |
| street revenue, FY2027 | $591.5M [59] |
| reported revenue, FY2025 | $427.5M [60] |
| latest-quarter revenue decline, year on year | -25.5% [61] |
| street revenue cut over twelve months | -27% [59] |

### Margin · **DRAFT — not ratified by the analyst**

Reported accounting basis throughout, and the depreciation assumption is vendor-sourced because this filer tags none at all in its own machine-readable filings - stated here so the basis is never mistaken for a primary figure. The gross-margin arc is real: minus twenty-eight per cent to plus thirty-one in three years. The operating margin turned positive for the first time in the latest full year and has already rolled over - the most recent quarter's adjusted operating profit is negative against a strongly positive comparison. The central case therefore takes levered auto-supplier economics rather than the street's cut-but-still-hopeful path, and the leverage read that matters is the company-adjusted one, not the headline.

| reference | value |
| --- | ---: |
| gross margin, FY2021 | -28.1% [62] |
| gross margin, FY2024 - the arc's peak | 31.5% [62] |
| gross margin, FY2025 | 28.6% [62] |
| reported operating margin, FY2025 - first positive year | 1.6% [63] |
| street operating margin, FY2026 - stated | 4.5% [64] |
| street operating margin, FY2027 - stated | 11.6% [64] |
| street earnings cut over twelve months | -52% [59] |
| leverage on company-adjusted earnings | 18.7x [65] |
| depreciation and amortisation - vendor basis | $33.228M [66] |

### Multiple · **DRAFT — not ratified by the analyst**

The exit is set at the closest economic analogue - a levered auto-parts maker - rather than at the scale leader, whose multiple belongs to a business with tens of billions of net cash and none of this balance sheet. This company's own trading history is unusable as an exit: six closes over one and a third years, with the current reading below its own trailing low, which the range read itself calls low-confidence. The peer median spans thirty-four million to two hundred and seventy-five billion of market value, so it is a number rather than a comparison.

| reference | value |
| --- | ---: |
| closest economic analogue, enterprise value to EBITDA `base` | 7.9x [67] |
| _scale leader, enterprise value to EBITDA — excluded: the scale leader's multiple belongs to a different business model (see method)_ | _14.5x_ [68] |
| peer median, heterogeneous nine-name set | 14.5x [69] |
| _this company's trailing median — excluded: six closes over 1.3 years — too short a series to stand on_ | _19.3x_ [70] |
| this company's current reading - below its own trailing low | 9x [71] |

### Horizon · **DRAFT — not ratified by the analyst**

Four years, matching the other records on this recipe so the three are comparable. The survival block sets breakeven three years out, so the terminal year sits one year past the point the business is assumed to fund itself.

| reference | value |
| --- | ---: |
| years to the terminal year | 4years [72] |
| waiting charge applied over the horizon | 74.9% [73] |


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-05-15)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [15]  <!-- ds-table -->

|  | FY18 (R) | FY19 (R) | FY20 (R) | FY21 | FY22 (R) | FY23 (R) | FY24 | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 174 | 76 | 108 | 152 | 204 | 307 | 380 | 428 | 368 | 444 | 592 |
| Revenue growth | — | -56% | +41% | — (basis) | — (basis) | +50% | — (basis) | +13% | — (basis) | +4% (vs FY25) | +33% |
| EBITDA ($M) | -45 | -39 | -15 | -180 | -140 | -85 | 5 | 74 | 41 | 62 | 148 |
| EBITDA margin | -26% | -51% | -14% | -118% | -68% | -28% | 1% | 17% | 11% | 14% | 25% |
| EBIT ($M) | -58 | -54 | -32 | -200 | -160 | -108 | -26 | 40 | 8 | 20 | 69 |
| Net income ($M) | -55 | -58 | -34 | -206 | -158 | -106 | -196 | -29 | 51 | 70 | 56 |
| EPS (GAAP, dil.) | -161.90 | -1.17 | -0.82 | -1.26 | -0.52 | -0.34 | -0.61 | -0.09 | -0.02 | 0.18 | 0.17 |
| EPS (Normalized) | -52.68 | -0.36 | -0.23 | -0.68 | -0.33 | -0.21 | -0.22 | 0.00 | 0.14 | 0.04 | 0.15 |
| Restructuring Charges ($M) | -1 | — | — | — | — | — | — | — | — | — | — |
| Gain (Loss) On Sale Of Assets ($M) | -1 | 0 | -0 | 0 | 0 | -2 | -1 | -0 | -0 | — | — |
| Asset Writedown ($M) | — | -3 | — | — | -2 | -0 | -93 | -37 | -35 | — | — |
| Other Unusual Items ($M) | 10 | 3 | 3 | -4 | 2 | 2 | 12 | 4 | 2 | — | — |
| CFO ($M) | -6 | 13 | 16 | -45 | -54 | -75 | 3 | 76 | -2 | — | — |
| Capex ($M) | -30 | -20 | -19 | -88 | -151 | -187 | -28 | -20 | -29 | — | — |
| FCF (levered, CIQ) | — | — | 16 | -175 | -136 | -117 | -65 | 18 | 63 | — | — |
| D&A ($M) | 13 | 15 | 17 | 21 | 20 | 23 | 31 | 33 | 33 | — | — |
| D&A (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | 43 | 56 |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-05-15; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_


> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 61 of D&A against 21 in the actuals (2.93x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.

### Quarterly — every exported quarter
- **Quarterly financials** — [74]  <!-- ds-table -->

|  | Q4-19 (R) | Q1-20 | Q2-20 | Q3-20 | Q4-20 (R) | Q1-21 (R) | Q2-21 | Q3-21 | Q4-21 | Q1-22 | Q2-22 | Q3-22 | Q4-22 | Q1-23 | Q2-23 (R) | Q3-23 (R) | Q4-23 (R) | Q1-24 | Q2-24 | Q3-24 (R) | Q4-24 (R) | Q1-25 (R) | Q2-25 | Q3-25 | Q4-25 | Q1-26 | Q2-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 31 | 7 | 22 | 31 | 48 | 15 | 33 | 37 | 67 | 37 | 64 | 39 | 65 | 47 | 75 | 80 | 105 | 81 | 84 | 101 | 113 | 116 | 91 | 123 | 96 | 61 | 87 |
| Gross margin | -21% | 27% | 16% | 12% | 18% | -8% | -20% | -97% | 2% | 0% | 8% | 5% | 3% | 10% | 15% | 22% | 22% | 21% | 33% | 33% | 37% | 37% | 35% | 38% | 35% | 32% | 30% |
| EBITDA ($M) | -12 | -6 | -4 | -5 | -1 | -8 | -18 | -109 | -45 | -38 | -40 | -33 | -30 | -26 | -22 | -21 | -15 | -16 | -4 | 12 | 12 | 22 | 18 | 23 | 11 | 0 | 6 |
| EBITDA margin | -40% | -88% | -16% | -15% | -2% | -53% | -53% | -295% | -68% | -103% | -63% | -85% | -47% | -56% | -30% | -27% | -15% | -20% | -5% | 12% | 11% | 19% | 19% | 19% | 11% | 0% | 7% |
| Revenue QoQ | — | — (basis) | +212% | +42% | — (basis) | -69% | — (basis) | +11% | +81% | -45% | +76% | -40% | +68% | -28% | — (basis) | +7% | +31% | — (basis) | +3% | — (basis) | +12% | +3% | — (basis) | +35% | -22% | -37% | +44% |
| Revenue YoY | — | — | — | — | +56% | — (basis) | +54% | +20% | — (basis) | — (basis) | +93% | +5% | -3% | +28% | — (basis) | — (basis) | — (basis) | +73% | — (basis) | +27% | +8% | — (basis) | +9% | — (basis) | — (basis) | — (basis) | -4% |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q2-26 ($M): cash & ST inv 128; total debt 193; net debt 65; equity 543; net working capital 31; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [75]
- **Coherence — BS vs implied-valuation bridge:** cash BS $128M / bridge $128M; debt BS $193M / bridge $193M — reconcile with the implied-valuation bridge. [76]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Mar-16-2026** — [56]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| Convertible Bond - CNY | Bonds and Notes | $41.7M | 3.000% - 4.000% | NA | 2027-01-31 | Y | Y | CNY |
| Convertible Loan With Shareholder - Delayed Draw Term Loan | Term Loans | $13.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Convertible Loan With Shareholder - Initial Term Loan | Term Loans | $12.0M | NA | SOFR + 9.750% | 2026-05-28 | Y | Y | USD |
| Loan Facilities Agreement With a Group of Lenders Led by a Bank in China | Term Loans | $42.9M | NA | New Benchmark | 2026-12-10 | Y | N | CNY |
| Long-term Loan Agreement With a Chinese Bank | Term Loans | $13.9M | 2.700% | NA | 2027-06-19 | Y | N | CNY |
| Notes Payable | Bonds and Notes | $78.3M | NA | NA | undated | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $17.3M | 5.000% | NA | undated | Y | N | USD |
| Short-term Loan Agreements and Bank Facilities With Chinese Banks | Term Loans | $49.5M | 2.400% - 4.850% | NA | 2027-06-30 | Y | N | USD |

- **8-Ks at instrument maturities:** 8-K at maturity 2026-05-28: filed 2026-05-28 [0000947871-26-000585] 5.02 Departure/Election of Directors or Certain Officers, 8.01 Other Events, 9.01 Financial Statements and Exhibits — read for resolution [77]
- **Covenant / contract pointers (CIK-verified execution filings)** — [78]  <!-- ds-table -->

|  | Filing | Date | Accession / exhibit (or note) |
|---|---|---|---|
| material contracts (10-K exhibit index) | latest 10-K | 2026-03-16 | 0001628280-26-018264 — mvst20251231-ex1013.htm, mvst20251231-ex1021.htm |
| Convertible Bond | 8-K | 2021-02-05 | 0001213900-21-007125 — ea134382ex10-1_tuscanhold.htm, ea134382ex10-2_tuscanhold.htm, ea134382ex10-3_tuscanhold.htm |
| Convertible Bond | 8-K | 2019-03-07 | 0001213900-19-003702 — f8k030519ex10-1_tuscan.htm, f8k030519ex10-2_tuscan.htm, f8k030519ex10-3_tuscan.htm |
| Convertible Loan | 8-K | 2025-03-17 | 0000947871-25-000313 — ss4588423_ex1001.htm |
| Convertible Loan | 8-K | 2024-06-04 | 0001760689-24-000021 — wu_microvast-guarantyagree.htm, wu_microvast-loanandsecuri.htm, wu_microvast-pledgeagreeme.htm |
| Loan Facilities Agreement | 8-K | 2022-09-29 | 0001760689-22-000094 — exhibit101-syndicatedloana.htm |
| Loan Facilities Agreement | 8-K | 2021-07-28 | 0001213900-21-039093 — ea144448ex10-13_microvast.htm, ea144448ex10-1_microvast.htm, ea144448ex10-2_microvast.htm |
| Notes Payable | — | — | no contract-level filing expected (aggregate line item) |
| Operating Lease Liabilities | — | — | no contract-level filing expected (aggregate line item) |

- **Covenant terms — Convertible Bond (governing agreement)** — [79]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | any conversion of the Convertible Loans into Conversion Shares pursuant to Section 3.2(c)(iii) will only occur in connection with a CL Share Sale; a CL Investor ... may at any time notify MPS of its… — full verbatim in JSON | base (footer) |
| Principal / commitment amount | the total amount of Convertible Loans outstanding under the Convertible Loan Agreement is equal to RMB 204,500,000 (“Convertible Loan Amount”), held respectively by (a) Ningbo CDH 1 in an amount equa… — full verbatim in JSON | base (footer) |
| Interest / coupon rate | non-interest bearing term loan facility | base (footer) |
| Maturity date | UNKNOWN | not stated in 8-K 0001213900-21-007125 · ea134382ex10-1_tuscanhold.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0001213900-21-007125 · ea134382ex10-1_tuscanhold.htm |
| Security / collateral / guarantors | a stock pledge (each, a “CL Stock Pledge”); pledge such CL Shares pursuant to the applicable CL Stock Pledge ... as collateral for the applicable CL Promissory Note; For any liabilities or indemnitie… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | As soon as practicable following the receipt by a CL Investor of the applicable Required Approvals, but in any event within five Business Days ... (A) MPS shall repay in full any remaining portion of… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0001213900-21-007125 · ea134382ex10-1_tuscanhold.htm_

- **Covenant terms — Convertible Loan (governing agreement)** — [79]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Principal / commitment amount | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Interest / coupon rate | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Maturity date | November 28, 2025 · clause (a) of the definition of “Maturity Date” changed from “November 28, 2025” to “May 28, 2026” | base (footer) |
| Financial-maintenance covenants | UNKNOWN | not stated in 8-K 0000947871-25-000313 · ss4588423_ex1001.htm |
| Security / collateral / guarantors | Liens securing the Obligations ratified and confirmed; Guarantors: Microvast Holdings, Inc., Microvast Advanced Materials Inc., Microvast Advanced Membrane Inc., Microvast Energy, Inc., Microvast Pow… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | references to “Default or Event of Default” as a condition to effectiveness and as a representation; no mandatory prepayment terms stated (defined in the Loan Agreement, not this Amendment) | base (footer) |

_Source §: 8-K 0000947871-25-000313 · ss4588423_ex1001.htm_

- **Covenant terms — Loan Facilities Agreement (governing agreement)** — [79]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm |
| Principal / commitment amount | RMB 800,000,000.00 yuan (Eight hundred million). Annex I Initial Commitments: Bank of China, Huzhou Branch RMB 250 million; China Construction Bank, Huzhou Branch RMB 250 million; Bank of Huzhou, Co.… — full verbatim in JSON | base (footer) |
| Interest / coupon rate | LPR + 115 bps · Floating rate: one year LPR published by the National Interbank Funding Center plus 115 bps (reset every 12 months) | base (footer) |
| Default Interest Rate | Late Default Interest Rate: 150% of applicable Interest Rate; Misappropriation Default Interest Rate: 200% of applicable Interest Rate | base (footer) |
| Maturity date | December 10, 2026 · December 10, 2026 (5 years in total) | base (footer) |
| Financial-maintenance covenants | Article 14.1(9) Financial indicator: 'The Borrower shall meet the following financial indicators: [/]' — the specific indicators are left blank ([/]). Article 14: '3) the Borrower shall ensure that t… — full verbatim in JSON | base (footer) |
| Security / collateral / guarantors | Mortgagor = Microvast Power Systems Co., Ltd. under three Mortgage Contracts (# HuKai 2022 C113, C114, C115) dated 1 September 2022; Pledgor = Microvast Power Systems Co., Ltd. (Pledge Contract detai… — full verbatim in JSON | base (footer) |
| Mandatory prepayment / events of default | 12 enumerated · Events of Default (Art. 15.1): 1. Misrepresentation; 2. Breach of covenants/obligations; 3. Payment default; 4. Material payment default (two consecutive/three total times); 5. Misappropriation of lo… — full verbatim in JSON | base (footer) |

_Source §: 8-K 0001760689-22-000094 · exhibit101-syndicatedloana.htm_

- **Covenant terms — material contracts (10-K exhibit index) (governing agreement)** — [79]  <!-- ds-table -->

|  | Governing value (lead · clause ≤200c) | Source § |
|---|---|---|
| Conversion price / mechanics | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Principal / commitment amount | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Interest / coupon rate | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Maturity date | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Financial-maintenance covenants | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Security / collateral / guarantors | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Mandatory prepayment / events of default | UNKNOWN | not stated in latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm |
| Vesting schedule | One-third on each of the first, second and third anniversaries of the Grant Date | base (footer) |
| Settlement | One Share per vested RSU (or cash value equal to Fair Market Value of a Share on the applicable Vesting Date), settled by the Settlement Date (no later than March 15 of the following year) | base (footer) |
| Forfeiture on termination | Unvested RSUs forfeited on any termination; all RSUs (vested-unsettled and unvested) forfeited on termination for Cause | base (footer) |
| Change in Control | Unvested RSUs treated per the Plan; vested unsettled RSUs settled immediately prior to the Change in Control | base (footer) |
| Dividend Equivalents | Dividend Equivalents credited and converted into additional RSUs; vest and settle with the corresponding Award | base (footer) |
| Transfer restrictions | Not assignable/transferable except by will or laws of descent and distribution | base (footer) |
| Clawback | Subject to clawback/recoupment per applicable law or Company policy | base (footer) |
| Governing law | State of Delaware | base (footer) |

_Source §: latest 10-K 0001628280-26-018264 · mvst20251231-ex1013.htm_

- _3 located agreement exhibit(s) not extracted this run (cost bound / fetch fail) — see the pointer table: 0001213900-19-003702, 0001213900-21-039093, 0001760689-24-000021_

### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 353.8 [80]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $127.80M, − total debt $193.00M [81]
- **Implied equity at peer-median ($M, CIQ)** — [82]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 449.3 |
| NTM Revenue (Capital IQ) | 1,173.9 |
| NTM EBITDA (Capital IQ) | 1,143.5 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q2 2026 Earnings Call, Aug 10, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [83]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 0 · sells 4 (3 insiders, $0.13M) — in the last 182 days · no purchase in the 3y scanned · last sale $0.01M, Chief Technology Officer, 2026-06-10 (~2mo ago) · largest sale $1.30M, director, 2023-11-14 (~33mo ago) · grants 52 · last filing 2026-06-12 · other filings 5 [84]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-08-14): 19.6M → 23.3M sh (+18.6%, rising) · 6.1% of shares out (EDGAR XBRL) · DTC 4.5d · recent: 2026-08-14 23.3M · 2026-07-31 19.6M · 2026-07-15 19.9M · 2026-06-30 21.9M [85]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence — filing DIVERGES from panel — verify; neither silently preferred: panel same-window $98.5M (CIQ panel, principal basis) vs filing $104.2M (10-Q, repayment basis) — 5.5% ≥ 5% tol → DIVERGES. Window [balance, +12m) EXCLUSIVE (filing convention). [86]
- **Guide verification — CIQ guide vs release:** revenue: CIQ FY guide 427.516 ≈ prior-FY actual 427.5 (within source-rounding) → VENDOR-ECHO flag (stale carry-forward); release outlook QUALITATIVE-only — render the qualitative growth line [87]

## Record & reproduce
- **Data window:** screened as of 2026-08-24 · assembled 2026-09-17 19:30 UTC
- **Extraction:** 2026-08-16.1 — every Multiples reader selects the latest close BY DATE, never by column position, and refuses on an NM or undated one rather than reaching back a quarter (#459)
- **Refreshed since assembly** (oldest first):
  - 2026-10-07 · forward_consensus, mechanical.catalyst_path — refresh at 2026-08-16.1
  - 2026-10-07 · forward_multiple_history — refresh at 2026-08-16.1
  - 2026-10-08 · forward_consensus, forward_multiple_history, historical_forecast_error — refresh at 2026-10-08.2
  - 2026-10-08 · forward_consensus — refresh at 2026-10-08.3
  - 2026-10-09 · ev_bridge — refresh at 2026-10-08.4
  - 2026-10-10 · anchor, date_semantics, forward_multiple_history, valuation_basis — refresh at 2026-10-09.3
  - 2026-10-20 · mechanical.valuation — refresh at 2026-10-09.3
  - 2026-10-21 · anchor, caveats, mechanical.financial_summary, mechanical.primary_source, mechanical.valuation — refresh at 2026-10-09.3
  - 2026-10-21 · anchor — anchor-backfill at 2026-10-09.3
  - 2026-10-22 · mechanical.primary_source — refresh at 2026-10-09.3
  - 2026-10-23 · mechanical.primary_source, mechanical.valuation — refresh at 2026-10-09.3
  - 2026-10-26 · mechanical.financial_summary — refresh at 2026-10-09.3
  - 2026-10-27 · mechanical.ciq_currency — refresh at 2026-10-09.3
  - 2026-10-27 · mechanical.capital_structure — refresh at 2026-10-09.3
  - 2026-10-27 · anchor — refresh at 2026-10-09.3
  - 2026-10-27 · mechanical.financial_summary, mechanical.valuation — refresh at 2026-10-09.3
- **Price store:** `wt-artifact → mosaic-theory-ta` · reaching 2026-09-16
- **Panel age:** oldest panel 36d old — 2026-08-12 (valuation.implied_expectations.tev_as_of), against a 2026-09-17 build
- **Consensus age:** consensus is 125d old (2026-05-15, valuation.implied_expectations.multiples_as_of) — beyond the 45d ceiling. No analyst has revised this name in that window; a re-export will NOT move it. Treat as a neglect signal, not a stale pull.
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001760689` · Nasdaq : MVST
- **Assembly log:** primary-source: 8-K 0000947871-26-000585 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+0.5s fetch)
- **Re-run:** `python -m vinci dossier --ticker MVST` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `10-Q 0001628280-26-055372`
[4] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[5] `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
[6] `EOD MVST 180d to 2026-08-24`
[7] `EOD IWM 180d to 2026-08-24 (cap-band: $0.4B @ 2026-08-24 → small (<$4B) → IWM)`
[8] `EOD MVST−IWM 180d to 2026-08-24 (assembly, cap-band)`
[9] `CIQ Net Debt $65M [Q2 Jun-30-2026] ÷ CIQ EBITDA $41M [LTM 12 months Jun-30-2026]`
[10] `EDGAR XBRL FCF sign (screen data-record)`
[11] `CIQ transcript: Microvast Holdings, Inc., Q2 2026 Earnings Call, Aug 10, 2026.rtf`
[12] `CIQ Estimates→Trends (FY26E/FY27E consensus EBITDA, latest snapshot)`
[13] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[14] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-08-12`
[15] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[16] `EDGAR companyfacts IntangibleAssetsNetExcludingGoodwill (as at 2026-06-30)`
[17] `EDGAR filing index (S-3/F-3 · 424B · S-1/F-1 · S-4 · S-8), window 2023-08-25→2026-08-24 · latest 0000947871-25-000882`
[18] `EDGAR filing index (SC 13D/G + SCHEDULE 13D/G — both vocabularies), window 2023-08-25→2026-08-24 · latest 0001213900-26-015862`
[19] `EDGAR XBRL ShareBasedCompensation (10-K, 2025-01-01→2025-12-31)`
[20] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[21] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[22] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[23] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[24] `CIQ Financials (Quarterly)→Historical Capitalization 'Total Enterprise Value' less the operating leases inside it (Balance Sheet 'Curr. Port. of Leases' + 'Long-Term Leases' less EDGAR FinanceLeaseLiability), over Income Statement 'EBITDA' summed over four quarters; checked against EDGAR OperatingLeaseLiability. Materiality: CIQ Financials (Annual)→Income Statement 'Net Rental Exp.' / 'EBITDA'`
[25] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[26] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[27] `8-K 0001628280-26-018235 EX-99.1`
[28] `8-K 0001628280-26-033601 EX-99.1`
[29] `CIQ Customers&Suppliers Microvast Holdings Inc NasdaqCM MVST Customers.rtf`
[30] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[31] `8-K 0001628280-26-055471 EX-99.1`
[32] `EDGAR XBRL pre-tax − operating, quarters 2024-09-30..2025-09-30`
[33] `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
[34] `8-K 0000947871-26-000585 (2026-05-28)`
[35] `EDGAR XBRL shares, trailing 2024-11-08..2026-08-03`
[36] `cadence: EDGAR submissions (median 92d gap over 20 results 8-Ks; last print 2026-08-11)`
[37] `CIQ capital-structure panel (maturity_date)`
[38] `CIQ Key Developments: Microvast Holdings Inc NasdaqCM MVST Key Developments.rtf · Jan-09-2026`
[39] `TEV = mcap 353.8 + net debt 65.2 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-08-12, exported 2026-08-13) — simple-TEV basis`
[40] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[41] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[42] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-08-12`
[43] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[44] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[45] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[46] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[47] `8-K 0001628280-26-033601 EX-99.1 (filed 2026-05-11)`
[48] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record) — CIQ states every guide as a LEVEL; where management guided a RATE, the level is CIQ's arithmetic, not the company's published figure`
[49] `CIQ Estimates→Recent Changes (31 broker revision events)  [data ≥ 2026-05-15 · export date unverified]`
[50] `CIQ Estimates→Surprise (annual)`
[51] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Jun-30-2026]`
[52] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[53] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-08-12`
[54] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Jun-30-2026]`
[55] `CIQ Capital Structure Details — A 2025 filed Mar-16-2026`
[56] `CIQ Financials→Capital Structure Details (A 2025 filed Mar-16-2026)`
[57] `CIQ Financials→Capital Structure Summary`
[58] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[59] `CIQ Estimates->Trends`
[60] `EDGAR Revenues`
[61] `CIQ transcript and quarterly income statement`
[62] `EDGAR GrossProfit / Revenues`
[63] `EDGAR OperatingIncomeLoss / Revenues`
[64] `CIQ Estimates->Trends (EBIT row)`
[65] `company-adjusted trailing figure, vs the 3.9x headline optic`
[66] `CIQ Financials->Cash Flow (no EDGAR tag exists)`
[67] `CIQ Comparable Analysis (BorgWarner, 13.9% EBITDA margin, levered)`
[68] `CIQ Comparable Analysis (CATL, 23.8% margin, large net cash)`
[69] `CIQ Comparable Analysis (set spans $34M to $275bn; several members not meaningful)`
[70] `CIQ Financials->Multiples`
[71] `CIQ Financials->Multiples (low-confidence range read)`
[72] `analyst judgement`
[73] `house rate of 15% a year compounded over four years`
[74] `CIQ Financials→Income Statement (quarterly, full exported history)`
[75] `CIQ Financials→Balance Sheet (quarterly, Q2-26)`
[76] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[77] `EDGAR 8-K submissions (±10d of instrument maturities)`
[78] `EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)`
[79] `fenced Tier-2 extraction (verbatim, source-bound)`
[80] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-08-12`
[81] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-08-12`
[82] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-08-12`
[83] `CIQ transcript(s): Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf; Microvast Holdings, Inc., Q2 2026 Earnings Call, Aug 10, 2026.rtf`
[84] `EDGAR Form 4 (latest 0000947871-26-000620; 48 filings in the 1095d scanned; counts over 182d)`
[85] `FINRA consolidated short interest (settle 2026-08-14); DTC = 23,272,872 short ÷ 5,197,773 screen 90d ADV`
[86] `10-Q maturity wall vs CIQ capital panel (same window)`
[87] `CIQ revenue guide vs release actual/outlook`