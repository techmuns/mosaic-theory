"""Parse CIQ **Business Relationships** exports → entity-resolved supply-chain edges.

Empirical layout (after ``striprtf``; see ``ciq_extraction_notes.md``): a pipe-delimited table whose
header is either ``Customer Name | Supplier Name | Relationship Type | Primary Industry | Source``
(Customers view) or ``Supplier Name | Customer Name | …`` (Suppliers view). So **col0 is always the
counterparty, col1 the focal**, and the header order gives the edge direction. Each data row is
followed by a "Business Description" line we ignore. There is no Current/Former column — the export
is "recently disclosed (within the last two years)", i.e. current-only.

We keep only supply-chain relationship types (Supplier/Customer/Distributor/Vendor/Manufacturer) and
drop the financial/legal/real-estate types the export mixes in (Creditor, Landlord, Licensor/ee,
Borrower, Lessee/or, Tenant, Transfer Agent, Franchisee/or). "Client Services" is **excluded** per
the spec's allow-list (a softer client relationship, not a goods/services dependency) — a documented
judgment call the PM can revisit. Counterparties are resolved by ticker (US only); foreign/private
counterparties are recorded with a reason rather than dropped silently.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from pydantic import BaseModel

from vinci.ciq.manual import ManualDataStore
from vinci.resolver import AmbiguousResolutionError, EntityResolver, UnknownSymbolError

# supply-chain relationship types to keep (lower-cased exact match)
SUPPLY_CHAIN_TYPES = frozenset({"supplier", "customer", "distributor", "vendor", "manufacturer"})

# CIQ exchange prefixes that are US-listed (resolvable via SEC); everything else is non-US.
_US_EXCHANGE_PREFIXES = ("Nasdaq", "NYSE", "OTC", "BATS", "Cboe", "AMEX")

# "Name (Exch:Ticker)", tolerant of a leading "*" (proprietary-relationship marker).
_ENTITY_RE = re.compile(r"^\*?\s*(?P<name>.+?)\s*\((?P<exch>[^:()]+):(?P<ticker>[^()]+)\)\s*$")


@dataclass(frozen=True)
class ParsedRow:
    counterparty_name: str
    counterparty_ticker: str | None
    counterparty_exchange: str | None
    relationship_type: str
    source: str


@dataclass(frozen=True)
class ParsedRelationships:
    focal_name: str
    focal_ticker: str | None
    focal_exchange: str | None
    view: str  # "customers" | "suppliers"
    rows: list[ParsedRow]


class CiqEdge(BaseModel, frozen=True):
    """One entity-resolved supply-chain edge from a CIQ Business Relationships export."""

    focal_ticker: str | None
    focal_name: str
    counterparty_name: str
    counterparty_ticker: str | None
    counterparty_exchange: str | None
    counterparty_internal_id: str | None  # set when resolved (US)
    relationship_type: str
    direction: str  # "downstream" (focal→counterparty) or "upstream" (counterparty→focal)
    source: str
    resolution: str  # resolved | non_us | private | unresolved_us | ambiguous


def _parse_entity(cell: str) -> tuple[str, str | None, str | None]:
    """'Name (Exch:Ticker)' → (name, exchange, ticker); private names → (name, None, None)."""
    m = _ENTITY_RE.match(cell.strip())
    if m:
        return m.group("name").strip(), m.group("exch").strip(), m.group("ticker").strip()
    return cell.strip().lstrip("*").strip(), None, None


def parse_relationships(text: str) -> ParsedRelationships | None:
    """Parse one export's text. Returns None if it isn't a Business Relationships table."""
    header_idx: int | None = None
    col0_label = ""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        cells = [c.strip() for c in ln.split("|")]
        if "Relationship Type" in cells and ("Customer Name" in cells or "Supplier Name" in cells):
            header_idx, col0_label = i, cells[0]
            break
    if header_idx is None:
        return None
    view = "customers" if col0_label == "Customer Name" else "suppliers"

    rows: list[ParsedRow] = []
    focal_cells: list[str] = []
    for ln in lines[header_idx + 1 :]:
        fields = ln.split("|")
        if len(fields) < 5 or not fields[0].strip():
            continue
        if fields[0].strip().startswith("Business Description") or "Relationship Type" in fields:
            continue
        cp_name, cp_exch, cp_ticker = _parse_entity(fields[0])
        rel_type = fields[2].strip()
        if not rel_type:
            continue
        focal_cells.append(fields[1].strip())
        rows.append(ParsedRow(cp_name, cp_ticker, cp_exch, rel_type, fields[4].strip()))

    focal_name = focal_ticker = focal_exch = None
    if focal_cells:
        dominant = Counter(focal_cells).most_common(1)[0][0]
        focal_name, focal_exch, focal_ticker = _parse_entity(dominant)
    return ParsedRelationships(focal_name or "", focal_ticker, focal_exch, view, rows)


def _is_us_exchange(exch: str | None) -> bool:
    return bool(exch) and exch.startswith(_US_EXCHANGE_PREFIXES)  # type: ignore[union-attr]


def _resolve(resolver: EntityResolver, row: ParsedRow) -> tuple[str | None, str]:
    """Resolve a counterparty by ticker (US only). Returns (internal_id, resolution_status)."""
    if row.counterparty_ticker is None:
        return None, "private"
    if not _is_us_exchange(row.counterparty_exchange):
        return None, "non_us"
    try:
        return resolver.resolve_ticker(row.counterparty_ticker).internal_id, "resolved"
    except AmbiguousResolutionError:
        return None, "ambiguous"
    except UnknownSymbolError:
        return None, "unresolved_us"


def load_ciq_edges(
    store: ManualDataStore, resolver: EntityResolver
) -> tuple[list[CiqEdge], dict[str, int]]:
    """Parse every export in the manual store → supply-chain edges + a resolution-stats summary."""
    edges: list[CiqEdge] = []
    stats: Counter[str] = Counter()
    for _name, text in store.iter_documents():
        parsed = parse_relationships(text)
        if parsed is None:
            stats["non_relationship_docs"] += 1
            continue
        stats["documents"] += 1
        direction = "downstream" if parsed.view == "customers" else "upstream"
        for row in parsed.rows:
            stats["rows_total"] += 1
            if row.relationship_type.lower() not in SUPPLY_CHAIN_TYPES:
                stats["dropped_non_supply_chain"] += 1
                continue
            internal_id, resolution = _resolve(resolver, row)
            stats[resolution] += 1
            edges.append(
                CiqEdge(
                    focal_ticker=parsed.focal_ticker,
                    focal_name=parsed.focal_name,
                    counterparty_name=row.counterparty_name,
                    counterparty_ticker=row.counterparty_ticker,
                    counterparty_exchange=row.counterparty_exchange,
                    counterparty_internal_id=internal_id,
                    relationship_type=row.relationship_type,
                    direction=direction,
                    source=row.source,
                    resolution=resolution,
                )
            )
    return edges, dict(stats)
