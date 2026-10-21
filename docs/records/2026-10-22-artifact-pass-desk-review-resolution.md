---
id: 2026-10-22-artifact-pass-desk-review-resolution
status: recorded
date: 2026-10-22
prs: [770]
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished so the app shows review resolution

**WHAT.**
- `frontend/theme-intelligence/` is republished from the same registry and run as before:
  `theme-intelligence-state` 9939047e, R-20261021T123639Z-market.
  - No code change and no model call.
  - It is rendered by main 42cd458f, which carries #768 (review resolution) and #769 (the
    one-step upload).
- **Why a republish was needed:** the app shows rendered pages, so #768 changed nothing there
  until now. `publish --check` compares runs, not rendering code.
- **What the app now shows** (operator, 2026-10-21: "yes, republish the desk"):
  - **The Review screen's hint** says how a finding closes: a re-review, an analyst correction,
    or — a warning only — a reviewer's dismissal with a name and a reason, which verifies
    nothing.
  - **The audit view** names each finding's key. On the 47 dismissible findings it gives the
    `review dismiss` command; on the 9 withheld ones it says they close only by a correction or
    a re-review.
  - **The weekly report's history fold** names dismissals. Its note no longer claims that none
    of its items bears on a current card.
- No finding is dismissed (none is, on the registry), so no line or count on the desk changes.

**HOW VERIFIED.**
- **What changed, classified element by element** against the published copy at main 42cd458f.
  - 100 of 101 files were rewritten, and 81 differ beyond the publication stamp.
  - Every added element is one of #768's:
    - 112 finding keys in the audit view — 56 findings, each on the Review screen and on its
      thesis page;
    - 62 copies of the new `.dismissed` card style — 60 cards and print cards, plus the
      dashboard and the printable report;
    - 2 report fold titles and 2 report notes;
    - 1 Review hint.
  - Nothing else was added.
- **Counts unchanged:** the Review screen still reads 58 open findings · 18 theses · 39 affecting
  an action, and no page says "Dismissed by".
- **The publication:**
  - the manifest equals the folder (101 files);
  - 0 broken links, no local path;
  - the 14 retired theses carried forward.
- **The app, served locally from this branch:**
  - the Review screen shows the new hint, with no console error;
  - with the audit view on, it shows 47 `review dismiss --finding F-…` commands and 9 "never a
    dismissal" notes.
- **Suite** on the published files: 6,193 passed / 527 skipped (main 42cd458f).

**BOUNDARY.** Registry 9939047e. Rendered by main 42cd458f on 2026-10-21 (UTC). Element counts
are tag-level additions across `frontend/theme-intelligence/**/*.html` against the copy at main
42cd458f. Finding counts are the desk's own: open items on the Review screen, and finding keys in
its audit view.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0. The stamp-only rewrite of 19 pages is the cost of a
whole-folder publication.
