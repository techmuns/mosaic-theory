"""The evaluated criteria reaching a human (ruling 3, second half).

The evaluator shipped in #548 and rendered nowhere. A state computed and not surfaced is the
unwired-capability shape this repo has now recorded twice — `dilution.py` (imported only by its
own test) and `stale_served` (no caller since it shipped). These pins bind the whole path: typed
on the row, carried into the committed artifact, and rendered as three DIFFERENT things.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest

from vinci.monitor import freshness_row

ROOT = pathlib.Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 9, 1)


def _record_and_mech() -> tuple[dict, dict]:
    r = ROOT / "scenarios" / "SMPL.json"
    d = ROOT / "data" / "dossiers" / "SMPL" / "dossier.json"
    if not (r.is_file() and d.is_file()):
        pytest.skip("no committed SMPL record + dossier")
    return json.loads(r.read_text()), json.loads(d.read_text())["mechanical"]


def _with(rec: dict, *trigs: dict) -> dict:
    out = json.loads(json.dumps(rec))
    out["verdict"]["measured_triggers"] = list(trigs)
    return out


_NDE = {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "unit": "x"}


#: SMPL's page as committed on 2026-08-18, frozen (tests/fixtures/frozen_pages/README.md): its net
#: debt / EBITDA of 1.5x sits between the two thresholds below, which the living page need not.
FROZEN_SMPL = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"


def test_all_three_states_reach_the_row_on_a_real_page() -> None:
    """VALUE-LEVEL, so on the frozen page (TEST-LAYER RULE): one real record and one real
    mechanical layer, and each of the three states reaches the row with the observed figure."""
    rec, _ = _record_and_mech()
    mech = json.loads(FROZEN_SMPL.read_text())["mechanical"]
    rec = _with(rec,
                {"trigger": "nde > 3.0x", "threshold": 3.0, **_NDE},
                {"trigger": "nde > 1.0x", "threshold": 1.0, **_NDE},
                {"trigger": "margin trend", "metric": "quality.margin_trend",
                 "comparator": "<", "threshold": 0.31, "unit": "%"})
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=mech)
    assert [m.state for m in row.measured] == ["NOT_FIRED", "FIRED", "UNKNOWN"]
    assert all(m.reason for m in row.measured), "every state carries its reason, not just refusals"
    assert row.measured[1].observed == 1.5 and row.measured[1].unit == "x"


def test_an_absent_dossier_is_unmeasured_not_quiet() -> None:
    """THE CASE THAT MUST NOT SILENTLY READ AS 'nothing fired'. The criteria exist and simply were
    not measurable on this run — a different sentence from a quiet page, and it reaches the human
    as one rather than being skipped."""
    rec, _ = _record_and_mech()
    rec = _with(rec, {"trigger": "nde > 3.0x", "threshold": 3.0, **_NDE})
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=None)
    assert [m.state for m in row.measured] == ["UNKNOWN"]
    assert "no committed dossier" in row.measured[0].reason


def test_the_prose_falsifiers_are_not_replaced_by_the_measured_ones() -> None:
    """Both representations ride the row. Dropping the sentences would leave a reader with numbers
    and no criterion to read them against."""
    rec, mech = _record_and_mech()
    rec = _with(rec, {"trigger": "nde > 3.0x", "threshold": 3.0, **_NDE})
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=mech)
    assert row.triggers, "the analyst's sentences vanished from the row"
    assert row.measured and row.measured[0].trigger


def test_a_record_with_no_measured_criteria_carries_an_empty_list_not_a_false_all_clear() -> None:
    """The row must be able to SAY 'no measured criteria' — the renderer distinguishes that from
    'measured, none fired'.

    DRIVEN OFF A RECORD STATED TO CARRY NONE, not off whatever the corpus happens to hold
    (corrected 2026-09-02). The original read the live SMPL record and asserted the row came back
    empty — true only while nothing could WRITE a criterion. `vinci scenario-criterion` is that
    write path, so the first criterion the operator arms would have reddened this pin: the same
    corpus-shaped assertion the sibling pin in `test_measured_triggers.py` was corrected for, in
    the file that ships beside it. The rule under test is unchanged and does not depend on the
    corpus: a record stating no measured criteria produces an empty `measured`, and its prose
    falsifiers survive.
    """
    rec, mech = _record_and_mech()
    rec = _with(rec)                     # STATED to carry none — the case the row must say
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=mech)
    assert row.measured == []
    assert row.triggers, "…while its prose falsifiers are still there to be read"


# --- the render, because computing a state and not showing it is the defect being fixed --------


def _panel_src() -> str:
    p = ROOT / "frontend" / "views" / "shared" / "decision-log.js"
    if not p.is_file():
        pytest.skip("no decision-log view")
    return p.read_text()


def test_the_three_states_render_as_three_different_things() -> None:
    """UNKNOWN and NOT_FIRED recommend opposite actions; a shared style would undo the whole
    point of separating them upstream."""
    src = _panel_src()
    assert "f.measured" in src, "the panel never reads the evaluated criteria"
    for state in ("FIRED", "UNKNOWN", "NOT_FIRED"):
        assert state in src, f"{state} has no rendering"
    assert "stateClass" in src and "avoid" in src and "conditional" in src, (
        "the three states must map to distinct styles, not one shared pill")


def test_the_panel_says_when_there_are_no_measured_criteria() -> None:
    """An empty list is NOT 'nothing fired' — it means every falsifier is a judgment. Silence
    there would read as reassurance."""
    src = _panel_src()
    assert "no measured criteria" in src and "judgment" in src


def test_the_number_and_its_source_ride_along() -> None:
    """A highlight the human cannot check is one they must trust — the opposite of the
    source-binding rule."""
    src = _panel_src()
    assert "m.observed" in src and "m.source" in src and "m.reason" in src


def test_the_stale_tags_reach_the_page() -> None:
    """MC1's reporting half had no caller since it shipped; the tags it names now render."""
    assert "stale_tags" in _panel_src()


