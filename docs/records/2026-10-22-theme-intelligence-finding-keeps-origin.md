---
id: 2026-10-22-theme-intelligence-finding-keeps-origin
status: recorded
date: 2026-10-22
prs: [777]
supersedes:
superseded-by:
---

# Theme intelligence: a re-grade's copy of a review finding keeps the origin of the finding it copies — a dismissal survives a correction

**WHAT.** Closes the agent's open item in `2026-10-22-theme-intelligence-uploads-one-step.md`:
"a re-grade or correction re-records open review findings as new". Operator, 2026-10-22: "yes,
start item 2".

- **The defect, shown on the registry of record first.** On a scratch copy of
  `theme-intelligence-state` cd0f4a08, run with main df07ff4f, one analyst correction rewords
  TH-8DDD7B2868 s02.0, a line with no finding. All 4 of the thesis's dismissed findings reopen:
  "0 open, 4 dismissed" becomes "4 open, 0 dismissed".
  - Each reopened finding now reads "raised by the review of version 2 (2026-10-22)", but no
    review ran on version 2.
  - The cause: `Engine.reassess` re-records the card review's findings into its own run as
    copies, and `report._findings` read every copy as raised by the re-graded version's own
    review. A finding's key (`finding_key`) includes that version, so every copy got a new key
    and no dismissal covered it.
- **The fix:**
  - **The copy carries a structured link.** `VerificationIssue.copied_from` holds the issue it
    re-records. `Engine.reassess` writes it, and it is serialized only when set, so every other
    stored issue is byte-identical.
  - **The copy keeps its origin.** `report._keep_origins` gives a copy's finding the origin of
    the finding it copies, as read on the previous version: its version, its date, and the line
    as the review read it. Its key, and a reviewer's dismissal, survive the re-grade, including
    a second re-grade (a copy of a copy).
  - **Fail-safe.** When a copy's source is not found on the previous version, or no longer reads
    as the same finding, the copy keeps its own version's origin. It gets a new key and reads
    OPEN, so no dismissal binds to it unless a reviewer gave one.
- **The 14 versions re-graded today keep their keys.** Their copies predate the link and carry
  none, so they read as before. Each finding there still reads "raised by the review of version
  N (2026-10-22)" — the re-graded version — because the 22 dismissals are bound to those keys. A
  later re-grade keeps those keys, since a copy of such a copy inherits what that copy reads as.
  Their true origin is not restored: doing so would reopen the 22.

- **The code review of this PR** (`/code-review high`, 5 findings; operator: "apply fixes and
  then merge"):
  - **A moved line kept its dismissal only in part.** The copy inherited the origin but kept its
    own stored words, which name the line's id. A re-grade that renumbers the line (a price line
    refiled last under section 07, so the earnings line after it moves up) still changed the key.
    The copy now keeps the review's words too, as a finding carried onto an unreviewed version
    already does.
  - **Registry schema v9**, a step with no table change: a stored issue's payload may now carry
    `copied_from`, which code before it rejects (payloads are validated with `extra="forbid"`).
    Older code refuses a v9 DATABASE up front (`migrate`), and `Store.import_jsonl` now refuses an
    EXPORT made at a newer schema. Before, it inserted the rows and failed mid-command. The guard
    protects from now on: a checkout made before this merge has no guard, and fails at the first
    copied issue it reads — **update a checkout before `state pull`.**
  - One previous-version helper (`report._previous`) is shared by the review carry and the origin
    inheritance, and the test helper is typed.

**HOW VERIFIED.**
- **The previously-broken case, on real data:** the same correction on the same scratch copy,
  run with this branch. TH-8DDD7B2868 reads "0 open (0 dismissible), 4 dismissed" before and
  after, with the same 4 keys (F-187044af477b, F-d7b1e0f3e131, F-fc87d6ad558e, F-dfdc5b36ccec).
  Each still reads "raised by the review of version 1 (2026-10-14)". QA of the reassess run:
  21/21.
- **The chain, on real data:** TH-C1889ABBA5, re-graded today, is corrected again (s03.2).
  "2 dismissed" before and after, with the same keys (F-e52d9cf1470d, F-99c9ca771d97).
- **A plain re-grade of every thesis, with no correction** (a scratch copy of cd0f4a08,
  `reassess --as-of 2026-10-29` over the 21 not archived; 4 change):
  - with main df07ff4f, the queue goes from 1 open / 22 dismissed to **6 open / 17 dismissed**;
    5 dismissals reopen, each "raised by the review of" its re-graded version;
  - with this branch it stays **1 open / 22 dismissed**;
  - the v8 export imports into v9 cleanly.
- **The registry of record reads unchanged under the fix** (a fresh import of cd0f4a08, this
  branch):
  - `review list`: 23 findings on 12 theses not archived — 1 open, 22 dismissed, as before;
  - all 23 runs of today's decisions (1 reassess, 22 review) pass QA;
  - a desk publish matches the live one (main df07ff4f) on all 102 pages beyond their stamps.
    `index.json` differs only in its `retired` carry, since the scratch publish had no previous
    publication.
- **Pins** in `tests/test_theme_intelligence_product_redesign.py`:
  - a dismissal survives a correction of another line and a second re-grade a week later (key,
    origin version and date; QA's check of the dismissal; the rendered card's JSON);
  - a withheld line's copy keeps its origin (its age on the desk);
  - NEGATIVE: copies written without the link read as before, and a later re-grade keeps their
    key;
  - the fail-safe: a copy whose source is nowhere reads OPEN under a new key;
  - an issue without the link serializes as before;
  - a dismissal survives a re-grade that moves its line to a new id;
  - in `tests/test_theme_intelligence_review_resolution.py`: old code refuses an export from a
    newer schema and its database, and reads its own export (NEGATIVE).
- **Mutation:** 8 mutants after one replacement; 7 killed and 1 survivor (equivalent, below).
  After the review: 11 mutants (the moved line, the import guard both ways, the migrations an
  import is given), all killed.
  - One mutant replaced the fail-safe with "fall back to the first issue in the run". It was
    killed only sometimes: issue ids derive from timestamped run ids, so their order varies
    between runs. It was replaced by the plausible form of the bug, "fall back to the line's
    previous finding", which was killed in 3 runs of 3.
  - **The survivor drops the same-finding check.** It is equivalent under the current writers:
    every REVIEW_ finding one run records on a line comes from the same review, so the origin
    cannot differ. The check stays, as the guard for a future writer.
- **Suite:** see the PR.

**FOUND, not fixed (out of scope; a task is proposed).** A re-grade copies findings only from
the previous version's OWN run. When that version was written without the card review, its
findings are carried onto it from an earlier version, not stored in its run, so the re-grade
copies none and the new version reads clean.
- Shown on the offline fixture: 2 findings on the unreviewed version, 0 after the re-grade.
- Latent on the registry of record: no current, non-archived version at cd0f4a08 was written
  without the review.

**BOUNDARY.** Registry `theme-intelligence-state` cd0f4a08, imported fresh on 2026-10-22 (UTC).
Code: this branch on main df07ff4f. Queue counts are `review list` over theses not archived.
Page counts are over a publication's `site/**`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0, with no model call.
- **Schema v9** adds no table: a registry migrates on first open, and older code refuses it.
- **The 14 versions re-graded on 2026-10-22 keep their re-graded version as each finding's
  origin.** Restoring the true origin would change the keys the 22 dismissals are bound to.
