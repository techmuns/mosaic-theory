"""Build + measure the 1-hop EDGAR graph on the small/mid-cap screen universe (moat-readiness read).

Test 0 ran on CIQ's mega-cap focals, which is the worst case for the moat: a mega-cap names few
counterparties (none is material to *it* — that's the 2% recall), and the few it names are the
famous, already-priced edges. The moat lives on OBSCURE edges, and SEC customer-concentration rules
force them to be disclosed from the SMALL party's side (QRVO→Apple, CRUS→Apple). So this read builds
the graph on the small/mid screen candidates and measures, via the CIQ-independent evidence judge:
extraction precision + counterparty-density (real supply-chain edges per name). No CIQ here — the
judge is the only precision instrument.
"""

from __future__ import annotations

from typing import Any

from mosaic.edgar.client import EdgarClient
from mosaic.graph.extract import extract_graph_edges
from mosaic.graph.judge import judge_edges
from mosaic.graph.llm import LlmClient
from mosaic.netcache import CachedHttp
from mosaic.resolver import EntityResolver
from mosaic.schemas.data_record import Identity


def graph_coverage(
    edgar: EdgarClient,
    resolver: EntityResolver,
    llm: LlmClient,
    focals: list[Identity],
    *,
    http: CachedHttp | None = None,
) -> dict[str, Any]:
    """Extract the 1-hop graph for ``focals`` and judge every edge against its own evidence.

    Returns extraction precision (evidence-grounded), counterparty-density (edges/name, real/name),
    resolution-rate, the verdict-class breakdown, and per-name detail — the moat-readiness read.
    """
    all_edges = []
    per_name: list[dict[str, Any]] = []
    for f in focals:
        edges, info = extract_graph_edges(edgar, resolver, llm, f, http=http)
        all_edges.extend(edges)
        per_name.append(
            {
                "focal": f.ticker,
                "name": f.name[:34],
                "status": info.get("status"),
                "edges": len(edges),
                "us_listed": sum(1 for e in edges if e.node_kind == "us_listed"),
            }
        )

    jrep = judge_edges(llm, all_edges)
    verdicts = [j["verdict"] for j in jrep["judged"]]
    edges_out = [
        {
            "focal_ticker": e.focal_ticker, "focal_cik": e.focal_cik,
            "counterparty_name": e.counterparty_name, "counterparty_ticker": e.counterparty_ticker,
            "counterparty_cik": e.counterparty_cik, "node_id": e.node_id, "node_kind": e.node_kind,
            "relationship_type": e.relationship_type, "direction": e.direction,
            "resolution": e.resolution, "verdict": v, "evidence": e.evidence,
        }
        for e, v in zip(all_edges, verdicts, strict=True)
    ]
    real_edges = [e for e in edges_out if e["verdict"] == "real_supply_chain"]

    n = len(focals)
    real = len(real_edges)
    us_listed = sum(1 for e in real_edges if e["node_kind"] == "us_listed")
    return {
        "model": llm.model,
        "n_names": n,
        "names_with_edges": sum(1 for p in per_name if p["edges"]),
        "total_edges": len(all_edges),
        "real_edges": real,
        "real_us_listed": us_listed,  # real edge to a position-eligible US node
        "real_global": real - us_listed,  # real edge to a foreign/private connector node
        "edges_per_name": round(len(all_edges) / n, 2) if n else 0.0,
        "real_edges_per_name": round(real / n, 2) if n else 0.0,  # moat-relevant density
        "evidence_precision": jrep["evidence_precision"],
        "by_class": jrep["by_class"],
        "shared_nodes": shared_node_map(real_edges),
        "per_name": per_name,
        "edges": edges_out,
    }


def shared_node_map(real_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nodes (US or foreign) that sit behind 2+ distinct US small/mid focals — the (a) Test-1 set.

    This is the moat-readiness read: a shared node is a single shock source whose exposure across
    several small-caps no individual filing reveals and no human has assembled. Grouped by node_id
    so a foreign hub (TSMC, CATL) counts even with no US position — identity, not tradeability.
    """
    by_node: dict[str, dict[str, Any]] = {}
    for e in real_edges:
        node = by_node.setdefault(
            e["node_id"],
            {"node_id": e["node_id"], "node_kind": e["node_kind"], "name": e["counterparty_name"],
             "ticker": e["counterparty_ticker"], "focals": set()},
        )
        node["focals"].add(e["focal_ticker"])
    shared = [
        {**v, "degree": len(v["focals"]), "focals": sorted(v["focals"])}
        for v in by_node.values()
        if len(v["focals"]) >= 2
    ]
    return sorted(shared, key=lambda s: s["degree"], reverse=True)
