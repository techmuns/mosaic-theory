# Dossier — Alphabet Inc. (Nasdaq: GOOGL)

_August 28, 2026 · extraction 2026-08-16.1_

# Brief — first cut

## At a glance
**Target (base)** $397.41 (+17.1% vs entry-vintage spot) · **Spot** $339.35 (entry-vintage — frozen at underwrite 2026-09-01) · **Reward** $58.06 · **Risk** $23.90 · **Reward : risk** 2.43 : 1 (bar 2 : 1) · **Base IRR** 17.1% (floor 15%, 1y) · **Gate** PASS (both tests)

**Asymmetry** preferred · **Return** preferred · **Eligibility** ELIGIBLE (≥1.75:1 & ≥12%)
_gate regime 2026-08-21 · IRR price-only — excludes dividends; conservative for dividend payers_

_Spot source: Alphabet Class A / GOOGL / Nasdaq completed regular-session close, 2026-08-31 — Polygon daily aggregates_

**Underwrite disposition:** CONFIRMED (2026-09-01) · entry $345.90 (entry-vintage) — _the BUY/AVOID verdict of record is the ledger's_

> **Not shown here:** any prior position, close or realized return for this name. This surface reads the underwrite record only — the ledger is the record of positions. **See the Decision log.**

### Thesis — our rationale
_Prices quoted below are entry-vintage (2026-09-01); the live close is in Snapshot, above._

The underwrite missed its asymmetry line at the 14 Aug spot of $345.90, where the ratio was 1.69x against 1.75x. It clears at the 31 Aug close of $339.35, where the same legs give 2.43x and a 17.1% base return. The improvement comes from the price falling, not from anything changing in the business, and the ratio is sensitive to that: risk is thin, so it leaves the preferred band above $342.77 and stops being eligible above $345.26. I am confirming the position on that basis, with the entry unchanged at $345.90.

Alphabet Inc. offers various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.
- **Segments:** Google Services 85%; Google Cloud 15%; Other Bets 0%; Unallocated Hedging Gains (Losses) -0% [1]
- **Geography:** United States 48%; Europe, The Middle East, and Africa (EMEA) 29%; Asia-Pacific (APAC) 17%; Other Americas 6%; Unallocated -0% [2]
- **Snapshot:** Nasdaq · CMP $342.00 (2026-08-26) · cap $4195.0B (2026-08-12) · 52-wk $205.28–$408.61 · shares 12.2B · book value/sh $50.90 [3]

**The crux — what decides this, and what would change our mind**
**Will the escalating AI/cloud capex earn a return that sustains compounding, or is the runway already fully paid for at a record-high trailing multiple while ROIC compresses?**
_7 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Next results print ~2026-10-20 `[cadence-estimate]` — calendar in Analysis

## What happened — and does it change the runway?
- **Shape:** gradual bleed — no discrete gap-down detected [4]
- **Price (180d):** 11.2% [5]
- **Market (SPY) 180d:** 11.5% [6]
- **vs market (180d):** -0.2% [7]
- **Read:** moved ALONE (idiosyncratic): name 11% vs cohort median 46% [8]
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
| Method | R3_forward_pe | applicable |
| Mid-cycle margin | 26.3% | 9y history · firm |
| Median multiple, own history | 17.4x | 37 closes · firm · EV/EBITDA |
| Screen value / share | $196.01 | spot-independent · EV/EBIT 21.2x |
| Overall confidence | firm |  |

**data_quality: vendor_bridge**
- vendor bridge: d_and_a supplied by the CIQ workbook because EDGAR had no usable tag

_OPERATOR RE-TAG 2026-09-01. The machine proposed R1 (mid-cycle margin x own-history EV/EBITDA); the underwrite of record is a FORWARD P/E on normalized EPS (IC memo 2026-08-17 SS5/SS7A), which is an EQUITY basis and reads no enterprise value at all. That is a judgment about which arithmetic fits this name and the machine cannot derive it: Alphabet's downside is multiple compression on earnings that still GROW (Bear EPS $15.388 exceeds today's NTM $13.28698), so a recipe reaching equity through EV minus net debt would model the wrong thing. The computed values below are the machine's R1 arithmetic and are left untouched - a re-tag is a judgment about the RECIPE, never a freeze on the numbers._

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the runway outlasts the price:_
- Revenue growth is accelerating, not decaying: Q2 2026 Alphabet revenue grew 24% year-over-year — the fastest same-quarter rate in the multi-year trajectory. [11]
- Cloud is the runway engine: Q2 2026 Cloud revenue grew 82% with backlog reaching $514 billion, up from over $460 billion the prior quarter, evidencing multi-year demand already contracted. [11]
- The core ad engine is intact and AI-monetizing: Q2 2026 Search & Other grew 17% and YouTube ads grew 13%, with management stating AI Mode surpassed 1 billion MAU and drives incremental query growth. [11]
_Bear case — the price already pays for it:_
- The reinvestment bill is escalating: capex rose from -$52,535M (FY24) to -$132,402M (LTM) and consensus FY26E capex is roughly -$201,617M, driving LTM levered FCF down to $22,665M — a genuine counter-point, though OCF minus capex on the same sheet is +$53,273M and the business remains self-funding. [12]
- The stock already prices durable compounding: EV/EBITDA (TEV/LTM) at 25.8x sits at the 100th percentile of its own 9-year history (range 10.9–24.8x, median 17.4x), the richest trailing level on record — the trailing-vs-forward tension is unresolved because there is no adjusted forward basis in the guidance. [13]
- The trailing 17.2x P/E is not an operating anchor: 3 of the trailing four quarters carry a large below-the-operating-line block (+$97,983M in Q2 2026 alone, 82% of revenue; +$151,120M netted across four), so the low headline P/E is a consensus MISREAD inflated by non-operating gains, not a clean earnings signal. [14]

## Financial snapshot
- **Financial snapshot** — [15]  <!-- ds-table -->

