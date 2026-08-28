"""The sealed per-row benchmark, and the run that does not apply it.

`score_ledger` applies ONE benchmark series to every row while each row seals the one its cap band
chose at log time. Until GOOGL — the first large-cap position — every sealed value was IWM, so the
two could not disagree. They can now, and an excess return measured off the wrong series is worse
than none.
"""
from __future__ import annotations

import pytest

from vinci.scoring.harness import BenchmarkMismatchError


def test_the_mismatch_is_gated_on_resolved_not_on_presence() -> None:
    """A row merely SITTING in the ledger must not block the fund's own metric.

    The first cut refused whenever a mismatched row was PRESENT, which would have stopped
    `vinci score` outright over a bench_return nothing had yet consumed. The guard fires when the
    number would actually count — the moment the row resolves.
    """
    import inspect

    from vinci.scoring import harness

    src = inspect.getsource(harness.score_ledger)
    assert "if resolved and entry.benchmark and entry.benchmark != _applied:" in src, (
        "the benchmark guard must be gated on `resolved` — refusing on presence blocks scoring "
        "for a number no surface reads yet")
    assert "raise BenchmarkMismatchError(" in src, "the mismatch must refuse, not warn"


def test_the_error_names_the_row_and_both_benchmarks() -> None:
    """A refusal a reader cannot act on is a crash with better manners."""
    e = BenchmarkMismatchError(
        "V-GOOGL sealed benchmark 'SPY' but this run applies 'IWM', and the row has now RESOLVED")
    assert "V-GOOGL" in str(e) and "SPY" in str(e) and "IWM" in str(e)


def test_it_is_a_runtime_error_so_no_caller_swallows_it_as_a_value_error() -> None:
    assert issubclass(BenchmarkMismatchError, RuntimeError)
    assert not issubclass(BenchmarkMismatchError, ValueError)


def test_an_unresolved_mismatch_does_not_raise_today() -> None:
    """GOOGL is in the committed ledger with SPY sealed and 199 days to run.

    Scoring must still work while it is unresolved — this is the case the gating exists for.
    """
    import json
    import pathlib

    p = pathlib.Path(__file__).resolve().parents[1] / "data/snapshots/decision_ledger.jsonl"
    if not p.exists():
        pytest.skip("no committed ledger in this worktree")
    rows = [json.loads(json.loads(x)["payload"]) for x in p.read_text().splitlines() if x.strip()]
    mism = [r for r in rows if r.get("benchmark") and r["benchmark"] != "IWM"]
    assert mism, "no non-IWM row left — this guard's whole case has gone away, so retire it"
    assert all(r.get("horizon_days") for r in mism), (
        "a mismatched row with no horizon could never resolve, so the guard could never fire")
