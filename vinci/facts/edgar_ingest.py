"""EDGAR ingest: companyfacts from the SEC CACHE into fact rows. The ONE writer for source 'edgar'.

CACHE-ONLY, BY CONSTRUCTION. This module never builds a request: it reads the on-disk copy that
:class:`vinci.netcache.CachedHttp` already holds, through that class's own key scheme (so the two
cannot disagree about where a URL lives), with no TTL. A CIK whose companyfacts is not cached
raises :class:`NotInCacheError`. It is never fetched here, so an ingest cannot spend SEC's rate
limit or depend on the network.

EVERY VERSION IS KEPT. Companyfacts lists a period once per filing that reported it: the original,
each later comparative, each restatement. All of them become rows, each with its own accession and
``filed_date``, because "as of" is a question about which of them existed on a day. Only an EXACT
duplicate (an identical row under the same taxonomy, tag and unit) is dropped, and the drop is
counted.

A ROW OF AN UNKNOWN SHAPE RAISES. A replay is only faithful if every key a row carries is stored,
so a key outside :data:`_ROW_KEYS`, a missing required key, or a value that is not a finite number
stops the ingest (:class:`IngestShapeError`) rather than storing part of a row. The one exception
is a row with no ``filed`` date: :func:`vinci.edgar.concepts.facts_as_of` drops such a row because
its knowable date cannot be shown, so it is dropped here too. It is still shape-checked first, and
it is NAMED (taxonomy, tag, unit, period, accession) in the result, and so in the manifest, not
only counted (review round 2 of #896).
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.edgar.client import _COMPANYFACTS
from vinci.netcache import CachedHttp

SOURCE = "edgar"
EXTRACTOR = "vinci.facts.edgar_ingest"
#: Bumped whenever the rows this module emits for the same response could change. "2" (slice 2a):
#: an integer above 2**53 that float64 holds exactly is stored, where "1" refused its response.
EXTRACTOR_VERSION = "2"

#: The SEC cache namespace `vinci.sec.build_sec_http` writes companyfacts under.
SEC_NAMESPACE = "sec"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

_REQUIRED_KEYS = frozenset({"end", "val", "accn", "fy", "fp", "form", "filed"})
_OPTIONAL_KEYS = frozenset({"start", "frame"})
_ROW_KEYS = _REQUIRED_KEYS | _OPTIONAL_KEYS


class NotInCacheError(LookupError):
    """The SEC cache holds no copy of this URL. It is never fetched by the fact layer."""


class IngestShapeError(ValueError):
    """A companyfacts row carries a shape this ingest cannot store faithfully."""


@dataclass(frozen=True)
class CachedResponse:
    url: str
    text: str
    fetched_at: datetime    # when CachedHttp fetched the copy (UTC), never when it was read back

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def pad_cik(cik: int | str) -> str:
    return f"{int(cik):010d}"


def companyfacts_url(cik: int | str) -> str:
    return _COMPANYFACTS.format(cik=pad_cik(cik))


def read_cached(url: str, cache_dir: Path) -> CachedResponse:
    """The cached copy of ``url`` under ``cache_dir`` (the dir holding ``sec/``). Never a fetch."""
    if not (cache_dir / SEC_NAMESPACE).is_dir():
        raise NotInCacheError(f"no SEC cache at {cache_dir / SEC_NAMESPACE}")
    with CachedHttp(cache_dir=cache_dir, user_agent="vinci-facts cache-only reader",
                    min_interval_sec=0.0, namespace=SEC_NAMESPACE) as http:
        text = http._read_cache(url, None)
        fetched = http.fetched_at(url)
    if text is None or fetched is None:
        raise NotInCacheError(f"not in the SEC cache: {url}")
    return CachedResponse(url=url, text=text, fetched_at=datetime.fromtimestamp(fetched, tz=UTC))


def read_cached_companyfacts(cik: int | str, cache_dir: Path) -> CachedResponse:
    return read_cached(companyfacts_url(cik), cache_dir)


def cik_for_ticker(ticker: str, cache_dir: Path) -> str:
    """A ticker's CIK from the CACHED ``company_tickers.json``. A ticker absent from it raises."""
    table = json.loads(read_cached(COMPANY_TICKERS_URL, cache_dir).text)
    hits = {pad_cik(v["cik_str"]) for v in table.values() if v.get("ticker") == ticker}
    if len(hits) != 1:
        raise NotInCacheError(f"{ticker}: {len(hits)} CIKs in the cached company_tickers.json")
    return hits.pop()


@dataclass(frozen=True)
class IngestResult:
    entity: str
    entity_name: str
    rows: list[dict[str, Any]]
    rows_in_response: int
    exact_duplicates_dropped: int
    rows_without_filed: int
    #: each row dropped for having no ``filed`` date, named so the manifest can show it
    rows_without_filed_named: list[dict[str, Any]]


