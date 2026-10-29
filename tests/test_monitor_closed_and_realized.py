"""Closed positions stay in the spread — and the reader can now see how much they carry.

TWO OPERATOR DECISIONS, 2026-08-12.

ITEM 1 — a decision keeps accruing to its horizon after the position is closed. The spread measures
the DISCRIMINATOR, and closing early is a capital decision that does not retract the call. That
ruling STANDS and nothing here changes the headline. What it does not license is a headline the
reader cannot decompose: on 2026-08-11 the book read **+9.54 pp**, and +29.00 pts of the BUY leg
came from IT — a position closed at the entry price on 2026-07-21 whose REALIZED P&L was +0.0%. Over
the rows still held the same spread is **−1.56 pp**. The sign flips, so both are printed.

ITEM 4 — the realized book reached the snapshot only as free-text `notes`, so the one view that says
what the fund actually EARNED was unreadable by anything not parsing English, while the
marked-to-market rows beside it were fully structured. It is typed now, and the note line is
RENDERED from the typed row so display cannot drift from data.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date

import pytest

from tests.dividend_support import no_splits
from vinci.monitor import (
    MonitorSnapshot,
    RealizedRow,
    compute_spread,
    position_row,
    render_table,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
MONITOR = ROOT / "data" / "monitor"
LIVE = MONITOR / "2026-08-11.json"
LEGACY = MONITOR / "2026-07-20.json"


def _row(ticker: str, verdict: str, *, excess_via: float, closed: bool = False,
         entry: date = date(2026, 1, 5)) -> object:
    """One marked row. ``excess_via`` is the position's close, so excess is real arithmetic rather
    than a number poked into the model."""
    return position_row(
        ticker=ticker, verdict=verdict, sector="Industrials", entry_price=100.0, entry_date=entry,
        current_price=excess_via, current_date=date(2026, 3, 1), benchmark="IWM",
        benchmark_entry=100.0, benchmark_now=100.0, horizon_days=180, closed=closed,
        position_growth=1.0, benchmark_growth=1.0)


# --------------------------------------------------------------------------------------------
# Item 1 — the decomposition
# --------------------------------------------------------------------------------------------

def test_the_headline_keeps_closed_rows_and_the_open_only_spread_sits_beside_it() -> None:
    """THE RULING AND ITS GUARD-RAIL IN ONE ASSERTION. The closed row must still be in the
    headline (that is the ruling) AND must be excluded from the open-only figure (that is the
    decomposition). A change that quietly dropped closed rows from the spread would pass a test
    that only checked the second half."""
    rows = [
        _row("WIN", "BUY", excess_via=130.0, closed=True),    # +30% — closed, still counted
        _row("MEH", "BUY", excess_via=95.0),                  # −5%  — still held
        _row("BAD", "AVOID_TERMINAL", excess_via=90.0),       # −10% — still held
    ]
    s = compute_spread(rows)
    assert s.buy_n == 2 and s.closed_n == 1
    # headline: mean(BUY) = (0.30 + −0.05)/2 = 0.125 ; AVOID = −0.10 → +0.225
    assert s.spread == pytest.approx(0.225), "the closed row was dropped from the headline"
    # open only: BUY = −0.05 ; AVOID = −0.10 → +0.05
    assert s.spread_open_only == pytest.approx(0.05), "the closed row leaked into the open figure"
    assert (s.open_buy_n, s.open_avoid_n) == (1, 1)


def test_with_nothing_closed_the_two_figures_agree() -> None:
    """The decomposition must not invent a difference where none exists — otherwise a reader
    learns to distrust it on exactly the books where it matters."""
    rows = [_row("A", "BUY", excess_via=120.0), _row("B", "AVOID_TERMINAL", excess_via=90.0)]
    s = compute_spread(rows)
    assert s.closed_n == 0
    assert s.spread_open_only == s.spread == pytest.approx(0.30)


def test_an_all_closed_book_reports_the_open_spread_undefined_not_zero() -> None:
    """A book whose positions are all closed has NO open spread. Zero would read as "no edge among
    the rows we still hold", which is a claim about a population that does not exist."""
    rows = [_row("A", "BUY", excess_via=120.0, closed=True),
            _row("B", "AVOID_TERMINAL", excess_via=90.0, closed=True)]
    s = compute_spread(rows)
    assert s.spread == pytest.approx(0.30), "the headline lost its closed rows"
    assert s.spread_open_only is None, "an empty held-book produced a number"
    assert "still held" in (s.open_undefined_reason or ""), (
        f"the reason does not say the rows are closed rather than absent: "
        f"{s.open_undefined_reason!r}")


