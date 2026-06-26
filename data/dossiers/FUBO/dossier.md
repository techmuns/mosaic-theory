# Dossier — FuboTV Inc. (FUBO)

_Finalist rank 1 · ref 2026-06-22 · assembled 2026-06-25 18:57 · LLM claude-opus-4-8_

> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is the human's, logged separately via the ledger with a frozen entry price.

## ⚠ Flags (human review)
- P/E may be distorted by non-recurring EPS — latest annual EPS -0.54 vs recent median -2.06; verify against normalized/forward EPS (CIQ)
- EPS shown is GAAP-based and understates earnings power; company-adjusted (non-GAAP) EPS is not in the CIQ workbook — it lives in the earnings-release/transcript reconciliation (currently UNAVAILABLE) — not a ceiling on earnings power.
- MISMATCH decisive.against: 'Survival capacity is explicitly flagged:…' asserts missing/UNKNOWN data yet cites a PRESENT field — move to key_unknowns, don't source-bind it
- DIRECTIONAL language 'recommendation' — human review (dossier frames, not concludes)
- FALSE-BALANCE? evidence_balance commits a strong lean but the body is near-symmetric (5 bull vs 8 bear) and the minority bull_points aren't qualified-as-outweighed — size the minority against the lean (rule 7), or it launders a one-sided case
- HETEROGENEOUS-BENCHMARK bear_point: 'On the one forward profitability multiple that exists, NTM TEV/EBITDA…' — leans on the peer set as a clean benchmark, but comparability flags it HETEROGENEOUS; confidence-gate every peer stat

## Mechanical layer (source-bound facts)

### Valuation
- **P/E:** 12.1x
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- **P/E percentile (5y):** 0th %ile
  - ↳ `EDGAR/EOD P/E pctile vs ~5y (screen data-record)`
- **EV/EBITDA (GAAP TEV/LTM):** _UNKNOWN_ — TEV/LTM EBITDA Close has no value
- **EV/EBITDA percentile (5y):** _UNKNOWN_ — TEV/LTM EBITDA Close <4 quarters (0) — no pctile
- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Adjusted EPS (earnings power):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Range position:** _UNKNOWN_ — TEV/LTM EBITDA Close has <4 quarters — no range position

### Quality / durability
- **FCF sign:** negative
  - ↳ `EDGAR XBRL FCF sign (screen data-record)`
- **Free cash flow ($M):** -131.2
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- **Margin trend:** gross margin: Oct-01-2022 0% → Sep-30-2023 0% → Sep-28-2024 0% → Sep-27-2025 0% → Mar-31-2026 (LTM) 4%; absolute revenue: Oct-01-2022 3,419 → Sep-30-2023 3,846 → Sep-28-2024 4,220 → Sep-27-2025 4,413 → Mar-31-2026 (LTM) 5,304  [R reclassified; margin % can fall while absolute EBITDA RISES — read them together]
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- **Net debt / EBITDA (GAAP):** _UNKNOWN_ — EBITDA<=0 or missing debt/cash
- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 revised guidance
- **Survival capacity (leverage + self-funding + wall):** net-debt/EBITDA UNKNOWN (EBITDA<=0 or missing debt/cash) — solvency risk | FCF-negative → burning cash; runway = cash ÷ burn (cash not derived — a risk) | nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- **Interest coverage:** _UNKNOWN_ — Income Statement missing EBITDA or Interest Expense row
- **Share-count trend:** diluting (trailing ~1.0y): 329,336,621 (2024-07-31) → 342,433,118 (2025-07-31), +4.0%
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2025-07-31`
- **Liquidity / covenant flags:** 2029 Convertible Notes (Bonds and Notes) 178 @ 7.500%; Disney Note (Bonds and Notes) 145 @ 4.200%; Operating Lease Liabilities (Capital Lease) 33 @ 6.800%; Other Notes (Bonds and Notes) 0 @ 2.250%
  - ↳ `CIQ Financials→Capital Structure Details`
- **Multi-year trajectory (compounder vs melting ice):** Revenue: Oct-01-2022 3,419 → Sep-30-2023 3,846 → Sep-28-2024 4,220 → Sep-27-2025 4,413 → Mar-31-2026 (LTM) 5,304; ROIC: Sep-30-2023 -11.2% → Sep-28-2024 -10.9% → Sep-27-2025 -10.7% → Mar-31-2026 (LTM) -3.3%  [R reclassified; per-period values, never YoY'd across a basis]
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`

