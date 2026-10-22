---
id: 2026-10-22-theme-intelligence-regrade-keeps-carried
status: recorded
date: 2026-10-22
prs: []
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
- **The fix is on the reading side.** A version written by a re-grade also reads on what the
  version before it only CARRIED, through the same rule an unreviewed version uses:
  - the same line by its words (or its id);
  - the origin kept, so the key and any dismissal stay;
  - a changed line reads NOT RE-REVIEWED;
  - a removed line is listed as removed.
  - An analyst correction closes the corrected line's earlier findings, as it does for copied
    ones.
  - A re-grade shows no "not reviewed" banner: its findings say which review made them.
  - `Engine.reassess` is unchanged: what it copies, it copies as before.
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

**HOW VERIFIED.**
- **The previously-broken case, end to end** on the real pipeline with the offline fixture
  articles: a reviewed scan (2 findings), then a scan without the review, for each of the three
  ways a review does not run (`--no-review`, an exhausted budget, no model client).
  - One finding is dismissed, then two re-grades follow, each with an analyst correction of
    another line.
  - Both findings stay on, with their keys and origin (version 1). The dismissal holds through
    both re-grades.
  - The rendered card's JSON lists both warnings and the dismissal.
  - Before the fix, the same sequence read 0 findings.
- **Pins** in `tests/test_theme_intelligence_review_carry.py`:
  - the case above (×3);
  - a correction of a carried line closes it, neither open nor listed as removed;
  - NEGATIVE: a re-grade after a REVIEWED version carries nothing and removes nothing, and its
    findings are its copies with that review's origin.
- **Mutation:** 5 mutants, all killed (among them the pre-fix reading, and every version read as
  a re-grade).
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
- **A re-grade's card lists removed findings only on the desk.** The card's own list sits under
  the "not reviewed" banner, which a re-grade does not show.
