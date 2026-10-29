---
id: 2026-10-29-quality-checks-say-what-they-can-support
status: open
date: 2026-10-29
prs: []
supersedes:
superseded-by:
---

# The CIQ scorecard's market-cap check confirms only a cap that reconciles, the anchor bridge reads each statement's stated unit, and the core refuses an unknown status (audit BC-D9, BC-D10, BC-D11)

**WHAT.**
- **BC-D9: the market-cap check scores what it can support** (`vinci/quality/sources/ciq.py`
  `_market_cap_share_basis`).
  - It scored CONFIRMED for any gap between a page's market cap and its price times its shares
    that was not a whole-number ratio. That was every committed page, MVST at +57.1%.
  - A whole-number ratio is a share-basis change, which the check does detect: DIFFERS_STATED, as
    before. A 1,000x or 1,000,000x step is a unit error, not a split: DIFFERS_UNEXPLAINED.
  - Only a cap inside `freshness.RECONCILE_TOLERANCE` (2%) is CONFIRMED. That is the line the page
    already renders by: "the cap and the spot do not describe the same equity" beyond it. Any other
    gap is UNCHECKED, because price drift since the cap's panel and a wrong cap look the same here.
  - This corrects the 2026-10-23 scorecard record's accepted risk ("the market-cap check is weak").
    That reason covered detecting drift, not the label it wrote.
- **BC-D10: a stated-unit check** (`ciq.stated_unit`, `ciq_balance._stated_units`/`_unit_lines`).
  - The scale check measured magnitude against revenue only. An export wholly in another unit leaves
    every ratio unchanged, and thousands against millions between the two exports (the balance sheet
    from the quarterly, revenue from the annual) sits inside the [1e-4, 1000]x band. Both passed.
  - Now each statement sheet the bridge reads has its own unit line read. Any unit but Millions is a
    `UNIT:` failure: the bridge is refused and the outcome is `differ`.
  - An export that states no unit is left to the magnitude screen, and the check line says so.
  - The scorecard's tolerance text no longer claims that billions land outside the band.
- **BC-D11: an unknown status is refused** (`vinci/quality/core.py` `_score_check`). Rows were built
  from the four statuses, so a check returning 'confirmd' had its units dropped from the row and the
  fleet. A key outside them now raises, naming the check, the item and the key.
- **Extraction version `2026-10-29.BC-D10`** in both tables, and the drift pins re-pinned. BC-D9
  and BC-D11 change the scorecard, which builds no dossier.

**WHY.** Audit group BC, root-cause class RC5: a check that cannot fail, or whose status overstates
what it tested. A status the test cannot support is UNCHECKED.

**HOW VERIFIED.**
- **Failing first.** Before the fixes, on this branch at `bb4ab6e5`, the defect pins failed: BC-D9
  ×5, BC-D10 ×4 (the two refusals, and the unit line on both negatives), BC-D11 ×1. The negative pins
  passed and still pass: a reconciling cap confirms, a whole-number ratio is stated, the four
  statuses score.
- **Mutation.** Six mutants, each reverting one fix, all turned the pins red.
- **Real run, main against this branch.**
  - The CIQ scorecard over the committed pages: only `market_cap_share_basis` moved, from 26
    confirmed to 6 confirmed (AORT, CNXC, IT, ORKA, SMPL, TJX) and 20 unchecked. The other 19 checks
    are unchanged, and none raised under BC-D11.
  - `ciq_balance.extract` over the `-ta` CIQ folders: on all 32 readable names, every value,
    verdict, scale outcome and failure is identical. Each gains the line "unit: every statement read
    states Millions (6 sheets)". Scale outcomes: 30 agree, 2 not run (no revenue). LLY and MCK are
    refused by A-X1 pending the CIQ sync.

**BOUNDARY.**
- **Pages:** the 26 non-test committed `data/dossiers/*/dossier.json` at `bb4ab6e5`, with the held
  test page excluded.
- **CIQ folders:** the 34 non-test folders of `mosaic-theory-ta/data/manual/ciq`, read 2026-10-29.
- **Unit census:** 204 statement sheets (34 names × 2 exports × 3 statements), every one stating
  "In Millions of the reported currency".
- **Gaps:** `(implied − spot) / spot` from each page's own `stock_info`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The committed scorecard snapshots keep the old market-cap counts** until the next `--write`
  after the Phase 1 rebuild. `test_quality_ciq` re-derives the latest snapshot only while its page
  hash matches, and the pages have moved since 2026-10-28.
- **No page value moves.** The unit check refuses nothing on file today, so it guards a future
  export.
- **DEFERRED: `check_freshness`'s refusal note still calls a 1,000x cap ratio a corporate action.**
  It refuses that build either way, so only the wording is wrong. Falsifier: a build refused on a
  unit error that the note sends someone to look for a split.
