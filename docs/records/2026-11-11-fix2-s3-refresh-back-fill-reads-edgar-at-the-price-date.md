---
status: shipped
date: 2026-11-11
prs: [1014]
supersedes:
superseded-by:
---

# The refresh back-fill reads EDGAR as filed by the page's price date: the lease basis, the three valuation bases and the statement reconciliation are cut where assembly cuts them

**WHAT.** Three back-fill paths in `vinci/dossier/refresh.py` read EDGAR companyfacts past the
page's price date. They were the "OPEN — NOT THIS PR" item of
`docs/records/2026-11-02-inputs-are-cut-at-the-pages-price-date.md` (#884), handed to stream S3 on
2026-11-11 (issue #1004: "Refresh paths that skip the price-date cut").
- **`lease_basis_transform`** handed `lease_basis` today's companyfacts, uncut.
- **`valuation_bases_transform`** handed `with_valuation_bases` today's companyfacts, uncut. That
  builder is shared with assembly, which hands it facts cut at the price date.
- **`statement_recon_transform`** read the facts as filed by the page's assembly date, which comes
  1 to 4 days after its price date on every committed page.

Now each reads EDGAR as assembly reads it: companyfacts pruned at the page's price date
(`edgar.concepts.facts_as_of`, the cut `AsOfEdgar.companyfacts` makes). The rules:
- The first two take the price date from `stock_info.as_of` (`anchor.price_as_of`). A page with
  none gets no block, the rule `capital_allocation_transform` already follows in the same file.
- The reconciliation uses `asof.page_price_date`, so with no stored close it cuts at the
  reference date. A page stating neither date is refused (`RefreshRefusedError`), never read
  uncut.
- The reconciliation's `filed_by` is still the assembly date. Assembly passes its own build date,
  so the block's `as_filed_by` reads as assembly writes it, and a page's existing block still
  reproduces.

**WHY.** Operator ruling C4 (2026-11-01, verbatim): "Inputs are cut at the page's price date (filed
on or before it; latest such filing wins; nothing after a sealed verdict)." Assembly has applied it
since #884. A back-fill that refreshes a block "under a KEPT synthesis" reads the same EDGAR, so
without the cut it states a page's lease reconciliation or EBITDA reconciliation from a 10-Q filed
after the price the page divides by. That 10-Q can also restate the comparative quarters the
reconciliation reads. `lease_basis` and `ebitda_recon.reconcile` bound nothing themselves; they
read whatever facts they are handed. `ev_ebitda_basis.ex_lease_at_price` already cuts its own
EDGAR legs at the page's close (#885): on NCNO's page it gives 30.47x on both the cut and the
uncut facts.

**HOW VERIFIED.**
- **Fail first, on real data:** `tests/test_refresh_price_date_cut.py`, 8 tests. On main
  `2637e91b`, 5 fail and 3 pass (two premise pins and the negative pin). On this branch, all 8
  pass.
  - NCNO's committed page is priced 2026-08-17. Its committed companyfacts
    (`tests/fixtures/companyfacts/NCNO.json`) carry its 10-Q filed 2026-08-25, which holds 481
    facts. On main, `lease_basis` and `with_valuation_bases` were each handed facts whose newest
    filing is 2026-08-25. Now the newest is on or before 2026-08-17, and every filing up to it is
    still there (the negative half).
  - The reconciliation uses TJX's frozen companyfacts, where the Q2 FY27 10-Q is filed
    2026-08-28. On a page priced 2026-08-27 and assembled 2026-10-21, main put 62,363 in the LTM
    row's filing column. Now that column is empty, and `as_filed_by` still reads 2026-10-21.
    Priced on 2026-08-28, the filing is read: the cut is inclusive, as `asof.within_cut` is.
- **Existing pins kept:**
  - `tests/test_statement_recon.py::test_every_committed_page_carries_the_block_and_it_reproduces_from_the_filings`
    passes on all 27 committed pages. Every page's block still reproduces from its committed
    companyfacts, because no committed fixture holds a filing between a page's price date and its
    assembly date (NCNO's 10-Q is after both).
  - The old test helper `_tjx_doc` stated neither a price date nor a reference date. It now
    carries the reference date 2026-10-16, as every committed page does. No other test changed.
- **The live corpus, $0 and offline.**
  - Base: main `2637e91b`. Head: this branch's code.
  - The three transforms ran on all 27 committed pages, served with the newest cached
    companyfacts and SEC documents across this machine's 18 worktree caches and the primary's.
    These are read-only and no request is sent. The CIQ exports are the primary checkout's.
  - Result: **0 leaves move on 0 of 27 pages**, in the lease basis, the three valuation-basis
    blocks, the statement reconciliation and its refusals.
  - Why nothing moves: 23 of the 27 on-disk quarterly exports are the pages' own (their bands'
    stamp), and none of those 23 pages' newest cached copies holds a filing after its price date.
    Two copies do:
    - MVST's holds a DEF 14A filed 2026-10-09, whose pay-versus-performance facts none of these
      blocks read.
    - NCNO's holds the 2026-08-25 10-Q, but NCNO's export on disk is not its page's (`a4ee9ab066`
      against the bands' `4279cbed71`), so the back-fill leaves NCNO's blocks alone at both refs.
  - So the defect is latent today. It bites on the first back-fill run with a copy fetched after
    a page's price date. On every page priced 2026-10-23 (BRBR, BURL, ORKA, PARR, TGT), any 10-Q
    filed since would have been read.

**BOUNDARY.**
- "481 facts": NCNO's committed companyfacts fixture, every taxonomy and unit, rows whose `filed`
  is after 2026-08-17. All are 2026-08-25, accession 0001902733-26-000101.
- "1 to 4 days": `assembled_at` minus `stock_info.as_of` on the 27 committed pages at `2637e91b`.
  The range is 1 (most pages) to 4 (TECX: 2026-11-06 to 2026-11-10).
- "0 leaves on 0 of 27": every leaf of the transforms' output blocks, compared between base and
  head. Inputs: for each page, the newest-`fetched_at` copy of each URL across
  `.claude/worktrees/*/data/cache/sec` and the primary's `data/cache/sec`, read 2026-11-11, and
  the primary's `data/manual/ciq`.
- "23 of the 27": the quarterly Financials export that `CiqBundle.from_files` picks from the
  primary's `data/manual/ciq/<T>`, whose `file_provenance` sha equals the page's single
  own-history stamp. The 4 that don't match are FUBO, ORKA and TECX (no stamp on the page) and
  NCNO (a different file).

**FOUND, NOT FIXED** (outside the three paths named; reported, not built).
- **`cross_check_transform`** also reads the latest-quarter OCF sign as filed by the page's
  assembly date. That is deliberate: it re-runs assembly's composition, and every outcome is
  written only behind a byte-for-byte reproduction of the stored line. For a page assembled
  before #884, the assembly date is the cut that page's assembly used. For one assembled since,
  it is not, and such a page's line may fail to reproduce and its outcome be left absent and
  named. That is a loud refusal, never a wrong value. Changing it means choosing the cut by the
  page's vintage.
- **Assembly's statement reconciliation states `as_filed_by` = its build date** while the facts
  it reads are already cut at the price date (`mechanical.py`, `statement_recon.attach(...,
  filed_by=datetime.now(UTC).date())`). The block's own date therefore says a day or more later
  than the cut it was read at. This is `mechanical.py`, which is in flight on
  `claude/fixreq2-e2-remainder`. The back-fill matches assembly here, so the two cannot disagree.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A page with no stored close gets no lease-basis or valuation-basis back-fill.** The two
  transforms receive the mechanical layer only, which carries no reference date. All 27 committed
  pages state a close, so none is affected. Falsifier: a committed page whose `stock_info.as_of`
  is null.
- **No committed page moves and no page is re-rendered.** The next back-fill pass after a fresh
  companyfacts fetch is where the change shows.
