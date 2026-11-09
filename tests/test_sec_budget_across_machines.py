"""SEC's fair-access ceiling is per USER across MACHINES, and a redirect hop is a request.

SEC's Internet Security Policy (sec.gov/privacy, read 2026-11-09), verbatim: "Current guidelines
limit users to a total of no more than 10 requests per second, regardless of the number of machines
used to submit requests." Its developer page (sec.gov/about/developer-resources) says the same of
"each user". Until this file, the budget was ONE machine's: 8 a second in a flock'd file in the
user's cache, so the operator's two Macs (or a Mac and a GitHub runner) sent 16 a second between
them (TeamNostra fix request 2, RE1-D1). Each `get` also took ONE slot however many redirects
`httpx` followed for it, so a 301 → 200 read sent 16 a second from one process (RE1-D2).

Nothing here reaches SEC: a mock transport, a virtual clock where a window is counted, and real
processes on a real clock where two "machines" are two processes that share no pace file.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

from vinci import netcache
from vinci.netcache import CachedHttp

_REPO = Path(__file__).resolve().parent.parent

#: SEC's published ceiling, per user, whatever the number of machines (sec.gov/privacy).
_SEC_CEILING_PER_USER = 10


class _VirtualClock:
    """Per-thread virtual time (as `test_sec_pacing.py`): only sleeping moves a thread's clock."""

    def __init__(self) -> None:
        self._local = threading.local()

    def time(self) -> float:
        return float(getattr(self._local, "now", 0.0))

    def monotonic(self) -> float:
        return self.time()

    def sleep(self, seconds: float) -> None:
        self._local.now = self.time() + max(0.0, seconds)
        time.sleep(0.001)


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
    monkeypatch.setenv("VINCI_SEC_PACE_FILE", str(tmp_path / "sec-pace"))
    monkeypatch.setattr(netcache, "_SEC_PACE", None, raising=False)
    vc = _VirtualClock()
    monkeypatch.setattr(netcache, "time", vc)
    return vc


# ─── RE1-D1: the budget is the USER's, split across the machines that may send ─────────────────

def test_every_machine_that_may_send_at_once_together_stays_under_secs_ceiling() -> None:
    """⊖ the declared share, as arithmetic SEC would count it: each machine's one-token bucket lets
    ceil(its rate) through any one-second window, and every declared machine sending flat out at
    once must still land under SEC's 10 for the one user they all are."""
    share = netcache.SEC_MAX_REQUESTS_PER_SEC
    assert share * netcache.SEC_MACHINES <= netcache.SEC_USER_MAX_REQUESTS_PER_SEC
    assert netcache.SEC_MACHINES * math.ceil(share) <= _SEC_CEILING_PER_USER


_CHILD = """
import json, sys, time
from pathlib import Path
import httpx
from vinci.netcache import CachedHttp
start, tag, cache, n = float(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
sent = []
def handler(request):
    sent.append(time.time())
    return httpx.Response(200, text="{}")
http = CachedHttp(cache_dir=Path(cache), user_agent="t t@x.org", min_interval_sec=0.0,
                  namespace=tag)
http._client = httpx.Client(transport=httpx.MockTransport(handler))
while time.time() < start:
    time.sleep(0.002)
for i in range(n):
    http.get_text(f"https://data.sec.gov/probe/{tag}/{i}.json")
print(json.dumps(sent))
"""


