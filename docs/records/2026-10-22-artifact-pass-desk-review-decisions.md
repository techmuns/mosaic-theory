---
id: 2026-10-22-artifact-pass-desk-review-decisions
status: recorded
date: 2026-10-22
prs: []
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished with the operator's review decisions and the one-step Uploads screen

**WHAT.**
- `frontend/theme-intelligence/` is republished from `theme-intelligence-state` **cd0f4a08** at
  its latest run, R-20261022T074313Z-review.
  - cd0f4a08 carries the operator's review decisions:
    `2026-10-22-theme-intelligence-review-decisions-applied.md`.
  - It is rendered by main f49c380a, which includes #775's Uploads screen. There is no code change
    and no model call.
  - Operator, 2026-10-22: "apply fixes, then merge 775 and republish the desk".
- **What changes on the app** — 68 of the 100 rewritten files differ beyond the publication stamp,
  run ids and week label, and 1 file is new (102 in all, up from 101):
  - **The desk opens on a new week:** "22 Oct 2026 — manual runs since the last weekly scan".
    - A `reassess` run is not a refresh (`report.REFRESH_MODES` holds market, enrich, review and
      author runs), so the analyst corrections open a week of their own.
    - That week reads 0 articles, **14 changed theses, each marked "Analyst correction"**, and 5
      at Research Now (unchanged).
    - The previous week, "Week of 12–21 Oct", moves into the archive as
      `site/articles-2026-10-21.html`, the new file.
  - **Review:** "1 open finding · 1 thesis · 1 affect a research action". It is TH-38CA111885
    s07.8, the line the operator kept. 106 findings sit under resolved and historical.
  - **18 cards (36 files with their print copies):**
    - the 14 corrected theses show their new versions;
    - the 4 theses with dismissals only read "No unresolved review findings · 1 review finding(s)
      dismissed by a reviewer", with the dismissal's name and reason (TH-0D381F307A, TH-393DF5CD2B,
      TH-8DDD7B2868, TH-ABE7D2B79D).
  - **22 thesis pages:** those 18, plus 4 that lose a "New" badge because the week changed.
  - **Uploads:** #775's how-to (price it with `--dry-run`, run it, clear, several at once) and its
    row commands.
  - **Plus:** the dashboard, printable report, index, articles, sources and themes pages, and
    `index.json`.

**HOW VERIFIED.**
- **Every change beyond the stamp, classified** against the copy at main f49c380a. Publication
  stamps, run ids and both week labels were normalised; the files and changes are listed above.
- **The publication:**
  - the manifest equals the folder (102 files);
  - 0 broken links;
  - no local path;
  - 14 retired theses carried;
  - `publish --check`: "the app's research desk shows the registry's latest run".
- **The app**, served locally from this branch on a fresh port: This week opens on the corrections
  week, and Review shows the one open finding. No console error.
- **Suite** on the published files: see the PR.

**BOUNDARY.** Registry cd0f4a08, rendered by main f49c380a on 2026-10-22 (UTC). File counts are
over `frontend/theme-intelligence/`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **The opening week is now the corrections**, not the week's research. "Week of 12–21 Oct" stays
  in the archive, and the next weekly scan opens its own week.
