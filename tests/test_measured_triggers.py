"""Measured re-underwrite triggers (ruling 3) — and the distinction the whole thing rests on.

`UNKNOWN` and `NOT_FIRED` recommend opposite actions and look identical when a check returns a
bare False. Most of these pins exist to keep them apart.
"""
from __future__ import annotations

import json
import os
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
    # the OBSERVED NUMBER, formatted the way the reason formats it — not a str() prefix, which
    # matches by luck at 1.5 and stops matching the moment the value is grouped or exponent-form.
    assert "is false" in r.reason and f"{r.observed:,.10g}" in r.reason


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
    """"Two consecutive quarters" is a DIFFERENT test from "once", so a satisfied single reading
    never fires it.

    AMENDED (step 2): the refusal is now conditional on having NO history rather than absolute —
    with prior readings in hand the criterion CAN be counted and returns a real answer. The
    property this pin protects is unchanged and is what the amendment must not lose: one reading
    alone never fires a multi-reading criterion.
    """
    r = evaluate(_t(threshold=1.0, sustain=2), _mech("SMPL"))
    assert r.state == UNKNOWN
    assert "consecutive readings" in r.reason and "no history was supplied" in r.reason


def test_a_stated_unit_that_disagrees_refuses_rather_than_comparing() -> None:
    """GOOGL's kill is written in $bn; the mechanical layer records revenue in $M. The comparison
    SUCCEEDS across that gap and `shown` labels both sides with the analyst's unit, so the wrong
    answer reads as a confident NOT_FIRED. The stated unit exists to make that refusable."""
    mech = {"quality": {"rev": {"value": 214_100.0, "unit": "$M", "status": "present"}}}
    r = evaluate(_t(metric="quality.rev", comparator="<", threshold=214.1, unit="$bn"), mech)
    assert r.state == UNKNOWN, r
    assert "$M" in r.reason and "$bn" in r.reason


def test_a_matching_unit_still_compares() -> None:
    """NON-VACUOUS: the refusal is conditional on disagreement, not on the node stating a unit."""
    mech = {"quality": {"rev": {"value": 5.0, "unit": "x", "status": "present"}}}
    assert evaluate(_t(metric="quality.rev"), mech).state == FIRED
    assert evaluate(_t(metric="quality.rev", unit=" X "), mech).state == FIRED


def test_a_non_finite_reading_is_unknown_not_not_fired() -> None:
    """NaN loses every comparison. Left unchecked it reaches NOT_FIRED — the exact bare-False that
    reassures where it should alarm, arrived at through the arithmetic instead of around it."""
    for bad in (float("nan"), float("inf")):
        r = evaluate(_t(), {"quality": {"net_debt_to_ebitda": {"value": bad,
                                                               "status": "present"}}})
        assert r.state == UNKNOWN, (bad, r)
        assert "finite" in r.reason


def test_a_metric_recorded_as_null_is_not_reported_as_a_bad_path() -> None:
    """A null value IS in the dossier. Saying "the path does not resolve" sends the operator after
    a typo that is not there — a wrong cause on a state whose only content is its cause."""
    r = evaluate(_t(), {"quality": {"net_debt_to_ebitda": None}})
    assert r.state == UNKNOWN
    assert "does not resolve" not in r.reason and "not a number" in r.reason


def test_the_reason_does_not_round_the_two_sides_into_looking_equal() -> None:
    """A kill criterion is decided AT its threshold, which is where 4 significant digits print
    "3 x > 3 x holds" — a sentence that reads as self-contradictory on the only readings that
    matter."""
    mech = {"quality": {"net_debt_to_ebitda": {"value": 3.00004, "status": "present"}}}
    r = evaluate(_t(), mech)
    assert r.state == FIRED
    assert "3.00004" in r.reason


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
        # ABSENT-vs-EMPTY, PER RECORD — not "no record has one" (corrected 2026-09-02). The
        # original read the corpus rather than the rule: it asserted the key appears NOWHERE,
        # which held only while nothing could write one. `scenario-criterion` is that write path,
        # so the first criterion the operator arms would have reddened this pin — the same
        # corpus-shaped assertion that broke three times on the tiered ladder the day a record
        # first carried it. The rule is unchanged: no stated trigger, no key; a stated one, a
        # non-empty list. Never an empty list, which is the default-spray this guards.
        got = (scoped.get("verdict") or {}).get("measured_triggers", "ABSENT")
        if rec.verdict.measured_triggers:
            assert isinstance(got, list) and got, f"{f.name} dropped a STATED measured trigger"
        else:
            assert got == "ABSENT", f"{f.name} gained an empty measured_triggers key"
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


# --- sustain: the count is in READINGS, not in monitor runs ------------------------------------


