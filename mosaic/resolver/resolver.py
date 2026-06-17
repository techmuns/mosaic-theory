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

from typing import Any, cast

from pydantic import BaseModel

from mosaic.config import Config, get_config, sec_user_agent
from mosaic.netcache import CachedHttp
from mosaic.resolver.errors import AmbiguousResolutionError, UnknownSymbolError
from mosaic.resolver.index import (
    ResolverIndex,
    normalize_name,
    normalize_ticker,
    pad_cik,
    share_class_of,
    to_eod_symbol,
)
from mosaic.schemas.data_record import Identity

_CT_URL = "https://www.sec.gov/files/company_tickers.json"
_CTE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
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
        cfg = config or get_config()
        cfg.ensure_dirs()
        http = CachedHttp(
            cache_dir=cfg.cache_dir,
            user_agent=sec_user_agent(),
            min_interval_sec=1.0 / cfg.pacing.sec_requests_per_sec,
            max_retries=cfg.pacing.max_retries,
            timeout_sec=cfg.pacing.http_timeout_sec,
            namespace="sec",
        )
        return cls(http=http, config=cfg)

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
        """(SIC code, description) — the pinned sector source for Screen-2 G2."""
        d = self.submissions(cik)
        sic = str(d["sic"]) if d.get("sic") else None
        return sic, d.get("sicDescription")

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
        former = tuple(fn["name"] for fn in d.get("formerNames", []) if fn.get("name"))
        secs = tuple(
            s.model_copy(update={"sic": sic, "sic_description": d.get("sicDescription")})
            for s in issuer.securities
        )
        return issuer.model_copy(
            update={
                "sic": sic,
                "sic_description": d.get("sicDescription"),
                "former_names": former,
                "securities": secs,
            }
        )
