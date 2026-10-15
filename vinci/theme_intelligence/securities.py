"""Resolve source-named entities to securities from SEC primary data — verified, never guessed.

Sources (SEC, cached; the retrieval date is recorded on every resolution):
- `company_tickers_exchange.json` — CIK, registrant name, ticker, exchange for every SEC-registered
  listed company, used to MATCH the name the article wrote to a registrant (CIK). It is a
  CURRENT-DAY map: it does not say what a ticker IS (Alphabet's row lists GOOGL, GOOG, GOOGM and
  GOOGN — the last two are depositary shares of convertible PREFERRED stock) nor WHEN it was
  registered (GOOGM/GOOGN were registered in June 2026).
- `submissions/CIK##########.json` — the registrant's filings: forms 20-F / 40-F mark a foreign
  private issuer (its US line is an ADR / secondary listing, NEVER substituted for the primary);
  the periodic filings and 8-A12B registrations drive the point-in-time check below.
- the COVER PAGE of the registrant's latest periodic filing (10-K / 10-Q / 20-F / 40-F) filed on or
  before the article's as-of date — its inline-XBRL `dei:TradingSymbol` / `dei:Security12bTitle` /
  `dei:SecurityExchangeName` facts are the issuer's own statement of every security registered
  under Section 12(b) at that time, with its title.

POINT-IN-TIME RULE. A company's EXPOSURE listings are the common-equity lines on that as-of cover
page (`pit_status VERIFIED`, `instrument common_equity`). Everything else is kept for the audit in
`other_securities` and never presented as the company's stock: preferred / depositary-preferred
shares and notes on the cover (VERIFIED, with their class), and current-map tickers absent from it
(`NOT_REGISTERED_AS_OF` — or `UNVERIFIED` when an 8-A12B registration fell between the cover-page
filing and the as-of date, so the cover cannot decide). When no cover page can be read, the
current-map tickers are kept but marked UNVERIFIED, and an UNVERIFIED listing never counts as a
verified exposure — a current-day mapping never enters a historical basket unverified.

Rules: a model-supplied ticker / issuer hint is only a LOOKUP KEY — it resolves nothing unless the
SEC registrant name it points to matches the name as written. A name matching several registrants
is AMBIGUOUS. No match is UNRESOLVED (or PRIVATE when the entity was classified as a private
company and no SEC-listed registrant matches).

IDENTITY BEFORE TICKER. A registered ticker proves a security exists, not that it is the company the
source means. Two checks run before the point-in-time listing check (found 2026-10-11: "Delta", an
SOFC competitor whose extraction hint was 2308 — Delta Electronics' Taiwan code — had resolved to
DAL, Delta Air Lines, on the bare prefix "delta"):
- a hint that names a listing the SEC data does not hold (a foreign code: 2308, SIE, 6501) says
  the company is listed elsewhere: a PARTIAL name match to some SEC registrant is then refused —
  only the registrant's exact name is accepted;
- the BUSINESS the source describes FOR THIS COMPANY (its role — what it does, never the quote's
  wording: "Merck's late-stage pipeline" is not an oil pipeline, 2026-10-14) must be compatible
  with the issuer's SEC industry (SIC). A clear incompatibility — fuel cells against "Air
  Transportation, Scheduled" — leaves the entity UNRESOLVED with both stated. The compatibility
  table is generous (an internet retailer's SIC is compatible with a cloud context; an industrial
  or electrical-equipment issuer with a software one, since industrial automation is sold as
  software), so it vetoes only what is plainly another business; with no business stated, or no
  SIC on file, nothing is vetoed.

A PARTIAL NAME NEEDS BACKING (2026-10-14: "Schneider" resolved to Schneider National, a trucking
firm; "Delta" described as an AI-rack power supplier to Delta Air Lines). A name that only
partly matches a registrant resolves only when something confirms it is that company: an
SEC-listed ticker hint naming the same registrant, the registrant's exact name, or the business
the source describes being the registrant's OWN industry. A private company is never listed by a
partial name, with or without a hint.

THE INDUSTRY A COMPANY SERVES IS NOT ITS OWN (2026-10-14: GE, "jet engines for commercial
aviation", refused as an airline; Thermo Fisher, "tools sold to pharmaceutical companies", as a
drug maker). The business is read without its customer clause ("… for …", "… sold to …",
"… supplying …"); "aviation" is not an airline and "pipeline" is oil and gas only when the oil or
gas is named. The check still refuses a plainly different OWN business ("oil pipeline operator"
for Merck).
"""

from __future__ import annotations

import hashlib
import html as htmllib
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

from vinci.netcache import CachedHttp, HttpError
from vinci.theme_intelligence.config import USER_AGENT
from vinci.theme_intelligence.schemas import (
    EntityType,
    InstrumentClass,
    Listing,
    Mention,
    PitStatus,
    ResolutionStatus,
    SecurityResolution,
)
from vinci.theme_intelligence.verify import norm_name