def _hist(*pairs: tuple[str | None, bool]) -> list:
    from vinci.triggers import Observation
    return [Observation(source=s, satisfied=ok) for s, ok in pairs]


_SUS = {"metric": "q.x", "comparator": ">", "threshold": 1.0, "unit": "x", "sustain": 2}
_MECH = {"q": {"x": {"value": 1.5, "status": "present", "source_ref": "Q2 2026"}}}


def test_the_same_reading_seen_twice_does_not_satisfy_a_two_reading_criterion() -> None:
    """THE CASE THE WHOLE DESIGN EXISTS FOR. "Two consecutive quarters" is stated in the ANALYST's
    cadence; the monitor can run twice in an afternoon. Counting runs would fire a kill on one
    observation the analyst deliberately wrote to need two. Readings are told apart by their
    `source_ref`, which already names the period — carried WHOLE and compared for equality, never
    parsed, because reaching into it for the quarter is the class this module refuses.
    """
    r = evaluate(MeasuredTrigger(trigger="t", **_SUS), _MECH, history=_hist(("Q2 2026", True)))
    assert r.state == NOT_FIRED
    assert "1 of the 2" in r.reason


def test_a_genuinely_prior_period_completes_the_streak() -> None:
    r = evaluate(MeasuredTrigger(trigger="t", **_SUS), _MECH, history=_hist(("Q1 2026", True)))
    assert r.state == FIRED and "2 consecutive readings" in r.reason


def test_a_broken_streak_restarts_and_does_not_reach_past_the_break() -> None:
    r = evaluate(MeasuredTrigger(trigger="t", **_SUS), _MECH,
                 history=_hist(("Q1 2026", False), ("Q4 2025", True)))
    assert r.state == NOT_FIRED and "1 of the 2" in r.reason


def test_no_history_supplied_stays_unknown_rather_than_guessing_a_streak() -> None:
    r = evaluate(MeasuredTrigger(trigger="t", **_SUS), _MECH, history=None)
    assert r.state == UNKNOWN and "no history was supplied" in r.reason


def test_a_metric_without_a_source_ref_cannot_be_counted() -> None:
    """Without it a repeat reading is indistinguishable from a new period, and counting monitor
    RUNS instead would satisfy a two-quarter test in an afternoon."""
    r = evaluate(MeasuredTrigger(trigger="t", **_SUS),
                 {"q": {"x": {"value": 1.5, "status": "present"}}}, history=_hist((None, True)))
    assert r.state == UNKNOWN and "no source_ref" in r.reason


def test_satisfied_diverges_from_state_on_a_short_streak() -> None:
    """The two are different facts, and conflating them is how a two-quarter kill never fires: a
    reading where the comparison HELD but the streak was short records NOT_FIRED, and counting the
    next day's streak off `state` alone would treat it as a failure and restart from zero."""
    short = evaluate(MeasuredTrigger(trigger="t", **_SUS), _MECH, history=_hist())
    assert short.state == NOT_FIRED and short.satisfied is True
    fired = evaluate(MeasuredTrigger(trigger="t", **_SUS), _MECH, history=_hist(("Q1", True)))
    assert fired.state == FIRED and fired.satisfied is True
    false = evaluate(MeasuredTrigger(trigger="t", **{**_SUS, "threshold": 9.0}), _MECH)
    assert false.state == NOT_FIRED and false.satisfied is False


def test_an_unreadable_prior_reading_refuses_the_count_instead_of_restarting_it() -> None:
    """A day the metric could not be read is NOT a day the criterion failed.

    `_history_for` coerced the stored `satisfied` with `bool(...)`, so an UNKNOWN prior reading
    (`satisfied: null`) arrived as `False` and `_streak` broke on it. The kill criterion's clock
    silently restarted: the reader was told "holds on 1 of the 2 consecutive readings" — the exact
    sentence a genuinely-failed period produces — with nothing saying the missing period was
    unreadable rather than benign. That is the third state collapsing into the second, inside the
    module whose whole purpose is keeping the three apart, on the one path that counts a kill.

    THREE INPUTS MUST GIVE THREE ANSWERS. The middle one is the regression.
    """
    from vinci.scenarios import MeasuredTrigger
    from vinci.triggers import FIRED, NOT_FIRED, UNKNOWN, Observation, _streak, evaluate

    trig = MeasuredTrigger(trigger="leverage kill", metric="quality.net_debt_to_ebitda",
                           comparator=">", threshold=3.0, unit="x", sustain=2, basis="CIQ")
    mech = {"quality": {"net_debt_to_ebitda": {"value": 4.2, "source_ref": "CIQ FQ3 2026"}}}

    def state(satisfied: bool | None) -> object:
        return evaluate(trig, mech,
                        history=[Observation(source="CIQ FQ2 2026", satisfied=satisfied)]).state

    assert state(True) == FIRED, "two satisfied readings must fire a sustain-2 criterion"
    assert state(False) == NOT_FIRED, "a genuinely failed prior period restarts the count"
    assert state(None) == UNKNOWN, (
        "an UNREADABLE prior period must refuse the count, not restart it — otherwise it is "
        "indistinguishable from a period that was measured and did not hold")

    # ...and the reason must SAY which, or the reader cannot act on either
    why = evaluate(trig, mech,
                   history=[Observation(source="CIQ FQ2 2026", satisfied=None)]).reason
    assert "UNKNOWN" in why and "source_ref" not in why, (
        f"the refusal must name the unreadable reading, not the other cause: {why!r}")

    # `_streak` refuses in its own right, not only through `evaluate`
    assert _streak("CIQ FQ3 2026", [Observation(source="CIQ FQ2 2026", satisfied=None)]) is None
    assert _streak("CIQ FQ3 2026", [Observation(source="CIQ FQ2 2026", satisfied=True)]) == 2


