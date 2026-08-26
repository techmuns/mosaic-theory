---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-23 gap-card quality pass (the three audit leftovers).**
(1) BRBR quarterly figures were labelled with the YEAR: `_release_period` expected "Quarter of 2026"
but BellRing writes "Quarter of Fiscal Year 2026", so it fell to the bare-year fallback →
"adj EBITDA 2026" was really Q2. Handled the FY phrasing; scoped the re-assembly EMPIRICALLY
(composed the fresh driver offline for every flagged name — only BRBR and SMPL actually change; FUBO's
"2026" is a genuine full-year figure, CNXC's gap driver was already Q2). (2) SMPL listed the SAME
OWYN integration expense twice ($3.9M quarter, $6.5M YTD, worded identically) and a dangling
"restructuring costs, integration expenses of": the one-off dedup now collapses byte-identical full
descriptions (keeping the first/quarter) while the amount-aware path still keeps distinct qualifiers
($12M European vs $30M Asia), and the description trims at the first comma + strips a trailing
preposition. (3) One 8-K explaining two consecutive gap-downs rendered its whole block twice
(SMPL 04-09/04-10, CNXC 02-11/02-12) — the md even printed "gap 04-10 → 04-09" like a date error;
both renderers now GROUP by accession, one card naming every gap-down ("filed Apr 9 (for the
2026-04-09 and 2026-04-10 gap-downs)"). Display-tier for CNXC (md re-render only, no re-assembly).
Verified live (SMPL: 1 filing card, both dates named, zero console errors). Gate green: 1026 passed.
The synthesis-overwrite incident recurred on BRBR (REWRITTEN but synth=NO) — caught by the
assembled_at+synth check, restored from git, retried clean.
(4) BRBR's 2026-02-03 gap 8-K carried ONLY Item 5.07 (annual-meeting vote) — an administrative
filing that cannot explain a de-rate. The shape line leaked the Python list repr (`non-narrative
items ['5.07']`) and the card recited the vote text (the human flagged: "this text doesn't explain
the gap"). Split 8-K items into explanatory (`_EXPLANATORY_ITEMS` = the `_CAUSE_BY_ITEM` keys; 5.02
management-change stays IN) vs administrative; an admin-only gap now reads the honest
`no earnings/guidance filing (annual-meeting 8-K only)` (mirrors the `no company filing` treatment),
and a new `FilingRef.explanatory` flag (default True, back-compatible) makes BOTH renderers suppress
the non-explanatory card — the filing ref STAYS in JSON (three-tier: fact preserved, noise removed).
The md header is now gated on ≥1 explanatory filing (no dangling heading). Only BRBR is affected
across the 11 names; re-assembled with synthesis verified present. Verified live (BRBR: shape reads
the honest label, 1 filing card = the real 2026-05-05 earnings 2.02, vote text gone, no list repr).
Gate green: 1028 passed. INVARIANT: a deterministic unit pin (`_is_explanatory`/`_gap_label` on item
codes) + a committed-artifact e2e (5.07 card suppressed, 2.02 card kept) on both renderers.
