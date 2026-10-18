"""The theme pipeline's model client: the shared Anthropic adapter (`vinci.graph.llm`), with ONE
addition — the parts of a split completeness review cache the ARTICLE they each resend.

Measured 2026-10-11 on the run that paid for Citi's 60-page "Overcoming Gridlock 2.0": its 22
completeness parts each resent the whole article — 309,342 to 334,027 input tokens per call,
7,130,969 in all, $35.65 of the pass's $39.44 at $5 per million — with 0 prompt-cache tokens.
Every part needs the whole article (a gap's account may cite any block), so the text is never
cut: it goes as a separate first block carrying a cache breakpoint, and the parts after the
first read it at a tenth of the input price. The model receives the same text either way —
caching changes the bill, not the input. OFF by default (`config.PROMPT_CACHE_PARTS`): one
measured run cut the pass's cost 45% but did not SHOW equivalent evidence quality — see the
2026-10-11 record — so adopting it is an operator decision.

`cache=True` means exactly this here. The shared adapter's `cache=True` sets ONE breakpoint at
the end of the whole prompt, which parts that differ after the article never read back — a 25%
write surcharge for nothing — so the pipeline builds this client, never the shared one.
"""

from __future__ import annotations

from typing import Any

from vinci.graph.llm import AnthropicLlmClient, LlmError

#: where the prefix every part of one review shares ends (`completeness.completeness_message`)
ARTICLE_END = "</untrusted_article>"


class ThemeLlmClient(AnthropicLlmClient):
    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        head, end, tail = user.partition(ARTICLE_END)
        if not (cache and end and tail):
            return super().extract(system=system, user=user, tool=tool)
        content = [{"type": "text", "text": head + end, "cache_control": {"type": "ephemeral"}},
                   {"type": "text", "text": tail}]
        msg = self._client.messages.create(  # type: ignore[call-overload]  # plain dicts ok at runtime
            model=self._model, max_tokens=self._max_tokens, system=system, tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": content}])
        # as the shared adapter: usage recorded before any raise; truncation fails loud
        u = getattr(msg, "usage", None)
        self._last_usage = {
            "input_tokens": int(getattr(u, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(u, "output_tokens", 0) or 0),
            "cache_creation_input_tokens": int(getattr(u, "cache_creation_input_tokens", 0) or 0),
            "cache_read_input_tokens": int(getattr(u, "cache_read_input_tokens", 0) or 0),
            "max_tokens": self._max_tokens,
        } if u is not None else None
        if msg.stop_reason == "max_tokens":
            raise LlmError(f"model {self._model} truncated at max_tokens={self._max_tokens} — "
                           "tool call incomplete; raise the cap or shrink the prompt")
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise LlmError(f"model {self._model} returned no tool_use block (stop={msg.stop_reason})")
