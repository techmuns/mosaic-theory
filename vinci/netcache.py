"""A small cached, throttled, retrying HTTP GET client — shared by the resolver and the EDGAR
and EOD clients so politeness/caching logic lives in exactly one place.

Why this exists
---------------
- **Pacing.** SEC fair-access is 10 req/s IN TOTAL per user, however many clients, threads or
  machines send them; Polygon's plan ~5 req/min. Each client keeps its own minimum interval
  (thread-safe), and every request to an SEC host ALSO takes a slot from ONE budget shared by
  every client, thread and process on the machine (:class:`SharedPace`).
- **Caching.** SEC reference files and immutable filings should not be refetched every run; an
  on-disk cache (with optional TTL) keeps reruns fast and idempotent.
- **Fail-loud.** Auth/permanent errors raise immediately; only transient errors (429/5xx) retry
  with backoff. Nothing degrades silently.
"""

from __future__ import annotations

import email.utils
import fcntl
import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import Any

import httpx

#: How long to wait after a 429 before retrying. Rate limits are enforced over a ROLLING
#: WINDOW — Polygon's is per minute — so a sub-window retry is refused by the same window
#: that refused the first call. 61s clears a 60s window with a second to spare. Only the
#: 429 path uses it; a 5xx keeps the fast exponential, since a server error is not a clock.
_RATE_LIMIT_WAIT_SEC = 61.0


#: The hosts behind SEC's ONE fair-access budget. SEC states the ceiling per USER across all
#: machines, so the three share it: a full-text search spends what a companyfacts read can't.
SEC_HOSTS = frozenset({"www.sec.gov", "data.sec.gov", "efts.sec.gov"})

#: The TOTAL every client, thread and `vinci` process on this machine may send to SEC_HOSTS.
#: SEC's published ceiling is 10 a second per user; 8 keeps two in hand for jitter and for
#: anything else on the machine that reads SEC (a browser, a notebook).
SEC_MAX_REQUESTS_PER_SEC = 8.0

#: How long EVERY SEC request is held off after SEC refuses one, when SEC sends no `Retry-After`.
#: SEC's policy: access resumes once the rate has stayed below the threshold for TEN MINUTES — so
#: anything shorter is spent inside the block, and every request sent then restarts its clock.
#: Eleven minutes: the ten SEC names plus one, the same one-unit margin as the 61 s above.
_SEC_REFUSAL_HOLD_SEC = 660.0

#: The longest hold an unattended run sits through. A `Retry-After` beyond it fails loud AT ONCE
#: (still silencing everyone for this long) — and anything further ahead than this in the shared
#: pace file can only be a wall clock that stepped back, so it is discarded.
_SEC_MAX_HOLD_SEC = 900.0


class HttpError(RuntimeError):
    """A non-retryable HTTP failure (auth, 4xx other than 429, or retries exhausted)."""


class HttpNotFoundError(HttpError):
    """A 404: the resource does not exist. The ONE failure a caller may read as absence ("no
    XBRL", "no frame for that period") — a throttle, a 5xx or a timeout is never that."""


class SecRateLimitedError(RuntimeError):
    """SEC refused us, and was still refusing after every SEC request on the machine had been held
    off for its whole window. NOT an :class:`HttpError`, on purpose: callers degrade an
    ``HttpError`` to UNKNOWN and move to the next name, which during a block means sending again
    into it and recording a refusal as missing data. This one stops the run — and once raised, no
    further SEC request leaves this process (:data:`_SEC_STOPPED`), so a broad ``except Exception``
    that swallows it cannot send into the block either."""


#: The refusal that stopped SEC traffic in this process, once one has. Every later request to an
#: SEC host raises at once without sending (a cached copy is still served). Process-wide and never
#: cleared: a block outlasting SEC's window is an operator's call, and the run is re-made later.
_SEC_STOPPED: SecRateLimitedError | None = None


def sec_refusal() -> SecRateLimitedError | None:
    """The refusal that stopped SEC traffic in this process, or None while SEC has not."""
    return _SEC_STOPPED


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else default


def _sec_pace_path() -> Path:
    """Where the machine-wide SEC budget lives: per USER, not per checkout — sessions run from
    separate worktrees, each with its own ``data/cache``, and they all share one IP."""
    cache_home = _env_path("XDG_CACHE_HOME", Path.home() / ".cache")
    return _env_path("VINCI_SEC_PACE_FILE", cache_home / "vinci" / "sec-pace")


