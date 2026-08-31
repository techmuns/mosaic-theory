---
id:
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: docs/audits/2026-07-28-smpl/ic-memo.md
date-source: the filename's own date prefix, which the document's heading repeats — not inferred
---

# Investment Committee Memo — The Simply Good Foods Company (Nasdaq: SMPL)

**Audit of:** `SMPL-dossier_today.md` (assembled 2026-07-24 13:02 UTC; disposition displayed WATCH 2026-07-27)
**Ledger rows in scope:** `V-SMPL-screen2-20260706` (ENTRY/BUY, 2026-07-21) · `C-SMPL-screen2-20260706` (CLOSE, 2026-07-24)
**Memo date:** 2026-07-28
**Priced at:** $10.28 (CIQ comps close, as-of 2026-07-24)
**Status:** Authoritative full version. Supersedes any abridged circulation.

---

## Artifact Manifest

Three artifacts came out of this audit. Only two were previously exported as files, which is why the committed copy of the audit lacked material present in the analysis as delivered.

| Artifact | Purpose | Authoritative for |
|---|---|---|
| **This memo** | Full Investment Committee audit and stress test, 13 sections plus scoring | The audit finding of record, the decision sequence, the evidence dashboard |
| `SMPL-dossier-defect-report.md` | Platform and name-level defects with root cause, fix and acceptance test | The engineering queue |
| `SMPL-independent-dossier.md` | Rebuilt thesis on corrected methodology (brand-level sum-of-parts, cross-section multiples, time-value discipline) | The investment view and entry conditions |

**Precedence on valuation.** §10 of this memo carries the audit-stage valuation (probability-weighted $14.44, 2.15:1 undiscounted). The independent dossier subsequently rebuilt it on a brand-level model with time-value discipline and reached $16.47 nominal / **$12.69 present value / 1.36:1 time-adjusted**. Where the two differ, **the independent dossier supersedes this section.** The direction and the findings are unchanged; the later document applies a discount to upside that this memo did not.

---

## ON MECHANISMS — appended 2026-07-28

This audit was conducted against the **artifact, not the code**. Every symptom recorded was
reproduced and verified. The stated root cause of each defect is **inference**, and has been wrong
in seven of nine cases on subsequent code inspection.

**Treat the symptom column as evidence and the mechanism column as hypothesis.**

Confirmed divergences at the time of writing: P1 (the line never reaches the assembled table, so a
guard scanning it could never fire) · P3 (a correctly-frozen reference row, mislabelled — not a
stale anchor) · P4 (the Polygon local store, not the ledger exit price) · P5 (the consumer, not the
series reader — and the defect is a value carrying no date of its own rendered under another
reading's as-of) · P8 (one extracted vintage plus one frozen record reference — not two
extractions) · the WATCH claim (a record reissue in a store the audit never saw) · and P5's second
half reaching further than stated (two consumers, not one).

The findings were sound and two of them uncovered defects nobody had looked at. The risk this note
guards against is narrower and specific: **a fix aimed at the wrong mechanism reports success while
the defect survives.**

---

## ERRATUM — appended 2026-07-28

**Kind:** `note_clear` · **Class:** scoping defect in the audit. Not a finding reversal.

§B of the audit trail below originally stated, of the 2026-07-27 WATCH disposition: *"There is no WATCH row."*

**That claim is wrong as written.** It was scoped to the five-row `decision_ledger.jsonl` supplied to the auditor. The WATCH is a **2026-07-27 record reissue** held in a separate store the auditor never saw.

**Corrected text:** *No WATCH row exists in the decision ledger; the WATCH is a 2026-07-27 record reissue, rendered by the md twin without the close-aware disposition chip the web surface carries.*

The underlying sequence is coherent — BUY logged 07-21, position closed 07-24, record reissued as WATCH 07-27. The defect is one of render parity, not data conflict, and is queued as a visible-absence rule.

**Note on the auditor's own error pattern.** This is the second time in the same audit that a conclusion was drawn from an artifact that did not declare its own limits. The first was P3, where a stale value was attributed to the anchor block because the dossier's source label said so. Both are instances of the assertion-integrity finding pointing back at the audit itself.

---

# Part I — Audit Trail

## A. Evidence Coverage — Final

| Materiality | Total | Verified | Partially verified | Outdated / contradicted | Unresolved | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| High | 48 | 37 | 3 | 7 | 1 | **98%** |
| Medium | 41 | 30 | 4 | 4 | 3 | 93% |
| Low | 15 | 9 | 2 | 1 | 3 | 80% |
| **Total** | **104** | **76** | **9** | **12** | **7** | **93%** |

