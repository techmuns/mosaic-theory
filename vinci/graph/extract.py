"""Extract a name's named customer/supplier relationships from its 10-K → entity-resolved edges.

The EDGAR "who-names-whom" graph: an LLM reads the focal issuer's latest 10-K excerpts and names the
counterparties it discloses (customers it sells to, suppliers it buys from), each with the verbatim
filing phrase as provenance. We then resolve every counterparty to the internal entity key — by the
LLM-proposed ticker first (verified through the resolver, never trusted blind), else by exact
normalised name — so the graph is comparable, edge-for-edge, to the CIQ ground truth in Test 0.

Extraction and resolution are kept separate on purpose: the LLM's job is to *read the filing* (name
the company, quote the line); mapping a name to the internal key is the resolver's job.
A ticker the model proposes is only a hint — if it doesn't resolve we fall back to the name; the
model never mints the internal id. Direction mirrors CIQ (downstream = focal→counterparty).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, NamedTuple

from pydantic import BaseModel

from vinci.ciq.relationships import SUPPLY_CHAIN_TYPES
from vinci.edgar.client import EdgarClient
from vinci.graph.filings import latest_10k_excerpts
from vinci.graph.llm import LlmClient
from vinci.netcache import CachedHttp
from vinci.resolver import AmbiguousResolutionError, EntityResolver, UnknownSymbolError
from vinci.resolver.index import normalize_name
from vinci.schemas.data_record import Identity

# Relationship vocabulary + the goods-flow direction each implies *from the focal's perspective*
# (the filer wrote the 10-K). The allow-list is exactly CIQ's SUPPLY_CHAIN_TYPES — the same
# definition on both sides of Test 0, so we never extract a category the ground truth excludes.
# "partner" is deliberately absent: in practice it sweeps in COMPETITORS named in the competitive-
# landscape / risk sections ("competition from ... such as X"), which are not supply-chain links.
_DOWNSTREAM = {"customer", "distributor"}  # focal sells to counterparty
_UPSTREAM = {"supplier", "manufacturer", "vendor"}  # counterparty sells to focal
_REL_TYPES = sorted(SUPPLY_CHAIN_TYPES)
assert _DOWNSTREAM | _UPSTREAM == SUPPLY_CHAIN_TYPES  # direction map must cover the vocabulary


EXTRACT_TOOL: dict[str, Any] = {
    "name": "record_relationships",
    "description": (
        "Record every NAMED customer or supplier company disclosed in the 10-K excerpts. Only "
        "specific named companies — never generic phrases like 'our customers' or 'a major "
        "supplier'. Do not infer relationships the text does not state. CRITICALLY: do NOT record "
        "COMPETITORS or peer companies named only in competitive comparisons (e.g. 'we compete "
        "with X', 'competitors such as Y') — a competitor is not a customer or supplier."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "counterparty_name": {
                            "type": "string",
                            "description": "The counterparty company exactly as named in the text.",
                        },
                        "counterparty_ticker": {
                            "type": ["string", "null"],
                            "description": (
                                "Its US-listed stock ticker if publicly traded — INCLUDING a "
                                "US-listed ADR for a foreign company (e.g. TSMC→TSM). Only if you "
                                "recognise it with high confidence; otherwise null. Never guess."
                            ),
                        },
                        "relationship": {
                            "type": "string",
                            "enum": _REL_TYPES,
                            "description": (
                                "From the FILER's perspective: 'customer' buys from the filer; "
                                "'supplier' sells to the filer."
                            ),
                        },
                        "evidence": {
                            "type": "string",
                            "description": "The verbatim phrase from the text naming this link.",
                        },
                    },
                    "required": ["counterparty_name", "relationship", "evidence"],
                },
            }
        },
        "required": ["relationships"],
    },
}

_SYSTEM = (
    "You extract supply-chain relationships from SEC 10-K filing text. The text is from ONE "
    "company's annual report (the 'filer'). Identify every place the filer names a SPECIFIC "
    "company as a customer (a company that buys from the filer) or a supplier/manufacturer/vendor "
    "(a company that sells to or makes product for the filer). Report only named companies, with "
    "the verbatim phrase as evidence. Do NOT report COMPETITORS or peers named only in competitive "
    "comparisons ('we compete with', 'competitors such as') — that is not a supply-chain link. If "
    "you confidently recognise a counterparty as US-listed, give its ticker; else leave it null. "
    "Do not invent relationships."
)


class GraphEdge(BaseModel, frozen=True):
    """One entity-resolved supply-chain edge extracted from a focal issuer's 10-K."""

    focal_ticker: str | None
    focal_name: str
    focal_cik: str
    counterparty_name: str
    counterparty_ticker: str | None  # the model's proposal (may be wrong / unverified)
    counterparty_cik: str | None  # resolved US issuer CIK — position-eligible; None for connectors
    counterparty_internal_id: str | None
    node_id: str  # stable graph identity for EVERY node ("US:<cik>" | "NAME:<canonical>")
    node_kind: str  # "us_listed" (position-eligible) | "global" (foreign/private connector)
    relationship_type: str
    direction: str  # "downstream" (focal→counterparty) | "upstream" (counterparty→focal)
    evidence: str  # verbatim 10-K phrase (provenance)
    accession: str  # the 10-K accession (filing provenance — point-in-time)
    source_model: str
    resolution: str  # resolved_ticker | resolved_name | ambiguous | unresolved


