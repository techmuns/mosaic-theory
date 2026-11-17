"""THE RATCHET: no test reads a LIVING page by name unless it is named here, with its reason (W27
follow-up, STATE row 41 (a), slice 5).

A retirement should edit no test. Slices 1–5 moved every value pin that read a living page by name
onto the cut (`tests/frozen_support.frozen_doc`) and every invariant onto a roster walk
(`covered_where`). What remains is RESIDUE, each pair named in `RESIDUE` below with its reason:

- the RECORD class: a page read beside that name's LIVING record (`scenarios/<T>.json`, a monitor
  record, `graph_coverage.json`), which a frozen page would pair with a newer record, two
  vintages (A's option (1), 2026-11-17);
- a test that watches the LIVING page by design (a tripwire awaiting a re-read, a live sentence);
- a scan FALSE POSITIVE the AST cannot tell from a read: a scratch checkout's path strings, a
  path string handed to a classifier, a read of history, a helper pointed at the cut by a fixture.

`test_no_test_reads_a_living_page_by_name_unless_it_is_named` fails on a NEW pair (move it, or
name it here with its reason) and on a pair named here that the scan no longer finds (delete the
entry: the ratchet only shrinks). An entry for a name with no living page is never stale, so a
retirement edits nothing here either.

THE SCAN IS A LOWER BOUND (`scripts/named_page_pins.py`): a read it cannot see (a ticker built at
run time, a page reached through a module outside `tests/`) passes this ratchet. Passing proves the
scan finds nothing new, never that no test names a living page. The proof is a retirement replayed
with the whole suite (slice 5's record).

The other pins hold each rule of the scan, a positive and a negative, on fixture sources whose
tickers (AAA, BBB) are no committed page, so this file is not itself a read.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _scanner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_named_page_pins", ROOT / "scripts" / "named_page_pins.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


NAMES = {"AAA", "BBB"}


def _pairs(sources: dict[str, str]) -> set[tuple[str, str]]:
    npp = _scanner()
    out: set[tuple[str, str]] = npp.pairs(npp.scan_sources(sources, NAMES))
    return out


def _one(src: str) -> set[tuple[str, str]]:
    return _pairs({"tests/test_x.py": src})


HEAD = 'import json\nfrom pathlib import Path\nDOSS = Path("data/dossiers")\n\n\n'


# --- the rules, each read counted and each look-alike not --------------------------------------


def test_a_named_read_is_counted_and_a_tmp_tree_is_not() -> None:
    """(+) `DOSS / "AAA"` is a read; (−) the same path rooted in `tmp_path`, or in a name assigned
    from it, is a scratch tree the test writes (slices 1–4's commonest false positive)."""
    assert _one(HEAD + 'def test_a():\n    (DOSS / "AAA" / "dossier.json").read_text()\n') == {
        ("tests/test_x.py::test_a", "AAA")}
    assert not _one(HEAD + 'def test_a(tmp_path):\n'
                    '    (tmp_path / "data" / "dossiers" / "AAA").mkdir(parents=True)\n'
                    '    data = tmp_path / "data"\n    (data / "dossiers" / "BBB").mkdir()\n')


def test_a_tmp_name_in_one_function_is_not_another_functions() -> None:
    """(+) `root` assigned from `tmp_path` in one test does not make another test's own `root`,
    bound to the repository, a scratch tree: that test's read still counts; (−) the first test's
    tmp-rooted path is still not a read."""
    src = HEAD + ('def test_a(tmp_path):\n    root = tmp_path / "x"\n'
                  '    (root / "data" / "dossiers" / "BBB").mkdir(parents=True)\n\n\n'
                  'def test_b():\n    root = Path(".")\n'
                  '    (root / "data" / "dossiers" / "AAA" / "dossier.json").read_text()\n')
    assert _one(src) == {("tests/test_x.py::test_b", "AAA")}


def test_a_helper_every_call_hands_a_tmp_directory_is_a_scratch_writer() -> None:
    """(−) `_copy(t, root)` called only with `tmp_path` writes a scratch tree; (+) the same helper
    called once with the repository's own root reads the living page, so it still counts."""
    helper = HEAD + 'def _copy(t, root):\n    return root / "data" / "dossiers" / t\n\n\n'
    assert not _one(helper + 'def test_a(tmp_path):\n    _copy("AAA", tmp_path)\n')
    assert _one(helper + 'def test_a(tmp_path):\n    _copy("AAA", tmp_path)\n\n\n'
                'def test_b():\n    _copy("BBB", Path("."))\n') == {
        ("tests/test_x.py::test_a", "AAA"), ("tests/test_x.py::test_b", "BBB")}


def test_a_git_object_path_and_a_docstring_are_not_reads() -> None:
    """(−) `f"{rev}:data/dossiers/AAA/…"` is the page at a commit, and a docstring naming a page is
    prose; (+) the same path as a plain literal is a read."""
    assert not _one(HEAD + 'def test_a(rev):\n    """Reads frontend/dossiers/AAA.md, in prose."""\n'
                    '    run(["git", "show", f"{rev}:data/dossiers/AAA/dossier.json"])\n')
    assert _one(HEAD + 'def test_a():\n    Path("data/dossiers/AAA/dossier.json").read_text()\n') \
        == {("tests/test_x.py::test_a", "AAA")}


def test_heads_own_object_is_the_living_page() -> None:
    """(+) `git show HEAD:data/dossiers/AAA/…` reads the page as committed at HEAD, which IS the
    living page, so it counts (code review of slice 5); (−) another revision's object does not."""
    assert _one(HEAD + 'def test_a():\n'
                '    run(["git", "show", "HEAD:data/dossiers/AAA/dossier.json"])\n'
                '    run(["git", "show", "4889ddba:data/dossiers/BBB/dossier.json"])\n') == {
        ("tests/test_x.py::test_a", "AAA")}


def test_a_web_mirror_and_a_javascript_template_are_reads() -> None:
    """(+) `frontend/dossiers/AAA.json` is the page's living mirror, and a node driver's
    `dossiers/${t}` over a quoted list reads each name it quotes (#1107's EV/EBITDA twin, which the
    first scan could not see); (−) a driver reading the cut by path is not a read."""
    assert _one(HEAD + 'def test_a():\n    Path("frontend/dossiers/AAA.json").read_text()\n') == {
        ("tests/test_x.py::test_a", "AAA")}
    driver = ('def test_a(dj):\n    js = f"""\nconst {{ r }} = await import("{dj}");\n'
              'for (const t of ["AAA", "BBB"]) {{\n'
              '  r(readFileSync(`frontend/dossiers/${{t}}.json`));\n}}\n"""\n    run(js)\n')
    assert _one(HEAD + driver) == {("tests/test_x.py::test_a", "AAA"),
                                   ("tests/test_x.py::test_a", "BBB")}
    assert not _one(HEAD + 'def test_a():\n    run("readFileSync('
                    '\\"tests/fixtures/frozen_pages/cut-4889ddba/AAA/dossier.json\\")")\n')


def test_a_name_is_read_in_the_function_that_binds_it() -> None:
    """(−) `root` bound to a frozen copy in this function is not the `root` another function
    binds to `frontend/dossiers` (test_covenant_document_identity's false positive); (+) the
    other function's own read still counts."""
    src = HEAD + ('def test_a():\n    root = Path("frontend") / "dossiers"\n'
                  '    (root / "AAA.json").read_text()\n    (root / "AAA").exists()\n\n\n'
                  'def test_b():\n    root = Path("tests/fixtures/frozen_pages/2026-08-18")\n'
                  '    (root / "AAA" / "dossier.json").read_text()\n')
    assert _one(src) == {("tests/test_x.py::test_a", "AAA")}


def test_a_subscript_counts_only_on_what_the_function_filled_from_pages() -> None:
    """(+) `got["AAA"]`, filled in a loop over the living pages, reads AAA's; (−) `cut["AAA"]`,
    filled from a frozen copy in the same function, does not (#1107's fleet split)."""
    src = HEAD + ('def test_a():\n    got, cut = {}, {}\n'
                  '    for f in sorted(DOSS.glob("*/dossier.json")):\n'
                  '        got[f.parent.name] = json.loads(f.read_text())\n'
                  '    cut["BBB"] = frozen_doc("BBB")\n    assert got["AAA"] and cut["BBB"]\n')
    assert _one(src) == {("tests/test_x.py::test_a", "AAA")}


def test_a_support_modules_page_reader_counts_where_it_is_called() -> None:
    """(+) a `tests/` support helper whose parameter reaches a page path (`living_doc(T)`,
    `page_export_sha(T)`) charges the name to each test that calls it, by import or by module
    alias (slice 2's review: a read through `ciq_export_support`'s own ROOT was invisible);
    (−) a support helper that reads the cut charges nothing."""
    support = (HEAD + 'CUT = Path("tests/fixtures/frozen_pages/cut-4889ddba")\n\n\n'
               'def living(t):\n    return (DOSS / t / "dossier.json").read_text()\n\n\n'
               'def frozen(t):\n    return (CUT / t / "dossier.json").read_text()\n')
    test = ('from tests.support_x import frozen, living\nimport tests.support_x as sx\n\n\n'
            'def test_a():\n    living("AAA")\n    frozen("BBB")\n\n\n'
            'def test_b():\n    sx.living("BBB")\n')
    assert _pairs({"tests/support_x.py": support, "tests/test_x.py": test}) == {
        ("tests/test_x.py::test_a", "AAA"), ("tests/test_x.py::test_b", "BBB")}


# --- the ratchet --------------------------------------------------------------------------------

RECORD = "record class: the page beside its LIVING record; a frozen page would mix two vintages"
LIVING = "watches the LIVING page by design"
SCRATCH = "scan false positive: a path in a scratch checkout or tree the test writes"
CLASSIFIER = "scan false positive: a path string handed to a path classifier, never opened"
HISTORY = "scan false positive: pages read at a past commit; at head a missing file is skipped"
FIXTURE = "scan false positive: the helper reads the cut here, or refuses before any read"

#: Every (test, page) pair the scan may find, and why. Measured on slice 5's tree (W27), 69 pairs.
RESIDUE: dict[str, dict[str, str]] = {
    # the helper reads through `ces.ROOT`, which `_pages_at_the_cut` points at the cut, or is
    # handed its page, or refuses before it reads one
    "tests/test_ciq_export_support.py::test_a_kind_no_page_stamps_is_refused_without_the_folder":
        {"SMPL": FIXTURE},
    "tests/test_ciq_export_support.py::test_a_page_that_records_no_export_fails_loud":
        {"SMPL": FIXTURE},
    "tests/test_ciq_export_support.py::"
    "test_an_unreadable_export_fails_rather_than_reading_as_absent": {"SMPL": FIXTURE},
    "tests/test_ciq_export_support.py::test_another_export_than_the_pages_skips_and_names_both":
        {"SMPL": FIXTURE},
    "tests/test_ciq_export_support.py::test_the_folder_lookup_is_the_path_the_suite_uses":
        {"SMPL": FIXTURE},
    # `ev_gap_transform` reads each name's living scenario record (#1107, round 1)
    "tests/test_consensus_parity.py::test_a_re_assembly_would_not_lose_a_persisted_gap":
        {"EPAM": RECORD, "IT": RECORD, "SMPL": RECORD},
    # each renders the page with its `frontend/scenarios/<T>.json` record (slice 4)
    "tests/test_dossier.py::test_admin_only_gap_8k_card_suppressed_on_committed_brbr_e2e":
        {"BRBR": RECORD},
    "tests/test_dossier.py::test_analysis_tier_reads_in_decision_order_e2e": {"SMPL": RECORD},
    "tests/test_dossier.py::test_buyside_cover_and_field_grids_e2e_node": {"IT": RECORD},
    "tests/test_dossier.py::test_catalyst_calendar_js_twin_parity_node": {"SMPL": RECORD},
    "tests/test_dossier.py::test_catalyst_calendar_render_placement_b_and_crux_line":
        {"SMPL": RECORD},
    "tests/test_dossier.py::test_caveats_collapse_dejargon_and_acronyms_committed_brbr_e2e":
        {"BRBR": RECORD},
    "tests/test_dossier.py::test_dossier_page_logs_anchor_and_scenario_panels": {"IT": RECORD},
    "tests/test_dossier.py::test_one_8k_explaining_two_gap_downs_renders_once_e2e":
        {"SMPL": RECORD},
    "tests/test_dossier.py::test_opener_narrative_slot_rationale_once_and_conditional_warning_node":
        {"IT": RECORD},
    "tests/test_dossier.py::test_what_broke_restructure_and_survival_columns_e2e_node":
        {"IT": RECORD},
    # the guard's scratch git checkout holds a file at that path (`_checkout`)
    **{f"tests/test_gate_on_workers.py::{fn}": {"AMZN": SCRATCH} for fn in (
        "test_a_committed_file_restored_with_its_old_times_trips_the_guard",
        "test_a_committed_file_rewritten_and_restored_trips_the_guard",
        "test_a_file_the_run_adds_outside_the_caches_trips_the_guard",
        "test_a_folder_the_guard_cannot_read_fails_it_never_passes_it",
        "test_a_mark_that_sees_nothing_is_refused",
        "test_the_caches_and_git_are_left_out",
        "test_the_checkout_starts_no_git_maintenance_beside_its_walk")},
    # a diff path the impact run classifies, and a file in its scratch repository
    "tests/test_impact_run.py::test_pages_are_built_when_the_diff_reaches_the_page_builder":
        {"MCK": CLASSIFIER},
    "tests/test_impact_run.py::"
    "test_a_frontend_source_change_is_code_and_never_the_same_by_construction":
        {"MCK": SCRATCH},
    "tests/test_leg_fiscal_year.py::"
    "test_the_total_gap_does_not_move_with_the_year_but_the_split_does": {"SMPL": RECORD},
    # each arms a criterion on SMPL's living record (`scenario-criterion SMPL`)
    **{f"tests/test_measured_triggers.py::{fn}": {"SMPL": RECORD} for fn in (
        "test_a_malformed_criterion_refuses_rather_than_traces_back",
        "test_the_write_path_accepts_a_resolvable_metric_and_reports_what_it_reads",
        "test_the_write_path_refuses_a_criterion_the_evaluator_cannot_read")},
    # FUBO's CURRENT synthesis, by design since 2026-08-18; it skips when the page is gone
    "tests/test_nm_is_not_missing.py::test_the_live_fubo_sentence_is_no_longer_flagged":
        {"FUBO": LIVING},
    # GOOGL's page cohort against the living `data/graph_coverage.json` (slice 2)
    "tests/test_price_date_bounds.py::"
    "test_a_member_whose_bars_stop_in_july_is_refused_never_priced_as_180_days": {"GOOGL": RECORD},
    "tests/test_r3_template.py::test_propose_then_create_writes_the_r3_record_with_no_hand_edit":
        {"GOOGL": RECORD},
    # GOOGL's page stamp beside GOOGL's living record (`_stamped`, `_stage_googl`)
    **{f"tests/test_recipe_3a.py::{fn}": {"GOOGL": RECORD} for fn in (
        "test_a_bear_at_or_below_consensus_or_with_a_real_miss_passes",
        "test_a_consensus_not_knowable_at_the_spot_is_refused",
        "test_a_miss_case_off_the_r3_bear_is_refused",
        "test_create_through_the_cli_refuses_the_committed_bear_and_stamps_the_page",
        "test_the_same_legs_as_a_new_record_are_refused")},
    # a living record and its page staged together (`_stage`, `_googl_new`)
    **{f"tests/test_recipe_3b.py::{fn}": {"GOOGL": RECORD} for fn in (
        "test_a_googl_shaped_create_on_unlike_lines_is_refused_naming_both",
        "test_a_matching_line_takes_the_bound",
        "test_a_miss_case_on_the_wrong_line_is_refused",
        "test_an_indistinguishable_stamp_matches_either_line",
        "test_an_undetermined_stamp_assumes_no_line",
        "test_every_r3_leg_states_its_line_and_no_other_record_carries_one",
        "test_googls_stamp_is_on_the_gaap_line_and_its_legs_are_normalized",
        "test_legs_on_two_lines_are_refused",
        "test_unlike_lines_pass_on_a_miss_case_stated_on_the_legs_own_line")},
    "tests/test_recipe_3b.py::test_a_confirmed_copy_of_it_without_a_horizon_is_refused":
        {"IT": RECORD},
    "tests/test_recipe_3b.py::test_a_superseded_r2_payload_is_struck_nominal": {"NCNO": RECORD},
    "tests/test_recipe_3b.py::test_it_and_wern_load_run_and_write_byte_identical":
        {"IT": RECORD, "WERN": RECORD},
    "tests/test_recipe_3b.py::test_its_watch_as_it_stands_is_not_refused_for_a_missing_horizon":
        {"IT": RECORD},
    "tests/test_review_process.py::test_gemini_skips_artifacts_and_prose_but_reviews_code":
        {"VRRM": CLASSIFIER},
    # NFLX's and PARR's strict-xfail tripwires flip on the living page's re-read; GOOGL's case of
    # the same helper reads the cut (`_committed`)
    "tests/test_surprise_listing_block.py::"
    "test_parrs_committed_page_states_its_own_listings_surprise_history": {"PARR": LIVING},
    "tests/test_surprise_listing_block.py::test_the_committed_page_states_what_its_own_export_reads":
        {"NFLX": LIVING, "GOOGL": FIXTURE},
    "tests/test_tracked_files_hold_no_transcript_run.py::"
    "test_the_guard_finds_the_three_runs_1036_cut_in_its_parent":
        {"LLY": HISTORY, "VITL": HISTORY, "WERN": HISTORY},
    # SMPL's page beside SMPL's living record (`_record_and_mech`; A's ruling on #1096)
    **{f"tests/test_trigger_state_surface.py::{fn}": {"SMPL": RECORD} for fn in (
        "test_a_building_streak_is_read_from_satisfied_not_from_state",
        "test_a_record_with_no_measured_criteria_carries_an_empty_list_not_a_false_all_clear",
        "test_a_rerun_of_the_same_day_cannot_extend_a_streak",
        "test_all_three_states_reach_the_row_on_a_real_page",
        "test_an_absent_dossier_is_unmeasured_not_quiet",
        "test_an_amended_threshold_starts_its_streak_again",
        "test_another_names_readings_do_not_extend_this_names_streak",
        "test_the_prose_falsifiers_are_not_replaced_by_the_measured_ones",
        "test_the_retired_stale_tag_row_has_no_surface")},
}


def _ratchet(found: set[tuple[str, str]], pages: set[str],
             residue: dict[str, dict[str, str]]) -> tuple[list[tuple[str, str]],
                                                          list[tuple[str, str]]]:
    """(the pairs the scan found that `residue` does not name, the named pairs it no longer
    finds). A named pair for a name with no living page is never stale: a retirement removes the
    name, and with it every pair, and must edit nothing here."""
    allowed = {(fn, t) for fn, ts in residue.items() for t in ts}
    return sorted(found - allowed), sorted(p for p in allowed - found if p[1] in pages)


def test_no_test_reads_a_living_page_by_name_unless_it_is_named() -> None:
    npp = _scanner()
    pages, sources = npp.worktree(ROOT)
    found: set[tuple[str, str]] = npp.pairs(npp.scan_sources(sources, pages))
    assert found, "the scan found no pair at all: it is broken, or every residue is gone"
    new, stale = _ratchet(found, pages, RESIDUE)
    assert not new, (
        f"{len(new)} test(s) read a LIVING page by name and are not named in RESIDUE: "
        + "; ".join(f"{fn} reads {t}" for fn, t in new)
        + ". Move a value pin to the cut (tests/frozen_support.frozen_doc) and an invariant to a "
        "roster walk (covered_where). Only a page read beside its living record, a test that "
        "watches the living page by design, or a scan false positive is named in RESIDUE, with "
        "its reason. THE SCAN IS A LOWER BOUND: a read it cannot see passes here.")
    assert not stale, (
        f"{len(stale)} pair(s) named in RESIDUE are no longer found: "
        + "; ".join(f"{fn} / {t}" for fn, t in stale)
        + ". Delete each entry: the ratchet only shrinks.")


def test_a_retired_names_residue_is_never_stale_and_a_new_read_is_refused() -> None:
    """(+) Retiring a name removes its pairs from the scan, and its RESIDUE entries are not stale,
    so a retirement edits nothing here; (−) a pair the residue does not name is refused, and a
    named pair the scan no longer finds is stale while its page is living."""
    residue = {"tests/test_x.py::test_a": {"AAA": RECORD, "BBB": RECORD}}
    assert _ratchet({("tests/test_x.py::test_a", "BBB")}, {"BBB"}, residue) == ([], [])
    assert _ratchet({("tests/test_x.py::test_a", "BBB"), ("tests/test_x.py::test_b", "BBB")},
                    {"AAA", "BBB"}, residue) == ([("tests/test_x.py::test_b", "BBB")],
                                                 [("tests/test_x.py::test_a", "AAA")])
