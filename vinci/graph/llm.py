"""Swappable LLM client for the graph track (who-names-whom extraction).

The model is a **config parameter** (``graph_llm_model``, default ``claude-opus-4-8``) behind this
interface — accuracy here gates the moat hypothesis, so we do not use the cheapest model.
Extraction is forced through a tool-use schema so the model returns validated structured output,
not prose. The operator's 2026-08-29 move to Opus 5 was REVERTED on 2026-09-01 after a synthesis
regression (``config.graph_llm_model``; ``docs/records/2026-09-01-opus5-synthesis-regression.md``);
the model is still a swap-the-config knob, not a runtime router.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Any

from vinci.config import LLM_PRICE_PER_MTOK, Config, get_config, require_env


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
        # PER THREAD (2026-10-23). `assemble_cohort` runs eight names at once on ONE client, so a
        # plain attribute let a thread read the token counts of another thread's call — the
        # synthesis cache check and the run record alike.
        self._usage = threading.local()
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

        ``None`` ALSO AFTER A CALL THAT NEVER GOT A RESPONSE (a connection error, a 4xx): the value
        is cleared when a call starts, so it can never be the previous call's count. It is kept per
        thread — read it on the thread that made the call.
        """
        usage: dict[str, int] | None = getattr(self._usage, "value", None)
        return usage

    def _record_usage(self, msg: Any) -> None:
        """Keep a response's token counts for :attr:`last_usage`, on this thread. ONE writer, used
        by every subclass that sends its own request (the theme client's split-cache parts), so
        the slot and its shape cannot drift between two copies — they did on 2026-10-23, when the
        theme client kept writing the old attribute after it moved."""
        u = getattr(msg, "usage", None)
        self._usage.value = {
            "input_tokens": int(getattr(u, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(u, "output_tokens", 0) or 0),
            "cache_creation_input_tokens": int(getattr(u, "cache_creation_input_tokens", 0) or 0),
            "cache_read_input_tokens": int(getattr(u, "cache_read_input_tokens", 0) or 0),
            "max_tokens": self._max_tokens,
        } if u is not None else None

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
        self._usage.value = None              # a call that raises before a response bills nothing
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
        self._record_usage(msg)
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


def cost_usd(model: str, usage: dict[str, int] | None) -> float | None:
    """List-price USD of one call, from its ``usage`` — ``None`` when the model is not in
    `vinci.config.LLM_PRICE_PER_MTOK` or the call has no usage. UNKNOWN, never zero: a zero would
    read as a free call in every total it joins."""
    if usage is None or model not in LLM_PRICE_PER_MTOK:
        return None
    pin, pout = LLM_PRICE_PER_MTOK[model]
    return (usage.get("input_tokens", 0) * pin
            + usage.get("cache_creation_input_tokens", 0) * pin * 1.25
            + usage.get("cache_read_input_tokens", 0) * pin * 0.1
            + usage.get("output_tokens", 0) * pout) / 1_000_000


class MeteredLlmClient(LlmClient):
    """Wraps a client for ONE unit of work — one name's assembly — and keeps a line per call.

    WHY (2026-10-23, Stage 0 of the agentic-engineering report). Nothing recorded what a dossier
    build cost or which of its calls failed: synthesis read token counts only to judge its own
    cache, the covenant, maturity and driver phases kept none, and `llm_call.log` is git-ignored.
    A change to a prompt cannot be judged without that series.

    THE PHASE IS THE TOOL NAME. Every phase forces its own tool, so the label comes from the call
    itself: nothing upstream has to remember to set it, and it cannot disagree with what was sent.

    A CALL IS COUNTED WHETHER IT RETURNS OR RAISES. A truncated or malformed tool call is billed,
    and it is the call whose cost most needs seeing. The usage is the inner client's, read on this
    thread straight after the call; a call that got no response records ``usage: None``.

    TRANSPARENT TO THE CALLER: the request reaching the inner client is the one the caller made —
    ``cache`` is passed only when the caller set it, so an uncached call stays byte-identical.
    """

    def __init__(self, inner: LlmClient) -> None:
        self._inner = inner
        self.calls: list[dict[str, Any]] = []

    @property
    def model(self) -> str:
        return self._inner.model

    @property
    def last_usage(self) -> dict[str, int] | None:
        usage: dict[str, int] | None = getattr(self._inner, "last_usage", None)
        return usage

    def extract(
        self, *, system: str, user: str, tool: dict[str, Any], cache: bool = False,
    ) -> dict[str, Any]:
        error: str | None = None
        try:
            if cache:
                return self._inner.extract(system=system, user=user, tool=tool, cache=True)
            return self._inner.extract(system=system, user=user, tool=tool)
        except BaseException as exc:      # an interrupted call did not succeed either
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            usage = self.last_usage
            self.calls.append({"phase": str(tool.get("name", "")), "ok": error is None,
                               "error": error, "cached_prompt": cache,
                               "usage": dict(usage) if usage is not None else None})
