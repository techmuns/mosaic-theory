"""Evidence-grounded precision judge for the EDGAR graph — the CIQ-independent precision instrument.

Test 0 showed CIQ-overlap mismeasures the graph: real edges CIQ doesn't list (NVDA→TSMC, QRVO→Apple)
score as "misses". This judge measures precision *without* CIQ — it scores each extracted edge
against ITS OWN cited 10-K passage and asks: does the evidence establish a genuine ongoing
supply-chain link (the filer buys from / sells to the counterparty), or is it one of the noise
classes Test 0 surfaced — a COMPETITOR named in a competitive comparison, or a company named only in
an executive-biography / governance / M&A-history context (the "served 18 years with KLA" class)?

This is the precision gate for the **small/mid-cap** graph, where there is no CIQ ground truth at
all. The verdict taxonomy and the precision policy (which classes count as "real") are documented
constants, not tuned values; the judge model is the swappable ``graph_llm_model``.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from mosaic.graph.extract import GraphEdge
from mosaic.graph.llm import LlmClient

# The judge's verdict taxonomy. The noise classes are exactly the failure modes Test 0 surfaced.
VERDICTS = ("real_supply_chain", "competitor", "bio_or_governance", "ma_or_legal", "unsupported")
# Precision policy (documented, not tuned): only a genuine ongoing supply-chain link counts as a
# true edge. Everything else — competitors, bio/governance mentions, M&A/legal context, or evidence
# that doesn't support the claim — is a false positive.
REAL_VERDICTS = frozenset({"real_supply_chain"})

JUDGE_TOOL: dict[str, Any] = {
    "name": "classify_edge",
    "description": "Classify what the cited 10-K evidence establishes about the relationship.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": list(VERDICTS),
                "description": (
                    "real_supply_chain = evidence shows the filer actually buys from / sells to "
                    "counterparty as an ongoing business relationship; competitor = named as a "
                    "competitor/peer; bio_or_governance = named only in a person's bio or board/"
                    "management/governance background; ma_or_legal = named only in M&A/divestiture/"
                    "spinoff/indemnification/litigation context; unsupported = evidence does not "
                    "support the claimed relationship."
                ),
            },
            "reason": {
                "type": "string",
                "description": "one short phrase from the evidence justifying the verdict",
            },
        },
        "required": ["verdict", "reason"],
    },
}

_JUDGE_SYSTEM = (
    "You verify ONE extracted supply-chain relationship against its cited evidence from a 10-K. "
    "You are given the filer, the counterparty, the claimed relationship, and the verbatim "
    "evidence phrase. Decide which single class the evidence supports. A 'real_supply_chain' link "
    "means the filer actually BUYS FROM or SELLS TO the counterparty as an ongoing business "
    "relationship (customer, supplier, manufacturer, distributor, vendor). Be strict: a competitor "
    "named in a competitive comparison, a company named only in someone's biography or board/"
    "governance background, or a company named only in an M&A/divestiture/spinoff/legal context is "
    "NOT a supply-chain link. Judge ONLY from the evidence provided; do not use outside knowledge."
)


def judge_edge(llm: LlmClient, edge: GraphEdge) -> tuple[str, str]:
    """Classify one edge against its own evidence. Returns (verdict, reason)."""
    user = (
        f"Filer: {edge.focal_name} ({edge.focal_ticker})\n"
        f"Counterparty: {edge.counterparty_name}\n"
        f"Claimed relationship: {edge.relationship_type} ({edge.direction})\n"
        f'Evidence (verbatim from the filer\'s 10-K): "{edge.evidence}"'
    )
    out = llm.extract(system=_JUDGE_SYSTEM, user=user, tool=JUDGE_TOOL)
    verdict = str(out.get("verdict", "unsupported"))
    if verdict not in VERDICTS:
        verdict = "unsupported"
    return verdict, str(out.get("reason", ""))


def judge_edges(llm: LlmClient, edges: list[GraphEdge]) -> dict[str, Any]:
    """Judge every edge against its evidence → evidence-grounded precision + a class breakdown.

    ``precision`` is the share of edges whose evidence supports a genuine supply-chain link
    (``REAL_VERDICTS``). The ``judged`` list keeps each edge's verdict + reason for eyeballing.
    """
    by_class: Counter[str] = Counter()
    judged: list[dict[str, Any]] = []
    for e in edges:
        verdict, reason = judge_edge(llm, e)
        by_class[verdict] += 1
        judged.append(
            {
                "focal": e.focal_ticker,
                "counterparty": e.counterparty_name,
                "relationship": e.relationship_type,
                "verdict": verdict,
                "reason": reason,
                "evidence": e.evidence,
            }
        )
    real = sum(by_class[v] for v in REAL_VERDICTS)
    precision = real / len(edges) if edges else 0.0
    return {
        "model": llm.model,
        "n_edges": len(edges),
        "real_edges": real,
        "evidence_precision": round(precision, 3),
        "by_class": dict(by_class),
        "judged": judged,
    }
