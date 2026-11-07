---
status: shipped
date: 2026-11-07
prs: [928]
supersedes:
superseded-by:
---

# A test named a branch commit that #923's squash merge left outside main's history, so main's gate went red at a9c59287; the pin now reads the record as merged

**WHAT.**
- **The test.**
  `tests/test_evals_round2.py::test_the_motivated_rule_reads_commit_bodies_and_in_flight_records`
  read `4449189d:docs/records/2026-11-06-the-fact-layers-labels-describe-never-judge.md`.
  `in_flight_names` reads the records of a fix in flight at the panel's freeze, and #923's record
  at its branch head `4449189d` was that record.
- **The break.** #923 was squash-merged as `a9c59287` on 2026-11-07. Its branch commits are
  reachable from no ref a CI checkout fetches, so `git show` exits 128.
  - main's own `gate` failed at `a9c59287` (run 42392613429).
  - #927's failed at `72d5b3b7` (run 42403763687): 1 failed, 9,368 passed.
  - The test passed locally only because this machine's object store still holds the branch's
    commits.
- **The fix.** The pin reads the record as merged, at `a9c59287`. That record names the same five
  tickers the pin asserts (MCK, NKE, ROST, CNXC, LLY); in all it names 28 of the corpus names,
  against 27 at `4449189d` (EPAM added).
- **What does not change.** `vinci/evals/synthesis_panel.json` still records `4449189d` as the
  in-flight record the freeze read. That is a record of what the freeze read, not something read
  at run time, so it is left alone (a change would be a silent re-freeze). `python -m vinci.evals
  panel` still yields the frozen six on a main-only clone: it reads the frozen file, not that ref.

**WHY.** A squash merge keeps the PR's diff and discards its commits. A test that names one of them
works on the author's machine and in the PR's own CI, where the branch exists. It breaks for
everyone the moment the PR merges and the branch goes away. It goes red on main, not on the PR
that introduced it.

**HOW VERIFIED.**
- **Fail-first.** In a clone of main alone from GitHub (`git clone --single-branch --branch main
  --no-tags`; `4449189d` absent, the freeze `bcda7ce3` present), the test fails at `a9c59287` with
  CI's `CalledProcessError`. With the fix it passes, and `tests/test_evals_round2.py` passes whole
  (23 passed).
- **The rest of the suite.** A scan finds no other test that executes an unreachable commit as a
  git ref. The 8 other short SHAs present only in the local object store (`0dbe8f97`, `3ee93db3`,
  `91e77597`, `97b31a78`, `a06e6756`, `a946e82d`, `e91490ae`, `ee754dd8`) are provenance text in
  docstrings, comments and fixture metadata.

**INCIDENT → INVARIANT (shipped N).** *A test may execute a git ref only if it is reachable from
main.*
- **Proposed, not built here** (coordinator, 2026-11-08): a lint over `tests/` and `vinci/evals/`
  that finds each hex literal handed to git (`git show`, `cat-file`, `merge-base`, a `ref:path`
  string) and requires `git merge-base --is-ancestor <sha> origin/main`.
- **Open:** STATE §5.0 row 56. Until it ships, a reviewer of any PR that adds a commit literal to
  a test checks it by hand.

**BOUNDARY.**
- **The scan:** hex literals of 8–40 characters bounded by a quote, colon, caret, backtick or space,
  in `tests/` and `vinci/evals/*.py` at `a9c59287`.
- **Its result:** 49 resolve as commits in the main-only clone; 9 resolve only in this machine's
  object store.
- **The command,** run in the main-only clone:
  `grep -rhoE "[\"'\` ]([0-9a-f]{8,40})[\"':\`^ ]" tests vinci/evals/*.py | grep -oE "[0-9a-f]{8,40}" | sort -u`,
  then `git cat-file -e <sha>^{commit}` on each, in the clone and in this checkout.
- **The ticker counts:** `in_flight_names` over the frozen panel file's page list, at each ref.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The pin now reads a later text** than the freeze read: the record as merged, after #923's
  review rounds, not the in-flight draft. Accepted: it pins the reader (`in_flight_names` reads a
  `ref:path` record), and the five names it asserts are in both texts.
- **Other provenance SHAs in docstrings are unreachable from main.** They are prose and run
  nothing. A reader cannot `git show` them from a fresh clone, so they are citations with a
  half-life.
