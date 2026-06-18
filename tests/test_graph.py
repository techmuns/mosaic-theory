"""Step 3b/3c verification — graph extraction resolution + direction, and Test-0 scoring math.

The live end-to-end run (LLM extraction from real 10-Ks, scored vs CIQ) is the `graph-test0` CLI;
these tests lock the deterministic pieces that do not need the network or an API key: how an
LLM-named counterparty is resolved to the internal key, the goods-flow direction, the reduction of
CIQ edges to ground-truth pairs, and the precision/recall arithmetic.
"""

from __future__ import annotations

from typing import Any, cast

from mosaic.ciq import CiqEdge
from mosaic.graph import GraphEdge, judge_edges
from mosaic.graph import test0 as t0mod
from mosaic.graph.extract import _direction, _resolve_counterparty
from mosaic.graph.llm import LlmClient
from mosaic.graph.test0 import ciq_ground_truth, score_test0
from mosaic.resolver import EntityResolver, RawEntry, ResolverIndex

_RESOLVER = EntityResolver(
    index=ResolverIndex(
        [
            RawEntry(cik="0000000009", name="Focal Inc", ticker="FOC", exchange="NYSE"),
            RawEntry(cik="0000000001", name="Acme Corp", ticker="ACME", exchange="Nasdaq"),
            RawEntry(cik="0000000002", name="Beta Industries", ticker="BETA", exchange="Nasdaq"),
        ]
    )
)


def test_direction_mirrors_ciq_goods_flow() -> None:
    assert _direction("customer") == "downstream"  # focal sells to the customer
    assert _direction("distributor") == "downstream"
    assert _direction("supplier") == "upstream"  # supplier sells to focal
    assert _direction("manufacturer") == "upstream"


def test_resolve_counterparty_ticker_first_then_name() -> None:
    # a clean ticker resolves directly
    assert _resolve_counterparty(_RESOLVER, "Acme Corp", "ACME") == (
        "0000000001", "SEC-0000000001-ACME", "resolved_ticker",
    )
    # a bad ticker hint falls back to the exact normalised name
    cik, _iid, res = _resolve_counterparty(_RESOLVER, "Beta Industries", "NOPE")
    assert (cik, res) == ("0000000002", "resolved_name")
    # neither a known ticker nor a known name → unresolved (never guessed)
    assert _resolve_counterparty(_RESOLVER, "Unknown Private LLC", None)[2] == "unresolved"


def _ciq_edge(cp_internal_id: str | None, *, ticker: str | None) -> CiqEdge:
    return CiqEdge(
        focal_ticker="FOC", focal_name="Focal Inc", counterparty_name="x",
        counterparty_ticker=ticker, counterparty_exchange="Nasdaq",
        counterparty_internal_id=cp_internal_id, relationship_type="Customer",
        direction="downstream", source="10-K",
        resolution="resolved" if cp_internal_id else "private",
    )


def test_ciq_ground_truth_keys_by_cik() -> None:
    edges = [
        _ciq_edge("SEC-0000000001-ACME", ticker="ACME"),
        _ciq_edge("SEC-0000000002-BETA", ticker="BETA"),
        _ciq_edge(None, ticker=None),  # unresolved CIQ edge is not ground truth
    ]
    gt, focal_ident = ciq_ground_truth(edges, _RESOLVER)
    assert gt == {"0000000009": {"0000000001", "0000000002"}}
    assert focal_ident["0000000009"].ticker == "FOC"


def _graph_edge(cp_cik: str | None) -> GraphEdge:
    return GraphEdge(
        focal_ticker="FOC", focal_name="Focal Inc", focal_cik="0000000009",
        counterparty_name="x", counterparty_ticker=None, counterparty_cik=cp_cik,
        counterparty_internal_id=None, relationship_type="customer", direction="downstream",
        evidence="...", accession="0000-00-000000", source_model="fake",
        resolution="resolved_ticker" if cp_cik else "unresolved",
    )


def test_score_test0_precision_recall(monkeypatch: Any) -> None:
    # CIQ truth for FOC = {ACME, BETA}
    ciq_edges = [
        _ciq_edge("SEC-0000000001-ACME", ticker="ACME"),
        _ciq_edge("SEC-0000000002-BETA", ticker="BETA"),
    ]
    # EDGAR graph finds ACME (match) + an unrelated CIK 0000000007 (spurious); misses BETA.
    fake_edges = [_graph_edge("0000000001"), _graph_edge("0000000007")]

    def _fake_extract(edgar: Any, resolver: Any, llm: Any, focal: Any, **kw: Any) -> Any:
        return fake_edges, {"status": "ok", "accession": "acc"}

    monkeypatch.setattr(t0mod, "extract_graph_edges", _fake_extract)
    rep = score_test0(
        edgar=cast(Any, None), resolver=_RESOLVER, llm=_FakeLlm(), ciq_edges=ciq_edges
    )

    assert rep["true_positives"] == 1
    assert rep["spurious"] == 1 and rep["missed"] == 1
    assert rep["precision"] == 0.5  # 1 of 2 extracted are in CIQ
    assert rep["recall"] == 0.5  # 1 of 2 CIQ edges found


class _FakeLlm(LlmClient):
    @property
    def model(self) -> str:
        return "fake-model"

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        return {"relationships": []}


def test_judge_edges_counts_only_real_supply_chain() -> None:
    # the evidence judge: precision = share of edges whose verdict is the real supply-chain class;
    # competitor / bio / M&A verdicts are false positives (the noise classes Test 0 surfaced).
    edges = [_graph_edge("0000000001"), _graph_edge("0000000002"), _graph_edge("0000000003")]
    verdicts = iter(["real_supply_chain", "competitor", "bio_or_governance"])

    class _Judge(LlmClient):
        @property
        def model(self) -> str:
            return "fake-judge"

        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            return {"verdict": next(verdicts), "reason": "because"}

    rep = judge_edges(_Judge(), edges)
    assert rep["real_edges"] == 1
    assert rep["evidence_precision"] == round(1 / 3, 3)
    assert rep["by_class"] == {"real_supply_chain": 1, "competitor": 1, "bio_or_governance": 1}
