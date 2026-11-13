---
status: open
date: 2026-11-09
prs: [936]
supersedes:
superseded-by:
---

# Fix request 2, order 2, the page group (RBC-D1, RA-D1, RBC-D8): the customer count is a structured field, PARR's surprise history is its own listing's, and NFLX's tie-break no longer says the filing confirmed the row. at $0, 20 of 28 page records move and 27 pages re-render; 7 print no customer count until each is re-assembled

**WHAT.**
- **RBC-D1, the customer count.**
  - The fault: both renderers (`render._fmt_customers`, `dossier.js` `fmtCustomers`) counted the
    ";" pieces of the stored roster. The roster keeps 30 rows plus "…(+N more)"
    (`ciq_sheets._roster`), so every list over 30 rows printed "31 mapped client relationship(s)".
  - The fix: `Concentration.customers_listed` (`DROP_WHEN_NONE`) holds every recently disclosed
    row the export lists. `ciq_sheets.customer_roster` returns it with the roster, from the parsed
    list before the cap. Both renderers print it. A page without it prints "mapped client
    relationships (count not recorded on this page)", never a number read back out of the roster
    string.
- **RA-D1, the surprise history.**
  - The fault: `ciq_sheets.surprise_history` read the first "EPS (GAAP)" row anywhere on
    Estimates→Surprise. Par Pacific's sheet opens with its predecessor's OTC listing
    (OTCPK:DPTR.Q), so the page stated that listing's FY2006–FY2010 ("+0%" each) as PARR's.
  - The fix: `_surprise_eps_block` reads the block CIQ heads with the company's own listing
    ("<exchange>:<ticker> (<ccy>)"), in the fiscal-year table only. CIQ repeats every block under
    "Calendar Years"; the first mutation test found the read falling through to that table.
  - The source_ref names the block read when the sheet's first listing is another one's. A sheet
    with no block of the company's refuses the GAAP-EPS read and names the listings it holds.
  - An own block with no "EPS (GAAP)" row says so, and its citation claims no EPS read.
  - Symbols match as share classes: "BRK.B" equals "BRK-B" (`_share_symbol`). The Trends reader's
    nested copy of that rule (audit A-D10) now calls the same helper.
  - The Revenue row ("Company Level") is read in the fiscal-year table only, against its own
    block's header. On every export on file that is the row and header the old read took.
  - The last three came from the code review (round 0, below).
- **RBC-D8, the containing-line headline.**
  - The fault: the caveat opened "CIQ READING CONFIRMED BY THE FILING". The filing states only the
    wider line (`NonoperatingIncomeExpense`), so the check confirms CIQ's breakdown of that line,
    and any split of it between the row and its parts passes.
  - The fix: the headline now reads "CIQ'S BREAKDOWN RECONCILES TO THE FILED LINE; THE ROW'S OWN
    FIGURE IS CIQ'S, NOT THE FILING'S" (`filed_tiebreak.CONTAINING_HEADLINE`). The check is
    unchanged: no filed concept can tell the splits apart, so the words say what was checked
    rather than the check being strengthened.
- **The $0 writers** (no assembly, no LLM, no network). Each records itself in `layer_refreshes`.
  - `vinci ciq-reread --field customers_listed`
    - writes the count only where the roster re-read from the export on disk equals the stored
      roster byte for byte: value, note, status and source_ref;
    - the Customers export is not stamped in `inputs`, so the roster is the only proof of vintage.
  - `vinci ciq-reread --field surprise_history`
    - writes only where the Estimates export on disk hashes to the page's stamped sha256;
    - refuses if any synthesis claim cites the field.
  - `vinci caveat-reword`
    - rewords a caveat under a retired headline (`filed_tiebreak.RETIRED_HEADLINES`);
    - the rest of the caveat is left as stored.
- Extraction version `2026-11-09.order2-pages`; the drift pins are re-pinned.

