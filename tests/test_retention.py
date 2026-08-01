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
    RunManifest,
    ScreenConfig,
    StampedInput,
    UniverseRow,
    append_rows,
    list_runs,
    next_run_id,
    outcome_from_gate,
    read_manifest,
    read_rows,
    rollup,
    run_path,
    write_manifest,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
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
        per_gate=_GATES[outcome], **kw)  # type: ignore[arg-type]


def _universe(ticker: str, run_id: str) -> UniverseRow:
    return UniverseRow(
        ticker=ticker, run_id=run_id, reference_date=REF,
        stage="cap_band", reason="market cap 120.4M below the band floor 300.0M",
        deciding_input=StampedInput(value=1.204e8, as_of=dt.date(2026, 7, 24),
                                    source="EOD close x EDGAR XBRL shares"),
)


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


def test_the_configuration_is_recorded_once_per_run_not_once_per_row(
    tmp_path: pathlib.Path) -> None:
    """The config answers "what TEST was applied?", and the answer belongs to the RUN.

    Every row carries a run_id and a row filed under another run's id is refused, so the reference
    already exists — copying the config onto ~1,800 rows buys nothing and makes a single threshold
    change read as 1,800 changes in a diff."""
    rid = next_run_id(REF, tmp_path)
    write_manifest(RunManifest(run_id=rid, reference_date=REF, screen=CFG, band=BAND,
                               stages=("out_of_band", "below_adv_floor")), snapshots_dir=tmp_path)
    append_rows([_candidate("CABA", rid), _universe("TINY", rid)],
                run_id=rid, snapshots_dir=tmp_path)
    m = read_manifest(rid, snapshots_dir=tmp_path)
    assert m is not None
    assert m.screen.thresholds["idio_rel_max"] == -0.15
    assert m.screen.benchmark == "IWM" and m.screen.lookback_days == 70
    assert m.band.market_cap_min_usd == 3e8 and m.band.exchanges == ("XNYS", "XNAS")
    # and the rows do NOT carry it — the duplication this replaced
    assert not hasattr(read_rows(rid, snapshots_dir=tmp_path)[0], "config")


def test_a_run_configuration_is_written_once_and_never_rewritten(tmp_path: pathlib.Path) -> None:
    """Rows are append-only and the manifest is write-once, so a completed run is immutable end to
    end. Rewriting the manifest would silently RE-LABEL every row already filed under it — the one
    edit that could make a whole run mean something else."""
    rid = next_run_id(REF, tmp_path)
    man = RunManifest(run_id=rid, reference_date=REF, screen=CFG, band=BAND)
    write_manifest(man, snapshots_dir=tmp_path)
    with pytest.raises(ValueError, match="written once"):
        write_manifest(man.model_copy(update={"screen": CFG.model_copy(update={
            "thresholds": {"idio_rel_max": -0.10}})}), snapshots_dir=tmp_path)


def test_a_config_change_is_visible_between_two_runs(tmp_path: pathlib.Path) -> None:
    """THE POINT of recording the config: if G2's ceiling moves off -15%, every earlier row means
    something else, and the record must SAY so rather than leaving a reader to assume one screen."""
    r1 = next_run_id(REF, tmp_path)
    write_manifest(RunManifest(run_id=r1, reference_date=REF, screen=CFG, band=BAND),
                   snapshots_dir=tmp_path)
    append_rows([_candidate("CABA", r1)], run_id=r1, snapshots_dir=tmp_path)
    r2 = next_run_id(REF, tmp_path)
    moved = CFG.model_copy(update={"thresholds": {**CFG.thresholds, "idio_rel_max": -0.10}})
    write_manifest(RunManifest(run_id=r2, reference_date=REF, screen=moved, band=BAND),
                   snapshots_dir=tmp_path)
    append_rows([_candidate("CABA", r2)], run_id=r2, snapshots_dir=tmp_path)
    a = read_manifest(r1, snapshots_dir=tmp_path)
    b = read_manifest(r2, snapshots_dir=tmp_path)
    assert a is not None and b is not None
    assert a.screen.thresholds["idio_rel_max"] != b.screen.thresholds["idio_rel_max"]


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
            per_gate={"g1": GateOutcome(outcome=Outcome.FAIL, reason="failed hard")})


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
        per_gate={"g1_drawdown": GateOutcome(outcome=Outcome.FAIL, reason="past terminal floor")})
    assert "g3_multiple_floor" not in row.per_gate, "an unreached gate must not be invented"
    assert row.outcome is Outcome.FAIL


def test_every_vinci_module_imports_standalone() -> None:
    """THE CIRCULAR IMPORT THE SUITE COULD NOT SEE.

    Wiring the thin grain put `from vinci.screens.retention import ...` at module scope in
    `vinci/universe.py` — but `vinci.screens.__init__` imports `run`, which imports
    `vinci.universe`. Importing `vinci.universe` FIRST therefore crashed, while importing
    `vinci.screens` first worked. Every test and the screen run itself happened to take the working
    order, so the suite stayed green and a real `build_universe` run was the thing that found it.

    A green suite that never imports a module in the failing order is not evidence the module
    imports. This walks the package and imports each module in a FRESH interpreter, so the order is
    the one a caller would actually use."""
    import subprocess
    import sys

    mods = sorted(
        ".".join(p.relative_to(ROOT).with_suffix("").parts).removesuffix(".__init__")
        for p in (ROOT / "vinci").rglob("*.py") if "__pycache__" not in p.parts)
    assert len(mods) > 50, f"only {len(mods)} modules discovered — the walk is near-vacuous"
    # one interpreter per module is slow; batch, but import each one FIRST in its own process
    failures = []
    probe = ("vinci.universe", "vinci.screens.retention", "vinci.screens.run",
             "vinci.orchestrator")
    for m in probe:
        r = subprocess.run([sys.executable, "-c", f"import {m}"], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"{m}: {r.stderr.strip().splitlines()[-1]}")
    assert not failures, "modules that do not import standalone:\n  " + "\n  ".join(failures)


