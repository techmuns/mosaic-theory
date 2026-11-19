---
id:
status: open
date: 2026-11-20
prs: []
supersedes:
superseded-by:
---

# W81 (defect SP-D20): CIQ's two EBITDAs are named apart wherever either prints — "CIQ's annual LTM EBITDA" (the annual export's LTM column, which the page called "reported LTM EBITDA") and "CIQ's four-quarter EBITDA" (the quarterly export's four quarters) — and the LTM-quarters check names the cause of an EBITDA DIFFER where the annual Cash Flow's 'Other Amortization' reconciles it; IN CODE, no committed page moves; watch pages keep the old wording until rebuilt; preview APPROVED 2026-11-19 ("Approve with correction")

**WHAT.**
- **The defect (SP-D20, found by the archetype probe, main `6e03501f`, 2026-11-19, $0).** A page
  carries two CIQ EBITDAs, and they can differ.
  - MORN (a scratch page): the annual export's LTM column reads 719.4 (Financials_Annual sha256
    `fef17b2405`, Income Statement 'EBITDA', the LTM column to 2026-09-30). That is EBIT 616.7 plus
    the Cash Flow's 'Depreciation & Amort., Total' 102.7, leaving out its 'Other Amortization'
    102.7.
  - The quarterly export's four quarters sum to 822.1 (Financials_Quarterly `b23ba84d1d`), exactly
    719.4 + 102.7.
  - The filings rebuild 848.9: `OperatingIncomeLoss` 643.5 + `DepreciationDepletionAndAmortization`
    205.4 (10-K 0001289419-26-000013; 10-Qs -000025, -000041, -000054).
  - The page called the annual figure "reported LTM EBITDA", which reads as the filed figure.
  - The LTM-quarters check flagged the 12.49% gap with no cause.
  - No value was wrong: each consumer divides on its own basis. The words were.
