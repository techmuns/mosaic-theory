---
id:
status: open
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# W50: the page's R1 screening anchor prices its band's CURRENT multiple, the median printed beside it and never priced; a band with no usable current anchors nothing and says why; IN CODE, no committed page re-rendered — the preview is stopped for the operator ($0)

**WHAT.**
- **The anchor.** `compute_anchor` strikes the screen value at the `current` of the band R1 prices
  on (`r1_multiple_band`: ex-lease where rent is material, else CIQ's own history). That is the
  multiple recipe 3a (#1093) proposes for the record's base. `anchor.multiple` now records:
  - `statistic: "current"`;
  - `as_of`, the latest close the current is struck at;
  - `median`, the trailing median, printed beside it and never priced.

  All three are written absent, never null, so every anchor committed before W50 round-trips
  byte-identically. The citation moves to `….current`. The `valuation.lease_basis` prefix, which
  `anchor_prices_ex_lease` and the renderers key on, is kept.
- **Fail loud.** A band whose current is absent, NM, non-finite or not positive prices nothing:
  - no multiple value and no base;
  - `applicable` is False;
  - the reason names the missing current and the median it refused to use in its place.

  The test is ONE helper, `anchor.usable_multiple`. Recipe 3a's proposal now uses it too
  (`propose._usable_multiple` is that helper), so a page can never propose a multiple its screen
  refuses.
- **What the anchor means now.** It reads the mid-cycle (median) margin at TODAY'S multiple:
  "what this is worth at the multiple it trades on today if its margin is what it was". It no
  longer reads "if the business and its rating both return to their history". The method row,
  the subtitle and the multiple row ("Current multiple, own history … median Xx beside it, not
  used") say so. The renderers choose those words from `multiple.statistic` (md
  `_screening_context_lines` and `_lease_basis_line`, and their twin `anchorInner` in
  dossier.js). A committed page, which priced the median, therefore prints the median words until
  it is re-derived.
- **The mid-cycle gap sentence** no longer says "R1 pairs that median with the median multiple".
  It says R1 prices the median at today's multiple. It also says which way that pushes the value
  when the twelve months sit five points or more off the median. This is arithmetic at one price:
  a multiple struck on above-median EBITDA reads lower than it would on median EBITDA, and one
  struck on below-median EBITDA reads higher.
- **`refresh.band_checks_backfill`** decides which band a committed anchor priced from that
  anchor's own statistic (`priced_band_value`). Before this change it would have refused every
  pre-W50 page as "not the band its anchor priced".
- **Not touched.** `R1_FORMULA` and `recipe_formula`, the record stamps, are unchanged. The
  anchor's description is not in a stamp.

**WHY.**
- **The bias recipe 3a removed was still on the page.** SMPL's page priced 18.2256x where its
  template proposes 5.1351x (ex-lease band, as of 2026-10-27). The median sat 2.4x–3.9x above the
  current on the de-rated names (3a's record). #1004 item 3c had already moved the screen off the
  headline because it flattered exactly those names.
- **Not a STOP on the definition.** R1's recipe id (`R1_midcycle_margin_evebitda`) and
  `R1_FORMULA` ("EV = EBITDA × exit multiple") make the MARGIN mid-cycle and name no statistic
  for the multiple. Pairing the median margin with the median multiple was the anchor's own design
  rationale (the `AnchorMidcycleGap` docstring), and 3a had already moved R1's proposal off it.
- **DOES THIS SELECT ON FORM?** No. The change chooses which statistic of one numeric series
  (TEV/LTM EBITDA, one basis, one unit) prices the screen. The refusal fires on a value: missing,
  NM (non-positive EBITDA), or ≤ 0. It never reads how a filer discloses.

**HOW VERIFIED.**
- **Pins** (`tests/test_w50_anchor_current.py`), built from the real committed pages and their
  committed companyfacts fixtures.
  - **Positive.** Every page whose anchor reaches the multiple leg prices its band's current, and
    that is the 3a proposal's base multiple. SMPL's base is R1's arithmetic at the current, not at
    the median. BRBR cites `own_history.current`.
  - **Negative.** On SMPL's real page, a current that is dropped, None, "NM", 0, negative,
    infinite or True prices nothing and never the median, and `check_tier_agreement` then
    refuses an R1 record. The gap sentence names the unmatched pair on WLK (below the median) and
    NFLX (above). Committed pages round-trip with no new keys. Both renderers print the median
    words for SMPL's committed anchor and today's words for its derived one (md, and node on
    dossier.js).
  - **Mutation.** 10 of 10 mutants turn their pin red: median fallback, null keys, md or JS
    always printing the median words, gap tails swapped, backfill assuming current, a `float()`
    band read, the base or the block priced at the median, and the gate ignoring a missing
    current.
- **Existing pins moved**, each from the median to the current, with the reason stated in the
  test:
  - four lease-basis pins;
  - the `AnchorMultiple` field set;
  - the parity pin, which now also binds the current-multiple method and subtitle;
  - `test_the_period_fix_moves_the_committed_anchor_and_exactly_these_names`. It strikes the
    fresh inputs at the COMMITTED multiple, which keeps it a guard on the INPUTS it watches. Its
    recorded set is unchanged.
- **The preview** (PREVIEW RULE) is stopped for the operator. Each AFTER page goes through the
  `anchor-backfill` path (head code, the committed companyfacts fixture, the CIQ export read-only,
  `write_recorded`), written only into a scratch folder. A control strikes the fresh inputs at the
  committed multiple, and it reproduces each committed base, so each move is the multiple alone:

  | Page | Multiple, before → after | Base, before → after | Control | Spot |
  | --- | --- | --- | --- | --- |
  | SMPL | 18.2256 → 5.1351 (median beside) | $46.48 → $11.37 | $46.48 | $12.64 |
  | GOOGL | 17.4518 → 22.8888 | $225.54 → $292.90 | $225.54 | $293.45 |
  | NKE | 23.3883 → 10.3518 | $99.30 → $43.58 | $99.30 | $37.15 |
  | BRBR, current set to −1.0 (schema-valid) | 19.7614 → none | $57.77 → none, applicable False, the reason printed | — | — |

**BOUNDARY.**
- **Pages:** 26 committed pages at `beb068e8`. 21 carry `anchor.multiple`, every one equal to its
  band's median. Every band R1 reads carries a usable current, so 0 of 26 refuse.
- **The schema:** `current` is a required float on the page (pydantic), so a validated page can
  carry an unusable current only as ≤ 0. The None, absent and NM pins guard the dict-level reader.
- **Preview:** 4 pages, head code at this branch, companyfacts fixtures as committed, CIQ exports
  from the primary checkout as of 2026-11-17.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The pair is no longer matched.** The current is struck on the twelve months' EBITDA. Where
  the twelve months sit five or more points off the median margin, the screen compounds the
  margin reversion with a multiple set on the margin it reverts from. The gap sentence says which
  way. No new gate is added. Falsifier: a page whose screen value crosses its spot only because
  of that pairing, against the median-margin multiple read beside it.
- **The current can be a percentile extreme** (SMPL: the 0th percentile, stated in its lease
  line). As in 3a, no threshold is added.
- **No page carries this yet.** The page refresh waits for the operator's preview approval AND
  for coordinator A's open page PRs (#1098, #1100, #1102) to land.
