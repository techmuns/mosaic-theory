---
id:
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: docs/audits/2026-07-28-smpl/defect-report.md
date-source: the filename's own date prefix, which the document's heading repeats — not inferred
---

# Defect Report — Mosaic Theory Dossier Pipeline

**Subject artefact:** `SMPL-dossier_today.md` (assembled 2026-07-24 13:02 UTC, disposition WATCH 2026-07-27)
**Ledger rows in scope:** `V-SMPL-screen2-20260706` (ENTRY/BUY, 2026-07-21) · `C-SMPL-screen2-20260706` (CLOSE, 2026-07-24)
**Audit date:** 2026-07-28
**Method:** Investment Committee audit + thesis stress test. Full CIQ bundle reconciliation (6 workbooks, 43 worksheets), both FY2026 earnings transcripts, ledger payloads, and independent web verification against primary filings.
**Claim coverage:** 104 registered claims, 93% resolved.

---

## Executive Summary

Nine platform defects and seven name-level analytical defects. **The platform defects are the priority** — each is mechanical, each will reproduce on every name the pipeline touches, and four of them (P1–P4) are individually capable of inverting a verdict.

The most consequential finding is not an error of judgment. It is **information regression**: three material facts were recorded in the ledger V-row on 2026-07-21 and were absent from the dossier assembled on 2026-07-24. The analyst knew; the pipeline lost it.

A second structural finding: the `C-` row closed the 21 July BUY explicitly for input staleness, promising the name would "return at re-underwrite on current data." The 24 July dossier **is** that re-underwrite, and it still carries six stale inputs. The remediation did not take, which suggests the staleness problem is not caught by any automated guard.

Three of the auditor's own preliminary flags were wrong and are formally retracted in §C. Section D lists machinery that verified exactly and **must not be changed**.

---

## Severity Scale

| Level | Meaning |
|---|---|
| **Critical** | Can invert or materially distort a verdict on its own |
| **High** | Materially distorts a thesis leg or the risk assessment |
| **Medium** | Degrades accuracy or reproducibility without changing direction |
| **Low** | Cosmetic, or correct conclusion reached by a wrong route |

---

## A. Platform Defects — Will Recur On Every Name

### P1 — Largest income-statement line item omitted from synthesis
**Severity:** Critical · **Blast radius:** every dossier

**Evidence.** CIQ Annual Income Statement carries an LTM `Asset Writedown` of **−$391.9M**. The dossier never mentions it. Its bear case cites a **$60.9M** Atkins impairment sourced to an FY2025 8-K (`0001702744-25-000043`). The omitted figure is 43% of market capitalisation and is the sole cause of LTM net income of −$198.8M.

**Reconciliation (exact, five sources).**

| Component | Amount | Source |
|---|---:|---|
| Q2 FY26 impairment (OWYN + Atkins brand assets) | $249.0M | Q2 transcript, 2026-04-09 |
| Q3 FY26 impairment (goodwill + Atkins/OWYN intangibles) | $82.0M | Q3 transcript + press release, 2026-07-09 |
| **YTD FY26** | **$331.0M** | Q3 press release; **also recorded verbatim in ledger V-row** |
| FY25 Q4 impairment | $60.9M | 8-K `0001702744-25-000043` |
| **LTM Asset Writedown** | **$391.9M** | CIQ Annual Income Statement |

**Root cause.** No materiality guard between extraction and synthesis. Nothing forces a line item to appear in the narrative on the basis of size alone.

**Fix.** Add a synthesis-time materiality guard. Any single income-statement or cash-flow line exceeding **10% of market capitalisation or 5% of revenue** must appear in the synthesis, or the build fails loud.

**Acceptance test.** Construct a fixture with a writedown at 11% of market cap; assert the build raises unless the line appears in the synthesis body.

---

### P2 — Guidance block reads the wrong 8-K
**Severity:** Critical · **Blast radius:** every name with guidance

