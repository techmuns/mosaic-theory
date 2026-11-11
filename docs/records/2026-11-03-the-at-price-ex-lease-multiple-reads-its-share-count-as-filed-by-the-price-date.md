---
id: 2026-11-03-ex-lease-share-cut
status: shipped
date: 2026-11-03
prs: [888]
supersedes:
superseded-by:
---

# The at-price ex-lease multiple reads its share count as filed by the page's price date: one cut for the whole bridge, as the anchor's (audit E2-D21; operator ruling C4; after #885)

**WHAT.**
- `ev_ebitda_basis.ex_lease_at_price` (`valuation.ev_ebitda_ex_lease_at_price`) cuts the companyfacts
  blob ONCE at its entry, with `concepts.facts_as_of(facts, stock_info.as_of)`. Its share count
  (`anchor.share_denominator`) and its net debt then read the same filings.
  - The net-debt read passes `as_of=None`, because the facts arrive cut.
  - It is the move #885 made at `compute_anchor`'s entry.
- The date is the stored close's. That is `vinci.edgar.asof.page_price_date`'s answer whenever there
  is a close. With no close, or a close with no date, there is nothing to strike the multiple at or
  cut at, so the function returns None before any fact is read. No second price-date rule.
  - Before this, a priced but undated close read the whole blob (in-session review, finding 2). No
    committed page has one.
- EXTRACTION_VERSIONS gains `2026-11-03.ex-lease-share-cut`, with its JS twin; the drift pins are
  repinned.

**WHY.**
- The operator's C4 ruling (2026-11-01), verbatim: "Inputs are cut at the page's price date (filed
  on or before it; latest such filing wins; nothing after a sealed verdict)."
- #885 cut this multiple's net debt but handed the facts it was given to `share_denominator`
  whole. #885's own record reported this, unfixed, as outside its brief.
- The assembly hands it facts already cut (#884's `AsOfEdgar` view). The valuation-bases refresh
  (`refresh.valuation_bases_transform`) hands it the UNCUT blob. So on a refresh, one multiple
  paired a price-date balance sheet with a share count from a later 10-Q.
- **NCNO is the live case** (price date 2026-08-17). Its tracking fixture holds the 10-Q filed
  2026-08-25.
  - Read whole, the denominator is that 10-Q's diluted average, 105,361,192. The point-in-time
    count is refused against that quarter's basic average.
  - Read as filed by the price date, it is the corroborated point-in-time count, 109,552,950.
- Cutting at the function's entry, rather than in the refresh, keeps the multiple correct
  whichever caller hands it facts.

**HOW VERIFIED.**
- **Failing first on bb5870f2 (#885's round 2).**
  `test_the_at_price_ex_lease_multiple_reads_its_share_count_as_filed_by_the_price_date` reads the
  multiple three ways on every committed page that states it: on the page's tracking fixture, on
  that fixture cut at the price date, and once every row gains a later filing. All three must
  agree.
  - On bb5870f2 it fails, first on AMZN (15.977484 → 24.152807 with later filings, net debt
    unchanged).
  - All 16 pages that state the multiple move their share count with a later filing:
    ```
    AMZN: whole (15.977484, 10786313572.0, 23783.0) | cut (15.977484, 10786313572.0, 23783.0) | later-filed (24.152807, 16354500000.0, 23783.0)
    NCNO: whole (29.402509, 105361192.0, 210.894) | cut (30.466958, 109552950.0, 210.894) | later-filed (42.780134, 158041788.0, 210.894)
    (14 more pages: AORT BURL CNXC EPAM NFLX NKE PARR ROST SMPL TGT TJX VITL WERN WLK — each moves only with the later filings; whole == cut)
    ```
    Each tuple is (multiple, shares, net debt $M). NCNO is the only page whose real fixture already
    moves it.
  - Non-vacuity: `test_ncnos_share_count_moves_with_a_filing_after_its_price_date_unless_cut`
    shows NCNO's `share_denominator` differs whole vs cut.
- **Mutation:** removing the entry cut fails this pin and #885's
  `test_the_at_price_ex_lease_multiple_is_cut_at_the_pages_price_date`.
- **The undated close:** `test_an_undated_close_strikes_no_ex_lease_multiple`. NCNO with its close
  undated states no multiple; dated, it states one. Without the guard, the undated page returned a
  figure read off the whole blob.
- **Shown run.** `compute_anchor` (EDGAR-only), the assembly's cross-check and
  `ex_lease_at_price` ran on all 27 committed pages. Inputs were each page's tracking fixture at
  its own `stock_info.as_of` and `reference_date`. Trees: main 89ae0ad1, bb5870f2 and this branch.
  - bb5870f2 vs this branch:
    ```
    NCNO: ev_ebitda_ex_lease_at_price 29.402509 -> 30.466958
    27 pages, bb5870f2 vs branch: pages that differ: 1
    ```
  - Main vs this branch: LLY and NCNO, as #885 records. NCNO's multiple reads 29.801016 →
    30.466958, and every other move is #885's own.

**BOUNDARY.**
- **Pages:** all 27 committed pages with a `dossier.json` on 2026-11-03.
  - 16 of them state an at-price ex-lease multiple on their tracking fixture
    (`tests/fixtures/companyfacts/<T>.json`), each at its own `stock_info.as_of`.
  - Only LLY's and NCNO's fixtures hold a filing after the price date, and LLY states no
    multiple.
- **Comparison:** EDGAR facts only. `ex_lease_at_price` reads no CIQ fact; the multiple's EBITDA is
  the page's own lease-basis history.
- **Trees:** main 89ae0ad1, bb5870f2, and this branch; measured 2026-11-03.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages** (STATE row 41; none is refreshed here). NCNO (not pursued) carries 29.801016. Its next
  valuation-bases refresh writes 30.466958 (29.8x → 30.5x), on 109,552,950 shares and net debt
  210.894. On #885 alone it would have written 29.402509.
- **Reported, not changed.** The same refresh hands the uncut blob to
  `ebitda_recon.reconcile` (`financial_summary.ebitda_reconciliation`). That reconciliation reads
  each of CIQ's four latest quarters against the filings, so a re-filing of one of those quarters
  after the price date could reach it.
  - Not measured. It needs each page's own quarterly CIQ export, matched by hash, and the tracking
    fixtures keep only the tags the anchor pins read.
  - A cut where the refresh fetches the facts would close it and this case together. It is outside
    this brief, which named the share count.
