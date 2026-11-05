---
id:
status: shipped
date: 2026-11-05
prs: [910]
supersedes:
superseded-by:
---

# Retired: the monitor's panel grid, the cost-of-borrowing panel and the commissioning reader — `vinci/panels*.py`, `vinci/borrowing.py`, `vinci/edgar/commissioning.py` and the app's Monitor panels view removed; STATE row 26 closed and row 5 cut to its two non-panel items (R3 of three retirements)

**WHAT.** This is R3 of the three retirement PRs from the operator's decision of 2026-11-04. R1
(#905, `3ad14793`) retired the calls tape, graph Test 0/1, the scale back-fill and triage. R2 (#908,
`7e9f6fa2`) retired `vinci.themes` and the CIQ charting reader. R3 retires the between-print
monitor's panel grid. The monitor day itself stays: its BUY−AVOID spread, its rows, the realized
returns and the freshness rows, with UNREAD PRINT and the next-print date. So do the decision log
that renders them and the measured kill criteria in the freshness rows. Removed:

| what | detail |
|---|---|
| the panel registry | `vinci/panels.py`, `panels_declare.py`, `panels_emit.py`, `panels_payload.py`, `panels_resolve.py`, `panels_universal.py`: 1,488 lines (`PanelSpec` / `PanelRegistry`, the universal seven, the cohort five, the declarations reader, the resolver, the payloads, the emitter) |
| the cost-of-borrowing panel | `vinci/borrowing.py` (183 lines); its one importer was `panels_payload` |
| the commissioning reader | `vinci/edgar/commissioning.py` (236 lines), the "built but not running" ratio; nothing outside its tests imported it |
| the monitor's grid | `_cmd_monitor`'s `emit_panels` call and its `PANEL GRID UNAVAILABLE` note; the `panels` field of `MonitorSnapshot` and its `PanelRow` import |
| the app's view | `frontend/views/shared/panels.js` (413 lines), its nav entry and route in `app.js`, and its `pn-*` block in `styles.css` (140 lines with its leading blank line) |
| data | the `panels` declarations of six names in `data/followed.json` (LLY, NFLX, UBER, V, GOOGL, TECX); every other field is byte-identical |
| tests | 6 files, 84 cases (`test_panels`, `test_panel_emit`, `test_panels_universal`, `test_cohort_five`, `test_commissioning_ratio`, `test_load_bearing_axis`); 3 of the 4 `tests/fixtures/commissioning/` files; the panels half of one render test. Six of the 84 pin behaviour this PR KEEPS and moved (**THE LOST PINS**, below) |

The GOOGL monitoring plan the panels were built from (`GOOGL_Monitoring_Plan_Plain_English.md`,
reviewed in `docs/records/2026-08-27-between-print-monitor-panels.md`) was never committed:
`git log --all` finds no such path. So the plan leaves as its code and its per-name declarations.

