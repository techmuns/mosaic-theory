"""THE UNIVERSE'S CAP AND ADV ON ONE BASIS (TeamNostra fix request 2: RF-D4 and RF-D9, 2026-11-09).

THE DEFECTS, reproduced on main 6fbbb4a2 before the fix, through the real `build_universe`:

- RF-D4. A close of 80 on 2026-09-22, after a 2-for-1 on 2026-08-01, times the 5,000,000 shares
  EDGAR's frame filed for 2026-06-30, sized the line at $400M against a true $800M — Polygon's
  close is restated to the day of the read and a filed count is as of its frame — and with the
  band's floor at $500M it was dropped `out_of_band`. Nothing adjusted the count or named the split.
- RF-D9. ADV was dollar volume over the days the NAME traded: a line that traded 3 of 65 sessions
  read $4.0M (against $0.18M over the sessions) and cleared the $3M floor, its cap sized off a
  close 84 days old with no stale mark.

THE FIX. A frame does not say which day its count is from, so a split anywhere since the earliest
frame could reach leaves a filed count's basis unknown: such a line is sized on Polygon's CURRENT
issuer-wide count (`weighted_shares_outstanding`: every class in the line's units, the same kind of
count as the filed one) or dropped loudly when none resolves; when neither reading of the filed
count could put it in the band it is dropped there without the request. Every split in the window
comes from ONE breadth read (`PolygonEodClient.splits_executed`), read through the day of the
read so a back-dated build moves the count across a later split as the close moved. ADV is over
every market session in the lookback, and a close older than `STALE_CLOSE_SESSIONS` is no latest
close (`stale_price`).

MEASURED ON THE COMMITTED POPULATION (`universe_snapshot.jsonl`, as_of 2026-10-16, 2,065 lines):
42 filed-count lines carry a split in the window; on Polygon's issuer-wide count 6 leave the band
(IESC above the ceiling; FUBO, BYND, GOSS, GRML and PMI, whose filed counts predate 1-for-12 to
1-for-80 reverse splits) and LXP resolves no count. The record holds the full table.
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci import universe as uni
from vinci.config import Config, UniverseConfig
from vinci.eod.client import RawBar
from vinci.schemas.data_record import Identity
from vinci.store import Store
from vinci.universe import STALE_CLOSE_SESSIONS, build_universe, latest_close_and_adv

REF = date(2026, 9, 22)                 # a Tuesday
FILED_FOR = "CY2026Q2I"                 # 2026-06-30 — before the split


def _ident() -> Identity:
    return Identity(internal_id="SEC-0000000001-SPLT", issuer_id="ISS-0000000001",
                    cik="0000000001", ticker="SPLT", mic="XNAS", exchange="Nasdaq",
                    eod_symbol="SPLT", name="Split Co", sic=None, sic_description=None)


def _build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, splits: list[dict[str, Any]],
           current: float | None, floor: float = 300e6, traded_on: date | None = None,
           retain: bool = False,
           tag: str = "dei:EntityCommonStockSharesOutstanding") -> dict[str, Any]:
    """The real `build_universe` over one line: close 80 on REF ($8M a day), a filed count of
    5,000,000 for 2026-06-30, ``splits`` in Polygon's breadth read, ``current`` Polygon's
    issuer-wide count. Returns the stats, the snapshot rows and every per-ticker count request."""
    asked: list[list[str]] = []
    asked_as_of: list[date | None] = []

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R:
            return cls()

        def iter_universe(self, exchanges: object) -> Iterator[Identity]:
            yield _ident()

        def sic_for(self, cik: str) -> tuple[str, str]:
            return ("7372", "Services-Prepackaged Software")

        def registered_line(self, *_a: object) -> None:
            return None

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E:
            return cls()

        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day.weekday() >= 5:
                return {}
            # the MARKET trades every weekday (a session exists whether or not SPLT traded it)
            out = {"MKT": RawBar(ticker="MKT", open=1, high=1, low=1, close=1, volume=1)}
            # SPLT trades every session ($8M a day) unless ``traded_on`` names its one day
            if (day == traded_on) if traded_on is not None else day <= REF:
                out["SPLT"] = RawBar(ticker="SPLT", open=80, high=80, low=80, close=80,
                                     volume=100_000)
            return out

        def splits_executed(self, start: date, end: date) -> list[dict[str, Any]]:
            # read through TODAY, not the reference date: the close is restated to the day of the
            # read, so a split after REF moves it too (review round 1, Codex P1 on #946)
            assert end >= REF and start <= date(2026, 6, 30) - timedelta(days=92)
            return splits

        def security_types(self) -> dict[str, str]:
            return {"SPLT": "CS"}

        def share_class_counts(self, tickers: list[str]) -> dict[str, float]:
            return {}                       # a single-class domestic line: no per-class count

        def issuer_share_counts(self, tickers: list[str], *,
                                as_of: date | None = None) -> dict[str, float]:
            asked.append(list(tickers))
            asked_as_of.append(as_of)
            return {"SPLT": current} if current is not None else {}

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed:
            return cls()

        def shares_outstanding_with_provenance(
                self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            return ({"0000000001": 5_000_000.0},
                    {"0000000001": tag})

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    cfg = Config(data_dir=tmp_path, universe=UniverseConfig(market_cap_min_usd=floor))
    retain_kw: dict[str, Any] = ({"retain_run_id": "2026-09-22-01", "retain_dir": tmp_path / "ret"}
                                 if retain else {})
    if retain:
        (tmp_path / "ret").mkdir(parents=True)
    stats = build_universe(cfg, reference_date=REF, share_periods=[FILED_FOR], **retain_kw)
    with Store(cfg.db_path) as store:
        rows = [dict(r) for r in store._conn.execute(
            "SELECT market_cap, source FROM universe_snapshot WHERE in_universe = 1")]
    return {"stats": stats, "rows": rows, "asked": asked, "asked_as_of": asked_as_of}


_TWO_FOR_ONE = [{"execution_date": "2026-08-01", "split_from": 1, "split_to": 2,
                 "ticker": "SPLT", "id": "x"}]


def test_a_split_since_the_filed_count_is_sized_on_the_current_count(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """RF-D4. On main: $400M, "Polygon close x EDGAR dei:…", and nothing named the split."""
    r = _build(monkeypatch, tmp_path, splits=_TWO_FOR_ONE, current=10_000_000.0)
    (row,) = r["rows"]
    assert row["market_cap"] == pytest.approx(800e6)
    assert "ISSUER-WIDE" in row["source"] and "as of 2026-09-22" in row["source"]
    assert "2-for-1 on 2026-08-01" in row["source"]
    assert r["stats"]["split_count_used"] == 1


def test_a_name_the_mixed_basis_dropped_is_admitted(monkeypatch: pytest.MonkeyPatch,
                                                    tmp_path: Path) -> None:
    """RF-D4's drop: with the floor at $500M, main sized $400M and dropped the line out of band."""
    r = _build(monkeypatch, tmp_path, splits=_TWO_FOR_ONE, current=10_000_000.0, floor=500e6)
    assert r["stats"]["in_universe"] == 1 and r["stats"].get("out_of_band", 0) == 0


