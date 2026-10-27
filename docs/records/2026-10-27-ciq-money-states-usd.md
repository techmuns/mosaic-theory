---
id:
status: shipped
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# A CIQ export's money must STATE USD: each money panel's stated currency is read, a stated other currency is refused before assembly, and the scorecard scores it; the checks that still store no outcome are measured

**WHAT.** Integrity wave 1, lane L1: the operator's pending items 9 and 10.

**Item 9: a CIQ export whose money is not USD can no longer pass silently.**

- `ciq_sheets.stated_currency(bundle)` reads the currency each CIQ money panel STATES, in the
  cells where the page reads it:
  - **Financials:** the per-column `Currency` row under each period header, and, on Capital
    Structure Details, the `Principal Due (USD)` header. The sheet's `Currency: Reported Currency`
    cell names a MODE, not a currency, and is never read as one.
  - **Estimates:** each section header's currency (`Company Level (USD)`, `NYSE:ONON (IFRS|CHF)`).
    Only the sections a page reads count: Company Level and the name's own listing. AMZN's
    `BOVESPA:AMZO34 (GDR)` / `SET:AMZN80 (GDR)` and HLF's `DB:HOO (EUR)` are other listings.
  - **Comps:** the `Currency:` label (`US Dollar`).
  - A block with **no currency-labelled header** (the Guidance sheet of BRBR, FUBO, MVST, PARR,
    VITL and ONON) reads the sheet's `Currency: Reported Currency` through the same export's
    Company Level sections, and says so in `where`. ONON's resolves to CHF, the others' to USD.
- **Not read**, because none of their values reaches a page as a money figure: Financials
  Multiples and Ratios, Estimates Multiples, Revisions (counts), Recent Changes (a revision log
  printed as plain numbers and ranked on % change), Comps Trading Multiples and Operating
  Statistics, Business Description, the credit-health scores (CIQ converts them to USD itself),
  and CHART exports (theme work, read by no page; the MSCI World Net precedent was one).
- **Per panel:** `agree` when every stated currency is in `USD_STATED` (`USD`, `US Dollar`);
  `differ` when one is not; `not_run` when the panel states none. An unfamiliar spelling of the
  dollar differs: it is refused, never guessed.
- **Assembly** (`mechanical.assemble_mechanical`) reads it first. A STATED other currency raises
  `CiqCurrencyError` before anything is fetched or paid for. A panel stating none is stored
  `not_run` and raises a QA flag. The read rides on the page as `mechanical.ciq_currency`, ABSENT
  until built.
- **Scorecard:** the new check `currency_stated_usd` counts one unit per panel. It is INTERNAL
  (CIQ's own label against the page's unit, a convention rather than a second figure) and declares
  `wrong_unit` alone: currency, never scale.
- **The scorecard's core** now splits an unguarded class by whether a second source EXISTS
  (`Family.fallback`), never by the family's derived class. The first real run exposed the old
  rule: consensus derives as internal on its currency alone, and the old split then counted its
  other four classes as "a second source exists" — false. No single-source family carried a check
  before, so every earlier snapshot and the prices source read the same.
- **Back-fill:** `refresh.ciq_currency_transform` writes the block onto committed pages through
  `refresh_fleet` (kept synthesis). It reads the workbooks only behind proof that each money
  workbook in the folder is the page's own:
  - the quarterly Financials and the Estimates by the sha256 the page stamps;
  - the annual Financials by its revenue and operating cash flow reproducing the page's annual
    table (#805's proof);
  - the comps book by its peer grid reproducing the page's, row for row.

**Item 10: checks that give no structured outcome, re-measured.**

- **The two band guards and `ciq_balance`'s scale check still store no outcome.** STOPPED by file
  ownership: all three run only inside `anchor.compute_anchor` / `cli._machine_anchor`, so storing
  agree / differ / not_run needs `vinci/dossier/anchor.py`, which is lane L2's this wave. Measured
  instead, from each committed page's own stored inputs through the producer's own functions
  (`r1_multiple_band`, `_band_read`, `band_guards.*`):

| guard | passed | tripped | never ran | of which: ex-lease history, no implied D&A margin | of which: guards not reached on the recipe path |
|---|--:|--:|--:|--:|--:|
| recorded D&A vs the sheet's implied D&A | 6 | 1 (VITL) | 20 | 14 | 6 (FUBO ORKA TECX: no own-history multiple; MVST NCNO: R2; UBER: R4) |
| market reconciliation | 20 | 1 (VITL) | 6 | 0 | 6 (the same six) |

  Every stored trip re-runs from its page's inputs, and no pass re-runs as a trip (0 mismatches).
  So a page with no recorded-D&A flag passed on 6 pages and never ran on 20, and the page cannot
  tell which. The reproduction also shows that a deterministic back-fill can write the outcomes
  once the anchor stores them.

  The scale check, run on the real workbooks: 25 of the 27 page names pass, 2 never run (ORKA and
  TECX carry no revenue to scale against), 0 fail. None of it reaches a page.
- **`guide_vs_release`, unchecked on 19 of the 26 pages it runs on (MVST carries no outcome).**
  By the decision branch, re-run from each page's stored inputs (the reads
  `refresh.cross_check_transform` proved):
  - **11: the releases state no numeric revenue guide.** BURL PARR TJX GOOGL UBER IT ROST NKE TGT
    V WLK. Of these, 4 parse a guide for another metric (BURL, TJX and TGT adjusted EPS; UBER
    adjusted EBITDA) and 7 parse no guide row of any metric (PARR GOOGL IT ROST NKE V WLK).
  - **4: CIQ's Guidance holds no revenue guide.** FUBO and WERN have bridge rows but none for
    revenue; ORKA and TECX export no Guidance sheet.
  - **3: cross-period, CIQ guides a quarter and the release a year.** NCNO NFLX SMPL.
  - **1: cross-basis, the release guides a CHANGE.** EPAM.

  Whether the 7 with no guide row guide nothing, or guide in a form the parser cannot read, is the
  release-parser lane's question (L5, wave 2; STATE §5.0 row 30 holds 22 unread ranges).
