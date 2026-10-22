---
id: 2026-10-22-theme-intelligence-regrade-keeps-carried
status: recorded
date: 2026-10-22
prs: [779]
supersedes:
superseded-by:
---

# Theme intelligence: a re-grade keeps the findings an unreviewed version carried — it never reads clean

**WHAT.** Items 2 and 3 of the open list. Operator, 2026-10-22: "yes, start item 2 and 3".

**Item 2 — the gap found while fixing #777** (`2026-10-22-theme-intelligence-finding-keeps-origin.md`).
- **The gap.** A re-grade (`reassess`) copies the card-review findings stored in the RUN of the
  version before it. A version written without the review (`--no-review`, an exhausted review
  budget, no model client) stores none: `report._findings` carries the earlier review's findings
  onto it. So a re-grade of such a version copied nothing and read CLEAN.
  - It breaks the rule in `_findings`: "A version written WITHOUT the card review … is never read
    as clean".
  - On the offline fixture, the unreviewed version's 2 open findings fell to 0 after a re-grade.
- **The fix is on the reading side.** A re-grade of an unreviewed version is read as
  unreviewed itself (`report._regrade_not_run`). The reason walks back through re-grades to the
  run whose review did not run, so it never nests. Everything open on the version before is
  carried on by the rule an unreviewed version already uses:
  - the same line by its words (or its id);
  - the origin kept, so the key and any dismissal stay;
  - a changed line reads NOT RE-REVIEWED;
  - a removed line is listed, on the card's "not reviewed" note and on the desk.
  - A line THIS re-grade's analyst correction rewrote has its earlier findings closed, as copied
    ones are.
  - A re-grade of a REVIEWED version is unchanged: its findings are the copies it stored.
  - `Engine.reassess` is unchanged.
- **The code review of this PR** (`/code-review high`, 6 findings; operator: "/code-review high
  779 and apply fixes"):
  - **The card could read clean.** The first version of the fix carried the findings on but left
    the re-grade "reviewed". The card lists findings on removed lines only inside the "not
    reviewed" note, so a removed-line finding the desk listed open left the card reading "No
    unresolved review findings". The re-grade now carries the not-run status, which also gives
    the card's note and the desk's "Version N was not reviewed" item.
  - **A correction closes a line only when it rewrote it** (`here in corrected and not same`).
    A copied correction note of an earlier run no longer closes an unchanged line's finding.
    This case is unreachable under the current writers.
  - **The test restates a line with its claim's own words**, a structured value, no longer by
    splitting the rendered figure label out of the line.
  - **Two findings not changed.** The altitude finding: the fix keys on the run mode, while
    `Engine.reassess` writing copies of carried findings would hold for every writer. The read
    side follows the rule unreviewed versions already use, and no other mode writes a version
    without a review. The efficiency finding: one run lookup per version read, memoised per
    render.
  - **An existing pin changes on purpose.**
    `test_a_thesis_new_and_downgraded_in_one_week_is_one_row_showing_both` builds its pipeline
    with the card review OFF, so version 1 is unreviewed — and so is the re-grade of it. Its
    desk row now shows "1 finding", the "not reviewed" item. The old expectation recorded the
    clean reading this PR removes.
- **No existing data can change.** Across all versions of the registry of record's 30 theses, 0
  were written without the review, and none of its 14 re-grades follows such a version.

**Item 3 — checkouts older than schema v9 (#777, dd85adf5).** An inventory of every git worktree
of this repo on this machine (read-only):
- **No checkout is set up to pull the shared registry:** none holds a `state_sync.json`.
- **The one other theme-intelligence registry** is in the retired `theme-intelligence` worktree:
  schema v5, 2 runs, last written 2026-10-14. It is not a copy of the shared registry.
- **The primary checkout** (`mosaic-theory`, branch main) is **14 commits behind origin/main**
  and holds another session's uncommitted changes, so it was not touched. Before any
  theme-intelligence command there, update it (`git pull`): code before dd85adf5 has no import
  guard and fails at the first copied issue it reads.
- The weekly Actions job runs main, so it reads v9.
- **Done the same day:** the operator ran `git pull` there, and the primary checkout went from
  06c9a5ed to dd85adf5 (schema v9, with the import guard), keeping that session's
  uncommitted changes.

**HOW VERIFIED.**
- **The previously-broken case, end to end** on the real pipeline with the offline fixture
  articles: a reviewed scan (2 findings), then a scan without the review, for each of the three
  ways a review does not run (`--no-review`, an exhausted budget, no model client).
  - One finding is dismissed, then two re-grades follow, each with an analyst correction of
    another line.
  - Both findings stay on, with their keys and origin (version 1). The dismissal holds through
    both re-grades.
  - The rendered card's JSON lists both warnings and the dismissal, and the re-grade's not-run
    reason names version 2.
  - Before the fix, the same sequence read 0 findings.
- **Pins** in `tests/test_theme_intelligence_review_carry.py`:
  - the case above (×3);
  - a correction of a carried line closes it, neither open nor listed as removed;
  - a re-grade lists a carried finding whose line it removed, on the card's note, with no "No
    unresolved review findings";
  - a changed line reads NOT RE-REVIEWED;
  - the removed list the version before handed on is kept;
  - NEGATIVE: a re-grade after a REVIEWED version carries nothing and removes nothing, and its
    findings are its copies with that review's origin.
- **Mutation, after the review:** 7 mutants; 6 killed, among them the pre-fix reading, every
  version read as a re-grade, and a re-grade after a reviewed version read as unreviewed.
  - The survivor, "any correction note closes a line", is equivalent under the current writers:
    a copied correction note reaches a re-grade only when the version before it was also a
    re-grade, and a re-grade after a reviewed version carries nothing.
  - **A correction to this PR's first run:** it reported "5 mutants, all killed". At that point
    an existing test was failing on the fix itself, and the runner stops at the first failure,
    so a kill could have come from that failure. All kills here are on a green baseline.
- **The registry of record reads unchanged** (a fresh import of `theme-intelligence-state`
  cd0f4a08, this branch):
  - `review list` reads 1 open / 22 dismissed;
  - all 23 runs of the 2026-10-22 decisions pass QA;
  - a desk publish matches the live one on all 102 pages beyond their stamps (`index.json` differs
    only in its `retired` carry);
  - a plain re-grade of the 21 theses not archived keeps 1 open / 22 dismissed.
- **Not shown on real data:** the broken case itself. The registry has no unreviewed version,
  and making one needs a paid re-read.
- **Suite:** see the PR.

**BOUNDARY.**
- Registry `theme-intelligence-state` cd0f4a08, imported fresh on 2026-10-22 (UTC). Code: this
  branch on main dd85adf5.
- Version counts are over all versions of all 30 theses, archived included.
- The worktree inventory is `git worktree list` on this machine, 2026-10-22.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0, with no model call, no write change and no migration.
- **A re-grade of an unreviewed version adds the desk's "Version N was not reviewed" item**, as
  the unreviewed version before it did.
