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

from collections import Counter
from typing import Any

from pydantic import BaseModel

from mosaic.ciq.relationships import SUPPLY_CHAIN_TYPES
from mosaic.edgar.client import EdgarClient
from mosaic.graph.filings import latest_10k_excerpts
from mosaic.graph.llm import LlmClient
from mosaic.netcache import CachedHttp
from mosaic.resolver import AmbiguousResolutionError, EntityResolver, UnknownSymbolError
from mosaic.schemas.data_record import Identity

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
                                "Its US stock ticker ONLY if it is a publicly-traded company you "
                                "recognise with high confidence; otherwise null. Never guess."
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
    counterparty_cik: str | None  # resolved issuer CIK (None if unresolved)
    counterparty_internal_id: str | None
    relationship_type: str
    direction: str  # "downstream" (focal→counterparty) | "upstream" (counterparty→focal)
    evidence: str  # verbatim 10-K phrase (provenance)
    accession: str  # the 10-K accession (filing provenance — point-in-time)
    source_model: str
    resolution: str  # resolved_ticker | resolved_name | ambiguous | unresolved


def _direction(rel: str) -> str:
    # every allowed type is in exactly one set (asserted above), so this is total
    return "downstream" if rel in _DOWNSTREAM else "upstream"


def _resolve_counterparty(
    resolver: EntityResolver, name: str, ticker: str | None
) -> tuple[str | None, str | None, str]:
    """(cik, internal_id, resolution). Ticker first (verified), then exact normalised name."""
    if ticker:
        try:
            ident = resolver.resolve_ticker(ticker)
            return ident.cik, ident.internal_id, "resolved_ticker"
        except (UnknownSymbolError, AmbiguousResolutionError):
            pass  # a bad/foreign ticker hint — fall back to the name
    try:
        issuer = resolver.resolve_name(name)
        internal = issuer.securities[0].internal_id if issuer.securities else None
        return issuer.cik, internal, "resolved_name"
    except AmbiguousResolutionError:
        return None, None, "ambiguous"
    except UnknownSymbolError:
        return None, None, "unresolved"


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
        ticker = rel.get("counterparty_ticker") or None
        cik, internal_id, resolution = _resolve_counterparty(resolver, name, ticker)
        if cik is not None and cik == focal.cik:
            counts["self_loop"] += 1
            continue
        counts[resolution] += 1
        edges.append(
            GraphEdge(
                focal_ticker=focal.ticker,
                focal_name=focal.name,
                focal_cik=focal.cik,
                counterparty_name=name,
                counterparty_ticker=ticker,
                counterparty_cik=cik,
                counterparty_internal_id=internal_id,
                relationship_type=rtype,
                direction=_direction(rtype),
                evidence=str(rel.get("evidence", "")).strip(),
                accession=accession,
                source_model=llm.model,
                resolution=resolution,
            )
        )
    info["status"] = "ok"
    info["edges"] = len(edges)
    info["resolution"] = dict(counts)
    return edges, info
