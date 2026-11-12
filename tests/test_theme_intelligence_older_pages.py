"""STATE §5.0 row 42 (a): the theme desk's filings walk names an older page it could not read,
and never joins a page of another vintage.

`SecResolver._walk_filings` walks a registrant's filings back from the recent submissions page to
the first periodic filing (or annual report) on or before the as-of date. It read the older pages
itself, and:
- a page it could not read ENDED THE WALK WITH NO WORD (a 404 or an unnamed listing), and every
  consumer read the short list as the SEC's answer — "no periodic filing on or before …", "no
  annual report …" — while a page answered with something not JSON (an interstitial) or not an
  object raised out of the resolver, and out of the enrichment step, which catches only HttpError;
- a page was held 30 days beside a document held 1 and never checked against the document's
  listing of it, so a page of an earlier vintage was joined as current. EDGAR re-cuts the pages
  from the newest end whenever the recent page's boundary moves (#878), so an earlier -001 ends
  earlier: the walk then found an OLDER filing and verified the listing against the wrong cover.

Now the walk's reason travels with its rows, and the cover page and the annual report state it
in place of "no … filing": the resolution's note and every UNVERIFIED listing name the page. A
page is held one day, as its document is, and is checked against its listing
(`vinci.edgar.client._page_mismatch`): on a disagreement both are read fresh once, and a second
disagreement is the stated reason. An SEC refusal still stops the run.

REAL DATA: Gartner's committed submissions document and its older page -001
(`tests/fixtures/submissions_pages/`, #878's fixtures) behind a REAL `CachedHttp`, served by a mock
transport. That document's recent page begins 2021-12-02, so as of 2021-09-01 the walk must read
page -001 (2021-03-02 → 2021-11-30), whose newest periodic filing by then is the 10-Q filed
2021-08-03. The live theme-desk corpus has no such walk (0 of 261 measured (CIK, as-of) pairs,
`docs/records/2026-11-12-fix2-s3-row42a-the-theme-desks-filings-walk-names-the-page-it-could-not-read.md`),
so a historical as-of on committed real pages is the one way to reach it. The cover pages are
minimal inline-XBRL stand-ins carrying Gartner's own symbol (`cover_html`).
"""
from __future__ import annotations

import json
import time
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.theme_intelligence_support import cover_html
from vinci.netcache import CachedHttp, SecRateLimitedError
from vinci.theme_intelligence.schemas import (
    EntityType,
    Mention,
    MentionRole,
    PitStatus,
    RecommendationStatus,
    ResolutionStatus,
    SecurityResolution,
)
from vinci.theme_intelligence.securities import (
    ARCHIVE_DOC,
    SUBMISSIONS,
    SUBMISSIONS_PAGE,
    TICKERS_EXCHANGE,
    TICKERS_MF,
    SecResolver,
)

ROOT = Path(__file__).resolve().parents[1]
_FIX = ROOT / "tests" / "fixtures" / "submissions_pages"
DOC: dict[str, Any] = json.loads((_FIX / "IT.json").read_text())
PAGE1: dict[str, Any] = json.loads((_FIX / "IT-submissions-001.json").read_text())
IT_CIK = "0000749251"
PAGE1_NAME = "CIK0000749251-submissions-001.json"
PAGE1_URL = SUBMISSIONS_PAGE.format(name=PAGE1_NAME)
DOC_URL = SUBMISSIONS.format(cik=IT_CIK)
#: before the recent page's first row (2021-12-02): the walk must read page -001
AS_OF = date(2021, 9, 1)
AUG_10Q = "0000749251-21-000030"  # 10-Q filed 2021-08-03, on page -001
MAY_10Q = "0000749251-21-000016"  # 10-Q filed 2021-05-04, on page -001
#: Gartner's row of the SEC ticker map (its CIK, registrant name and symbol as the document
#: states them; listed on the NYSE)
EXCHANGE = {"fields": ["cik", "name", "ticker", "exchange"],
            "data": [[749251, DOC["name"], "IT", "NYSE"]]}
