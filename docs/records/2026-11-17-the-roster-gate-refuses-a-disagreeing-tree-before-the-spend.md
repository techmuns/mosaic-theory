---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# #1092's three review follow-ups, each verified on main `71573a69` before it was fixed: `vinci dossier` refuses a tree whose pages disagree with the roster before any model client (a stray `data/dossiers/ZZZZ/` cost a whole paid build of an active name, refused only at the mirror); the build twin refuses a status the roster does not name (a `"Watch"` line dropped AMZN from the mirror in silence); the fact scope's stated rule names the intake names it walks; nothing rendered moves ($0)

**WHERE THESE CAME FROM.** Another session ran `/code-review high --fix` in the wrong checkout,
which reviewed #1092 (the coverage roster, `4889ddba`) by accident. It left three findings as an
unverified patch in the session notes and reverted them. This PR checks each finding on current
main before fixing it. The patch was a starting point. Two of its three fixes are kept close to
as written. Its tests were rewritten so each fails first for the reason stated. The six lower
findings that reviewer skipped are not addressed here.

**WHAT.**
1. **A refusal after the spend.** `vinci dossier` (`_cmd_dossier`) checked only that each
   finalist is buildable (`coverage_roster.require_buildable`). The mirror it runs once a page is
   written (`mirror_to_frontend` → `frontend/build.py` `_covered_pages`) refuses any tree whose
   pages disagree with the roster, but only after the model calls are paid. The command now calls
   `coverage_roster.covered_pages` before any client exists, and refuses with exit 1, naming every
   disagreement.
   - **Stricter than the mirror, on purpose.** An ACTIVE name whose page has vanished is refused
     even when it is the name being built, though a successful build would have re-written the
     page and the mirror would then pass. The roster's contract is that an active page that
     vanishes is refused. Its page is restored from git at $0, never rebuilt at a cost. A first
     page goes through `intake`, whose page is optional, so a first build is unaffected
     (`test_a_first_build_needs_one_appended_intake_line` still passes). The strict check is also
     the only one that guarantees no refusal at the mirror from a disagreement that existed
     before the spend. A cohort in which that name's build failed while another's succeeded would
     still reach the mirror and be refused there.
2. **The build twin accepted any status.** `frontend/build.py` `_covered_pages`, the stdlib twin
   of the roster reader, read each name's latest status as any string. A paged name whose latest
   line says `"Watch"` was neither covered nor a disagreement, so the mirror dropped it and the
   build passed. The twin now refuses a status outside `_STATUSES`, a literal pinned equal to
   `vinci.coverage_roster.STATUSES`.
3. **The scope's stated boundary.** `vinci/facts/scope.py` `RULE` said "the coverage roster's
   active and watch names". `covered_pages` also returns an intake name once its first page is
   committed, and the scope walks it. The rule now says so. `RULE` is the `scope.rule` an ingest
   writes into its manifest.

**WHY (2, the decision).** #1092's round 0b dismissed "the twin is laxer" because the strict
reader runs in the suite. That is true, and the suite still catches a `"Watch"` line before any
merge: `test_the_committed_roster_reads_and_every_move_cites_its_ruling` reads the file strictly.
But the twin runs where no strict read has happened first:
- a hand run of `python frontend/build.py`: RUNBOOKS' monthly-scoring and monitor mirror steps,
  and the retirement procedure in `docs/records/2026-11-17-the-coverage-roster.md`;
- `vinci ciq-reread` and `vinci caveat-reword`, which mirror with no roster read at all;
- the driver-facts and transcript-cut passes, when given their names (`--tickers` / `--pages`);
- `bin/commit` and `vinci.impact`, which run the build beside the suite.

A roster line is typed by hand from a template (RUNBOOKS §i step 1b), so a mis-cased status is a
plausible typo. On those paths it would delete that name's served page from
`frontend/dossiers/` without a word. The twin's own docstring promises "never a quiet publish of
whatever is on disk". The cost is four lines, and a literal held equal to the reader's by a pin.
So: yes.