**Evidence.** The dossier's "Revised guidance" block reproduces the **2026-04-09** guide (net sales $1.31–1.35B, adj EBITDA $217–225M, "not satisfied" quote). The current guide, issued **2026-07-09**, is net sales **$1.345–1.355B** (−7% to −6%), adj EBITDA **$220–225M** (−21% to −19%), gross margin −375bps, capex $25–30M, tax ~25%, weighted-average diluted shares ~90M.

The bear case argues from the superseded, worse guide. The base case narrative correctly uses the fresher one. Both appear in the same document.

The ledger V-row cites 8-K `0001702744-26-000021` (Q3). The dossier cites `0001702744-26-000010` (Q2).

**Root cause.** The guidance extractor reads the prose `Situation` cell (Guidance sheet row 14) of a matched 8-K, rather than the structured numeric grid (rows 32–127) which carries its own guidance-date row.

**Fix.** Select guidance by **max guidance date** from the structured grid, never by filing match. Cross-check the prose `Situation` cell against the numeric grid and fail loud on disagreement.

**Acceptance test.** Fixture with two guidance events three months apart; assert the extractor returns the later one and raises if prose and grid disagree.

---

### P3 — Stale committed anchors survive a new print
**Severity:** Critical · **Blast radius:** every name with committed anchors

**Evidence.** The committed anchor block records LTM revenue of **$1,416.208M**. Current LTM is **$1,392M**.

| Window | Quarters | Sum |
|---|---|---:|
| LTM through FQ2 2026 (anchor value) | 381 + 369 + 340 + 326 | **1,416** |
| LTM through FQ3 2026 (current) | 369 + 340 + 326 + 357 | **1,392** |

The anchor was committed before the 2026-07-09 print and never refreshed. It then propagated into the bull-leg rule ("bull sits just under the trailing twelve months"), which the applied figure of $1,420M violates against both values.

**Root cause.** No staleness guard on committed anchors keyed to filing date.

**Fix.** Invalidate any anchor whose `as_of` predates the latest 10-Q/8-K filing date for the CIK; force recompute before the scenario block builds.

**Acceptance test.** Commit an anchor, advance the filing date, assert recompute is forced.

---

### P4 — "Spot" is the ledger's exit price, not a market price
**Severity:** Critical · **Blast radius:** every re-underwrite of a closed name

**Evidence.** The dossier prints `Spot $10.53 (underwritten 2026-07-27)`. That value is the `C-` row's `exit_price`, as-of **2026-07-22**.

