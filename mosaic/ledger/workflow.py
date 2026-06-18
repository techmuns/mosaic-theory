"""Decision-ledger entry workflow — record one paper verdict per judged candidate.

The discriminator judgment is **manual** (the PM's A/B/C + CIQ process); this code only *records* it
and does the one mechanical thing that must not be left to memory: **freeze the entry price/as_of**
at decision time, so scoring measures forward return from a fixed anchor. Both **BUY** and
**AVOID-terminal** verdicts are logged — they are the two legs of the BUY−AVOID spread.

The ledger is append-only: re-logging a candidate fails loud (a verdict is never overwritten).
"""

from __future__ import annotations

from datetime import date, datetime

from mosaic.schemas.ledger import Confidence, LedgerEntry, Verdict
from mosaic.store import Store


class LedgerError(RuntimeError):
    """The verdict cannot be recorded (unknown candidate, or no price to anchor the entry)."""


def log_verdict(
    store: Store,
    *,
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
) -> LedgerEntry:
    """Freeze the entry price and append a verdict for ``candidate_id``; returns the entry."""
    cand = store.get_candidate(candidate_id)
    if cand is None:
        raise LedgerError(f"no candidate {candidate_id!r} in the store (run the screen first)")
    ident = cand.data_record.identity

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

    entry = LedgerEntry(
        entry_id=f"V-{candidate_id}",  # one verdict per candidate; re-log → append-only conflict
        candidate_id=candidate_id,
        internal_id=ident.internal_id,
        ticker=ident.ticker,
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
    )
    store.append_ledger(entry)
    return entry
