---
id:
status: shipped
date: 2026-11-04
prs: [905]
supersedes:
superseded-by:
---

# Retired: the calls tape, graph Test 0/1's code, the CIQ scale back-fill and the triage pass — removed with their tests and data, restorable by reverting #905 (R1 of three retirements)

**WHAT.** The operator decided on 2026-11-04 to retire four low-use features. This is the first of
three retirement PRs (R1; R2 retires `vinci.themes`, R3 the between-print panels). Removed:

| feature | code | data | tests (cases collected at `481e82f7`) |
|---|---|---|---|
| the calls tape (scoring a public commentator's posted calls) | `vinci/calls/` (7 modules, 841 lines); the `vinci calls` command group (`accounts`, `fetch-bars`, `score`, `import-labels`); `frontend/views/calls/tape.js`, `frontend/lib/callscore.js`, the tape's nav entry and route in `frontend/app.js`, its candle primitives in `frontend/lib/exhibit.js`, its CSS block, and `frontend/build.py`'s `_mirror_calls` | `data/calls/` (247 files) and its mirror `frontend/calls/` (247 files); the `.gitignore` carve-out | 66, in six `tests/test_calls_*.py` files |
| graph Test 0 / Test 1 (falsified 2026-07; STATE §3) | `vinci/graph/test0.py`, `vinci/graph/test1.py`, the `vinci graph-test0` command, `scripts/run_test1.py`, `scripts/run_test1_xsector.py` | none committed (`data/graph_test0.json` was git-ignored) | 5 of `tests/test_graph.py`'s 12 |
| the CIQ scale back-fill (a one-off, run 2026-10-27) | `vinci/dossier/ciq_scale_backfill.py` | none | 1 of `tests/test_ciq_balance_scale_outcome.py`'s 7 |
| the triage pass (de-rating causes by 8-K item code, 2026-08-28, never wired into the ranker) | `vinci/triage.py`, `scripts/triage_pass.py`, `scripts/triage_cost_gate.py` | `data/snapshots/event_provenance.jsonl`, the #515 measurement (525 de-rating events, one row each; nothing else read it) | 15, `tests/test_triage.py` |

**Restore** by reverting #905's squash commit on `main`. That undoes every edit at once, the deletions
and the edits to kept files listed below. Copying the deleted files back by hand is NOT a restore:
`tape.js` imports `candleDomain` from `frontend/lib/exhibit.js`, which this PR edits, so a reviewer who
restored `tape.js` and `callscore.js` onto the head got `SyntaxError: ... does not provide an export
named 'candleDomain'`; and without the `.gitignore` exception, new `data/calls/` files are silently
ignored. `git checkout 481e82f7 -- <path>` is right only for a DELETED path. Every one of the 519 is
unchanged on `main` from `481e82f7` through `bd6e0d12` (#904 touched none of them).

**What stays, by the operator's decision:** the graph exposure map (`data/graph_coverage.json`,
read by `vinci/dossier/mechanical.py` and `assemble.py`, and `vinci graph-coverage` /
`graph-exposure`), and the ranker's `cause_class` (`vinci/rank/cause.py`).

**Every kept file this PR edits** (each edit only where a removal forced it):

- `vinci/cli.py`: the `vinci calls` command group and its handlers, and `graph-test0` with its
  handler, are removed.
- `frontend/app.js`: the tape's nav entry and its `calls` route are removed.
- `frontend/build.py`: `_mirror_calls`, its call, its `CALLS` / `OUT_CALLS` paths and its line in
  the build's printout are removed.
- `frontend/lib/snapshots.js` (round 1): the tape's seven getters and its `./calls` root are
  removed.
- `frontend/lib/exhibit.js`: the candle primitives only the tape drew (`candleDomain`, `candles`,
  `candleWidth`) are removed.
- `frontend/assets/styles.css`: the tape's block (153 lines) is removed. Two of its rules,
  `.rd-head` and `.rd-head .gt`, sat after the radar's own `.rd-head` and so have styled the
  Themes radar since 2026-08-25 (`align-items: center; margin-bottom: 10px` over the radar's
  `baseline; 6px`). Their values move into the radar's rule, so the radar renders as before from
  one definition instead of two.
- `.gitignore`: the `!data/calls/` exception is removed.
- `vinci/graph/__init__.py`: the package docstring no longer advertises Test 0.
- `vinci/quality/sources/ciq.py` (round 2): a comment only, beside the not-run reason that names
  the removed back-fill (below).
- `tests/test_graph.py` loses Test 0/1's 5 cases, their two helpers and its pointer to the removed
  command, and keeps its 7 tests of the exposure map, extraction and judge.
  `tests/test_ciq_balance_scale_outcome.py` loses the back-fill's 1 case.
- `tests/test_extraction_version_drift.py` is re-pinned (`--repin`): `ciq_scale_backfill.py` left the
  watched set. No version row, because no page's output changes: nothing on the assembly path
  imported the back-fill. Its docstring (round 2) no longer says `vinci/ciq` feeds the graph test:
  `tests/test_ciq.py` reads its relationship parser, and `vinci/graph/extract.py` imports only its
  `SUPPLY_CHAIN_TYPES` taxonomy.
- `tests/test_frontend_data_roots.py` (new, round 1): every data root `lib/snapshots.js` fetches must
  be a committed directory under `frontend/` or a mirror `build.py` writes. Round 2 reads `build.py`
  through `ast`, so a commented-out mirror line no longer vouches for an orphan root. Negative pin:
  `test_a_mirror_named_only_in_a_comment_or_a_string_is_not_built`, which failed on the text search
  (`assert not True`).
- `docs/engineering.md`: the three glossary entries coined for the tape (*calls tape*,
  *counter-directional target*, *implausible target*) stay as vocabulary, their `Home:` pointers
  now naming the commit that held the code.
- STATE.md: the §2 calls-tape bullet carries the RETIRED claim pointing here, with the withdrawal
  below as its third line; §3's Test 1 bullet notes its code is removed; row 5's precedent
  `triage.py` is marked retired; and the §5.0 paragraph **"MEASURED, NOW AN OPERATOR CALL — not a
  build: the LLM cause tier"** is deleted.

**WITHDRAWN 2026-11-04 by the operator: the LLM cause tier.** Asked "Withdraw the cause-tier
decision, as recorded below?", the operator answered "Withdraw it". The decision priced spending a
model on the 20% of de-rating events (104 of 525) whose cause the triage pass's 8-K item codes could
not name. Triage is retired, so the tier has no input. The ranker's cause slot (`vinci/rank/cause.py`,
`cause_class`) stays and is unfed; reopen only if cause classification becomes needed. That slot is
a decision-path question, and this PR does not touch `vinci/rank`. The measurement's narrative stays
in `docs/records/2026-08-28-triage-pass.md`. Its data, `event_provenance.jsonl`, is deleted with the
pass and restorable from `481e82f7`.

