"""`vinci/ciq/` IS REMOVED, NOT LEFT DEAD (fix request 2: A-D13, A-D16, RBC-D7 = BC-D1 and BC-D2;
2026-11-10).

Document 15 asked of each: "no production caller: fix or remove". The package parsed CIQ's
Business-Relationships exports into supply-chain edges for graph Test 0, whose command left in
#905 (`3ad14793`). After that its only importers were `tests/test_ciq.py` and
`vinci/graph/extract.py`, which took the SUPPLY_CHAIN_TYPES taxonomy and nothing else (`rg` and
`git log -S load_ciq_edges`, 2026-11-10). Every defect TeamNostra reproduced in it went with it:
- A-D13: `manual.extract_text` read an OLE `.xls` as empty text;
- A-D16: a diagnostic PNG aborted the store's load;
- BC-D1: 4-column views were read by position;
- BC-D2: the focal group was read as its own counterparty;
- BC-D3, BC-D5 and BC-D6: a non-relationship document, a truncated view and a blank-type row;
- BC-D7's graph half: a former customer counted as current.

The live F27 reader, `vinci.dossier.ciq_sheets.customer_roster`, is untouched.
"""
from __future__ import annotations

import importlib.util

from vinci.graph import extract


def test_the_package_is_gone_and_nothing_imports_it() -> None:
    assert importlib.util.find_spec("vinci.ciq") is None


def test_the_graph_extractor_keeps_the_taxonomy_it_took_from_it() -> None:
    """The one value the package still served, byte for byte, and the direction map that
    asserts it covers the vocabulary still holds (`extract._DOWNSTREAM | extract._UPSTREAM`)."""
    five = frozenset({"supplier", "customer", "distributor", "vendor", "manufacturer"})
    assert five == extract.SUPPLY_CHAIN_TYPES
    assert extract._DOWNSTREAM | extract._UPSTREAM == extract.SUPPLY_CHAIN_TYPES
