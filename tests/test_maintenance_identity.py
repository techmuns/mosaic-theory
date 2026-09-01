"""The MAINTENANCE route must build on the store's ENRICHED identity, not the resolver's thin one.

Two routes reach a data record. The screen iterates ``store.iter_securities()`` directly
(``vinci/screens/run.py``), so every candidate record carries the SIC the universe build filled in
from the submissions payload. The maintenance route (a followed name, or one carrying a committed
dossier) called ``resolver.resolve_ticker`` instead — and the resolver's index is
``company_tickers.json``, which carries ticker / CIK / name / exchange and **nothing else**. So
``identity.sic`` came back ``None``, ``resolve_label(None).sector`` is ``"Unknown"``, and the page
rendered ``sector: Unknown`` for a name whose sector the entity master already knew.

Found on TECX's onboarding run (review of #558): the store row said SIC 2836, which resolves to
Health Care, while the committed dossier said Unknown — and
``tests/test_dossier_sector_coherence.py`` caught it, naming exactly that contradiction. Nothing
pinned the CAUSE, so this file does.

Both identities are the SAME ``Identity`` type, which is why the bug was invisible: the thin one
type-checks everywhere the enriched one does.
"""

from __future__ import annotations

import ast
import json
import pathlib
import tempfile
from datetime import date

import vinci.dossier.assemble as asm
from vinci.config import Config
from vinci.labels import resolve_label
from vinci.resolver import EntityResolver
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store import Store

REPO = pathlib.Path(__file__).resolve().parents[1]
ROOT = REPO / "vinci"
PRICE_FIXTURES = REPO / "tests" / "fixtures" / "prices"

#: The maintained name the BEHAVIOURAL pins run through, and the benchmark its record needs. Both
#: are in the committed price fixture (``scripts/build_price_fixture.py``), so the store dependency
#: that made `test_maintenance_path` CI-red for eleven merges does not come back here.
_NAME = "GOOGL"
_BENCH = "IWM"

#: A SIC the name does NOT have. The point of the pin is PROVENANCE — the record's SIC has to come
#: from the STORE ROW and nowhere else, so a value that only the temp store could have supplied is
#: the only one that proves it. 2836 is TECX's real SIC (the live case), and resolves to Health
#: Care; nothing is written to the real DB, which stays untouched.
_STORE_SIC = "2836"

#: Everything under ``data/`` the assembly legitimately reads — the resolver index and the EDGAR
#: cache above all. Symlinked, never copied: only the STORE is substituted.
_LINKED = ("dossiers", "snapshots", "cache", "manual", "monitor", "followed.json",
           "graph_coverage.json")


def _fixture_cfg(*, with_store_row: bool) -> tuple[Config, Identity]:
    """A Config whose store holds the fixture's bars and, optionally, an ENRICHED securities row.

    Not cached: the two behavioural pins differ only by whether that row exists, so sharing a
    store between them would make one depend on the other's ordering.
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="vinci-maint-identity-"))
    for name in _LINKED:
        src = REPO / "data" / name
        if src.exists():
            (tmp / name).symlink_to(src)
    cfg = Config(data_dir=tmp)
    ident = EntityResolver.from_config(cfg).resolve_ticker(_NAME)
    with Store(cfg.db_path) as store:
        for sym in (_NAME, _BENCH):
            store.write_prices([
                PriceBar(**json.loads(line))
                for line in (PRICE_FIXTURES / f"{sym}.jsonl").read_text().splitlines()
                if line.strip()
            ])
        if with_store_row:
            store.upsert_security(ident.model_copy(update={"sic": _STORE_SIC}))
    return cfg, ident


def _reference_date(cfg: Config, ident: Identity) -> date:
    """The store's own frontier — asserted against the store, never a literal, so it cannot rot."""
    with Store(cfg.db_path) as store:
        return store.get_price_history(ident.internal_id)[-1].bar_date


def _identity(ticker: str, *, sic: str | None) -> Identity:
    """Built from the REAL type — the same constructor both routes produce."""
    return Identity(
        internal_id=f"SEC-0001681087-{ticker}", issuer_id="ISS-0001681087", cik="0001681087",
        ticker=ticker, mic="XNAS", exchange="Nasdaq", eod_symbol=ticker,
        name="Tectonic Therapeutic, Inc.", sic=sic)