- **`wall_vs_10q`, unchecked on 26 of 27.**
  - **25: the 10-Q's debt section is `state='not_stated'`** — located, holding a composition
    table, stating no ≤12-month figure (`MaturityWall` note: *no near-term wall stated in filing*).
  - **1: no debt section located** (TECX, `maturity_wall` absent).

  Whether any of the 25 carries a year-by-year maturity table the extractor deliberately declines
  (its docstring cites the thousands-units trap) is not measured here.
- **`fcf_sign_vs_edgar_ocf`: its limit was already declared.** Tolerance *"SIGN ONLY, of two
  different measures"*; `catches` names wrong file and wrong cell only, never unit, period or
  definition. Nothing added.

**WHY.** Every CIQ money figure on a page is read as USD ($M), and nothing asserted it. #792's
search for one found none (its finding 7), and a CIQ chart export (MSCI World Net) had already
arrived in EUR, unlabelled. On the assembler's copy, ONON's workbooks state CHF on every Financials
and Estimates panel, while its Historical Capitalization (trading currency) and comps book
(converted at spot) state USD. A page built from it would set CHF EBITDA beside a USD TEV under one
dollar sign. Reading a foreign-currency workbook stays STATE §5.0 row 4's FPI5; this build makes
sure such a workbook is refused rather than misread.

**HOW VERIFIED.**

- **The census came first.** Before the reader existed, the header region of every money sheet in
  every folder of the assembler's copy was dumped. That showed the three shapes above, the
  foreign-listing sections, and the CHF case.
- **A first rule was wrong, and the corpus said so.** The first reader skipped an Estimates sheet
  with no currency-labelled section, taken as "no data". BRBR's and VITL's Guidance hold revenue
  guidance under a blank header, and both pages' guide checks AGREE, so that rule would have
  dropped real money panels from the check. The reported-currency resolution replaced it. A second
  rule ("a sheet with no period block holds nothing") had no real case in the 35 folders (ORKA's
  and TECX's exports simply lack the sheet), so it was removed rather than shipped speculative.
- **The real run.** The reader over all 35 folders:
  - the 27 page names: 484 panels, all USD;
  - the 7 other names: 126 panels, all USD;
  - ONON: 15 panels CHF (refused) and 3 USD.
- **The back-fill, for real, through `refresh_fleet`:**
  - 25 pages moved, 449 panels;
  - FUBO and TECX left absent and named: neither stamps a quarterly Financials export, so its
    workbook cannot be proved;
  - checked page by page against HEAD: each JSON gained only `mechanical.ciq_currency` and one
    `layer_refreshes` record, each `dossier.md` only its refresh line, and the frontend mirror
    followed.
- **Every proof held on every page it could test.** The Estimates sha matches 27 of 27; the
  quarterly Financials sha 25 of the 25 that stamp one; the annual table reproduces 27 of 27; the
  comps peer grid reproduces 27 of 27.
- **Pins** (`tests/test_ciq_currency.py`, 18 tests): run on frozen HEADER rows of the real exports
  (`tests/fixtures/ciq_currency_headers.json` — labels, period names and currency codes, no CIQ
  figure) built into the real `CiqBundle`. Each rule has a positive and a negative pin:
  - USD everywhere vs ONON's CHF;
  - another listing's section vs a read section in EUR;
  - the reported-currency resolution to USD (BRBR) vs to CHF (ONON);
  - a verbatim header naming `US Dollar` vs `Euro`;
  - an unstated panel (not_run, flagged, not refused) vs a differ, which outranks it;
  - a `No Data Available` shell vs a bare sheet;
  - euro repayment vs the panel's stated principal;
  - an exact dollar spelling vs an unfamiliar one.

  Further pins cover assembly's CALL SITE (refused before any store, EDGAR, network or graph read,
  each a tripwire; the stored read and the flag pinned on the function's AST), each back-fill
  proof refusing on its own, an end-to-end invariant over the committed blocks, and the scorecard
  mapping. A core pin covers the fallback-based split.
- **Mutation:** 27 mutants of the new production code, run in a scratch copy of the tree whose
  unmutated baseline passes: 13 in `ciq_sheets`, 3 in the assembly call site, 6 in the back-fill,
  4 in the CIQ source's check, and 1 in the core (the derived-class split restored, which three
  pins kill). 27 of 27 were killed.
