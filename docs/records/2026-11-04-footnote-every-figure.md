---
id: 2026-11-04-footnote-every-figure
status: open
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# Every figure of a synthesis point is footnoted to the fact that states it, or to the operation and cited inputs that compute it; the blocks the assembler builds carry a ref a point can cite (item 29)

**WHAT.** Item 29 is built as designed (Phase 1, `item29-design.md`) and as approved by the
operator, verbatim: *"for item 29, go ahead with 1 + 4"*, then *"The item-29 design: build approved"*.

**(1) Every figure footnoted.**
- **The shape.** `schemas.FigureCite` is `{figure, source_ref | derived + inputs}`. Exactly one of
  a ref and an operation; `derived` is one of `FIGURE_OPERATIONS` (difference, sum, ratio, premium,
  growth) with exactly two inputs.
- **The point.** `SourcedPoint.figures` is ABSENT when empty, so every committed point round-trips
  byte for byte.
- **The check, per figure** (`synthesis._validate` → `check_figure`):
  - A cited figure traces to ITS fact by the per-fact rule (G-D6).
  - A computed figure's two inputs must each have their own entry that traces. The declared
    operation is then recomputed on the inputs AS WRITTEN: each is an interval of half a unit of
    its last digit, the figure's own interval must meet the result, units must agree, and a
    percentile rank is never an operand.
  - A figure with no entry is traced to the point's own ref, exactly as before.
- **Flags.**
  - UNTRACEABLE, now naming the ref it was cited to (`[cited to …]`). The caveat reads "footnoted
    to <ref>, which does not contain it".
  - UNDERIVED: "Unverified computed figure …", a reader-facing caveat.
  - MISMATCH, for an entry naming no figure of the claim (QA only). A malformed model entry is
    dropped and named, and its figure falls back to the point's ref.
- **The prompt.** The tool schema makes `figures` required on every point. System rule (13), FOOTNOTE
  EVERY FIGURE, carries its shape contract and ONE literal example: LLY's committed FCF bear point,
  its refs read from the page, its "$19,661M" declared a difference. The example is pinned on a frozen
  copy of LLY's quality block (`tests/fixtures/item29/lly_quality_a439eabe.json`), so it never rots on
  LLY's next assembly.

**(4) Refs on the built blocks.** `schemas.SourceRefWhenBuilt` gives a `source_ref`, absent until
built, to:
- consensus levels, one per FY row, with both builders using `ciq_sheets.consensus_level_ref`;
- each peer capital row and the intensity block;
- each checked maturity;
- the EV/EBITDA bases (`headline_basis`, `ex_lease_at_price`);
- the EBITDA basis;
- implied expectations and each of its rows;
- a filed LTM's two CIQ readings (`filed_tiebreak.ciq_readings_ref`). #891 added this block while
  this branch was open, and the schema guard refused it on the merge: the annual export's LTM cell,
  which the page's table no longer shows, and the quarterly export's quarters summed sat under no
  ref of their own. No committed page carries the block yet.

Computations carry a ref that names the computation and its inputs, as "CIQ Net Debt ÷ CIQ EBITDA"
already did.

The EV-gap block is deliberately left without one: it is computed after the synthesis, which never
sees it (`test_synthesis_is_blind_to_the_gap`).

**The guard runs twice.**
- **On the schema.** No field that can state a figure sits under no ref, unless `NOT_A_FACT` names
  why: a label, a date, a parameter, machine QA, a twin of a cited fact, or the EV gap.
- **On every committed page.** Numbers no point could cite are refused. The blocks that now carry a
  ref are excused on a page assembled before this extraction version.

**Render.**
- **Web.** An endnote mark right after each footnoted figure (the tier's Sources list, deduped by
  ref) and ‡ after a computed one. In Analysis, a collapsed "How each figure is sourced (N)" block
  lists each figure's source inline and a computed figure's operation and inputs; it force-opens in
  print with every `<details>`. The page computes nothing.
- **Markdown.** The same marks, plus a "How each figure is sourced" line.

