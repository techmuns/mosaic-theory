---
id: 2026-11-02-net-debt-as-of
status: shipped
date: 2026-11-02
prs: [885]
supersedes:
superseded-by:
---

# Net debt, and every leg of the anchor, is read as filed by the page's price date: a later re-filing, or a later quarter, never moves a sealed figure (audit E2-D21; operator ruling C4)

**WHAT.**
- **`edgar.net_debt.net_debt(facts, *, as_of=None)`.** With an as-of, the companyfacts blob is cut
  by `concepts.facts_as_of` (#801, called, never edited) before any leg is read.
  - `_at` and every `latest_instant` keep an instant's LATEST filing, and now see only rows filed
    by the as-of. That is the route `facts_as_of`'s docstring prescribes: prune the whole blob
    once, rather than thread a date through each reader.
  - `None` reads every row, as before. The screen's snapshot cuts its own facts first
    (`compute_fundamental_snapshot`, #884), so it is unchanged.
- **The anchor's two net-debt builders take `as_of` as a REQUIRED keyword**
  (`_lease_inclusive_net_debt`, `lease_inclusive_net_debt`), so no caller reads every filing by
  default. mypy named the three callers that had none.
- **ONE CUT FOR EVERY LEG OF THE ANCHOR (round 2).** `compute_anchor` cuts the companyfacts blob
  ONCE, at its entry, with `facts_as_of(facts, price_date)`. The margin, D&A, FCF, the diluted and
  basic weighted averages, the point-in-time count's corroboration and net debt all read the same
  filings. Its own net-debt read passes `as_of=None`, because the facts arrive cut.
- **The price date is `vinci.edgar.asof.page_price_date` (#884), with its reference-date
  fallback.** It is the stored close's date (`stock_info.as_of`), or the page's reference date
  when there is no stored close. No second price-date helper: round 0's
  `anchor.page_price_date(mechanical)` is gone. `anchor.price_as_of(mechanical)` only parses the
  field off a dumped layer.
  - `compute_anchor` takes `reference_date`. Both production callers pass the page's:
    `assemble._assembly_anchor` passes `fin.reference_date`, and the CLI's anchor backfill passes
    `d.reference_date`. A page that states neither date is read whole.
  - The assembly's EV-bridge cross-check is now `assemble._edgar_cross_check`, the same date.
  - The bridge refresh (`refresh.ev_bridge_transform`) uses the same date, with the page's
    `reference_date` as the fallback.
  - The at-price ex-lease multiple (`ev_ebitda_basis.ex_lease_at_price`) keeps `stock_info.as_of`.
    A page with no stored close has no price to strike that multiple at, so it returns None
    before any net debt is read.
- **Where the cut leaves no balance sheet, the source says so:** "UNKNOWN — no debt/cash tag filed
  by the <date> price date". It says that only where the uncut blob holds one; a filer that tags
  none (ORKA) keeps "UNKNOWN — no debt/cash tag" byte-for-byte.
- **Two files outside Session A's list:** `assemble.py` (the cross-check helper and the reference
  date) and `ev_ebitda_basis.py:144` (one argument).
- **Bookkeeping.** EXTRACTION_VERSIONS gains `2026-11-02.net-debt-as-of` (round 0) and
  `2026-11-03.anchor-cut-at-price-date` (round 2), each with its JS twin; the drift pins are
  repinned.

**WHY.**
- The operator's C4 ruling (2026-11-01), verbatim: "Inputs are cut at the page's price date (filed
  on or before it; latest such filing wins; nothing after a sealed verdict)."
- Net debt took no as-of, so whatever companyfacts held when a page was rebuilt became its figure.
  - The audit's case, N2: OC's 2026-06-30 debt total re-filed 101M higher reads leverage net debt
    4,919.0M → 5,020.0M.
  - The same hole lets a balance sheet filed after the price date in. It is live on NCNO, below.
- **Round 2: cutting net debt alone mixed quarters inside one anchor.** On LLY, round 1's anchor
  read net debt at the 2026-06-30 balance sheet but D&A over an LTM window to 2026-09-30 and a
  diluted average from the Q3 10-Q filed 2026-10-29, after the page's 2026-10-28 price date. A
  cut at `compute_anchor`'s entry closes every leg at once. Threading a date through each reader
  is the route #884's review rejected.
- The parameter is `as_of`, as on `compute_fundamental_snapshot` and `facts_as_of`. C4's own sites
  (the screens' enrichment, `mechanical._adjusted_facts`, the CIQ-empty fallback, the EOD features)
  do not call net debt or the anchor, so no call is shared with Session C.

**HOW VERIFIED.**
- **Round 0, failing first on main 60151ccc.** All 4 tests then in `tests/test_net_debt_as_of.py`
  fail.
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
- **Round 2, failing first on round 1's head ec5bf1ce.** The six new tests in
  `tests/test_net_debt_as_of.py`:
  - `test_every_leg_of_the_anchor_reads_the_facts_as_filed_by_the_price_date`: on every committed
    page, the anchor equals the anchor on its fixture cut at the price date. It also equals the
    anchor once every row gains a later filing.
  - Run on ec5bf1ce without the new keyword, that equality fails on exactly LLY and NCNO:
    ```
    LLY: d_and_a 2174.0 (uncut) vs None (as filed by 2026-10-28); diluted_shares 893400000.0 (uncut) vs 893700000.0 (as filed by 2026-10-28); base 750.7357 vs None
    NCNO: diluted_shares 105361192.0 (uncut) vs 109458472.0 (as filed by 2026-08-17); shares_outstanding None (uncut) vs 109552950.0 (as filed by 2026-08-17); dilutive_increment None (uncut) vs 955925.0 (as filed by 2026-08-17)
    ```
  - Non-vacuity: on NCNO, the later filings move every leg the anchor reads from EDGAR unless cut
    (D&A, net debt, diluted, shares outstanding, the increment, FCF). LTM revenue is the page's own.
  - The reference-date fallback, with its negative pin: neither date means the blob is read whole.
  - The cross-check (`_edgar_cross_check`) and the ex-lease multiple are pinned on NCNO, the one
    live case.
  - The empty-balance-sheet wording, with its negative pin (a blob with no tag keeps the old words).
  - On ec5bf1ce, 5 of the 6 fail (the ex-lease site was already cut there).
- **Mutations on round 2's tree, each caught:**
  - `_edgar_cross_check` at `as_of=None` fails its NCNO pin.
  - `ex_lease_at_price` at `as_of=None` fails its NCNO pin. Before this round, either mutation
    survived 531 tests.
  - Removing the entry cut fails 5 tests.
  - Dropping the reference-date fallback fails its pin.
- **Shown run (decision path, anchor/R1).** `compute_anchor` (EDGAR-only, `ciq=None`), the
  assembly's cross-check and `ex_lease_at_price` ran on every committed page under main 89ae0ad1,
  round 1's head ec5bf1ce and round 2. Inputs were each page's tracking fixture
  (`tests/fixtures/companyfacts/<T>.json`, the facts it was built from), each page's
  `reference_date` and its stored close.
  - Main vs round 2:
    ```
    LLY:  anchor_base_value_per_share 752.2356 -> None; applicable True -> False; anchor_ev_ebit 27.8482 -> None; d_and_a 2174.0 -> None; diluted_shares 893400000.0 -> 893700000.0; net_debt 45980.0 -> 47320.0; ev_bridge.edgar_net_debt 45980.0 -> 47320.0
    NCNO: net_debt 242.641 -> 210.894; diluted_shares 105361192.0 -> 109458472.0; shares_outstanding None -> 109552950.0; dilutive_increment None -> 955925.0; ev_bridge.edgar_net_debt 255.337 -> 223.899; ev_ebitda_ex_lease_at_price 29.801016 -> 29.402509 (its net debt 242.641 -> 210.894)
    27 pages, main vs r2: pages that differ: 2
    ```
  - Round 1 vs round 2: the same two pages. LLY's base goes 750.7357 → None, D&A 2,174.0 → None,
    and the diluted average 893,400,000 → 893,700,000. NCNO's diluted, shares-outstanding and
    increment legs move as above. Round 1 had already cut net debt, the cross-check and the
    ex-lease multiple.
  - No other page moves on any of the three trees; the other 25 read identically. Of the 27
    fixtures, only LLY's (a filing of 2026-10-29) and NCNO's (2026-08-25) hold a filing after the
    page's price date. The committed
    values match main's on both moved pages. LLY's committed base is 752.2356; NCNO's committed
    net debt is 242.641, its cross-check 255.337 and its multiple 29.801016.
  - **LLY** (pursued). Price date 2026-10-28; assembled 2026-10-29, the day its Q3 10-Q
    (0000059478-26-000108) was filed.
    - Cut whole at its price date, it reads the 2026-06-30 balance sheet (net debt 47,320.0) and
      the Q2 averages. No EDGAR D&A covers the page's window to 2026-09-30, so its base is None.
    - Round 1 read 750.7357: Q2 net debt beside a Q3 D&A and diluted average.
  - **NCNO** (not pursued). Price date 2026-08-17; assembled 2026-08-18. Its committed figures read
    the 2026-07-31 balance sheet, whose 10-Q (0001902733-26-000101) was filed 2026-08-25. The
    anchor recomputed on 2026-10-21 took that 10-Q in.
    - Cut at its price date, it reads the 2026-04-30 balance sheet as filed 2026-05-27: net debt
      210.894. The cross-check reads 223.899.
    - The point-in-time count now corroborates (109,552,950, 1.0% above Q1's basic average).
      Uncut, it was refused against Q2's.
    - Its recipe is R2_NEEDED, so no per-share value moves.
  - **AMZN** reads the same on all three trees here: its fixture holds no filing after its
    2026-10-23 price date.
    - Round 0's claim (279.70 a share kept, where main's code on "today's cache" reads 274.35) was
      measured on the opening session's companyfacts cache. Its AMZN copy
      (`data/cache/sec/350c1a14b67a3810a0cd23f8baa26cbf71f8efc902eb74f7eebcb413b1fef425.json`,
      the CIK0001018724 companyfacts URL's key) was fetched 2026-11-02 and holds AMZN's 10-Q filed
      2026-10-30.
    - It reproduces only on a copy holding that 10-Q. A cache fetched 2026-10-27 reads 279.70 on
      both trees (the coordinator's review of b310fda0).
    - Not re-run here: no AMZN companyfacts copy from October or later is on this machine.
- **Suites.** ruff and `mypy --strict vinci` are clean, and `node --check` passes. The full offline
  suite, and its comparison with ec5bf1ce, are in the PR body.

**BOUNDARY.**
- **Pages:** all 27 committed pages with a `dossier.json` on this branch on 2026-11-03, each with
  its tracking fixture, each at its own `stock_info.as_of` (2026-08-17 … 2026-10-28) and
  `reference_date`. Round 0's 26 left out a held pack; this count leaves out nothing.
- **Comparison:** `compute_anchor` with `ciq=None`, so a CIQ fill is not part of any side. ORKA's
  and TECX's committed net debts are CIQ fills, and read None on all trees here. LLY's CIQ exports
  were re-exported 2026-11-03 for its rebuild, so a with-CIQ read would pair the page's old layer
  with a new export; it was not run.
- **Trees:** main 89ae0ad1, round 1's head ec5bf1ce, and round 2's working tree; measured
  2026-11-03.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages** (STATE row 41; none is re-assembled here). Two committed anchors move at their next
  EDGAR-only recompute:
  - LLY (pursued): base 752.2356 → None, until its owed re-assembly takes a new price date, and
    the Q3 10-Q with it.
  - NCNO (not pursued): net debt 242.641 → 210.894, plus its share legs.
  NCNO's at-price multiple 29.801016 and cross-check 255.337 move at the next refresh of each: to
  29.402509 and 223.899.
- **LLY is NOT added to `ANCHORS_AWAITING_BACKFILL`** (and round 0's addition is reverted). Cut
  whole, its EDGAR-only base is None, not another number. A recompute that values nothing is not a
  divergence: the gate pin counts it in `unvalued`, which LLY's place in `BRIDGE_ONLY_ANCHORS`
  already covers. Listing it would red the pin.
  - The cost: until LLY is re-assembled, that pin does not compare LLY's committed 752.2356 at
    all.
  - Likewise `test_lillys_real_page_refuses_its_count_and_keeps_its_equity` now moves LLY's close
    to 2026-10-29, the 10-Q's filing date, so its pin stays on the count.
- **Reported, not changed.**
  - **The ex-lease multiple's share count is still read whole on the refresh path.**
    `ex_lease_at_price` cuts net debt, but `share_denominator` reads the facts it is handed.
    `valuation_bases_transform` hands it the uncut blob. (The assembly hands it facts already cut
    by #884's view.)
    - On NCNO, the 29.402509 above therefore divides by the diluted average from the 10-Q filed
      after the price date (105,361,192). The point-in-time count was refused against that 10-Q.
    - Fully cut, it is 30.466958 on 109,552,950 shares.
    - A cut at `ex_lease_at_price`'s entry, the same move as `compute_anchor`'s, would close it. It
      is outside this brief, which named `compute_anchor`.
  - **DEFERRED (round 1): the anchor's CIQ net-debt fill is not cut at the price date.** Where the
    cut leaves EDGAR no net debt, the workbook's latest balance-sheet column fills it. That export
    is the page's own input, matched by hash, and CIQ's balance-sheet facts carry no
    `period_end` to cut on. C4 rules on EDGAR filings, and cutting a CIQ export at the price date
    is a question of its own.

**ROUND 1 (in-session `/code-review high` on 2d638da3; Codex's review failed on its usage limit).**
- **STATE row 41's figures now state their boundary:** `compute_anchor`, EDGAR-only, on each page's
  tracking fixture at its own price date, measured 2026-11-02 at 2d638da3.
- **DEFERRED: the CIQ net-debt fill**, above.
- **DISMISSED: the bridge refresh reuses the committed anchor net debt on a page not priced
  ex-lease.** That is by design (the cross-check follows the anchor's figure), and the anchor's own
  recompute applies the cut.

**ROUND 2 (the coordinator's review of b310fda0, 2026-11-03; the last round).**
- **BLOCKER, fixed:** one cut for every leg, at `compute_anchor`'s entry, on #884's price date.
- **The two untested cut sites are pinned** on NCNO: the assembly's cross-check and the at-price
  ex-lease multiple.
- **NCNO's two moved values are in row 41**, re-derived from the replay: the multiple 29.801016 →
  29.402509, and the cross-check 255.337 → 223.899.
- **AMZN's claim states its cache**, above.
- **Nits.**
  - The no-balance-sheet wording.
  - `prs: [885]`.
  - #884 cited for the screen's own cut.
  - The reference-date fallback.
  - The CIQ deferral is kept.