def test_the_history_read_carries_the_third_state_off_a_committed_row() -> None:
    """END-TO-END on the stored shape: `satisfied: null` on a monitor row must reach `Observation`
    as None. A unit pin on `_streak` alone would stay green with the `bool()` coercion restored,
    because the coercion lives in the READER, not the counter."""
    from vinci.monitor import _history_for
    from vinci.scenarios import MeasuredTrigger

    trig = MeasuredTrigger(trigger="k", metric="quality.net_debt_to_ebitda", comparator=">",
                           threshold=3.0, unit="x", sustain=2, basis="CIQ")
    day = {"freshness": [{"ticker": "SMPL", "measured": [
        {"metric": "quality.net_debt_to_ebitda", "comparator": ">", "threshold": 3.0,
         "satisfied": None, "source": "CIQ FQ2 2026"}]}]}
    got = _history_for("SMPL", trig, [day])
    assert got is not None and len(got) == 1
    assert got[0].satisfied is None, (
        f"a stored null must stay None, not become False: {got[0].satisfied!r}")


def test_the_write_path_refuses_a_metric_the_dossier_cannot_resolve() -> None:
    """`scenario-criterion` REFUSES an unresolvable metric, and that refusal is its whole point.

    A criterion naming a path the dossier does not carry evaluates to UNKNOWN on every run, which
    on the dashboard is indistinguishable from a working criterion that has not fired — the
    absent-vs-broken collapse, on the surface built to keep three states apart. SMPL's own "Quest
    revenue growth" is the live example: real arithmetic, but a BRAND figure read from a transcript
    and LLM-fenced by the covenant discipline, so no anchored path carries it.

    DRIVEN OFF THE COMMITTED DOSSIER, and the refusal must NAME what the dossier does offer — a
    refusal the analyst cannot act on sends them to grep the schema.
    """
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "vinci.cli", "scenario-criterion", "SMPL",
         "--trigger", "Quest revenue growth <= 0% YoY for two consecutive quarters",
         "--metric", "operating_drivers.quest_net_sales_yoy",
         "--comparator", "<=", "--threshold", "0", "--unit", "%", "--sustain", "2", "--dry-run"],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert proc.returncode == 1, f"an unresolvable metric must be refused, got {proc.returncode}"
    assert "REFUSED" in proc.stdout
    assert "quality.net_debt_to_ebitda" in proc.stdout, (
        "the refusal must list what SMPL CAN resolve, or the analyst cannot act on it")


def test_the_write_path_accepts_a_resolvable_metric_and_reports_what_it_reads() -> None:
    """The accepting side: it resolves through the EVALUATOR's own reader, and shows the state the
    criterion reads TODAY — a criterion already firing when written is a fact the analyst should
    meet at the keyboard, not discover on the next monitor day.

    `--dry-run` so the pin never writes to a committed record: the threshold is the operator's
    judgment, and a test that armed a real falsifier would be inventing one.
    """
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "vinci.cli", "scenario-criterion", "SMPL",
         "--trigger", "Leverage past 3.0x net debt / EBITDA",
         "--metric", "quality.net_debt_to_ebitda",
         "--comparator", ">", "--threshold", "3.0", "--unit", "x", "--dry-run"],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "NOT_FIRED" in proc.stdout, "it must report the state the criterion reads today"
    assert "nothing written" in proc.stdout
    # the resolved value carries its OWN source, so the analyst can see WHICH series armed it
    assert "CIQ" in proc.stdout, "the resolved value must show its source_ref"