|  | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 282,836 | 307,394 | 350,018 | 402,836 | 445,866 | 497,688 | 606,647 |
| Revenue growth | +10% | — (basis) | +14% | — (basis) | — (basis) | +24% (vs FY25) | +22% |
| EBITDA ($M) | 88,317 | 96,239 | 127,701 | 150,175 | 173,164 | 231,455 | 294,833 |
| EBITDA margin | 31% | 31% | 36% | 37% | 39% | 47% | 49% |
| EBIT ($M) | 74,842 | 84,293 | 112,390 | 129,039 | 147,628 | 171,315 | 214,120 |
| Net income ($M) | 59,972 | 73,795 | 100,118 | 132,170 | 244,205 | 251,783 | 184,633 |
| EPS (GAAP, dil.) | 4.56 | 5.80 | 8.04 | 10.80 | 19.93 | 20.59 | 14.77 |
| FCF ($M) | 49,939 | 56,280 | 53,158 | 38,088 | 22,665 | — | — |

_table shows the last 4 fiscal years · 1 earlier year is in the Appendix_

> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 70,426 of D&A against 14,393 in the actuals (4.89x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.


**Capital allocation — created or destroyed**

- **Impairment headroom — goodwill + intangibles remaining:** $66,933.0M [16]
- **Goodwill:** $57,828.0M [16]
- **Intangibles (net):** $9,105.0M [17]
- **Impairment:** _NONE IN THE CURRENT PERIOD_ — the filer records no impairment under any tag tried
- **Buyback — cash:** $0.0M [18]
- **Buyback — shares repurchased:** _UNKNOWN_ — no annual repurchased-share count under TreasuryStockSharesAcquired — EDGAR XBRL companyfacts
- **Buyback — average cost/share:** _UNKNOWN_ — no TreasuryStockAcquiredAverageCostPerShare, and the share-count leg is absent — refused rather than derived (EDGAR XBRL companyfacts). The repurchase CASH and SHARE COUNT above are each sound on their own basis; it is their QUOTIENT that is not a price
- **Acquisition consideration:** _UNKNOWN_ — no acquisition consideration under any of BusinessCombinationConsiderationTransferred1, BusinessCombinationConsiderationTransferred, PaymentsToAcquireBusinessesNetOfCashAcquired — EDGAR XBRL companyfacts
- **Registered offering pipeline (equity/debt not distinguished):** shelf registrations 2 (S-3ASR, last 2026-06-01); prospectus supplements 28 (424B2/424B5, last 2026-08-07) · employee-plan (S-8) 1 (S-8, last 2026-07-23) — routine — 3y window to 2026-08-24 [19]
- **Schedule 13D/G filing activity:** no 13D on file · Schedule 13G filings 13 (SC 13G/A/SCHEDULE 13G/SCHEDULE 13G/A, last 2026-04-29) — 3y window to 2026-08-24 [20]
- **Stock-based compensation:** stock-based compensation $24,953.0M = 6.2% of revenue ($402,836.0M, FY 2025-01-01→2025-12-31) [21]
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [22]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap | why |
|---|---:|---:|---:|---:|---:|---|
| **GOOGL** | **4,195,028** | **66,933** | **921,983** | **7%** | **2%** | **—** |
| MSFT | 3,656,561 | 120,933 | 758,376 | 16% | 3% | — |
| AMZN | 2,882,966 | 32,701 | 1,095,689 | 3% | 1% | — |
| META | 1,474,624 | 27,098 | 449,956 | 6% | 2% | — |
| NFLX | 309,006 | 33,838 | 58,450 | 58% | 11% | — |
| DASH | 92,072 | 7,500 | 19,561 | 38% | 8% | — |
| RDDT | 29,523 | 53 | 3,637 | 1% | 0% | — |
| PINS | 12,969 | 558 | 4,759 | 12% | 4% | — |
| SNAP | 8,794 | 1,874 | 7,470 | 25% | 21% | — |
| MTCH | 8,397 | 2,488 | 4,034 | 62% | 30% | — |
| TTD | 6,339 | — | 5,764 | — | — | no-tag |

- **Median — all peers (n=9):** 16% of assets · 4% of market cap
- **Median — peers ≥ $1,000M market cap (n=9):** 16% of assets · 4% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [23]  <!-- ds-table -->

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
| SNAP | reports nil | 0 of 5 | — | — | never | — |
| MTCH | wrote down | 2 of 2 | 31 | 1% | 2025-12-31 ($0M) | 25 |
| TTD | does not tag | — | — | — | never | — |

- **Base rate — 1 of 4 large peers ASSESSED over the window took a charge**, median 1% of acquired assets among those that did. The denominator counts only peers with an annual observation in the window — a name with none was not measured, and is not a clean year.
- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. `no annual obs.` and `does not tag` are not measurements and must not be read as clean years. The **live YTD** column is excluded from the window total: a year-to-date charge is not an annual one, and the two are different quantities._

## Valuation — first cut
- **vs own trading history:** EV/EBITDA (TEV/LTM) 25.8x as-of 2026-06-30 — trailing range 10.9–24.8x (median 17.4x) over 37 closes → 100%ile → near-ceiling; P/LTM EPS 27.3x [24]
- **vs peers:** EV/EBITDA 22.9x vs peer median 18.0x (+27%); P/E 17.2x vs peer median 23.4x (-26%) [25]
- **Comparability:** market caps span $6.3B–$3656.6B (577x); the name is $4195.0B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [26]
- **The street, for contrast (target · ratings):** Target price: mean $428.04, median $428.00, high/low 515.00/340.00, N 55/56; Ratings: Buy 45, Outperform 13, Hold 6, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 44, Outperform 13, Hold 6, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 1, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0  [data ≥ 2026-08-10 · export date unverified] [27]

# Analysis — full dossier

## What moved the price — and did it move alone?
- **Read — what moved:** gradual bleed — no discrete gap-down detected [4]
- **Gap-down dates:** _UNKNOWN_ — no gap-down events on the data-record

_Company-specific or market-wide?_
- **Name 180d return:** 11.2% [5]
- **Market (SPY) 180d return:** 11.5% [6]
- **Relative vs market:** -0.2% [7]
- **Cohort read:** moved ALONE (idiosyncratic): name 11% vs cohort median 46% [8]
- **Graph cohort** (`graph_coverage.json node=US:0001652044; EOD 180d ret`):
  - [1h] EXTR: 74% · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "]
  - [1h] NN: 18% · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"]
  - [2h] T: no bars · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"] · NN —customer→ AT&T Services, Inc. ["Our Pinnacle solution, launched in partnership with AT&T
  - [2h] AMZN: no bars · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Amazon Web Services ["Our cloud networking solution is avai
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
- **Customers:** 31 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [28]
- **Geographic:** United States 48%; Europe, The Middle East, and Africa (EMEA) 29%; Asia-Pacific (APAC) 17%; Other Americas 6%; Unallocated -0% [2]

## The argument

**Evidence balance:** mixed — accelerating revenue and cloud backlog run into a record-high trailing multiple, falling ROIC and rising capex whose payback is unresolved.

### Bull case — the runway outlasts the price
- Revenue growth is accelerating, not decaying: Q2 2026 Alphabet revenue grew 24% year-over-year — the fastest same-quarter rate in the multi-year trajectory. [11]
- Cloud is the runway engine: Q2 2026 Cloud revenue grew 82% with backlog reaching $514 billion, up from over $460 billion the prior quarter, evidencing multi-year demand already contracted. [11]
- The core ad engine is intact and AI-monetizing: Q2 2026 Search & Other grew 17% and YouTube ads grew 13%, with management stating AI Mode surpassed 1 billion MAU and drives incremental query growth. [11]
- Absolute EBITDA has compounded from $88,987M (FY21) to $173,164M (LTM Jun-30-2026) alongside EBITDA margin rising to 39% — scale and profitability improving together, not a mix that is optically flattering. [29]
- On a P/E basis Alphabet screens at 17.2x versus the peer median 23.4x — a discount to a peer set on the earnings line; whether it is EARNED or RESIDUAL turns on the fundamental deltas, since Alphabet posts a higher EBITDA margin (39% vs 26%) and faster revenue growth (20% vs 16%) but LOWER long-term EPS growth (14% vs 20%). [30]
- The balance sheet funds the reinvestment internally: net-debt/EBITDA is -0.7x (net cash), interest coverage 76.9x, and an AA+ S&P issuer rating versus a peer-median credit profile several notches weaker. [31]
- Consensus revisions are strongly one-sided upward: FY2026 EPS breadth is 47 up / 0 down last month and 55/56 targets carry a mean $428.04 with a Buy (1.00) rating. [32]

### Bear case — the price already pays for it
- The reinvestment bill is escalating: capex rose from -$52,535M (FY24) to -$132,402M (LTM) and consensus FY26E capex is roughly -$201,617M, driving LTM levered FCF down to $22,665M — a genuine counter-point, though OCF minus capex on the same sheet is +$53,273M and the business remains self-funding. [12]
- The stock already prices durable compounding: EV/EBITDA (TEV/LTM) at 25.8x sits at the 100th percentile of its own 9-year history (range 10.9–24.8x, median 17.4x), the richest trailing level on record — the trailing-vs-forward tension is unresolved because there is no adjusted forward basis in the guidance. [13]
- The trailing 17.2x P/E is not an operating anchor: 3 of the trailing four quarters carry a large below-the-operating-line block (+$97,983M in Q2 2026 alone, 82% of revenue; +$151,120M netted across four), so the low headline P/E is a consensus MISREAD inflated by non-operating gains, not a clean earnings signal. [14]
- On EV/EBITDA Alphabet trades at a PREMIUM to peers (22.9x vs median 18.0x, +27%) and on TEV/Rev (9.2x vs 4.8x) — so the 'cheap on P/E' read reverses on enterprise-value bases, a divergence the human must reconcile against the heterogeneous peer set. [25]
- Returns on capital are compressing even as the multiple peaks: ROIC fell from 21.0% (FY24) to 15.8% (LTM Jun-30-2026), the lowest in the six-period window, as the capital base expands faster than operating profit. [33]

### Decisive question
**Will the escalating AI/cloud capex earn a return that sustains compounding, or is the runway already fully paid for at a record-high trailing multiple while ROIC compresses?**

### …evidence for
- Cloud grew 82% in Q2 2026 with backlog of $514 billion, and customers are exceeding their commitments by more than 50% — a signed, accelerating demand base that the capex is being built to serve. [11]
- Management reports declining unit economics on the core AI product — the cost of AI Mode responses fell to its lowest level since launch — suggesting the infrastructure spend is lowering marginal cost as volume scales. [11]
- Absolute EBITDA rose to $173,164M (LTM) with EBITDA margin at 39%, so the reinvestment has so far coincided with rising, not falling, absolute profitability. [29]

### …evidence against
- ROIC has fallen to 15.8% (LTM) from 21.0% (FY24) — the capital base is growing faster than operating profit, the first hard sign the incremental spend is not yet earning the prior franchise return. [33]
- LTM levered FCF has dropped to $22,665M as capex reached -$132,402M and consensus FY26E capex is about -$201,617M, so the cash cost of the runway is rising sharply and ahead of the payback. [12]
- EV/EBITDA at 25.8x is at the 100th percentile of its own 9-year range, so the market is already paying a record trailing multiple for the outcome to go right. [13]

### Key unknowns
- No adjusted or forward EV/EBITDA is in the revised guidance, so the record 100th-percentile TRAILING 25.8x cannot be distinguished from a normal forward level — the overshoot-vs-terminal question is unresolved and sits in neither the bull nor bear column.
- The trailing P/E percentile cannot be built: a ~20x split falls inside the window and comparatives are on mismatched bases, so the 17.2x P/E has no own-history context.
- No segment EBITDA is disclosed — revenue is segmented (Google Services 85% / Cloud 15%) but the profitability of the fast-growing Cloud runway is opaque, an expected disclosure that is missing and bears on whether Cloud's 82% growth is margin-accretive.
- The trailing/forward EBITDA basis diverges (estimate columns imply 4.89x more D&A than actuals), so growth across the actual→estimate boundary is part-definitional and any multiple comparison across it is unsafe.
- Debt covenant terms are UNKNOWN — no agreement exhibit located; immaterial at net-cash today but a disclosed gap.
- The consensus FY26 FCF picture is contested: several brokers revised FY26 FCF sharply negative (e.g. -$107,315M, -$65,500M) versus a consensus near +$8,719M — the payback on capex is not agreed even among analysts.
- The peer set is HETEROGENEOUS (market caps span $6.3B–$3,656.6B, 577x); every peer multiple is a confidence-gated input, not a clean benchmark, so neither the P/E discount nor the EV/EBITDA premium can be read cleanly.

### Twin reference cases
- **Microsoft Corporation** — kept compounding
  - distinguished by: Mega-cap platform funding a large cloud/AI capex build from net-cash strength while the core franchise keeps growing — the same 'reinvest through the balance sheet' pattern, and it sits in this very peer roster.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Amazon.com** — kept compounding
  - distinguished by: A dominant franchise that repeatedly depressed near-term free cash flow with heavy infrastructure investment while the market debated whether the spend would earn its return — a runway-vs-already-priced analogue in the roster.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Meta Platforms** — kept compounding
  - distinguished by: An ad-driven platform that absorbed a sharp step-up in AI/infrastructure spend against skeptics questioning payback, then reaccelerated on the core — parallel to the capex-versus-ad-engine debate here.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Cisco Systems** — re-rated to fair value (LLM-claimed — verify)
  - distinguished by: A category-leading franchise whose multiple peaked on an infrastructure-buildout narrative and then de-rated for years even as the business stayed profitable — the cautionary 'quality was real but fully paid for' pattern.
  - source: [LLM-suggested, unverified]
- **Intel Corporation** — re-rated to fair value (LLM-claimed — verify)
  - distinguished by: A once-unassailable compute franchise where a heavy capital-intensity cycle coincided with a new-entrant compute-architecture challenge and returns on capital fell — a reminder that incumbency plus rising capex can precede a de-rate.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Next results print** — ~2026-10-20 `[cadence-estimate]` — the next reported quarter against the committed trajectory [34]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 22.9x vs peer median 18.0x (+27%); P/E 17.2x vs peer median 23.4x (-26%) [25]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-08-12 · multiples as-of 2026-08-10 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [35]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **15.72x** | **$259,118.6M EBITDA †** |
| peer-median NTM TEV/EBITDA | 10.87x | $374,732.7M EBITDA |
| peer-median LTM TEV/EBITDA | 18x | $226,296.9M EBITDA |
| **name NTM TEV/Rev** | **7.44x** | **$547,492.6M Revenue †** |
| peer-median NTM TEV/Rev | 4.01x | $1,015,796.7M Revenue |
| peer-median LTM TEV/Rev | 4.8x | $848,613.5M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $231454.7M · FY27E $294832.6M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $497687.6M · FY27E $606647.4M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)

### The EV gap — our base case vs the street

_No gap is struck for this name: shares unavailable. The consensus side alone still routes to **two-ratio** at FY2026, so the form is known even though the comparison is not._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 25.8x as-of 2026-06-30 — trailing range 10.9–24.8x (median 17.4x) over 37 closes → 100%ile → near-ceiling; P/LTM EPS 27.3x [24]

## Peer comps
- **Peer set (roster · caps · business)** — [36]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Meta Platforms | $1474.6B | engages in the development of products that enable people to connect and share with friends and family through mobile devices, personal computers (United States) |
| Amazon.com | $2883.0B | engages in the retail sale of consumer products, advertising, and subscriptions service through online and physical stores in North America and internationally. (United States) |
| Microsoft Corporation | $3656.6B | develops and supports a portfolio of technology solutions for individuals and businesses worldwide. (United States) |
| Reddit | $29.5B | operates a digital community in the United States and internationally. (United States) |
| Pinterest | $13.0B | operates as a visual search and discovery platform in the United States, Canada, Europe, and internationally. (United States) |
| Netflix | $309.0B | provides entertainment services worldwide. (United States) |
| The Trade Desk | $6.3B | operates as a technology company in the United States and internationally. (United States) |
| Snap Inc. | $8.8B | operates as a technology company in North America, Europe, and internationally. (United States) |
| DoorDash | $92.1B | operates a commerce platform that connects merchants, consumers, and dashers in the United States and internationally. (United States) |
| Match Group | $8.4B | provides digital technologies in the United States and internationally. (United States) |

_the name: $4195.0B_

- **Comparability (confidence gate):** market caps span $6.3B–$3656.6B (577x); the name is $4195.0B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [26]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [37]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 7.44 | 1.45 | 4.01 | 4.49 | 9.48 |
| NTM TEV/EBITDA | 15.72 | 7.1 | 10.87 | 12.33 | 21.07 |
| NTM P/E | 25.86 | 7.4 | 19.75 | 19.7 | 33.11 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [38]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| **Alphabet Inc. · the name** | **$4,195.0B** | **22.9** | **9.2** | **17.2** | **39%** | **20%** | **0.7** | **121,683 (net cash)** |
| Microsoft Corporation | $3,656.6B | 18.0 | 11.2 | 27.4 | 59% | 18% | 0.6 | 51,970 |
| Amazon.com | $2,883.0B | 16.1 | 3.9 | 21.5 | 22% | 16% | 1.3 | 128,647 |
| Meta Platforms | $1,474.6B | 13.1 | 6.6 | 21.8 | 48% | 28% | 1.0 | 22,058 |
| Netflix | $309.0B | 20.5 | 6.5 | 23.4 | 30% | 16% | 1.1 | 7,527 |
| DoorDash | $92.1B | 57.3 | 5.7 | 111.6 | 9% | 34% | 2.1 | 2,042 (net cash) |
| Reddit | $29.5B | 32.9 | 9.6 | 35.8 | 29% | 67% | 0.0 | 2,766 (net cash) |
| Pinterest | $13.0B | 35.8 | 2.8 | 175.2 | 7% | 17% | 3.3 | 78 (net cash) |
| Snap Inc. | $8.8B | NM | 1.6 | NM | -2% | 13% | NM | 1,566 |
| Match Group | $8.4B | 9.4 | 3.3 | 12.9 | 34% | 2% | 3.0 | 3,084 |
| The Trade Desk | $6.3B | 6.6 | 1.8 | 15.9 | 23% | 12% | 0.5 | 1,051 (net cash) |
| Peer median (peers) | $60.8B | 18.0 | 4.8 | 23.4 | 26% | 16% | 1.1 | 2,325 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [29]  <!-- ds-table -->

|  | Dec-2021 | Dec-2022 | Dec-2023 (R) | Dec-2024 (R) | Dec-2025 | Jun-2026 (LTM) |
|---|---|---|---|---|---|---|
| Gross margin | 57% | 55% | 57% | 58% | 60% | 61% |

_Revenue YoY (latest same-quarter): +24.2% (Q2 Jun-30-2026 vs Q2 Jun-30-2025). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** flat (trailing ~1.7y): 12,264,000,000 (2024-09-30) → 12,230,000,000 (2026-06-30), -0.3% [39]
- **Non-operating earnings:** 3 of the trailing four quarters carry a material block from BELOW the operating line — 2025-09-30 +$12,759M (29% of pre-tax · 12% of revenue) · 2026-03-31 +$37,716M (49% of pre-tax · 34% of revenue) · 2026-06-30 +$97,983M (71% of pre-tax · 82% of revenue) — netting +$151,120M across the four. A trailing EPS or P/E spanning them is not an operating anchor, and the LTM figure carries the SUM, not the largest of them. [14]
- **Return ratios — per fiscal period** — [40]  <!-- ds-table -->

|  | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|
| RoE % | 32.1% | 23.6% | 27.4% | 32.9% | 35.7% | 48.7% |
| RoCE % | 18.5% | 16.5% | 17.6% | 21.0% | 19.3% | 15.8% |
| RoA % | 14.5% | 12.9% | 13.7% | 16.5% | 15.4% | 13.0% |
| Total debt/equity | 0.11x | 0.12x | 0.11x | 0.09x | 0.16x | 0.19x |
| Current ratio | 2.93x | 2.38x | 2.10x | 1.84x | 2.01x | 2.72x |
| Dividend/sh | none | none | none | none | 0.38 | 0.05 |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-08-10)_
- **Horizon read (FQ — next-2Q revision breadth)** — [41]:
  - EPS Normalized FQ3 2026: 1m 17↑/14↓, 2m 18↑/12↓, 3m 18↑/13↓
  - EPS Normalized FQ4 2026: 1m 16↑/13↓, 2m 16↑/13↓, 3m 18↑/12↓
  - EPS (GAAP) FQ3 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/1↓
  - EPS (GAAP) FQ4 2026: 1m 0↑/1↓, 2m 0↑/1↓, 3m 0↑/1↓
  - Revenue FQ3 2026: 1m 32↑/1↓, 2m 31↑/1↓, 3m 32↑/1↓
  - Revenue FQ4 2026: 1m 30↑/2↓, 2m 30↑/2↓, 3m 31↑/1↓
  - EBITDA FQ3 2026: 1m 12↑/9↓, 2m 12↑/9↓, 3m 13↑/9↓
  - EBITDA FQ4 2026: 1m 14↑/7↓, 2m 13↑/8↓, 3m 14↑/7↓
  - EBIT FQ3 2026: 1m 17↑/14↓, 2m 17↑/13↓, 3m 21↑/10↓
  - EBIT FQ4 2026: 1m 18↑/12↓, 2m 19↑/11↓, 3m 20↑/10↓
  - _+7 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS Normalized: 10.6 (12m) → 11.1 (9m) → 11.5 (6m) → 14.2 (3m) → 14.2 (2m) → 14.2 (1m) → 20.6 (latest); net +93% (12m→latest) | FY 2026 EPS (GAAP): 10.6 (12m) → 11.1 (9m) → 11.5 (6m) → 14.2 (3m) → 14.2 (2m) → 14.2 (1m) → 20.6 (latest); net +95% (12m→latest) | FY 2026 Revenue: 439,588.0 (12m) → 453,197.4 (9m) → 470,308.0 (6m) → 486,659.9 (3m) → 487,719.9 (2m) → 488,501.5 (1m) → 497,687.6 (latest); net +13% (12m→latest) | FY 2026 EBITDA: 203,447.2 (12m) → 211,886.9 (9m) → 217,676.3 (6m) → 227,509.8 (3m) → 227,055.7 (2m) → 227,966.5 (1m) → 231,454.7 (latest); net +14% (12m→latest) | FY 2026 EBIT: 147,394.5 (12m) → 153,811.4 (9m) → 158,508.0 (6m) → 169,137.0 (3m) → 169,849.3 (2m) → 170,134.3 (1m) → 171,315.2 (latest); net +16% (12m→latest) | FY 2026 Interest Expense: -3,880.0 (12m) → -3,600.0 (9m) → -3,200.0 (6m) → -3,297.5 (3m) → -3,297.5 (2m) → -3,538.0 (1m) → -4,441.3 (latest); worsening (magnitude away from zero) (12m→latest) | FY 2026 EBT (GAAP): 152,482.0 (12m) → 159,498.4 (9m) → 165,124.8 (6m) → 212,274.8 (3m) → 211,448.9 (2m) → 211,712.5 (1m) → 311,618.9 (latest); net +104% (12m→latest) | FY 2026 Net Income (Excl. Excep): 127,497.0 (12m) → 134,125.1 (9m) → 138,941.1 (6m) → 174,028.7 (3m) → 172,920.8 (2m) → 173,052.7 (1m) → 253,526.7 (latest); net +99% (12m→latest) | FY 2026 Net Income (GAAP): 126,745.4 (12m) → 133,846.6 (9m) → 139,189.7 (6m) → 174,050.4 (3m) → 173,596.0 (2m) → 173,827.4 (1m) → 251,783.5 (latest); net +99% (12m→latest)  [data ≥ 2026-08-10 · export date unverified] [42]
