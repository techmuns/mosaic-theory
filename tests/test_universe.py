"""Step 2 verification — universe-builder pure logic + the universe-membership lookup."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from vinci import universe as uni
from vinci.config import Config, UniverseConfig
from vinci.eod.client import RawBar
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import DataField, SourceTier
from vinci.sectors import sector_for_sic
from vinci.store import Store
from vinci.universe import (
    admit_security_type,
    benchmark_identity,
    build_universe,
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


def test_build_universe_persists_fetched_sic_onto_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: the SIC fetched for the Axis-1 gate must be PERSISTED onto the stored identity —
    was a dead write (fetched, gated on, then discarded via ``[0]``), so every committed security
    carried ``sic=None`` and the coarse-sector view was blank. The resolver yields UN-enriched
    identities (``sic=None``); the builder must attach the gate's SIC.
    """
    ref = date(2026, 6, 12)
    unenriched = Identity(
        internal_id="SEC-0000000001-ACME", issuer_id="ISS-0000000001", cik="0000000001",
        ticker="ACME", mic="XNAS", exchange="Nasdaq", eod_symbol="ACME",
        name="Acme Software Inc.", sic=None, sic_description=None,
    )

    class _FakeResolver:
        @classmethod
        def from_config(cls, cfg: object) -> _FakeResolver:
            return cls()

        def iter_universe(self, exchanges: object) -> Iterator[Identity]:
            yield unenriched

        def sic_for(self, cik: str) -> tuple[str, str]:
            return ("7372", "Services-Prepackaged Software")  # operating-co software → admitted

        def registered_line(self, cik: str, ticker: str, as_of: date) -> None:
            return None  # no cover read: the line keeps what the type allowlist decided

        def latest_report(self, cik: str, as_of: date) -> None:
            return None  # no periodic report read: not shown to be a foreign private issuer

    class _FakeEod:
        @classmethod
        def from_config(cls, cfg: object) -> _FakeEod:
            return cls()

        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day == ref:  # one in-band close; $-vol 10M clears the $3M ADV floor
                bar = RawBar(ticker="ACME", open=100, high=101, low=99, close=100, volume=100_000)
                return {"ACME": bar}
            return {}

        def security_types(self) -> dict[str, str]:
            return {"ACME": "CS"}  # common stock → passes the Axis-2 allowlist
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            return {}  # domestic common stock — no depositary receipts to price

    class _FakeEdgar:
        @classmethod
        def from_config(cls, cfg: object) -> _FakeEdgar:
            return cls()

        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            # cap = 100 × 5M = $500M (small/mid band); a FILED instant count, so the row it
            # stamps must NOT carry the period-average warning
            return ({"0000000001": 5_000_000.0},
                    {"0000000001": "dei:EntityCommonStockSharesOutstanding"})

    monkeypatch.setattr(uni, "EntityResolver", _FakeResolver)
    monkeypatch.setattr(uni, "PolygonEodClient", _FakeEod)
    monkeypatch.setattr(uni, "EdgarClient", _FakeEdgar)

    cfg = Config(data_dir=tmp_path)
    stats = build_universe(cfg, reference_date=ref, share_periods=["CY2026Q1I"])
    assert stats["in_universe"] == 1

    with Store(cfg.db_path) as store:
        secs = list(store.iter_securities())
    assert len(secs) == 1
    assert secs[0].sic == "7372"  # the dead write is fixed — the fetched SIC persists at rest
    assert sector_for_sic(secs[0].sic) == "Technology"  # → the coarse bucket the roll-up uses