# --- the wiring: retention must never claim rows it did not write --------------------------------


def test_partial_retention_config_is_refused_by_both_writers() -> None:
    """REVIEW FINDING, and the dangerous half is the STAT. The first cut COLLECTED rows on
    `retain_run_id` alone but only WROTE them when `retain_dir` was also set — so a caller passing
    one and not the other got ~1,800 rows built, silently discarded, and a stats dict REPORTING
    them as retained.

    A partially-configured retention that claims success is worse than one that refuses: the caller
    believes evidence exists on disk, and the absence is only discovered when someone goes looking
    for a run that was never written."""
    import datetime as _dt
    import inspect

    from vinci.screens.run import screen_universe
    from vinci.universe import build_universe

    for fn in (screen_universe, build_universe):
        src = inspect.getsource(fn)
        assert "(retain_run_id is None) != (retain_dir is None)" in src, (
            f"{fn.__name__} does not enforce both-or-neither — one without the other silently "
            "discards every retained row")
    # and the stat reports what the WRITER returned, not what was collected
    assert '"retained_candidate_rows": written,' in inspect.getsource(screen_universe)

    with pytest.raises(ValueError, match="must be given together"):
        build_universe(reference_date=_dt.date(2026, 7, 29), retain_run_id="2026-07-29-01")


def test_no_universe_drop_increments_a_stat_without_emitting_a_row() -> None:
    """THE THIN GRAIN'S INVARIANT, derived from the source rather than string-matched.

    A stage that increments a counter but appends no row MOVES the blind spot instead of closing it
    — and `build_universe`'s drops are precisely the filter nothing has ever measured. The check is
    structural: inside `build_universe`, the ONLY `stats[...] += 1` sites outside the `_drop` helper
    must be the two non-drop counters. Every genuine drop must route through `_drop`, which
    increments and appends together so the two cannot diverge.

    Two stages (`unknown_type`/`non_common_equity`) are chosen into a variable before the call, so a
    substring scan for `_drop(..., "unknown_type"` reports a false absence — the reason this parses
    instead of grepping."""
    import ast
    import inspect

    from vinci.universe import DROP_STAGES, build_universe

    assert len(DROP_STAGES) == 8, DROP_STAGES
    tree = ast.parse(inspect.getsource(build_universe).lstrip())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
              and n.name == "build_universe")
    helper = next((n for n in ast.walk(fn) if isinstance(n, ast.FunctionDef) and n.name == "_drop"),
                  None)
    assert helper is not None, "_drop is gone — nothing couples the counter to the row"
    inside = {id(n) for n in ast.walk(helper)}
    loose: list[str] = []
    for node in ast.walk(fn):
        if (isinstance(node, ast.AugAssign) and id(node) not in inside
                and isinstance(node.target, ast.Subscript)
                and isinstance(node.target.value, ast.Name) and node.target.value.id == "stats"
                and isinstance(node.target.slice, ast.Constant)):
            loose.append(str(node.target.slice.value))
    assert set(loose) <= {"considered", "in_universe"}, (
        f"these stats are incremented outside _drop: {sorted(set(loose))} — a drop that counts "
        "without emitting a row leaves that stage with no evidence trail")
    # and the guard that refuses a run when the two diverge anyway
    # matched on the literal, not across the implicit-concatenation boundary the message spans
    assert "drop path is not writing its row" in inspect.getsource(build_universe)


# --- the start anchor: a hole in the series silently widened the window --------------------------


def _bars(pairs: list[tuple[str, float]]) -> list:
    from vinci.schemas.market import PriceBar
    return [PriceBar(internal_id="X", bar_date=dt.date.fromisoformat(d), open=c, high=c, low=c,
                     close=c, volume=1.0, source="t") for d, c in pairs]


G2_REF = dt.date(2026, 7, 29)
G2_WIN = 180                       # DECLINE_WINDOW_DAYS; start = 2026-01-30
BENCH = _bars([("2026-01-30", 100.0), ("2026-07-29", 105.0)])

#: OPI's real shape from the 2026-07-29 run: the anchor sits 116d before the window start, on the
#: far side of an eight-month hole, and the "180-day" comparison actually spanned 296 days.
OPI = _bars([("2025-10-06", 0.20), ("2026-06-22", 17.00), ("2026-07-29", 17.45)])


def test_the_red_opi_is_not_evaluated_where_it_was_a_fail() -> None:
    """THE RED. `_bar_on_or_before` reached back with no limit, so OPI's start price came from
    2025-10-06 at $0.20 and the gate computed 17.45/0.20 − 1 = +8,625% over 296 days against a
    180-day threshold. A longer window means a larger |rel|, which makes the −15% bar EASIER — so
    the failure mode ADMITS names, and with the legs reversed it puts one in the pool cohort
    selection draws from.

    NOT_EVALUATED, never FAIL: the name could not be assessed on the window the threshold was
    calibrated for, and must not look like one that was assessed and rejected."""
    from vinci.eod.features import relative_return
    from vinci.screens.screen2 import Screen2Thresholds, gate_g2_idiosyncratic

    f = relative_return(OPI, BENCH, reference_date=G2_REF, lookback_days=G2_WIN)
    assert f.value is None, f"the unbounded anchor still produced {f.value}"
    assert "116d before the window start" in (f.note or ""), f.note
    assert "296d against a 180d threshold" in (f.note or ""), f.note

    class _P:
        rel_ret_vs_market = f

    class _R:
        prices = _P()

    result, why = gate_g2_idiosyncratic(_R(), Screen2Thresholds())  # type: ignore[arg-type]
    assert outcome_from_gate(result) is Outcome.NOT_EVALUATED, (result, why)


