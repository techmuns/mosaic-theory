"""ENTRY CORRECTIONS — a decision sealed on a stale close is corrected by an APPENDED row
(TeamNostra fix request 2, RF-D7; operator ruling 2026-11-09).

WHY. `log_verdict` checked `is_known`, true for a STALE close, so a decision could be sealed on a
close days before it was made, and its forward clock — scored from `entry_price_as_of` — started
there. The code is fixed going forward (a stale close is refused at sealing); the committed rows
are corrected here, by ONE rule applied to every row, never by hand to one.

THE RULE (`rule_session`). An entry's corrected price is the last US close COMPLETED at the
decision moment: a decision made after a session's close uses that close, one made before it uses
the session before. HOW A DECISION TIME IS READ: ``decided_at`` is the logging machine's local
time — `log-verdict` stamps ``datetime.now()`` and the operator works in India — so it is read as
IST and set against each session's 16:00 ET close. A ``decided_at`` of exactly 00:00:00 carries a
DATE only (the hand-authored early rows); it is read as made during that IST day, at its end — the
latest close it could have seen. Half-day sessions (13:00 ET closes) are read at 16:00: a decision
between the two on such a day reads that day's close as not yet completed.

THE RECORD. The decision row is never rewritten. A CORRECTION row (`EVENT_CORRECTION`) names it and
carries the corrected entry price and date; every reader of returns reads the decision through
`schemas.ledger.corrected`, and its horizon runs from the corrected date. One correction per
decision.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from vinci.ledger.workflow import LedgerError
from vinci.schemas.ledger import (
    EVENT_CORRECTION,
    LedgerEntry,
    correction_entry_id,
    corrections_by_decision,
)
from vinci.store import Store

#: where ``decided_at`` was stamped, and where the sessions close
DECIDED_TZ = ZoneInfo("Asia/Kolkata")
MARKET_TZ = ZoneInfo("America/New_York")
MARKET_CLOSE = time(16, 0)


def decision_moment(decided_at: datetime) -> datetime:
    """``decided_at`` as a moment in US Eastern time (see the module note)."""
    date_only = decided_at.time() == time(0, 0)     # `time()` carries the microseconds too
    local = datetime.combine(decided_at.date(), time(23, 59, 59)) if date_only else decided_at
    return local.replace(tzinfo=DECIDED_TZ).astimezone(MARKET_TZ)


def rule_session(decided_at: datetime, sessions: Sequence[date]) -> date | None:
    """The last of ``sessions`` whose close had completed at the decision moment — the session the
    entry is read at. None when no session in ``sessions`` closed before it."""
    moment = decision_moment(decided_at)
    done = [d for d in sorted(sessions)
            if datetime.combine(d, MARKET_CLOSE, MARKET_TZ) <= moment]
    return done[-1] if done else None


def correct_entry(store: Store, *, entry_id: str, entry_price: float, entry_price_as_of: date,
                  reason: str, corrected_at: datetime) -> LedgerEntry:
    """Append the CORRECTION row for decision ``entry_id``; returns it.

    Refused, with nothing written: an unknown or non-decision ``entry_id``; a decision already
    corrected; a correction equal to the sealed entry (nothing to correct); a corrected date after
    the day the decision was logged (a price the decider could not have seen); a blank reason. The
    row copies the decision's provenance, as a close does, and is re-validated before the append."""
    rows = list(store.iter_ledger())
    decision = next((r for r in rows if r.entry_id == entry_id and r.event is None), None)
    if decision is None:
        raise LedgerError(f"no decision row {entry_id!r} in the ledger — nothing to correct")
    if entry_id in corrections_by_decision(rows):
        raise LedgerError(f"{entry_id!r} is already corrected; the ledger is append-only, and one "
                          f"correction per decision is the rule")
    if (entry_price, entry_price_as_of) == (decision.entry_price, decision.entry_price_as_of):
        raise LedgerError(f"{entry_id!r} is sealed at {decision.entry_price:g} on "
                          f"{decision.entry_price_as_of} already — nothing to correct")
    if entry_price_as_of > decision.decided_at.date():
        raise LedgerError(f"the corrected entry date {entry_price_as_of} is after {entry_id!r} was "
                          f"logged ({decision.decided_at.date()}) — a price the decision could not "
                          f"have been made at")
    # A POSITION CLOSED BEFORE THE CORRECTED ENTRY would pair an exit dated before its entry — the
    # realized view (`monitor.pair_closes`) would read its dividends over a reversed window
    early = [r for r in rows if r.closes_entry_id == entry_id
             and r.exit_price_as_of is not None and r.exit_price_as_of < entry_price_as_of]
    if early:
        raise LedgerError(f"{entry_id!r} was closed by {early[0].entry_id} on "
                          f"{early[0].exit_price_as_of}, before the corrected entry date "
                          f"{entry_price_as_of} — a position cannot close before it opened")
    row = decision.model_copy(update={
        "entry_id": correction_entry_id(decision.candidate_id),
        "event": EVENT_CORRECTION,
        "corrects_entry_id": decision.entry_id,
        "entry_price": entry_price,
        "entry_price_as_of": entry_price_as_of,
        "reason": reason,
        "decided_at": corrected_at,
        # cleared, as on a close: none of these describe a correction
        "facts": {},
        "machine_proposal": None,
        "machine_lean": None,
        "proposal_assembled_at": None,
        "disposition": None,
        "stated_limit": None,
        "thesis": f"correction row - see reason; the thesis of record stays on {decision.entry_id}",
        "twin_call": f"n/a - correction row; the twin call of record is on {decision.entry_id}",
        "kill_criteria": "n/a - correction row",
    })
    try:
        row = LedgerEntry.model_validate(row.model_dump())
    except ValidationError as exc:
        raise LedgerError(f"the correction row for {entry_id!r} is invalid and was NOT written: "
                          f"{exc}") from exc
    store.append_ledger(row)
    return row
