"""Company matching — the PR #703 review findings O8-O12, and the verified leads U21 and U23d
(`docs/records/2026-10-14-theme-intelligence-open-review-findings.md`,
`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`).

The registrants are REAL SEC registrants with their REAL ticker-map rows, SIC codes and periodic
filings (`tests/fixtures/theme_intelligence/company_matching/sec_records.json`, provenance in the
file). Cover pages are minimal inline-XBRL stand-ins carrying each registrant's own symbols — the
point-in-time check that follows identity. Each pin carries its negative: what must still
resolve beside what must not.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import FIXTURES, cover_html
from vinci.netcache import CachedHttp, HttpError
from vinci.theme_intelligence.schemas import (
    EntityType,
    Mention,
    MentionRole,
    RecommendationStatus,
    ResolutionStatus,
)
from vinci.theme_intelligence.securities import (
    ARCHIVE_DOC,
    SUBMISSIONS,
    SUBMISSIONS_PAGE,
    TICKERS_EXCHANGE,
    TICKERS_MF,
    SecResolver,
)

AS_OF = date(2026, 10, 11)
SEC = json.loads((FIXTURES / "company_matching" / "sec_records.json").read_text())
ENB, TRP, DAL = "0000895728", "0001232384", "0000027904"


class RealSec:
    """The fixture's SEC records in place of the network; anything else fails like the network.
    `fail_submissions` makes the first N submissions reads of that CIK fail (O12)."""

    def __init__(self, *, fail_submissions: tuple[str, int] | None = None) -> None:
        self.fail = dict([fail_submissions]) if fail_submissions else {}
        self.reads: dict[str, int] = {}

    def get_json(self, url: str, ttl_seconds: float | None = None) -> Any:
        if url == TICKERS_EXCHANGE:
            return SEC["exchange"]
        if url == TICKERS_MF:
            return SEC["mf"]
        for cik, sub in SEC["submissions"].items():
            if url == SUBMISSIONS.format(cik=cik):
                self.reads[cik] = self.reads.get(cik, 0) + 1
                if self.reads[cik] <= self.fail.get(cik, 0):
                    raise HttpError(f"Exhausted retries for {url}")
                return {"name": sub["name"], "sic": sub["sic"],
                        "sicDescription": sub["sicDescription"],
                        "filings": {"recent": sub["recent"], "files": []}}
        raise HttpError(f"not in the fixture: {url}")

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        for cik, sub in SEC["submissions"].items():
            rec = sub["recent"]
            for acc, doc in zip(rec["accessionNumber"], rec["primaryDocument"], strict=True):
                if url == ARCHIVE_DOC.format(cik=int(cik), acc=acc.replace("-", ""), doc=doc):
                    return cover_html([{"title": "Preferred Stock" if "-P" in t else "Common Stock",
                                        "symbol": t, "exchange": e}
                                       for c, _n, t, e in SEC["exchange"]["data"]
                                       if int(c) == int(cik) and e in ("NYSE", "Nasdaq")])
        raise HttpError(f"not in the fixture: {url}")

    def fetched_at(self, url: str, **_kw: Any) -> float | None:
        return None  # a double records no fetch time


def _resolver(http: Any = None) -> SecResolver:
    return SecResolver(Path("/nonexistent"), http=http or RealSec())  # type: ignore[arg-type]


def mention(name: str, quote: str, role_detail: str, *, hint: str | None = None,
            role: str = "potential_beneficiary",
            entity: EntityType = EntityType.COMPANY) -> Mention:
    return Mention(
        mention_id="M-test", article_id="A-test", article_version_id="AV-test",
        name_as_written=name, normalized_name=name.lower(), entity_type=entity,
        role=MentionRole(role), role_detail=role_detail, direction="positive",
        recommendation_status=RecommendationStatus.NOT_A_RECOMMENDATION, block_id="b001",
        quote=quote, ticker_hint=hint, issuer_name_hint=None)


def _tickers(m: Mention, *, as_of: date = AS_OF, http: Any = None) -> list[str]:
    return [x.ticker for x in _resolver(http).resolve(m, as_of=as_of).listings]


# --- O8: the ticker-hint path and the fund path -------------------------------------------------

def test_a_private_company_is_not_listed_by_a_partial_name_even_with_a_ticker_hint() -> None:
    """"Cognition", the private AI lab, with the extraction's hint CGTX had resolved to Cognition
    Therapeutics: the private-company guard ran only on the no-hint path."""
    lab = mention("Cognition", "the viral Devin agent demo in March 2024",
                  "AI lab behind the Devin coding agent", hint="CGTX",
                  entity=EntityType.PRIVATE_COMPANY, role="context")
    r = _resolver().resolve(lab, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED and not r.listings
    assert "classified as a private company" in r.note
    # the registrant's exact name still overrides the classification; a company-typed mention
    # with the hint is the hint's registrant
    exact = lab.model_copy(update={"name_as_written": "Cognition Therapeutics"})
    assert _tickers(exact) == ["CGTX"]
    company = lab.model_copy(update={"entity_type": EntityType.COMPANY})
    assert _tickers(company) == ["CGTX"]


def test_a_fund_takes_the_ticker_printed_beside_its_own_name() -> None:
    """The first fund ticker in the quote was taken: VanEck's ETF resolved to iShares' SOXX."""
    quote = ("semis ETFs such as the iShares Semiconductor ETF (SOXX) and the VanEck "
             "Semiconductor ETF (SMH) rallied")
    vaneck = mention("VanEck Semiconductor ETF", quote, "", entity=EntityType.ETF_OR_FUND)
    r = _resolver().resolve(vaneck, as_of=AS_OF)
    assert r.status is ResolutionStatus.FUND and [x.ticker for x in r.listings] == ["SMH"]
    ishares = vaneck.model_copy(update={"name_as_written": "iShares Semiconductor ETF"})
    assert _tickers(ishares) == ["SOXX"]
    # the name beside its ticker, whatever its case or spacing as the model wrote it
    for spelt in ("VanEck semiconductor ETF", "VanEck  Semiconductor  ETF"):
        assert _tickers(vaneck.model_copy(update={"name_as_written": spelt})) == ["SMH"]
    # several printed and none beside the name: which one is not said
    both = vaneck.model_copy(update={"name_as_written": "semiconductor ETFs"})
    rb = _resolver().resolve(both, as_of=AS_OF)
    assert rb.status is ResolutionStatus.AMBIGUOUS and "SOXX" in rb.note and "SMH" in rb.note
    # one printed: that one
    one = vaneck.model_copy(update={"name_as_written": "the semis ETF",
                                    "quote": "the VanEck Semiconductor ETF (SMH) rallied"})
    assert _tickers(one) == ["SMH"]


# --- O9: a partial name needs backing -----------------------------------------------------------

def test_a_partial_name_with_nothing_confirming_it_is_not_resolved() -> None:
    """"Schneider" (the electrical-equipment maker, which files no SEC report) resolved to
    Schneider National, a trucking firm, on the bare name prefix: no hint, no business stated
    that the trucking SIC would veto."""
    schneider = mention("Schneider", "Schneider and Vertiv benefit from data-centre buildouts",
                        "data-centre supplier")
    r = _resolver().resolve(schneider, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED and not r.listings
    assert "a partial name with nothing confirming it" in r.method
    assert "Schneider National" in r.note
    # "GE" with no hint is not GE Vernova by prefix
    ge = mention("GE", "GE's jet engines", "jet engine maker for commercial aviation")
    assert _resolver().resolve(ge, as_of=AS_OF).status is ResolutionStatus.UNRESOLVED
    # backed: the exact name, a ticker hint, or the company's own industry
    assert _tickers(schneider.model_copy(update={"name_as_written": "Schneider National"})) \
        == ["SNDR"]
    assert _tickers(schneider.model_copy(update={"ticker_hint": "SNDR"})) == ["SNDR"]
    assert _tickers(schneider.model_copy(update={"role_detail": "trucking and freight carrier"})) \
        == ["SNDR"]


def test_the_issuer_hint_backs_a_partial_name_it_narrowed() -> None:
    """Two registrants share the prefix: the model's issuer hint naming one EXACTLY is backing
    (the backing rule must not refuse what the hint picked)."""
    m = mention("Constellation", "Constellation was named", "").model_copy(
        update={"issuer_name_hint": "Constellation Energy Corp"})
    r = _resolver().resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.LISTED_EQUITY and [x.ticker for x in r.listings] == ["CEG"]
    assert "narrowed by the model's issuer hint" in r.method
    bare = m.model_copy(update={"issuer_name_hint": None})
    assert _resolver().resolve(bare, as_of=AS_OF).status is ResolutionStatus.AMBIGUOUS


# --- O10: the industry a company serves is not its own -----------------------------------------

@pytest.mark.parametrize(("name", "quote", "role_detail", "hint"), [
    ("General Electric", "General Electric's jet engines for commercial aviation",
     "jet engine maker for commercial aviation", "GE"),
    ("General Electric", "General Electric's aviation engines", "aviation engine maker", "GE"),
    ("Boeing", "Boeing's commercial aviation backlog", "commercial aircraft maker for airlines",
     "BA"),
    ("Howmet", "Howmet supplies engine components to the aviation industry",
     "aerospace engine parts supplier to aviation", "HWM"),
    ("Thermo Fisher", "Thermo Fisher's tools sold to pharmaceutical and biotech customers",
     "life-science tools supplier to pharmaceutical companies", "TMO"),
    ("Danaher", "Danaher's bioprocessing sales to biotech and pharmaceutical customers",
     "bioprocessing equipment supplier to drug makers", "DHR"),
    ("CVS", "CVS pharmacy sales of GLP-1 drugs", "pharmacy chain dispensing drugs", "CVS"),
])
def test_a_company_described_by_the_industry_it_serves_is_still_itself(
        name: str, quote: str, role_detail: str, hint: str) -> None:
    r = _resolver().resolve(mention(name, quote, role_detail, hint=hint), as_of=AS_OF)
    assert r.status is ResolutionStatus.LISTED_EQUITY, r.note
    assert [x.ticker for x in r.listings] == [hint]


def test_the_name_as_written_may_be_the_ticker_the_hint_names() -> None:
    """"GE" with hint GE was refused as two identities: the first token of "GE" is not that of
    GENERAL ELECTRIC CO. Seen on the real corpus as AMD, WMB, GEV, KMI and DTM."""
    ge = mention("GE", "GE's jet engines", "jet engine maker for commercial aviation", hint="GE")
    assert _tickers(ge) == ["GE"]
    # a ticker for ANOTHER issuer is still two identities
    other = ge.model_copy(update={"ticker_hint": "BA"})
    ro = _resolver().resolve(other, as_of=AS_OF)
    assert ro.status is ResolutionStatus.UNRESOLVED and "BOEING CO" in ro.note


def test_an_infinitive_to_is_not_a_customer_clause() -> None:
    """Everything after the first "to" was dropped as the industry served: "Expected to sell SOFC
    fuel cells to data centres" read as no business at all, and a wrong hint went unchecked."""
    m = mention("Delta", "Delta was named", "Expected to sell SOFC fuel cells to data centres",
                hint="DAL")
    r = _resolver().resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED and "SIC 4512" in r.note
    # a supplying word before "to" still names the customer, not the company
    tmo = mention("Thermo Fisher", "Thermo Fisher was named",
                  "instruments supplier to pharmaceutical companies", hint="TMO")
    assert _tickers(tmo) == ["TMO"]


