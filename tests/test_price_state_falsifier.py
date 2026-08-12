"""The R3 waiting-cost accounting — a never-entered book holds CASH, not the benchmark.

REVIEW FINDING (#405). The first cut recorded `0.0` as the deferred strategy's excess whenever the
50d-MA reclaim never landed inside the exit window. That claims a cash position MATCHED MDY. It
does not: cash returns 0% while MDY moves, so the excess is minus MDY's return.

Why it mattered rather than being a rounding detail: the error's SIGN follows the market. In a
rising tape it credits the deferred book with MDY's gain it never earned, flattering "wait for the
reclaim" — and 2023–2026 rose, which is the direction of the conclusion R3 reported. A measurement
whose bias points at its own finding has to be pinned, not just fixed.

The up-market case is the regression the review asked for; the down-market case is its mirror and
guards against over-correcting into a blanket penalty.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "price_state_falsifier.py"


def _falsifier() -> ModuleType:
    """Import by path — `scripts/` is not a package and must not become one just for a test."""
    if not SCRIPT.exists():
        pytest.skip("price_state_falsifier.py not in this worktree")
    spec = importlib.util.spec_from_file_location("_psf", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_psf"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_never_entering_in_an_up_market_is_penalised_by_the_benchmark_it_missed() -> None:
    """THE REGRESSION. MDY +10% over the window, the name never reclaims, so the book sat in cash.
    Its excess is −10, not 0 — the old code handed it the market's gain for free."""
    m = _falsifier()
    a = [100.0] * 20          # the name's path is irrelevant when the book never enters
    mdy = [100.0] * 20
    mdy[10] = 110.0           # +10% from i=0 to j=10
    assert m.deferred_excess(a, mdy, 0, 10, None) == pytest.approx(-10.0)
    # a reclaim that lands AFTER the exit is the same "never entered" case
    assert m.deferred_excess(a, mdy, 0, 10, 12) == pytest.approx(-10.0)


def test_never_entering_in_a_down_market_is_credited_for_holding_cash() -> None:
    """The mirror, so the fix is an accounting correction and not a blanket penalty on waiting:
    when MDY falls 20%, sitting in cash genuinely beat the benchmark by 20 points."""
    m = _falsifier()
    a = [100.0] * 20
    mdy = [100.0] * 20
    mdy[10] = 80.0
    assert m.deferred_excess(a, mdy, 0, 10, None) == pytest.approx(+20.0)


def test_an_actual_delayed_entry_is_marked_from_the_reclaim_not_from_appearance() -> None:
    """When the reclaim DOES land inside the window the book is live from `r_idx`, so both legs are
    measured from there — the shorter benchmark is correct only in this branch."""
    m = _falsifier()
    a = [100.0] * 20
    a[5], a[10] = 90.0, 108.0     # entered at 90, exited at 108 -> +20%
    mdy = [100.0] * 20
    mdy[5], mdy[10] = 100.0, 105.0  # benchmark +5% over the SAME held window
    assert m.deferred_excess(a, mdy, 0, 10, 5) == pytest.approx(15.0)


def test_a_delisted_name_after_a_real_entry_is_carried_at_a_total_loss() -> None:
    """A missing bar at the exit is a real loss, never a dropped observation — the same rule the
    rest of the falsifier uses. −100% raw, less whatever the benchmark did."""
    m = _falsifier()
    a = [100.0] * 20
    a[5], a[10] = 90.0, 0.0
    mdy = [100.0] * 20
    mdy[5], mdy[10] = 100.0, 104.0
    assert m.deferred_excess(a, mdy, 0, 10, 5) == pytest.approx(-104.0)
