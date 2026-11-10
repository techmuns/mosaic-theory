---
status: open
date: 2026-11-10
prs: [953]
supersedes:
superseded-by:
---

# Fix request 2, order 2, RD-D1: impairment headroom is goodwill and intangibles at ONE date, or UNKNOWN naming the dates found; a newer alias beats a stale first tag; a peer row never totals a missing leg as 0.0. MCK's headroom moves from $12,950.0M to $15,214.0M; all 27 committed pages re-rendered at $0

**WHAT.**
- **The fault.** Three pieces of `vinci/dossier/capital_allocation.py`, and its render:
  - `_pick(kind="instant")` took the first tag in a family with any point at all.
    - MCK's `IntangibleAssetsNetExcludingGoodwill` ends 2012-06-30.
    - Its `FiniteLivedIntangibleAssetsNet` runs to 2026-09-30.
    - So the page carried a 2012 intangibles balance as current.
  - Both renderers added each leg's own latest balance and cited goodwill's date only
    (`render.py`, `dossier.js`). MCK printed "$12,950.0M" (11,272 as at 2026-09-30 + 1,678 as at
    2012-06-30).
  - `_acquired_and_assets` (the peer intensity) added the legs the same way and read a missing leg
    as 0.0, over Assets at whatever date they had.
- **The fix.**
  - An instant is the first tag in the preference order whose latest balance is within
    `CURRENT_DAYS` (366) of the family's newest balance. So:
    - a stale first tag no longer wins (MCK's 2012 total);
    - a current total still beats a newer partial leg (review round 0);
    - the tag that answered is still named.
  - Every leg of the headroom is read under that one tag's dates.
  - `capital_allocation.impairment_headroom` (`CapitalAllocation.impairment_headroom`, an
    `ImpairmentHeadroom` of value, `as_at` and `legs`; `DROP_WHEN_NONE`) is built where both
    dates are structured:
    - it reads goodwill and intangibles at the latest date they SHARE, and states that date;
    - that date must be within `CURRENT_DAYS` (366, fix 3b's line) of the page's price date;
    - otherwise it is UNKNOWN, naming the dates found;
    - a family the filer never tags is no leg: goodwill alone is its own headroom while current.
  - Both renderers print the stored field and never add anything. A page without the field says
    the headroom is not recorded.
  - A peer row totals its legs at ONE date, with Assets at that date.
    - Legs sharing no date within `CURRENT_DAYS` of the filer's own latest balance state no total
      ("no shared balance — …").
    - A filer tagging only one family has that leg alone, labelled ("goodwill only — …"). That is
      the subject page's own rule, never a 0.0 added to the other leg.
  - The synthesis never receives the new field (`synthesis.NOT_SENT`): it derives from two
    balances the model already reads. All requests stay byte-identical to main's.
- **The refresh path.**
  - `refresh.impairment_headroom_transform` rewrites only the balance fields
    (`refresh.HEADROOM_FIELDS`): goodwill, intangibles, the dated headroom, and the two impairment
    fields whose STALE notes quote the balance date beside them.
  - A whole-block refresh would also land fix 3b's buyback rule (#930) on pages its own build left
    for their rebuild.
  - **Found and fixed on the way:** `capital_allocation_transform` and
    `peer_capital_intensity_transform` read TODAY's companyfacts, uncut. A refresh could therefore
    state a balance from a 10-Q filed after the page's price date. Assembly cuts there
    (`AsOfEdgar`). All three now read `refresh._facts_at`: companyfacts as filed by the page's
    `stock_info.as_of`.
- Extraction version `2026-11-10.dated-headroom`; the drift pins are re-pinned.
- **THE OPERATOR'S RULING ON ONE-FAMILY PEERS (2026-11-10, "yes" to the middle path, relayed by
  the coordinator).** Codex's round-1 P1 on #953 said a peer's lone leg should not enter the
  medians, because an absent tag is not a zero balance. The operator ruled for the middle path:
  1. **Display:** the peer is shown with the one leg it reports, labelled "goodwill only" or
     "intangibles only", as the subject page states its own headroom.
  2. **Median:** that peer is left OUT of the goodwill-plus-intangibles medians, and each median
     prints its count, e.g. "median of 6 of 10 peers". The charge median in the base-rate line
     prints its count too, since a charged peer stating no total has no ratio.
  3. **Base rate:** that peer stays IN the impairment base rate. The base-rate population no
     longer depends on the acquired total: it is every large peer whose write-down history was
     measured (`charged` or `explicit-zero`), whether or not its balance sheet gives a total.
  - **Found while building it, and fixed with it:** a peer's impairment window ended at its
    goodwill balance, even one the filer stopped tagging years ago. ROST's window was 2010-2015
    and URBN's 2018-2023. Once the base rate stopped depending on the acquired total, such a stale
    window would have counted as a current measurement. The window now ends at the first family
    whose balance is within `CURRENT_DAYS` of the filer's latest balance, so every row whose
    goodwill is current keeps its window.
  - Extraction version `2026-11-10.one-family-peers`; the drift pins are re-pinned.

**WHY.** RD-D1 is the last of the five order-2 defects in code. It waited for #930, which rewrote
the same `build_capital_allocation` sites (merged as `f491d155`).

**HOW VERIFIED.**
- **Fail first.** 9 pins were run against main `fd123ada`; all 9 fail.
  - They include MCK at 15,214.0 as at 2026-09-30, AMZN dated 2025-12-31, TGT and BURL UNKNOWN,
    the D notes' constructed input (600 as at 2026-03-31, which the audit's run printed as 800),
    the single-leg cases, and the peer legs.
  - The end-to-end page pin is among them: on main, MCK's page prints $12,950.0M.
  - Pins on the refresh path were added after them: it reads as filed by the price date, a
    2027-filed goodwill is never stated, and it moves its five fields only.
  - A pin for review round 0 was added too: a current total beats a newer partial leg.
