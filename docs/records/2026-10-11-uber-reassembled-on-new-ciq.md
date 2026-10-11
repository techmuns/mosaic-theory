---
id:
status: shipped
date: 2026-10-11
prs: [705]
supersedes:
superseded-by:
---

# UBER re-assembled on a fresh CIQ export — the six-week-old snapshot is gone, the bridge reads the 10-Q column, the history gets its bands, and the covenant mislabel corrects

**WHAT.** UBER was re-assembled on main @78abb62e (`2026-10-09.3`), on CIQ exports the operator put in
the Drive folder on 2026-10-11 (14:53–14:55 IST).

**The CIQ sync, archived first:**
- **The set replaced:** the data copy's previous files (10, the 2026-08-05 snapshot) were copied to
  `data/manual/ciq-archive/replaced-2026-10-11/UBER/`, following the `replaced-2026-09-22`
  convention.
- **The new live set:** `data/manual/ciq/UBER` was made an exact mirror of Drive: 11 files, sha256
  equal on every one. Eight files were refreshed, one is new (the Credit Health Panel), and the two
  earnings-call transcripts are unchanged.
- **One file had to go, not just be overwritten.** The old comps export was named
  "…Uber Technologies Inc .xls" (with a space), the new one "…Inc.xls". `CiqBundle.workbook()`
  takes the FIRST file of a kind, and the old name sorts first, so a plain copy would have assembled
  on the August comps. The old file was moved out of the live folder; its copy is in the archive.

**The new exports, read before use:**
- **Estimates:** ≥2026-10-08.
- **Financials:** the latest close is 2026-10-09 and numeric, history runs through 2026-09-30, and
  nothing is withheld.
- **Comps:** 2026-10-11.
- **The latest balance sheet** is still Q2 (2026-06-30); Uber reports Q3 around early November
  (not announced; trackers say 11-02 or 11-03).

**Prices:** UBER was refreshed 2026-10-07 → 10-09 by per-symbol aggregates (3 bars); the
benchmarks were already current. The close is $71.51 on 2026-10-09; the page had $70.97 on
2026-09-16.

**Only artifacts changed:** UBER's page and its mirror, `frontend/dossiers/index.json`, the UBER
price and companyfacts fixtures, and STATE rows 10, 27 and 28.

