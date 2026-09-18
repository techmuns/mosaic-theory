---
id:
status: shipped
date: 2026-09-18
prs: [634]
supersedes:
superseded-by:
---

# Amazon's guidance and Westlake's EBITDA were never read; three pages go from "not cross-checked" to VERIFIED

**WHAT.** A cross-consistency sweep over all 22 committed pages (calendar, market-cap and leverage
arithmetic, bridge/balance-sheet coherence, display-cell vs structured-value agreement,
source-binding, cross-name contamination, release coverage) found that **27 of the 91 releases the
pages cite parse zero reconciliation AND zero guidance rows.** 23 are genuinely silent. 4 were real
misses, in exactly two names, and this record's PR fixes both:

1. **The guidance introducer had to follow the metric almost immediately**, so the most ordinary
   English shape a filer writes was invisible: Amazon's "Net sales **are expected to be** between
   $197.0 billion and $202.0 billion" (both 2026 releases) and EPAM's "revenues **will be** in the
   range of $1.410 billion". The auxiliary is now a spelled-out SLOT — never a wildcard gap, which
   is what once bound VITL's revenue guide to the adjusted-EBITDA range one clause later.
   `expected to range **from**` joined the range introducers.
2. **`_RECON` demanded a `non-GAAP`/`adjusted` prefix**, and Westlake names its reconciled non-GAAP
   measure plainly: "**EBITDA of $679 million** for the second quarter of 2026". The prefix is now
   optional for EBITDA **alone** — EBITDA is never a GAAP line item, while net income, operating
   income and EPS all have GAAP meanings and still require it.
3. **A guide's period is now read from the rest of its own clause**, cut at its comparison, and
   from the bullet lead-in above it. This was not optional: without it the widening emitted
   quarterly guides wearing annual labels, and `period_scope` reads that as a full year.

**WHY.** The primary-source tier is the one place the company speaks for itself. An empty panel
reads as "the company said nothing", which is a different claim from "we could not parse it" — and
the `no anchored pattern matched` flag fires on 27 releases, so the 4 that mattered did not stand
out.

**HOW VERIFIED.** All 91 releases re-fetched from EDGAR and re-parsed, old vs new: **20 rows added,
12 replaced, 0 lost.** Every added row was read against its own sentence. Releases parsing nothing:
27 → 23. End-to-end, with each page's own CIQ inputs:

| name | guide verification BEFORE | AFTER |
|---|---|---|
| AMZN | CIQ 197000–202000 vs release **NO NUMERIC OUTLOOK** | CIQ 197000–202000 vs release 197000–202000 → **VERIFIED** |
| EPAM | CIQ a LEVEL, release a CHANGE — NOT CROSS-CHECKED | 1410.0–1425.0 both sides → **VERIFIED** |
| NCNO | CIQ a QUARTER, release a YEAR — NOT CROSS-CHECKED | 157.75–159.75 both sides → **VERIFIED** |
| VITL | VERIFIED | VERIFIED (unchanged) |
| SMPL | NOT CROSS-CHECKED (genuinely different periods) | unchanged |
| WLK | no revenue guide (Westlake does not guide revenue) | unchanged — its gain is 6 EBITDA rows |

nCino's refusal was caused by the release-side mislabel alone: the two sources carried the SAME
numbers and disagreed only on the period. The period fix also corrects five nCino quarterly guides
that were labelled with a bare year — $142–144M against an FY near $580M, live on the page.

Three pins, each red on the baseline parser, built from verbatim sentences of the four filings.
Mutation battery: 7 mutations, 7 caught — removing the auxiliary slot, `to range from`, the EBITDA
lookahead, widening the prefix to every metric, and dropping each of the three period guards.

**BOUNDARY.** Population: the 91 `primary_source.releases` entries across all 22
`data/dossiers/*/dossier.json` at `origin/main` f4c4302, re-fetched from EDGAR 2026-09-18. The
witness test that found the 4 misses covers TWO vocabularies — `<metric> is/are expected to be
between $X` and a prefix-free `EBITDA of $X million` — so "23 genuinely silent" means silent in
those two, not in every phrasing a filer could use.

**WHAT IT COSTS / WHAT IS ACCEPTED — the guides deliberately NOT shipped.** Adding `operating
income` and the prefix-free per-share forms to the guidance vocabulary extracts **22 more real
ranges**: Amazon's operating-income guide (the most-read number in that release), EPAM's GAAP
diluted EPS, Concentrix's and nCino's operating income, Uber's non-GAAP EPS. Every one of them
states its period in a bullet-list HEADER that the clause cannot reach, so all 22 land on the
`next-fy` default — which `period_scope` reads as ANNUAL. A quarterly guide wearing an annual label
is a ~4x error in a decision figure, so the vocabulary was held where it was. Unblocking them needs
a period source above the clause; the falsifier is simple — if a bullet-list header can be resolved
without crossing into a neighbouring section, the 22 become shippable.

Also recorded, not fixed: **the price box and the CIQ valuation block sit up to 42 days apart.**
#625 moved `prices.last` and the EDGAR P/E to the latest stored close; the CIQ block (market cap,
implied equity, peer grid) stays at its export's as-of, as it must. Both are stamped and the CIQ
block is internally coherent — but price × shares vs the displayed cap diverges by **+57% (MVST),
+27% (BRBR), +22% (VITL), −17% (EPAM), −12% (NCNO)**; 14 of 22 pages by more than 2%. AMZN, PARR
and WLK are exact, being the freshly-pulled names. And **UBER's capital-structure panel is a quarter
behind its own balance sheet** — summary `Q1 Mar-31-2026` total debt $12,419M vs $14,731M at Q2.

Checks that fired ZERO times fleet-wide, and are therefore UNPROVEN rather than clean: the
cross-name CIQ contamination check and the unsourced-present-value check.