Three of the auditor's own preliminary flags were retracted during the audit and are recorded in §11.

**Sources.** CIQ bundle (6 workbooks, 43 worksheets, comps as-of 2026-07-24), FQ2 and FQ3 FY2026 earnings transcripts, ledger payloads `V-` and `C-`, and independent verification against SEC filings, company releases, competitor filings and market data.

## B. The Decision Sequence

| Date | Row | Event | Price | Ratio | Record |
|---|---|---|---|---|---|
| 2026-07-21 | `V-SMPL-screen2-20260706` | **ENTRY — BUY** | $10.92 @ 07-20 | 4.03:1 | `machine_lean: mixed`, `disposition: no_proposal`, `revealed_pre_verdict: false` — machine proposed nothing; the human decided |
| 2026-07-24 | `C-SMPL-screen2-20260706` | **CLOSE** | exit $10.53 @ 07-22 | — | Reason: input-staleness. Every financial and valuation panel predated the 2026-07-09 quarterly report. A process correction, not a market call |
| 2026-07-24 13:02 UTC | — | Dossier assembled | — | 3.83:1 | The promised re-underwrite on current data |
| 2026-07-27 | *(record reissue — see ERRATUM)* | Disposition **WATCH** | $10.53 | — | Held in the record store; the md twin renders it without the close-aware chip |

Three consequences.

**The $10.53 is not a spot price.** The dossier presents it as "Spot $10.53 (underwritten 2026-07-27)." It is a 2026-07-22 close (Polygon, local store), two sessions stale, while the bundle's own comps panel carries **$10.28** as-of 2026-07-24. Every ratio in the headline grid is measured against it. At $10.28 the grid reads 4.19:1.

**The re-underwrite did not cure the defect it was ordered to cure.** The close was called for staleness against the 2026-07-09 print. The 2026-07-24 dossier still carries: April guidance, a one-month-old consensus vintage, a stale LTM revenue reference row, a March-vintage P/LTM EPS, a 07-22 price, and the FY2025 impairment instead of the FY2026 one.

**Information regression.** Three facts were recorded in the ledger V-row on 21 July and absent from the dossier assembled on 24 July.

| Fact | V-row text | Dossier |
|---|---|---|
| FY26 impairments | "YTD FY26 non-cash impairments $331.0M" | cites $60.9M (FY25) |
| Loan-basis leverage | "the 8-K's loan-basis reads 1.2x" | "covenant basis: UNKNOWN" — a false UNKNOWN |
| Q3 buyback pace | "~2.1M sh / ~$25M in the quarter" | share-count reduction only |

## C. Boundary-Cell Reconciliation

The headline 3.83:1 and the appendix cells are different objects: the headline uses the *recorded* bear leg ($6.95); the cells are *combined-stress* tests. The parallel `V-IT-` ledger row confirms the convention. All six reproduce exactly.

| Cell | Price | Normal margin | Base value | Computed | Recorded |
|---|---|---|---|---:|---|
| A — 1,100 × 8% × 6.0x → $3.54 | $10.92 | 15.5% | $26.90 | 2.17:1 | 2.17 clears |
| B — 1,050 × 7% × 6.0x → $2.62 | $10.92 | 15.5% | $26.90 | 1.93:1 | 1.92 fails |
| A | $10.53 | 15.5% | $26.90 | 2.34:1 | ≈2.34 |
| B | $10.53 | 15.5% | $26.90 | 2.07:1 | ≈2.07 |
| A | $10.53 | 14.0% | $24.24 | 1.96:1 | ≈1.96 |
| B | $10.53 | 14.0% | $24.24 | 1.73:1 | ≈1.73 |

**What survives as a finding:** at entry one stress cell already failed (1.92:1, disclosed as "Known fragility, accepted"). On the re-set 14% normal **both** now fail. The downside envelope deteriorated between 21 and 27 July, which the WATCH reflects and the dossier states accurately.

---

# Part II — Investment Committee Memo

## 1. Source-Data Reconciliation

**The Q3 print verifies completely.** Net sales $357.0M against $381.0M; net loss $52.0M against net income $41.1M; diluted loss $0.58 against earnings of $0.40; adjusted EBITDA $57.2M; adjusted diluted EPS $0.42. Adjusted EPS beat the Zacks consensus of $0.35 and revenue beat the $343M consensus. *(Q3 FY2026 press release, 2026-07-09; Zacks, 2026-07-10)*