**WHY.** Operator instruction, 2026-10-11: "re-assemble UBER, new files added". UBER's page priced on
an 08-05 CIQ snapshot 42 days before its own price (#702's snapshot field), and §5.0 row 28 listed it
among the names blocked on a CIQ re-export.

**WHAT MOVED** (against main's page):

    extraction stamp      2026-08-16.1 (+refreshes)  ->  2026-10-09.3 (assembled)
    reference_date        2026-08-24  ->  2026-09-22 (the fleet's current reference; moves the windows anchored to it)
    price                 $70.97 (2026-09-16)  ->  $71.51 (2026-10-09)
    CIQ snapshot          market cap $139,262M @ 2026-08-05  ->  $146,064M @ 2026-10-09 (0 days before the price)
    NTM TEV/EBIT          15.43x  ->  15.59x (struck at the page's own snapshot; reconciles)
    bridge (claims)       $10,423M  ->  $5,827M (same 2026-06-30 balance sheet; see below)
    forward history       every band withheld  ->  4 bands (EV/NTM EBIT 15.59x on 10-09 against 14 earlier closes)
    non-operating count   absent  ->  3 of the trailing 4
    draws                 —  ->  strongly-bullish 3 / mixed 2, proposal withheld
    caveats / qa          7 / 2  ->  6 / 4

**THE BRIDGE FELL $4.6BN AT THE SAME BALANCE SHEET — CIQ'S OWN RECLASSIFICATION, VERIFIED.**
- **The 08-05 export** read Q2 from CIQ's PRESS-RELEASE balance-sheet column: Net Debt $9,340M (debt
  $14,731M − cash & ST investments $5,391M) + minority interest $1,083M = $10,423M.
- **The 10-11 export** reads the 10-Q column for the same quarter, which discloses **$4,596M of
  long-term marketable securities** that CIQ nets: Net Debt $4,744M + $1,083M = **$5,827M**.
- **It is on the multiple's own basis:** that figure equals CIQ's TEV less market cap exactly, and
  the 15.59x NTM TEV/EBIT is struck on the same TEV.
- **EDGAR's cross-check is unchanged** at $7,565M (EDGAR's read does not net long-term securities).
- **All three exit years are held at $5,827M** (HOLD_CURRENT_SAME_BASIS). The consensus net-debt line
  still fails its basis test.
- **At the point-in-time count** (2,042.6M shares) the bridge move is about **$2.25 a share** on any
  R4 leg.

**THE COVENANT MISLABEL CORRECTS (§5.0 row 28's UBER item).**
- **Main's digest** led with "[2025 Convertible Notes · 0001552781-23-000469 …]", whose own text said
  it was "a capped call confirmation, not the convertible note itself".
- **The new digest** leads with "[TERM LOAN AGREEMENT · 0001552781-21-000058 · amended by
  0001552781-23-000080, 0001552781-23-000109]". That is #652's document-identity fix, which needed a
  fresh panel.
- **The capped-call exhibit** is refused, with the QA flag "(E5) not a debt agreement".
- **Row 30's "panel a quarter behind its balance sheet" still holds:** the capital-structure detail
  is still the FY2025 10-K, filed 2026-02-13.

**⚠ THE OPERATOR'S RE-TAG REASON WAS REPLACED.** The machine's own read proposes R4 (all three
conditions hold: NTM TEV/EBIT 15.6x; R1 declines and the EBITDA basis is divergent at 4.08×; the
P/E is GAAP-struck with 3 of 4 quarters material).
- **So the recipe is unchanged,** and the keep-recipe step wrote the machine's reason over "OPERATOR
  RE-TAG 2026-10-09. R2_NEEDED -> R4 …".
- **This is AMZN's case on #700,** which the operator had restored by hand (#701). The provenance
  decision is open in STATE row 10, and nothing was hand-edited here.

**Redrawn by the LLM-fenced phases:**
- **The synthesis:** 10 bull / 7 bear → 9 / 5, still strongly-bullish.
- **#678's GAAP-EPS check fired on a BEAR point:** over 12 months, FY26 GAAP EPS consensus moved −10%
  while normalized moved −22%.
- **Two QA flags were added:** an uncited decisive-against, and the refused exhibit above.
- **The covenant digest and the operating-driver rows** were rewritten.

**TWO OPERATOR RULINGS THIS PASS NEEDED (2026-10-11).**

1. **AN UNCITED DECISIVE POINT — DISCLOSED, NOT RE-ROLLED.** The new synthesis's decisive
   evidence_against[1] (the FY26 EPS cuts) carries a `source_ref` that is a peer-heterogeneity note,
   not a source.
   - The assembler had already marked the point `cited: false` and flagged it UNCITED.
   - The citation-integrity pin (`test_multiples_vintage`, since #460) refused ANY untraceable
     reference, while its own docstring guards a point still reading as source-verified.
   - Since 2026-08-17 no committed page had carried such a point.
   - **Ruled:** narrow the pin to that invariant. An untraceable reference passes only when DISCLOSED
     (`cited: false` and the UNCITED flag quoting the claim), the 2026-08-07 precedent ("the flags
     stay on the page for the human"). A `cited: true` point that resolves to nothing fails as
     before.
   - **The rule is pinned both ways** on UBER's real point: disclosed passes; claimed or unflagged
     fails. Three mutants on it, all killed.
2. **A NEW MONITOR DAY, NOT A RE-CUT.** `test_panel_emit` requires the latest monitor day's panels to
   equal what today's pages emit, and UBER's page moved two of its panels.
   - **#657 had re-cut the dated day.** Doing that here would have written later information into a
     record dated 2026-09-22: IT's 2026-10-08 8-K, WERN's 2026-10-06 and 10-08 8-Ks, and UBER's
     10-09 multiple. The monitor's "newer filings" are not bounded by `--ref`.
   - **Ruled:** mark the book on a new day. The book's prices (GOOGL, IT, SMPL, VRRM) were refreshed
     2026-10-07 → 10-09 (12 bars), then `vinci monitor --ref 2026-10-09` was run and mirrored.
   - **The new day:** 5 rows and 124 panels, with no filing or evidence dated after 2026-10-09 (the
     latest filing is 10-08). BUY−AVOID spread +44.70 pp, diagnostic, with no row at horizon.
   - **2026-09-22 is unchanged.**

**THE TEST-ONLY COMMIT** (four pins, each keeping its invariant):
- **The cap-drift pin** named UBER's own drift, and UBER now reconciles. It is now MEASURED over every
  drifting page (15 of 26), like its sibling.
- **The R4-proposal pin's R1 stand-in** kept the page's reason, which is now the machine's own text.
  It now carries R1's own (CONSTRUCTED) reason.
- **The valuation-basis test lost my own value pin** (UBER's snapshot over 30 days old), a value pin on
  a living artifact, which the test-layer rule forbids.
- **The citation pin** was narrowed as ruled.

**Three tests now SKIP that ran before, each by design:**
- `test_ev_bridge` and `test_pe_eps_basis` pin the extractor against FROZEN exports by hash, and
  UBER's on-disk export is now a different file. The frozen cases stand; the other names' cases still
  run.
- `test_latest_col_provenance` skips because its premise cleared: UBER's new export no longer lands
  on a non-period column.

**HOW VERIFIED.**
- **The sync:** sha256 equal on 11 of 11 files between Drive and the live folder, and the archive
  holds the replaced set (10 files, the old-named comps among them).
- **The new exports were read in place before the sync** (dates above).
- **Prices:** `vinci refresh UBER --start 2026-10-07 --end 2026-10-09 --aggs` wrote 3 bars.
- **Assembly:** `dossier --ticker UBER` exited 0 with `1 done · 0 error(s)`, 2026-10-11
  14:58–15:06 IST.
- **The page was diffed against main's key by key.** The bridge was traced line by line across both
  exports, and the covenant digests were compared.
- **Mirror:** byte-identical to the page.
- **Fixtures:**
  - UBER prices: +3 bars.
  - The companyfacts fixture moved one line, SEC's `entityName` capitalisation ("UBER
    TECHNOLOGIES, INC." → "Uber Technologies, Inc").
- **Suite:** `pytest -m "not network"` on the freshly-committed artifacts. Counts are in the PR. The first run failed 5 (four pins above, and the panel-emit check that the new monitor day answers).

**BOUNDARY.**
- **Scope:** one page, UBER, 2026-10-11.
- **Prices:** through the 2026-10-09 close.
- **CIQ:** the 2026-10-11 exports.
- **Draw counts:** five draws, one build.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A latent loader hazard, reported and not fixed here.** `CiqBundle.workbook()` silently takes the
  first file when a folder holds two exports of one kind. This sync avoided it by moving the old
  file out. A re-export that leaves an old file under a different name would assemble on the wrong
  one with nothing said.
- **The operator's re-tag reason is replaced** (above; STATE row 10).
- **The monitor's lookahead, reported and not fixed here.** A day re-run with `--ref` takes "newer
  filings" up to TODAY, not up to its date.
  - The panel-emit pin forces a re-run whenever a page moves.
  - So any re-cut of a past day can write later information into it, as #657's may have done on
    2026-09-29.
  - Avoided here by writing a new day.
- **Uber's Q3 report (around 11-02) will stale this page.**
