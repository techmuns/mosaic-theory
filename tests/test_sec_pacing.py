"""SEC's fair-access ceiling is a TOTAL — 10 requests a second per user, however many clients,
threads or machines send them — so the pace that keeps us under it must be a total too.

Until 2026-10-29 every `CachedHttp` paced ITSELF (an unlocked "last request at" per instance), so
eight clients in eight threads sent 64 a second, and one client shared by eight threads did the
same. No test exercised the throttle at all: every test client is built with
`min_interval_sec=0`. These pins run the throttle, on a VIRTUAL clock (each thread keeps its own
time, and only sleeping moves it) over a mock transport — nothing here reaches SEC.

This file deliberately imports nothing new from `vinci.netcache`, so it runs against the old
per-instance pacer and shows the 64 it allowed (audit item E1-D1).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from vinci import netcache
from vinci.config import Config
from vinci.netcache import CachedHttp
from vinci.sec import build_sec_http

_REPO = Path(__file__).resolve().parent.parent
_SEC_HOSTS = ("data.sec.gov", "www.sec.gov", "efts.sec.gov")


class _VirtualClock:
    """Per-thread virtual time: ``sleep`` advances only the sleeper's clock, then yields the GIL
    for real so other threads interleave exactly where a real sleep would let them."""

    def __init__(self) -> None:
        self._local = threading.local()

    def time(self) -> float:
        return float(getattr(self._local, "now", 0.0))

    def monotonic(self) -> float:
        return self.time()

    def sleep(self, seconds: float) -> None:
        self._local.now = self.time() + max(0.0, seconds)
        time.sleep(0.001)  # a real yield, long enough for every other thread to run


def _peak_per_second(times: list[float]) -> int:
    """The most sends in any half-open one-second window (t - 1, t]."""
    ts, best, lo = sorted(times), 0, 0
    for hi, t in enumerate(ts):
        while ts[lo] <= t - 1.0:
            lo += 1
        best = max(best, hi - lo + 1)
    return best


@pytest.fixture
def clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _VirtualClock:
    """A virtual clock for `vinci.netcache`, and a pace file of this test's own."""
    monkeypatch.setenv("VINCI_SEC_PACE_FILE", str(tmp_path / "sec-pace"))
    monkeypatch.setattr(netcache, "_SEC_PACE", None, raising=False)  # rebuilt from the env above
    vc = _VirtualClock()
    monkeypatch.setattr(netcache, "time", vc)
    return vc


def _recording(http: CachedHttp, clock: _VirtualClock, sent: list[float]) -> CachedHttp:
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(clock.time())
        return httpx.Response(200, text="{}")

    http._client = httpx.Client(transport=httpx.MockTransport(handler))  # noqa: SLF001
    return http


