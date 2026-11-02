"""Phase 2 C3 — E1-D10: a filings window that reaches past the submissions document's recent page
reads the older pages it overlaps, or says it could not.

`recent_filings(cik, since=…)` read only `filings.recent`, which holds a filer's newest ~1,000
filings, and ignored the `files` pages the document lists for the rest. A window older than the
recent page therefore ended silently at its first row: Gartner's recent page starts 2021-12-02,
so a window from 2021-06-01 missed every filing in between. Measured 2026-10-30 on the 2,961
cached submissions documents: 1,566 list older pages, and for 16 (high-volume filers — BlackRock,
Bank of America, Citigroup, JPMorgan …) the recent page starts after 2023-10-31, so a 3-year window
on 2026-10-30 is cut. No committed page's 3-year window is cut today.

Fixtures are Gartner's real submissions document and its real older page -001, each cut to a
slice of its rows (`tests/fixtures/submissions_pages`). HTTP is mocked."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.edgar.client import EdgarClient
from vinci.netcache import CachedHttp, HttpError

_FIX = Path(__file__).resolve().parent / "fixtures" / "submissions_pages"
DOC = json.loads((_FIX / "IT.json").read_text())
PAGE1 = json.loads((_FIX / "IT-submissions-001.json").read_text())
CIK = "0000749251"


class _Sec:
    """Serves Gartner's document and older page -001; refuses -002, or every older page."""

    def __init__(self, *, refuse_pages: bool = False) -> None:
        self.refuse_pages = refuse_pages
        self.urls: list[str] = []

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> dict[str, Any]:
        self.urls.append(url)
        if url.endswith(f"CIK{CIK}.json"):
            return cast(dict[str, Any], DOC)
        if url.endswith("-submissions-001.json") and not self.refuse_pages:
            return cast(dict[str, Any], PAGE1)
        raise HttpError(f"not served: {url}")


def _client(sec: _Sec) -> EdgarClient:
    return EdgarClient(http=cast(CachedHttp, sec))


def _page1_8ks_since(since: date) -> set[str]:
    return {a for a, f, d in zip(PAGE1["accessionNumber"], PAGE1["form"], PAGE1["filingDate"],
                                 strict=True) if f == "8-K" and date.fromisoformat(d) >= since}


def test_a_window_past_the_recent_page_reads_the_older_page() -> None:
    """From 2021-06-01: the 8-Ks Gartner filed before its recent page begins (2021-12-02) are
    read from page -001; page -002 (1996–2010) is never fetched."""
    sec = _Sec()
    got = _client(sec).recent_filings(CIK, forms=("8-K",), since=date(2021, 6, 1))
    older = _page1_8ks_since(date(2021, 6, 1))
    assert older and older <= {f.accession for f in got}
    assert all(f.filing_date >= date(2021, 6, 1) for f in got)
    assert not any("-submissions-002" in u for u in sec.urls)
    dates = [f.filing_date for f in got]
    assert dates == sorted(dates, reverse=True)  # newest first, as the recent page reads


@pytest.mark.parametrize("since", [date(2022, 1, 1), None])
def test_a_window_inside_the_recent_page_fetches_nothing_more(since: date | None) -> None:
    """The negative pin: a window the recent page covers, or no window at all, reads the recent
    page only — as before, at no extra request."""
    sec = _Sec()
    _client(sec).recent_filings(CIK, forms=("8-K",), since=since)
    assert not any("-submissions-" in u for u in sec.urls)


def test_an_older_page_that_cannot_be_read_is_never_a_short_answer() -> None:
    """A page the window needs and cannot read raises, naming it — the callers degrade an
    HttpError to UNKNOWN, where a short list read as "no filings" before the recent page."""
    with pytest.raises(HttpError, match="submissions-001"):
        _client(_Sec(refuse_pages=True)).recent_filings(CIK, forms=("8-K",),
                                                        since=date(2021, 6, 1))


def test_a_page_that_failed_is_not_fetched_again_by_the_same_client() -> None:
    """An assembly makes several windowed reads of one filer (ownership, insider, dilution, gap
    8-Ks …). A page that failed once is remembered as the document's failure is
    (`_submissions`), so a degraded feed costs its retry storm once — every later read still
    raises, naming the page."""
    sec = _Sec(refuse_pages=True)
    client = _client(sec)
    for forms in (("8-K",), ("4",)):
        with pytest.raises(HttpError, match="submissions-001"):
            client.recent_filings(CIK, forms=forms, since=date(2021, 6, 1))
    assert sum(u.endswith("-submissions-001.json") for u in sec.urls) == 1


