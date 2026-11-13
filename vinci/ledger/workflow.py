"""Decision-ledger entry workflow — record one paper verdict per judged candidate.

The discriminator judgment is **manual** (the PM's A/B/C + CIQ process); this code only *records* it
and does the one mechanical thing that must not be left to memory: **freeze the entry price/as_of**
at decision time, so scoring measures forward return from a fixed anchor. Both **BUY** and
**AVOID-terminal** verdicts are logged — they are the two legs of the BUY−AVOID spread.

The ledger is append-only: re-logging a candidate fails loud (a verdict is never overwritten).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # annotation only — no runtime import, so no cycle with `vinci.scenarios`
    from vinci.scenarios import StatedLimit

from pydantic import ValidationError

from vinci.labels import resolve_label
from vinci.schemas.data_record import Identity
from vinci.schemas.ledger import (
    CLOSE_ID_PREFIX,
    EVENT_CLOSE,
    ORIGIN_FOLLOWED,
    ORIGIN_SCREEN,
    Confidence,
    Disposition,
    LedgerEntry,
    LedgerFact,
    OriginRef,
    Verdict,
    corrected,
    corrections_by_decision,
    decision_entry_id,
    follow_up_id,
    voids_by_decision,
)
from vinci.store import Store


class SicSource(Protocol):
    """Anything that can resolve a CIK's SEC SIC (the resolver). Kept a Protocol so the ledger
    stays decoupled from the resolver implementation and is trivial to stub in tests."""

    def sic_for(self, cik: int | str) -> tuple[str | None, str | None]: ...


class LedgerError(RuntimeError):
    """The verdict cannot be recorded (unknown candidate, or no price to anchor the entry)."""


@dataclass(frozen=True)
class UnderwriteLink:
    """The LIVE underwrite record a verdict is logged against, as `log-verdict` read it
    (`vinci.ledger.underwrite.read_underwrite`): its path, the commit it was read at, the sha256 of
    its bytes (equal to that commit's blob), its base leg's horizon, its stated limit, and the
    record's own recipe re-run at a price (``ratio_at``), so the ratio is struck at the frozen
    entry inside `log_verdict` — the one place that price exists."""

    ref: str                       # e.g. "scenarios/SMPL.json"
    commit: str                    # full sha of the commit the record was read at
    sha256: str                    # of the record's bytes
    horizon_years: float | None    # the base leg's `years_to_terminal`
    limit: StatedLimit | None
    #: price → (ratio, why undefined); the recipe's own arithmetic, never a second definition
    ratio_at: Callable[[float], tuple[float | None, str | None]]


#: ``origin_ref`` for a followed row is built from its follow entry; screen rows build their own
def follow_origin(ticker: str, followed_since: date) -> OriginRef:
    """The origin of a FOLLOWED row: its follow-list entry and the date it was followed from."""
    return OriginRef(kind="follow_entry", id=ticker.upper(), followed_since=followed_since)


def require_underwrite(ticker: str, underwrite: UnderwriteLink | None,
                       no_underwrite_reason: str | None) -> str | None:
    """THE UNDERWRITE REFUSALS, one definition (2026-11-13, #1004 item 5): asked by `log-verdict`
    before its paid confirmation draws anything, and again at the seat in `log_verdict`. Returns
    the stated reason for logging with no record (stripped), or None.

    A verdict is logged against its live record, or states why it has none; a reason beside a
    live record is refused. A record WITHOUT A HORIZON loads, prints and recomputes as it always
    has (refusing at load would repeat #762); it is refused only here, at the decision, because a
    call struck on a record with no realisation date has no IRR to stand on."""
    why_none = (no_underwrite_reason or "").strip() or None
    if underwrite is None and why_none is None:
        raise LedgerError(
            f"REFUSED: {ticker} has no live underwrite record (scenarios/{ticker.upper()}.json) "
            f"— a verdict is logged against the record that priced it, or states why there is "
            f"none (`--no-underwrite-reason`).")
    if underwrite is not None and why_none is not None:
        raise LedgerError(
            f"{ticker} has a live underwrite record ({underwrite.ref}), so no reason for "
            f"logging without one applies — the verdict is sealed against the record")
    if underwrite is not None and underwrite.horizon_years is None:
        raise LedgerError(
            f"REFUSED: {underwrite.ref} states no horizon (its base leg has no years_to_terminal), "
            f"so its IRR is undefined — a verdict is not logged on a record with no realisation "
            f"date. Re-underwrite with a stated horizon; the record itself still loads as it is.")
    return why_none


def _require_verdict_in_sleeve(
    verdict: Verdict, sleeve: str | None, *, machine_proposal: Verdict | None = None
) -> None:
    """Verdict AND sealed proposal must belong to the sleeve's vocabulary — refused at WRITE.

    THE LEDGER IS APPEND-ONLY, so this has to refuse here or not at all: a row recording a verdict
    its book does not use cannot be un-logged, and it would fall out of that book's curve (which
    reads the sleeve's own leg labels) without appearing anywhere else. Failing at scoring time
    instead would mean the damage is already sealed.

    THE PROPOSAL IS CHECKED TOO, and that half is subtler than the verdict half. ``disposition`` is
    stamped by comparing the human verdict to the machine proposal, so a proposal drawn from
    ANOTHER book's vocabulary does not merely look odd — it makes the comparison meaningless and
    seals OVERRIDDEN onto a row where the machine and the human may well have agreed.

    SINCE PR-2b THE MAPPING IS PER-BOOK, so this no longer fires on the normal path: a quality
    dossier's bearish lean proposes PASS, which IS in quality's vocabulary. The check STAYS because
    it guards the join rather than the mapping — a caller passing a proposal sealed under a
    different sleeve than the row it is writing (a stale artifact, a re-tagged name, a future
    caller that reads the two from different places) would still corrupt the disposition, and that
    is a class the mapping cannot close from its own side."""
    if sleeve is None:
        return                                   # legacy/untagged: the pre-sleeve vocabulary holds
    from vinci.sleeves import BY_KEY

    row = BY_KEY.get(sleeve)
    if row is None:
        return                                   # validated at every write path; nothing to check
    # THE ACTIVATION GATE, ENFORCED AT THE WRITE BOUNDARY (review #380). The registry says which
    # books may appear on a decision-ledger row; `theme` validates in its OWN append-only
    # ratification ledger and `neglect` is dormant. Without this a followed entry naming either one
    # would append a row to the fund's proof ledger under a book that is not being measured there —
    # and the ledger is append-only, so it could not be taken back out.
    if not row.ledger_active:
        raise LedgerError(
            f"sleeve {sleeve!r} is defined but NOT activated for the decision ledger "
            f"(vinci/sleeves.py: ledger_active=False). "
            + ("`theme` validates in its own append-only ratification ledger; a single name from a "
               "theme is logged under overshoot/quality with the variant-vs-cross-section edge "
               "basis." if sleeve == "theme" else
               "Activate it deliberately — with its kill criterion stated first — before logging "
               "a verdict under it."))
    if verdict.value not in row.verdicts:
        raise LedgerError(
            f"sleeve {sleeve!r} records {list(row.verdicts)}, not {verdict.value!r} — use one of "
            f"the sleeve's own labels. Recording {verdict.value!r} here would put another book's "
            f"claim against a {row.label.lower()}.")
    if machine_proposal is not None and machine_proposal.value not in row.verdicts:
        raise LedgerError(
            f"the sealed machine proposal is {machine_proposal.value!r}, which is not in sleeve "
            f"{sleeve!r}'s vocabulary {list(row.verdicts)}. The proposal mapping is still GLOBAL "
            f"(the per-sleeve mapping lands with PR-2b), so it proposed another book's label for "
            f"this name. Logging now would stamp a confirm/override disposition off a comparison "
            f"between two different vocabularies — a disagreement statistic measuring a mismatch.")


def log_verdict(
    store: Store,
    *,
    resolver: SicSource,
    candidate_id: str,
    verdict: Verdict,
    twin_call: str,
    thesis: str,
    facts: Mapping[str, LedgerFact] | None = None,
    kill_criteria: str,
    horizon_days: int,
    confidence: Confidence,
    decided_at: datetime,
    reference_date: date,
    staleness_days: int,
    stated_limit: StatedLimit | None = None,
    benchmark: str = "IWM",
    machine_proposal: Verdict | None = None,
    machine_lean: str | None = None,
    proposal_assembled_at: datetime | None = None,
    revealed_pre_verdict: bool = False,
    machine_tally: Mapping[str, Any] | None = None,
    identity: Identity | None = None,
    origin: str = ORIGIN_SCREEN,
    sleeve: str | None = None,
    underwrite: UnderwriteLink | None,
    no_underwrite_reason: str | None = None,
    origin_ref: OriginRef | None = None,
) -> LedgerEntry:
    """Freeze the entry price + the sector and append a verdict for ``candidate_id``; returns it.

    The sector is captured HERE, at log time, from the name's EDGAR SIC (via ``resolver``) → it is
    frozen with the verdict and never derived later, so the spread is sector-readable forever.

    The machine's SEALED proposal (2026-07-13 pivot) arrives from the caller — derived by
    ``vinci.dossier.verdict.derive_proposal`` over the COMMITTED dossier artifact, never recomputed
    from live data — and the disposition (confirm / override / no-proposal) is stamped here, once:
    the human's verdict is the verdict of record; the disposition is the disagreement ledger.

    ``facts`` (item 18a) carries the TYPED, source-stamped numbers the thesis rests on, alongside
    the prose and never replacing it. Optional and defaulting to empty: this parameter changes the
    write path's SHAPE so a structured fact CAN be recorded, and does not oblige any caller to
    record one. Rows logged before it existed keep an empty mapping and are never backfilled — a
    sealed decision is not rewritten to satisfy a later schema.

    THE FOLLOWED ROUTE (2026-08-09). Until now this refused any name without a ``CandidateRecord``,
    so a followed name could carry a dossier and an underwrite and still be unable to record a
    verdict at all — the fund could research a megacap and never log what it decided. ``identity``
    opens that door and ONLY that door: it is used solely when the store has no candidate, and the
    caller must pass ``origin=ORIGIN_FOLLOWED`` with it, so a row that did not come through the
    screen says so in the record rather than being inferred later from a missing join.

    IT IS NOT A BACK DOOR FOR A FORGED SCREEN ROW. A supplied identity with the default
    ``screen`` origin is REFUSED: screen origin asserts screen admission, and the only honest proof
    of that is the candidate record itself. The caller is responsible for establishing that the
    name is genuinely followed (the CLI checks ``followed.json``) — this function refuses the
    combination that would let a caller skip that check silently."""
    cand = store.get_candidate(candidate_id)
    if cand is None and identity is None:
        raise LedgerError(
            f"no candidate {candidate_id!r} in the store (run the screen first). If this is a "
            f"FOLLOWED name, log it by ticker — it has no candidate record by construction.")
    if cand is not None:
        ident = cand.data_record.identity
    else:
        if origin != ORIGIN_FOLLOWED:
            raise LedgerError(
                f"an identity was supplied without a candidate record, but origin is {origin!r}. "
                f"Only {ORIGIN_FOLLOWED!r} may be logged without one — the candidate record IS the "
                f"proof of screen admission, and a row claiming it without one is a fabricated "
                f"screen verdict.")
        assert identity is not None  # narrowed by the guard above; mypy cannot see it
        ident = identity
    # EVERY NEW ROW NAMES ITS ORIGIN AND ITS BOOK (2026-11-13, #1004 item 5). A screen row names
    # its candidate record's run; a followed row names its follow entry, which only the caller can
    # read (the ledger package reads no follow list). The screen's book is the default book: a
    # screen row left untagged read as overshoot through `sleeve_of` and skipped the book's
    # vocabulary check below, so a screen PASS could be sealed into a book that records none.
    if cand is not None:
        if origin_ref is not None:
            raise LedgerError(
                f"{candidate_id!r} is a screen candidate, so its origin is its screen run — an "
                f"origin_ref passed for it ({origin_ref.kind} {origin_ref.id!r}) would be dropped")
        origin_ref = OriginRef(kind="screen_run", id=cand.candidate_id,
                               screen_run_at=cand.screen_run_at,
                               screens_fired=tuple(cand.screens_fired))
        if sleeve is None:
            from vinci.sleeves import DEFAULT_SLEEVE
            sleeve = DEFAULT_SLEEVE
    elif origin_ref is None or origin_ref.kind != "follow_entry":
        raise LedgerError(
            f"a FOLLOWED verdict for {ident.ticker} names its follow entry (origin_ref, with "
            f"followed_since) — a row whose origin is unnamed cannot be traced to the decision "
            f"that covered the name")
    _require_verdict_in_sleeve(verdict, sleeve, machine_proposal=machine_proposal)
    # THE UNDERWRITE LINK (2026-11-13, #1004 item 5), refused HERE as the limit is: the ledger is
    # append-only (`require_underwrite`).
    why_none = require_underwrite(ident.ticker, underwrite, no_underwrite_reason)
    sector = resolve_label(resolver.sic_for(ident.cik)[0]).sector

    try:
        # point-in-time: freeze on the latest bar ON OR BEFORE the decision date — never a future
        # one (that would be lookahead). Fails loud if no such bar exists.
        close = store.close_as_of(
            ident.internal_id, reference_date=reference_date, staleness_days=staleness_days
        )
    except LookupError as exc:
        raise LedgerError(
            f"no price to freeze an entry for {ident.ticker} ({ident.internal_id}): {exc}"
        ) from exc
    if not close.is_known or close.value is None or close.as_of is None:
        raise LedgerError(
            f"no price to freeze an entry for {ident.ticker} "
            f"({ident.internal_id}) — refresh EOD bars first"
        )
    # A STALE CLOSE IS NO ENTRY (TeamNostra fix request 2, RF-D7, 2026-11-09). `close_as_of` marks
    # a bar older than ``staleness_days`` STALE, and this checked `is_known` — true for a stale
    # value — so the parameter had no effect: a 31-day-old close was sealed, and the row's forward
    # clock (scored from `entry_price_as_of`) started 31 days before the decision. Live on the
    # committed ledger: GOOGL's BUY, decided 2026-08-28, sealed the 2026-08-14 close. A seal is
    # now the price the decision was made at, or nothing: refresh the bars and log again. The
    # sealed rows are never rewritten — how GOOGL's is read is the operator's ruling.
    if not close.is_evaluable:
        age = (reference_date - close.as_of).days
        raise LedgerError(
            f"REFUSED: the latest close for {ident.ticker} on or before {reference_date} is "
            f"{close.value:,.2f} from {close.as_of}, {age} days old (more than the "
            f"{staleness_days} a seal allows). Sealing it would start this decision's forward "
            f"clock {age} days before it was made — refresh EOD bars "
            f"(`vinci refresh {ident.ticker} --start {close.as_of} --end {reference_date}`) and "
            f"log again."
        )
    # ...AND STALE AGAINST THE DECISION ITSELF (review round 0). The bound above is measured from
    # ``reference_date``, which the CLI takes from `--ref`; a `--ref` set back before the day the
    # verdict is logged would seal that old close as fresh while ``decided_at`` is today — RF-D7's
    # failure through another input, and a door to deciding with hindsight. The one decision
    # moment this code knows is ``decided_at``, so the close is held to it as well.
    lag = (decided_at.date() - close.as_of).days
    if lag > staleness_days:
        raise LedgerError(
            f"REFUSED: {ident.ticker}'s seal would be the {close.value:,.2f} close of "
            f"{close.as_of}, {lag} days before this verdict is logged ({decided_at.date()}; "
            f"the reference date given is {reference_date}). A decision is sealed at the price it "
            f"is made at: more than {staleness_days} days back is a back-dated decision, never "
            f"logged unmarked — log it at a current reference date."
        )

    # THE STATED-LIMIT GATE, and its seat is mechanical rather than stylistic. The entry price is
    # frozen HERE, inside this function; the CLI's pre-write gates (the edge-basis check) run
    # before it exists. A limit gate in the CLI would have to resolve the close a SECOND time, and
    # two resolutions of one price is the divergent-parse class this repo keeps paying for. So it
    # sits beside `_require_verdict_in_sleeve`, at the first point where the verdict and the price
    # both exist — and before the append, because the ledger is append-only: "the gate has to
    # refuse here or not at all" (the edge-basis gate's own words).
    #
    # BUY ONLY. An AVOID_TERMINAL row freezes a REFERENCE price for scoring, not a purchase, so
    # refusing it above a limit would be meaningless — VRRM's 4.71 is not capital at risk.
    #
    # READS THE COMMITTED RECORD, never a recomputed ceiling: the question is what the analyst
    # committed to, not what today's legs imply. A record with no limit is not refused — `unstated`
    # is not `absent`, and six of seven records carry no limit today.
    # A DEFERRED limit carries NO price and must enforce nothing — the analyst looked and
    # chose not to commit, which is a different fact from a commitment. `price is None` is
    # therefore checked explicitly rather than trusted from `state`: two ways to ask the
    # same question is how they drift, and the model already refuses the mismatch.
    if underwrite is not None and stated_limit is None:
        stated_limit = underwrite.limit      # the record's limit, read once with the record
    _lim = stated_limit.price if stated_limit is not None else None
    if (verdict is Verdict.BUY and stated_limit is not None
            and _lim is not None and close.value > _lim):
        raise LedgerError(
            f"REFUSED: {ident.ticker} BUY at {close.value:,.2f} (as of {close.as_of}) is ABOVE the "
            f"stated limit of {_lim:,.2f} from {stated_limit.stated_at}"
            + (f" — {stated_limit.note}" if stated_limit.note else "")
            + ". The limit is the analyst's commitment and the ledger is append-only, so this "
              "cannot be un-logged: either wait for the price, or restate the limit deliberately.")

    # Disposition — stamped ONCE, at log time (every post-pivot entry carries one; a None
    # disposition in the ledger therefore always means "logged before the pivot").
    disposition = (
        Disposition.NO_PROPOSAL if machine_proposal is None
        else Disposition.CONFIRMED if machine_proposal is verdict
        else Disposition.OVERRIDDEN
    )
    # THE RATIO AT ENTRY, by the record's own recipe at the price just frozen — never the record's
    # spot, which is the underwrite date's and has since moved
    ratio, ratio_why = (underwrite.ratio_at(close.value) if underwrite is not None
                        else (None, None))
    entry = LedgerEntry(
        # one OPEN decision per candidate, never entered before the earlier one left the book
        entry_id=next_decision_id(store, candidate_id, entering_on=close.as_of),
        candidate_id=candidate_id,
        internal_id=ident.internal_id,
        ticker=ident.ticker,
        sector=sector,
        origin=origin,
        sleeve=sleeve,
        origin_ref=origin_ref,
        verdict=verdict,
        twin_call=twin_call,
        entry_price=close.value,  # frozen
        entry_price_as_of=close.as_of,  # frozen
        ratio_at_entry=ratio,
        ratio_at_entry_undefined=ratio_why if ratio is None and underwrite is not None else None,
        underwrite_ref=underwrite.ref if underwrite is not None else None,
        underwrite_commit=underwrite.commit if underwrite is not None else None,
        underwrite_sha256=underwrite.sha256 if underwrite is not None else None,
        no_underwrite_reason=why_none,
        thesis=thesis,
        facts=dict(facts or {}),
        kill_criteria=kill_criteria,
        horizon_days=horizon_days,
        confidence=confidence,
        decided_at=decided_at,
        benchmark=benchmark,
        machine_proposal=machine_proposal,
        machine_lean=machine_lean,
        proposal_assembled_at=proposal_assembled_at,
        machine_tally=dict(machine_tally) if machine_tally is not None else None,
        disposition=disposition,
        revealed_pre_verdict=revealed_pre_verdict,  # anti-anchoring: did the human peek? (No)
    )
    store.append_ledger(entry)
    return entry


def next_decision_id(store: Store, candidate_id: str, *, entering_on: date | None = None) -> str:
    """The id the next decision for ``candidate_id`` takes (operator ruling 2026-11-11): its first
    is ``V-{candidate}``; a fresh one after the earlier is CLOSED or VOIDED is ``V-{candidate}-{n}``
    (`decision_entry_id`). While an earlier decision is still open it is refused — a candidate
    holds one open decision, so a re-log can never stand beside the call it would contradict.

    NOR BEFORE THE EARLIER ONE LEFT THE BOOK (Codex round 2 on #984). A close takes a decision out
    of the book from its exit session and a void from its ruling date, as every reader reads them
    (`closed_decision_ids`, `voids_by_decision(as_of=…)`). A fresh decision ``entering_on`` an
    earlier date — a back-dated ``--ref`` — would stand beside it in every cut between the two, so
    it is refused. On or after that date it is the next decision."""
    rows = list(store.iter_ledger())
    mine = [r for r in rows if r.candidate_id == candidate_id and r.event is None]
    if not mine:
        return decision_entry_id(candidate_id)
    if still_open := _open_decisions(rows, mine):
        raise LedgerError(
            f"{candidate_id!r} already holds an open decision {still_open[0].entry_id!r} — the "
            f"ledger is append-only: close it, or have it voided by a ruling, before a fresh "
            f"decision is logged")
    if entering_on is not None:
        left = {r.closes_entry_id: r.exit_price_as_of for r in rows
                if r.event == EVENT_CLOSE and r.exit_price_as_of is not None}
        left.update({k: v.ruled_on for k, v in voids_by_decision(rows).items()
                     if v.ruled_on is not None})
        for d in mine:
            if (gone := left.get(d.entry_id)) is not None and entering_on < gone:
                raise LedgerError(
                    f"a fresh {candidate_id!r} decision would enter on {entering_on}, before "
                    f"{d.entry_id!r} left the book on {gone} — every cut between the two would "
                    f"hold both; enter it on or after {gone}")
    return decision_entry_id(candidate_id, len(mine) + 1)


def _open_decisions(rows: list[LedgerEntry], decisions: list[LedgerEntry]) -> list[LedgerEntry]:
    """``decisions`` that neither a close nor a void in ``rows`` (the whole ledger) names — the
    one rule `next_decision_id` and `close_position` both read "open" by."""
    closed = {r.closes_entry_id for r in rows if r.event == EVENT_CLOSE}
    voided = voids_by_decision(rows)
    return [d for d in decisions if d.entry_id not in closed and d.entry_id not in voided]


def close_position(
    store: Store,
    *,
    candidate_id: str,
    exit_price: float,
    exit_price_as_of: date,
    reason: str,
    closed_at: datetime,
    check: Callable[[LedgerEntry], None] | None = None,
) -> LedgerEntry:
    """Append the CLOSE row for ``candidate_id``'s decision; returns it.

    ``check`` runs on the VALIDATED close row after every guard here and before the append, and a
    check that raises writes nothing. It is how `close-position` reads the vendors its realized
    return needs (the split record, confirmed; the dividends) only for a close this function would
    write, and refuses before the row exists (RF-D2, 2026-11-09) — the guards stay in one place.

    THE WRITER THAT WAS NEVER BUILT. `4f34c11` shipped the close-row SCHEMA, the readers
    (``monitor.close_rows`` / ``pair_closes``), the display and the id helper — everything except a
    way to write one. So the two committed closes were hand-authored JSON, which is how a row can
    reach an append-only record without passing a single guard.

    THE PROVENANCE FIELDS ARE COPIED, NEVER RETYPED. A close repeats its decision's ticker,
    candidate, verdict, frozen entry price and horizon so the realized view can pair them; retyping
    those by hand is how a close comes to describe a position that does not exist. What the close
    does NOT inherit is anything that would read as a second underwrite: ``facts`` (the schema
    refuses them outright — they belong to the decision they justified), the machine proposal and
    its disposition (no proposal was made about closing), and the thesis/twin/kill prose, which are
    replaced by pointers back to the decision of record.
    """
    rows = list(store.iter_ledger())
    decisions = [r for r in rows if r.candidate_id == candidate_id and r.event is None]
    if not decisions:
        known = sorted({r.candidate_id for r in rows if r.event is None})
        raise LedgerError(
            f"no open decision for candidate {candidate_id!r} — nothing to close. Known: {known}")
    if len(decisions) > 1:
        # A FRESH DECISION AFTER A CLOSE OR A VOID (`next_decision_id`): the candidate holds one
        # OPEN decision, and that is the one a close names
        live = _open_decisions(rows, decisions)
        if len(live) != 1:
            raise LedgerError(
                f"{candidate_id!r} has {len(decisions)} decision rows "
                f"({sorted(d.entry_id for d in decisions)}) and {len(live)} of them open — a close "
                f"names exactly one open position.")
        decisions = live
    # A VOIDED DECISION IS NO POSITION (operator ruling 2026-11-11): it was ruled out of the
    # record, so there is nothing to close — a close row would put it back into the realized book
    if (void := voids_by_decision(rows).get(decisions[0].entry_id)) is not None:
        raise LedgerError(
            f"{decisions[0].entry_id!r} is VOIDED by {void.entry_id} (ruled {void.ruled_on}) — it "
            f"is out of the record, and a voided decision is never closed")
    # READ AT ITS CORRECTION (RF-D7): the exit is guarded against, and the close repeats, the entry
    # every reader of returns measures from — a close typed between the sealed and the corrected
    # entry date would otherwise pass here and pair an exit before its entry in the realized view
    decision = corrected(decisions[0], corrections_by_decision(rows).get(decisions[0].entry_id))
    # ALREADY CLOSED → REFUSE. `pair_closes` raises on a duplicated close, so a second one would
    # not corrupt the realized book quietly — it would break every later monitor run instead, at a
    # point far from the command that caused it.
    existing = [r for r in rows if r.closes_entry_id == decision.entry_id]
    if existing:
        raise LedgerError(
            f"{candidate_id!r} is already closed by {existing[0].entry_id} "
            f"(exit {existing[0].exit_price} on {existing[0].exit_price_as_of}). The ledger is "
            f"append-only: a correction is a new DECISION, never a second close.")
    if exit_price_as_of < decision.entry_price_as_of:
        raise LedgerError(
            f"exit date {exit_price_as_of} precedes the frozen entry date "
            f"{decision.entry_price_as_of} — a position cannot close before it opened.")
    return _append_close(store, decision, exit_price, exit_price_as_of, reason, closed_at, check)


def _append_close(
    store: Store, decision: LedgerEntry, exit_price: float, exit_price_as_of: date,
    reason: str, closed_at: datetime, check: Callable[[LedgerEntry], None] | None = None,
) -> LedgerEntry:
    """Build, VALIDATE and append the close row. Split out so the guards above read as one list.

    THE ROW IS RE-VALIDATED BEFORE IT IS PERSISTED (operator review P1 on #417), and it has to be:
    ``model_copy(update=...)`` does NOT run the model validators, and ``Store.append_ledger`` only
    serializes. So `close-position --exit-price -1` sailed past the guards above, printed a success
    line, and wrote a row the close-row schema forbids straight into an APPEND-ONLY record — where
    it cannot be deleted. The next ``iter_ledger()`` then raised, which means one bad flag made the
    whole decision ledger unreadable: every later close, `vinci ledger`, `score`, and the monitor's
    DB path.

    Validating here converts that into a refusal at the command, before anything is written.
    ``Store.append_ledger`` also re-validates now, as the backstop for every OTHER writer — this
    call site is simply the one that had the hole.
    """
    close = decision.model_copy(update={
        "entry_id": follow_up_id(CLOSE_ID_PREFIX, decision.entry_id),
        "event": EVENT_CLOSE,
        "closes_entry_id": decision.entry_id,
        "exit_price": exit_price,
        "exit_price_as_of": exit_price_as_of,
        "reason": reason,
        "decided_at": closed_at,
        # cleared — see the docstring: none of these describe a close
        "facts": {},
        "machine_proposal": None,
        "machine_lean": None,
        "proposal_assembled_at": None,
        "disposition": None,
        "stated_limit": None,
        "thesis": f"close row - see reason; the thesis of record stays on {decision.entry_id}",
        "twin_call": f"n/a - close row; the twin call of record is on {decision.entry_id}",
        "kill_criteria": "n/a - close row",
    })
    try:
        close = LedgerEntry.model_validate(close.model_dump())
    except ValidationError as exc:
        # Re-raised as the type this module documents, so a caller catching LedgerError does not
        # silently miss exactly the failure that would have corrupted the record.
        raise LedgerError(
            f"the close row for {decision.candidate_id!r} is invalid and was NOT written: {exc}"
        ) from exc
    if check is not None:
        check(close)
    store.append_ledger(close)
    return close