TICKERS_EXCHANGE = "https://www.sec.gov/files/company_tickers_exchange.json"
TICKERS_MF = "https://www.sec.gov/files/company_tickers_mf.json"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SUBMISSIONS_PAGE = "https://data.sec.gov/submissions/{name}"
ARCHIVE_DOC = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_MAJOR = ("NYSE", "Nasdaq", "CBOE", "NYSE American", "NYSE Arca")
PERIODIC_FORMS = frozenset({"10-K", "10-Q", "20-F", "40-F", "10-K/A", "10-Q/A", "20-F/A",
                            "40-F/A", "10-KT", "10-QT"})
REGISTRATION_FORMS = frozenset({"8-A12B", "8-A12B/A"})
_FOREIGN_FORMS = frozenset({"20-F", "40-F"})  # a foreign private issuer's annual report
_COVER_TAGS = ("dei:TradingSymbol", "dei:Security12bTitle", "dei:SecurityExchangeName")
_IX = re.compile(r"<ix:nonnumeric\b([^>]*)>(.*?)</ix:nonnumeric>", re.I | re.S)


def _tokens(s: str) -> list[str]:
    return norm_name(s).split()


#: strong product / industry terms → a business family (face-validity table, never tuned)
_FAMILY_TERMS: dict[str, re.Pattern[str]] = {k: re.compile(v, re.I) for k, v in {
    "power_equipment": r"fuel[- ]cells?|\bsofc\b|solid[- ]oxide|gas turbines?|turbines?\b|"
                       r"transformers?\b|switchgear|reciprocating engines?|gas engines?|"
                       r"generators?\b|inverters?|electrical equipment|power equipment|"
                       r"grid equipment|power solutions?",
    "utilities_power": r"\butilit(?:y|ies)\b|power producer|nuclear power|\bppas?\b|"
                       r"power purchase|independent power|ratepayers?|electric(?:ity)? "
                       r"suppl(?:y|ier)",
    "oil_gas": r"midstream|(?:oil|gas|crude|ngl|natural gas|products) pipelines?\b|"
               r"pipeline (?:operator|compan(?:y|ies)|networks?)|\blng\b|natural gas producer|"
               r"oil producer|upstream|refin(?:er|ery|ing)|drilling",
    "semis_hardware": r"semiconductors?|\bchips?\b|\bgpus?\b|accelerators?|\bdram\b|"
                      r"\bnand\b|\bhbm\b|foundr(?:y|ies)|wafers?|\bservers?\b|"
                      r"networking equipment|optical (?:modules?|components?)",
    "software_internet": r"software|\bsaas\b|\bcloud\b|hyperscalers?|search engine|"
                         r"social media|online advertising|internet",
    "airlines": r"airlines?|air carriers?|passenger flights?",
    "transport": r"railroads?|trucking|shipping lines?|freight|logistics",
    "financials": r"\bbanks?\b|lenders?|insurers?|asset managers?|brokerages?",
    "healthcare": r"pharmaceuticals?|\bdrugs?\b|biotech|hospitals?|medical devices?",
    "materials": r"\bmining\b|miners?\b|copper|lithium|\bsteel\b|aluminium|aluminum|"
                 r"chemicals?\b|cement",
    "autos": r"automakers?|carmakers?|\bev makers?\b|vehicle makers?",
    "real_estate": r"\breits?\b|real estate|propert(?:y|ies) developer",
    "consumer": r"retailers?|apparel|restaurants?|consumer goods|beverages?",
    "telecom": r"telecom|wireless carriers?|fiber network",
}.items()}

#: what each family the SOURCE describes may plausibly be, as an ISSUER family (generous)
_COMPATIBLE: dict[str, frozenset[str]] = {
    "power_equipment": frozenset({"power_equipment", "industrials", "semis_hardware",
                                  "utilities_power", "oil_gas"}),
    "utilities_power": frozenset({"utilities_power", "power_equipment", "oil_gas",
                                  "industrials"}),
    "oil_gas": frozenset({"oil_gas", "utilities_power", "power_equipment", "industrials",
                          "materials"}),
    "semis_hardware": frozenset({"semis_hardware", "software_internet", "power_equipment",
                                 "industrials", "telecom"}),
    # industrial automation is sold as software, and the SEC's industry code lags the business:
    # Emerson, now an automation-software company, is still filed under SIC 3600 (electrical
    # equipment) — a "software" description refused it (operator, 2026-10-14)
    "software_internet": frozenset({"software_internet", "semis_hardware", "telecom",
                                    "consumer", "industrials", "power_equipment"}),
    "airlines": frozenset({"airlines", "transport"}),
    "transport": frozenset({"transport", "airlines", "industrials"}),
    "financials": frozenset({"financials", "real_estate"}),
    "healthcare": frozenset({"healthcare"}),
    "materials": frozenset({"materials", "oil_gas", "industrials"}),
    "autos": frozenset({"autos", "industrials", "power_equipment", "semis_hardware"}),
    "real_estate": frozenset({"real_estate", "financials"}),
    "consumer": frozenset({"consumer", "software_internet"}),
    "telecom": frozenset({"telecom", "software_internet", "semis_hardware"}),
}


