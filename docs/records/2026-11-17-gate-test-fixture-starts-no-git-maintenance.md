---
status: shipped
date: 2026-11-17
prs: [1103]
supersedes:
superseded-by:
---

# The gate guard's test fixture starts no git maintenance, so the walk it takes has no other writer

**WHAT.** `tests/test_gate_on_workers.py`'s `_checkout` commits into a temp repo, then walks it
(`rglob` + `lstat`). The commit started a detached `git maintenance run --auto`, which creates
and removes `.git/objects/maintenance.lock`. On CI gate run 44051868311 (PR #1099's head
`d33f45ca`, git 2.56.1) that lock was listed by `rglob` and gone by `lstat`, which raised
`FileNotFoundError` and failed the gate on a change that touches none of the file. `_git` now
passes `-c maintenance.auto=false -c gc.auto=0`, so the fixture's repo has no writer but the test.

**WHY.** I removed the cause and did not tolerate it. The repo is private to the test, and
auto-maintenance was its only background writer. Skipping a vanished entry would guard against
a writer that does not exist. gate.yml's real guard does not have this race: both of its
`find`s prune `./.git`.

**HOW VERIFIED.** `test_the_checkout_starts_no_git_maintenance_beside_its_walk` reads git's own
trace (`GIT_TRACE`) of `_checkout`:
- it must show the commit;
- it must show no `maintenance run` or `gc --auto`.

Whether git starts maintenance is decided by config, not timing, so the pin is deterministic.
With main's `_git` it failed, listing the spawned `git maintenance run --auto --quiet --detach`;
at head it passes.

**BOUNDARY.** "1 failed of 11,843" is gate run 44051868311, attempt 1: 1 failed + 11,842 passed,
under `-m "not network"`, with 675 skipped and 7 xfailed beside it. The trace pin was run on
Apple Git 2.50.1 (main's `_git` against head's, 2026-11-17). Whether git 2.56.1 honours
`maintenance.auto=false` the same way is first checked by #1103's own gate run.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Nothing accepted. The lock never appeared on the Mac: 0 of
40 commits, with either set of flags. The CI log is the race's only evidence, and the trace is
what makes the pin independent of it.