### Concentration
- **Segments (revenue share):** [12 months Sep-27-2025] Streaming Business 4,413 (100%) of Total 4,413
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`
- **Segments (EBITDA share — where profit sits):** _UNKNOWN_ — Segments sheet has no 'EBITDA' section as expected
- **Customers:** CBS Corporation (Acquired) — fuboTV Inc. · Customer · src: Broadcasting; Denso Aircool Corporation — fuboTV Inc. · Customer · src: Automotive Parts and Equipment; International Family Entertainment, Inc. — fuboTV Inc. · Customer · src: Movies and Entertainment; NBCUniversal Media, LLC — fuboTV Inc. · Customer · src: Movies and Entertainment; ProBank Austin (Acquired) — fuboTV Inc. · Customer · src: Research and Consulting Services; TEGNA Inc. — fuboTV Inc. · Distributor · src: Broadcasting; Viacom Inc. (Acquired) — fuboTV Inc. · Customer · src: Movies and Entertainment; WideOpenWest, Inc. — fuboTV Inc. · Distributor · src: Cable and Satellite
  - ↳ `CIQ Customers&Suppliers FuboTV Inc NYSE FUBO Customers.rtf`
- **Geographic:** [12 months Sep-27-2025] United States 4,413 (100%) of Total 4,413
  - ↳ `CIQ Financials→Segments (Geographic Segment → Revenues, latest annual column)`

### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)
- **Peer set (roster · caps · business):** 10 peers — Roku $19.9B — operates a TV streaming platform in the United States (United States); Netflix $306.6B — provides entertainment services worldwide. The company (United States); Sirius XM Holdings Inc. $9.5B — operates as an audio entertainment company in North (United States); Taboola.com Ltd. $1.3B — operates an artificial intelligence-based algorithmic (United States); Match Group $8.2B — provides digital technologies in the United States and (United States); Reddit $31.9B — operates a digital community in the United States and (United States); People Incorporated $3.1B — operates as a media and internet company worldwide. (United States); Bilibili Inc. $6.6B — provides online entertainment services for the young (China); Paramount Skydance Corporation $10.9B — operates as a media and entertainment company (United States); Starz Entertainment Corp. $478M — provides subscription video programming services to (Canada) | the name: $256M
  - ↳ `CIQ Comparable Analysis→Financial Data + Business Description (roster + caps + business)`
- **Comparability (confidence gate):** market caps span $478M–$306.6B (642x); the name is $256M → HETEROGENEOUS — low comparability: the peer median is anchored by businesses of differing scale/model; scrutinise comparability before reading any peer stat as a clean benchmark.
  - ↳ `CIQ Comparable Analysis→Financial Data (market-cap dispersion) + Business Description`
- **Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM):** TEV/Rev: name 0.4 vs peers Low 0.7 / Median 1.9 / Mean 3.2 / High 11.8; TEV/EBITDA: name NM vs peers Low 7.5 / Median 10.6 / Mean 17.6 / High 44.9; P/E: name NM vs peers Low 11.9 / Median 23.7 / Mean 33.6 / High 101.3; NTM TEV/Rev: name 0.36 vs peers Low 0.62 / Median 2.07 / Mean 2.81 / High 8.42; NTM TEV/EBITDA: name 17.77 vs peers Low 5.4 / Median 8.19 / Mean 11.64 / High 24.65; NTM P/E: name NM vs peers Low 7.26 / Median 19.23 / Mean 21.13 / High 51.57  [LTM + NTM forward; NM = a real state (negative base), not missing]
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- **Fundamental deltas (earned-vs-residual inputs):** EBITDA margin name – vs peer-median 11%; rev growth name 22% vs peer-median 9%; EBITDA growth name – vs peer-median 18%; Debt/EBITDA name NM vs peer-median 3.2; LT EPS growth name – vs peer-median 17%; beta name 2.4 vs peer-median 1.4  [justified-vs-residual inputs: is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)? the human judges — not computed here]
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### Drawdown cause
- **Shape:** discrete gap-downs by 8-K item code — 2026-02-03 earnings (2.02); 2026-03-26 no 8-K matched; 2026-05-06 earnings (2.02)
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- **Gap-down dates:** 2026-02-03, 2026-03-26, 2026-05-06
  - ↳ `EOD gap-down detector (screen events)`
- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**
  - gap 2026-02-03 → 2026-02-03 [`0001493152-26-004826`](https://www.sec.gov/Archives/edgar/data/1484769/000149315226004826/form8-k.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On February 3, 2026, FuboTV Inc. announced its financial results for the quarter ended December 31, 2025 . The full text of the shareholder letter and press release issued in connection with the announcement are attached as Exhibits 99.1 and 99.2, respectively, to this Current Report on Form 8-K. The information in this
  - gap 2026-05-06 → 2026-05-06 [`0001493152-26-021406`](https://www.sec.gov/Archives/edgar/data/1484769/000149315226021406/form8-k.htm)
    - items: 2.02 Results of Operations and Financial Condition, 9.01 Financial Statements and Exhibits
    - 2.02 Results of Operations and Financial Condition: Results of Operations and Financial Condition. On May 6, 2026, FuboTV Inc. announced its financial results for the quarter ended March 31, 2026. The full text of the shareholder letter and press release issued in connection with the announcement are attached as Exhibits 99.1 and 99.2, respectively, to this Current Report on Form 8-K. The information in this
- **Revised guidance (catalyst 8-K Ex-99.1):** _UNKNOWN_ — no revised-outlook 99.1 exhibit parsed for 8-Ks ['0001493152-26-004826', '0001493152-26-021406']

### Idiosyncratic vs shared (G2-vs-market compensation)
- **Name 180d return:** -72.1%
  - ↳ `EOD FUBO 180d to 2026-06-22`
- **Market (IWM) 180d return:** 17.8%
  - ↳ `EOD IWM 180d to 2026-06-22`
- **Relative vs market:** -89.9%
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- **Cohort read:** _UNKNOWN_ — no graph cohort to compare — see rel_vs_market for the name-vs-market read
- **Graph cohort:** _UNKNOWN_ — FUBO not in graph_coverage.json — no exposed cross-section to compare

### Consensus context
- **EPS trend:** EPS (GAAP) FY 2026: 0↑/0↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revenue trend:** Revenue FY 2026: 0↑/1↓ last mo
  - ↳ `CIQ Estimates→Revisions (Last-Month breadth, FY)`
- **Revision history:** Target price: mean $17.00 / median $17.00; Recommendation: Buy (1.00) (CIQ score, 1=buy … 5=sell)
  - ↳ `CIQ Estimates→Consensus`
- **Surprise history (beat/miss):** _UNKNOWN_ — Surprise sheet has no fiscal-year header row

### Management commentary (transcript POINTER — read the file; not a machine excerpt)
- **Earnings call:** Earnings-call transcript on file — read FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf in full for management posture (pointer only; the machine does not curate or embed transcript content)
  - ↳ `CIQ transcript FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf`

## Synthesis (LLM — framing for the human, every point source-bound)

**Evidence balance:** strongly-bearish — idiosyncratic -90% relative collapse with cash burn and UNKNOWN runway/leverage/refinancing, against only a rising but unprofitable top line.

### Bull case (overshoot / mean-revert)
- Revenue is on a sustained absolute uptrend (Oct-2022 3,419 → LTM Mar-2026 5,304), so the falling/zero gross-margin % is the optical misread, not a revenue-collapse signal — the absolute base is rising.
  - ↳ `CIQ Financials→Income Statement (margin % + absolute EBITDA reconciler)`
- ROIC has improved each period from -11.2% to -3.3% LTM, indicating the loss-making trajectory is narrowing rather than deepening.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- On NTM TEV/Rev the name (0.36) sits below the peer low (0.62), and the revenue-growth fundamental delta is favourable (name 22% vs peer-median 9%), posing whether the revenue discount is RESIDUAL (overshoot) rather than EARNED — though comparability is gated and beta is adverse.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- Consensus posture is constructive — target mean/median $17.00 and a Buy (1.00) recommendation — against a current name cap of $256M.
  - ↳ `CIQ Estimates→Consensus`
- Management posture cites the closed Hulu Live combination as adding scale, distribution and integration synergies (ad-tech migration, ESPN commerce flow) — a strategic offset to be weighed (tone only, no figures derived).
  - ↳ `CIQ transcript FuboTV Inc., Q1 2026 Earnings Call, Feb 03, 2026.rtf`

### Bear case (terminal / value-trap)
- Levered FCF is negative at -131.2 and the FCF sign is negative — the company is burning cash, a real cash-generation signal not offset by any reconciler in the facts.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- The headline P/E (12.1) is the optical MISREAD, not the real signal — it rests on a non-current positive EPS while the latest annual EPS is negative (-0.54), so the multiple is not meaningful.
  - ↳ `EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)`
- On the one forward profitability multiple that exists, NTM TEV/EBITDA (name 17.77) is a PREMIUM to the peer median (8.19), so the only clean forward EBITDA read is not cheap — undercutting the overshoot framing on EBITDA.
  - ↳ `CIQ Comparable Analysis→Trading Multiples (name row + Summary Statistics Low/Median/Mean/High)`
- Share count is diluting (+4.0% trailing ~1yr) and a reverse stock split was announced, compounding shareholder dilution risk.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2025-07-31`
- Beta is elevated (name 2.4 vs peer-median 1.4) and Debt/EBITDA is NM vs a peer-median 3.2 — the fundamental deltas show adverse risk legs that can make the revenue discount EARNED rather than residual.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`
- The name fell -72.1% over 180d while the small-cap market rose +17.8%, a -89.9% relative underperformance — the de-rating is idiosyncratic, not a shared-market move.
  - ↳ `EOD name−IWM 180d (screen data-record, G2)`
- Gap-downs cluster on discrete earnings 8-Ks (2026-02-03 and 2026-05-06, both item 2.02), tying the collapse to results events.
  - ↳ `EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)`
- Revenue is 100% one segment (Streaming) and 100% US-geographic, with a key NBCUniversal/Comcast distribution renewal stalled per management — concentration plus content-rights risk.
  - ↳ `CIQ Financials→Segments (Revenues, latest annual column)`

### Twin reference cases
- **Roku Inc.** — recovered
  - distinguished by: US streaming-platform name that de-rated hard on profitability fears then stabilised as ad-monetization and scale narrative reasserted.
  - source: [LLM-suggested, unverified]
- **Chewy Inc.** — recovered
  - distinguished by: Growth name that paired persistent GAAP losses with rising revenue and improving cash trajectory, eventually inflecting toward profitability.
  - source: [LLM-suggested, unverified]
- **WeWork** — went terminal
  - distinguished by: Cash-burning name with unresolved runway/refinancing visibility where dilution and solvency overwhelmed a scale-growth story.
  - source: [LLM-suggested, unverified]
- **Quibi** — went terminal
  - distinguished by: Streaming entrant dependent on content/distribution deals where loss of partner access undercut the subscriber thesis.
  - source: [LLM-suggested, unverified]
- **DISH Network** — went terminal
  - distinguished by: Pay-TV-exposed business pressured by content-carriage renewals and subscriber churn against a heavy debt load.
  - source: [LLM-suggested, unverified]

### Decisive question
**Does the post-Hulu-Live combined entity reach self-funding (positive FCF) before cash burn and dilution force a dilutive raise or solvency event?**

### …evidence for
- ROIC improving each period to -3.3% LTM and revenue rising to 5,304 LTM suggest the loss trajectory is narrowing.
  - ↳ `CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)`
- Favourable revenue-growth delta (name 22% vs peer-median 9%) is consistent with a still-scaling top line.
  - ↳ `CIQ Comparable Analysis→Operating Statistics (name vs peer median: growth/margin/leverage/beta)`

### …evidence against
- Levered FCF is -131.2 and FCF sign negative — still burning cash.
  - ↳ `CIQ Financials→Cash Flow 'Levered Free Cash Flow' [LTM 12 months Mar-31-2026]`
- Survival capacity is explicitly flagged: net-debt/EBITDA UNKNOWN, runway not derived, nearest refinancing wall UNKNOWN — solvency risk. ⚠ uncited
  - ↳ `EDGAR net-debt/EBITDA + FCF sign + CIQ Capital Structure (survival capacity)`
- Share count diluting +4.0% trailing alongside an announced reverse split.
  - ↳ `EDGAR XBRL shares, trailing 2024-07-31..2025-07-31`

### Key unknowns
- EV/EBITDA (LTM), EV/EBITDA percentile, adjusted EV/EBITDA fwd and adjusted EPS are all UNKNOWN (EBITDA<=0 / not in 99.1 guidance) — no clean enterprise-value or profitability multiple to anchor valuation.
- Net-debt/EBITDA and net-debt/EBITDA adjusted are UNKNOWN — leverage cannot be assessed; with cash-burn this is a BEARISH opacity, not a neutral gap.
- Cash runway is NOT derived and the nearest refinancing wall is UNKNOWN (no maturity dates parsed) — survival visibility missing; BEARISH opacity given negative FCF.
- Interest coverage UNKNOWN (missing EBITDA or interest expense row) — debt-service capacity unverifiable.
- Revised guidance from the 99.1 exhibits was NOT parsed for either earnings 8-K — forward outlook absent; a missing expected disclosure, treated as BEARISH.
- Segment-level EBITDA UNKNOWN (no EBITDA section) — profitability of the single Streaming segment is opaque.
- Surprise history UNKNOWN (no fiscal-year header) — cannot gauge beat/miss pattern behind the earnings gap-downs.
- No graph cohort (FUBO absent from coverage) — idiosyncratic-vs-shared read relies solely on the name-vs-IWM relative.
- Outcome of the stalled NBCUniversal/Comcast renewal and its subscriber impact is unresolved per management commentary.
- TEV/LTM EBITDA has <4 quarters, so range_position and the 5y EBITDA percentile cannot be computed.