def test_a_normal_market_gap_at_the_window_start_still_evaluates() -> None:
    """The control that keeps the bound from refusing ordinary names. 593 of the 596 anchored
    exactly ON the start; a start landing on a holiday weekend must still resolve."""
    from vinci.eod.features import MAX_ANCHOR_LAG_DAYS, relative_return

    for back in range(MAX_ANCHOR_LAG_DAYS + 1):
        a = (dt.date(2026, 1, 30) - dt.timedelta(days=back)).isoformat()
        name = _bars([(a, 10.0), ("2026-07-29", 6.0)])
        r = relative_return(name, BENCH, reference_date=G2_REF, lookback_days=G2_WIN)
        assert r.value is not None, f"{back}d back was refused — inside normal market structure"
    over = (dt.date(2026, 1, 30) - dt.timedelta(days=MAX_ANCHOR_LAG_DAYS + 1)).isoformat()
    beyond = _bars([(over, 10.0), ("2026-07-29", 6.0)])
    assert relative_return(beyond, BENCH, reference_date=G2_REF,
                           lookback_days=G2_WIN).value is None


def test_a_stale_benchmark_anchor_is_refused_on_the_same_rule() -> None:
    """BOTH SIDES. A hole in the BENCHMARK's series widens the window identically, and the
    benchmark's own staleness is what made the 2026-07-27 incident invisible."""
    from vinci.eod.features import relative_return

    holed = _bars([("2025-10-06", 100.0), ("2026-07-29", 105.0)])
    name = _bars([("2026-01-30", 10.0), ("2026-07-29", 6.0)])
    r = relative_return(name, holed, reference_date=G2_REF, lookback_days=G2_WIN)
    assert r.value is None and "benchmark start anchor" in (r.note or ""), r.note


def test_the_stamp_says_what_the_number_covers_not_only_when_it_ends() -> None:
    """`as_of` is the window's END. It could not say that a "180-day" return spanned 296 days over
    28 bars — which is exactly what OPI's row claimed before the bound. Span AND bar count, both,
    because 296 days is innocuous at 124 bars and a hole at 28."""
    from vinci.eod.features import relative_return

    name = _bars([("2026-01-30", 10.0), ("2026-04-15", 8.0), ("2026-07-29", 6.0)])
    note = relative_return(name, BENCH, reference_date=G2_REF, lookback_days=G2_WIN).note or ""
    assert "spans 180d over 3 bars" in note, note
    assert "target 180d" in note, note


def test_a_window_described_by_only_one_of_span_or_bars_is_refused() -> None:
    """One without the other cannot distinguish a long-but-dense window from a holed one."""
    for kw in ({"span_days": 296}, {"observations": 28}):
        with pytest.raises(ValidationError, match="SPAN and its BAR COUNT together"):
            StampedInput(value=-0.18, as_of=REF, source="EOD derived", **kw)  # type: ignore[arg-type]
    ok = StampedInput(value=-0.18, as_of=REF, source="EOD derived", span_days=296, observations=28)
    assert (ok.span_days, ok.observations) == (296, 28)


