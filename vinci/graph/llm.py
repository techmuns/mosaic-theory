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
    def extract(
        self, *, system: str, user: str, tool: dict[str, Any], cache: bool = False,
    ) -> dict[str, Any]:
        """Force the model to call ``tool`` (a JSON-schema tool spec) and return its input dict.

        ``cache`` declares that the caller is about to send this EXACT prompt again. It may change
        what the call COSTS, never what it returns — see :class:`AnthropicLlmClient`."""

    @property
    @abstractmethod
    def model(self) -> str: ...


#: SAMPLING PARAMETERS ARE NOT AVAILABLE ON THIS MODEL FAMILY — DO NOT ADD THEM BACK.
#: `messages.create` here passes NO `temperature`, `top_p` or `top_k`, and that is deliberate:
#: the API REMOVED them on Opus 4.7/4.8 (and the Fable/Sonnet-5 tier). Sending one is not ignored,
#: it is a hard failure — measured 2026-09-24 against `claude-opus-4-8`:
#:
#:     BadRequestError: 400 — {'type': 'invalid_request_error',
#:                             'message': '`temperature` is deprecated for this model.'}
#:
#: Every LLM phase in the package runs through this one call site, so a single added parameter
#: takes down dossier synthesis, the graph extractions and the theme phases together. It did:
#: five names failed assembly this way before the parameter was removed again.
#:
#: WHY ANYONE WOULD TRY. Artifacts here are supposed to be reproducible from their inputs, and
#: `vinci/dossier/assemble.py` used to reason about that as "the property temperature-0 protects".
#: It never did — no temperature was ever passed — and it now CANNOT: there is no sampling knob and
#: no seed on this model. Identical inputs may produce different syntheses, and where a lean label
#: sits near a boundary that `derive_proposal` maps deterministically, the machine's PROPOSAL moves
#: with it (AMZN, 2026-09-23: `strongly-bullish`/BUY and `mixed`/none from the same inputs).
#: Reproducibility, if the fund wants it, has to be bought at the DESIGN layer — e.g. drawing more
#: than once and refusing a proposal the draws disagree on — never by a request parameter.
_REJECTED_SAMPLING_PARAMS = ("temperature", "top_p", "top_k")


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
    def max_tokens(self) -> int:
        return self._max_tokens

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

        ``input_tokens`` IS ONLY THE UNCACHED REMAINDER once a call caches. The real prompt size is
        ``input_tokens + cache_creation_input_tokens + cache_read_input_tokens`` — on a cached
        re-send of a 200K-token prompt ``input_tokens`` reads a few dozen. Both cache fields are
        always present (0 when the call did not cache), so a reader never has to guess which shape
        a log line has.
        """
        return self._last_usage

    def extract(
        self, *, system: str, user: str, tool: dict[str, Any], cache: bool = False,
    ) -> dict[str, Any]:
        # PROMPT CACHING — ONLY WHEN THE CALLER WILL RE-SEND THIS EXACT PROMPT, and never by
        # default. Measured 2026-10-05 on BRBR's real synthesis prompt (`claude-opus-4-8`, this
        # request shape, forced tool included): three sequential sends wrote 112,791 tokens once
        # and READ them twice, ~$0.82 against ~$1.70 uncached. The docs state caching has no effect
        # on output tokens, so the five-draw gate's draws stay independent samples.
        #
        # OFF BY DEFAULT BECAUSE A WRITE NOBODY READS IS A SURCHARGE: the first send bills 1.25x
        # input, which only pays back on a re-send inside the 5-minute TTL. Every single-call phase
        # here — covenant and driver extraction, graph, themes — would pay 25% more for nothing.
        # And the re-sends must be SEQUENTIAL: an entry is readable only once the first response
        # begins, so parallel identical calls all pay full price.
        #
        # ABSENT, NOT `None`, when off: an uncached request is byte-identical to every request this
        # package has ever sent.
        extra: dict[str, Any] = {"cache_control": {"type": "ephemeral"}} if cache else {}
        msg = self._client.messages.create(  # type: ignore[call-overload]  # plain dicts ok at runtime
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": user}],
            **extra,
        )
        # RECORD USAGE BEFORE ANY RAISE, so a truncated or malformed call is still measurable —
        # the failing call is the one whose token count you most want.
        u = getattr(msg, "usage", None)
        self._last_usage = {
            "input_tokens": int(getattr(u, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(u, "output_tokens", 0) or 0),
            "cache_creation_input_tokens": int(getattr(u, "cache_creation_input_tokens", 0) or 0),
            "cache_read_input_tokens": int(getattr(u, "cache_read_input_tokens", 0) or 0),
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
