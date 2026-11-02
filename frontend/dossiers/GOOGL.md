# Dossier — Alphabet Inc. (Nasdaq: GOOGL)

_November 2, 2026 · extraction 2026-10-30.submissions-pages_

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

> ⚠ **Verify before the verdict:** Untraceable figure -0.6 (a bull point); Untraceable figure 60.3 (a bull point) — full caveats in Analysis.

Alphabet Inc. offers various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.
- **Segments:** Google Services 85%; Google Cloud 15%; Other Bets 0%; Unallocated Hedging Gains (Losses) -0% [1]
- **Geography:** United States 48%; Europe, The Middle East, and Africa (EMEA) 29%; Asia-Pacific (APAC) 17%; Other Americas 6%; Unallocated -0% [2]
- **Snapshot:** Nasdaq · CMP $279.84 (2026-10-30) · cap $3977.5B (2026-10-28) ⚠ implies $323.53/sh vs CMP (+15.6%) · 52-wk $244.15–$408.61 · shares 12.3B · book value/sh $53.65 [3]

**The crux — what decides this, and what would change our mind**
**Will the AI-infrastructure reinvestment cycle — $159,804M LTM capex rising toward a consensus FY27 -$318,716M — convert the $561B Cloud backlog into durable, high-return operating cash flow fast enough to justify a trailing EV/EBITDA at its own 92nd percentile, or is the price paying ahead for a runway that first drives free cash flow through a trough?**
_8 key unknowns + the evidence for/against — in Analysis_
**Next catalyst:** Early access to the Lyft app rolls out in Barcelona and Hamburg first; throughout October, the Lyft app will become a… ~2026-10 `[stated]` — calendar in Analysis

## What happened — and does it change the runway?
- **Shape:** gradual bleed — no discrete gap-down detected [4]
- **Price (180d):** -0.3% [5]
- **Market (SPY) 180d:** 7.5% [6]
- **vs market (180d):** -7.8% [7]
- **Read:** mixed: name -0% vs cohort median -0% (cohort steady) [8]
- **Net debt / EBITDA:** -0.6x [9]
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
| Screen value / share | $225.54 | spot-independent · EV/EBIT 21.5x · on 12,294,000,000 shares outstanding |
| Dilution test / share | $223.50 | + 112,000,000 dilutive shares (diluted less basic weighted average, latest 10-Q) |
| Overall confidence | firm |  |

**The operator's decision: R3_forward_pe** — 2026-09-01, operator

⚠ **The machine reads R4_forward_ev_ebit.** The operator's decision stands; it changes only by hand.

> OPERATOR RE-TAG 2026-09-01. The machine proposed R1 (mid-cycle margin x own-history EV/EBITDA); the underwrite of record is a FORWARD P/E on normalized EPS (IC memo 2026-08-17 SS5/SS7A), which is an EQUITY basis and reads no enterprise value at all. That is a judgment about which arithmetic fits this name and the machine cannot derive it: Alphabet's downside is multiple compression on earnings that still GROW (Bear EPS $15.388 exceeds today's NTM $13.28698), so a recipe reaching equity through EV minus net debt would model the wrong thing. The computed values below are the machine's R1 arithmetic and are left untouched - a re-tag is a judgment about the RECIPE, never a freeze on the numbers.

