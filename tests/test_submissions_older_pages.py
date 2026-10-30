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
    missing its `form` array, or a `files` entry with no name."""

    def __init__(self, how: str) -> None:
        super().__init__()
        self.how = how

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> dict[str, Any]:
        if url.endswith(f"CIK{CIK}.json") and self.how == "unnamed":
            doc = json.loads(json.dumps(DOC))
            for page in doc["filings"]["files"]:
                page.pop("name")
            self.urls.append(url)
            return cast(dict[str, Any], doc)
        if url.endswith("-submissions-001.json"):
            self.urls.append(url)
            if self.how == "interstitial":
                raise ValueError("Expecting value: line 1 column 1 (char 0)")
            return {k: v for k, v in PAGE1.items() if k != "form"}
        return super().get_json(url, ttl_seconds=ttl_seconds)


@pytest.mark.parametrize("how", ["interstitial", "no-form-array", "unnamed"])
def test_a_malformed_older_page_raises_an_http_error_naming_it(how: str) -> None:
    """The windowed callers degrade an HttpError to UNKNOWN, and several catch nothing else: a
    page SEC answers with an interstitial, or one missing its arrays, must not escape as a
    ValueError or KeyError that aborts the assembly — and an unnamed page is never fetched."""
    sec = _Malformed(how)
    with pytest.raises(HttpError, match="older submissions page"):
        _client(sec).recent_filings(CIK, forms=("8-K",), since=date(2021, 6, 1))
    assert not any(u.endswith("/None") for u in sec.urls)