def test_a_plainly_different_own_business_is_still_refused() -> None:
    m = mention("Merck", "Merck was mentioned", "oil pipeline operator", hint="MRK")
    r = _resolver().resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED and "not the same company" in r.note
    airline = mention("Delta", "Ceres Power (and its licensees), Weichai, Doosan, and Delta",
                      "SOFC competitor", role="disruptor")
    assert _resolver().resolve(airline, as_of=AS_OF).status is ResolutionStatus.UNRESOLVED


# --- O11: the identity check reads the role, not the quote's wording ----------------------------

def test_the_identity_check_reads_the_role_never_the_quote() -> None:
    """The quote's words were read as the company's business: "nuclear power demand" made a
    uranium miner a power producer, "Merck's late-stage pipeline" an oil and gas company."""
    uec = mention("Uranium Energy",
                  "Uranium Energy benefits as nuclear power demand from data centres rises",
                  "uranium producer", hint="UEC")
    assert _tickers(uec) == ["UEC"]
    merck = mention("Merck", "Merck's late-stage pipeline includes several obesity readouts",
                    "company with a late-stage obesity pipeline", hint="MRK")
    assert _tickers(merck) == ["MRK"]  # a drug pipeline is not an oil pipeline
    # the role still decides: a role naming another business is refused
    power = uec.model_copy(update={"role_detail": "nuclear power producer"})
    rp = _resolver().resolve(power, as_of=AS_OF)
    assert rp.status is ResolutionStatus.UNRESOLVED and "SIC 1090" in rp.note