FUNDS: dict[str, Any] = {"fields": ["cik", "seriesId", "classId", "symbol"], "data": []}
INTERSTITIAL = "<!DOCTYPE html><html><body>Please wait while we verify your request…</body></html>"


def _earlier_vintage(page: dict[str, Any], through: str = "2021-07-31") -> dict[str, Any]:
    """Page -001 as an EARLIER vintage held it: EDGAR re-cuts from the newest end, so it ended
    earlier — its rows filed after ``through`` were then on the recent page. Same arrays, fewer
    rows; the document's listing of -001 (114 rows to 2021-11-30) no longer describes it."""
    keep = [i for i, d in enumerate(page["filingDate"]) if d <= through]
    return {k: ([v[i] for i in keep] if isinstance(v, list) else v) for k, v in page.items()}


def _docs(rows: dict[str, Any]) -> dict[str, str]:
    """Each filing's archive URL → its primary document, for the 10-Qs and 10-Ks of ``rows``."""
    return {ARCHIVE_DOC.format(cik=749251, acc=a.replace("-", ""), doc=p): f
            for f, a, p in zip(rows["form"], rows["accessionNumber"], rows["primaryDocument"],
                               strict=True) if f in ("10-Q", "10-K")}


COVERS = {**_docs(DOC["filings"]["recent"]), **_docs(PAGE1)}


class _Sec:
    """The SEC as a transport for Gartner: the ticker maps, its document (``doc`` overrides it),
    page -001 as ``page`` says (``ok`` = the committed page), and a cover for every 10-Q / 10-K.
    Counts the requests that reached the wire."""

    def __init__(self, *, page: str = "ok", doc: dict[str, Any] | None = None) -> None:
        self.page, self.doc = page, doc or DOC
        self.requests: Counter[str] = Counter()

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.requests[url] += 1
        if url == TICKERS_EXCHANGE:
            return httpx.Response(200, text=json.dumps(EXCHANGE))
        if url == TICKERS_MF:
            return httpx.Response(200, text=json.dumps(FUNDS))
        if url == DOC_URL:
            return httpx.Response(200, text=json.dumps(self.doc))
        if url == PAGE1_URL:
            body = {"ok": json.dumps(PAGE1), "interstitial": INTERSTITIAL,
                    "not-an-object": json.dumps([PAGE1]),
                    "earlier-vintage": json.dumps(_earlier_vintage(PAGE1))}.get(self.page)
            return (httpx.Response(200, text=body) if body is not None
                    else httpx.Response(404, text="not served"))
        if url in COVERS:
            return httpx.Response(200, text=cover_html([{
                "title": "Common Stock, $.0005 Par Value", "symbol": "IT", "exchange": "NYSE"}]))
        return httpx.Response(404, text="not served")


def _http(tmp_path: Path, sec: _Sec) -> CachedHttp:
    http = CachedHttp(cache_dir=tmp_path / "cache", user_agent="test test@example.com",
                      min_interval_sec=0.0, max_retries=0, namespace="sec")
    http._client = httpx.Client(transport=httpx.MockTransport(sec))  # noqa: SLF001
    # the ticker maps held, so the machine's SEC pace (~2.7 a second) is spent on the filings
    _hold(http, TICKERS_EXCHANGE, EXCHANGE, age_sec=60.0)
    _hold(http, TICKERS_MF, FUNDS, age_sec=60.0)
    return http


def _hold(http: CachedHttp, url: str, body: dict[str, Any], *, age_sec: float) -> None:
    """A copy of ``url`` in the cache, fetched ``age_sec`` seconds ago."""
    http._cache_path(url).write_text(json.dumps(  # noqa: SLF001
        {"url": url, "fetched_at": time.time() - age_sec, "text": json.dumps(body)}))


def _gartner() -> Mention:
    return Mention(
        mention_id="M-test", article_id="A-test", article_version_id="AV-test",
        name_as_written="Gartner", normalized_name="gartner", entity_type=EntityType.COMPANY,
        role=MentionRole.POTENTIAL_BENEFICIARY, role_detail="IT research and advisory",
        direction="positive", recommendation_status=RecommendationStatus.NOT_A_RECOMMENDATION,
        block_id="b001", quote="Gartner was named", ticker_hint="IT", issuer_name_hint=None)