**Restore** by reverting #910's squash commit on `main`. That undoes every edit at once: the 18
deletions, the moved fixture and the edits to the kept files listed below. Copying the deleted files
back by hand is NOT a restore: the monitor needs its field and its emitter call, the app its route
and nav entry, and the six names their declarations. `git checkout 7e9f6fa2 -- <path>` is right only
for a DELETED path. `7e9f6fa2` (R2's merge) is the last `main` commit that holds the code.

**KEPT, on purpose.**

- **The `panels` block of every committed monitor day** from 2026-08-11 to 2026-11-02 (eight days,
  124 rows each: 105 universal, 13 cohort, 6 theme; on 2026-11-02, 68 ready and 56 refused). It
  is history. `MonitorSnapshot` ignores an unknown key, so the days still load, and
  `tests/test_total_return.py` validates every one of them. The mirror in `frontend/monitor/`
  keeps it too. Nothing renders it now.
- **`vinci/edgar/segments.py`**, the R-file segment reader `commissioning.py` was built on. It is
  MC2's extractor; STATE row 4 already records it as unwired, and says to delete or replace it
  separately. With `commissioning.py` gone, its `_pick_report` parameters (`topic`, `refine`,
  `what`, `absent_means`) have no caller but the default segment route; the guards on them stay
  pinned (below).
- **`tests/fixtures/tiingo_reserve/data/followed.json`**, a frozen copy of the follow list that still
  carries the `panels` key. The reader ignores the key, and the fixture is a copy of what the list
  held then.
- **The records** of the panel build (`docs/records/2026-08-27-between-print-monitor-panels.md`, the
  phase records of 2026-09-03 to 2026-09-10, `2026-09-10-load-bearing-axis-is-a-portfolio-property.md`)
  are immutable and stay as history.

**THE LOST PINS.** R2's deleted tests held the only pins on some kept behaviour, so all six files
were audited the same way. There are 84 test functions. **Statically:** does a test, through the
helpers, fixtures and constants it reaches, name anything this PR removes? **Empirically:** each
file ran against the head with its removed-module imports neutralised and the commissioning
fixtures restored. Four tests are static-clean and pass. Six more pass only because they read the
`panels` block of a committed day, which is history. Two tests that name removed code also pin a
kept fact no kept test pins. Those six moved: four verbatim, two cut to their kept half, each with a
docstring line naming where it came from. Each passes on the head and FAILS under a mutant of the
code it guards:

| pin (from) | now in | guards | mutant → result |
|---|---|---|---|
| `test_a_new_topic_must_state_its_own_absence_meaning_or_fail_loudly` (`test_panels`) | `tests/test_segment_economics.py` | `_pick_report`'s absence guard reads the topic, not the `what` label | guard keyed on `what` again → FAIL |
| `test_a_blank_absence_clause_is_the_same_hole_as_a_missing_one` (`test_panels`) | same | a blank `absent_means` is refused | blank check removed → FAIL |
| `test_the_segment_route_keeps_its_own_absence_meaning` (`test_commissioning_ratio`) | same | the segment route's refusal keeps its clause | default clause emptied → FAIL |
| `test_a_third_topic_cannot_inherit_the_segment_absence_story_by_forgetting_a_keyword` (`test_commissioning_ratio`) | same | every other topic must state its own clause | guard removed → FAIL |
| `test_the_repo_wide_pattern_refuses_a_filing_with_two_economics_reports` (the first half of `test_cohort_five::test_the_declared_note_name_resolves_what_the_repo_wide_pattern_cannot`) | same, with the summary it read (moved to `tests/fixtures/segments/`) | the default route refuses GOOGL's Q2 2026 10-Q, which carries two economics reports, rather than take one | first economics report taken → FAIL |
| `test_a_percent_display_cell_reads_through_the_shared_ciq_helper` (the two `clean_num` assertions of `test_cohort_five::test_the_coupon_cell_is_read_through_the_shared_ciq_helper`) | `tests/test_dossier.py` | `read_cell` reads "4.500%" as 4.5; the one pin on a `%` cell | `%` no longer stripped → FAIL |

The other 78 name removed code. Six of those pass only on the history: five `test_panel_emit`
checks of the committed `panels` block, and `test_load_bearing_axis`'s check of the 2026-08-11
day. `test_panel_emit`'s `test_a_snapshot_predating_the_grid_still_validates` asserted the removed
field. Its other half, that the pre-grid 2026-07-20 day loads, is pinned by
`tests/test_total_return.py`, which loads every committed day. `test_commissioning_ratio`'s
`test_the_report_is_resolved_by_name_because_its_number_moves` resolves commissioning's own PP&E
topic through its removed constants. The segment route's by-name resolution stays pinned by
`test_the_details_report_is_chosen_over_the_policy_note`. The two `panels.js` pins R2 moved into
`test_panel_emit.py` leave with `panels.js`, as R2's record said.

**Every kept file this PR edits** (each edit only where a removal forced it):

- `vinci/monitor.py`: the `PanelRow` import and the `panels` field are removed. A comment says the
  eight committed days still carry the block and load it as an unknown key. Two docstrings that
  named the grid as a reader of the measured rows (`MeasuredTriggerRow`, `write_snapshot`) are
  reworded.
- `vinci/cli.py`: `_cmd_monitor` no longer calls `emit_panels` and builds its day without `panels`.
- `vinci/edgar/segments.py`: one docstring names `commissioning.py` as the picker's retired other
  topic. Docstrings only, which the drift hash ignores.
- `data/followed.json`: the six `panels` declarations are removed by a text edit, so the file's
  other bytes (its mixed `—` escapes among them) are unchanged. `follow_records` never read the
  key; the assembler, the scoring baskets and the fact layer read the same records as before.
- `frontend/app.js`: the Monitor panels nav entry and route are removed.
- `frontend/assets/styles.css`: the `MONITOR PANELS (phase 6)` block (every `pn-*` rule and the
  `--pn-hot` token) is removed. Nothing else uses a `pn-` class.
- `docs/RUNBOOKS.md` §j: the monitor day no longer lists a panel grid. The **When** paragraph no
  longer says a red `test_panel_emit` corpus pin forces a new day; that pin is gone, so **an artifact
  pass no longer requires a monitor day.** The check list drops "the panel-emit pin is green". Two
  sentences on what a re-cut reads from today's pages name the measured rows instead of the panels.
- Tests that receive the moved pins: `tests/test_segment_economics.py` (gains `import re`) and
  `tests/test_dossier.py`.
- `tests/test_monitor_horizon_close.py`: the render test drops its third view, the panels page's
  `the_call`, and is renamed `test_the_two_views_label_a_resolved_mark_as_the_horizon_close_node`.
  Its decision-log and dossier assertions are unchanged.
- `tests/test_extraction_version_drift.py`: the `commissioning.py` row leaves the watched set. No
  version row is needed, because no page's output moves.

**PAGES.** No committed page embeds a panel. No `data/dossiers/*/dossier.json` carries a panel field
(`changes_the_call`, `render_config` or a panel tier), and the page renderer imports nothing from
the panel stack. So no page is re-rendered into the repo and no artifact pass follows.

**STATE.**

- **Row 26 is CLOSED.** Its concrete instance is removed: the universal multiple panel generalised
  GOOGL's load-bearing axis, and the per-name `load_bearing_axis` field (in `followed.json` and
  `PanelSpec.render_config`) fixed that. WST therefore has no axis to set. The row's
  portfolio-level point stands as a design rule for any future monitor: monitoring follows the
  load-bearing axis, so the axis is carried per name and never as universal text.