def test_the_render_shows_both_figures_only_when_something_is_closed() -> None:
    """The ARTIFACT pin: a decomposition present in the model and missing from the printed book is
    the #378 failure — correct, and invisible to the reader who acts on it."""
    closed_book = [_row("WIN", "BUY", excess_via=130.0, closed=True),
                   _row("MEH", "BUY", excess_via=95.0),
                   _row("BAD", "AVOID_TERMINAL", excess_via=90.0)]
    txt = render_table(MonitorSnapshot(
        as_of=date(2026, 3, 1), rows=closed_book, spread=compute_spread(closed_book),
        return_basis="total"))
    assert "STILL HELD" in txt, f"the open-only spread never reached the printed book:\n{txt}"
    assert "CLOSED positions" in txt

    open_book = [_row("A", "BUY", excess_via=120.0), _row("B", "AVOID_TERMINAL", excess_via=90.0)]
    plain = render_table(MonitorSnapshot(
        as_of=date(2026, 3, 1), rows=open_book, spread=compute_spread(open_book),
        return_basis="total"))
    assert "STILL HELD" not in plain, (
        "a book with nothing closed printed a decomposition line — noise that trains the reader to "
        "skip it")


# --------------------------------------------------------------------------------------------
# The trap this keys around
# --------------------------------------------------------------------------------------------

def test_a_re_entered_ticker_does_not_mark_the_live_position_closed() -> None:
    """SMPL IS THE LIVE CASE, not a hypothetical: it was closed 2026-07-22 and re-entered
    2026-08-04, so a ticker-keyed `closed` set marks the live re-entry as closed and moves the
    spread. Keyed on the DECISION's entry_id, which is what the close row names.

    Asserted against the committed snapshot, where both SMPL rows exist on opposite sides of this
    flag."""
    snap = json.loads(LIVE.read_text())
    smpl = [r for r in snap["rows"] if r["ticker"] == "SMPL"]
    assert len(smpl) == 2, f"the corpus no longer holds SMPL twice — re-read this pin: {len(smpl)}"
    by_entry = {r["entry_date"]: r["closed"] for r in smpl}
    assert by_entry == {"2026-07-20": True, "2026-08-04": False}, (
        f"the re-entered SMPL position is mis-flagged: {by_entry}. A ticker-keyed close set would "
        f"mark both True and quietly drop the live row out of the open-only spread.")


