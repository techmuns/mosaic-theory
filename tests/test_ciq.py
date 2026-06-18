"""Step 3a verification — the CIQ Business Relationships parser (synthetic, deterministic)."""

from __future__ import annotations

from collections.abc import Iterator

from mosaic.ciq import ManualDataStore, load_ciq_edges, parse_relationships
from mosaic.ciq.relationships import _parse_entity
from mosaic.resolver import EntityResolver, RawEntry, ResolverIndex

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
