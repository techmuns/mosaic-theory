"""The resolver index — an in-memory map built from SEC's bulk reference files.

Built from two SEC files (both verified live):
- ``company_tickers.json``          → ``{ "0": {cik_str, ticker, title}, ... }``
- ``company_tickers_exchange.json`` → ``{ "fields": [...], "data": [[cik, name, ticker, exch]] }``

The index is the deterministic core: it normalises tickers, merges the two sources, and **records
any cross-source disagreement** (same ticker → different CIK) so the resolver can fail loud on that
exact ticker rather than silently picking one. Keeping the index pure (no I/O) makes the fail-loud
behaviour unit-testable without the network.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


def normalize_ticker(ticker: str) -> str:
    """Canonicalise a ticker to SEC's convention: upper-case, trimmed, dot→dash for class shares.

    SEC writes class shares with a dash (``BRK-B``); callers may type ``BRK.B``. We map ``.``→``-``
    so both resolve identically. (Polygon's dot convention is produced separately by
    :func:`to_eod_symbol`.)
    """
    return ticker.strip().upper().replace(".", "-")


def to_eod_symbol(sec_ticker: str) -> str:
    """SEC ticker → Polygon/EOD symbol. Polygon uses a dot for class shares (``BRK.B``)."""
    return sec_ticker.replace("-", ".")


def share_class_of(sec_ticker: str) -> str | None:
    """Best-effort share class from the dash convention (``BRK-B`` → ``"B"``); else None."""
    if "-" in sec_ticker:
        return sec_ticker.rsplit("-", 1)[1] or None
    return None


def normalize_name(name: str) -> str:
    """Loose-but-deterministic name key: upper-case, collapse whitespace, drop trailing punctuation.

    Used only for exact normalised-name matching with fail-loud on collisions — never fuzzy.
    """
    cleaned = " ".join(name.upper().split())
    return cleaned.rstrip(".,")


def pad_cik(cik: int | str) -> str:
    """SEC CIK as a 10-digit zero-padded string (the canonical form for data.sec.gov)."""
    return str(int(str(cik).lstrip("CIK").strip())).zfill(10)


@dataclass(frozen=True)
class RawEntry:
    """One (security, issuer) row after normalisation."""

    cik: str  # 10-digit
    name: str
    ticker: str  # SEC-normalised (dash)
    exchange: str | None


class ResolverIndex:
    """Deterministic ticker/CIK/name index with cross-source conflict detection."""

    def __init__(self, entries: Iterable[RawEntry]) -> None:
        self._by_ticker: dict[str, list[RawEntry]] = defaultdict(list)
        self._by_cik: dict[str, list[RawEntry]] = defaultdict(list)
        self._by_name: dict[str, set[str]] = defaultdict(set)  # norm name -> set of CIKs
        self._cik_name: dict[str, str] = {}
        seen: set[tuple[str, str, str | None]] = set()
        for e in entries:
            key = (e.ticker, e.cik, e.exchange)
            if key in seen:
                continue
            seen.add(key)
            self._by_ticker[e.ticker].append(e)
            self._by_cik[e.cik].append(e)
            self._by_name[normalize_name(e.name)].add(e.cik)
            self._cik_name.setdefault(e.cik, e.name)

    # --- construction -------------------------------------------------------------------------
    @classmethod
    def from_sec_files(
        cls, company_tickers: dict[str, Any], company_tickers_exchange: dict[str, Any]
    ) -> ResolverIndex:
        entries: list[RawEntry] = []
        # exchange file (authoritative for exchange)
        fields = company_tickers_exchange["fields"]
        i_cik, i_name = fields.index("cik"), fields.index("name")
        i_tic, i_exch = fields.index("ticker"), fields.index("exchange")
        for row in company_tickers_exchange["data"]:
            entries.append(
                RawEntry(
                    cik=pad_cik(row[i_cik]),
                    name=row[i_name],
                    ticker=normalize_ticker(row[i_tic]),
                    exchange=row[i_exch] or None,
                )
            )
        # primary file (cross-check + any tickers missing from the exchange file)
        for rec in company_tickers.values():
            entries.append(
                RawEntry(
                    cik=pad_cik(rec["cik_str"]),
                    name=rec["title"],
                    ticker=normalize_ticker(rec["ticker"]),
                    exchange=None,
                )
            )
        return cls(entries)

    # --- lookups (return raw matches; the resolver applies the fail-loud policy) ---------------
    def ticker_ciks(self, norm_ticker: str) -> set[str]:
        return {e.cik for e in self._by_ticker.get(norm_ticker, [])}

    def ticker_entries(self, norm_ticker: str) -> list[RawEntry]:
        return list(self._by_ticker.get(norm_ticker, []))

    def cik_entries(self, cik: str) -> list[RawEntry]:
        return list(self._by_cik.get(cik, []))

    def name_ciks(self, norm_name: str) -> set[str]:
        return set(self._by_name.get(norm_name, set()))

    def issuer_name(self, cik: str) -> str | None:
        return self._cik_name.get(cik)

    @property
    def n_tickers(self) -> int:
        return len(self._by_ticker)

    @property
    def n_ciks(self) -> int:
        return len(self._by_cik)