@pytest.mark.parametrize(
    ("ref", "expect_closed", "expect_realized"),
    [
        ("2026-07-20", set(), 0),                              # before BOTH exits
        ("2026-07-21", {"V-IT-screen2-20260706"}, 1),           # IT exits this day, SMPL has not
        ("2026-07-22", {"V-IT-screen2-20260706",
                        "V-SMPL-screen2-20260706"}, 2),         # both exits are now history
    ],
    ids=["before-both-exits", "after-IT-only", "after-both"],
)
def test_closure_state_is_read_as_of_the_snapshot_date(
    ref: str, expect_closed: set[str], expect_realized: int,
) -> None:
    """OPERATOR REVIEW P1 ON #418 — LOOK-AHEAD, in the one module whose price path refuses it.

    `closed_decision_ids`/`pair_closes` counted every close in the ledger regardless of WHEN it
    happened, so `vinci monitor --ref <past date>` marked positions closed and printed their
    realized P&L for exits that had not occurred at that point in the book. Measured before the
    fix: at ref 2026-07-20 the code reported 2 closes against a truth of 0; at 2026-07-21, 2
    against 1. A historical snapshot was therefore not reproducible — while `bars_on_or_before`
    beside it was carefully refusing future bars.

    IT exits 2026-07-21 and SMPL 2026-07-22, so the committed ledger supplies all three states
    without a synthetic row. The boundary case is deliberate: a close is visible ON its exit date,
    not the day after.
    """
    from vinci.monitor import closed_decision_ids, pair_closes

    ledger = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
    raw = [json.loads(ln) for ln in ledger.read_text().splitlines() if ln.strip()]
    as_of = date.fromisoformat(ref)
    assert closed_decision_ids(raw, as_of=as_of) == expect_closed, (
        f"as of {ref} the book's closure state is wrong — a close dated after that day was "
        f"counted, which is look-ahead")
    assert len(pair_closes(raw, as_of=as_of, splits=no_splits)) == expect_realized, (
        f"as of {ref} the realized view reported P&L for an exit that had not happened")


def test_a_superseded_day_cannot_be_silently_rewritten(tmp_path: pathlib.Path) -> None:
    """FOUND BY DOING IT. Verifying the point-in-time fix meant running `monitor --ref 2026-07-20`,
    which silently REPLACED that committed snapshot — and comparing the two is how the decision
    look-ahead above was found.

    `write_snapshot`'s docstring already claimed the history is "never overwritten across days";
    nothing enforced it.

    THE RULE IS "SUPERSEDED", NOT "NOT TODAY". The normal daily run resolves to the LAST TRADING
    DAY, which is usually not today, so a not-today rule would refuse the routine re-run — the
    first cut of this guard did exactly that. Rewriting the FRONT of the book is fine; rewriting a
    day that later snapshots sit on top of is not.
    """
    from vinci.monitor import compute_spread, write_snapshot

    (tmp_path / "data" / "monitor").mkdir(parents=True)

    def snap(d: date) -> MonitorSnapshot:
        return MonitorSnapshot(as_of=d, rows=[], spread=compute_spread([]))

    older, newer = date(2026, 3, 1), date(2026, 3, 2)
    first = write_snapshot(snap(older), root=tmp_path)
    # RE-RUNNING THE FRONT OF THE BOOK IS ROUTINE — nothing sits on top of it yet
    assert write_snapshot(snap(older), root=tmp_path) == first, (
        "the guard refused a re-run of the latest day, which is the normal daily operation")
    write_snapshot(snap(newer), root=tmp_path)
    # now `older` is superseded, and rewriting it would replace what the book recorded then
    with pytest.raises(FileExistsError, match="later snapshot"):
        write_snapshot(snap(older), root=tmp_path)
    assert write_snapshot(snap(older), root=tmp_path, rewrite_history=True) == first


def test_a_back_dated_day_is_refused_even_though_it_was_never_written(
        tmp_path: pathlib.Path) -> None:
    """REVIEW OF #708. The guard above fired only when the day's file ALREADY existed, so a day
    that was never written slipped under it: `--ref 2026-10-01` between the committed 09-22 and
    10-09 wrote a new file reading today's pages into an October-1 day. ⊖ that back-dated day is
    refused, and nothing is written; ⊕ the front of the book still re-runs; ⊕ a day after the
    newest is still written; ⊖ `rewrite_history` does NOT let it through — it names an overwrite,
    and a back-dated day has no override (second review of #708)."""
    from vinci.monitor import compute_spread, write_snapshot

    mon_dir = tmp_path / "data" / "monitor"
    mon_dir.mkdir(parents=True)

    def snap(d: date) -> MonitorSnapshot:
        return MonitorSnapshot(as_of=d, rows=[], spread=compute_spread([]))

    write_snapshot(snap(date(2026, 9, 22)), root=tmp_path)
    write_snapshot(snap(date(2026, 10, 9)), root=tmp_path)
    with pytest.raises(FileExistsError, match=r"BACK-DATED day: 1 later snapshot\(s\) already "
                                               r"exist \(next: 2026-10-09\)"):
        write_snapshot(snap(date(2026, 10, 1)), root=tmp_path)
    assert not (mon_dir / "2026-10-01.json").exists()
    write_snapshot(snap(date(2026, 10, 9)), root=tmp_path)          # the front: routine
    write_snapshot(snap(date(2026, 10, 12)), root=tmp_path)         # a NEW day after the newest
    with pytest.raises(FileExistsError, match="BACK-DATED"):
        write_snapshot(snap(date(2026, 10, 1)), root=tmp_path, rewrite_history=True)
    assert not (mon_dir / "2026-10-01.json").exists()


