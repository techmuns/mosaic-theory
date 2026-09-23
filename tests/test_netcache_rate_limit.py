"""How the shared HTTP client answers a RATE LIMIT, as opposed to a server error.

A 429 is a CLOCK: the limit is enforced over a rolling window, so a retry inside that window is
refused by the same window that refused the first call. A 5xx is not a clock — retrying it fast is
right. Until 2026-09-23 both shared one exponential ladder (1+2+4+8+16 ≈ 31s) against Polygon's
PER-MINUTE limit, so every 429 retry landed inside the window that had just refused, and the
weekly screen died with `Exhausted retries for …/2021-09-29`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from vinci.netcache import _RATE_LIMIT_WAIT_SEC, CachedHttp, HttpError


def _http(tmp_path: Path, handler: Any, *, max_retries: int = 4) -> CachedHttp:
    http = CachedHttp(cache_dir=tmp_path, user_agent="test", min_interval_sec=0.0,
                      max_retries=max_retries, namespace="probe")
    http._client = httpx.Client(transport=httpx.MockTransport(handler))  # noqa: SLF001
    return http


def _slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record what the client WOULD wait, without waiting: the durations are the behaviour."""
    waits: list[float] = []
    monkeypatch.setattr("vinci.netcache.time.sleep", waits.append)
    return waits


def test_a_rate_limit_waits_out_the_window_before_retrying(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊕ 429 then 200: the client waits the WINDOW (61s), not the 1s first rung of the ladder.

    Polygon sends no `Retry-After` and no rate-limit headers (checked 2026-09-23 — the body only
    says "wait or upgrade"), so the window is the only honest number available."""
    seen = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["n"] += 1
        if seen["n"] == 1:
            return httpx.Response(429, json={"status": "ERROR", "error": "too many requests"})
        return httpx.Response(200, text="ok")

    waits = _slept(monkeypatch)
    assert _http(tmp_path, handler).get_text("https://x.test/a") == "ok"
    assert waits == [_RATE_LIMIT_WAIT_SEC] and _RATE_LIMIT_WAIT_SEC > 60.0


def test_a_server_error_still_retries_fast(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ a 5xx must NOT be punished with a minute — it is not a clock. Three 503s then a 200 keep
    the exponential ladder (1, 2, 4)."""
    seen = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["n"] += 1
        return httpx.Response(503) if seen["n"] <= 3 else httpx.Response(200, text="ok")

    waits = _slept(monkeypatch)
    assert _http(tmp_path, handler).get_text("https://x.test/b") == "ok"
    assert waits == [1.0, 2.0, 4.0]


def test_a_rate_limit_that_never_clears_still_fails_loud(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ waiting longer is not waiting forever: the retry budget is unchanged and the failure is
    still the loud one the operator saw. Every wait is a full window."""
    waits = _slept(monkeypatch)
    http = _http(tmp_path, lambda r: httpx.Response(429), max_retries=2)
    with pytest.raises(HttpError, match="Exhausted retries"):
        http.get_text("https://x.test/c")
    assert waits == [_RATE_LIMIT_WAIT_SEC, _RATE_LIMIT_WAIT_SEC]


def test_a_mixed_failure_sequence_waits_per_cause(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊕ the two paths do not contaminate each other: a 503 then a 429 then a 200 waits 1s then a
    full window — the rate-limit wait is not a function of how many 5xx preceded it."""
    codes = iter([503, 429, 200])

    def handler(request: httpx.Request) -> httpx.Response:
        c = next(codes)
        return httpx.Response(c, text="ok" if c == 200 else "")

    waits = _slept(monkeypatch)
    assert _http(tmp_path, handler).get_text("https://x.test/d") == "ok"
    assert waits == [1.0, _RATE_LIMIT_WAIT_SEC]
