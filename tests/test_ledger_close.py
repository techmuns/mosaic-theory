"""CLOSE ROWS — the machinery that must exist before any position is closed.

THE LANDMINE. ``compute_spread`` partitions rows by verdict alone, and a close row carries the
ORIGINAL verdict for provenance. Append a close for a BUY without a position/close partition and
that name is counted TWICE on its own side of the BUY−AVOID spread — the one number this fund
exists to measure — silently, with nothing red anywhere.

Every pin below is written as a DEMONSTRATION of the defect it prevents: the naive partition is
computed alongside the correct one so the test states what would have gone wrong, not merely that
things are currently fine.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from vinci import monitor as mon
from vinci.schemas.ledger import EVENT_CLOSE, LedgerEntry, close_entry_id

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"


def _committed() -> list[dict]:
    return [json.loads(ln) for ln in LEDGER.read_text().splitlines() if ln.strip()]


def _open_buy(rows: list[dict]) -> dict:
    """A BUY decision row that is NOT already closed — the synthetic-close pins need a free one.

    IT occupied this role until it was closed for real on 2026-07-21; hard-coding "the first BUY"
    silently started re-closing an already-closed position. Selected by state, not by name."""
    closed = {mon.entry_of(c).get("closes_entry_id") for c in mon.close_rows(rows)}
    for r in mon.decision_rows(rows):
        e = mon.entry_of(r)
        if e["verdict"].upper().startswith("BUY") and e["entry_id"] not in closed:
            return e
    raise AssertionError("no un-closed BUY row in the committed ledger")


def _close_for(row: dict, exit_price: float = 100.0) -> dict:
    """A synthetic, well-formed close for ``row`` — built through the MODEL so the schema
    validators run, then dumped the way the ledger stores it."""
    e = LedgerEntry(
        entry_id=close_entry_id(row["candidate_id"]), candidate_id=row["candidate_id"],
        internal_id=row["internal_id"], ticker=row["ticker"], verdict=row["verdict"],
        twin_call=row.get("twin_call") or "n/a — close row",
        entry_price=row["entry_price"], entry_price_as_of=date.fromisoformat(
            str(row["entry_price_as_of"])[:10]),
        thesis="close row", kill_criteria="n/a", horizon_days=row["horizon_days"],
        confidence="medium", decided_at=datetime(2026, 7, 22, 12, 0, 0),
        event=EVENT_CLOSE, closes_entry_id=row["entry_id"],
        exit_price=exit_price, exit_price_as_of=date(2026, 7, 22),
        reason="synthetic close for the pin")
    return json.loads(e.model_dump_json())


# --- (a) THE DOUBLE-COUNT PIN -------------------------------------------------------------------
def test_a_close_row_does_not_double_count_its_position() -> None:
    """PIN (a), proven against the defective partition.

    With a close appended for the BUY, the NAIVE read (every row, partitioned by verdict) counts
    that ticker twice; ``decision_rows`` counts it once."""
    rows = _committed()
    buy = _open_buy(rows)
    with_close = [*rows, _close_for(buy)]

    def buys_named(rows_):
        return [r for r in rows_ if mon.entry_of(r)["ticker"] == buy["ticker"]
                and mon.entry_of(r)["verdict"].upper().startswith("BUY")]
    naive = buys_named(with_close)                     # every row, partitioned by verdict alone
    correct = buys_named(mon.decision_rows(with_close))
    assert len(naive) == 2, "the defect this pin exists for did not reproduce"
    assert len(correct) == 1, f"{buy['ticker']} is counted {len(correct)}x as a position"
    # and the close row is still THERE — filtered from positions, not discarded from the ledger
    assert len(mon.close_rows(with_close)) == len(mon.close_rows(rows)) + 1


def test_a2_the_spread_itself_is_unmoved_by_a_close() -> None:
    """The consequence that matters: appending a close must not move the BUY−AVOID spread. The
    call stays in calibration at its own entry price; only the realized view changes."""
    rows = _committed()
    buy = _open_buy(rows)
    before = mon.decision_rows(rows)
    after = mon.decision_rows([*rows, _close_for(buy)])
    assert [r["entry_id"] for r in before] == [r["entry_id"] for r in after]


# --- (b) and (c) PAIRING REFUSALS ---------------------------------------------------------------
def test_b_a_close_must_reference_an_existing_entry() -> None:
    """PIN (b). A close pointing at nothing is a hole in the realized book — refuse, never skip."""
    rows = _committed()
    orphan = _close_for(rows[0])
    orphan["closes_entry_id"] = "V-does-not-exist"
    with pytest.raises(ValueError, match="not a decision row"):
        mon.pair_closes([*rows, orphan])


def test_c_a_second_close_for_one_entry_is_refused() -> None:
    """PIN (c). Two closes for one position make the realized return ambiguous."""
    rows = _committed()
    buy = _open_buy(rows)
    first = _close_for(buy, exit_price=100.0)
    second = {**_close_for(buy, exit_price=120.0), "entry_id": "C-second"}
    with pytest.raises(ValueError, match="closed TWICE"):
        mon.pair_closes([*rows, first, second])


# --- (d) REALIZED RETURN IS DERIVED -------------------------------------------------------------
def test_d_realized_return_is_derived_and_never_stored() -> None:
    """PIN (d). The return is computed from the two frozen prices. Storing it would create a
    second source of truth able to drift from the numbers it came from."""
    rows = _committed()
    buy = _open_buy(rows)
    close = _close_for(buy, exit_price=buy["entry_price"] * 0.9)
    # the stored close row carries NO return field of any kind
    assert not any("return" in k or "realized" in k or "pnl" in k.lower() for k in close)
    paired = [r for r in mon.pair_closes([*rows, close]) if r["ticker"] == buy["ticker"]]
    assert len(paired) == 1
    assert paired[0]["realized_return"] == pytest.approx(-0.10, abs=1e-12)
    assert paired[0]["entry_price"] == buy["entry_price"]


# --- schema shape: a close is fully specified or refused ----------------------------------------
def _decision_kwargs(**over):
    d = {"entry_id": "V-x", "candidate_id": "x", "internal_id": "i", "ticker": "XYZ",
         "verdict": "BUY", "twin_call": "t", "entry_price": 10.0,
         "entry_price_as_of": date(2026, 1, 1), "thesis": "th", "kill_criteria": "k",
         "horizon_days": 180, "confidence": "medium",
         "decided_at": datetime(2026, 1, 1, 0, 0, 0)}
    d.update(over)
    return d


@pytest.mark.parametrize("missing", ["closes_entry_id", "exit_price", "exit_price_as_of"])
def test_a_half_specified_close_is_refused(missing: str) -> None:
    kw = _decision_kwargs(entry_id="C-x", event=EVENT_CLOSE, closes_entry_id="V-x",
                          exit_price=9.0, exit_price_as_of=date(2026, 7, 22))
    kw[missing] = None
    with pytest.raises(ValueError, match="is missing"):
        LedgerEntry(**kw)


def test_close_fields_on_a_decision_row_are_refused() -> None:
    """An exit price on a row with no event is a close hiding as a position."""
    with pytest.raises(ValueError, match="DECISION row"):
        LedgerEntry(**_decision_kwargs(exit_price=9.0))


def test_unknown_event_is_refused_and_a_close_cannot_close_itself() -> None:
    with pytest.raises(ValueError, match="unknown ledger event"):
        LedgerEntry(**_decision_kwargs(event="SELL"))
    with pytest.raises(ValueError, match="closes itself"):
        LedgerEntry(**_decision_kwargs(entry_id="C-x", event=EVENT_CLOSE, closes_entry_id="C-x",
                                       exit_price=9.0, exit_price_as_of=date(2026, 7, 22)))


# --- legacy rows are untouched ------------------------------------------------------------------
def test_every_committed_row_loads_and_the_committed_closes_pair_cleanly() -> None:
    """Every committed row validates; decision rows carry no event; every close pairs.

    Was "no committed row has an event key" until IT was closed for real on 2026-07-21. The
    invariant that actually matters is not that closes are absent — it is that every one of them
    resolves to exactly one decision row."""
    rows = _committed()
    assert rows, "committed ledger is empty"
    assert len(mon.decision_rows(rows)) + len(mon.close_rows(rows)) == len(rows)
    paired = mon.pair_closes(rows)                       # refuses loud on orphan/duplicate
    assert len(paired) == len(mon.close_rows(rows))
    for c in mon.close_rows(rows):
        e = mon.entry_of(c)
        assert e["event"] == EVENT_CLOSE and e["closes_entry_id"] and e["exit_price"] > 0
        assert (e.get("reason") or "").strip(), "a committed close must state its reason"
    for r in mon.decision_rows(rows):
        e = mon.entry_of(r)
        assert e.get("event") is None, f"{r['entry_id']} is a decision row but carries an event"
        LedgerEntry.model_validate(e)      # the payload IS the full entry


def test_close_id_convention_is_one_per_candidate() -> None:
    """The decision row is V-{candidate_id} and re-logging fails loud; the convention is widened
    exactly once, to admit one close per candidate."""
    assert close_entry_id("abc") == "C-abc"
    assert close_entry_id("abc") != "V-abc"


# --- C1.4 record layer: the lifecycle transition, with the seal unchanged -----------------------
def test_confirmed_may_transition_to_watch_while_the_seal_still_binds() -> None:
    """A position that is exited becomes a WATCH: the name is still followed, it is no longer held.

    Two things must both hold. The status transition is PERMITTED (a record whose verdict changes
    lifecycle stage is not a corrupted record), and the rationale SEAL is untouched by it — the
    reasoning recorded at the verdict may still only grow by dated amendment tags. An exit is a
    capital decision; it does not license a rewrite of why the call was made.
    """
    import json as _json

    from vinci import scenarios as sc
    from vinci import seal

    # IT held this role until its own exit moved it to watch. Pick whichever record is still
    # confirmed — the pin is about the TRANSITION, not about any particular name.
    src = next(p for p in sorted((ROOT / "scenarios").glob("[A-Z]*.json"))
               if _json.loads(p.read_text())["verdict"]["status"] == "confirmed")
    rec = _json.loads(src.read_text())
    ticker = rec["ticker"]

    rec["verdict"]["status"] = "watch"
    moved = sc.ScenarioRecord.model_validate(rec)         # validators RUN — transition allowed
    assert moved.verdict.status == "watch"

    manifest = seal.load_manifest(ROOT)
    assert seal.check(ticker=ticker, status="watch", rationale=rec["verdict"]["rationale"],
                      entry=manifest[ticker]) == [], "the seal must survive a lifecycle transition"

    # ...and the seal still REFUSES a rewrite at the new status
    rec["verdict"]["rationale"] = "Rewritten after the fact. " + rec["verdict"]["rationale"]
    assert seal.check(ticker=ticker, status="watch", rationale=rec["verdict"]["rationale"],
                      entry=manifest[ticker]), "a reworded rationale must still fail under watch"


def test_a_close_must_state_a_reason() -> None:
    """A position that closes without a stated reason cannot be reviewed later — and the exit is
    exactly the decision a track record most needs explained."""
    kw = _decision_kwargs(entry_id="C-x", event=EVENT_CLOSE, closes_entry_id="V-x",
                          exit_price=9.0, exit_price_as_of=date(2026, 7, 22))
    with pytest.raises(ValueError, match="no reason"):
        LedgerEntry(**kw)
    ok = LedgerEntry(**{**kw, "reason": "closed flat; the re-underwrite did not clear the bar"})
    assert ok.reason and ok.event == EVENT_CLOSE