- **Row 5 is cut to what was never a panel.** Its panel-registry history, the cost-of-borrowing
  coverage floor (b) and the phase-5 and emitter ruling (c) go with the code. Two items stand,
  restated:
  - **(a)** the monitor's blindness to foreign private issuers (`vinci/cli.py:2589` pulls
    8-K/10-Q/10-K only), a decision-path change for its own PR;
  - row 6's four operator rulings of 2026-08-31, merged into row 5 on 2026-11-01, with their two
    open actions.
- **Row 6** has been empty since that merge.
- **Rows 11, 12 and 13 stay open.** They describe kept code:
  - row 11, the freshness rows' `stale_tags` scan (`monitor._stale_tags`);
  - row 12, the measured criteria and `vinci scenario-criterion`;
  - row 13, `triggers.evaluate`'s unchecked unit.

  R3 removes none of it. The panel payload was one more reader of the measured rows; the decision
  log still renders them.
- **§2** carries one three-line claim: every §2 line naming the removed modules describes removed
  code, restorable by reverting this PR.

**CLAUDE.md — for the operator's ruling, NOT edited here:** line 239, the **A TRUNCATED OUTPUT
PRINTS ITS OWN TRUNCATION** rule, cites "rendered panels (`vinci/panels_render.py` carried two…)".
That module was already replaced by `panels.js` in #603, and the panels it rendered are now gone.
The rule is general; only its last example is history.

**WHY.** The operator decided on 2026-11-04 to retire low-use features in three PRs; this is the third.
Measured at `7e9f6fa2`:

- The grid had ONE reader, the app's Monitor panels view.
- No decision path read it: screen, ranker, ledger, scoring, dossier assembly and render. Its only
  importers were `vinci/monitor.py`, for the field's type, and `_cmd_monitor`.
- `vinci/edgar/commissioning.py` had no importer outside its own tests. `vinci/borrowing.py` had one,
  `panels_payload`.
- On the latest committed day, 56 of the 124 rows are refusals.

**HOW VERIFIED.** Every run below is on this PR's code (local commit `689a7990`, squashed into the
PR's code commit) against `main` (`7e9f6fa2`).
`main` ran first; the branch ran on a clone of what `main`'s run left. Outputs are in the PR body.