**The impairment chain closes exactly across five sources.**

| Component | Amount | Source |
|---|---:|---|
| Q2 FY26 (OWYN + Atkins brand assets) | $249.0M | Q2 transcript, 2026-04-09 |
| Q3 FY26 (goodwill + Atkins/OWYN intangibles) | $82.0M | Q3 transcript and release, 2026-07-09 |
| **YTD FY26** | **$331.0M** | Q3 release; also recorded verbatim in the ledger V-row |
| FY25 Q4 | $60.9M | 8-K `0001702744-25-000043` |
| **LTM Asset Writedown** | **$391.9M** | CIQ Annual Income Statement |

**The guidance conflict resolves against the dossier.** The July 9 outlook is net sales $1.345–1.355B (−7% to −6%), gross margins down approximately 375bps, adjusted EBITDA $220–225M (−21% to −19%). *(Q3 release)* The dossier's "Revised guidance" block reproduces the **April 9** figures and its bear case argues from them. Sell-side commentary on 10 July characterised the quarter as a beat with a modest FY26 guidance raise.

| Claim | Dossier | Verified | Status |
|---|---|---|---|
| FY26 revenue guide | $1.31–1.35B | **$1.345–1.355B** | **Outdated** |
| FY26 adj EBITDA guide | $217–225M | **$220–225M** | **Outdated** |
| Impairment | $60.9M (FY25) | **$331.0M YTD FY26** | **Contradicted** |
| Q3 net sales / EBITDA / adj EPS | $357M / $57.2M / — | $357.0M / $57.2M / $0.42 | **Verified** |
| Atkins −24.6%, Quest +1.1%, OWYN +3.6% | as stated | Q3 transcript, verbatim | **Verified** |
| Takeaway −6.7%, penetration 8.5% / −220bps | as stated | Q3 transcript, verbatim | **Verified** |
| Category +10% | as stated | Management-sourced, Q3 transcript | **Verified as reported, not independently** |
| Insider buys 2 / sells 0, +90.0K sh | as stated | ~$1.1M across two transactions, 90,000 shares, three months, no selling | **Verified** |
| Hain cap $49M | as stated | $0.56/share, ~$50.5M capitalisation | **Verified** |
| 52-week range $10.21–$34.19 | as stated | Confirmed | **Verified** |

## 2. Calculation and Financial Audit

| Calculation | Report | Recalculated | Finding |
|---|---|---|---|
| Own-history band (35 closes, 2017-12→2026-06) | low 6.11x, med 17.85x, p25 15.20x, p75 20.88x | **identical to 2dp** | **Exact** |
| 12.5x / 16.0x percentiles | 14th / ~29th | **14.3% / 28.6%** | **Exact** |
| Margin anchors (FY20 9.58%, FY22 17.35%, 7yr median 15.51%, FY25 ex-impairment 15.01%) | as stated | all reproduce exactly on GAAP `OperatingIncomeLoss` including unusuals | **Exact** |
| Entry-boundary cells | 2.34 / 2.07 / 1.96 / 1.73 | all four exact; ledger's 2.17 / 1.92 at $10.92 also exact | **Exact — auditor flag retracted** |
| EBIT→EBITDA bridge | undisclosed | D&A $21.8M, matching the V-row's "~17.1% EBITDA-margin equivalent" against a 15.5% operating margin | **Legitimate — auditor flag retracted** |
| Valuation share count | 88.46M disclosed | **engine used 93.68M**; management guides ~90M weighted-average diluted | **Not reproducible from the page; understates base ~$1.00–1.50/sh** |
| "P/LTM EPS 16.0x… normalized basis" | 16.0x | 2026-03-31 close of a **GAAP** metric now NM; current P/LTM Normalized is 8.90x | **Stale + definition mismatch** |
| "FCF ≈13% of market value" | ~13% | $107.2M ÷ $909M = **11.8%**; the 12.3% originates in the V-row using $125.5M levered FCF on a $1,023M entry cap | **Inherited stale input** |
| LTM revenue $1,416.208M | as stated | **$1,392M** current; 1,416 is LTM through FQ2, held in the underwrite record's frozen reference row and mislabelled as the anchor block | **Provenance mislabel** |
| Base margin derivation | "between 15.51% median and ~13.8% trailing" | 15.51% is GAAP-inclusive; 13.89% is CIQ clean EBIT. On the anchor basis LTM is **−17.05%** | **Two bases averaged** |
| Term loans "249.1→397.0 QoQ" | implied one-quarter jump | 396.7 → 396.9 → **397.0** across three quarters | **Period mismatch — auditor flag retracted** |
| Total debt/EBITDA 1.9x | as stated | 2.0x (Financials), 1.93x (comps EBITDA $232.8M) | **Match after basis disclosure** |
| Spot $10.53 | "underwritten 2026-07-27" | 2026-07-22 close; bundle's own close 2026-07-24 is **$10.28** | **Stale, falsely stamped** |

