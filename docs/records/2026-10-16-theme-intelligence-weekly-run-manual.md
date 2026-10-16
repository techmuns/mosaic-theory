---
id: 2026-10-16-theme-intelligence-weekly-run-manual
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the weekly run is started by hand, never on a timer (operator ruling)

**WHAT.** Operator, 2026-10-16: "can we keep weekly run on manual like its done for existing
weekly run scans?". The `theme-intelligence-weekly` workflow now has only `workflow_dispatch`,
as `weekly-screen.yml` and `monthly-score.yml` already do. Changed:
- the workflow: its Monday 03:00 UTC cron and the job condition reading the repository variable
  `THEME_INTELLIGENCE_SCHEDULE_ENABLED` are removed;
- `bin/theme-intelligence-weekly`: its header says it is run by hand;
- `docs/theme_intelligence.md`: the cron and launchd templates are gone, and "scheduled run"
  reads "Actions run";
- STATE §5.0 row 32 item (8)(c): it now records the ruling, where it used to ask the operator to
  switch the schedule on.

**WHY.** The cron never ran: the variable was never set (`gh variable list` shows none,
2026-10-16). The 2026-08-24 ruling recorded in `weekly-screen.yml` already holds that a job which
moves the fund's state belongs to the operator, not to a clock. A dormant cron was one variable
away from contradicting that.

**HOW VERIFIED.**
- **The workflow parses** (Ruby YAML): its triggers are `["workflow_dispatch"]`, the job has no
  condition, and the `days` and `max_articles` inputs are unchanged.
- **`tests/test_theme_intelligence_workflow.py` pins the manual trigger.** No schedule, cron or
  variable gate is allowed. The check finds all 3 such lines in the old trigger, and it fails on
  main's workflow file and passes on this one.
- **`tests/test_scheduled_workflows.py`** still passes.

**BOUNDARY.** Workflows as of main 0c47d794. Repository variables listed 2026-10-16.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **A week passes unscanned unless someone starts the run.** The desk's This week shows the last
  run's date, so a missed week is visible, never a silent gap.
- **U31f (the Actions cache keeping a failed run's paid answers) is still proven only by an
  Actions run.** It waits for the first one started by hand.