def test_the_window_facts_have_exactly_one_implementation() -> None:
    """REVIEW FINDING. `span_days`/`observations` were computed twice — once in `relative_return`
    for the note, once in `screens.run` for the row. They agreed, which is how twin drift always
    starts; the risk was never string-parsing, it was duplication.

    Pinned on the CALL, not on a comment: `screens.run` must reach the same function the field
    uses, so a later edit to one cannot leave the row saying something the note does not."""
    import ast
    import inspect

    from vinci.eod.features import relative_return, window_facts
    from vinci.screens import run as _run

    assert _run.window_facts is window_facts, "screens.run rebound its own window_facts"
    assert not hasattr(_run, "_window_facts"), "the duplicate implementation is back"

    # STRUCTURAL, not the argument spelling. The first cut pinned the exact call text and reddened
    # when a caller legitimately renamed a variable — the seen-instances defect, one layer up. What
    # must hold is that every producer of a window description CALLS the shared function.
    for fn in (relative_return, _run._gate_inputs, _run.screen_universe):
        tree = ast.parse(inspect.getsource(fn).lstrip())
        called = {n.func.id for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        assert "window_facts" not in defined, f"{fn.__name__} defines its own window_facts"
        if fn is not _run.screen_universe:
            assert "window_facts" in called, f"{fn.__name__} no longer calls the shared helper"


def test_the_anchor_bound_clears_the_market_calendar_not_the_halt_tail() -> None:
    """REVIEW CORRECTION to the bound's stated basis. It was derived from the STORE-wide gap
    distribution, whose 5–9d tail is per-name HALTS — the very thing the bound refuses — so that
    derivation set the threshold from the population it screens out.

    The relevant gap is MARKET-WIDE. IWM and MDY agree exactly (which is what makes them the
    calendar) and neither exceeds 4d. The bound must clear that with room, and must not be so wide
    that a halt of a few weeks slips through."""
    import sqlite3

    from vinci.eod.features import MAX_ANCHOR_LAG_DAYS

    db = ROOT / "data" / "vinci.db"
    if not db.is_file():
        pytest.skip("no local store in this worktree")
    c = sqlite3.connect(db)
    worst = 0
    for sym in ("IWM", "MDY"):
        q = "select bar_date from prices where internal_id like ? order by bar_date"
        ds = [dt.date.fromisoformat(r[0]) for r in c.execute(q, (f"%-{sym}",))]
        if len(ds) < 2:
            continue
        worst = max(worst, max((b - a).days for a, b in zip(ds, ds[1:], strict=False)))
    if not worst:
        pytest.skip("no benchmark bars to measure the calendar from")
    assert worst <= MAX_ANCHOR_LAG_DAYS, (
        f"the market calendar shows a {worst}d gap but the bound is {MAX_ANCHOR_LAG_DAYS}d — every "
        "name would read unassessable after that weekend. Re-derive from the benchmark series.")
    assert 2 * worst + 2 >= MAX_ANCHOR_LAG_DAYS, (
        f"bound {MAX_ANCHOR_LAG_DAYS}d is far wider than the {worst}d market gap it must clear — "
        "a wide bound admits the halted windows this exists to refuse")


# --- G1's reach-back: the drawdown is a ratio to `latest`, however old that is -------------------


G1_REF = dt.date(2026, 7, 29)
#: INHD's real shape from the run: bars stop 2026-06-08, 51 days before the reference, and G1
#: computed a drawdown against that close and recorded FAIL.
INHD = _bars([("2025-06-02", 40.0), ("2026-01-15", 30.0), ("2026-06-08", 12.0)])


def _g1(bars: list, staleness: int = 5) -> tuple:
    from vinci.eod.features import compute_price_features
    from vinci.screens.screen2 import Screen2Thresholds, gate_g1_drawdown

    feats = compute_price_features(bars, reference_date=G1_REF, staleness_days=staleness)

    class _R:
        prices = feats

    return gate_g1_drawdown(_R(), Screen2Thresholds()), feats  # type: ignore[arg-type]


def test_the_red_a_stale_latest_bar_is_not_evaluated_where_it_was_a_fail() -> None:
    """THE RED. `drawdown_from_high` is `latest.close / hi - 1` and G1 gates on it, so a name whose
    bars stopped weeks ago is judged on a price from that day while the gate treats the answer as
    current. INHD ran on a 2026-06-08 close, 51 days stale, and was recorded FAIL — assessed and
    rejected, when it could not be assessed at all."""
    (result, why), feats = _g1(INHD)
    assert feats.drawdown_from_high.value is None, "the stale drawdown still produced a value"
    assert outcome_from_gate(result) is Outcome.NOT_EVALUATED, (result, why)
    note = feats.drawdown_from_high.note or ""
    assert "51d before the 2026-07-29 reference" in note, note
    assert "presented as current" in note, note


def test_a_bar_inside_the_staleness_contract_still_evaluates() -> None:
    """The control. 1,778 of the 1,780 names had a same-day bar; the bound must not touch them, and
    must still clear a holiday weekend — IWM and MDY agree exactly and neither gap exceeds 4d."""
    from vinci.config import get_config

    contract = get_config().price_staleness_days
    for age in range(contract + 1):
        d = (G1_REF - dt.timedelta(days=age)).isoformat()
        (result, _), feats = _g1(_bars([("2025-06-02", 40.0), ("2026-01-15", 30.0), (d, 12.0)]))
        assert feats.drawdown_from_high.value is not None, f"{age}d refused, in contract"
        assert outcome_from_gate(result) is Outcome.PASS
    over = (G1_REF - dt.timedelta(days=contract + 1)).isoformat()
    _, feats = _g1(_bars([("2025-06-02", 40.0), ("2026-01-15", 30.0), (over, 12.0)]))
    assert feats.drawdown_from_high.value is None


def test_the_bound_is_the_shipped_contract_not_a_new_constant() -> None:
    """It is not a number picked for this fix. `staleness_days` already existed and was already
    applied to `last`; the defect was that the DERIVED ratio G1 gates on ignored it. Pinned so a
    later edit cannot fork a second staleness rule for the same input."""
    from vinci.config import get_config
    from vinci.eod.features import compute_price_features

    assert get_config().price_staleness_days == 5
    # STRUCTURAL, not a source-text count (review finding — a `src.count(...) == 2` pin reds on any
    # rename or restructure, which is the brittleness just removed from the window_facts pin one PR
    # earlier). The property: BOTH the `last` field and the derived ratio must change behaviour at
    # the SAME threshold, proven by moving it.
    bars = _bars([("2025-06-02", 40.0), ("2026-01-15", 30.0), ("2026-07-19", 12.0)])  # 10d stale
    tight = compute_price_features(bars, reference_date=G1_REF, staleness_days=5)
    loose = compute_price_features(bars, reference_date=G1_REF, staleness_days=30)
    assert tight.drawdown_from_high.value is None and tight.last.value is not None
    assert "10d old" in (tight.last.note or ""), tight.last.note
    assert loose.drawdown_from_high.value is not None, "the ratio ignored a widened contract"
    assert not (loose.last.note or "").startswith("10d old")


def test_the_stale_drawdown_records_its_window_via_the_shared_helper() -> None:
    """Span and count come from `window_facts` — the one implementation consolidated in #294. This
    class recurred on the fix after it, which is why it is pinned here too."""
    import inspect

    from vinci.eod.features import compute_price_features, window_facts
    from vinci.screens import run as _run

    src = inspect.getsource(compute_price_features)
    assert "window_facts(" in src and "def window_facts" not in src
    assert _run.window_facts is window_facts
    _, feats = _g1(INHD)
    assert "spans" in (feats.drawdown_from_high.note or "")


def test_each_input_is_described_by_its_own_window() -> None:
    """G2 compares over the decline window, G1 over 52 weeks. One start for both would mis-describe
    whichever it did not belong to — the stamp-names-a-different-object class."""
    import inspect

    from vinci.screens import run as _run

    src = inspect.getsource(_run.screen_universe)
    assert '"rel_ret_vs_market": reference_date - timedelta(days=DECLINE_WINDOW_DAYS)' in src
    assert '"drawdown_from_high": reference_date - timedelta(days=YEAR_DAYS)' in src


def test_an_unresolvable_window_says_so_rather_than_reporting_zeros() -> None:
    """REVIEW FINDING. `window_facts` returns None when no bar sits at or before the window start —
    reachable whenever `have_year` is met by a span beginning INSIDE the 52-week window — and the
    first cut defaulted to (0, 0), printing "spans 0d over 0 bars". That reads as a MEASURED empty
    window rather than a measurement that could not be made: a fabricated zero, inside the fix for
    a mislabelled value."""
    from vinci.eod.features import compute_price_features

    # span 340d (clears the 330d history rule) but the first bar is after ref−365, and 13d stale
    bars = _bars([("2025-08-10", 40.0), ("2026-03-01", 20.0), ("2026-07-16", 12.0)])
    note = compute_price_features(
        bars, reference_date=G1_REF, staleness_days=5).drawdown_from_high.note or ""
    assert "spans 0d over 0 bars" not in note, note
    assert "window not resolvable" in note and "2025-07-29" in note, note


# --- G3 recorded a PASS for every name it could not value ----------------------------------------


def _g3(pe_note: str | None, pctile: float | None = None) -> tuple:
    from vinci.schemas.envelope import DataField, SourceTier
    from vinci.screens.screen2 import Screen2Thresholds, gate_g3_multiple_floor

    u: DataField[float] = (
        DataField.present(pctile, as_of=REF, source="EDGAR", tier=SourceTier.DERIVED)
        if pctile is not None
        else DataField.unknown(source="EDGAR", tier=SourceTier.DERIVED, note=pe_note))
    ev: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.DERIVED, note="EV/EBITDA deferred")

    class _F:
        ev_ebitda_pctile_vs_history = ev
        pe_pctile_vs_history = u

    class _R:
        fundamentals = _F()

    return gate_g3_multiple_floor(_R(), Screen2Thresholds())  # type: ignore[arg-type]


