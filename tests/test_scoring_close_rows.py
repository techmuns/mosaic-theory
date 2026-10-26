"""A CLOSE row is not a second verdict — the scoring harness must skip it.

THE LANDMINE, one layer over from where it was already defused. `monitor.decision_rows` filters
close rows out before `compute_spread` partitions by verdict, and its docstring says exactly why:
a close carries the ORIGINAL verdict for provenance, so counting it again doubles that name's leg
"corrupting the one number the fund exists to measure, silently, with nothing red".

`score_ledger` partitions by verdict the same way and had NO such filter — it iterates
`store.iter_ledger()` whole. The committed ledger already holds two close rows (C-IT, C-SMPL)
against four decisions, and the committed report reads "5 pending" over 4 decisions.

It is harmless only while nothing has resolved. The first BUY resolves 2027-01-16, and the quality
book is about to start logging (and closing) its own rows — so this pin exists to make the day
those legs land uneventful.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from tests.dividend_support import no_dividends
from vinci.schemas.ledger import (
    EVENT_CLOSE,
    Confidence,
    LedgerEntry,
    Verdict,
)
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.store import Store

ENTRY_D = date(2026, 1, 5)
EXIT_D = date(2026, 8, 10)          # well past a 180d horizon → the rows RESOLVE


def _bars(iid: str, start: float, end: float) -> list[PriceBar]:
    return [
        PriceBar(internal_id=iid, bar_date=d, open=c, high=c + 1, low=c - 1, close=c,
                 volume=1e6, source="t")
        for d, c in ((ENTRY_D, start), (EXIT_D, end))
    ]


def _decision(ticker: str, iid: str, verdict: Verdict) -> LedgerEntry:
    return LedgerEntry(
        entry_id=f"V-{ticker}", candidate_id=f"{ticker}-c", internal_id=iid, ticker=ticker,
        verdict=verdict, twin_call="t", entry_price=100.0, entry_price_as_of=ENTRY_D,
        thesis="t", kill_criteria="k", horizon_days=180, confidence=Confidence.MEDIUM,
        decided_at=datetime.combine(ENTRY_D, datetime.min.time()))


def _close_of(d: LedgerEntry) -> LedgerEntry:
    """The close a real exit appends: same ticker, same verdict (provenance), event=CLOSE.

    Fully specified, because the model refuses half a close — link, price AND date together."""
    return d.model_copy(update={
        "entry_id": f"C-{d.ticker}",
        "event": EVENT_CLOSE,
        "closes_entry_id": d.entry_id,
        "exit_price": 130.0,
        "exit_price_as_of": EXIT_D - timedelta(days=1),
        "reason": "exited on the thesis playing out",
    })


def _score(tmp_path: Path, entries: list[LedgerEntry]) -> tuple[list, object]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 105.0))       # benchmark +5%
        store.write_prices(_bars("SEC-A", 100.0, 130.0))         # the BUY name +30%
        store.write_prices(_bars("SEC-B", 100.0, 80.0))          # the AVOID name -20%
        for e in entries:
            store.append_ledger(e)
        return score_ledger(store, as_of=EXIT_D, dividends=no_dividends)


def test_a_close_row_does_not_become_a_second_buy_leg(tmp_path: Path) -> None:
    """THE REGRESSION. Both rows carry verdict=BUY on the same name; only ONE is a decision.

    Asserted on the RESOLVED counts rather than the pending count, because pending is where the
    defect is currently invisible — everything committed is unresolved, which is exactly why this
    has cost nothing yet and would have cost a corrupted spread later."""
    buy = _decision("AAA", "SEC-A", Verdict.BUY)
    avoid = _decision("BBB", "SEC-B", Verdict.AVOID_TERMINAL)

    without_close = _score(tmp_path / "a", [buy, avoid])[1]
    with_close = _score(tmp_path / "b", [buy, avoid, _close_of(buy)])[1]

    assert without_close.n_resolved_buy == 1, "fixture broken: the BUY did not resolve"
    assert with_close.n_resolved_buy == 1, (
        f"appending a CLOSE for AAA counted it as a SECOND resolved BUY "
        f"({with_close.n_resolved_buy}) — a close carries the original verdict for provenance and "
        f"is not a decision. `monitor.decision_rows` already filters these; the scorer must too.")
    assert with_close.buy_avoid_spread == without_close.buy_avoid_spread, (
        "the close moved the BUY−AVOID spread — the one number the fund exists to measure")


def test_the_close_is_skipped_entirely_not_merely_deduplicated(tmp_path: Path) -> None:
    """A close must not appear as a SCORE either. Deduplicating by ticker would also make the
    counts right while leaving a phantom row in the per-verdict listing the report renders."""
    buy = _decision("AAA", "SEC-A", Verdict.BUY)
    scores, _ = _score(tmp_path, [buy, _close_of(buy)])
    ids = [s.entry_id for s in scores]
    assert ids == ["V-AAA"], f"the close row reached the score list: {ids}"


def test_the_ledger_listing_marks_closes_instead_of_showing_two_verdicts(
    tmp_path: Path, capsys: object, monkeypatch: object,
) -> None:
    """THE DISPLAY HALF, found reviewing the fix above. `iter_ledger` has exactly two consumers —
    `score_ledger` and `vinci ledger` — and fixing one while leaving the other is this session's
    recurring failure, so the neighbour was checked rather than assumed.

    `vinci ledger` printed close rows unmarked under a VERDICT header: the same ticker twice, both
    reading BUY, nothing to tell them apart. It corrupts no number, but it is how a reader
    miscounts the book by hand.

    NOT hidden — this is the append-only record and dropping rows would misrepresent it. Marked,
    which is what the web decision log settled on 2026-07-27: the decision keeps its verdict word,
    the close says it is a close."""
    import argparse

    from vinci import cli

    buy = _decision("AAA", "SEC-A", Verdict.BUY)
    db = tmp_path / "s.db"
    with Store(db) as store:
        store.append_ledger(buy)
        store.append_ledger(_close_of(buy))

    class _Cfg:
        db_path = db
    monkeypatch.setattr(cli, "get_config", lambda: _Cfg())  # type: ignore[attr-defined]
    assert cli._cmd_ledger(argparse.Namespace()) == 0
    out = capsys.readouterr().out  # type: ignore[attr-defined]

    assert out.count("AAA") == 2, "the append-only record must still show both rows"
    assert "CLOSE" in out, (
        f"a close row printed with nothing marking it — two rows reading BUY "
        f"for one decision:\n{out}")
    assert "1 decision(s) · 1 close(s)" in out, (
        f"the listing does not state how many of its rows are decisions:\n{out}")


def test_a_close_is_not_counted_as_pending_either(tmp_path: Path) -> None:
    """The unresolved path has the same hole, and it is the one the committed report shows: a
    close with no forward price inflates `n_pending`, which reads to a human as 'decisions still
    running'. Committed today: 4 decisions, report says 5 pending."""
    buy = _decision("AAA", "SEC-A", Verdict.BUY)
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 105.0))
        # NO bars for SEC-A → both rows take the no-forward-price branch
        store.append_ledger(buy)
        store.append_ledger(_close_of(buy))
        _scores, report = score_ledger(store, as_of=EXIT_D, dividends=no_dividends)
    assert report.n_pending == 1, (
        f"n_pending={report.n_pending} for ONE undecided name — the close row was counted as a "
        f"second pending decision")