#: a CUSTOMER clause: what follows names the industry served, not the company's own. "to" only
#: after a supplying word — an infinitive "to" introduces the company's OWN business ("expected
#: to sell fuel cells"), and cutting there left nothing for the identity check to read
_SERVED = re.compile(
    r"\b(?:for|serving|supplying|used by|(?:supplier|suppliers|supplies|supply|sells?|selling|"
    r"sold|provides?|providing|provider|vendor|exposed|exposure|leases?|leasing)\s+to)\b.*$",
    re.I | re.S)


def context_families(text: str) -> set[str]:
    """The business families a source passage describes, by strong terms only — read without its
    customer clause ("jet engines for commercial aviation" describes an engine maker)."""
    own = _SERVED.sub("", text or "")
    return {fam for fam, rx in _FAMILY_TERMS.items() if rx.search(own)}


def sic_families(sic: int | None) -> set[str]:
    """An issuer's business family from its SEC SIC code (ranges of the standard SIC divisions);
    empty when unknown — an unknown SIC vetoes nothing."""
    if sic is None:
        return set()
    out: set[str] = set()
    ranges = (
        (1000, 1099, "materials"), (1300, 1399, "oil_gas"), (1400, 1499, "materials"),
        (1500, 1799, "industrials"), (2000, 2399, "consumer"), (2400, 2799, "materials"),
        (2800, 2829, "materials"), (2830, 2836, "healthcare"), (2840, 2899, "materials"),
        (2900, 2999, "oil_gas"), (3000, 3399, "materials"), (3400, 3499, "industrials"),
        (3510, 3519, "power_equipment"), (3520, 3569, "industrials"),
        (3570, 3579, "semis_hardware"), (3580, 3599, "industrials"),
        (3600, 3629, "power_equipment"), (3630, 3659, "consumer"),
        (3660, 3679, "semis_hardware"), (3680, 3699, "power_equipment"),
        (3710, 3716, "autos"), (3720, 3799, "industrials"), (3810, 3839, "semis_hardware"),
        (3840, 3851, "healthcare"), (3852, 3999, "consumer"), (4000, 4499, "transport"),
        (4500, 4599, "airlines"), (4600, 4699, "oil_gas"), (4700, 4799, "transport"),
        (4800, 4899, "telecom"), (4900, 4919, "utilities_power"), (4920, 4925, "oil_gas"),
        (4926, 4999, "utilities_power"), (5000, 5199, "industrials"), (5200, 5960, "consumer"),
        (5912, 5912, "healthcare"),  # drug stores (CVS): a pharmacy is a healthcare business
        (5961, 5961, "software_internet"), (5961, 5961, "consumer"), (5962, 5999, "consumer"),
        (6000, 6499, "financials"), (6500, 6553, "real_estate"), (6700, 6797, "financials"),
        (6798, 6798, "real_estate"), (6799, 6799, "financials"), (7000, 7359, "consumer"),
        (7370, 7379, "software_internet"), (7380, 7999, "consumer"), (8000, 8099, "healthcare"),
        (8100, 8999, "industrials"))
    for lo, hi, fam in ranges:
        if lo <= sic <= hi:
            out.add(fam)
    return out


def identity_conflict(context: str, sic: int | None,
                      sic_description: str | None) -> str | None:
    """Why the issuer cannot be the company the source describes — or None (no conflict, or not
    decidable: no business stated, or no SIC on file)."""
    ctx = context_families(context)
    issuer = sic_families(sic)
    if not ctx or not issuer:
        return None
    allowed = set().union(*(_COMPATIBLE[f] for f in ctx))
    if issuer & allowed:
        return None
    return (f"the source describes {' / '.join(sorted(ctx)).replace('_', ' ')} business; the "
            f"issuer's SEC industry is SIC {sic} {sic_description or ''}".rstrip()
            + f" ({' / '.join(sorted(issuer)).replace('_', ' ')}) — not the same company")


def instrument_of(title: str | None) -> InstrumentClass:
    """What a registered line IS, from the issuer's own title — preferred and debt checked first,
    so "Depositary Shares … Convertible Preferred Stock" is never read as common equity."""
    if not title:
        return InstrumentClass.UNKNOWN
    t = title.lower()
    if "preferred" in t or "preference" in t:
        return InstrumentClass.PREFERRED
    if re.search(r"\bnotes?\b|\bdebentures?\b|\bbonds?\b|\bdue\s+(?:19|20)\d{2}\b", t):
        return InstrumentClass.DEBT
    if "warrant" in t or re.search(r"\brights?\b", t):
        return InstrumentClass.WARRANT_OR_RIGHT
    if re.search(r"\bunits?\b", t) and "common unit" not in t:
        return InstrumentClass.UNIT
    if "depositary" in t or "depository" in t:
        # an ADS of ordinary / common shares; a bare "Depositary Shares" (Duke Energy tags its
        # preferred depositary line exactly so) does not say what it represents — never guessed
        if re.search(r"american\s+depositar|ordinary|common", t):
            return InstrumentClass.DEPOSITARY_RECEIPT
        return InstrumentClass.UNKNOWN
    if re.search(r"common\s+(?:stock|shares?|units?)|capital\s+stock|ordinary\s+shares?|"
                 r"class\s+[a-z]\s+(?:shares?|stock)|shares\s+of\s+beneficial\s+interest", t):
        return InstrumentClass.COMMON_EQUITY
    return InstrumentClass.UNKNOWN