class SharedPace:
    """One request per ``interval`` across every thread of this process AND every process that
    opens the same ``path`` — a token bucket ONE token deep, which is the only depth that holds the
    cap in EVERY one-second window (a bucket of depth b lets b + rate through one window).

    THE STATE IS TWO NUMBERS in a small file — when the next request may go, and until when every
    request is held off after a refusal — read and written under an exclusive ``flock``. The file
    lock orders processes; the thread lock orders threads, because ``flock`` excludes open files,
    not threads sharing one. Wall-clock seconds, because they are the one clock two processes
    agree on.

    TAKE-AT-WAKE, not reserve-ahead. A caller sleeps until the slot looks free, then takes it under
    the locks — or sleeps again if another got there first. So a hold-off binds at once: nothing
    sleeps through it on a slot reserved before the refusal arrived.
    """

    def __init__(self, interval: float, path: Path) -> None:
        self._interval = interval
        self._path = path
        self._lock = threading.Lock()
        self._fd: int | None = None
        self._pid = 0

    def acquire(self) -> None:
        """Block until this caller may send one request, and count it."""
        while (wait := self._update(take=True)) > 0:
            time.sleep(wait)

    def hold_off(self, seconds: float) -> None:
        """Nobody sends before ``seconds`` from now."""
        self._update(hold=seconds)

    def _open(self) -> int:
        # a forked child must not share the parent's open file: flock would not exclude the two
        if self._fd is None or self._pid != os.getpid():
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._fd = os.open(self._path, os.O_RDWR | os.O_CREAT, 0o600)
            except OSError as exc:
                raise RuntimeError(
                    f"cannot open the shared SEC pace file {self._path} ({exc.strerror}) — every "
                    "SEC request takes its turn from it. Set VINCI_SEC_PACE_FILE to a writable "
                    "path.") from exc
            self._pid = os.getpid()
        return self._fd

    def _update(self, *, take: bool = False, hold: float = 0.0) -> float:
        """Under both locks: record a hold-off, or take the slot if it is free. Returns how long
        until the slot may be free (0.0 once taken)."""
        with self._lock:
            fd = self._open()
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                now = time.time()
                try:
                    next_at, held_until = (float(x) for x in os.pread(fd, 64, 0).split())
                except ValueError:  # a new file, or a write cut short by a crash
                    next_at = held_until = 0.0
                stepped_back = max(next_at, held_until) > now + _SEC_MAX_HOLD_SEC + self._interval
                if stepped_back:
                    next_at = held_until = now  # nothing legitimate is that far ahead
                held_until = max(held_until, now + hold)
                wait = max(next_at, held_until) - now
                taken = take and wait <= 0
                if taken:
                    next_at, wait = now + self._interval, 0.0
                if taken or hold > 0 or stepped_back:  # a waiter's check changes nothing
                    os.ftruncate(fd, 0)
                    os.pwrite(fd, f"{next_at!r} {held_until!r}".encode(), 0)
                return wait
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)


_SEC_PACE: SharedPace | None = None
_SEC_PACE_LOCK = threading.Lock()


def sec_pace() -> SharedPace:
    """THE budget every request to an SEC host takes its turn from (built on first use)."""
    global _SEC_PACE
    with _SEC_PACE_LOCK:
        if _SEC_PACE is None:
            _SEC_PACE = SharedPace(1.0 / SEC_MAX_REQUESTS_PER_SEC, _sec_pace_path())
        return _SEC_PACE


def _retry_after_sec(resp: httpx.Response) -> float | None:
    """A `Retry-After` header in seconds (it may be a number or an HTTP date), or None."""
    raw = resp.headers.get("Retry-After", "").strip()
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, when.timestamp() - time.time())


@dataclass(frozen=True)
class _CacheEntry:
    url: str
    fetched_at: float
    text: str


