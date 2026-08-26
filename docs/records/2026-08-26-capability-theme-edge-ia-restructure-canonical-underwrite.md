---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **THEME EDGE IA RESTRUCTURE + CANONICAL UNDERWRITE CARD + SHARED-SURFACE SURFACING (2026-07-20,

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **(1) DESIGN LANGUAGE.** The `.uw-*` hand-styled card (ad-hoc flex legs, private type scale, no
    cites, disc bullets) is replaced by ONE shared renderer `frontend/views/shared/uw-card.js` built
    from the canonical components only: `.card` h3 eyebrow, `.fact` rows (verdict pills VERBATIM-cased;
    ratio-vs-bar; reward/risk; spot with inline `↳` cite), the 3-leg matrix as `table.data` (bull
    column `.est-col` — printed for range honesty, NEVER in the ratio; value/share on `tr.name-row`;
    EV/EBIT + norm-FCF as labelled cross-check rows), `.kv-list` reasons/triggers, `facts[]` sources
    behind a `<details>`. Gaps are pills, never blank; no `citeMark` (inline cites only) so the card
    is inert inside the dossier endnote pass — one component, two hosts.
  - **(2) THEME EDGE IA — funnel, one path per destination.** Stages become **[Themes | Radar]**:
    the rail lands on the GLANCE (`#/themes` — pooled honesty, theme table with the theme name as the
    single drill, a collapsed lazy-loading cross-theme watchlist, a radar intake strip), the theme
    page is the READ (brief + tier cards + watchlist with FULL underwrite cards — the only
    full-fidelity site — + avoid-controls + forward), radar folds into the sub-router as the INTAKE
    (`#/themes/radar`, its Map|Inbox|Log restyled to subordinate chips — ONE underline bar). The flat
    Watchlist tab died (`watchlist.js` deleted); tier tables reachable via the theme page only;
    `frame()` gained `{title, crumbExtra}` so drill-downs keep the stage tabs (they used to vanish);
    legacy `#/radar`/`#/themes/watchlist`/`scan`/`forward` normalize in `parseHash`. Radar→theme
    links FIXED: a view-side resolver (explicit `theme_route` → slug → label vs the themes index —
    `defense-demand-shift`→`#/themes/defense`, `ai-datacenter` now links; NO link fabricated for
    uncommitted candidates, whose verbatim rules stay); log `map_ref` dead links became in-view
    "view on map →"; a resolved candidate's drawer suppresses the verbatim rules block (the theme
    page owns triggers). Reserved sub-router names guarded in `build.py::_slug` (a colliding theme
    slug fails the build LOUD).
  - **(3) SHARED-SURFACE SURFACING (operator delegated; decided from first principles: index by NAME,
    not the path the work arrived through; TYPE the rows, never hide a type).** `build.py
    emit_scenarios()` emits a committed `frontend/scenarios/` mirror (index + per-ticker card, the
    EXACT `_scenario_card()` shape the theme JSON embeds — one contract, pinned by shape-parity +
    determinism tests). The Dossier index gains a typed **"First analysis · underwrites"** group
    (dashed cards + `underwrite` pill, labelled "not dossiers … no assembled facts");
    `#/dossier/WERN` renders the RICH degrade (first-analysis header + honesty line + the canonical
    card + logged-verdict block + assemble help) instead of the bare notice. `getProcessedStates()`
    gained a 4th state `underwritten` (presence-only, never the scenario verdict; amber ranker pill) —
    NOTE: WERN itself is not in the ranked queue (it entered via themes), so the state currently has
    no visible ranker instance; it is wired for any queue name that gains a record. Decision log
    UNTOUCHED — a scenario `watch` has no frozen entry leg.
  - **VERIFIED:** ruff + `mypy --strict` + **690 passed** (incl. 2 new build pins; the ESM walk
    auto-covers the new modules); all 10 committed dossiers re-render **byte-identical** to
    origin/main (headless harness); `python3 frontend/build.py` (the Cloudflare invocation, no
    PYTHONPATH) leaves the tree byte-identical and is idempotent; browser-walked every route + legacy
    redirects, light AND dark, incl. the previously-broken radar links and the WERN card/degrade.
  - **REVIEW ROUND (operator, on the live preview): the dossier index was wordy + one-scroll.**
    De-worded and re-tiered: the frame's persistent "assembled facts · no verdict" line REMOVED —
    it was PRE-PIVOT copy (the anti-anchoring pivot renamed the identity to "proposal sealed";
    the dossier.js pin already banned the phrase there) — identity now lives ONCE per typed panel;
    the SHARED `does` line cut to one sentence covering both artifact types; the ×10 per-card
    "assembled facts · proposal sealed →" collapsed into the panel subtitle (cards are ticker-only);
    the search-instruction sentence dropped (the placeholder is the instruction; the ranker link
    moved into the search row); assemble-help moved to the foot. SCALE: the index became TWO
    segmented-chip panels — "Dossiers · N" | "First analysis · M" (the ds-tabs/radar chip
    precedent, client-side, no route) — so 100 dossiers stay one tab away from the underwrites,
    not one long page above them.
  - **DRIVE-BY FIX (explicit, not silent):** `dossier.js` carried a LITERAL NUL byte as a
    compound-key separator (`fam + NUL + name`), making the whole file read as BINARY to grep — now
    the behavior-identical `"\x00"` escape. **Two implementation bugs caught by the browser walk,
    fixed + noted:** `getRadarCandidates()` returns `{candidates}`, not an array (both new call
    sites unwrapped wrong → the landing hung on Loading); `themeIdx` was referenced inside
    module-level `mapTab()` from `render()`'s scope (drawer clicks silently died).