def norm_exchange(name: str | None) -> str | None:
    if not name:
        return None
    n = name.lower()
    if "nasdaq" in n:
        return "Nasdaq"
    if "arca" in n:
        return "NYSE Arca"
    if "american" in n:
        return "NYSE American"
    if "new york stock exchange" in n or n.strip() == "nyse":
        return "NYSE"
    if "cboe" in n:
        return "CBOE"
    return name.strip()


def norm_symbol(sym: str) -> str:
    """One spelling for a symbol written two ways: cover pages write preferred lines "DUK PR A" /
    "ORCL PRD" where the SEC ticker map writes "DUK-PA" / "ORCL-PD"."""
    s = re.sub(r"\s+", " ", sym.upper().strip())
    m = re.fullmatch(r"([A-Z]+)[\s.\-]*PR[\s.\-]*([A-Z])", s)
    if m:
        return f"{m.group(1)}-P{m.group(2)}"
    return re.sub(r"[\s.]+", "-", s)


@dataclass(frozen=True)
class CoverLine:
    symbol: str | None
    title: str | None
    exchange: str | None


def parse_cover(doc_html: str) -> list[CoverLine]:
    """Cover-page securities from an inline-XBRL periodic filing, grouped by XBRL context (each
    registered class carries its own context)."""
    by_ctx: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for m in _IX.finditer(doc_html):
        attrs = m.group(1)
        nm = re.search(r'\bname="([^"]+)"', attrs)
        if not nm or nm.group(1) not in _COVER_TAGS:
            continue
        ctx_m = re.search(r'\bcontextref="([^"]+)"', attrs, re.I)
        ctx = ctx_m.group(1) if ctx_m else "?"
        text = " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split())
        if ctx not in by_ctx:
            by_ctx[ctx] = {}
            order.append(ctx)
        by_ctx[ctx].setdefault(nm.group(1), text)
    out: list[CoverLine] = []
    for ctx in order:
        d = by_ctx[ctx]
        sym = d.get("dei:TradingSymbol")
        if sym and sym.strip().lower() in ("n/a", "none", "-"):
            sym = None
        if sym:  # the filing's own typography ("“CBRE”") is not part of the symbol
            sym = sym.strip().strip("\"'“”‘’").strip()
        out.append(CoverLine(symbol=sym.upper() if sym else None,
                             title=d.get("dei:Security12bTitle"),
                             exchange=d.get("dei:SecurityExchangeName")))
    return out


@dataclass
class PitCover:
    form: str
    filed: date
    accession: str
    url: str
    lines: list[CoverLine]
    #: 8-A12B registrations filed after the cover-page filing and on or before the as-of date
    later_registrations: list[tuple[str, date, str]] = field(default_factory=list)

    @property
    def ref(self) -> str:
        return f"{self.form} filed {self.filed.isoformat()} (accession {self.accession}) cover page"


@dataclass
class SecIndex:
    by_ticker: dict[str, tuple[str, str, str]]  # ticker -> (cik10, name, exchange)
    by_cik: dict[str, list[tuple[str, str]]]  # cik10 -> [(ticker, exchange)]
    names: dict[str, str]  # cik10 -> registrant name
    funds: dict[str, str]  # fund ticker -> cik10
    #: when the SEC files were fetched (the older of the two maps) — None when the HTTP layer
    #: holds no fetch time; never the day they were read from the cache
    retrieved: date | None