def test_the_red_a_name_with_no_valuation_is_not_evaluated_not_passed() -> None:
    """THE RED. G3 returns UNKNOWN when nothing values the name and the runner admits it anyway —
    so **186 of the 281 in the 2026-07-29 pool were never valued at all and every one passed**.
    UNKNOWN maps to NOT_EVALUATED, so the row must record that the name could not be assessed."""
    from vinci.screens.assemble import G3_NO_INPUT

    result, why = _g3(G3_NO_INPUT)
    assert outcome_from_gate(result) is Outcome.NOT_EVALUATED, (result, why)
    assert outcome_from_gate(result) is not Outcome.PASS


def test_each_cause_carries_its_own_reason() -> None:
    """THREE CAUSES, THREE REASONS, because a reader acts differently on each: nothing tagged is a
    DATA gap, negative-throughout is an ANSWER about the business, a short history is a TIMING
    state that resolves by waiting. Measured across the 412 reaching G3: 48 / 85 / 49.

    One reason covering two causes would put 'we have no data' and 'the company has never earned
    anything' behind the same label."""
    from vinci.screens.assemble import (
        G3_NEGATIVE_ECONOMICS,
        G3_NO_INPUT,
        G3_SHORT_HISTORY,
    )

    reasons = {G3_NO_INPUT, G3_NEGATIVE_ECONOMICS, G3_SHORT_HISTORY}
    assert len(reasons) == 3, "two causes collapsed onto one reason"
    for r in reasons:
        result, why = _g3(r)
        assert outcome_from_gate(result) is Outcome.NOT_EVALUATED
        assert why == r, f"the gate restated the reason instead of forwarding it: {why!r}"
    # and the distinction is legible, not just distinct strings
    assert "not a gap in the data" in G3_NEGATIVE_ECONOMICS
    assert "no diluted EPS in the filing history" in G3_NO_INPUT
    assert "too short" in G3_SHORT_HISTORY


def test_a_resolved_percentile_still_passes_and_fails_normally() -> None:
    """The control: labelling the unvaluable must not change the 226 that got a real judgment."""
    from vinci.screens.screen2 import Screen2Thresholds

    floor = Screen2Thresholds().multiple_floor_pctile
    assert outcome_from_gate(_g3(None, pctile=floor - 0.05)[0]) is Outcome.PASS
    assert outcome_from_gate(_g3(None, pctile=floor + 0.05)[0]) is Outcome.FAIL


def test_the_row_records_the_gates_result_not_the_admission() -> None:
    """The silent pass ONE LAYER ALONG. The row wrote PASS whenever a candidate was produced, so a
    name G3 could not value was recorded as having passed G3. Routing is not decided here — the
    runner still admits it — so the two are recorded as SEPARATE gates and whoever chooses the
    routing can count both from the same rows."""
    import inspect

    from vinci.screens.run import screen_universe

    src = inspect.getsource(screen_universe)
    assert 'gates["g3_multiple_floor"]' in src and "outcome_from_gate(g3)" in src
    assert 'gates["admitted"]' in src, "admission is no longer recorded at all"
    assert '"g3_and_distress"' not in src, "the conflated gate is back"


