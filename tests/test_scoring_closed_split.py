"""The scoring report decomposes its headline the way the monitor already does.

THE RULING (2026-08-12) IS UNCHANGED: a decision closed early KEEPS accruing to its horizon. The
spread measures the DISCRIMINATOR, and closing is a capital decision that does not retract the call.
Nothing here moves the headline.

WHAT IT ADDS is the split the monitor has printed since #418 and this report did not — the same
surface-gap #378 was about, where a per-book number existed in one place and not the other. On the
monitor's 2026-08-11 book the two figures were +9.54pp and −1.56pp: THE SIGN FLIPS, so a reader
given only the headline is reading a spread partly earned on positions the book no longer holds.

TESTABLE TODAY, contrary to my own earlier objection. The live report shows nothing because zero
verdicts have resolved (the first BUY horizon passes 2027-01-16) — but the CODE is exercised with
fixtures where rows DO resolve, exactly as `test_scoring_close_rows.py` already does. "The artifact
is blank" and "the logic is unverifiable" are different claims.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from vinci.schemas.ledger import EVENT_CLOSE, Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.store import Store

ENTRY_D = date(2026, 1, 5)
HORIZON_D = ENTRY_D + timedelta(days=180)      # 2026-07-04 — the scoring date for these rows
AS_OF = date(2026, 8, 10)                      # comfortably past it → the rows RESOLVE


def _bars(iid: str, start: float, end: float) -> list[PriceBar]:
    return [
        PriceBar(internal_id=iid, bar_date=d, open=c, high=c + 1, low=c - 1, close=c,
                 volume=1e6, source="t")
        for d, c in ((ENTRY_D, start), (HORIZON_D, end))
    ]


def _decision(ticker: str, iid: str, verdict: Verdict) -> LedgerEntry:
    return LedgerEntry(
        entry_id=f"V-{ticker}", candidate_id=f"{ticker}-c", internal_id=iid, ticker=ticker,
        verdict=verdict, twin_call="t", entry_price=100.0, entry_price_as_of=ENTRY_D,
        thesis="t", kill_criteria="k", horizon_days=180, confidence=Confidence.MEDIUM,
        decided_at=datetime.combine(ENTRY_D, datetime.min.time()))


def _close_of(d: LedgerEntry, *, on: date) -> LedgerEntry:
    return d.model_copy(update={
        "entry_id": f"C-{d.ticker}", "event": EVENT_CLOSE, "closes_entry_id": d.entry_id,
        "exit_price": 101.0, "exit_price_as_of": on, "reason": "closed for the test",
        "facts": {}, "machine_proposal": None, "disposition": None})


def _score(tmp_path: Path, entries: list[LedgerEntry], *, as_of: date = AS_OF):
    tmp_path.mkdir(parents=True, exist_ok=True)
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 100.0))    # flat benchmark → excess == return
        store.write_prices(_bars("SEC-WIN", 100.0, 140.0))    # +40%
        store.write_prices(_bars("SEC-MEH", 100.0, 105.0))    # +5%
        store.write_prices(_bars("SEC-BAD", 100.0, 90.0))     # −10%
        for e in entries:
            store.append_ledger(e)
        return score_ledger(store, as_of=as_of)


def test_the_headline_keeps_closed_rows_and_the_split_sits_beside_it(tmp_path: Path) -> None:
    """THE RULING AND ITS GUARD-RAIL IN ONE ASSERTION. The closed row must still be IN the headline
    (that is the ruling) and OUT of the still-held figure (that is the decomposition). A change that
    quietly dropped closed rows from the spread would pass a test checking only the second half."""
    win = _decision("WIN", "SEC-WIN", Verdict.BUY)          # +40%, closed
    meh = _decision("MEH", "SEC-MEH", Verdict.BUY)          # +5%, still held
    bad = _decision("BAD", "SEC-BAD", Verdict.AVOID_TERMINAL)   # −10%, still held
    _s, rep = _score(tmp_path, [win, meh, bad, _close_of(win, on=date(2026, 2, 1))])

    assert rep.n_resolved_buy == 2 and rep.n_closed == 1
    # headline: mean(BUY) = (0.40 + 0.05)/2 = 0.225 ; AVOID = −0.10 → +0.325
    assert rep.buy_avoid_spread == pytest.approx(0.325), "the closed row left the headline"
    # still held: BUY = 0.05 ; AVOID = −0.10 → +0.15
    assert rep.buy_avoid_spread_open_only == pytest.approx(0.15), (
        "the closed row leaked into the still-held figure")
    assert (rep.n_open_buy, rep.n_open_avoid) == (1, 1)


def test_with_nothing_closed_the_two_figures_agree(tmp_path: Path) -> None:
    """The split must not invent a difference where none exists, or a reader learns to distrust it
    on exactly the books where it matters."""
    _s, rep = _score(tmp_path, [
        _decision("MEH", "SEC-MEH", Verdict.BUY),
        _decision("BAD", "SEC-BAD", Verdict.AVOID_TERMINAL)])
    assert rep.n_closed == 0
    assert rep.buy_avoid_spread_open_only == rep.buy_avoid_spread == pytest.approx(0.15)


def test_an_all_closed_book_reports_the_held_spread_undefined_not_zero(tmp_path: Path) -> None:
    """Zero would read as "no edge among the rows we still hold" — a claim about a population that
    does not exist. UNDEFINED with its reason is the honest state, as everywhere else here."""
    win = _decision("WIN", "SEC-WIN", Verdict.BUY)
    bad = _decision("BAD", "SEC-BAD", Verdict.AVOID_TERMINAL)
    _s, rep = _score(tmp_path, [win, bad,
                                _close_of(win, on=date(2026, 2, 1)),
                                _close_of(bad, on=date(2026, 2, 1))])
    assert rep.buy_avoid_spread == pytest.approx(0.50), "the headline lost its closed rows"
    assert rep.buy_avoid_spread_open_only is None, "an empty held-book produced a number"
    assert "still held" in (rep.open_only_note or ""), (
        f"the reason does not distinguish 'closed' from 'never logged': {rep.open_only_note!r}")


def test_a_close_dated_after_the_scoring_date_has_not_happened_yet(tmp_path: Path) -> None:
    """THE AS-OF DISCIPLINE, carried over rather than re-learned. Review P1 on #418 found the
    monitor counting every close in the ledger regardless of when it happened; the same filter is
    applied here from the start. A close dated after the scoring date is not yet part of the book
    being scored."""
    win = _decision("WIN", "SEC-WIN", Verdict.BUY)
    meh = _decision("MEH", "SEC-MEH", Verdict.BUY)
    bad = _decision("BAD", "SEC-BAD", Verdict.AVOID_TERMINAL)
    future_close = _close_of(win, on=date(2026, 12, 1))     # AFTER as_of
    _s, rep = _score(tmp_path, [win, meh, bad, future_close])

    assert rep.n_closed == 0, "a close dated after the scoring date was counted as history"
    assert rep.buy_avoid_spread_open_only == rep.buy_avoid_spread, (
        "a not-yet-happened close moved the still-held figure")


def test_the_split_reaches_the_rendered_report_only_when_something_is_closed(
    tmp_path: Path,
) -> None:
    """THE ARTIFACT PIN. A decomposition present in the model and missing from the rendered report
    is the #378 failure — correct, and invisible to the reader who acts on it."""
    win = _decision("WIN", "SEC-WIN", Verdict.BUY)
    meh = _decision("MEH", "SEC-MEH", Verdict.BUY)
    bad = _decision("BAD", "SEC-BAD", Verdict.AVOID_TERMINAL)

    _s, closed_book = _score(tmp_path / "a",
                             [win, meh, bad, _close_of(win, on=date(2026, 2, 1))])
    md = closed_book.to_markdown()
    assert "still held" in md, f"the decomposition never reached the rendered report:\n{md}"
    assert "CLOSED positions" in md

    _s, open_book = _score(tmp_path / "b", [meh, bad])
    assert "still held" not in open_book.to_markdown(), (
        "a book with nothing closed printed the split — noise that trains the reader to skip it")


def test_a_re_entered_ticker_is_keyed_by_decision_not_by_name(tmp_path: Path) -> None:
    """SMPL IS THE LIVE SHAPE: closed 2026-07-22 and re-entered 2026-08-04. A ticker-keyed close set
    marks the live re-entry closed too and drops it out of the still-held figure."""
    first = _decision("MEH", "SEC-MEH", Verdict.BUY)
    again = first.model_copy(update={"entry_id": "V-MEH-2", "candidate_id": "MEH-c2"})
    bad = _decision("BAD", "SEC-BAD", Verdict.AVOID_TERMINAL)
    scores, rep = _score(tmp_path, [first, again, bad, _close_of(first, on=date(2026, 2, 1))])

    by_id = {s.entry_id: s.closed for s in scores}
    assert by_id == {"V-MEH": True, "V-MEH-2": False, "V-BAD": False}, by_id
    assert rep.n_closed == 1, "the re-entry was marked closed by its ticker"
    assert rep.n_open_buy == 1