def _resolve(tmp_path: Path, sec: _Sec, *, as_of: date = AS_OF,
             http: CachedHttp | None = None) -> SecurityResolution:
    return SecResolver(tmp_path, http=http or _http(tmp_path, sec)).resolve(_gartner(), as_of=as_of)


def _verified_from(r: SecurityResolution, accession: str) -> bool:
    return (r.status is ResolutionStatus.LISTED_EQUITY and [x.ticker for x in r.listings] == ["IT"]
            and all(x.pit_status is PitStatus.VERIFIED and accession in (x.pit_source or "")
                    for x in r.listings))


# --- a page the walk could not read is named, never read as "no filing" ----------------------

@pytest.mark.parametrize("page", ["404", "interstitial", "not-an-object"])
def test_an_unreadable_older_page_is_named_never_read_as_no_filing(
        tmp_path: Path, page: str) -> None:
    """Before: a 404 ended the walk silently and the resolution read "no periodic filing on or
    before 2021-09-01 in the SEC submissions index" — a false statement about Gartner; an
    interstitial (ValueError) or a JSON list (AttributeError) raised out of the resolver."""
    r = _resolve(tmp_path, _Sec(page=page))
    assert r.status is ResolutionStatus.LISTED_EQUITY and r.listings == ()
    assert f"older submissions page {PAGE1_NAME} for CIK{IT_CIK} could not be read" in r.note
    assert "no periodic filing" not in r.note
    assert r.other_securities and all(
        x.pit_status is PitStatus.UNVERIFIED and PAGE1_NAME in (x.note or "")
        for x in r.other_securities)


def test_a_page_listed_with_no_name_is_named(tmp_path: Path) -> None:
    """Before: the listing's missing `name` (KeyError) ended the walk silently."""
    doc = json.loads(json.dumps(DOC))
    del doc["filings"]["files"][0]["name"]
    r = _resolve(tmp_path, _Sec(doc=doc))
    assert r.listings == ()
    assert (f"older submissions page (no name) for CIK{IT_CIK} could not be read" in r.note
            and "no periodic filing" not in r.note)


def test_negative_a_readable_older_page_gives_the_cover_it_holds(tmp_path: Path) -> None:
    """The committed page read: the listing is verified on the August 10-Q's cover, found on
    page -001 — the walk's ordinary result, unchanged."""
    sec = _Sec()
    r = _resolve(tmp_path, sec)
    assert _verified_from(r, AUG_10Q), (r.note, r.listings)
    assert sec.requests[PAGE1_URL] == 1


@pytest.mark.parametrize("page", ["404", "interstitial"])
def test_the_annual_report_names_the_page_it_could_not_read(tmp_path: Path, page: str) -> None:
    """The enrichment step's read. Before: "no annual report (10-K / 20-F / 40-F) on or before
    2021-09-01 in the SEC submissions index" on a 404, and a ValueError out of a step that
    degrades only an HttpError on an interstitial."""
    rep, why = SecResolver(tmp_path, http=_http(tmp_path, _Sec(page=page))).annual_report(
        IT_CIK, AS_OF)
    assert rep is None
    assert why.startswith(f"older submissions page {PAGE1_NAME} for CIK{IT_CIK} could not be "
                          f"read") and "no annual report" not in why


def test_negative_a_recent_annual_report_reads_no_older_page(tmp_path: Path) -> None:
    """The live corpus's case (every measured pair): the recent page holds the annual report,
    so no older page is asked for — and an unreadable one changes nothing."""
    sec = _Sec(page="404")
    rep, why = SecResolver(tmp_path, http=_http(tmp_path, sec)).annual_report(
        IT_CIK, date(2026, 9, 1))
    assert rep is not None, why
    assert rep.form == "10-K" and sec.requests[PAGE1_URL] == 0


# --- a page of another vintage is read again, never joined ------------------------------------