**The multiple axis and the margin anchors are fully auditable and correct.** That is the dossier's real methodological strength.

## 3. Forecast and Consensus Audit

The dossier stops at FY27. Extending the CIQ Trends ladder changes the reading of its own base case.

| Consensus (current vintage) | FY26 | FY27 | **FY28** | FY29 | FY30 | FY31 |
|---|---:|---:|---:|---:|---:|---:|
| Revenue | 1,351.8 | 1,284.6 | **1,331.0** | 1,337.6 | 1,365.9 | 1,455.0 |
| EBITDA | 222.1 | 220.9 | **232.9** | 235.4 | 240.8 | 271.0 |
| EBIT | 198.7 | 199.6 | **211.9** | 209.9 | 215.4 | 233.0 |

**The dossier's "mid-cycle" base revenue of $1,330M is consensus FY2028 revenue ($1,331.0M) to within 0.1%.** Not a conservative mid-cycle estimate — the street's two-years-out number. Its base EBITDA of $208.0M sits 10.7% below consensus FY28, so on earnings the dossier is more conservative than the street in every year. **The entire disagreement is the multiple.**

Brand-mix decomposition from the YTD disclosures — net sales $1,023.2M, down 5.4%, Atkins and OWYN declining 22.6% and 5.5% against Quest growth of 3.4% *(Q3 release)* — implies FY25 weights of approximately Quest 60%, Atkins 31%, OWYN 9.5%, moving to Quest ~65% / Atkins ~25% by FY26.

- Atkins at ~25% of sales declining ~25% is a **−6pt annual drag** persisting at least two more years.
- **Quest decelerated from +3.4% YTD to +1.1% in Q3.** The V-row named it: *"the carry engine is unproven, the accepted open risk."* It is now visibly weakening.

## 4. Thesis Pillar Review

| Pillar | Report view | Independent view | Confidence | Decision impact |
|---|---|---|---|---|
| Priced below its own history | 5.3x vs 6.11x band low | **Verified exactly.** But the band was earned 2018–23 while EBITDA compounded $67M→$262M | Medium | Weakens the anchor, not the fact |
| **Overshoot, not terminal** | Market prices category decline | **Mis-specified.** The category is growing; see §8 | **Low** | **Thesis-altering** |
| Balance sheet carries the wait | 1.5x net, self-funding | **Verified and strong.** ~1.2x loan basis, coverage 8–11x, no covenant stress evident | High | Genuine support |
| Quest is the carry engine | +1.1%, ahead of plan | Verified but **decelerating** | **Low** | Bull leg unproven and weakening |
| Margin re-set to 14% is conservative | vs 15.51% median | Verified — below consensus and below guided ~16.5% adj-EBITDA margin | High | Real conservatism |
| Base conservative vs guidance | 1,330 < guide | **Verified** — below the $1,345M floor. But it equals consensus FY28 | Medium | True but duration-mismatched |
| September price increase repairs margin | asserted | **Unsupported and contra-indicated.** See §8 | **Low** | Pivotal and unhedged |
| **12.5x exit multiple** | 14th percentile of own history | **Unsupported by the cross-section.** 43% above peer median NTM of 8.72x | **Low** | **Drives the entire target** |

## 5. Variant Perception — The Decisive Finding

| Multiple applied to base EBITDA of $208.0M | Implied value | vs $10.28 |
|---|---:|---:|
| 5.34x — what the market pays today | $8.88 | −14% |
| 7.85x — peer median LTM | $14.78 | +44% |
| 8.72x — peer median NTM | $16.82 | +64% |
| 10.0x — generous re-rate | $19.83 | +93% |
| **12.5x — dossier base** | **$25.71** | **+150%** |
| 17.85x — own-history median | $38.28 | +272% |

At today's price the market capitalises **consensus FY2028 EBITDA of $232.9M at 5.30x**. The dossier capitalises *below*-consensus FY2028 EBITDA at 12.5x. Earnings are not the disagreement. **The entire +130% is a multiple re-rating call, and the dossier never states it as one.**

