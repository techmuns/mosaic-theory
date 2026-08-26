---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-27 SCHEMA 1.3 — FIELDED REFERENCES (ratified proposal built; one PR).**
The four ratified decisions executed exactly (docs/refpoint_schema_proposal.md header): census
role list · one tag · archive sealed · one PR. MODEL: `RefPoint` gains `role` (validated against
`REF_ROLES`, 14 members, every one census-evidenced), `leg` (bear/base/bull Literal), `excluded` +
`excluded_reason` (pair-coherent both directions, margin/margin_basis precedent); new `AxisNote`
(text + ISO date + optional source) on `AssumptionDerivation.notes`. GATE: `require_fielded_refs`
— forward-binding from `FIELDED_REFS_FROM = "1.3"` exactly like `BASIS_REQUIRED_FROM` — REFUSES a
1.3 label carrying a leg token or an exclusion token, and any unit outside `REF_UNITS` (the 8
units in legitimate committed use; the smuggled-sentence unit becomes unrepresentable). Narrowing
recorded with its real sentence, prose_lint convention: "stated, not derived" is PROVENANCE
(AORT's street margins), NOT an exclusion token — my first regex wrongly caught it. `_schema_ver`
extracted and shared by both gates (the inner `_ver` copy retired). LINTER: `lint_record` now
scans `references[].label`, `excluded_reason` and `notes[].text` (flag-only, as everywhere) —
closing the blind spot where its own banned vocabulary sat 26 times, incl. the explicitly-banned
"DEAD REGIME". MIGRATION: 35 hand-authored row edits across all 7 live records (worklist printed,
each edit read individually — NO regex transform ever touched a label; json round-trip proven
byte-stable first), all bumped 1.2→1.3 after verifying every record carries bear_basis. SMPL
multiple[5] — the 380-char smuggled finding — became two honest references (cell A 1.96:1, cell B
1.73:1) + one dated AxisNote carrying the narrative VERBATIM; archived SMPL-2026-07-21 untouched
(sealed, ratified). CONSUMERS: uw-card's masthead median now selects `role === "median" &&
!excluded` — the label regex is DELETED, not kept as fallback; **verified live: MVST's masthead
reads "base exit 7.9×" with NO "vs 14.5× median"** (the wrong peer-median comparator is gone;
an untagged legacy record honestly shows no sub-line). build.py emits role/leg/excluded/
excludedReason/notes (only when set — legacy refs byte-identical); theme embed re-embedded via
`refresh_theme_cards()`; `_schema.json` regenerated. RENDER, both twins: leg chips FROM FIELDS
(labels never parsed), excluded rows dimmed/struck with the reason stated ("NOT a reference for
us" no longer borrows the aligned column's authority), notes render dated. PINS: 4 model-layer
(validators; gate refusals with the real committed shapes; narrowings-stay-legal on the AORT
sentence; e2e every-committed-record-passes-the-gate + migration-population floors) + masthead
behaviour on a FROZEN fixture (the MVST shape ⇒ NO sub-line; clean median ⇒ selected; legacy ⇒
honest absence — living-mirror tags are analyst data, so the fixture is frozen by design) + a
conditional-invariant e2e (IF a record declares a tag THEN both surfaces and the mirror show it —
re-underwrites cannot redden it). SIX mutations caught: label-regex revert · excluded-median
selected · gate floor raised · emitter drops excluded · (earlier pair on the endnote/table pins).
Gate: ruff + `mypy --strict` clean · **1114 passed, 1 skipped** — the pre-existing suite survived
the migration with ZERO test edits (the three initial reds were stale derived artifacts:
`_schema.json`, mirrors, theme embed — all regenerated via their sanctioned paths). Queue item 16
DISCHARGED; queue item 2's generating-cells half partially discharged (the boundary cells now
live structurally beside their narrative). ACCEPTED RISK, recorded at review (pre-existing class,
1cf191d precedent): the migration wrote MINIMAL diffs (new keys only where set), so the NEXT
programmatic `write_record` of a migrated record (the refresh path) will materialize `role:
null / leg: null / excluded: false / excluded_reason: null` on every untagged reference — ~156
mechanical lines on SMPL, no value moved. Committed records already carry such
materialized-optional keys from past writes (`years_to_terminal` on R1 rows), so this joins an
accepted class rather than opening one; FALSIFIER: if a materializing write ever changes a VALUE
(not just adds a null key), the acceptance is void and the write path gets a byte-preserving
mode.
