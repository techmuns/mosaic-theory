"""Measured re-underwrite triggers (ruling 3) — and the distinction the whole thing rests on.

`UNKNOWN` and `NOT_FIRED` recommend opposite actions and look identical when a check returns a
bare False. Most of these pins exist to keep them apart.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.scenarios import MeasuredTrigger
from vinci.triggers import FIRED, NOT_FIRED, UNKNOWN, evaluate

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _mech(ticker: str) -> dict:
    p = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not p.is_file():
        pytest.skip(f"no committed dossier for {ticker}")
    return json.loads(p.read_text())["mechanical"]


def _t(**kw: object) -> MeasuredTrigger:
    base: dict[str, object] = {"trigger": "t", "metric": "quality.net_debt_to_ebitda",
                               "comparator": ">", "threshold": 3.0, "unit": "x"}
    base.update(kw)
    return MeasuredTrigger(**base)  # type: ignore[arg-type]


# --- the two real answers, on the committed corpus ---------------------------------------------


def test_a_threshold_not_crossed_reads_not_fired_with_its_number() -> None:
    r = evaluate(_t(threshold=3.0), _mech("SMPL"))
    assert r.state == NOT_FIRED and r.observed is not None
    assert "is false" in r.reason and str(r.observed)[:3] in r.reason


def test_a_threshold_crossed_reads_fired_and_says_what_fired_it() -> None:
    """A human reading FIRED needs the number as much as one reading UNKNOWN needs the cause."""
    r = evaluate(_t(threshold=1.0), _mech("SMPL"))
    assert r.state == FIRED and r.fired
    assert "holds" in r.reason and r.observed is not None


# --- UNKNOWN: every path that cannot answer must SAY so ----------------------------------------


def test_an_unresolvable_path_is_unknown_not_quietly_not_fired() -> None:
    r = evaluate(_t(metric="quality.no_such_metric"), _mech("SMPL"))
    assert r.state == UNKNOWN and not r.fired
    assert "does not resolve" in r.reason


def test_a_display_string_is_refused_rather_than_parsed() -> None:
    """`quality.margin_trend` is prose ("EBITDA margin: … 13% → 17% → …"). Reaching into it with a
    regex is the display-string-as-data class this repo has paid for three times; the evaluator
    refuses and names the shape it found."""
    r = evaluate(_t(metric="quality.margin_trend", comparator="<", threshold=0.15, unit="%"),
                 _mech("SMPL"))
    assert r.state == UNKNOWN
    assert "not a number" in r.reason and "str" in r.reason


def test_a_non_present_status_is_not_a_reading() -> None:
    r = evaluate(_t(), {"quality": {"net_debt_to_ebitda": {"value": 9.0, "status": "unknown"}}})
    assert r.state == UNKNOWN and "not a reading" in r.reason


def test_a_bool_is_not_a_number() -> None:
    """`True` compares as 1 in Python. A metric that resolved to a flag must not silently become
    one side of a numeric threshold."""
    r = evaluate(_t(), {"quality": {"net_debt_to_ebitda": {"value": True, "status": "present"}}})
    assert r.state == UNKNOWN and "not a number" in r.reason


def test_a_sustain_count_refuses_rather_than_firing_on_one_reading() -> None:
    """"Two consecutive quarters" is a DIFFERENT test from "once". Nothing here records a prior
    observation yet, so a satisfied single reading is UNKNOWN — firing would be the weaker test the
    analyst deliberately did not write."""
    r = evaluate(_t(threshold=1.0, sustain=2), _mech("SMPL"))
    assert r.state == UNKNOWN
    assert "consecutive observations" in r.reason and "weaker test" in r.reason


def test_fired_is_the_only_true_and_unknown_is_never_a_quiet_no() -> None:
    """The property every call site depends on: `.fired` must not be True for UNKNOWN, and a
    caller that branches on it alone still cannot mistake an unreadable criterion for a quiet one,
    because UNKNOWN is false there AND visible in `state`."""
    assert evaluate(_t(threshold=1.0), _mech("SMPL")).fired is True
    assert evaluate(_t(threshold=3.0), _mech("SMPL")).fired is False
    assert evaluate(_t(metric="quality.nope"), _mech("SMPL")).fired is False
    assert evaluate(_t(metric="quality.nope"), _mech("SMPL")).state == UNKNOWN


# --- the model refuses what it cannot evaluate -------------------------------------------------


@pytest.mark.parametrize("bad", ["==", "!=", "~", "", "=>"])
def test_an_unknown_comparator_is_refused_at_construction(bad: str) -> None:
    with pytest.raises(ValueError, match="comparator"):
        _t(comparator=bad)


@pytest.mark.parametrize("field", ["metric", "unit", "trigger"])
def test_a_blank_required_field_is_refused(field: str) -> None:
    with pytest.raises(ValueError, match="required"):
        _t(**{field: "   "})


def test_the_analysts_sentence_is_carried_beside_the_arithmetic_not_replaced() -> None:
    """The structure never supersedes the prose: both are written by a human and neither is derived
    from the other. A measured trigger that lost its sentence would be a number nobody can audit."""
    t = _t(trigger="Quest revenue growth <= 0% YoY for two consecutive quarters")
    assert "Quest" in t.trigger and t.metric and t.threshold is not None


# --- the field on the record, and the null-spray it must not cause ----------------------------


def test_a_record_stating_no_measured_trigger_carries_no_key_for_one() -> None:
    """THE #302 RULE, ON A NEW FIELD. An empty list would assert "this analyst considered measured
    triggers and wrote none"; the truth for all eight committed records is "this record predates
    the question". Version-scoping keeps those apart — and getting it wrong sprays a default
    across the corpus, which is the defect that mechanism exists for and which this PR's sibling
    (`eps`) already reached a committed record with once.
    """
    from vinci import scenarios as sc

    root = ROOT / "scenarios"
    seen = 0
    for f in sorted(root.glob("*.json")):
        if f.name.startswith("_"):
            continue
        seen += 1
        rec = sc.read_record(f.stem, root=ROOT)
        scoped = sc._version_scoped(rec)
        assert "measured_triggers" not in (scoped.get("verdict") or {}), (
            f"{f.name} gained an empty measured_triggers key")
    assert seen >= 8, f"walked only {seen} committed records"


def test_a_record_that_states_one_keeps_it() -> None:
    """NON-VACUOUS: the drop is conditional on being empty, not unconditional — a scoping rule that
    dropped a stated value would be silent data loss rather than null-suppression."""
    from vinci import scenarios as sc

    rec = sc.read_record("SMPL", root=ROOT)
    v = rec.verdict
    assert v is not None
    trig = MeasuredTrigger(trigger="Quest revenue growth <= 0% YoY for two consecutive quarters",
                           metric="quality.net_debt_to_ebitda", comparator=">", threshold=3.0,
                           unit="x", sustain=2)
    v2 = v.model_copy(update={"measured_triggers": [trig]})
    with_one = rec.model_copy(update={"verdict": v2})
    scoped = sc._version_scoped(with_one)
    kept = (scoped.get("verdict") or {}).get("measured_triggers")
    assert kept and kept[0]["trigger"].startswith("Quest"), kept
    assert kept[0]["sustain"] == 2
