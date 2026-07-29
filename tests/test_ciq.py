"""Step 3a verification — the CIQ Business Relationships parser (synthetic, deterministic)."""

from __future__ import annotations

from collections.abc import Iterator

from vinci.ciq import ManualDataStore, load_ciq_edges, parse_relationships
from vinci.ciq.relationships import _parse_entity
from vinci.resolver import EntityResolver, RawEntry, ResolverIndex

_CUSTOMERS_VIEW = "\n".join(
    [
        "Customize View|",
        "Recently Disclosed Customers|",
        "Customer Name|Supplier Name|Relationship Type|Primary Industry|Source|",
        "Acme Corp (NasdaqGS:ACME)|Focal Inc. (NYSE:FOC)|Customer|Tech|Acme 2025 Form 10-K|",
        "Business Description: irrelevant|",
        "Beta Ltd (TSE:1234)|Focal Inc. (NYSE:FOC)|Supplier|Mfg|Beta Form Doc|",
        "*Private Mfg Co|Focal Inc. (NYSE:FOC)|Distributor|Industrials|Private Doc|",
        "Bank Co (NYSE:BNK)|Focal Inc. (NYSE:FOC)|Creditor|Banks|Bank Doc|",
    ]
)


def test_entity_parse_handles_ticker_private_and_star() -> None:
    assert _parse_entity("Acme Corp (NasdaqGS:ACME)") == ("Acme Corp", "NasdaqGS", "ACME")
    name, exch, tic = _parse_entity("*ACL Computers & Software, Inc.")
    assert tic is None and exch is None and name == "ACL Computers & Software, Inc."


def test_parse_relationships_identifies_view_and_focal() -> None:
    p = parse_relationships(_CUSTOMERS_VIEW)
    assert p is not None
    assert p.view == "customers"  # "Customer Name" first → focal is the supplier
    assert p.focal_ticker == "FOC"
    assert len(p.rows) == 4  # all rows parsed; the supply-chain filter happens in load_ciq_edges


def test_parse_relationships_returns_none_for_non_table() -> None:
    assert parse_relationships("just some text\nwith no header") is None


class _OneDocStore(ManualDataStore):
    def __init__(self, text: str) -> None:
        self._text = text

    def iter_documents(self) -> Iterator[tuple[str, str]]:
        yield "focal.rtf", self._text


def test_load_ciq_edges_filters_resolves_and_directs() -> None:
    resolver = EntityResolver(
        index=ResolverIndex(
            [RawEntry(cik="0000000001", name="Acme Corp", ticker="ACME", exchange="Nasdaq")]
        )
    )
    edges, stats = load_ciq_edges(_OneDocStore(_CUSTOMERS_VIEW), resolver)

    assert stats["dropped_non_supply_chain"] == 1  # the Creditor row is dropped
    assert {e.relationship_type for e in edges} == {"Customer", "Supplier", "Distributor"}
    by_name = {e.counterparty_name: e for e in edges}
    assert by_name["Acme Corp"].resolution == "resolved"  # US ticker resolves
    assert by_name["Acme Corp"].counterparty_internal_id == "SEC-0000000001-ACME"
    assert by_name["Acme Corp"].direction == "downstream"  # customers view: focal → customer
    assert by_name["Beta Ltd"].resolution == "non_us"  # TSE → not resolved
    assert by_name["Private Mfg Co"].resolution == "private"  # no ticker

def test_capital_structure_refuses_a_descending_export_rather_than_mislabel() -> None:
    """(the [-1] scan, 2026-07-28) `_capital_summary` reads `vcols[-1]` and stamps the figure
    "(latest quarter)". That was correct only because CIQ happens to export columns oldest-first —
    an UNASSERTED convention, and an unasserted convention is precisely how `source_ref="Close
    (latest)"` came to sit on a months-old value in three dossiers (item 20).

    DRIVES `_capital_summary` ITSELF, not the date helper. The first cut of this test asserted only
    on `_cs_col_date`, and deleting the entire refusal from the shipped function left it GREEN — a
    test whose name claims one thing while its assertion checks another, in the very PR about
    vacuous tests. Caught by mutation, which is the only thing that catches this.

    POSITIVE: ascending columns → PRESENT, and the value is read from the LATEST column.
    NEGATIVE: the same sheet reversed → UNKNOWN naming the ordering, rather than "(latest
    quarter)" stamped on the oldest column."""
    from vinci.dossier.ciq_sheets import _capital_summary
    from vinci.dossier.schemas import SourceStatus

    cols = ["3 months Sep-30-2025", "3 months Dec-31-2025", "3 months Mar-31-2026"]
    debts = ["100.0", "200.0", "300.0"]

    class _Stub:
        def __init__(self, headers: list[str], vals: list[str]) -> None:
            self.rows = [["Fiscal Period", *headers], ["Total Debt Outstanding", *vals]]

        def sheet(self, kind: str, name: str, *, freq: str | None = None) -> list[list[object]]:
            return self.rows

    ok = _capital_summary(_Stub(cols, debts))                       # type: ignore[arg-type]
    assert ok.status is SourceStatus.PRESENT, f"ascending export refused: {ok.note}"
    assert "300.0" in str(ok.value), (
        f"the LATEST column was not the one read — got {ok.value!r}")

    # the same data, exported newest-first: the last column is now the OLDEST
    bad = _capital_summary(_Stub(cols[::-1], debts[::-1]))          # type: ignore[arg-type]
    assert bad.status is not SourceStatus.PRESENT, (
        f"a descending export was accepted and stamped '(latest quarter)': {bad.value!r} — this "
        "is the false-provenance shape arriving through the data provider")
    assert "ascending" in str(bad.note or ""), (
        f"refused, but not for the ordering reason — note was {bad.note!r}")

    # a header naming no date degrades to "order unknown", never to a wrong pick
    from vinci.dossier.ciq_sheets import _cs_col_date

    assert _cs_col_date("LTM") is None and _cs_col_date("") is None