def test_a_building_streak_is_read_from_satisfied_not_from_state() -> None:
    """THE BUG THIS PIN EXISTS FOR, caught while wiring the history rather than by review.

    Every prior reading of a BUILDING streak records `NOT_FIRED` by definition — the comparison
    held but the count was still short. Reading `state` to decide whether a prior reading counted
    therefore treats each one as a failure, the streak can never exceed 1, and a multi-reading
    criterion NEVER FIRES no matter how long the condition persists. Measured: with two prior
    satisfying readings and `sustain=3`, reading `state` gives "1 of the 3"; reading `satisfied`
    gives FIRED on 3.
    """
    rec, mech = _record_and_mech()
    rec = _with(rec, {"trigger": "nde > 1.0x for three readings", "threshold": 1.0,
                      "sustain": 3, **_NDE})
    prior = [{"freshness": [{"ticker": "SMPL", "measured": [
        {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "threshold": 1.0,
         "source": f"period-{i}", "satisfied": True, "state": "NOT_FIRED"}]}]}
        for i in (1, 2)]
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=mech, prior_days=prior)
    assert row.measured[0].state == "FIRED", (
        f"a building streak was not counted: {row.measured[0].reason}")
    assert "3 consecutive readings" in row.measured[0].reason


def test_a_rerun_of_the_same_day_cannot_extend_a_streak() -> None:
    """Two guards cover this and both are load-bearing: the caller passes only days STRICTLY
    EARLIER than the one being built, and the evaluator de-duplicates on `source_ref`. Either
    alone would leave running the monitor twice able to advance a kill."""
    rec, mech = _record_and_mech()
    cur = mech["quality"]["net_debt_to_ebitda"].get("source_ref")
    rec = _with(rec, {"trigger": "nde > 1.0x twice", "threshold": 1.0, "sustain": 2, **_NDE})
    same = [{"freshness": [{"ticker": "SMPL", "measured": [
        {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "threshold": 1.0,
         "source": cur, "satisfied": True, "state": "NOT_FIRED"}]}]}]
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=mech, prior_days=same)
    assert row.measured[0].state == "NOT_FIRED" and "1 of the 2" in row.measured[0].reason


