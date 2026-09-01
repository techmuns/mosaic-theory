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


def test_all_three_states_reach_the_row_on_the_committed_corpus() -> None:
    rec, mech = _record_and_mech()
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
    """Every committed record is in this state today. The row must be able to SAY so — the
    renderer distinguishes 'no measured criteria' from 'measured, none fired'."""
    rec, mech = _record_and_mech()
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
