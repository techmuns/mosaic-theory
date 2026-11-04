---
id:
status: shipped
date: 2026-11-04
prs: [905]
supersedes:
superseded-by:
---

# Retired: the calls tape, graph Test 0/1's code, the CIQ scale back-fill and the triage pass — removed with their tests and data, each restorable from `481e82f7` (R1 of three retirements)

**WHAT.** The operator decided on 2026-11-04 to retire four low-use features. This is the first of
three retirement PRs (R1; R2 retires `vinci.themes`, R3 the between-print panels). Removed:

| feature | code | data | tests (cases collected at `481e82f7`) |
|---|---|---|---|
| the calls tape (scoring a public commentator's posted calls) | `vinci/calls/` (7 modules, 841 lines); the `vinci calls` command group (`accounts`, `fetch-bars`, `score`, `import-labels`); `frontend/views/calls/tape.js`, `frontend/lib/callscore.js`, the tape's nav entry and route in `frontend/app.js`, its candle primitives in `frontend/lib/exhibit.js`, its CSS block, and `frontend/build.py`'s `_mirror_calls` | `data/calls/` (247 files) and its mirror `frontend/calls/` (247 files); the `.gitignore` carve-out | 66, in six `tests/test_calls_*.py` files |
| graph Test 0 / Test 1 (falsified 2026-07; STATE §3) | `vinci/graph/test0.py`, `vinci/graph/test1.py`, the `vinci graph-test0` command, `scripts/run_test1.py`, `scripts/run_test1_xsector.py` | none committed (`data/graph_test0.json` was git-ignored) | 5 of `tests/test_graph.py`'s 12 |
| the CIQ scale back-fill (a one-off, run 2026-10-27) | `vinci/dossier/ciq_scale_backfill.py` | none | 1 of `tests/test_ciq_balance_scale_outcome.py`'s 7 |
| the triage pass (de-rating causes by 8-K item code, 2026-08-28, never wired into the ranker) | `vinci/triage.py`, `scripts/triage_pass.py`, `scripts/triage_cost_gate.py` | `data/snapshots/event_provenance.jsonl` (525 rows; nothing else read it) | 15, `tests/test_triage.py` |

**Restore** any of it with `git checkout 481e82f7 -- <path>` (`481e82f7` is the last `main` commit
that held every removed file, unchanged since).

**What stays, by the operator's decision:** the graph exposure map (`data/graph_coverage.json`,
read by `vinci/dossier/mechanical.py` and `assemble.py`, and `vinci graph-coverage` /
`graph-exposure`), and the ranker's `cause_class` (`vinci/rank/cause.py`).

**Rewired, and only where a removal forced it:**

- `tests/test_extraction_version_drift.py` re-pinned (`--repin`): `ciq_scale_backfill.py` left the
  watched set. No version row, because no page's output changes: nothing on the assembly path
  imported the back-fill.
- `tests/test_graph.py` keeps its 7 tests of the exposure map, extraction and judge; its docstring
  no longer points at the removed command.
- `frontend/assets/styles.css`: the tape's block (153 lines) is removed. Two of its rules,
  `.rd-head` and `.rd-head .gt`, sat after the radar's own `.rd-head` and so have styled the
  Themes radar since 2026-08-25 (`align-items: center; margin-bottom: 10px` over the radar's
  `baseline; 6px`). Their values move into the radar's rule, so the radar renders as before from
  one definition instead of two.
- `vinci/graph/__init__.py`: the package docstring no longer advertises Test 0.
- `docs/engineering.md`: the three glossary entries coined for the tape (*calls tape*,
  *counter-directional target*, *implausible target*) stay as vocabulary, their `Home:` pointers
  now naming the commit that held the code.
- STATE.md: the §2 calls-tape bullet carries a two-line claim pointing here; §3's Test 1 bullet
  notes its code is removed; and the §5.0 paragraph **"MEASURED, NOW AN OPERATOR CALL — not a
  build: the LLM cause tier"** is DELETED as withdrawn. That call priced spending a model on the
  20% of de-rating events (104 of 525) the triage pass's item codes could not name. With the
  triage pass retired, the tier has no input until the pass is restored, so the call has nothing
  to decide. Its measurement stays in `docs/records/2026-08-28-triage-pass.md`.

**Left alone, on purpose:**

- `vinci/quality/sources/ciq.py`'s not-run reason still names `ciq_scale_backfill.scale_check_backfill`.
  The sentence is history: it explains why a page carries no `anchor.ciq_scale_check`. It is also
  the text of five committed scorecards (`data/snapshots/data_quality/ciq/2026-10-28` … `11-04`), so
  rewording it would change the next scorecard's text for no change in what it measures.
- `vinci/ciq`'s `load_ciq_edges` and `LocalFolderManualStore` now have no production caller (Test 0
  was the last). `vinci.ciq` itself stays: `vinci/graph/extract.py` reads its `SUPPLY_CHAIN_TYPES`.
  Removing them was not decided, so this PR only reports it.
- `README.md` still names Test 0 / Test 1 in its build history, in the past tense. `.gemini/config.yaml`
  (inert) still lists `frontend/calls/**` among its excludes. `.claude/launch.json` keeps a preview
  config named `calls-tape` that serves another machine's frontend folder.
- The records of the removed features keep their bodies. Their statuses are not flipped: each
  described what was built, and that stays true.

**STATE rows.** §5.0 rows 31, 41 and 43 use *calls* only in its ordinary sense (Polygon API calls,
earnings calls, LLM calls); none refers to `vinci.calls`, and no row closes with R1.

**WHY.** Operator, 2026-11-04, from the coordinator's audit of what the core paths reach: dossier
assembly, the weekly refresh and theme intelligence reach 185 of the 229 `vinci` modules. The calls
tape's last output was 2026-08-25 and it was "not a decision path"; Test 0/1 is a falsified
experiment; the back-fill was a one-off, already run; the triage pass was a cost measurement never
wired in. Each costs suite time and review surface on every change near it.

**HOW VERIFIED.** (Outputs are in the PR body.)

- **The weekly path is untouched — a `vinci run-weekly` replay of the last committed run
  (2026-10-16).** RUN_WEEKLY_RESULT
- **The $0 pre-spend check on three pages.** PRECHECK_RESULT
- **The frontend.** `frontend/build.py` (code from this worktree) rebuilt every mirror and changed
  no committed file. Served locally: the nav has no Calls entry, `#/calls` falls back to the
  overview, the Themes radar and the dossier view render, and the console logs no error.
- **No reference left behind.** `git grep` for `vinci.calls`, `vinci/calls`, `callscore`,
  `views/calls`, `graph.test0`, `graph.test1`, `run_test1`, `ciq_scale_backfill`, `vinci.triage`,
  `triage_pass`, `triage_cost_gate` and `event_provenance` outside `docs/records/` finds only the
  deliberate leftovers listed above.
- **Gate.** SUITE_RESULT

**BOUNDARY.** Line and file counts: `git ls-files` / `wc -l` at `481e82f7`, before the removal.
Test cases: `pytest --collect-only` over the named files at `481e82f7` (each parametrised case
counted). The replay's boundary is stated in its own line above.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The four features are gone from `main`; restoring one is a
`git checkout` of its paths from `481e82f7`, plus re-adding its command to `vinci/cli.py`, its
route to `frontend/app.js` and, for the calls tape, its mirror to `frontend/build.py`. Falsifier
for the retirement itself: a later build that needs one of them back within the quarter.