**Left alone, on purpose:**

- `vinci/quality/sources/ciq.py`'s not-run reason still names `ciq_scale_backfill.scale_check_backfill`.
  The sentence explains why a page carries no `anchor.ciq_scale_check`. It is also the text of the
  committed scorecards since 2026-10-28 (`data/snapshots/data_quality/ciq/2026-10-28` … `11-04`), and
  `test_the_committed_snapshot_reproduces_from_the_pages_it_names` requires the latest to reproduce
  byte for byte from the code. Rewording the string failed that test in round 2, and passing it would
  mean rewriting a dated measurement. So the string stays, and a comment beside it (round 2) says
  the function was retired here and restores from `481e82f7`.
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
assembly, the weekly refresh and theme intelligence reach 185 of the 229 `vinci` modules (static
import reachability from those three entry points, at `main` `1b8a5a2f`, 2026-11-04). The calls
tape's last output was 2026-08-25 and it was "not a decision path"; Test 0/1 is a falsified
experiment; the back-fill was a one-off, already run; the triage pass was a cost measurement never
wired in. Each costs suite time and review surface on every change near it.

**HOW VERIFIED.** (Outputs are in the PR body.)

- **The weekly path is untouched — a `vinci run-weekly` replay of the last committed run
  (2026-10-16).** Inputs: the 2026-10-16 weekly's own HTTP cache and
  store (`research-alpha-audit-bcba59/data`, APFS-cloned, source md5 unchanged), every cached
  response served whatever its age, and the committed snapshots of each tree. `origin/main`
  (`481e82f7`) ran first, at `--end 2026-10-16`. Its cache misses were fetched live into its own
  clone: 1,940 (1,882 SEC filing documents, 58 Polygon), from paths added after 10-16 (cover-page
  typing, the rename carry-forward). The branch then ran on a clone of that filled cache with the
  network REFUSED: 0 misses, 97 s. **Every one of the 86 files in `data/snapshots` came out
  byte-identical between the two runs** — universe (2,065 members), candidate records (344),
  ranked queue (344), the screen run `2026-10-16-02` and its manifest, universe stats and the
  alias table — except `event_provenance.jsonl`, which this PR deletes. Against the COMMITTED
  2026-10-16 run, main's own replay already differs: universe identical, but the queue is 344
  against 343 (AKTS out; OGG and SKYD in, SKYD by the rename carry-forward #833 added after that
  run) and four universe drop counts move by one. That is `main`'s code since 10-16, not this
  PR; the branch reproduces main exactly.