def _run_threads(work: list[Callable[[], None]]) -> None:
    errors: list[BaseException] = []

    def wrap(fn: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            try:
                fn()
            except BaseException as exc:  # noqa: BLE001 — re-raised on the main thread below
                errors.append(exc)
        return run

    gate = threading.Barrier(len(work))

    def gated(fn: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            gate.wait()  # every thread starts together, as a pool's workers do
            fn()
        return run

    threads = [threading.Thread(target=wrap(gated(fn))) for fn in work]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errors:
        raise errors[0]


def _fetches(http: CachedHttp, host: str, tag: str, n: int) -> Callable[[], None]:
    def fn() -> None:
        for i in range(n):
            http.get_text(f"https://{host}/probe/{tag}/{i}.json")
    return fn


def test_eight_clients_on_eight_threads_send_at_most_eight_a_second(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ the shape the dossier assembly runs (8 workers, each building its own clients) and the
    theme scans run: eight clients from the REAL factory, eight threads each, across all three SEC
    hosts. The per-instance pacer let this reach 64 a second."""
    sent: list[float] = []
    clients = [_recording(build_sec_http(Config(data_dir=tmp_path / f"c{i}")), clock, sent)
               for i in range(8)]
    _run_threads([_fetches(c, _SEC_HOSTS[i % 3], f"c{i}t{j}", 3)
                  for i, c in enumerate(clients) for j in range(8)])
    assert len(sent) == 8 * 8 * 3
    peak = _peak_per_second(sent)
    assert peak <= 8, f"peak {peak} SEC requests in one second across 8 clients x 8 threads"


def test_one_client_shared_by_eight_threads_sends_at_most_eight_a_second(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ the shape `themes/exposure.py` runs: ONE client driven from a thread pool. An unlocked
    "last request at" let every thread read the same value and send together."""
    sent: list[float] = []
    http = _recording(build_sec_http(Config(data_dir=tmp_path)), clock, sent)
    _run_threads([_fetches(http, "data.sec.gov", f"t{j}", 6) for j in range(8)])
    assert len(sent) == 8 * 6
    peak = _peak_per_second(sent)
    assert peak <= 8, f"peak {peak} SEC requests in one second from 1 client x 8 threads"


def test_a_client_built_without_any_pace_still_shares_the_sec_budget(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ the budget belongs to the HOST, not to whoever built the client: theme intelligence
    builds its own SEC client at 0.15 s, the quality pass its own at 0, and a test or a script can
    pass `min_interval_sec=0`. None of them may step outside the total."""
    sent: list[float] = []
    clients = [_recording(CachedHttp(cache_dir=tmp_path / f"z{i}", user_agent="t t@x.org",
                                     min_interval_sec=0.0, namespace="sec"), clock, sent)
               for i in range(4)]
    _run_threads([_fetches(c, "www.sec.gov", f"z{i}", 8) for i, c in enumerate(clients)])
    peak = _peak_per_second(sent)
    assert peak <= 8, f"peak {peak} from four unpaced clients"


def test_a_host_outside_sec_is_not_held_to_the_sec_budget(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ the SEC budget binds SEC hosts ONLY: an unpaced client to any other host is not slowed by
    it (each upstream keeps the pace its own client was built with)."""
    sent: list[float] = []
    http = _recording(CachedHttp(cache_dir=tmp_path, user_agent="t", min_interval_sec=0.0,
                                 namespace="other"), clock, sent)
    _run_threads([_fetches(http, "api.example.test", f"o{j}", 4) for j in range(4)])
    assert sent == [0.0] * 16  # nobody waited


def test_a_client_shared_by_threads_keeps_its_own_interval_off_sec_too(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ the per-instance interval is LOCKED, which matters where no shared budget stands behind
    it (Polygon's plan allows ~5 a minute): eight threads on one client paced at 0.25 s must still
    send one at a time, never two inside the interval."""
    sent: list[float] = []
    http = _recording(CachedHttp(cache_dir=tmp_path, user_agent="t", min_interval_sec=0.25,
                                 namespace="other"), clock, sent)
    _run_threads([_fetches(http, "api.example.test", f"o{j}", 4) for j in range(8)])
    ts = sorted(sent)
    assert len(ts) == 32 and min(b - a for a, b in zip(ts, ts[1:], strict=False)) >= 0.25


_CHILD = """
import json, sys, time
from pathlib import Path
import httpx
from vinci.netcache import CachedHttp
start, tag, cache = float(sys.argv[1]), sys.argv[2], sys.argv[3]
sent = []
def handler(request):
    sent.append(time.time())
    return httpx.Response(200, text="{}")
http = CachedHttp(cache_dir=Path(cache), user_agent="t t@x.org", min_interval_sec=0.0,
                  namespace=tag)
http._client = httpx.Client(transport=httpx.MockTransport(handler))
while time.time() < start:
    time.sleep(0.002)
for i in range(8):
    http.get_text(f"https://data.sec.gov/probe/{tag}/{i}.json")
print(json.dumps(sent))
"""


def _spawn(start: float, tag: str, tmp_path: Path, pace_file: Path) -> subprocess.Popen[str]:
    env = {**os.environ, "PYTHONPATH": str(_REPO), "VINCI_SEC_PACE_FILE": str(pace_file)}
    return subprocess.Popen([sys.executable, "-c", _CHILD, repr(start), tag, str(tmp_path)],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _times(proc: subprocess.Popen[str]) -> list[float]:
    out, err = proc.communicate(timeout=60)
    assert proc.returncode == 0, err
    return [float(t) for t in json.loads(out)]


def _min_gap(times: list[float]) -> float:
    ts = sorted(times)
    return min(b - a for a, b in zip(ts, ts[1:], strict=False))


def test_two_processes_on_one_machine_share_one_budget(tmp_path: Path) -> None:
    """⊖ two `vinci` processes on one machine share one IP, so they share SEC's ceiling. REAL
    clock, REAL processes, mock transport. A PAIR sharing a pace file must interleave at the shared
    pace; a CONTROL pair with a file each must not — which is what shows this check can see the
    failure at all (each control process alone paces at 8 a second, so together they overlap)."""
    start = time.time() + 3.0  # past both interpreters' start-up, so they begin together
    shared = tmp_path / "shared-pace"
    procs = {tag: _spawn(start, tag, tmp_path, shared if tag in ("a", "b") else
                         tmp_path / f"own-{tag}")
             for tag in ("a", "b", "c", "d")}
    got: dict[str, list[float]] = {tag: _times(p) for tag, p in procs.items()}
    pair, control = got["a"] + got["b"], got["c"] + got["d"]
    assert len(pair) == len(control) == 16
    # sharing: no two sends from either process closer than the pace (8 a second), less jitter
    assert _min_gap(pair) >= 0.1, f"min gap {_min_gap(pair):.3f}s across two processes"
    assert max(pair) - min(pair) >= 15 * 0.125 - 0.05
    assert _peak_per_second(pair) <= 8
    # the control proves the check can fail: two independent 8-a-second trains overlap
    assert _min_gap(control) < 0.1 and _peak_per_second(control) > 8
