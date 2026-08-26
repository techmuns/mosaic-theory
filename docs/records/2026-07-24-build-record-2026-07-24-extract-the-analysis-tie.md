---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 EXTRACT THE ANALYSIS TIER INTO HELPERS (PR 2a — pure refactor).**
Prerequisite for the section-ordering pass. The two twin renderers had drifted STRUCTURALLY: the
web's `analysisTier` is a 14-line composition of 9 named calls, while the markdown equivalent was a
**201-line inline block inside `render_markdown` with 30 interleaved conditionals**. Reordering
that inline would have meant relocating 200 lines of conditional code in a diff no reviewer could
check — and the fact-inventory guard catches DROPPED facts, not a conditional that quietly stopped
firing. So the extraction ships first, on its own, where it is provable. BUILT: SEVEN helpers
mirroring the JS twin one-for-one — `_drawdown_idio_lines`, `_leverage_survival_lines`,
`_trajectory_section_lines`, `_valuation_section_lines`, `_peer_comps_lines`,
`_business_quality_lines`, `_argument_lines` — each carrying the JS function it twins in its
docstring. The analysis block is now **26 lines** and reads like `analysisTier`. NO reordering, NO
content change: PR 2b does the actual moves on top. VERIFICATION (the only one that matters for a
refactor): re-render all 11 md from committed JSON + rebuild the frontend ⇒ **zero artifact diff**;
the sole changed file is `render.py`. INCIDENT CAUGHT BY THAT CHECK: the first extraction pass
inserted the new defs between `@_endnote_scope` and `def render_markdown`, silently orphaning the
decorator onto a helper — the endnote ContextVar never opened, so EVERY citation fell back from
`[n]` to an inline `↳ ref` across all 11 dossiers. The byte-identity check caught it immediately.
**CORRECTION (review of PR #220):** the first version of this record claimed the suite "stayed
green and would NOT have caught it". That was FALSE and unverified — I never ran the suite in the
broken state. `tests/test_dossier.py::test_endnotes_complete_on_every_committed_dossier` asserts
`"↳" not in md` on every committed dossier and reddens immediately (89 fallbacks vs 0 expected).
The existing invariant DID cover this class; byte-identity caught it first, not alone.
Decorator reattached, re-verified.
Gate: ruff + `mypy --strict` clean · 1073 passed.
