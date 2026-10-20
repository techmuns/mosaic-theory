# Dossier — Alphabet Inc. (Nasdaq: GOOGL)

_September 28, 2026 · extraction 2026-08-16.1 · layers refreshed to 2026-10-09.3_

# Brief — first cut

## At a glance
**Target (base)** $397.41 (+17.1% vs entry-vintage spot) · **Spot** $339.35 (entry-vintage — frozen at underwrite 2026-09-01) · **Reward** $58.06 · **Risk** $23.90 · **Reward : risk** 2.43 : 1 (bar 2 : 1) · **Base IRR** 17.1% (floor 15%, 1y) · **Gate** PASS (both tests)

**Asymmetry** preferred · **Return** preferred · **Eligibility** ELIGIBLE (≥1.75:1 & ≥12%)
_gate regime 2026-08-21 · IRR price-only — excludes dividends; conservative for dividend payers_

_Spot source: Alphabet Class A / GOOGL / Nasdaq completed regular-session close, 2026-08-31 — Polygon daily aggregates_

**Underwrite disposition:** CONFIRMED (2026-09-01) · entry $345.90 (entry-vintage) — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

### Thesis — our rationale
_Prices quoted below are entry-vintage (2026-08-31); the live close is in Snapshot, above._

The underwrite missed its asymmetry line at the 14 Aug spot of $345.90, where the ratio was 1.69x against 1.75x. It clears at the 31 Aug close of $339.35, where the same legs give 2.43x and a 17.1% base return. The improvement comes from the price falling, not from anything changing in the business, and the ratio is sensitive to that: risk is thin, so it leaves the preferred band above $342.77 and stops being eligible above $345.26. I am confirming the position on that basis, with the entry unchanged at $345.90.

Alphabet Inc. offers various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.
- **Segments:** Google Services 85%; Google Cloud 15%; Other Bets 0%; Unallocated Hedging Gains (Losses) -0% [1]
- **Geography:** United States 48%; Europe, The Middle East, and Africa (EMEA) 29%; Asia-Pacific (APAC) 17%; Other Americas 6%; Unallocated -0% [2]
- **Snapshot:** Nasdaq · CMP $351.16 (2026-09-22) · cap $4318.6B (2026-09-21) · 52-wk $235.84–$408.61 · shares 12.2B · book value/sh $50.90 [3]

**The crux — what decides this, and what would change our mind**
**Will the escalating capex/AI reinvestment (rising cash cost, FCF compression) convert into durable operating-EBITDA growth long enough to beat expectations already priced near a self-history ceiling — or is the quality fully paid for?**
_7 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-10-20 `[cadence-estimate]` — calendar in Analysis

## What happened — and does it change the runway?
- **Shape:** gradual bleed — no discrete gap-down detected [4]
- **Price (180d):** 25.0% [5]
- **Market (SPY) 180d:** 19.9% [6]
- **vs market (180d):** 5.1% [7]
- **Read:** mixed: name 25% vs cohort median 23% (cohort steady) [8]
- **Net debt / EBITDA:** -0.7x [9]
- **Free cash flow:** positive [10]

## Scenario analysis
_R3_forward_pe_

| scenario | EPS | multiple | value / sh | vs entry-vintage spot |
| --- | ---: | ---: | ---: | ---: |
| bear | $15.388 | 20.5x | $315.45 | -7.0% |
| base | $16.221 | 24.5x | $397.41 | +17.1% |
| bull | $16.649 | 26x | $432.87 | +27.6% |

- **bear** — IC memo 2026-08-17 §7A. Normalized EPS $15.388 at 20.5x — the de-rating case: Bear EPS EXCEEDS today's NTM $13.29, so the downside is multiple compression from ~26x, not an earnings fall. A ruling on either remedies docket is its most likely trigger.
- **base** — IC memo 2026-08-17 §7A. Normalized EPS $16.221 at 24.5x — Search and Cloud economics run modestly above consolidated expectations while the capital build proves less damaging than the Q2 reset implies. Both locked variants hold, neither dramatically.
- **bull** — IC memo 2026-08-17 §7A. Normalized EPS $16.649 at 26.0x — today's multiple sustained on demonstrated capital productivity: FY27 EBIT revisions outrunning FY27 capex revisions, which is the memo's single most important live screen.

**Scenario inputs** — this recipe reads no record-level facts; each leg carries its own inputs, and the chain below is how they combine.

_Chain (P/E):_ value/share = EPS × forward P/E multiple

### Screening context — how this name surfaced — _not a verdict_

_A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite._

| input | value | basis |
| --- | ---: | --- |
| Method | R3_forward_pe | R1 screen: applicable |
| Mid-cycle margin | 26.3% | 9y history · firm |
| Median multiple, own history | 17.5x | 38 closes · firm · EV/EBITDA |
| Screen value / share | $212.17 | spot-independent · EV/EBIT 21.3x |
| Overall confidence | firm |  |

**Mid-cycle assumption under strain.** The last twelve months' operating margin of 33.1% (CIQ EBIT) sits 6.8 points ABOVE the 9-year median of 26.3% (EDGAR GAAP operating income) that R1 reverts to. R1 pairs that median with the median multiple from the same history, so an R1 value answers what the business is worth if it is still what it was. If the gap is STRUCTURAL — a changed mix or model — that history understates it; if it is a cyclical PEAK, reverting is right. The two sources agree within 0.0 points on FY2024, so the gap is the business, not the source.

**data_quality: vendor_bridge**
- vendor bridge: d_and_a supplied by the CIQ workbook because EDGAR had no usable tag

_OPERATOR RE-TAG 2026-09-01. The machine proposed R1 (mid-cycle margin x own-history EV/EBITDA); the underwrite of record is a FORWARD P/E on normalized EPS (IC memo 2026-08-17 SS5/SS7A), which is an EQUITY basis and reads no enterprise value at all. That is a judgment about which arithmetic fits this name and the machine cannot derive it: Alphabet's downside is multiple compression on earnings that still GROW (Bear EPS $15.388 exceeds today's NTM $13.28698), so a recipe reaching equity through EV minus net debt would model the wrong thing. The computed values below are the machine's R1 arithmetic and are left untouched - a re-tag is a judgment about the RECIPE, never a freeze on the numbers._

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the runway outlasts the price:_
- Cloud revenue accelerated to 82% year-over-year growth in Q2 2026, up from 63% in Q1, evidencing a reinvestment engine that is speeding up rather than maturing. [11]
- Cloud backlog grew to $514 billion in Q2 2026 (from over $460 billion in Q1), a committed-revenue runway that supports the long-duration expectations embedded in the price. [11]
- Absolute EBITDA has compounded from $35,813M (FY17) to $173,164M (LTM Jun-30-2026) with margin rising to 39%, so scale is deepening returns, not diluting them. [12]
_Bear case — the price already pays for it:_
- Reinvestment intensity is escalating hard: capex rose to $132,402M (LTM) and consensus models FY26 capex near -$201,846M, driving reported FCF down to $22,665M (LTM) from $56,280M (FY23) — the runway is real but its cash cost is rising faster than reported free cash flow. [13]
- Consensus long-term EPS growth of 13% trails the peer median of 21%, a genuine counter to the runway thesis — OUTWEIGHED for now by the near-term acceleration in Cloud (82% Q2 growth) and rising 12-month EBITDA/EBT revisions, but a real drag on the very long-duration expectations the price embeds. [14]
- The 17.8x trailing P/E is the OPTICAL MISREAD, not the real signal: three of the last four quarters carry large below-operating-line gains netting +$151,120M, so the low P/E reflects one-off investment gains inflating net income — the NTM P/E of 26.52x is the operating anchor and sits at a premium to the peer-median NTM P/E of 22.12x. [15]

## Financial snapshot
- **Financial snapshot** — [16]  <!-- ds-table -->

