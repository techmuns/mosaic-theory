"""The five synthesis draws cache their prompt; nothing else does.

MEASURED BEFORE IT WAS BUILT (`docs/records/2026-10-05-pending-after-the-forward-multiples.md`).
A synthesis sends ONE prompt five times in a row — 113K-212K tokens, identical across draws, 87%
of synthesis cost — and before this every draw re-billed all of it. A probe on BRBR's real prompt
(`claude-opus-4-8`, this request shape, forced tool included) wrote 112,791 tokens once and read
them on each re-send: ~$0.82 against ~$1.70 for three calls. Caching reprices the prompt; it does
not change a returned token, so the draw gate's samples stay independent.

THREE WAYS TO GET IT WRONG, each pinned below: caching a prompt nobody re-sends (a 25% write
surcharge on every single-call phase), losing the real prompt size from the usage log
(`input_tokens` becomes the uncached remainder), and a cache that silently stops hitting — which
does not fail, it only bills.
"""

from __future__ import annotations

import typing
import warnings
from types import SimpleNamespace

import pytest

from tests.test_dossier import _minimal_mech
from tests.test_synthesis_draws import _LEANS, _payload
from vinci.dossier import synthesis as syn
from vinci.graph.llm import AnthropicLlmClient, LlmError

_UNCACHED_KEYS = {"model", "max_tokens", "system", "tools", "tool_choice", "messages"}


def _spy_client(
    usage: object | None = None,
) -> tuple[AnthropicLlmClient, list[dict[str, typing.Any]]]:
    """A real client with a SPY transport: every request's kwargs recorded, nothing sent."""
    client = AnthropicLlmClient(model="claude-x", api_key="test")
    seen: list[dict[str, typing.Any]] = []

    def create(**kw: typing.Any) -> typing.Any:
        seen.append(kw)
        return SimpleNamespace(
            content=[SimpleNamespace(type="tool_use", input={"ok": True})], stop_reason="tool_use",
            usage=usage or SimpleNamespace(input_tokens=1, output_tokens=1))

    client._client = SimpleNamespace(messages=SimpleNamespace(create=create))  # noqa: SLF001
    return client, seen


# --- the client --------------------------------------------------------------------------------

def test_a_cached_call_asks_the_api_to_cache_the_prompt() -> None:
    """(+) `cache=True` reaches the request as top-level automatic caching — the shape the probe
    measured working with a forced tool call on `claude-opus-4-8`."""
    client, seen = _spy_client()
    client.extract(system="s", user="u", tool={"name": "t"}, cache=True)
    assert seen[0]["cache_control"] == {"type": "ephemeral"}


def test_an_uncached_call_is_byte_identical_to_before() -> None:
    """(−) THE DEFAULT SENDS NOTHING NEW. A write that is never read back bills 1.25x input for
    nothing, and every single-call phase — covenant and driver extraction, graph, themes — is that
    case. Pinned as the exact key set, so neither an always-on key nor `cache_control: None`
    passes."""
    client, seen = _spy_client()
    client.extract(system="s", user="u", tool={"name": "t"})
    assert set(seen[0]) == _UNCACHED_KEYS


def test_usage_keeps_the_real_prompt_size_once_calls_cache() -> None:
    """(+) On a cached re-send `input_tokens` is a few dozen; the prompt lives in the cache
    fields. Dropping them would make every log line after this change report a 112K-token prompt
    as 24 tokens — the probe's real figures."""
    client, _ = _spy_client(SimpleNamespace(input_tokens=24, output_tokens=64,
                                            cache_creation_input_tokens=0,
                                            cache_read_input_tokens=112_791))
    client.extract(system="s", user="u", tool={"name": "t"}, cache=True)
    u = client.last_usage
    assert u is not None
    assert u["cache_read_input_tokens"] == 112_791 and u["cache_creation_input_tokens"] == 0
    assert u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"] \
        == 112_815


# --- the draw loop -----------------------------------------------------------------------------

class _Recording:
    """Scripted draws that RECORD whether each call asked for the cache, and report usage the way
    the real client does: the first send writes the prompt, later sends read it — unless told
    which draw should miss."""

    def __init__(self, *, miss_on: int | None = None, cache_fields: bool = True) -> None:
        self.cache_flags: list[bool] = []
        self._miss_on, self._fields = miss_on, cache_fields
        self.last_usage: dict[str, int] | None = None

    @property
    def model(self) -> str:
        return "recording"

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        self.cache_flags.append(cache)
        n = len(self.cache_flags)
        first, missed = n == 1, n == self._miss_on
        usage = {"input_tokens": 24 if not missed else 1000, "output_tokens": 50}
        if self._fields:
            usage |= {"cache_creation_input_tokens": 1000 if first else 0,
                      "cache_read_input_tokens": 0 if (first or missed) else 1000}
        self.last_usage = usage
        return _payload(_LEANS["mixed"], draw=n)


