---
id:
status: shipped
date: 2026-11-13
prs: [1057]
supersedes:
superseded-by:
---

# A retrospective's composite scorer checkout also takes main's `vinci/graph/llm.py`: since #1049 the harness imports `sdk_version` from it, and #953's composite did not import without it

**WHAT.** RUNBOOKS §n's composite checkout for a retrospective panel check is now: BASE checked
out, then `git checkout origin/main -- vinci/evals docs/evals tests/fixtures/synthesis_gold
vinci/graph/llm.py`. §n also gives the check to run before registering: import every
`vinci.evals` module from the composite.

**WHY.** #953's retrospective (prepared 2026-11-13, not registered) built the composite as §n
said. At main `01ab6923`, `vinci/evals/replay.py` imports `sdk_version` from `vinci.graph.llm` at
module top (#1049: the ledger stamps each draw's SDK version), and #953's BASE `586fdcfd` has no
such name, so the harness did not import. The coordinator approved the fix on 2026-11-13 as harness
plumbing. `llm.py` is in neither `PRODUCTION_SCORER_FILES` nor `HARNESS_SCORER_FILES`, so the
scorer fingerprint does not move.

**HOW VERIFIED.**
- **Names, not the closure.** At main `01ab6923` against `586fdcfd`:
  - `vinci/evals/`'s static import closure (`vinci.impact.graph`) reaches 124 modules outside
    `vinci/evals`, and 50 of them differ from BASE. That is production code the composite keeps at
    BASE on purpose, so the closure is the wrong unit.
  - Of the 33 production names `vinci/evals/` imports directly (AST of every `from vinci.… import`),
    BASE lacks 2: `vinci.graph.llm.sdk_version` (top of `replay.py`) and
    `vinci.dossier.ciq.workbook_kind` (inside `replay.comps_export`, which only a frozen-page replay
    with a comps transform reaches, never `register --from-impact`).
  - Main's `llm.py` imports four `vinci.config` names (`LLM_PRICE_PER_MTOK`, `Config`, `get_config`,
    `require_env`), and BASE defines all four.
- **The check, run both ways:**
  - importing all 14 `vinci.evals` modules passes on #953's composite;
  - on a scratch copy with BASE's `llm.py` it fails, naming `sdk_version`;
  - `register --help` exits 0 on that broken copy, because argparse exits before the harness
    imports, so it is not a check.
- **With main's `llm.py`, #953's $0 dry check passes:** the export reads, the fixed scorer is
  accepted, 0 of 11 distinct request pins were drawn before, and 12 of 12 layers parse under BASE's
  schema.

**BOUNDARY.**
- **Commits:** main `01ab6923` (harness) and #953's BASE `586fdcfd`, read 2026-11-13.
- **The names:** "33" counts the distinct (module, name) pairs that `vinci/evals/*.py` imports from
  `vinci.*` outside `vinci.evals`, across 10 modules. "Lacks" means BASE's module file neither
  defines nor imports the name, and has no submodule of that name.
- **The closure:** "124" and "50" count modules in `vinci.impact.graph`'s static closure of the 16
  `vinci.evals` modules, and those whose file differs at BASE or is missing there.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A lazy missing name is not caught by the import check.** `workbook_kind` would fail only when
  a comps-transform replay ran at such a composite.
- **Proposed, not built:** a harness that names its production imports, with a test against each
  composite's BASE, would turn the check into a refusal.
