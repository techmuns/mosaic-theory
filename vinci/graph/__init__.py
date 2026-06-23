"""Graph track — the 1-hop dependency graph + Test 0 (validating the parallel-native moat).

Offline and separate from the forward loop: the EDGAR who-names-whom graph is scored against the CIQ
ground truth (Test 0) to decide whether the graph artifact is good enough to be worth pursuing — the
moat is uncapturable if the graph is noisy, regardless of whether the lag exists.
"""

from vinci.graph.extract import EXTRACT_TOOL, GraphEdge, extract_graph_edges
from vinci.graph.filings import html_to_text, latest_10k_excerpts, relevant_excerpts
from vinci.graph.judge import JUDGE_TOOL, REAL_VERDICTS, judge_edge, judge_edges
from vinci.graph.llm import AnthropicLlmClient, LlmClient, LlmError

__all__ = [
    "EXTRACT_TOOL",
    "JUDGE_TOOL",
    "REAL_VERDICTS",
    "AnthropicLlmClient",
    "GraphEdge",
    "LlmClient",
    "LlmError",
    "extract_graph_edges",
    "html_to_text",
    "judge_edge",
    "judge_edges",
    "latest_10k_excerpts",
    "relevant_excerpts",
]
