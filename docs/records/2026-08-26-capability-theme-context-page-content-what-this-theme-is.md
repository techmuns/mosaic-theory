---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **THEME-CONTEXT PAGE CONTENT — "What this theme is" (2026-07-15, feat/theme-context; PR open, not

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **SINGLE-SOURCE rule (machine-checked):** `driver_summary` is the ratified `DriverSpec`
    description's opening sentence, quoted verbatim (attributed "ratified driver definition") — NOT
    free text. New committed file `frontend/themes/context.json` (analyst-owned), generated from the
    specs and keyed by the theme-page slug (`defense`, not the driver key `defense-demand-shift`),
    joined at view time (`getThemeContext`; graceful absence). `test_theme_context.py` pins each
    `driver_summary.quote` to `first_sentence(spec.description)` — a drift or an un-regenerated edit
    reddens (proven: mutating the quote fails the test).
  - **analyst_notes** are judgment, verbatim, analyst-owned (NOT pinned to the spec): truckload
    carries the 4 valuation/proof/loser-side/thesis-break lines; defense + ai-datacenter each carry
    the one calibration line ("scanned after the market had already re-rated it").
  - **The FROZEN `frontend/themes/*.json` stay BYTE-IDENTICAL** (the #124 clobber lesson) — new
    content ships as a SEPARATE file, never a regenerate.
  - **candidates.json** (the one sanctioned Radar TEXT touch — no Radar view/UI change; the cap
    holds): `detail.summary` added for the three non-scanned candidates (senior-housing,
    in-silico-evidence, trade-flow-shipping), advisor-drafted + analyst-ratified 2026-07-15. The
    Radar drawer already renders `detail.summary || note || lead`, so it is a pure data edit (clean
    +3 insertions, no reformat). Among data files, only `candidates.json` + the new `context.json`
    changed; every other radar/theme artifact byte-identical. ruff + `mypy --strict vinci` + pytest
    (648) + `node --check` green.
