---
id:
status: shipped
date: 2026-08-29
prs: [517]
supersedes:
superseded-by:
---

# Theme thesis card + economics roll-up (`vinci/themes/thesis.py`, `vinci/themes/rollup.py`, the theme page) — the lane gets a declared thesis and an economics surface

**WHAT.** Brief Items 1 and 4 (rulings R1–R5 adopted 2026-08-28, recorded in
`docs/records/2026-08-29-anchoring-falsifier-measured-in-scoring-report.md`).

*Item 1 — the thesis card.* `ThemeThesis` (`vinci/themes/thesis.py`): a HUMAN-TYPED, frozen record
per driver — `mechanism` (closed 7-value enum, ruling R1, adapted from the predecessor framework's
`mechanism_type` list; face-validity-frozen, routes surface grouping now and theme-tier PanelSpec
attachment later), `market_mistake` (the mechanism, never the conclusion — stated limit: that
distinction is human discipline, the machine checks presence/shape only), `null_thesis`,
`first_confirming` + `falsifiers` (≥1, the `vinci/scenarios.py` `DatedTrigger` imported never
duplicated, every deadline ISO-validated — the theme-level end of the deadline-less
`watchlist_triggers` class). Declared via **`vinci theme-thesis declare <driver> --file card.json`**
(`--supersede` archives the prior card under `themes/thesis/archive/` — the baskets
archive-and-reissue pattern, never an in-place edit). The card carries a MACHINE-STAMPED
`mirror_slug` from the registry (the #412 binding lesson; a hand-typed wrong slug is refused).
**THE GATE:** `require_thesis_card` in `themes-forward`'s preflight cluster — FIRST, before
`assert_basket_writable` and the ledger append (#424 refuse-with-NOTHING-written ordering, pinned
by a source-order test) — so no Stage-4 freeze runs card-less. The three baskets frozen before the
gate stay frozen (ruling R2): the page stamps them **`THESIS UNSTATED`** (danger-toned, the
`.uw-survival-fail` register — a blocking state, not a caveat; ONE shared wording constant,
twin-pinned into the JS).

*Item 4 — the economics roll-up.* `ThemeEconomicsRollup` (`vinci/themes/rollup.py`), built by
**`vinci theme-economics --driver <k> --as-of <date>`** → committed
`data/themes/economics/<driver>.json`: per member of the COMMITTED frozen basket (the only
committed membership surface — exposure scans are local-only), the name-level economics the repo
already computes: ladder tiers + `eligible` (+ `gate_regime`, None → rendered "unstamped
(pre-ladder)" — absence never reads as passage), `avoid_priced`, underwrite date, and
`mechanical.ev_gap` WITH its vintages, always (the ev_gap-stale-after-supersede honesty). **NO
COMPOSITE** — pinned by a forbidden-token walk and an artifact-key scan: the predecessor weighted
scenarios by probabilities; this repo has none, and an average would fabricate a theme number.
A basket-less driver yields a LOUD empty artifact carrying its reason.

*Surfaces.* `frontend/build.py` gains two stdlib emitters mirroring both classes by the stamped
slug (verbatim; `archive/` never reaches the page); `snapshots.js` gains `getThemeThesis` /
`getThemeEconomics` (404 → null); the theme page renders ONE identity band (design pass 2026-08-30): the ratified definition,
then THE CLAIM (mechanism chip + declared date in the head, mistake / null thesis / the
committed **radar priced read** joined by the page's ONE candidate finder), then WHAT WOULD
PROVE IT WRONG (dated triggers; a deadline already past carries a `deadline passed` gate chip —
the same date arithmetic and the same word the monitor uses, never an adjudication), with the
analyst notes collapsed. **The previous two-card layout was merged**: "THEME THESIS" sat ABOVE
"WHAT THIS THEME IS", so the reader met an absence stamp before learning what the theme was,
and the page opened with two competing mastheads. The absent state moved from danger-red to the
GATE register (amber) with its consequence spelled out — every driver holds that state until its
card is declared, and a red alarm on every page is how red stops meaning anything. The tier grid
gained an `Exposure scan` band label, and the roll-up leads with the coverage COUNT (sparseness
is the finding) above the underwritten table + collapsed `no underwrite` list. `.gitignore` carves out `data/themes/thesis/` and
`data/themes/economics/` beside the baskets.

**WHY.** The lane could carry a driver from detection to ratification with its thesis living
nowhere but the operator's head — the theme-level analog of the pre-A4 state the edge-basis gate
closed for names — and had NO economics surface: admissibility and ratification see breadth,
coherence, persistence, forward returns; never the members' underwritten asymmetry. The
predecessor framework's theme-intake step (declare the mechanism before the machine elaborates)
and its scenario-EV gate ("does this theme pay?") are the ported disciplines, re-idiomed:
declaration as a gated record; economics as an inform-only assembly that concludes nothing.

**HOW VERIFIED.**
- Suite green: ruff (incl. `frontend/build.py`), `mypy --strict` on both new modules,
  `pytest -m "not network"` **3097 passed** — including 26 new pins across
  `test_theme_thesis.py` (validation refusals with the observed failure shapes; supersede
  archives; gate message + SOURCE-ORDER pin; no-conclude walk; card-only field names absent from
  every LLM tool-schema module) / `test_theme_rollup.py` (fixture rows incl. the pre-ladder and
  vintage pins; loud empty; COMMITTED-CORPUS structural invariants — membership parity over the
  real ai-datacenter basket, non-vacuous) / `test_theme_thesis_mirror.py` (emitters skip
  slugless + archive, verbatim copy; registry-stamp drift guard with ABSENCE-PARITY so zero
  committed cards still asserts; twin-wording stamp pin; JS-reads-only-model-keys pin).
- FOUR EXISTING freeze tests reddened when the gate landed and were seeded with cards — the gate
  proving it binds the real path, not a bespoke one.
- REAL RUNS (corpus before synthetic): `theme-economics` over all four drivers —
  ai-datacenter **56 members, 0 underwritten** (zero overlap with the 8 committed scenario
  records: the sparseness IS the finding this surface exists to make visible);
  defense **108/0**; truckload **37/1** — WERN renders the full honest row
  (`asset-based-tl · unstamped (pre-ladder) · — · 2026-07-19 · 0.98× tev 2026-08-19 ·
  cons ≥2026-08-13`); glp1 → loud empty (no basket, and slugless → data-side only). Freeze gate
  demoed against the REAL data dir: card-less `themes-forward` for ai-datacenter → REFUSED with
  the remedy, nothing written. Declare demoed refusing a non-ISO falsifier deadline.
- PHASE-1 PREVIEW from committed JSON (`thesis-preview`, port 8873, launch.json entry added):
  ai-datacenter page shows the loud stamp above "What this theme is" and the roll-up's honest
  0-of-56; truckload shows the WERN row; details verified COLLAPSED and EXPANDED (56 tickers);
  the card-present state was previewed with a clearly-labeled PLACEHOLDER card (rendered with
  vintage leading + the radar priced line resolving to the real committed candidate), then
  DELETED and the frontend rebuilt — the committed state is card-less because the first real
  card's content is the OPERATOR's judgment, which this build refuses to fabricate.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The three committed roll-ups are derived artifacts stamped `as_of 2026-08-29`; they refresh
  only when `theme-economics` is re-run (operator-triggered, like every job here). A stale
  roll-up shows its own as_of — accepted; the standing artifact pass may regenerate them.
- The card's rewrites are supersede-archive only; the seal MANIFEST machinery was NOT extended to
  cards (its loaders are scenarios-bound; the core is path-free). Accepted with a falsifier: if a
  card ever genuinely needs an in-place `[amended …]` tag rather than a re-declare, that is the
  signal to parameterize `vinci/seal.py`'s loaders instead of widening this build.
- The card's priced-read companion is the committed RADAR candidate map only — the assay quadrant
  and priced-check basket axis remain deliberately uncommitted (local-only by design) and are NOT
  smuggled onto the page here. If they ever earn a committed artifact, the card block is where
  they join.
- `glp1-demand-shift` has no mirror_slug (a real registry state) — its future card/roll-up stay
  data-side until its theme page exists. The mirror tests treat that as correct, not missing.
- Item 2 (the monitor's theme-falsifier deadline sweep) is NOT in this build — next per R4; the
  card's `falsifiers` are its ready input.
