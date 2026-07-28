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

    POSITIVE: ascending columns → the last column is the latest and the claim stands.
    NEGATIVE: a descending export → REFUSE, rather than stamp "(latest quarter)" on the oldest
    column. Uses the real ordering helper, so the pin binds the shipped check, not a copy."""
    from vinci.dossier.ciq_sheets import _cs_col_date

    asc = ["3 months Sep-30-2025", "3 months Dec-31-2025", "3 months Mar-31-2026"]
    desc = list(reversed(asc))
    a = [_cs_col_date(h) for h in asc]
    d = [_cs_col_date(h) for h in desc]
    assert all(x is not None for x in a), "the real headers must parse, or the guard sees nothing"
    assert a == sorted(a), "ascending headers must read as ascending"
    assert d != sorted(d), "a reversed export must be DETECTED as out of order"
    # the last column really is the latest only in the ascending case — the whole claim
    assert a[-1] == max(a) and d[-1] != max(d)
    # and a header naming no date degrades to None (order unknown), never to a wrong pick
    assert _cs_col_date("LTM") is None and _cs_col_date("") is None
