---
id: 2026-11-04-ciq-workbook-tests-skip-when-the-export-is-not-theirs
status: shipped
date: 2026-11-04
prs: [889]
supersedes:
superseded-by:
---

# The CIQ-workbook tests skip, naming both sha256s, when the export on disk is not the one their expectation came from

**WHAT.** The agent half of STATE §5.0 row 32 item (28). With the operator's Drive CIQ folder
linked, eight offline tests failed on main `9e996d7f` with nothing broken: SMPL's and NCNO's
exports in Drive are 2026-10-28's while their pages were assembled in August, and NFLX's export
carries FQ3 2026, which its pin predates. They now SKIP with a reason that names both sha256s, and
they still run, and still catch their defect, on the export their expectation came from.

One shared helper, `tests/ciq_export_support.py`, hashes the workbook `CiqBundle.workbook` picks
with `ciq_sheets.file_provenance` (the first 10 hex digits of the sha256, the form every page stamp
takes). It has two checks, one for each kind of expectation:

- **`skip_unless_pages_export`** is for a comparison with the committed page. It runs only on the
  export the page records (`forward_consensus.source_sha256`, the stamp `ev_bridge_transform`,
  `historical_forecast_error_transform` and `ciq_currency_transform` already check before they
  write from the folder). With no export on disk it does nothing, so a machine without the folder
  runs exactly what it ran before. A page that records no export FAILS the test.
- **`skip_unless_export`** is for a value pinned from one export. It runs only on that export's
  sha256. This is the TEST-LAYER rule's frozen fixture, frozen by identity because licensed bytes
  cannot be committed.

| Test | What depends on the export | Check | What still runs on any export |
|---|---|---|---|
| `test_consensus_parity::test_a_re_assembly_would_not_lose_a_persisted_gap[SMPL]` | the ev_gap vintages | page (Estimates) | status, ratios |
| `test_ev_gap_transform_idempotent::test_a_second_refresh_preserves_the_computed_gap[SMPL]`, `[NCNO]` | the ev_gap vintages, now checked LAST | page (Estimates) | status, ratios, shape, the third pass |
| `test_materiality::test_the_defect_itself_the_extraction_drops_the_line` | the −391.9 LTM magnitude | frozen: SMPL annual Financials `049150fb62` | the writedown row surfaces |
| `test_guidance_point_refusal::test_nflx_fq2_2026_reads_at_guide_not_missed` | FQ2 2026 as the most recent call | frozen: NFLX Estimates `406592d103` | the record discloses at-guide calls |
| `test_consensus_rows::test_revenue_resolves_on_every_name[SMPL]` | first forward FY, median, pair | the file's own vintage rule | Revenue resolves |
| `test_consensus_transform::test_the_levels_reach_the_written_dossier[SMPL]` | first forward FY, median, pair | the file's own vintage rule | the levels land, forward years only |
| `test_consensus_rows::test_the_block_is_selected_by_value_not_by_position` | the FY2026 figures | the file's own vintage rule | — |

**WHY.**

- **The page-keyed three are page comparisons.** `ev_gap_transform` re-reads `consensus_as_of`
  off the Estimates export on disk and keeps the rest of the gap from the stored page. So the
  vintage matches the page's only on the page's export. On the 2026-10-28 exports it read
  ≥2026-10-27 against the pages' ≥2026-07-21 (SMPL) and ≥2026-07-22 (NCNO).
- **NFLX is frozen by sha, not keyed on the page.** NFLX's page is current: its recorded
  Estimates export `a1a68bc0b2` is the one on disk. A page key would therefore still fail, because
  "most recent" is FQ2 2026 only on an export pulled before FQ3 2026 reported (2026-10-20). The
  pin was written 2026-08-13 (#443) against an August export that no folder on this machine still
  holds. `406592d103` is the export of 2026-10-07 that NFLX's page was built from at #704
  (`forward_consensus.source_sha256` at `78abb62e`), archived by the operator in Drive under
  `manual/ciq-archive/replaced-2026-10-28/`. The pin holds on it. A committed frozen fixture of
  the sheet is not an option, because raw CIQ tables are never committed. The refusal is already
  pinned on frozen rows with NFLX's FQ2 figures
  (`test_a_point_call_inside_the_band_is_refused_and_named`), so the skip loses no value pin.
- **Materiality is frozen by sha too.** −391.9 is one export's LTM column. `049150fb62` is the
  annual Financials SMPL's page was built from: its revenue and operating cash flow reproduce the
  page's annual table, 22 of 22 figures (the #805 proof, `statement_recon.ciq_figures` against
  `table_figures`). The 2026-10-28 export closed fiscal 2026 and carries the writedown as −60.9
  and −331.0 in two columns. The row still surfaces, and that check still runs ungated.