_Where this decision is recorded: docs/records/2026-09-01-r3-reaches-the-create-path.md (#557)_

**Mid-cycle assumption under strain.** The last twelve months' operating margin of 33.3% (CIQ EBIT) sits 7.0 points ABOVE the 9-year median of 26.3% (EDGAR GAAP operating income) that R1 reverts to. R1 pairs that median with the median multiple from the same history, so an R1 value answers what the business is worth if it is still what it was. If the gap is STRUCTURAL — a changed mix or model — that history understates it; if it is a cyclical PEAK, reverting is right. The two sources agree within 0.0 points on FY2024, so the gap is the business, not the source.

**data_quality: vendor_bridge**
- vendor bridge: d_and_a supplied by the CIQ workbook because EDGAR had no usable tag

_The machine’s read: EV/NTM EBIT (R4) — all three ratified conditions hold: NTM EBIT > 0: CIQ NTM TEV/EBIT 16.6x · R1 cannot anchor: EBITDA basis divergent: consensus-implied D&A 5.75× the actuals · R3 cannot price it cleanly: CIQ's FY P/E struck on gaap EPS; 4 of the trailing 4 quarters carry material non-operating income (≥2 ruled). R1's own arithmetic is left in this block._

## The case
_(top points; the full argument is in Analysis)_

_Bull case — the runway outlasts the price:_
- Google Cloud revenue grew 103% to $30.7B in Q3 2026 with operating margin expanding from 23.7% to 36.2%, evidencing both demand-driven scale and operating leverage in the segment the runway case rests on. [11]
- Google Cloud backlog reached $561 billion in Q3 (up from $514B a quarter earlier), with management expecting to recognize just over 55% as revenue over the next 24 months — a contracted-demand signal supporting a longer, larger reinvestment runway. [11]
- Search query growth is the highest in five years and AI Mode surpassed 1 billion monthly active users, management framing AI features as expansionary to query volume rather than cannibalistic to the core ad engine. [11]
_Bear case — the price already pays for it:_
- Capex escalated to $159,804M LTM (from $91,447M FY25 and $52,535M FY24) against CFO of $179,551M, and consensus models FY27 capex of -$318,716M — the reinvestment the bull case celebrates is also what is pressuring free cash flow, a real and load-bearing counterweight. [12]
- LTM levered free cash flow is negative $1,162.5M on CIQ's basis, and the trailing LTM free-cash-flow sign is negative even as CFO minus capex on the same sheet is +$19,747M — the basis decides whether the business generated or consumed cash this period, and the self-funding read is MIXED until that is resolved. [13]
- Trailing GAAP earnings are not an operating anchor: four consecutive quarters each carry a material below-the-operating-line block netting +$140,237M, including +$97,983M in 2026-06-30 (82% of revenue) — the LTM P/E of 17.3x and the LTM net income of $235,694M embed non-operating gains, not operating power. [14]

## Financial snapshot
- **Financial snapshot** — [12]  <!-- ds-table -->

|  | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue ($M) | 282,836 | 307,394 | 350,018 | 402,836 | 471,098 | 499,579 | 634,499 |
| Revenue growth | +10% | — (basis) | +14% | — (basis) | — (basis) | +24% (vs FY25) | +27% |
| EBITDA ($M) | 88,317 | 96,239 | 127,701 | 150,175 | 185,516 | 227,919 | 303,791 |
| EBITDA margin | 31% | 31% | 36% | 37% | 39% | 46% | 48% |
| EBIT ($M) | 74,842 | 84,293 | 112,390 | 129,039 | 156,976 | 168,487 | 216,958 |
| Net income ($M) | 59,972 | 73,795 | 100,118 | 132,170 | 235,694 | 240,071 | 186,433 |
| EPS (GAAP, dil.) | 4.56 | 5.80 | 8.04 | 10.80 | 19.15 | 19.71 | 14.81 |
| Gain (Loss) On Sale Of Invest. ($M) | -5,519 | -823 | 2,671 | 24,620 | 129,109 | — | — |
| FCF (levered, CIQ) | 49,939 | 56,280 | 53,158 | 38,088 | -1,162 | — | — |

_FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_

_table shows the last 4 fiscal years · 5 earlier years are in the Appendix_

> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 73,132 of D&A against 12,710 in the actuals (5.75x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.


**Capital allocation — created or destroyed**

- **Impairment headroom — goodwill + intangibles remaining:** $66,934.0M [15]
- **Goodwill:** $58,117.0M [15]
- **Intangibles (net):** $8,817.0M [16]
- **Impairment:** _NONE IN THE CURRENT PERIOD_ — the filer records no impairment under any tag tried
- **Buyback — cash:** $0.0M [17]
- **Buyback — shares repurchased:** _UNKNOWN_ — no annual repurchased-share count under TreasuryStockSharesAcquired — EDGAR XBRL companyfacts
- **Buyback — average cost/share:** _UNKNOWN_ — no TreasuryStockAcquiredAverageCostPerShare, and the share-count leg is absent — refused rather than derived (EDGAR XBRL companyfacts). The repurchase CASH and SHARE COUNT above are each sound on their own basis; it is their QUOTIENT that is not a price
- **Acquisition consideration:** _UNKNOWN_ — no acquisition consideration under any of BusinessCombinationConsiderationTransferred1, BusinessCombinationConsiderationTransferred, PaymentsToAcquireBusinessesNetOfCashAcquired — EDGAR XBRL companyfacts
- **Registered offering pipeline (equity/debt not distinguished):** shelf registrations 2 (S-3ASR, last 2026-06-01); prospectus supplements 28 (424B2/424B5, last 2026-08-07) · employee-plan (S-8) 1 (S-8, last 2026-07-23) — routine — 3y window to 2026-10-16 [18]
- **Schedule 13D/G filing activity:** no 13D on file · Schedule 13G filings 13 (SC 13G/A/SCHEDULE 13G/SCHEDULE 13G/A, last 2026-04-29) — 3y window to 2026-10-16 [19]
- **Stock-based compensation:** stock-based compensation $24,953.0M = 6.2% of revenue ($402,836.0M, FY 2025-01-01→2025-12-31) [20]
- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — goodwill and intangible impairment separate by TAG, but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate above is complete only at the goodwill/intangible level
- **Peer acquired-asset intensity — goodwill + intangibles** — [21]  <!-- ds-table -->

|  | mcap $M | acquired $M | assets $M | % assets | % mcap | why |
|---|---:|---:|---:|---:|---:|---|
| **GOOGL** | **3,977,464** | **66,934** | **1,003,312** | **7%** | **2%** | **—** |
| MSFT | 3,943,384 | 120,928 | 779,403 | 16% | 3% | — |
| AMZN | 2,746,195 | 32,940 | 1,243,390 | 3% | 1% | — |
| META | 1,565,672 | 27,113 | 478,836 | 6% | 2% | — |
| NFLX | 254,551 | 34,605 | 58,682 | 59% | 14% | — |
| DASH | 73,440 | 7,434 | 20,580 | 36% | 10% | — |
| RDDT | 25,916 | 52 | 3,962 | 1% | 0% | — |
| PINS | 11,847 | 556 | 4,951 | 11% | 5% | — |
| SNAP | 10,080 | 1,874 | 7,470 | 25% | 19% | — |
| MTCH | 9,655 | 2,488 | 4,034 | 62% | 26% | — |
| TTD | 6,033 | — | 5,764 | — | — | no-tag |

- **Median — all peers (n=9):** 16% of assets · 5% of market cap
- **Median — peers ≥ $1,000M market cap (n=9):** 16% of assets · 5% of market cap
- _Read the ASSETS column for the peer judgement — it measures how acquisitive the balance sheet is. The market-cap column sizes the exposure but moves with the price, so a de-rated name shows a high ratio on unchanged accounting._
- **Peer write-down history — did they MARK DOWN what they carry? (trailing 5 fiscal years)** — [22]  <!-- ds-table -->

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
- **vs own trading history:** EV/EBITDA (TEV/LTM) 22.9x as-of 2026-09-30 — trailing range 10.9–25.8x (median 17.5x) over 38 closes → 92%ile → near-ceiling; P/LTM EPS 17.3x [23]
- **vs peers:** EV/EBITDA 20.3x vs peer median 15.8x (+28%); P/E 17x vs peer median 20.9x (-19%) [24]
- **Forward multiples:** P/FY26E (normalized) 19.8x (EPS $14.14); P/FY26E (GAAP) 14.2x (EPS $19.71); P/FY27E (normalized) 18.4x (EPS $15.19); P/FY27E (GAAP) 18.9x (EPS $14.81) — at $279.84 as-of 2026-10-30 [25]
- **What CIQ's EV/EBITDA divides:** CIQ's 22.9x divides TEV $3,854,283M (comps, 2026-10-28) by $168,309M, which reproduces neither pairing: reported LTM EBITDA $185,516M (-9.3%) and reported LTM EBITDA $185,516M + rent $5,084M (FY ending 2025-12-31) = $190,600M (-11.7%). Read CIQ's own denominator before comparing it with a multiple of reported EBITDA.
- **Comparability:** market caps span $6.0B–$3943.4B (654x); the name is $3977.5B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [26]
- **The street, for contrast (target · ratings):** Target price: mean $404.54, median $400.00, high/low 500.00/300.00, N 53/53; Ratings: Buy 43, Outperform 10, Hold 5, Underperform 0, Sell 0, No Opinion 2  [data ≥ 2026-11-01 · export date unverified] [27]

# Analysis — full dossier

## What moved the price — and did it move alone?
- **Read — what moved:** gradual bleed — no discrete gap-down detected [4]
- **Gap-down dates:** _UNKNOWN_ — no gap-down events on the data-record

_Company-specific or market-wide?_
- **Name 180d return:** -0.3% [5]
- **Market (SPY) 180d return:** 7.5% [6]
- **Relative vs market:** -7.8% [7]
- **Cohort read:** mixed: name -0% vs cohort median -0% (cohort steady) [8]
- **Graph cohort** (`graph_coverage.json node=US:0001652044; EOD 180d ret`):
  - [1h] EXTR: 23% · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "]
  - [1h] NN: -33% · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"]
  - [2h] T: no bars · via NN —supplier→ Google ["we and our customers must have access to barometric pressure measurements and 2D"] · NN —customer→ AT&T Services, Inc. ["Our Pinnacle solution, launched in partnership with AT&T
  - [2h] AMZN: -0% · via EXTR —supplier→ Google Cloud Platform ["Our cloud networking solution is available on all major cloud providers (Amazon "] · EXTR —supplier→ Amazon Web Services ["Our cloud networking solution is avai
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
- **Segments (profit — the filer's own measure, 10-K):** FY2025 segment operating income (10-K XBRL): Google Services $139,404M (40.7% margin) · Google Cloud $13,910M (23.7% margin) · All Other −$7,515M (margin n.m.) — segments sum $145,799M vs consolidated $129,039M (−$16,760M not allocated to segments). [28]
- **Customers:** 31 mapped client relationship(s) — roster in JSON; concentration %, when disclosed, is the 10-Q read above [29]
- **Geographic:** United States 48%; Europe, The Middle East, and Africa (EMEA) 29%; Asia-Pacific (APAC) 17%; Other Americas 6%; Unallocated -0% [2]

## The argument

**Evidence balance:** mixed — compounding Cloud and margin expansion run against a trailing multiple at its own ceiling and a capex-driven free-cash-flow trough.

**Reproducibility: the draws DISAGREED** — 5 of 5 draws gave 4x mixed, 1x strongly-bullish. The read below is the first draw carrying the majority lean, and the machine proposal is withheld. A tally of this build, not a rate.

### Bull case — the runway outlasts the price
- Google Cloud revenue grew 103% to $30.7B in Q3 2026 with operating margin expanding from 23.7% to 36.2%, evidencing both demand-driven scale and operating leverage in the segment the runway case rests on. [11]
- Google Cloud backlog reached $561 billion in Q3 (up from $514B a quarter earlier), with management expecting to recognize just over 55% as revenue over the next 24 months — a contracted-demand signal supporting a longer, larger reinvestment runway. [11]
- Search query growth is the highest in five years and AI Mode surpassed 1 billion monthly active users, management framing AI features as expansionary to query volume rather than cannibalistic to the core ad engine. [11]
- LTM revenue YoY grew +24.7% (Q3 Sep-30-2026 vs Q3 Sep-30-2025) and Q3 consolidated revenue was up 25%, a run-rate acceleration for a business already at roughly $0.5T annual scale. [30]
- Absolute EBITDA rose every year from $35,813M (FY17) to $185,516M (LTM Sep-30-2026) with the EBITDA margin climbing to 39% and gross margin to 61% LTM — the absolute-dollar reconciler shows compounding, not a margin-squeezed business. [31]
- FY2025 segment operating income shows Google Services at $139,404M (40.7% margin) and Google Cloud at $13,910M (23.7% margin) on the 10-K XBRL, grounding the quality claim in disclosed segment profitability rather than a blended figure. [28]
- The balance sheet carries net cash: net-debt/EBITDA -0.6x, interest coverage 60.3x and an S&P AA+ issuer rating, so the heavy AI capex is self-funded from a fortress position rather than requiring external leverage. [32]
- ROE reached 44.3% LTM and ROCE 15.6%, with RoE rising across the multi-year window — a high-return profile consistent with the durable-compounder thesis. [33]

### Bear case — the price already pays for it
- Capex escalated to $159,804M LTM (from $91,447M FY25 and $52,535M FY24) against CFO of $179,551M, and consensus models FY27 capex of -$318,716M — the reinvestment the bull case celebrates is also what is pressuring free cash flow, a real and load-bearing counterweight. [12]
- LTM levered free cash flow is negative $1,162.5M on CIQ's basis, and the trailing LTM free-cash-flow sign is negative even as CFO minus capex on the same sheet is +$19,747M — the basis decides whether the business generated or consumed cash this period, and the self-funding read is MIXED until that is resolved. [13]
- Trailing GAAP earnings are not an operating anchor: four consecutive quarters each carry a material below-the-operating-line block netting +$140,237M, including +$97,983M in 2026-06-30 (82% of revenue) — the LTM P/E of 17.3x and the LTM net income of $235,694M embed non-operating gains, not operating power. [14]
- The LTM Gain (Loss) On Sale Of Invest. line is $129,109.0M — a single marked-material non-operating item that dwarfs most quarters' operating earnings and inflates any trailing earnings-based multiple struck off the actual row. [12]
- FY2026 EPS (GAAP) consensus breadth is 3↑/40↓ in the last month and the latest revision events on 2026-11-01 are overwhelmingly downward across EBT, EBIT, EBITDA and net income — near-term estimate momentum is negative even as the stock prices durability. [34]
- EV/EBITDA (TEV/LTM) sits at 22.9x — its own 92nd percentile over 38 quarters (range 10.9–25.8x, median 17.5x) — so on its own trailing history the quality is priced near the ceiling, the thing a fully-priced read must beat; this is trailing-only with no forward basis to distinguish a temporarily depressed from a permanently elevated level. [35]

### Decisive question
**Will the AI-infrastructure reinvestment cycle — $159,804M LTM capex rising toward a consensus FY27 -$318,716M — convert the $561B Cloud backlog into durable, high-return operating cash flow fast enough to justify a trailing EV/EBITDA at its own 92nd percentile, or is the price paying ahead for a runway that first drives free cash flow through a trough?**

### …evidence for
- Cloud grew 103% to $30.7B with margin expanding to 36.2% and backlog of $561B, of which just over 55% is expected to convert to revenue within 24 months — the demand-to-revenue mechanism is contracted, not speculative. [11]
- Management states an attractive ROIC meaningfully above cost of capital through the investment cycle and nearly 100 customers now use TPUs with new TPU-system partnerships (Oracle, Crux AI), indicating the capex is being matched to signed demand. [11]

### …evidence against
- LTM levered free cash flow is negative $1,162.5M and capex of $159,804M already nearly absorbs CFO of $179,551M, with consensus FY27 capex at -$318,716M — the cash return on this reinvestment is not yet visible in trailing free cash flow. [12]
- Future purchase commitments of $924 billion plus $152 billion of pre-commencement leases quantify the forward obligation the backlog must outrun, and the trailing EV/EBITDA at its 92nd percentile offers little cushion if conversion disappoints. [11]

### Key unknowns
- Forward EV/EBITDA on a revised guidance basis is UNKNOWN — the trailing 22.9x cannot distinguish a temporarily elevated from a permanently high level because there is no forward basis and no revised guidance at the drawdown to read an adjusted figure from.
- The 5-year EV/EBITDA percentile is at its ceiling (92nd) but the P/E percentile is unbuildable: a stock split inside the window divides split-adjusted prices against as-filed older EPS by ~20x, so the trailing P/E range cannot be constructed — a neutral measurement gap, not a directional signal.
- Segment EBITDA is not disclosed — the filing segments revenue and segment operating income but not segment EBITDA, so Cloud vs Services EBITDA economics underlying the consolidated multiple cannot be separated; an expected disclosure that is absent.
- Whether LTM free cash flow is genuinely negative or positive turns entirely on basis: CIQ levered FCF is -$1,162.5M while CFO−capex is +$19,747M on the same sheet — self-funding reads MIXED and the human must pick the basis before quoting either.
- No covenant terms could be extracted — no CIK-scoped agreement exhibit was located, so covenant protections on $150,331M total debt are UNKNOWN; a missing expected disclosure to weigh as a risk, mitigated by AA+ rating and net-cash position.
- Peer set is HETEROGENEOUS (market caps span $6.0B–$3,943.4B, 654x; the name is $3,977.5B) — every peer multiple (TEV/EBITDA name 20.3 vs peer median 15.8; P/E name 17 vs 20.9) is a confidence-gated input, not a clean benchmark, and whether the P/E discount is EARNED (LT EPS growth 13% vs peer 21%) or RESIDUAL is for the human to judge, not computed here.
- The CIQ 22.9x EV/EBITDA does not reproduce either reported pairing (divides TEV by $168,309M vs reported LTM EBITDA $185,516M, -9.3%) — read CIQ's own denominator before comparing it with a multiple of reported EBITDA.
- Forward multiple ladder shows EV/EBITDA falling to 11.82x NTM and 4.63x by FY32 on consensus, but the estimate EBITDA basis adds back ~5.75x more D&A than the actual row, so trailing-vs-forward multiples are part-definitional and not directly comparable.

### Twin reference cases
- **Microsoft Corporation** — kept compounding
  - distinguished by: Mega-cap platform carrying a premium multiple that re-accelerated by pivoting a high-margin franchise into a surging enterprise-AI cloud business — the pattern the runway case leans on.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Amazon.com** — kept compounding
  - distinguished by: A dominant franchise that ran years of depressed free cash flow while building out capital-intensive infrastructure, where the market had to judge whether the spend was runway or value destruction.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **Meta Platforms** — re-rated to fair value
  - distinguished by: An advertising-led platform whose multiple compressed sharply when a capex super-cycle collided with softening near-term estimates, then recovered — the pattern a fully-priced read must weigh against a capex-driven free-cash-flow trough.
  - source: CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)
- **NVIDIA Corporation** — kept compounding (LLM-claimed — verify)
  - distinguished by: A silicon-and-platform supplier whose own-designed accelerators and an apparent supply-constrained demand backlog carried valuation to high absolute multiples that were later validated by delivered revenue.
  - source: [LLM-suggested, unverified]

## Catalyst calendar — what tests the thesis, and when

- **Early access to the Lyft app rolls out in Barcelona and Hamburg first; throughout October, the Lyft app will become a…** — ~2026-10 `[stated]` — a management-stated dated operating action — the thesis mechanism on a timetable; the following print reads its result [36]
- **Next results print** — ~2027-01-30 `[cadence-estimate]` — the next reported quarter against the committed trajectory [37]

_Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job._

## Valuation & own-history
- **Cross-sectional (vs peers — the edge):** EV/EBITDA 20.3x vs peer median 15.8x (+28%); P/E 17x vs peer median 20.9x (-19%) [24]
- **What the current price implies (at stated multiples)** — comparability: HETEROGENEOUS (see Peer comps gate)
  - _TEV as-of 2026-10-28 · multiples as-of 2026-11-01 · † at the name's own multiple the implied level is consensus by identity_
- **Price-implied levels (at each stated multiple)** — [38]  <!-- ds-table -->

|  | Multiple (× used) | Implied level |
|---|---|---|
| **name NTM TEV/EBITDA** | **11.82x** | **$326,081.4M EBITDA †** |
| peer-median NTM TEV/EBITDA | 10.63x | $362,585.4M EBITDA |
| peer-median LTM TEV/EBITDA | 15.8x | $243,941.9M EBITDA |
| **name NTM TEV/Rev** | **5.58x** | **$690,731.7M Revenue †** |
| peer-median NTM TEV/Rev | 3.55x | $1,085,713.4M Revenue |
| peer-median LTM TEV/Rev | 3.9x | $988,277.6M Revenue |

- **Consensus path anchors (EBITDA):** FY26E $227919.0M · FY27E $303791.2M (direct consensus EBITDA — CIQ Estimates→Trends latest snapshot)
- **Consensus path anchors (Revenue):** FY26E $499579.1M · FY27E $634498.6M (direct consensus Revenue — CIQ Estimates→Trends latest snapshot)
  - _⚠ multiple-pricing vintage differs from TEV as-of — re-pull comps (derived FY26 $263450.6M vs direct $227919.0M, residual 0.156 > 0.10)_

### The EV gap — our base case vs the street

_No gap is struck for this name: shares unavailable. The consensus side alone still routes to **three-ratio** at FY2026, so the form is known even though the comparison is not._

- **EV/EBITDA (adjusted, forward) · Adjusted EPS (earnings power) · Guidance at the drawdown (8-K 99.1) · Net debt / EBITDA [FWD-ADJ]:** _UNKNOWN_ — no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN
- **Own-history range position:** EV/EBITDA (TEV/LTM) 22.9x as-of 2026-09-30 — trailing range 10.9–25.8x (median 17.5x) over 38 closes → 92%ile → near-ceiling; P/LTM EPS 17.3x [23]

## Peer comps
- **Peer set (roster · caps · business)** — [39]  <!-- ds-table -->

|  | Mkt cap | Business |
|---|---|---|
| Meta Platforms | $1565.7B | engages in the development of products that enable people to connect and share with friends and family through mobile devices, personal computers (United States) |
| Amazon.com | $2746.2B | engages in the retail sale of consumer products, advertising, and subscriptions service through online and physical stores in North America and internationally. (United States) |
| Microsoft Corporation | $3943.4B | develops and supports a portfolio of technology solutions for individuals and businesses worldwide. (United States) |
| Reddit | $25.9B | operates a digital community in the United States and internationally. (United States) |
| Pinterest | $11.8B | operates as a visual search and discovery platform in the United States, Canada, Europe, and internationally. (United States) |
| Netflix | $254.6B | provides entertainment services worldwide. (United States) |
| Snap Inc. | $10.1B | operates as a technology company in North America, Europe, and internationally. (United States) |
| The Trade Desk | $6.0B | operates as a technology company in the United States and internationally. (United States) |
| DoorDash | $73.4B | operates a commerce platform that connects merchants, consumers, and dashers in the United States and internationally. (United States) |
| Match Group | $9.7B | provides digital technologies in the United States and internationally. (United States) |

_the name: $3977.5B_

- **Comparability (confidence gate):** market caps span $6.0B–$3943.4B (654x); the name is $3977.5B → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark. [26]
- **Forward multiples (name vs peer Low/Median/Mean/High · NTM)** — [40]  <!-- ds-table -->

|  | Name | Low | Median | Mean | High |
|---|---|---|---|---|---|
| NTM TEV/Rev | 6.5 | 1.62 | 3.55 | 4.2 | 9.64 |
| NTM TEV/EBITDA | 13.73 | 7.63 | 10.63 | 11.22 | 15.61 |
| NTM P/E | 23.52 | 8.24 | 17.93 | 18.04 | 27.38 |

_NM = a real state (negative base), not missing_

- **Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)** — [41]  <!-- ds-table -->

|  | Cap | TEV/EBITDA | TEV/Rev | P/E | EBITDA margin | Rev growth (1y) | Total debt/EBITDA | Net debt ($M) |
|---|---|---|---|---|---|---|---|---|
| **Alphabet Inc. · the name** | **$3,977.5B** | **20.3** | **8.2** | **17.0** | **39%** | **22%** | **0.7** | **123,181 (net cash)** |
| Microsoft Corporation | $3,943.4B | 18.1 | 11.4 | 27.7 | 59% | 18% | 0.3 | 7,309 (net cash) |
| Amazon.com | $2,746.2B | 15.4 | 3.7 | 20.5 | 22% | 16% | 1.3 | 128,647 |
| Meta Platforms | $1,565.7B | 13.2 | 6.6 | 20.9 | 48% | 28% | 1.0 | 32,393 |
| Netflix | $254.6B | 15.8 | 5.3 | 17.9 | 32% | 15% | 1.0 | 9,307 |
| DoorDash | $73.4B | 36.2 | 4.2 | 70.4 | 11% | 35% | 1.7 | 2,684 (net cash) |
| Reddit | $25.9B | 28.5 | 8.3 | 31.4 | 29% | 67% | 0.0 | 2,766 (net cash) |
| Pinterest | $11.8B | 32.7 | 2.6 | 53.5 | 7% | 17% | 3.3 | 78 (net cash) |
| Snap Inc. | $10.1B | NM | 1.8 | NM | -2% | 13% | NM | 1,566 |
| Match Group | $9.7B | 10.5 | 3.6 | 14.9 | 34% | 2% | 3.0 | 3,084 |
| The Trade Desk | $6.0B | 6.2 | 1.7 | 15.0 | 23% | 12% | 0.5 | 1,051 (net cash) |
| Peer median (peers) | $49.7B | 15.8 | 4.0 | 20.9 | 26% | 16% | 1.0 | 744 |


## Operating trajectory
- **Trajectory ($M · % — per period)** — [31]  <!-- ds-table -->

|  | Dec-2017 (R) | Dec-2018 (R) | Dec-2019 (R) | Dec-2020 | Dec-2021 | Dec-2022 | Dec-2023 (R) | Dec-2024 (R) | Dec-2025 | Sep-2026 (LTM) |
|---|---|---|---|---|---|---|---|---|---|---|
| Gross margin | 59% | 56% | 56% | 54% | 57% | 55% | 57% | 58% | 60% | 61% |

_Revenue YoY (latest same-quarter): +24.7% (Q3 Sep-30-2026 vs Q3 Sep-30-2025). R reclassified; margin % can fall while absolute EBITDA RISES — read them together; per-period values, never YoY'd across a basis_

- **Share-count trend:** flat (trailing ~1.7y): 12,211,000,000 (2024-12-31) → 12,294,000,000 (2026-09-30), +0.7% [42]
- **Non-operating earnings:** 4 of the trailing four quarters carry a material block from BELOW the operating line — 2025-09-30 +$12,759M (29% of pre-tax · 12% of revenue) · 2026-03-31 +$37,716M (49% of pre-tax · 34% of revenue) · 2026-06-30 +$97,983M (71% of pre-tax · 82% of revenue) · 2026-09-30 −$8,221M (25% of pre-tax · 6% of revenue) — netting +$140,237M across the four. A trailing EPS or P/E spanning them is not an operating anchor, and the LTM figure carries the SUM, not the largest of them. [14]
- **Return ratios — per fiscal period** — [43]  <!-- ds-table -->

|  | FY17 | FY18 | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | LTM |
|---|---|---|---|---|---|---|---|---|---|---|
| RoE % | 8.7% | 18.6% | 18.1% | 19.0% | 32.1% | 23.6% | 27.4% | 32.9% | 35.7% | 44.3% |
| RoCE % | 12.1% | 12.1% | 11.3% | 11.0% | 18.5% | 16.5% | 17.6% | 21.0% | 19.3% | 15.6% |
| RoA % | 9.9% | 9.5% | 8.8% | 8.7% | 14.5% | 12.9% | 13.7% | 16.5% | 15.4% | 12.7% |
| Total debt/equity | 0.03x | 0.02x | 0.08x | 0.13x | 0.11x | 0.12x | 0.11x | 0.09x | 0.16x | 0.22x |
| Current ratio | 5.14x | 3.92x | 3.37x | 3.07x | 2.93x | 2.38x | 2.10x | 1.84x | 2.01x | 2.79x |
| Dividend/sh | none | none | none | none | none | none | none | none | 0.38 | 0.05 |



## The street — estimates & guidance
_export date unverified (data ≥ 2026-11-01)_
- **Horizon read (FQ — next-2Q revision breadth)** — [44]:
  - EPS (GAAP) FQ4 2026: 1m 11↑/24↓, 2m 12↑/22↓, 3m 12↑/22↓
  - EPS (GAAP) FQ1 2027: 1m 5↑/10↓, 2m 6↑/10↓, 3m 7↑/10↓
  - EPS Normalized FQ4 2026: 1m 3↑/8↓, 2m 3↑/8↓, 3m 3↑/8↓
  - EPS Normalized FQ1 2027: 1m 1↑/3↓, 2m 1↑/3↓, 3m 2↑/3↓
  - Revenue FQ4 2026: 1m 18↑/11↓, 2m 20↑/8↓, 3m 21↑/7↓
  - Revenue FQ1 2027: 1m 9↑/4↓, 2m 11↑/3↓, 3m 12↑/3↓
  - EBITDA FQ4 2026: 1m 8↑/15↓, 2m 9↑/14↓, 3m 10↑/13↓
  - EBITDA FQ1 2027: 1m 3↑/4↓, 2m 4↑/4↓, 3m 4↑/4↓
  - EBIT FQ4 2026: 1m 9↑/19↓, 2m 10↑/19↓, 3m 10↑/19↓
  - EBIT FQ1 2027: 1m 4↑/5↓, 2m 5↑/5↓, 3m 5↑/5↓
  - _+8 non-headline metric rows in JSON_
- **Acceleration read (monthly consensus path):** FY 2026 EPS (GAAP): 11.0 (12m) → 11.2 (9m) → 14.0 (6m) → 20.6 (3m) → 20.6 (2m) → 20.6 (1m) → 19.7 (latest); net +79% (12m→latest) | FY 2026 EPS Normalized: 11.0 (12m) → 11.2 (9m) → 11.8 (6m) → 11.7 (3m) → 11.7 (2m) → 11.8 (1m) → 14.1 (latest); net +28% (12m→latest) | FY 2026 Revenue: 451,565.9 (12m) → 457,525.0 (9m) → 485,288.5 (6m) → 497,686.1 (3m) → 498,042.6 (2m) → 498,627.6 (1m) → 499,579.1 (latest); net +11% (12m→latest) | FY 2026 EBITDA: 211,488.8 (12m) → 212,377.8 (9m) → 226,219.5 (6m) → 231,454.7 (3m) → 231,597.7 (2m) → 233,391.2 (1m) → 227,919.0 (latest); net +8% (12m→latest) | FY 2026 EBIT: 152,951.9 (12m) → 155,425.0 (9m) → 167,908.6 (6m) → 171,315.2 (3m) → 171,577.8 (2m) → 171,656.1 (1m) → 168,487.3 (latest); net +10% (12m→latest) | FY 2026 Interest Expense: -3,600.0 (12m) → -3,600.0 (9m) → -3,195.0 (6m) → -4,441.3 (3m) → -4,441.3 (2m) → -4,441.3 (1m) → -4,110.0 (latest); worsening (magnitude away from zero) (12m→latest) | FY 2026 EBT (GAAP): 158,627.2 (12m) → 161,643.4 (9m) → 212,094.2 (6m) → 310,904.0 (3m) → 311,032.0 (2m) → 311,294.7 (1m) → 295,969.2 (latest); net +87% (12m→latest) | FY 2026 Net Income (Excl. Excep): 132,920.6 (12m) → 135,854.2 (9m) → 138,590.3 (6m) → 153,288.2 (3m) → 153,288.2 (2m) → 181,663.8 (1m) → 244,694.3 (latest); net +84% (12m→latest) | FY 2026 Net Income (GAAP): 132,633.5 (12m) → 135,737.3 (9m) → 172,058.2 (6m) → 253,597.4 (3m) → 253,689.5 (2m) → 254,161.0 (1m) → 240,071.1 (latest); net +81% (12m→latest)  [data ≥ 2026-11-01 · export date unverified] [45]
- **Cross-name anchor (NTM forward-multiple ladder)** — [46]:
  - NTM: TEV/REV 5.58 · TEV/EBITDA 11.82 · TEV/EBIT 16.57 · Price/Earnings 20.30 · PEG 1.56 · P/BV –
  - FY 2026: TEV/REV 6.67 · TEV/EBITDA 14.63 · TEV/EBIT 19.79 · Price/Earnings 14.20 · PEG 1.09 · P/BV 4.87
  - FY 2027: TEV/REV 5.26 · TEV/EBITDA 11.02 · TEV/EBIT 15.37 · Price/Earnings 18.90 · PEG 1.45 · P/BV 3.78
  - FY 2028: TEV/REV 4.33 · TEV/EBITDA 8.51 · TEV/EBIT 12.38 · Price/Earnings 15.38 · PEG 1.18 · P/BV 3.05
  - _+4 later fiscal years in JSON_
- **Current guide (latest results filing):** _UNKNOWN_ — no guide in any of the 4 parsed release(s)
- **Guidance bridge (latest guide + sign-aware delivery track-record)** — [47]  <!-- ds-table -->

|  | Latest guide | For | Dated | Age | Record (met/resolved) | Most recent |
|---|---|---|---|---|---|---|
| DPS | 0.22 | FQ4 2026 | 2026-10-28 | fresh | actual ≥ floor 1/1 · 9 at-guide (±0.5% of a point, not adjudicated) | FQ3 2026 AT GUIDE (±0.5% of a point) |
| Capital Expenditure | '(195,000.00) - (205,000.00)' | FY 2026 | 2026-10-28 | fresh | spend ≤ ceiling 1/1 | FY 2025 MET |
| EPS Normalized | none current (last: 0.18) | FY 2006 | 2005-10-20 | 7666d (stale) | actual ≥ floor 1/1 | FY 2006 MET |
| EPS (GAAP) | none current (last: 0.18) | FY 2006 | 2005-10-20 | 7666d (stale) | actual ≥ floor 1/1 | FY 2006 MET |
| Revenue | none current (last: 11,800.0) | FY 2007 | 2006-03-20 | 7515d (stale) | actual ≥ floor 3/3 | FY 2007 MET |

_CIQ states every guide as a LEVEL in the metric's own units. Where management guided a RATE, the level is CIQ's arithmetic on its own base, not a figure the company published — check the release before quoting one as guidance._

- **Consensus stats (target + ratings):** Target price: mean $404.54, median $400.00, high/low 500.00/300.00, N 53/53; Ratings: Buy 43, Outperform 10, Hold 5, Underperform 0, Sell 0, No Opinion 2  [data ≥ 2026-11-01 · export date unverified] [27]
- **Revision-event log (250 events · 23 broker-days)** — [48]  <!-- ds-table -->

|  | Broker | Revisions | ↑ | ↓ | Init | Largest revision | Prior | Current | Δ |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2026-11-01 | Loop Capital Markets | 1 | 1 | — | — | EBT (GAAP) FY 2026 | 164124.0 | 305811.0 | +141687.0 |
| 2026-11-01 | Mirae Asset Securities Co., Ltd. | 1 | 1 | — | — | EBT (GAAP) FY 2026 | 189319.0 | 306288.0 | +116969.0 |
| 2026-11-01 | Phillip Securities Pte Ltd | 6 | 3 | 3 | — | Revenue FY 2026 | 493435.0 | 500616.0 | +7181.0 |
| 2026-11-01 | broker undisclosed | 18 | 1 | 17 | — | EBITDA FQ4 2026 | 56532.0 | 56028.0 | −504.0 |
| 2026-10-30 | Morningstar Inc. | 6 | 3 | 3 | — | EBITDA FY 2026 | 205243.1 | 205243.0 | −0.13 |
| 2026-10-29 | China International Capital Corporation Limited | 19 | 3 | 15 | 1 | EBITDA FY 2026 | 198697.0 | 191194.0 | −7503.0 |

_+17 more broker-days in JSON_

- **Surprise history (annual beat/miss):** GAAP-EPS surprise: FY2004 +33%, FY2005 +0%, FY2006 +9%, FY2007 -3%, FY2008 -20%, FY2009 +2%, FY2010 +3%, FY2011 -5%, FY2012 -1%, FY2013 -2%, FY2014 +6%, FY2015 -1%, FY2016 -1%, FY2017 -44%, FY2018 +5%, FY2019 +6%, FY2020 +13%, FY2021 +4%, FY2022 -4%, FY2023 +1%, FY2024 +0%, FY2025 +2%; Revenue surprise: FY2004 +2%, FY2005 +0%, FY2006 +1%, FY2007 +1%, FY2008 +0%, FY2009 +0%, FY2010 +1%, FY2011 -1%, FY2012 -4%, FY2013 +1%, FY2014 -1%, FY2015 +1%, FY2016 +2%, FY2017 +1%, FY2018 +0%, FY2019 -1%, FY2020 +2%, FY2021 +1%, FY2022 -0%, FY2023 +1%, FY2024 -0%, FY2025 +1% (GAAP-EPS basis; +beat / −miss) [49]

## Leverage & survival
- **Net debt / EBITDA [NET]:** -0.6x [9]
- **Total debt / EBITDA vs peers:** name 0.7x vs peer median 1.0x (comps TOTAL-debt/EBITDA basis) [50]
- **Net debt / OCF:** -0.6x [51]
- **Interest coverage:** 60.3x [52]
- **Self-funding:** self-funding: MIXED — latest-Q OCF > 0, LTM FCF < 0 (both must be positive to self-fund) [53]
- **Credit health — relative to each peer group** — [54]  <!-- ds-table -->

|  | Industry (21) | Comps (11) |
|---|---:|---:|
| Overall | 1 | 1 |
| Operational | 1 | 2 |
| Solvency | 1 | 1 |
| Liquidity | 1 | 1 |

_industry = 21 Interactive Media and Services companies (GICS industry), the primary panel; comps = the 11 companies of the CIQ comps template · S&P-MI relative score: 1 = top … 4 = bottom WITHIN each peer group — a rank among those companies, not an absolute measure · the two groups rank it differently on Operational · S&P issuer rating AA+ · industry panel reflects financials updated through 2026-10-22 — the export stamps no date of its own_


- **FCF sign:** positive [10]
- **Free cash flow ($M):** -1162.5 — basis: CIQ 'Levered Free Cash Flow', NOT CFO − capex — and the two carry OPPOSITE SIGNS: on the same sheet and period [LTM 12 months Sep-30-2026], CFO $179,551.0M − capex $159,804.0M = $19,747.0M. One says the business generated cash this period and the other says it consumed it; the basis decides which, so name it before quoting either. [13]
- **Debt schedule vintage:** the debt schedule is 253d old (source filed 2026-02-05); no Item 1.02 (termination of a material agreement) has been filed since [55]
- **Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Feb-05-2026** — [56]  <!-- ds-table -->

|  | Type | Principal | Coupon | Floating | Maturity | Sec | Conv | Cur |
|---|---|---:|---|---|---|---|---|---|
| 16 US Dollar Notes | Bonds and Notes | $2,000.0M | 2.000% | NA | 2026-08-15 | N | N | USD |
| Revolving Credit Facilities | Revolving Credit | – | NA | NA | 2026-04-01 | N | N | USD |

_17 undated / later aggregate line item(s) in the appendix panel_

- **Maturity wall** · vs the 2026-10-16 reference:
  - **matured (pre-reference): $2,000.0M + 1 with no principal stated** — resolution not in this data; verify each against its 8-K (NEVER assume repaid or defaulted):
    - 2026-04-01 (198d before ref): – Revolving Credit Facilities
    - 2026-08-15 (62d before ref): $2,000.0M 16 US Dollar Notes
  - due 2028: $500.0M
  - due 2029: $1,759.9M
  - due 2030: $750.0M + 1 with no principal stated
  - due 2033: $1,759.9M
  - due 2035: $1,250.0M
  - due 2037: $1,466.6M
  - due 2045: $1,466.6M
  - due 2054: $1,466.6M
  - due 2055: $1,500.0M
  - due 2065: $1,500.0M
  - undated (floor — no panel maturity): $52,084.8M + 1 with no principal stated — 20 US Dollar Notes $9,000.0M, Commercial Paper Program –, Euro Denominated Fixed Rate… $7,631.8M, Finance Lease Liabilities $2,500.0M, Operating Lease Liabilities $15,953.0M, US Dollar Denominated Fixed Rate… $17,000.0M
  - _no principal stated — the CIQ panel gives no amount (–), and no total in this wall counts it as $0: Commercial Paper Program (Commercial Paper), Revolving Credit Facilities (Revolving Credit), Revolving Credit Facilities (Revolving Credit). On a revolving-credit or commercial-paper line no amount can mean an undrawn facility; the panel does not say which._
  - _reconciliation: itemized $67,504.4M + 3 with no principal stated (panel A 2025 filed Feb-05-2026) vs the aggregates below — the gap is unitemized / newer term loans, or principal the panel does not state; read the term-loan movement in the aggregates line, which names the period columns it spans._
- **Capital-structure aggregates:** senior bonds 126,791.8; leases 24,213.0; total principal 152,225.8; total debt 150,331.0 (3 months Q3 Sep-30-2026) ($M) [57]
- **Maturity resolution (8-K verbatim):** _UNKNOWN_ — (P3) 8-K body at 8-K 0001652044-26-000031 (2026-04-02) states no maturity-resolution event

### Filing cross-checks — going concern · leverage basis

- **Going-concern language:** none in latest 10-Q — checked, absent [58]
- **EBITDA-basis triangulation (each leverage basis-labeled):** [59]
  - net debt / EBITDA (CIQ's EBITDA, vendor-normalised): -0.6x
  - total debt / EBITDA (CIQ comps EBITDA, vendor-normalised): 0.7x
  - net debt / company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN
  - covenant basis: no structured source for this decision vintage

## ⚠ Analyst caveats — verify before the verdict

_10 to verify._

- NOT A CURRENT SCREEN CANDIDATE — assembled because the name carries an operator follow decision — Alphabet Class A, HELD — a $50,000 / 5.0% NAV starter entered 2026-08-14 at ~$345 under an external IC memo, recorded here so the machinery can see a live position it was previously blind to. Followed under the QUALITY book: the binding question is duration — whether Search and Cloud economics outlast what a ~26x normalized NTM multiple already pays for — not whether a de-rating is overdone, which is the overshoot twin's question and the wrong one here. The $300M-$10B band answers where the fund HUNTS, not what it may hold or follow, and this name is covered deliberately from outside it. Class A specifically: the memo, the $345.90 verified close and the frozen legs are all Class A, and GOOG (Class C) is a distinct security. The cap band decides where the fund HUNTS, not what it may hold or follow, so absence from it is not a rejection — read the verdict, not the absence: no screen run on file has evaluated it.
- Untraceable figure -0.6 (a bull point) — cited to structured data that does not contain it; verify the source before relying on it: 'The balance sheet carries net cash: net-debt/EBITDA -0.6x, interest coverage 60.3x and an S&P AA+ issuer rating, so the heavy AI capex is self-funded from a fortress position rather than requiring external leverage.'
- Untraceable figure 60.3 (a bull point) — cited to structured data that does not contain it; verify the source before relying on it: 'The balance sheet carries net cash: net-debt/EBITDA -0.6x, interest coverage 60.3x and an S&P AA+ issuer rating, so the heavy AI capex is self-funded from a fortress position rather than requiring external leverage.'
- Untraceable figure 22.9 (a bear point) — cited to structured data that does not contain it; verify the source before relying on it: 'EV/EBITDA (TEV/LTM) sits at 22.9x — its own 92nd percentile over 38 quarters (range 10.9–25.8x, median 17.5x) — so on its own trailing history the quality is priced near the ceiling, the thing a fully-priced read must beat; this is trailing-only with no forward basis to distinguish a temporarily depressed from a permanently elevated level.'
- Untraceable figure 10.9 (a bear point) — cited to structured data that does not contain it; verify the source before relying on it: 'EV/EBITDA (TEV/LTM) sits at 22.9x — its own 92nd percentile over 38 quarters (range 10.9–25.8x, median 17.5x) — so on its own trailing history the quality is priced near the ceiling, the thing a fully-priced read must beat; this is trailing-only with no forward basis to distinguish a temporarily depressed from a permanently elevated level.'
- Untraceable figure 25.8 (a bear point) — cited to structured data that does not contain it; verify the source before relying on it: 'EV/EBITDA (TEV/LTM) sits at 22.9x — its own 92nd percentile over 38 quarters (range 10.9–25.8x, median 17.5x) — so on its own trailing history the quality is priced near the ceiling, the thing a fully-priced read must beat; this is trailing-only with no forward basis to distinguish a temporarily depressed from a permanently elevated level.'
- Untraceable figure 17.5 (a bear point) — cited to structured data that does not contain it; verify the source before relying on it: 'EV/EBITDA (TEV/LTM) sits at 22.9x — its own 92nd percentile over 38 quarters (range 10.9–25.8x, median 17.5x) — so on its own trailing history the quality is priced near the ceiling, the thing a fully-priced read must beat; this is trailing-only with no forward basis to distinguish a temporarily depressed from a permanently elevated level.'
- Untraceable figure 17.3 (a bear point) — cited to structured data that does not contain it; verify the source before relying on it: 'Trailing GAAP earnings are not an operating anchor: four consecutive quarters each carry a material below-the-operating-line block netting +$140,237M, including +$97,983M in 2026-06-30 (82% of revenue) — the LTM P/E of 17.3x and the LTM net income of $235,694M embed non-operating gains, not operating power.'
- Untraceable figure 235694 (a bear point) — cited to structured data that does not contain it; verify the source before relying on it: 'Trailing GAAP earnings are not an operating anchor: four consecutive quarters each carry a material below-the-operating-line block netting +$140,237M, including +$97,983M in 2026-06-30 (82% of revenue) — the LTM P/E of 17.3x and the LTM net income of $235,694M embed non-operating gains, not operating power.'
- synthesis draws DISAGREED — 5 draw(s) of 5 gave {'mixed': 4, 'strongly-bullish': 1}; the machine proposal is withheld and the kept read is the first draw carrying the modal label (a tally of this build, never a rate)

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


## Financial statements (actuals + consensus estimates) — export date unverified (data ≥ 2026-11-01)
### Annual — every exported fiscal year + LTM + consensus
- **Annual financials ($M; E = consensus)** — [12]  <!-- ds-table -->

|  | FY17 (R) | FY18 (R) | FY19 (R) | FY20 | FY21 | FY22 | FY23 (R) | FY24 (R) | FY25 | LTM | FY26E | FY27E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 110,855 | 136,819 | 161,857 | 182,527 | 257,637 | 282,836 | 307,394 | 350,018 | 402,836 | 471,098 | 499,579 | 634,499 |
| Revenue growth | — | +23% | +18% | — (basis) | +41% | +10% | — (basis) | +14% | — (basis) | — (basis) | +24% (vs FY25) | +27% |
| EBITDA ($M) | 35,813 | 41,624 | 47,579 | 54,903 | 88,987 | 88,317 | 96,239 | 127,701 | 150,175 | 185,516 | 227,919 | 303,791 |
| EBITDA margin | 32% | 30% | 29% | 30% | 35% | 31% | 31% | 36% | 37% | 39% | 46% | 48% |
| EBIT ($M) | 28,914 | 32,595 | 35,928 | 41,224 | 78,714 | 74,842 | 84,293 | 112,390 | 129,039 | 156,976 | 168,487 | 216,958 |
| Net income ($M) | 12,662 | 30,736 | 34,343 | 40,269 | 76,033 | 59,972 | 73,795 | 100,118 | 132,170 | 235,694 | 240,071 | 186,433 |
| EPS (GAAP, dil.) | 0.90 | 2.19 | 2.46 | 2.93 | 5.61 | 4.56 | 5.80 | 8.04 | 10.80 | 19.15 | 19.71 | 14.81 |
| EPS (Normalized) | 1.34 | 1.49 | 1.71 | 1.90 | 3.62 | 3.65 | 4.25 | 5.88 | 6.86 | 8.05 | 14.14 | 15.19 |
| Gain (Loss) On Sale Of Invest. ($M) | -193 | 6,530 | 3,188 | 6,317 | 12,270 | -5,519 | -823 | 2,671 | 24,620 | 129,109 | — | — |
| Legal Settlements ($M) | -2,736 | -5,071 | -1,697 | — | — | — | — | — | — | — | — | — |
| CFO ($M) | 37,091 | 47,971 | 54,520 | 65,124 | 91,652 | 91,495 | 101,746 | 125,299 | 164,713 | 179,551 | 182,588 | 270,948 |
| Capex ($M) | -13,184 | -25,139 | -23,548 | -22,281 | -24,640 | -31,485 | -32,251 | -52,535 | -91,447 | -159,804 | -201,254 | -318,716 |
| FCF (levered, CIQ) | 23,683 | 20,529 | 25,116 | 35,504 | 47,009 | 49,939 | 56,280 | 53,158 | 38,088 | -1,162 | — | — |
| D&A ($M) | 6,899 | 9,029 | 11,651 | 13,679 | 10,273 | 13,475 | 11,946 | 15,311 | 21,136 | 28,540 | — | — |
| FCF (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | -17,946 | -41,807 |
| D&A (consensus basis) ($M) | — | — | — | — | — | — | — | — | — | — | 31,615 | 50,918 |

_E = consensus (Estimates→Trends 'Current'), as-of ≥2026-11-01; (R) = Reclassified basis · FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex_


> **EBITDA basis — the actual and estimate rows differ.** the estimate columns imply 73,132 of D&A against 12,710 in the actuals (5.75x) — the consensus EBITDA row adds back MORE than depreciation, so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth across the boundary as part definitional; do not compare a trailing multiple struck off the actual row with a forward multiple struck off the estimate row.

### Quarterly — every exported quarter
- **Quarterly financials** — [60]  <!-- ds-table -->

|  | Q1-17 | Q2-17 | Q3-17 | Q4-17 | Q1-18 (R) | Q2-18 (R) | Q3-18 (R) | Q4-18 (R) | Q1-19 | Q2-19 | Q3-19 | Q4-19 | Q1-20 | Q2-20 | Q3-20 | Q4-20 | Q1-21 | Q2-21 | Q3-21 | Q4-21 | Q1-22 | Q2-22 | Q3-22 | Q4-22 | Q1-23 (R) | Q2-23 (R) | Q3-23 (R) | Q4-23 (R) | Q1-24 (R) | Q2-24 | Q3-24 | Q4-24 (R) | Q1-25 | Q2-25 | Q3-25 | Q4-25 | Q1-26 | Q2-26 | Q3-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue ($M) | 24,750 | 26,010 | 27,772 | 32,323 | 31,146 | 32,657 | 33,740 | 39,276 | 36,339 | 38,944 | 40,499 | 46,075 | 41,159 | 38,297 | 46,173 | 56,898 | 55,314 | 61,880 | 65,118 | 75,325 | 68,011 | 69,685 | 69,092 | 76,048 | 69,787 | 74,604 | 76,693 | 86,310 | 80,539 | 84,742 | 88,268 | 96,469 | 90,234 | 96,428 | 102,346 | 113,829 | 109,896 | 119,796 | 127,577 |
| Gross margin | 60% | 60% | 60% | 56% | 57% | 57% | 58% | 54% | 56% | 56% | 57% | 54% | 54% | 52% | 54% | 54% | 56% | 58% | 58% | 56% | 56% | 57% | 55% | 54% | 56% | 57% | 57% | 56% | 58% | 58% | 59% | 58% | 60% | 60% | 60% | 60% | 62% | 62% | 60% |
| EBITDA ($M) | 8,061 | 8,492 | 9,537 | 9,691 | 9,619 | 10,228 | 10,981 | 10,796 | 10,918 | 12,015 | 12,651 | 12,549 | 11,080 | 9,755 | 14,691 | 19,377 | 19,179 | 22,306 | 24,335 | 25,324 | 23,876 | 23,352 | 21,181 | 19,908 | 20,050 | 24,662 | 24,514 | 27,013 | 28,885 | 31,133 | 32,506 | 35,177 | 35,215 | 36,393 | 36,968 | 41,974 | 46,356 | 48,241 | 49,320 |
| EBITDA margin | 33% | 33% | 34% | 30% | 31% | 31% | 33% | 27% | 30% | 31% | 31% | 27% | 27% | 25% | 32% | 34% | 35% | 36% | 37% | 34% | 35% | 34% | 31% | 26% | 29% | 33% | 32% | 31% | 36% | 37% | 37% | 36% | 39% | 38% | 36% | 37% | 42% | 40% | 39% |
| Revenue QoQ | — | +5% | +7% | +16% | — (basis) | +5% | +3% | +16% | — (basis) | +7% | +4% | +14% | -11% | -7% | +21% | +23% | -3% | +12% | +5% | +16% | -10% | +2% | -1% | +10% | — (basis) | +7% | +3% | +13% | -7% | — (basis) | +4% | — (basis) | — (basis) | +7% | +6% | +11% | -3% | +9% | +6% |
| Revenue YoY | — | — | — | — | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | — (basis) | +13% | -2% | +14% | +23% | +34% | +62% | +41% | +32% | +23% | +13% | +6% | +1% | — (basis) | — (basis) | — (basis) | — (basis) | +15% | — (basis) | — (basis) | +12% | — (basis) | +14% | +16% | — (basis) | +22% | +24% | +25% |

_QoQ/YoY same-basis only; (R) = Reclassified_

### Balance-sheet posture
- **Posture:** as of Q3-26 ($M): cash & ST inv 265,098; total debt 150,331; net debt -114,767; equity 659,526; net working capital 240,164; net-debt/EBITDA → see the Leverage & survival block (not recomputed) [61]
- **Coherence — BS vs implied-valuation bridge:** CAVEAT — the two CIQ sources DISAGREE: cash BS $265,098M vs bridge $265,098M; debt BS $150,331M vs bridge $141,917M; verify which the verdict should use — neither is silently preferred. [62]


### Capital structure & debt terms — instruments · pointers · covenants
- **Capital structure — full instrument panel A 2025 filed Feb-05-2026** — [56]  <!-- ds-table -->

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
| Finance Lease Liabilities | Capital Lease | $2,500.0M | 4.000% | NA | undated | Y | N | USD |
| Floating-rate Notes Due in 2028 | Bonds and Notes | $500.0M | NA | SOFR + 0.520% | 2028-11-15 | N | N | USD |
| Operating Lease Liabilities | Capital Lease | $15,953.0M | 4.000% | NA | undated | Y | N | USD |
| Revolving Credit Facilities | Revolving Credit | – | NA | NA | 2026-04-01 | N | N | USD |
| Revolving Credit Facilities | Revolving Credit | – | NA | NA | 2030-04-01 | N | N | USD |
| US Dollar Denominated Fixed Rate Senior Unsecured Notes | Bonds and Notes | $17,000.0M | 4.920% | NA | undated | N | N | USD |

- **8-Ks at instrument maturities:** 8-K at maturity 2026-04-01: filed 2026-04-02 [0001652044-26-000031] 5.02 Departure/Election of Directors or Certain Officers — read for resolution; 8-K at maturity 2026-04-01: filed 2026-04-10 [0001652044-26-000034] 5.02 Departure/Election of Directors or Certain Officers — read for resolution; 8-K at maturity 2026-08-15: filed 2026-08-10 [0001193125-26-342390] 8.01 Other Events, 9.01 Financial Statements and Exhibits — read for resolution [63]
- **Covenant exhibit pointers:** _UNKNOWN_ — no CIK-scoped agreement exhibit located across the filing history
- **Covenant terms (from the filed agreement):** COVENANT DIGEST — extraction failed: no agreement exhibit was located to extract from — the gap is in the pointer search, not in extraction (terms UNKNOWN, not pending). [64]

### Implied equity at peer multiples
> **Comparability gate:** comparability: HETEROGENEOUS (see Peer comps gate)
> _Reference only — the human judges earned vs residual (not a machine upside); the full Low/Mean/High and all bases are in the JSON._
- **Name market cap ($M) — the ADJACENT fact to compare against:** 3977463.7 [65]
- **Bridge (TEV → equity):** TEV→equity bridge: + cash $265,098.00M, − total debt $141,917.00M [66]
- **Implied equity at peer-median ($M, CIQ)** — [67]  <!-- ds-table -->

|  | Implied equity (median) |
|---|---:|
| LTM EBITDA | 3,027,369.4 |
| NTM Revenue (Capital IQ) | 2,218,579.3 |
| NTM EBITDA (Capital IQ) | 3,104,440.0 |


### Management commentary
- **Earnings call (transcript pointer — read the file):** 2 earnings-call transcript(s) on file — read in full for management posture: Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf; Alphabet Inc., Q3 2026 Earnings Call, Oct 28, 2026.rtf (pointer only; the synthesis cites them, the machine does not curate an excerpt) [68]

### Ownership & positioning
- **Insider activity (Form 4):** Open-market buys 0 · sells 39 (4 insiders, $4.45M) — in the last 182 days · no purchase in the 3y scanned · last sale $0.03M, director, 2026-09-30 (~1mo ago) · largest sale $6.87M, director, 2024-12-10 (~22mo ago) · grants 464 · last filing 2026-10-15 · other filings 772 [69]
- **Short interest (FINRA):** Short interest (FINRA, settle 2026-10-15): 80.4M → 78.4M sh (-2.4%, falling) · 0.6% of shares out (EDGAR XBRL) · DTC 2.9d · recent: 2026-10-15 78.4M · 2026-09-30 80.4M · 2026-09-15 87.4M · 2026-08-31 77.7M [70]

### Assembly verification — filing vs panel
- **Wall coherence — filing ≤12m vs CIQ panel (same window):** wall coherence: UNKNOWN — filing states no ≤12m figure [71]
- **Guide verification — CIQ guide vs release:** revenue: CIQ 11800.0 vs release NO NUMERIC OUTLOOK → not cross-checked [72]

## Record & reproduce
- **Data window:** screened as of 2026-10-16 · assembled 2026-11-02 09:21 UTC
- **Extraction:** 2026-10-30.submissions-pages — a filings window that reaches past the submissions index's recent page (a heavy filer's newest ~1,000 filings) reads every older page it overlaps, through the SEC client, each checked against the document's listing of it and read again fresh when the two are of different vintages, or raises naming the page it could not read — never a short list read as complete (audit E1-D10)
- **Price store:** `b6-model-inputs-1e3db3 → mosaic-theory-ta` · reaching 2026-10-30
- **Panel age:** oldest panel 5d old — 2026-10-28 (valuation.implied_expectations.tev_as_of), against a 2026-11-02 build
- **Consensus age:** consensus 1d old (2026-11-01, valuation.implied_expectations.multiples_as_of) — within the ceiling
- **Synthesis:** model `claude-opus-4-8` — facts assembled mechanically; the synthesis frames, the analyst decides
- **Identifiers:** CIK `0001652044` · Nasdaq : GOOGL
- **Assembly log:** primary-source: 8-K 0001193125-26-342390 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 8-K 0001193125-26-234488 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 8-K 0001193125-26-216986 carries 8.01 but no EX-99.1 exhibit was found; primary-source: 4 EX-99.1 release(s) + 1 10-Q parsed (+9.6s fetch)
- **Re-run:** `python -m vinci dossier --ticker GOOGL` — regenerates every assembled fact from the same sources; committed values change only when the sources have.
- **Verdict record:** logged via the CLI to the append-only decision ledger (entry price frozen at the screen date); this document displays state, never records it.


# Sources

[1] `CIQ Financials→Segments (Revenues, latest annual column, Dec-31-2025)`
[2] `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column, Dec-31-2025)`
[3] `exchange · EOD · EDGAR shares · CIQ book value + cap`
[4] `EOD gap-down detector (screen events): none`
[5] `EOD GOOGL 180d to 2026-10-16`
[6] `EOD SPY 180d to 2026-10-16 (cap-band: $3977.5B @ 2026-10-16 → large (>$25B) → SPY)`
[7] `EOD GOOGL−SPY 180d to 2026-10-16 (assembly, cap-band)`
[8] `derived from 3 cohort names; face-validity`
[9] `CIQ Net Debt $-114,767M [Q3 Sep-30-2026] ÷ CIQ EBITDA $185,516M [LTM 12 months Sep-30-2026]`
[10] `EDGAR XBRL FCF sign (screen data-record): NetCashProvidedByUsedInOperatingActivities 2025-01-01..2025-12-31 (10-K 0001652044-26-000018, filed 2026-02-05) − PaymentsToAcquirePropertyPlantAndEquipment 2025-01-01..2025-12-31 (10-K 0001652044-26-000018, filed 2026-02-05)`
[11] `CIQ transcript: Alphabet Inc., Q3 2026 Earnings Call, Oct 28, 2026.rtf`
[12] `CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)`
[13] `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Sep-30-2026]`
[14] `EDGAR XBRL pre-tax − operating, quarters 2025-09-30..2026-09-30`
[15] `EDGAR companyfacts Goodwill (as at 2026-09-30)`
[16] `EDGAR companyfacts IntangibleAssetsNetExcludingGoodwill (as at 2026-09-30)`
[17] `EDGAR companyfacts PaymentsForRepurchaseOfCommonStock (2026-01-01→2026-09-30, 272d)`
[18] `EDGAR filing index (S-3/F-3 · 424B · S-1/F-1 · S-4 · S-8), window 2023-10-17→2026-10-16 · latest 0001193125-26-340264`
[19] `EDGAR filing index (SC 13D/G + SCHEDULE 13D/G — both vocabularies), window 2023-10-17→2026-10-16 · latest 0002100119-26-000161`
[20] `EDGAR XBRL ShareBasedCompensation (10-K, 2025-01-01→2025-12-31)`
[21] `EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from the CIQ comps grid`
[22] `EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · each row's window ends at that filer's own balance date`
[23] `CIQ Financials→Multiples (Close; last col = current, excluded from history)`
[24] `CIQ Comparable Analysis→Trading Multiples (name vs peer Median)`
[25] `price ÷ CIQ consensus EPS, per estimate column of the Financials annual summary`
[26] `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
[27] `CIQ Estimates→Consensus (target stats) + Trends Non-Periodic (ratings)`
[28] `EDGAR 10-K 0001652044-26-000018 XBRL instance goog-20251231_htm.xml — us-gaap:OperatingIncomeLoss on the segment contexts, fiscal year ending 2025-12-31`
[29] `CIQ Customers&Suppliers Alphabet Inc NasdaqGS GOOGL Customers.rtf`
[30] `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
[31] `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
[32] `CIQ Comparable Analysis→Credit Health Panel · as-of 2026-10-28`
[33] `CIQ Financials→Ratios [LTM 12 months Sep-30-2026]`
[34] `CIQ Estimates→Revisions (Last-Month breadth, FY)`
[35] `CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 38 quarters spanning 2017-03-31..2026-06-30 (9.2y) (partial last column excluded from the distribution)`
[36] `CIQ Key Developments: Alphabet Inc NasdaqGS GOOGL Key Developments.rtf · Sep-30-2026`
[37] `cadence: EDGAR submissions (median 94d gap over 13 results 8-Ks; last print 2026-10-28)`
[38] `TEV = mcap 3977463.7 + net debt -123181.0 (CIQ Comparable Analysis→Financial Data, Latest, data 2026-10-28, exported 2026-10-29) — simple-TEV basis`
[39] `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
[40] `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
[41] `CIQ Comparable Analysis→Financial Data + Operating Statistics (per-peer grid) · as-of 2026-10-28`
[42] `EDGAR XBRL shares, trailing 2024-12-31..2026-09-30`
[43] `CIQ Financials→Ratios (RoE / RoCE / RoA + leverage, multi-year columns)`
[44] `CIQ Estimates→Revisions (next-2-FQ breadth; 1m/2m/3m Upward/Downward)`
[45] `CIQ Estimates→Trends (current-FY consensus path; ragged, absent lookbacks n/a)`
[46] `CIQ Estimates→Multiples (forward-multiple ladder: NTM + FY26→FY33)`
[47] `CIQ Estimates→Guidance (latest guide + sign-aware delivery track-record) — CIQ states every guide as a LEVEL; where management guided a RATE, the level is CIQ's arithmetic, not the company's published figure`
[48] `CIQ Estimates→Recent Changes (250 broker revision events)  [data ≥ 2026-11-01 · export date unverified]`
[49] `CIQ Estimates→Surprise (annual)`
[50] `CIQ Comparable Analysis→Operating Statistics (LTM Total Debt/EBITDA) · as-of 2026-10-28`
[51] `CIQ Net Debt $-114,767M [Q3 Sep-30-2026] ÷ CIQ OCF $179,551M [LTM 12 months Sep-30-2026]`
[52] `CIQ Financials→Income Statement EBITDA ÷ Interest Expense [LTM 12 months Sep-30-2026]`
[53] `EDGAR OCF sign, quarter to 2026-09-30 + CIQ LTM FCF sign`
[54] `CIQ Credit Health Panel export→Summary (industry peers; export date not stamped) · CIQ Comparable Analysis→Credit Health Panel · as-of 2026-10-28`
[55] `CIQ Capital Structure Details — A 2025 filed Feb-05-2026`
[56] `CIQ Financials→Capital Structure Details (A 2025 filed Feb-05-2026)`
[57] `CIQ Financials→Capital Structure Summary`
[58] `10-Q 0001652044-26-000084`
[59] `CIQ leverage bases + release LTM adj-EBITDA/margins`
[60] `CIQ Financials→Income Statement (quarterly, full exported history)`
[61] `CIQ Financials→Balance Sheet (quarterly, Q3-26)`
[62] `CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation`
[63] `EDGAR 8-K submissions (±10d of instrument maturities)`
[64] `fenced Tier-2 digest (P1)`
[65] `CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-10-28`
[66] `CIQ Comparable Analysis→Implied Valuation (cash/debt bridge) · as-of 2026-10-28`
[67] `CIQ Comparable Analysis→Implied Valuation (= Implied Equity Value, basis × Low/Median/Mean/High) · as-of 2026-10-28`
[68] `CIQ transcript(s): Alphabet Inc., Q2 2026 Earnings Call, Jul 22, 2026.rtf; Alphabet Inc., Q3 2026 Earnings Call, Oct 28, 2026.rtf`
[69] `EDGAR Form 4 (latest 0001193125-26-423187; 497 filings in the 1095d scanned; 11 more filed by this company as a holder of another issuer's stock, not counted; counts over 182d)`
[70] `FINRA consolidated short interest (settle 2026-10-15); DTC = 78,436,901 short ÷ 26,762,109 screen 90d ADV`
[71] `10-Q maturity wall vs CIQ capital panel (same window)`
[72] `CIQ revenue guide vs release actual/outlook`