- **Cross-name anchor (NTM forward-multiple ladder)** — [43]:
  - NTM: TEV/REV 7.44 · TEV/EBITDA 15.72 · TEV/EBIT 21.37 · Price/Earnings 25.86 · PEG 1.80 · P/BV –
  - FY 2026: TEV/REV 8.22 · TEV/EBITDA 17.68 · TEV/EBIT 23.88 · Price/Earnings 16.69 · PEG 1.16 · P/BV 5.78
  - FY 2027: TEV/REV 6.74 · TEV/EBITDA 13.88 · TEV/EBIT 19.11 · Price/Earnings 23.31 · PEG 1.63 · P/BV 4.63
  - FY 2028: TEV/REV 5.67 · TEV/EBITDA 10.72 · TEV/EBIT 15.90 · Price/Earnings 19.87 · PEG 1.39 · P/BV 3.68
  - _+4 later fiscal years in JSON_
- **Current guide (latest results filing):** _UNKNOWN_ — no guide in any of the 3 parsed release(s)
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [44]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| Capital Expenditure | '(195,000.00) - (205,000.00)' | FY 2026 | 2026-07-22 | fresh | spend ≤ ceiling 1/1 | FY 2025 MET |
| DPS | 0.22 | FQ3 2026 | 2026-07-22 | fresh | actual ≥ floor 1/1 · 7 at-guide (±0.5% of a point, not adjudicated) | FQ1 2026 AT GUIDE (±0.5% of a point) |
| Revenue | none current (last: 11,800.0) | FY 2007 | 2006-03-20 | 7462d (stale) | actual ≥ floor 3/3 | FY 2007 MET |
| EPS Normalized | none current (last: 0.18) | FY 2006 | 2005-10-20 | 7613d (stale) | actual ≥ floor 1/1 | FY 2006 MET |
| EPS (GAAP) | none current (last: 0.18) | FY 2006 | 2005-10-20 | 7613d (stale) | actual ≥ floor 1/1 | FY 2006 MET |

