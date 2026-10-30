"""Phase 2 C1 — reads that stopped short, or widened, and never said so.

E1-D11. `fulltext_search` read ONE 100-hit efts page and returned it as the answer (250 matches came
back as 100), and `mention_prefilter` stopped at its page cap with no word — 6 of the 984 batched
queries in the efts cache did, all `"defense"`, 530-774 hits read as 500 (2026-10-30).

The covenant-pointer table's two caps. It searched 6 agreement families and named 4 aggregate
lines, dropping the rest silently: the aggregate cap binds on 13 of the 26 committed pages measured
(LLY named 4 of its 52).

E1-D16. `latest_instant` fell back to the whole list when no point was an instant, so a list of
flows answered with a flow (WOR's revenue, as a balance).

Every fixture is real: WOR's committed companyfacts subset, committed pages' CIQ instruments, and
efts pages in the shape efts serves (`parse_fts_hit`'s `_source` fields)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import vinci.dossier.mechanical as mech
from vinci.dossier.mechanical import (
    _COVENANT_CLASS_RE,
    COVENANT_SEARCH_FOUND_NOTHING,
    _covenant_pointers,
)
from vinci.dossier.schemas import CapitalInstrument, SourceStatus
from vinci.edgar.client import EdgarClient, FtsHit, FtsResult
from vinci.edgar.concepts import extract_points, latest_instant
from vinci.netcache import CachedHttp
from vinci.themes.exposure import mention_prefilter

_ROOT = Path(__file__).resolve().parent.parent


# ─── E1-D16: an instant reader never answers with a flow ──────────────────────────────────────

def _wor() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(
        (_ROOT / "tests/fixtures/companyfacts/WOR.json").read_text()))


def test_latest_instant_of_flows_is_none() -> None:
    """WOR's revenue is a flow series: no instant to serve. It served the year to 2026-05-31."""
    revenue = extract_points(_wor(), "revenue")
    assert revenue and not any(p.is_instant for p in revenue)
    assert latest_instant(revenue) is None


def test_latest_instant_still_serves_a_balance() -> None:
    """The negative pin: a real balance-sheet series still answers, with its newest instant."""
    cash = latest_instant(extract_points(_wor(), "cash"))
    assert cash is not None and cash.is_instant
    assert cash.period_end == max(p.period_end for p in extract_points(_wor(), "cash")
                                  if p.is_instant)


# ─── E1-D11: a full-text search reads every page, or says it did not ──────────────────────────

def _hit(i: int) -> dict[str, Any]:
    return {"_id": f"0000000001-26-{i:06d}:ex10-1.htm", "_source": {
        "adsh": f"0000000001-26-{i:06d}", "ciks": ["0000000001"], "root_forms": ["8-K"],
        "file_type": "8-K", "file_date": "2026-01-05", "display_names": ["SUBJECT CO (SUBJ)"]}}


class _PagedEfts:
    """efts in miniature: ``total`` matches served 100 a page, the page chosen by ``from=``."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.urls: list[str] = []

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> dict[str, Any]:
        self.urls.append(url)
        start = int(url.split("&from=")[1].split("&")[0]) if "&from=" in url else 0
        n = max(0, min(100, self.total - start))
        return {"hits": {"total": {"value": self.total, "relation": "eq"},
                         "hits": [_hit(start + k) for k in range(n)]}}


def _client(efts: _PagedEfts) -> EdgarClient:
    return EdgarClient(http=cast(CachedHttp, efts), efts_http=cast(CachedHttp, efts))


def test_fulltext_search_reads_past_the_first_page() -> None:
    """250 matches are 250 hits from three requests — not 100 from one."""
    efts = _PagedEfts(250)
    got = _client(efts).fulltext_search("Credit Agreement", ciks="1")
    assert len(efts.urls) == 3
    assert len(got.hits) == 250 and got.total == 250 and not got.capped
    assert len({h.accession for h in got.hits}) == 250


def test_fulltext_search_says_when_it_stopped_short() -> None:
    efts = _PagedEfts(250)
    got = _client(efts).fulltext_search("Credit Agreement", ciks="1", max_pages=2)
    assert len(efts.urls) == 2
    assert got.capped and len(got.hits) == 200 and got.total == 250


def test_a_one_page_search_is_one_request_on_the_url_it_always_had() -> None:
    """The negative pin: a search that fits one page costs one request, on the URL (the cache key)
    it was always read from — no ``from=`` on it."""
    efts = _PagedEfts(17)
    got = _client(efts).fulltext_search("Credit Agreement", ciks="1")
    assert len(efts.urls) == 1 and "from=" not in efts.urls[0]
    assert len(got.hits) == 17 and not got.capped


def test_the_prefilter_names_a_query_its_page_cap_cut() -> None:
    """A batch×phrase whose matches outrun the cap is named with what it read of its total — the
    shape of the cached `"defense"` queries (530-774 hits, read as 500)."""
    efts = _PagedEfts(564)
    capped: list[str] = []
    mention_prefilter(cast(CachedHttp, efts), ["0000000001"], ("defense",),
                      startdt="2025-09-01", enddt="2026-06-30", capped=capped)
    assert len(efts.urls) == 5
    assert len(capped) == 1 and "read 500 of 564" in capped[0] and "'defense'" in capped[0]


def test_the_prefilter_names_nothing_it_read_whole() -> None:
    efts = _PagedEfts(120)
    capped: list[str] = []
    mention_prefilter(cast(CachedHttp, efts), ["0000000001"], ("defense",),
                      startdt="2025-09-01", enddt="2026-06-30", capped=capped)
    assert len(efts.urls) == 2 and capped == []


# ─── the covenant-pointer table states its own caps ──────────────────────────────────────────

def _instruments(ticker: str) -> list[CapitalInstrument]:
    page = json.loads((_ROOT / f"data/dossiers/{ticker}/dossier.json").read_text())
    return [CapitalInstrument.model_validate(i)
            for i in page["mechanical"]["capital_structure"]["instruments"]["value"]]


class _Edgar:
    """Every search finds one exhibit-bearing 8-K, so the table has a located row to keep."""

    def __init__(self, result: FtsResult | None = None) -> None:
        self.phrases: list[str] = []
        self.result = result

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ()) -> list[Any]:
        return []

    def fulltext_search(self, phrase: str, *, forms: str = "", ciks: str = "") -> FtsResult:
        self.phrases.append(phrase)
        if self.result is not None:
            return self.result
        n = len(self.phrases)
        return FtsResult(hits=[FtsHit(accession=f"0000000001-26-{n:06d}", cik="0000000001",
                                      form="8-K", file_date=date(2026, 1, 5),
                                      display_names=[])], total=1)


def _pointers(insts: list[CapitalInstrument], edgar: _Edgar, *,
              exhibits: tuple[str, ...] = ("ex10-1_agreement.htm",)) -> Any:
    with patch.object(mech, "_exhibit_names", lambda http, cik, acc: list(exhibits)):
        return _covenant_pointers(cast(EdgarClient, edgar), cast(CachedHttp, None),
                                  "0000000001", insts, date(2026, 10, 16))


def test_the_aggregate_line_cap_prints_itself() -> None:
    """LLY's committed panel holds 52 aggregate lines; the table names 4 and now says so."""
    out = _pointers(_instruments("LLY"), _Edgar())
    assert out.status is SourceStatus.PRESENT
    tail = [r for r in out.value if r.family == "48 more aggregate lines"]
    assert len(tail) == 1 and "showing 4 of 52 aggregate lines" in tail[0].note
    assert not tail[0].accession  # a statement, never a pointer


