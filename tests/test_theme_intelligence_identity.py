"""Company IDENTITY before ticker verification (found 2026-10-11 in the Citi Gridlock card:
"Delta" — named among SOFC competitors, its extraction hint 2308 — resolved to DAL, Delta Air
Lines, on the bare name prefix "delta").

The registrants below are REAL SEC registrants with their REAL names, tickers and SIC codes
(SEC submissions, retrieved 2026-10-11); the mentions are the REAL shapes from the Citi PDF's
extraction (name, quote, role, hint). The cover pages are minimal inline-XBRL stand-ins carrying
only each registrant's own registered symbol — the point-in-time check after identity.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import cover_html
from vinci.netcache import HttpError
from vinci.theme_intelligence.schemas import (
    EntityType,
    Mention,
    MentionRole,
    PitStatus,
    RecommendationStatus,
    ResolutionStatus,
)
from vinci.theme_intelligence.securities import (
    ARCHIVE_DOC,
    SUBMISSIONS,
    TICKERS_EXCHANGE,
    TICKERS_MF,
    SecResolver,
    context_families,
    identity_conflict,
    parse_cover,
    sic_families,
)

AS_OF = date(2026, 10, 11)
#: cik, name, ticker, exchange, SIC, SIC description — as the SEC files them
REGISTRANTS = [
    ("0000027904", "DELTA AIR LINES, INC.", "DAL", "NYSE", 4512, "Air Transportation, Scheduled"),
    ("0001018724", "AMAZON COM INC", "AMZN", "Nasdaq", 5961,
     "Retail-Catalog & Mail-Order Houses"),
    ("0001664703", "Bloom Energy Corp", "BE", "NYSE", 3620,
     "Electrical Industrial Apparatus"),
    ("0001868275", "Constellation Energy Corp", "CEG", "Nasdaq", 4911, "Electric Services"),
    ("0000016918", "CONSTELLATION BRANDS, INC.", "STZ", "NYSE", 2084,
     "Wines, Brandy & Brandy Spirits"),
    ("0001559998", "Tencent Music Entertainment Group", "TME", "NYSE", 7370,
     "Services-Computer Programming, Data Processing, Etc."),
]


class SecDouble:
    """The SEC files the resolver reads, for the registrants above: ticker maps, submissions
    (with SIC and one 10-K) and a cover page per 10-K."""

    def get_json(self, url: str, ttl_seconds: float | None = None) -> Any:
        if url == TICKERS_EXCHANGE:
            return {"fields": ["cik", "name", "ticker", "exchange"],
                    "data": [[int(c), n, t, e] for c, n, t, e, _s, _d in REGISTRANTS]}
        if url == TICKERS_MF:
            return {"fields": ["cik", "seriesId", "classId", "symbol"], "data": []}
        for c, _n, _t, _e, sic, desc in REGISTRANTS:
            if url == SUBMISSIONS.format(cik=c):
                return {"sic": str(sic), "sicDescription": desc, "filings": {"recent": {
                    "form": ["10-K"], "filingDate": ["2026-02-10"],
                    "accessionNumber": [f"{c}-26-000001"], "primaryDocument": ["k.htm"]},
                    "files": []}}
        raise HttpError(f"not in the double: {url}")

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        for c, _n, t, e, _s, _d in REGISTRANTS:
            if url == ARCHIVE_DOC.format(cik=int(c), acc=f"{c}26000001", doc="k.htm"):
                return cover_html([{"title": "Common Stock", "symbol": t, "exchange": e}])
        raise HttpError(f"not in the double: {url}")


def _resolver(tmp_path: Path) -> SecResolver:
    return SecResolver(tmp_path / "sec", http=SecDouble())  # type: ignore[arg-type]


def mention(name: str, quote: str, role_detail: str, *, hint: str | None = None,
            role: str = "potential_beneficiary") -> Mention:
    return Mention(
        mention_id="M-test", article_id="A-test", article_version_id="AV-test",
        name_as_written=name, normalized_name=name.lower(), entity_type=EntityType.COMPANY,
        role=MentionRole(role), role_detail=role_detail, direction="positive",
        recommendation_status=RecommendationStatus.NOT_A_RECOMMENDATION, block_id="b001",
        quote=quote, ticker_hint=hint, issuer_name_hint=None)


# --- the Citi case, as extracted --------------------------------------------------------------

def test_delta_named_among_sofc_competitors_is_not_delta_air_lines(tmp_path: Path) -> None:
    m = mention("Delta", "Ceres Power (and its licensees), Weichai, Doosan, and Delta",
                "SOFC competitor", hint="2308", role="disruptor")
    r = _resolver(tmp_path).resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED and not r.listings and r.cik is None
    assert "'2308' is not an SEC-listed ticker" in r.note and "DELTA AIR LINES" in r.note


def test_without_the_hint_the_business_still_refuses_the_airline(tmp_path: Path) -> None:
    """The second guard alone: no hint, a unique prefix match — the source's business (SOFC)
    against the issuer's SEC industry (scheduled air transportation)."""
    m = mention("Delta", "Ceres Power (and its licensees), Weichai, Doosan, and Delta",
                "SOFC competitor", role="disruptor")
    r = _resolver(tmp_path).resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED and not r.listings
    assert "SIC 4512" in r.note and "not the same company" in r.note


