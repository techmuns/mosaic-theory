---
id:
status: shipped
date: 2026-11-17
prs: [1110]
supersedes:
superseded-by:
---

# The impact check's fail-first stage runs each side in its own clone of the repository, so a test that asks git runs as it does in a checkout and nothing it writes reaches the repository: #1104's 7 hooks nodes that FAILED at both refs now pass at both, and #1098's 10 frozen-cut nodes that SKIPPED now run

**WHAT.**
- **`vinci.impact.run.fail_first`** runs head's changed tests in two throwaway clones of the
  repository at head's commit (`_checkout`, `_checkouts`), no longer in a `git archive` extract.
  Each clone:
  - is made with `git clone --shared --no-checkout`, so it borrows the repository's objects and
    copies none;
  - has its `origin/*` fetched from the repository's own `refs/remotes/origin/*`, `--prune`d to
    exactly those;
  - has its push URL set to `no-push://…`, so a push goes nowhere;
  - is checked out detached at head's commit.
- **Base's clone** then swaps `vinci/` for base's in its index as well as its files (`git rm -r
  vinci`, then `git checkout <base> -- vinci`), so git there lists, diffs and reads base's code.
- **The placeholder for a name base lacks** (`_SHIM`) is written beside the checkout, on the
  child's `PYTHONPATH`, never inside it. In a checkout, git would list it as an untracked file at
  base alone.
- **No repository-local git variable steers the stage.** Every git call the stage makes, and each
  side's pytest, runs without the variables git itself names repository-local
  (`git rev-parse --local-env-vars`: `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`,
  `GIT_COMMON_DIR`, and 12 more).
- **Nothing is registered in the repository.** The clones are removed when the tests end. A run
  killed mid-stage leaves them as two folders under `--out` and nothing else. Logs and junit files
  stay.
- **The report says how part 1 ran.** The result records `checkout: "clone"`, and section 1 prints
  "each in its own clone of the repository at head's commit, base's with its `vinci/` swapped in".
  An older report, with no such field, now says its tree was "a `git archive` extract with no
  `.git`", rather than claiming a checkout it never had.
- **RUNBOOKS §o step 4.1** states the same, and the limitation below.

**WHY.** The coordinator found this on #1104 (2026-11-17), and the notes on earlier PRs record the
same shape:
- An archive extract has no `.git`, so a test that asks git about its own checkout cannot run
  there. The hooks find their checkout with `git rev-parse --show-toplevel`. With no `.git`, the
  guard printed nothing, and 7 `tests/test_claude_hooks.py` nodes FAILED at both refs, among them
  #1104's own new pin. `tests/test_frozen_pages_are_cuts.py` skips by design outside a checkout.
- Section 1 then printed them as a result: "fail at head: 7" on a PR whose tests all pass in a
  checkout, or "skipped: 10". Neither said whether those nodes fail first.
- The three fixes the brief offered:
  - **A shallow clone at the ref** has one commit. 12 `.py` files under `tests/` read
    `origin/main` (13 files in all, with one JSON fixture, at `e15659ba`), and
    `test_frozen_pages_are_cuts.py` reads commit `4889ddba`'s blobs. Those would fail or differ in
    a shallow clone: a different false signal. The gate's CI checks out with `fetch-depth: 0`.
  - **A named "needs git" bucket** would report those nodes without running them. It needs a
    detector, and a message match is a guess. A test that skips or passes vacuously without git
    would not be caught at all.
  - **A real checkout with full history.** Chosen.
- **The first cut (`6553a1ed`) used linked worktrees. Review round 1 (A) replaced them with
  clones.** A linked worktree is registered in the shared repository and shares its refs and
  config. Three of A's five points held on `6553a1ed`, each reproduced in the fixture:
  - a run killed while its tests ran left both worktrees registered, because a `finally` does not
    run on SIGTERM;
  - a test's `git tag` and `git config` landed in the repository, and the second side to write the
    tag failed on timing alone;
  - started under a hook's `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`, base's `git rm -r vinci`
    staged `M vinci/m.py` and `D vinci/only_at_head.py` in that repository's own index.

  A clone keeps all of it in its own `.git`, and needs no cleanup of anything outside `--out`.
- Two adjacent changes are required once git is present, and each is pinned by a mutation:
  - **The index swap.** Without it, a module only head has stays a tracked file missing on disk at
    base, and a test that lists `git ls-files vinci` FAILS at base alone: a false fail-first.
  - **The shim's move.** Inside the checkout, it is an untracked file at base alone.