- **The three `REVENUE_BASELINE` pins keep the file's own vintage rule, not the page key.** They
  pin a baseline, not a page, and the file already has a shared rule for when the baseline is
  current (`data_vintage` against each row's verified-at date). A page key would be wrong here.
  AORT's page export is the one on disk (`16630136ba`), but that export's data is ≥2026-10-19
  against a baseline verified 2026-06-30, so a page key would run AORT's median pin against a
  re-pulled export. The failing assertion was the first forward FY, which sat ABOVE the vintage
  gate on the reasoning that brokers do not move it. True, but the calendar does: SMPL's fiscal
  2026 closed, and its export opens at FY2027. The assertion moves under the gate, beside the
  median and the pair, and the skip prints what it reads now. The block-selection case had no
  gate at all and gets the same one.

**HOW VERIFIED.** All runs on this machine, 2026-11-04, `pytest -m "not network"`. "Live" is the
Drive folder as it stands. "Pages' exports" is a scratch CIQ root identical to live except that
SMPL, NCNO and NFLX point at `manual/ciq-archive/replaced-2026-10-28/` (SMPL `06670995ba` /
`e41ebc16a4` / `049150fb62`, NCNO `f08e783c6d` / `4279cbed71`, both matching every stamp their
pages carry; NFLX `406592d103`).

- **On main `9e996d7f`, pages' exports:** all 8 pass. The archive reproduces every pin, so the
  newer exports were the only cause.
- **On this branch, the 8 tests:**
  - Live: 8 skipped, each reason naming the page's or the pin's sha256 and the one on disk (SMPL
    Estimates `c50fddc012` vs `06670995ba`; NCNO `bbafd3d81b` vs `f08e783c6d`; NFLX `a1a68bc0b2`
    vs `406592d103`; SMPL annual `c05a220538` vs `049150fb62`; the vintage gates ≥2026-10-27 >
    2026-07-21).
  - Pages' exports: 8 passed.
  - No folder: the same 6 skips as main, with the same reasons, and the 2 ev_gap tests pass.
- **Mutations of production code, each run on the pages' exports, each reverted:**
  - M1, the consensus vintage's floor marker stripped in `ev_gap_transform`: parity[SMPL],
    idempotent[SMPL] and [NCNO] fail. On the LIVE folder, M1 still fails 8 test ids across the 6
    names whose export IS the page's (parity EPAM, IT; idempotent AORT, BRBR, EPAM, IT, MVST,
    WERN), and only SMPL and NCNO skip.
  - M2 + M2b, block selection by position (no value check, last title wins): the
    block-selection test and both baseline tests fail.
  - M3, the forward window off by one (`< current_fy - 1`):
    `test_revenue_resolves_on_every_name[SMPL]` fails on the first-FY assertion that moved under
    the gate ("first forward year 2025, expected 2026"). The transform test fails one step
    earlier, on its ungated forward-years-only check.
  - M4, the surfaced unusual items at 1/1000 scale: materiality fails on the frozen magnitude.
  - M5, `_POINT_DECISION_BAND = 0.0`: NFLX fails.
- **The helper's own pins** (`tests/test_ciq_export_support.py`, 9 tests): constructed export
  files and SMPL's real committed page. They run in CI, and cover:
  - the page's export running, and another export skipping with both sha256s named;
  - no export on disk doing nothing;
  - a page with no stamp failing loud;
  - a frozen pin running only on its own export;
  - the configured-folder path the parity and ev_gap tests use;
  - an unhashable export failing rather than reading as absent;
  - a kind no page stamps being refused without the folder.

  A positive pin cannot pass by skipping. With both helpers forced to always skip, the two
  positive pins FAIL; before review round 0 they would have read as skipped.
- **Review round 0** (`/code-review high --fix`, 8 findings):
  - FIXED: findings 1–4. Positive pins wrap their call so a wrongful skip fails. An unhashable
    export fails rather than reading as absent. An unknown kind is refused before the disk is
    read. The folder-lookup path has a pin.
  - FIXED: the frozen-pin skip said "drawn from" where it should say "verified on" (from finding
    5). NFLX's pin was written on an August export and is verified on `406592d103`.
  - DISMISSED: the rest of finding 5. It also asks for a time-independent rewrite, but "most
    recent" depends on the export by design, and the pin runs wherever the archived export is
    linked (shown above).
  - DISMISSED: finding 6, the third inline copy of the vintage gate. Consolidating is a refactor,
    and identity-keying a baseline is wrong (AORT, above).
  - DISMISSED: findings 7 and 8, an extra folder read per test. That costs I/O only.