- **The $0 pre-spend check on three pages.** `vinci dossier precheck --ticker` on GOOGL, VRRM and TJX, with
  the Anthropic key removed from the process, so any model call fails loud ($0 by construction).
  Inputs: the assembler's CIQ copy (`mosaic-theory-ta/data/manual`, linked) and an APFS clone of
  its store (bars to 2026-10-30; source md5 unchanged). Branch: GOOGL 110 Sourced fields + 6
  blocks compared, **0 regressions, 0 post-spend refusals, exit 0**; TJX **0 / 0, exit 0**; VRRM
  **0 regressions and 1 post-spend refusal, exit 1** — its CIQ panels are 99 days old against the
  45-day ceiling, a stop the check exists to make and unrelated to this PR. The same three on
  `origin/main` print the same 44 lines once timestamps and paths are removed; the outputs are equal
  in content, not byte-identical.
- **The monitor day.** `vinci monitor --ref 2026-11-02 --out <scratch>` on `origin/main`, then on
  the branch with a clone of the cache main filled: **the two days are byte-identical.** Main's
  own re-cut differs from the COMMITTED 2026-11-02 day in one field, mirrored into one panel: IT's
  `newer_filings` lists 3 filings where the committed day lists 5. The two extra are a 10-Q and an
  8-K filed 2026-11-03, a day after the day's as-of. That is designed behaviour, not a defect:
  `_cmd_monitor`'s "TWO ANCHORS, NAMED" comment says a routine run reads filings through today,
  while a `--ref` re-cut reads only what was filed by the reference date. The live run was made on
  11-03, so it kept them.
- **Re-run after round 1 and the #904 merge**, by two independent reviewers (the coordinator's
  round 2), head `216329c5` against `main` `bd6e0d12`, offline. Precheck on TJX and GOOGL: the full
  $0 build JSON is identical in values, apart from 3 timestamps and 2 store paths.
  `vinci monitor --ref 2026-11-02` is byte-identical. `run_weekly(end=2026-10-16)` returns identical
  results. The suite passed (9,110 in their environment), mypy and ruff are clean, every module
  imports, all 44 CLI commands' `--help` work, and the exposure map is intact.
- **The frontend.** `frontend/build.py` (code from this worktree) rebuilt every mirror and changed
  no committed file. Served locally: the nav has no Calls entry, `#/calls` falls back to the
  overview, the Themes radar and the dossier view render, and the console logs no error.
- **No reference left behind.** `git grep` for `vinci.calls`, `vinci/calls`, `callscore`,
  `views/calls`, `graph.test0`, `graph.test1`, `run_test1`, `ciq_scale_backfill`, `vinci.triage`,
  `triage_pass`, `triage_cost_gate` and `event_provenance` outside `docs/records/` finds only the
  deliberate leftovers listed above.
- **Gate, at the final head** (round 2, after the #904 merge). ruff: all checks passed;
  `mypy --strict vinci`: no issues in 219 source files; `pytest -m "not network"`:
  **9,114 passed, 0 failed**, 555 skipped (chiefly the tests that need the git-ignored CIQ
  exports, absent in a worktree as in CI), 8 xfailed, 39 deselected, 366.2 s. Earlier
  heads: 9,062 passed at round 0 (its first full run, 9,059 passed and 1 failed, caught §5.0 over
  its 60-line cap; deleting the withdrawn paragraph instead of annotating it fixed it), and 9,112
  after the merge.

**BOUNDARY.** Line and file counts: `git ls-files` / `wc -l` at `481e82f7`, before the removal.
Test cases: `pytest --collect-only` over the named files at `481e82f7` (each parametrised case
counted). The replay's boundary is stated in its own line above.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The four features are gone from `main`. Restoring them means
reverting #905's squash commit (see **Restore** above). Restoring only one means checking out its
deleted paths from `481e82f7` AND re-applying this PR's edits to the kept files it needs (its
command in `vinci/cli.py`; for the calls tape, its route, mirror, getters, candle primitives, CSS
and `.gitignore` exception). The LLM cause tier is withdrawn, and the ranker's cause slot stays
unfed. Falsifier for the retirement itself: a later build that needs one of them back within the
quarter.
