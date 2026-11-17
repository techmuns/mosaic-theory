---
id:
status: shipped
date: 2026-11-17
prs: [1107]
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 3 OF 5 (W27 follow-up, STATE row 41 (a)): 23 valuation, anchor, EV-gap, lease and consensus test files read the cut or walk the roster, every assertion unchanged but one read through another page reader and the fleet split's two named routes, now read off the cut into their own map; seven invariants now hold on every covered page with the property, each measured first, and a refresh keeps every watch page's frozen line; the scan's named-living-page pairs fall 423 → 307 (83 → 62 files) ($0)

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
  - the nearest year both metrics carry: SMPL's living page → the 24 with both levels.
- **Kept on the living page, by name: the record class** (A's option (1)).
  `test_consensus_parity::test_a_re_assembly_would_not_lose_a_persisted_gap` stays parametrized on
  SMPL, EPAM and IT, as on main. `ev_gap_transform` reads each name's LIVING scenario record beside
  its page, so the pin is a page-and-record pair. Round 0 made it a walk of the 5 decomposed pages,
  whose per-page `continue`s the checker read as CONTROL; A's review, round 1, reverted it, and
  slice 5's record writes up the class.
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
  Financials, and EVERY archived folder holding the bands' Financials is searched for one whose
  Estimates are the page's too (this slice's reviews: the second found that taking only the first
  such folder skipped after an Estimates-only re-export followed by a Financials-only one, while a
  later archived folder held both; replayed in scratch on AMZN's real exports, the first-folder
  helper skipped and this one ran on that later folder). For that search the shared
  `tests/ciq_export_support.py` gains `archived_bundles`, every archived folder holding an export,
  and `archived_bundle` becomes its first, its behaviour unchanged (`test_ciq_export_support`
  passes, 18 of 18).
  **Round 1.** Each helper now builds the live bundle itself, None with no live folder. The pins
  first built it with `_bundle`, which skipped, naming no sha256, before the archive was searched.
  So with no live AMZN folder, a retirement's likeliest state, they skipped where the archive held
  the page's exports (A's review, round 1). `ciq_export_support.retired_checkout` stages that
  state: a scratch checkout whose CIQ folder holds no AMZN, with every folder this machine holds
  for AMZN linked under `ciq-archive/`, never copied.
  `test_the_amzn_pins_run_from_the_archive_when_no_live_folder_holds_the_name` (both
  forward-multiple pins) and `test_ev_bridge`'s
  `test_the_refresh_pin_runs_from_the_archive_when_no_live_folder_holds_the_name` run each pin
  there. Each failed on the round-0 helpers, skipped by `_bundle`, and passes.
  **A band or a page with no export stamp now fails the pin, where it skipped** (Codex, P2). Read
  as the string "None", a missing stamp named an export no folder holds.
  `test_a_band_with_no_export_stamp_fails_the_pin_and_never_skips_it` and
  `test_a_page_with_no_export_stamp_fails_the_pin_and_never_skips_it[bands|estimates]` failed
  first and pass.
- **The forward-multiple refresh pin's scratch tree carries the roster** (A's ruling on the #1100
  flag). `_copy_page` builds a data tree holding the real `coverage_roster.jsonl` and
  `watch_defects.json` beside its dossiers, because the renderer reads both from there (#1100).
  "The refresh moved nothing" is measured against the page's own re-render in that tree, never the
  cut's md, which an older renderer wrote.
  `test_watch_frozen_line::test_a_refresh_keeps_every_watch_pages_line_and_its_defects_e2e` walks
  every watch page (15) through a refresh in such a tree. Each keeps its line once, above the
  Brief, with each defect bound to it. Its no-roster version fails on AMZN ("a refresh dropped the
  watch line").
- **Both twins on one vintage.** `test_anchor_point_in_time_shares`'s web twin read the living
  `frontend/dossiers/` mirrors of TJX and LLY, which no longer match the cut its markdown twin
  reads. It now renders the cut's pages too (this slice's review).
  `test_ev_ebitda_basis::test_the_web_states_the_same_lines_e2e` too (A's review, round 1). Its JS
  driver read the living mirrors of TJX and NFLX by name, while its md siblings read the cut. A
  web mirror is its page's `dossier.json`, byte for byte, so the driver reads the cut's.
  `test_the_web_twin_runs_in_a_checkout_with_no_mirror_of_its_pages` runs it in a checkout whose
  `frontend/dossiers/` holds neither mirror. It failed on the round-0 driver and passes. **A scan
  blind spot:** `named_page_pins.py` reads no path built inside a JS driver string
  (`frontend/dossiers/${t}.json`), so it never counted this read. Slice 5 adds it.
- **The fleet split's named routes, in their own map.**
  `test_ev_gap_routing::test_every_name_routes_and_the_split_is_the_measured_one` round 0
  overwrote the living walk's `got["VITL"]` and `got["SMPL"]` with the cut's routes. So
  `got["SMPL"] == Route.FULL` read the cut while it named the walk, and "VITL's living page
  carries…" could not fail (A's review, round 1). The cut's routes now go in `cut`, and `got`
  keeps the living fleet's. No outcome moves, so no test can fail first. MVST's frozen route keeps
  `got` non-empty on main too, and SMPL's FULL is read off the cut at both rounds. The checker
  reads the assertion as CHANGED, which round 0's overwrite hid from it.

**WHY.** A retirement re-points every test reading the retired name's living page by name (STATE
row 41 (a)). This slice moves that cost off the valuation group, which had the most value pins
(76 of the 208 value pairs at main `8a71a383`).

**HOW VERIFIED.**
- **The checker.** `python scripts/asserts_unchanged.py origin/main` (main `2f85a6f2`, merged)
  over 24 files and 479 functions: 0 disabled, 0 control, 0 vanished; 1 reader-only
  (`test_valuation_basis::test_the_ids_and_formulas_are_the_engines`, `_page("BRBR")` →
  `frozen_doc("BRBR")` inside the assert, the READER category #1098 added); 7 population (the
  walks above); 1 changed, the fleet split's named routes (above); 13 new. Round 0, against
  `8a71a383`, read 0 changed and 1 control, `test_consensus_parity`'s walk, which round 1
  reverted. Mutation: the reader-only assert reading `frozen_doc("BURL")` is CHANGED, and the
  checker exits 1. Slice 5's checker, which follows a skip into a helper to any depth and compares
  skips by what they call, reads 3 disabled (cost 3).
- **Each walk was run on every page it walks before it moved** (the populations above). No page
  failed one.
- **The files.** The 23 changed test files, offline, with the CIQ link present, at round 1's
  merged head: 15 fail. Main `2f85a6f2` with the same link fails 16 of the same files' tests: the
  same 15 (the mislabelled PARR workbook, re-exported CIQ data) and
  `test_forward_multiple_history::test_the_refresh_lands_the_layer_and_moves_nothing_else`, the
  no-roster refresh pin that round 1's data tree fixes (A's review, round 1). At round 0 the same
  files read 740 passed and 15 failed, against main `8a71a383`'s 724 passed and the same 15.
