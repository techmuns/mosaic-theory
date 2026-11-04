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

NOTHING IS SWITCHED. No page or screen reader reads the store in this slice. A mismatch here is a
finding to report, never something to tune away.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from vinci.edgar.concepts import facts_as_of
from vinci.facts.edgar_ingest import read_cached_companyfacts
from vinci.facts.reader import FactAmbiguousError, FactStore, FactUnknownError, Period

#: How many keys per page go through the public `get()` (the rest are compared in bulk).
GET_SAMPLE = 200

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


RefLatest = tuple[str, Any, str, frozenset[str]]    # kind, value(s), filed, accessions


def reference_latest(cut_blob: dict[str, Any]) -> dict[RefKey, RefLatest]:
    """Per key: ('value', val, filed, accessions) or ('ambiguous', values, filed, accessions)."""
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
        if len(values) > 1:
            out[key] = ("ambiguous", tuple(sorted(values)), latest, accns)
        else:
            out[key] = ("value", values.pop(), latest, accns)
    return out


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
    examples: list[str]

    @property
    def zero_diff(self) -> bool:
        return (self.row_diffs == 0 and self.order_diffs == 0 and self.key_diffs == 0
                and self.get_diffs == 0 and self.rows_compared == self.store_rows)


def compare_page(ticker: str, doc: dict[str, Any], store: FactStore, cache_dir: Path, *,
                 at: date | None = None) -> PageParity:
    """``doc``'s page at its own price date, or at ``at`` when given."""
    entity = f"{int(doc['cik']):010d}"
    cut = at if at is not None else page_cut(doc)
    resp = read_cached_companyfacts(entity, cache_dir)
    blob = json.loads(resp.text)
    reference = facts_as_of(blob, cut)
    candidate = store.companyfacts_as_of(entity, cut)
    examples: list[str] = []

    # 1. ROWS — every field of every row, as a multiset per (taxonomy, tag, unit), then in order
    ref_tree, cand_tree = _tree(reference), _tree(candidate)
    row_diffs = order_diffs = 0
    for k in sorted(set(ref_tree) | set(cand_tree)):
        a, b = ref_tree.get(k, []), cand_tree.get(k, [])
        ca, cb = Counter(map(_row_key, a)), Counter(map(_row_key, b))
        if ca != cb:
            n = sum(((ca - cb) + (cb - ca)).values())
            row_diffs += n
            if len(examples) < 5:
                examples.append(f"rows {k}: {n} differ")
        elif a != b:
            order_diffs += 1
            if len(examples) < 5:
                examples.append(f"order {k}")
    rows_compared = sum(len(v) for v in ref_tree.values())
    store_rows = sum(len(v) for v in cand_tree.values())
    rows_in_response = sum(len(v) for v in _tree(blob).values())

    # 2. LATEST — plain Python on the cut blob against the store's SQL
    ref = reference_latest(reference)
    got = store.latest(entity, cut)
    got_by_key: dict[RefKey, Any] = {
        (k[1], k[2], k[3], k[4].isoformat() if k[4] else None, k[5].isoformat()): v
        for k, v in got.items()}
    key_diffs = 0
    for rk in sorted(set(ref) | set(got_by_key), key=str):
        want, have = ref.get(rk), got_by_key.get(rk)
        ok: bool
        if want is None or have is None:
            ok = False
        elif want[0] == "ambiguous":
            ok = isinstance(have, FactAmbiguousError)
        else:
            ok = (not isinstance(have, FactAmbiguousError) and have.value == want[1]
                  and have.filed_date.isoformat() == want[2]
                  and frozenset({have.accession, *have.concurrent_accessions}) == want[3])
        if not ok:
            key_diffs += 1
            if len(examples) < 5:
                examples.append(f"latest {rk}: reference {want!r}, store {have!r}")
    ambiguous_keys = sum(1 for v in ref.values() if v[0] == "ambiguous")
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
            fact = store.get(entity, f"{ns}:{tag}", period, cut, unit=unit)
            ok = (want[0] == "value" and fact.value == want[1]
                  and fact.filed_date.isoformat() == want[2]
                  and fact.snapshot_id == store.snapshot_id
                  and fact.source_ref.accession in want[3])
        except FactAmbiguousError:
            ok = want[0] == "ambiguous"
        except FactUnknownError:
            ok = False
        if not ok:
            get_diffs += 1
            if len(examples) < 5:
                examples.append(f"get {sk}")

    return PageParity(
        ticker=ticker, entity=entity, cut=cut.isoformat(),
        fetched_at=resp.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        rows_in_response=rows_in_response, rows_after_cut=rows_in_response - rows_compared,
        rows_compared=rows_compared, store_rows=store_rows, row_diffs=row_diffs,
        order_diffs=order_diffs, keys_compared=len(set(ref) | set(got_by_key)),
        key_diffs=key_diffs, keys_restated=keys_restated, ambiguous_keys=ambiguous_keys,
        get_sampled=len(sample), get_diffs=get_diffs, examples=examples)


def as_json(results: list[PageParity]) -> str:
    return json.dumps([asdict(r) for r in results], indent=2)
