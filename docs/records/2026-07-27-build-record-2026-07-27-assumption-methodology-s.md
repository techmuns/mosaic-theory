---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-27 ASSUMPTION METHODOLOGY SURFACED + BRIEF RE-ORDER (PR 3).** Completes
the report re-structure. (1) **"How these numbers were set" — the framework's addition #1, now
built.** Schema 1.1 has captured per-AXIS methodology on every underwrite record since it shipped —
a method sentence plus the SOURCE-BOUND reference points each leg was chosen against — and NOTHING
rendered it: the reviewable "why these numbers" was committed and shown to nobody (0 of 12 in the
PDF, 1 of 12 on the web, that one being the multiple's median on a small Method tile). It renders
in the APPENDIX, first, because it audits the ANALYST's inputs and everything below it is
machine-assembled; the legs and their reasons already render in the Brief grid. An UNRATIFIED axis
is badged — the record distinguishes a method the analyst stood behind from one that merely shipped
with the run, and the card already encoded this as `unratified` (emitted only when true, so a
ratified axis stays byte-identical): NO build.py change was needed, unlike the #216 dated-triggers
case. Reference values render display-natural via a new twinned `_ref_value`/`refValue` — a currency
unit PREFIXES its symbol ("$1,450.9M"), because the record stores value and unit separately and
"1450.9$M" is not a number anyone reads. (2) **BRIEF RE-ORDER**: "What happened — and can it
survive?" now PRECEDES the scenario grid in both twins; the reader was meeting the valuation before
the problem it values. VERIFIED: rendered on real committed data in both twins (SMPL: 3 axes, 12
references, all sources intact; AORT: 4 axes incl. R2's horizon); fact inventory unchanged (0 lost,
0 gained); md and web brief orders match. INVARIANT:
`test_assumption_methodology_renders_in_both_twins_e2e` pins presence + APPENDIX tier + every axis's
method + every reference's SOURCE, in both twins, across every committed record that has
assumptions — mutation-tested (dropping either call site reddens it). The JS half UNESCAPES before
comparing: `escapeHtml` encodes the apostrophe in AORT's "the street's FY2027 figure", so a raw
substring check failed on correct output — a fixture trap of the same family as #216's. **REVIEW FIXES (blocking + 2 minor).** The formatter twins DID NOT agree — py `,.6g` against a
bare js `toLocaleString`, and THREE committed references already rendered differently in the PDF
and on the web (EPAM $5,555.43 vs $5,555.425; IT $6,474.14 vs $6,474.137; SMPL $1,416.21 vs
$1,416.208). Two traps were reachable: `g` flips to SCIENTIFIC at 1e6 ("$1.23457e+06M" in a PDF),
and `toLocaleString`'s default 3-fraction-digit cap silently rounds a non-zero source-bound value
to "$0M" — the fabrication class. BOTH twins rewritten to fixed 6 decimals + trailing trim + manual
grouping (never scientific, never a rounded-away non-zero) and pinned by
`test_ref_value_py_js_parity` over EVERY committed reference value plus the pathological set. I had
written these as "twins" without ever comparing their output — the repo carries 7+ py↔js parity
pins precisely for this, and the new test compared no VALUE between surfaces. Also fixed: analyst
free text is now pipe-escaped in the md reference TABLE (GFM splits on `|` before inline parsing,
so a pipe silently shifts cells and DROPS the source — backticks do not protect it; 0 committed
labels contain one today), and the ratification badge now reads `ratified_by` in BOTH twins (py had
used the `ratified` DATE while the card derives `unratified` from `ratified_by`, so a record
setting only one would show DRAFT on one surface and ratified on the other). Test tightened: the
web half loops EVERY record (was `names[0]`), `all(sources)` is no longer vacuous on an empty list,
and absent node SKIPS rather than silently returning. Gate: ruff + `mypy --strict` clean · 1076
passed.
