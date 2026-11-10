---
status: open
date: 2026-11-10
prs: []
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
- **Gate.** `bin/commit` green, with CIQ unlinked.

**BOUNDARY.**
- Pages: `data/dossiers/*/dossier.json` at `fd123ada`, 27 pages.
- SEC companyfacts read 2026-11-10, cut as filed by each page's `stock_info.as_of`.
- `CURRENT_DAYS` = 366.
- Peer-block refresh: the four pages named above.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The other 23 pages' peer blocks** are as assembled, with the old reading (a missing leg as 0.0,
  legs at their own dates) until each is rebuilt or refreshed.
  - How many of their rows that moves is not measured: it would need about 230 more peer fetches.
- **The single-leg rule is a choice.** A family the filer never tags is no leg: its other leg
  stands alone, labelled, on the subject page and on a peer row alike.
  - Falsifier: a filer whose 10-K states an intangibles balance it tags under its own extension
    tag. Its headroom would then read goodwill alone.