def test_a_partial_name_with_a_foreign_hint_is_never_a_us_registrant(tmp_path: Path) -> None:
    """Tencent (hint 0700.HK) is not Tencent Music Entertainment (TME) — seen on the 2026-10-11
    SemiAnalysis article."""
    m = mention("Tencent", "Tencent and Alibaba are racing", "Chinese AI lab owner",
                hint="0700.HK")
    r = _resolver(tmp_path).resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.UNRESOLVED and r.registrant is None


# --- no false negatives: the right company still resolves, point in time ----------------------

@pytest.mark.parametrize(("name", "quote", "role_detail", "hint", "ticker"), [
    ("Delta Air Lines", "Delta Air Lines raised capacity", "airline carrier", None, "DAL"),
    ("Amazon", "Amazon has described its global PPA approach as central",
     "hyperscaler using PPAs for renewables", "AMZN", "AMZN"),
    ("Bloom Energy (BE)", "companies like Bloom Energy (BE) have emerged as leading providers",
     "solid oxide fuel cell supplier to data centers", "BE", "BE"),
], ids=["airline-context", "amazon-cloud-context", "bloom-sofc"])
def test_the_right_company_still_resolves_and_is_verified_point_in_time(
        tmp_path: Path, name: str, quote: str, role_detail: str, hint: str | None,
        ticker: str) -> None:
    r = _resolver(tmp_path).resolve(mention(name, quote, role_detail, hint=hint), as_of=AS_OF)
    assert r.status is ResolutionStatus.LISTED_EQUITY, r.note
    assert [x.ticker for x in r.listings] == [ticker]
    assert all(x.pit_status is PitStatus.VERIFIED for x in r.listings)  # identity, THEN ticker
    assert "identity checked against the issuer's SEC industry" in r.method


def test_a_shared_name_is_narrowed_by_the_business_the_source_describes(tmp_path: Path) -> None:
    """"Constellation" matches Constellation Energy and Constellation Brands: a nuclear power
    supplier is the utility, without any hint."""
    m = mention("Constellation", "Microsoft- Constellation's 20-year PPA",
                "nuclear power supplier in PPAs with hyperscalers")
    r = _resolver(tmp_path).resolve(m, as_of=AS_OF)
    assert r.status is ResolutionStatus.LISTED_EQUITY and r.registrant == \
        "Constellation Energy Corp"
    assert "narrowed by the source's described business" in r.method
    beer = mention("Constellation", "Constellation said beer depletions fell",
                   "beverage company")
    assert _resolver(tmp_path).resolve(beer, as_of=AS_OF).registrant == \
        "CONSTELLATION BRANDS, INC."


def test_with_no_business_stated_two_matches_stay_ambiguous(tmp_path: Path) -> None:
    m = mention("Constellation", "(Constellation, 2026)", "cited as a data source")
    assert _resolver(tmp_path).resolve(m, as_of=AS_OF).status is ResolutionStatus.AMBIGUOUS


# --- the pieces --------------------------------------------------------------------------------

def test_the_business_table_reads_strong_terms_only() -> None:
    assert context_families("SOFC competitor") == {"power_equipment"}
    assert context_families("hyperscaler using PPAs for renewables") == {
        "software_internet", "utilities_power"}
    assert context_families("cited on labor shortage / data center development") == set()
    assert sic_families(4512) == {"airlines"} and sic_families(None) == set()
    assert identity_conflict("SOFC competitor", None, None) is None  # no SIC: no veto
    assert identity_conflict("cited as a data source", 4512, "Air") is None  # nothing stated


def test_a_cover_page_symbol_loses_the_filings_typography() -> None:
    doc = ('<ix:nonNumeric contextRef="c-0" name="dei:TradingSymbol">“CBRE”</ix:nonNumeric>'
           '<ix:nonNumeric contextRef="c-0" name="dei:Security12bTitle">Class A Common Stock'
           '</ix:nonNumeric>')
    assert [ln.symbol for ln in parse_cover(doc)] == ["CBRE"]
