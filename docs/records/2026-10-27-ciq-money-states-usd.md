---
id:
status: shipped
date: 2026-10-27
prs: [819]
supersedes:
superseded-by:
---

# A CIQ export's money must STATE USD: each money panel's stated currency is read, a stated other currency is refused before assembly, and the scorecard scores it; the anchor stores the band guards' outcomes, and the checks still unchecked are measured

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
  - A page whose stamped Financials or Estimates export is no longer in the folder is refused,
    so no block is built from what remains (Codex, #819 round 1).

**Item 10: checks that give no structured outcome, re-measured.**

- **The two band guards store their outcome on the anchor** (`anchor.band_checks`). Each guard
  sets a flag only when it trips, so a pass and a guard that never ran read the same.
  - `band_guards.recorded_d_and_a_outcome` / `reconciliation_outcome` give agree / differ /
    not_run from the flag's own gate (`_d_and_a_runs`, now shared by the check).
  - **`anchor.py`, additive only** (its own commit, agreed with the wave's coordinator so L2 can
    rebase around it): one optional field, one kwarg in `compute_anchor`'s R1 return, one entry in
    `anchor_absent_fields`. An anchor that returns before the guards (no own-history multiple, R2,
    R4) carries no block.
  - **Back-fill** (`refresh.band_checks_backfill`): no workbook and no EDGAR. Each guard re-runs on
    the page's stored inputs, and the outcome is written only where three things reproduce: the
    re-selected band is the one the anchor priced, the ex-lease line sits exactly on ex-lease
    pages, and the re-run's trip lines equal the page's.
  - **Scored:** `recorded_d_and_a_vs_edgar` (independent: EDGAR's D&A) and
    `market_reconciliation` (internal: CIQ on both sides, with EDGAR legs). The TEV-history
    family's UNSCORED entry for `anchor.data_quality` is gone.

| guard (21 anchors reach it) | agree | differ | not run | the not-runs |
|---|--:|--:|--:|---|
| recorded D&A vs the sheet's implied D&A | 6 | 1 (VITL) | 14 | the ex-lease history carries no implied D&A margin |
| market reconciliation | 20 | 1 (VITL) | 0 | — |

  Six anchors never reach the guards and carry no block: FUBO, ORKA and TECX (no own-history
  multiple), MVST and NCNO (R2), UBER (R4). Before this build, a page with no recorded-D&A flag had
  passed on 6 pages and never run on 20, and could not say which.
- **`ciq_balance`'s scale check still stores no outcome: STOPPED.** It runs only in
  `cli._machine_anchor` on the raw workbooks, and its natural home is wherever assembly keeps the
  CIQ bridge — L2's lane this wave. Run on the real workbooks: 25 of the 27 page names pass, 2
  never run (ORKA and TECX carry no revenue to scale against), 0 fail. None of it reaches a page.
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
- **The band-check back-fill, for real:**
  - 21 of the 21 anchors that reach the guards reproduced and were written; 6 were named
    unreached; none was refused;
  - checked page by page against HEAD: each JSON gained only `anchor.band_checks` and one
    `layer_refreshes` record (layer `anchor`), each `dossier.md` its refresh line;
  - its counts equal the measurement taken before any code, re-running the producer's functions
    on the stored inputs.
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
- **The band-check pins** (`tests/test_band_checks.py`, 10 tests):
  - through `compute_anchor`'s synthetic facts: agree/agree on a coherent band; each guard that
    trips differs alone; a band with no implied D&A margin, or no market cap, reads not_run —
    never agree; an anchor that never reaches the guards writes no key;
  - every committed page without the block loads, serializes unchanged and renders (old JSON);
  - END TO END, every committed block is exactly what the back-fill rebuilds from its page;
  - each back-fill proof refuses on its own, each case asserted to exist on the corpus first.
- **Mutation:** 42 mutants of the new production code, each run in a scratch copy of the tree
  whose unmutated baseline passes, all killed:
  - currency: 13 in `ciq_sheets`, 3 in the assembly call site, 6 in the back-fill, 4 in the CIQ
    source's check;
  - core: 1 (the derived-class split restored, which three pins kill);
  - band checks: 5 in `band_guards`, 2 in `anchor.py`, 6 in the back-fill, 2 in the scorecard.
- **The scorecard, by the real command:** `vinci audit quality --source ciq --write` on the
  back-filled pages wrote `data/snapshots/data_quality/ciq/2026-10-27.json`.

**THE ANSWER, BEFORE → AFTER** (the CIQ scorecard over the 27 committed pages, one unit per page,
or per panel for the new check):

| | BEFORE | AFTER |
|---|---|---|
| measured at | 47d8ca27 (main), page-set sha256 `e6e09ad9…` | d65d4f50, inputs matching it, page-set sha256 `b660504a…` |
| checks | 15 | 18 |
| `currency_stated_usd` | — | 449 of 449 panels confirmed on 25 pages; FUBO, TECX not run |
| `recorded_d_and_a_vs_edgar` | — | 6 confirmed, 1 unexplained (VITL), 14 unchecked on 21 pages; 6 not run |
| `market_reconciliation` | — | 20 confirmed, 1 unexplained (VITL) on 21 pages; 6 not run |
| coverage, 25 families (ind / int / single / unchecked) | 8 / 4 / 10 / 3 | 9 / 6 / 9 / 1 |
| UNSCORED entries | 2 (the scale check, `anchor.data_quality`) | 1 (the scale check — item 10's STOPPED part) |

By failure class (independent / internal only / none, a second source exists / none,
single-source):

| class | BEFORE | AFTER |
|---|---|---|
| wrong file | 7 / 1 / 7 / 10 | 8 / 1 / 6 / 10 |
| wrong cell | 7 / 3 / 5 / 10 | 8 / 2 / 5 / 10 |
| wrong unit | 8 / 3 / 4 / 10 | 9 / 6 / 1 / 9 |
| wrong period | 7 / 3 / 5 / 10 | unchanged |
| different definition | 4 / 1 / 10 / 10 | 5 / 0 / 10 / 10 |

- **The TEV-history family** moves internal → independent, on the recorded-D&A check against
  EDGAR.
- **Three families move on the currency check alone**, and their notes say so: consensus
  (single-source → internal), segments and surprise (unchecked → internal). Nothing about their
  VALUES gained a second source.
- **Every other check's counts** are unchanged between the two points.

**BOUNDARY.**

- **Reader census and back-fill:** the assembler's workbook copy
  (`mosaic-theory-ta/data/manual/ciq`, read-only), read 2026-10-27. The census covers 35 folders,
  one unit per money panel the folder holds (18 possible). The back-fill covers the 27 committed
  pages at 6ec47e9c.
- **Item 10's guide and wall causes:** the 27 committed pages at 47d8ca27, one unit per page, read
  off each page's stored inputs (no EDGAR read).
- **Band guards:** the same 27 pages. Measured at 47d8ca27 by re-running the producer's
  functions on the stored inputs; back-filled at a2d2186f; scored at d65d4f50.
- **Scale check:** `ciq_balance.extract` on the 27 page names' folders in the assembler's copy,
  2026-10-27.
- **Mutation counts:** over the 42 listed mutants, against `tests/test_ciq_currency.py` (the
  currency 26), `tests/test_quality_core.py` + `tests/test_quality_ciq.py` (the core's one), and
  `tests/test_band_checks.py` + `tests/test_band_guards.py` (the band checks' 15).

**FOUND, NOT FIXED (out of scope; reported).**

- **The scale check's outcome** belongs wherever assembly keeps the CIQ bridge (L2's lane).
- **The six anchors that never reach the guards carry no block**, so the scorecard reads them as
  not run. It cannot tell "never reached" from "predates the field" off the page; its reason names
  both.
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
- **FUBO's and TECX's currency blocks stay absent** until each is re-assembled (assembly writes it
  from the workbook); the card counts them not run, never a pass.
- **A band-check outcome back-filled as `agree` is the guard's outcome on the page's CURRENT
  inputs.** The reproduction proves the priced band and every trip line, but a PASS leaves no line
  to compare. The guards are order-of-magnitude screens (8x and 2.5x), so an input drift since
  assembly that flips a pass would itself be a trip-sized change.
- **The reported-currency resolution trusts that a sheet's `Reported Currency` and the same
  export's Company Level sections mean one currency.** True by CIQ's own definition on every export
  read. Falsifier: a filer that changed reporting currency, whose older guidance years would be in
  the old one.
- **The check is a LABEL check.** It proves what the export says, not that the figures are in it.
  A mislabelled export passes, and the independent checks against EDGAR (revenue, OCF, EBITDA,
  leases) are what would catch that.
