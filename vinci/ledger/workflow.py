"""Decision-ledger entry workflow — record one paper verdict per judged candidate.

The discriminator judgment is **manual** (the PM's A/B/C + CIQ process); this code only *records* it
and does the one mechanical thing that must not be left to memory: **freeze the entry price/as_of**
at decision time, so scoring measures forward return from a fixed anchor. Both **BUY** and
**AVOID-terminal** verdicts are logged — they are the two legs of the BUY−AVOID spread.

The ledger is append-only: re-logging a candidate fails loud (a verdict is never overwritten).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Protocol

from vinci.labels import resolve_label
from vinci.schemas.data_record import Identity
from vinci.schemas.ledger import (
    ORIGIN_FOLLOWED,
    ORIGIN_SCREEN,
    Confidence,
    Disposition,
    LedgerEntry,
    LedgerFact,
    Verdict,
)
from vinci.store import Store


class SicSource(Protocol):
    """Anything that can resolve a CIK's SEC SIC (the resolver). Kept a Protocol so the ledger
    stays decoupled from the resolver implementation and is trivial to stub in tests."""

    def sic_for(self, cik: int | str) -> tuple[str | None, str | None]: ...


class LedgerError(RuntimeError):
    """The verdict cannot be recorded (unknown candidate, or no price to anchor the entry)."""


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
    benchmark: str = "IWM",
    machine_proposal: Verdict | None = None,
    machine_lean: str | None = None,
    proposal_assembled_at: datetime | None = None,
    revealed_pre_verdict: bool = False,
    identity: Identity | None = None,
    origin: str = ORIGIN_SCREEN,
    sleeve: str | None = None,
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
    _require_verdict_in_sleeve(verdict, sleeve, machine_proposal=machine_proposal)
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

    # Disposition — stamped ONCE, at log time (every post-pivot entry carries one; a None
    # disposition in the ledger therefore always means "logged before the pivot").
    disposition = (
        Disposition.NO_PROPOSAL if machine_proposal is None
        else Disposition.CONFIRMED if machine_proposal is verdict
        else Disposition.OVERRIDDEN
    )
    entry = LedgerEntry(
        entry_id=f"V-{candidate_id}",  # one verdict per candidate; re-log → append-only conflict
        candidate_id=candidate_id,
        internal_id=ident.internal_id,
        ticker=ident.ticker,
        sector=sector,
        origin=origin,
        sleeve=sleeve,
        verdict=verdict,
        twin_call=twin_call,
        entry_price=close.value,  # frozen
        entry_price_as_of=close.as_of,  # frozen
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
        disposition=disposition,
        revealed_pre_verdict=revealed_pre_verdict,  # anti-anchoring: did the human peek? (No)
    )
    store.append_ledger(entry)
    return entry
