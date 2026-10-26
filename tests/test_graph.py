"""Step 3b/3c verification — graph extraction resolution + direction, and Test-0 scoring math.

The live end-to-end run (LLM extraction from real 10-Ks, scored vs CIQ) is the `graph-test0` CLI;
these tests lock the deterministic pieces that do not need the network or an API key: how an
LLM-named counterparty is resolved to the internal key, the goods-flow direction, the reduction of
CIQ edges to ground-truth pairs, and the precision/recall arithmetic.
"""

from __future__ import annotations

from typing import Any, cast

from vinci.ciq import CiqEdge
from vinci.graph import GraphEdge, judge_edges
from vinci.graph import test0 as t0mod
from vinci.graph.extract import _direction, _is_generic_placeholder, _resolve_node
from vinci.graph.llm import LlmClient
from vinci.graph.test0 import ciq_ground_truth, score_test0
from vinci.resolver import EntityResolver, RawEntry, ResolverIndex

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


def test_resolve_node_ticker_then_name_then_global_identity() -> None:
    # a clean US ticker resolves to a position-eligible us_listed node
    n = _resolve_node(_RESOLVER, "Acme Corp", "ACME")
    assert (n.cik, n.resolution, n.node_id, n.node_kind) == (
        "0000000001", "resolved_ticker", "US:0000000001", "us_listed",
    )
    # a bad ticker hint falls back to the exact normalised name
    n = _resolve_node(_RESOLVER, "Beta Industries", "NOPE")
    assert (n.cik, n.resolution, n.node_kind) == ("0000000002", "resolved_name", "us_listed")
    # a foreign hub with no US listing still gets a stable GLOBAL identity (a shared connector),
    # canonicalised so variant spellings collapse to one node — but no US position (cik None)
    n = _resolve_node(_RESOLVER, "Foxconn", None)
    assert n.cik is None and n.node_kind == "global"
    assert n.node_id == _resolve_node(_RESOLVER, "Hon Hai Precision", None).node_id  # unified


def test_generic_placeholder_rejects_non_nodes() -> None:
    assert _is_generic_placeholder("Distributor A")
    assert _is_generic_placeholder("vendor in Spain")
    assert _is_generic_placeholder("third-party manufacturers")
    assert not _is_generic_placeholder("Taiwan Semiconductor Manufacturing")


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
        counterparty_internal_id=None,
        node_id=f"US:{cp_cik}" if cp_cik else "NAME:x",
        node_kind="us_listed" if cp_cik else "global",
        relationship_type="customer", direction="downstream",
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


def test_score_test0_states_the_edges_refused_for_their_evidence(monkeypatch: Any) -> None:
    """(-) An edge the verbatim check refused is absent from Test 0's matches, so a CIQ edge it
    would have matched reads as MISSED — the per-focal row must say how many were refused."""
    def _fake_extract(edgar: Any, resolver: Any, llm: Any, focal: Any, **kw: Any) -> Any:
        return [_graph_edge("0000000001")], {"status": "ok", "accession": "acc",
                                             "evidence_refused": 2}

    monkeypatch.setattr(t0mod, "extract_graph_edges", _fake_extract)
    rep = score_test0(edgar=cast(Any, None), resolver=_RESOLVER, llm=_FakeLlm(),
                      ciq_edges=[_ciq_edge("SEC-0000000001-ACME", ticker="ACME")])
    assert rep["per_focal"][0]["evidence_refused"] == 2


class _FakeLlm(LlmClient):
    @property
    def model(self) -> str:
        return "fake-model"

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        return {"relationships": []}


def test_detect_shocks_is_market_adjusted() -> None:
    from datetime import date, timedelta

    from vinci.graph.test1 import detect_shocks
    from vinci.schemas.market import PriceBar

    def bars(iid: str, closes: list[float]) -> list[PriceBar]:
        d0 = date(2025, 1, 1)
        return [
            PriceBar(internal_id=iid, bar_date=d0 + timedelta(days=i * 7), open=c, high=c,
                     low=c, close=c, volume=1e6, source="test")
            for i, c in enumerate(closes)
        ]

    # a hub-idiosyncratic -8% day against a flat market IS a shock
    hub = bars("H", [100, 100, 92, 92])
    flat = bars("B", [50, 50, 50, 50])
    shocks = detect_shocks("H", hub, flat, abnormal_threshold=-0.06)
    assert len(shocks) == 1 and shocks[0].abnormal_return < -0.06
    # the SAME -8% move on a -8% market day is NOT a shock — market-adjusted to ~0
    down_mkt = bars("B", [50, 50, 46, 46])
    assert detect_shocks("H", hub, down_mkt, abnormal_threshold=-0.06) == []