- **The scan** (`named_page_pins.py HEAD`, against main; main reads 423 at `8a71a383` and at
  `2f85a6f2`): 423 → 311 pairs (value 208 → 135, invariant 215 → 176), 366 → 276 functions, 83 →
  64 files. Round 0 read 307 / 274 / 62. Round 1 adds 4 pairs: the consensus pin's 3 (SMPL, EPAM,
  IT), back on its named living pages as record-class residue, and a scan false positive, the
  forward-multiple refresh pin's `tmp_path` data tree (`data/dossiers/AMZN`). Left in these files:
  those, a `tmp_path` writer (`test_lease_basis`) and the fleet split's subscript keys
  (`test_ev_gap_routing`), whose named routes now read the cut. The false positives are for
  slice 5.
- **The suite, at round 0.** The full offline suite (`-m "not network" -n 8`, the CIQ folder
  linked) at `3b4e7c08`, against the same run of main `8a71a383` on the same machine: **74 → 80 failing**.
  Every one of main's 74 is a local-data failure CI does not run. Of the differences:
  - named noise: `test_records_ledger` (this record's PR number, filled once the PR opened) and
    `test_transcript_run_guard`, 4 new and 4 gone (a different subset of its cases on every run);
  - `test_claude_hooks` ×3 and `test_fix_log` ×2, files this slice does not touch. Run alone they
    pass, 104 of 104, on this tree and on main. The run took 55 minutes, against main's 15,
    while another session's suite and this slice's review ran beside it.
- **The impact check.** `python -m vinci.impact run --base origin/main --head HEAD` at
  `fc764178` (round 1, main `2f85a6f2` merged): 0 of 791 tests fail on base code and pass on head
  code (536 pass at both, 255 skipped), and `verify` reads VALID. At round 0 (`e6bdc5b3`) it read
  0 of 761. The PR body carries the report.

**BOUNDARY.**
- **Counts:** at this slice's commit, against main at `8a71a383` (slice 1 merged as #1098), or at
  round 1 against main `2f85a6f2`, as each names.
- **"Pages":** the roster's 26 covered names at the cut.
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`, a lower bound.

**WHAT REMAINS (slices 4–5).** Dossier render and refreshes, then propose, templates and triggers,
the proof, the ratchet and STATE row 41.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A walk's floor fails loud** when the last covered page with its property leaves (A's ruling).
   An R4 walk with AMZN and UBER both retired is the nearest case. Falsifier: a walk passes on an
   empty population.
2. **CIQ-paired refresh pins skip when neither the folder nor `ciq-archive/` holds their page's
   exports.** Falsifier: one skips while either holds them, with or without a live folder.
3. **The checker could not see a skip inside a helper, nor one skip traded for another.**
   `_the_bands_export` skips only through `skip_unless_export`, and `_the_pages_exports` itself,
   inside functions the test calls; `asserts_unchanged.py` counted neither. Slice 5's checker
   reads this slice as **3 disabled**, where round 0 here said 1 (A's review, round 1):
   `test_ev_bridge::test_the_refresh_lands_the_layer_only_from_the_pages_own_exports`, and
   `test_forward_multiple_history`'s `test_the_refresh_lands_the_layer_and_moves_nothing_else` and
   `test_a_page_that_cannot_name_this_export_is_left_alone`. On main a drift between the folder's
   exports and the page's FAILED each. Here each SKIPS behind its export gate, naming the sha256s,
   by design (cost 2).
4. **`test_ev_bridge`'s `if not step(before): pytest.skip(...)` now guards only a transform
   regression**, since the gate above it guarantees the page's exports. It hid one on main in the
   same form. Left for a follow-up: as an assertion it would change what the test asserts.
5. **The anchor-base walk's filter restates main's named precondition** (A's review, round 1).
   `test_anchor::test_backfilled_anchor_base_consistent_with_stored_inputs` asserted on main that
   IT's anchor is R1 and applicable, and failed when it left R1. The walk's filter is now that
   test, so IT leaving R1 drops out of the walk silently, and only its floor of 1 holds.
   Falsifier: a page's anchor leaves R1, the walk stays green, and nothing names the page.
6. **$0.**