_CIQ states every guide as a LEVEL in the metric's own units. Where management guided a RATE, the level is CIQ's arithmetic on its own base, not a figure the company published — check the release before quoting one as guidance._

- **Consensus stats (target + ratings):** Target price: mean $428.04, median $428.00, high/low 515.00/340.00, N 55/56; Ratings: Buy 45, Outperform 13, Hold 6, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 44, Outperform 13, Hold 6, Underperform 0, Sell 0, No Opinion 1, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0, Buy 1, Outperform 0, Hold 0, Underperform 0, Sell 0, No Opinion 0, Buy 6, Outperform 0, Hold 0, Underperform 0, Sell 0  [data ≥ 2026-08-10 · export date unverified] [27]
- **Revision-event log (250 events · 18 broker-days)** — [45]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-08-10 | Monness, Crespi, Hardt & Co., Inc. | 4 | 2 | — | 2 | EPS Normalized FY 2026 | 14.7 | 20.8 | +6.1 |
| 2026-07-31 | China Merchants Securities (HK) Co., Ltd | 19 | 11 | 8 | — | EBITDA FY 2026 | 193457.0 | 97525.0 | −95932.0 |
| 2026-07-30 | KGI Securities Co. Ltd. | 8 | 7 | 1 | — | EBITDA FY 2026 | 203272.0 | 204252.0 | +980.0 |
| 2026-07-28 | Arete Research Services LLP | 4 | 1 | 3 | — | EBITDA FY 2026 | 218000.0 | 214000.0 | −4000.0 |
| 2026-07-28 | Loop Capital Markets | 22 | 14 | 8 | — | Revenue FQ3 2026 | 119344.7 | 126644.6 | +7299.9 |
| 2026-07-28 | Oppenheimer & Co. Inc. | 13 | 10 | 3 | — | EBITDA FQ3 2026 | 58892.0 | 60271.0 | +1379.0 |