def test_the_reason_taxonomy_is_exhaustive_no_inline_fourth() -> None:
    """REVIEW FINDING. The gate emitted a FOURTH reason — "no price at the reference date" — as an
    inline literal: not a named constant, not counted in the population split, not covered by the
    three-causes pin. An un-named reason is a cause the taxonomy does not know about, so it escapes
    both the exhaustiveness check and the count.

    Pinned structurally: every string literal assigned to `why`, plus the note prefix, must come
    from `G3_REASONS`."""
    import ast
    import inspect

    from vinci.screens import assemble as asm

    src = inspect.getsource(asm.pe_current_and_percentile)
    tree = ast.parse(src.lstrip())
    inline = [n.value.value for n in ast.walk(tree)
              if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
              and isinstance(n.value.value, str)
              and any(isinstance(t, ast.Name) and t.id == "why" for t in n.targets)]
    assert not inline, f"a reason is an inline literal, outside the taxonomy: {inline}"
    # five since the EPS bound added G3_EPS_TOO_OLD — the pin caught the taxonomy growing,
    # which is what it is for
    assert len(set(asm.G3_REASONS)) == 5, asm.G3_REASONS
    for r in asm.G3_REASONS:
        assert r.strip(), "an empty reason is not a reason"


# --- the record must not claim a judgment that was never made -----------------------------------


def test_a_universe_row_cannot_claim_an_outcome() -> None:
    """REVIEW OF #296, applied. `UniverseRow.outcome` was the constant FAIL on all 5,871 rows of a
    run — only DROPS emit a universe row, so the field carried no information and actively misled:
    a name filtered by the cap band was never assessed by a gate, and FAIL reads as a judgment the
    screen made.

    NOT_EVALUATED would be wrong in the other direction — the band rule DID assess it, just not
    against the gates. `stage` + `reason` + `deciding_input` already say what happened, so the
    field is gone rather than set to a less-wrong constant."""
    assert "outcome" not in UniverseRow.model_fields, (
        "a universe row can report an outcome again — the constant that carried no information")
    assert "not_evaluated_reason" not in UniverseRow.model_fields
    for f in ("stage", "reason", "deciding_input"):
        assert f in UniverseRow.model_fields, f
    # the candidate grain keeps both, because its gates genuinely decided
    assert "outcome" in CandidateRow.model_fields
    assert "not_evaluated_reason" in CandidateRow.model_fields


def test_the_g3_resolved_count_reads_the_gate_not_the_capability() -> None:
    """#296 PUBLISHED CAPABILITY, NOT THE GATE. It reported 230 resolving / 182 not, the UNION of
    the P/E and EV/EBITDA paths. But `gate_g3_multiple_floor` reads `ev_ebitda_pctile_vs_history`,
    which `enrich_with_fundamentals` sets UNKNOWN unconditionally — so EV/EBITDA never decides and
    the gate's own figure is 226 / 186. The four-name difference is ENPH, IDR, LAND, TRUP.

    Pinned on the CODE: as long as the EV field is unconditionally UNKNOWN, any count that credits
    it is counting a path that cannot fire."""
    import inspect

    from vinci.screens.assemble import enrich_with_fundamentals

    src = inspect.getsource(enrich_with_fundamentals)
    assert "ev_ebitda_pctile_vs_history=ev_unknown" in src, (
        "EV/EBITDA now resolves — the gate's count is no longer P/E-only and STATE's 226/186 "
        "must be re-measured on the union")
    assert "ev_unknown: DataField[float] = DataField.unknown(" in src


def test_a_retired_key_is_dropped_only_when_it_held_nothing(tmp_path: pathlib.Path) -> None:
    """REVIEW FINDING on the removal itself. Pydantic's default is `extra="ignore"`, so removing
    `UniverseRow.outcome` meant 5,871 committed rows per run read CLEAN with the field silently
    vanishing. Fine for a field that was the constant FAIL; catastrophic for one that held data —
    and `scenarios.RETIRED_VERDICT_FIELDS` already refuses exactly this class.

    Retention cannot simply raise: the committed rows ARE the evidence, and making them unreadable
    to protect them is self-defeating. So the rule is narrower — a retired key is dropped silently
    only when it carries the value it always carried, and anything else raises."""
    from vinci.screens.retention import RETIRED_ROW_FIELDS

    assert RETIRED_ROW_FIELDS["universe"] == {"outcome": "FAIL"}
    rid = next_run_id(REF, tmp_path)
    append_rows([_universe("TINY", rid)], run_id=rid, snapshots_dir=tmp_path)
    path = run_path(rid, tmp_path)

    legacy = json.loads(path.read_text().strip())
    # the shape every committed row has: the retired key at its only-ever value
    path.write_text(json.dumps({**legacy, "outcome": "FAIL"}) + "\n")
    assert len(read_rows(rid, snapshots_dir=tmp_path)) == 1, "a legacy row became unreadable"

    # and a retired key holding something else is a key that carried real data
    path.write_text(json.dumps({**legacy, "outcome": "PASS"}) + "\n")
    with pytest.raises(ValueError, match="held real data"):
        read_rows(rid, snapshots_dir=tmp_path)


def test_the_committed_run_still_reads_after_the_field_was_removed() -> None:
    """The corpus check the schema change needed: 5,871 universe rows on disk carry `outcome`, and
    the removal must not have made the committed evidence unreadable."""
    from vinci.config import get_config

    d = get_config().snapshots_dir / "screen_runs"
    if not (d / "2026-07-29-01.jsonl").is_file():
        pytest.skip("no committed retention run in this worktree")
    rows = read_rows("2026-07-29-01", snapshots_dir=get_config().snapshots_dir)
    univ = [r for r in rows if r.grain == "universe"]
    assert len(univ) > 5_000, f"only {len(univ)} universe rows read back"


