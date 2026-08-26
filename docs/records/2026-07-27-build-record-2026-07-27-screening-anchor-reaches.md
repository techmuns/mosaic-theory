---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-27 SCREENING ANCHOR REACHES THE MARKDOWN TWIN (audit Q1).** The
post-restructure structural read asked whether any section needs redesign against the full
buy-side architecture. ANSWER: no re-ordering — the tier map is right and #221 settled it — but
measuring per-section COVERAGE across all 11 committed dossiers surfaced a twin divergence that
ordering work would never have found. `anchorInner()` (dossier.js) rendered the screening ANCHOR
for all 11 names; `render.py` had **no screening renderer at all**, so the block reached ZERO
committed `.md` files. SCOPE, CORRECTED 2026-07-27 after a live preview — the first three
statements of this build (PR #227's body, this record, and two docstrings) all said "every PDF
omitted it", and that was WRONG. The download menu offers three scopes and the PDF ones are
**`window.print()` on the WEB page**, which has always rendered `anchorInner`; only `Full dossier
MD` fetches the committed `.md`. So a reader printing to PDF from the browser DID see the anchor.
What lacked it was the **markdown export and the committed `.md` record** — a real deliverable and
the artifact the repo keeps, but NOT the PDF. The fix and its pins stand unchanged; only the blast
radius was overstated, and the overstatement is recorded rather than quietly edited away. This was
never limited to the no-scenario path — every name lost it from the markdown. The loss is WORST on the five names carrying no
scenario card (BRBR, CNXC, FUBO, VITL, VRRM), where the anchor is the ONLY valuation LEVEL in the
document — `Valuation — first cut` is relative-only by the ImpliedValuation fence — and on the two
INAPPLICABLE anchors (VITL, FUBO) it also swallowed the DIAGNOSTIC saying why no screen value
exists (a failed coherence guard; a missing own-history multiple). Three of the five carry a real
base: CNXC $62.33 firm, BRBR $55.41 firm, VRRM $21.40 weak. Shipped `_screening_context_lines()`,
a field-for-field twin of `anchorInner`, appended to `## Scenario analysis` in both twins — and the
section now RENDERS when only the anchor exists, stating `_no scenario record for this name_`
exactly as the web does. Saying "not underwritten" IS the fail-honest behaviour; a silently shorter
PDF was the failure mode. FENCE HELD: the base renders as a LEVEL labelled spot-independent, never
differenced against price — guarded by a negative pin that scans the renderer's CODE (not its
docstring, which necessarily names every forbidden word) and rejects any signed % in the block;
mutation-tested both directions (renderer-absent ⇒ 2 pins red; implied-upside ⇒ fence red).
TEST-LAYER: two committed tests had pinned the DIVERGENCE rather than a property and were amended
with the reason recorded in-place — `test_md_without_a_card_*` asserted the section was ABSENT
(that WAS the bug), and the proposal test used the section header as a PROXY for the proposal being
hidden (now asserts the proposal TEXT is absent — strictly stronger). Artifacts re-rendered from
committed JSON with a line-diff check: **+11..23 lines, ZERO removed, on all 11** — the check that
would have caught #220's orphaned decorator. Gate: ruff + `mypy --strict` clean · **1092 passed,
1 skipped**.