Three cross-checks converge; none reaches $24:

- Peer-parity re-rate (8.72x): **$16.82**
- Forward FCF at 9% on ~$92M post-capex: **$11.55**; at 7%: **$14.85**
- Street: CIQ mean $14.88 · MarketBeat 13-analyst consensus Hold, average $15.20 · Yahoo one-year estimate $17.50

**Verdict on differentiation: none once the multiple is set from evidence.** The probability-weighted value in §10 is $14.44. The street is $14.88–$15.20. The dossier's edge is an artefact of borrowing a growth-era multiple.

**Regime test on the own-history band** (added post-memo, supporting the same conclusion): 31 of 35 closes (89%) were formed while trailing adjusted EBITDA was growing, median 18.96x; 4 of 35 (11%) while declining, median 6.93x. EBITDA compounded 19.5% a year FY17→FY25 then fell 20% into FY26E. The engine's 17.85x is effectively the growth-regime median.

## 6. Catalyst and Timing Audit

| Catalyst | Window | Mechanism | Awareness | Prob. | Transmission | Failure risk |
|---|---|---|---|---|---|---|
| FQ4 FY26 print + **initial FY27 guidance** | ~Oct 2026 | First test of price-increase retention and Quest re-acceleration | High | 100% | **High — the only true near-term catalyst** | Guidance below ~$1.30B breaks the base path |
| September price increase | Sep 2026, visible Jan 2027 | Margin repair | Medium | 100% occurs; ~50% sticks cleanly | High if it holds | Elasticity; see §8 |
| Target / Walmart launches | ~Jan 2027 | Distribution | Low | Medium | **Negligible** | Immaterial to a $909M cap |
| Multiple re-rating | Undefined | Sentiment | — | — | **This is the thesis** | **No catalyst exists for it** |

**Timing verdict: the catalyst path does not support the thesis.** The value driver is a re-rate with no scheduled trigger, on a 180-day fund horizon, against a base case equal to consensus FY2028.

## 7. Management, Governance and Accounting Quality

**A material governance event is absent from the dossier.** On 2026-04-21 the company announced cost savings and corporate realignment; the Chief Human Resources Officer was to step down and depart by 2026-06-01, and the Chief Supply Chain Officer would work on strategic projects before separating. *(Company release, 2026-04-21)* C-suite turnover concurrent with a turnaround is a monitoring item the dossier does not mention.

**Insider buying looks different in context.** The 90,000-share purchase is verified, but insiders sold roughly $12.36M over a prior twelve-month window including a 147,200-share sale by the CEO at $36.86 in November 2024. Roughly $1.1M of buying at ~$11 against $12.4M of selling at ~$36 is a weak confidence signal; the dossier presents only the buying half.

**Capital allocation is the sharpest governance question.** Buybacks of ~$213M in the fiscal year against $102.2M of YTD operating cash flow — roughly 2× — drew cash from $194.1M to $123.9M and took net debt from $257M to $324.6M while EBITDA fell. The pace has since corrected (~$23M in Q3), and management would not commit the remaining $158M authorisation.

**Earnings quality.** $391.9M of writedowns in twelve months against a $909M market capitalisation is management's own mark on permanent brand-value destruction. Normalized EPS of $1.155 against GAAP of −$2.08 is a $3.23/share gap the dossier never itemises. No revenue-recognition, receivables or off-balance-sheet concerns surfaced. The accounting issue is *classification of the impairments as non-recurring* when Atkins has now been written down in consecutive years.

## 8. Competitive and Industry Audit — The Thesis Breaker

The dossier's premise is that the market wrongly believes GLP-1s are shrinking the category. **Competitor filings contradict the premise.**

BellRing's FY2025 annual report states that category growth remains robust and expects marketing spend, expanded shelf space, innovation and the mainstreaming and affordability of GLP-1s to drive higher household penetration and category growth over the medium to long term. Its CEO has described better-for-you RTD shakes as one of the fastest-growing CPG categories, driven by health and wellness trends, functional beverage preferences and GLP-1 usage. Independent work puts functional nutrition growth at roughly 7% per year in early 2026 and treats GLP-1 adoption as structurally additive to high-protein demand, since users are advised to raise protein intake to preserve muscle mass.

SMPL's own CEO says the challenges are execution-driven rather than category-driven. **The market, the competitor and the company all agree the category is fine.** The dossier's variant perception is aimed at a consensus that does not exist. What the market prices is SMPL-specific share loss — a category growing ~10% against company takeaway of −6.7% implies a share-loss rate the dossier reports but never computes.

