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

EVERY FILING'S ACCEPTANCE TIME, FROM THE SAME CACHE (schema v3, TeamNostra fix request 2,
RFL-D2). companyfacts dates a filing only to the day; SEC's submissions documents (the recent page
and the older pages it lists) carry each filing's ``acceptanceDateTime``. :func:`acceptance_rows`
reads them from the cache, never fetched, and writes one row per accession the entity's data rows
carry: the reader's cut stands on it. The clock is UTC, as written: read so, 3,749 of 3,760
periodic and 8-K filings of the committed pages' companies obey SEC's 17:30 New York filing-date
rule (read as New York time, 1,374), the rest at the 17:30 boundary or carrying a filing date SEC
later moved. An accession no read document lists, a page the cache does not hold, and a filing
whose SEC filing date is not the data rows' ``filed`` are stated as such and given no time.

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
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.edgar.client import _COMPANYFACTS, _SUBMISSIONS, _SUBMISSIONS_PAGE
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
        present = http._cache_path(url).exists()
    if text is None or fetched is None:
        # A COPY THAT IS THERE BUT CANNOT BE READ IS NOT ABSENT (round 2 of #904): CachedHttp
        # reads a corrupt entry as a miss, which the fact layer would have recorded as "not cached"
        raise NotInCacheError(f"unreadable SEC cache entry: {url}" if present
                              else f"not in the SEC cache: {url}")
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


def submissions_url(cik: int | str) -> str:
    return _SUBMISSIONS.format(cik=pad_cik(cik))


@dataclass(frozen=True)
class Acceptance:
    """One entity's filings rows (``vinci.facts.schema.FILING_COLUMNS``) and what was read for
    them: each submissions document, and every accession of the data rows given no time, why."""

    rows: list[dict[str, Any]]
    #: each document read: url, fetched_at, response_sha256, the filings it lists
    documents: list[dict[str, Any]]
    #: documents listed by the recent page and not in the cache: url -> why
    unread: dict[str, str]
    accessions: int                   # distinct accessions the data rows carry
    #: accession -> why it has no time (listed by no document read; dates disagree)
    unstated: dict[str, str]

    def summary(self) -> dict[str, Any]:
        """The manifest's ``acceptance`` entry: every count, with the reason for each gap."""
        return {"documents": self.documents, "documents_unread": self.unread,
                "accessions": self.accessions, "stated": len(self.rows),
                "unstated": len(self.unstated),
                **({"unstated_named": self.unstated} if self.unstated else {})}


_ACCEPTED_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _accepted_at(raw: Any, *, where: str) -> datetime:
    """``acceptanceDateTime`` (``2025-02-20T21:05:12.000Z``) as a naive UTC datetime."""
    if not isinstance(raw, str):
        raise IngestShapeError(f"{where}: acceptanceDateTime {raw!r} is not a string")
    try:
        return datetime.strptime(raw, _ACCEPTED_FORMAT)
    except ValueError as exc:
        raise IngestShapeError(f"{where}: acceptanceDateTime {raw!r} is not "
                               f"{_ACCEPTED_FORMAT}") from exc


def _listed(page: Any, *, where: str) -> list[tuple[str, str, str | None, str]]:
    """(accession, filingDate, form, acceptanceDateTime) for every filing one page lists."""
    if not isinstance(page, dict):
        raise IngestShapeError(f"{where}: not an object")
    cols = ("accessionNumber", "filingDate", "form", "acceptanceDateTime")
    missing = [c for c in cols if not isinstance(page.get(c), list)]
    if missing:
        raise IngestShapeError(f"{where}: no {missing} list")
    lens = {len(page[c]) for c in cols}
    if len(lens) != 1:
        raise IngestShapeError(f"{where}: its lists are of different lengths {sorted(lens)}")
    return list(zip(*(page[c] for c in cols), strict=True))