class SecResolver:
    def __init__(self, cache_dir: Path, *, http: CachedHttp | None = None) -> None:
        self._http = http or CachedHttp(cache_dir=cache_dir, user_agent=USER_AGENT,
                                        min_interval_sec=0.15, max_retries=4, timeout_sec=60.0,
                                        namespace="sec")
        self._index: SecIndex | None = None
        self._subs: dict[str, dict[str, Any]] = {}
        #: why a registrant's submissions could not be read — remembered for this resolver's run
        #: (every lookup re-paid the whole retry ladder: an SEC outage stretched a scan to hours),
        #: and never read as "no data": a partial name whose filings were not read is refused
        #: as unchecked (a cached None had switched the identity check off, 2026-10-14)
        self.sub_errors: dict[str, str] = {}
        self._rows: dict[tuple[str, date], list[tuple[str, date, str, str]]] = {}
        self._covers: dict[tuple[str, date], tuple[PitCover | None, str]] = {}

    def index(self) -> SecIndex:
        if self._index is not None:
            return self._index
        ex = cast(dict[str, Any], self._http.get_json(TICKERS_EXCHANGE, ttl_seconds=7 * 86_400.0))
        mf = cast(dict[str, Any], self._http.get_json(TICKERS_MF, ttl_seconds=7 * 86_400.0))
        fields = ex["fields"]
        ic, inm, it, iex = (fields.index(k) for k in ("cik", "name", "ticker", "exchange"))
        by_ticker: dict[str, tuple[str, str, str]] = {}
        by_cik: dict[str, list[tuple[str, str]]] = {}
        names: dict[str, str] = {}
        for row in ex["data"]:
            cik = str(row[ic]).zfill(10)
            tick = str(row[it]).upper()
            exch = str(row[iex] or "")
            by_ticker[tick] = (cik, str(row[inm]), exch)
            by_cik.setdefault(cik, []).append((tick, exch))
            names[cik] = str(row[inm])
        mfields = mf["fields"]
        fc, fs = mfields.index("cik"), mfields.index("symbol")
        funds = {str(r[fs]).upper(): str(r[fc]).zfill(10) for r in mf["data"]}
        stamps = [self._http.fetched_at(u) for u in (TICKERS_EXCHANGE, TICKERS_MF)]
        retrieved = (datetime.fromtimestamp(min(s for s in stamps if s is not None), tz=UTC).date()
                     if all(s is not None for s in stamps) else None)
        self._index = SecIndex(by_ticker, by_cik, names, funds, retrieved)
        return self._index

    def submissions(self, cik10: str) -> dict[str, Any] | None:
        if cik10 in self.sub_errors:
            return None  # failed once this run: not asked again
        if cik10 not in self._subs:
            try:
                self._subs[cik10] = cast(dict[str, Any], self._http.get_json(
                    SUBMISSIONS.format(cik=cik10), ttl_seconds=86_400.0))
            except HttpError as exc:
                self.sub_errors[cik10] = str(exc)
                return None
        return self._subs[cik10]

    def is_foreign_private_issuer(self, cik10: str, *, as_of: date) -> bool | None:
        """Whether the issuer files as a foreign private issuer AS OF `as_of`: its latest
        periodic report on or before that date is a 20-F / 40-F (an amendment restates an earlier
        period, so it does not decide). None when the submissions cannot be read or hold no
        periodic report by then. (2026-10-14: any 20-F / 40-F among the recent filings refused
        Enbridge — a 40-F filer to 2017, a 10-K filer since 2018 — at every date.)"""
        if self.submissions(cik10) is None:
            return None
        periodic = [(d, f) for f, d, _a, _p in self._filing_rows(cik10, as_of)
                    if f in PERIODIC_FORMS and not f.endswith("/A") and d <= as_of]
        if not periodic:
            return None
        return max(periodic)[1] in _FOREIGN_FORMS

    def _filing_rows(self, cik10: str, as_of: date) -> list[tuple[str, date, str, str]]:
        """(form, filing date, accession, primary document) — recent first, then older pages
        until one periodic filing on or before `as_of` is in hand. Walked once per registrant and
        date: the foreign-filer check, the cover page and enrichment read the same rows."""
        if (cik10, as_of) not in self._rows:
            self._rows[(cik10, as_of)] = self._walk_filings(cik10, as_of)
        return self._rows[(cik10, as_of)]

    def _walk_filings(self, cik10: str, as_of: date) -> list[tuple[str, date, str, str]]:
        sub = self.submissions(cik10)
        if sub is None:
            return []
        rows = _rows(sub.get("filings", {}).get("recent", {}))
        if any(f in PERIODIC_FORMS and d <= as_of for f, d, _a, _p in rows):
            return rows
        for page in sub.get("filings", {}).get("files", []):
            frm = page.get("filingFrom")
            if frm and date.fromisoformat(frm) > as_of:
                continue
            try:
                older = cast(dict[str, Any], self._http.get_json(
                    SUBMISSIONS_PAGE.format(name=page["name"]), ttl_seconds=30 * 86_400.0))
            except (HttpError, KeyError):
                break
            rows += _rows(older)
            if any(f in PERIODIC_FORMS and d <= as_of for f, d, _a, _p in rows):
                break
        return rows

    def pit_cover(self, cik10: str, as_of: date) -> tuple[PitCover | None, str]:
        """The cover page of the latest periodic filing on or before `as_of`, or (None, why)."""
        key = (cik10, as_of)
        if key in self._covers:
            return self._covers[key]
        rows = self._filing_rows(cik10, as_of)
        periodic = sorted(((f, d, a, p) for f, d, a, p in rows
                           if f in PERIODIC_FORMS and d <= as_of and p),
                          key=lambda r: r[1], reverse=True)
        result: tuple[PitCover | None, str]
        if not rows:
            result = (None, "SEC submissions unavailable")
        elif not periodic:
            result = (None, f"no periodic filing on or before {as_of.isoformat()} in the SEC "
                            f"submissions index")
        else:
            form, filed, acc, doc = periodic[0]
            url = ARCHIVE_DOC.format(cik=int(cik10), acc=acc.replace("-", ""), doc=doc)
            try:
                lines = parse_cover(self._http.get_text(url, ttl_seconds=None))
            except HttpError as exc:
                lines = []
                result = (None, f"cover page of {form} {acc} not retrievable: {exc}")
            else:
                if not any(ln.symbol for ln in lines):
                    result = (None, f"{form} filed {filed.isoformat()} ({acc}) carries no tagged "
                                    f"cover-page trading symbols")
                else:
                    later = [(f, d, a) for f, d, a, _p in rows
                             if f in REGISTRATION_FORMS and filed < d <= as_of]
                    result = (PitCover(form, filed, acc, url, lines, later), "")
        self._covers[key] = result
        return result

    # -- resolution -------------------------------------------------------------------------------
    def sic(self, cik10: str) -> tuple[int | None, str | None]:
        sub = self.submissions(cik10)
        if not sub:
            return None, None
        raw = str(sub.get("sic") or "").strip()
        return (int(raw) if raw.isdigit() else None), (sub.get("sicDescription") or None)

    def resolve(self, m: Mention, *, as_of: date) -> SecurityResolution:
        idx = self.index()
        now = datetime.now(tz=UTC)
        mapref = (f"SEC ticker map retrieved {idx.retrieved.isoformat()} (name match only)"
                  if idx.retrieved else "SEC ticker map, retrieval date not recorded (name match "
                                        "only)")

        def res(status: ResolutionStatus, method: str, listings: tuple[Listing, ...] = (),
                cik: str | None = None, registrant: str | None = None, note: str = "",
                other: tuple[Listing, ...] = (), source_ref: str = mapref) -> SecurityResolution:
            # the id hashes EVERY field the stored record carries (its time aside): one name
            # resolved two ways in one run ("Citi" with hint C, refused as another issuer's; and
            # without a hint, refused on identity) is two records — never one id with two
            # payloads, which the append-only store refuses and which failed the whole article
            rid = "SR-" + hashlib.sha256(
                f"{m.normalized_name}|{status}|{cik}|{[x.ticker for x in listings]}|"
                f"{[(x.ticker, x.pit_status.value) for x in other]}|{idx.retrieved}|"
                f"{as_of}|{method}|{registrant}|{note}|{source_ref}".encode()).hexdigest()[:14]
            return SecurityResolution(resolution_id=rid, normalized_name=m.normalized_name,
                                      status=status, listings=listings, cik=cik,
                                      registrant=registrant, method=method,
                                      source_ref=source_ref, resolved_at=now, note=note,
                                      other_securities=other)

        if m.entity_type is EntityType.INDEX:
            return res(ResolutionStatus.INDEX, "entity is an index — not a security")
        if m.entity_type in (EntityType.PRODUCT, EntityType.GOVERNMENT_OR_AGENCY,
                             EntityType.BASKET, EntityType.SECTOR):
            return res(ResolutionStatus.NOT_A_SECURITY, f"entity type {m.entity_type.value}")
        if m.entity_type is EntityType.ETF_OR_FUND:
            # the ticker printed in the fund's own name, or right after it; else the only fund
            # ticker printed — the FIRST of several picked another fund ("…(SOXX) and the VanEck
            # Semiconductor ETF (SMH)" resolved VanEck to SOXX)
            name_t = re.findall(r"\(([A-Z]{2,6})\)", m.name_as_written)
            spelled = r"\s+".join(re.escape(w) for w in m.name_as_written.split())
            beside = re.findall(rf"(?i:{spelled})\s*\(([A-Z]{{2,6}})\)", m.quote)
            printed = list(dict.fromkeys(t for t in re.findall(
                r"\(([A-Z]{2,6})\)", m.name_as_written + " " + m.quote) if t in idx.funds))
            own = [t for t in (*name_t, *beside) if t in idx.funds]
            pick = own[0] if own else printed[0] if len(printed) == 1 else None
            if pick is not None:
                return res(ResolutionStatus.FUND, "ticker printed by the source + SEC fund "
                           "ticker map", (Listing(ticker=pick, exchange=None,
                                                  note="fund/ETF share class",
                                                  instrument=InstrumentClass.FUND_SHARE),),
                           cik=idx.funds[pick])
            if len(printed) > 1:
                return res(ResolutionStatus.AMBIGUOUS, "several fund tickers printed",
                           note=f"the source prints {', '.join(printed)} and none beside "
                                f"{m.name_as_written!r} — which one is not said")
            return res(ResolutionStatus.UNRESOLVED, "fund named without a verifiable ticker")

        written = _tokens(m.name_as_written)
        cands: dict[str, str] = {}
        method = ""
        hint = (m.ticker_hint or "").strip().upper()
        # a hint naming a listing the SEC data does not hold = the company is listed elsewhere
        foreign_hint = bool(hint) and hint not in idx.by_ticker and hint not in idx.funds
        hinted: str | None = None  # the registrant an SEC-listed hint names, when the name differs
        hint_backed = False  # the name and an SEC-listed ticker hint name the same registrant
        issuer_backed = False  # the model's issuer hint picked one registrant by its exact name
        if m.ticker_hint and m.ticker_hint.upper() in idx.by_ticker:
            cik, name, _ = idx.by_ticker[m.ticker_hint.upper()]
            if written and _prefix_match(written, _tokens(name)):
                cands[cik] = name
                method = "model ticker hint verified against SEC registrant name"
                hint_backed = True
            elif written == [hint.lower()]:  # "GE", hint GE: the name as written is the ticker
                cands[cik] = name
                method = "the name as written is the SEC-listed ticker the hint names"
                hint_backed = True
            else:
                hinted = name
        if not cands and written:
            for cik, name in idx.names.items():
                if _prefix_match(written, _tokens(name)):
                    cands[cik] = name
            method = "SEC registrant-name prefix match"
            if len(cands) > 1 and m.issuer_name_hint:
                ihint = _tokens(m.issuer_name_hint)
                narrowed = {c: n for c, n in cands.items() if _tokens(n) == ihint}
                if len(narrowed) == 1:
                    cands = narrowed
                    issuer_backed = True
                    method += " narrowed by the model's issuer hint (exact registrant name)"
            if foreign_hint and cands:
                exact = {c: n for c, n in cands.items() if _tokens(n) == written}
                if not exact:
                    return res(ResolutionStatus.UNRESOLVED,
                               method + "; refused — the hint names a non-SEC listing",
                               note=f"the extraction's hint {hint!r} is not an SEC-listed "
                                    f"ticker (a listing elsewhere); "
                                    f"{m.name_as_written!r} only partially matches "
                                    + "; ".join(sorted(cands.values())[:3])
                                    + " — a partial name is not identity: not resolved")
                cands = exact
                method += " (exact registrant name; the hint names a non-SEC listing)"
            if hinted and cands and all(_tokens(n)[:1] != _tokens(hinted)[:1]
                                        for n in cands.values()):
                # the hint names one SEC issuer, the name partly matches ANOTHER business: two
                # identities (2026-10-14: "Citi", hint C — Citigroup — had resolved to Citi
                # Trends, CTRN). One family stays one ("Entergy Louisiana", hint ETR, Entergy)
                return res(ResolutionStatus.UNRESOLVED,
                           method + "; refused — the hint names another SEC issuer",
                           note=f"the extraction's hint {hint!r} is {hinted}'s ticker, which "
                                f"{m.name_as_written!r} does not name; the name only partially "
                                f"matches " + "; ".join(sorted(cands.values())[:3])
                                + " — two identities: not resolved")
        if m.entity_type is EntityType.PRIVATE_COMPANY and cands:
            # the source's classification stands against a PARTIAL name — on every path, a
            # ticker hint's included: only the registrant's exact name overrides it (2026-10-14:
            # "Cognition", the private AI lab behind Devin, had resolved to Cognition
            # Therapeutics, CGTX — and still did when the extraction hinted CGTX)
            exact = {c: n for c, n in cands.items() if _tokens(n) == written}
            if not exact:
                return res(ResolutionStatus.UNRESOLVED,
                           method + "; refused — the source names a private company",
                           note=f"{m.name_as_written!r} is classified as a private company "
                                f"and only partially matches "
                                + "; ".join(sorted(cands.values())[:3])
                                + " — a partial name is not identity: not resolved")
            cands = exact
            method += " (exact registrant name; classified as a private company)"
        # what the source says THIS company does — its role, never the quote's wording ("Merck's
        # late-stage pipeline" read as oil and gas; 2026-10-14)
        described = m.role_detail
        if len(cands) > 1 and context_families(described):
            # choosing between registrants: an issuer whose own industry IS among the described
            # businesses first (the generous table is for vetoes — it lets a brewer through a
            # sentence that names cloud customers); else the only one not in conflict
            fams = context_families(described)
            fit = {c: n for c, n in cands.items() if sic_families(self.sic(c)[0]) & fams}
            if len(fit) != 1:
                fit = {c: n for c, n in cands.items()
                       if identity_conflict(described, *self.sic(c)) is None
                       and sic_families(self.sic(c)[0])}
            if len(fit) == 1:
                cands = fit
                method += "; narrowed by the source's described business (SEC SIC)"
        if len(cands) > 1:
            return res(ResolutionStatus.AMBIGUOUS, method,
                       note="matches " + "; ".join(f"{n} (CIK {c})" for c, n in
                                                   sorted(cands.items())[:8])
                       + (f" (showing 8 of {len(cands)})" if len(cands) > 8 else ""))
        if not cands:
            if m.entity_type is EntityType.PRIVATE_COMPANY:
                return res(ResolutionStatus.PRIVATE, "no SEC-listed registrant matches; the "
                                                     "entity was classified as a private company")
            return res(ResolutionStatus.UNRESOLVED, "no SEC-listed registrant matches the name")

        cik, name = next(iter(cands.items()))
        sic, sic_desc = self.sic(cik)
        conflict = identity_conflict(described, sic, sic_desc)
        if conflict:
            return res(ResolutionStatus.UNRESOLVED, method + "; identity refused",
                       note=f"{m.name_as_written!r} → {name} (CIK {cik}) refused: {conflict}"
                            + (f"; the extraction's hint {hint!r} names a listing the SEC "
                               f"data does not hold" if foreign_hint else ""))
        unread = self.sub_errors.get(cik)
        if unread is not None and _tokens(name) != written:
            # the business it files under was not read: a partial name is never resolved unchecked
            return res(ResolutionStatus.UNRESOLVED,
                       method + "; refused — identity not checked",
                       note=f"{m.name_as_written!r} only partially matches {name} (CIK {cik}), "
                            f"whose SEC submissions could not be read this run ({unread}) — "
                            f"the business it files under was not checked: not resolved")
        # a PARTIAL name needs backing: the hint, the exact name, or the company's own industry
        own_industry = bool(sic_families(sic) & context_families(described))
        if not (hint_backed or issuer_backed or _tokens(name) == written or own_industry):
            return res(ResolutionStatus.UNRESOLVED,
                       method + "; refused — a partial name with nothing confirming it",
                       note=f"{m.name_as_written!r} only partially matches {name} (CIK {cik}), "
                            f"and no SEC-listed ticker hint, exact name or the business the "
                            f"source describes confirms it is that company — a partial name is "
                            f"not identity: not resolved")
        if sic is not None:
            method += f"; identity checked against the issuer's SEC industry (SIC {sic})"
        current = sorted(idx.by_cik.get(cik, []), key=lambda x: (x[1] not in _MAJOR, x[0]))
        fpi = self.is_foreign_private_issuer(cik, as_of=as_of)
        if fpi:
            return res(ResolutionStatus.UNRESOLVED, method + "; issuer files 20-F/40-F",
                       cik=cik, registrant=name,
                       note=("foreign private issuer — its US line(s) "
                             f"{[t for t, _e in current]} are ADR/secondary listings; the "
                             "primary listing is not resolved here and the ADR is NOT "
                             "substituted"))
        cover, why = self.pit_cover(cik, as_of)
        if cover is None:
            listings = tuple(Listing(
                ticker=t, exchange=e or None, pit_status=PitStatus.UNVERIFIED,
                note=f"current SEC ticker map only — point-in-time registration not verifiable "
                     f"({why}); never use in a historical basket") for t, e in current)
            if not any((x.exchange or "") in _MAJOR for x in listings):
                return res(ResolutionStatus.UNRESOLVED, method, (), cik, name,
                           note="only OTC/unlisted lines in the SEC map", other=listings)
            return res(ResolutionStatus.LISTED_EQUITY, method, (), cik, name,
                       note=f"listing NOT point-in-time verified as of {as_of.isoformat()}: "
                            f"{why}" + ("" if fpi is False else
                                        "; foreign-issuer check unavailable"),
                       other=listings)
        pit_ref = f"SEC {cover.ref} — registered securities as of {as_of.isoformat()}"
        equity: list[Listing] = []
        other: list[Listing] = []
        on_cover: set[str] = set()
        for ln in cover.lines:
            if not ln.symbol:
                continue
            on_cover.add(norm_symbol(ln.symbol))
            inst = instrument_of(ln.title)
            lst = Listing(ticker=ln.symbol, exchange=norm_exchange(ln.exchange),
                          security_class=ln.title, instrument=inst,
                          pit_status=PitStatus.VERIFIED, pit_source=cover.ref)
            (equity if inst is InstrumentClass.COMMON_EQUITY else other).append(
                lst if inst is InstrumentClass.COMMON_EQUITY else lst.model_copy(update={
                    "note": f"{inst.value.replace('_', ' ')} — not the company's common equity"}))
        for t, e in current:
            if norm_symbol(t) in on_cover:
                continue
            if cover.later_registrations:
                status, note = PitStatus.UNVERIFIED, (
                    f"absent from the {cover.ref}, but {len(cover.later_registrations)} 8-A12B "
                    f"registration(s) fell between it and {as_of.isoformat()} — undecidable here")
            else:
                status, note = PitStatus.NOT_REGISTERED_AS_OF, (
                    f"absent from the {cover.ref} and no 8-A12B registration before "
                    f"{as_of.isoformat()} — first registered after the as-of date")
            other.append(Listing(ticker=t, exchange=e or None, pit_status=status, note=note))
        if not equity:
            return res(ResolutionStatus.UNRESOLVED, method + "; point-in-time cover page", (),
                       cik, name, note=f"no common equity among the securities registered on "
                                       f"the {cover.ref}", other=tuple(other), source_ref=pit_ref)
        if len(equity) > 1:
            equity = [x.model_copy(update={"note": f"one of {len(equity)} common-equity classes "
                                                   f"registered as of {as_of.isoformat()}"})
                      for x in equity]
        return res(ResolutionStatus.LISTED_EQUITY, method + "; point-in-time cover page",
                   tuple(equity), cik, name, other=tuple(other), source_ref=pit_ref,
                   note="" if fpi is False else "foreign-issuer check unavailable")


def _rows(block: dict[str, Any]) -> list[tuple[str, date, str, str]]:
    forms = block.get("form", [])
    dates = block.get("filingDate", [])
    accs = block.get("accessionNumber", [])
    docs = block.get("primaryDocument", [""] * len(forms))
    out: list[tuple[str, date, str, str]] = []
    for f, d, a, p in zip(forms, dates, accs, docs, strict=False):
        try:
            out.append((str(f), date.fromisoformat(str(d)), str(a), str(p)))
        except ValueError:
            continue
    return out


def _prefix_match(written: list[str], registrant: list[str]) -> bool:
    """The written name is the leading token sequence of the registrant name ("meta" ⊑ "meta
    platforms"), or equal after normalisation ("amazon com" for "Amazon.com, Inc.")."""
    if not written or len(written) > len(registrant):
        return False
    return registrant[: len(written)] == written