- **The scorecard, by the real command:** `vinci audit quality --source ciq --write` on the
  back-filled pages wrote `data/snapshots/data_quality/ciq/2026-10-27.json`.

**THE ANSWER, BEFORE → AFTER** (the CIQ scorecard over the 27 committed pages, one unit per page,
or per panel for the new check):

| | BEFORE | AFTER |
|---|---|---|
| measured at | 47d8ca27 (main), page-set sha256 `e6e09ad9…` | 33a13b33, inputs matching it, page-set sha256 `e6cdc291…` |
| checks | 15 | 16 |
| `currency_stated_usd` | — | 449 of 449 panels confirmed on 25 pages; FUBO, TECX not run |
| coverage, 25 families (ind / int / single / unchecked) | 8 / 4 / 10 / 3 | 8 / 7 / 9 / 1 |
| wrong unit (ind / int only / none, a second source exists / none, single-source) | 8 / 3 / 4 / 10 | 8 / 7 / 1 / 9 |
| the other four failure classes | — | unchanged |
| UNSCORED entries | 2 (the scale check, `anchor.data_quality`) | the same 2 — item 10's STOPPED half |

The three families that move class do so ON THE CURRENCY CHECK ALONE, and their notes say so:
consensus (single-source → internal), segments and surprise (unchecked → internal). Nothing about
their VALUES gained a second source. Every other check's counts are unchanged between the two
points.

**BOUNDARY.**

- **Reader census and back-fill:** the assembler's workbook copy
  (`mosaic-theory-ta/data/manual/ciq`, read-only), read 2026-10-27. The census covers 35 folders,
  one unit per money panel the folder holds (18 possible). The back-fill covers the 27 committed
  pages at 5a2fe9e1.
- **Item 10's guide and wall causes:** the 27 committed pages at 47d8ca27, one unit per page, read
  off each page's stored inputs (no EDGAR read).
- **Band guards:** the same 27 pages, inputs re-run through the producer's functions at 47d8ca27.
- **Scale check:** `ciq_balance.extract` on the 27 page names' folders in the assembler's copy,
  2026-10-27.
- **Mutation counts:** over the 27 listed mutants; `tests/test_ciq_currency.py` for the 26, and
  `tests/test_quality_core.py` + `tests/test_quality_ciq.py` for the core's one.

**FOUND, NOT FIXED (out of scope; reported).**

- **The anchor-time outcomes need `anchor.py`** (item 10, STOPPED above). The spec, for whoever
  owns that file:
  - an optional outcome per guard on `Anchor`, set in `compute_anchor`'s R1 return;
  - one entry in `anchor_absent_fields`;
  - `not_run` on the ex-lease branch and wherever an input is missing;
  - then a back-fill, which the 0-mismatch reproduction above shows is possible.

  The scale check's outcome belongs wherever assembly keeps the CIQ bridge (L2's lane).
- **The SCALE statement is not read.** Financials sheets state `In Millions of the reported
  currency`, and Capital Structure Summary states ` Units: Millions`; Estimates state only
  `Units: Capital IQ (Default)`, and comps state none. The `wrong_unit` class's scale half rests on
  `ciq_balance`'s magnitude check, which reaches no page.
- **An instrument's repayment currency is carried verbatim and never set against the panel's**
  (AMZN's euro notes). Correct for the principal, which CIQ states in USD; a covenant or coupon
  read in the instrument's own currency is not checked.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **A foreign filer cannot be assembled at all now** — refused, not misread. That is the intended
  trade until FPI5 builds the reading.
- **FUBO's and TECX's blocks stay absent** until each is re-assembled (assembly writes it from the
  workbook); the card counts them not run, never a pass.
- **The reported-currency resolution trusts that a sheet's `Reported Currency` and the same
  export's Company Level sections mean one currency.** True by CIQ's own definition on every export
  read. Falsifier: a filer that changed reporting currency, whose older guidance years would be in
  the old one.
- **The check is a LABEL check.** It proves what the export says, not that the figures are in it.
  A mislabelled export passes, and the independent checks against EDGAR (revenue, OCF, EBITDA,
  leases) are what would catch that.