def acceptance_rows(entity: str, data_rows: list[dict[str, Any]], cache_dir: Path, *,
                    keep_original: Callable[[CachedResponse], dict[str, Any]] | None = None
                    ) -> Acceptance:
    """Each accession ``data_rows`` carry, with SEC's acceptance time from the CACHED submissions
    documents. Never fetched: a document not cached leaves its filings with no time, stated."""
    filed: dict[str, set[date]] = {}
    for r in data_rows:
        filed.setdefault(r["accession"], set()).add(r["filed_date"])
    documents: list[dict[str, Any]] = []
    unread: dict[str, str] = {}
    listed: dict[str, tuple[date, str | None, datetime]] = {}

    def read(url: str, page: Any) -> None:
        listing = _listed(page, where=url)
        for accn, fdate, form, at in listing:
            if not isinstance(accn, str) or (form is not None and not isinstance(form, str)):
                raise IngestShapeError(f"{url}: accession {accn!r} / form {form!r} not strings")
            # ONLY THE FILINGS THE DATA ROWS CARRY are read strictly (review round 0): one odd
            # time on a Form 4 the store never reads must not stop every company's ingest
            if accn in filed and accn not in listed:
                listed[accn] = (_date(fdate, where=f"{url} {accn}"), form,
                                _accepted_at(at, where=f"{url} {accn}"))
        documents[-1]["filings"] = len(listing)

    def doc(url: str) -> Any:
        resp = read_cached(url, cache_dir)
        body = json.loads(resp.text)
        documents.append({"url": url, "fetched_at": resp.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "response_sha256": resp.sha256,
                          # the document itself, kept write-once (RFL-D3), when the writer keeps it
                          **({"original": keep_original(resp)} if keep_original else {})})
        return body

    main_url = submissions_url(entity)
    try:
        main = doc(main_url)
    except NotInCacheError as exc:
        unread[main_url] = str(exc)
        main = None
    if main is not None:
        filings = main.get("filings") if isinstance(main, dict) else None
        if not isinstance(filings, dict) or not isinstance(filings.get("files", []), list):
            raise IngestShapeError(f"{main_url}: no 'filings' object with a 'files' list")
        read(main_url, filings.get("recent"))
        for f in filings.get("files", []):
            name = f.get("name") if isinstance(f, dict) else None
            if not isinstance(name, str) or "/" in name:
                raise IngestShapeError(f"{main_url}: an older page named {name!r}")
            url = _SUBMISSIONS_PAGE.format(name=name)
            try:
                page = doc(url)
            except NotInCacheError as exc:
                unread[url] = str(exc)
                continue
            read(url, page)
    rows: list[dict[str, Any]] = []
    unstated: dict[str, str] = {}
    for accn in sorted(filed):
        hit = listed.get(accn)
        if hit is None:
            unstated[accn] = ("listed by no submissions document read" if documents
                              else "no submissions document in the SEC cache")
            continue
        fdate, form, at = hit
        if filed[accn] != {fdate}:
            unstated[accn] = (f"SEC's filing date {fdate} is not the data rows' "
                              f"{', '.join(sorted(d.isoformat() for d in filed[accn]))}")
            continue
        rows.append({"entity": entity, "accession": accn, "form": form, "filing_date": fdate,
                     "accepted_at": at})
    return Acceptance(rows=rows, documents=documents, unread=unread, accessions=len(filed),
                      unstated=unstated)


def unread_reason(facts: Any, got: IngestResult) -> str:
    """Why a parsed response yields no row to store, as the response shows it (RFL-D10): a
    response with no ``facts`` key is not "no row with a filed date"."""
    if not isinstance(facts, dict) or "facts" not in facts:
        keys = sorted(facts) if isinstance(facts, dict) else type(facts).__name__
        return f"the cached response has no 'facts' key (its keys: {keys}): not companyfacts"
    if got.rows_in_response == 0:
        return "the cached response's 'facts' holds no fact row"
    return (f"the cached response's {got.rows_in_response:,} fact rows all lack a filed date, "
            "so none can be dated")


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
    if not isinstance(facts, dict) or "cik" not in facts:
        raise IngestShapeError("companyfacts response carries no cik")
    if "facts" in facts and not isinstance(facts["facts"], dict):
        raise IngestShapeError(f"companyfacts 'facts' is a {type(facts['facts']).__name__}, "
                               "not an object")
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