- **Real data.**
  - The value pins read SEC's companyfacts for MCK, AMZN, TGT and BURL, cut to the five balance
    tags as filed by each page's price date (`tests/fixtures/capital_allocation_balances.json`,
    `scripts/build_balance_fixture.py`).
- **The $0 page pass.** `refresh_dossier` with the narrow transform, run on all 27 committed pages
  (AORT is retired, #942):
  - **MCK:** intangibles 1,678.0 (2012-06-30) → 3,942.0 (2026-09-30); headroom **$15,214.0M as at
    2026-09-30**.
  - **AMZN:** headroom $32,470.0M as at **2025-12-31**. That is the last balance both legs carry,
    because intangibles are filed annually; the note says goodwill is reported to 2026-09-30.
  - **TGT and BURL:** UNKNOWN. Intangibles were last tagged in 2021 and 2020, so the legs share no
    date within 366 days of the price date.
  - **ROST:** UNKNOWN. Its goodwill is last tagged in 2015, on a 2026 page. The audit did not list
    it; it is the same staleness.
  - **V:** goodwill and intangibles move from their 2026-03-31 balances to 2026-06-30. That is EDGAR
    as filed by V's own price date (2026-10-23), which its page had not caught up to. V's synthesis
    names no V balance.
  - **The other 21:** the field is added, and goodwill and intangibles are unchanged.
  - Every changed `dossier.json` differs from HEAD only inside `mechanical.capital_allocation`, in
    `layer_refreshes`, and, on the four below, inside `mechanical.peer_capital_intensity`. A script
    diff printed every page.
- **The peer block** was refreshed on MCK, AMZN, TGT and BURL only. Each subject row now matches its
  own headroom: MCK 15,214.0; AMZN 32,470.0 with Assets as at 2025-12-31.
  - **Labelled single legs:** COST and TJX ("goodwill only"); NFLX and BHIC ("intangibles only").
  - **Peers that state no total**, because their legs share no current date: KSS (goodwill last
    tagged 2009), ROST (2015), URBN (2023), ANF (intangibles 2018), DLTR, BBY and VSXY. TGT and
    BURL fall out as peers and as subjects.
  - **Median %-of-assets:**
    - MCK 45.1% → 45.1%;
    - AMZN 18.9% → 22.3% (n 10 → 9);
    - TGT 6.0% → 7.9% (n 10 → 8);
    - BURL 1.0% → 1.7% (n 8 → 3).
  - TGT's and BURL's own %-of-assets are now none.
  - No synthesis on these four pages cites a peer-intensity figure (searched).
- **Under the operator's ruling** (the same four pages, refreshed again at $0 with
  `peer_capital_intensity_transform`; a dry run printed every move first, and the refresh matched
  it):
  - **Fail first:** the four pins in `tests/test_peer_median_one_family.py` all fail on `4f6b4563`
    and pass here. They cover a one-leg peer shown but kept out of the median, the base rate
    counting a measured peer that states no total, a window ending at the filer's latest balance,
    and every committed page printing each median's count.
  - **Medians %-of-assets** (all peers; the counts are peers in the median out of peers shown):
    - MCK 45.1% → 48.6% (7 → 6 of 9; BHIC, intangibles only, left out). The large-peer median is
      unchanged: 3 of 4 (one large peer is unresolved).
    - AMZN 22.3% → 20.0% (9 → 8 of 10; NFLX left out). Leaving a lone leg out can move a median
      either way.
    - TGT 7.9% → 10.2% (8 → 6 of 10; COST and TJX left out).
    - BURL 1.7% → 3.9% (3 → 2 of 9; TJX left out).
  - **Base rate:**
    - TGT 3 of 6 → **5 of 8**: DLTR and BBY are measured, but their legs share no current date.
    - BURL 1 of 2 → **2 of 5**.
    - The charge median covers 3 of 5 on TGT (DLTR and BBY have no ratio) and 1 of 2 on BURL
      (ANF has none).
  - **Windows corrected:**
    - BURL: URBN moves from 2018-2023 (`charged`, reading a 2020 charge as current) to 2021-2026
      (`none-in-window`). ANF moves from 2013-2018 (`none-in-window`) to 2021-2026 (`charged`, its
      FY2026 charge). ROST's window moves too, and it stays `untagged`.
    - AMZN: KSS moves from 2004-2009 to 2021-2026, and it stays `untagged`.
  - Every `dossier.json` change is inside `mechanical.peer_capital_intensity` and
    `layer_refreshes`, on those four pages only. All 27 `dossier.md` re-render because the median
    lines now print their counts; on the other 23, only those lines and the counts change.
  - No synthesis on the four cites the intensity median or the base rate. Every "peer median" in
    them is the CIQ comps multiples (searched).
  - **Code review of this delta (`/code-review high --fix`): 10 findings.**
    - **Fixed (4):**
      - A filer tagging ONE family that is not current read "no shared balance". It now reads "no
        current balance": KSS, ROST, URBN and ANF.
      - A row stating no total had dropped its current Assets, which it showed before RD-D1. It
        keeps it now.
      - These two are behind `::test_a_row_with_no_total_names_its_case_and_keeps_its_assets`,
        which failed first.
      - The `_pick` docstrings were corrected, and a long line in `scripts/build_balance_fixture.py`
        was wrapped.
    - **Dismissed (2):**
      - The renderers count from the rows rather than from stored fields. The end-to-end pin checks
        those counts against each page's stored median on every committed page, so no schema field
        is added.
      - A duplicate `_pick` scan is a cleanup.
    - **Put to the operator (1):** whether a one-leg peer's ratio (COST's charge over its goodwill)
      belongs in the CHARGE median. The ruling keeps the peer in the base rate, and the code does;
      the median's count is printed.
    - **Found, not fixed (3):**
      - The subject's STALE impairment check dates itself against the first family's balance, even
        a stale one. No committed subject is affected: ROST has no charge, and TGT and BURL have
        current goodwill.
      - A peer whose current total is exactly 0.0 gets no ratio and no note. TENX on TECX's page has
        this, and it predates #953.
      - The Goodwill and Intangibles lines print each leg's own latest balance with no date beside
        it; ROST prints a 2015 goodwill. This predates #953.
