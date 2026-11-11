"""THE SEC CHECK SENDS NOTHING, AND CHECKS WHAT THE PIPELINES CHECK (fix request 2, RE1-D17).

`validate_keys.check_sec` used to GET a submissions document, with "vinci-research validate-keys"
as the User-Agent when the secret was unset: one SEC request with no declared contact, outside the
machine's shared SEC budget (`vinci.netcache.sec_pace`), proving only that EDGAR was up. The
secret is an identity, not a key, so the check now applies `vinci.config.sec_user_agent`'s own
rule to it, sends no request, and fails the run only when a set value would be refused.
"""
from __future__ import annotations

from typing import Any

import httpx
import pytest

from tests.validate_keys_support import validator
from vinci import config


def _no_request(*_a: Any, **_k: Any) -> Any:
    raise AssertionError("check_sec sent a request")


@pytest.fixture
def vk(monkeypatch: pytest.MonkeyPatch) -> Any:
    v = validator()
    for name in ("get", "request", "head", "post"):
        monkeypatch.setattr(httpx, name, _no_request)
    return v


@pytest.mark.parametrize(("value", "ok", "says"), [
    (None, True, "PASS — not set"),
    ("", True, "PASS — not set"),
    ("Jane Analyst jane@example.org", True, "PASS — declares a contact"),
    ("Jane Analyst your@email.com", False, "FAIL — still the .env.example placeholder"),
    ("Distinctive Name Without Mail", False, "FAIL — carries no contact email"),
])
def test_the_sec_check_applies_the_pipelines_rule_and_sends_nothing(
        vk: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        value: str | None, ok: bool, says: str) -> None:
    """Both halves: an unset or contact-bearing value passes, a placeholder or contact-less one
    fails — and no value reaches EDGAR, or the log (the secret is never printed)."""
    if value is None:
        monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    else:
        monkeypatch.setenv("SEC_USER_AGENT", value)
    assert vk.check_sec() is ok
    out = capsys.readouterr().out
    assert f"SEC_USER_AGENT: {says}" in out
    assert not value or value not in out


def test_the_sec_rule_is_vincis_own(vk: Any) -> None:
    """The script cannot import vinci (its workflow installs only anthropic and httpx), so its copy
    of the rule is pinned to the one every SEC request is checked against."""
    assert vk.SEC_UA_PLACEHOLDER_EMAIL == config._SEC_UA_PLACEHOLDER_EMAIL
    assert vk.SEC_UA_EMAIL.pattern == config._EMAIL.pattern


def test_a_refused_sec_value_turns_the_validator_red(
        vk: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Wired into the verdict: a set value the pipelines would refuse fails the run, like a set
    Tiingo key that is refused. NEGATIVE: a good one leaves the run green."""
    for name in ("check_anthropic", "check_polygon", "check_tiingo", "check_r2"):
        monkeypatch.setattr(vk, name, lambda: True)
    monkeypatch.setenv("SEC_USER_AGENT", "Distinctive Name Without Mail")
    assert vk.main() == 1
    monkeypatch.setenv("SEC_USER_AGENT", "Jane Analyst jane@example.org")
    assert vk.main() == 0