- **The names.** `ev_ebitda_basis.ANNUAL_LTM` = "CIQ's annual LTM EBITDA" and
  `ev_ebitda_basis.FOUR_QUARTER` = "CIQ's four-quarter EBITDA", each held once. "After rent"
  appears only as a qualifier, where the rent contrast is drawn ("It is NOT a multiple of CIQ's
  annual LTM EBITDA, after rent ($8,903M, …)").
- **Where each prints:**
  - **CIQ's annual LTM EBITDA:**
    - the basis line ("What CIQ's EV/EBITDA divides"), every reading;
    - the lease line's margin ("against 14.3% on CIQ's annual LTM EBITDA");
    - `_multiple_basis_md`'s restatement;
    - the three `anchor_split` refusal reasons.
  - **CIQ's four-quarter EBITDA:**
    - the ex-lease band's denominator in the lease line;
    - the at-price line ("÷ CIQ's four-quarter EBITDA $8,903M (to 2026-08-01)");
    - the EBITDA reconciliation caveat ("CIQ's four-quarter EBITDA $7,518M against …", where it
      read "its LTM").
  - **R1's own earnings are neither figure** (its mid-cycle EBITDA, EBIT + D&A from the filings).
    So the lease line describes them instead of naming one: "R1's earnings are its mid-cycle
    EBITDA (EBIT + D&A), after rent; on that basis — TEV less operating leases over CIQ's
    four-quarter EBITDA — the median is …".
    - This one sentence corrects the wording B relayed with the approval ("R1's earnings are CIQ's
      four-quarter EBITDA"), which would have stated a false fact. B accepted the correction.
- **What keeps its name:**
  - The stored keys (`reported_ltm_ebitda`, the reading `"reported"`, `REPORTED_READINGS`).
  - The anchor's never-printed `multiple.source` identity string.
  - The basis block's `source_ref`. It is a citation key: NCNO's and TJX's kept syntheses cite it
    verbatim in 7 figure source_refs, and the figure tracer matches a cite by exact key.
  - `schemas.py` docstrings (protected, never printed).
- **The renderer's words follow the page's vintage** (B's ruling, 2026-11-19: watch pages stay as
  committed).
  - `render.names_ebitdas_apart(d)` is `extraction_version.includes()` of the page's assembly stamp,
    or any refresh stamp, against vintage `2026-11-19.ciq-two-ebitdas-named-apart-and-the-ltm-cause`.
  - A page at that vintage prints the new names on the lines the renderer words (the lease line,
    `_multiple_basis_md`).
  - An older page prints its old sentences verbatim, as its stored basis line does, so no page
    calls one figure by two names.
  - **Watch pages keep the old wording until rebuilt.**
- **The cause** (`ltm_quarters._ebitda_cause`, the EBITDA row's DIFFER only). It is named only when
  all five hold on the name's own sheets:
  1. CIQ's annual LTM EBITDA is its EBIT plus 'Depreciation & Amort., Total', to 0.5 $M. This is an
     identity of CIQ's construction: it held to the cent on IT, MCK, WLK, CNXC and NCNO and within
     0.04 on VITL.
  2. The Cash Flow's LTM column carries a positive 'Other Amortization'.
  3. The quarters are the higher figure.
  4. The annual figure plus that row agrees with the quarters by the check's own test (2%, or
     0.5 $M).
  5. The row closes more of the gap than it leaves.

  The flag states the row, its 1-based position, the reconciled figure, the remainder in $M and as
  a share, and the annual export's sha256. Elsewhere it says "Its cause was not read:" and why. It
  claims no quarterly mechanism, because the mechanism differs: on MCK every quarter is EBIT + D&A
  and the gap sits in EBIT; on IT it sits in a fiscal fourth quarter whose EBITDA adds the row back.
- **The $0 refresh step** (`refresh.refreshed_ltm_flags` / `ltm_quarters_transform`, with
  `qa_flags` admitted to the top-level seam for this one use). It re-runs the check on the page's
  OWN recorded Financials exports. It refuses:
  - an export whose sha256 is not the recorded one;
  - a page recording none;
  - a re-run that moves anything but the cause.

**WHY.** The operator approved the preview on 2026-11-19 ("Approve with correction", answering B's
"Approve W81's preview with the two-figure naming correction?"). The correction was to name each
figure distinctly everywhere it prints, because the preview's "EBITDA after rent" named both. B's
five decisions followed:
1. No "(pre-rent)": it reads as EBITDAR.
2. The R1 sentence is relabelled.
3. The cause is named at the check's own 2%, stating the remainder.
4. NCNO and TJX are refreshed anyway. Their kept bear points say "reported" about the same figure,
   an imprecise word, not a contradicting claim, and the next paid rebuild regenerates the prose.
5. The $0 transform is added.

B then ruled the vintage keying, over re-rendering all 17 lease-line pages (the #1100 precedent).
The re-render would have left 8 watch pages calling one figure by two names: the new lease line
beside a stored "reported" basis line.

**HOW VERIFIED.**
- **Measured first** (main `6e03501f`, the 26 committed pages):
  - "reported LTM EBITDA" sat in 21 page JSONs: the 20 with `ev_ebitda_basis`, plus SMPL.
  - The basis line is printed on 13 pages and JSON-only on 7.
  - The lease line's "reported" margin prints on 16 pages.
- **Pins:** `tests/test_w81_two_ebitdas.py`, 103 tests. 89 of the 99 present at the fail-first run
  failed on base `bc1c0e16`; the ten that pass there are population and control checks. The 100th
  (the zero-row reason pin) was added after it, for the one live mutant, and the three coherence
  pins below after review round 0. The pins:
  - every committed basis page's line, rebuilt by the head code, names the annual figure with its
    stored value, never "reported", and differs from the committed line by W81's words alone (18
    pages; the 2 pre-W65 pages, AMZN and GOOGL, are named and set apart);
  - the reconciliation's own sentence builder on the 16 committed reconciliations;
  - the at-price line on TJX and PARR (frozen companyfacts);
  - every old-vintage committed lease page renders byte for byte as committed;
  - each lease page stamped at W81 moves only its lease line, plus the lines printing the vintage;
  - the cause on frozen cells of IT, MCK, VITL and WLK's own exports (`tests/fixtures/
    ciq_ltm_ebitda_cause.json`, row positions kept). On all four, the fixture reproduces the real
    workbooks' flags exactly;
  - three single-cell mutations of MCK's real cells;
  - the transform's acceptance on IT and VITL, and its three refusals.
- **Mutants:** 11 of 11 red. The first run left one live: a non-positive 'Other Amortization'
  reached the same verdict by a wrong stated reason, and a pin on the reason closed it.
- `tests/test_refresh_path.py::test_a_noop_refresh_is_byte_identical` stays green, untouched.
- **The coherence pin** (`test_every_w81_committed_page_is_coherent`; review round 0, B: an accepted
  risk with a cheap fix is not accepted). On every committed page at W81 or later, no code-owned
  line carries an old name: not the stored basis, at-price or reconciliation line, and not their
  rendered lines in `dossier.md` or its `frontend/dossiers` mirror.
  - **The path is LIVE, not latent.** Every writer that records a layer refresh stamps the current
    version whenever anything moves: `refresh_dossier` with any transform (price values, the EV gap,
    consensus…), `anchor-backfill`, `financials-backfill`, `caveat-reword`, `ciq-reread`,
    `driver-facts-pass` and `transcript-run-cut`. Only `valuation_bases_transform` rebuilds the three
    stored lines.
  - **Red** on TJX's committed page stamped at W81 with its stored lines left as built: it names all
    three stored lines and their three rendered lines.
  - **Green** on TJX's frozen page with the three lines rebuilt, on today's pages (all old-vintage,
    so exempt), and on the 9 active pages after the rehearsed refresh (MCK and WLK stay old and
    exempt).
  - The block's `source_ref` is exempt by design: it is a citation key the kept prose matches
    verbatim.
- **The $0 refresh, rehearsed on scratch copies** against each page's recorded exports (head
  code). All 9 active pages move (BRBR and GOOGL excluded; see the boundary), and none refuses.
  - No figure moves.
  - The rebuilt basis block also gains W65's three date fields as new keys.
  - md lines moved: EPAM 6, TJX 6, NCNO 5, SMPL 5, WERN 5, VITL 4, VRRM 3, IT 2, LLY 2. Each count
    includes the vintage stamp and refresh-log lines.
  - On the web, each moved caveat's text is the md line's sentence, collapsed and force-open.
  - IT's flag gains "The cause, read: …, 9.8 $M (0.65%) left"; VITL's gains "Its cause was not
    read: … 1.5 $M apart".
  - LLY's `valuation_basis.current_multiple.as_of` moves 2026-10-30 → 2026-11-02. That is W73's
    `_r1_current` reading the rebuilt block's `multiple_close`, not W81's change.
  - MCK and WLK (watch) would refuse: their other LTM flags predate the quoting of '-'.

**BOUNDARY.**
- **Pages:** the 26 committed `data/dossiers/*/dossier.json` at main `6e03501f` (the measurement)
  and `bc1c0e16` (the build, the pins and the rehearsal).
- **Active pages:** the coverage roster's 11 at `bc1c0e16`. BRBR is excluded (it waits for CIQ's
  FY2026 segments), and so is GOOGL (rebuilt under W73).
- **The cause measurement:** the 15 pages whose recorded Financials exports were found by sha256.
  - 9 predate the input record: AMZN, BRBR, BURL, FUBO, NKE, ORKA, PARR, ROST and TGT.
  - SMPL and V carry no annual LTM column.
  - Of the 15, five differ beyond 2% on EBITDA. IT and MCK are named; VITL, WLK and CNXC are not
    read. CNXC's committed page predates the check.
- **Shares:** IT's 0.65% divides by the larger of the two figures, the check's own convention; the
  preview's 0.66% divided by the quarters.
- **Rows:** 1-based. The probe's MORN rows were 0-based, so its row 80 is row 81 here.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **SP-D20 stays on the watch pages until each is rebuilt** (operator's standing rule; B,
  2026-11-19). Their lease line and stored basis line keep "reported", consistently. Falsifier: a
  watch page printing a new name beside an old one.
- **The two active pages with kept prose.** After the refresh, NCNO's and TJX's kept bear points
  still say "reported" about the figure the block now names. Accepted by B as imprecise, not
  contradicting, until the next paid rebuild.
- **A partial refresh after W81 can stamp the vintage without rebuilding the stored lines.** Such a
  page fails the coherence pin in CI, so it cannot ship two names for one figure; the writer must
  run `valuation_bases_transform` with it.
- **The $0 refresh of the active pages is its own PR, after this one merges.**
