> **FOSSIL — superseded, kept for the reasoning.** Last substantive change 2026-07-16. Nothing live
> cites this: it is referenced only by other fossils (`planning/`), which CLAUDE.md already calls
> "the planning fossils". Read it for WHY a decision was made, never for what is true now — the
> current state is STATE.md §5.0 OPEN NOW, and the operating loops are docs/RUNBOOKS.md.
> *Banner added by P0 of the knowledge-ledger plan; the file itself is unchanged below.*

# UI glow-up — implementation plan (Hybrid direction + dark mode)

> North-star for the product-wide visual restyle. Direction locked: **Hybrid** — Direction B's
> editorial *structure* rendered in Direction A's cool-sans / indigo / hairline *language*. Ships
> a light + dark theme with an icon-only toggle. Dependency-free (hand CSS + system fonts), served
> static; no framework, no webfonts.

## Why this is tractable

The frontend is already ~75% token-driven — **every SVG exhibit is 100% `var()`-driven**, and the
radar/pills read tokens too. The only theme-blockers are **~64 hardcoded colours in
`frontend/assets/styles.css` and 6 hex literals in JS** (`lib/ui.js`, `views/shared/dossier.js`,
`views/edge2/ranker.js`). Absorb those into semantic tokens and the palette + dark mode propagate to
every screen at once. The Dossier then gets an editorial restructure on top.

## Load-bearing facts (from a full code read)

- **Toggle mount:** the sidebar `.brand` block in `app.js` `renderSidebar()` renders **once** at
  startup, so a control there is bound once and survives every route. `app.js` is never tested → safe.
- **What the suite pins (and *only* this):** four var **names** — `--danger`, `--live`, `--accent`,
  `--ink-3` (literal in `dossier.js`); a set of class names (`brief-body`, `brief-snap`,
  `brief-snap-idn`, `brief-proposal`, `cite-n`, `ds-exhibit brief-perf`); the `EXHIBIT` geometry
  tokens; the `>Source:` inline-caption guard; and **one** `styles.css` rule
  (`details:not([open]){display:none}`). Every colour *value*, the dark layer, and the toggle are
  unconstrained. Classes `brief-idn`/`brief-meta`/`brief-stock`/`brief-tag` must stay absent.
- **The print landmine:** `@media print` forces `background:#fff` + `print-color-adjust:exact` on
  `*`. Dark tokens **will bleed into the PDF** unless print re-asserts the light palette. Must-fix.

## Token system

Keep **all existing token names** (renames churn the exhibits + break pinned names) and extend with a
semantic set that absorbs the 64 literals — every token gets a **light and dark** value:

| Family | Tokens | Absorbs |
|---|---|---|
| Core | `--bg --surface --surface-2 --ink/-2/-3 --line/-2` | greys → cooler Hybrid neutrals |
| Accent | `--accent --accent-bg --accent-border --accent-text` | `#2f6fde`→indigo `#33459a`; blue callouts |
| Positive | `--live --live-bg --pos-text --pos-border` | greens |
| Teal | `--teal --teal-bg --teal-text` | radar-live (kept distinct from green) |
| Warn/gate | `--warn --conditional-bg --warn-text --warn-border --warn-strong --gate-*` | ambers, cream gate, gold |
| Danger | `--danger --danger-bg --danger-border --danger-text` | reds |
| Synthesis | `--synth --synth-bg --synth-border` | purple LLM fence (kept distinct — semantic) |
| Chrome | `--nav-* --on-nav --row-hi --glow-* --nav-wash --shadow` | nav text, row highlights, rgba glows |

Delivered via `:root` (light) + `@media (prefers-color-scheme:dark)` + `:root[data-theme]` overrides;
system default, toggle persists to `localStorage`. **`@media print` re-asserts the light palette.**

## PR sequence (each previewed light+dark, suite green)

1. **Tokenize — *invisible*.** Absorb all 64 CSS + 6 JS literals into the semantic tokens at their
   current values (near-dupe shades consolidate; render HTML stays byte-identical → node smoke passes).
   Low-risk refactor that unlocks the rest.
2. **Hybrid palette + dark + toggle — *the engine*.** Swap token values to the Hybrid palette; add the
   `data-theme` dark layer; add the icon-only sun/moon toggle in `.brand`; re-assert light under
   `@media print`. Lands the new look *and* dark mode product-wide → **stop for sign-off.**
3. **Hybrid Dossier — *editorial*.** Restructure the Brief teaser (masthead, `Assessment`/`Key figures`
   labels, key-figures strip, framed body, pull-quote decisive question). Preserve pinned classes +
   md/print parity + exhibits.
4. **Component craft.** Nav, header, tabs, cards, tables, tiles, chips, Radar, Ranker — spacing rhythm,
   hairlines, type scale, tabular nums. Screen-by-screen.
5. **QA + a11y + print.** Every screen light+dark, 640/820 responsive, PDF stays light & clean, focus
   states + WCAG-AA contrast in both themes. Ship a guard test: **print always renders light.**

## Guardrails

- Preserve verbatim: the 4 pinned var names, the pinned classes, no `>Source:` caption, the
  `details:not([open])` print rule, the `EXHIBIT` geometry tokens.
- Suite green (`ruff` + `mypy --strict` + `pytest -m "not network"`) every PR; preview every render PR.
- Dependency-free: system font stacks, hand CSS. No webfonts, no libraries.

## Coordination

Rewrites `styles.css`, `dossier.js`, `app.js` — the same files as in-flight frontend work. PR 1
(tokenize, invisible) is safe to land early and rebases trivially; PRs 2–4 should ideally land after
the active frontend branches merge. Everything branches off `main`; the stack is reviewed together.