- **The fetched `origin/*` is required too.** A plain clone names the repository's LOCAL branches
  `origin/*`. In the `~/dev` clone, local `main` is `2bd2facf` while `origin/main` is `6110795d`,
  so a stale `main` would have read as `origin/main`.

**HOW VERIFIED.** All runs are $0: no model call, and no Polygon or Tiingo pull. "Main's harness" is
`vinci/impact` at `e15659ba`. "The fix" is this branch at round 1.
- **Reproduced on #1104** (head `25759619`, base `e15659ba`, 3 changed test files, 147 nodes):
  - Main's harness: 140 pass at both and **7 FAILED at both**, exactly the 7 nodes in #1104's body
    (`test_guard_*` ×6, at `tests/test_claude_hooks.py:90/98/114/129/144/152`, and
    `test_open_now_indexes_every_row_of_the_committed_state` at `:181`). 98.4 s.
  - The same 7 nodes in real checkouts: **7 of 7 pass at head**. At base, the 5 that exist there
    **pass, 5 of 5**. The other 2 are new in #1104, and `vinci/` is identical between the refs.
  - The fix: **147 of 147 pass at both, 0 fail at head**. 213.3 s, on a loaded machine: two
    other sessions' full suites ran alongside. `6553a1ed` took 74.5 s and main's harness 98.4 s,
    both on a quieter machine.
- **#1098** (`8a71a383`, base `6b5fbe51`, 24 changed test files, 560 nodes):
  - Main's harness: 546 pass at both, 14 skipped at both. Of the 14, **10 are
    `test_frozen_pages_are_cuts.py`, "not a git checkout"**, and 4 are CIQ-bound.
  - The fix: **556 pass at both**, 4 skipped at both. All 12 frozen-cut nodes run and pass. The 4
    left are the CIQ-bound ones, "licensed CIQ bundles unavailable (never committed)", an honest
    skip: neither checkout holds git-ignored data. 52.6 s.
- **The pins** (`tests/test_impact_failfirst.py`, 8 new tests) run on real fixture repositories.
  The asks-git fixture PR's changed test file has 8 nodes. Per node, base/head:

  | node | main's harness | `6553a1ed` (worktrees) | the fix |
  |---|---|---|---|
  | `test_a_git_pin_that_fails_first` | failed / **failed** | failed / passed | failed / passed |
  | `test_a_name_only_head_defines` | failed / passed | failed / passed | failed / passed |
  | `test_a_git_pin_that_passes_at_both` | **failed / failed** | passed / passed | passed / passed |
  | `test_git_lists_exactly_the_modules_on_disk` | **failed / failed** | passed / passed | passed / passed |
  | `test_head_is_heads_commit_and_the_refs_are_the_repositorys` | **skipped / skipped** | passed / passed | passed / passed |
  | `test_a_test_that_writes_git_keeps_it_in_its_own_checkout` | **failed / failed** | one side **failed** on timing; tag and config left in the repository | passed / passed; the repository as it was |
  | `test_the_checkout_is_clean` | failed / failed | failed / passed | failed / passed: the limitation, pinned |
  | `test_a_real_failure_at_both_refs` | failed / failed | failed / failed | failed / failed (`assert 1 == 99` / `assert 2 == 99`, same line) |

  - The outer pins also cover:
    - **a run killed mid-stage**, through `python -m vinci.impact run`: SIGTERM to its process
      group once both sides' pytest is running;
    - **a run started under a hook's git variables**;
    - **three decoy worktrees** with names like part 1's own: `out/failfirst-decoy/head-tree`
      unlocked, `out/failfirstX` locked, and `other/failfirst/head-tree` locked.
  - **On `6553a1ed`, 5 of the 10 tests in the file are red**: asks-git, writes-git, the counts,
    killed run and hook env. The limitation pin and the decoy pin are green there, as they should
    be for behaviour `6553a1ed` already had. **A's mutation of `6553a1ed`'s cleanup**
    (`if path != repo.resolve():`, which removes every linked worktree) **turns the decoy pin
    red**.
  - **Each mutant of the fix fails at least one pin:**
    - N1: `origin/*` left as a plain clone names it;
    - N2: no push guard;
    - N3: the stage's git keeps `GIT_DIR` & co;
    - N4: the child pytest keeps them;
    - N5: a linked worktree instead of a clone (5 red);
    - from the first cut: `vinci/` swapped on disk only, not in the index; base's `vinci/`
      extracted, not checked out; the shim written inside the checkout.
  - An index-swap mutant first SURVIVED a weaker pin ("every tracked module is on disk" passes
    vacuously when git lists nothing). The pin was tightened to "git lists exactly the modules on
    disk, and some".
