---
id: 2026-10-22-artifact-pass-desk-authors-stated
status: recorded
date: 2026-10-22
prs: []
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished at the registry's latest run — no page shows article authors

**WHAT.**
- `frontend/theme-intelligence/` is republished from `theme-intelligence-state` **0cdebc0f**
  (the three `author` runs that stated "Morgan Stanley") at its latest run,
  R-20261022T035404Z-author.
  - It is rendered by main 3bd32228. There is no code change and no model call.
  - Operator, 2026-10-22: "merge 772 and republish the desk".
- **What changes on the app** — 13 of the 101 files differ beyond the publication stamp and run
  id:
  - **The weekly report** (dashboard and printable report) covers 12 runs, adding the three
    author runs. Its window now ends on 2026-10-22, and its verification log counts 77 INFO
    records, up from 74 with the three AUTHORS_STATED.
  - **10 thesis pages:** the suggested `market` command is dated 2026-10-22.
  - **The week label is unchanged** ("Week of 12–21 Oct 2026 · with research re-read after the
    scan"): an `author` run is a refresh and opens no week. The counts read as before: 16
    articles, 22 theses, 5 Research Now, 58 findings.
- **A correction to what I told the operator.** I said a republish would show "Morgan Stanley" on
  the weekly report's source lines. **No published page shows article authors.**
  - The report's source line (`report._sources_line`) renders only in the Markdown and CSV
    exports, which the publication does not carry. The publication is 99 HTML pages, a stylesheet,
    a script and `index.json`.
  - The cards' source rows are sealed with their versions.
  - The Articles screen does not list authors.
  - So the statement shows in QA, in the article record, and in the Markdown/CSV report — not on
    the app — until a card's next version.

**HOW VERIFIED.**
- **Every change beyond the stamp, classified** against the copy at main 3bd32228 (tag-level diff,
  publication stamps and run ids normalised): the 13 files and the changes listed above. Nothing
  else changed.
- **Before and after**, none of the published pages contains "Morgan Stanley — Morgan Stanley"
  or "Morgan Stanley — author UNKNOWN".
- **The publication:**
  - the manifest equals the folder (101 files);
  - 0 broken links;
  - no local path;
  - 14 retired theses carried;
  - `publish --check`: "the app's research desk shows the registry's latest run".
- **The app**, served locally from this branch: This week and Review render as before, with no
  console error.
- **Suite** on the published files: see the PR.

**BOUNDARY.** Registry 0cdebc0f, rendered by main 3bd32228 on 2026-10-22 (UTC). File counts are
over `frontend/theme-intelligence/`; occurrence counts are over its `site/**/*.html`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0. 87 pages rewritten for their stamp alone, the cost of a
whole-folder publication. The authors stay off the app until the cards' next versions — or a
surface that shows them, which nothing asks for yet.
