"""Polite, honest, cached HTTP for publisher pages.

COMPLIANCE RULES THIS ENFORCES, not just documents:
- One identifying User-Agent (`config.USER_AGENT`). No browser spoofing, no header games: a site
  that refuses it is BLOCKED and reported as such — never worked around.
- robots.txt per RFC 9309: a 2xx file is obeyed; a 4xx (incl. 403/404) means "no restrictions"; a
  5xx or network failure FAILS CLOSED (treated as disallow-all) and is reported.
- Per-host spacing = max(source floor, robots Crawl-delay for our agent or `*`).
- Paywalls are not bypassed: a fetched page that is only a teaser is classified PARTIAL by the
  parser and never analysed as a full text.

A failed fetch RETURNS a BLOCKED result (with status and reason) instead of raising, so the caller
can keep the record in its coverage counts — a blocked article must never vanish from the census.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from vinci.theme_intelligence.config import DEFAULT_MIN_CRAWL_DELAY_S, USER_AGENT
from vinci.theme_intelligence.schemas import RetrievalState

MAX_BYTES = 15_000_000


@dataclass
class FetchResult:
    url: str
    final_url: str | None
    status: int | None
    state: RetrievalState
    note: str
    content: bytes | None
    content_type: str | None
    fetched_at: datetime
    sha256: str | None
    cache_path: Path | None
    from_cache: bool
    seconds: float

    @property
    def text(self) -> str | None:
        if self.content is None:
            return None
        return self.content.decode("utf-8", errors="replace")


@dataclass
class _HostPolicy:
    parser: urllib.robotparser.RobotFileParser | None
    robots_status: int | None
    crawl_delay: float
    note: str
    disallow_all: bool = False


@dataclass
class FetchStats:
    requests: int = 0
    cache_hits: int = 0
    blocked: int = 0
    seconds: float = 0.0
    by_host: dict[str, int] = field(default_factory=dict)


class PoliteFetcher:
    def __init__(self, cache_dir: Path, *, user_agent: str = USER_AGENT,
                 min_delay_s: float = DEFAULT_MIN_CRAWL_DELAY_S, timeout_s: float = 45.0,
                 max_retries: int = 2, client: httpx.Client | None = None) -> None:
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent
        self.min_delay_s = min_delay_s
        self.max_retries = max_retries
        self._client = client or httpx.Client(headers={"User-Agent": user_agent},
                                              timeout=timeout_s, follow_redirects=True)
        self._hosts: dict[str, _HostPolicy] = {}
        self._last: dict[str, float] = {}
        self._host_floor: dict[str, float] = {}
        self.stats = FetchStats()
        #: when set, no cached copy older than this is served — a source-health check tests the
        #: LIVE site (its fresh answers are cached, so the scan that follows does not refetch)
        self.ttl_cap: float | None = None

    # -- policy ----------------------------------------------------------------------------------
    def set_host_floor(self, url: str, seconds: float) -> None:
        self._host_floor[urlparse(url).netloc] = seconds

    def host_policy(self, url: str) -> _HostPolicy:
        p = urlparse(url)
        host = p.netloc
        if host in self._hosts:
            return self._hosts[host]
        robots_url = f"{p.scheme}://{host}/robots.txt"
        floor = max(self.min_delay_s, self._host_floor.get(host, 0.0))
        try:
            self._space(host, floor)
            r = self._client.get(robots_url)
            self.stats.requests += 1
            status = r.status_code
        except httpx.HTTPError as exc:
            pol = _HostPolicy(None, None, floor, f"robots.txt unreachable ({type(exc).__name__})"
                              f" — FAIL CLOSED, nothing fetched from {host}", disallow_all=True)
            self._hosts[host] = pol
            return pol
        if 200 <= status < 300:
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(r.text.splitlines())
            delay = rp.crawl_delay(self.user_agent) or rp.crawl_delay("*")
            pol = _HostPolicy(rp, status, max(floor, float(delay or 0.0)),
                              f"robots.txt {status} obeyed" + (f"; Crawl-delay {delay}s"
                                                               if delay else ""))
        elif 400 <= status < 500:
            pol = _HostPolicy(None, status, floor,
                              f"robots.txt {status} — RFC 9309: no restrictions")
        else:
            pol = _HostPolicy(None, status, floor, f"robots.txt {status} — FAIL CLOSED",
                              disallow_all=True)
        self._hosts[host] = pol
        return pol

    def allowed(self, url: str) -> tuple[bool, str]:
        pol = self.host_policy(url)
        if pol.disallow_all:
            return False, pol.note
        if pol.parser is not None and not pol.parser.can_fetch(self.user_agent, url):
            return False, f"robots.txt disallows {urlparse(url).path} for our agent"
        return True, pol.note

    def _space(self, host: str, delay: float) -> None:
        last = self._last.get(host)
        if last is not None:
            wait = delay - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last[host] = time.monotonic()

    # -- cache -----------------------------------------------------------------------------------
    def _paths(self, url: str) -> tuple[Path, Path]:
        key = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_dir / f"{key}.body", self.cache_dir / f"{key}.json"

    def cached(self, url: str, ttl_s: float | None) -> FetchResult | None:
        body, meta = self._paths(url)
        if not (body.exists() and meta.exists()):
            return None
        m = json.loads(meta.read_text())
        fetched = datetime.fromisoformat(m["fetched_at"])
        if ttl_s is not None and (datetime.now(tz=UTC) - fetched).total_seconds() > ttl_s:
            return None
        content = body.read_bytes()
        self.stats.cache_hits += 1
        return FetchResult(url=url, final_url=m.get("final_url"), status=m.get("status"),
                           state=RetrievalState(m["state"]), note=m.get("note", "") + " (cache)",
                           content=content, content_type=m.get("content_type"),
                           fetched_at=fetched, sha256=hashlib.sha256(content).hexdigest(),
                           cache_path=body, from_cache=True, seconds=0.0)

    def _write_cache(self, res: FetchResult) -> None:
        if res.content is None:
            return
        body, meta = self._paths(res.url)
        body.write_bytes(res.content)
        meta.write_text(json.dumps({
            "url": res.url, "final_url": res.final_url, "status": res.status,
            "state": res.state.value, "note": res.note, "content_type": res.content_type,
            "fetched_at": res.fetched_at.isoformat(), "sha256": res.sha256}, sort_keys=True))
        res.cache_path = body

    # -- fetch -----------------------------------------------------------------------------------
    def fetch(self, url: str, *, ttl_s: float | None = 7 * 86_400.0) -> FetchResult:
        if self.ttl_cap is not None:
            ttl_s = self.ttl_cap if ttl_s is None else min(ttl_s, self.ttl_cap)
        hit = self.cached(url, ttl_s)
        if hit is not None:
            return hit
        now = datetime.now(tz=UTC)
        ok, why = self.allowed(url)
        if not ok:
            self.stats.blocked += 1
            return FetchResult(url, None, None, RetrievalState.BLOCKED, why, None, None, now,
                               None, None, False, 0.0)
        pol = self.host_policy(url)
        host = urlparse(url).netloc
        t0 = time.monotonic()
        last_note = ""
        for attempt in range(self.max_retries + 1):
            self._space(host, pol.crawl_delay)
            try:
                r = self._client.get(url)
            except httpx.HTTPError as exc:
                last_note = f"{type(exc).__name__}: {str(exc)[:160]}"
                self.stats.requests += 1
                if attempt < self.max_retries:
                    time.sleep(min(30.0, 3.0 * (attempt + 1)))
                    continue
                break
            self.stats.requests += 1
            self.stats.by_host[host] = self.stats.by_host.get(host, 0) + 1
            if r.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                last_note = f"HTTP {r.status_code}"
                time.sleep(min(60.0, 10.0 * (attempt + 1)))
                continue
            elapsed = time.monotonic() - t0
            self.stats.seconds += elapsed
            if r.status_code != 200:
                self.stats.blocked += 1
                return FetchResult(url, str(r.url), r.status_code, RetrievalState.BLOCKED,
                                   f"HTTP {r.status_code}", None, r.headers.get("content-type"),
                                   now, None, None, False, elapsed)
            content = r.content[:MAX_BYTES]
            res = FetchResult(url, str(r.url), 200, RetrievalState.FULL,
                              "fetched" + (" (truncated at 15MB)" if len(r.content) > MAX_BYTES
                                           else ""),
                              content, r.headers.get("content-type"), now,
                              hashlib.sha256(content).hexdigest(), None, False, elapsed)
            self._write_cache(res)
            return res
        elapsed = time.monotonic() - t0
        self.stats.seconds += elapsed
        self.stats.blocked += 1
        return FetchResult(url, None, None, RetrievalState.BLOCKED,
                           f"failed after {self.max_retries + 1} attempts: {last_note}", None,
                           None, now, None, None, False, elapsed)
