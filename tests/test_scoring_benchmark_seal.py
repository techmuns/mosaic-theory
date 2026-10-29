"""The sealed per-row benchmark, and the guard that refuses to choose.

`score_ledger` applied ONE benchmark series to every row while each row seals the one its cap band
chose at log time, and refused a resolved row that sealed another. Since 2026-10-29 each row is
measured against its own (`scoring.harness.row_benchmark`, `tests/test_per_row_benchmark.py`), and
the guard narrows to the one case left: a sealed benchmark and a committed assignment that disagree
with no operator ruling on the assignment.
"""
from __future__ import annotations

import pytest

from vinci.scoring.harness import BenchmarkMismatchError


def test_the_mismatch_is_gated_on_resolved_not_on_presence() -> None:
    """A row merely SITTING in the ledger must not block the fund's own metric: the refusal fires
    when the number would count — the moment the row resolves — and an unresolved row is held
    pending and named instead (pinned end to end in `tests/test_per_row_benchmark.py`)."""
    import inspect

    from vinci.scoring import harness

    src = inspect.getsource(harness.score_ledger)
    assert "if conflict is not None:\n            if resolved:\n                raise " \
           "BenchmarkMismatchError(" in src, (
        "the benchmark guard must be gated on `resolved` — refusing on presence blocks scoring "
        "for a number no surface reads yet")


def test_the_error_names_the_row_and_both_benchmarks() -> None:
    """A refusal a reader cannot act on is a crash with better manners."""
    e = BenchmarkMismatchError(
        "V-GOOGL sealed benchmark 'SPY' but this run applies 'IWM', and the row has now RESOLVED")
    assert "V-GOOGL" in str(e) and "SPY" in str(e) and "IWM" in str(e)


def test_it_is_a_runtime_error_so_no_caller_swallows_it_as_a_value_error() -> None:
    assert issubclass(BenchmarkMismatchError, RuntimeError)
    assert not issubclass(BenchmarkMismatchError, ValueError)


def test_an_unresolved_mismatch_does_not_raise_today() -> None:
    """GOOGL is in the committed ledger with SPY sealed (and assigned) and 199 days to run — a
    non-IWM row, the case the per-row benchmark exists for."""
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