def test_omitting_as_of_still_returns_the_whole_book() -> None:
    """The filter is OPT-IN: existing callers that want the full realized book (and the
    unpairable/duplicate refusals it performs) keep getting it."""
    from vinci.monitor import closed_decision_ids, pair_closes

    ledger = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
    raw = [json.loads(ln) for ln in ledger.read_text().splitlines() if ln.strip()]
    assert len(pair_closes(raw, splits=no_splits)) == 2
    assert len(closed_decision_ids(raw)) == 2


def test_a_malformed_close_is_still_refused_even_when_dated_past_the_as_of() -> None:
    """THE FILTER MUST NOT BECOME AN ESCAPE HATCH. Filtering happens AFTER pairing, so a close
    that points at nothing still raises even when its exit date is beyond ``as_of`` — otherwise a
    future-dated malformed row would sit unexamined in the ledger until the day it came into
    scope."""
    from vinci.monitor import pair_closes

    ledger = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
    raw = [json.loads(ln) for ln in ledger.read_text().splitlines() if ln.strip()]
    orphan = json.loads(json.dumps(next(r for r in raw if "C-" in json.dumps(r))))
    payload = json.loads(orphan["payload"]) if isinstance(orphan["payload"], str) else \
        orphan["payload"]
    payload["entry_id"] = "C-ORPHAN"
    payload["closes_entry_id"] = "V-DOES-NOT-EXIST"
    payload["exit_price_as_of"] = "2099-01-01"
    orphan["payload"] = json.dumps(payload)
    orphan["entry_id"] = "C-ORPHAN"
    with pytest.raises(ValueError, match="must close something"):
        pair_closes([*raw, orphan], as_of=date(2026, 8, 11), splits=no_splits)


def test_the_closed_set_is_keyed_on_decisions_over_the_real_ledger() -> None:
    """MUTATION FINDING: the artifact pin above cannot catch a code regression, because the
    artifact is STATIC — mutating the keying does not regenerate it, so the test stayed green.

    The keying now lives in `monitor.closed_decision_ids` and is exercised against the committed
    LEDGER, where SMPL's two decisions sit on opposite sides of it. Both pins are kept: this one
    catches the logic, the one above catches the shipped artifact."""
    from vinci.monitor import closed_decision_ids

    ledger = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
    raw = [json.loads(ln) for ln in ledger.read_text().splitlines() if ln.strip()]
    ids = closed_decision_ids(raw)
    assert ids == {"V-IT-screen2-20260706", "V-SMPL-screen2-20260706"}, ids
    assert "V-SMPL-screen2-20260729" not in ids, (
        "the LIVE SMPL re-entry was marked closed — the set is keyed on the ticker, not the "
        "decision it closes")


# --------------------------------------------------------------------------------------------
# Item 4 — the realized book, typed
# --------------------------------------------------------------------------------------------

def test_the_committed_snapshot_carries_typed_realized_rows() -> None:
    """THE ARTIFACT, not the model. The realized book existing as a class while the committed
    snapshot still carries only prose is precisely the state this closes."""
    snap = json.loads(LIVE.read_text())
    rows = snap.get("realized", [])
    assert len(rows) == 2, f"the committed snapshot carries {len(rows)} typed realized row(s)"
    by_ticker = {r["ticker"]: r for r in rows}
    assert by_ticker["IT"]["realized_return"] == pytest.approx(0.0)
    assert by_ticker["SMPL"]["realized_return"] == pytest.approx(10.53 / 10.92 - 1.0)
    for r in rows:  # each names the pair it was derived from, so a reader can audit it
        assert r["close_id"] == f"C-{r['entry_id'][2:]}"


