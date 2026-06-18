"""Verification — the lazy universe screen (``screen_universe``).

Fake EOD + EDGAR clients drive the whole loop deterministically (no network): the cheap price gates
run on every name, EDGAR is fetched only for the price-gate survivors, and one clean idiosyncratic
de-rating is admitted while a flat name is rejected without ever touching EDGAR.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from mosaic.edgar.client import all_unknown_snapshot
from mosaic.eod.client import RawBar
from mosaic.resolver.index import pad_cik
from mosaic.schemas.data_record import Identity
from mosaic.schemas.envelope import DataField, SourceTier
from mosaic.screens import screen_universe
from mosaic.store import Store

REF = date(2026, 6, 12)
LOOKBACK = 500


def _ident(ticker: str, cik: str) -> Identity:
    return Identity(
        internal_id=f"SEC-{cik}-{ticker}", issuer_id=f"ISS-{cik}", cik=cik, ticker=ticker,
        mic="XNYS", exchange="NYSE", eod_symbol=ticker, name=f"{ticker} Inc.",
    )


class _FakeEod:  # duck-types EodClient.grouped_daily
    def __init__(self, paths: dict[str, object]) -> None:
        self._paths = paths

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        out = {}
        for t, fn in self._paths.items():
            c = fn(day)  # type: ignore[operator]
            out[t] = RawBar(ticker=t, open=c, high=c + 1, low=c - 1, close=c, volume=1e6)
        return out


class _FakeEdgar:  # duck-types the two EdgarClient methods enrich uses
    def __init__(self) -> None:
        self.fetched: list[str] = []

    def fundamental_snapshot(self, cik):  # type: ignore[no-untyped-def]
        self.fetched.append(pad_cik(cik))
        return all_unknown_snapshot(pad_cik(cik))

    def companyfacts(self, cik):  # type: ignore[no-untyped-def]
        return {}  # no EPS → G3 P/E-percentile defers (UNKNOWN)


def _drop(day: date) -> float:
    # flat at 100 until ~120 days before the ref date, then a sharp idiosyncratic decline to 55
    days_before = (REF - day).days
    return 100.0 if days_before > 120 else 100.0 - (120 - days_before) / 120 * 45.0


def _flat(_day: date) -> float:
    return 100.0


def test_screen_universe_lazy_admits_one_de_rating(tmp_path: Path) -> None:
    drop, flat = _ident("DROP", "0000000001"), _ident("FLAT", "0000000002")
    with Store(tmp_path / "u.db") as store:
        for s in (drop, flat):
            store.upsert_security(s)
            cap = DataField.present(1e9, as_of=REF, source="DERIVED", tier=SourceTier.DERIVED)
            store.record_universe(
                as_of=REF, internal_id=s.internal_id, in_universe=True, market_cap=cap
            )
        eod = _FakeEod({"DROP": _drop, "FLAT": _flat, "IWM": _flat})
        edgar = _FakeEdgar()
        cands, stats = screen_universe(
            store, eod, edgar, reference_date=REF, lookback_days=LOOKBACK, staleness_days=5
        )

    assert stats["universe"] == 2
    # the de-rating is admitted; the flat name is not
    assert {c.data_record.identity.ticker for c in cands} == {"DROP"}
    # EDGAR was fetched ONLY for the price-gate survivor (lazy), never for the flat name
    assert edgar.fetched == ["0000000001"]
