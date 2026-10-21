---
id: 2026-10-21-artifact-pass-evidence-label
status: recorded
date: 2026-10-21
prs: []
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished so the app shows the corrected evidence label

**WHAT.**
- `frontend/theme-intelligence/` is republished, with no code change and no model call, from the
  same registry and run as before: `theme-intelligence-state` 9939047e, R-20261021T123639Z-market.
- It is rendered by main 77e3d336, which carries #766's label: "New supporting evidence — not a
  confirmation", where the desk printed "Direct confirmation — new evidence".
- **Why a republish was needed:** the app shows rendered pages, so #766 changed nothing on the app
  until now. `publish --check` compares runs, not rendering code, so it read "current" throughout.
  This was the code review of #766's finding, 2026-10-21.

**HOW VERIFIED.**
- **The label:** 0 occurrences of the old label and 48 of the new one on the published pages:
  - TH-38CA111885 ×10 and TH-DEB6560D7F ×6, each on its card and print card;
  - 16 in the printable weekly report.
- **The publication:**
  - the manifest equals the folder;
  - 0 broken links; no local path;
  - the 14 retired theses carried forward;
  - 100 files rewritten. Most change only their publication stamp; 5 carry the label.
- **The app**, served locally from this branch: TH-38CA111885's Full record shows the new label 10
  times and the old one 0 times, with no console error.
- **Suite** on the published files: 6,149 passed / 526 skipped (main 77e3d336).

**BOUNDARY.** Registry 9939047e. Rendered by main 77e3d336 on 2026-10-21. Label counts are
occurrences across the published `site/**/*.html`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0. The stamp-only rewrite of 95 pages is the cost of a
whole-folder publication.