- **Full suite, both ways, branch `5550b738` against main `9e996d7f`:** `pytest -m "not network"
  -rs`, each run in its own checkout of that commit, run in parallel on 2026-11-04. None of the
  checkouts had a local store (`data/vinci.db`).

  | Folder | main `9e996d7f` | branch `5550b738` |
  |---|---|---|
  | Live | 14 failed, 9163 passed, 82 skipped | 6 failed, 9169 passed, 90 skipped |
  | None | 0 failed, 8709 passed, 550 skipped | 0 failed, 8715 passed, 550 skipped |

  Each run also deselected 39 network tests and recorded 8 xfailed.

  - **Live:** exactly the 8 moved from failed to skipped. The +6 passed are the helper's own pins,
    so nothing that passed on main now skips.
  - **None:** the +6 passed are the same 6 pins, and the 550 skip reasons are identical line for
    line once line numbers are stripped.
  - **The 6 left on the branch:** AORT's bridge (`test_ev_bridge.py::test_claims_equal_ciqs_
    current_figure_on_every_committed_name`), GOOGL's and LLY's 2% Consensus-vs-Trends check, and
    three AMZN tests, below.
  - **`test_store_freshness`** skips in these checkouts ("no local store in this worktree"). That
    is why main reads 14 here: the brief's 12, less that one, plus the three AMZN tests.

**BOUNDARY.** "Eight", "twelve" and "fourteen" are test ids in the offline suite (`-m "not
network"`) on main `9e996d7f`, with the Drive folder as it stood 2026-11-04 (37 ticker folders).
"Twelve" is the brief's count, in a checkout with a local store. "Fourteen" was measured here, in
a checkout with none. Every sha256 is the
10-hex prefix `file_provenance` returns, read 2026-11-04. The 8 test ids under M1 are
parametrizations of two tests on the live folder: parity (SMPL, EPAM, IT) and idempotent (the 8
committed pages whose ev_gap is computed: AORT, BRBR, EPAM, IT, MVST, NCNO, SMPL, WERN), less the
3 that skip (SMPL twice, NCNO once).

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The first-forward-FY check no longer runs on an export newer than its baseline.** On the live
  folder that is 6 names that ran it and passed before (AORT, BRBR, CNXC, EPAM, FUBO, NCNO), each
  against a pin its export no longer had to carry. Re-pinning `REVENUE_BASELINE` on current
  exports restores it; each skip prints the re-pin tuple.
- **The two frozen pins run only where the archived export is linked.** NFLX and materiality skip
  on every current folder. What else still runs: NFLX's frozen-rows unit pin and record check, and
  materiality's row-surfaces check. Re-pinning either on a current export would restore it. That
  is a new pin, and not this change.
- **The page key is `forward_consensus.source_sha256`.** `forward_consensus_transform` writes it
  from whatever export is on disk, with no identity check. So strictly it names the export the
  forward layer was read from. For SMPL and NCNO that is the assembly export (the archive
  reproduces every stamp), and the production transforms make the same assumption.
- **Not changed, reported:**
  - **Three more failures of the same class, on AMZN, fail on main `9e996d7f` with the folder
    linked and were not in the brief's twelve.** They are
    `test_forward_multiple_history.py::test_the_refresh_lands_the_layer_and_moves_nothing_else`,
    `::test_a_page_that_cannot_name_this_export_is_left_alone` and
    `test_historical_forecast_error.py::test_the_refresh_lands_the_layer_only_from_the_pages_own_export`.
    AMZN's Drive export is 2026-11-02's (Estimates `1b971fda50`, quarterly Financials
    `796a53f316`), while main's AMZN page stamps `e10ed62223` / `e5abf9d69d`. #886 re-assembles
    AMZN onto exactly the export on disk (its page stamps `1b971fda50` / `796a53f316`), so they
    clear when #886 merges. Unlike `test_ev_bridge`'s AMZN refresh test, they assume rather than
    check that the export is the page's. `skip_unless_pages_export` would make that explicit; it
    was left out because the brief named eight.
  - `ev_gap_transform`, run on a page with a newer Estimates export on disk, writes that export's
    consensus vintage beside the page's stored levels. That is a vintage that does not describe the
    numbers. Today only assembly calls it (`vinci/dossier/assemble.py:1194`, from `grep -rn
    ev_gap_transform vinci`), and assembly reads the export it assembles from, so no committed page
    is affected. The refresh path reaches it only from tests.
  - `test_the_block_is_selected_by_value_not_by_position` cannot see value selection replaced by
    position on SMPL's export. M2 alone survived, because the consensus block is also the first
    `Revenue` title there. It catches position selection only where position picks another block
    (M2b).
- **Left for the operator (row 32 (28)):** AORT's half-refreshed folder, the GOOGL and LLY
  Consensus-vs-Trends 2% check, and `test_store_freshness`.
