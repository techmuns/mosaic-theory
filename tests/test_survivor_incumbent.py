"""THE INCUMBENT LINE KEEPS ITS ISSUER'S SLOT (2026-10-27): a record never changes ticker mid-way.

THE FALSIFIER #549 PRE-REGISTERED FIRED. One-line-per-issuer picks the HIGHEST-ADV line among an
issuer's lines that clear every gate, and ADV is a 90-day average, so the record said "if any
issuer's survivor changes between two consecutive weekly runs, this needs a stickiness rule (keep
the incumbent unless it fails a gate)". It changed, on real data:

    2026-08-24 build (#553)   U-Haul enters the signed-off population as UHAL  ($1.37B; per-class)
                              UHAL.B is $11.00B — above the $10B ceiling, so it is not a rival
    2026-09-22 weekly         UHAL.B falls to $54.89 -> $9.62B, enters the band, and takes the slot
                              on ADV: $22.1M/day against UHAL's $11.9M (retention row, run
                              2026-09-22-01) — UHAL, which cleared every gate, is dropped

One company's forward record now spans two tickers. The 08-24 / 09-22 / 10-16 universe snapshots in
git history are the evidence; the fixture below is those numbers, frozen: closes and ADVs from the
2026-09-22 grouped-daily bars, per-class counts from Polygon's share_class_shares_outstanding.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from vinci import universe as uni
from vinci.config import Config
from vinci.eod import RawBar
from vinci.schemas.data_record import Identity
from vinci.universe import build_universe

_UHAL_CIK = "0000004457"
_SEP22 = date(2026, 9, 22)
_AUG24 = date(2026, 8, 24)

#: 2026-09-22, read from the grouped-daily bars and Polygon's per-class reference counts
_CLOSE = {"UHAL": 62.07, "UHAL.B": 54.89}
_ADV = {"UHAL": 11_886_334.998433346, "UHAL.B": 22_147_679.718684737}
_CLASS_COUNT = {"UHAL": 19_224_580.0, "UHAL.B": 175_168_915.0}


def _uhal(sec_ticker: str) -> Identity:
    """The real identity, as the resolver builds it (SEC dash form, Polygon dot form)."""
    return Identity(
        internal_id=f"SEC-{_UHAL_CIK}-{sec_ticker}", issuer_id=f"ISS-{_UHAL_CIK}", cik=_UHAL_CIK,
        ticker=sec_ticker, mic="XNYS", exchange="NYSE", eod_symbol=sec_ticker.replace("-", "."),
        name="U-Haul Holding Co /NV/", share_class=("B" if sec_ticker.endswith("-B") else None))


def _incumbent_snapshot(tmp_path: Path, as_of: date, internal_ids: list[str],
                        table: str = "universe_snapshot") -> None:
    snaps = tmp_path / "snapshots"
    snaps.mkdir(parents=True, exist_ok=True)
    (snaps / f"{table}.jsonl").write_text("".join(
        json.dumps({"as_of": as_of.isoformat(), "coverage_status": "present", "in_universe": 1,
                    "internal_id": iid, "market_cap": 1.0, "source": "fixture"}) + "\n"
        for iid in internal_ids))


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, reference_date: date = _SEP22,
         retain: bool = False, band_name: str = "primary") -> tuple[dict, set[str], list[dict]]:
    """The REAL builder over U-Haul's two lines; returns (stats, admitted tickers, retention)."""
    idents = [_uhal("UHAL"), _uhal("UHAL-B")]

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield from idents
        def sic_for(self, cik: str) -> tuple[str, str]: return ("7510", "Services-Auto Rental")
        def registered_line(self, *_: object) -> None: return None     # both lines are common
        def latest_report(self, *_: object) -> None: return None       # U-Haul files 10-Q

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day != reference_date:
                return {}
            # one bar, so ADV = close x volume = the measured 90-day ADV
            return {t: RawBar(ticker=t, open=p, high=p, low=p, close=p, volume=_ADV[t] / p)
                    for t, p in _CLOSE.items()}
        def security_types(self) -> dict[str, str]: return {"UHAL": "CS", "UHAL.B": "CS"}
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            return {t: _CLASS_COUNT[t] for t in tickers if t in _CLASS_COUNT}  # type: ignore[attr-defined]

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            return ({_UHAL_CIK: 194_393_495.0},
                    {_UHAL_CIK: "dei:EntityCommonStockSharesOutstanding"})

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    run_id = f"{reference_date.isoformat()}-01"
    stats = build_universe(Config(data_dir=tmp_path), reference_date=reference_date,
                           share_periods=["CY2026Q2I"], band_name=band_name,
                           retain_run_id=(run_id if retain else None),
                           retain_dir=(tmp_path / "retain" if retain else None))
    table = "universe_snapshot" if band_name == "primary" else "theme_universe_snapshot"
    snap = tmp_path / "snapshots" / f"{table}.jsonl"
    admitted = {json.loads(x)["internal_id"].split("-", 2)[2]
                for x in snap.read_text().splitlines() if x.strip()}
    rows: list[dict] = []
    if retain:
        from vinci.screens.retention import run_path
        rows = [json.loads(x) for x in run_path(run_id, tmp_path / "retain").read_text()
                .splitlines() if x.strip()]
    return stats, admitted, rows


