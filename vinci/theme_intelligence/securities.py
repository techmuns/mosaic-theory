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
_COVER_TAGS = ("dei:TradingSymbol", "dei:Security12bTitle", "dei:SecurityExchangeName")
_IX = re.compile(r"<ix:nonnumeric\b([^>]*)>(.*?)</ix:nonnumeric>", re.I | re.S)


def _tokens(s: str) -> list[str]:
    return norm_name(s).split()


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
        out.append(CoverLine(symbol=sym.strip().upper() if sym else None,
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
    retrieved: date


class SecResolver:
    def __init__(self, cache_dir: Path, *, http: CachedHttp | None = None) -> None:
        self._http = http or CachedHttp(cache_dir=cache_dir, user_agent=USER_AGENT,
                                        min_interval_sec=0.15, max_retries=4, timeout_sec=60.0,
                                        namespace="sec")
        self._index: SecIndex | None = None
        self._subs: dict[str, dict[str, Any] | None] = {}
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
        self._index = SecIndex(by_ticker, by_cik, names, funds, datetime.now(tz=UTC).date())
        return self._index

    def submissions(self, cik10: str) -> dict[str, Any] | None:
        if cik10 not in self._subs:
            try:
                self._subs[cik10] = cast(dict[str, Any], self._http.get_json(
                    SUBMISSIONS.format(cik=cik10), ttl_seconds=86_400.0))
            except HttpError:
                self._subs[cik10] = None
        return self._subs[cik10]

    def is_foreign_private_issuer(self, cik10: str) -> bool | None:
        sub = self.submissions(cik10)
        if sub is None:
            return None
        forms = set(sub.get("filings", {}).get("recent", {}).get("form", []))
        return bool(forms & {"20-F", "40-F", "20-F/A", "40-F/A"})

    def _filing_rows(self, cik10: str, as_of: date) -> list[tuple[str, date, str, str]]:
        """(form, filing date, accession, primary document) — recent first, then older pages
        until one periodic filing on or before `as_of` is in hand."""
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
    def resolve(self, m: Mention, *, as_of: date) -> SecurityResolution:
        idx = self.index()
        now = datetime.now(tz=UTC)
        mapref = f"SEC ticker map retrieved {idx.retrieved.isoformat()} (name match only)"

        def res(status: ResolutionStatus, method: str, listings: tuple[Listing, ...] = (),
                cik: str | None = None, registrant: str | None = None, note: str = "",
                other: tuple[Listing, ...] = (), source_ref: str = mapref) -> SecurityResolution:
            rid = "SR-" + hashlib.sha256(
                f"{m.normalized_name}|{status}|{cik}|{[x.ticker for x in listings]}|"
                f"{[(x.ticker, x.pit_status.value) for x in other]}|{idx.retrieved}|"
                f"{as_of}".encode()).hexdigest()[:14]
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
            stated = re.findall(r"\(([A-Z]{2,6})\)", m.name_as_written + " " + m.quote)
            for t in stated:
                if t in idx.funds:
                    return res(ResolutionStatus.FUND, "ticker printed by the source + SEC fund "
                               "ticker map", (Listing(ticker=t, exchange=None,
                                                       note="fund/ETF share class",
                                                       instrument=InstrumentClass.FUND_SHARE),),
                               cik=idx.funds[t])
            return res(ResolutionStatus.UNRESOLVED, "fund named without a verifiable ticker")

        written = _tokens(m.name_as_written)
        cands: dict[str, str] = {}
        method = ""
        if m.ticker_hint and m.ticker_hint.upper() in idx.by_ticker:
            cik, name, _ = idx.by_ticker[m.ticker_hint.upper()]
            if written and _prefix_match(written, _tokens(name)):
                cands[cik] = name
                method = "model ticker hint verified against SEC registrant name"
        if not cands and written:
            for cik, name in idx.names.items():
                if _prefix_match(written, _tokens(name)):
                    cands[cik] = name
            method = "SEC registrant-name prefix match"
            if len(cands) > 1 and m.issuer_name_hint:
                hint = _tokens(m.issuer_name_hint)
                narrowed = {c: n for c, n in cands.items() if _tokens(n) == hint}
                if len(narrowed) == 1:
                    cands = narrowed
                    method += " narrowed by the model's issuer hint (exact registrant name)"
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
        current = sorted(idx.by_cik.get(cik, []), key=lambda x: (x[1] not in _MAJOR, x[0]))
        fpi = self.is_foreign_private_issuer(cik)
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