def _machine(start: float, tag: str, tmp_path: Path, n: int) -> subprocess.Popen[str]:
    """A process standing for a MACHINE: its own user cache, so its own pace file — two hosts, or
    two user accounts, share nothing the flock can see."""
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "VINCI_SEC_PACE_FILE": str(tmp_path / f"{tag}-cache" / "vinci" / "sec-pace")}
    return subprocess.Popen([sys.executable, "-c", _CHILD, repr(start), tag, str(tmp_path),
                             str(n)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)


def test_two_machines_sending_at_once_stay_under_secs_ceiling_per_user(tmp_path: Path) -> None:
    """⊖ the operator runs this repo on two Macs (TeamNostra's E1 probe: two separate user caches
    sent 16.47 a second, peak 16 in one second). REAL processes, REAL clock, mock transport. Each
    machine sends enough to fill a few seconds of its own budget; the two together must stay under
    SEC's per-user ceiling in every one-second window."""
    n = 3 * math.ceil(netcache.SEC_MAX_REQUESTS_PER_SEC)  # ~three seconds of each machine's share
    start = time.time() + 5.0  # past every interpreter's start-up, so the two begin together
    procs = [_machine(start, tag, tmp_path, n) for tag in ("mac-a", "mac-b")]
    sent: list[float] = []
    for p in procs:
        out, err = p.communicate(timeout=120)
        assert p.returncode == 0, err
        sent += [float(t) for t in json.loads(out)]
    assert len(sent) == 2 * n
    peak = _peak_per_second(sent)
    # SEC's ceiling, not the slot arithmetic (2 x 3 = 6): a send leaves some milliseconds after it
    # takes its slot, and on a loaded machine that delay bunches sends — the full suite measured
    # 8 in one second here on 2026-11-09, against 17 before this file
    assert peak <= _SEC_CEILING_PER_USER, f"two machines sent {peak} in one second"


# ─── RE1-D2: a redirect hop is a request, and takes its own slot ───────────────────────────────

def _redirecting(clock: _VirtualClock, sent: list[tuple[float, str]],
                 to_host: str = "data.sec.gov") -> httpx.Client:
    """The production client's redirect setting (`follow_redirects=True`) over a mock: every
    `/old/…` answers 301 to `/new/…` on ``to_host``, which answers 200."""
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append((clock.time(), str(request.url)))
        if request.url.path.startswith("/old/"):
            return httpx.Response(301, headers={
                "Location": f"https://{to_host}{request.url.path.replace('/old/', '/new/', 1)}"})
        return httpx.Response(200, text="{}")
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


def test_a_redirect_hop_to_sec_takes_its_own_slot(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ TeamNostra's probe (each request answered 301, then 200): 48 sends in 2.92 s, peak 16 in
    one second from one process — every hop `httpx` followed went unpaced. Four threads, six reads
    each, every read redirected once: twelve SEC requests a thread, and no window above the
    machine's share."""
    sent: list[tuple[float, str]] = []
    http = CachedHttp(cache_dir=tmp_path, user_agent="t t@x.org", min_interval_sec=0.0,
                      namespace="sec")
    http._client = _redirecting(clock, sent)  # noqa: SLF001
    threads = [threading.Thread(target=lambda j=j: [  # type: ignore[misc]
        http.get_text(f"https://www.sec.gov/old/t{j}/{i}.json") for i in range(6)])
        for j in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(sent) == 4 * 6 * 2
    assert sum("/new/" in u for _, u in sent) == 24  # every hop was sent, and only once
    peak = _peak_per_second([at for at, _ in sent])
    assert peak <= math.ceil(netcache.SEC_MAX_REQUESTS_PER_SEC), f"peak {peak} with redirects"


def test_a_redirect_answers_with_the_page_it_lands_on(tmp_path: Path,
                                                      clock: _VirtualClock) -> None:
    """⊕ following by hand changes what is PACED, never what is read: the body is the final
    page's, cached under the URL asked for, and a second read is served from the cache."""
    sent: list[tuple[float, str]] = []
    http = CachedHttp(cache_dir=tmp_path, user_agent="t t@x.org", min_interval_sec=0.0,
                      namespace="sec")
    http._client = _redirecting(clock, sent)  # noqa: SLF001
    assert http.get_json("https://www.sec.gov/old/x.json") == {}
    assert http.get_json("https://www.sec.gov/old/x.json") == {}
    assert [u for _, u in sent] == ["https://www.sec.gov/old/x.json",
                                    "https://data.sec.gov/new/x.json"]


def test_a_hop_off_sec_takes_no_sec_slot(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ the budget binds SEC hosts only, hop by hop: a redirect from SEC to another host spends
    one SEC slot for the first request and none for the hop."""
    sent: list[tuple[float, str]] = []
    http = CachedHttp(cache_dir=tmp_path, user_agent="t t@x.org", min_interval_sec=0.0,
                      namespace="sec")
    http._client = _redirecting(clock, sent, to_host="mirror.example.test")  # noqa: SLF001
    for i in range(8):
        http.get_text(f"https://www.sec.gov/old/{i}.json")
    sec_sends = [at for at, u in sent if "sec.gov" in u]
    off_sec = [at for at, u in sent if "example.test" in u]
    assert len(sec_sends) == len(off_sec) == 8
    # each hop leaves at once, on the heels of the SEC request it follows
    assert [round(b - a, 6) for a, b in zip(sec_sends, off_sec, strict=True)] == [0.0] * 8


def test_a_redirect_loop_fails_loud_rather_than_reading_on(tmp_path: Path,
                                                          clock: _VirtualClock) -> None:
    """⊖ a page that redirects for ever is an error, never a read: the hops are bounded, and once
    the retries are spent the failure names the URL."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": str(request.url)})
    http = CachedHttp(cache_dir=tmp_path, user_agent="t t@x.org", min_interval_sec=0.0,
                      namespace="sec", max_retries=0)
    http._client = httpx.Client(transport=httpx.MockTransport(handler),  # noqa: SLF001
                                follow_redirects=True)
    with pytest.raises(netcache.HttpError, match="loop.json"):
        http.get_text("https://www.sec.gov/loop.json")