def test_cumulative_abnormal_return_lag_and_own_news_guard() -> None:
    from datetime import date, timedelta

    from vinci.graph.test1 import cumulative_abnormal_return
    from vinci.schemas.market import PriceBar

    def bars(iid: str, closes: list[float]) -> list[PriceBar]:
        d0 = date(2025, 1, 1)
        return [
            PriceBar(internal_id=iid, bar_date=d0 + timedelta(days=i * 7), open=c, high=c,
                     low=c, close=c, volume=1e6, source="test")
            for i, c in enumerate(closes)
        ]

    flat = bars("B", [50] * 6)
    # dependent drifts down ~2%/period for 3 periods after the shock (index 0) vs a flat market
    dep = bars("D", [100, 98, 96.04, 94.12, 94.12, 94.12])
    car = cumulative_abnormal_return(dep, flat, date(2025, 1, 1), lo=1, hi=3)
    assert car is not None and car < -0.05  # ~ -6% cumulative abnormal (lag captured)
    # a dependent with its OWN >20% single-day move in the window is excluded (its own news)
    own = bars("D", [100, 98, 70, 70, 70, 70])
    assert cumulative_abnormal_return(own, flat, date(2025, 1, 1), lo=1, hi=3) is None


def test_exposure_graph_n_hop_with_provenance() -> None:
    from vinci.graph.exposure import ExposureGraph

    def edge(focal_cik: str, ft: str, node: str, cp: str) -> dict[str, Any]:
        return {
            "focal_cik": focal_cik, "focal_ticker": ft, "node_id": node, "counterparty_name": cp,
            "counterparty_ticker": None, "relationship_type": "supplier",
            "evidence": f"{ft} uses {cp}",
        }

    # A→Hub, B→Hub (both directly exposed); B→Hub2 (Hub2 reachable from Hub only at 2 hops)
    g = ExposureGraph.from_edges([
        edge("1", "A", "US:9", "Hub"),
        edge("2", "B", "US:9", "Hub"),
        edge("2", "B", "US:8", "Hub2"),
    ])
    one = g.exposed_within("US:9", hops=1)
    assert {x.node_id for x in one} == {"US:1", "US:2"}  # A, B at 1 hop; Hub2 not yet
    two = g.exposed_within("US:9", hops=2)
    assert "US:8" in {x.node_id for x in two}  # Hub2 reached via B at 2 hops
    hub2 = next(x for x in two if x.node_id == "US:8")
    assert hub2.hops == 2 and len(hub2.path) == 2  # provenance chain Hub→B→Hub2


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


# --- token usage (the 2026-08-04 rider) ---------------------------------------------------------


class _UsageMsg:
    """A minimal Anthropic message: one tool_use block plus a usage record."""

    def __init__(self, stop_reason: str = "tool_use") -> None:
        self.stop_reason = stop_reason
        self.usage = type("U", (), {"input_tokens": 1234, "output_tokens": 567})()
        self.content = [type("B", (), {"type": "tool_use", "input": {"ok": True}})()]


def _client(msg: object) -> object:
    import threading

    from vinci.graph.llm import AnthropicLlmClient
    c = AnthropicLlmClient.__new__(AnthropicLlmClient)
    c._model, c._max_tokens, c._usage = "m", 16384, threading.local()  # type: ignore[attr-defined]
    c._client = type("C", (), {"messages": type("M", (), {         # type: ignore[attr-defined]
        "create": staticmethod(lambda **kw: msg)})()})()
    return c


def test_the_client_records_token_usage() -> None:
    """THE RIDER. Nothing measured actual tokens, so cost was unmeasured and the 2026-08-04
    crowding question had to be answered by counting log characters and dividing by a GUESSED
    chars-per-token. Worse, `synthesis.py` reports "(likely truncated)" from MISSING FIELDS alone —
    an inference — and on SMPL it said so about a response using a fifth of its budget."""
    c = _client(_UsageMsg())
    assert c.last_usage is None                                    # type: ignore[attr-defined]
    c.extract(system="s", user="u", tool={"name": "t"})            # type: ignore[attr-defined]
    assert c.last_usage == {                                       # type: ignore[attr-defined]
        "input_tokens": 1234, "output_tokens": 567, "max_tokens": 16384,
        # Both cache fields ALWAYS present, 0 when the call did not cache — see `last_usage`.
        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}


def test_usage_is_recorded_even_when_the_call_raises() -> None:
    """THE PROPERTY THE FIRST CUT CLAIMED AND DID NOT PIN. Usage is written BEFORE the truncation
    guard, because the FAILING call is the one whose token count you most want — a count recorded
    only on success would be missing in exactly the case that prompted the rider."""
    import pytest as _pytest

    from vinci.graph.llm import LlmError
    c = _client(_UsageMsg(stop_reason="max_tokens"))
    with _pytest.raises(LlmError, match="truncated"):
        c.extract(system="s", user="u", tool={"name": "t"})         # type: ignore[attr-defined]
    assert c.last_usage == {                                        # type: ignore[attr-defined]
        "input_tokens": 1234, "output_tokens": 567, "max_tokens": 16384,
        # Both cache fields ALWAYS present, 0 when the call did not cache — see `last_usage`.
        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}, (
        "usage was lost on the raising path — recorded after the guard instead of before it")