_+12 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2004 +33%, FY2005 +0%, FY2006 +9%, FY2007 -3%, FY2008 -20%, FY2009 +2%, FY2010 +3%, FY2011 -5%, FY2012 -1%, FY2013 -2%, FY2014 +6%, FY2015 -1%, FY2016 -1%, FY2017 -44%, FY2018 +5%, FY2019 +6%, FY2020 +14%, FY2021 +4%, FY2022 -4%, FY2023 +1%, FY2024 +0%, FY2025 +2%; Revenue surprise: FY2004 +2%, FY2005 +0%, FY2006 +1%, FY2007 +1%, FY2008 +0%, FY2009 +0%, FY2010 +1%, FY2011 -1%, FY2012 -4%, FY2013 +1%, FY2014 -1%, FY2015 +1%, FY2016 +2%, FY2017 +1%, FY2018 +0%, FY2019 -1%, FY2020 +2%, FY2021 +1%, FY2022 -0%, FY2023 +1%, FY2024 -0%, FY2025 +1% (GAAP-EPS basis; +beat / −miss) [46]

## Leverage & survival
- **Net debt / EBITDA [NET]:** -0.7x [9]
- **Total debt / EBITDA vs peers:** name 0.7x vs peer median 1.1x (comps TOTAL-debt/EBITDA basis) [47]
- **Net debt / OCF:** -0.7x [48]
- **Interest coverage:** 76.9x [49]
- **Self-funding:** self-funding: YES — latest-Q OCF > 0 AND LTM FCF > 0 [50]
- **Credit health** — [31]  <!-- ds-table -->