Two findings cut against the pivotal margin assumption:

- BellRing's Q2 FY2026 Premier Protein RTD net sales rose 2.3% on 12% volume growth — roughly ten points of negative price/mix at the category leader. **Taking a high-single-digit increase into that is high-risk.** No elasticity analysis exists in the dossier, the transcripts, or locatable sell-side work.
- Whey protein isolate spot prices reached record levels in 2026 — WPC80 above $11/lb and isolate in the $12 range per USDA, standard whey up more than 50% since January, with some suppliers sold out for the year. The cost pressure is industry-wide; the price increase is defensive, not margin-expanding.

**The twin analysis needs re-specification.** Medifast's Q1 2026 revenue fell 34.3% to $76.0M as active earning coaches dropped 44.9% to 14,000, attributed partly to rapid GLP-1 adoption, with full-year guidance of $270–300M. Terminal — verified. But Medifast is a weight-loss MLM, not a snacking brand. **SMPL is a composite of both twins:** Atkins is the Medifast analogue, Quest is the BellRing analogue, OWYN is broken. A single overshoot-versus-terminal binary cannot represent that.

## 9. Devil's Advocate

**The strongest bear case is not bankruptcy — it is a value trap with a decade-long clock.** Net leverage of 1.5x, coverage of 8–11x, no going concern, positive free cash flow: SMPL can decline for years without a financing event. That removes catastrophic risk *and* removes the forcing mechanism that would compel a re-rate.

1. **The multiple never comes back.** The market pays 5.3x today and 5.30x on FY2028 consensus. If a declining brand portfolio deserves 6–7x, fair value is $9–12 and the stock is fairly priced now.
2. **Quest stalls.** +3.4% YTD → +1.1% Q3. Flat Quest leaves the −6pt Atkins drag unopposed and revenue heads toward $1,200M, below the dossier's bear leg.
3. **The price increase backfires.** HSD pricing into −6.7% takeaway while the category leader absorbs ten points of negative price/mix.
4. **The bear leg embeds a re-rate.** 7.0x sits at the 5.7th percentile of the name's history — but the market pays 5.34x today, **below the entire 35-close range**. Risk of $3.58 is understated.
5. **Impairments are recurring, not one-time.** Atkins written down in consecutive years. A third would confirm secular erosion.
6. **The single assumption with the greatest downside is the exit multiple.** Moving base from 12.5x to 8.0x removes $10.58/share — more than the current share price.
7. **The combination creating permanent loss:** Quest flat + Atkins −25% + multiple at 5.5x → roughly $5–6/share, a 45% impairment with no solvency event to force resolution.

**What a short seller would argue.** You are paying for a portfolio whose largest legacy asset lost 220bps of household penetration in a year, whose growth engine decelerated to 1%, whose management wrote off $392M of goodwill and intangibles in twelve months, and whose balance sheet was weakened by $213M of buybacks at 2× operating cash flow at prices three times higher. It is cheap because the earnings base is still falling and nobody knows where it stops.

## 10. Scenario and Valuation Stress Test

*Audit-stage view. Superseded on valuation by the independent dossier — see Artifact Manifest.*

Multiples anchored to the peer cross-section, not to the name's growth-era history. Priced against **$10.28**.

| Variable | Severe | Bear | Base | Bull |
|---|---:|---:|---:|---:|
| Revenue ($M) | 1,180 | 1,240 | 1,300 | 1,380 |
| EBITDA margin | 13.5% | 14.5% | 16.0% | 17.5% |
| EBITDA ($M) | 159.3 | 179.8 | 208.0 | 241.5 |
| Net debt ($M) | 360 | 340 | 325 | 300 |
| EV/EBITDA | 5.0x | 6.0x | 8.0x | 10.5x |
| **Value / share** | **$4.93** | **$8.35** | **$15.13** | **$25.26** |
| vs spot | −52.0% | −18.8% | +47.2% | +145.7% |
| Probability | 10% | 25% | 45% | 20% |

**Probability-weighted value $14.44 (+40.5%). Reward $4.16 / risk $1.93 = 2.15:1** — 44% below the published 3.83:1, and fragile: a base multiple of 7.5x instead of 8.0x drops it below 2:1.

**Sensitivity, ranked:** exit multiple (±1.0x = ±$2.35/sh) ≫ EBITDA margin (±100bps = ±$1.18) > revenue (±$50M = ±$0.72) > net debt (±$25M = ±$0.28).