def test_with_no_current_count_the_line_is_dropped_loudly(monkeypatch: pytest.MonkeyPatch,
                                                          tmp_path: Path) -> None:
    r = _build(monkeypatch, tmp_path, splits=_TWO_FOR_ONE, current=None)
    assert r["rows"] == [] and r["stats"]["split_basis_unresolved"] == 1


def test_out_of_band_on_either_basis_spends_no_request(monkeypatch: pytest.MonkeyPatch,
                                                       tmp_path: Path) -> None:
    """$400M or $800M, against a floor of $900M: out on both readings, so no count is asked for."""
    r = _build(monkeypatch, tmp_path, splits=_TWO_FOR_ONE, current=10_000_000.0, floor=900e6)
    assert r["stats"]["out_of_band"] == 1 and r["asked"] == []


def test_with_no_split_the_filed_count_sizes_the_line_as_before(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """THE NEGATIVE PIN: no split in the window — the filed count, its tag, no request."""
    r = _build(monkeypatch, tmp_path, splits=[], current=10_000_000.0)
    (row,) = r["rows"]
    assert row["market_cap"] == pytest.approx(400e6)
    assert row["source"] == "Polygon close x EDGAR dei:EntityCommonStockSharesOutstanding"
    assert r["asked"] == []


def test_the_new_drop_stages_write_their_retention_rows(monkeypatch: pytest.MonkeyPatch,
                                                         tmp_path: Path) -> None:
    """A RETAINED build (the weekly run's) refuses itself when a counted drop has no row in
    `DROP_STAGES`: before the review fix, `split_basis_unresolved` and `stale_price` were counted
    and written but not enumerated, and the build raised "retention emitted 1 thin rows against 0
    counted drops"."""
    r = _build(monkeypatch, tmp_path / "a", splits=_TWO_FOR_ONE, current=None, retain=True)
    assert r["stats"]["split_basis_unresolved"] == 1
    assert r["stats"]["retained_universe_rows"] == 1
    stale_day = REF - timedelta(days=28)                 # 20 sessions back, past the bound
    r = _build(monkeypatch, tmp_path / "b", splits=[], current=None, traded_on=stale_day,
               retain=True)
    assert r["stats"]["stale_price"] == 1 and r["stats"]["retained_universe_rows"] == 1


def test_an_unreadable_split_row_for_another_ticker_does_not_abort_the_build(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The breadth read spans every ticker Polygon lists; a row this build never sizes (no ratio)
    is not parsed, so it cannot raise — SPLT's own rows are still read and still fail loud."""
    bad = [{"execution_date": "2026-08-03", "ticker": "OTHR", "id": "y"}]
    r = _build(monkeypatch, tmp_path, splits=_TWO_FOR_ONE + bad, current=10_000_000.0)
    assert r["stats"]["split_count_used"] == 1


def test_a_period_average_count_out_of_band_on_both_bases_is_counted_as_one(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The early either-basis drop is decided on the filed count, so a period-average one is
    tallied in `out_of_band_period_average` as the ordinary band drop tallies it."""
    from vinci.edgar.client import SHARES_TAG_WAVG
    r = _build(monkeypatch, tmp_path, splits=_TWO_FOR_ONE, current=10_000_000.0, floor=900e6,
               tag=SHARES_TAG_WAVG)
    assert r["stats"]["out_of_band"] == 1 and r["stats"]["out_of_band_period_average"] == 1


# --- RF-D9 ------------------------------------------------------------------------------------


def _market(traded: set[date], ref: date, n: int = 65) -> Any:
    """``n`` weekday sessions to ``ref``: BUSY trades every one, THIN only on ``traded``."""
    days = [ref - timedelta(days=i) for i in range(200) if (ref - timedelta(days=i)).weekday() < 5]
    sessions = set(days[:n])

    class _E:
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day not in sessions:
                return {}
            out = {"BUSY": RawBar(ticker="BUSY", open=10, high=10, low=10, close=10,
                                  volume=1_000_000)}
            if day in traded:
                out["THIN"] = RawBar(ticker="THIN", open=20, high=20, low=20, close=20,
                                     volume=200_000)
            return out
    return _E(), sorted(sessions, reverse=True)


def test_adv_is_over_the_markets_sessions_not_the_days_a_name_traded() -> None:
    """RF-D9: THIN trades 3 scattered sessions of 65 at $4.0M each — $4.0M on main, $0.18M over
    the market's 65 sessions."""
    ref = date(2026, 10, 9)
    _eod, sessions = _market(set(), ref)
    eod, _s = _market({sessions[64], sessions[30], sessions[0]}, ref)
    p = latest_close_and_adv(eod, ref, lookback_days=95)
    assert p.sessions == 65
    assert p.adv["THIN"] == pytest.approx(3 * 4_000_000.0 / 65)
    assert p.adv["BUSY"] == pytest.approx(10_000_000.0)        # the negative pin: unchanged


def test_a_line_that_trades_only_its_newest_sessions_is_averaged_over_the_window() -> None:
    """REVIEW ROUND 1 (Codex P2 on #946). The denominator had started at the name's first trade
    in the lookback, so a long-listed line that resumed trading three sessions ago read its $4.0M
    over 3 and cleared the floor: absence before that bar is no proof the line did not exist. ADV
    is over every market session in the lookback — the audit's own fix — and a line with less
    than a lookback of history reads low until it has one (SWRD and SVIA on the committed
    2026-10-16 population; the record)."""
    ref = date(2026, 10, 9)
    _eod, sessions = _market(set(), ref)
    eod, _s = _market(set(sessions[:3]), ref)
    p = latest_close_and_adv(eod, ref, lookback_days=95)
    assert p.adv["THIN"] == pytest.approx(3 * 4_000_000.0 / 65)


def test_a_close_older_than_the_stale_bound_is_no_latest_close() -> None:
    """RF-D9: the latest close kept however old. THIN last traded 30 sessions back."""
    ref = date(2026, 10, 9)
    _eod, sessions = _market(set(), ref)
    eod, _s = _market({sessions[30]}, ref)
    p = latest_close_and_adv(eod, ref, lookback_days=95)
    assert "THIN" not in p.closes and p.stale["THIN"] == (sessions[30], 30)
    assert p.closes["BUSY"] == 10.0
    # THE EDGE: a close inside the bound is still the latest
    eod, _s = _market({sessions[STALE_CLOSE_SESSIONS - 1]}, ref)
    assert latest_close_and_adv(eod, ref, lookback_days=95).closes["THIN"] == 20.0


# --- review round 1 (Codex P1 on #946): a build dated before the read --------------------------


_LATER = [{"execution_date": "2026-10-15", "split_from": 1, "split_to": 2, "ticker": "SPLT",
           "id": "y"}]


def test_a_split_after_the_reference_date_moves_the_filed_count_onto_the_closes_basis(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """RF-D4's back-dated build: built for REF (2026-09-22) after a 2-for-1 on 2026-10-15, the
    close is restated to the read's day and the filed count (frames up to 2026-06-30) is not. On
    the PR head the window ended at REF and the cap read $400M; the count is now put on the
    close's basis by the later split, exactly — the count predates it for certain."""
    r = _build(monkeypatch, tmp_path, splits=_LATER, current=99.0)
    (row,) = r["rows"]
    assert row["market_cap"] == pytest.approx(800e6)
    assert "2-for-1 on 2026-10-15" in row["source"] and r["asked"] == []


def test_the_current_count_is_read_as_of_the_reference_date(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Codex P1 on #946: the replacement count was today's record, so a back-dated build sized a
    past close on today's issuance and buybacks. It is read as of the build's reference date."""
    r = _build(monkeypatch, tmp_path, splits=_TWO_FOR_ONE, current=10_000_000.0)
    assert r["asked_as_of"] == [REF]
