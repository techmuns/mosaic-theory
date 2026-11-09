"""Step 3b/3c verification — graph extraction resolution + direction.

These tests lock the deterministic pieces that do not need the network or an API key: how an
LLM-named counterparty is resolved to the internal key and the goods-flow direction. (Test 0's
scoring against CIQ and Test 1's event study were retired with their code on 2026-11-04.)
"""

from __future__ import annotations

from typing import Any

from vinci.graph import GraphEdge, judge_edges
from vinci.graph.extract import _direction, _is_generic_placeholder, _resolve_node
from vinci.graph.llm import LlmClient
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


class _ScriptedJudge(LlmClient):
    """Answers each judge call with the next item: a dict is the tool's answer, an exception is
    raised — the shape of a transient failure (a 529, a malformed tool block)."""

    def __init__(self, script: list[Any]) -> None:
        self._script = iter(script)

    @property
    def model(self) -> str:
        return "fake-judge"

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        step = next(self._script)
        if isinstance(step, Exception):
            raise step
        return dict(step)


def test_a_judge_failure_is_its_own_verdict_never_an_unsupported_edge() -> None:
    """(audit RG-D16) A call that raises is `judge_error`, with the exception in its reason — never
    "unsupported", which is the judge's verdict that the EVIDENCE does not support the edge. It
    counts toward no precision: one real edge of the two judged is 0.5, not 1 of 3."""
    from vinci.graph.judge import JUDGE_ERROR

    edges = [_graph_edge("0000000001"), _graph_edge("0000000002"), _graph_edge("0000000003")]
    rep = judge_edges(_ScriptedJudge([
        {"verdict": "real_supply_chain", "reason": "named supplier"},
        KeyError("content"),
        {"verdict": "unsupported", "reason": "no relationship stated"},
    ]), edges)
    assert rep["by_class"] == {"real_supply_chain": 1, JUDGE_ERROR: 1, "unsupported": 1}
    assert rep["judge_errors"] == 1 and rep["real_edges"] == 1
    assert rep["evidence_precision"] == 0.5
    assert [j["reason"] for j in rep["judged"]] == [
        "named supplier", "judge_error: KeyError: 'content'", "no relationship stated"]


def test_an_answer_outside_the_taxonomy_is_a_judge_error() -> None:
    """(-) No verdict, or one the taxonomy does not name: a judge error naming what came back —
    this too was coerced to "unsupported"."""
    from vinci.graph.judge import JUDGE_ERROR

    rep = judge_edges(_ScriptedJudge([{"reason": "no verdict key"}, {"verdict": "maybe"}]),
                      [_graph_edge("0000000001"), _graph_edge("0000000002")])
    assert rep["by_class"] == {JUDGE_ERROR: 2} and "unsupported" not in rep["by_class"]
    assert rep["judged"][0]["reason"].startswith("judge_error: the judge answered verdict None")
    assert rep["judged"][1]["reason"].startswith("judge_error: the judge answered verdict 'maybe'")
    rep = judge_edges(_ScriptedJudge([{"verdict": "customer", "reason": "sells to X"}]),
                      [_graph_edge("0000000001")])
    assert rep["judged"][0]["reason"].endswith("its reason: sells to X")   # the judge's own words


def test_a_failures_stored_text_is_bounded_and_says_so() -> None:
    """The reason reaches the committed, public map: a long error body is cut, and the cut is
    stated — never a multi-kilobyte provider payload, never a silent truncation."""
    from vinci.graph.judge import REASON_CAP

    rep = judge_edges(_ScriptedJudge([RuntimeError("x" * 5000)]), [_graph_edge("0000000001")])
    reason = rep["judged"][0]["reason"]
    assert reason.endswith(f"… (cut at {REASON_CAP} characters)")
    assert len(reason) < REASON_CAP + 80


def test_with_no_edge_judged_there_is_no_precision() -> None:
    """(-) Every call failed, or there were no edges: the precision is None, never a 0.0 that reads
    as "every edge judged and none real"."""
    assert judge_edges(_ScriptedJudge([]), [])["evidence_precision"] is None
    rep = judge_edges(_ScriptedJudge([RuntimeError("down")]), [_graph_edge("0000000001")])
    assert rep["evidence_precision"] is None and rep["judge_errors"] == 1


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

