---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 3 OF 5 (W27 follow-up, STATE row 41 (a)): 23 valuation, anchor, EV-gap, lease and consensus test files read the cut or walk the roster, every assertion unchanged but one read through another page reader; nine invariants now hold on every covered page with the property, each measured first; the scan's named-living-page pairs fall 423 → 307 (83 → 62 files) ($0)

**WHAT.**
- **Slice 3 of the plan A approved on 2026-11-17** (slice 1:
  `docs/records/2026-11-17-pins-off-living-pages-slice-1.md`). It reads through slice 1's cut and
  `tests/frozen_support.py`.
- **To the cut.** These read a page by name as a host for a frozen fixture, a value, or a page's
  own shape:
  - `test_lease_basis`, whose `_doc` is the host for every frozen lease-basis fixture;
  - `test_valuation_basis`'s named AMZN, BRBR and NFLX reads, and `_r4_page`'s default;
  - `test_ev_gap_render`'s named folders (its corpus lists still read the living pages, now
    through `_living_gapj`);
  - `test_ev_ebitda_basis` (TJX, LLY, and the parametrized ex-lease cases);
  - `test_ev_gap_routing`'s cells, and its fleet split's two named routes (VITL, SMPL);
  - `test_anchor` (AMZN's mid-cycle gap, EPAM's negative, WLK's basis check);
  - `test_peer_capital_intensity`'s grid, a network test outside the offline suite;
  - `test_consensus_transform`'s host;
  - `test_forward_multiples_and_basis`, `test_ev_gap` (EPAM's spans), `test_ev_bridge`,
    `test_forward_consensus`, `test_pe_eps_basis`, `test_forward_layers_basis`,
    `test_forward_multiple_history`, `test_anchor_point_in_time_shares`,
    `test_net_debt_securities_leg`, `test_multiples_vintage`, `test_net_debt_one_builder`,
    `test_share_basis` and `test_ebitda_recon`.
- **To the roster.** Each states an invariant every page with a property must meet, so it walks all
  of them. Each population was measured before the move and holds on every page in it:
  - every exit share count is the basic count: AMZN, UBER and BRBR → the 21 covered pages
    stating one;
  - today's multiple at its snapshot and at the page price: AMZN and UBER → every covered page
    tagged R4 (AMZN and UBER at the cut);
  - an immaterial-rent page carries no ex-lease figure: LLY, V and GOOGL → the 6 with an
    immaterial lease basis (BRBR, GOOGL, IT, LLY, V, VRRM);
  - a living page prints its gap's shape at its anchor year: SMPL → the 5 with a computed shape
    (BRBR, EPAM, IT, SMPL, WERN);
  - the stored anchor base value recomputes from its own inputs: IT → the 16 with an applicable
    R1 anchor;
  - the one-family peer median: MCK, AMZN, TGT and BURL → all 26 with the block;
  - the nearest year both metrics carry: SMPL's living page → the 24 with both levels;
  - a re-assembly would not lose a persisted gap: SMPL, EPAM and IT → the 5 with a computed,
    decomposed gap (BRBR, EPAM, IT, SMPL, WERN). It walks LIVING pages because the transform reads
    the page's own record and export, and a frozen page beside a newer record would mix two
    vintages (CLAUDE.md, derived-pin source layers). Its per-page CIQ skips became per-page
    `continue`s, and it skips only when no page could verify its vintages. A partial check warns,
    naming each page it could not verify, so one verified page does not read as five (review of
    this slice: on main each name skipped in its own parametrized case).
- **CIQ-paired refresh pins run on their page's exports.** `test_forward_multiple_history`'s two
  refresh pins and `test_ev_bridge`'s pair the page with CIQ exports, and each transform writes
  only from the exports the page names: the quarterly Financials its bands stamp, and for the
  bridge also the Estimates its `forward_consensus` stamps. The frozen page takes its bundle from
  `skip_unless_export(..., <the page's own sha256>)`, and the store the transform reads points at
  that bundle's folder: the folder's own export while it is the page's, else the archived folder
  that holds it (`ciq-archive/replaced-<date>/`, kept by the operator at each re-export). The
  bridge also requires that folder's Financials to be the bands'. Each skips, naming both sha256s,
  only when no folder holds the page's exports. Run in scratch with the live folder missing the
  export and a stand-in archive holding AMZN's: all three passed, reading the archive. (Found in
  slice 2's review, where the same gate had skipped after any re-export.) The bridge also finds a
  Financials-only re-export: the live folder then holds the page's Estimates beside another
  Financials, and the archived folder holding the bands' Financials serves, if its Estimates are
  the page's too (this slice's review).
- **Both twins on one vintage.** `test_anchor_point_in_time_shares`'s web twin read the living
  `frontend/dossiers/` mirrors of TJX and LLY, which no longer match the cut its markdown twin
  reads. It now renders the cut's pages too (this slice's review).

