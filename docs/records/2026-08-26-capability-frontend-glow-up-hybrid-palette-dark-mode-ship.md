---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **FRONTEND GLOW-UP — Hybrid palette + DARK MODE, shipped across 11 PRs (#138–#148).** The

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - Delivered: Hybrid palette (cool neutrals, indigo accent); dark theme via `:root[data-theme="dark"]`
    + a `prefers-color-scheme` pre-JS fallback, stamped on `<html>` by a head script so there is no
    flash; icon-only sun/moon toggle in the sidebar `.brand`, persisted to `localStorage`; editorial
    Dossier (pull-quote decisive question, Assessment / Key-figures eyebrows, tabular figures);
    institutional `tabular-nums` on every data table + pill; Radar quadrant recrafted (compact map
    beside a status panel, bare 2×2 cross — the frame/gridlines/ticks an earlier pass had ADDED were
    removed as noise on a qualitative map); nav to the locked mockup (logo mark, inset pills);
    WCAG-AA contrast in BOTH themes; `:focus-visible` rings on every interactive element.
  - **INCIDENT→INVARIANT (shipped Y): `test_print_reasserts_light_palette_so_dark_never_prints`.**
    `@media print { * { print-color-adjust: exact } }` would bleed the dark canvas into every PDF.
    The guard asserts that EVERY token the dark theme overrides is re-declared to its base `:root`
    LIGHT value under `@media print` — so it also catches a NEW dark token added without a matching
    print re-assert. Verified both ways (green on light; reddens when a print token is mutated dark).
  - **CAVEAT (conscious, not a defect):** `--locked` (inactive locked pills/chips) is left below
    AA — WCAG 1.4.3 exempts inactive UI components from the contrast ratio; forcing it would make
    disabled controls read as active.
  - **NOT copied from the mockup, deliberately:** the study's Radar showed `CONVICTION × MATURITY`
    with invented themes (Nuclear SMR / Quantum …) and a "first-mention sweep" month heatmap. The
    real axes are evidence-is-real × price-already-moved, and `radar/inbox.json` carries an EMPTY
    `inbox` array (0 rows — note the file is a `{scan_date, inbox: []}` dict, so check the ARRAY, not
    the file) — there is no first-mention flow to chart. Only the mockup's LAYOUT/type language
    was adopted; its fabricated analytical model and its invented data block were not.