class _NoCacheParam:
    """A client whose `extract` has NO `cache` parameter — so any call that passes one raises."""

    model = "strict"

    def extract(self, *, system: str, user: str,
                tool: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return _payload(_LEANS["mixed"])


def test_every_draw_of_a_multi_draw_build_asks_for_the_cache() -> None:
    """(+) Five draws, five requests asking to cache: the first writes, the other four read."""
    llm = _Recording()
    syn.synthesize(_minimal_mech(), llm=llm, ticker="X", name="X Co",  # type: ignore[arg-type]
                   draws=syn.SYNTHESIS_DRAWS)
    assert llm.cache_flags == [True] * syn.SYNTHESIS_DRAWS


def test_a_single_draw_passes_no_cache_argument_at_all() -> None:
    """(−) One draw re-sends nothing, so caching it would be a pure surcharge — and its request
    must stay byte-identical to every build before caching existed. A client with no `cache`
    parameter proves no argument is passed, not merely `False`."""
    s, _flags, _log = syn.synthesize(_minimal_mech(), llm=_NoCacheParam(),  # type: ignore[arg-type]
                                     ticker="X", name="X Co", draws=1)
    assert s is not None


# --- the miss guard ----------------------------------------------------------------------------

def test_a_draw_that_reads_nothing_is_named_with_its_cause() -> None:
    """(+) Inside the cache lifetime a miss means the prompt was not cached or not reused —
    a timestamp in the facts, a reordered dict, draws moved onto a thread pool."""
    sends = [(1, {"cache_read_input_tokens": 0, "cache_creation_input_tokens": 1000,
                  "input_tokens": 24}, 0.0),
             (2, {"cache_read_input_tokens": 0, "cache_creation_input_tokens": 1000,
                  "input_tokens": 24}, 60.0)]
    [miss] = syn._cache_misses(sends)
    assert "draw 2" in miss and "1,024-token prompt" in miss and "inside the cache lifetime" in miss


def test_a_miss_past_the_lifetime_is_called_expiry() -> None:
    """(+) A draw that started more than 300s after the last outlived its entry; the remedy differs
    (a slow draw, not a broken prefix), so the message says which."""
    sends = [(1, {"cache_read_input_tokens": 0}, 0.0), (2, {"cache_read_input_tokens": 0}, 400.0)]
    [miss] = syn._cache_misses(sends)
    assert "past the 300s cache lifetime" in miss


def test_no_miss_is_reported_when_it_cannot_be_judged_or_did_not_happen() -> None:
    """(−) Three non-events: every re-send read the cache; a client that reports no cache fields
    (absence is not evidence of a miss); and the FIRST send, which writes and never reads."""
    hits = [(1, {"cache_read_input_tokens": 0}, 0.0), (2, {"cache_read_input_tokens": 900}, 50.0)]
    blind = [(1, {"input_tokens": 1000}, 0.0), (2, {"input_tokens": 1000}, 50.0)]
    writer_only = [(1, {"cache_read_input_tokens": 0}, 0.0)]
    assert syn._cache_misses(hits) == []
    assert syn._cache_misses(blind) == []
    assert syn._cache_misses(writer_only) == []


def test_a_miss_warns_the_operator_and_never_reaches_the_dossier() -> None:
    """(+/−) END TO END through `synthesize`: a draw that re-bills its prompt WARNS and is written
    to the call log — and is kept OFF the returned flags, which become dossier caveats. A cache
    miss is a cost event; it cannot touch a fact, so it has no business on the decision surface."""
    with pytest.warns(syn.PromptCacheMissWarning, match="draw 3 read 0"):
        s, flags, log = syn.synthesize(_minimal_mech(), llm=_Recording(miss_on=3),  # type: ignore[arg-type]
                                       ticker="X", name="X Co", draws=syn.SYNTHESIS_DRAWS)
    assert s is not None
    assert "=== PROMPT CACHE MISSED ===" in log and "draw 3 read 0" in log
    assert not [f for f in flags if "cache" in f.lower()], flags


def test_a_healthy_build_is_silent() -> None:
    """(−) Every re-send read the cache, so nothing warns and the log carries no miss section."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", syn.PromptCacheMissWarning)
        _s, _flags, log = syn.synthesize(_minimal_mech(), llm=_Recording(),  # type: ignore[arg-type]
                                         ticker="X", name="X Co", draws=syn.SYNTHESIS_DRAWS)
    assert "PROMPT CACHE MISSED" not in log
    assert '"cache_read_input_tokens": 1000' in log and '"started_s"' in log


class _RaisesOnTwo(_Recording):
    """Draw 2 comes back unusable (the API answered, so the cache was touched) and draw 3 misses."""

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        out = super().extract(system=system, user=user, tool=tool, cache=cache)
        if len(self.cache_flags) == 2:
            raise LlmError("no tool_use block")
        return out


def test_a_raised_draw_still_anchors_the_next_gap(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) REGRESSION — the gap is measured from the draw that was SENT before, not the last one
    that returned. Draw 2 raised at 200s; draw 3 started at 360s and missed. Measured from draw 1
    the 360s gap reads as expiry; measured from draw 2 it is 160s — inside the lifetime, so the
    real cause is a prompt not cached or not reused, and that is what must be said."""
    clock = iter([0.0, 0.0, 200.0, 360.0, 420.0, 480.0])
    monkeypatch.setattr(syn.time, "monotonic", lambda: next(clock))
    with pytest.warns(syn.PromptCacheMissWarning) as rec:
        syn.synthesize(_minimal_mech(), llm=_RaisesOnTwo(miss_on=3),  # type: ignore[arg-type]
                       ticker="X", name="X Co", draws=syn.SYNTHESIS_DRAWS)
    [miss] = [str(w.message) for w in rec]
    assert "draw 3 read 0" in miss and "160s after draw 2" in miss
    assert "inside the cache lifetime" in miss and "past the" not in miss


def test_a_raised_draw_is_never_itself_judged() -> None:
    """(−) A raised draw carries no usage, so it supplies timing only and is never a miss."""
    sends = [(1, {"cache_read_input_tokens": 0}, 0.0), (2, {}, 60.0),
             (3, {"cache_read_input_tokens": 900}, 120.0)]
    assert syn._cache_misses(sends) == []