def test_the_enriched_identity_is_what_makes_the_sector_resolvable() -> None:
    """THE POSITIVE PIN. With the store's SIC the sector resolves; this is what the page prints."""
    enriched = _identity("TECX", sic="2836")
    label = resolve_label(enriched.sic)
    assert label.sector == "Health Care", label
    assert label.industry and label.industry != "Unknown"


def test_the_thin_identity_is_what_produced_unknown() -> None:
    """THE NEGATIVE PIN — the observed failure shape, kept so the bug cannot come back silently.

    A record built off the resolver's identity has no SIC, and the sector the page renders is
    therefore Unknown even though the entity master knows it. If this ever stops being true the
    fix above has been superseded and this file should be re-derived, not deleted."""
    thin = _identity("TECX", sic=None)
    assert thin.sic is None
    assert resolve_label(thin.sic).sector == "Unknown"


def test_the_stores_sic_reaches_the_assembled_record() -> None:
    """THE BEHAVIOURAL PIN — the fix's actual EFFECT, run through ``_standalone_record`` itself.

    The structural pin below only reads source text, so it stays GREEN on a mutation that calls
    ``get_security`` and then throws the answer away — which is the whole bug back again. This one
    reddens on it: the record's SIC is a value ONLY the temp store could have supplied, so its
    presence proves the store row reached the identity the record was built from.
    """
    cfg, ident = _fixture_cfg(with_store_row=True)
    assert ident.sic is None, (
        "the resolver has started returning a SIC — the premise of this file has changed, and the "
        "pin below no longer proves the value came from the STORE")

    rec = asm._standalone_record(cfg, _NAME, _reference_date(cfg, ident))

    assert rec.identity.sic == _STORE_SIC, (
        f"{_NAME}'s record carries sic={rec.identity.sic!r}, not the store row's {_STORE_SIC!r} — "
        "the maintenance route is building on the resolver's thin identity again")
    assert resolve_label(rec.identity.sic).sector == "Health Care"
    # ...and ONLY the SIC was taken. The store row is a snapshot of the last universe build that
    # touched the name, and an out-of-band maintained name is never re-upserted; the live resolver
    # index stays the authority on who the registrant IS.
    assert rec.identity.name == ident.name
    assert (rec.identity.exchange, rec.identity.mic) == (ident.exchange, ident.mic)


def test_without_a_store_row_the_record_falls_back_to_the_thin_identity() -> None:
    """THE NEGATIVE, run end-to-end: the observed failure shape, and the case the fallback exists
    for. A name can be followed before any universe build has seen it — no securities row — and it
    must still ASSEMBLE, with the honest ``Unknown`` rather than a raise or a guessed sector."""
    cfg, ident = _fixture_cfg(with_store_row=False)

    rec = asm._standalone_record(cfg, _NAME, _reference_date(cfg, ident))

    assert rec.identity.sic is None
    assert resolve_label(rec.identity.sic).sector == "Unknown"


def test_the_maintenance_route_reads_the_store_before_building_the_record() -> None:
    """The fix itself, pinned structurally too — cheap, and it names the ORDER constraint that the
    behavioural pin can only observe the consequence of. ``_standalone_record`` must consult
    ``store.get_security`` BEFORE the record is built; reading the store for BARS only, as it did,
    is what left the SIC behind."""
    src = (ROOT / "dossier" / "assemble.py").read_text()
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "_standalone_record")
    body = ast.unparse(fn)
    assert "get_security(" in body, (
        "_standalone_record no longer reads the store's security — a maintained name is being "
        "built off the resolver's thin identity again, and its sector will render Unknown")
    assert body.index("get_security(") < body.index("build_data_record("), (
        "the store lookup must happen BEFORE the record is built, or the enriched identity "
        "cannot reach it")


def test_the_screen_route_still_uses_the_store_directly() -> None:
    """The CONTROL. The screen was never broken — it iterates the store — and this fix must not
    have changed that. If this fails, the two routes have diverged in the other direction."""
    src = (ROOT / "screens" / "run.py").read_text()
    assert "store.iter_securities()" in src, (
        "the screen no longer iterates the store's securities — the route that was CORRECT has "
        "changed, and candidate records may now be missing their SIC too")
