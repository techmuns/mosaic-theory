---
id:
status: shipped
date: 2026-11-17
prs: [1110]
supersedes:
superseded-by:
---

# The impact check's fail-first stage runs each side in a detached git worktree, so a test that asks git runs as it does in a checkout: #1104's 7 hooks nodes that FAILED at both refs now pass at both, and #1098's 10 frozen-cut nodes that SKIPPED now run

**WHAT.**
- **`vinci.impact.run.fail_first`** runs head's changed tests in two detached git worktrees of
  head's commit (`_worktree`, `_checkouts`), no longer in a `git archive` extract. Base's checkout
  swaps `vinci/` for base's in its index as well as its files (`git rm -r vinci`, then
  `git checkout <base> -- vinci`), so git there lists, diffs and reads base's code.
- **The placeholder for a name base lacks** (`_SHIM`) is written beside the checkout, on the
  child's `PYTHONPATH`, no longer inside it. In a checkout, git would list it as an untracked file
  at base alone.
- **No worktree outlives the stage.** Both are removed when the tests end, and a run killed
  mid-stage has its worktrees removed by the next run (`_drop_worktrees`, which touches only paths
  under the run's `failfirst/`; never a `git worktree prune`). Logs and junit files stay. The
  removal is `--force --force`: a run killed during `git worktree add` leaves that worktree locked
  ("initializing"), and a single `--force` refuses it. Found in review: the pin failed with
  `StampError: cannot remove a locked working tree` before the fix.
- **The report says how part 1 ran.** The result records `checkout: "worktree"`, and section 1
  prints "each in a detached git worktree of head's commit, base's with its `vinci/` swapped in".
  An older report, with no such field, now says its tree was "a `git archive` extract with no
  `.git`", rather than claiming a checkout it never had.
- **RUNBOOKS §o step 4.1** states the same.

**WHY.** The coordinator found this on #1104 (2026-11-17), and the notes on earlier PRs record the
same shape:
- An archive extract has no `.git`, so a test that asks git about its own checkout cannot run
  there. The hooks find their checkout with `git rev-parse --show-toplevel`. With no `.git`, the
  guard printed nothing, and 7 `tests/test_claude_hooks.py` nodes FAILED at both refs, among them
  #1104's own new pin. `tests/test_frozen_pages_are_cuts.py` skips by design outside a checkout.
- Section 1 then printed them as a result: "fail at head: 7" on a PR whose tests all pass in a
  checkout, or "skipped: 10". Neither said whether those nodes fail first.
- The three fixes the brief offered:
  - **A shallow clone at the ref** gives `.git` but one commit. 12 test files read `origin/main`,
    and `test_frozen_pages_are_cuts.py` reads commit `4889ddba`'s blobs. Those would fail or
    differ in a shallow clone: a different false signal. The gate's CI checks out with
    `fetch-depth: 0`.
  - **A named "needs git" bucket** would report those nodes without running them. It needs a
    detector, and a message match is a guess. A test that skips or passes vacuously without git
    would not be caught at all.
  - **A detached worktree** is a real checkout. It shares the repository's objects and refs, so
    nothing is copied. It is what an operator's run sees (every session works in a worktree) and
    what CI's full clone sees. Chosen.
- Two adjacent changes are required once git is present, and each is pinned by a mutation:
  - **The index swap.** Without it, a module only head has stays a tracked file missing on disk at
    base, and a test that lists `git ls-files vinci` FAILS at base alone: a false fail-first.
  - **The shim's move.** Inside the checkout, it is an untracked file at base alone.

**HOW VERIFIED.** All runs are $0: no model call, and no Polygon or Tiingo pull. "Main's harness" is
`vinci/impact` at `e15659ba`. "The fix" is this branch.
- **Reproduced on #1104** (head `25759619`, base `e15659ba`, 3 changed test files, 147 nodes):
  - Main's harness: 140 pass at both and **7 FAILED at both**, exactly the 7 nodes in #1104's body
    (`test_guard_*` ×6, at `tests/test_claude_hooks.py:90/98/114/129/144/152`, and
    `test_open_now_indexes_every_row_of_the_committed_state` at `:181`). 98.4 s.
  - The same 7 nodes in real detached worktrees: **7 of 7 pass at head**. At base, the 5 that
    exist there **pass, 5 of 5**. The other 2 are new in #1104, and `vinci/` is identical between
    the refs.
  - The fix: **147 of 147 pass at both, 0 fail at head**. 74.5 s.
- **#1098** (`8a71a383`, base `6b5fbe51`, 24 changed test files, 560 nodes):
  - Main's harness: 546 pass at both, 14 skipped at both. Of the 14, **10 are
    `test_frozen_pages_are_cuts.py`, "not a git checkout"**, and 4 are CIQ-bound.
  - The fix: **556 pass at both**, 4 skipped at both. The 4 are the CIQ-bound ones, "licensed CIQ
    bundles unavailable (never committed)", an honest skip: neither checkout holds git-ignored
    data.
- **The pins** (`tests/test_impact_failfirst.py`, 4 new tests) run on a real two-commit fixture
  PR. Its changed test file has 6 nodes. Per node, base/head:

  | node | main's harness | the fix |
  |---|---|---|
  | `test_a_git_pin_that_fails_first` | failed / **failed** (CalledProcessError) | failed / passed |
  | `test_a_git_pin_that_passes_at_both` | **failed / failed** (CalledProcessError) | passed / passed |
  | `test_git_lists_exactly_the_modules_on_disk` | **failed / failed** (CalledProcessError) | passed / passed |
  | `test_a_pin_that_skips_outside_a_checkout` | **skipped / skipped** | passed / passed |
  | `test_a_name_only_head_defines` | failed / passed | failed / passed |
  | `test_a_real_failure_at_both_refs` | failed / failed | failed / failed (`assert 1 == 99` / `assert 2 == 99`, same line) |

  - Run on main's harness, 4 of the 6 tests in the file fail. The 2 that pass are the two
    pre-existing tests.
  - Each mutant of the fix fails at least one pin:
    - **M1**: `vinci/` swapped on disk only, not in the index;
    - **M1b**: base's `vinci/` extracted, not checked out, so it is untracked;
    - **M2**: the shim written inside the checkout;
    - **M3**: the checkouts never dropped;
    - **M4**: a killed run's worktrees not cleared first.
  - M1b first SURVIVED a weaker pin ("every tracked module is on disk" passes vacuously when git
    lists nothing). The pin was tightened to "git lists exactly the modules on disk, and some".
- **Nothing else moves.** Two recent merged PRs that build pages were run on main's harness and on
  the fix, with one set of inputs: store file `65cbae7d1474` (frontier 2026-11-11), the primary's
  CIQ root (277 exports on 26 pages), its HTTP cache and its `.env`. The PRs are #1105
  (`e15659ba`, base `5c9c7eac`) and #1097 (`18970909`, base `75f303b7`).
  - On both PRs, `report.md` from `### 2` to the end is **byte-identical** once durations are
    normalised.
  - In the JSON, `panel_requests`, `frontend`, `downstream`, `page_reach` and `same_code` are
    identical.
  - The page results are identical except PARR's wall-clock build timings. PARR fails at both
    sides (`CiqMislabelledError`, its known mislabelled quarterly export). A failed build is never
    reused, so it was re-built.
  - Part 1's per-node outcomes are identical too; no node's outcome moved. #1105 has 71 nodes: 51
    pass at both, 11 skipped and 9 fail first. #1097 has 131 nodes: 88 pass at both, 38 fail first
    (7 failed and 31 errors at base), 4 skipped, and 1 error at base with no node at head (a file
    that did not collect). Every skip names a CIQ or IT export, or a name base lacks.
  - The fix's runs reused the first runs' page builds, by the build key's normal rule: same code,
    inputs, store and UTC day. Main's #1097 run built all 52 page sides fresh.
- **No worktree is left behind.** After the seven real runs, the shared repository's
  `git worktree list` held no `failfirst/` path.

**BOUNDARY.**
- **Node counts** are pytest node ids in each PR's changed `tests/test_*.py` files that exist at
  head. They were run `-m "not network"` with no git-ignored data, on 2026-11-17 between 14:51 and
  15:09 UTC, at the shas named above.
- **"Main's harness"** is `vinci/impact` at `e15659ba`. **"The fix"** is this branch's working
  tree, cut from `e15659ba`.
- **The fixture counts** are over the fixture PR's one changed test file: 6 nodes.
- **The real-worktree check on #1104** ran the 7 named nodes only.
- **Durations** are part 1's own `seconds`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Base's checkout is head's COMMIT with base's `vinci/` staged over it.** This is what the
  archive extract also was (head's tree with base's `vinci/`), now stated. A test that asks git
  for `HEAD`'s history or `git diff HEAD -- vinci` sees head's commit, and a test that asserts a
  clean `git status` of its own checkout would fail at base alone. Measured at `e15659ba`: no
  file in `tests/` asserts a clean status or `git diff HEAD` of its own checkout. A grep for
  `porcelain` and `diff --quiet HEAD` beside `ROOT` finds only a temporary repository
  (`test_gate_on_workers.py`) and this PR's fixture, which excludes `vinci/`.
  `test_duplicate_definitions.py` diffs the working tree against a commit, so at base it reads
  base's code, as a checkout of base would. A synthetic commit for base would make the tree clean,
  but it would change HEAD's sha and its history count instead. Falsifier: a node that fails at
  base only, with a message about a git status, diff or log of `vinci/`.
- **Disk.** While the tests run, part 1 holds two full checkouts: 284 MB each (4,025 tracked files
  at `e15659ba`), where the extract and its APFS clone shared blocks. Both are removed when the
  stage ends. Main's harness left its trees in every run folder: #1104's run folder held 559 MB
  after the run.
- **A stage stopped mid-run (Ctrl-C) removes the checkouts while the other side's pytest may still
  run.** If that removal fails, its error replaces the interrupt. Deferred from review: it
  needs the retry loop's processes tracked, and the next run clears what is left.
- **A test that writes to git now writes to the shared repository**, as it does in an operator's
  own checkout. HEAD is detached, so a commit moves no branch, but a test that creates a ref
  would leave one. Falsifier: a ref that appears after a run. None of the 7 runs was checked for
  this.
- **A CIQ-bound test still skips.** Neither checkout links git-ignored data, unchanged. Its own
  reason is printed.
- **The page sides' code trees** (`<out>/code/<side>`) are still `git archive` extracts. No test
  runs there.