def _direction(rel: str) -> str:
    # every allowed type is in exactly one set (asserted above), so this is total
    return "downstream" if rel in _DOWNSTREAM else "upstream"


# A graph NODE must be a specific named company. The model sometimes emits unnamed placeholders
# ("Distributor A", "vendor in Spain", "third-party vendors", "dark fiber vendors") — a real
# *relationship* but a useless node (can't resolve, can't propagate). Reject them at extraction.
_PLACEHOLDER_HEAD = re.compile(
    r"^(distributor|vendor|supplier|manufacturer|customer|reseller|subcontractor)s?\b",
    re.IGNORECASE,
)
_PLACEHOLDER_LEAD = re.compile(
    r"^(a|an|the|our|certain|various|multiple|several|other|third[- ]party|unnamed)\b",
    re.IGNORECASE,
)


def _is_generic_placeholder(name: str) -> bool:
    """True for unnamed/generic counterparties that are real relationships but not usable nodes."""
    n = name.strip()
    if not n or n[0].islower():  # a real company name is capitalised
        return True
    return bool(_PLACEHOLDER_HEAD.match(n) or _PLACEHOLDER_LEAD.match(n))


# Recurring global supply-chain hubs a US-filers-only resolver misses — the highest-degree shared
# nodes there are. Each alias maps to (canonical node name, US-ADR ticker or None). The canonical
# name unifies variant spellings into ONE shared node ("Hon Hai" and "Foxconn" → one); the ADR
# ticker, where one exists, also makes the node position-eligible. A node needs an IDENTITY to be a
# shared connector; only a POSITION needs a US ticker. Hand-curated + documented; extend as needed.
_FOREIGN_HUBS: dict[str, tuple[str, str | None]] = {
    "tsmc": ("Taiwan Semiconductor Manufacturing", "TSM"),
    "taiwan semiconductor": ("Taiwan Semiconductor Manufacturing", "TSM"),
    "asml": ("ASML Holding", "ASML"),
    "umc": ("United Microelectronics", "UMC"),
    "united microelectronics": ("United Microelectronics", "UMC"),
    "globalfoundries": ("GlobalFoundries", "GFS"),
    "stmicroelectronics": ("STMicroelectronics", "STM"),
    "infineon": ("Infineon Technologies", None),
    "sk hynix": ("SK Hynix", None),
    "samsung": ("Samsung Electronics", None),
    "foxconn": ("Hon Hai Precision (Foxconn)", None),
    "hon hai": ("Hon Hai Precision (Foxconn)", None),
    "catl": ("Contemporary Amperex (CATL)", None),
    "contemporary amperex": ("Contemporary Amperex (CATL)", None),
    "lg energy": ("LG Energy Solution", None),
    "panasonic": ("Panasonic Holdings", None),
    "sony": ("Sony Group", "SONY"),
    "bosch": ("Robert Bosch", None),
    "weichai": ("Weichai Power", None),
    "hyundai": ("Hyundai", None),
    "mitsubishi": ("Mitsubishi", None),
}


class NodeResolution(NamedTuple):
    """A counterparty's graph IDENTITY (always present) + US POSITION key (only when US-listed)."""

    cik: str | None  # US issuer CIK — position-eligible (incl. ADRs); None for connector-only nodes
    internal_id: str | None
    resolution: str  # resolved_ticker | resolved_name | ambiguous | unresolved
    node_id: str  # stable identity for EVERY node: "US:<cik>" or "NAME:<canonical>"
    node_kind: str  # "us_listed" (position-eligible) | "global" (foreign/private connector)


