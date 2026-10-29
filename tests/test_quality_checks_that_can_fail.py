"""THE SCORECARD'S CHECKS SAY WHAT THEY CAN SUPPORT (audit BC-D9, BC-D11; BC-D10 is pinned on the
real export format in `tests/test_ciq_reader_contract.py`).

BC-D9 — `market_cap_share_basis` scored CONFIRMED at ANY gap between the page's market cap and its
price times its shares that was not a whole-number ratio: 27 of 27 committed pages read confirmed,
MVST at +57.1%. A whole-number ratio is a share-basis change, which the check DOES detect; a gap of
any other size is price drift or something else, which it cannot tell apart, so it is UNCHECKED.
Only a gap inside `freshness.RECONCILE_TOLERANCE` — the repo's own line for "the cap and the spot
describe the same equity" — is CONFIRMED. And a 1,000x ratio is a UNIT error, not the corporate
action the whole-number rule names.

BC-D11 — the core built each row from the four known statuses, so a check returning an unknown key
('confirmd') had its units dropped from the row and the fleet with no error.

The page inputs below are FROZEN literals of the committed pages' `stock_info` (2026-10-29,
bb4ab6e5) — a value-level pin on a re-drawn artifact would rot at the next rebuild.
"""
from __future__ import annotations

from typing import Any

import pytest

from vinci.quality import core
from vinci.quality.core import (
    CONFIRMED,
    DIFFERS_STATED,
    DIFFERS_UNEXPLAINED,
    UNCHECKED,
    Check,
    ItemResult,
)
from vinci.quality.sources import ciq


def _page(cap_musd: float, shares: float, spot: float) -> dict[str, Any]:
    return {"ticker": "X", "mechanical": {"stock_info": {
        "market_cap": {"value": cap_musd}, "shares_out": {"value": shares},
        "price": {"value": spot}}}}


#: (market cap $M, shares out, price) as committed, 2026-10-29
MVST = (353.8, 384534486.0, 0.5856)      # implies $0.920 against $0.5856: +57.1%
AORT = (1136.0, 48756221.0, 23.3)        # implies $23.30: +0.0%
IT = (11090.6, 63148976.0, 179.19)       # implies $175.63: -1.99%


def test_a_gap_that_is_not_a_share_basis_change_is_unchecked_never_confirmed() -> None:
    """BC-D9 on MVST's committed figures: +57.1% is no whole-number ratio, and the check cannot
    tell price drift from a wrong cap — so it confirms nothing."""
    assert ciq._market_cap_share_basis(_page(*MVST)).counts == {UNCHECKED: 1}


@pytest.mark.parametrize("inputs", [AORT, IT], ids=["AORT +0.0%", "IT -1.99%"])
def test_a_cap_that_reconciles_inside_the_tolerance_is_still_confirmed(
        inputs: tuple[float, float, float]) -> None:
    """NEGATIVE PIN: a cap that IS the price times the shares, within `RECONCILE_TOLERANCE`,
    confirms."""
    assert ciq._market_cap_share_basis(_page(*inputs)).counts == {CONFIRMED: 1}


@pytest.mark.parametrize(("spot_over_implied", "want"), [
    (1.015, CONFIRMED),            # inside the 2% line
    (1.025, UNCHECKED),            # just past it
    (0.80, UNCHECKED),
    (2.0, DIFFERS_STATED),         # a 2-for-1 between the panels: the stated reason
    (1 / 11, DIFFERS_STATED),      # FUBO's ~11x reverse split, the other way up
    (1000.0, DIFFERS_UNEXPLAINED),  # a thousands-vs-millions unit error is not a corporate action
    (0.001, DIFFERS_UNEXPLAINED),
])
def test_each_gap_scores_what_the_check_can_support(spot_over_implied: float, want: str) -> None:
    implied = 50.0
    shares = 10_000_000.0
    page = _page(implied * shares / 1e6, shares, implied * spot_over_implied)
    assert ciq._market_cap_share_basis(page).counts == {want: 1}


def _check(result: ItemResult) -> Check:
    return Check("c", "t", "s", "s2", core.INDEPENDENT, "page", "tol", "pop", None, None, (),
                 lambda _item: result)


def test_an_unknown_status_key_is_refused_never_dropped() -> None:
    """BC-D11: a check returning 'confirmd' had its unit silently left out of the row and the
    fleet. A key outside the four statuses names the check, the item and the key."""
    with pytest.raises(ValueError, match=r"'c'.*'X'.*'confirmd'"):
        core._score_check(_check(ItemResult(counts={"confirmd": 1})), {"X": {}})


def test_the_four_statuses_still_score() -> None:
    """NEGATIVE PIN: every known status counts, nothing raises."""
    got = core._score_check(_check(ItemResult(counts=dict.fromkeys(core.STATUSES, 1))), {"X": {}})
    assert all(got["fleet"][s] == 1 for s in core.STATUSES)
