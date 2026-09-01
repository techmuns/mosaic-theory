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
import pathlib

from vinci.labels import resolve_label
from vinci.schemas.data_record import Identity

ROOT = pathlib.Path(__file__).resolve().parents[1] / "vinci"


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


def test_the_maintenance_route_reads_the_store_before_building_the_record() -> None:
    """The fix itself, pinned structurally rather than by re-running an assembly (which needs a
    populated DB and a network). ``_standalone_record`` must consult ``store.get_security`` and
    prefer its answer — reading the store for BARS only, as it did, is what left the SIC behind."""
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