**WHY.** These are three of the seven defects TeamNostra's fix request 2 (document 15, 2026-11-09)
lists under order 2 as live on committed pages. CLAUDE.md forbids re-parsing a display string, so
the count rides as a structured field, and a page that cannot be given one prints none.

**HOW VERIFIED.**
- **Fail first.** The new and changed pins, run against main `cb8139ee`'s code in a detached
  checkout: 40 fail. Among them:
  - `test_every_committed_page_prints_its_structured_count_or_none[AMZN]` reads
    "- **Customers:** 31 mapped client relationship(s)";
  - `test_parrs_committed_page_states_its_own_listings_surprise_history` reads "GAAP-EPS
    surprise: FY2006 +0% … FY2010 +0%";
  - `test_nflxs_committed_page_carries_the_caveat_the_code_writes` fails.
  On this branch all of them pass.
- **Corpus before synthetic.**
  - Before any write, the new surprise reader was run against every committed page whose Estimates
    export is on disk.
    - 25 of 28 pages re-read byte-identical, AORT has no export, and only PARR moves.
    - V also moved: its export was re-exported at 21:07 today and carries FY2026, and its stamped
      sha256 differs, so the writer refuses it.
  - The panel table for the surprise fix came from a sweep of all 36 on-disk exports: each one but
    PARR's opens with the company's own listing.
  - The customer writer's refusals are real: each refused page's export on disk has been replaced
    since its build (EPAM 20:58 today, V 21:05, WLK 21:02, UBER 2026-11-06, NCNO 2026-10-29), or
    its roster was built by an older reader (TECX, the prior-section split of #878).
- **Real runs.**
  - `ciq-reread --field customers_listed` over the 27 pages with a PRESENT roster wrote 20,
    refused 6 and skipped 1:
    - written: AMZN 726, BRBR 5, CNXC 3, FUBO 8, GOOGL 653, IT 5, LLY 54, MCK 8, MVST 6, NFLX 49,
      NKE 34, ORKA 1, PARR 4, ROST 1, SMPL 6, TGT 8, TJX 1, VITL 15, VRRM 4, WERN 2;
    - refused: EPAM, NCNO, TECX, UBER, V, WLK;
    - skipped: AORT, which has no export on disk.
    - The audit's true counts (AMZN 726, GOOGL 653, LLY 54, NFLX 49, NKE 34) are reproduced.
  - `--field surprise_history` wrote PARR: its export `2d58fb99…` is the stamped one. The page
    now states NYSE:PARR's FY2014–FY2025 (FY2023 +52%, FY2025 +18%).
  - `caveat-reword` wrote NFLX caveat 5. The frozen fixture reproduces NFLX's caveat byte for
    byte under the new headline.
  - Every page was then re-rendered and mirrored to `frontend/`.
  - Each changed `dossier.json` differs from HEAD only at `layer_refreshes`,
    `mechanical.concentration.customers_listed`, PARR's `surprise_history` value and source_ref,
    and NFLX's `caveats[5]` (script diff, every page printed).
- **The synthesis.** No request changes. The count is the roster's display twin and is not sent
  (`synthesis.NOT_SENT`). All 28 pages' synthesis requests, built by main's code
  (`replay.capture_at("HEAD")`) and by this branch's, are byte-identical, so row 53 owes no panel
  measurement. The first gate caught the field reaching the request; that is why it is excluded.
- **Prechecks, $0** (`vinci.dossier.prespend.run`, run against the primary checkout's data dir;
  nothing written to `data/dossiers`). These are the pages that only a paid re-assembly can give a
  count. Every one exits 1 (STOP):
  - NCNO, TECX, EPAM, WLK: a post-spend `FreshnessError`. Each one's oldest panel is 130d old
    (`stock_info.as_of` 2026-07-02 in that store), against the 45d ceiling.
    - NCNO regresses 2 fields (`catalyst_path.guidance_bridge`, `_rows`: guidance dated after the
      price date, row 57).
    - TECX regresses 1 (`concentration.customers`, the prior-section read of #878).
    - EPAM and WLK regress 4 each (the two guidance fields, `idiosyncratic_vs_shared.rel_vs_market`
      and others).
  - UBER, V: refused at $0, "no price history in the store".
  - AORT: 63 regressions and 2 refusals. There is no Financials export on disk, so
    `MaterialityUnavailableError` fires, and market cap is missing.
- **Gate.** `bin/commit` green, CIQ unlinked (CI's view): ruff, `mypy --strict vinci` and
  `pytest -m "not network"`.
- **Code review (round 0, `/code-review high --fix`):** 10 findings.
  - Fixed (6):
    - the Revenue read in the fiscal-year table, against its own block's header;
    - share-class matching;
    - the no-EPS-row note and citation;
    - writer pins for `surprise_history` (a write; refusals for a sha256 mismatch and a cited field);
    - the `RETIRED_HEADLINES` comment now says what `reworded()` checks;
    - `provenance.file_sha256` replaces a second hashing path.
  - Not changed (4):
    - the record and STATE, which this commit writes;
    - the three pages that lose a count, an accepted cost (below);
    - code and pages in one commit, because the e2e pins read the pages and no split is green;
    - a value with no EPS series still ends "(GAAP-EPS basis; …)", as before this branch, because
      changing it moves committed pages.

**BOUNDARY.**
- Pages: `data/dossiers/*/dossier.json` at `cb8139ee`, 28 pages. 27 carry a PRESENT customer
  roster; BURL's is UNKNOWN.
- CIQ: the operator's Drive `manual/ciq`, read in place on 2026-11-09 between about 21:10 and
  21:40 IST, while that folder was being re-exported (VITL 20:49, VRRM 20:54, EPAM 20:58, WLK
  21:02, V 21:08). A page whose export moved is refused, not read.
- Counts: rows CIQ lists under "Recently Disclosed Customers".

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Seven pages print "count not recorded on this page" until each is re-assembled (paid): AORT,
  EPAM, NCNO, TECX, UBER and V, plus WLK.
  - Three of them printed a count before. AORT printed 4 and WLK 16; neither can be shown right,
    because AORT has no export on disk and WLK's export was replaced today. TECX printed 2, which
    #878 had already found wrong.
  - The other four (EPAM, NCNO, UBER, V) printed "31", wrong in all but NCNO's case.
  - Their prechecks are above and in STATE.md §5.0: all seven STOP.
  - Falsifier: a re-assembled page that still prints no count.
- RBC-D8's value half is unchanged by design: a different split of the same filed line still
  passes, and the page now says the figure is CIQ's. Reading the 10-Q's own text on the fee
  would settle it; that is not built.
- **A guarded file was edited around its hook once.** `vinci/dossier/schemas.py` is on
  `decision_path_guard.py`'s list (it holds the `Synthesis` field set). Three edits were made to it:
  - two went through the Edit tool, which the hook sees: `Concentration.customers_listed`, and its
    `DROP_WHEN_NONE` entry;
  - one went through a Bash script, which the hook does not see: the two writer names in
    `LAYER_REFRESH_WRITERS` and `LayerRefresh.writer`.
  - None touches `Synthesis`. The operator should read that diff as one the hook did not ask about.
## Amendments

- **2026-11-13 — what this PR's next build changes, from the impact sweep** (operator ruling 3, 2026-11-12, verbatim: "Yes, as appended amendments (Recommended)"). The body above is unchanged. The sweep ran this PR with `vinci.impact` (base `7c87164a`, head `6fbbb4a2`, measured 2026-11-11, $0): base code against head code on the same inputs, which shows what each page's NEXT build would change. Its record, with all 49 rows, is `docs/records/2026-11-13-fix2-impact-sweep.md`.
  - **#936: PARR's synthesis request moves**, in its `facts` section (the surprise history, now read from the NYSE:PARR block, RA-D1). PARR is off the panel. The body says "All 28 pages' synthesis requests, built by main's code (`replay.capture_at("HEAD")`) and by this branch's, are byte-identical". That compare held each committed page fixed, so it could not see the page's own re-read.