|  | Name | Peer median |
|---|---:|---:|
| Overall | 1 | 3 |
| Operational | 2 | 3 |
| Solvency | 1 | 3 |
| Liquidity | 1 | 3 |

_S&P issuer rating AA+ · scale 1=strongest … 4=weakest (S&P-MI PD model)_


- **FCF sign:** positive [10]
- **Free cash flow ($M):** 22665.0 — basis: CIQ 'Levered Free Cash Flow', NOT CFO − capex: on the same sheet and period [LTM 12 months Jun-30-2026], CFO $185,675.0M − capex $132,402.0M = $53,273.0M — 0.43x apart. Company-defined FCF is usually the second; a per-share or self-funding read should say which it used. [12]
- **Debt schedule vintage:** the debt schedule is 200d old (source filed 2026-02-05); no Item 1.02 (termination of a material agreement) has been filed since [51]
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Feb-05-2026** — [52]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 16 US Dollar Notes | Bonds and Notes | $2,000.0M | 2.000% | NA | 2026-08-15 | N | N | USD |
| Revolving Credit Facilities | Revolving Credit | – | NA | NA | 2026-04-01 | N | N | USD |

_17 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-08-24 reference:
  - **matured (pre-reference): $2,000.0M** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-04-01 (145d before ref): – Revolving Credit Facilities
    - 2026-08-15 (9d before ref): $2,000.0M 16 US Dollar Notes
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
- **Capital-structure aggregates:** senior bonds 99,876.5; leases 20,627.0; total principal 122,189.5; total debt 120,791.0 (3 months Q2 Jun-30-2026) ($M) [53]
- **Maturity resolution (8-K verbatim):** _UNKNOWN_ — (P3) 8-K body at 8-K 0001652044-26-000031 (2026-04-02) states no maturity-resolution event

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [54]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [55]
  - net debt / EBITDA (CIQ, GAAP basis): -0.7x
  - total debt / EBITDA (CIQ comps, GAAP basis): 0.7x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: UNKNOWN (not disclosed)

## ⚠ Analyst caveats — verify before the verdict

_1 to verify._

- NOT A CURRENT SCREEN CANDIDATE — assembled because the name carries an operator follow decision — Alphabet Class A, HELD — a $50,000 / 5.0% NAV starter entered 2026-08-14 at ~$345 under an external IC memo, recorded here so the machinery can see a live position it was previously blind to. Followed under the QUALITY book: the binding question is duration — whether Search and Cloud economics outlast what a ~26x normalized NTM multiple already pays for — not whether a de-rating is overdone, which is the overshoot twin's question and the wrong one here. The $300M-$10B band answers where the fund HUNTS, not what it may hold or follow, and this name is covered deliberately from outside it. Class A specifically: the memo, the $345.90 verified close and the frozen legs are all Class A, and GOOG (Class C) is a distinct security. The cap band decides where the fund HUNTS, not what it may hold or follow, so absence from it is not a rejection — read the verdict, not the absence: no screen run on file has evaluated it.