## 11. Red Flag Register

| Red flag | Category | Severity | Thesis impact | Action |
|---|---|---|---|---|
| Variant perception aimed at a non-existent consensus | Thesis-breaking | **Critical** | Removes the stated edge | Re-specify as a share-loss thesis |
| $331.0M FY26 impairment omitted | Data-quality / thesis | **Critical** | Bear case argues from a figure 5.3× too small | Rebuild the bear leg |
| Exit multiple 43% above peer median | Valuation | **Critical** | Drives all excess upside | Reprice at 8.0–8.7x |
| Guidance block one quarter stale | Data-quality | High | Bear leg overstated | Refresh |
| "Spot" is a 07-22 price stamped 07-27 | Process | High | Every ratio mis-anchored | Re-price at market |
| Quest decelerating 3.4%→1.1% | Operating | High | Bull leg weakening | Enforce the existing kill criterion |
| Price increase into negative category price/mix | Operating | High | Pivotal lever unhedged | Model elasticity |
| Buybacks at ~2× operating cash flow | Governance | High | Balance sheet weakened pre-turnaround | Monitor Q4 pace |
| Share count 93.68M vs 88.46M disclosed | Calculation | Medium | Understates base ~$1.00–1.50 | Correct and disclose |
| C-suite turnover unreported | Governance | Medium | Execution risk understated | Add |
| Insider buying without the selling history | Framing | Medium | Overstates signal | Present both |
| Covenant terms printed UNKNOWN | Data gap | Medium | False UNKNOWN — the V-row knew 1.2x | Ledger read-back |
| ~~Headline 3.83:1 contradicts 1.96:1 cells~~ | — | **Retracted** | Stress cells ≠ governing ratio | — |
| ~~EV computed on EBIT~~ | — | **Retracted** | Bridge is deliberate and correct | — |
| ~~Term loans +$148M QoQ~~ | — | **Retracted** | Period mismatch only | — |

## 12. Falsification and Monitoring Framework

| Condition | Measurement | Warning | Failure | Frequency | Action |
|---|---|---|---|---|---|
| Quest carry engine | Quest net sales YoY | <+1.0% one quarter | **≤0% two consecutive quarters** | Quarterly | Bull and base legs void |
| Revenue path | Initial FY27 guidance | $1.30–1.32B | **<$1.30B** | Oct 2026 | Base revenue path fails |
| Margin regime | Reported gross margin | <32.5% | **<31.0% sustained, or FY26 decline >375bps** | Quarterly | Margin re-set invalid |
| Price realisation | Q1 FY27 price/mix vs volume | Volume −5% or worse | **Net sales decline widens post-increase** | Jan 2027 | Pivotal lever failed |
| Atkins terminality | Household penetration | <8.0% | **<7.0%, or takeaway decline steepens two quarters** | Quarterly | Terminal twin confirmed for 25% of sales |
| Impairment recurrence | Further writedown | any | **>$50M in FY27** | Quarterly | Secular, not cyclical |
| Multiple thesis | TEV/NTM EBITDA | <5.0x two quarters | **<4.5x** | Monthly | Re-rate thesis has no market support |
| Balance sheet | Net debt / adj EBITDA | >1.8x | **>2.5x, or buybacks above operating cash flow** | Quarterly | Capital allocation broken |
| Valuation exit | Price | — | **>$16.50** (peer-parity value) | Continuous | Trim/exit — thesis realised |

## 13. Final Decision

### Executive decision: **WATCHLIST — defer pending the October print**

| | |
|---|---|
| **Confidence** | Medium-high in the analysis; low in the dossier's stated ratio |
| **Horizon** | 12–24 months if entered; the fund's 180-day horizon is **incompatible** with a base case equal to consensus FY2028 |
| **Primary catalyst** | FQ4 FY26 print and initial FY27 guidance, ~October 2026 |
| **Principal downside** | Value trap: −19% to bear, −52% to severe, with no solvency event to force resolution |
| **Risk–reward** | **2.15:1** on independent numbers, against 3.83:1 claimed |
| **Most important unresolved question** | Does the September price increase hold without accelerating volume and distribution loss? |

### Independent finding

The dossier reaches a defensible disposition through substantially unreliable reasoning. Its methodological machinery — the multiple band, the margin anchors, the boundary cells, the EBITDA bridge — is auditable and reproduces exactly. Its inputs and its framing do not. The stated 3.83:1 is anchored to a stale price, a superseded guidance block, a one-month-stale consensus vintage, a share count 6% above the disclosed figure, and an exit multiple 43% above the peer cross-section, while omitting $331M of impairments its own author had recorded three days earlier.