def _date(raw: Any, *, where: str) -> date:
    if not isinstance(raw, str):
        raise IngestShapeError(f"{where}: date {raw!r} is not a string")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise IngestShapeError(f"{where}: {raw!r} is not an ISO date") from exc


def _value(raw: Any, *, where: str) -> float:
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise IngestShapeError(f"{where}: value {raw!r} is not a number")
    try:
        stored = float(raw)
    except OverflowError:
        raise IngestShapeError(f"{where}: integer {raw} does not survive float64 storage") from None
    # EXACT ROUND TRIP, NOT A SIZE LIMIT (slice 2a). "Above 2**53" refused EEFT's cover count of
    # 52752851000000000, which float64 holds exactly, and with it four of the screen's companies;
    # what cannot be stored is a value that comes back as another number.
    if isinstance(raw, int) and int(stored) != raw:
        raise IngestShapeError(f"{where}: integer {raw} does not survive float64 storage")
    if not math.isfinite(stored):
        raise IngestShapeError(f"{where}: value {raw!r} is not finite")
    return stored


def _walk(facts: dict[str, Any]) -> Iterator[tuple[str, str, str, dict[str, Any]]]:
    """(taxonomy, tag, unit, row) in the response's own order."""
    for taxonomy, tags in (facts.get("facts") or {}).items():
        for tag, body in (tags or {}).items():
            for unit, rows in (body.get("units") or {}).items():
                for row in rows:
                    yield taxonomy, tag, unit, row


def rows_from_companyfacts(facts: dict[str, Any]) -> IngestResult:
    """Every fact row in ``facts`` (a parsed companyfacts response), every filing's version kept."""
    if "cik" not in facts:
        raise IngestShapeError("companyfacts response carries no cik")
    entity = pad_cik(facts["cik"])
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    total = dupes = 0
    no_filed: list[dict[str, Any]] = []
    for position, (taxonomy, tag, unit, row) in enumerate(_walk(facts)):
        total += 1
        where = f"{entity} {taxonomy}:{tag} [{unit}] row {position}"
        if not isinstance(row, dict):
            raise IngestShapeError(f"{where}: not an object")
        has_filed = bool(row.get("filed"))
        unknown = set(row) - _ROW_KEYS
        missing = _REQUIRED_KEYS - set(row) - (set() if has_filed else {"filed"})
        if unknown or missing:
            raise IngestShapeError(
                f"{where}: unknown keys {sorted(unknown)}, missing {sorted(missing)}")
        fy = row["fy"]
        if fy is not None and (isinstance(fy, bool) or not isinstance(fy, int)):
            raise IngestShapeError(f"{where}: fy {fy!r} is not an integer")
        if not isinstance(row["accn"], str) or not row["accn"]:
            raise IngestShapeError(f"{where}: accn {row['accn']!r} is not a non-empty string")
        for k in ("fp", "form"):          # always present; null is a stated "none"
            if row[k] is not None and not isinstance(row[k], str):
                raise IngestShapeError(f"{where}: {k} {row[k]!r} is not a string")
        # present only when SEC assigned one: a present-but-null frame could not be replayed
        if "frame" in row and not isinstance(row["frame"], str):
            raise IngestShapeError(f"{where}: frame {row['frame']!r} is not a string")
        start = _date(row["start"], where=where) if "start" in row else None
        end = _date(row["end"], where=where)
        value = _value(row["val"], where=where)
        if not has_filed:
            # facts_as_of drops it too: its knowable date cannot be shown. Named, not just counted.
            no_filed.append({"taxonomy": taxonomy, "concept": tag, "unit": unit,
                             "start": row.get("start"), "end": row["end"], "accn": row["accn"]})
            continue
        key = (taxonomy, tag, unit, json.dumps(row, sort_keys=True))
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        out.append({
            "source": SOURCE,
            "entity": entity,
            "taxonomy": taxonomy,
            "concept": tag,
            "unit": unit,
            "period_start": start,
            "period_end": end,
            "value": value,
            "filed_date": _date(row["filed"], where=where),
            "accession": row["accn"],
            "form": row["form"],
            "fiscal_year": fy,
            "fiscal_period": row["fp"],
            "frame": row.get("frame"),
            "dimensions": None,
            "extractor": EXTRACTOR,
            "extractor_version": EXTRACTOR_VERSION,
            "status": "present",
            "reason": None,
            "source_position": position,
        })
    return IngestResult(entity=entity, entity_name=str(facts.get("entityName") or ""), rows=out,
                        rows_in_response=total, exact_duplicates_dropped=dupes,
                        rows_without_filed=len(no_filed), rows_without_filed_named=no_filed)