class _Malformed(_Sec):
    """Page -001 answered with an HTML interstitial (a ValueError from the JSON parse), a page
    missing its `form` array, a `files` entry with no name, or one whose `filingTo` is not an ISO
    date (review round 1: its parse ran outside the guard)."""

    def __init__(self, how: str) -> None:
        super().__init__()
        self.how = how

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> dict[str, Any]:
        if url.endswith(f"CIK{CIK}.json") and self.how in ("unnamed", "bad-span"):
            doc = json.loads(json.dumps(DOC))
            for page in doc["filings"]["files"]:
                if self.how == "unnamed":
                    page.pop("name")
                else:
                    page["filingTo"] = page["filingTo"].replace("-", "/")
            self.urls.append(url)
            return cast(dict[str, Any], doc)
        if url.endswith("-submissions-001.json"):
            self.urls.append(url)
            if self.how == "interstitial":
                raise ValueError("Expecting value: line 1 column 1 (char 0)")
            return {k: v for k, v in PAGE1.items() if k != "form"}
        return super().get_json(url, ttl_seconds=ttl_seconds)


@pytest.mark.parametrize("how", ["interstitial", "no-form-array", "unnamed", "bad-span"])
def test_a_malformed_older_page_raises_an_http_error_naming_it(how: str) -> None:
    """The windowed callers degrade an HttpError to UNKNOWN, and several catch nothing else: a
    page SEC answers with an interstitial, or one missing its arrays, must not escape as a
    ValueError or KeyError that aborts the assembly — and an unnamed page is never fetched."""
    sec = _Malformed(how)
    with pytest.raises(HttpError, match="older submissions page"):
        _client(sec).recent_filings(CIK, forms=("8-K",), since=date(2021, 6, 1))
    assert not any(u.endswith("/None") for u in sec.urls)


# ─── review round 2 (coordinator) ─────────────────────────────────────────────────────────────
# EDGAR RE-CUTS the older pages from the newest end whenever the recent page's boundary moves:
# WFC's page -001 spanned 2020-02-11..2024-10-20 on 2026-06-30 and 2020-05-29..2025-10-28 on
# 2026-10-30. A page cached longer than the document listing it therefore belongs to another
# vintage: it leaves a hole between its newest row and the recent page, or repeats rows the
# recent page holds. Measured on the 35 document/page pairs this machine's caches hold from one
# run, a page's rows always match its listing: the count is `filingCount`, the oldest row is
# `filingFrom`, the newest is at most `filingTo` + 1 day.

def _rows(src: dict[str, Any], keep: list[int]) -> dict[str, Any]:
    """The rows ``keep`` of a page's parallel arrays (the non-array keys carried as they are)."""
    return {k: ([v[i] for i in keep] if isinstance(v, list) else v) for k, v in src.items()}


_N = len(PAGE1["accessionNumber"])
_FIRST_8K = PAGE1["form"].index("8-K")
#: page -001 as an OLDER vintage would serve it: its newest rows, the first 8-K among them,
#: re-cut onto the recent page since — so a hole where they were
STALE_PAGE1 = _rows(PAGE1, list(range(_FIRST_8K + 1, _N)))


class _Vintages(_Sec):
    """Serves ``page`` and ``doc`` from the cache (any TTL above 0) and the consistent pair
    (DOC, PAGE1) when asked for a fresh copy (``ttl_seconds=0``), or ``page`` always."""

    def __init__(self, page: dict[str, Any], doc: dict[str, Any] | None = None, *,
                 always_stale: bool = False) -> None:
        super().__init__()
        self.page, self.doc, self.always_stale = page, doc or DOC, always_stale
        self.ttls: dict[str, list[float | None]] = {}

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> dict[str, Any]:
        self.urls.append(url)
        self.ttls.setdefault(url.rsplit("/", 1)[-1], []).append(ttl_seconds)
        fresh = ttl_seconds == 0 and not self.always_stale
        if url.endswith(f"CIK{CIK}.json"):
            return cast(dict[str, Any], DOC if fresh else self.doc)
        if url.endswith("-submissions-001.json"):
            return cast(dict[str, Any], PAGE1 if fresh else self.page)
        raise HttpError(f"not served: {url}")


