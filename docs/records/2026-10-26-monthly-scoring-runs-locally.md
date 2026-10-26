---
id: 2026-10-26-monthly-scoring-runs-locally
status: shipped
date: 2026-10-26
prs: [797]
supersedes:
superseded-by:
---

# Monthly scoring runs on the operator's machine and lands by PR; its CI step carries the Tiingo key

**WHAT.** Two operator rulings of 2026-10-26, made after #790 and #796.

- **Row 32 item (14), option (b):** the monthly score is produced locally and lands by a PR, which
  `gate` checks like any other. `docs/RUNBOOKS.md` §l has the exact steps:
  - a clean worktree of `main`, linked to the primary's store, cache and `.env`. Not the primary
    itself: `bin/commit` refuses its unstaged and untracked files, and `git stash` is shared
    across worktrees (this change's own review found it);
  - the keys it needs;
  - `python -m vinci run-monthly`;
  - the frontend mirror;
  - reading the report's `Return basis:` line;
  - committing through `bin/commit`, and a PR.
- **Row 32 item (15):** the `TIINGO_API_KEY` repository secret exists. Its creation stamp is
  2026-10-21 08:42:50Z, read through `gh secret list` as both `nogods404` and `techmuns`. The
  operator added the env line to `monthly-score.yml`'s *Run monthly scoring* step; this PR carries
  that edit exactly as written.

`monthly-score.yml` gains a header note: its closing push is refused by design, so run the scoring
locally (§l). Item (15) is deleted from row 32. Item (14) is narrowed to what stays open:
`weekly-screen.yml`'s push, a workflow that cannot run in CI under the Polygon plan anyway (row 31).

**WHY.** `main` requires a PR and the `gate` check (`2026-10-23-main-requires-gate`). The workflow
ends in a direct `git push` with its own token, which that rule refuses.

Opening a PR from the workflow instead (option a) runs into GitHub's anti-recursion rule, which
`weekly-screen.yml` already documents: a PR created with a workflow's own `GITHUB_TOKEN` starts no
other workflow. So `gate` would never run and the PR would stay blocked. Option (a) would therefore
also need a `workflow_dispatch` trigger on `gate.yml`, plus a dispatch from the job. The operator
chose the local run.

Since 2026-10-26 the score is a total return (`2026-10-26-split-restatement-and-total-return`). A
resolved row whose dividends cannot be read stops the run with `TotalReturnUnknownError`, which is
why the key matters on any path that scores.

**HOW VERIFIED.**

- **The secret:** read by name and creation time only; the value was never read.
- **The workflow:** the env line is byte-identical to the operator's edit (applied as a patch taken
  from their working tree).
- **The runbook against the code on `main` at `57558564`:**
  - `run_monthly` refreshes prices over a 730-day lookback (`_SCORE_LOOKBACK_DAYS`), scores with
    Tiingo dividends, exports the snapshots, and writes `scoring_report.md`;
  - the CLI prints `spread=… pending=…`;
  - the report's markdown carries a `Return basis:` line, with the price-return spread beside it.
- **The maturity dates the runbook names**, read from `data/snapshots/decision_ledger.jsonl` as
  entry date plus `horizon_days`: VRRM 2026-12-14; IT and SMPL 2027-01-16 (two rows each); GOOGL
  2027-03-01; SMPL's long row 2028-02-04.
- **No monthly run was made in this change.** The first local run is the next step: a rehearsal
  before VRRM matures.

**BOUNDARY.**

- **Secrets:** the listing as of 2026-10-26.
- **Ledger dates:** the 7 committed rows on `main` at `57558564`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: the CI workflow still runs, then fails at its push.** It is kept rather than deleted:
  it can still score in CI for anyone who wants to read the output.
- **The monthly score now depends on someone running it.** Nothing schedules it.
  - Falsifier: a ledger row matures and no PR carrying its scoring report follows within a week of
    the next close.
  - The first such date is 2026-12-14.
