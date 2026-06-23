"""CIQ manual-data parsing — the licensed Customers & Suppliers exports → supply-chain edges.

CIQ has no programmatic feed (depth-only), so its exports are read from a swappable
:class:`ManualDataStore`. This package only *parses* the manual data; the discriminator's judgment
stays manual.
"""

from vinci.ciq.manual import (
    CiqFormatError,
    LocalFolderManualStore,
    ManualDataStore,
    extract_text,
)
from vinci.ciq.relationships import (
    SUPPLY_CHAIN_TYPES,
    CiqEdge,
    ParsedRelationships,
    ParsedRow,
    load_ciq_edges,
    parse_relationships,
)

__all__ = [
    "SUPPLY_CHAIN_TYPES",
    "CiqEdge",
    "CiqFormatError",
    "LocalFolderManualStore",
    "ManualDataStore",
    "ParsedRelationships",
    "ParsedRow",
    "extract_text",
    "load_ciq_edges",
    "parse_relationships",
]
