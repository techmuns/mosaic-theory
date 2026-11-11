"""SHADOW PARITY: the fact layer against the reader it will replace, on every committed page.

For each page, the EDGAR facts its mechanical layer reads are
``facts_as_of(edgar.companyfacts(cik), page_price_date(...))`` (:class:`vinci.edgar.asof.AsOfEdgar`
hands every reader exactly that blob). This module computes the same blob from the same cached
response and compares it with what the fact store returns at the same as-of, three ways:

1. ROWS — every row of every taxonomy, tag and unit, every field, in order
   (:meth:`FactStore.companyfacts_as_of`).
2. LATEST — for every (taxonomy, tag, unit, period) the cut holds, the latest filing by the cut,
   computed here in plain Python from the cut blob, against the store's SQL
   (:meth:`FactStore.latest`).
   A key whose latest day states two values must be ambiguous on BOTH sides.
3. GET — a deterministic sample of those keys through :meth:`FactStore.get`, the public call, and
   the sample is labelled a sample.

It also counts the rows filed AFTER the cut, so a page whose cut excludes nothing (and so proves
nothing about the cut) is visible as such; and the keys whose cut holds two or more DIFFERENT values
across filings (restatements), so the latest-filing-wins rule is shown exercised, not assumed.
``at`` replays a page at another as-of than its own price date, for the same reason.

IT COMPARES THE RESPONSE THE SNAPSHOT INGESTED, OR SAYS IT CANNOT (TeamNostra fix request 2,
RFL-D7). The cache is read as it is now. A copy refetched since the ingest is another response:
compared as the same one, its new filings showed as hundreds of row "differences" in the store,
under the new copy's fetch time. A page whose cached response is not the one the snapshot
ingested (by sha256) is reported CHANGED, with both copies' fetch times, and compared no further,
as the screen replay already does.

AN EXACT DUPLICATE THE INGEST HOLDS ONCE IS NAMED, NOT A DIFFERENCE (RFL-D8). The ingest stores an
identical row once and counts the drop; `facts_as_of` keeps both, so every cut after it showed an
unexplained row difference. Later exact duplicates are dropped from the reference as the ingest
drops them, and counted beside the snapshot's own count.

THE CUT IS THE PAGE'S: BY DAY. The page's reader still cuts on ``filed`` (``facts_as_of``), so the
store is read with ``basis="filed"`` and ``stale_ok=True``: both sides read the same copy, and a
cut past its fetch is shown in its own column, never refused here.

NOTHING IS SWITCHED. No page or screen reader reads the store in this slice. A mismatch here is a
finding to report, never something to tune away.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, NamedTuple

from vinci.edgar.concepts import facts_as_of
from vinci.facts.edgar_ingest import NotInCacheError, read_cached_companyfacts
from vinci.facts.reader import (
    FILED,
    FactAmbiguousError,
    FactNotHeldError,
    FactStore,
    FactUnknownError,
    Period,
    is_periodic,
)
from vinci.facts.store import FactsStoreError

#: How many keys per page go through the public `get()` (the rest are compared in bulk).
GET_SAMPLE = 200
#: How many discrepancy lines a page keeps; the count of all of them is kept beside them.
EXAMPLES_SHOWN = 5

RefKey = tuple[str, str, str, str | None, str]       # taxonomy, tag, unit, start, end


def page_cut(doc: dict[str, Any]) -> date:
    """The page's price date, read exactly as the assembly reads it."""
    from vinci.dossier.anchor import price_as_of
    from vinci.edgar.asof import page_price_date
    return page_price_date(price_as_of(doc.get("mechanical") or {}),
                           date.fromisoformat(str(doc["reference_date"])))


