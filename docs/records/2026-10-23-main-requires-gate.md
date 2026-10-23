---
id: 2026-10-23-main-requires-gate
status: shipped
date: 2026-10-23
prs: [790]
supersedes:
superseded-by:
---

# `main` requires the `gate` check, so a red or pending PR can no longer merge — and the two hand-run workflows that push straight to `main` now meet its PR rule

**WHAT.** On 2026-10-23, at the operator's request, `main`'s branch protection gained one required
status check: `gate`, accepted only from GitHub Actions (app id 15368), so a status posted by
anything else cannot satisfy it. The protection is the classic kind; the repository has no
rulesets. Read back as the owner (`GET /repos/techmuns/mosaic-theory/branches/main/protection`):

| Setting | Before | After |
|---|---|---|
| Required status checks | none | `gate` (GitHub Actions only) |
| Branch must be up to date with `main` (`strict`) | — | off |
| Pull request required / approvals | yes / 0 | unchanged |
| Force-push, deletion | blocked | unchanged |
| Rules enforced on admins | no | unchanged |
| Bypass list for the PR rule | none | unchanged |

**How it was made.** `nogods404`, the agents' account, has write access but not admin, so it can
neither read nor change protection. The change was made with the owner account `techmuns`: its
token was passed inside the single `gh api -X PUT …/protection` call, and `gh`'s active account,
which other sessions share, was not switched. That call re-sent every other setting at the value
it had read back.

**WHY.** This is P0-2 of the 2026-10-22 agentic-engineering research report: a PR could merge with
`gate` red or still running. It was seen on #789 on 2026-10-23: while `gate` ran, GitHub reported
the PR MERGEABLE / UNSTABLE, not BLOCKED.

`2026-10-22-repo-made-public` left this question open ("the operator confirms it requires
`gate`"), because the agent account cannot read the rule. The owner-account read answers it:
nothing was required until this change.

**HOW VERIFIED.**

- **The readback** after the PUT: checks `[{context: gate, app_id: 15368}]`, `strict` false,
  approvals 0, force-push false, deletion false, admins not enforced.
- **As `nogods404`**, GraphQL `refUpdateRule` on `refs/heads/main` returns
  `requiredStatusCheckContexts: ["gate"]`.
- **On the open PRs:**
  - #695 and #611, both into `main`, now list `gate` under `gh pr checks --required`;
  - #511, also into `main`, has no `gate` run on its head, so its required check is simply waiting;
  - #616 targets `artifact/monitor-run` and is correctly unaffected.
- **Not yet seen:** a PR into `main` reading BLOCKED while `gate` runs. The next PR into `main`
  will show it.

**THE WORKFLOW CONFLICT — OPEN (STATE.md §5.0 row 32, item 14).** `monthly-score.yml` and
`weekly-screen.yml` both run only on `workflow_dispatch`. Both commit, then `git push` to `main`
with the workflow's own token. Under GitHub's documented rule, a branch that requires a pull
request (and now a status check) refuses a push from an actor who is neither an admin nor on a
bypass list, and the bypass list is empty.

**This is NOT OBSERVED here:**

- Neither workflow has run since protection began. The last runs were `weekly-screen` on
  2026-09-23 (a failure) and `monthly-score` on 2026-08-01.
- All 25 commits on `main`'s first-parent line since 2026-10-21 are PR merges. The last direct
  pushes were on 2026-08-31.
- GraphQL's `viewerCanPush` reads `true` for `nogods404`. That flag does not account for the PR
  rule, so it neither confirms nor refutes the refusal.
- It cannot be tested without risking a real push to `main`.

**The consequence, if the documented rule holds:** the workflow cannot regenerate the scoring
report (`data/snapshots/scoring_report.md`, last regenerated 2026-08-01) as written. The first
ledger row, VRRM, matures on 2026-12-14.

There are two ways out:
- (a) the workflow pushes a branch and opens a PR;
- (b) the operator runs it locally and opens a PR.

Choosing is the operator's call; building (a) is agent work.

**BOUNDARY.**

- **The settings.** Read as `techmuns` on 2026-10-23, after #789 merged (12:29:15Z) and before
  12:47Z.
- **The PR checks.** The four open PRs as of 12:47Z.
- **The commit count.** First-parent commits on `origin/main` committed since 2026-10-21, read at
  `f62ddc32`.
- **The workflow dates.** The latest run of each, from `gh run list`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: `strict` is off.** A PR that is green on an older base can merge and break `main`.
  `main`'s own `gate` run after the merge catches it, after the fact rather than before. Turning
  `strict` on would make every concurrent agent PR merge `main` in again before merging.
  Falsifier: a red `gate` on `main` right after merging a green PR → turn `strict` on.
- **ACCEPTED: rules not enforced on admins.** `techmuns` can still merge a red PR, as the
  operator's emergency path. The agents cannot.
- **The required check is the offline suite, not the full one.** `gate` passed 6,411 tests and
  skipped 531 on #789's head, among them the tests that need the licensed CIQ workbooks, which
  CI does not have. `bin/commit`
  on the operator's machine remains the only place the full suite runs.
