"""Test 0 — score the EDGAR who-names-whom graph against the CIQ ground truth (graph-track gate).

The question: is an LLM-extracted, entity-resolved 1-hop graph from dated EDGAR 10-Ks precise enough
to be worth pursuing? We build the EDGAR graph for the focal names that have CIQ
Business-Relationships exports, reduce both sides to ``(focal_cik, counterparty_cik)`` issuer pairs,
and report precision / recall / resolution-rate, with matched/missed/spurious edges for eyeballing.

Coverage caveat (intrinsic, not a bug): a 10-K names only the *material* counterparties (customer-
concentration, key-supplier disclosures), while CIQ aggregates many sources — so EDGAR **recall** vs
CIQ is a lower bound by construction. The decisive metric is **precision** (are the edges EDGAR
asserts actually real?) and how cleanly they resolve; weak precision kills the track, while a weak
recall is the known coverage limit, not a failure. If precision is weak on Sonnet, the caller reruns
a sample on Opus (``claude-opus-4-8``) to separate a source/approach problem from model strength.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from vinci.edgar.client import EdgarClient
from vinci.graph.extract import GraphEdge, extract_graph_edges
from vinci.graph.llm import LlmClient
from vinci.netcache import CachedHttp
from vinci.resolver import AmbiguousResolutionError, EntityResolver, UnknownSymbolError
from vinci.schemas.data_record import Identity


def _cik_from_internal_id(internal_id: str) -> str | None:
    """internal_id is ``SEC-<10digit cik>-<ticker>``; the CIK is always the second dash field."""
    parts = internal_id.split("-")
    return parts[1] if len(parts) >= 2 and parts[1].isdigit() else None


def ciq_ground_truth(
    ciq_edges: list[Any], resolver: EntityResolver
) -> tuple[dict[str, set[str]], dict[str, Identity]]:
    """Reduce resolved CIQ edges to ``focal_cik -> {counterparty_cik}`` + one Identity per focal.

    Only US-resolved counterparties (``counterparty_internal_id`` set) count as ground truth — the
    EDGAR graph can only be scored against edges that live in the same internal key space.
    """
    gt: dict[str, set[str]] = defaultdict(set)
    focal_ident: dict[str, Identity] = {}
    for e in ciq_edges:
        if e.counterparty_internal_id is None or not e.focal_ticker:
            continue
        try:
            fid = resolver.resolve_ticker(e.focal_ticker)
        except (UnknownSymbolError, AmbiguousResolutionError):
            continue
        cp_cik = _cik_from_internal_id(e.counterparty_internal_id)
        if cp_cik:
            gt[fid.cik].add(cp_cik)
            focal_ident.setdefault(fid.cik, fid)
    return dict(gt), focal_ident


def score_test0(
    edgar: EdgarClient,
    resolver: EntityResolver,
    llm: LlmClient,
    ciq_edges: list[Any],
    *,
    http: CachedHttp | None = None,
    max_focals: int | None = None,
) -> dict[str, Any]:
    """Build the EDGAR graph for the CIQ focal names and score it against the CIQ ground truth.

    Returns aggregate precision/recall/resolution-rate, a per-focal breakdown, and the EDGAR edges
    bucketed into matched / spurious (not in CIQ) / and the CIQ edges EDGAR missed — all by CIK so a
    human can eyeball *which* links it got right and wrong, not just the rates.
    """
    gt, focal_ident = ciq_ground_truth(ciq_edges, resolver)
    focals = list(focal_ident)
    if max_focals is not None:
        focals = focals[:max_focals]

    per_focal: list[dict[str, Any]] = []
    tp = fp = fn = 0
    extracted_total = resolved_total = 0
    all_edges: list[GraphEdge] = []

    for cik in focals:
        ident = focal_ident[cik]
        edges, info = extract_graph_edges(edgar, resolver, llm, ident, http=http)
        all_edges.extend(edges)
        extracted_total += len(edges)
        resolved = {e.counterparty_cik for e in edges if e.counterparty_cik}
        resolved_total += sum(1 for e in edges if e.counterparty_cik)

        truth = gt.get(cik, set())
        matched = resolved & truth
        spurious = resolved - truth  # EDGAR asserted, not in CIQ (coverage gap OR false positive)
        missed = truth - resolved  # CIQ has, EDGAR didn't name (mostly the coverage limit)
        tp += len(matched)
        fp += len(spurious)
        fn += len(missed)
        per_focal.append(
            {
                "focal": ident.ticker,
                "focal_cik": cik,
                "status": info.get("status"),
                "accession": info.get("accession"),
                "edges_extracted": len(edges),
                "evidence_refused": int(info.get("evidence_refused", 0)),  # not in the excerpts
                "edges_resolved": len(resolved),
                "ciq_truth": len(truth),
                "matched": sorted(matched),
                "spurious": sorted(spurious),
                "missed": sorted(missed),
            }
        )

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    resolution_rate = resolved_total / extracted_total if extracted_total else 0.0
    return {
        "model": llm.model,
        "focals_scored": len(focals),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "resolution_rate": round(resolution_rate, 3),
        "true_positives": tp,
        "spurious": fp,
        "missed": fn,
        "edges_extracted": extracted_total,
        "per_focal": per_focal,
        "edges": all_edges,
    }
