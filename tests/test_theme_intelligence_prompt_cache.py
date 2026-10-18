"""The parts of a split completeness review cache the ARTICLE they each resend (llm.py).

Measured 2026-10-11 on the run that paid for Citi's 60-page "Overcoming Gridlock 2.0": 22 parts,
each resending the whole article (309,342 to 334,027 input tokens per call; $35.65 of the
pass's $39.44), with 0 prompt-cache tokens. The model must receive the SAME text — caching may
change the bill, never the input — and nothing else may change: a single call and every other
pass send exactly what the shared adapter sends.

The SDK is replaced by a recorder; nothing here reaches the network.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import vinci.theme_intelligence.completeness as completeness_mod
from tests.test_theme_intelligence_long_articles import AS_OF, LONG, FakeLlm, _pass1
from vinci.graph.llm import LlmError
from vinci.theme_intelligence.completeness import run_completeness, scan_article
from vinci.theme_intelligence.config import load_taxonomy
from vinci.theme_intelligence.extract import Extraction, cost_of
from vinci.theme_intelligence.llm import ARTICLE_END, ThemeLlmClient

USER = ("Publisher: P\n<untrusted_article>\n[b001|paragraph] The article text.\n"
        f"{ARTICLE_END}\n<first_pass_record>\nClaims:\n</first_pass_record>")
TOOL = {"name": "record_completeness", "input_schema": {"type": "object"}}


class Sdk:
    """Stands in for `anthropic.Anthropic().messages`: records each request."""

    def __init__(self, stop: str = "tool_use") -> None:
        self.requests: list[dict[str, Any]] = []
        self.stop = stop
        self.messages = self

    def create(self, **kw: Any) -> Any:
        self.requests.append(kw)
        usage = SimpleNamespace(input_tokens=40, output_tokens=12,
                                cache_creation_input_tokens=0, cache_read_input_tokens=300_000)
        return SimpleNamespace(stop_reason=self.stop, usage=usage, content=[
            SimpleNamespace(type="tool_use", input={"figure_reviews": []})])


def _client(sdk: Sdk) -> ThemeLlmClient:
    c = ThemeLlmClient(model="claude-opus-4-8", max_tokens=100, api_key="offline-test")
    c._client = sdk  # type: ignore[assignment]  # the SDK, replaced: nothing reaches the network
    return c


def test_a_cached_part_sends_the_same_text_with_the_article_as_a_cached_first_block() -> None:
    sdk = Sdk()
    out = _client(sdk).extract(system="s", user=USER, tool=TOOL, cache=True)
    assert out == {"figure_reviews": []}
    (req,) = sdk.requests
    first, second = req["messages"][0]["content"]
    assert first["text"] + second["text"] == USER  # the model receives the same text
    assert first["text"].endswith(ARTICLE_END) and first["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in second and "cache_control" not in req  # one breakpoint only


@pytest.mark.parametrize(("user", "cache"), [(USER, False),  # every single call
                                              ("no article marker in this message", True)])
def test_anything_else_is_sent_exactly_as_the_shared_adapter_sends_it(user: str,
                                                                      cache: bool) -> None:
    sdk = Sdk()
    _client(sdk).extract(system="s", user=user, tool=TOOL, cache=cache)
    (req,) = sdk.requests
    assert req["messages"] == [{"role": "user", "content": user}] and "cache_control" not in req


def test_cache_reads_are_measured_and_priced_at_a_tenth() -> None:
    c = _client(Sdk())
    c.extract(system="s", user=USER, tool=TOOL, cache=True)
    assert c.last_usage is not None and c.last_usage["cache_read_input_tokens"] == 300_000
    assert cost_of("claude-opus-4-8", c.last_usage) == pytest.approx(
        (40 * 5 + 300_000 * 0.5 + 12 * 25) / 1e6)


def test_a_truncated_cached_part_fails_loud_with_its_usage_kept() -> None:
    c = _client(Sdk(stop="max_tokens"))
    with pytest.raises(LlmError, match="truncated"):
        c.extract(system="s", user=USER, tool=TOOL, cache=True)
    assert c.last_usage is not None  # the failing call is still measured


class Recording(FakeLlm):
    def __init__(self, *a: Any, **kw: Any) -> None:
        super().__init__(*a, **kw)
        self.cache_flags: list[tuple[str, bool]] = []

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.cache_flags.append((tool["name"], cache))
        return super().extract(system=system, user=user, tool=tool, cache=cache)


def _flags(tmp: Path, *, parts: bool) -> list[tuple[str, bool]]:
    doc = LONG.doc()
    x = Extraction.model_validate(_pass1(bad_items=False))
    fake = Recording(_pass1(bad_items=False))
    run_completeness(doc, x, scan_article(doc), publisher="P", as_of=AS_OF.isoformat(),
                     taxonomy=load_taxonomy(), client=fake, cache_dir=tmp)
    assert all(ARTICLE_END in u for u in fake.users.values())  # the split point is there
    assert (len(fake.cache_flags) > 1) is parts
    return fake.cache_flags


def test_the_article_cache_is_off_until_its_evidence_quality_is_shown_equivalent(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert completeness_mod.PROMPT_CACHE_PARTS is False  # an operator decision (config.py)
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    assert not any(c for _n, c in _flags(tmp_path, parts=True))


def test_switched_on_only_the_parts_of_a_split_review_ask_for_the_cache(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "PROMPT_CACHE_PARTS", True)
    assert _flags(tmp_path / "one", parts=False) == [("record_completeness", False)]
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    flags = _flags(tmp_path / "parts", parts=True)
    assert len(flags) == 3 and all(c for _n, c in flags)


def test_the_pipeline_builds_the_theme_client_never_the_shared_one(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The shared adapter's cache=True would write at the END of each part and never read."""
    from vinci.theme_intelligence.__main__ import _client

    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-test")
    assert type(_client(required=True)) is ThemeLlmClient