|  | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 282,836 | 307,394 | 350,018 | 402,836 | 445,866 | 498,548 | 613,730 |
| Revenue growth | +10% | — (basis) | +14% | — (basis) | — (basis) | +24% (vs FY25) | +23% |
| EBITDA ($M) | 88,317 | 96,239 | 127,701 | 150,175 | 173,164 | 233,038 | 297,027 |
| EBITDA margin | 31% | 31% | 36% | 37% | 39% | 47% | 48% |
| EBIT ($M) | 74,842 | 84,293 | 112,390 | 129,039 | 147,628 | 171,734 | 216,725 |
| Net income ($M) | 59,972 | 73,795 | 100,118 | 132,170 | 244,205 | 252,155 | 186,577 |
| EPS (GAAP, dil.) | 4.56 | 5.80 | 8.04 | 10.80 | 19.93 | 20.62 | 14.91 |
| FCF ($M) | 49,939 | 56,280 | 53,158 | 38,088 | 22,665 | — | — |

_table shows the last 4 fiscal years · 5 earlier years are in the Appendix_

> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 70,803 of D&A against 12,710 in the actuals (5.57x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.


**Capital allocation — created or destroyed**

- **Impairment headroom — goodwill + intangibles remaining:** $66,933.0M [17]
- **Goodwill:** $57,828.0M [17]
- **Intangibles (net):** $9,105.0M [18]
- **Impairment:** _NONE IN THE CURRENT PERIOD_ — the filer records no impairment under any tag tried
- **Buyback — cash:** $0.0M [19]
- **Buyback — shares repurchased:** _UNKNOWN_ — no annual repurchased-share count under TreasuryStockSharesAcquired — EDGAR XBRL companyfacts
- **Buyback — average cost/share:** _UNKNOWN_ — no TreasuryStockAcquiredAverageCostPerShare, and the share-count leg is absent — refused rather than derived (EDGAR XBRL companyfacts). The repurchase CASH and SHARE COUNT above are each sound on their own basis; it is their QUOTIENT that is not a price
- **Acquisition consideration:** _UNKNOWN_ — no acquisition consideration under any of BusinessCombinationConsiderationTransferred1, BusinessCombinationConsiderationTransferred, PaymentsToAcquireBusinessesNetOfCashAcquired — EDGAR XBRL companyfacts
- **Registered offering pipeline (equity/debt not distinguished):** shelf registrations 2 (S-3ASR, last 2026-06-01); prospectus supplements 28 (424B2/424B5, last 2026-08-07) · employee-plan (S-8) 1 (S-8, last 2026-07-23) — routine — 3y window to 2026-09-22 [20]
- **Schedule 13D/G filing activity:** no 13D on file · Schedule 13G filings 13 (SC 13G/A/SCHEDULE 13G/SCHEDULE 13G/A, last 2026-04-29) — 3y window to 2026-09-22 [21]
- **Stock-based compensation:** stock-based compensation $24,953.0M = 6.2% of revenue ($402,836.0M, FY 2025-01-01→2025-12-31) [22]
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [23]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap | why |
|---|---:|---:|---:|---:|---:|---|
| **GOOGL** | **4,318,622** | **66,933** | **921,983** | **7%** | **2%** | **—** |
| MSFT | 3,724,728 | 120,933 | 758,376 | 16% | 3% | — |
| AMZN | 2,787,723 | 32,701 | 1,095,689 | 3% | 1% | — |
| META | 1,888,326 | 27,098 | 449,956 | 6% | 1% | — |
| NFLX | 305,467 | 33,838 | 58,450 | 58% | 11% | — |
| DASH | 83,986 | 7,500 | 19,561 | 38% | 9% | — |
| RDDT | 30,539 | 53 | 3,637 | 1% | 0% | — |
| PINS | 10,964 | 558 | 4,759 | 12% | 5% | — |
| MTCH | 9,907 | 2,488 | 4,034 | 62% | 25% | — |
| SNAP | 9,640 | 1,874 | 7,470 | 25% | 19% | — |
| TTD | 6,562 | — | 5,764 | — | — | no-tag |

- **Median — all peers (n=9):** 16% of assets · 5% of market cap
- **Median — peers ≥ $1,000M market cap (n=9):** 16% of assets · 5% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [24]  <!-- ds-table -->

|  | state | yrs charged | window $M | % acquired | last charge (any date) | live YTD $M |
|---|---|---|---|---:|---:|---|
| **GOOGL** | **reports nil** | **0 of 5** | **—** | **—** | **never** | **—** |
| MSFT | reports nil | 0 of 1 | — | — | 2012-06-30 ($6,193M) | — |
| AMZN | does not tag | — | — | — | never | — |
| META | no annual obs. | — | — | — | never | — |
| NFLX | does not tag | — | — | — | never | — |
| DASH | reports nil | 0 of 5 | — | — | never | — |
| RDDT | does not tag | — | — | — | never | — |
| PINS | does not tag | — | — | — | never | 9 |
| MTCH | wrote down | 2 of 2 | 31 | 1% | 2025-12-31 ($0M) | 25 |
| SNAP | reports nil | 0 of 5 | — | — | never | — |
| TTD | does not tag | — | — | — | never | — |

- **Base rate — 1 of 4 large peers ASSESSED over the window took a charge**, median 1% of acquired assets among those that did. The denominator counts only peers with an annual observation in the window — a name with none was not measured, and is not a clean year.
- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. `no annual obs.` and `does not tag` are not measurements and must not be read as clean years. The **live YTD** column is excluded from the window total: a year-to-date charge is not an annual one, and the two are different quantities._

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 23.6x as-of 2026-09-21 — trailing range 10.9–25.8x (median 17.5x) over 38 closes → 95%ile → near-ceiling; P/LTM EPS 17.8x [25]
- **vs peers:** EV/EBITDA 23.6x vs peer median 18.3x (+29%); P/E 17.8x vs peer median 27.9x (-36%) [26]
- **Comparability:** market caps span $6.6B–$3724.7B (568x); the name is $4318.6B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [27]
- **The street, for contrast (target · ratings):** Target price: mean $429.46, median $430.00, high/low 515.00/340.00, N 54/54; Ratings: Buy 43, Outperform 13, Hold 5, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 42, Outperform 13, Hold 5, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 1, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0  [data ≥ 2026-09-17 · export date unverified] [28]

# Analysis — full dossier

## What moved the price — and did it move alone?
- **Read — what moved:** gradual bleed — no discrete gap-down detected [4]
- **Gap-down dates:** _UNKNOWN_ — no gap-down events on the data-record

_Company-specific or market-wide?_
- **Name 180d return:** 25.0% [5]
- **Market (SPY) 180d return:** 19.9% [6]
- **Relative vs market:** 5.1% [7]
- **Cohort read:** mixed: name 25% vs cohort median 23% (cohort steady) [8]
- **Graph cohort** (`graph_coverage.json node=US:0001652044; EOD 180d ret`):
  - [1h] EXTR: 43% · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "]
  - [1h] NN: -19% · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"]
  - [2h] T: no bars · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"] · NN —customer→ AT&T Services, Inc. ["Our Pinnacle solution, launched in partnership with AT&T
  - [2h] AMZN: 23% · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Amazon Web Services ["Our cloud networking solution is avai
  - [2h] AAPL: no bars · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"] · NN —supplier→ Apple ["we and our customers must have access to barometric pressure measureme
  - [2h] AVGO: no bars · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Broadcom ["Our product development efforts also depend upon
  - [2h] CHKP: no bars · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Check Point ["EdgeSentry (in partnership with Check Point) 
  - [2h] MSFT: no bars · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Microsoft Azure ["Our cloud networking solution is availabl
  - [2h] PANW: no bars · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Palo Alto Networks ["integration with Secure Web Gateway pa
  - [2h] SNX: no bars · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —distributor→ TD Synnex Corporation ["Extreme maintains distribution a
  - [2h] VZ: no bars · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"] · NN —customer→ Verizon ["we are continuing to grow our E911 service, including with Verizon"]
  - [2h] ZS: no bars · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Zscaler ["integration with Secure Web Gateway partners such

## Business quality
- **Segments (revenue share):** Google Services 85%; Google Cloud 15%; Other Bets 0%; Unallocated Hedging Gains (Losses) -0% [1]
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — reports 4 segments (Google Services; Google Cloud; Other Bets; Unallocated Hedging Gains (Losses)) but discloses no segment EBITDA — revenue is segmented in the filing and EBITDA is not
- **Segments (profit — the filer's own measure, 10-K):** FY2025 segment operating income (10-K XBRL): Google Services $139,404M (40.7% margin) · Google Cloud $13,910M (23.7% margin) · All Other −$7,515M (margin n.m.) — segments sum $145,799M vs consolidated $129,039M (−$16,760M not allocated to segments). [29]
- **Customers:** 31 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [30]
- **Geographic:** United States 48%; Europe, The Middle East, and Africa (EMEA) 29%; Asia-Pacific (APAC) 17%; Other Americas 6%; Unallocated -0% [2]

## The argument

**Evidence balance:** strongly-bullish — accelerating Cloud growth and rising EBITDA/estimates outweigh a rich trailing multiple and compressing FCF.

**Reproducibility: the draws DISAGREED** — 5 of 5 draws gave 3x strongly-bullish, 2x mixed. The read below is the first draw carrying the majority lean, and the machine proposal is withheld. A tally of this build, not a rate.

### Bull case — the runway outlasts the price
- Cloud revenue accelerated to 82% year-over-year growth in Q2 2026, up from 63% in Q1, evidencing a reinvestment engine that is speeding up rather than maturing. [11]
- Cloud backlog grew to $514 billion in Q2 2026 (from over $460 billion in Q1), a committed-revenue runway that supports the long-duration expectations embedded in the price. [11]
- Absolute EBITDA has compounded from $35,813M (FY17) to $173,164M (LTM Jun-30-2026) with margin rising to 39%, so scale is deepening returns, not diluting them. [12]
- The core Search franchise remains a durable compounder: Search & Other grew 17% in Q2 2026 with AI Mode surpassing 1 billion monthly active users since global expansion, so AI is expanding rather than cannibalising the ad engine. [11]
- Consensus EBITDA revisions have moved sharply up over 12 months (FY26 EBITDA +14%, FY26 EBT +104%), a rising-estimate backdrop rather than a fading one. [31]
- On a forward basis the name trades at NTM TEV/EBITDA 16.13x vs a heterogeneous peer median 12.06x while carrying a superior EBITDA margin (39% vs peer-median 26%) and faster revenue growth (20% vs 16%) — posing whether the forward premium is EARNED by fundamentals rather than a residual overshoot; the human judges against the heterogeneous peer set. [14]
- The balance sheet is net cash at -0.7x net-debt/EBITDA with 76.9x interest coverage and an S&P AA+ issuer rating, so the heavy reinvestment is self-funded and carries no survival risk. [9]

### Bear case — the price already pays for it
- Reinvestment intensity is escalating hard: capex rose to $132,402M (LTM) and consensus models FY26 capex near -$201,846M, driving reported FCF down to $22,665M (LTM) from $56,280M (FY23) — the runway is real but its cash cost is rising faster than reported free cash flow. [13]
- Consensus long-term EPS growth of 13% trails the peer median of 21%, a genuine counter to the runway thesis — OUTWEIGHED for now by the near-term acceleration in Cloud (82% Q2 growth) and rising 12-month EBITDA/EBT revisions, but a real drag on the very long-duration expectations the price embeds. [14]
- The 17.8x trailing P/E is the OPTICAL MISREAD, not the real signal: three of the last four quarters carry large below-operating-line gains netting +$151,120M, so the low P/E reflects one-off investment gains inflating net income — the NTM P/E of 26.52x is the operating anchor and sits at a premium to the peer-median NTM P/E of 22.12x. [15]
- The trailing EV/EBITDA of 23.6x sits at the 95th percentile of its own ~9.5-year history (range 10.9–25.8x, median 17.5x) — the reinvestment quality is being paid for near a self-history ceiling, so future returns must be beaten from a rich starting point; note this multiple is trailing-only with no forward basis, so a depressed-vs-terminal read cannot be distinguished here. [32]

### Decisive question
**Will the escalating capex/AI reinvestment (rising cash cost, FCF compression) convert into durable operating-EBITDA growth long enough to beat expectations already priced near a self-history ceiling — or is the quality fully paid for?**

### …evidence for
- Cloud revenue grew 82% in Q2 2026 with backlog at $514 billion, the load-bearing driver that the runway case turns on. [11]
- Operating EBITDA compounded to $173,164M (LTM) at a 39% margin, showing the reinvestment is translating into rising absolute profit, not just revenue. [12]
- 12-month consensus EBITDA and EBT revisions rose (+14% and +104% for FY26), evidence the estimate path is still moving up. [31]

### …evidence against
- Trailing EV/EBITDA of 23.6x sits at the 95th percentile of its own ~9.5-year history — much of the quality is already in the price. [32]
- LTM reported FCF fell to $22,665M as capex climbed to $132,402M, so the reinvestment's cash cost is currently outrunning free-cash generation. [13]
- Consensus long-term EPS growth of 13% lags the peer median of 21%, tempering the durability the priced runway assumes. [14]

### Key unknowns
- Segment EBITDA is not disclosed — revenue is segmented but EBITDA is not, so Cloud's true profitability (and whether the 82% growth carries margin) cannot be verified from the filing (opacity: bearish gap on the load-bearing growth driver).
- Trailing EV/EBITDA is trailing-only with no forward basis in the revised guidance; a depressed-vs-permanently-impaired / overshoot-vs-terminal read is unresolved and belongs to the human, not a directional read.
- 5-year P/E percentile cannot be built because a share-basis change (split) sits inside the window and older EPS is as-filed — the trailing P/E range is not comparable.
- Forward adjusted EBITDA and adjusted EPS are not in the revised guidance, so an adjusted leverage/multiple cross-check is unavailable.
- The estimate-basis EBITDA implies ~5.57x the D&A of the actuals, so trailing-vs-forward EBITDA multiples are on non-identical bases — growth across the boundary is partly definitional.
- Covenant terms are UNKNOWN (no agreement exhibit located) — a gap in the pointer search, not confirmed absence.
- Whether the FY26E FCF (consensus basis) of $7,783M and FY27E -$32,380M reflect a sustained capex peak or a durable cash-flow impairment is unresolved.

### Twin reference cases
- **Microsoft Corporation** — kept compounding
  - distinguished by: Mega-cap platform that funded a step-change in cloud/AI capex out of a net-cash balance sheet while the core franchise kept compounding — the analogue for reinvestment that the market ultimately paid up for.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Amazon.com** — kept compounding
  - distinguished by: Heavy multi-year capex build depressed reported free cash flow while a high-growth cloud segment carried the runway — the analogue for a rising-capex, falling-FCF profile that later re-accelerated.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Meta Platforms** — re-rated to fair value
  - distinguished by: Advertising-led compounder whose AI-capex ramp compressed near-term free cash flow and triggered a valuation swing before the ad engine reasserted — the analogue for capex-anxiety on a dominant ad platform.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Cisco Systems** — re-rated to fair value (LLM-claimed — verify)
  - distinguished by: A dominant franchise that traded at a peak multiple on a durable-growth narrative and then de-rated when growth normalised — the analogue for paying a top-of-history multiple for quality already recognised.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-10-20 `[cadence-estimate]` — the next reported quarter against the committed trajectory [33]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 23.6x vs peer median 18.3x (+29%); P/E 17.8x vs peer median 27.9x (-36%) [26]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-09-21 · multiples as-of 2026-09-17 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [34]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **16.13x** | **$260,194.6M EBITDA †** |
| peer-median NTM TEV/EBITDA | 12.06x | $348,004.9M EBITDA |
| peer-median LTM TEV/EBITDA | 18.3x | $229,341.0M EBITDA |
| **name NTM TEV/Rev** | **7.63x** | **$550,057.6M Revenue †** |
| peer-median NTM TEV/Rev | 3.94x | $1,065,213.0M Revenue |
| peer-median LTM TEV/Rev | 4.5x | $932,653.2M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $233038.5M · FY27E $297027.3M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $498547.7M · FY27E $613730.2M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

### The EV gap — our base case vs the street

_No gap is struck for this name: shares unavailable. The consensus side alone still routes to **three-ratio** at FY2026, so the form is known even though the comparison is not._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 23.6x as-of 2026-09-21 — trailing range 10.9–25.8x (median 17.5x) over 38 closes → 95%ile → near-ceiling; P/LTM EPS 17.8x [25]

## Peer comps
- **Peer set (roster · caps · business)** — [35]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Meta Platforms | $1888.3B | engages in the development of products that enable people to connect and share with friends and family through mobile devices, personal computers (United States) |
| Amazon.com | $2787.7B | engages in the retail sale of consumer products, advertising, and subscriptions service through online and physical stores in North America and internationally. (United States) |
| Microsoft Corporation | $3724.7B | develops and supports a portfolio of technology solutions for individuals and businesses worldwide. (United States) |
| Reddit | $30.5B | operates a digital community in the United States and internationally. (United States) |
| Pinterest | $11.0B | operates as a visual search and discovery platform in the United States, Canada, Europe, and internationally. (United States) |
| Netflix | $305.5B | provides entertainment services worldwide. (United States) |
| Snap Inc. | $9.6B | operates as a technology company in North America, Europe, and internationally. (United States) |
| The Trade Desk | $6.6B | operates as a technology company in the United States and internationally. (United States) |
| DoorDash | $84.0B | operates a commerce platform that connects merchants, consumers, and dashers in the United States and internationally. (United States) |
| Match Group | $9.9B | provides digital technologies in the United States and internationally. (United States) |

_the name: $4318.6B_

- **Comparability (confidence gate):** market caps span $6.6B–$3724.7B (568x); the name is $4318.6B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [27]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [36]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 7.63 | 1.56 | 3.94 | 4.65 | 9.66 |
| NTM TEV/EBITDA | 16.13 | 7.05 | 12.06 | 12.47 | 19.14 |
| NTM P/E | 26.52 | 7.94 | 22.12 | 20.02 | 30.21 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [37]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| **Alphabet Inc. · the name** | **$4,318.6B** | **23.6** | **9.5** | **17.8** | **39%** | **20%** | **0.7** | **121,683 (net cash)** |
| Microsoft Corporation | $3,724.7B | 18.3 | 11.4 | 27.9 | 59% | 18% | 0.6 | 51,970 |
| Amazon.com | $2,787.7B | 15.6 | 3.8 | 20.8 | 22% | 16% | 1.3 | 128,647 |
| Meta Platforms | $1,888.3B | 16.8 | 8.4 | 27.9 | 48% | 28% | 1.0 | 22,058 |
| Netflix | $305.5B | 20.2 | 6.5 | 23.1 | 30% | 16% | 1.1 | 7,527 |
| DoorDash | $84.0B | 52.2 | 5.2 | 101.8 | 9% | 34% | 2.1 | 2,042 (net cash) |
| Reddit | $30.5B | 34.2 | 10.0 | 37.0 | 29% | 67% | 0.0 | 2,766 (net cash) |
| Pinterest | $11.0B | 30.2 | 2.4 | 148.1 | 7% | 17% | 3.3 | 78 (net cash) |
| Match Group | $9.9B | 10.7 | 3.7 | 15.2 | 34% | 2% | 3.0 | 3,084 |
| Snap Inc. | $9.6B | NM | 1.8 | NM | -2% | 13% | NM | 1,566 |
| The Trade Desk | $6.6B | 6.8 | 1.8 | 16.3 | 23% | 12% | 0.5 | 1,051 (net cash) |
| Peer median (peers) | $57.3B | 18.3 | 4.5 | 27.9 | 26% | 16% | 1.1 | 2,325 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [12]  <!-- ds-table -->

|  | Dec-2017 (R) | Dec-2018 (R) | Dec-2019 (R) | Dec-2020 | Dec-2021 | Dec-2022 | Dec-2023 (R) | Dec-2024 (R) | Dec-2025 | Jun-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 59% | 56% | 56% | 54% | 57% | 55% | 57% | 58% | 60% | 61% |

_Revenue YoY (latest same-quarter): +24.2% (Q2 Jun-30-2026 vs Q2 Jun-30-2025). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** flat (trailing ~1.7y): 12,264,000,000 (2024-09-30) → 12,230,000,000 (2026-06-30), -0.3% [38]
- **Non-operating earnings:** 3 of the trailing four quarters carry a material block from BELOW the operating line — 2025-09-30 +$12,759M (29% of pre-tax · 12% of revenue) · 2026-03-31 +$37,716M (49% of pre-tax · 34% of revenue) · 2026-06-30 +$97,983M (71% of pre-tax · 82% of revenue) — netting +$151,120M across the four. A trailing EPS or P/E spanning them is not an operating anchor, and the LTM figure carries the SUM, not the largest of them. [15]
- **Return ratios — per fiscal period** — [39]  <!-- ds-table -->

|  | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | 8.7% | 18.6% | 18.1% | 19.0% | 32.1% | 23.6% | 27.4% | 32.9% | 35.7% | 48.7% |
| RoCE % | 12.1% | 12.1% | 11.3% | 11.0% | 18.5% | 16.5% | 17.6% | 21.0% | 19.3% | 15.8% |
| RoA % | 9.9% | 9.5% | 8.8% | 8.7% | 14.5% | 12.9% | 13.7% | 16.5% | 15.4% | 13.0% |
| Total debt/equity | 0.03x | 0.02x | 0.08x | 0.13x | 0.11x | 0.12x | 0.11x | 0.09x | 0.16x | 0.19x |
| Current ratio | 5.14x | 3.92x | 3.37x | 3.07x | 2.93x | 2.38x | 2.10x | 1.84x | 2.01x | 2.72x |
| Dividend/sh | none | none | none | none | none | none | none | none | 0.38 | 0.05 |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-09-17)_
- **Horizon read (FQ — next-2Q revision breadth)** — [40]:
  - EPS Normalized FQ3 2026: 1m 2↑/0↓, 2m 19↑/15↓, 3m 20↑/11↓
  - EPS Normalized FQ4 2026: 1m 2↑/0↓, 2m 17↑/14↓, 3m 19↑/11↓
  - EPS (GAAP) FQ3 2026: 1m 2↑/1↓, 2m 21↑/17↓, 3m 21↑/14↓
  - EPS (GAAP) FQ4 2026: 1m 2↑/1↓, 2m 19↑/15↓, 3m 21↑/13↓
  - Revenue FQ3 2026: 1m 1↑/0↓, 2m 33↑/1↓, 3m 31↑/1↓
  - Revenue FQ4 2026: 1m 2↑/0↓, 2m 31↑/2↓, 3m 30↑/2↓
  - EBITDA FQ3 2026: 1m 2↑/0↓, 2m 17↑/8↓, 3m 14↑/8↓
  - EBITDA FQ4 2026: 1m 2↑/0↓, 2m 16↑/8↓, 3m 15↑/7↓
  - EBIT FQ3 2026: 1m 2↑/0↓, 2m 17↑/16↓, 3m 18↑/12↓
  - EBIT FQ4 2026: 1m 2↑/0↓, 2m 19↑/12↓, 3m 21↑/9↓
  - _+8 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 10.6 (12m) → 11.2 (9m) → 11.6 (6m) → 14.2 (3m) → 14.3 (2m) → 20.6 (1m) → 20.6 (latest); net +94% (12m→latest) | FY 2026 EPS (GAAP): 10.6 (12m) → 11.2 (9m) → 11.5 (6m) → 14.2 (3m) → 14.3 (2m) → 20.6 (1m) → 20.6 (latest); net +94% (12m→latest) | FY 2026 Revenue: 440,500.3 (12m) → 455,329.2 (9m) → 472,202.6 (6m) → 487,719.9 (3m) → 489,251.2 (2m) → 497,864.3 (1m) → 498,547.7 (latest); net +13% (12m→latest) | FY 2026 EBITDA: 203,980.1 (12m) → 211,230.1 (9m) → 217,975.8 (6m) → 227,055.7 (3m) → 228,088.2 (2m) → 231,852.0 (1m) → 233,038.5 (latest); net +14% (12m→latest) | FY 2026 EBIT: 147,987.5 (12m) → 154,569.9 (9m) → 158,634.4 (6m) → 169,849.3 (3m) → 170,646.9 (2m) → 171,652.0 (1m) → 171,734.2 (latest); net +16% (12m→latest) | FY 2026 Interest Expense: -3,880.0 (12m) → -3,600.0 (9m) → -3,200.0 (6m) → -3,297.5 (3m) → -3,538.0 (2m) → -4,441.3 (1m) → -4,441.3 (latest); worsening (magnitude away from zero) (12m→latest) | FY 2026 EBT (GAAP): 152,783.4 (12m) → 160,911.6 (9m) → 165,698.7 (6m) → 211,448.9 (3m) → 212,440.5 (2m) → 311,704.1 (1m) → 311,740.1 (latest); net +104% (12m→latest) | FY 2026 Net Income (Excl. Excep): 127,333.5 (12m) → 135,242.3 (9m) → 139,376.2 (6m) → 172,920.8 (3m) → 173,686.2 (2m) → 253,683.4 (1m) → 254,017.9 (latest); net +99% (12m→latest) | FY 2026 Net Income (GAAP): 127,162.3 (12m) → 135,167.8 (9m) → 139,676.0 (6m) → 173,596.0 (3m) → 174,447.4 (2m) → 251,976.0 (1m) → 252,154.9 (latest); net +98% (12m→latest)  [data ≥ 2026-09-17 · export date unverified] [31]
- **Cross-name anchor (NTM forward-multiple ladder)** — [41]:
  - NTM: TEV/REV 7.63 · TEV/EBITDA 16.13 · TEV/EBIT 21.90 · Price/Earnings 26.52 · PEG 2.07 · P/BV –
  - FY 2026: TEV/REV 8.45 · TEV/EBITDA 18.09 · TEV/EBIT 24.54 · Price/Earnings 17.21 · PEG 1.35 · P/BV 5.98
  - FY 2027: TEV/REV 6.87 · TEV/EBITDA 14.19 · TEV/EBIT 19.45 · Price/Earnings 23.85 · PEG 1.87 · P/BV 4.71
  - FY 2028: TEV/REV 5.73 · TEV/EBITDA 11.03 · TEV/EBIT 16.05 · Price/Earnings 20.16 · PEG 1.58 · P/BV 3.81
  - _+4 later fiscal years in JSON_
- **Current guide (latest results filing):** _UNKNOWN_ — no guide in any of the 3 parsed release(s)
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [42]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Capital Expenditure | '(195,000.00) - (205,000.00)' | FY 2026 | 2026-07-22 | 62d (stale) | spend ≤ ceiling 1/1 | FY 2025 MET |
| DPS | 0.22 | FQ3 2026 | 2026-07-22 | 62d (stale) | actual ≥ floor 1/1 · 8 at-guide (±0.5% of a point, not adjudicated) | FQ2 2026 AT GUIDE (±0.5% of a point) |
| Revenue | none current (last: 11,800.0) | FY 2007 | 2006-03-20 | 7491d (stale) | actual ≥ floor 3/3 | FY 2007 MET |
| EPS Normalized | none current (last: 0.18) | FY 2006 | 2005-10-20 | 7642d (stale) | actual ≥ floor 1/1 | FY 2006 MET |
| EPS (GAAP) | none current (last: 0.18) | FY 2006 | 2005-10-20 | 7642d (stale) | actual ≥ floor 1/1 | FY 2006 MET |

_CIQ states every guide as a LEVEL in the metric's own units. Where management guided a RATE, the level is CIQ's arithmetic on its own base, not a figure the company published — check the release before quoting one as guidance._

- **Consensus stats (target + ratings):** Target price: mean $429.46, median $430.00, high/low 515.00/340.00, N 54/54; Ratings: Buy 43, Outperform 13, Hold 5, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 42, Outperform 13, Hold 5, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 1, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0  [data ≥ 2026-09-17 · export date unverified] [28]
- **Revision-event log (250 events · 23 broker-days)** — [43]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-09-17 | Tigress Financial Partners LLC | 31 | 22 | 9 | — | EBITDA FQ3 2026 | 55286.2 | 59132.4 | +3846.2 |
| 2026-09-16 | broker undisclosed | 10 | 10 | — | — | EBITDA FY 2026 | 230000.0 | 235000.0 | +5000.0 |
| 2026-09-10 | Oppenheimer & Co. Inc. | 23 | 16 | 2 | 5 | EBITDA FQ3 2026 | 60271.0 | 62861.0 | +2590.0 |
| 2026-09-08 | broker undisclosed | 12 | 3 | 9 | — | EBITDA FY 2026 | 211777.8 | 211706.4 | −71.4 |
| 2026-09-03 | Arete Research Services LLP | 2 | 2 | — | — | Revenue FY 2026 | 506000.0 | 509000.0 | +3000.0 |
| 2026-09-03 | China International Capital Corporation Limited | 9 | 3 | 6 | — | EBITDA FY 2026 | 198836.0 | 198841.0 | +5.0 |

_+17 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2004 +33%, FY2005 +0%, FY2006 +9%, FY2007 -3%, FY2008 -20%, FY2009 +2%, FY2010 +3%, FY2011 -5%, FY2012 -1%, FY2013 -2%, FY2014 +6%, FY2015 -1%, FY2016 -1%, FY2017 -44%, FY2018 +5%, FY2019 +6%, FY2020 +13%, FY2021 +4%, FY2022 -4%, FY2023 +1%, FY2024 +0%, FY2025 +2%; Revenue surprise: FY2004 +2%, FY2005 +0%, FY2006 +1%, FY2007 +1%, FY2008 +0%, FY2009 +0%, FY2010 +1%, FY2011 -1%, FY2012 -4%, FY2013 +1%, FY2014 -1%, FY2015 +1%, FY2016 +2%, FY2017 +1%, FY2018 +0%, FY2019 -1%, FY2020 +2%, FY2021 +1%, FY2022 -0%, FY2023 +1%, FY2024 -0%, FY2025 +1% (GAAP-EPS basis; +beat / −miss) [44]

## Leverage & survival
- **Net debt / EBITDA [NET]:** -0.7x [9]
- **Total debt / EBITDA vs peers:** name 0.7x vs peer median 1.1x (comps TOTAL-debt/EBITDA basis) [45]
- **Net debt / OCF:** -0.7x [46]
- **Interest coverage:** 76.9x [47]
- **Self-funding:** self-funding: YES — latest-Q OCF > 0 AND LTM FCF > 0 [48]
- **Credit health** — [49]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 1 | 3 |
| Operational | 2 | 3 |
| Solvency | 1 | 3 |
| Liquidity | 1 | 3 |

_S&P issuer rating AA+ · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [10]
- **Free cash flow ($M):** 22665.0 — basis: CIQ 'Levered Free Cash Flow', NOT CFO − capex: on the same sheet and period [LTM 12 months Jun-30-2026], CFO $185,675.0M − capex $132,402.0M = $53,273.0M — 0.43x apart. Company-defined FCF is usually the second; a per-share or self-funding read should say which it used. [13]
- **Debt schedule vintage:** the debt schedule is 229d old (source filed 2026-02-05); no Item 1.02 (termination of a material agreement) has been filed since [50]
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Feb-05-2026** — [51]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 16 US Dollar Notes | Bonds and Notes | $2,000.0M | 2.000% | NA | 2026-08-15 | N | N | USD |
| Revolving Credit Facilities | Revolving Credit | – | NA | NA | 2026-04-01 | N | N | USD |

_17 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-09-22 reference:
  - **matured (pre-reference): $2,000.0M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-04-01 (174d before ref): – Revolving Credit Facilities
    - 2026-08-15 (38d before ref): $2,000.0M 16 US Dollar Notes
  - due 2028: $500.0M
  - due 2029: $1,759.9M
  - due 2030: $750.0M
  - due 2033: $1,759.9M
  - due 2035: $1,250.0M
  - due 2037: $1,466.6M
  - due 2045: $1,466.6M
  - due 2054: $1,466.6M
  - due 2055: $1,500.0M
  - due 2065: $1,500.0M
  - undated (floor — no panel maturity): $52,084.8M — 20 US Dollar Notes $9,000.0M, Commercial Paper Program –, Euro Denominated Fixed Rate… $7,631.8M, Finance Lease Liabilities $2,500.0M, Operating Lease Liabilities $15,953.0M, US Dollar Denominated Fixed Rate… $17,000.0M
  - _reconciliation: itemized $67,504.4M (panel A 2025 filed Feb-05-2026) vs the aggregates below — the gap is unitemized / newer term loans; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** senior bonds 99,876.5; leases 20,627.0; total principal 122,189.5; total debt 120,791.0 (3 months Q2 Jun-30-2026) ($M) [52]
- **Maturity resolution (8-K verbatim):** _UNKNOWN_ — (P3) 8-K body at 8-K 0001652044-26-000031 (2026-04-02) states no maturity-resolution event

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [53]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [54]
  - net debt / EBITDA (CIQ, GAAP basis): -0.7x
  - total debt / EBITDA (CIQ comps, GAAP basis): 0.7x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage

## ⚠ Analyst caveats — verify before the verdict

_4 to verify._

- NOT A CURRENT SCREEN CANDIDATE — assembled because the name carries an operator follow decision — Alphabet Class A, HELD — a $50,000 / 5.0% NAV starter entered 2026-08-14 at ~$345 under an external IC memo, recorded here so the machinery can see a live position it was previously blind to. Followed under the QUALITY book: the binding question is duration — whether Search and Cloud economics outlast what a ~26x normalized NTM multiple already pays for — not whether a de-rating is overdone, which is the overshoot twin's question and the wrong one here. The $300M-$10B band answers where the fund HUNTS, not what it may hold or follow, and this name is covered deliberately from outside it. Class A specifically: the memo, the $345.90 verified close and the frozen legs are all Class A, and GOOG (Class C) is a distinct security. The cap band decides where the fund HUNTS, not what it may hold or follow, so absence from it is not a rejection — read the verdict, not the absence: no screen run on file has evaluated it.
- **Bare peer-comparison** — The 17.8x trailing P/E is the OPTICAL MISREAD, not the real signal: three of the last four quarters carry large below-operating-line gains netting +$151,120M, so the low P/E reflects one-off investment gains inflating net income — the NTM P/E of 26.52x is the operating anchor and sits at a premium to the peer-median NTM P/E of 22.12x.
  - _where:_ a bear point
  - _why it matters:_ presents cheap/rich vs peers as a verdict without the earned-vs-residual decomposition or the peer-set composition
  - _how to verify:_ POSE justified-vs-residual, never the bare gap
- **Heterogeneous-peer benchmark** — The 17.8x trailing P/E is the OPTICAL MISREAD, not the real signal: three of the last four quarters carry large below-operating-line gains netting +$151,120M, so the low P/E reflects one-off investment gains inflating net income — the NTM P/E of 26.52x is the operating anchor and sits at a premium to the peer-median NTM P/E of 22.12x.
  - _where:_ a bear point
  - _why it matters:_ leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS
  - _how to verify:_ confidence-gate every peer stat
- synthesis draws DISAGREED — 5 draw(s) of 5 gave {'mixed': 2, 'strongly-bullish': 3}; the machine proposal is withheld and the kept read is the first draw carrying the modal label (a tally of this build, never a rate)

# Appendix — data & audit

## How to read this dossier
- The machine assembles and cites; **the analyst decides**. Nothing here is a recommendation — the verdict of record is the human's, logged to an append-only ledger with a frozen entry price.
- The machine's proposed verdict is derived deterministically from its written assessment and stays **sealed until the analyst's verdict is recorded**, so it cannot anchor the decision. A two-sided assessment proposes nothing.
- Citations [n] resolve in the Sources list at the document end. **Cited is not verified** — the reference locates the claim so you can check it.
- Reference values (peer-implied equity, price-implied levels) are shown **beside** the figures they contextualize, never differenced into an upside — the reader judges the gap.
- A value shown as UNKNOWN is honestly absent at the source — nothing is imputed.

## How these numbers were set

_Per-axis methodology from the underwrite record — the reference frame each leg was chosen against, not a re-derivation._

### Earnings · ratified 2026-09-10

FUNDAMENTAL HORIZON (~Aug-2027) ONLY, on the Street TARGET-PERIOD construction: the target-period Street controls give EPS Normalized $16.02-16.07 and this record's point lock is $16.0445, and the three legs are struck around that on the SAME Street-like diluted-share basis, so they differ by economics and not by share count. Speculative bear ATM dilution and bull buyback shrinkage are deliberately not embedded. The memo's Method A / Method B pair is NOT this axis: those are the March-2027 TRADE-horizon denominator constructions (annual day-weight 306/366 versus annual-constrained FY27-seasonality), the memo rules neither uniquely correct to point precision, and this record carries no trade-horizon leg, so neither is used or adopted here. bear: $15.388, ~4% below the target-period Street range. base: $16.221, modestly above that range. bull: $16.649, above it. IC memo 2026-08-17 section 4.

_No reference points recorded — stated as judgment._

### Multiple · ratified 2026-09-10

FUNDAMENTAL HORIZON (~Aug-2027) ONLY. Every leg is a DISPLACEMENT FROM THE VERIFIED CURRENT normalized P/NTM of ~26.03x, never a draw from a distribution. bear: 20.5x, a substantial de-rating; it sets the risk denominator, and it is consistent with the memo's mechanism that the downside is DURATION/MULTIPLE risk rather than earnings collapse, since bear EPS $15.388 EXCEEDS today's NTM $13.28698 and the entire bear outcome is therefore a de-rating. base: 24.5x, one notch of compression on duration. bull: 26.0x, holding the current multiple, conditional on demonstrated capital productivity - FY27 EBIT revisions outrunning FY27 capex revisions. CORROBORATION ONLY, NONE LOAD-BEARING: the company's own P/NTM quartiles (p25 21.46x, median 24.24x, p75 26.75x, n=38 settled quarter-ends) are labelled `P/NTM EPS` and are NOT proven to share this normalized denominator - the memo records that basis match as LIMITED and states three times that the quartiles cannot support these turns; EV/NTM direct-EBIT (~21.5x current against a ~18.85x median) is a cross-check, not a target-generator; peer context likewise. The proximity of base 24.5x to the 24.24x median is COINCIDENTAL CORROBORATION, NOT DERIVATION - bull is the test, and it sits 0.03 from current against 0.75 from p75, where a distribution-derived bull would sit. DISPLACEMENT MAGNITUDE IS ANALYST JUDGMENT. RECORDED GAP, NOT PAPERED: the memo documents NO reason for this 20.5x fundamental bear against the 22.0x trade bear - base and bull are IDENTICAL across the two horizons and only the bear differs. The reason is missing and is left missing; authoring one would manufacture support for the leg that sets the risk denominator on a record at gate PASS. The memo's phrase 'single binding valuation assumption' belongs to the TRADE bear's ~26x to 22x compression, NOT to 20.5x; an earlier draft of this sentence and STATE row 20 both mislocated it. IC memo 2026-08-17 sections 5 and 7A.

_No reference points recorded — stated as judgment._


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-09-17)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [16]  <!-- ds-table -->

|  | FY17 (R) | FY18 (R) | FY19 (R) | FY20 | FY21 | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 110,855 | 136,819 | 161,857 | 182,527 | 257,637 | 282,836 | 307,394 | 350,018 | 402,836 | 445,866 | 498,548 | 613,730 |
| Revenue growth | — | +23% | +18% | — (basis) | +41% | +10% | — (basis) | +14% | — (basis) | — (basis) | +24% (vs FY25) | +23% |
| EBITDA ($M) | 35,813 | 41,624 | 47,579 | 54,903 | 88,987 | 88,317 | 96,239 | 127,701 | 150,175 | 173,164 | 233,038 | 297,027 |
| EBITDA margin | 32% | 30% | 29% | 30% | 35% | 31% | 31% | 36% | 37% | 39% | 47% | 48% |
| EBIT ($M) | 28,914 | 32,595 | 35,928 | 41,224 | 78,714 | 74,842 | 84,293 | 112,390 | 129,039 | 147,628 | 171,734 | 216,725 |
| Net income ($M) | 12,662 | 30,736 | 34,343 | 40,269 | 76,033 | 59,972 | 73,795 | 100,118 | 132,170 | 244,205 | 252,155 | 186,577 |
| EPS (GAAP, dil.) | 0.90 | 2.19 | 2.46 | 2.93 | 5.61 | 4.56 | 5.80 | 8.04 | 10.80 | 19.93 | 20.62 | 14.91 |
| EPS (Normalized) | 1.34 | 1.49 | 1.71 | 1.90 | 3.62 | 3.65 | 4.25 | 5.88 | 6.86 | 7.67 | 20.62 | 14.88 |
| Gain (Loss) On Sale Of Invest. ($M) | -193 | 6,530 | 3,188 | 6,317 | 12,270 | -5,519 | -823 | 2,671 | 24,620 | 149,012 | — | — |
| Legal Settlements ($M) | -2,736 | -5,071 | -1,697 | — | — | — | — | — | — | — | — | — |
| CFO ($M) | 37,091 | 47,971 | 54,520 | 65,124 | 91,652 | 91,495 | 101,746 | 125,299 | 164,713 | 185,675 | 215,570 | 268,208 |
| Capex ($M) | -13,184 | -25,139 | -23,548 | -22,281 | -24,640 | -31,485 | -32,251 | -52,535 | -91,447 | -132,402 | -201,846 | -298,205 |
| FCF (levered, CIQ) | 23,683 | 20,529 | 25,116 | 35,504 | 47,009 | 49,939 | 56,280 | 53,158 | 38,088 | 22,665 | — | — |
| D&A ($M) | 6,899 | 9,029 | 11,651 | 13,679 | 10,273 | 13,475 | 11,946 | 15,311 | 21,136 | 25,536 | — | — |
| FCF (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | 7,783 | -32,380 |
| D&A (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | 32,382 | 50,391 |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-09-17; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_


> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 70,803 of D&A against 12,710 in the actuals (5.57x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.

### Quarterly — every exported quarter
- **Quarterly financials** — [55]  <!-- ds-table -->

|  | Q1-17 | Q2-17 | Q3-17 | Q4-17 | Q1-18 (R) | Q2-18 (R) | Q3-18 (R) | Q4-18 (R) | Q1-19 | Q2-19 | Q3-19 | Q4-19 | Q1-20 | Q2-20 | Q3-20 | Q4-20 | Q1-21 | Q2-21 | Q3-21 | Q4-21 | Q1-22 | Q2-22 | Q3-22 | Q4-22 | Q1-23 (R) | Q2-23 (R) | Q3-23 (R) | Q4-23 (R) | Q1-24 (R) | Q2-24 | Q3-24 | Q4-24 (R) | Q1-25 | Q2-25 | Q3-25 | Q4-25 | Q1-26 | Q2-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 24,750 | 26,010 | 27,772 | 32,323 | 31,146 | 32,657 | 33,740 | 39,276 | 36,339 | 38,944 | 40,499 | 46,075 | 41,159 | 38,297 | 46,173 | 56,898 | 55,314 | 61,880 | 65,118 | 75,325 | 68,011 | 69,685 | 69,092 | 76,048 | 69,787 | 74,604 | 76,693 | 86,310 | 80,539 | 84,742 | 88,268 | 96,469 | 90,234 | 96,428 | 102,346 | 113,829 | 109,896 | 119,796 |
| Gross margin | 60% | 60% | 60% | 56% | 57% | 57% | 58% | 54% | 56% | 56% | 57% | 54% | 54% | 52% | 54% | 54% | 56% | 58% | 58% | 56% | 56% | 57% | 55% | 54% | 56% | 57% | 57% | 56% | 58% | 58% | 59% | 58% | 60% | 60% | 60% | 60% | 62% | 62% |
| EBITDA ($M) | 8,061 | 8,492 | 9,537 | 9,691 | 9,619 | 10,228 | 10,981 | 10,796 | 10,918 | 12,015 | 12,651 | 12,549 | 11,080 | 9,755 | 14,691 | 19,377 | 19,179 | 22,306 | 24,335 | 25,324 | 23,876 | 23,352 | 21,181 | 19,908 | 20,050 | 24,662 | 24,514 | 27,013 | 28,885 | 31,133 | 32,506 | 35,177 | 35,215 | 36,393 | 36,839 | 41,974 | 46,356 | 48,241 |
| EBITDA margin | 33% | 33% | 34% | 30% | 31% | 31% | 33% | 27% | 30% | 31% | 31% | 27% | 27% | 25% | 32% | 34% | 35% | 36% | 37% | 34% | 35% | 34% | 31% | 26% | 29% | 33% | 32% | 31% | 36% | 37% | 37% | 36% | 39% | 38% | 36% | 37% | 42% | 40% |
| Revenue QoQ | — | +5% | +7% | +16% | — (basis) | +5% | +3% | +16% | — (basis) | +7% | +4% | +14% | -11% | -7% | +21% | +23% | -3% | +12% | +5% | +16% | -10% | +2% | -1% | +10% | — (basis) | +7% | +3% | +13% | -7% | — (basis) | +4% | — (basis) | — (basis) | +7% | +6% | +11% | -3% | +9% |
| Revenue YoY | — | — | — | — | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | +13% | -2% | +14% | +23% | +34% | +62% | +41% | +32% | +23% | +13% | +6% | +1% | — (basis) | — (basis) | — (basis) | — (basis) | +15% | — (basis) | — (basis) | +12% | — (basis) | +14% | +16% | — (basis) | +22% | +24% |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q2-26 ($M): cash & ST inv 242,474; total debt 120,791; net debt -121,683; equity 622,457; net working capital 217,413; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [56]
- **Coherence — BS vs implied-valuation bridge:** cash BS $242,474M / bridge $242,474M; debt BS $120,791M / bridge $120,791M — reconcile with the implied-valuation bridge. [57]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Feb-05-2026** — [51]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 1.25 Billion of 4.50% Notes Due 2035 * | Bonds and Notes | $1,250.0M | 4.500% | NA | 2035-05-15 | N | N | USD |
| 1.25billion of 3.38% Notes Due 2037 - Euro * | Bonds and Notes | $1,466.6M | 3.375% | NA | 2037-05-06 | N | N | EUR |
| 1.25billion of 3.88% Notes Due 2045- Euro * | Bonds and Notes | $1,466.6M | 3.875% | NA | 2045-05-06 | N | N | EUR |
| 1.25billion of 4.00% Notes Due 2054- Euro * | Bonds and Notes | $1,466.6M | 4.000% | NA | 2054-05-06 | N | N | EUR |
| 1.5 Billion of 5.25% Notes Due 2055 * | Bonds and Notes | $1,500.0M | 5.250% | NA | 2055-05-15 | N | N | USD |
| 1.5billion of 2.50% Notes Due 2029 - Euro * | Bonds and Notes | $1,759.9M | 2.500% | NA | 2029-05-06 | N | N | EUR |
| 1.5billion of 3.00% Notes Due 2033 - Euro * | Bonds and Notes | $1,759.9M | 3.000% | NA | 2033-05-06 | N | N | EUR |
| 1.5billion of 5.30% Notes Due 2065 * | Bonds and Notes | $1,500.0M | 5.300% | NA | 2065-05-15 | N | N | USD |
| 16 US Dollar Notes | Bonds and Notes | $2,000.0M | 2.000% | NA | 2026-08-15 | N | N | USD |
| 20 US Dollar Notes | Bonds and Notes | $9,000.0M | 0.800% - 2.250% | NA | undated | N | N | USD |
| 750 Million of 4.00% Notes Due 2030 * | Bonds and Notes | $750.0M | 4.000% | NA | 2030-05-15 | N | N | USD |
| Commercial Paper Program | Commercial Paper | – | 4.400% | NA | undated | N | N | USD |
| Euro Denominated Fixed Rate Senior Unsecured Notes | Bonds and Notes | $7,631.8M | 3.440% | NA | undated | N | N | EUR |
| Finance Lease Liabilities | Capital Lease | $2,500.0M | 3.300% | NA | undated | Y | N | USD |
| Floating-rate Notes Due in 2028 | Bonds and Notes | $500.0M | NA | SOFR + 0.520% | 2028-11-15 | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $15,953.0M | 3.800% | NA | undated | Y | N | USD |
| Revolving Credit Facilities | Revolving Credit | – | NA | NA | 2030-04-01 | N | N | USD |
| Revolving Credit Facilities | Revolving Credit | – | NA | NA | 2026-04-01 | N | N | USD |
| US Dollar Denominated Fixed Rate Senior Unsecured Notes | Bonds and Notes | $17,000.0M | 4.920% | NA | undated | N | N | USD |

- **8-Ks at instrument maturities:** 8-K at maturity 2026-04-01: filed 2026-04-02 [0001652044-26-000031] 5.02 Departure/Election of Directors or Certain Officers — read for resolution; 8-K at maturity 2026-04-01: filed 2026-04-10 [0001652044-26-000034] 5.02 Departure/Election of Directors or Certain Officers — read for resolution; 8-K at maturity 2026-08-15: filed 2026-08-10 [0001193125-26-342390] 8.01 Other Events, 9.01 Financial Statements and Exhibits — read for resolution [58]
- **Covenant exhibit pointers:** _UNKNOWN_ — no CIK-scoped agreement exhibit located across the filing history
- **Covenant terms (from the filed agreement):** COVENANT DIGEST — extraction failed: no agreement exhibit was located to extract from — the gap is in the pointer search, not in extraction (terms UNKNOWN, not pending). [59]

### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 4318622.4 [60]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $242,474.00M, − total debt $120,791.00M [61]
- **Implied equity at peer-median ($M, CIQ)** — [62]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 3,279,485.0 |
| NTM Revenue (Capital IQ) | 2,276,310.9 |
| NTM EBITDA (Capital IQ) | 3,255,295.8 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Alphabet Inc., Q1 2026 Earnings Call, Apr 29, 2026.rtf; Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [63]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 0 · sells 72 (6 insiders, $22.58M) — in the last 182 days · last purchase $4.95M, 10% owner, 2025-08-01 (~14mo ago) · last sale $0.03M, director, 2026-08-28 (~1mo ago) · largest sale $33.36M, 10% owner, 2026-01-30 (~8mo ago) · grants 464 · last filing 2026-09-16 · other filings 783 [64]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-09-15): 77.7M → 87.4M sh (+12.5%, rising) · 0.7% of shares out (EDGAR XBRL) · DTC 3.0d · recent: 2026-09-15 87.4M · 2026-08-31 77.7M · 2026-08-14 72.7M · 2026-07-31 70.5M [65]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [66]
- **Guide verification — CIQ guide vs release:** revenue: CIQ 11800.0 vs release NO NUMERIC OUTLOOK → not cross-checked [67]

## Record & reproduce
- **Data window:** screened as of 2026-09-22 · assembled 2026-09-28 15:29 UTC
- **Extraction:** 2026-08-16.1 — every Multiples reader selects the latest close BY DATE, never by column position, and refuses on an NM or undated one rather than reaching back a quarter (#459)
- **Refreshed since assembly** (oldest first):
  - 2026-10-07 · forward_consensus, mechanical.catalyst_path — refresh at 2026-08-16.1
  - 2026-10-07 · forward_multiple_history — refresh at 2026-08-16.1
  - 2026-10-08 · forward_consensus, forward_multiple_history, historical_forecast_error — refresh at 2026-10-08.2
  - 2026-10-08 · anchor — anchor-backfill at 2026-10-08.2
  - 2026-10-08 · forward_consensus — refresh at 2026-10-08.3
  - 2026-10-09 · ev_bridge — refresh at 2026-10-08.4
  - 2026-10-10 · anchor, date_semantics, forward_multiple_history, valuation_basis — refresh at 2026-10-09.3
  - 2026-10-18 · mechanical.idiosyncratic_vs_shared, mechanical.stock_performance — refresh at 2026-10-09.3
  - 2026-10-20 · mechanical.valuation — refresh at 2026-10-09.3
- **Price store:** `wt-fl2 → mosaic-theory-ta` · reaching 2026-09-22
- **Panel age:** oldest panel 7d old — 2026-09-21 (valuation.implied_expectations.tev_as_of), against a 2026-09-28 build
- **Consensus age:** consensus 11d old (2026-09-17, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001652044` · Nasdaq : GOOGL
- **Assembly log:** primary-source: 8-K 0001193125-26-342390 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 8-K 0001193125-26-234488 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 8-K 0001193125-26-216986 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 3 EX-99.1 release(s) + 1 10-Q parsed (+3.8s fetch)
- **Re-run:** `python -m vinci dossier --ticker GOOGL` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EOD gap-down detector (screen events): none`
[5] `EOD GOOGL 180d to 2026-09-22`
[6] `EOD SPY 180d to 2026-09-22 (cap-band: $4318.6B @ 2026-09-22 → large (>$25B) → SPY)`
[7] `EOD GOOGL−SPY 180d to 2026-09-22 (assembly, cap-band)`
[8] `derived from 3 cohort names; face-validity`
[9] `CIQ Net Debt $-121,683M [Q2 Jun-30-2026] ÷ CIQ EBITDA $173,164M [LTM 12 months Jun-30-2026]`
[10] `EDGAR XBRL FCF sign (screen data-record)`
[11] `CIQ transcript: Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf`
[12] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[13] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Jun-30-2026]`
[14] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[15] `EDGAR XBRL pre-tax − operating, quarters 2025-06-30..2026-06-30`
[16] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[17] `EDGAR companyfacts Goodwill (as at 2026-06-30)`
[18] `EDGAR companyfacts IntangibleAssetsNetExcludingGoodwill (as at 2026-06-30)`
[19] `EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2026-01-01→2026-06-30, 180d)`
[20] `EDGAR filing index (S-3/F-3 · 424B · S-1/F-1 · S-4 · S-8), window 2023-09-23→2026-09-22 · latest 0001193125-26-340264`
[21] `EDGAR filing index (SC 13D/G + SCHEDULE 13D/G — both vocabularies), window 2023-09-23→2026-09-22 · latest 0002100119-26-000161`
[22] `EDGAR XBRL ShareBasedCompensation (10-K, 2025-01-01→2025-12-31)`
[23] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[24] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[25] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[26] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[27] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[28] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[29] `EDGAR 10-K 0001652044-26-000018 XBRL instance goog-20251231_htm.xml — us-gaap:OperatingIncomeLoss on the segment contexts, fiscal year ending 2025-12-31`
[30] `CIQ Customers&Suppliers Alphabet Inc NasdaqGS GOOGL Customers.rtf`
[31] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[32] `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 38 quarters spanning 2017-03-31..2026-06-30 (9.2y) (partial last column excluded from the distribution)`
[33] `cadence: EDGAR submissions (median 90d gap over 13 results 8-Ks; last print 2026-07-22)`
[34] `TEV = mcap 4318622.4 + net debt -121683.0 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-09-21, exported 2026-09-22) — simple-TEV basis`
[35] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[36] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[37] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-09-21`
[38] `EDGAR XBRL shares, trailing 2024-09-30..2026-06-30`
[39] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[40] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[41] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[42] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record) — CIQ states every guide as a LEVEL; where management guided a RATE, the level is CIQ's arithmetic, not the company's published figure`
[43] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-09-17 · export date unverified]`
[44] `CIQ Estimates→Surprise (annual)`
[45] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-09-21`
[46] `CIQ Net Debt $-121,683M [Q2 Jun-30-2026] ÷ CIQ OCF $185,675M [LTM 12 months Jun-30-2026]`
[47] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Jun-30-2026]`
[48] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[49] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-09-21`
[50] `CIQ Capital Structure Details — A 2025 filed Feb-05-2026`
[51] `CIQ Financials→Capital Structure Details (A 2025 filed Feb-05-2026)`
[52] `CIQ Financials→Capital Structure Summary`
[53] `10-Q 0001652044-26-000071`
[54] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[55] `CIQ Financials→Income Statement (quarterly, full exported history)`
[56] `CIQ Financials→Balance Sheet (quarterly, Q2-26)`
[57] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[58] `EDGAR 8-K submissions (±10d of instrument maturities)`
[59] `fenced Tier-2 digest (P1)`
[60] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-09-21`
[61] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-09-21`
[62] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-09-21`
[63] `CIQ transcript(s): Alphabet Inc., Q1 2026 Earnings Call, Apr 29, 2026.rtf; Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf`
[64] `EDGAR Form 4 (latest 0001193125-26-393517; 513 filings in the 1095d scanned; counts over 182d)`
[65] `FINRA consolidated short interest (settle 2026-09-15); DTC = 87,393,404 short ÷ 29,306,528 screen 90d ADV`
[66] `10-Q maturity wall vs CIQ capital panel (same window)`
[67] `CIQ revenue guide vs release actual/outlook`