- **Nothing else moves.** Two recent merged PRs that build pages were run on main's harness and on
  the fix, with one set of inputs: store file `65cbae7d1474` (frontier 2026-11-11), the primary's
  CIQ root (277 exports on 26 pages), its HTTP cache and its `.env`. The PRs are #1105
  (`e15659ba`, base `5c9c7eac`) and #1097 (`18970909`, base `75f303b7`).
  - On both PRs, `report.md` from `### 2` to the end is **byte-identical** once durations are
    normalised.
  - In the JSON, `panel_requests`, `frontend`, `downstream`, `page_reach`, `same_code` and the
    page results, less their wall-clock timings, are identical.
  - Part 1's per-node outcomes are identical too. #1105 has 71 nodes: 51 pass at both, 11 skipped
    and 9 fail first. #1097 has 131 nodes: 88 pass at both, 38 fail first (7 failed and 31 errors
    at base), 4 skipped, and 1 error at base with no node at head (a file that did not collect).
    Every skip names a CIQ or IT export, or a name base lacks.
  - The fix's runs reused main's page builds, by the build key's normal rule: same code, inputs,
    store and UTC day. 50 of 52 sides were kept. PARR's 2 were re-built because a failed build is
    never reused: PARR fails at both sides with `CiqMislabelledError`, its known mislabelled
    quarterly export.
- **Nothing is registered.** After the runs above, the shared repository's `git worktree list` held
  no `failfirst/` path.

**BOUNDARY.**
- **Node counts** are pytest node ids in each PR's changed `tests/test_*.py` files that exist at
  head, run `-m "not network"` with no git-ignored data. Main's harness was run on 2026-11-17
  between 14:51 and 15:09 UTC, and the fix at round 1 between 18:27 and 18:39 UTC, at the shas named above.
- **"Main's harness"** is `vinci/impact` at `e15659ba`. **"The fix"** is this branch's round-1
  working tree.
- **The fixture counts** are over the asks-git fixture PR's one changed test file: 8 nodes.
- **The real-checkout check on #1104** ran the 7 named nodes only.
- **Durations** are part 1's own `seconds`.
- **"12 `.py` files read `origin/main`"** is `git grep -l origin/main e15659ba -- 'tests/*.py'`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Base's checkout is head's COMMIT with base's `vinci/` staged over it. PINNED, not only
  accepted** (`test_bases_checkout_is_heads_commit_with_bases_vinci_staged`). This is what the
  archive extract also was (head's tree with base's `vinci/`), now stated. At base, `git rev-parse
  HEAD` is head's sha, and `git status` and `git diff HEAD` show base's `vinci/` as staged. A test
  asserting a clean checkout therefore fails at base alone, and reads as "fails first" for no
  reason in the code. The pin holds the exact outcome, base FAILED with
  `D vinci/only_at_head.py ; M vinci/m.py` and head passed, so a regression and a later fix both
  turn it red, differently.
  - Measured at `e15659ba`: no file in `tests/` asserts a clean status or `git diff HEAD` of its
    own checkout. A grep for `porcelain` and `diff --quiet HEAD` beside `ROOT` finds only a
    temporary repository (`test_gate_on_workers.py`).
  - `test_duplicate_definitions.py` diffs the working tree against a commit, so at base it reads
    base's code, as a checkout of base would.
  - A synthetic base commit would make the tree clean, but it would change HEAD's sha and its
    history count instead.
- **Disk.** While the tests run, part 1 holds two full checkouts: 284 MB each (4,025 tracked files
  at `e15659ba`), where the extract and its APFS clone shared blocks. Both are removed when the
  stage ends. A killed run leaves them under its `--out`, which is that run's to delete. Main's
  harness left its trees in every run folder: #1104's run folder held 559 MB after the run.
- **The run's own reads of the repository still inherit the environment.** `stamp.git` (the stamp,
  the changed paths) is unchanged here. Under a hook's own `GIT_DIR` they name the same
  repository, so they read the same. A `GIT_DIR` naming a different repository would misdirect the
  whole run, not part 1 alone, and is outside this PR.
- **A CIQ-bound test still skips.** Neither checkout links git-ignored data, unchanged. Its own
  reason is printed.
- **The page sides' code trees** (`<out>/code/<side>`) are still `git archive` extracts. No test
  runs there.
