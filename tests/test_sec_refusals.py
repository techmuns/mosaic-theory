"""What an SEC refusal, a server error and a true absence each become — three different things.

- A REFUSAL (429, or SEC's fair-access 403; SEC documents no status) silences EVERY SEC request
  on the machine for SEC's whole window — `Retry-After` when SEC sends one, else ten minutes plus
  a margin — retries ONCE, and then fails loud. It is never retried fast, and it is never "no
  data". Until 2026-10-29 a 403 raised on the first attempt while every other thread kept sending,
  and a 429 waited 61 s four times — about four minutes, inside a ten-minute block.
- A SERVER ERROR (5xx) retries on the fast ladder, then raises with its status.
- Only a 404 means the thing does not exist: companyfacts → "no XBRL" (audit item E1-D8), a frame
  → skipped (E1-D9).

And the User-Agent SEC requires is checked before it is sent (E1-D15).

Every test runs on a VIRTUAL clock over a mock transport — nothing here reaches SEC.
"""

from __future__ import annotations

import email.utils
import json
import threading
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any, cast

import httpx
import pytest

from tests.test_screen2 import REF, _rec
from vinci import netcache
from vinci.config import Config, sec_user_agent
from vinci.edgar.client import EdgarClient, compute_fundamental_snapshot
from vinci.netcache import CachedHttp, HttpError, HttpNotFoundError, SecRateLimitedError
from vinci.screens.assemble import enrich_with_fundamentals
from vinci.sec import build_sec_http

_REPO = Path(__file__).resolve().parent.parent
_FACTS = json.loads((_REPO / "tests/fixtures/companyfacts/AMZN.json").read_text())
_CF_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"
_WINDOW = 600.0  # SEC: access resumes after ten minutes below the threshold


class _VirtualClock:
    """Per-thread virtual time; ``sleep`` moves only the sleeper's clock."""

    def __init__(self) -> None:
        self._local = threading.local()

    def time(self) -> float:
        return float(getattr(self._local, "now", 0.0))

    def monotonic(self) -> float:
        return self.time()

    def sleep(self, seconds: float) -> None:
        self._local.now = self.time() + max(0.0, seconds)
        time.sleep(0)

    def set(self, now: float) -> None:
        self._local.now = now


@pytest.fixture
def clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _VirtualClock:
    monkeypatch.setenv("VINCI_SEC_PACE_FILE", str(tmp_path / "sec-pace"))
    monkeypatch.setattr(netcache, "_SEC_PACE", None)
    vc = _VirtualClock()
    monkeypatch.setattr(netcache, "time", vc)
    return vc


Script = Callable[[httpx.Request], httpx.Response]


def _client(tmp_path: Path, clock: _VirtualClock, script: Script,
            sent: list[tuple[float, str]], *, name: str = "c") -> CachedHttp:
    http = build_sec_http(Config(data_dir=tmp_path / name))

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append((clock.time(), str(request.url)))
        return script(request)

    http._client = httpx.Client(transport=httpx.MockTransport(handler))  # noqa: SLF001
    return http


def _sequence(*responses: httpx.Response) -> Script:
    it = iter(responses)
    return lambda request: next(it)


_REFUSAL_PAGE = ("<title>SEC.gov | Request Rate Threshold Exceeded</title> Your request rate has "
                 "exceeded the threshold.")


# --- a refusal: one shared hold-off for SEC's whole window, one retry, then loud ----------------

