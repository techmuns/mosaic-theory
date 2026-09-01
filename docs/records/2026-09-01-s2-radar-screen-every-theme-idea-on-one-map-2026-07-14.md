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

# RADAR SCREEN — every theme idea on one map (2026-07-14, feat/radar-screen; PR open, not merged; DEPLOYS on merge — viewer gains a "Radar" tab under Themes).

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **RADAR SCREEN — every theme idea on one map (2026-07-14, feat/radar-screen; PR open, not merged;
  DEPLOYS on merge — viewer gains a "Radar" tab under Themes).** Shipped per operator sign-off 2026-07-14
  (DESIGN option A: quadrant-map hero + detail panel BELOW). A read-only, **zero-LLM** mirror of the
  analyst's own dispositions: 6 theme ideas plotted on evidence-the-idea-is-real (x) × price-already-moved
  (y), color-coded by status (live-teal / watch-amber / parked+priced-gray / past-gray-hollow), selected
  ring, hover tooltip, click-to-select; a detail panel renders the analyst's wake-up rules + comparison
  legs **VERBATIM**; a Theme/Status/Found-by/Price-12mo list (paginates past 12). **No run buttons —
  nothing fires here** (the machine assembles/cites, never concludes; past markers are story-placed, not
  measured). **DATA CONTRACT:** `frontend/radar/candidates.json` is **analyst-owned** (the 6 entries +
  every disposition/rule authored by hand, committed, never machine-written); `frontend/radar/sweep.json`
  is **emitted by build.py** (`_radar_sweep_payload`: `last_run` = latest ts in the git-ignored
  `data/scan_history/component-a/manifest.jsonl`, else seeded `2026-06-17`; `next_due` = last_run + 30d;
  the run **command is single-sourced in build.py** `_SWEEP_COMMAND = "python -m vinci.cli themes"` — the
  screen renders it, never hardcodes it). **Verified — mock-first rule satisfied:** rendered the view from
  committed JSON in preview (no backend), confirmed quadrant/dots/captions/axes, sweep bar (green dot,
  seeded 2026-06-17, next-due 2026-07-17), filter counts (All 6 / Live 1 / Watch 1 / Parked 1 / Too late 1
  / Past 2), BOTH detail panels verbatim (Truckload WERN/MRTN/HTLD + RXO/LSTR/ARCB; In-silico's 4 wake-up
  rules), the 6-row list, and all interactions (filter narrows dots+list, dot/row click selects, "full
  page →" routes to the theme page, "▸ run command" reveals+copies the command chip) — **zero console
  errors**. Two sweep-payload tests pinned (`test_radar_sweep_seeded_fallback_and_next_due`,
  `…_reads_manifest_latest_ts`). ruff + `mypy --strict vinci` + pytest (593) + `node --check` all
  frontend JS green; `frontend/themes/*.json` byte-identical to HEAD (radar adds, never churns themes).
