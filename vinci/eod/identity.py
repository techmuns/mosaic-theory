"""WHOSE BAR IS IT — the two identity repairs the price store needs (2026-10-28, wave 2 L7's
measured defects, `docs/records/2026-10-27-price-flags-checked-against-tiingo.md`).

1. A REUSED TICKER. Grouped-daily bars are filed under whichever id holds a ticker TODAY
   (`ingest_prices`), so a store backfilled across a reuse holds the former holder's bars under
   the current one's id: ten hole-steps on the 2026-10-28 scorecard, each another security's
   series on Tiingo's side of the hole. Proven on Polygon's dated record (`detect_reuse`), the
   bars before the current holder's first session are re-filed under the former filer's own id
   (`Store.refile_bars`), and the committed tenure table keeps every later ingest from filing
   them back (`first_sessions`).
2. A RE-DOMICILE. A new filer under the same ticker is a new id with no history (XPRO, CLBK).
   Proven on the share-class FIGI or the new filer's 8-K12B (`detect_successions`), the pair joins
   #833's alias table and the new id is given the old one's history (`carry_forward`), tagged
   ``polygon-alias:<old id>``. The old id is never re-keyed.

Nothing here reads a forward return or touches the ledger: it decides which security a stored
bar belongs to, and only on a filer's or a reference record's own word.
"""
from __future__ import annotations

from array import array
from datetime import date
from pathlib import Path
from typing import Any

from vinci.eod.client import (
    GAP_SESSIONS,
    EodClient,
    carry_forward,
    market_sessions,
    missed_sessions,
)
from vinci.resolver.aliases import (
    Filings,
    ShareClassAlias,
    TickerTenure,
    detect_reuse,
    detect_successions,
    load_aliases,
    load_tenures,
    write_aliases,
    write_tenures,
)
from vinci.schemas.data_record import Identity


def series_holes(store: Any, ids: list[str]) -> dict[str, list[tuple[date, date]]]:
    """``{internal_id: [(last bar before, first bar after), ...]}`` for every step across more
    than `GAP_SESSIONS` market sessions, oldest first — THE SCORECARD'S OWN HOLE (series_gap), on
    its own market calendar, so what this repairs is what the scorecard flags."""
    per_day = store.bars_per_session()
    if not per_day or not ids:
        return {}
    market = market_sessions(per_day)
    out: dict[str, list[tuple[date, date]]] = {}
    for iid in ids:
        bars = store.bar_dates(iid)
        if len(bars) < 2:
            continue
        missed = missed_sessions(market, array("i", (d.toordinal() for d in bars)))
        found = [(bars[i - 1], bars[i]) for i in range(1, len(bars))
                 if missed[i - 1] > GAP_SESSIONS]
        if found:
            out[iid] = found
    return out


def reconcile(store: Any, eod: EodClient, filings: Filings, snapshots_dir: Path, *,
              lines: list[Identity], master: list[Identity], as_of: date) -> dict[str, Any]:
    """Run both repairs over ``lines`` (a population, or every security the store holds):
    detect and record, then re-file every recorded reuse's bars and carry every recorded
    succession's history to its successor among ``lines``. Idempotent: a known row costs no call,
    a re-filed or carried name moves nothing more. Returns what moved, name by name."""
    tenures = load_tenures(snapshots_dir)
    found_t = detect_reuse(lines, series_holes(store, [s.internal_id for s in lines]),
                           lambda t, on: eod.ticker_details(t, on), known=tenures)
    write_tenures(snapshots_dir, found_t)
    ids = {s.internal_id for s in lines}
    refiled: dict[str, int] = {}
    for t in tenures + found_t:
        if t.internal_id in ids and (n := store.refile_bars(t.internal_id, t.prior_id,
                                                            before=t.first_session)):
            refiled[t.internal_id] = refiled.get(t.internal_id, 0) + n

    def span(iid: str) -> tuple[date, date] | None:
        bars = store.bar_dates(iid)
        return (bars[0], bars[-1]) if bars else None

    aliases = load_aliases(snapshots_dir)
    found_a = detect_successions(lines, master, lambda t, on: eod.ticker_details(t, on), filings,
                                 span, as_of=as_of, known=aliases)
    write_aliases(snapshots_dir, found_a)
    carried = {a.successor_id: carry_forward(
                   eod, store, predecessor_id=a.predecessor_id,
                   predecessor_symbol=a.predecessor_symbol, successor_id=a.successor_id,
                   listed=a.listed, end=as_of)
               for a in aliases + found_a if a.successor_id in ids}
    return {"tenures": found_t, "refiled": refiled,
            "successions": found_a, "carried": {k: v for k, v in carried.items() if v}}


__all__ = ["ShareClassAlias", "TickerTenure", "reconcile", "series_holes"]