# --- O12: one failed SEC read is not "no data" --------------------------------------------------

def test_a_failed_submissions_read_fails_closed_and_is_not_asked_again_this_run() -> None:
    """One failed fetch was cached as None for the run and the identity check was OFF: Delta (the
    Taiwanese power-supply maker) resolved to Delta Air Lines on every later lookup. Retrying on
    every lookup instead re-paid the whole retry ladder each time (an SEC outage stretched a scan
    to hours). A failure is remembered for the run — and a partial name whose filings were not
    read is refused as unchecked, never resolved without the check."""
    m = mention("Delta", "Ceres Power (and its licensees), Weichai, Doosan, and Delta",
                "SOFC competitor", hint="DAL", role="disruptor")
    http = RealSec(fail_submissions=(DAL, 1))
    r = SecResolver(Path("/nonexistent"), http=http)  # type: ignore[arg-type]
    first = r.resolve(m, as_of=AS_OF)
    assert first.status is ResolutionStatus.UNRESOLVED and not first.listings
    assert "identity not checked" in first.method and "could not be read" in first.note
    second = r.resolve(m, as_of=AS_OF)  # the SEC would answer now — not asked again this run
    assert second.status is ResolutionStatus.UNRESOLVED and http.reads[DAL] == 1
    # the next run reads it again, and the business it files under refuses the airline
    again = SecResolver(Path("/nonexistent"), http=http)  # type: ignore[arg-type]
    third = again.resolve(m, as_of=AS_OF)
    assert third.status is ResolutionStatus.UNRESOLVED and "SIC 4512" in third.note
    assert http.reads[DAL] == 2
    # the registrant's exact name needs no industry check: it is not refused as unchecked
    exact = m.model_copy(update={"name_as_written": "Delta Air Lines", "role_detail": "airline"})
    failing = RealSec(fail_submissions=(DAL, 1))
    fresh = SecResolver(Path("/nonexistent"), http=failing)  # type: ignore[arg-type]
    assert "identity not checked" not in fresh.resolve(exact, as_of=AS_OF).method