# Appendix — data & audit

## How to read this dossier
- The machine assembles and cites; **the analyst decides**. Nothing here is a recommendation — the verdict of record is the human's, logged to an append-only ledger with a frozen entry price.
- The machine's proposed verdict is derived deterministically from its written assessment and stays **sealed until the analyst's verdict is recorded**, so it cannot anchor the decision. A two-sided assessment proposes nothing.
- Citations [n] resolve in the Sources list at the document end. **Cited is not verified** — the reference locates the claim so you can check it.
- Reference values (peer-implied equity, price-implied levels) are shown **beside** the figures they contextualize, never differenced into an upside — the reader judges the gap.
- A value shown as UNKNOWN is honestly absent at the source — nothing is imputed.

## How these numbers were set

_Per-axis methodology from the underwrite record — the reference frame each leg was chosen against, not a re-derivation._

### Earnings · **DRAFT — not ratified by the analyst**

bear: Normalized EPS on the ~Aug-2027 fundamental horizon; all three legs struck on the same Street-like diluted-share basis, so they differ by economics and not by share count. $15.388, ~4% below the target-period Street range $16.02–16.07. IC memo 2026-08-17 §4. · base: $16.221, modestly above that Street range. IC memo 2026-08-17 §4. · bull: $16.649, above it. IC memo 2026-08-17 §4.

_No reference points recorded — stated as judgment._

### Multiple · **DRAFT — not ratified by the analyst**

bear: Normalized P/NTM turns set by judgment rather than by a statistic — the company's own multiple quartiles over its trading history (p25 21.46x, median 24.24x, p75 26.75x) are labelled `P/NTM EPS` and are NOT proven to share this normalized denominator, a basis match the memo records as LIMITED, so they are context and not load-bearing. 20.5x is compression from today's ~26.03x, and it is the SINGLE BINDING ASSUMPTION of this underwrite: Bear EPS exceeds today's NTM $13.28698, so the whole downside is a de-rating rather than an earnings fall. IC memo 2026-08-17 §5 and §7A. · base: 24.5x, a partial de-rate from today's ~26.03x. IC memo 2026-08-17 §5. · bull: 26.0x holds today's ~26.03x, conditional on demonstrated capital productivity — FY27 EBIT revisions outrunning FY27 capex revisions. IC memo 2026-08-17 §5 and §7A.

_No reference points recorded — stated as judgment._


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-08-10)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [15]  <!-- ds-table -->

|  | FY21 | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 257,637 | 282,836 | 307,394 | 350,018 | 402,836 | 445,866 | 497,688 | 606,647 |
| Revenue growth | — | +10% | — (basis) | +14% | — (basis) | — (basis) | +24% (vs FY25) | +22% |
| EBITDA ($M) | 88,987 | 88,317 | 96,239 | 127,701 | 150,175 | 173,164 | 231,455 | 294,833 |
| EBITDA margin | 35% | 31% | 31% | 36% | 37% | 39% | 47% | 49% |
| EBIT ($M) | 78,714 | 74,842 | 84,293 | 112,390 | 129,039 | 147,628 | 171,315 | 214,120 |
| Net income ($M) | 76,033 | 59,972 | 73,795 | 100,118 | 132,170 | 244,205 | 251,783 | 184,633 |
| EPS (GAAP, dil.) | 5.61 | 4.56 | 5.80 | 8.04 | 10.80 | 19.93 | 20.59 | 14.77 |
| EPS (Normalized) | 3.62 | 3.65 | 4.25 | 5.88 | 6.86 | 7.67 | 20.58 | 14.74 |
| Gain (Loss) On Sale Of Invest. ($M) | 12,270 | -5,519 | -823 | 2,671 | 24,620 | 149,012 | — | — |
| CFO ($M) | 91,652 | 91,495 | 101,746 | 125,299 | 164,713 | 185,675 | 219,079 | 265,345 |
| Capex ($M) | -24,640 | -31,485 | -32,251 | -52,535 | -91,447 | -132,402 | -201,617 | -288,144 |
| FCF (levered, CIQ) | 47,009 | 49,939 | 56,280 | 53,158 | 38,088 | 22,665 | — | — |
| D&A ($M) | 10,273 | 13,475 | 11,946 | 15,311 | 21,136 | 25,536 | — | — |
| FCF (consensus basis) ($M) | — | — | — | — | — | — | 8,719 | -18,433 |
| D&A (consensus basis) ($M) | — | — | — | — | — | — | 32,338 | 49,951 |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-08-10; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_


> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 70,426 of D&A against 14,393 in the actuals (4.89x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.

### Quarterly — every exported quarter
- **Quarterly financials** — [56]  <!-- ds-table -->

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
- **Posture:** as of Q2-26 ($M): cash & ST inv 242,474; total debt 120,791; net debt -121,683; equity 622,457; net working capital 217,413; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [57]
- **Coherence — BS vs implied-valuation bridge:** cash BS $242,474M / bridge $242,474M; debt BS $120,791M / bridge $120,791M — reconcile with the implied-valuation bridge. [58]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Feb-05-2026** — [52]  <!-- ds-table -->

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

- **8-Ks at instrument maturities:** 8-K at maturity 2026-04-01: filed 2026-04-02 [0001652044-26-000031] 5.02 Departure/Election of Directors or Certain Officers — read for resolution; 8-K at maturity 2026-04-01: filed 2026-04-10 [0001652044-26-000034] 5.02 Departure/Election of Directors or Certain Officers — read for resolution; 8-K at maturity 2026-08-15: filed 2026-08-10 [0001193125-26-342390] 8.01 Other Events, 9.01 Financial Statements and Exhibits — read for resolution [59]
- **Covenant exhibit pointers:** _UNKNOWN_ — no CIK-scoped agreement exhibit located across the filing history
- **Covenant terms (from the filed agreement):** COVENANT DIGEST — extraction failed: no agreement exhibit was located to extract from — the gap is in the pointer search, not in extraction (terms UNKNOWN, not pending). [60]

### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 4195027.6 [61]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $242,474.00M, − total debt $120,791.00M [62]
- **Implied equity at peer-median ($M, CIQ)** — [63]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 3,222,163.8 |
| NTM Revenue (Capital IQ) | 2,305,463.9 |
| NTM EBITDA (Capital IQ) | 2,931,985.4 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Alphabet Inc., Q1 2026 Earnings Call, Apr 29, 2026.rtf; Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [64]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 0 · sells 91 (7 insiders, $43.05M) — in the last 182 days · last purchase $4.95M, 10% owner, 2025-08-01 (~13mo ago) · last sale $0.03M, director, 2026-07-30 (~1mo ago) · largest sale $33.36M, 10% owner, 2026-01-30 (~7mo ago) · grants 415 · last filing 2026-08-11 · other filings 753 [65]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-08-14): 70.5M → 72.7M sh (+3.1%, rising) · 0.6% of shares out (EDGAR XBRL) · DTC 2.3d · recent: 2026-08-14 72.7M · 2026-07-31 70.5M · 2026-07-15 78.7M · 2026-06-30 85.9M [66]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [67]
- **Guide verification — CIQ guide vs release:** revenue: CIQ 11800.0 vs release NO NUMERIC OUTLOOK → not cross-checked [68]

