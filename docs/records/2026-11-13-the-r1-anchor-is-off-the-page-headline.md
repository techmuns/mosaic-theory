---
status: shipped
date: 2026-11-13
prs: [1054]
supersedes:
superseded-by:
---

# The R1 screening anchor is off the page headline (#1004 item 3c): the block moves, unchanged, off the Brief to the end of Analysis → Valuation, after "Own-history range position", on all 26 pages, web and markdown; a page with no scenario record keeps a one-line pointer; anchor ÷ price stays unprinted

**THE RULINGS.** The operator, 2026-11-13, on the Phase-1 preview, relayed by the coordinator (A),
verbatim:
- placement: *"Approve as shown (Recommended)"*;
- the ratio: *"Keep it off (Recommended)"*. Anchor ÷ price stays unprinted, and
  `test_screening_context_never_differences_the_anchor_against_spot` stays as it is.

The design is B's #1004 note (issuecomment-6847522000, "### 3. The recipes", item (c)). A's reply
(issuecomment-6847633111) explains why 3c is render-only. The R1 anchor is computed after the
synthesis call: `assemble.py` synthesizes, and the anchor is persisted after `ev_gap_transform`.
So moving where it renders changes no synthesis request. The impact run below confirms that.

**WHAT.** The screening block is `anchorInner()` on the web and `_screening_context_lines()` in the
markdown. It rendered in exactly one place per twin: the Brief, card 2, "Scenario analysis". On a
page with no scenario record, the anchor was the card's only content. It now renders at the end of
the Analysis tier's Valuation section, directly after "Own-history range position". That line
states today's multiple and the median the anchor re-rates to, so what the screen value assumes is
read beside it.

The block's content is unchanged, byte for byte:
- every row;
- `data_quality` and its detail;
- the mid-cycle strain line;
- the operator's decision and the machine's read;
- the INAPPLICABLE `reason`.

It stays main body, never inside a `<details>`. On a page with an anchor and no scenario record,
the Brief card stays. It states the absence and adds one pointer sentence, hand-copied in both
twins (`SCREEN_POINTER` / `_SCREEN_POINTER`, pinned equal). Main 12764514's two renderers had the
block nowhere else. Searched: the dossier index, the ranker and queue views, and `build.py` (none
render it).

**WHY.** B's diagnosis, re-checked by A at main `12764514`: R1's screen value read 2.0–10.6× the
page price on 8 of the 26 pages. VRRM, the one AVOID, read $23.23 against $2.19, or 10.6×. On a
no-record page it was the first valuation level on page 1, so it flattered exactly the de-rated
names. The Brief is the first cut (PASS vs READ DEEPER), and a mechanical re-rate is the wrong
figure to lead it.

The three-tier rule keeps the block MAIN BODY rather than on-demand: on the 19 no-record pages it
is the document's only valuation level. History: the three-tier redesign (`2a8dab72`, 2026-07-21)
returned the block from the Appendix to the Brief, "beside the underwrite it feeds"; this moves it
to Analysis.

**HOW VERIFIED.**
- **Phase-1 preview ($0, from committed JSON, before any commit).**
  - Pages: VRRM, SMPL, IT, NCNO (inapplicable, with a record) and VITL (inapplicable, no record).
  - Rendered on the web, collapsed and force-open, and in both PDF scopes, which are
    `window.print()` of the page: the Brief scope and the full dossier.
  - The block's text is identical before (Brief) and after (Analysis → Valuation) on all 10
    page×state pairs, with 0 console errors.
  - The Brief-scope PDF no longer carries the block. The full PDF carries it under Valuation:
    VRRM p2 → p12, SMPL p5 → p17, IT p4–5 → p12, NCNO p5 → p11, VITL p2 → p12.
  - NCNO's and VITL's INAPPLICABLE reasons print in full.
- **Markdown, all 26 pages.**
  - The control: main's code renders 26 of 26 identical to the committed `.md`.
  - With the change, 26 of 26 move. The 7 record pages add or remove 0 non-blank lines (a pure
    move). The 19 no-record pages add exactly the 1 pointer line.
- **Tests:** `tests/test_anchor_off_headline.py`, 9 tests, end to end from committed JSON through
  the production renderers. Each is red on main's renderers: main's `render.py` and `dossier.js`
  were swapped in, then restored by sha256. They pin:
  - the block is off the Brief on all 26 pages (md, web);
  - it sits under Valuation after the own-history row (md, web), outside every `<details>`
    (collapsed and force-open);
  - the pointer is on no-record pages only, and the twins agree;
  - the INAPPLICABLE reason moves with the block (md, web);
  - the print path: tier membership, plus the three print-scope rules in `styles.css`.
