---
id:
status: shipped
date: 2026-11-17
prs: [1100]
supersedes:
superseded-by:
---

# A WATCH PAGE SAYS IT IS FROZEN (STATE row 41 (b)): each of the 15 watch pages prints, above its Brief on both surfaces, the date and ruling of its move to watch, that it is kept as committed with no paid rebuild until it goes active, and the known defects it keeps; the line is read from the coverage roster at render and deploy, never stored in a page; the defects are a committed file bound to the page field each lives in, and of the six the marking named, three measure as still on their pages (UBER row 28, PARR row 34, ORKA row 35); 15 `dossier.md` + 15 mirrors move by the line alone, 0 `dossier.json` ($0)

**WHAT.**
- **The line.** A page whose name's latest roster move is `watch` prints one block under its date
  and stamp line:
  - md (`render._watch_lines`): above the Brief;
  - web (`dossier.js` `watchLine`): in the page header, above the tier tabs and outside every
    `<details>`, so the collapsed page, the force-opened one and both PDF scopes carry it.

  It names:
  - the move's date and the operator's ruling, with its source and record (from the roster line);
  - that the page is kept as committed, with no paid rebuild, until the name goes active;
  - each known defect, closing on its STATE row and record.

  UBER's prints:

  > **Frozen since 2026-11-13: UBER is on watch.** The operator's ruling: "go ahead" (issue #1004
  > comment 6847554747; docs/records/2026-11-13-fix2-bookkeeping-batch-8.md). This page is kept as
  > committed, with no paid rebuild, until UBER goes active.
  > **Known defects it keeps until then:** 1. Its R4 valuation is not priceable: its Financials and
  > comps exports sit on different balance sheets, so the comps are owed a re-export (STATE row 28;
  > docs/records/2026-11-12-rebuild-prep-prechecks-on-all-27-pages.md).

  A watch page with no listed defect prints the first paragraph only. An active page prints
  nothing new.
- **Read from the roster, never stored.**
  - md: the renderer reads `coverage_roster.jsonl` and `watch_defects.json` beside the tree it
    renders (the `dossiers_root` every writer passes, the known-wrong banner's rule).
  - web: `frontend/build.py` writes `snapshots/coverage.json` on every deploy, git-ignored like
    `extraction_versions.json`; `snapshots.js` `getCoverage()` reads it.

  So a move to active removes the line at the next render with no page edit. A committed md that
  keeps the line after that move fails the live-render drift pin
  (`test_screening_context_reaches_every_committed_dossier_e2e`).
- **The defects: `data/watch_defects.json`** (un-ignored, `.gitignore` (h)).
  - The file maps each ticker to its defects. A name with no defect has no key.
  - Each defect carries `defect`, `state_row`, `record`, `page_field` (a JSON pointer into
    `dossier.json`), `page_value` (what the page holds there) and `measured` (the date and commit).
  - `vinci.coverage_roster.read_defects` reads it strictly, in one canonical form. A roster
    with no defect file beside it is refused, and so is a malformed file.
  - `watch_notice` prints only the defects the page being rendered still `holds`, read as its one
    writer (`dossier_json`) writes it. `frontend/build.py` does the same from the committed page,
    so the line never names a defect the page no longer has, on either surface.
  - The suite (`defect_problems`, over every committed page) refuses:
    - an entry whose committed page no longer holds its value;
    - an entry listed for a name that is neither watch nor active.

    So a rebuild or a refresh past a defect, or a retirement, goes red until the entry is removed.
  - **Review round 0 moved that check from the render to the suite.** The first cut refused at
    render, and two problems followed:
    - the cross-setup harness renders a fresh $0 build of every watch name (`vinci/impact/child.py`),
      which holds none of its committed page's defects (PARR's build has no covenant rows), so
      every future impact run would have reported a render failure there;
    - one stale entry, for example a name retired by its one roster line, stopped every other
      watch page's render.

    The output on every committed page is unchanged.
