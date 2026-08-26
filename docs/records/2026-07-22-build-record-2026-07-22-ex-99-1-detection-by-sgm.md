---
id: 
status: recorded
date: 2026-07-22
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-22 EX-99.1 detection by SGML TYPE + five-name re-assembly.** The
exhibit locator matched FILENAMES (`ex991`/`dex991`/`ex99_1`), so every other filer convention was
invisible: `a991_pressrelease…` (SMPL), `exhibit991…` (CNXC, NCNO), `exh991…` (BRBR), and EPAM's
`exhibit99_q1x2026` whose only "1" is the quarter — unclassifiable by ANY filename rule. Measured
over every 2.02/8.01 8-K of the eleven names: **24 of 53 press releases lost (45%)** across five
names, each silently — the fetch recorded nothing, and the What-broke card fell back to reciting
raw 8-K item text. Fixed by reading EDGAR's own `<TYPE>EX-99.1` from the filing SGML header
(HTML-escaped in `-index-headers.html`; filename match demoted to fallback when the header is
unreadable). Live re-check: **53/53 discovered**. Two side-findings closed with it: `mechanical.py`
carried a SECOND copy of the regex that had already DRIFTED (no `_` class → it missed `ex99_1.htm`
the other matched) — collapsed to one detector, pinned against recurrence; and a passing 8-K that
yields no exhibit now emits a QA flag instead of a silent zero. Re-assembled BRBR/CNXC/EPAM/NCNO/
SMPL: releases 1→4, 0→6, 0→4, 0→6, 0→5; operating-driver rows +22/+21/+28/0/+25; gap-down "what the
results showed" now present on CNXC, EPAM and SMPL (SMPL: `adj EBITDA Q2 2026 $55.5M`).
**LEAN FLIP:** BRBR strongly-bearish → mixed on 4× the evidence, so its machine proposal changed
AVOID_TERMINAL → none (no ledger entry existed; nothing invalidated). **VINTAGE:** the standing
CNXC/SMPL to-do is now CLOSED by this re-assembly — both widened 7→12 annual columns AND took
newer-export restatements (SMPL LTM net income −106 → −199, FCF 125 → 107; CNXC FCF 517 → 776),
with each synthesis regenerated against the new numbers. SMPL is a LIVE confirmed position
(entry $10.92) — its analysis text changed under an open position, deliberately and disclosed.

**PARSER COVERAGE — folded into the same PR (operator: "why can't we build that as part of 194").**
Recovering the RELEASES was not the same as reading them: the first pass left SMPL reading
`adj EBITDA Q2 2026 $55.5M` (a number, no reason) and BRBR with no drivers at all despite its
release stating the cause outright. Diagnosed across ALL five recovered texts (not one — the
sampling lesson): `_RECON` broke on a footnote marker (`Adjusted EBITDA*`) and demanded the word
"adjusted" (EPAM/CNXC write `Non-GAAP Diluted EPS`); `_ONEOFF` knew only impairment-family nouns,
missing the actual causes (`$11.3M inventory-related charge`, `$4.5M restructuring costs`);
`_GUIDE_RANGE` lacked `net sales`/`total revenues`, the `between X and Y` and bare-hyphen range
forms, and did not scale BILLIONS — CNXC's $2.465B printed as `2.465` beside VRRM's `985.0` ($M),
a magnitude error in a decision figure. All fixed and pinned on the verbatim sentences.
Yield per release: BRBR 0/0/0 → 1/1/2, SMPL 2/0/0 → 3/1/2, CNXC 2/0/1 → 4/0/1, EPAM 0/0/1 → 2/0/1,
NCNO 0/0/0 → 0/0/2 (recon/one-offs/guidance). Three quality bugs found and fixed IN the widening:
one-off duplicates (the same charge eight times at different roundings → dedup by noun phrase,
most precise mention wins), prior-year comparatives promoted as this period's cause (excluded), and
`operating income` bucketed as `adjusted NET income` by the metric normaliser — a mislabel, not a
rounding, so it got its own label. Composer: clause-boundary description trim (no more
"…charge associated with a") and `$M` units on guidance ranges.

**NCNO SYNTHESIS — 0 bull / 6 bear, SHIPPED FLAGGED, deliberately NOT re-rolled.** The final NCNO
synthesis emitted zero bull points under a lean that itself cites bullish evidence ("a genuine
margin/cash inflection and cheap forward multiples"). The false-balance guard fired and carries it
as an analyst caveat. Re-running the LLM until the content improved would be shopping for an
outcome — the discipline this fund exists to hold — so the caveat stands for the analyst to judge.