**HOW VERIFIED.**
- **(1), the real command on main, model calls trapped ($0).** A scratch script ran the real
  `vinci dossier --ticker VRRM` through `cli.main`. The model client's `from_config` was trapped,
  recording the build and returning an object that raises on any call. `assemble_cohort` (the
  paid phases) was stubbed to report one written page, so the run reached the mirror. The run
  used an untracked `data/dossiers/ZZZZ/dossier.json` and a clone of the primary's store, both
  removed afterwards. Output at `71573a69`:
  ```
  TRAP: a model client was BUILT — a real run spends from here
  TRAP: assemble_cohort reached for ['VRRM'] — the paid phases (stubbed)
  SystemExit raised AFTER ['client', 'cohort']: the committed pages disagree with data/coverage_roster.jsonl: ZZZZ has a committed page and no line in the roster
  ```
  On the fix:
  ```
  === dossier · REFUSED before any model call: the committed pages disagree with data/coverage_roster.jsonl on 1 name(s): ZZZZ has a committed page and no line in the coverage roster ===
  exit 1; events []
  ```
  The control, the same run with no stray page and the mirror stubbed: `exit 0; events ['client',
  'cohort']`. An agreeing tree still builds.
- **(2), the twin on a real tree.** The scratch tree linked all 26 committed pages and the roster,
  with AMZN's latest line rewritten to `"Watch"`. On main's `frontend/build.py` (`git show
  71573a69:frontend/build.py`): `publishes 25 of 26 pages; AMZN published: False; no error`. The
  build's `main` then clears `frontend/dossiers` and re-copies only that list. On the fix:
  `REFUSED — data/coverage_roster.jsonl: AMZN's status 'Watch' is not one of ('intake', 'active',
  'watch', 'retired')`.
- **The pins, each failing first.** With only the tests changed, `tests/test_coverage_roster.py`
  ran 7 failed and 68 passed. The 7 are exactly the new nodes:
  - `test_assembly_refuses_a_tree_the_roster_disagrees_with_before_any_model_client`, five
    cases (`stray_page`, the observed shape, plus `no_roster_line`, `no_page`, `active_no_page`
    and `retired_paged`). Each failed `assert (0 == 1)`: the build ran, its client built. They
    drive the path that BUILDS A CLIENT (`no_llm=False`), as #1092's R6 requires.
  - `test_the_build_twin_refuses_a_status_the_roster_does_not_name`: `DID NOT RAISE SystemExit`.
    It also checks that the strict reader refuses the same tree, and that `_STATUSES` equals the
    reader's.
  - `test_the_fact_scopes_stated_rule_names_every_status_it_walks`: `assert ['intake'] == []`. It
    takes the statuses from the names the real scope walks on an `intake_paged` tree, never from a
    literal list.

  With the fix: 75 passed.
- **Nothing rendered moves.** `python frontend/build.py` on the committed tree published 26
  pages and left no tracked file changed. No page, mirror or manifest is in the diff. The two
  committed fact-store manifests carry an older, pre-roster wording of `RULE`, and nothing
  compares it. The new wording reaches only the next ingest's manifest.

**BOUNDARY.**
- **Commit and tree.** Every count is at main `71573a69`, on its committed tree: 26 pages
  (`data/dossiers/*/dossier.json`) and 28 roster moves (11 active, 15 watch, 2 retired).
- **The replay.** One name, VRRM, one run per side. The test cases use `_a("active")`, the
  roster's first active name.
- **The test counts.** 7 / 68 / 75 are nodes of `tests/test_coverage_roster.py` alone, run with
  `-o addopts=""`. The full offline suite's count is in the PR body.
- **The twin's path list.** Found by `git grep` for `mirror_to_frontend` and `frontend/build.py`
  over `vinci/`, `scripts/`, `bin/` and `frontend/`. It is the list of callers, not a measure of
  how often each runs.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- An active name whose page vanished can no longer be rebuilt over the hole. Restoring the page
  from git ($0) is the remedy, and the refusal names the name. Falsifier: a documented workflow
  that deletes an active page before rebuilding it. None was found: in RUNBOOKS §i, or by
  `git grep rmtree -- vinci`, where no hit names a dossier path.
- A malformed or absent roster still ends `vinci dossier` in a traceback
  (`CoverageRosterError`, not caught). It does so before any client, so it is loud and costs
  nothing. It is one of the six lower findings left alone.