## Record & reproduce
- **Data window:** screened as of 2026-08-24 · assembled 2026-08-28 05:48 UTC
- **Extraction:** 2026-08-16.1 — every Multiples reader selects the latest close BY DATE, never by column position, and refuses on an NM or undated one rather than reaching back a quarter (#459)
- **Price store:** `mosaic-theory-pg → mosaic-theory-wb` · reaching 2026-08-26
- **Panel age:** oldest panel 16d old — 2026-08-12 (valuation.implied_expectations.tev_as_of), against a 2026-08-28 build
- **Consensus age:** consensus 18d old (2026-08-10, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001652044` · Nasdaq : GOOGL
- **Assembly log:** primary-source: 8-K 0001193125-26-342390 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 8-K 0001193125-26-234488 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 8-K 0001193125-26-216986 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 3 EX-99.1 release(s) + 1 10-Q parsed (+0.4s fetch)
- **Re-run:** `python -m vinci dossier --ticker GOOGL` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EOD gap-down detector (screen events): none`
[5] `EOD GOOGL 180d to 2026-08-24`
[6] `EOD SPY 180d to 2026-08-24 (cap-band: $4195.0B @ 2026-08-24 → large (>$25B) → SPY)`
[7] `EOD GOOGL−SPY 180d to 2026-08-24 (assembly, cap-band)`
[8] `derived from 2 cohort names; face-validity`
[9] `CIQ Net Debt $-121,683M [Q2 Jun-30-2026] ÷ CIQ EBITDA $173,164M [LTM 12 months Jun-30-2026]`
[10] `EDGAR XBRL FCF sign (screen data-record)`
[11] `CIQ transcript: Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf`
[12] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Jun-30-2026]`
[13] `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) — current multiple`
[14] `EDGAR XBRL pre-tax − operating, quarters 2025-06-30..2026-06-30`
[15] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[16] `EDGAR companyfacts Goodwill (as at 2026-06-30)`
[17] `EDGAR companyfacts IntangibleAssetsNetExcludingGoodwill (as at 2026-06-30)`
[18] `EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2026-01-01→2026-06-30, 180d)`
[19] `EDGAR filing index (S-3/F-3 · 424B · S-1/F-1 · S-4 · S-8), window 2023-08-25→2026-08-24 · latest 0001193125-26-340264`
[20] `EDGAR filing index (SC 13D/G + SCHEDULE 13D/G — both vocabularies), window 2023-08-25→2026-08-24 · latest 0002100119-26-000161`
[21] `EDGAR XBRL ShareBasedCompensation (10-K, 2025-01-01→2025-12-31)`
[22] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[23] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[24] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[25] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[26] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[27] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[28] `CIQ Customers&Suppliers Alphabet Inc NasdaqGS GOOGL Customers.rtf`
[29] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[30] `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
[31] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-08-12`
[32] `CIQ Estimates→Revisions (Last-Month breadth, FY)`
[33] `CIQ Financials→Ratios (Return on Capital %, multi-year columns)`
[34] `cadence: EDGAR submissions (median 90d gap over 13 results 8-Ks; last print 2026-07-22)`
[35] `TEV = mcap 4195027.6 + net debt -121683.0 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-08-12, exported 2026-08-13) — simple-TEV basis`
[36] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[37] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[38] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-08-12`
[39] `EDGAR XBRL shares, trailing 2024-09-30..2026-06-30`
[40] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[41] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[42] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[43] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[44] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record) — CIQ states every guide as a LEVEL; where management guided a RATE, the level is CIQ's arithmetic, not the company's published figure`
[45] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-08-10 · export date unverified]`
[46] `CIQ Estimates→Surprise (annual)`
[47] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-08-12`
[48] `CIQ Net Debt $-121,683M [Q2 Jun-30-2026] ÷ CIQ OCF $185,675M [LTM 12 months Jun-30-2026]`
[49] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Jun-30-2026]`
[50] `EDGAR latest-Q OCF sign + CIQ LTM FCF sign`
[51] `CIQ Capital Structure Details — A 2025 filed Feb-05-2026`
[52] `CIQ Financials→Capital Structure Details (A 2025 filed Feb-05-2026)`
[53] `CIQ Financials→Capital Structure Summary`
[54] `10-Q 0001652044-26-000071`
[55] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[56] `CIQ Financials→Income Statement (quarterly, full exported history)`
[57] `CIQ Financials→Balance Sheet (quarterly, Q2-26)`
[58] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[59] `EDGAR 8-K submissions (±10d of instrument maturities)`
[60] `fenced Tier-2 digest (P1)`
[61] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-08-12`
[62] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-08-12`
[63] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-08-12`
[64] `CIQ transcript(s): Alphabet Inc., Q1 2026 Earnings Call, Apr 29, 2026.rtf; Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf`
[65] `EDGAR Form 4 (latest 0001193125-26-345383; 497 filings in the 1095d scanned; counts over 182d)`
[66] `FINRA consolidated short interest (settle 2026-08-14); DTC = 72,705,550 short ÷ 32,050,189 screen 90d ADV`
[67] `10-Q maturity wall vs CIQ capital panel (same window)`
[68] `CIQ revenue guide vs release actual/outlook`