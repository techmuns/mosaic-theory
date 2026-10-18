---
id: 2026-10-17-artifact-pass-desk-for-experts
status: shipped
date: 2026-10-17
prs: [741]
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished at 375d1dc5, so the app shows the redesign (#740)

**WHAT.** `python -m vinci.theme_intelligence publish --run R-20261016T163302Z-market` at main
375d1dc5 (#740 merged) into `frontend/theme-intelligence/`. The main app's Theme intelligence
section frames these pages, so this is the step that puts #740's redesign in front of the team
(`docs/records/2026-10-17-theme-intelligence-desk-for-experts.md`).

**WHY.** Operator instruction, 2026-10-17: "yes, move the pilot to main and republish".

**HOW.**
1. **The pilot checkout** (`.claude/worktrees/theme-intelligence`) moved from 6965d5b4 to
   375d1dc5. It was clean before and after. #740 changes no schema; the registry stays v7.
2. **The live registry was copied, never opened by the CLI.** The copy used SQLite's backup API
   on a read-only connection: integrity ok, 23 theses.
   - The live registry's checksum is `7c5840a55993419a4e7abf3846004afe`, the same before the
     copy, after it, and after publishing. It is also the value #738 recorded, so the pilot has
     not changed since.
3. **The run is the same one #738 published.** `R-20261016T163302Z-market` is still the pilot's
   latest run, so the data on the desk is unchanged; only the presentation moved.
4. **Published from the copy.** 79 files plus `index.json`, all inside
   `frontend/theme-intelligence/`. Nothing else in the repo changed.

**WHAT MOVED.**
- **The pages are #740's.** Every page is identical to the preview reviewed on #740 (the same run
  and code, from a copy taken the day before), except the "Generated …" timestamp. That covers 77
  differing files, with 0 differing lines once timestamps are ignored.
- **The redesign's elements, counted over the published site:**
  - This week: 2 groups (Moved 3, New 10), the retired-or-archived fold, and 13 "Missing:" lines;
  - Themes: 1 table, 23 rows and 13 "Missing:" lines;
  - Articles: 6 retired-or-archived folds;
  - thesis pages: 23 of 23 carry "What would change the call", and none carries raise or lower
    in the panel.
- **`desk.js` and `intel.css`** equal their generators (`desk_js()`, `app_css()`), the pin in
  `tests/test_duplicate_definitions.py`.

**HOW VERIFIED.**
- **Leak scan** of every published file: 0 files match local paths (`/Users/`, `/private/tmp`,
  `/home/`), key prefixes (`sk-ant-`, `ghp_`, `gho_`, `github_pat_`, `AKIA…`) or key or token
  assignments.
- **Suite.** ruff and `mypy --strict` clean. `pytest -m "not network"` on these published files:
  5858 passed, 513 skipped, 1 failed. The failure was this record's own empty `prs:` field
  (`test_a_shipped_record_names_the_pr_that_carried_it`). With #741 written in, the record and
  STATE lints plus the generated-file pin pass: 754 passed, 1 skipped.

**BOUNDARY.** 2026-10-17. Pilot registry `pilot-2026-10-12` (v7, 23 theses: 13 active, 10
archived), run `R-20261016T163302Z-market`, code at main 375d1dc5.

**WHAT IT COSTS / WHAT IS ACCEPTED.** None new. The desk goes live in the app on the deploy after
this merges.
