---
id:
status: recorded
date: 2026-09-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §2 (capability entry, compacted)
date-source: the migration date — the capability is older and is dated in the body
---

# RADAR RESTRUCTURED TO TABS — final structural pass per operator direction 2026-07-15 (feat/radar-tabs-restructure; PR open, not merged; DEPLOYS on merge). VIEW-LAYER ONLY — all data contracts BYTE-IDENTICAL (candidates/sweep/reviews/inbox/log/themes JSON), build.py UNTOUCHED.

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **RADAR RESTRUCTURED TO TABS — final structural pass per operator direction 2026-07-15
  (feat/radar-tabs-restructure; PR open, not merged; DEPLOYS on merge). VIEW-LAYER ONLY — all data
  contracts BYTE-IDENTICAL (candidates/sweep/reviews/inbox/log/themes JSON), build.py UNTOUCHED.** One
  Radar nav stage, three internal sub-tabs **Map · Inbox · Log**. **REMOVED (the clutter):** the status
  filter-chip row (All/Live/…; code comment retains it only if judged themes exceed 12), the inbox lane
  inside the map SVG (killing the y-axis-label collision — map is now full-width), the always-open detail
  panel, the long footer paragraphs (each tab now ≤1 muted line), and the Found-by column (moved to the
  drawer). **ADDED:** a slim one-line sweep status above the tabs (dot · "scan Jul 14 · next Aug 13" ·
  run-command copy); a **drawer** (collapsed by default, one open at a time) opened by a map dot OR a
  judged-list row — title + status chip · one-line summary · Watching/Comparison ticker rows · muted
  "found by …" · "full page →" · a "Wake-up rules ▾" expander revealing the rules VERBATIM from
  candidates.json (wall-of-text removed from the default view, verbatim preserved); the **Inbox tab**
  (full-width table sorted by |price move| ASCENDING — "least-moved first"); the **Log tab** (search +
  Rejected-only + verbatim reasons). Inbox tab badge is WARNING-styled when any item is >14 days old.
  **Deep links** #/radar/inbox and #/radar/log load the right tab (router params, like themes sub-routes);
  tab clicks sync the URL via replaceState without re-fetching. Copy pass: sentence case throughout,
  12–13px body, right-aligned tabular numbers, reused chip classes, no new colors. Verified in preview
  (all data files byte-identical, zero console errors): each tab; drawer from the Truckload dot AND its
  list row; the wake-up-rules expander shows verbatim text; inbox sort order + a row expanded; log search
  "quantum"→1; Rejected-only→6; deep links load the right tab; Overview + Watchlist unregressed. ruff +
  `mypy --strict vinci` + pytest (598) + `node --check` all JS green. **The standing SCOPE CAP re-applies
  verbatim after this PR:** *"Radar polish is CAPPED after this PR: no further Radar UI work until a first
  BUY, a fired watchlist trigger, or actual LP usage of the site."*