- **The monitor day** — `vinci monitor --ref 2026-11-02 --out <scratch>`, on a clone of the cache
  R2's `main` run filled. `main`'s day carries 118 panels (R2 removed the 6 theme ones). Take that
  day and remove its `panels` key: what remains **equals this branch's day exactly**. That covers
  the spread (+73.96pp), the 5 rows, the 2 realized returns, the 9 freshness rows (7 UNREAD PRINT,
  9 with a next-print date) and the 4 notes. The two printouts are identical apart from the lines
  naming the code path and the output path; neither printed the grid.
- **Pages** — every committed page outside the six held packs (26 pages; BURL is skipped by name)
  re-rendered from its committed `dossier.json` with its committed record (`render_markdown`, no
  LLM, no extraction). Every render equals the committed `dossier.md`, on `main` and on the branch,
  and the two sets of renders are identical. `frontend/build.py` rebuilds every mirror and changes
  no committed file.
- **The weekly path — a `vinci run-weekly` replay of the 2026-10-16 run.** Inputs: that weekly's own
  store (`research-alpha-audit-bcba59/data/vinci.db`, APFS-cloned; md5 `9e727a63…` before and after)
  and a clone of the cache R2's `main` replay filled; every cached response is served whatever its
  age. `main` ran with misses allowed and needed none (0 misses, 95 s). The branch then ran with the
  network REFUSED (0 misses, 123 s). The result dicts are identical (436 G1/G2 survivors, 344
  candidates, 344 ranked, 69 structural flags). `data/snapshots` (85 files each) and `data/facts`
  are byte-identical.
- **The $0 pre-spend check** — `vinci dossier precheck` on GOOGL, VRRM and TJX, with the Anthropic
  key removed from the process, the assembler's CIQ copy (`mosaic-theory-ta/data/manual`) and a
  clone of its store. `main` and the branch print the same 87 lines once timestamps and paths are
  removed. GOOGL: 116 Sourced fields + 6 blocks, 0 regressions, 0 post-spend refusals, exit 0. TJX:
  the same, exit 0. VRRM: 0 regressions and its standing stale-export refusal, exit 1.
- **The app** — served on a fresh port from this branch's `frontend/`:
  - the nav lists Overview, Dossier, Decision log, Overshoot, Theme intelligence and the locked
    edges, with no Monitor panels;
  - `#/monitor-panels/GOOGL` falls back to the overview;
  - the decision log renders the 2026-11-02 spread, 7 "unread print" and 2 "current" freshness pills
    (the day's own `unread_print` values) and 9 next-print dates;
  - the console logs no error;
  - `node --check` passes on `app.js` and `views/shared/decision-log.js`.
- **The moved pins** — each passes on the head and fails under its mutant (table above). The mutant
  runner edits the real file, runs the pin and restores the file byte for byte.
- **Gate.** ruff: all checks passed. `mypy --strict vinci`: no issues in 183 source files (191 less
  the 8 removed modules). `pytest -m "not network"`: **8,747 passed, 0 failed**, 555 skipped, 8
  xfailed, 39 deselected, 421.7 s. That is `main`'s 8,825 (R2's final gate, the same tree) less the
  84 deleted cases plus the 6 moved pins.

**BOUNDARY.**

- Line counts: `git show 7e9f6fa2:<path> | wc -l`.
- Test counts: `pytest --collect-only -m "not network"` over a `git archive` of `7e9f6fa2`, with no
  parametrised cases in these files.
- The 84 audit functions: top-level `test_*` functions in the six files at `7e9f6fa2`.
- The 18 deletions: `git diff --name-status origin/main...HEAD`, status `D`, at this PR's head.
- Panel rows: the `panels` list of each committed `data/monitor/<day>.json`.
- Each run states its own inputs above.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The between-print panels are gone from `main`. The monitor
day still marks the book, computes the spread and flags unread prints and passed deadlines, but no
longer answers "what has happened to this name since it was underwritten, one panel per question".
An artifact pass no longer forces a new monitor day, so the latest day can trail a moved page. Its
marks do not depend on the pages, but its `measured` and `stale_tags` fields do, until the next
routine run. Falsifier: a page moves and a decision is made off a freshness row that a fresh run
would have changed. Restoring means reverting #910's squash commit.
