"""Step 2 verification — universe-builder pure logic + the universe-membership lookup."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from mosaic.config import UniverseConfig
from mosaic.eod.client import RawBar
from mosaic.schemas.envelope import DataField, SourceTier
from mosaic.store import Store
from mosaic.universe import (
    admit_security_type,
    benchmark_identity,
    latest_close_and_adv,
    recent_share_periods,
)


def test_latest_close_and_adv() -> None:
    class _FakeEod:
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day == date(2026, 6, 12):
                return {"X": RawBar(ticker="X", open=12, high=13, low=11, close=12, volume=200)}
            if day == date(2026, 6, 11):
                return {"X": RawBar(ticker="X", open=10, high=11, low=9, close=10, volume=100)}
            return {}  # weekend / no data

    closes, adv = latest_close_and_adv(_FakeEod(), date(2026, 6, 12), lookback_days=3)
    assert closes["X"] == 12.0  # most-recent close wins
    assert adv["X"] == (12 * 200 + 10 * 100) / 2  # mean daily $-volume over the 2 trading days


def test_admit_security_type_allowlist_fail_closed() -> None:
    """Universe Axis 2 (instrument type): an ALLOWLIST of operating-co common equity, fail-closed.

    Regression for the SHNY leak — a leveraged ETN (Polygon type ``ETS``) whose ticker→CIK correctly
    resolves to Bank of Montreal must be EXCLUDED: it is not common equity. ADR common (``ADRC`` —
    NICE/KEP/SID) must survive, and a blank/unknown type must be excluded, never silently admitted.
    """
    allowed = UniverseConfig().allowed_security_types
    # admitted — operating-company common equity
    for t in ("CS", "ADRC", "OS", "GDR"):
        assert admit_security_type(t, allowed) is True, t
    # excluded — structured products / non-common / the SHNY case (ETS)
    for t in ("ETS", "ETN", "ETF", "ETV", "FUND", "SP", "PFD", "RIGHT", "WARRANT", "UNIT"):
        assert admit_security_type(t, allowed) is False, t
    # fail-closed: blank / unknown / unenumerated → excluded, not admitted
    assert admit_security_type(None, allowed) is False
    assert admit_security_type("", allowed) is False
    assert admit_security_type("SOMETHINGNEW", allowed) is False


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
