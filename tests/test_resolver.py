"""Step 1 verification — the US entity resolver.

Two layers:
- **Unit tests** (no network) on a synthetic index — exercise the fail-loud paths deterministically
  (the real SEC snapshot happens to have zero ticker→multi-CIK collisions, so ambiguity must be
  injected to test the refusal).
- A **network test** (``-m network``) against the real SEC files — resolve a basket of known and
  tricky names, confirming CIKs, dual-class handling, and fail-loud on renamed/garbage input.
"""

from __future__ import annotations

import pytest

from mosaic.resolver import (
    AmbiguousResolutionError,
    EntityResolver,
    RawEntry,
    ResolverIndex,
    UnknownSymbolError,
    normalize_ticker,
    share_class_of,
    to_eod_symbol,
)

# --- synthetic index --------------------------------------------------------------------------
SYNTHETIC = [
    RawEntry(cik="0000320193", name="Apple Inc.", ticker="AAPL", exchange="Nasdaq"),
    RawEntry(cik="0001652044", name="Alphabet Inc.", ticker="GOOGL", exchange="Nasdaq"),
    RawEntry(cik="0001652044", name="Alphabet Inc.", ticker="GOOG", exchange="Nasdaq"),
    RawEntry(cik="0001067983", name="BERKSHIRE HATHAWAY INC", ticker="BRK-B", exchange="NYSE"),
    RawEntry(cik="0001067983", name="BERKSHIRE HATHAWAY INC", ticker="BRK-A", exchange="NYSE"),
    # injected ambiguity: one ticker, two issuers (ticker reuse)
    RawEntry(cik="0000000001", name="Reuse One Corp", ticker="ZZZZ", exchange="NYSE"),
    RawEntry(cik="0000000002", name="Reuse Two Corp", ticker="ZZZZ", exchange="Nasdaq"),
    # injected name collision: two CIKs normalising to the same name
    RawEntry(cik="0000000010", name="Twin Co", ticker="TWN1", exchange="NYSE"),
    RawEntry(cik="0000000011", name="Twin Co", ticker="TWN2", exchange="Nasdaq"),
]


@pytest.fixture
def resolver() -> EntityResolver:
    return EntityResolver(index=ResolverIndex(SYNTHETIC))


# --- normalization ----------------------------------------------------------------------------
def test_ticker_normalization() -> None:
    assert normalize_ticker(" brk.b ") == "BRK-B"
    assert normalize_ticker("aapl") == "AAPL"
    assert to_eod_symbol("BRK-B") == "BRK.B"  # Polygon's dot convention
    assert share_class_of("BRK-B") == "B"
    assert share_class_of("AAPL") is None


# --- happy path -------------------------------------------------------------------------------
def test_resolve_simple_ticker(resolver: EntityResolver) -> None:
    ident = resolver.resolve_ticker("AAPL")
    assert ident.cik == "0000320193"
    assert ident.internal_id == "SEC-0000320193-AAPL"
    assert ident.issuer_id == "ISS-0000320193"
    assert ident.mic == "XNAS"
    assert ident.eod_symbol == "AAPL"


def test_dual_class_same_issuer(resolver: EntityResolver) -> None:
    googl = resolver.resolve_ticker("GOOGL")
    goog = resolver.resolve_ticker("GOOG")
    assert googl.cik == goog.cik == "0001652044"
    assert googl.issuer_id == goog.issuer_id
    assert googl.internal_id != goog.internal_id  # distinct securities

    issuer = resolver.resolve_cik("0001652044")
    tickers = {s.ticker for s in issuer.securities}
    assert {"GOOGL", "GOOG"} <= tickers


def test_dotted_class_ticker_maps_to_dash(resolver: EntityResolver) -> None:
    ident = resolver.resolve_ticker("BRK.B")  # user types a dot
    assert ident.ticker == "BRK-B"
    assert ident.cik == "0001067983"
    assert ident.share_class == "B"
    assert ident.eod_symbol == "BRK.B"  # round-trips to Polygon convention


# --- fail loud --------------------------------------------------------------------------------
def test_unknown_ticker_fails_loud(resolver: EntityResolver) -> None:
    with pytest.raises(UnknownSymbolError):
        resolver.resolve_ticker("FB")  # renamed to META — must not silently mis-resolve
    with pytest.raises(UnknownSymbolError):
        resolver.resolve_ticker("NOTATICKER123")
    with pytest.raises(UnknownSymbolError):
        resolver.resolve_ticker("   ")


def test_ambiguous_ticker_fails_loud(resolver: EntityResolver) -> None:
    with pytest.raises(AmbiguousResolutionError):
        resolver.resolve_ticker("ZZZZ")  # maps to two CIKs


def test_ambiguous_name_fails_loud(resolver: EntityResolver) -> None:
    with pytest.raises(AmbiguousResolutionError):
        resolver.resolve_name("Twin Co")  # two issuers normalise to the same name


def test_resolve_name_exact(resolver: EntityResolver) -> None:
    issuer = resolver.resolve_name("Apple Inc.")
    assert issuer.cik == "0000320193"


def test_unknown_cik_fails_loud(resolver: EntityResolver) -> None:
    with pytest.raises(UnknownSymbolError):
        resolver.resolve_cik(999999999)


# --- network: real SEC files ------------------------------------------------------------------
@pytest.mark.network
def test_resolver_against_real_sec_data() -> None:
    r = EntityResolver.from_config()

    # known CIKs (stable) including dual-class and dotted class shares
    cases = {
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "NVDA": "0001045810",
        "GOOGL": "0001652044",
        "GOOG": "0001652044",
        "AMZN": "0001018724",
        "META": "0001326801",
        "BRK.B": "0001067983",
        "BRK.A": "0001067983",
    }
    for tic, expected_cik in cases.items():
        ident = r.resolve_ticker(tic)
        assert ident.cik == expected_cik, f"{tic} -> {ident.cik}, expected {expected_cik}"

    # dual-class: GOOGL and GOOG are the same issuer
    assert r.resolve_ticker("GOOGL").issuer_id == r.resolve_ticker("GOOG").issuer_id

    # recent ticker change: FB was renamed to META → must fail loud, never mis-resolve
    with pytest.raises(UnknownSymbolError):
        r.resolve_ticker("FB")
    # garbage input → fail loud
    with pytest.raises(UnknownSymbolError):
        r.resolve_ticker("NOTATICKER123")

    # SIC enrichment (the pinned sector source for Screen-2 G2)
    meta = r.resolve_ticker("META", enrich=True)
    assert meta.sic == "7370"
    assert meta.sic_description
