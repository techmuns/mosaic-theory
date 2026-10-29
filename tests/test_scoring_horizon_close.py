"""A ledger row is scored on its HORIZON SESSION'S CLOSE, never on a stale bar (2026-10-27).

Two rules, set by face validity (no forward return was read to set either):

1. A row RESOLVES only once the store holds a BENCHMARK bar dated on or after its horizon date
   (and on or before the scoring date). Until then it is pending, and the report says why. A
   weekend horizon resolves when Monday's bar lands; its exit is still the last session on or
   before the horizon.
2. The exit stays the last name bar on or before the horizon. If the benchmark has a later session
   on or before the horizon than the name's last bar, the name stopped trading: a RESOLVED row
   raises `StaleExitError`; an UNRESOLVED row's interim mark carries a note and does not raise.

FROZEN FIXTURES CUT FROM REAL BARS: `tests/fixtures/horizon_close/vrrm_iwm_bars.jsonl` is VRRM's
and IWM's Polygon bars for 2026-06-15 → 2026-10-16 (87 sessions each, the same sessions), cut from
`tests/fixtures/prices/{VRRM,IWM}.jsonl` at 987d2b4e. That file is rewritten by the weekly screen,
so the cut is frozen here. The ledger row is VRRM's real one, read from the append-only
`data/snapshots/decision_ledger.jsonl` (`V-VRRM-screen2-20260617`: AVOID_TERMINAL, $4.71 on
2026-06-17, 180 days → 2026-12-14). Where a rule needs a horizon inside the fixture's window, the
row's horizon is shortened ON A COPY (`model_copy`) — the ledger is never written.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from tests.dividend_support import no_dividends, no_splits
from vinci.schemas.ledger import ORIGIN_FOLLOWED, LedgerEntry
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.scoring.harness import StaleExitError
from vinci.store import Store

_ROOT = Path(__file__).resolve().parent.parent
_BARS = Path(__file__).parent / "fixtures" / "horizon_close" / "vrrm_iwm_bars.jsonl"
_LEDGER = _ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
_VRRM_ID = "V-VRRM-screen2-20260617"
_VRRM_IID = "SEC-0001682745-VRRM"


def _vrrm_row(**update: object) -> LedgerEntry:
    for ln in _LEDGER.read_text().splitlines():
        if ln.strip() and json.loads(ln)["entry_id"] == _VRRM_ID:
            row = LedgerEntry.model_validate(json.loads(json.loads(ln)["payload"]))
            return row.model_copy(update=update) if update else row
    raise AssertionError(f"{_VRRM_ID} is not in the committed ledger")


def _bars(*, vrrm_through: date | None = None) -> list[PriceBar]:
    """The frozen bars; ``vrrm_through`` truncates VRRM's series there — a halt mid-window."""
    out = [PriceBar.model_validate(json.loads(ln)) for ln in _BARS.read_text().splitlines()]
    return [b for b in out if vrrm_through is None or b.internal_id != _VRRM_IID
            or b.bar_date <= vrrm_through]


def _close(iid: str, on: date) -> float:
    return next(b.close for b in _bars() if b.internal_id == iid and b.bar_date == on)


def _score(tmp_path: Path, row: LedgerEntry, *, as_of: date, vrrm_through: date | None = None):
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars(vrrm_through=vrrm_through))
        store.append_ledger(row)
        scores, report = score_ledger(store, as_of=as_of, dividends=no_dividends, splits=no_splits)
    (score,) = scores
    return score, report


def test_the_fixture_is_the_real_row_and_the_real_entry_close() -> None:
    row = _vrrm_row()
    assert (row.ticker, row.verdict.value, row.entry_price) == ("VRRM", "AVOID_TERMINAL", 4.71)
    assert (row.entry_price_as_of, row.horizon_days) == (date(2026, 6, 17), 180)
    assert _close(_VRRM_IID, date(2026, 6, 17)) == 4.71


# --- rule 1: resolved only once a benchmark bar on or after the horizon is in the store ---------


def test_at_its_horizon_date_with_bars_ending_weeks_earlier_vrrm_is_pending_not_resolved(
        tmp_path: Path) -> None:
    """THE DEFECT: scored as of 2026-12-14 on bars ending 2026-10-16, VRRM resolved on the 10-16
    close. Now it is pending, and the report names the row, its horizon and the bar it waits on."""
    score, report = _score(tmp_path, _vrrm_row(), as_of=date(2026, 12, 14))
    assert score.resolved is False
    assert (report.n_resolved_avoid, report.n_pending) == (0, 1)
    md = report.to_markdown()
    line = next(ln for ln in md.splitlines() if _VRRM_ID in ln)
    for part in ("VRRM", "2026-12-14", "2026-10-16", "awaiting the horizon session's close"):
        assert part in line, (part, line)


def test_once_the_horizon_sessions_benchmark_bar_is_in_the_store_the_row_resolves_on_it(
        tmp_path: Path) -> None:
    """NEGATIVE PIN: the guard holds nothing back once the bar has landed. Horizon shortened to
    119 days → Wednesday 2026-10-14, a session in the fixture; exit is that day's close."""
    score, report = _score(tmp_path, _vrrm_row(horizon_days=119), as_of=date(2026, 10, 16))
    assert score.resolved is True
    assert report.n_resolved_avoid == 1 and report.n_pending == 0
    assert score.name_price_return == pytest.approx(
        _close(_VRRM_IID, date(2026, 10, 14)) / 4.71 - 1)
    assert "awaiting" not in report.to_markdown()


