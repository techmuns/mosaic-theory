"""STATE §5.0 row 42 (2): a 200 body that is not JSON is never cached as the JSON it was asked for.

`CachedHttp.get_text` wrote every 200 body to the cache BEFORE `get_json` parsed it, so an
interstitial served once for a submissions document or an older page was the cached page for its
whole TTL (one day for both since #878): every windowed read of that filer, in every process, read
"could not be read" (UNKNOWN) until the copy expired, though SEC was serving the page again.

REAL DATA through the real client: Gartner's (IT) committed submissions document and its older
page -001 (`tests/fixtures/submissions_pages/`), served by a mock transport behind a real
`CachedHttp` and a real `EdgarClient` — the reader the monitor and every windowed caller go through.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from vinci.edgar.client import EdgarClient
from vinci.netcache import CachedHttp, HttpError

_FIX = Path(__file__).resolve().parent / "fixtures" / "submissions_pages"
DOC = (_FIX / "IT.json").read_text()
PAGE1 = (_FIX / "IT-submissions-001.json").read_text()
CIK = "0000749251"
SINCE = date(2021, 6, 1)        # reaches past the recent page (it begins 2021-12-02) into -001
#: what a 200 interstitial looks like: an HTML page where JSON was asked for
INTERSTITIAL = "<!DOCTYPE html><html><body>Please wait while we verify your request…</body></html>"


class _Sec:
    """The SEC as a transport: the document always; page -001 as an interstitial ``bad`` times
    first, then the real page. Counts what reached the wire."""

    def __init__(self, bad: int) -> None:
        self.bad = bad
        self.page_requests = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith(f"CIK{CIK}.json"):
            return httpx.Response(200, text=DOC)
        if url.endswith("-submissions-001.json"):
            self.page_requests += 1
            body = INTERSTITIAL if self.page_requests <= self.bad else PAGE1
            return httpx.Response(200, text=body)
        return httpx.Response(404, text="not served")


def _http(tmp_path: Path, sec: _Sec) -> CachedHttp:
    http = CachedHttp(cache_dir=tmp_path, user_agent="test test@example.com",
                      min_interval_sec=0.0, namespace="sec")
    http._client = httpx.Client(transport=httpx.MockTransport(sec))  # noqa: SLF001
    return http


def _eight_ks(http: CachedHttp) -> list[Any]:
    # a FRESH EdgarClient each read: its memo of a failed page lasts one client (one assembly);
    # the disk cache is what outlives it
    return EdgarClient(http=http).recent_filings(CIK, forms=("8-K",), since=SINCE)


def test_an_interstitial_is_not_cached_so_the_next_read_gets_the_page(tmp_path: Path) -> None:
    """THE DEFECT: the interstitial was written to the cache, so the next client read it back from
    disk — no request — and the window stayed unreadable for the day. Now the first read still
    raises (naming the page, as #878 made it), nothing is cached, and the next read fetches the
    page and returns the 8-Ks on it."""
    sec = _Sec(bad=1)
    http = _http(tmp_path, sec)
    with pytest.raises(HttpError, match="submissions-001"):
        _eight_ks(http)
    got = _eight_ks(http)
    assert sec.page_requests == 2                    # the second read went to SEC, not the disk
    page1 = json.loads(PAGE1)
    on_page = {a for a, f, d in zip(page1["accessionNumber"], page1["form"], page1["filingDate"],
                                    strict=True) if f == "8-K" and date.fromisoformat(d) >= SINCE}
    assert on_page and on_page <= {f.accession for f in got}


def test_negative_a_json_page_is_cached_and_read_back_without_a_request(tmp_path: Path) -> None:
    """(−) A body that IS JSON is cached as before: the second read costs no request."""
    sec = _Sec(bad=0)
    http = _http(tmp_path, sec)
    first = _eight_ks(http)
    assert _eight_ks(http) == first and sec.page_requests == 1


def test_a_non_json_copy_already_on_disk_is_refetched_not_served(tmp_path: Path) -> None:
    """A copy written before bodies were checked (the cache a machine holds today) is a MISS for
    `get_json` — fetched again once — never parsed into the same error for the rest of its TTL."""
    sec = _Sec(bad=0)
    http = _http(tmp_path, sec)
    url = "https://data.sec.gov/submissions/CIK0000749251-submissions-001.json"
    http._write_cache(url, INTERSTITIAL)            # noqa: SLF001 — the state old code left
    got = _eight_ks(http)
    assert sec.page_requests == 1 and got
    assert json.loads(json.loads(http._cache_path(url).read_text())["text"])  # noqa: SLF001


def test_get_text_still_caches_any_200_body(tmp_path: Path) -> None:
    """(−) Only `get_json` checks the body: a document read as text (a filing's HTML) is any 200
    body, cached as it always was."""
    sec = _Sec(bad=1)
    http = _http(tmp_path, sec)
    url = "https://data.sec.gov/submissions/CIK0000749251-submissions-001.json"
    assert http.get_text(url, ttl_seconds=86_400) == INTERSTITIAL
    assert http.get_text(url, ttl_seconds=86_400) == INTERSTITIAL and sec.page_requests == 1