| Source | Price | As-of |
|---|---:|---|
| Ledger `C-` row `exit_price` | $10.53 | 2026-07-22 |
| **CIQ comps close (bundle's own)** | **$10.28** | **2026-07-24** (serial 46227) |
| Cross-check: market cap ÷ shares | 909.4 ÷ 88.4605 = **$10.28** | 2026-07-24 |
| Cross-check: P/LTM Normalized EPS 8.90 × $1.155 | **$10.28** | 2026-07-23 |

Every ratio in the headline grid — reward, risk, 3.83:1, +130.2% — is measured against a closed position's exit print, two sessions stale, with a fresher price sitting inside the same bundle. At $10.28 the grid reads 4.19:1.

**This is the precise defect the `C-` row was opened to correct.** It survived the re-underwrite.

**Root cause.** Price sourced from the ledger rather than from a market panel with an independent as-of stamp.

**Fix.** Price must carry its own `as_of`. **Fail loud if `price.as_of < max(as_of)` across all data panels in the build.**

**Acceptance test.** Fixture where the price panel is older than the comps panel; assert the build raises.

---

### P5 — `NM` values silently fall back to a stale column
**Severity:** High · **Blast radius:** every multiples series

**Evidence.** The dossier reports "CIQ P/LTM EPS 16.0x" with a caveat that it "rests on normalized earnings." Both parts are wrong:

- 16.0x is the **2026-03-31** close of `P/LTM EPS` — a **GAAP** metric, four months stale
- The current value of that series is **NM** (LTM GAAP EPS is negative)
- The correct current normalized figure is **P/LTM Normalized EPS = 8.90x**
- Independent corroboration: Yahoo Finance carried a trailing P/E of 16.03 as of 2026-07-02 — the same stale metric

**Root cause.** `ciq.py` correctly refuses to coerce UNAVAILABLE cells to zero (`clean_num` → `None`), but the multiples-series reader walks backward to the last numeric cell. Backward-fill is the same class of error as coercion, arriving by a different route.

**Fix.** Propagate `NM` as UNKNOWN through series reads. No backward-fill on any time series.

**Acceptance test.** Series ending in `NM`; assert the reader returns UNKNOWN, not the prior value.

---

### P6 — Wrong extractor branch on spreadsheet inputs
**Severity:** Medium · **Blast radius:** every `.xls`/`.xlsx` non-financials workbook

**Evidence.** The dossier reports `Customers.xls: format biff_xls is not text — use read_sheets()` and records customer concentration as UNKNOWN. The file reads without error.

**Root cause.** `read_text()` called on a path classified `BIFF_XLS`. The error message in the dossier is `ciq.py`'s own fail-loud text, correctly raised — but the caller chose the wrong branch.

**Note.** The downstream conclusion was still right for a different reason: CIQ's Customers export lists named customers (Walmart, Amazon) with **no concentration percentages**. `Suppliers.xls` was never opened at all; it carries the Barclays / BMO / Goldman / SunTrust creditor group.

**Fix.** Route `BIFF_XLS` and `OOXML` to `read_sheets()`. Add `Suppliers` to `_WORKBOOK_KEYWORDS` consumers.

**Acceptance test.** Assert `read_sheets()` is reached for every workbook classified as a spreadsheet.

---

### P7 — Valuation inputs undisclosed and unreproducible
**Severity:** High · **Blast radius:** every scenario block

**Evidence.** The three scenario cells cannot be reproduced from any figure printed in the dossier. Solving the system yields:

| Input | Engine value (solved) | Disclosed in dossier | Management guidance |
|---|---:|---:|---:|
| D&A | $21.79M | not printed | — |
| Net debt | $326.81M | $325M | — |
| **Shares** | **93.77M** | **88.4605M** | **~90M** wtd avg diluted |

Verification: each cell reproduces to the cent with these inputs (bear $6.95, base $24.24, bull $40.21).

The share count is a weighted-average diluted figure applied to a forward per-share value while the company is retiring 11.7% of its equity. Using 88.46M raises the base to $25.72; using management's guided 90M gives $25.26. Direction: the target is **understated** by roughly $1.00–1.50/share.

**Root cause.** Weighted-average diluted used for forward per-share valuation; scenario inputs not surfaced.

**Fix.** Use current shares outstanding. **Print shares, D&A and net debt inside the scenario block** so the target is reproducible from the page alone.

**Acceptance test.** Assert every scenario value recomputes from figures printed in the same document.

---

### P8 — Consensus vintage drift within a single build
**Severity:** Medium · **Blast radius:** every name using consensus anchors

**Evidence.** CIQ Trends, FY2026 revenue: Current **1,352** · 1 month ago **1,334** · 3 months ago **1,334** · 12 months ago 1,500.

The dossier's base case is built on **1,334** and describes it as "consensus FY26E." Elsewhere in the same document it prints **1,351.8** as the consensus path anchor. Two vintages, one build, no reconciliation.

Valuation impact is small (~+$0.41/sh at current consensus) but the defect is systemic.

**Fix.** Single vintage per build, stamped once at the top of the document.

**Acceptance test.** Assert only one Trends vintage is referenced per build.

---

### P9 — Structural inference from sheet shape
**Severity:** Low · **Blast radius:** every segment read

**Evidence.** The dossier states the Segments sheet "has no EBITDA section as expected" and concludes brand-level profitability cannot be sized. The sheet **does** carry Operating Profit Before Tax and D&A by segment. The correct reason is that the company reports a **single reportable segment**.

Right conclusion, wrong cause. Same pattern as P6.

**Fix.** State filing-based reasons for data absence, not sheet-shape artefacts.

---

## B. Name-Level Analytical Defects

| # | Defect | Severity | Impact |
|---|---|---|---|
| **N1** | **Variant perception aimed at a consensus nobody holds.** The dossier's thesis is "overshoot over category decline." BellRing's FY2025 annual report describes category growth as robust and expects GLP-1 mainstreaming to *drive* penetration and category growth; its CEO calls better-for-you RTD shakes one of the fastest-growing CPG categories. SMPL's own CEO says the challenges are execution-driven rather than category-driven. The market is pricing **SMPL-specific share loss**, not category decline. | Critical | Removes the stated edge; requires re-specification as a share-loss thesis |
| **N2** | **Exit multiple 12.5x is 43% above peer median NTM (8.72x)** and unsupported outside the 2018–23 growth era. At today's 5.34x the base is $8.88; at peer parity $16.82; at 12.5x $25.71. | Critical | Drives 100% of the excess upside |
| **N3** | **Base revenue $1,330M equals consensus FY2028 ($1,331.0M) to 0.1%.** Not a conservative mid-cycle figure — the street's two-years-out number, against a 180-day ledger horizon. | High | Duration mismatch |
| **N4** | **Bear multiple 7.0x exceeds the 5.34x the market pays today** (below all 35 historical closes). The bear case embeds a 31% multiple re-rate while assuming operational deterioration. | High | Understates risk; $3.58 risk figure is soft |
| **N5** | **Surprise record inverted.** The dossier shows annual GAAP surprises ending FY2025 at −36%. The last three quarters beat normalized EPS by **+8.3%, +12.5%, +20.0%**, and Q3 beat revenue consensus by 7.3% and its own EBITDA guide by 14.5%. | High | Biases the bear leg |
| **N6** | **Governance gaps.** (a) 2026-04-21 cost-savings and leadership-change announcement — CHRO departing by 2026-06-01, CSCO separating — unreported. (b) Insider buying (90,000 sh, ~$1.1M) shown without the ~$12.36M of prior-year selling at ~$36–37, including 147,200 shares by the CEO. (c) Buybacks of ~$213M against $102.2M YTD operating cash flow (~2×) framed purely as a confidence signal; net debt rose $257M → $324.6M and cash fell $194.1M → $123.9M over two quarters. | High | Management section materially incomplete |
| **N7** | **Kill criteria thinner than the ledger's.** The V-row carries three measurable triggers (Quest ≤0% two consecutive quarters; FY26 guidance cut at Q4 print or initial FY27 below ~$1.30B; GM erosion beyond guided ~375bps or sustained GM below ~31%). The dossier carries one. | Medium | Monitoring degraded relative to the decision of record |

**Information regression — recorded in the V-row 2026-07-21, absent from the dossier 2026-07-24:**

| Fact | V-row text | Dossier |
|---|---|---|
| FY26 impairments | "YTD FY26 non-cash impairments $331.0M" | cites $60.9M (FY25) |
| Loan-basis leverage | "the 8-K's loan-basis reads 1.2x" | "covenant basis: UNKNOWN" |
| Q3 buyback pace | "~2.1M sh / ~$25M in the quarter" | share-count reduction only |

---

## C. Retractions — Auditor Flags That Were Wrong

Recorded for the avoidance of unnecessary rework.

### R1 — "3.83:1 headline contradicts 1.96:1 appendix cells"
**Retracted.** They are different objects. The headline uses the *recorded* bear leg ($6.95); the boundary cells are *combined-stress* tests ($3.54, $2.62) deliberately harsher than the bear leg. The parallel `V-IT-` ledger row confirms the convention explicitly. All six ratios reproduce exactly:

| Cell | Price | Normal margin | Base | Computed | Recorded |
|---|---|---|---|---:|---|
| A (1,100 × 8% × 6.0x → $3.54) | $10.92 | 15.5% | $26.90 | 2.17:1 | 2.17 clears |
| B (1,050 × 7% × 6.0x → $2.62) | $10.92 | 15.5% | $26.90 | 1.93:1 | 1.92 fails |
| A | $10.53 | 15.5% | $26.90 | 2.34:1 | ≈2.34 |
| B | $10.53 | 15.5% | $26.90 | 2.07:1 | ≈2.07 |
| A | $10.53 | 14.0% | $24.24 | 1.96:1 | ≈1.96 |
| B | $10.53 | 14.0% | $24.24 | 1.73:1 | ≈1.73 |

**What survives:** at entry one stress cell already failed (1.92:1, disclosed as "Known fragility, accepted"). On the re-set 14% normal **both** now fail. The downside envelope genuinely deteriorated between 21 and 27 July — which the WATCH disposition appears to reflect, and which the dossier states accurately.

### R2 — "EV computed on EBIT rather than EBITDA"
**Retracted.** The bridge is deliberate and correct. The V-row states "our normalized ~17.1% EBITDA-margin equivalent" against a 15.5% operating margin — an implied D&A of ~1.6% of revenue, or $21.8M, matching the solved engine value of $21.79M. What remains is only the mixed-basis issue in *setting* the 14% normal (P10-adjacent, see below).

### R3 — "Term loans rose $148M QoQ"
**Retracted.** Term loans were **396.7 (Nov-25) → 396.9 (Feb-26) → 397.0 (May-26)** — flat for three quarters. The 249.1 figure is the FY2025 year-end Capital Structure Details panel. The label "(249.1→397.0 QoQ)" is a period mismatch that makes a three-quarter-old financing event look current. Correct the label; the debt build is not new.

---

## D. Verified Correct — Do Not Change

This machinery reproduced exactly from source and is the platform's real strength.

| Component | Verification |
|---|---|
| Own-history multiple band | 35 closes, 2017-12-29 → 2026-06-30. Min **6.11**, max **28.88**, median **17.85**, p25 **15.20**, p75 **20.88**, current **5.34**. All match to 2dp |
| Percentile placements | 12.5x = **14.3%** (dossier: 14th); 16.0x = **28.6%** (dossier: ~29th) |
| Margin anchors | FY2020 **9.58%**, FY2022 **17.35%**, 7yr clean median **15.51%**, FY2025 ex-impairment **15.01%** — all exact on GAAP `OperatingIncomeLoss` including unusual items |
| Entry-boundary arithmetic | All six ratios exact (see R1) |
| EBIT→EBITDA bridge | Deliberate, documented, correct (see R2) |
| Transcript-sourced operating claims | Quest +1.1%, OWYN +3.6%, Atkins −24.6%, takeaway −6.7%, penetration 8.5%/−220bps, category +10%, HSD September price increase, chips +17%, milkshakes ~50% — **all verbatim** |
| Peer data | Hain cap $49.1M is real ($0.54/sh, independently confirmed at $0.56/$50.5M). Peer medians 7.85x LTM / 8.725x NTM both exact |
| Insider activity | 2 buys, 0 sells, 90,000 shares — independently confirmed |
| Base-vs-guidance claim | $1,330M **is** below the $1,345M guide floor. Conclusion holds, though the cited comparison figure was a stale vintage |
| Self-flagged caveats | Both analyst caveats are real, material, and honestly disclosed. The "[LLM-suggested, unverified]" twin labels were warranted — Medifast's terminal outcome verified independently (Q1 2026 revenue −34.3%, coaches −44.9%, FY26 guide $270–300M) |

**One methodological item not yet classified as a defect but worth a decision:** the base-margin derivation averages two different bases — the 15.51% median is GAAP-inclusive of unusuals, while the "~13.8% trailing" is CIQ clean EBIT. On the anchor basis LTM is **−17.05%**. The resulting 14% happens to be defensible, but the stated derivation does not hold together. Recommend standardising the adjustment policy across both ends of the anchor.

---

## E. Suggested Issue Order

| Order | Issues | Rationale |
|---:|---|---|
| 1 | **P4** (price staleness guard) | Cheapest fix, highest recurrence, and the exact defect the SMPL close row failed to remediate |
| 2 | **P2, P3** (guidance date selection, anchor staleness) | Same root class as P4 — no freshness contract between panels. Fix together |
| 3 | **P1** (materiality guard) | Highest single-defect severity; independent of the freshness work |
| 4 | **P7** (scenario input disclosure) | Makes every future target reproducible from the page; enables external audit |
| 5 | **P5, P6, P8, P9** | Mechanical, low-risk, well-covered by tests |
| 6 | **N1, N2** | Analytical policy: require a falsifiable variant-perception field; down-weight or window own-history multiples where the earnings regime has changed |
| 7 | **N3–N7** | Dossier template additions: earnings-vs-multiple decomposition, recent surprise record, governance events, ledger kill-criteria parity |

---

## F. Reference — Independent Valuation Under Corrected Inputs

Provided so the team can compare against a re-run. Priced at **$10.28** (CIQ close 2026-07-24), 88.5M shares, multiples anchored to the peer cross-section rather than own history.

| | Severe | Bear | Base | Bull |
|---|---:|---:|---:|---:|
| Revenue ($M) | 1,180 | 1,240 | 1,300 | 1,380 |
| EBITDA margin | 13.5% | 14.5% | 16.0% | 17.5% |
| EBITDA ($M) | 159.3 | 179.8 | 208.0 | 241.5 |
| Net debt ($M) | 360 | 340 | 325 | 300 |
| EV/EBITDA | 5.0x | 6.0x | 8.0x | 10.5x |
| **Value/share** | **$4.93** | **$8.35** | **$15.13** | **$25.26** |
| vs spot | −52.0% | −18.8% | +47.2% | +145.7% |
| Probability | 10% | 25% | 45% | 20% |

**Probability-weighted value $14.44 (+40.5%). Reward:risk 2.15:1** — versus 3.83:1 as published, a 44% reduction.

Street consensus for comparison: $14.88 (CIQ), $15.20 (MarketBeat, 13 analysts), $17.50 (Yahoo 1y target est). **The independent value lands on the street**, which is the quantitative statement of N1: once the multiple is set from evidence, there is no variant perception.

**Sensitivity, ranked:** exit multiple (±1.0x = ±$2.35/sh) ≫ EBITDA margin (±100bps = ±$1.18) > revenue (±$50M = ±$0.72) > net debt (±$25M = ±$0.28).

---

## G. Unresolved

| Item | Status |
|---|---|
| Close price 2026-07-27/28 | Retail quote sources conflict badly; best-evidenced recent price is $10.28 (CIQ, 2026-07-24) |
| Credit-agreement covenant terms | Never located. Low risk — loan-basis leverage of ~1.2x is disclosed on the Q2 call |
| FINRA short interest | Dossier's figure is primary-sourced; not independently re-verified |
| Twin outcomes: Central Garden & Pet, e.l.f. Beauty | Unverified (low materiality). Medifast, BellRing, Hain confirmed |
| Brand-level profitability | Not disclosed by the company anywhere — single reportable segment |
| Circana category data | The +10% category figure is management-sourced; verified as reported, not independently |
| Q4 FY26 buyback quantum | Unknown; determines year-end net debt and share count |
