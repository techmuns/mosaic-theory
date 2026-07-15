"""Decision-ledger entry workflow — record one paper verdict per judged candidate.

The discriminator judgment is **manual** (the PM's A/B/C + CIQ process); this code only *records* it
and does the one mechanical thing that must not be left to memory: **freeze the entry price/as_of**
at decision time, so scoring measures forward return from a fixed anchor. Both **BUY** and
**AVOID-terminal** verdicts are logged — they are the two legs of the BUY−AVOID spread.

The ledger is append-only: re-logging a candidate fails loud (a verdict is never overwritten).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from vinci.schemas.ledger import Confidence, Disposition, LedgerEntry, Verdict
from vinci.sectors import sector_for_sic
from vinci.store import Store


class SicSource(Protocol):
    """Anything that can resolve a CIK's SEC SIC (the resolver). Kept a Protocol so the ledger
    stays decoupled from the resolver implementation and is trivial to stub in tests."""

    def sic_for(self, cik: int | str) -> tuple[str | None, str | None]: ...


class LedgerError(RuntimeError):
    """The verdict cannot be recorded (unknown candidate, or no price to anchor the entry)."""


def log_verdict(
    store: Store,
    *,
    resolver: SicSource,
    candidate_id: str,
    verdict: Verdict,
    twin_call: str,
    thesis: str,
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
) -> LedgerEntry:
    """Freeze the entry price + the sector and append a verdict for ``candidate_id``; returns it.

    The sector is captured HERE, at log time, from the name's EDGAR SIC (via ``resolver``) → it is
    frozen with the verdict and never derived later, so the spread is sector-readable forever.

    The machine's SEALED proposal (2026-07-13 pivot) arrives from the caller — derived by
    ``vinci.dossier.verdict.derive_proposal`` over the COMMITTED dossier artifact, never recomputed
    from live data — and the disposition (confirm / override / no-proposal) is stamped here, once:
    the human's verdict is the verdict of record; the disposition is the disagreement ledger."""
    cand = store.get_candidate(candidate_id)
    if cand is None:
        raise LedgerError(f"no candidate {candidate_id!r} in the store (run the screen first)")
    ident = cand.data_record.identity
    sector = sector_for_sic(resolver.sic_for(ident.cik)[0])

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
        verdict=verdict,
        twin_call=twin_call,
        entry_price=close.value,  # frozen
        entry_price_as_of=close.as_of,  # frozen
        thesis=thesis,
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