# --- the EPS reach-back: valuing a company on pre-loss earnings ----------------------------------


def _eps(rows: list[tuple[str, str, float]]) -> list:
    """(period_end, filed, value) -> annual ConceptPoints."""
    from vinci.edgar.concepts import ConceptPoint
    return [ConceptPoint(concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares",
                         value=v, period_start=dt.date.fromisoformat(pe).replace(
                             year=dt.date.fromisoformat(pe).year - 1),
                         period_end=dt.date.fromisoformat(pe), filed=dt.date.fromisoformat(f),
                         fy=None, fp="FY", form="10-K", accession=None)
            for pe, f, v in rows]


EPS_REF = dt.date(2026, 7, 29)
#: The defect's shape: profitable through 2021, loss-making since. The unbounded reader reaches
#: back to the 2021 figure and prices the company on earnings it no longer reports.
PRE_LOSS = _eps([("2021-12-31", "2022-02-20", 3.10),
                 ("2022-12-31", "2023-02-20", -1.40),
                 ("2025-12-31", "2026-02-20", -2.05)])


def test_the_red_a_pre_loss_eps_is_out_of_range() -> None:
    """THE RED. `annual_eps_as_of` takes the latest POSITIVE annual figure, so a name loss-making
    for years is valued on pre-loss earnings — measured p90 4.8 years, max 16.6. The 2021 figure is
    1,671 days past its period end at the reference date, well beyond one filing cycle."""
    from vinci.screens.assemble import MAX_EPS_AGE_DAYS, annual_eps_as_of

    assert annual_eps_as_of(PRE_LOSS, EPS_REF, max_age_days=10**6) == 3.10, "fixture is wrong"
    assert annual_eps_as_of(PRE_LOSS, EPS_REF) is None, (
        f"the {MAX_EPS_AGE_DAYS}d bound did not refuse a 1,671-day-old figure")


def test_the_bound_clears_a_late_filer_and_refuses_the_next_period_back() -> None:
    """DERIVED FROM THE FILING CADENCE, both directions. 470 = 365 annual period + 90 statutory
    10-K deadline + 15 NT extension; the next-older annual figure sits at 730d, so the bound must
    sit strictly between and cannot be reached by a filer who is merely late."""
    from vinci.screens.assemble import MAX_EPS_AGE_DAYS, annual_eps_as_of

    assert MAX_EPS_AGE_DAYS == 470
    assert MAX_EPS_AGE_DAYS == 365 + 105, "the derivation no longer adds up"
    assert MAX_EPS_AGE_DAYS < 730, "the bound reaches the next annual period — it cannot"
    # a maximally late filer: FY ended 365d ago, filed 90d late, +15d extension
    late = _eps([((EPS_REF - dt.timedelta(days=MAX_EPS_AGE_DAYS)).isoformat(),
                  (EPS_REF - dt.timedelta(days=30)).isoformat(), 1.25)])
    assert annual_eps_as_of(late, EPS_REF) == 1.25, "a filer inside the statutory window refused"
    older = _eps([((EPS_REF - dt.timedelta(days=MAX_EPS_AGE_DAYS + 1)).isoformat(),
                   (EPS_REF - dt.timedelta(days=30)).isoformat(), 1.25)])
    assert annual_eps_as_of(older, EPS_REF) is None


def test_out_of_range_is_not_evaluated_and_names_its_own_cause() -> None:
    """NOT_EVALUATED, never PASS or FAIL — and distinct from `G3_NEGATIVE_ECONOMICS`. That name has
    NEVER earned anything; this one HAS, but the last positive year is too far back to describe the
    business now. They resolve differently: one needs a different valuation basis, the other needs
    the company to file again."""
    from vinci.schemas.market import PriceBar
    from vinci.screens.assemble import (
        G3_EPS_TOO_OLD,
        G3_NEGATIVE_ECONOMICS,
        pe_current_and_percentile,
    )

    bars = [PriceBar(internal_id="X", bar_date=EPS_REF, open=9.0, high=9.0, low=9.0, close=9.0,
                     volume=1.0, source="t")]
    pe, pctile = pe_current_and_percentile(bars, PRE_LOSS, reference_date=EPS_REF)
    assert pe.value is None and pctile.value is None
    assert pe.note == G3_EPS_TOO_OLD, pe.note
    assert G3_EPS_TOO_OLD != G3_NEGATIVE_ECONOMICS

    # a name that never earned anything keeps the OTHER reason
    never = _eps([("2025-12-31", "2026-02-20", -2.05)])
    pe2, _ = pe_current_and_percentile(bars, never, reference_date=EPS_REF)
    assert pe2.note == G3_NEGATIVE_ECONOMICS, pe2.note