def test_a_weekend_horizon_waits_for_mondays_bar_even_when_later_bars_are_stored(
        tmp_path: Path) -> None:
    """Horizon 115 days → Saturday 2026-10-10. As of Sunday the benchmark's last bar ON OR BEFORE
    the scoring date is Friday's: pending. The store holds Monday's bar, and it is not read — a
    bar after the scoring date has not landed in the book being scored."""
    score, report = _score(tmp_path, _vrrm_row(horizon_days=115), as_of=date(2026, 10, 11))
    assert score.resolved is False
    assert report.n_pending == 1
    assert "2026-10-09" in next(ln for ln in report.to_markdown().splitlines() if _VRRM_ID in ln)


def test_a_weekend_horizon_resolves_on_monday_and_still_exits_on_fridays_close(
        tmp_path: Path) -> None:
    score, _report = _score(tmp_path, _vrrm_row(horizon_days=115), as_of=date(2026, 10, 12))
    assert score.resolved is True
    assert score.name_price_return == pytest.approx(_close(_VRRM_IID, date(2026, 10, 9)) / 4.71 - 1)
    assert score.bench_price_return == pytest.approx(
        _close("IDX-IWM", date(2026, 10, 9)) / _close("IDX-IWM", date(2026, 6, 17)) - 1)


# --- rule 2: the name stopped trading before the benchmark's last session ----------------------


def test_a_resolved_row_whose_name_stopped_trading_raises_naming_the_row_and_both_dates(
        tmp_path: Path) -> None:
    """VRRM's real bars cut at 2026-09-15: a halt. The benchmark trades on to the 10-14 horizon.
    Scored on the stale bar, the AVOID would exit at its last trade — the very event it predicts."""
    with pytest.raises(StaleExitError) as exc:
        _score(tmp_path, _vrrm_row(horizon_days=119), as_of=date(2026, 10, 16),
               vrrm_through=date(2026, 9, 15))
    msg = str(exc.value)
    for part in (_VRRM_ID, "2026-09-15", "2026-10-14"):
        assert part in msg, (part, msg)


def test_a_resolved_row_with_both_series_on_the_horizon_session_does_not_raise(
        tmp_path: Path) -> None:
    """NEGATIVE PIN: a name trading through the horizon is not a halt, and carries no note."""
    score, report = _score(tmp_path, _vrrm_row(horizon_days=119), as_of=date(2026, 10, 16))
    assert score.resolved is True and score.note is None
    assert _VRRM_ID not in report.to_markdown()


def test_an_unresolved_row_whose_name_stopped_trading_carries_a_note_and_does_not_raise(
        tmp_path: Path) -> None:
    """The same halt on the real 180-day row, scored as of 2026-10-16: an interim mark feeds no
    number, so it is marked on the stale close and SAYS so — on the score and in the report."""
    score, report = _score(tmp_path, _vrrm_row(), as_of=date(2026, 10, 16),
                           vrrm_through=date(2026, 9, 15))
    assert score.resolved is False
    assert score.name_price_return == pytest.approx(_close(_VRRM_IID, date(2026, 9, 15)) / 4.71 - 1)
    assert score.note is not None
    for part in ("2026-09-15", "2026-10-16"):
        assert part in score.note, (part, score.note)
    assert score.note in report.to_markdown()


def test_an_unresolved_row_with_no_gap_carries_no_note(tmp_path: Path) -> None:
    score, report = _score(tmp_path, _vrrm_row(), as_of=date(2026, 10, 16))
    assert score.resolved is False and score.note is None
    assert _VRRM_ID not in report.to_markdown()


# --- review round 0: the notes say which count they belong to, and when scoring stops ------------


def test_a_followed_rows_note_says_it_is_outside_the_screen_origin_pending_count(
        tmp_path: Path) -> None:
    """The pending count is screen-origin only; a followed row named under it must say it is not
    in that count, or the reader audits the count against one row too many."""
    score, report = _score(tmp_path, _vrrm_row(origin=ORIGIN_FOLLOWED), as_of=date(2026, 12, 14))
    assert report.n_pending == 0 and score.note is not None
    assert "outside the screen-origin counts" in score.note
    (tmp_path / "s").mkdir()
    screen, _ = _score(tmp_path / "s", _vrrm_row(), as_of=date(2026, 12, 14))
    assert screen.note is not None and "outside the screen-origin" not in screen.note


def test_an_awaiting_rows_gap_note_does_not_name_a_horizon_already_passed_as_the_deadline(
        tmp_path: Path) -> None:
    """As of the 12-14 horizon on bars ending 10-16, with VRRM cut at 09-15: the row awaits the
    horizon close AND carries the gap — scoring stops when it resolves, not 'by' a passed date."""
    score, _ = _score(tmp_path, _vrrm_row(), as_of=date(2026, 12, 14),
                      vrrm_through=date(2026, 9, 15))
    assert score.note is not None and "awaiting the horizon session's close" in score.note
    assert "when the row resolves" in score.note
    assert "by its horizon" not in score.note
