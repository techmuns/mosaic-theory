"""EVERY ROW HELD PENDING SAYS WHY (TeamNostra fix request 2, RF-D13, 2026-11-09).

THE DEFECT, reproduced on main 7c87164a before the fix: an interim row whose dividends could not be
read was counted pending with ``row_notes == ()`` — ``{'scores': 0, 'n_pending': 1, 'row_notes':
()}`` — and the no-forward-price branch did the same. Every other branch that holds a row back
names it under the pending count (`ScoreReport.row_notes`, rendered in ``scoring_report.md``); these
two left a count the reader could not audit. On the committed ledger GOOGL, whose bars the
primary's store does not hold, sits in that count today with no line saying so.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from tests.dividend_support import no_dividends, no_splits
from vinci.eod.dividends import DividendsUnknownError
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.store import Store

ENTRY, AS_OF = date(2026, 1, 5), date(2026, 3, 2)     # an interim row: horizon 180 days


def _bars(iid: str, a: date, b: date, px: float = 100.0) -> list[PriceBar]:
    out, d = [], a
    while d <= b:
        if d.weekday() < 5:
            out.append(PriceBar(internal_id=iid, bar_date=d, open=px, high=px, low=px, close=px,
                                volume=1000, source="polygon-grouped"))
        d += timedelta(days=1)
    return out


def _store(path: Path, *, name_bars: bool) -> Store:
    store = Store(path)
    store.write_prices(_bars("IDX-IWM", ENTRY, AS_OF, 200.0))
    if name_bars:
        store.write_prices(_bars("SEC-0000000011-PND", ENTRY, AS_OF))
    store.append_ledger(LedgerEntry(
        entry_id="V-PND", candidate_id="PND-c", internal_id="SEC-0000000011-PND", ticker="PND",
        verdict=Verdict.BUY, twin_call="t", entry_price=100.0, entry_price_as_of=ENTRY,
        thesis="t", kill_criteria="k", horizon_days=180, confidence=Confidence.MEDIUM,
        decided_at=datetime(2026, 1, 5)))
    return store


def _unread(symbol: str, a: date, b: date) -> list[tuple[date, float]]:
    raise DividendsUnknownError(f"{symbol}: the Tiingo request failed (HttpError)")


def test_an_interim_row_whose_dividends_cannot_be_read_is_named(tmp_path: Path) -> None:
    with _store(tmp_path / "s.db", name_bars=True) as store:
        scores, report = score_ledger(store, as_of=AS_OF, dividends=_unread, splits=no_splits)
    assert scores == [] and report.n_pending == 1
    (note,) = report.row_notes
    assert "V-PND (PND) is PENDING" in note and "dividends are unknown" in note
    assert "the Tiingo request failed" in note


def test_a_row_with_no_forward_price_is_named(tmp_path: Path) -> None:
    """GOOGL's shape on the primary's store: the name has no bars at all."""
    with _store(tmp_path / "s.db", name_bars=False) as store:
        scores, report = score_ledger(store, as_of=AS_OF, dividends=no_dividends,
                                      splits=no_splits)
    assert scores == [] and report.n_pending == 1
    (note,) = report.row_notes
    assert "V-PND (PND) is PENDING: no forward price yet" in note and "no bars" in note


def test_a_row_that_scores_adds_no_pending_note(tmp_path: Path) -> None:
    """THE NEGATIVE PIN: a readable interim row is marked, and nothing is said under the count."""
    with _store(tmp_path / "s.db", name_bars=True) as store:
        scores, report = score_ledger(store, as_of=AS_OF, dividends=no_dividends,
                                      splits=no_splits)
    assert len(scores) == 1 and not scores[0].resolved and report.row_notes == ()
