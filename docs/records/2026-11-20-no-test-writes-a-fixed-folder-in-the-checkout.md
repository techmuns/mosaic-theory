---
status: shipped
date: 2026-11-20
prs: [1153]
supersedes:
superseded-by:
---

# No test writes a fixed folder in the checkout, and the protected-approval ids carry no date: the suite's last named parallel hazards, fixed in test files only and held by an AST guard ($0)

**WHAT.**
- **The authority.** Coordinator B asked why builds are slow. A read-only measurement at main
  `ac3c9479` (2026-11-19) found 0 outcome changes over 13,172 ids in 4 parallel runs, but its
  write audit named 5 hazards. B's brief to this session: fix them, in test files only. No change
  to `bin/commit`, `gate.yml`, `pyproject.toml`, conftest or `.claude/hooks`. Whether `bin/commit`
  runs on workers stays the operator's decision.
- **The fixed folders.** The brief named four sites. On main `51c84843` three remain: W73 (#1144)
  deleted W62's test and added a fourth copy of the same pattern. Each wrote a node driver and its
  JSON into `ROOT / ".pytest_wNN_tmp"`, ran `node` from the checkout, then removed the folder with
  `rmtree`:

  | test | folder | now |
  |---|---|---|
  | `test_anchor_gap_split_render.py` `_web()` (`@cache`d, 4 callers) | `.pytest_w61_tmp` | `tempfile.TemporaryDirectory()`, since a cached helper takes no fixture |
  | `test_w50_anchor_current.py::test_both_renderers_print_what_each_anchor_priced` | `.pytest_w50_tmp` | `tmp_path` |
  | `test_w73_dated_multiple.py::test_the_web_prints_the_dated_multiple_and_its_flag_collapsed_and_open` | `.pytest_w73_tmp` | `tmp_path` |

  Node still runs with `cwd=ROOT`. The driver resolves `frontend/views/shared/dossier.js` from its
  cwd and imports only `node:` builtins, so only where the driver file lives has changed.
- **The ids.** `test_protected_approval.py` reads `TODAY = dt.date.today()` at import. Six of the
  eight parametrize ids of `test_only_the_fixed_form_naming_the_file_approves_it` carried it, and
  a seventh carried the constant `2026-13-40`. Each is now a `pytest.param(..., id="another-file")`
  etc. `TODAY` stays in the values.
- **The guard.** `tests/test_no_test_writes_the_checkout.py` reads the AST of every module under
  `tests/` (569 at this change, the guard's own included; the hand-run generators in
  `tests/fixtures/` aside). It refuses two shapes:
  - a call that writes on a path built from the module's own location (`Path(__file__)…`, or a
    name bound to one, such as `ROOT`). `Path` is matched however it is reached: bare (241
    modules), `pathlib.Path` (147), an alias such as `_pl.Path` (2) or `__import__("pathlib").Path`
    (2). Review round 1 added all but the bare form, which alone had left 147 modules unguarded
    (coordinator B's finding). The writes are mkdir, write_text, write_bytes, touch,
    unlink, rename, open for writing, `shutil.rmtree`, a copy's or move's destination, and `os`'s
    makedirs, remove, rename and replace. It keys on what the call does, not on the folder's name,
    so `ROOT / "build_w90"` is refused as `ROOT / ".pytest_w61_tmp"` was;
  - a checkout path that names a `.pytest_*` folder, by `/` or `.joinpath`, pytest's own
    `.pytest_cache` aside. Such a name is a scratch folder by intent, even where a child process
    does the writing.

  Names are bound per function, so a `tmp` that is a temp dir in one test and a checkout path in
  another is judged by its own binding. Each function is its own scope: it inherits its enclosing
  scope's names, less its own parameters. So a parameter that shadows a module name
  (`def f(ROOT)`, nested or not) is whatever its caller passes, and a closure writing an outer
  checkout path is still refused (review round 1).
- **The id pin.** `test_the_forms_ids_hold_no_date_so_every_worker_collects_the_same_tests`
  collects the module in a child pytest and reads pytest's own ids: 8, unique, none date-shaped.

**WHY.**
- **A fixed folder races on workers.** One worker's `rmtree` can delete another worker's driver
  while node is reading it. W61's `_web()` is cached per process, so its 4 callers landing on two
  workers each build it once, in the same folder. W50's and W73's tests are single, so under
  `--dist load` they do not race with themselves. They still share the other two costs.
- **A killed run leaves it behind.** The folder is not git-ignored. A run stopped mid-test leaves
  it untracked, and the next `bin/commit` refuses the checkout ("untracked files").
- **CI cannot see it.** The ctime check of 2026-11-14 is blind to a folder created and deleted
  inside the run, by its own recorded accepted risk.
- **This is the accepted risk of 2026-11-13 recurring.** The #1065 sweep moved four tests out of
  the tree. W50 (`8edf9ebb`), W61 (`8ea51e99`), W62 (`65a8b863`) and then W73 added the pattern
  again in the five days after. Hence a guard, not a fourth fix by hand.
- **Ids read at import split a run at midnight.** Each pytest-xdist worker collects the suite on
  its own. A run whose workers collect on either side of local midnight stops with "Different
  tests were collected between gw0 and gwN". The measurement saw it happen to the ids between two
  runs: 12 ids differed, the 6 renamed `2026-11-19` → `2026-11-20`.
- **Left alone, by the brief:** `tests/test_sec_pacing.py:249`. It is a wall-clock test of 4 real
  processes, a load flake rather than shared state, and widening it would weaken it.

**HOW VERIFIED.**
- **The guard is red on the live suite before the fix.** At `51c84843` it found 15 findings in
  569 modules, all at the three sites (5 each: the folder name, the mkdir, two write_texts, the
  rmtree), and nothing anywhere else. That matches the write audit's finding that no other test
  writes a fixed path. After the fix it is green.
- **It is red on shapes outside its own name list.** Thirteen shapes that name no `.pytest_`
  folder are refused:
  - a mkdir under another name, a write beside the test, an append under a bound subfolder;
  - a copy into the checkout, an rmtree on `Path(__file__)`, an unlink in a glob loop;
  - `Path.open("w")`, `os.replace` into `data/`, `joinpath(".pytest_w90_tmp")`;
  - a closure writing an outer checkout path;
  - a root spelled `pathlib.Path(__file__)`, `_pl.Path(__file__)` or
    `__import__("pathlib").Path(__file__)`.

  The shape W61 had is refused at each of its 5 lines. Eight reads and tmp writes pass, among
  them the same driver in a temp dir with `cwd=ROOT`, a checkout file name under `tmp_path`, and a
  parameter shadowing `ROOT`, at the top level and nested. The nested-parameter case and the three
  `pathlib` spellings were red before review round 1's fixes. After them the live scan is still at
  0, and the three base sites still give 5 findings each.
- **The race is real on the old code and gone on the new.** The four node tests were run on 4
  workers with `--dist each`, which runs every selected test on every worker, so all of them enter
  the folder at once. Base `51c84843`: 2 of 4 runs failed, both
  `test_both_renderers_print_what_each_anchor_priced`, with `CalledProcessError` on
  `.pytest_w50_tmp/drv.mjs`. Head: 4 of 4 passed (24 passed each). Neither left a folder in the
  root.
- **The id pin is red before the fix.** It found 7 of 8 ids carrying a date. After the fix it is
  green, with the ids `another-file`, `words-not-quoted`, `no-date`, `not-a-date`, `no-words`,
  `not-one-of-the-lists`, `not-a-whole-line` and `not-the-fixed-form`.
- **The full suite, base against head, both at `-n auto` (8 workers):**

  | run | outcomes | wall | load1, start → end |
  |---|---|---|---|
  | base `51c84843` | 12,591 passed, 667 skipped, 7 xfailed | 1,305 s | 6.0 → 12.6 |
  | head (this change, before its PR number was written) | 12,612 passed, 666 skipped, 7 xfailed, 1 failed | 1,963 s | 12.1 → 19.2 (5-min average peaked near 53) |

  Of the 13,257 ids common to both runs, 13,255 have the same outcome. The two that differ:
  - `test_records_ledger.py::test_a_shipped_record_names_the_pr_that_carried_it` failed on head
    because this record's `prs:` was still empty. Writing the number fixes it.
  - `test_vote_rule_confirmation.py::test_the_transcripts_are_read_as_the_replay_harness_reads_them`
    skipped on base and passed on head. It finds the licensed CIQ folder through
    `ROOT.parents[2]` when the checkout is a worktree (:191). From head's worktree that path is
    the primary checkout; from the scratch base worktree it is not. The difference is where the
    worktree sits, not the code.

  8 ids exist only on base and 29 only on head. The 8 are the protected-approval ids under their
  old, dated names, all passed. The 29 are those 8 under their new names, the guard's 19 tests
  at `e1b69719` (review round 1 adds 2),
  the id pin, and the record-hygiene case of this record, all passed. No `.pytest_w*` folder was
  left in either root.
- **The gate.** ruff and `mypy --strict vinci` are clean. `bin/commit` ran green on one process.

**BOUNDARY.**
- **Code:** base = main `51c84843`. Head = this change on it.
- **Module count:** every `*.py` under `tests/` except `tests/fixtures/`, at `51c84843` plus the
  guard file.
- **Race demo:** 2026-11-20 at about 11:20 local. 4 tests (W61's 3-param web test and its
  no-split test, W50's, W73's) × 4 workers = 24 executions per run. 4 runs on base, 4 on head.
  Shared Mac, load about 4–6.
- **Full runs:** `python -m pytest -m "not network" -p no:cacheprovider -n auto` in two
  worktrees. Each holds the same ignored data (`data/cache`, `frontend/snapshots`, the `.env`
  link) and no `data/manual`, so CIQ-keyed tests skip, as on CI, except the one test that looks
  through `ROOT.parents[2]` (above). Primary `.venv`: Python 3.12.13,
  pytest 9.1.1, pytest-xdist 3.8.0. `PYTHONPATH` = the worktree.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **ACCEPTED RISK, what the guard cannot see.** A child process that writes relative to its
  `cwd=ROOT` (a static scan cannot look inside it); a path built from a value the module does not
  bind to its own location (`Path(str(ROOT))`, a class attribute read as `self.X`); a
  `TemporaryDirectory(dir=ROOT)`. Deferred from review round 1, since neither shape occurs in the
  569 modules: a binding by tuple unpacking, `:=` or `with … as` (only single-name assignments and
  `for` targets are followed), and a write function imported by name (`from shutil import rmtree`;
  only the `shutil.`/`os.` attribute forms are matched).
  - **Falsifier:** a `.pytest_*` or other untracked folder appears in a checkout root after a run,
    or the gate's ctime check names a file in the tree, with this guard green.
- **The id pin starts a child pytest** (about 0.7 s), so that it reads pytest's real ids rather
  than the source's spelling of them.
- **Not done, by the brief:** `bin/commit` still runs on one process.
- **Found and not fixed:**
  - STATE row 65 and `tests/test_one_gate.py:33–35` still say the shared venv has no
    pytest-xdist; it has had 3.8.0 since 2026-11-16.
  - `bin/commit`'s extra `-q` makes `-qq`, which prints no totals line.
  - `mypy --strict` over `tests/test_w73_dated_multiple.py:575` reports `rn.sys` as not
    explicitly exported. The gate type-checks `vinci` only.
  - About 15 test modules each carry their own copy of the `renderDossier` node driver. A shared
    tmp-only helper would remove the class this guard polices.
