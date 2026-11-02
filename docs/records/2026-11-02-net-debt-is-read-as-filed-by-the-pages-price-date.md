---
id: 2026-11-02-net-debt-as-of
status: open
date: 2026-11-02
prs: []
supersedes:
superseded-by:
---

# Net debt is read as filed by the page's price date: a later re-filing, or a later balance sheet, never moves a sealed figure (audit E2-D21; operator ruling C4)

**WHAT.**
- **`edgar.net_debt.net_debt(facts, *, as_of=None)`.** With an as-of, the companyfacts blob is cut
  by `concepts.facts_as_of` (#801, called, never edited) before any leg is read.
  - `_at` and every `latest_instant` keep an instant's LATEST filing, and now see only rows filed
    by the as-of. That is the route `facts_as_of`'s docstring prescribes: prune the whole blob
    once, rather than thread a date through each reader.
  - `None` reads every row, as before. The screen's snapshot cuts its own facts first
    (`compute_fundamental_snapshot`), so it is unchanged.
- **The anchor's two builders take `as_of` as a REQUIRED keyword** (`_lease_inclusive_net_debt`,
  `lease_inclusive_net_debt`), so no caller reads every filing by default. mypy named the three
  callers that had none.
- **`anchor.page_price_date(mechanical)`** is the page's price date: `stock_info.as_of`, the EOD
  bar, which `date_semantics.price_as_of` names. Every net-debt read on a page passes it:
  - the anchor (`_bridge_inputs`, so `compute_anchor` at assembly and the CLI's anchor backfill);
  - the assembly's EV-bridge cross-check (`assemble.py`);
  - the at-price ex-lease multiple (`ev_ebitda_basis.ex_lease_at_price`);
  - the bridge refresh (`refresh.ev_bridge_transform`).
- **Two files outside Session A's list carry one argument each:** `assemble.py:1203` and
  `ev_ebitda_basis.py:144`.

**WHY.**
- The operator's C4 ruling (2026-11-01), verbatim: "Inputs are cut at the page's price date (filed
  on or before it; latest such filing wins; nothing after a sealed verdict)."
- Net debt took no as-of, so whatever companyfacts held when a page was rebuilt became its figure.
  - The audit's case, N2: OC's 2026-06-30 debt total re-filed 101M higher reads leverage net debt
    4,919.0M → 5,020.0M.
  - The same hole lets a balance sheet filed after the price date in. It is live on NCNO, below.
- The parameter is `as_of`, as on `compute_fundamental_snapshot` and `facts_as_of`. C4's own sites
  (the screens' enrichment, `mechanical._adjusted_facts`, the CIQ-empty fallback, the EOD features)
  do not call net debt, so no call is shared with Session C.

**HOW VERIFIED.**
- **Failing first, on main 60151ccc:** all 4 tests in `tests/test_net_debt_as_of.py` fail.
  - The `net_debt` pair fails on the absent keyword.
  - The anchor's lease-inclusive figure moves 5,458.0 → 5,559.0 with a 10-K/A filed after the price
    date.
  - The bridge refresh lands 5,559.0.
  - The fixture is OC's frozen companyfacts (`tests/fixtures/net_debt_shapes/OC.json`). The
    re-filing is its real 2026-06-30 `LongTermDebt` row (5,125M), 101M higher, under a later
    accession.
  - Re-filing `LongTermDebtNoncurrent` instead moves nothing, because OC's bare total completes its
    current tag. That is why the first construction of the probe moved nothing.
- **Negative pins:** a re-filing on or before the price date is read ("latest such filing wins"),
  `filed == as_of` included. `as_of=None` still reads every row.
- **Shown run (decision path, anchor/R1).** `compute_anchor` ran on each of the 26 committed pages'
  mechanical layers (held pack excluded), EDGAR-only, under main 60151ccc's code and this branch's.
  - **On the facts each page was built from** (its tracking fixture,
    `tests/fixtures/companyfacts/<T>.json`):
    ```
    26 anchors
    LLY:  anchor_base_value_per_share 752.2356 -> 750.7357 (committed 752.2356); net_debt.value 45980.0 -> 47320.0
    NCNO: net_debt.value 242.641 -> 210.894 (committed 242.641)
    anchors that differ: 2
    ```
  - **On today's cache** (cache only, no SEC call; fetched 2026-10-27, AMZN 2026-11-02):
    ```
    AMZN: net_debt.value 81536.0 -> 23783.0; anchor_base_value_per_share 274.3457 -> 279.7 (committed 279.7)
    NCNO: net_debt.value 242.641 -> 210.894
    anchors that differ: 2
    ```
    Here LLY reads 47,320.0 on both trees: its cached copy predates the Q3 10-Q. The first cut of
    this record read that as cache vintage. The gate's
    `test_the_period_fix_moves_the_committed_anchor_and_exactly_these_names` found LLY on the
    fixture.
  - **LLY** (pursued). Price date 2026-10-28; assembled 2026-10-29, the day its Q3 10-Q
    (0000059478-26-000108) was filed. The committed anchor read that 2026-09-30 balance sheet.
    - Cut at its price date, it reads the 2026-06-30 balance sheet (filed 2026-08-05): base
      750.7357 a share, 0.2% under the committed 752.2356.
    - It moves only on an anchor recompute before its owed re-assembly. The re-assembly takes a new
      price date, and the 10-Q with it.
    - Added to `ANCHORS_AWAITING_BACKFILL`.
  - **NCNO** (not pursued). The committed page (price 2026-08-17, assembled 2026-08-18) carries
    242.641.
    - That figure is read off the 2026-07-31 balance sheet, whose 10-Q (0001902733-26-000101) was
      filed 2026-08-25, after its price date. The anchor recomputed on 2026-10-21 took it in.
    - Cut at its price date it reads 210.894, the 2026-04-30 balance sheet as filed 2026-05-27.
    - Its recipe is R2_NEEDED, so no per-share value moves.
  - **AMZN.** Its cache holds the Q3 10-Q, filed after its 2026-10-23 price date. On main's code an
    anchor backfill on that cache would move its sealed R1 from 279.70 a share to 274.35. Here it
    keeps 279.70.
  - The other pages are identical on both trees. The lease-inclusive cross-check differs on the same
    names only.
- **The suites for net debt, the anchor, the lease basis, the EV bridge, tag freshness and the
  securities leg** pass (358). The one failure, `test_claims_equal_ciqs_current_figure_on_every_committed_name`
  on AORT, fails identically on main against the `-ta` copy.

**BOUNDARY.**
- **Pages:** the 26 committed pages' names on 2026-11-02, held pack excluded, each at its own
  `stock_info.as_of` (2026-08-17 … 2026-10-28). They were read twice: on each page's tracking
  fixture (the facts it was built from), and on the companyfacts cache (fetched 2026-10-27; AMZN
  2026-11-02).
- **Comparison:** `compute_anchor` with `ciq=None`, so a CIQ fill is not part of either side.
  ORKA's and TECX's committed net debts are CIQ fills, and read None on both trees here.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages** (STATE row 41; none is re-assembled here). Two committed anchors move at their next
  recompute:
  - LLY (pursued): 752.2356 → 750.7357 a share, until its owed re-assembly takes a new price date;
  - NCNO (not pursued): net debt 242.641 → 210.894.
  AMZN is kept from moving.
- **Not changed, reported.** The anchor's other EDGAR legs (D&A, FCF, the share counts) still read
  the whole blob, so a filing after a page's price date can still reach them on an anchor backfill.
  NCNO's recompute on 2026-10-21 shows the route.
  - This brief named net debt only.
  - C4's listed sites are the screens' enrichment, `mechanical._adjusted_facts` and the CIQ-empty
    fallback, and none of them is the anchor.
  - The same cut at `compute_anchor`'s entry would close it.

**ROUND 1 (in-session `/code-review high` on 2d638da3; Codex's review failed on its usage limit).**
- **STATE row 41's figures now state their boundary:** `compute_anchor`, EDGAR-only, on each page's
  tracking fixture at its own price date, measured 2026-11-02 at 2d638da3.
- **DEFERRED: the anchor's CIQ net-debt fill is not cut at the price date.** Where the cut leaves
  EDGAR no net debt, the workbook's latest balance-sheet column fills it. That export is the page's
  own input, matched by hash. C4 rules on EDGAR filings, and cutting a CIQ export at the price date
  is a question of its own.
- **DISMISSED: the bridge refresh reuses the committed anchor net debt on a page not priced
  ex-lease.** That is by design (the cross-check follows the anchor's figure), and the anchor's own
  recompute applies the cut.
