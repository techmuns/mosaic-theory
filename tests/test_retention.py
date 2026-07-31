"""RETENTION'S PERSISTENCE LAYER — the round trip, and the two properties calibration depends on.

WHY THIS EXISTS. `candidate_records.jsonl` is rewritten every run, so the only screen evidence that
has ever existed is the latest run's SURVIVORS. Survivors-only retention can only confirm the
screen: a screen discarding names that later outperform has negative alpha and nothing would show
it. These pins cover the layer that makes the reject set durable.

THE ROUND TRIP IS TWO PROPERTIES, NOT ONE (operator). Rows written are rows read back — and
**appending a run leaves every prior byte untouched.** The second half is the one calibration
actually depends on: a retained row a later run could edit is not evidence.

NOT COVERED HERE, deliberately: wiring the screen to emit these grains, and the first real run with
the outcome-join verified. Those are the next piece; this is the layer beneath them.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest
from pydantic import ValidationError

from vinci.schemas.candidate import GateResult
from vinci.screens.retention import (
    BandConfig,
    CandidateRow,
    GateOutcome,
    Outcome,
    ScreenConfig,
    StampedInput,
    UniverseRow,
    append_rows,
    list_runs,
    next_run_id,
    outcome_from_gate,
    read_rows,
    rollup,
    run_path,
)

REF = dt.date(2026, 7, 27)
CFG = ScreenConfig(thresholds={"drawdown_max": -0.30, "idio_rel_max": -0.15},
                   benchmark="IWM", lookback_days=70)
BAND = BandConfig(market_cap_min_usd=3e8, market_cap_max_usd=1e10, exchanges=("XNYS", "XNAS"))


def _g(outcome: Outcome, reason: str) -> GateOutcome:
    return GateOutcome(outcome=outcome, reason=reason)


_G1 = _g(Outcome.PASS, "drawdown -42.0% <= -30%")
_GATES = {
    Outcome.FAIL: {"g1_drawdown": _G1,
                   "g2_idiosyncratic": _g(Outcome.FAIL, "rel -18% vs -15%")},
    Outcome.PASS: {"g1_drawdown": _G1,
                   "g2_idiosyncratic": _g(Outcome.PASS, "rel -18% clears -15%")},
    Outcome.NOT_EVALUATED: {
        "g1_drawdown": _G1,
        "g2_idiosyncratic": _g(Outcome.NOT_EVALUATED, "the 70d window has no start")},
}


def _candidate(ticker: str, run_id: str, outcome: Outcome = Outcome.FAIL, **kw: object
               ) -> CandidateRow:
    return CandidateRow(
        ticker=ticker, run_id=run_id, reference_date=REF, outcome=outcome,
        gate_inputs={
            # the benchmark-incident shape: the input's OWN frontier, four days behind the run
            "rel_ret_vs_market": StampedInput(
                value=-0.18, as_of=dt.date(2026, 7, 21), source="EOD derived",
                note="window 2026-05-18→2026-07-21 (common last bar; 6d short of the reference)"),
            "drawdown_from_high": StampedInput(
                value=-0.42, as_of=dt.date(2026, 7, 24), source="EOD"),
        },
        per_gate=_GATES[outcome],
        config=CFG, **kw)  # type: ignore[arg-type]


def _universe(ticker: str, run_id: str) -> UniverseRow:
    return UniverseRow(
        ticker=ticker, run_id=run_id, reference_date=REF, outcome=Outcome.FAIL,
        stage="cap_band", reason="market cap 120.4M below the band floor 300.0M",
        deciding_input=StampedInput(value=1.204e8, as_of=dt.date(2026, 7, 24),
                                    source="EOD close x EDGAR XBRL shares"),
        config=BAND)


# --- the round trip: both halves ----------------------------------------------------------------


def test_rows_written_are_rows_read_back_across_both_grains(tmp_path: pathlib.Path) -> None:
    """Half one. Both grains through one file, because they SHARE a run and a reader must get each
    back as its own type rather than a lowest common shape."""
    rid = next_run_id(REF, tmp_path)
    written = [_candidate("CABA", rid), _universe("TINY", rid), _candidate("GO", rid)]
    assert append_rows(written, run_id=rid, snapshots_dir=tmp_path) == 3
    back = read_rows(rid, snapshots_dir=tmp_path)
    assert back == written, "a row did not survive the round trip"
    assert [type(r).__name__ for r in back] == ["CandidateRow", "UniverseRow", "CandidateRow"]
    # the input's OWN stamp survived, not the run's — the property the benchmark incident turned on
    assert back[0].gate_inputs["rel_ret_vs_market"].as_of == dt.date(2026, 7, 21)  # type: ignore[union-attr]
    assert back[0].reference_date == REF


def test_appending_a_run_leaves_every_prior_byte_untouched(tmp_path: pathlib.Path) -> None:
    """HALF TWO, and the property calibration depends on: a retained row a later run could edit is
    not evidence. Asserted on the BYTES, not on a re-read — a rewrite that happened to reproduce the
    same rows would pass a value comparison and still have destroyed the append-only guarantee."""
    rid = next_run_id(REF, tmp_path)
    append_rows([_candidate("CABA", rid), _universe("TINY", rid)],
                run_id=rid, snapshots_dir=tmp_path)
    before = run_path(rid, tmp_path).read_bytes()

    append_rows([_candidate("NOMD", rid)], run_id=rid, snapshots_dir=tmp_path)
    after = run_path(rid, tmp_path).read_bytes()

    assert after.startswith(before), "an append rewrote bytes that were already committed"
    assert len(after) > len(before)
    assert len(read_rows(rid, snapshots_dir=tmp_path)) == 3


def test_two_runs_on_one_reference_date_get_distinct_monotonic_ids(tmp_path: pathlib.Path) -> None:
    """A re-run after a fixed input is ordinary, and the two must be distinguishable AND orderable.
    The suffix is scanned from the directory, not counted in memory, so a partially-copied checkout
    cannot reissue an id that already has rows under it."""
    first = next_run_id(REF, tmp_path)
    append_rows([_candidate("CABA", first)], run_id=first, snapshots_dir=tmp_path)
    second = next_run_id(REF, tmp_path)
    assert (first, second) == ("2026-07-27-01", "2026-07-27-02")
    append_rows([_candidate("CABA", second)], run_id=second, snapshots_dir=tmp_path)
    assert list(list_runs(tmp_path)) == [first, second], "runs must sort oldest-first"
    assert run_path(first, tmp_path).read_bytes(), "the first run's file was disturbed"


def test_a_row_cannot_be_filed_under_another_runs_id(tmp_path: pathlib.Path) -> None:
    """Evidence attributed to the wrong screen is worse than missing evidence — it is counted."""
    rid = next_run_id(REF, tmp_path)
    stray = _candidate("CABA", "2026-07-27-09")
    with pytest.raises(ValueError, match="does not match the file"):
        append_rows([stray], run_id=rid, snapshots_dir=tmp_path)


# --- three outcomes, and the one that must never collapse ---------------------------------------


def test_not_evaluated_requires_its_reason(tmp_path: pathlib.Path) -> None:
    """THE DISTINCTION THIS GRAIN EXISTS TO KEEP. A name that could not be assessed must never look
    like one that was assessed and rejected — an unexplained NOT_EVALUATED is exactly that."""
    with pytest.raises(ValidationError, match="requires its reason"):
        _candidate("HALT", "2026-07-27-01", outcome=Outcome.NOT_EVALUATED)
    ok = _candidate("HALT", "2026-07-27-01", outcome=Outcome.NOT_EVALUATED,
                    not_evaluated_reason="only 12 bars since listing; the 70d window has no start")
    assert ok.outcome is Outcome.NOT_EVALUATED


def test_a_reason_for_a_state_the_row_is_not_in_is_refused() -> None:
    """The other direction: a stale reason left on a PASS row reads as if it applied."""
    with pytest.raises(ValidationError, match="not_evaluated_reason is set on a"):
        _candidate("CABA", "2026-07-27-01", outcome=Outcome.PASS,
                   not_evaluated_reason="left over from an earlier state")


def test_the_gate_vocabulary_maps_unknown_to_not_evaluated_not_to_fail() -> None:
    """ONE mapping, so the screen's vocabulary and retention's cannot drift. `GateResult.UNKNOWN` is
    the gate saying it had nothing to judge with — collapsing it into FAIL would poison the
    calibration population with names that were never actually tested."""
    assert outcome_from_gate(GateResult.UNKNOWN) is Outcome.NOT_EVALUATED
    assert outcome_from_gate(GateResult.PASS) is Outcome.PASS
    assert outcome_from_gate(GateResult.FAIL) is Outcome.FAIL
    # every member is mapped — a new GateResult must not fall through to a silent default
    for member in GateResult:
        assert isinstance(outcome_from_gate(member), Outcome), member


def test_a_gate_outcome_carries_the_gates_own_reason_even_on_pass() -> None:
    """A row recording only the outcome cannot later answer WHY, which is what calibration asks."""
    with pytest.raises(ValidationError, match="the gate's own reason"):
        GateOutcome(outcome=Outcome.PASS, reason="   ")


# --- stamps: the input's own, and the configuration that judged it -------------------------------


def test_a_present_input_without_its_own_as_of_is_refused() -> None:
    """The benchmark incident in one assertion: an unstamped input is how a stale benchmark passed
    for a current one. Absent values may be unstamped — that is a real state — but a present one
    may not."""
    with pytest.raises(ValidationError, match="must carry its own as-of"):
        StampedInput(value=-0.18, source="EOD derived")
    assert StampedInput(value=None, source="EOD derived").as_of is None


def test_both_grains_carry_the_configuration_that_produced_them(tmp_path: pathlib.Path) -> None:
    """Without it, comparing two runs compares two different screens and nothing says so. Asserted
    THROUGH the round trip, because a config that does not serialise is a config that is not there
    when the comparison is finally made."""
    rid = next_run_id(REF, tmp_path)
    append_rows([_candidate("CABA", rid), _universe("TINY", rid)],
                run_id=rid, snapshots_dir=tmp_path)
    cand, univ = read_rows(rid, snapshots_dir=tmp_path)
    assert cand.config.thresholds["idio_rel_max"] == -0.15  # type: ignore[union-attr]
    assert cand.config.benchmark == "IWM" and cand.config.lookback_days == 70  # type: ignore[union-attr]
    assert univ.config.market_cap_min_usd == 3e8  # type: ignore[union-attr]
    assert univ.config.exchanges == ("XNYS", "XNAS")  # type: ignore[union-attr]


def test_a_config_change_is_visible_between_two_runs(tmp_path: pathlib.Path) -> None:
    """THE POINT of stamping the config: if G2's ceiling moves off -15%, every earlier row means
    something else, and the rows must SAY so rather than leaving a reader to assume one screen."""
    r1 = next_run_id(REF, tmp_path)
    append_rows([_candidate("CABA", r1)], run_id=r1, snapshots_dir=tmp_path)
    r2 = next_run_id(REF, tmp_path)
    moved = CandidateRow(**{**_candidate("CABA", r2).model_dump(),
                            "config": CFG.model_copy(update={
                                "thresholds": {**CFG.thresholds, "idio_rel_max": -0.10}})})
    append_rows([moved], run_id=r2, snapshots_dir=tmp_path)
    a = read_rows(r1, snapshots_dir=tmp_path)[0]
    b = read_rows(r2, snapshots_dir=tmp_path)[0]
    assert a.config.thresholds["idio_rel_max"] != b.config.thresholds["idio_rel_max"]  # type: ignore[union-attr]


# --- fail loud, never quietly shrink the reject set ----------------------------------------------


def test_a_malformed_line_raises_rather_than_being_skipped(tmp_path: pathlib.Path) -> None:
    """A retention file that silently drops rows reports a SMALLER reject set than occurred, which
    biases calibration in the one direction that flatters the screen."""
    rid = next_run_id(REF, tmp_path)
    append_rows([_candidate("CABA", rid)], run_id=rid, snapshots_dir=tmp_path)
    with run_path(rid, tmp_path).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"grain": "candidate", "ticker": "BROKEN"}) + "\n")
    with pytest.raises(ValueError, match="is not a valid retention row"):
        read_rows(rid, snapshots_dir=tmp_path)


def test_an_absent_run_reads_empty_and_a_bad_run_id_raises(tmp_path: pathlib.Path) -> None:
    """An unrun run is empty; a MALFORMED id is a caller error and must not silently address a file
    outside the retention directory."""
    assert read_rows("2026-07-27-01", snapshots_dir=tmp_path) == []
    assert list(list_runs(tmp_path)) == []
    for bad in ("2026-07-27", "latest", "../escape", "2026-07-27-1"):
        with pytest.raises(ValueError, match="is not <YYYY-MM-DD>-<NN>"):
            run_path(bad, tmp_path)


def test_the_row_outcome_must_agree_with_its_gates(tmp_path: pathlib.Path) -> None:
    """REVIEW FINDING. The first cut let `outcome` be set independently of `per_gate`, so a row
    could read PASS while a gate it carries read FAIL — the record saying two things, in the one
    artifact whose purpose is to be re-read later.

    It matters more here than elsewhere: a calibration query GROUPS BY the aggregate and EXPLAINS
    with the detail, so a disagreement is not cosmetic — the analysis is silently wrong."""
    with pytest.raises(ValidationError, match="contradicts its gates"):
        CandidateRow(
            ticker="X", run_id="2026-07-27-01", reference_date=REF, outcome=Outcome.PASS,
            gate_inputs={"a": StampedInput(value=1.0, as_of=REF, source="s")},
            per_gate={"g1": GateOutcome(outcome=Outcome.FAIL, reason="failed hard")}, config=CFG)


def test_fail_dominates_and_not_evaluated_never_reads_as_a_pass() -> None:
    """The rollup order, stated as behaviour. A name that failed ANY gate failed the screen — later
    gates need not have run. A name that could not be assessed has NOT passed."""
    def g(o: Outcome) -> GateOutcome:
        return GateOutcome(outcome=o, reason="r")
    assert rollup({"a": g(Outcome.PASS), "b": g(Outcome.PASS)}) is Outcome.PASS
    assert rollup({"a": g(Outcome.PASS), "b": g(Outcome.FAIL)}) is Outcome.FAIL
    ne = rollup({"a": g(Outcome.PASS), "b": g(Outcome.NOT_EVALUATED)})
    assert ne is Outcome.NOT_EVALUATED
    # FAIL beats NOT_EVALUATED: a short-circuiting screen stops after the failure, and the name
    # was genuinely rejected rather than merely unassessable
    assert rollup({"a": g(Outcome.FAIL), "b": g(Outcome.NOT_EVALUATED)}) is Outcome.FAIL
    with pytest.raises(ValueError, match="records nothing"):
        rollup({})


def test_an_absent_gate_is_not_a_silent_pass() -> None:
    """A short-circuiting screen legitimately never reaches G3, so only gates PRESENT are judged —
    but the row must not therefore read as though the missing gate passed."""
    row = CandidateRow(
        ticker="X", run_id="2026-07-27-01", reference_date=REF, outcome=Outcome.FAIL,
        gate_inputs={"a": StampedInput(value=1.0, as_of=REF, source="s")},
        per_gate={"g1_drawdown": GateOutcome(outcome=Outcome.FAIL, reason="past terminal floor")},
        config=CFG)
    assert "g3_multiple_floor" not in row.per_gate, "an unreached gate must not be invented"
    assert row.outcome is Outcome.FAIL