def test_a_panel_inside_the_cap_gets_no_truncation_row() -> None:
    """The negative pin: BRBR's committed panel holds 2 aggregate lines — nothing was cut."""
    out = _pointers(_instruments("BRBR"), _Edgar())
    assert not [r for r in out.value if "more aggregate" in r.family]


def _seven_agreement_families() -> list[CapitalInstrument]:
    """Seven agreement-class instruments, each a real committed instrument; no page has seven."""
    seen: dict[str, CapitalInstrument] = {}
    for t in ("AORT", "MVST", "WERN"):
        for i in _instruments(t):
            fam = i.description.split(" With ")[0].split(" - ")[0].strip()
            if _COVENANT_CLASS_RE.search(i.description) and fam not in seen:
                seen[fam] = i
    assert len(seen) >= 7, sorted(seen)
    return list(seen.values())[:7]


def test_the_query_cap_names_the_families_it_did_not_search() -> None:
    edgar = _Edgar()
    out = _pointers(_seven_agreement_families(), edgar)
    assert len(edgar.phrases) == 6
    tail = [r for r in out.value if r.family == "1 more agreement family"]
    assert len(tail) == 1 and "not searched" in tail[0].note and "6 of 7" in tail[0].note


def test_a_search_that_stopped_short_never_reports_found_nothing() -> None:
    """Nothing located in a CAPPED search is not "nothing across the filing history"."""
    hits = [FtsHit(accession=f"0000000001-26-{k:06d}", cik="0000000001", form="8-K",
                   file_date=date(2026, 1, 5), display_names=[]) for k in range(500)]
    out = _pointers(_instruments("BRBR"), _Edgar(FtsResult(hits=hits, total=640)), exhibits=())
    assert out.status is SourceStatus.UNKNOWN
    assert out.note != COVENANT_SEARCH_FOUND_NOTHING
    assert "stopped short" in (out.note or "") and "500 of 640" in (out.note or "")


def test_a_whole_search_that_found_nothing_still_says_so() -> None:
    """The negative pin: an uncapped search that located nothing keeps the found-nothing note,
    which assembly keys on to tell 'searched, none' from 'could not search'."""
    out = _pointers(_instruments("BRBR"), _Edgar(FtsResult(hits=[], total=0)), exhibits=())
    assert out.status is SourceStatus.UNKNOWN and out.note == COVENANT_SEARCH_FOUND_NOTHING


class _ShortPageEfts(_PagedEfts):
    """efts serving 60 hits a page — the cap line must count what came back, not the offsets."""

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> dict[str, Any]:
        data = super().get_json(url, ttl_seconds=ttl_seconds)
        data["hits"]["hits"] = data["hits"]["hits"][:60]
        return data


def test_the_prefilter_cap_line_counts_the_hits_it_read() -> None:
    """Review round 1: the line said "read 500" from the request offsets; with 60-hit pages it read
    300."""
    capped: list[str] = []
    mention_prefilter(cast(CachedHttp, _ShortPageEfts(564)), ["0000000001"], ("defense",),
                      startdt="2025-09-01", enddt="2026-06-30", capped=capped)
    assert len(capped) == 1 and "read 300 of 564" in capped[0], capped
