"""The fact layer: every extracted fact, persisted point-in-time, read through one API.

It holds EDGAR companyfacts (ADR: ``docs/records/2026-11-04-fact-layer-adr.md``). A snapshot is a
set of immutable Parquet objects, each named by a hash of its rows, listed by a committed JSON
manifest; DuckDB reads them in memory; "as of a date" is ``filed_date <= :as_of``. Two snapshots
are current: ``pages`` (the committed pages' companies, objects in git) and ``screen`` (the
screen's universe, objects on the machine that ingested it). Both are uploaded to R2, and any
reader given ``root="r2://"`` reads them from there (:mod:`vinci.facts.remote`).

    from vinci.facts import open_store, Period
    with open_store() as store:                       # the snapshot data/facts/current.json names
        f = store.get(1065280, "us-gaap:EarningsPerShareDiluted",
                      Period.duration(date(2023, 1, 1), date(2023, 12, 31)), date(2025, 6, 30))
        f.value, f.source_ref, f.filed_date, f.snapshot_id

NOTHING READS THIS YET. The page and the screen keep their own EDGAR paths; the store only
shadows them (``python -m vinci.facts parity``, ``python -m vinci.facts screen-replay``).
Each reader moves later, one at a time, behind a zero-diff replay.
"""
from __future__ import annotations

from pathlib import Path

from vinci.facts.reader import (
    Fact,
    FactAmbiguousError,
    FactsStoreNotPresentError,
    FactStore,
    FactUnknownError,
    FrameResult,
    Period,
    SourceRef,
)
from vinci.facts.store import DEFAULT_NAME, FactsStoreError, RemoteStoreNotConfiguredError


def open_store(snapshot_id: str | None = None, *, source: str = "edgar",
               name: str = DEFAULT_NAME, facts_base: Path | None = None,
               root: str | Path | None = None, verify: bool = True) -> FactStore:
    """Open a snapshot for reading: ``snapshot_id``, else the one ``current.json`` names for
    (``source``, ``name``)."""
    return FactStore(snapshot_id, source=source, name=name, facts_base=facts_base, root=root,
                     verify=verify)


__all__ = [
    "Fact",
    "FactAmbiguousError",
    "FactStore",
    "FactUnknownError",
    "FactsStoreError",
    "FactsStoreNotPresentError",
    "FrameResult",
    "Period",
    "RemoteStoreNotConfiguredError",
    "SourceRef",
    "open_store",
]