def _tree(blob: dict[str, Any]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for ns, tags in (blob.get("facts") or {}).items():
        for tag, body in (tags or {}).items():
            for unit, rows in (body.get("units") or {}).items():
                out[(ns, tag, unit)] = list(rows)
    return out


def _row_key(r: dict[str, Any]) -> str:
    return json.dumps(r, sort_keys=True)


def held_once(blob: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """``blob`` with every LATER exact duplicate of a row under its taxonomy, tag and unit
    removed, as the ingest stores it (`edgar_ingest.rows_from_companyfacts` keeps the first), and
    how many were removed."""
    dropped = 0
    nsmap: dict[str, Any] = {}
    for ns, tags in (blob.get("facts") or {}).items():
        for tag, body in (tags or {}).items():
            units: dict[str, list[dict[str, Any]]] = {}
            for unit, rows in (body.get("units") or {}).items():
                seen: set[str] = set()
                kept = []
                for r in rows:
                    k = _row_key(r)
                    if k in seen:
                        dropped += 1
                        continue
                    seen.add(k)
                    kept.append(r)
                units[unit] = kept
            nsmap.setdefault(ns, {})[tag] = {**body, "units": units}
    return {**blob, "facts": nsmap}, dropped


class RefLatest(NamedTuple):
    kind: str                     # 'value' or 'ambiguous'
    value: Any                    # the value, or the sorted values that disagree
    filed: str
    accessions: frozenset[str]    # every filing on the latest day
    primary: str                  # the one the store must NAME: a periodic report's, then greatest


def filing_eve(blob: dict[str, Any], cut: date) -> date | None:
    """The day before the last day anything in ``blob`` was filed on or before ``cut``. A store that
    reads one day late passes every cut that falls between filings; this is the cut that sees it
    (review round 2 of #896: an off-by-one was flagged on 0 of 104 cuts, and on 26 of 26 eves)."""
    days = [r["filed"] for rows in _tree(blob).values() for r in rows
            if r.get("filed") and r["filed"] <= cut.isoformat()]
    return date.fromisoformat(max(days)) - timedelta(days=1) if days else None


def reference_latest(cut_blob: dict[str, Any]) -> dict[RefKey, RefLatest]:
    """Per key, the latest filing day's reading, computed here in plain Python: one value or the
    values that disagree, every accession that day, and the PRIMARY the store must name (a
    periodic report over a proxy, then the greatest accession)."""
    groups: dict[RefKey, list[dict[str, Any]]] = {}
    for (ns, tag, unit), rows in _tree(cut_blob).items():
        for r in rows:
            groups.setdefault((ns, tag, unit, r.get("start"), r["end"]), []).append(r)
    out: dict[RefKey, RefLatest] = {}
    for key, rows in groups.items():
        latest = max(r["filed"] for r in rows)
        top = [r for r in rows if r["filed"] == latest]
        values = {float(r["val"]) for r in top}
        accns = frozenset(r["accn"] for r in top)
        periodic = [r["accn"] for r in top if is_periodic(r.get("form"))]
        primary = max(periodic) if periodic else max(accns)
        if len(values) > 1:
            out[key] = RefLatest("ambiguous", tuple(sorted(values)), latest, accns, primary)
        else:
            out[key] = RefLatest("value", values.pop(), latest, accns, primary)
    return out


class RowsCompared(NamedTuple):
    row_diffs: int        # rows in one blob and not the other, every field compared, as multisets
    order_diffs: int      # (taxonomy, tag, unit) lists holding the same rows in another order
    rows_compared: int    # rows in the reference
    store_rows: int       # rows in the candidate


def compare_rows(reference: dict[str, Any], candidate: dict[str, Any], examples: list[str]
                 ) -> RowsCompared:
    """Every row of two companyfacts-shaped blobs, every field, as a multiset per (taxonomy, tag,
    unit), then in order. Appends up to :data:`EXAMPLES_SHOWN` lines to ``examples``."""
    ref_tree, cand_tree = _tree(reference), _tree(candidate)
    row_diffs = order_diffs = 0
    for k in sorted(set(ref_tree) | set(cand_tree)):
        a, b = ref_tree.get(k, []), cand_tree.get(k, [])
        ca, cb = Counter(map(_row_key, a)), Counter(map(_row_key, b))
        if ca != cb:
            n = sum(((ca - cb) + (cb - ca)).values())
            row_diffs += n
            if len(examples) < EXAMPLES_SHOWN:
                examples.append(f"rows {k}: {n} differ")
        elif a != b:
            order_diffs += 1
            if len(examples) < EXAMPLES_SHOWN:
                examples.append(f"order {k}")
    # THE ORDER OF THE LISTS THEMSELVES: a reader takes the FIRST namespace or unit present
    # (`points_for_tag`), so two blobs holding the same lists in another order read differently
    if not row_diffs and list(ref_tree) != list(cand_tree):
        order_diffs += 1
        if len(examples) < EXAMPLES_SHOWN:
            examples.append("order of the (taxonomy, tag, unit) lists")
    return RowsCompared(row_diffs, order_diffs, sum(len(v) for v in ref_tree.values()),
                        sum(len(v) for v in cand_tree.values()))


@dataclass
class PageParity:
    ticker: str
    entity: str
    cut: str
    fetched_at: str
    rows_in_response: int
    rows_after_cut: int
    rows_compared: int
    store_rows: int
    row_diffs: int
    order_diffs: int
    keys_compared: int
    key_diffs: int
    keys_restated: int
    ambiguous_keys: int
    get_sampled: int
    get_diffs: int
    #: the first EXAMPLES_SHOWN discrepancies; `discrepancies` is how many there were in all
    examples: list[str]
    discrepancies: int = 0
    #: why this page could not be compared at all (its response is not cached, or its entity is
    #: not in the snapshot); such a page is never zero-diff
    unread: str | None = None
    #: the cache holds another response than the snapshot ingested (RFL-D7): never zero-diff
    changed: str | None = None
    #: later exact duplicates in the cut, which the ingest stores once (RFL-D8), and how many the
    #: snapshot says it dropped from the whole response
    duplicates_held_once: int = 0
    duplicates_dropped_by_ingest: int = 0
    #: the cut is past the moment the snapshot's copy was fetched (RFL-D1)
    past_fetch: bool = False

    @property
    def zero_diff(self) -> bool:
        return (self.unread is None and self.changed is None and self.row_diffs == 0
                and self.order_diffs == 0 and self.key_diffs == 0
                and self.get_diffs == 0 and self.rows_compared == self.store_rows
                and self.duplicates_held_once <= self.duplicates_dropped_by_ingest)


def compare_page(ticker: str, doc: dict[str, Any], store: FactStore, cache_dir: Path, *,
                 at: date | None = None, eve: bool = False,
                 originals: Path | None = None) -> PageParity:
    """``doc``'s page at its own price date, or at ``at`` when given; with ``eve``, at the eve of
    the last filing day on or before that date (:func:`filing_eve`). The reference is the
    snapshot's own ORIGINAL of the response where it kept one (from ``originals``, default the
    local originals root, or R2 for an ``r2://`` store), else the cache's copy."""
    entity = f"{int(doc['cik']):010d}"
    cut = at if at is not None else page_cut(doc)

    def unreadable(why: str, *, changed: bool = False, fetched: str = "") -> PageParity:
        # REPORTED, NOT RAISED: one page that cannot be read must not hide every other page's
        # result, and it is never counted as a zero diff
        return PageParity(ticker=ticker, entity=entity, cut=cut.isoformat(), fetched_at=fetched,
                          rows_in_response=0, rows_after_cut=0, rows_compared=0, store_rows=0,
                          row_diffs=0, order_diffs=0, keys_compared=0, key_diffs=0,
                          keys_restated=0, ambiguous_keys=0, get_sampled=0, get_diffs=0,
                          examples=[], unread=None if changed else why,
                          changed=why if changed else None)

    ingested = next((e for e in store.manifest["entities"] if e["entity"] == entity), None)
    try:
        if ingested is None:
            raise FactNotHeldError(f"{entity}: not in snapshot {store.snapshot_id} — it was not "
                                   "ingested")
        if "original" in ingested:
            # THE ORIGINAL, NOT THE CACHE (RFL-D3): the response the snapshot read, kept
            # write-once, so a refetched cache no longer stops the comparison
            blob = store.original(entity, originals=originals)
        else:
            resp = read_cached_companyfacts(entity, cache_dir)
            if not ingested.get("response_sha256"):
                return unreadable(f"snapshot {store.snapshot_id} states no response hash for "
                                  f"{entity}, so the cached response cannot be shown to be the "
                                  "one it ingested")
            if resp.sha256 != ingested["response_sha256"]:
                return unreadable(
                    f"the SEC cache now holds another response than snapshot "
                    f"{store.snapshot_id} ingested: the snapshot's copy was fetched "
                    f"{ingested['fetched_at']} (sha256 {ingested['response_sha256'][:12]}…), the "
                    f"cache's {resp.fetched_at:%Y-%m-%dT%H:%M:%SZ} (sha256 {resp.sha256[:12]}…); "
                    "re-ingest to compare", changed=True, fetched=str(ingested["fetched_at"]))
            blob = json.loads(resp.text)
        if eve:
            day = filing_eve(blob, cut)
            if day is None:
                raise FactUnknownError(f"nothing filed by {cut}: no filing eve")
            cut = day
        reference, dupes = held_once(facts_as_of(blob, cut))
        candidate = store.companyfacts_as_of(entity, cut, basis=FILED, stale_ok=True)
    except (NotInCacheError, FactUnknownError, FactNotHeldError, FactsStoreError) as exc:
        return unreadable(str(exc))
    examples: list[str] = []

    # 1. ROWS — every field of every row, as a multiset per (taxonomy, tag, unit), then in order
    row_diffs, order_diffs, rows_compared, store_rows = compare_rows(reference, candidate,
                                                                    examples)
    ref_tree = _tree(reference)
    rows_in_response = sum(len(v) for v in _tree(blob).values())

    # 2. LATEST — plain Python on the cut blob against the store's SQL
    ref = reference_latest(reference)
    got = store.latest(entity, cut, basis=FILED, stale_ok=True)
    got_by_key: dict[RefKey, Any] = {
        (k[1], k[2], k[3], k[4].isoformat() if k[4] else None, k[5].isoformat()): v
        for k, v in got.items()}
    key_diffs = 0
    for rk in sorted(set(ref) | set(got_by_key), key=str):
        want, have = ref.get(rk), got_by_key.get(rk)
        ok: bool
        if want is None or have is None:
            ok = False
        elif want.kind == "ambiguous":
            ok = isinstance(have, FactAmbiguousError)
        else:
            ok = (not isinstance(have, FactAmbiguousError) and have.value == want.value
                  and have.filed_date.isoformat() == want.filed
                  and frozenset({have.accession, *have.concurrent_accessions}) == want.accessions
                  and have.accession == want.primary)
        if not ok:
            key_diffs += 1
            if len(examples) < EXAMPLES_SHOWN:
                examples.append(f"latest {rk}: reference {want!r}, store {have!r}")
    ambiguous_keys = sum(1 for v in ref.values() if v.kind == "ambiguous")
    stated: dict[RefKey, set[float]] = {}
    for (ns, tag, unit), rows in ref_tree.items():
        for r in rows:
            stated.setdefault((ns, tag, unit, r.get("start"), r["end"]), set()).add(float(r["val"]))
    keys_restated = sum(1 for vals in stated.values() if len(vals) > 1)

    # 3. GET — the public call, on a deterministic sample (every n-th key in sorted order)
    keys = sorted(ref, key=str)
    step = max(1, len(keys) // GET_SAMPLE)
    sample = keys[::step][:GET_SAMPLE]
    get_diffs = 0
    for sk in sample:
        ns, tag, unit, start, end = sk
        period = Period(end=date.fromisoformat(end),
                        start=date.fromisoformat(start) if start else None)
        want = ref[sk]
        try:
            fact = store.get(entity, f"{ns}:{tag}", period, cut, unit=unit, basis=FILED,
                             stale_ok=True)
            ok = (want.kind == "value" and fact.value == want.value
                  and fact.filed_date.isoformat() == want.filed
                  and fact.snapshot_id == store.snapshot_id
                  and fact.source_ref.accession == want.primary)
        except FactAmbiguousError:
            ok = want.kind == "ambiguous"
        except FactUnknownError:
            ok = False
        if not ok:
            get_diffs += 1
            if len(examples) < EXAMPLES_SHOWN:
                examples.append(f"get {sk}")

    return PageParity(
        ticker=ticker, entity=entity, cut=cut.isoformat(),
        fetched_at=str(ingested["fetched_at"]),
        rows_in_response=rows_in_response, rows_after_cut=rows_in_response - rows_compared - dupes,
        rows_compared=rows_compared, store_rows=store_rows, row_diffs=row_diffs,
        order_diffs=order_diffs, keys_compared=len(set(ref) | set(got_by_key)),
        key_diffs=key_diffs, keys_restated=keys_restated, ambiguous_keys=ambiguous_keys,
        get_sampled=len(sample), get_diffs=get_diffs, examples=examples,
        discrepancies=row_diffs + order_diffs + key_diffs + get_diffs,
        duplicates_held_once=dupes,
        duplicates_dropped_by_ingest=int(ingested.get("exact_duplicates_dropped", 0)),
        past_fetch=store.is_stale(entity, cut, basis=FILED))


def as_json(results: list[PageParity]) -> str:
    return json.dumps([asdict(r) for r in results], indent=2)