def test_a_page_of_another_vintage_is_read_again_not_joined(tmp_path: Path) -> None:
    """An earlier vintage of -001, held an hour (inside any TTL), lacks the rows filed after
    2021-07-31. Before: it was joined as current, the walk's newest 10-Q by 2021-09-01 was the
    MAY one, and the listing was verified on the wrong cover. Now the disagreement with the
    document's listing (fewer rows than the 114 it lists) reads both again."""
    sec = _Sec()
    http = _http(tmp_path, sec)
    _hold(http, PAGE1_URL, _earlier_vintage(PAGE1), age_sec=3600.0)
    r = _resolve(tmp_path, sec, http=http)
    assert _verified_from(r, AUG_10Q), (r.note, r.listings)
    assert not _verified_from(r, MAY_10Q)
    assert sec.requests[PAGE1_URL] == 1  # read again, fresh


def test_a_page_that_still_disagrees_when_read_fresh_is_named(tmp_path: Path) -> None:
    """Before: an earlier vintage served even fresh was joined and verified on the May cover.
    Now the second disagreement is the stated reason, and no listing is verified."""
    r = _resolve(tmp_path, _Sec(page="earlier-vintage"))
    assert r.listings == ()
    n = len(_earlier_vintage(PAGE1)["accessionNumber"])
    assert (f"older submissions page {PAGE1_NAME} for CIK{IT_CIK} disagrees with the document's "
            f"listing of it, read fresh ({n} rows where it lists 114)") in r.note


def test_a_page_held_longer_than_its_document_is_read_again(tmp_path: Path) -> None:
    """A page is held no longer than its document's day: a copy two days old is fetched again
    (before: held 30 days). Its negative: a copy an hour old is read from the cache."""
    for age, fetched in ((2 * 86_400.0, 1), (3600.0, 0)):
        sec = _Sec()
        http = _http(tmp_path / str(age), sec)
        _hold(http, PAGE1_URL, PAGE1, age_sec=age)
        r = _resolve(tmp_path, sec, http=http)
        assert _verified_from(r, AUG_10Q), (age, r.note)
        assert sec.requests[PAGE1_URL] == fetched, age


def test_the_listing_check_is_the_edgar_clients() -> None:
    """The theme desk may not import the EDGAR client (`test_theme_intelligence_isolation`), so
    the check is restated: held to the client's answer on the committed pair and on each way a
    page of another vintage breaks it."""
    from vinci.edgar.client import _page_mismatch as client
    from vinci.theme_intelligence.securities import _page_mismatch as desk
    (listing,) = [f for f in DOC["filings"]["files"] if f["name"] == PAGE1_NAME]
    newest = {**PAGE1, "filingDate": ["2021-12-03", *PAGE1["filingDate"][1:]]}
    cases = [(listing, PAGE1, None),                                     # the committed pair
             (listing, _earlier_vintage(PAGE1), "rows where it lists 114"),
             ({**listing, "filingFrom": "2021-03-01"}, PAGE1, "its oldest row is"),
             (listing, newest, "its newest row is"),
             ({"name": PAGE1_NAME}, _earlier_vintage(PAGE1), None)]     # nothing listed to check
    for lst, rows, says in cases:
        assert desk(lst, rows) == client(lst, rows)
        assert (desk(lst, rows) is None) if says is None else says in (desk(lst, rows) or "")


# --- an SEC refusal still stops the run ---------------------------------------------------------

def test_negative_an_sec_refusal_still_stops_the_run(tmp_path: Path) -> None:
    """`SecRateLimitedError` is not an HttpError on purpose: a run never keeps sending into a
    fair-access block, so it is not turned into a reason."""
    http = _http(tmp_path, _Sec())
    real = http.get_json

    def refusing(url: str, *, ttl_seconds: float | None = None) -> Any:
        if url == PAGE1_URL:
            raise SecRateLimitedError(f"SEC refused {url} with 403")
        return real(url, ttl_seconds=ttl_seconds)

    http.get_json = refusing  # type: ignore[method-assign,assignment]
    with pytest.raises(SecRateLimitedError):
        _resolve(tmp_path, _Sec(), http=http)
