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
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from vinci.ledger.workflow import LedgerError
from vinci.schemas.ledger import (
    CORRECTION_ID_PREFIX,
    EVENT_CLOSE,
    EVENT_CORRECTION,
    EVENT_VOID,
    VOID_REASONS,
    LedgerEntry,
    VoidMark,
    corrected,
    corrections_by_decision,
    follow_up_id,
    origin_of,
    sleeve_of,
    void_entry_id,
    voids_by_decision,
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
    the day the decision was logged (a price the decider could not have seen); a decision closed
    before the corrected entry date; a blank reason. The row copies the decision's provenance, as
    a close does, tagged with the origin and sleeve its decision is read at, and is re-validated
    before the append."""
    rows = list(store.iter_ledger())
    decision = next((r for r in rows if r.entry_id == entry_id and r.event is None), None)
    if decision is None:
        raise LedgerError(f"no decision row {entry_id!r} in the ledger — nothing to correct")
    if entry_id in voids_by_decision(rows):
        raise LedgerError(f"{entry_id!r} is VOIDED — a voided decision is out of the record, and "
                          f"nothing is corrected on it")
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
        "entry_id": follow_up_id(CORRECTION_ID_PREFIX, decision.entry_id),
        "event": EVENT_CORRECTION,
        "corrects_entry_id": decision.entry_id,
        "entry_price": entry_price,
        "entry_price_as_of": entry_price_as_of,
        "reason": reason,
        "decided_at": corrected_at,
        # TAGGED AS ITS DECISION IS READ, never copied untagged: a decision logged before `origin`
        # and `sleeve` existed carries neither, and every row logged since must carry both
        # (`tests/test_sleeves.py`) — a correction is such a row, so it states the reading the
        # helpers give its decision (a legacy row reads screen/overshoot)
        "origin": origin_of(decision),
        "sleeve": sleeve_of(decision),
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


def void_decision(store: Store, *, entry_id: str, reason: str, ruled_on: date, mark: VoidMark,
                  voided_at: datetime, reason_code: str) -> LedgerEntry:
    """Append the VOID row for decision ``entry_id`` (operator ruling 2026-11-11); returns it.

    WHY A VOID. The operator ruled GOOGL's BUY out of the record — "we want to remove the buy card/
    buy verdict altogether given it was done based on really old and wrong data and we dont want
    this buy verdict to interfere in future at all". The ledger is append-only and has no delete,
    so the decision is VOIDED by an appended row: every reader of positions and returns leaves it
    out, and its decision, correction and void rows stay as audit history. Only a ruling applies it
    — ``reason`` states it and ``ruled_on`` dates it — though the mechanism is generic.

    THE RESULT TO DATE IS SEALED WITH IT (``mark``): the monitor's own mark of the decision at the
    last session it could read, taken by the caller, so the removal is seen and can never read as
    a hidden loser. It must describe the decision AS READ — its corrected entry when corrected.

    ONLY ON A PRE-REGISTERED GROUND (2026-11-13, #1004 item 5): ``reason_code`` is one of
    `VOID_REASONS` — a data error at entry, the wrong instrument, or the wrong identity. A change of
    mind is a CLOSE (`close_position`), and a close stays scored to its horizon.

    Refused, with nothing written: a ``reason_code`` outside the list; an unknown or non-decision
    ``entry_id``; a decision already
    voided; a closed decision (its outcome is realized — a close is the record of it); a blank
    reason; a mark taken on another entry than the one the decision is read at. The row copies the
    decision's provenance, as a close does, tagged as the decision is read, and is re-validated."""
    if reason_code not in VOID_REASONS:
        raise LedgerError(
            f"void reason {reason_code!r} is not pre-registered — a decision is voided only for "
            f"{sorted(VOID_REASONS)}. A change of mind is a CLOSE (`close-position`), and it stays "
            f"scored to its horizon.")
    rows = list(store.iter_ledger())
    decision = next((r for r in rows if r.entry_id == entry_id and r.event is None), None)
    if decision is None:
        raise LedgerError(f"no decision row {entry_id!r} in the ledger — nothing to void")
    if entry_id in voids_by_decision(rows):
        raise LedgerError(f"{entry_id!r} is already voided; one void per decision")
    closes = [r for r in rows if r.event == EVENT_CLOSE and r.closes_entry_id == entry_id]
    if closes:
        raise LedgerError(f"{entry_id!r} was closed by {closes[0].entry_id} — a closed position's "
                          f"outcome is realized, and a void does not undo it")
    if not reason.strip():
        raise LedgerError(f"no reason given — {entry_id!r} is voided only on stated grounds")
    # A RULING IS NEVER IN THE FUTURE. A void is in effect from ``ruled_on`` (`voids_by_decision`),
    # and the pages key on the row's presence alone, so a row dated after its own append would take
    # the decision off the web before the reports drop it.
    # ``voided_at`` is naive UTC (as `decided_at` is); a ruling is dated locally, as `--ref` is.
    appended_on = voided_at.replace(tzinfo=UTC).astimezone().date()
    if ruled_on > appended_on:
        raise LedgerError(f"ruled on {ruled_on}, after the void is appended ({appended_on}) — a "
                          f"void records a ruling already made")
    read = corrected(decision, corrections_by_decision(rows).get(entry_id))
    # THE ENTRY SESSION, not the price: the monitor marks the entry on the MARK's split basis
    # (`entry_on_basis`), so a name that split since its entry carries a restated entry price in
    # its own row — comparing the price would refuse every split name's void
    if mark.entry_date != read.entry_price_as_of:
        raise LedgerError(f"the mark reads {entry_id!r} at {mark.entry_price:g} on "
                          f"{mark.entry_date}, but the decision is read at {read.entry_price:g} on "
                          f"{read.entry_price_as_of} — the result sealed with a void is the "
                          f"decision's own")
    row = decision.model_copy(update={
        "entry_id": void_entry_id(decision.entry_id),
        "event": EVENT_VOID,
        "voids_entry_id": decision.entry_id,
        "ruled_on": ruled_on,
        "void_mark": mark,
        "void_reason_code": reason_code,
        "entry_price": read.entry_price,
        "entry_price_as_of": read.entry_price_as_of,
        "reason": reason,
        "decided_at": voided_at,
        "origin": origin_of(decision),
        "sleeve": sleeve_of(decision),
        # cleared, as on a close and a correction: none of these describe a void
        "facts": {},
        "machine_proposal": None,
        "machine_lean": None,
        "proposal_assembled_at": None,
        "disposition": None,
        "stated_limit": None,
        "thesis": f"void row - see reason; the thesis of record stays on {decision.entry_id}",
        "twin_call": f"n/a - void row; the twin call of record is on {decision.entry_id}",
        "kill_criteria": "n/a - void row",
    })
    try:
        row = LedgerEntry.model_validate(row.model_dump())
    except ValidationError as exc:
        raise LedgerError(f"the void row for {entry_id!r} is invalid and was NOT written: "
                          f"{exc}") from exc
    store.append_ledger(row)
    return row
