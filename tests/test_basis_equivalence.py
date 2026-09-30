"""Entry and exit denominators must cover the same period, or the leg must bridge them.

A return called "multiple compression" is only measuring compression when both multiples are
struck on period-equivalent denominators. GOOGL's bear leg reads "Bear EPS EXCEEDS today's NTM
$13.29, so the downside is multiple compression from ~26x" — an NTM entry denominator against an
exit leg whose year is unstated, and 339.35 / 13.29 = 25.5x confirms the ~26x is NTM-struck.
Nothing could check that while the entry window was never written down.

THE DEAD-GUARD LESSON THIS FILE IS BUILT AROUND. `leg_fy_problems` already claims to "refuse an
unexplained disagreement", escaping on any non-blank `reason`. `ScenarioInput` validates `reason`
as required and non-blank, so that refusal fires only in a state the constructor forbids; its own
pin reaches it via `model_copy`, which skips validators. The guard is unreachable in production.
`basis_problems` therefore does NOT take that route: a mismatch is excused only by a reason naming
BOTH periods, which is the bridge the mismatch requires anyway and cannot be met by boilerplate.
"""

from __future__ import annotations

import pathlib
import warnings

import vinci.scenarios as sc

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _rec(**over: object) -> sc.ScenarioRecord:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rec = sc.read_record("SMPL", root=ROOT)
    return rec.model_copy(update=over)


def _with_base(rec: sc.ScenarioRecord, **over: object) -> sc.ScenarioRecord:
    legs = dict(rec.scenarios or {})
    legs["base"] = legs["base"].model_copy(update=over)
    return rec.model_copy(update={"scenarios": legs})


# --- the field, and the corpus it must not disturb ---------------------------------------------

def test_every_committed_record_round_trips_byte_identical(tmp_path: pathlib.Path) -> None:
    """(+) CORPUS, NOT FIXTURE. A new optional field that serialises as null would rewrite all nine
    committed records on the next write and bury the real diff — the #302 defect this codebase
    already carries a mechanism for. Absent-key and None must say one thing."""
    seen = 0
    for f in sorted((ROOT / "scenarios").glob("*.json")):
        if f.name.startswith("_"):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rec = sc.read_record(f.stem, root=ROOT)
            out = sc.write_record(rec, root=tmp_path)
        assert out.read_text() == f.read_text(), f"{f.stem} churned on a no-op write"
        seen += 1
    assert seen >= 9, f"expected the committed corpus, saw {seen}"


def test_a_stated_entry_basis_survives_the_write(tmp_path: pathlib.Path) -> None:
    """(+) The mirror: a record that DOES state its window carries it."""
    rec = _rec(entry_basis="NTM")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = sc.write_record(rec, root=tmp_path)
    assert '"entry_basis": "NTM"' in out.read_text()


# --- step 2: the write boundary may require a stated year --------------------------------------

def test_the_read_path_still_accepts_an_unstated_year() -> None:
    """(-) THE ADOPTION ARGUMENT, PRESERVED. Nine committed records state no year. A guard added
    after they were written must never make them unrecomputable, so the DEFAULT stays permissive
    and only the write boundary opts in."""
    base = (_rec().scenarios or {})["base"]
    assert sc.leg_fy_problems(base.model_copy(update={"leg_fy": None}), "2026") == []


def test_the_write_boundary_requires_a_stated_year() -> None:
    """(+) A record being written today states the year its base leg strikes at."""
    base = (_rec().scenarios or {})["base"].model_copy(update={"leg_fy": None})
    got = sc.leg_fy_problems(base, "2026", require_stated=True)
    assert len(got) == 1 and "unstated" in got[0]
    # and an ANCHOR is not needed to ask for it — WERN has no committed dossier
    assert len(sc.leg_fy_problems(base, None, require_stated=True)) == 1


# --- step 3: the equivalence check -------------------------------------------------------------

def test_the_same_fiscal_year_on_both_sides_passes() -> None:
    """(+) Period-equivalent by identity: nothing to bridge, nothing to say."""
    rec = _with_base(_rec(entry_basis="FY2028"), leg_fy="2028")
    assert sc.basis_problems(rec, require_stated=True) == []


def test_a_rolling_window_against_a_fiscal_year_is_refused() -> None:
    """(+) THE CASE THE RULE EXISTS FOR. NTM entry against an FY leg: the move between the two
    multiples is part window-roll and part re-rating, in unknown proportion."""
    rec = _with_base(_rec(entry_basis="NTM"), leg_fy="2028", reason="a perfectly good reason")
    got = sc.basis_problems(rec, require_stated=True)
    assert len(got) == 1, got
    assert "different windows" in got[0] and "NTM" in got[0] and "FY2028" in got[0]


def test_a_non_blank_reason_does_not_excuse_the_mismatch() -> None:
    """(-) THE DEAD-GUARD LESSON, PINNED. `leg_fy_problems` escapes on any non-blank reason, and
    `reason` can never be blank — so its refusal is unreachable. This guard must not inherit that:
    a reason that says nothing about either period leaves the mismatch refused."""
    wordy = ("Revenue 1,340 is the median FY2028 street forecast and the margin matches the "
             "median of the last eight years, so the leg is anchored rather than invented.")
    rec = _with_base(_rec(entry_basis="NTM"), leg_fy="2027", reason=wordy)
    assert len(sc.basis_problems(rec, require_stated=True)) == 1, (
        "a long, sincere, non-bridging reason must NOT satisfy the guard")