**WHY.** A retirement re-points every test reading the retired name's living page by name (STATE
row 41 (a)). This slice moves that cost off the valuation group, which had the most value pins
(76 of the 208 value pairs at main `8a71a383`).

**HOW VERIFIED.**
- **No assertion changed.** `python scripts/asserts_unchanged.py 8a71a383` (main, with slice 1
  merged) over 23 files and 432 functions: 0 changed, 0 disabled, 0 vanished; 1 reader-only
  (`test_valuation_basis::test_the_ids_and_formulas_are_the_engines`, `_page("BRBR")` →
  `frozen_doc("BRBR")` inside the assert, the READER category #1098 added); 8 population (the
  walks above); and 1 control, `test_consensus_parity`'s per-page `continue`s (above), an exit
  added by design. Mutation: the same assert reading `frozen_doc("BURL")` is CHANGED, and the
  checker exits 1.
- **Each walk was run on every page it walks before it moved** (the populations above). No page
  failed one.
- **The files.** The 23 changed files, offline, with the CIQ link present: 722 passed, 24 skipped,
  15 failed. Main `8a71a383` with the same link fails the same 15 (the mislabelled PARR workbook,
  re-exported CIQ data) and passes 724. The two fewer items are `test_consensus_parity`'s three
  parametrized cases, now one walk: 10 → 8 collected, and no other file's count moves.
- **The scan** (`named_page_pins.py HEAD`, against main at `8a71a383`): 423 → 307 pairs (value
  208 → 132, invariant 215 → 175), 366 → 274 functions, 83 → 62 files. Left in these files: a
  `tmp_path` writer (`test_lease_basis`) and the fleet split's subscript keys
  (`test_ev_gap_routing`), whose named routes now read the cut. Both are scan false positives, for
  slice 5.
- **The suite.** {SUITE}
- **The impact check.** {IMPACT}

**BOUNDARY.**
- **Counts:** at this slice's commit, against main at `8a71a383` (slice 1 merged as #1098).
- **"Pages":** the roster's 26 covered names at the cut.
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`, a lower bound.

**WHAT REMAINS (slices 4–5).** Dossier render and refreshes, then propose, templates and triggers,
the proof, the ratchet and STATE row 41.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A walk's floor fails loud** when the last covered page with its property leaves (A's ruling).
   An R4 walk with AMZN and UBER both retired is the nearest case. Falsifier: a walk passes on an
   empty population.
2. **CIQ-paired refresh pins skip when neither the folder nor `ciq-archive/` holds their page's
   exports.** Falsifier: one skips while either holds them.
3. **The checker cannot see a skip inside a helper.** `_the_bands_export` and `_the_pages_exports`
   skip from inside a function the test calls, so `asserts_unchanged.py`'s "0 disabled" does not
   cover them. Slice 5 teaches it the repo's skip helpers.
4. **`test_ev_bridge`'s `if not step(before): pytest.skip(...)` now guards only a transform
   regression**, since the gate above it guarantees the page's exports. It hid one on main in the
   same form. Left for a follow-up: as an assertion it would change what the test asserts.
5. **$0.**
