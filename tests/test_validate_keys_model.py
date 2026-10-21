"""`validate-keys` pings the model the pipelines call (2026-10-21).

Until then it pinged Haiku while every pipeline calls Opus 4.8, so a key that could use Haiku but
not the pipelines' model passed — and a 404 for that model read as "connectivity, NOT a key
problem" and passed too.
"""

from __future__ import annotations

from typing import Any

import anthropic
import httpx

from tests.test_theme_intelligence_open_leads import _validator
from vinci.config import Config
from vinci.theme_intelligence.config import LLM_MODEL


class _Messages:
    def __init__(self, seen: dict[str, Any], error: Exception | None) -> None:
        self.seen, self.error = seen, error

    def create(self, **kw: Any) -> object:
        self.seen.update(kw)
        if self.error is not None:
            raise self.error
        return object()


def _client(seen: dict[str, Any], error: Exception | None = None) -> Any:
    """A stand-in for `anthropic.Anthropic`: records the request, answers or raises."""
    def make(**_kw: Any) -> Any:
        return type("Client", (), {"messages": _Messages(seen, error)})()
    return make


def _not_found(model: str) -> anthropic.NotFoundError:
    """The error the API returned on 2026-10-21 for a model the key cannot use."""
    url = "https://api.anthropic.com/v1/messages"
    body = {"type": "error", "error": {"type": "not_found_error", "message": f"model: {model}"}}
    return anthropic.NotFoundError(f"Error code: 404 - {body}", body=body,
                                   response=httpx.Response(404, request=httpx.Request("POST", url)))


def test_the_key_check_pings_the_model_the_pipelines_call(monkeypatch: Any, capsys: Any) -> None:
    """The ping's model is the one both pipelines are configured to call — the dossier and graph
    pipeline (`graph_llm_model`) and theme intelligence (`LLM_MODEL`) — and it stays one token."""
    vk = _validator()
    seen: dict[str, Any] = {}
    monkeypatch.setattr(anthropic, "Anthropic", _client(seen))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert vk.check_anthropic() is True
    pipelines = {Config.model_fields["graph_llm_model"].default, LLM_MODEL}
    assert pipelines == {seen["model"]}, f"the pipelines call {pipelines}; the ping {seen['model']}"
    assert seen["max_tokens"] == 1
    assert f"ANTHROPIC_API_KEY: PASS — authenticated; {seen['model']} answered" in (
        capsys.readouterr().out)


def test_a_key_that_cannot_use_the_pipelines_model_fails(monkeypatch: Any, capsys: Any) -> None:
    """A 404 for the model is a key problem, never "connectivity": the run goes red."""
    vk = _validator()
    monkeypatch.setattr(anthropic, "Anthropic", _client({}, _not_found(vk.PIPELINE_MODEL)))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert vk.check_anthropic() is False
    out = capsys.readouterr().out
    assert f"FAIL — NotFoundError: this key cannot use {vk.PIPELINE_MODEL}" in out
    assert "sk-ant-test" not in out


def test_a_connection_error_still_only_warns(monkeypatch: Any, capsys: Any) -> None:
    """NEGATIVE: an unreachable API is the runner's environment, not the key — a WARN that does
    not fail the run (a padded key is refused before this point, by its own check)."""
    vk = _validator()
    err = anthropic.APIConnectionError(
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    monkeypatch.setattr(anthropic, "Anthropic", _client({}, err))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert vk.check_anthropic() is True
    assert "ANTHROPIC_API_KEY: WARN — APIConnectionError" in capsys.readouterr().out