class CachedHttp:
    """Synchronous cached GET with a per-instance throttle and bounded retries.

    One instance per upstream (SEC, Polygon), each with its own ``min_interval_sec`` and default
    headers. THREAD-SAFE PACING: the dossier assembly and the theme scans drive clients from
    thread pools, so the per-instance interval is taken under a lock — and a request to an SEC
    host also takes its turn from :func:`sec_pace`, whatever this instance's own interval is.
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
        self._next_at = 0.0
        self._pace_lock = threading.Lock()
        # extra_headers carries secrets like ``Authorization: Bearer <key>`` so the key travels in a
        # header, never in the request URL — keeping it out of the on-disk cache, logs, and errors.
        headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}
        if extra_headers:
            headers.update(extra_headers)
        self._client = httpx.Client(headers=headers, timeout=timeout_sec, follow_redirects=True)
        #: url -> when the copy this instance last read or wrote was fetched (`fetched_at`)
        self._fetched: dict[str, float] = {}

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

    def fetched_at(self, url: str, *, params: dict[str, Any] | None = None) -> float | None:
        """When the cached copy of ``url`` was fetched (epoch seconds), or None when no readable
        copy is held — so data read from the cache carries its RETRIEVAL time, never the time it
        was read back. A copy this instance just read or wrote answers from memory (the entry can
        be megabytes; it is not parsed twice)."""
        full = self._with_params(url, params)
        if full in self._fetched:
            return self._fetched[full]
        path = self._cache_path(full)
        if not path.exists():
            return None
        try:
            return float(json.loads(path.read_text())["fetched_at"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

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
        self._fetched[url] = entry.fetched_at
        return entry.text

    def _write_cache(self, url: str, text: str) -> None:
        entry = _CacheEntry(url=url, fetched_at=time.time(), text=text)
        self._cache_path(url).write_text(json.dumps(entry.__dict__))
        self._fetched[url] = entry.fetched_at

    def _throttle(self) -> None:
        """This instance's own interval, reserved under a lock so threads sharing the instance
        queue behind each other rather than all reading one "last request" and sending together."""
        if self._min_interval <= 0:
            return
        with self._pace_lock:
            now = time.monotonic()
            at = max(self._next_at, now)
            self._next_at = at + self._min_interval
        if at > now:
            time.sleep(at - now)

    def _fetch_with_retries(
        self, url: str, *, json_body: dict[str, Any] | None = None
    ) -> str:
        global _SEC_STOPPED
        sec = httpx.URL(url).host in SEC_HOSTS
        backoff = 1.0
        last_exc: Exception | None = None
        attempt = 0
        refused = False
        while True:
            if sec and _SEC_STOPPED is not None:
                raise SecRateLimitedError(
                    f"not sent: {url} — SEC refused this process earlier ({_SEC_STOPPED})")
            self._throttle()
            if sec:
                sec_pace().acquire()
            wait = backoff
            try:
                resp = (
                    self._client.post(url, json=json_body)
                    if json_body is not None
                    else self._client.get(url)
                )
            except httpx.HTTPError as exc:  # transport-level (timeout, connection)
                last_exc = exc
                backoff = min(backoff * 2, 30.0)
            else:
                if resp.status_code == 200:
                    return resp.text
                if sec and resp.status_code in (403, 429):
                    # SEC REFUSED THE IP, NOT THIS REQUEST (2026-10-29). SEC documents no status
                    # for excess traffic; it answers with a 403 page, and a 429 means the same
                    # thing. Hold off EVERY SEC request on the machine for the whole window (the
                    # retry waits it out in `acquire` above), try once more, then stop: a request
                    # sent inside the block restarts SEC's ten-minute clock.
                    hold = _retry_after_sec(resp)
                    hold = _SEC_REFUSAL_HOLD_SEC if hold is None else hold
                    sec_pace().hold_off(min(hold, _SEC_MAX_HOLD_SEC))
                    if refused or hold > _SEC_MAX_HOLD_SEC:
                        _SEC_STOPPED = SecRateLimitedError(
                            f"SEC refused {url} with {resp.status_code}"
                            + (f" after every SEC request was held off {hold:.0f}s"
                               if refused else f" and asked for {hold:.0f}s")
                            + " — stopping rather than sending into a fair-access block "
                            f"(SEC_MAX_REQUESTS_PER_SEC={SEC_MAX_REQUESTS_PER_SEC:g})"
                            # SEC answers both with a 403 page, and its status cannot tell them
                            # apart: name both, so the operator is not sent only to the pacing
                            + ("; a 403 is also how SEC answers a User-Agent it does not accept as "
                               "a declared contact — check SEC_USER_AGENT"
                               if resp.status_code == 403 else "")
                            + f": {resp.text[:200]}")
                        raise _SEC_STOPPED
                    refused = True
                    continue
                if resp.status_code == 429:
                    # A RATE LIMIT IS A CLOCK, NOT A QUEUE — WAIT THE WINDOW OUT (2026-09-23).
                    # 429 shared the exponential path, whose whole ladder (1+2+4+8+16) is ~31s
                    # against a limit measured PER MINUTE, so every retry landed inside the same
                    # window that refused the first call and the run died with "Exhausted
                    # retries". Polygon sends NO `Retry-After` and no rate-limit headers (checked
                    # 2026-09-23; the body just says "wait or upgrade"), so the window is the
                    # honest wait — and a host that does say how long is taken at its word.
                    last_exc = HttpError(f"429 from {url}")
                    after = _retry_after_sec(resp)
                    wait = _RATE_LIMIT_WAIT_SEC if after is None else after
                elif resp.status_code in (500, 502, 503, 504):
                    # A server error is not a clock: retry FAST, the way this always has.
                    last_exc = HttpError(f"{resp.status_code} from {url}")
                    backoff = min(backoff * 2, 30.0)
                elif resp.status_code == 404:
                    raise HttpNotFoundError(f"Non-retryable 404 from {url}: {resp.text[:200]}")
                else:
                    # 401/403 etc. — permanent; fail loud immediately.
                    raise HttpError(
                        f"Non-retryable {resp.status_code} from {url}: {resp.text[:200]}"
                    )
            if attempt >= self._max_retries:
                raise HttpError(f"Exhausted retries for {url}") from last_exc
            attempt += 1
            time.sleep(wait)
