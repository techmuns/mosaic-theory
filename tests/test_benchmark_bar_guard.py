"""A benchmark close older than the date it is labelled with is refused, never read (STATE §5.0
row 32 (7)).

2026-10-07: SPY and MDY had stopped at 2026-09-16, and the dossier's market-relative figures, run
"to 2026-09-22", read each benchmark's latest close at or before that date — the 09-16 close,
published as the 09-22 close. SPY rose 2.6% in those four days, so seven SPY pages understated the
market's return by that much (MDY 0.7%, four pages). The screen had fixed the same defect on
2026-07-30 (`vinci.eod.features.relative_return`: both legs end on the COMMON last bar); the
dossier never adopted it.

Built from the COMMITTED price fixtures — real Polygon bars (GOOGL against IWM, both through
2026-10-16) — with the incident's hole cut out of the benchmark. The dossier's real
`_idiosyncratic_vs_shared` and `_stock_performance` are called, so the pins hold at the call site
the page is built from, not only on the helper.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import mechanical as dm
from vinci.dossier.freshness import _COVERAGE_GAP_DAYS
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store import Store
from vinci.universe import benchmark_identity

PRICES = Path(__file__).parent / "fixtures" / "prices"
GOOGL = Identity(internal_id="SEC-0001652044-GOOGL", issuer_id="ISS-0001652044", cik="0001652044",
                 ticker="GOOGL", mic="XNAS", exchange="Nasdaq", eod_symbol="GOOGL",
                 name="Alphabet Inc.")
IWM = benchmark_identity("IWM")
REF = date(2026, 9, 22)  # the incident's page date
HOLE = (date(2026, 9, 17), date(2026, 9, 22))  # the sessions SPY and MDY were missing


def _bars(name: str, *, drop: tuple[date, date] | None = None) -> list[PriceBar]:
    out = [PriceBar(**json.loads(x)) for x in (PRICES / f"{name}.jsonl").read_text().splitlines()
           if x.strip()]
    return [b for b in out if drop is None or not drop[0] <= b.bar_date <= drop[1]]


def _store(tmp_path: Path, *, drop: tuple[date, date] | None = None) -> Store:
    s = Store(tmp_path / "prices.db")
    s.write_prices(_bars("GOOGL"))
    s.write_prices(_bars("IWM", drop=drop))
    return s


def _idio(store: Store, ref: date = REF) -> Any:
    graph: Any = type("G", (), {"resolve": lambda self, t, r: None})()
    record: Any = type("R", (), {"identity": GOOGL})()
    resolver: Any = None  # the stub graph resolves nothing, so the cohort never asks
    return dm._idiosyncratic_vs_shared(record, store, graph, resolver, ref, bench=IWM,
                                       bench_basis="cap-band test")


def test_a_benchmark_that_stopped_before_the_page_date_is_refused(tmp_path: Path) -> None:
    """The incident's shape: the benchmark stops at 09-16, the page is dated 09-22. The market's
    move and the difference are UNKNOWN, naming both dates and the refresh command — the 09-16
    close is never read as the 09-22 close. The name's own move still stands, to 09-22."""
    with _store(tmp_path, drop=HOLE) as s:
        idio = _idio(s)
    assert idio.market_180d_return.value is None and idio.rel_vs_market.value is None
    note = idio.market_180d_return.note or ""
    assert "latest stored close is 2026-09-16, 6 days before 2026-09-22" in note
    assert "vinci refresh IWM" in note
    assert "IWM is stale (latest close 2026-09-16)" in (idio.rel_vs_market.note or "")
    assert idio.name_180d_return.value is not None
    assert idio.name_180d_return.source_ref.endswith("to 2026-09-22")
    # what the old lookup did: read the 09-16 close as the 09-22 close
    assert dm._window_return(_bars("IWM", drop=HOLE), REF, 180) is not None