Extraction `2026-11-04.footnote-every-figure` (+ web twin), re-pinned.

**WHY.** An expert research team footnotes every figure and checks it against its source before the
memo goes to committee. #890's measurement found 49 of the 52 caveats on #886's pages were a real
figure cited to the wrong single fact. That is a citation-shape problem, which only a per-figure
citation fixes without loosening the trace.

**HOW VERIFIED.** All runs go through the real `_validate` / renderers with no model call.
- **Committed pages unchanged** (the 27 pages, the same at 4a820016, 8d2bb733 and 865c8b5c; main's
  code at each against this branch, the later two after merging main):
  - every `_validate` flag identical: 399 flags, 326 UNTRACEABLE;
  - the web render (`renderDossier`, node) byte-identical on all 27;
  - the Markdown render byte-identical on all 27;
  - every page round-trips through `dossier_json` byte for byte.
- **The prototype cases on committed pages** (refs read from each page's schema fields):
  - **Today → footnoted: 11 → 0 caveats.** AMZN's EV/EBITDA bear point (4 → 0), GOOGL's
    relative-laggard point (4 → 0) and LLY's FCF point (3 → 0, its "$19,661M" declared a
    difference).
  - **Negatives, all flagged:** every figure cited to one wrong ref; a made-up "457.3x" with its own
    entry; LLY's computed figure written "$21,661M" (UNDERIVED: difference gives 19,660 to 19,662);
    an input cited to a fact without it.
- **Made-up figures, bare against footnoted to the point's own ref:**
  - #890's 30 page versions: the same **1,362 of 1,564** caught either way.
  - Today's 27 pages: the same **1,236 of 1,408**.
  - The frozen G-D6 draw: 195 of 199 either way (pinned).
  - **Made-up COMPUTED figures** declared from two real, traced inputs: 1,564 of 1,564 and 1,408 of
    1,408 caught.
  - Re-run on the code after the review round and the merge with main (c46310e3): every count above
    reproduces, set for set.
- **Pins.** `tests/test_footnote_every_figure.py`, 85 cases:
  - schema and serializer;
  - the per-figure check, positive and negative, on frozen SMPL;
  - derived arithmetic and units;
  - a malformed entry;
  - the legacy-equivalence invariant over every committed page;
  - the prompt example against frozen LLY facts;
  - both guards;
  - each producer's ref, the filed LTM's on CELH's and NFLX's committed fixture rows (a point
    footnoting its readings to that ref traces; to a quarter's filing, or on a block built before
    it, it does not);
  - the review round's five (a footnote covers only its own figure, a transcript-looking ref the
    page lacks, a non-list `inputs`, a mark inside a decimal, a tag's place before the cite);
  - the web e2e (a mark per figure, ‡, the collapsed block, the print rule) and Markdown.
- **Screenshots** in `docs/dossier/footnote-every-figure-2026-11-04/screenshots/`: GOOGL, LLY and
  AMZN, one committed point each with `figures` injected, collapsed and force-open, from this
  branch's renderer. No console errors.

**BOUNDARY.**
- The committed corpus is the 27 `data/dossiers/*/dossier.json` at 4a820016, measured 2026-11-04,
  and unchanged at 8d2bb733 and 865c8b5c (`git diff 4a820016 865c8b5c -- data/dossiers` is empty).
  The 30-version population is 9e996d7f's 27 pages plus #886's three at 2746d0ef.
- Mutations: one-point syntheses through the real `_validate`, seeded `20261104:<T>`, four per
  committed structured point.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No page changes in this PR, and no assembly spend.** Each page draws footnotes at its next
  assembly, about $3–6 a page at #886's costs. Until then it renders and checks as before. The
  model's compliance is unmeasured until the first re-draw.
- The large-fact residual of G-D6 is unchanged: a made-up figure footnoted to a fact holding hundreds
  of numbers can still trace (172 of 1,408 today). It now shows as that fact's footnote beside the
  figure.
- A computed figure can only be one of the five operations. A median, a CAGR or a three-input
  figure is cited to the fact that states it, or flagged.