**Direction: correct. Magnitude: overstated by roughly 78%. Differentiation: none.** A probability-weighted value of $14.44 against a street consensus of $14.88–$15.20 means this is a consensus long, not a variant one.

### What the report gets right

The balance-sheet pillar is real and verified. The margin re-set to 14% is genuinely conservative — below consensus in every year and below management's guided ~16.5% adjusted-EBITDA margin. The multiple statistics are exact. The bear direction on Atkins is correct and corroborated. The self-flagged caveats are honest, and the entry-boundary disclosure of accepted fragility is exemplary discipline.

### What it gets wrong

The variant perception is aimed at a consensus no participant holds. The largest number in the income statement is absent. The bear case argues from superseded guidance. The upside is a pure multiple re-rate presented as an earnings-and-multiple story. Catalyst timing does not match the horizon. The surprise history shows only annual GAAP data ending in a −36% year while the last three quarters beat normalized EPS by +8.3%, +12.5% and +20.0%.

### Conditions for entry

- **Price:** below **$9.00**, restoring a margin of safety against a peer-parity fair value of ~$16.80. *(Refined to ≤$9.50 in the independent dossier on a time-adjusted basis.)*
- **Evidence:** Quest ≥ +3% YoY for two consecutive quarters, **and** initial FY27 guidance ≥ $1.30B
- **Sizing:** half-weight maximum. Single-name, single-segment, 8.2% short interest, ~2.9-day days-to-cover
- **Not before:** the October FQ4 print

### Scoring

| Category | Score | Reason |
|---|---:|---|
| Factual accuracy | 2 | Core operating facts verify; guidance, impairment, spot price and share count do not |
| Source quality | 4 | Primary-sourced and stamped throughout; wrong 8-K selected |
| Calculation integrity | 4 | Everything disclosed reproduces exactly; the undisclosed inputs do not |
| Forecast credibility | 3 | Conservative on earnings; stops one year short of the number that matters |
| Thesis coherence | 2 | Base equals consensus FY28 but is sold on a 180-day horizon |
| Variant perception | **1** | Aimed at a consensus contradicted by the competitor, the company and the market |
| Valuation support | 2 | 12.5x is 43% above peers and unjustified outside the growth era |
| Catalyst quality | 2 | One real catalyst; the value driver has none |
| Downside protection | 3 | Balance sheet genuinely protects; the bear leg's 7.0x embeds a re-rate |
| Governance quality | 2 | Misses C-suite turnover, the buyback/cash-flow gap, the insider selling history |
| Risk identification | 4 | Risks well populated and honestly flagged |
| Decision usefulness | 3 | Right disposition, unreliable supporting arithmetic |

**Report quality 2.7 / 5 · Thesis quality 2.0 / 5 · Investment attractiveness 3.0 / 5 · Confidence in this conclusion: high**

Not averaged mechanically. One critical failure — a variant perception contradicted by primary competitor evidence — caps thesis quality regardless of the strong process scores.

---

## Unresolved, Unavailable and Conditional

**Unresolved (7 claims).** The 2026-07-27/28 close could not be established; retail quote sources conflict and the best-evidenced recent price is $10.28 (CIQ, 2026-07-24). Credit-agreement covenant terms were never located, though the disclosed ~1.2x loan-basis leverage makes this low-risk. FINRA short interest rests on the dossier's own primary pull and was not independently re-verified. Twin outcomes for Central Garden & Pet and e.l.f. Beauty remain unverified (low materiality). Q4 FY26 buyback quantum is unknown and will determine year-end net debt and share count.

**Unavailable.** Brand-level profitability is not disclosed anywhere — single reportable segment. Circana category data is management-sourced only; the +10% figure is verified *as reported*, not independently. Customer concentration percentages do not exist in the CIQ export; only Walmart and Amazon are named.

**Conditional.** The base-case multiple of 8.0x is a judgment anchored to peer parity. Every conclusion about magnitude — the $14.44 weighted value, the 2.15:1 ratio, the exit trigger — moves proportionally with it. The direction of the finding (the dossier's edge is a multiple assumption, not an earnings insight) does not depend on that judgment; the size of the remaining upside does.

**No further CIQ files are required.** Two public items would raise confidence without changing the decision: the FQ3 FY2026 10-Q impairment note by reporting unit, and independent Circana MULO++C category data to test the +10% figure. Neither blocks this conclusion.
