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

# RADAR INBOX LANE + REVIEW LOG — shipped per operator sanction 2026-07-14 (feat/radar-inbox-log; PR open, not merged; DEPLOYS on merge).

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **RADAR INBOX LANE + REVIEW LOG — shipped per operator sanction 2026-07-14 (feat/radar-inbox-log; PR
  open, not merged; DEPLOYS on merge).** The Radar gains (1) an INBOX lane left of the quadrant — current
  sweep clusters NOT yet matched to a review (11 from the 2026-07-14 sweep), hollow-gray dots by 12mo
  rel-strength (NO quadrant x-position — an unjudged cluster has no "how real" reading yet); and (2) a
  REVIEW LOG below the list — the analyst's recorded dispositions (search, All/Rejected-only, expandable
  members + membership-drift note, paginated past 15). **DATA CONTRACT:** `frontend/radar/reviews.json`
  is the **single analyst-owned record** of group reviews (35 June-17 clusters; STATE points here, never
  copies reasons); `frontend/radar/{inbox,log}.json` are **emitted by build.py** (`emit_radar_inbox_log`
  joins the latest component-a snapshot × reviews.json by MEMBER OVERLAP ≥50% of the smaller set —
  cluster_ids are per-run, never matched on id; non-destructive when a source is absent). Today's split:
  **46 clusters → 35 matched / 11 inbox; 35 reviews (1 gone** = June auto-parts ADNT/ALV/LEA). The
  machine SORTS (matched→log, unmatched→inbox) but NEVER decides — every inbox detail carries "review is
  recorded in reviews.json — this screen never decides." **JUNE BACK-FILL ATTRIBUTION:** of the 35
  reasons, **29 are advisor-drafted (analyst-agreed)** and 6 are analyst-direct — recorded in each
  entry's `by` field, never laundered. Verified in preview (rendered from committed JSON, zero console
  errors): inbox count, lane dots + tooltips, dot-click detail, log search "quantum"→1, Rejected-only→6,
  a June row's verbatim reason. Emitter tests pinned (`test_radar_inbox_log_join` 50%-boundary /
  drift-to-inbox / gone / deltas, `…_deterministic`). ruff + `mypy --strict vinci` + pytest (597) +
  `node --check` all JS green; `themes/*.json` + `candidates.json` + `sweep.json` BYTE-IDENTICAL.
  **SCOPE CAP (operator-ratified 2026-07-14, recorded verbatim):** *"Radar polish is CAPPED after this
  PR: no further Radar UI work until a first BUY, a fired watchlist trigger, or actual LP usage of the
  site."*
