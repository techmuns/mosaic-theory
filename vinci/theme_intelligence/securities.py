"""Resolve source-named entities to securities from SEC primary data — verified, never guessed.

Sources (SEC, cached; the retrieval date is recorded on every resolution):
- `company_tickers_exchange.json` — CIK, registrant name, ticker, exchange for every SEC-registered
  listed company; one CIK can carry several tickers (share classes) and ALL are kept: "Alphabet"
  resolves to the issuer with GOOGL and GOOG listed, because the article names the company, not a
  share class.
- `company_tickers_mf.json` — fund / ETF ticker map (no names), used ONLY when the source itself
  prints the ticker ("iShares ... ETF (IGV)").
- `submissions/CIK##########.json` — filer forms: an issuer filing 20-F / 40-F is a foreign private
  issuer, so its US line is an ADR / secondary listing and is NEVER substituted for the primary
  listing (status UNRESOLVED with the US line recorded as a note).

Rules: a model-supplied ticker / issuer hint is only a LOOKUP KEY — it resolves nothing unless the
SEC registrant name it points to matches the name as written. A name matching several registrants
is AMBIGUOUS. No match is UNRESOLVED (or PRIVATE when the entity was classified as a private
company and no SEC-listed registrant matches). The SEC map is CURRENT at retrieval, not
point-in-time — that limitation is written onto every resolution for replay runs.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

from vinci.netcache import CachedHttp, HttpError
from vinci.theme_intelligence.config import USER_AGENT
from vinci.theme_intelligence.schemas import (
    EntityType,
    Listing,
    Mention,
    ResolutionStatus,
    SecurityResolution,
)
from vinci.theme_intelligence.verify import norm_name

TICKERS_EXCHANGE = "https://www.sec.gov/files/company_tickers_exchange.json"
TICKERS_MF = "https://www.sec.gov/files/company_tickers_mf.json"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
_MAJOR = ("NYSE", "Nasdaq", "CBOE", "NYSE American", "NYSE Arca")


def _tokens(s: str) -> list[str]:
    return norm_name(s).split()


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
        self._fpi: dict[str, bool | None] = {}

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

    def is_foreign_private_issuer(self, cik10: str) -> bool | None:
        if cik10 in self._fpi:
            return self._fpi[cik10]
        try:
            sub = cast(dict[str, Any], self._http.get_json(SUBMISSIONS.format(cik=cik10),
                                                           ttl_seconds=30 * 86_400.0))
        except HttpError:
            self._fpi[cik10] = None
            return None
        forms = set(sub.get("filings", {}).get("recent", {}).get("form", []))
        fpi = bool(forms & {"20-F", "40-F", "20-F/A", "40-F/A"})
        self._fpi[cik10] = fpi
        return fpi

    # -- resolution -------------------------------------------------------------------------------
    def resolve(self, m: Mention, *, as_of: date) -> SecurityResolution:
        idx = self.index()
        now = datetime.now(tz=UTC)
        pit = (f"SEC ticker map retrieved {idx.retrieved.isoformat()} (current, not point-in-time"
               + (f"; run as-of {as_of.isoformat()})" if idx.retrieved > as_of else ")"))

        def res(status: ResolutionStatus, method: str, listings: tuple[Listing, ...] = (),
                cik: str | None = None, registrant: str | None = None,
                note: str = "") -> SecurityResolution:
            rid = "SR-" + hashlib.sha256(
                f"{m.normalized_name}|{status}|{cik}|{[x.ticker for x in listings]}|"
                f"{idx.retrieved}|{as_of}".encode()).hexdigest()[:14]
            return SecurityResolution(resolution_id=rid, normalized_name=m.normalized_name,
                                      status=status, listings=listings, cik=cik,
                                      registrant=registrant, method=method, source_ref=pit,
                                      resolved_at=now, note=note)

        if m.entity_type is EntityType.INDEX:
            return res(ResolutionStatus.INDEX, "entity is an index — not a security")
        if m.entity_type in (EntityType.PRODUCT, EntityType.GOVERNMENT_OR_AGENCY,
                             EntityType.BASKET):
            return res(ResolutionStatus.NOT_A_SECURITY, f"entity type {m.entity_type.value}")
        if m.entity_type is EntityType.ETF_OR_FUND:
            stated = re.findall(r"\(([A-Z]{2,6})\)", m.name_as_written + " " + m.quote)
            for t in stated:
                if t in idx.funds:
                    return res(ResolutionStatus.FUND, "ticker printed by the source + SEC fund "
                               "ticker map", (Listing(ticker=t, exchange=None,
                                                       note="fund/ETF share class"),),
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
        if len(cands) == 1:
            cik, name = next(iter(cands.items()))
            tickers = idx.by_cik.get(cik, [])
            listings = tuple(Listing(ticker=t, exchange=e or None,
                                     note=None if len(tickers) == 1 else "one of "
                                     f"{len(tickers)} tickers the SEC map lists for this "
                                     "registrant — the map does not state the security type "
                                     "(share class, note or other listed security)")
                             for t, e in sorted(tickers, key=lambda x: (x[1] not in _MAJOR, x[0])))
            fpi = self.is_foreign_private_issuer(cik)
            if fpi:
                return res(ResolutionStatus.UNRESOLVED, method + "; issuer files 20-F/40-F",
                           cik=cik, registrant=name,
                           note=("foreign private issuer — its US line(s) "
                                 f"{[x.ticker for x in listings]} are ADR/secondary listings; the "
                                 "primary listing is not resolved here and the ADR is NOT "
                                 "substituted"))
            if not any((x.exchange or "") in _MAJOR for x in listings):
                return res(ResolutionStatus.UNRESOLVED, method, listings, cik, name,
                           note="only OTC/unlisted lines in the SEC map")
            return res(ResolutionStatus.LISTED_EQUITY, method, listings, cik, name,
                       note="" if fpi is False else "foreign-issuer check unavailable")
        if len(cands) > 1:
            return res(ResolutionStatus.AMBIGUOUS, method,
                       note="matches " + "; ".join(f"{n} (CIK {c})" for c, n in
                                                   sorted(cands.items())[:8])
                       + (f" (showing 8 of {len(cands)})" if len(cands) > 8 else ""))
        if m.entity_type is EntityType.PRIVATE_COMPANY:
            return res(ResolutionStatus.PRIVATE, "no SEC-listed registrant matches; the entity "
                                                 "was classified as a private company")
        return res(ResolutionStatus.UNRESOLVED, "no SEC-listed registrant matches the name")


def _prefix_match(written: list[str], registrant: list[str]) -> bool:
    """The written name is the leading token sequence of the registrant name ("meta" ⊑ "meta
    platforms"), or equal after normalisation ("amazon com" for "Amazon.com, Inc.")."""
    if not written or len(written) > len(registrant):
        return False
    return registrant[: len(written)] == written