# --- U21: foreign-filer status as of the date ---------------------------------------------------

def test_foreign_filer_status_is_read_as_of_the_resolution_date() -> None:
    """Enbridge filed 40-F to 2017 and 10-K since 2018. Any 20-F / 40-F among its recent filings
    made it a foreign private issuer at every date."""
    enb = mention("Enbridge", "Enbridge's Mainline expansion", "crude oil pipeline operator",
                  hint="ENB")
    now = _resolver().resolve(enb, as_of=AS_OF)
    assert now.status is ResolutionStatus.LISTED_EQUITY and [x.ticker for x in now.listings] \
        == ["ENB"]
    then = _resolver().resolve(enb, as_of=date(2016, 6, 30))
    assert then.status is ResolutionStatus.UNRESOLVED and "issuer files 20-F/40-F" in then.method
    r = _resolver()
    assert r.is_foreign_private_issuer(ENB, as_of=date(2018, 1, 31)) is True  # 40-F 2017-02-17
    assert r.is_foreign_private_issuer(ENB, as_of=date(2018, 2, 16)) is False  # 10-K 2018-02-16
    # a filer of 40-F to this day stays one
    trp = mention("TC Energy", "TC Energy's gas pipelines", "natural gas pipeline operator",
                  hint="TRP")
    rt = _resolver().resolve(trp, as_of=AS_OF)
    assert rt.status is ResolutionStatus.UNRESOLVED and "issuer files 20-F/40-F" in rt.method
    # no periodic report on or before the date: not decidable, never guessed
    assert r.is_foreign_private_issuer(TRP, as_of=date(2020, 1, 1)) is None


def test_an_amendment_does_not_decide_the_filer_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """An amendment restates an EARLIER period: a 10-K/A filed after TC Energy's latest 40-F
    (added here to its real filings) does not make it a domestic filer."""
    rec = SEC["submissions"][TRP]["recent"]
    amended = {"form": ["10-K/A", *rec["form"]], "filingDate": ["2026-03-02", *rec["filingDate"]],
               "accessionNumber": ["0001232384-26-000099", *rec["accessionNumber"]],
               "primaryDocument": ["a.htm", *rec["primaryDocument"]]}
    monkeypatch.setitem(SEC["submissions"][TRP], "recent", amended)
    assert _resolver().is_foreign_private_issuer(TRP, as_of=AS_OF) is True


# --- U23d: the map's date is when it was fetched ------------------------------------------------

