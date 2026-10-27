"""The US entity resolver — CIK ↔ ticker ↔ name → a stable internal id, **fail-loud on ambiguity**.

Two-level model (production-correct): an **issuer** (keyed by SEC CIK) owns one or more
**securities** (ticker + share class). Dual-class names (GOOGL/GOOG) are several securities under
one issuer; that distinction matters because you *price* a security but read *fundamentals* for an
issuer.

Resolution is deterministic and refuses to guess: an unknown ticker raises
:class:`UnknownSymbolError`; a ticker (or name) that maps to more than one issuer raises
:class:`AmbiguousResolutionError`. Mis-resolution is the system's worst failure, so this is the
component hardened hardest.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import date
from typing import Any, cast

from pydantic import BaseModel

from vinci.config import Config, get_config
from vinci.edgar.submissions import parse_former_names
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver.errors import (
    AmbiguousResolutionError,
    ResolutionError,
    UnknownSymbolError,
)
from vinci.resolver.index import (
    ResolverIndex,
    normalize_name,
    normalize_ticker,
    pad_cik,
    share_class_of,
    to_eod_symbol,
)
from vinci.resolver.instrument import RegisteredLine, latest_periodic, registered_line
from vinci.schemas.data_record import Identity

_CT_URL = "https://www.sec.gov/files/company_tickers.json"
_CTE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_ARCHIVE_DOC = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_ONE_DAY = 86_400.0

# SEC exchange strings → ISO 10383 MIC. Unknown venues resolve to None (still identifiable).
_MIC: dict[str, str] = {
    "Nasdaq": "XNAS",
    "NYSE": "XNYS",
    "NYSE American": "XASE",
    "Cboe": "XCBO",
    "CBOE": "XCBO",
    "OTC": "OTCM",
}


class ResolvedIssuer(BaseModel, frozen=True):
    """An issuer (CIK) and the securities it owns."""

    issuer_id: str
    cik: str
    name: str
    securities: tuple[Identity, ...]
    sic: str | None = None
    sic_description: str | None = None
    former_names: tuple[str, ...] = ()


class EntityResolver:
    """Resolves US tickers/CIKs/names to a stable :class:`Identity` / :class:`ResolvedIssuer`."""

    def __init__(
        self,
        *,
        http: CachedHttp | None = None,
        index: ResolverIndex | None = None,
        config: Config | None = None,
    ) -> None:
        self._http = http
        self._index = index
        self._cfg = config or get_config()

    @classmethod
    def from_config(cls, config: Config | None = None) -> EntityResolver:
        """Build a network-backed resolver with a SEC-polite cached HTTP client."""
        from vinci.sec import build_sec_http

        cfg = config or get_config()
        return cls(http=build_sec_http(cfg), config=cfg)

    # --- index --------------------------------------------------------------------------------
    @property
    def index(self) -> ResolverIndex:
        if self._index is None:
            if self._http is None:
                raise RuntimeError("EntityResolver has no injected index and no HTTP client")
            ct = self._http.get_json(_CT_URL, ttl_seconds=_ONE_DAY)
            cte = self._http.get_json(_CTE_URL, ttl_seconds=_ONE_DAY)
            self._index = ResolverIndex.from_sec_files(ct, cte)
        return self._index

    # --- universe iteration -------------------------------------------------------------------
    def iter_universe(self, exchanges: Iterable[str]) -> Iterator[Identity]:
        """Yield an :class:`Identity` for every cleanly-resolvable security on ``exchanges``.

        The seed for the cap-band universe builder. Ambiguous/unknown tickers are skipped (not a
        clean universe member); the band/coverage filtering happens downstream.
        """
        wanted = set(exchanges)
        for tic in self.index.all_tickers():
            try:
                ident = self.resolve_ticker(tic)
            except ResolutionError:
                continue
            if ident.exchange in wanted:
                yield ident

    # --- resolution ---------------------------------------------------------------------------
    def resolve_ticker(self, ticker: str, *, enrich: bool = False) -> Identity:
        """Resolve a ticker to a security :class:`Identity`. Fail loud on unknown/ambiguous."""
        norm = normalize_ticker(ticker)
        if not norm:
            raise UnknownSymbolError("empty ticker")
        ciks = self.index.ticker_ciks(norm)
        if not ciks:
            raise UnknownSymbolError(f"no US issuer for ticker {ticker!r} (renamed/delisted?)")
        if len(ciks) > 1:
            raise AmbiguousResolutionError(
                f"ticker {ticker!r} maps to multiple CIKs {sorted(ciks)} — refusing to guess"
            )
        cik = next(iter(ciks))
        exchange = self._exchange_for(norm)
        name = self.index.issuer_name(cik) or norm
        identity = self._make_identity(cik=cik, sec_ticker=norm, exchange=exchange, name=name)
        if enrich:
            sic, sic_desc = self.sic_for(cik)
            identity = identity.model_copy(update={"sic": sic, "sic_description": sic_desc})
        return identity

    def resolve_cik(self, cik: int | str, *, enrich: bool = False) -> ResolvedIssuer:
        """Resolve a CIK to its issuer and all its securities."""
        cik10 = pad_cik(cik)
        entries = self.index.cik_entries(cik10)
        if not entries:
            raise UnknownSymbolError(f"no issuer for CIK {cik!r}")
        name = self.index.issuer_name(cik10) or cik10
        # one Identity per distinct ticker, preferring an entry that carries an exchange
        securities: list[Identity] = []
        for tic in sorted({e.ticker for e in entries}):
            securities.append(
                self._make_identity(
                    cik=cik10, sec_ticker=tic, exchange=self._exchange_for(tic), name=name
                )
            )
        issuer = ResolvedIssuer(
            issuer_id=f"ISS-{cik10}",
            cik=cik10,
            name=name,
            securities=tuple(securities),
        )
        if enrich:
            issuer = self._enrich_issuer(issuer)
        return issuer

    def resolve_name(self, name: str, *, enrich: bool = False) -> ResolvedIssuer:
        """Resolve an exact (normalised) issuer name. Fail loud on no-match / collision."""
        norm = normalize_name(name)
        ciks = self.index.name_ciks(norm)
        if not ciks:
            raise UnknownSymbolError(f"no issuer named {name!r} (exact normalised match)")
        if len(ciks) > 1:
            raise AmbiguousResolutionError(
                f"name {name!r} matches multiple CIKs {sorted(ciks)} — refusing to guess"
            )
        return self.resolve_cik(next(iter(ciks)), enrich=enrich)

    # --- submissions enrichment (SIC for G2; former names for hardening) ----------------------
    def submissions(self, cik: int | str) -> dict[str, Any]:
        if self._http is None:
            raise RuntimeError("submissions enrichment requires an HTTP client")
        cik10 = pad_cik(cik)
        data = self._http.get_json(_SUBMISSIONS_URL.format(cik=cik10), ttl_seconds=_ONE_DAY)
        return cast(dict[str, Any], data)

    def sic_for(self, cik: int | str) -> tuple[str | None, str | None]:
        """(SIC code, description) — the operating-co universe gate's structural fact.

        BOTH HALVES ARE NORMALISED TO None WHEN ABSENT, here at the SOURCE rather than in each
        caller (review of #528). EDGAR returns `sicDescription: ""` — an empty STRING, not null —
        for a SIC-less issuer; observed live on FSK, a BDC. That blank is not cosmetic downstream:
        `Store.upsert_security` COALESCEs `sic_description`, and SQL COALESCE treats '' as PRESENT,
        so a blank OVERWRITES a stored description instead of deferring to it — re-opening on the
        sibling column the erasure #523 closed. Normalising in the one place every consumer reads
        (`resolve_ticker(enrich=True)`, `_enrich_issuer`, `build_universe`, `vinci refresh`, the
        backfill script) is what stops the next consumer repeating it, which #528's first draft did
        until a live run caught it.
        """
        d = self.submissions(cik)
        sic = str(d["sic"]) if d.get("sic") else None
        return sic, (d.get("sicDescription") or None)

    def registered_line(self, cik: int | str, ticker: str, as_of: date) -> RegisteredLine | None:
        """How the issuer's latest cover page filed on or before ``as_of`` registers ``ticker`` —
        the instrument check the reference feed's ``type`` cannot make (see
        :mod:`vinci.resolver.instrument`).

        None when there is nothing to read: no periodic report in the recent submissions, a cover
        that does not carry the symbol, or a document the SEC would not serve. None changes
        nothing for the caller — a line is excluded only on what its issuer's cover SAYS, never on
        a cover that could not be read (the same retreat as `share_class_counts`: one bad lookup
        must not end a build, and an unread cover is no evidence the line is debt)."""
        cik10 = pad_cik(cik)
        filing = latest_periodic(self.submissions(cik10), as_of)
        if filing is None:
            return None
        form, filed, acc, doc = filing
        if self._http is None:
            raise RuntimeError("cover-page reading requires an HTTP client")
        url = _ARCHIVE_DOC.format(cik=int(cik10), acc=acc.replace("-", ""), doc=doc)
        try:
            html = self._http.get_text(url, ttl_seconds=None)   # a filed document never changes
        except HttpError:
            return None
        return registered_line(html, ticker, form=form, filed=filed, accession=acc)

    # --- internals ----------------------------------------------------------------------------
    def _exchange_for(self, norm_ticker: str) -> str | None:
        for e in self.index.ticker_entries(norm_ticker):
            if e.exchange:
                return e.exchange
        return None

    def _make_identity(
        self, *, cik: str, sec_ticker: str, exchange: str | None, name: str
    ) -> Identity:
        return Identity(
            internal_id=f"SEC-{cik}-{sec_ticker}",
            issuer_id=f"ISS-{cik}",
            cik=cik,
            ticker=sec_ticker,
            mic=_MIC.get(exchange or "", "") or "XXXX",
            exchange=exchange or "UNKNOWN",
            eod_symbol=to_eod_symbol(sec_ticker),
            name=name,
            share_class=share_class_of(sec_ticker),
        )

    def _enrich_issuer(self, issuer: ResolvedIssuer) -> ResolvedIssuer:
        d = self.submissions(issuer.cik)
        sic = str(d["sic"]) if d.get("sic") else None
        # ONE parse of the formerNames array, shared with EdgarClient.registrant_history — this
        # path had its own inline comprehension, and two parsers of one source is the twin-drift
        # class (review, #558): a change to either skip rule would have landed in only one, and
        # the dossier's rename caveat could then disagree with the resolved issuer record.
        former = tuple(fn.name for fn in parse_former_names(d))
        # same '' → None rule as `sic_for`; this path reads the payload directly, so it cannot
        # inherit the normalisation and has to state it.
        sic_desc = d.get("sicDescription") or None
        secs = tuple(
            s.model_copy(update={"sic": sic, "sic_description": sic_desc})
            for s in issuer.securities
        )
        return issuer.model_copy(
            update={
                "sic": sic,
                "sic_description": sic_desc,
                "former_names": former,
                "securities": secs,
            }
        )