- **Artifact pass ($0, commit `b1326afc`):**
  - Ran production's own `refresh._rerender_only` on every page, then `mirror_to_frontend()`.
  - 26 of 26 pages moved: 26 `dossier.md` files and their 26 `frontend/dossiers/*.md` mirrors.
  - Every `dossier.json` and JSON mirror is byte-identical (`git diff --quiet`).
  - The five previewed pages are byte-identical to the preview's renders.
  - The full gate (`bin/commit`) is green: ruff, `mypy --strict vinci` (219 files), and pytest:
    11,156 passed, 652 skipped, 11 xfailed, 0 failed (counted from the progress lines). The
    frontend mirror is in sync.
  - Before the pass, the code-only tree (commit `4b420bcc`) failed exactly 3 tests, all
    stale-artifact pins: `test_parity_pins::test_screening_context_reaches_every_committed_dossier_e2e`,
    `test_dossier::test_analysis_tier_reads_in_decision_order_e2e`, and the `test_refresh_path`
    no-op refresh, which would have rewritten all 26 pages.
- **Cross-setup validation** (`python -m vinci.impact run`, RUNBOOKS §o; base `b207c8a9` = the
  merge base with `origin/main`; head `cb08c15f`; $0; vendor pulls refused; wall 350 s; the full
  section is in #1054's body):
  - **Synthesis requests:** 0 of 25 pages' requests differ, and the frozen panel (BURL, CNXC,
    LLY, MCK, ROST, SMPL) is 0 of 6. So the row-53 panel check is not owed, and A's
    "render-only" reasoning holds.
  - **Pages:** 0 of 25 move a field.
  - **Rendered surface:** 26 of 26 committed `dossier.md` files re-render, which is the move
    itself, already committed in `b1326afc`. Head's code owes 0 re-renders.
  - **Downstream:** the ledger, scoring report, monitor, screen and theme desk are not reached.
  - **PARR is built at neither ref:** its CIQ quarterly export is a byte copy of the annual one
    (`CiqMislabelledError`). That is an input problem, not a code effect.
  - **Fail-first:** 5 of the 9 new tests fail on base `vinci/`. The tool swaps only `vinci/`, so
    the 4 web tests pass at both refs there. With main's `dossier.js` swapped in by hand, all 9
    fail.
  - `vinci.impact verify` says VALID at head.

**BOUNDARY.**
- "26 pages" means every `data/dossiers/*/dossier.json` at main `b207c8a9`, all 26 carrying an
  anchor block. 7 have a scenario record listed in `frontend/scenarios/index.json`: BRBR, EPAM,
  GOOGL, IT, NCNO, SMPL, WERN.
- "2.0–10.6× on 8 pages" is B's and A's measure at `12764514`. It divides
  `anchor.anchor_base_value_per_share` by `mechanical.stock_info.price` on each page, and the
  ratio is not printed anywhere.
- The preview's page numbers are from headless Chrome 157's `printToPDF`, with the app's own scope
  classes and `beforeprint` applied, on 2026-11-13.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A Brief-only PDF no longer carries the anchor. That is the point of the change; the full PDF
  and the web Analysis tab do.
- The hand-copied pointer is a twin, pinned equal.
- Nothing was accepted as risk.

## Review round 0 (`/code-review high --fix`)

Six findings:
1. **The pointer's last clause is untrue on 6 of the 19 pages that carry it: FUBO, ORKA, TECX,
   UBER, V and VITL.** The clause is "beside the own-history multiple it re-rates to". Those
   pages carry no screen value, and FUBO, ORKA, TECX and UBER carry no own-history multiple
   either. DEFERRED to the operator: the wording was approved as shown, VITL's pointer card
   included. The proposed fix is to drop the clause, which keeps a sentence true on every page.
2. **The screening table loses the `.uw-card` table styling under Valuation.** DISMISSED: the
   approved preview was drawn with this exact `dossier.js` (byte-identical to commit
   `4b420bcc`'s), so the shipped layout is the approved one.
3. **Warnings leave page 1 with the block:** 7 mid-cycle strain notices (AMZN, GOOGL, LLY, NFLX,
   PARR, VITL, WLK), 9 `data_quality` notices, and 4 operator decisions (AMZN, CNXC, GOOGL, UBER).
   The Brief-scope PDF no longer carries any of them. DEFERRED to the operator: the ruling moved
   the block unchanged. Whether those notices should also stay on the Brief is a placement call.
4. **No record and no STATE.md change.** FIXED: this file and the section-2 claim.
5. **A comment named the wrong file as the pointer's pin.** FIXED.
6. **The `_valuation_section_lines` docstring omitted the block.** FIXED.