- **Code review (round 0, `/code-review high --fix`):** 10 findings.
  - Fixed (9):
    - the goodwill-only peers fell out of the medians and the impairment base rate: they are now
      single legs, as on the subject page. The reviewer's fixture edit to
      `test_peer_impairment.py`, which hid this, is reverted;
    - V's impairment STALE notes quoted the old balance date: the transform now rebuilds the two
      impairment fields;
    - "newest across the family" could read a partial leg over a current total: the pick is now
      preference-with-currency;
    - a peer's staleness note said "price date": it now says "the filer's latest balance date";
    - the network-marked absence test now accepts a dated UNKNOWN;
    - the zero-coercion lint's stale ALLOWED entry is removed;
    - the fixture builder is exempted in the one-write pin;
    - a long line is wrapped;
    - duplicate scans are removed.
  - Not changed (1): treating a single-family filer as one leg is a choice (below).
- **The overlap with the order-1 rebuild (#949).** It merged first and re-assembled VITL, VRRM, EPAM, WLK, V, UBER and TECX. The merge of main took #949's pages as they are and re-ran this PR's $0 headroom refresh on them with the merged code; no `.md` was hand-merged.
  - Each of the seven then differs from main only by the headroom field and its refresh entry.
  - V's re-assembly already carries its 2026-06-30 balances.
- **Gate.** `bin/commit` green, with CIQ unlinked.

**BOUNDARY.**
- Pages: `data/dossiers/*/dossier.json` at `fd123ada`, 27 pages.
- SEC companyfacts read 2026-11-10, cut as filed by each page's `stock_info.as_of`.
- `CURRENT_DAYS` = 366.
- Peer-block refresh: the four pages named above, once for RD-D1 and once under the ruling
  (SEC read 2026-11-10, cut at each page's `stock_info.as_of`; code at `4f6b4563` plus the ruling).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The other 23 pages' peer blocks** are as assembled, with the old reading (a missing leg as 0.0,
  legs at their own dates) until each is rebuilt or refreshed.
  - How many of their rows that moves is not measured: it would need about 230 more peer fetches.
- **The single-leg rule is RULED by the operator (2026-11-10, above).** A family the filer never
  tags is no leg. Its other leg stands alone, labelled, on the subject page and on a peer row
  alike, and on a peer row it is kept out of the medians.
  - Falsifier: a filer whose 10-K states an intangibles balance it tags under its own extension
    tag. Its headroom would then read goodwill alone.
- **OPEN, not built: a "confirmed nil" third state** (the operator's follow-up, 2026-11-10). A peer
  whose balance-sheet presentation shows the other line is ABSENT has a confirmed nil leg, not an
  untagged one, so its single leg is its whole total and could enter the medians. Today the code
  cannot tell an absent line from an untagged one. Recorded here, not in STATE §5.0.
- **Two network-marked tests fail, and they fail on main's code too** (not in the gate):
  - `test_peer_capital_intensity.py::test_the_two_denominators_disagree_and_that_is_the_point`:
    SMPL's ratio to market cap reads 1.39 against a pinned 1.66, and main's builder gives the same
    1.389 on today's companyfacts.
  - `::test_the_peer_table_renders_without_capital_allocation`: no committed page now has a peer
    block without a capital-allocation block.
  - Found, not fixed.
- **Found, not fixed:** a charge's "% of acquired" divides a five-year charge total by the CURRENT
  balance, so a name that wrote most of it off reads far above 100%. ETSY on AMZN's page reads
  2,381% (1,146.7 over 48.2), and AMZN's charge median of 2 reads 1,194%. This predates #953.
