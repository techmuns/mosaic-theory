---
id: 2026-10-30-the-synthesis-is-asked-for-each-material-figure
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# The synthesis is asked for every material figure the citation guard demands (audit D-D5 follow-up)

**WHAT.**
- **One selection, two readers.** `synthesis.demanded_material_figures(mech)` is the figure
  selection that `uncited_material_figures` (item 19c) used inline. It covers rows already marked
  material, values at or over `MATERIAL_FIGURE_FLOOR_MUSD`, actual columns only, and the largest
  plus the latest actual per row. It returns `MaterialFigure` records (label, periods, value, the
  annual table's source_ref). The guard now reads it. So does `synthesize`, which appends a
  section opening `=== MATERIAL FIGURES — STATE EACH ONE ===` and listing each figure as the table
  holds it, the exact form the guard accepts (`"$4,544.0M"`; `_material_figures_digest` refuses to
  offer a form `_figure_cited` would not accept), and the source_ref. The section asks for each
  figure in an entry of `SYNTHESIS_CLAIM_LISTS` (bull_points, bear_points, key_unknowns), or in
  key_unknowns where it bears on neither case, and says a synthesis omitting one is refused. It
  carries no lean, direction or verdict word. No material row, no section.
- **The marks come first.** `assemble_one` now calls `_mark_material` immediately before
  `synthesize`, not after it. The model used to read `"material": false` on the rows the guard
  then demanded. Nothing between the two touches the financial summary, so the guard reads the
  same marks.
- Extraction version `2026-10-29.D-D5-prompt` (Python table and the `dossier.js` twin); drift
  pins re-pinned.

**WHY.** #858 widened "material" to 5% of revenue, and the 19c guard refuses a synthesis whose
prose never states a material row's figure. But the prompt never named those rows, so a page
passed only when a draw happened to state the figure unprompted. In the 2026-10-29 rebuild two
pages paid for five draws each and were refused: a merger and restructuring charge at 5.63% of
revenue (run `e0ecf6df`, $5.06) and in-process R&D at 9.33% (run `41a3c51b`, $2.91). The run ids,
costs and percentages come from the coordinating session's brief; this build did not re-read
those run records. The operator chose "Prompt fix first", so those pages build once each.

**HOW VERIFIED.**
- **Red on main, green here.** `tests/test_material_figures_in_prompt.py` captures the user
  message `synthesize` sends and reads its lines naming a material row back as prose. The guard
  must be satisfied by those lines alone.
  - On main, 11 of 11 tests fail. The six frozen tables (AMZN, GOOGL, LLY, MVST and WLK at
    c51c286a in the frozen SMPL carrier, plus the frozen SMPL page) fail with e.g. `LLY: the prompt
    sent never states ['In Process R & D Exp. ($M) LTM = -4,544.0']`; the corpus invariant fails
    the same way; the order pin fails `173 < 149` (`_mark_material` after `synthesize`).
  - On this branch all pass. The suite includes a negative pin (no material row, no section), a
    mutation pin (raising the floor empties both the guard and the section; a substituted
    selection is demanded by the guard and listed by the prompt), and a no-direction pin.
- **The prompt each version sends, all 27 committed pages** (each page's committed mechanical
  layer, marks stripped, captured with no LLM call, main 8d351bb8 against this branch):
  - **19 pages byte-identical.** These have no material row.
  - **8 pages differ in two places only:** `"material": true` on the marked row, and the section
    at the end. The 8 are AMZN, CNXC, GOOGL, LLY, MVST, NFLX, SMPL and WLK.
- **Shown run, one paid draw each** (`draws=1`, claude-opus-4-8). Inputs: the committed
  mechanical layer marked as `assemble_one` now marks it, the name's own sleeve, and both calls on
  file in the `-ta` CIQ folder, converted under an isolated LibreOffice profile. Written to
  scratch only; no page and no `assembly_runs` file.
  - **NFLX** (overshoot; demand `Merger & Related Restruct. Charges ($M) LTM = 2,800.0`): 19c
    PASS, 182,347 input / 4,520 output tokens, $1.0247. Bear point: "The LTM carries a $2,800.0M
    Merger & Related Restructuring charge — a non-recurring item sitting inside the trailing
    window that complicates reading the trailing figures cleanly." It also appears in a key
    unknown.
  - **LLY** (quality; demand `In Process R & D Exp. ($M) LTM = -4,544.0`): 19c PASS, 236,014
    input / 4,245 output tokens, $1.2862. Bull point: "…LTM Acquired In-Process R&D expense of
    $4,544.0M reflects aggressive, self-funded pipeline building."
  - **Before the review fix**, the section also offered a 1-dp billions form. One draw each on
    that prompt also passed: NFLX $1.0230 (a bear point and a key unknown), LLY $1.2947 (a key
    unknown). Shown-run spend in all: $4.63.
  - **Directional flags on the draws come from text the section does not touch.** LLY's 'fair
    value' is the quality sleeve's own twin-outcome wording ("re-rated to fair value",
    `vinci/sleeves.py`), and the committed LLY page carries the same flag. 'conviction' (first
    LLY draw) sits in an insider-selling key unknown. NFLX's 'sell' sits in a bear point
    reporting broker downgrades ("downgrades to Sell/Hold").

**BOUNDARY.**
- Page counts: the 27 `data/dossiers/*/dossier.json` at main 8d351bb8 (2026-10-29). "Material" is
  `_mark_material` on each page's committed annual table and market cap at that commit.
- Frozen tables: `tests/fixtures/materiality_revenue/annual_tables.json` (c51c286a).
- Shown runs: 2026-10-29/30 IST.
  - Demands come from the COMMITTED mechanical layers (both assembled 2026-10-26), not today's
    exports. The rebuild's own demand will differ: LLY's re-export moves its LTM to −8,070.0 per
    the brief, and NFLX's committed LTM reads +2,800.0 where the rebuild's read −2,800.0.
  - Transcripts: the `-ta` folders as of 2026-10-29 (LLY re-exported 23:00 with the Q3 call;
    NFLX 2026-10-28).
  - Costs are list price from `cost_usd`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A single draw passing is not a rate.** Two of two final-prompt draws (four of four in all)
  stated their figure. The rebuild's five-draw builds are the real measure.
  - Falsifier: a rebuild page refused by 19c with this section in its logged prompt.
- **The section names a figure; it does not place it.** The model chose a bull point on LLY and a
  bear point on NFLX. Saying which case a figure supports would be the direction this prompt must
  not set.
- **Found, not fixed (follow-ups):**
  - (1) `_synthesis_prose` lists `decisive_question` in `SYNTHESIS_CLAIM_SCALARS` but skips it,
    because it is an object, not a string. So a figure stated only in decisive-question evidence
    reads as uncited. The section names only the fields the guard reads.
  - (2) `_RATING_CTX` does not redact "downgrades to Sell/Hold", so a draw reporting broker
    downgrades raises a DIRECTIONAL flag.
  - (3) `refresh.material_figures` repeats the floor and estimate-column filter for its own
    every-cell selection.
  - (4) One NFLX draw echoed the house mark into prose ("flagged material").
