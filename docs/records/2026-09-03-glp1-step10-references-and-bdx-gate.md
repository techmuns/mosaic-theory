---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# Step-10 reference distributions, the revision-drift width — and BDX fails its gate

**BOUNDARY.** Source: operator's CIQ exports read 2026-09-03 through `CiqBundle`. Multiple history =
`Financials→Multiples` `P/NTM EPS` **Close, settled quarters, n=38**, current excluded. Revision drift
= `Estimates→Trends` consensus vintages. Transcript quotes are verbatim from the exports named. USD.
No raw CIQ committed.

## A population ruling is needed before the multiple table is used

The operator's figures and mine differ because they are **different populations**, not different
arithmetic — reproduced both:

| WST basis | n | P15 | P25 | med | P75 | P85 | rank |
|---|---|---|---|---|---|---|---|
| daily charting | 2,511 | 33.1 | 34.6 | 39.7 | 46.2 | 49.4 | 40% |
| **quarterly settled** | **38** | 33.2 | 34.5 | **41.7** | 45.9 | 51.0 | **37%** |

**The quarterly basis is the one to use, for two reasons that are not preference.** It is the GOOGL
precedent — that memo states *"38 settled quarter-end observations"* — and, decisively, **BDX and MCK
have no charting export**, so quarterly is the only basis available for all four. A table mixing
bases across names would not be comparable.

### Reference distributions, quarterly settled, all four

| | n | P15 | P25 | med | P75 | P85 | current | rank |
|---|---|---|---|---|---|---|---|---|
| WST | 38 | 33.2 | 34.5 | 41.7 | 45.9 | 51.0 | 36.9 | 37% |
| WAT | 38 | 21.7 | 22.9 | 24.5 | 27.8 | 29.1 | 26.4 | 63% |
| BDX | 38 | 15.8 | 18.5 | 19.7 | 20.5 | 21.2 | 14.2 | 13% |
| MCK | 38 | 9.4 | 10.0 | 13.1 | 16.2 | 18.5 | 19.9 | 95% |

**This is a reference distribution, not a scenario generator.** Setting base = own median bakes in
mean reversion: WST's median implies **+13% multiple expansion** before any earnings growth, WAT's
**−7%**, MCK at the 95th would assume a large de-rating and BDX at the 13th a large re-rating — which
would make BDX screen well for purely mechanical reasons. Each multiple needs a stated reason, and a
departure from history needs the business reason. **The GOOGL precedent also caps how much weight this
table can carry: its own quartiles are recorded as `BASIS MATCH: LIMITED` — "valuation context, not
load-bearing evidence" — because the workbook does not prove historical `P/NTM EPS` shares the
normalized denominator the current figure uses. The same limitation applies here and should be
restated per name.**

## Revision drift — an empirical width, instead of picking ±X%

Consensus for the exit-year FY, 18 months ago versus now:

| | FY2027 drift | FY2026 drift | shape |
|---|---|---|---|
| **WST** | **+24.2%** (8.02 → 9.96) | +26.6% | steady climb |
| MCK | +7.9% (41.36 → 44.62) | — | steady |
| WAT | +5.9% (15.63 → 16.55) | +3.3% | flat |
| **BDX** | **−21.0%** (16.82 → 13.29) | −18.9% | **discrete reset between 9m and 6m ago** |

The realized 18-month move is the honest scale for a bear/bull spread on a ~5-quarter horizon, and it
is **name-specific and directional** — WST's Street has been raising 24%/18m while BDX's cut 21%. A
symmetric ±12% would misdescribe every one of them.

*Limitation: `Trends` carries vintages only to 18 months, so this is the drift of a live forecast, not
a multi-year realized-error series. The workbook does not support the latter.*

## BDX FAILS the gate — recommend dropping it to three names

The screen is **materiality WITHOUT premium**. BDX passes the premium half and **fails materiality**,
which is the prong it was never tested on.

**Its own transcripts give agreement COUNTS, never a figure:**

> Q3 2026: *"We're achieving high win rates across the biologics market, including GLP-1s, and we now
> have approximately 100 agreements signed across novel and biosimilar GLP-1 programs."*
> Q2 2026: *"we secured several significant long-term customer wins, including two next-generation
> GLP-1 programs"*

And the segment carrying it is barely moving: **"BioPharma Systems declined 1[%]"** (Q2), **"grew
5[%]"** (Q3), mid-teens excluding vaccines. Against the other three — WST 18% of net sales, WAT
"grew over 40% this quarter", MCK ~$15bn quarterly — **BDX has no quantified GLP-1 economic at all.**

**And the cheapness is explained.** 13th percentile with −18% to peers sits alongside FY27 consensus
cut **16.82 → 13.29 (−21%)** in a discrete reset, **shares +27%** (224m → 283m) and **net debt +245%**
(4,670 → 16,099). The de-rating and the estimate collapse are the same event. Cheap because
expectations fell, not because exposure is unpriced.

**Recommendation: gate BDX out and underwrite WST, WAT, MCK.** The judgement is the operator's; the
evidence is that it entered the shortlist on prose beside two names carrying figures, and the figure
never arrived.

## WAT's non-filing source_ref, verbatim

Confirmed in `Waters Corporation, Q2 2026 Earnings Call, Aug 04, 2026`:

> *"GLP-1 testing part of the business grew over 40% this quarter."*
> *"In fact, moving ahead of what we had promised on the GLP-1 testing contribution."*

The `source_ref` must cite that transcript. The 10-Q reports the line blended, so a filings-anchored
reader does not find it.

## `scenario-propose` is NOT a one-liner — hand-correct instead

It is built on `AXES = ("revenue", "margin", "multiple")`, threaded through `ANCHORED`, the
per-cell reason table and cell construction. **R3 is two-axis** (`EPS × forward P/E`), so an R3
proposer means a recipe-dependent axis set through all of it. Three hand-corrections are cheaper than
that build, exactly as the operator judged.

## Known-wrong artifact, recorded because git log is permanent

The squash title of **#586** reads *"the peer spread widens against instruments, not containment"*.
**That is contradicted by its own record body**, which was corrected before merge: the widening is
broad-based, and the CRO subset flips sign on whether Illumina is included. The title cannot be
amended without a force push over merged history. **The record body is authoritative; the commit
title is known-wrong.**
