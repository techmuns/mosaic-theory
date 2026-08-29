"""Swappable LLM client for the graph track (who-names-whom extraction).

The model is a **config parameter** (``graph_llm_model``, default Claude Opus 5 — operator ruling
2026-08-29) behind this interface — accuracy here gates the moat hypothesis, so we do not use the
cheapest model. Extraction is forced through a tool-use schema so the model returns validated
structured output, not prose. Opus 4.8 held the default after a groundedness benchmark (see
``config.graph_llm_model`` — the benchmark has not yet been re-run on Opus 5, accepted with its
falsifier there); the model is still a swap-the-config knob, not a runtime router.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from vinci.config import Config, get_config, require_env


class LlmError(RuntimeError):
    """The model did not return usable structured output."""


class LlmClient(ABC):
    @abstractmethod
    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        """Force the model to call ``tool`` (a JSON-schema tool spec) and return its input dict."""

    @property
    @abstractmethod
    def model(self) -> str: ...


class AnthropicLlmClient(LlmClient):
    """Anthropic adapter — forces a single tool call and returns its structured input."""

    def __init__(self, *, model: str, max_tokens: int = 16384, api_key: str | None = None) -> None:
        import anthropic  # lazy: the package only needs anthropic for the graph track

        self._model = model
        self._max_tokens = max_tokens
        self._last_usage: dict[str, int] | None = None
        self._client = anthropic.Anthropic(api_key=api_key or require_env("ANTHROPIC_API_KEY"))

    @classmethod
    def from_config(cls, config: Config | None = None) -> AnthropicLlmClient:
        return cls(model=(config or get_config()).graph_llm_model)

    @property
    def model(self) -> str:
        return self._model

    @property
    def last_usage(self) -> dict[str, int] | None:
        """Token usage of the MOST RECENT ``extract`` call, or ``None`` before any call.

        NOTHING MEASURED THIS BEFORE, and the cost of that showed up twice on 2026-08-04. First,
        `synthesis.py` reports "(likely truncated)" whenever a tool call comes back missing fields —
        an INFERENCE, not a measurement — and on SMPL it said so about a response using a FIFTH of
        its budget. Second, asked whether an enlarged brief was crowding the output, the answer had
        to be estimated by counting characters in a log and dividing by a guessed chars-per-token,
        because the real number was never kept. One field retires both.
        """
        return self._last_usage

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        msg = self._client.messages.create(  # type: ignore[call-overload]  # plain dicts ok at runtime
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": user}],
        )
        # RECORD USAGE BEFORE ANY RAISE, so a truncated or malformed call is still measurable —
        # the failing call is the one whose token count you most want.
        u = getattr(msg, "usage", None)
        self._last_usage = {
            "input_tokens": int(getattr(u, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(u, "output_tokens", 0) or 0),
            "max_tokens": self._max_tokens,
        } if u is not None else None
        # FAIL LOUD on truncation: a tool call cut off at max_tokens yields a PARTIAL input dict
        # (trailing required fields dropped). Never accept it as complete — raise so the caller
        # marks the result UNAVAILABLE rather than surfacing silently-missing fields as blanks.
        if msg.stop_reason == "max_tokens":
            raise LlmError(
                f"model {self._model} truncated at max_tokens={self._max_tokens} — tool call "
                "incomplete; raise the cap or shrink the prompt"
            )
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise LlmError(f"model {self._model} returned no tool_use block (stop={msg.stop_reason})")
