---
id: 2026-10-21-theme-intelligence-desk-review-760
status: recorded
date: 2026-10-21
prs: []
supersedes:
superseded-by:
---

# Theme intelligence: research re-read after a scan joins that scan's week, a retired thesis is answered by name, and a desk left behind is said

**WHAT.** The code review of the desk publication #760 (operator, 2026-10-21: "apply fixes and
then merge"). Three code fixes here. The fourth, company suggestions for the replayed theses, is
data on the state branch. The fifth, the record's counts, is in #760.
1. **A replay joins the week of the scan it follows** (`report.follows`, read by `report_runs`
   and `desk.desk_weeks`).
   - A replay is a run that re-reads research, as `state pull` does. It keeps its original as-of
     (`replay_of`).
   - When that as-of falls in the scan's window and BEFORE the scan's day, it is older research
     read again late, so it is that week's. The label says so: "Week of 12–21 Oct 2026 · with
     research re-read after the scan".
   - Dated before the window, it is no week's research, as `report_runs` has always held.
   - Dated ON the scan's day or later, it is research that arrived after the scan, so it is the
     week in progress and then the next scan's report, like any manual run. A laptop's upload
     replayed by a pull is this case.
     - The full suite caught a first, `<=`, version that put it in the scan's week:
       `test_the_weekly_report_counts_the_replay_once_never_the_carried_runs`.
   - The next scan never takes it in.
   - Before this, the merge's replays opened a "latest" week, "13–14 Oct — manual runs since the
     last weekly scan", dated BEFORE the 12–21 Oct scan it followed. The scan's three Research
     Now sat one step back, and the Articles screen listed "‹ 12–21 Oct | 13–14 Oct latest week".
2. **A retired thesis is answered by name.**
   - `publish` keeps every thesis a publication dropped in `index.json`'s `retired`: title, the
     day it left, and the last run that showed it. The list is carried forward; a thesis
     published again leaves it.
   - The app's view (`frontend/views/intel/desk.js`) names it: "This thesis was retired from the
     research desk on …".
   - A real HTTP 404 for any page but the desk's home no longer says "No theme-intelligence run
     is published yet".
3. **A desk left behind is said.**
   - `publish --check` writes nothing. It says whether the published desk shows the registry's
     latest run, and exits 2 when it does not.
   - The weekly job runs it after its state-branch commit, as a `::warning::` that never fails
     the job.

**HOW VERIFIED.** On the real data: the registry of record, imported from `theme-intelligence-state`
d1d192b7, and main's published desk (the pilot's, 2026-10-17).
- **The week.**
  - The registry of record now opens on "Week of 12–21 Oct 2026 · with research re-read after the
    scan": 15 articles, 22 thesis rows. The scan's 3 Research Now and the documents' 2 are all on
    the front page.
  - The weekly job's own registry is unchanged: "Week of 12–21 Oct 2026", 7 articles, 10 rows.
- **Retired.**
  - Publishing the registry of record into a copy of main's desk records 14 retired theses, each
    with its title, retired 2026-10-21, last shown by R-20261016T163302Z-market. Among them: the
    two HBM theses, "AI boom masks rising US risk premium" and "Broadening S&P 500 earnings
    super-cycle".
- **The lag.**
  - `publish --check` against main's desk: "the app's research desk shows run
    R-20261016T163302Z-market (as of 2026-10-15 …); the registry's latest run is
    R-20261021T104152Z-market (as of 2026-10-21) — republish", exit 2.
  - Against the fresh publication: current, exit 0.
- **Pins:**
  - 5 replay pins in `tests/test_theme_intelligence_desk_weeks.py`:
    - END TO END through `publish`, "2 articles read" under the re-read label;
    - never the next scan's;
    - NEGATIVES: dated before the window is no week; dated after the window, or on the scan's own
      day, is the week in progress.
  - 5 in `tests/test_theme_intelligence_retired_and_lag.py`:
    - retired by name and leaving on return;
    - END TO END, a real republish's `index.json` read by the app's view under node, for a real
      404 and for Cloudflare's app-index answer;
    - NEGATIVE: not retired is "not in the desk", never "nothing published";
    - the lag;
    - the workflow step.
- **Mutation:** 16 mutants, all killed (including `<` → `<=`).

**BOUNDARY.**
- Registry of record: `theme-intelligence-state` d1d192b7 (15 articles, 30 theses).
- Main's desk: published 2026-10-17 from run R-20261016T163302Z-market.
- Measured 2026-10-21 at main 9d07d94e with this branch's code.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The `retired` list only grows from this publication on.** Theses dropped before it are not
  recoverable by name. The first republish after this merge records the pilot's 14.
- **The staleness warning is a to-do, not a guard.** Republishing stays a manual, artifact-only
  PR, because the weekly job never commits to main. Falsifier: the warning appears on two weekly
  runs in a row with no republish between them.