def test_the_bound_lives_in_the_shared_reader_so_both_consumers_get_it() -> None:
    """TWO CONSUMERS: `enrich_with_fundamentals` (G3) and `cli.py`'s `_pc_valuation` peer-cohort
    command, both reaching `annual_eps_as_of` through `pe_current_and_percentile`. Bounding at the
    gate alone would have left the peer-cohort command valuing names on sixteen-year-old earnings.

    Pinned on the DEFAULT: neither caller can opt out by omission, and no call site may widen it."""
    import inspect

    from vinci.screens import assemble as asm

    sig = inspect.signature(asm.annual_eps_as_of)
    assert sig.parameters["max_age_days"].default == asm.MAX_EPS_AGE_DAYS, (
        "the bound is no longer the default — a caller that omits it reaches back forever")
    # no production call site may pass a wider age; the only widened calls are the cause-split
    # probe inside pe_current_and_percentile (which asks 'did a positive figure EXIST at all')
    # STRUCTURAL, not the call's source text (review finding — a hard-matched literal is the
    # brittleness this session has removed twice already). Parse the module: every call that
    # widens the bound must pass the explicit `None` sentinel, and there may be exactly one —
    # the cause-split probe asking "did a positive figure exist AT ALL".
    import ast

    tree = ast.parse(inspect.getsource(asm))
    widened = [n for n in ast.walk(tree)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "annual_eps_as_of"
               and any(k.arg == "max_age_days" for k in n.keywords)]
    assert len(widened) == 1, f"{len(widened)} call sites override the bound; expected 1"
    kw = next(k for k in widened[0].keywords if k.arg == "max_age_days")
    assert isinstance(kw.value, ast.Constant) and kw.value.value is None, (
        "the unbounded sentinel is not the explicit `None` — a magic number here is a bound "
        "a reader cannot check")


# --- routing must state its policy ----------------------------------------------------------------


def test_the_policy_exists_with_two_values_and_carry_is_the_default() -> None:
    """ONE SETTING, TWO VALUES. The gates already record NOT_EVALUATED; this is the separate
    question of whether such a name enters the candidate set. CARRY is today's behaviour exactly,
    so the -03 run reproduces — making it a named setting changes nothing about what the screen
    does, it makes what the screen does STATEABLE."""
    import inspect

    from vinci.schemas.candidate import RoutingPolicy
    from vinci.screens.run import screen_universe
    from vinci.screens.screen2 import evaluate_screen2

    assert [p.value for p in RoutingPolicy] == ["carry_not_evaluated", "drop_not_evaluated"]
    for fn in (evaluate_screen2, screen_universe):
        d = inspect.signature(fn).parameters["policy"].default
        assert d is RoutingPolicy.CARRY, f"{fn.__name__} default is {d!r}, not CARRY"


def test_drop_refuses_to_forward_or_admit_a_gate_that_could_not_judge() -> None:
    """BOTH "not FAIL" POINTS. G2's forward read `g2 is FAIL` — so a G2 returning UNKNOWN sent the
    name on to G3 (3 names did on the 2026-07-29 run). And the admit test read
    `FAIL not in results` — so a G3 that could not value admitted (282 of the 331).

    Under DROP each requires an actual PASS. Pinned on the SOURCE of both, since the two live in
    different modules and a fix to one would otherwise look complete."""
    import inspect

    from vinci.screens.run import screen_universe
    from vinci.screens.screen2 import evaluate_screen2

    fwd = inspect.getsource(screen_universe)
    assert ("if g2 is GateResult.FAIL or (policy is RoutingPolicy.DROP "
            "and g2 is not GateResult.PASS):") in fwd, "the G2 forward ignores the policy"
    adm = inspect.getsource(evaluate_screen2)
    assert "if policy is RoutingPolicy.DROP:" in adm, "the admit test ignores the policy"
    assert "all(r is GateResult.PASS for r in results.values())" in adm, (
        "DROP must require every gate to have actually PASSED, not merely not-FAILed")


def test_the_manifest_records_which_policy_the_run_used() -> None:
    """A POOL COUNT MEANS NOTHING WITHOUT IT — 331 and 49 are the same screen under different
    routing. Defaulted to CARRY so a manifest written before the field reads as what that run
    actually did, rather than as unknown."""
    from vinci.schemas.candidate import RoutingPolicy
    from vinci.screens.retention import RunManifest

    assert "routing_policy" in RunManifest.model_fields
    m = RunManifest(run_id="2026-07-29-09", reference_date=REF, screen=CFG, band=BAND)
    assert m.routing_policy is RoutingPolicy.CARRY
    moved = RunManifest(run_id="2026-07-29-09", reference_date=REF, screen=CFG, band=BAND,
                        routing_policy=RoutingPolicy.DROP)
    assert moved.routing_policy is RoutingPolicy.DROP
    assert "routing_policy" in moved.model_dump_json(), "the policy is not serialised"


def test_detection_refuses_to_overwrite_the_pointer_without_an_archive() -> None:
    """THE ARCHIVE PROTECTED NOTHING. `candidate_themes.jsonl` — the only committed cluster file —
    was overwritten BEFORE the immutable snapshot was written, and `data/scan_history/` was
    git-ignored, so "a monthly sweep must never clobber the prior harvest" described an intent the
    sequence did not implement.

    Archive first, pointer last, and `--no-scan-history` with a write is refused outright."""
    import inspect

    from vinci import cli

    src = inspect.getsource(cli._cmd_themes)
    assert "if not args.no_write and args.no_scan_history:" in src
    assert "REFUSED:" in src and "no immutable snapshot kept" in src
    # ORDER: the archive call must precede the pointer write
    assert src.index("record_snapshot(") < src.index('"candidate_themes.jsonl"'), (
        "the pointer is still written before the snapshot is secured")


def test_the_scan_history_archive_is_tracked() -> None:
    """It was git-ignored, so the archive standing behind the pointer kept nothing."""
    import subprocess

    keep = ROOT / "data" / "scan_history" / "README.md"
    assert keep.is_file(), "the archive directory is not present"
    r = subprocess.run(["git", "check-ignore", "-q", str(keep)], cwd=ROOT)
    assert r.returncode != 0, "data/scan_history/ is still git-ignored — it keeps nothing"
