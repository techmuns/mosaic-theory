---
id: 2026-10-21-artifact-pass-desk-one-registry
status: recorded
date: 2026-10-21
prs: [760]
supersedes:
superseded-by:
---

# Artifact pass: the app's research desk is published from the ONE registry — the pilot's copy of 2026-10-17 is replaced

**WHAT.**
- `frontend/theme-intelligence/` is republished, with no code change and no model call, from the
  shared registry:
  - `theme-intelligence-state` at **ddf4f8b7**;
  - its latest run, R-20261021T115013Z-market, as of 2026-10-21;
  - rendered by main **257e8748**.
- It replaces the pilot's publication of 2026-10-17 (run R-20261016T163302Z-market).
- This is step 3 of the operator's plan (2026-10-21: "yes go ahead with 1–4"). It is rebuilt
  after the code review of its first version (operator: "apply fixes and then merge").

**BEFORE IT, the review's fixes landed.**
- **#761, the desk's week.** Research re-read after a scan (a replay dated in its window)
  joins that scan's week, labelled as re-read. A retired thesis is named. `publish --check` flags
  a desk left behind.
- **#763, enrich is a refresh.** A company-proposal refresh joins the scan's week.
- **Data on the state branch, d1d192b7 → ddf4f8b7.**
  - `enrich` gave company proposals to the 11 active theses the one-registry merge left without
    them: R-20261021T114639Z-enrich, **$0.4101**. TH-393DF5CD2B is held for review and skipped.
  - A $0 `market` run re-priced every active thesis (R-20261021T115013Z-market).

**WHAT THE APP NOW SHOWS.**
- **30 theses: 21 active, 9 archived.** These are the weekly scan's 10 and the pilot documents'.
- **This week:** "Week of 12–21 Oct 2026 · with research re-read after the scan".
  - 15 articles read, 22 new or changed theses, 5 at Research Now.
  - All five Research Now are on the front page: the weekly scan's optical fibre and cloud capex
    lead.
- **The 11 enriched theses** carry their company proposals.
- **The 14 theses the publication dropped** are kept in `index.json`'s `retired`, with title,
  day and last run. A saved link answers "This thesis was retired from the research desk on
  2026-10-21. …".

**THE FILES** (counts as the PR's file list gives them, git rename detection on):
- 59 added, 36 modified (including `index.json`), 37 deleted, and 5 "renamed".
- The 5 renames are git pairing a removed thesis page with a similar new one, for example
  TH-2E2C6735DB → TH-431B4B9195. No thesis was renamed.
- So 42 pages left (37 + 5: 14 theses × card, print card and reading page) and 64 arrived
  (59 + 5).
- `desk.js` and `intel.css` are unchanged.
- The publication holds 101 files plus `index.json`.

**HOW VERIFIED.**
- `publish` refused nothing:
  - no test-domain article;
  - no stray file;
  - no local path;
  - the manifest equals the folder;
  - 0 broken local links.
- `publish --check` against the result: "the app's research desk shows the registry's latest
  run", exit 0.
- **The app, served locally from this branch, read in the browser pane** on a fresh port (the
  earlier port's cached module served the old view):
  - `#/intel` opens on the week above with those counts, and the 5 Research Now listed;
  - `#/intel/themes/TH-FBDC863613` answers "This thesis was retired … Broadening S&P 500
    earnings super-cycle extends beyond the mega-caps";
  - an unknown thesis answers "This page is not in the published research desk";
  - TH-DEB6560D7F's page carries its company proposals;
  - the only console errors are those two deliberate 404s.
- **Suite:** `pytest -m "not network"` on the published files, with the store moved aside: 6,095
  passed / 526 skipped.

**BOUNDARY.** Registry ddf4f8b7: 15 articles, 9 documents, 30 theses. Rendered by main 257e8748
on 2026-10-21. File counts are `git diff --cached --name-status -M` against 257e8748.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0 in this PR.** The enrichment's $0.41 is on the state branch.
- **The pilot's 2026-10-17 pages leave the app.** Its 14 dropped theses are answered by name.
  Their last pages stay in git history (#741) and the pilot archive.