def _cached_maps(cache: Path, exchange_at: float, funds_at: float) -> CachedHttp:
    http = CachedHttp(cache_dir=cache, user_agent="test", min_interval_sec=0.0, max_retries=0,
                      namespace="sec")
    for url, body, at in ((TICKERS_EXCHANGE, SEC["exchange"], exchange_at),
                          (TICKERS_MF, SEC["mf"], funds_at)):
        http._cache_path(url).write_text(json.dumps(
            {"url": url, "fetched_at": at, "text": json.dumps(body)}))
    return http


def test_the_ticker_map_is_stamped_with_the_day_it_was_fetched(tmp_path: Path) -> None:
    """A map served from a cache up to seven days old was stamped with the day it was READ — in
    the record's source and in its id."""
    fetched = datetime.now(tz=UTC) - timedelta(days=3)  # the older map dates the pair
    http = _cached_maps(tmp_path, fetched.timestamp(),
                        (datetime.now(tz=UTC) - timedelta(days=1)).timestamp())
    m = mention("Zzyzx Holdings", "Zzyzx Holdings was named", "")
    r = SecResolver(tmp_path, http=http).resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED
    assert r.source_ref == (f"SEC ticker map retrieved {fetched.date().isoformat()} "
                            f"(name match only)")
    # an HTTP layer that holds no fetch time says so — never today's date
    rd = _resolver().resolve(m, as_of=AS_OF)
    assert rd.source_ref == "SEC ticker map, retrieval date not recorded (name match only)"


def test_the_filings_are_walked_once_per_registrant_and_date(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The foreign-filer check and the cover page each walked the older submission pages."""
    page = "CIK0000310158-submissions-001.json"
    http = RealSec()
    real = http.get_json
    walks: list[str] = []

    def with_page(url: str, ttl_seconds: float | None = None) -> Any:
        if url == SUBMISSIONS_PAGE.format(name=page):
            walks.append(url)  # an older page of Merck's filings (added here)
            return {"form": ["10-K"], "filingDate": ["2019-02-27"],
                    "accessionNumber": ["0000310158-19-000010"], "primaryDocument": ["k.htm"]}
        got = real(url, ttl_seconds)
        if url == SUBMISSIONS.format(cik="0000310158"):
            got["filings"]["files"] = [{"name": page, "filingFrom": "2010-01-01"}]
        return got
    monkeypatch.setattr(http, "get_json", with_page)
    m = mention("Merck", "Merck was named", "drug maker", hint="MRK")
    r = SecResolver(Path("/nonexistent"), http=http)  # type: ignore[arg-type]
    res = r.resolve(m, as_of=date(2020, 1, 1))
    assert res.registrant == "Merck & Co., Inc." and walks == [SUBMISSIONS_PAGE.format(name=page)]
    assert r.is_foreign_private_issuer("0000310158", as_of=date(2020, 1, 1)) is False
    assert len(walks) == 1  # the enrichment's check reads the same rows


def test_the_http_cache_remembers_the_fetch_time_of_what_it_read(tmp_path: Path) -> None:
    """The fetch time was read by parsing the whole cached entry again — megabytes for the SEC
    ticker map — right after the map itself had been read."""
    http = CachedHttp(cache_dir=tmp_path, user_agent="test", min_interval_sec=0.0, max_retries=0)
    read, fresh = "https://example.test/read.json", "https://example.test/fresh.json"
    stamp = time.time() - 60
    http._cache_path(read).write_text(json.dumps({"url": read, "fetched_at": stamp,
                                                  "text": "{}"}))
    assert http.get_json(read) == {}
    http._cache_path(read).unlink()  # gone from disk: the time comes from the read itself
    assert http.fetched_at(read) == stamp
    http._fetch_with_retries = lambda *_a, **_k: "{}"  # type: ignore[method-assign]
    assert http.get_json(fresh) == {}
    http._cache_path(fresh).unlink()
    assert http.fetched_at(fresh) is not None  # … and from a fresh write


def test_the_http_cache_reports_when_its_copy_was_fetched(tmp_path: Path) -> None:
    http = CachedHttp(cache_dir=tmp_path, user_agent="test", min_interval_sec=0.0, max_retries=0)
    url = "https://example.test/a.json"
    assert http.fetched_at(url) is None  # nothing held
    stamp = time.time() - 60
    http._cache_path(url).write_text(json.dumps({"url": url, "fetched_at": stamp, "text": "{}"}))
    assert http.fetched_at(url) == stamp
    http._cache_path(url).write_text("{torn")
    assert http.fetched_at(url) is None  # unreadable: no time, never a guess
