---
id: 2026-10-14-theme-intelligence-layout-room
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# The app's menu collapses and is slimmer; This week and Uploads give their content the full width

**WHAT.** At the operator's request (2026-10-14): "make the nav bar smaller or collapsable so
there's more room to look at content on the right", and "'needs your attention' … is repetitive
and is making the actual content squeeze, similar for other screens as well".
- **The app's menu (the left rail), app-wide** (`frontend/app.js`, `assets/styles.css`,
  `index.html`):
  - slimmer by default, 236 → 212 px;
  - a collapse button next to the theme switch shrinks it to a 52 px strip holding the logo and
    the two buttons;
  - the choice is remembered (`localStorage` "nv-nav") and applied before first paint, as the
    theme is, so it never flickers;
  - on a phone the menu stacks on top as before, and collapsed it is just the brand row, so the
    content starts at the top of the screen.
- **This week:**
  - the "Needs your attention" side panel is gone, since its findings and uploads lines
    repeated the count tiles beside it;
  - what the tiles do not already say (failed or blocked articles, theses close to archiving,
    sources needing attention) is one line of links under the tiles;
  - the week's changes and articles take the page's full width.
- **Uploads:** the "Each week" side panel is one closed fold above the list ("How to supply
  documents each week — pull · import · clear · push"), its four steps side by side when opened.
  The list takes the full width.
- **The other screens** (Themes, Articles, Review, Sources) had no side panel. The reading page's
  side-by-side pairs are content, not panels, and stay.

**WHY.** On a 1280 px laptop the menu took 236 px and a 300 px panel took more, leaving the
week's content about 640 px. The panel repeated numbers already shown above it.

**HOW VERIFIED.**
- **In the app** (local preview, headless Brave, the pilot registry published):
  - This week at 1280 px went from 4,284 to 3,508 px tall with the menu open, and 3,468
    collapsed;
  - no horizontal overflow at 1280 and 390 px, menu open or collapsed;
  - "Nostra Vinci" fits on one line in the slimmer rail;
  - the Theme intelligence pages load with no console errors. The Overview's "Loading fund
    status…" locally is a missing `frontend/snapshots/` in this worktree (404 on
    `decision_ledger.jsonl`), not this change.
- **Pin** (`tests/test_theme_intelligence_desk.py`):
  - neither screen has a side panel, and no "Needs your attention";
  - the heads-up line links Articles and Sources, and the tiles still link Review and Uploads;
  - Uploads' routine is a closed fold of four steps above the list.
  - An existing This week test whose selector (`section.main div.area`) had stopped matching
    anything — passing vacuously — now selects the page's areas and asserts it finds them.
- `node --check` on `app.js`; ruff and `mypy --strict` are clean; the offline suite result is in
  the PR.

**BOUNDARY.** The heights are `documentElement.scrollHeight` of the app framed at exactly 1280 px,
real pilot registry at `R-20261014T070200Z-ingest`, before and after on 2026-10-14.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- The menu change is app-wide: every section gets the slimmer rail and the collapse button.
- No test pins the app shell's JavaScript; it was checked in the browser.
