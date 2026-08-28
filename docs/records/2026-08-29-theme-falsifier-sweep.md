---
id:
status: shipped
date: 2026-08-29
prs: [518]
supersedes:
superseded-by:
---

# Theme falsifier sweep (`vinci/monitor.py::theme_falsifier_rows` + the THEME FALSIFIERS panel) — the card's deadlines reach the monitor

**WHAT.** Brief Item 2 — the last build item of the adopted theme-thesis brief. `vinci monitor`
now sweeps every DECLARED thesis card's dated triggers (`first_confirming` + `falsifiers`, via
`load_all_theses` — top-level only: `thesis/archive/` never feeds the sweep, because a superseded
falsifier flagged as live is the stale-criterion class this exists to end) into typed
`ThemeFalsifierRow`s on the `MonitorSnapshot` (field DEFAULTED, so every committed pre-Item-2 day
still validates — corpus-pinned on the real 2026-08-11 file). The console renders a THEME
FALSIFIERS section beside the scenario freshness panel: a deadline on/before the run date flags
`⚑ … — deadline <date> PASSED → re-underwrite due` (the scenario `dated_triggers` wording,
deliberately); a future one lists `(by <date>)`; zero cards prints the STATED
`no thesis cards declared` — never a silent absence. **Flag-only, exactly as the panel's own
doctrine says**: the machine says the window closed; whether the falsifier FIRED is the human's
read, and indicator MEASUREMENT stays with the PanelSpec plan (§5.0 row 5) — this sweep must
never grow into a rival panel.

**ADJACENT FIX, shipped loudly rather than silently:** the scenario
`FreshnessRow.passed_trigger_deadlines` were TYPED and PERSISTED since the catalyst calendar but
NEVER RENDERED in the terminal view — an artifact-only flag the operator's console never showed
(latent: every committed day carries the field empty, so nothing ever misprinted). Rendering the
theme flags beside invisible scenario flags would have shipped a fresh incoherence, so the one
render line was added and pinned. Held-scope note: this is the only line touched outside Item 2's
own surface.

**WHY.** The card (Items 1/4) declared falsifiers with deadlines precisely so a machine could
flag the closed windows; until this sweep they were record-only — the theme-level SMPL/OWYN
class (a criterion faithfully recorded and never watched). The predecessor framework's
trigger-deadline discipline is the ported idea; the repo's flag-never-adjudicate line is kept
verbatim.

**HOW VERIFIED.**
- Suite green: ruff, `mypy --strict` on `vinci/monitor.py` + `vinci/themes/thesis.py`,
  `pytest -m "not network"` **3105 passed** — 7 new pins in
  `tests/test_theme_falsifier_sweep.py`: passed/future/first-confirming row semantics; the render
  wording INCLUDING the never-adjudicates pin (`"fired"` must not appear); the stated zero-card
  absence; the corpus pin (committed 2026-08-11 snapshot validates with the defaulted field);
  archive-skip + sort in `load_all_theses`; the adjacent-fix render line; and a source pin that
  `_cmd_monitor` both builds AND persists the rows (a sweep computed but not written would be the
  artifact-only inverse of the render gap).
- REAL RUNS on the live book (network EDGAR + the worktree store): (1) zero cards →
  `THEME FALSIFIERS … no thesis cards declared` printed and `theme_falsifiers: []` in the
  snapshot; (2) the clearly-labeled PLACEHOLDER card declared → re-run → two pending rows with
  `(by <date>)` + basis lines, and the past-due one flagged
  `⚑ … — deadline 2026-08-15 PASSED → re-underwrite due`, with the typed rows shown in the
  written `data/monitor/2026-08-27.json`. Both demo artifacts then DELETED (the placeholder card,
  and the demo monitor day — placeholder text must not enter the committed book history; the
  operator's next real monitor run writes the real day).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The sweep reads DECLARED cards only; with none declared (the current committed state) it prints
  the stated absence every run until the operator declares the first card — that repetition is
  the point, not noise.
- A corrupted card deadline raises LOUDLY at sweep time (declare-time ISO validation makes this
  unreachable by the CLI path) — unlike the scenario path, where an unparseable analyst date
  legitimately renders verbatim in the dossier instead. Deliberate asymmetry, stated here.
- The frontend monitor surface renders whatever the committed snapshot carries; no theme-page
  join of falsifier status was added (the page lists the card's falsifiers verbatim from Item 1).
  If the operator wants the flag state ON the theme page, that is a small follow-up reading the
  latest monitor artifact — noted, not built (hold scope).