def test_within_the_calendar_gap_both_legs_end_on_the_common_last_bar(tmp_path: Path) -> None:
    """One missing session (09-22 alone), inside the calendar's gap: both legs end on the COMMON
    last bar, 09-21, and every figure says so — the name's move is not run to a date its
    yardstick does not reach."""
    one = (date(2026, 9, 22), date(2026, 9, 22))
    with _store(tmp_path, drop=one) as s:
        idio = _idio(s)
    end = date(2026, 9, 21)
    name, iwm = _bars("GOOGL"), _bars("IWM", drop=one)
    assert idio.name_180d_return.value == dm._window_return(name, end, 180)
    assert idio.market_180d_return.value == dm._window_return(iwm, end, 180)
    for f in (idio.name_180d_return, idio.market_180d_return, idio.rel_vs_market):
        assert "to 2026-09-21" in f.source_ref, f.source_ref
    # NEGATIVE: the name's own move to 09-22 differs — the common end is a real choice
    assert dm._window_return(name, REF, 180) != idio.name_180d_return.value


def test_a_complete_benchmark_reads_exactly_as_before(tmp_path: Path) -> None:
    """NEGATIVE: on complete real bars nothing changes — every value equals the old lookup's, and
    every stamp still reads "to {ref}"."""
    with _store(tmp_path) as s:
        idio = _idio(s)
    name, iwm = _bars("GOOGL"), _bars("IWM")
    assert idio.name_180d_return.value == dm._window_return(name, REF, 180)
    assert idio.market_180d_return.value == dm._window_return(iwm, REF, 180)
    assert idio.rel_vs_market.value == pytest.approx(
        dm._window_return(name, REF, 180) - dm._window_return(iwm, REF, 180))  # type: ignore[operator]
    for f in (idio.name_180d_return, idio.market_180d_return, idio.rel_vs_market):
        assert "to 2026-09-22" in f.source_ref, f.source_ref


def test_the_chart_stops_a_stale_benchmark_line_and_refuses_its_return(tmp_path: Path) -> None:
    """The 52-week exhibit: the benchmark's line stops at its last close rather than carrying the
    09-16 close flat to 09-22, and its window return — labelled with the name's window — is not
    stated. NEGATIVE: on complete bars every point and the return equal the old as-of reading."""
    with _store(tmp_path, drop=HOLE) as s:
        sp = dm._stock_performance(GOOGL, s, REF, bench=IWM)
    assert sp is not None and sp.benchmark_return is None
    after = [p for p in sp.points if date.fromisoformat(p.date) > date(2026, 9, 16)
             and (date.fromisoformat(p.date) - date(2026, 9, 16)).days > _COVERAGE_GAP_DAYS]
    assert after and all(p.benchmark is None for p in after)
    assert all(p.benchmark is not None for p in sp.points
               if date.fromisoformat(p.date) <= date(2026, 9, 16))
    assert "latest 2026-09-16" in sp.source_ref
    (tmp_path / "full").mkdir()
    with _store(tmp_path / "full") as s:
        full = dm._stock_performance(GOOGL, s, REF, bench=IWM)
    assert full is not None
    iwm = _bars("IWM")
    base = dm._close_on_or_before(iwm, date.fromisoformat(full.points[0].date))
    assert base is not None
    assert [p.benchmark for p in full.points] == [
        round(c / base * 100.0, 2) if (c := dm._close_on_or_before(iwm, date.fromisoformat(p.date)))
        else None for p in full.points]
    last = dm._close_on_or_before(iwm, full.as_of)
    assert last is not None and full.benchmark_return == pytest.approx(last / base - 1.0)
    assert "latest" not in full.source_ref


def test_the_screen_and_the_dossier_read_one_frontier() -> None:
    """ONE reading of a series' end for both surfaces: the screen's G2 and the dossier's legs."""
    from vinci.eod import features

    assert vars(dm)["frontier"] is features.frontier
    bars = _bars("IWM", drop=HOLE)
    assert features.frontier(bars, REF) == date(2026, 9, 16)
    assert features.frontier(bars, date(2026, 9, 16) - timedelta(days=1)) == date(2026, 9, 15)