def test_a_429_without_retry_after_holds_off_sec_whole_window(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ 429 then 200: the retry waits SEC's ten-minute window, not 61 s and not 1 s."""
    sent: list[tuple[float, str]] = []
    http = _client(tmp_path, clock, _sequence(httpx.Response(429), httpx.Response(200, text="ok")),
                   sent)
    assert http.get_text(_CF_URL) == "ok"
    assert len(sent) == 2 and sent[1][0] - sent[0][0] >= _WINDOW


def test_a_retry_after_is_honoured(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ when SEC says how long, that is the wait — no longer, no shorter."""
    sent: list[tuple[float, str]] = []
    http = _client(tmp_path, clock, _sequence(
        httpx.Response(429, headers={"Retry-After": "30"}), httpx.Response(200, text="ok")), sent)
    assert http.get_text(_CF_URL) == "ok"
    assert 30.0 <= sent[1][0] - sent[0][0] < 31.0


def test_a_retry_after_given_as_a_date_is_honoured(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ `Retry-After` may be an HTTP date; it is read as the seconds until then."""
    sent: list[tuple[float, str]] = []
    when = email.utils.formatdate(45.0, usegmt=True)  # 45 s after the virtual clock's 0
    http = _client(tmp_path, clock, _sequence(
        httpx.Response(429, headers={"Retry-After": when}), httpx.Response(200, text="ok")), sent)
    assert http.get_text(_CF_URL) == "ok"
    assert 45.0 <= sent[1][0] - sent[0][0] < 46.0


def test_sec_fair_access_403_is_a_refusal_not_a_permanent_error(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ SEC answers excess traffic with a 403 page. It raised on the FIRST attempt while every
    other thread kept sending into the block; it now holds off the window like a 429."""
    sent: list[tuple[float, str]] = []
    http = _client(tmp_path, clock, _sequence(httpx.Response(403, text=_REFUSAL_PAGE),
                                              httpx.Response(200, text="ok")), sent)
    assert http.get_text(_CF_URL) == "ok"
    assert sent[1][0] - sent[0][0] >= _WINDOW


def test_a_refusal_that_outlasts_the_window_fails_loud_after_two_requests(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ never hammer: one request, the whole window, one more — then a loud, distinct error that
    no `except HttpError` degrade path can swallow into "no data"."""
    sent: list[tuple[float, str]] = []
    http = _client(tmp_path, clock, lambda r: httpx.Response(403, text=_REFUSAL_PAGE), sent)
    with pytest.raises(SecRateLimitedError, match="403"):
        http.get_text(_CF_URL)
    assert len(sent) == 2 and sent[1][0] - sent[0][0] >= _WINDOW
    assert not issubclass(SecRateLimitedError, HttpError)


def test_a_refusal_holds_off_every_other_sec_client(
        tmp_path: Path, clock: _VirtualClock, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ SEC limits the IP, not the client: when one client is refused, a DIFFERENT client on
    another thread must not send until the window is over — or it extends the block."""
    sent: list[tuple[float, str]] = []
    refused = _client(tmp_path, clock, _sequence(httpx.Response(429),
                                                 httpx.Response(200, text="ok")), sent, name="a")
    other = _client(tmp_path, clock, lambda r: httpx.Response(200, text="fine"), sent, name="b")
    pace = netcache.sec_pace()
    held = threading.Event()
    real_hold_off = pace.hold_off

    def hold_off(seconds: float) -> None:
        real_hold_off(seconds)
        held.set()

    monkeypatch.setattr(pace, "hold_off", hold_off)
    t = threading.Thread(target=lambda: refused.get_text(_CF_URL))
    t.start()
    assert held.wait(10)
    clock.set(1.0)  # this thread asks one virtual second after the refusal
    assert other.get_text("https://www.sec.gov/other.json") == "fine"
    t.join(10)
    when = {u: at for at, u in sent}["https://www.sec.gov/other.json"]
    assert when >= _WINDOW


def test_an_absurd_retry_after_fails_loud_at_once(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ a wait longer than any unattended run should sit through is refused NOW (and still
    silences everyone for the cap), rather than sleeping a day."""
    sent: list[tuple[float, str]] = []
    http = _client(tmp_path, clock, lambda r: httpx.Response(429, headers={"Retry-After": "86400"}),
                   sent)
    with pytest.raises(SecRateLimitedError, match="86400"):
        http.get_text(_CF_URL)
    assert len(sent) == 1


def test_a_polygon_429_keeps_its_own_path_and_reads_retry_after(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊕ outside SEC nothing about the 429 path changes except that a `Retry-After` is read when
    one is sent (Polygon sends none — `test_netcache_rate_limit.py` pins its 61 s)."""
    waits: list[float] = []
    monkeypatch.setattr("vinci.netcache.time.sleep", waits.append)
    http = CachedHttp(cache_dir=tmp_path, user_agent="t", min_interval_sec=0.0, namespace="p")
    codes = iter([httpx.Response(429, headers={"Retry-After": "7"}),
                  httpx.Response(200, text="ok")])
    http._client = httpx.Client(transport=httpx.MockTransport(lambda r: next(codes)))  # noqa: SLF001
    assert http.get_text("https://api.polygon.test/x") == "ok"
    assert waits == [7.0]


# --- E1-D8: only a 404 is "no XBRL" -------------------------------------------------------------

def _edgar(tmp_path: Path, clock: _VirtualClock, script: Script,
           sent: list[tuple[float, str]]) -> EdgarClient:
    return EdgarClient(_client(tmp_path, clock, script, sent))


def _ok() -> httpx.Response:
    return httpx.Response(200, text=json.dumps(_FACTS))


def test_a_transient_503_is_never_no_xbrl(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ 503 five times then 200: the snapshot read "no XBRL" for a filer whose data the very next
    request returned. It now raises, with the status."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, _sequence(*[httpx.Response(503)] * 5, _ok()), sent)
    with pytest.raises(HttpError, match="Exhausted retries"):
        edgar.fundamental_snapshot(1)


def test_the_screen_reads_companyfacts_once_and_never_records_a_503_as_no_xbrl(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ the screen read companyfacts TWICE — the snapshot's read, then its own. A transient
    failure on the first became "no XBRL" while the second succeeded; now ONE read, which raises."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, _sequence(*[httpx.Response(503)] * 5, _ok()), sent)
    with pytest.raises(HttpError):
        enrich_with_fundamentals(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1), edgar=edgar,
                                 price_bars=[], reference_date=REF)
    assert len(sent) == 5


def test_the_screen_reads_a_filers_companyfacts_once(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ the success path: the snapshot and the screen's own reads come from ONE document."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, lambda r: _ok(), sent)
    out = enrich_with_fundamentals(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1), edgar=edgar,
                                   price_bars=[], reference_date=REF)
    want = compute_fundamental_snapshot("0000000001", _FACTS)
    assert len(sent) == 1
    assert out.fundamentals.fcf_sign == want.fcf_sign


def test_a_404_is_no_xbrl_in_the_snapshot_and_in_the_screen(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ a filer SEC holds no companyfacts for IS "no XBRL" — and the screen's second read used to
    raise on exactly that 404, so a no-XBRL name stopped the screen instead of reading UNKNOWN."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, lambda r: httpx.Response(404), sent)
    snap = edgar.fundamental_snapshot(1)
    assert not snap.fcf_sign.is_known and snap.fcf_sign.note == "no XBRL"
    out = enrich_with_fundamentals(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1), edgar=edgar,
                                   price_bars=[], reference_date=REF)
    assert out.fundamentals.fcf_sign.note == "no XBRL"


def test_a_throttle_is_never_no_xbrl(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ a refused companyfacts read is loud — never an issuer "without XBRL"."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, lambda r: httpx.Response(429), sent)
    with pytest.raises(SecRateLimitedError):
        edgar.fundamental_snapshot(1)


# --- E1-D9: a frame is skipped on a 404 only ----------------------------------------------------

def _frames(older: Any, newest: Callable[[], httpx.Response]) -> Script:
    def script(request: httpx.Request) -> httpx.Response:
        if "CY2026Q1I" in str(request.url):
            return newest()
        if "CY2025Q4I" in str(request.url) and "dei" in str(request.url):
            return httpx.Response(200, text=json.dumps(older))
        return httpx.Response(404)
    return script


_OLDER = {"data": [{"cik": 1, "val": 111.0}]}


def test_a_refused_newest_frame_never_serves_the_older_one(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ the newest frame answered 403 and the broad `except` quietly served last quarter's count
    (111 for 222), stamped with the same tag and no flag. It now raises."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, _frames(_OLDER, lambda: httpx.Response(403)), sent)
    with pytest.raises(SecRateLimitedError):
        edgar.shares_outstanding_with_provenance(["CY2025Q4I", "CY2026Q1I"])


def test_a_failing_newest_frame_never_serves_the_older_one(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ the same for a server error that outlives its retries."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, _frames(_OLDER, lambda: httpx.Response(503)), sent)
    with pytest.raises(HttpError, match="Exhausted retries"):
        edgar.shares_outstanding_with_provenance(["CY2025Q4I", "CY2026Q1I"])


def test_a_frame_that_does_not_exist_is_still_skipped(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ a period SEC has no frame for (404) contributes nothing, as before."""
    sent: list[tuple[float, str]] = []
    edgar = _edgar(tmp_path, clock, _frames(_OLDER, lambda: httpx.Response(404)), sent)
    values, tags = edgar.shares_outstanding_with_provenance(["CY2025Q4I", "CY2026Q1I"])
    assert values == {"0000000001": 111.0}


def test_a_404_is_its_own_type_and_still_an_http_error() -> None:
    """⊕ every existing `except HttpError` still catches a 404."""
    assert issubclass(HttpNotFoundError, HttpError)


# --- E1-D15: the User-Agent SEC requires --------------------------------------------------------

def _example_value() -> str:
    """The committed `.env.example` placeholder, read from the file itself."""
    line = next(ln for ln in (_REPO / ".env.example").read_text().splitlines()
                if ln.startswith("SEC_USER_AGENT="))
    return line.split("=", 1)[1]


def test_the_env_example_placeholder_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ copied unedited, `.env.example` declared a contact that reaches nobody."""
    monkeypatch.setenv("SEC_USER_AGENT", _example_value())
    with pytest.raises(RuntimeError, match="placeholder"):
        sec_user_agent()


@pytest.mark.parametrize("ua", ["x", "vinci-research", "Jane Doe", "jane at fund dot com"])
def test_a_user_agent_without_a_contact_email_is_refused(
        ua: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", ua)
    with pytest.raises(RuntimeError, match="contact email"):
        sec_user_agent()


def test_the_refusal_does_not_print_the_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ the CI value is a repository secret; the error names the variable, never its value."""
    monkeypatch.setenv("SEC_USER_AGENT", "Distinctive Name Without Mail")
    with pytest.raises(RuntimeError) as err:
        sec_user_agent()
    assert "Distinctive" not in str(err.value) and "SEC_USER_AGENT" in str(err.value)


@pytest.mark.parametrize("ua", ["Jane Doe jane.doe@fund.example.com", "Fund jane@fund.io"])
def test_a_declared_contact_passes(ua: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", ua)
    assert sec_user_agent() == ua


def test_the_default_user_agent_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    assert "@" in sec_user_agent()


def test_the_sec_factory_refuses_the_placeholder(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ end to end: the factory every SEC consumer builds through will not build with it."""
    monkeypatch.setenv("SEC_USER_AGENT", _example_value())
    with pytest.raises(RuntimeError, match="placeholder"):
        build_sec_http(Config(data_dir=tmp_path))


# --- a refusal stops the RUN, not one name (PR #854 review round 1) -----------------------------

def _refuse_once(tmp_path: Path, clock: _VirtualClock, sent: list[tuple[float, str]]) -> None:
    """Provoke the refusal that stops SEC traffic in this process: two requests, then the error."""
    http = _client(tmp_path, clock, lambda r: httpx.Response(429), sent, name="refused")
    with pytest.raises(SecRateLimitedError):
        http.get_text(_CF_URL)


def test_after_a_refusal_no_sec_request_leaves_the_process(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ dozens of broad `except Exception` handlers can swallow the refusal and go on to the next
    read. None of them may send: every later SEC request, from ANY client, raises at once."""
    sent: list[tuple[float, str]] = []
    _refuse_once(tmp_path, clock, sent)
    assert len(sent) == 2 and netcache.sec_refusal() is not None
    other = _client(tmp_path, clock, lambda r: httpx.Response(200, text="x"), sent, name="o")
    with pytest.raises(SecRateLimitedError, match="not sent"):
        other.get_text("https://www.sec.gov/Archives/edgar/data/1/x.htm")
    assert len(sent) == 2  # nothing more reached SEC


def test_after_a_refusal_other_hosts_are_untouched(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ the stop is SEC's: a Polygon or FINRA read still goes."""
    sent: list[tuple[float, str]] = []
    _refuse_once(tmp_path, clock, sent)
    plain = CachedHttp(cache_dir=tmp_path / "p", user_agent="t", min_interval_sec=0.0,
                       namespace="p")
    plain._client = httpx.Client(  # noqa: SLF001
        transport=httpx.MockTransport(lambda r: httpx.Response(200, text="ok")))
    assert plain.get_text("https://api.polygon.test/y") == "ok"


def test_a_403_refusal_names_the_user_agent_as_a_possible_cause(
        tmp_path: Path, clock: _VirtualClock) -> None:
    """⊖ SEC answers a fair-access block AND a User-Agent it does not accept with a 403, and the
    status cannot tell them apart — so the error names both, not only the pacing."""
    sent: list[tuple[float, str]] = []
    http = _client(tmp_path, clock, lambda r: httpx.Response(403, text="Forbidden"), sent)
    with pytest.raises(SecRateLimitedError, match="SEC_USER_AGENT"):
        http.get_text(_CF_URL)


def test_a_429_refusal_does_not_blame_the_user_agent(tmp_path: Path, clock: _VirtualClock) -> None:
    """⊕ a 429 is a rate limit and nothing else."""
    sent: list[tuple[float, str]] = []
    http = _client(tmp_path, clock, lambda r: httpx.Response(429), sent)
    with pytest.raises(SecRateLimitedError) as err:
        http.get_text(_CF_URL)
    assert "SEC_USER_AGENT" not in str(err.value)


def _finalists(n: int) -> list[Any]:
    from vinci.dossier import assemble as asm
    from vinci.rank import load_candidates_from_snapshot

    snap = _REPO / "data" / "snapshots" / "candidate_records.jsonl"
    if not snap.exists():
        pytest.skip("no committed candidate records in this checkout")
    by_ticker = {r.data_record.identity.ticker: r for r in load_candidates_from_snapshot(snap)}
    recs = list(by_ticker.values())[:n]
    assert len(recs) == n
    return [asm.Finalist(r, rank=i + 1, reference_date=date(2026, 10, 1))
            for i, r in enumerate(recs)]


def test_a_refused_cohort_stops_at_the_first_name(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ `assemble_cohort` logged SEC's refusal as ONE failed name and went on: the next name waited
    out the hold, sent, was refused, and re-armed it — for hours, every name recorded as failed.
    Through the real cohort: the first name's refusal stops the batch, loud."""
    from tests.sec_offline_support import no_network, seed_sec_cache
    from vinci.dossier import assemble as asm

    fins = _finalists(4)
    tried: list[str] = []

    def refused(fin: Any, **kw: Any) -> Any:
        tried.append(fin.data_record.identity.ticker)
        raise SecRateLimitedError("SEC refused (test)")

    monkeypatch.setattr(asm, "assemble_one", refused)
    cfg = Config(data_dir=tmp_path)
    seed_sec_cache(cfg)
    with no_network(), pytest.raises(SecRateLimitedError, match=r"3 name\(s\) not attempted"):
        asm.assemble_cohort(fins, cfg=cfg, max_workers=1)
    assert len(tried) == 1


def test_a_refused_exposure_scan_stops_instead_of_grading_every_name(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ the exposure scan graded a refusal as one more UNASSESSED name and moved on to the next."""
    import vinci.themes.exposure as ex_mod
    from vinci.themes.drivers import AI_DATACENTER

    names = [(f"T{i}", str(3000 + i)) for i in range(6)]
    tried: list[str] = []

    def stream(*a: Any, **k: Any) -> Any:
        tried.append("x")
        raise SecRateLimitedError("SEC refused (test)")

    monkeypatch.setattr(ex_mod, "mention_prefilter", lambda *a, **k: {c for _, c in names})
    monkeypatch.setattr(ex_mod, "recent_disclosure_stream", stream)
    with pytest.raises(SecRateLimitedError, match="STOPPED"):
        ex_mod.scan_driver_exposure(
            AI_DATACENTER, names, edgar=cast(Any, None), sec_http=cast(Any, None),
            efts_http=cast(Any, None), llm=cast(Any, None), startdt="2026-01-01",
            enddt="2026-06-01", max_workers=1)
    assert len(tried) <= 2  # the one refused, and at most the one a worker had already begun


def test_no_page_is_written_once_sec_has_refused_the_process(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ a page built across a refusal can carry blanks where a swallowed SEC read belonged — so the
    one write path refuses it; ⊕ and writes it once there is no refusal."""
    from vinci.dossier import assemble as asm
    from vinci.dossier.schemas import Dossier

    live = sorted((_REPO / "data" / "dossiers").glob("*/dossier.json"))[0]
    dossier = Dossier.model_validate_json(live.read_text())
    monkeypatch.setattr(netcache, "_SEC_STOPPED", SecRateLimitedError("SEC refused (test)"))
    with pytest.raises(SecRateLimitedError, match="NOT WRITTEN"):
        asm._write(dossier, "(test)", tmp_path)  # noqa: SLF001
    assert not (tmp_path / dossier.ticker).exists()
    monkeypatch.setattr(netcache, "_SEC_STOPPED", None)
    asm._write(dossier, "(test)", tmp_path)  # noqa: SLF001
    assert (tmp_path / dossier.ticker / "dossier.json").exists()
