"""Step 2 verification — universe-builder pure logic + the universe-membership lookup."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from mosaic.schemas.envelope import DataField, SourceTier
from mosaic.store import Store
from mosaic.universe import benchmark_identity, recent_share_periods


def test_recent_share_periods() -> None:
    keys = recent_share_periods(date(2026, 6, 12))
    assert len(keys) == 5
    assert all(k.startswith("CY") and k.endswith("I") for k in keys)
    assert keys == sorted(keys, key=lambda k: (k[2:6], k[7]))  # oldest → newest
    # most recent quarter-end with a filing-lag buffer is 2026-03-31 (filed by ~May)
    assert keys[-1] == "CY2026Q1I"


def test_benchmark_identity_is_not_a_sec_issuer() -> None:
    b = benchmark_identity("IWM")
    assert b.internal_id == "IDX-IWM" and b.cik == "" and b.eod_symbol == "IWM"


def test_latest_universe_picks_most_recent_snapshot(tmp_path: Path) -> None:
    cap = DataField.present(1e9, as_of=date(2026, 1, 1), source="DERIVED", tier=SourceTier.DERIVED)
    with Store(tmp_path / "u.db") as store:

        def rec(as_of: date, iid: str) -> None:
            store.record_universe(as_of=as_of, internal_id=iid, in_universe=True, market_cap=cap)

        rec(date(2026, 1, 1), "A")
        rec(date(2026, 6, 1), "B")
        assert store.latest_universe(date(2026, 6, 12)) == ["B"]  # newest at/before
        assert store.latest_universe(date(2026, 3, 1)) == ["A"]  # earlier as-of
        assert store.latest_universe(date(2025, 1, 1)) == []  # nothing yet
