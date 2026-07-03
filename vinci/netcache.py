"""A small cached, throttled, retrying HTTP GET client — shared by the resolver and the EDGAR
and EOD clients so politeness/caching logic lives in exactly one place.

Why this exists
---------------
- **Pacing.** SEC fair-access is ~10 req/s and Polygon's free tier ~5 req/min; exceeding either
  gets you blocked. A per-host minimum interval enforces politeness centrally.
- **Caching.** SEC reference files and immutable filings should not be refetched every run; an
  on-disk cache (with optional TTL) keeps reruns fast and idempotent.
- **Fail-loud.** Auth/permanent errors raise immediately; only transient errors (429/5xx) retry
  with backoff. Nothing degrades silently.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


class HttpError(RuntimeError):
    """A non-retryable HTTP failure (auth, 4xx other than 429, or retries exhausted)."""


@dataclass(frozen=True)
class _CacheEntry:
    url: str
    fetched_at: float
    text: str


class CachedHttp:
    """Synchronous cached GET with per-instance throttle and bounded retries.

    One instance per upstream (SEC, Polygon), each with its own ``min_interval_sec`` and default
    headers. Thread-safety is not required — the orchestrator is single-threaded by design.
    """

    def __init__(
        self,
        *,
        cache_dir: Path,
        user_agent: str,
        min_interval_sec: float,
        max_retries: int = 4,
        timeout_sec: float = 30.0,
        namespace: str = "http",
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._cache_dir = cache_dir / namespace
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._min_interval = min_interval_sec
        self._max_retries = max_retries
        self._last_request_at = 0.0
        # extra_headers carries secrets like ``Authorization: Bearer <key>`` so the key travels in a
        # header, never in the request URL — keeping it out of the on-disk cache, logs, and errors.
        headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}
        if extra_headers:
            headers.update(extra_headers)
        self._client = httpx.Client(headers=headers, timeout=timeout_sec, follow_redirects=True)

    # --- public API ---------------------------------------------------------------------------
    def get_text(
        self,
        url: str,
        *,
        ttl_seconds: float | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """GET ``url`` and return the body text, using the on-disk cache when fresh.

        ``ttl_seconds=None`` means cache forever (use for immutable resources); a number means
        refetch once the cached copy is older than that.
        """
        full_url = self._with_params(url, params)
        cached = self._read_cache(full_url, ttl_seconds)
        if cached is not None:
            return cached
        text = self._fetch_with_retries(full_url)
        self._write_cache(full_url, text)
        return text

    def get_json(
        self,
        url: str,
        *,
        ttl_seconds: float | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return json.loads(self.get_text(url, ttl_seconds=ttl_seconds, params=params))

    def post_json(
        self,
        url: str,
        *,
        json_body: dict[str, Any],
        ttl_seconds: float | None = None,
    ) -> Any:
        """POST a JSON body and return the parsed JSON, cached by (url + body) — for query APIs
        whose filters don't fit a GET (e.g. FINRA's ``compareFilters``). Same throttle/retry/fail-
        loud path as GET; the cache key folds in the body so distinct queries don't collide."""
        cache_key = f"{url}\n#POST#{json.dumps(json_body, sort_keys=True)}"
        cached = self._read_cache(cache_key, ttl_seconds)
        if cached is not None:
            return json.loads(cached)
        text = self._fetch_with_retries(url, json_body=json_body)
        self._write_cache(cache_key, text)
        return json.loads(text)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> CachedHttp:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- internals ----------------------------------------------------------------------------
    @staticmethod
    def _with_params(url: str, params: dict[str, Any] | None) -> str:
        if not params:
            return url
        request = httpx.Request("GET", url, params=params)
        return str(request.url)

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json"

    def _read_cache(self, url: str, ttl_seconds: float | None) -> str | None:
        path = self._cache_path(url)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text())
            entry = _CacheEntry(**raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None  # corrupt cache → refetch
        if ttl_seconds is not None and (time.time() - entry.fetched_at) > ttl_seconds:
            return None
        return entry.text

    def _write_cache(self, url: str, text: str) -> None:
        entry = _CacheEntry(url=url, fetched_at=time.time(), text=text)
        self._cache_path(url).write_text(json.dumps(entry.__dict__))

    def _throttle(self) -> None:
        if self._min_interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        wait = self._min_interval - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _fetch_with_retries(
        self, url: str, *, json_body: dict[str, Any] | None = None
    ) -> str:
        backoff = 1.0
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._throttle()
            try:
                resp = (
                    self._client.post(url, json=json_body)
                    if json_body is not None
                    else self._client.get(url)
                )
            except httpx.HTTPError as exc:  # transport-level (timeout, connection)
                last_exc = exc
            else:
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code in (429, 500, 502, 503, 504):
                    last_exc = HttpError(f"{resp.status_code} from {url}")
                else:
                    # 401/403/404 etc. — permanent; fail loud immediately.
                    raise HttpError(
                        f"Non-retryable {resp.status_code} from {url}: {resp.text[:200]}"
                    )
            if attempt < self._max_retries:
                time.sleep(backoff)
                backoff = min(backoff * 2, 30.0)
        raise HttpError(f"Exhausted retries for {url}") from last_exc
