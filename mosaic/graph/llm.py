"""Swappable LLM client for the graph track (who-names-whom extraction).

The model is a **config parameter** (``graph_llm_model``, default Claude Sonnet 4.6) behind this
interface — accuracy here gates the moat hypothesis, so we do not use the cheapest model. Extraction
is forced through a tool-use schema so the model returns validated structured output, not prose.
Opus is the *diagnostic* fallback (swap the config), not a runtime router.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from mosaic.config import Config, get_config, require_env


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

    def __init__(self, *, model: str, max_tokens: int = 4096, api_key: str | None = None) -> None:
        import anthropic  # lazy: the package only needs anthropic for the graph track

        self._model = model
        self._max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key or require_env("ANTHROPIC_API_KEY"))

    @classmethod
    def from_config(cls, config: Config | None = None) -> AnthropicLlmClient:
        return cls(model=(config or get_config()).graph_llm_model)

    @property
    def model(self) -> str:
        return self._model

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        msg = self._client.messages.create(  # type: ignore[call-overload]  # plain dicts ok at runtime
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": user}],
        )
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise LlmError(f"model {self._model} returned no tool_use block (stop={msg.stop_reason})")