- **A tree with no roster renders no line.** That is a scratch copy, never the data tree, whose
  roster every fleet reader and `vinci dossier` already require. The first cut raised there, and
  about 20 test files that copy real pages into roster-less scratch trees went red. Reading the
  configured tree's roster instead would paste the live roster onto a copy built to differ from
  it. That is the two-sources defect `_known_wrong_lines` documents.
- **If the deploy's coverage table does not load,** the web page says "This deploy's coverage
  roster did not load", never nothing, since nothing reads as "not on watch".

**WHY.**
- **The design.** B's design (issue #1004 comment 6847522000, item 6) gave each watch page "a dated
  'frozen' line until it goes active". The operator's marking (comment 6847554747, 2026-11-13, "go
  ahead") says the watch pages "stay as committed" and names the six that keep known errors:
  - UBER (rows 28 and 34);
  - WLK, PARR, AMZN and NFLX (row 34);
  - ORKA (row 35).
- **The defect list as measured.** Before any defect went onto a page, each claim was re-measured
  on the committed pages. Four of the six row-34 claims were written before their pages were
  re-assembled on #838's withholding extractor (`covenant_extract.rate_components`), and are gone:

  | page | claim | measured on the committed page | listed |
  |---|---|---|---|
  | UBER | row 28: R4 not priceable, comps owed | still there: `/valuation_basis/priceable` is false (the bridge, $5,356M, disagrees with CIQ's TEV less market cap, $8,973M) | yes |
  | PARR | row 34 | still there: `covenant_term_rows/value/2/margin_bps` = 225, printed "LIBOR Rate + 225 bps"; one level of a pricing grid, which #838's record diagnosed as a wrong value; page assembled 2026-10-26 | yes |
  | ORKA | row 35 | still there: the insider line reads "sells 98 (7 insiders, $335.55M)", with its last sale dated 2026-10-20 on a page referenced 2026-10-16, and a bear point quotes the 98 | yes |
  | UBER | row 34 | gone: re-assembled 2026-11-09; 8 of 8 components stated | no |
  | WLK | row 34 | gone: re-assembled 2026-11-09; 1 of 1 stated | no |
  | AMZN | row 34 | gone: re-assembled 2026-11-03; 6 of 6 stated | no |
  | NFLX | row 34 | gone: re-assembled 2026-11-05; 5 of 5 stated, 1 withheld with its (E5) flag | no |

  Operator, 2026-11-17, relayed by A: **"The three that measure (Recommended)"** for the defect
  list, and **"Approve as shown (Recommended)"** for the preview (the wording, the placement above
  the tabs, and `data/watch_defects.json` with its page-value guard).
- **Why a file and not a field on the roster move.**
  - A move is a coverage decision, and the reader refuses a move that repeats a status. A defect
    fixed by a $0 refresh while its name stays on watch could not be recorded on the roster at
    all.
  - The roster's six fields are strict on every line, so a seventh would rewrite an append-only
    log.

  A defect is a fact about a page, so it is bound to the page field it lives in.
- **Why not `known_wrong.json`.** It seals a record: `refresh_dossier` refuses it, and the $0
  refreshes watch pages still get would stop. Its banner, "do not read the figures on this page as
  current", also says more than "stay as committed".
- **STATE row 34 is corrected in the same change.** It said that AMZN, NFLX, UBER and WLK keep the
  lead until they go active.

**HOW VERIFIED.**
- **Preview (PREVIEW RULE).**
  - Inputs: UBER (watch, a defect), BURL (watch, none) and SMPL (active).
  - Rendering: production `renderDossier` with `frontend/assets/styles.css` under headless Chrome,
    collapsed and force-open, plus Brief and Full PDFs. BEFORE was `4889ddba`'s code; AFTER was this
    branch. The input JSON was identical.
  - Results: the line prints on page 1 of both PDF scopes. Page counts are unchanged: UBER 6/30,
    BURL 6/25, SMPL 9/34.
  - The operator approved it as shown (above).
- **The $0 re-render.** `refresh_fleet()` from the branch (no transform):
  - moved 15 (the watch pages), left 11 unchanged (the active pages), refused 0 and skipped 0;
  - the diff is 30 files, +84 −0: 15 `dossier.md` and their 15 byte-identical mirrors;
  - 12 pages gain 2 lines and the 3 with defects gain 6;
  - no `dossier.json` and no `index.json` moved.
- **Pins:** `tests/test_watch_frozen_line.py`, each on the real roster, defect file and pages.
  - **md and web:** the line is on every watch page and on no active page, above the Brief or tier
    tabs. The web text equals the md text word for word.
  - **Artifacts:** the committed md and its mirror carry the line.
  - **Citations:** every defect cites an open §5.0 row and an existing record, and still holds its
    value on its page.
  - **Going active:** an appended move to active removes the line on both surfaces.
  - **Guards:**
    - a listed defect whose field is moved or missing on its page is printed on neither surface,
      the page keeps its line, and the suite's check names the entry (run on whichever defect
      is listed first, never a hard-coded value);
    - an entry for MVST (retired) or an unlisted name is named by the suite's check, and the
      listed page still renders;
    - refused: a roster with no defect file, and eight malformed-file shapes;
    - a roster that did not load on the web is SAID, never silent.

    The positive pin sits beside each one.
