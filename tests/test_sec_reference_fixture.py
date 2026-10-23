"""THE SEC TICKER-FILE SLICE — it covers the fleet, it stays a slice, and it keeps share classes.

WHY (2026-10-23). The maintenance pins (`tests/test_maintenance_path.py`,
`tests/test_maintenance_identity.py`) read SEC's `company_tickers.json` and
`company_tickers_exchange.json` through the resolver. On a fresh checkout `data/cache` is absent, so
they fetched both live inside `pytest -m "not network"`; with the network refused, 8 of 21 failed.
They now read `tests/fixtures/sec_reference/` (`scripts/build_sec_reference_fixture.py`), seeded by
`tests/sec_offline_support.py`. A slice can fall behind the fleet it serves, so this file pins that
it does not — and that it is still read with the resolver's real fail-loud semantics.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from tests.sec_offline_support import COMPANYFACTS, SEC_REFERENCE, no_network, seed_sec_cache
from vinci.config import Config
from vinci.resolver import EntityResolver, UnknownSymbolError
from vinci.resolver.index import ResolverIndex

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _index() -> ResolverIndex:
    return ResolverIndex.from_sec_files(
        json.loads((SEC_REFERENCE / "company_tickers.json").read_text()),
        json.loads((SEC_REFERENCE / "company_tickers_exchange.json").read_text()))


def _fleet() -> set[str]:
    """Derived independently of the builder: committed dossiers ∪ scenario records ∪ followed."""
    dossiers = {p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json")}
    records = {p.stem for p in (ROOT / "scenarios").glob("*.json") if not p.stem.startswith("_")}
    followed = set(json.loads((ROOT / "data" / "followed.json").read_text()))
    return dossiers | records | followed


def test_both_ticker_files_list_every_fleet_name() -> None:
    """Per FILE, not just through the index: the resolver merges the two files, so a name missing
    from one still resolves through the other and only this check sees the slice fall behind."""
    ct = json.loads((SEC_REFERENCE / "company_tickers.json").read_text())
    cte = json.loads((SEC_REFERENCE / "company_tickers_exchange.json").read_text())
    i_ticker = cte["fields"].index("ticker")
    for label, tickers in (("company_tickers.json", {r["ticker"] for r in ct.values()}),
                           ("company_tickers_exchange.json", {r[i_ticker] for r in cte["data"]})):
        missing = sorted(_fleet() - tickers)
        assert not missing, (
            f"{len(missing)} fleet name(s) missing from sec_reference/{label}: {missing}. Run "
            "`python scripts/build_sec_reference_fixture.py` in the SAME PR that adds the name.")


def test_the_slice_resolves_every_fleet_name() -> None:
    resolver = EntityResolver(index=_index())
    unresolved = []
    for name in sorted(_fleet()):
        try:
            resolver.resolve_ticker(name)
        except UnknownSymbolError:
            unresolved.append(name)
    assert not unresolved, (
        f"{len(unresolved)} fleet name(s) missing from tests/fixtures/sec_reference/: "
        f"{unresolved}. "
        "Run `python scripts/build_sec_reference_fixture.py` in the SAME PR that adds the name.")


def test_a_name_outside_the_fleet_fails_loud_rather_than_resolving() -> None:
    """A slice read through the real resolver: an absent name raises, it is never invented."""
    assert "MSFT" not in _fleet()
    with pytest.raises(UnknownSymbolError):
        EntityResolver(index=_index()).resolve_ticker("MSFT")


def test_a_fleet_issuer_keeps_every_share_class() -> None:
    """Sliced by CIK as well as ticker, so a dual-class issuer is whole: GOOG resolves to GOOGL's
    issuer, not to nothing — the two-level issuer/security model survives the slice."""
    resolver = EntityResolver(index=_index())
    assert resolver.resolve_ticker("GOOG").issuer_id == resolver.resolve_ticker("GOOGL").issuer_id


def test_a_seeded_cache_resolves_with_the_network_refused(tmp_path: pathlib.Path) -> None:
    """The maintenance pins' path: a Config-built resolver over a seeded cache, no network."""
    cfg = Config(data_dir=tmp_path)
    # the two ticker files plus one companyfacts entry per committed fixture file
    assert seed_sec_cache(cfg) == 2 + len(list(COMPANYFACTS.glob("*.json")))
    with no_network():
        ident = EntityResolver.from_config(cfg).resolve_ticker("GOOGL")
    assert ident.ticker == "GOOGL"


def test_an_unseeded_cache_fails_loud_instead_of_fetching(tmp_path: pathlib.Path) -> None:
    """The guard the pins rely on: nothing seeded, the resolver reaches for SEC and is refused."""
    with no_network(), pytest.raises(Exception, match="reached for the network"):
        EntityResolver.from_config(Config(data_dir=tmp_path)).resolve_ticker("GOOGL")