def test_the_incumbent_keeps_the_slot_when_a_more_traded_sibling_enters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE U-HAUL CASE. UHAL is the issuer's line in the 2026-08-24 population and still clears
    every gate on 2026-09-22; UHAL.B enters the band trading twice as much. The record stays on
    UHAL."""
    _incumbent_snapshot(tmp_path, _AUG24, [f"SEC-{_UHAL_CIK}-UHAL"])
    stats, admitted, rows = _run(monkeypatch, tmp_path, retain=True)
    assert admitted == {"UHAL"}, "the issuer's forward record moved to another ticker mid-history"
    assert stats["in_universe"] == 1 and stats["duplicate_class"] == 1
    [drop] = [r for r in rows if r["stage"] == "duplicate_class"]
    assert drop["ticker"] == "UHAL.B"
    # the evidence trail says WHY the less-traded line won, and on what record
    assert "incumbent" in drop["reason"] and "UHAL" in drop["reason"]
    assert drop["deciding_input"]["as_of"] == _AUG24.isoformat()


def test_with_no_incumbent_the_more_traded_line_still_wins(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """NO OVER-REACH — the negative pin. An issuer entering the population for the first time is
    still represented by its most tradeable line: stickiness only ever PROTECTS a record that
    exists, it never re-ranks a fresh choice."""
    stats, admitted, rows = _run(monkeypatch, tmp_path, retain=True)
    assert admitted == {"UHAL-B"}
    [drop] = [r for r in rows if r["stage"] == "duplicate_class"]
    assert drop["ticker"] == "UHAL"
    assert drop["deciding_input"]["source"] == "Polygon ADV"


def test_the_more_traded_incumbent_reads_as_an_adv_win(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Where the incumbent is ALSO the more traded line, nothing was overridden — the row must say
    ADV decided, not claim a stickiness the rule never needed."""
    _incumbent_snapshot(tmp_path, _AUG24, [f"SEC-{_UHAL_CIK}-UHAL-B"])
    _, admitted, rows = _run(monkeypatch, tmp_path, retain=True)
    assert admitted == {"UHAL-B"}
    [drop] = [r for r in rows if r["stage"] == "duplicate_class"]
    assert drop["deciding_input"]["source"] == "Polygon ADV"
    assert "incumbent" not in drop["reason"]


def test_an_incumbent_that_fails_a_gate_loses_the_slot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """KEEP THE INCUMBENT UNLESS IT FAILS A GATE — the second half of the rule. On 2026-08-24 UHAL.B
    was $11.00B, above the primary band's $10B ceiling. Had IT been the primary incumbent, the
    issuer must not vanish with it: the sibling that clears every gate is admitted."""
    _incumbent_snapshot(tmp_path, _AUG24, [f"SEC-{_UHAL_CIK}-UHAL-B"])
    monkeypatch.setitem(_CLOSE, "UHAL.B", 62.82)          # its 2026-08-24 close: $11.00B
    stats, admitted, _ = _run(monkeypatch, tmp_path)
    assert stats["out_of_band"] == 1
    assert admitted == {"UHAL"}


def test_a_snapshot_dated_after_the_build_is_never_an_incumbent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """NO LOOKAHEAD. A backdated rebuild must not be steered by a population chosen later: a
    snapshot dated after the reference date is not a record that existed then."""
    _incumbent_snapshot(tmp_path, date(2026, 10, 16), [f"SEC-{_UHAL_CIK}-UHAL"])
    _, admitted, _ = _run(monkeypatch, tmp_path)
    assert admitted == {"UHAL-B"}


def test_each_band_reads_its_own_incumbent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The theme band's population is a different record. A primary incumbent must not steer the
    theme band, and the reverse."""
    from vinci.universe import incumbent_lines
    _incumbent_snapshot(tmp_path, _AUG24, [f"SEC-{_UHAL_CIK}-UHAL"])
    assert incumbent_lines(tmp_path / "snapshots", "theme_universe_snapshot", _SEP22) == (
        frozenset(), None)
    assert incumbent_lines(tmp_path / "snapshots", "universe_snapshot", _SEP22) == (
        frozenset({f"SEC-{_UHAL_CIK}-UHAL"}), _AUG24)


def test_rows_out_of_the_population_are_not_incumbents(tmp_path: Path) -> None:
    """Only ADMITTED rows are a record. A row carried with `in_universe: 0` never protected
    anything."""
    from vinci.universe import incumbent_lines
    snaps = tmp_path / "snapshots"
    snaps.mkdir()
    (snaps / "universe_snapshot.jsonl").write_text(
        json.dumps({"as_of": "2026-08-24", "in_universe": 0, "internal_id": "SEC-1-A"}) + "\n"
        + json.dumps({"as_of": "2026-08-24", "in_universe": 1, "internal_id": "SEC-1-B"}) + "\n")
    assert incumbent_lines(snaps, "universe_snapshot", _SEP22) == (
        frozenset({"SEC-1-B"}), _AUG24)
