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

from vinci.edgar.client import EdgarClient
from vinci.graph.extract import extract_graph_edges
from vinci.graph.judge import judge_edges
from vinci.graph.llm import LlmClient
from vinci.netcache import CachedHttp
from vinci.resolver import EntityResolver
from vinci.schemas.data_record import Identity


def graph_coverage(
    edgar: EdgarClient,
    resolver: EntityResolver,
    llm: LlmClient,
    focals: list[Identity],
    *,
    http: CachedHttp | None = None,
    super_connector_degree: int = 5,
) -> dict[str, Any]:
    """Extract the 1-hop graph for ``focals`` and judge every edge against its own evidence.

    Returns extraction precision (evidence-grounded), counterparty-density (edges/name, real/name),
    resolution-rate, the verdict-class breakdown, and per-name detail — the moat-readiness read.
    """
    all_edges = []
    per_name: list[dict[str, Any]] = []
    for f in focals:
        try:
            edges, info = extract_graph_edges(edgar, resolver, llm, f, http=http)
            status = info.get("status")
        except Exception as exc:  # one bad name must never lose a whole 100+-name run
            edges, status = [], f"error:{type(exc).__name__}"
        all_edges.extend(edges)
        per_name.append(
            {
                "focal": f.ticker,
                "name": f.name[:34],
                "status": status,
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
    sn = shared_node_map(real_edges, super_connector_degree=super_connector_degree)
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
        "shared_nodes": sn["shared_nodes"],
        "super_connectors": sn["super_connectors"],
        "per_name": per_name,
        "edges": edges_out,
    }


def super_connectors(real_edges: list[dict[str, Any]], *, degree: int) -> set[str]:
    """Focals naming ``degree``+ distinct hubs — they manufacture shared-degree, so exclude them."""
    out: dict[str, set[str]] = {}
    for e in real_edges:
        out.setdefault(e["focal_ticker"], set()).add(e["node_id"])
    return {f for f, nodes in out.items() if len(nodes) >= degree}


def shared_node_map(
    real_edges: list[dict[str, Any]], *, super_connector_degree: int = 5
) -> dict[str, Any]:
    """Nodes (US or foreign) behind 2+ *independent* US small/mid focals — the (a) Test-1 set.

    A shared node is a single shock source whose exposure across several small-caps no individual
    filing reveals. Grouped by node_id so a foreign hub (TSMC, CATL) counts even with no US position
    — identity, not tradeability. Super-connector focals (an IT integrator naming every hyperscaler)
    are flagged and **excluded from the degree count**: their sharing is one name's known multi-
    dependency, not independent signal. A node qualifies on 2+ NON-super-connector focals.
    """
    supers = super_connectors(real_edges, degree=super_connector_degree)
    by_node: dict[str, dict[str, Any]] = {}
    for e in real_edges:
        node = by_node.setdefault(
            e["node_id"],
            {"node_id": e["node_id"], "node_kind": e["node_kind"], "name": e["counterparty_name"],
             "ticker": e["counterparty_ticker"], "focals": set()},
        )
        if e["focal_ticker"] not in supers:  # only independent focals build shared-degree
            node["focals"].add(e["focal_ticker"])
    shared = [
        {**v, "degree": len(v["focals"]), "focals": sorted(v["focals"])}
        for v in by_node.values()
        if len(v["focals"]) >= 2
    ]
    return {
        "super_connectors": sorted(supers),
        "shared_nodes": sorted(shared, key=lambda s: s["degree"], reverse=True),
    }
