---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-27 "HOW THESE NUMBERS WERE SET" — ENDNOTE CITES + ONE GRID.** Operator
spotted inline sources on a MAIN-BODY card and asked why, against the house convention. They were
right, and it was worse than a style slip: the card used NEITHER sanctioned citation mode.
`frontend/lib/cites.js` states two and says the choice is not stylistic — `withEndnotes()` for the
main body, `auditCitesInline()` for on-demand `<details>`. This card HARDCODED the source string
into the markup on BOTH twins, so no pass ever saw it. A RECURRENCE: cites.js was extracted out of
uw-card.js for this exact defect (its docstring names it), uw-card was fixed, and #222 then shipped
a NEW card that reintroduced it. Fixed to `citeMark`/`_cite`; the Appendix tier already wraps in
`withEndnotes("X", …)` so the markers number and list themselves with no plumbing, and DEDUPE for
free (AORT's street-revenue rows share one source — [X1] twice instead of the 60-char path twice).
DESIGN AUDIT that followed, operator-prompted ("data is simply added line by line"), measured
rather than eyeballed: the web rendered a flat `<ul>`, so 24 AORT values sat at 24 different x —
while the MD twin already used an aligned table, i.e. the twins diverged in STRUCTURE and the
markdown was the better-designed surface. Root cause was documented in the code: `dataTable` was
rejected because it right-aligns the SOURCE string as if numeric — a correct objection that
DISSOLVED once the source became an endnote. A 100%-width `.ref-table` was tried here and
REVERTED on operator challenge — the third correction of this build, and the sharpest. `.vs-table`
stretches because it is a MULTI-column comparison whose number columns must group right against one
wide label; a reference list is TWO columns, so 100% only opens a GULF. Measured on AORT: 603–785px
of empty space between a label and its own value stretched, against 149–243px content-sized — and
with rule-free rows there is nothing to carry the eye across it. Worse, the raggedness that
motivated the override (32%/34%/97%) was **SMPL ALONE**, caused by its 380-char malformed label;
clean records sit at 353–497px. I had generalised from the worst case and then written CSS to
compensate for one bad DATA row. Reverted to the K2 content-sized default, and the non-override is
now PINNED with the measurements so it is not "fixed" again. Axis heads
moved from a bare `<b>` to the house 12px in-card `.ds-title` used by briefCase/argument — the name,
its method prose and its data had all been 13px, three roles with no typographic step. TWO
CORRECTIONS TO MY OWN AUDIT, both caught by checking instead of assuming: (1) I proposed adding row
hairlines — styles.css carries an explicit "rows rule-free, tighter rhythm; the section head carries
the rule" policy applied to `.fact`, `.brief-snap-t` and `table.data tbody td` alike, so adding them
would have overridden a stated decision on preference; NOT done, and now PINNED so nobody adds them
later. (2) I argued per-axis (ragged) width was correct because the units differ — that conflated
unit comparability with GEOMETRY; the axis headings already separate the units. SENTENCE CASE
checked and left alone: 95 labels lowercase / 19 upper, and all 19 lead with an acronym or fiscal
token (LTM, FY2025, Q1-2026) — a consistent convention, not sloppiness. NOT FIXED, deliberately
out of scope and recorded for the schema decision: 14/118 references carry the LEG they anchor as
prose in `label` ("… — bear"); 3 carry an EXCLUSION flag ("— DEAD REGIME", "NOT a reference for
us") yet still render a value in the aligned numeric column, which now lends them authority the
data does not have; and SMPL's last multiple "reference" is a 380-char narrative with a sentence in
its `unit` — DIAGNOSED, not just flagged: `9afc554` (operator directive 2026-07-26) cut the base
margin 15.5%→14%, and the honest consequence was that two entry-boundary stress cells which used to
clear the fund's 2:1 bar now FAIL it (≈1.96 and ≈1.73). That is a real, important finding — and the
schema had NOWHERE to put it. An assumption axis offers only `method` (one sentence) and
`references[]` of `{label, value, unit, source}` scalars, so a two-number narrative finding was
poured into a reference row: the prose into `label`, cell A into `value`, and cell B smuggled into
`unit` (":1 (cell A at the re-set 14% normal; cell B ≈1.73)"). It is also filed under `multiple`
though it is a whole-record boundary finding, not a multiple reference. So this is a SCHEMA GAP
producing a data defect, the same class as the leg-in-label issue — structured meaning travelling
as display text because no field exists to hold it. The fix is a per-axis note/finding slot, not a
renderer accommodation. Labels are printed VERBATIM and never parsed — grouping by leg needs a FIELD, not a
regex over a display string. Verified: every removal from the md is the 3-column ref row or a
renumbered cite (0 unexplained across 6 dossiers), and all 74 distinct sources still resolve in the
rendered markdown. Four mutations caught (web inline revert · md column revert · width rule dropped
· row-rule policy overridden). Gate: ruff + `mypy --strict` clean · **1101 passed, 1 skipped**.