def test_an_older_page_is_cached_no_longer_than_the_document_listing_it() -> None:
    """A page held 30 days beside a document held 1 is two vintages a day after the boundary
    moves. The page takes the document's TTL."""
    sec = _Vintages(PAGE1)
    _client(sec).recent_filings(CIK, forms=("8-K",), since=date(2021, 6, 1))
    assert sec.ttls[f"CIK{CIK}-submissions-001.json"] == sec.ttls[f"CIK{CIK}.json"]


def test_a_stale_older_page_is_read_again_never_left_with_a_hole() -> None:
    """The cached -001 is of an older vintage (its newest rows, an 8-K among them, missing): its
    rows disagree with the listing, so the window is read again fresh — never returned short."""
    sec = _Vintages(STALE_PAGE1)
    got = {f.accession for f in _client(sec).recent_filings(CIK, forms=("8-K",),
                                                              since=date(2021, 6, 1))}
    assert _page1_8ks_since(date(2021, 6, 1)) <= got
    assert 0 in sec.ttls[f"CIK{CIK}-submissions-001.json"]  # read fresh


def test_a_page_that_never_matches_its_listing_raises_naming_it() -> None:
    sec = _Vintages(STALE_PAGE1, always_stale=True)
    with pytest.raises(HttpError, match=r"submissions-001.*listing"):
        _client(sec).recent_filings(CIK, forms=("8-K",), since=date(2021, 6, 1))


def test_pages_of_two_vintages_never_return_a_filing_twice() -> None:
    """A NEWER -001 beside an older document: re-cut from the newest end, it holds the recent
    page's oldest rows too (BMO's document of 07-13 beside its -001 of 08-06 returned 529
    accessions twice). Its oldest row disagrees with the listing, so the pair is read fresh."""
    rec = DOC["filings"]["recent"]
    k = 5
    older = list(range(len(rec["accessionNumber"]) - k, len(rec["accessionNumber"])))
    newer = {key: ([rec[key][i] for i in older] + PAGE1[key][:_N - k]
                   if isinstance(PAGE1.get(key), list) and key in rec else PAGE1[key])
             for key in PAGE1}
    forms = tuple(sorted(set(rec["form"]) | set(PAGE1["form"])))
    got = _client(_Vintages(newer)).recent_filings(CIK, forms=forms, since=date(2021, 6, 1))
    accessions = [f.accession for f in got]
    assert len(accessions) == len(set(accessions))


def test_a_repeated_accession_across_pages_is_returned_once() -> None:
    """Belt to the listing check, on a shape no cached pair shows (0 of 35 share a date with the
    newer page): a page consistent with its listing whose newest row, dated `filingTo` + 1,
    repeats the recent page's oldest accession."""
    rec = DOC["filings"]["recent"]
    page = json.loads(json.dumps(PAGE1))
    page["accessionNumber"][0] = rec["accessionNumber"][-1]
    page["form"][0] = rec["form"][-1]
    page["filingDate"][0] = "2021-12-01"
    got = _client(_Vintages(page)).recent_filings(CIK, forms=(rec["form"][-1],),
                                                  since=date(2021, 6, 1))
    accessions = [f.accession for f in got]
    assert accessions.count(rec["accessionNumber"][-1]) == 1


def test_a_page_listed_to_the_day_before_the_window_is_still_read() -> None:
    """A page's listed `filingTo` is the newer page's first day minus 2, while its rows run to
    minus 1 on 17 of the 35 same-run pairs measured: a window opening on `filingTo` + 1 must read
    the page. Page -001 listed to 2021-11-30, its newest row dated 2021-12-01."""
    page = json.loads(json.dumps(PAGE1))
    page["filingDate"][0] = "2021-12-01"
    got = _client(_Vintages(page)).recent_filings(CIK, forms=(page["form"][0],),
                                                  since=date(2021, 12, 1))
    assert page["accessionNumber"][0] in {f.accession for f in got}


def test_a_blank_filing_date_on_an_unrequested_row_does_not_stop_the_read() -> None:
    """`assay.py` records a blank `filingDate` as observed (0 of 2,961 cached documents carry
    one today). On a row of a form the caller did not ask for, main returned the 8-Ks; the
    early exit parsed every recent date and raised a ValueError past the HttpError-only
    callers."""
    doc = json.loads(json.dumps(DOC))
    rec = doc["filings"]["recent"]
    rec["filingDate"][next(i for i, f in enumerate(rec["form"]) if f != "8-K")] = ""
    got = _client(_Vintages(PAGE1, doc)).recent_filings(CIK, forms=("8-K",),
                                                        since=date(2021, 6, 1))
    assert _page1_8ks_since(date(2021, 6, 1)) <= {f.accession for f in got}