def test_a_reason_naming_both_periods_bridges_them() -> None:
    """(+) The escape hatch that works: the analyst writes the bridge the mismatch requires."""
    bridge = ("Entry is quoted on NTM; the leg strikes FY2027 because the eighteen-month horizon "
              "this record states lands inside that year, and the roll between them is ~1.1x.")
    rec = _with_base(_rec(entry_basis="NTM"), leg_fy="2027", reason=bridge)
    assert sc.basis_problems(rec, require_stated=True) == []


def test_a_window_a_machine_cannot_compare_is_refused() -> None:
    """(-) The field's value is that it compares. Free text compares with nothing."""
    got = sc.basis_problems(_rec(entry_basis="next year-ish"), require_stated=True)
    assert len(got) == 1 and "compare" in got[0]


def test_the_read_path_never_demands_the_entry_basis() -> None:
    """(-) Same placement rule as `leg_fy_problems`: recomputing a record must not demand a field
    it predates. All nine committed records are in that state."""
    assert sc.basis_problems(_rec()) == []


def test_run_recipe_still_refuses_nothing_on_either_field() -> None:
    """(-) THE PLACEMENT, RE-PINNED. Neither field may make a committed record unrecomputable —
    the invariant that keeps the drift check alive on the only open position."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rec = sc.read_record("SMPL", root=ROOT)
        out = sc.run_recipe(rec)
    assert out is not None


def test_the_write_boundary_requires_a_stated_entry_window() -> None:
    """(+) THE PIN I FIRST OMITTED. `require_stated` was pinned for the leg YEAR and not for the
    entry WINDOW, so disabling the window's refusal left every test green — the same blindness as
    testing one half of a two-part gate. Without this, the field can be declared and never asked
    for, which is the state the whole sequence exists to end."""
    got = sc.basis_problems(_rec(), require_stated=True)
    assert len(got) == 1 and "entry_basis is unstated" in got[0], got
    # and it is the WRITE boundary only — the read path stays silent on the same record
    assert sc.basis_problems(_rec()) == []


# --- the write boundary the first cut left open ------------------------------------------------

def test_a_fiscal_year_leg_written_with_its_prefix_is_period_equivalent() -> None:
    """(-) `leg_fy` HAS NO FORMAT VALIDATOR, so an analyst may write "FY2028" where the committed
    records write "2028". The first cut compared the regex's bare-year group with the raw leg
    string, so an entry and a leg naming THE SAME YEAR were refused — with the message "strikes
    at FYFY2028". Both sides are canonicalised before anything is compared or printed."""
    rec = _with_base(_rec(entry_basis="FY2028"), leg_fy="FY2028", reason="a plain reason")
    assert sc.basis_problems(rec, require_stated=True) == []


def test_the_refusal_echoes_the_canonical_window() -> None:
    """(-) The regex is case-insensitive, so "ntm" is legal input — and the refusal used to tell
    the analyst to "strike the leg at ntm"."""
    rec = _with_base(_rec(entry_basis="ntm"), leg_fy="2027", reason="a plain reason")
    got = sc.basis_problems(rec, require_stated=True)
    assert len(got) == 1 and "entry_basis is NTM" in got[0] and "ntm" not in got[0]


def test_the_create_path_can_ask_for_the_entry_window() -> None:
    """(+) THE WRITE BOUNDARY THE FIRST CUT LEFT OPEN. The guard ran on `scenario-supersede`
    only, so `scenario-create` never asked for `entry_basis` and never carried one — every record
    the tool created was refused by the very next supersede, on a field its own writer could not
    set. The rule is reachable from the two values the create path actually holds."""
    base = (_rec().scenarios or {})["base"].model_copy(update={"leg_fy": "2028"})
    got = sc.entry_basis_problems(None, base, require_stated=True)
    assert len(got) == 1 and "entry_basis is unstated" in got[0]
    assert sc.entry_basis_problems("FY2028", base, require_stated=True) == []


def test_both_write_paths_run_the_entry_window_guard() -> None:
    """(+) ONE WRITE PATH GUARDED IS NOT GUARDED — the shape `leg_fy` already has a pin for, one
    file over. `scenario-create` ran neither the entry-window guard nor carried the field, so the
    record it wrote was refused by the very next `scenario-supersede`."""
    import inspect
    import json

    from vinci import cli
    from vinci.dossier.propose import build_template

    for fn in (cli._cmd_scenario_create, cli._cmd_scenario_supersede):
        src = inspect.getsource(fn)
        assert "basis_problems" in src, (
            f"{fn.__name__} does not run the entry-window guard — the field would be enforced on "
            "one write path and unsettable on the other")
    assert "entry_basis=" in inspect.getsource(cli._cmd_scenario_create), (
        "scenario-create validates the entry window but never writes it onto the record")

    doc = json.loads((ROOT / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    tpl = build_template(doc)
    assert "entry_basis" in tpl, "the template has no cell for the entry window"
    assert tpl["entry_basis"] == "", (
        "the entry window must be EMPTY, never proposed — the dossier publishes a price, not an "
        "entry multiple, so a proposed window would be the machine inventing the denominator")


def test_the_leg_year_guard_is_not_gated_on_revenue() -> None:
    """(-) R3 (forward P/E) legs carry `eps` and NO revenue — GOOGL's own recipe. The create
    path ran the leg-year guard only when `revenue` was present, so the requirement was silently
    skipped on exactly the recipe this work was motivated by."""
    import inspect

    from vinci import cli
    src = inspect.getsource(cli._cmd_scenario_create)
    marker = 'if _base.get("revenue") is not None and _base.get("multiple") is not None:'
    assert marker not in src, (
        "the leg-year / entry-window gate is behind a revenue check again — an R3 leg has no "
        "revenue, so the guard would never run on it")