def _canonicalize(name: str) -> tuple[str, str | None]:
    """Map a counterparty name through the foreign-hub table → (canonical name, US-ADR ticker)."""
    key = normalize_name(name).lower()
    for alias, (canon, adr) in _FOREIGN_HUBS.items():
        if re.search(rf"\b{re.escape(alias)}\b", key):
            return canon, adr
    return name, None


def _resolve_node(resolver: EntityResolver, name: str, ticker: str | None) -> NodeResolution:
    """Identity-first resolution: a US/ADR security if we can, else a stable global connector node.

    Decouples node identity from tradeability — a foreign hub (TSMC, CATL) is a real shared node
    even with no US position. We try the model's ticker, then a known ADR ticker, then the US name
    index; failing all three the node keeps a canonical NAME identity so it still connects.
    """
    canon, adr = _canonicalize(name)
    for t in (ticker, adr):
        if t:
            try:
                ident = resolver.resolve_ticker(t)
                return NodeResolution(ident.cik, ident.internal_id, "resolved_ticker",
                                      f"US:{ident.cik}", "us_listed")
            except (UnknownSymbolError, AmbiguousResolutionError):
                pass  # a bad/foreign ticker hint — keep trying
    resolution = "unresolved"
    try:
        issuer = resolver.resolve_name(name)
        internal = issuer.securities[0].internal_id if issuer.securities else None
        return NodeResolution(
            issuer.cik, internal, "resolved_name", f"US:{issuer.cik}", "us_listed"
        )
    except AmbiguousResolutionError:
        resolution = "ambiguous"
    except UnknownSymbolError:
        resolution = "unresolved"
    return NodeResolution(None, None, resolution, f"NAME:{normalize_name(canon)}", "global")


def extract_graph_edges(
    edgar: EdgarClient,
    resolver: EntityResolver,
    llm: LlmClient,
    focal: Identity,
    *,
    http: CachedHttp | None = None,
) -> tuple[list[GraphEdge], dict[str, Any]]:
    """Extract + resolve the focal issuer's named supply-chain edges from its latest 10-K.

    Returns ``(edges, info)`` where ``info`` records the accession (or ``no_10k``) and a resolution
    breakdown. Self-loops (counterparty resolving to the focal) are dropped.
    """
    info: dict[str, Any] = {"focal": focal.eod_symbol, "accession": None}
    got = latest_10k_excerpts(edgar, focal.cik, http=http)
    if got is None:
        info["status"] = "no_10k"
        return [], info
    accession, text = got
    info["accession"] = accession
    if not text.strip():
        info["status"] = "empty_excerpts"
        return [], info

    raw = llm.extract(system=_SYSTEM, user=text, tool=EXTRACT_TOOL)
    rels = raw.get("relationships", []) if isinstance(raw, dict) else []

    edges: list[GraphEdge] = []
    counts: Counter[str] = Counter()
    for rel in rels:
        if not isinstance(rel, dict):  # the model occasionally emits a bare string item — skip it
            counts["skipped_malformed"] += 1
            continue
        name = str(rel.get("counterparty_name", "")).strip()
        rtype = str(rel.get("relationship", "")).strip().lower()
        if not name or rtype not in _REL_TYPES:
            counts["skipped_malformed"] += 1
            continue
        if _is_generic_placeholder(name):  # unnamed placeholder — a non-node, drop it
            counts["skipped_generic"] += 1
            continue
        ticker = rel.get("counterparty_ticker") or None
        node = _resolve_node(resolver, name, ticker)
        if node.cik is not None and node.cik == focal.cik:
            counts["self_loop"] += 1
            continue
        counts[node.resolution] += 1
        counts[f"kind_{node.node_kind}"] += 1
        edges.append(
            GraphEdge(
                focal_ticker=focal.ticker,
                focal_name=focal.name,
                focal_cik=focal.cik,
                counterparty_name=name,
                counterparty_ticker=ticker,
                counterparty_cik=node.cik,
                counterparty_internal_id=node.internal_id,
                node_id=node.node_id,
                node_kind=node.node_kind,
                relationship_type=rtype,
                direction=_direction(rtype),
                evidence=str(rel.get("evidence", "")).strip(),
                accession=accession,
                source_model=llm.model,
                resolution=node.resolution,
            )
        )
    info["status"] = "ok"
    info["edges"] = len(edges)
    info["resolution"] = dict(counts)
    return edges, info
