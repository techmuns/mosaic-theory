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
                "resolved": sum(1 for e in edges if e.counterparty_cik),
            }
        )

    jrep = judge_edges(llm, all_edges)
    n = len(focals)
    real = jrep["real_edges"]
    resolved = sum(p["resolved"] for p in per_name)
    return {
        "model": llm.model,
        "n_names": n,
        "names_with_edges": sum(1 for p in per_name if p["edges"]),
        "total_edges": len(all_edges),
        "resolved_edges": resolved,
        "edges_per_name": round(len(all_edges) / n, 2) if n else 0.0,
        "real_edges_per_name": round(real / n, 2) if n else 0.0,  # moat-relevant density
        "resolution_rate": round(resolved / len(all_edges), 3) if all_edges else 0.0,
        "evidence_precision": jrep["evidence_precision"],
        "real_edges": real,
        "by_class": jrep["by_class"],
        "per_name": per_name,
        "judged": jrep["judged"],
    }
