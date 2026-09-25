"""What sampling parameters the model calls may carry — and why the answer is NONE.

TWO FACTS, BOTH MEASURED, that point in opposite directions.

1. The artifacts are NOT reproducible. `vinci/dossier/assemble.py` used to justify dating a
   dossier from the fleet as-of rather than the wall clock as protecting a property
   "temperature-0 protects". No temperature was ever passed, so that property never existed:
   AMZN re-assembled twice on IDENTICAL inputs (2026-09-23) returned `strongly-bullish`
   (machine proposal BUY) and `mixed` (proposal none) — a flip across the proposal boundary
   caused by sampling alone.

2. It cannot be fixed with a parameter. `temperature`, `top_p` and `top_k` are REMOVED on this
   model family; sending one is a 400, not a no-op. Measured 2026-09-24 against
   `claude-opus-4-8`: "`temperature` is deprecated for this model." Five names failed assembly
   that way before it was taken back out.

So the guard here is the INVERSE of the obvious one: the request must stay clean, because the
obvious repair for (1) causes an outage. Reproducibility has to be bought at the design layer.
"""

from __future__ import annotations

import typing
from types import SimpleNamespace

from vinci.graph.llm import _REJECTED_SAMPLING_PARAMS, AnthropicLlmClient


def _spy_client() -> tuple[AnthropicLlmClient, list[dict[str, typing.Any]]]:
    """A real client with a SPY transport: every request's kwargs recorded, nothing sent."""
    client = AnthropicLlmClient(model="claude-x", api_key="test")
    seen: list[dict[str, typing.Any]] = []

    def create(**kw: typing.Any) -> typing.Any:
        seen.append(kw)
        return SimpleNamespace(
            content=[SimpleNamespace(type="tool_use", input={"ok": True})],
            stop_reason="tool_use", usage=SimpleNamespace(input_tokens=1, output_tokens=1))

    client._client = SimpleNamespace(messages=SimpleNamespace(create=create))  # noqa: SLF001
    return client, seen


def test_the_model_call_carries_no_sampling_parameter() -> None:
    """⊖ NONE of `temperature` / `top_p` / `top_k` may reach the API.

    Not style — availability. The API removed them on this model family and answers a 400, and
    EVERY LLM phase in the package (dossier synthesis, graph extraction, theme drafting) goes
    through this one call site, so one added parameter fails all of them at once."""
    client, seen = _spy_client()
    client.extract(system="s", user="u", tool={"name": "t"})
    assert len(seen) == 1
    offenders = sorted(p for p in _REJECTED_SAMPLING_PARAMS if p in seen[0])
    assert not offenders, (
        f"the model call now passes {offenders} — the API REMOVED these on this model family and "
        f"answers 400 '`temperature` is deprecated for this model.', which fails every LLM phase "
        f"in the package. Reproducibility cannot be bought this way; see the constant's comment.")


def test_no_call_shape_smuggles_one_in() -> None:
    """⊖ Whatever a phase varies — prompt size, tool, model — the request stays clean."""
    client, seen = _spy_client()
    for tool in ({"name": "a"}, {"name": "b"}, {"name": "c"}):
        client.extract(system="sys", user="u" * 5000, tool=tool)
    assert len(seen) == 3
    assert all(p not in kw for kw in seen for p in _REJECTED_SAMPLING_PARAMS)


def test_the_request_still_carries_what_the_call_actually_needs() -> None:
    """⊕ The negative guard above must not be satisfiable by sending nothing at all."""
    client, seen = _spy_client()
    client.extract(system="s", user="u", tool={"name": "t"})
    assert seen[0]["model"] == "claude-x"
    assert seen[0]["max_tokens"] > 0
    assert seen[0]["tool_choice"] == {"type": "tool", "name": "t"}
    assert seen[0]["messages"] == [{"role": "user", "content": "u"}]
