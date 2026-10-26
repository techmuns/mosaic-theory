---
id: 2026-10-26-artifact-pass-17-pages
status: open
date: 2026-10-26
prs: []
supersedes:
superseded-by:
---

# Seventeen pages re-assembled on the 2026-10-23 close: the stale self-funding reads and benchmark closes are gone, the first run records land, and ten pages wait on CIQ exports after their next filings

**WHAT.** One paid artifact pass, assembled on main `121c29be` (which includes #806–#809) and landed on `d7564c69` (+#810). It covers the
17 committed pages whose CIQ comps were inside the 45-day freshness ceiling once the operator
re-exported AORT, CNXC and ORKA on 2026-10-26:

AORT, CNXC, ORKA, V, PARR, WLK, BRBR, GOOGL, LLY, NKE, BURL, ROST, TGT, AMZN, NFLX, UBER, TJX.

What it closes and moves:
- **STATE.md §5.0 row 32 item (17) closes.** The self-funding line now reads the latest quarter
  (#806):
  - PARR, WLK, BRBR and CNXC go from MIXED to YES;
  - AORT's latest-quarter cash flow turns negative (it stays MIXED).
  
  On the CIQ scorecard's FCF-sign check, those five go from differs-unexplained to confirmed. The
  fleet reads 25 confirmed and 2 unexplained, against 20 and 7.
- **Row 32 item (7) closes.** NKE, ROST, TGT (SPY) and ORKA, PARR, WLK (MDY) measure their 52-week
  benchmark leg to the reference date, 2026-10-16, on fresh closes. On main they ended at 2026-09-22,
  on a close the store had stopped updating.
- **Row 32 item (3) closes.** Every page it names now prices at the 2026-10-23 close.
- **Row 32 item (12) shrinks to MCK.** V is re-assembled on its 2026-10-12 export.
- **#804's quote check reaches 12 of the pages.** 39 covenant-term values are withheld, each
  UNKNOWN with its `(E5) refused` note: CNXC 4, AORT 3, V 1, PARR 2, WLK 5, NKE 3, BURL 2, TGT 3,
  AMZN 7, NFLX 2, UBER 4, TJX 3. #804's record said the next re-assembly would do this.
- **The first run records.** `data/snapshots/assembly_runs/` gets 19 files: one per `vinci dossier`
  run, refused attempts and the re-run of V included. This starts the Stage 0 series.
- **A monitor day at the 2026-10-23 close** (`data/monitor/2026-10-23.json`). It is the first day on
  total return (operator ruling B), as RUNBOOKS §j requires once pages move under the panel-emit pin.
- **Test artifacts that must move with the pages.** (#809 and #810 first moved the pins that read
  values a re-assembly redraws, so these are the only test edits here.)
  - NFLX's companyfacts fixture is regenerated: its page reads the new September-quarter 10-Q. The
    other 16 fixtures regenerate byte-identical.
  - `test_staleness_split` admits BRBR, on the same measured mechanism as AORT and TECX before it.
    Its merged age is 61 days, all of it consensus panels from the 2026-08-26 Estimates export; its
    export age is 35 days, inside the ceiling.
  - `test_one_snapshot_holds_one_basis` also requires the 2026-10-23 day to be present and on
    total return. This is #810's review finding, deferred to the PR that commits that day.

**WHY.** The pages carried figures their own fixes had made wrong (#806's self-funding read, the
stale benchmark close), and 14 of the 27 pages sat past the 45-day ceiling on CIQ comps age.

The operator re-exported three names now and deferred ten until after their next filings. A full
export after a filing carries the new quarter, so exporting those ten now would mean doing it twice
within weeks. With AORT, CNXC and ORKA re-exported and V's export already fresh, 17 pages could be
re-assembled.

**HOW VERIFIED.**
- **Inputs, before any paid run:**
  - **CIQ:** Drive and the assembler's copy compared by sha256 across all 35 folders. Only AORT,
    CNXC and ORKA differed. They were archived to `ciq-archive/replaced-2026-10-26/` and mirrored.
    AORT's Drive folder held two comps exports (the old `…Artivion Inc .xls` beside the new one),
    which the loader refuses. The old one was left out of the mirror, and the operator then removed
    it from Drive. All 35 folders match afterwards.
  - **Prices:** the store topped up to 2026-10-23 for the 17 names, SPY, MDY and IWM (300 bars),
    then for VRRM, IT and SMPL ahead of the monitor day (45 bars).
  - **The claim:** `artifacts/fleet-17-reassemble-2026-10-26` pushed before any work. No open PR
    touched `data/dossiers/`.
- **Every page compared with main.** Operator decisions and scenario records are untouched.
  - **Anchors:** unchanged except GOOGL, ORKA, NFLX, CNXC and V.
  - **NFLX:** its September-quarter 10-Q moved net debt from $5,181M to $6,909M and the base value
    from $53.21 to $53.54.
  - **CNXC:** the re-export moved its base from $93.11 to $84.80.
  - **V:** the share-count refusal is still in place.
  - **GOOGL and ORKA:** see below.
- **CNXC was refused once.** Its synthesis omitted the $2,573.3M LTM goodwill impairment the new
  export shows, and the material-figure guard refused the page. The re-run named it and was written.
  Both runs are in the run records.
- **#808 moves 0 of the 17.** The old and new latest-quarter readers give identical reads on each
  page, as filed by its assembly date.
- **Suite, with the shared CIQ copy and store linked** (final tree, 2026-10-27): 7,309 passed, 3
  failed. All 3 fail identically on main `7213d486` with the same links:
  - MCK's capital panel (row 32 item 12);
  - store freshness: the store's top-up leaves these names newer than the rest, a state CI never
    has;
  - the EV-bridge check on AORT. It compares two of AORT's own CIQ exports: today's comps (TEV less
    cap, $330.7M) against the 2026-07-20 Financials bridge ($202.4M). Only the comps were
    re-exported, and AORT's full post-filing export fixes it. This is also the scorecard's one new
    unexplained EV-bridge difference.
  
  In a CI-like tree with nothing linked, `bin/commit` ran the full offline suite green.

**FOUND, NOT FIXED.**
- **A refused newer covenant term lets an OLDER exhibit govern, unsaid — now on 3 pages, 0 on
  main.** `covenant_extract.governing_terms` (and its JS mirror) take the latest PRESENT row, so when
  #804 refuses a newer exhibit's quote the older value governs, and nothing says the newer exhibit
  stated the term. #804 recorded this as a follow-up, a render change under the preview rule. This
  pass made it live:
  - NKE's credit agreement interest rate governs from 0000320187-23-000006 (2023-03-13) over a
    refused 0000320187-24-000009 (2024-03-11);
  - BURL's from 0001193125-21-364998 (2021-12-22) over a refused 0001193125-25-168007 (2025-07-29);
  - NFLX's financial-maintenance covenants from 0001193125-19-094705 (2019-04-01) over a refused
    0001193125-21-193187 (2021-06-17).
  
  Counted by re-running `governing_terms` on each page's own term and pointer rows, on main and on
  the pass.
- **A fresh assembly drops CIQ-bridged anchor inputs.**
  - `assemble.py` calls `compute_anchor` with no `ciq=`, so an input EDGAR does not tag is filled
    from the CIQ workbook only by `vinci anchor-backfill`, which passes it (`cli.py`).
  - On this pass, GOOGL's D&A went to UNKNOWN and its anchor became inapplicable, and ORKA lost its
    net debt.
  - `anchor-backfill --tickers GOOGL,ORKA` restored both, equal to main apart from `computed_at`.
    Your R3 forward-P/E decision on GOOGL stands.
  - Until assembly passes the bridge, every pass must backfill the vendor-bridged names. Those are
    the pages whose anchor reads `vendor_bridge` on main.
- **SEC's companyfacts API carries no facts from V's 10-Q of 2026-07-29.** That counts every
  concept, not only cash flow. So V's latest-quarter read is the quarter to 2026-03-31, the newest
  EDGAR serves. This is upstream, not an alias gap.
- **GOOGL's and NKE's comps exports are still dated 2026-09-21.** Their market-cap date stays there,
  35 days old at 2026-10-26.

**BOUNDARY.**
- **Pages:** the 17 above, at main `121c29be` against the re-assembled files.
- **Comps ages:** each page's `date_semantics.tev_as_of` against 2026-10-26.
- **Cost:** 19 runs, 166 calls, 0 failed, **$69.75** (the sum of the records' `usd`; the per-run figures below are rounded), model `claude-opus-4-8`. Read from the
  committed run records.
  - The first 17 runs cost $61.91.
  - The CNXC re-run cost $5.13 and V's re-run $2.72.
  - The refused CNXC attempt ($5.16) is inside the $61.91.
- **Draw tallies:** one build each, five draws. A tally, never a rate. TJX completed 4 of its 5 draws.
- **Scorecard:** `data/snapshots/data_quality/ciq/2026-10-26.json` is rewritten over the final page
  set. The prices scorecard is not rewritten. It reads whichever store is linked, and the assembler's
  store covers 2,265 names against the committed snapshot's 2,797, so rewriting it would shrink its
  population.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$69.75** in LLM calls.
- **39 covenant values withheld** that were most likely read correctly. #804 accepted that, with
  its own falsifier.
- **Ten pages stay refused at the ceiling** until the operator's post-filing exports: NCNO, VRRM,
  IT, VITL, EPAM, FUBO, SMPL, MVST, WERN, TECX. VRRM's ledger outcome on 2026-12-14 is scored from
  prices, not from its page.
