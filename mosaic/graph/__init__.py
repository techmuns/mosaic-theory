"""Graph track — the 1-hop dependency graph + Test 0 (validating the parallel-native moat).

Offline and separate from the forward loop: the EDGAR who-names-whom graph is scored against the CIQ
ground truth (Test 0) to decide whether the graph artifact is good enough to be worth pursuing — the
moat is uncapturable if the graph is noisy, regardless of whether the lag exists.
"""

from mosaic.graph.filings import html_to_text, latest_10k_excerpts, relevant_excerpts
from mosaic.graph.llm import AnthropicLlmClient, LlmClient, LlmError

__all__ = [
    "AnthropicLlmClient",
    "LlmClient",
    "LlmError",
    "html_to_text",
    "latest_10k_excerpts",
    "relevant_excerpts",
]
