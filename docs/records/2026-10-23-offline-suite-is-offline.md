---
id: 2026-10-23-offline-suite-is-offline
status: shipped
date: 2026-10-23
prs: [786]
supersedes:
superseded-by:
---

# The offline suite is offline: the last SEC-dependent pin runs on a seeded temp Config, and a fresh checkout with the network refused passes in full

**WHAT.** `tests/test_synthesis_write_block.py::test_the_failure_is_counted_as_an_error_not_a_flag`
now calls `assemble_cohort([fin], cfg=cfg)`. `cfg` is a temporary Config seeded by
`tests/sec_offline_support.seed_sec_cache` (added in #785), and the call runs under `no_network`.
The test's assertions are unchanged. The refusal message in `no_network` now says "a pin" rather
than "a maintenance pin", because the helper serves more than the maintenance files.

**WHY.** The test called `assemble_cohort([fin])` with no `cfg`, which means the DEFAULT Config:
the checkout's own `data/`. `assemble_cohort` preloads the resolver index before any worker runs.
So on a fresh checkout (no `data/cache`):

- it fetched SEC's `company_tickers.json` live inside `pytest -m "not network"`;
- as a side effect, it created `data/cache/` in the checkout.

#785's full-suite run found it: on a fresh checkout of `ca17bc05` with #785 applied and outbound
traffic refused, the suite gave 6,385 passed and 1 failed, and this test was the 1. It is the ninth
and last SEC-dependent test in the offline suite.

**HOW VERIFIED.**

- **This test, fresh checkout, network refused:** 7 passed in `test_synthesis_write_block.py`, in
  2.1 s, and no `data/cache` created.
- **The test still does its job.** Narrowing `assemble_cohort`'s handler from `except Exception`
  to `except ValueError` turns it red with `DossierAssemblyError: TEST: synthesis returned NOTHING
  — refusing to write`.
- **The guard works.** Dropping the `seed_sec_cache(cfg)` call turns it red at `no_network`
  ("a pin reached for the network …"). Both mutants were restored.
- **The full offline suite, fresh checkout, outbound refused: 6,386 passed, 529 skipped, 37
  deselected, 0 failed, in 183 s.** For comparison: before #785 the two maintenance files alone
  failed 8 under this condition, and with #785 alone the full suite failed 1 (this test). No
  full-suite run was made before #785. Afterwards `git status` shows the checkout unchanged. One empty `data/cache/sec/`
  directory is created by a test's `ensure_dirs` on the default Config, with no file written and no
  fetch made.

**BOUNDARY.**

- **"Fresh checkout."** A `git worktree` of this branch, which is #785's head `93a16a2b` plus this
  change, with no `data/cache`.
- **"Network refused."** `HTTPS_PROXY`/`HTTP_PROXY` pointed at a closed local port.
- **Counts.** One run, on the operator's Mac, on 2026-10-23.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The cost.** None beyond #785's fixtures: the test reuses them.
- **ACCEPTED: the test now runs on a temp Config, not the checkout's `data/`.** The only things
  `assemble_cohort` reads before `assemble_one` (which the test replaces) are the resolver index
  (seeded), `graph_coverage.json` (absent is read as no edges) and the manual store path (not read
  here). So nothing the assertions depend on is lost.