def test_an_amended_threshold_starts_its_streak_again() -> None:
    """History is matched on the TEST, not the sentence. A changed threshold is a different
    criterion, so its prior readings do not carry over — and a reworded sentence, which is the
    same test, keeps its streak."""
    rec, mech = _record_and_mech()
    rec = _with(rec, {"trigger": "nde > 1.0x twice", "threshold": 1.0, "sustain": 2, **_NDE})
    other = [{"freshness": [{"ticker": "SMPL", "measured": [
        {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "threshold": 2.0,
         "source": "period-1", "satisfied": True, "state": "NOT_FIRED"}]}]}]
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=mech, prior_days=other)
    assert row.measured[0].state == "UNKNOWN", "a different threshold's history was carried over"
    assert "no history was supplied" in row.measured[0].reason


def test_another_names_readings_do_not_extend_this_names_streak() -> None:
    """REVIEW FIX. A monitor day carries EVERY followed name's freshness row, and the criterion
    identity `(metric, comparator, threshold)` is unique WITHIN a record, never across the book:
    `quality.net_debt_to_ebitda > 1.0x` is the same triple on every name that writes it. Scanned
    name-blind, two peers reading on the same day supplied two "consecutive" observations — each
    with its own `source_ref`, so the de-duplication that stops a monitor re-run extending a
    streak could not stop them, and a two-reading kill fired on one reading of this name.
    """
    rec, mech = _record_and_mech()
    rec = _with(rec, {"trigger": "nde > 1.0x twice", "threshold": 1.0, "sustain": 2, **_NDE})
    peers = [{"freshness": [
        {"ticker": "AORT", "measured": [
            {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "threshold": 1.0,
             "source": "AORT FQ2", "satisfied": True, "state": "NOT_FIRED"}]},
        {"ticker": "NCNO", "measured": [
            {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "threshold": 1.0,
             "source": "NCNO FQ2", "satisfied": True, "state": "NOT_FIRED"}]}]}]
    row = freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                        mechanical=mech, prior_days=peers)
    assert row.measured[0].state == "UNKNOWN", (
        f"another name's readings were counted into SMPL's streak: {row.measured[0].reason}")
    assert "no history was supplied" in row.measured[0].reason
    # ...and the pin is not inert: the SAME rows under this name's ticker DO complete the streak.
    mine = [{"freshness": [{"ticker": "SMPL", "measured": [
        {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "threshold": 1.0,
         "source": "SMPL FQ2", "satisfied": True, "state": "NOT_FIRED"}]}]}]
    assert freshness_row(ticker="SMPL", verdict="BUY", record=rec, filings=[], today=TODAY,
                         mechanical=mech, prior_days=mine).measured[0].state == "FIRED"


def test_the_stale_tag_scan_cannot_match_and_says_so() -> None:
    """`_stale_tags` is DEAD BY CONSTRUCTION, and this pin exists so that stays deliberate.

    It scans mechanical nodes for `status == "stale"`. `SourceStatus` has three members — PRESENT,
    UNKNOWN, MISSING — so no assembled dossier can carry that value: the monitor's stale-tag row is
    unconditionally empty and `stale_served` still has no production caller. The reporting half of
    #531 is NOT delivered.

    THIS PIN IS THE FALSIFIER, not an endorsement. It reddens the moment `SourceStatus` gains a
    `stale` member — which is exactly when someone must decide whether to finish the wiring
    (companyfacts in the monitor) or drop the row. A test asserting the empty list against today's
    corpus would instead go green forever and hide that decision.
    """
    import json
    import pathlib

    from vinci.dossier.schemas import SourceStatus
    from vinci.monitor import _stale_tags

    assert "stale" not in {m.value for m in SourceStatus}, (
        "SourceStatus gained a `stale` member — `_stale_tags` can now match, so decide: finish "
        "the wiring (companyfacts in the monitor) or remove the row. Do not just update this pin.")

    # ...and it really does return nothing on every committed dossier, not merely on a fixture
    root = pathlib.Path(__file__).resolve().parents[1] / "data" / "dossiers"
    seen = 0
    for f in sorted(root.glob("*/dossier.json")):
        assert _stale_tags(json.loads(f.read_text()).get("mechanical")) == []
        seen += 1
    assert seen >= 8, f"corpus scan covered {seen} dossiers — it is not exercising anything"