- **Test trees that gained the file:**
  - `tests/roster_support.write_roster` writes an empty defect file beside the roster;
  - `test_refresh_fleet_and_bridge_guards` copies the committed one;
  - `test_refresh_path::test_a_noop_refresh_is_byte_identical` now lays its copy out as the data
    tree, with the roster and defect file beside the pages. In a tree with no roster, the 15
    committed watch pages re-rendered without their line and read as churn. It failed on the
    re-rendered pages at `29924075` and passes at `b2bcf8c1`.
- **Suite at `29924075`** (8 workers, `-m "not network"`): 4 failures.
  - `test_records_ledger` (this record's empty `prs:`, filled once the PR exists) and the no-op
    refresh pin above are this PR's.
  - Two `test_theme_intelligence_group3` browser tests failed under machine load (load average
    10–22, other sessions' suites running) and pass alone, 2 of 2.

**BOUNDARY.**
- **The defect measurement:**
  - 26 committed pages at main `4889ddba`, 2026-11-17;
  - row 34 through the release scorecard's own covenant check (`figure_in_own_quote`'s
    `_stored_figures` + `_quote_value`) over each page's present `covenant_term_rows`;
  - rows 28 and 35 read from the page fields named above.
- **Other stored components the same check counts:**
  - BURL (watch) stores 2 that its quote does not state (a 1.50% grid level as margin and a 0%
    floor). Its term is withheld as UNKNOWN on both surfaces, so neither prints.
  - BRBR (active) stores 1, a 0.75% floor that its lead does not print; its table names it in a QA
    flag.

  Neither is listed. BURL's prints nowhere, and BRBR is active and owes its rebuild.
- **The re-render:** the 26 pages the roster covers, at `4889ddba` plus this branch.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A defect's binding is index-based** (`covenant_term_rows/value/2`). A frozen page does not
   reorder its rows; if one does, the defect drops from the line and the suite refuses its entry,
   rather than mis-bind.

   Falsifier: an entry refused while its defect is still on the page.
2. **An active page with a known defect prints no line.** The line is the watch status, by the
   brief. A name that goes active keeps its entries until its rebuild moves the bound value, which
   the suite then refuses until the entry is removed.

   Falsifier: an active page served for long with a listed defect and no rebuild.
3. **A scratch tree with no roster renders no line** (above). The data tree's line is held by the
   suite, not by the renderer, and so is the defect file's agreement with the committed pages.

   Falsifier: a committed watch page without its line, or naming a defect it no longer holds,
   passing the suite.
4. **Review round 0, deferred.** `refresh.band_checks_backfill` and `cli._attach_midcycle` write
   `dossier.json` before they render `dossier.md`. Unlike `refresh_dossier`, which renders first,
   they leave the JSON written if the render raises. This change adds two ways for a render to
   raise: an absent or malformed defect file beside a roster. Each would leave that page's md stale
   against its JSON, and the drift pins go red. The reorder is in code outside this change, and it
   has its own falsifier: a half-written page from either path.
5. **$0.** No model call, no vendor call; the pages move by render only.