def test_the_note_text_is_rendered_from_the_typed_row() -> None:
    """ONE DEFINITION. The prose used to be composed from raw dicts beside the data; now it is
    derived FROM the typed row, so a number cannot appear in the sentence that is absent from the
    record — the repo's standing rule that display formatting is never load-bearing."""
    row = RealizedRow(
        ticker="ZZZ", entry_id="V-ZZZ", close_id="C-ZZZ", verdict="BUY", entry_price=10.0,
        entry_price_as_of=date(2026, 1, 5), exit_price=12.5,
        exit_price_as_of=date(2026, 2, 2), realized_return=0.25)
    note = row.note()
    assert "+25.0%" in note and "10.00" in note and "12.50" in note, note
    assert "2026-01-05" in note and "2026-02-02" in note, note


def test_the_committed_notes_still_match_their_typed_rows() -> None:
    """Corpus check: every realized note in the live snapshot is reproducible from its row. If the
    two ever diverge, the prose is being written somewhere other than `RealizedRow.note`."""
    snap = json.loads(LIVE.read_text())
    notes = [n for n in snap["notes"] if "REALIZED" in n]
    rendered = [RealizedRow.model_validate(r).note() for r in snap["realized"]]
    assert sorted(notes) == sorted(rendered), (
        "a realized note in the committed snapshot is not what its typed row renders:\n"
        f"  snapshot: {sorted(notes)}\n  rendered: {sorted(rendered)}")


def test_a_legacy_snapshot_without_the_new_fields_still_loads() -> None:
    """The book history is APPEND-PER-RUN and never rewritten, so every earlier snapshot must keep
    loading. 2026-07-20 predates all of this."""
    snap = MonitorSnapshot.model_validate_json(LEGACY.read_text())
    assert snap.realized == [], "a legacy snapshot invented a realized book"
    assert snap.spread.closed_n == 0 and snap.spread.spread_open_only is None
    assert all(not r.closed for r in snap.rows), "legacy rows defaulted to closed"


def test_decisions_are_read_as_of_the_snapshot_date_too() -> None:
    """THE LOUDER HALF OF THE P1, and a mutation finding on my own fix.

    The review flagged the CLOSE half; the same defect sat on the ENTRY half. Re-running
    `--ref 2026-07-20` marked SMPL's 2026-08-04 re-entry into that day's book with
    ``days_elapsed: -15`` — a position that did not exist yet.

    First fixed inline in the CLI, where the only available pin was a STATIC artifact — so
    mutation went green on it, exactly as it had for the ticker-keying. Moved next to
    ``closed_decision_ids`` and exercised against the real ledger."""
    from vinci.monitor import decisions_as_of, entry_of

    ledger = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
    raw = [json.loads(ln) for ln in ledger.read_text().splitlines() if ln.strip()]

    def ids(d: str) -> set[str]:
        return {entry_of(r)["entry_id"] for r in decisions_as_of(raw, as_of=date.fromisoformat(d))}

    # SMPL's re-entry is dated 2026-08-04 — the live case, not a constructed one
    assert "V-SMPL-screen2-20260729" not in ids("2026-07-20"), (
        "a decision entered 2026-08-04 appeared in the book as of 2026-07-20 — it would carry "
        "negative days_elapsed")
    assert "V-SMPL-screen2-20260729" in ids("2026-08-04"), "a decision is invisible on its own "\
        "entry date"
    assert len(ids("2026-06-16")) == 0, "the book predates its first decision and is not empty"
    assert len(ids("2026-08-11")) == 4, "the full book as of 2026-08-11 is not 4 decisions"
