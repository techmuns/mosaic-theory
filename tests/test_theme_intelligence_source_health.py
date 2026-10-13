"""Source health monitoring (Priority 1A) — the acceptance tests (H.1–H.13) and the guards around
them. Every publisher here is a SCRIPTED web (httpx.MockTransport): pages, statuses and refusals
are stated per URL, and every request is logged, so "never retried" and "nothing else fetched"
are counted, not assumed. Nothing touches the network; nothing calls an LLM.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.theme_intelligence_support import claim, extraction, hyp, make_pipeline
from vinci.theme_intelligence.config import USER_AGENT, SourceConfig, load_sources
from vinci.theme_intelligence.fetch import PoliteFetcher
from vinci.theme_intelligence.health import (
    BLOCKED_RECHECK_HOURS,
    HOOK_ENV,
    check_sources,
    render_text,
    summary,
    to_json,
)
from vinci.theme_intelligence.schemas import Freshness, HealthStatus, RunStatus
from vinci.theme_intelligence.store import Store

T0 = datetime(2026, 10, 11, 6, 0, tzinfo=UTC)
W_FROM, W_TO = date(2026, 10, 2), date(2026, 10, 11)


# --- a scripted web -------------------------------------------------------------------------------

class Web:
    """url -> (status, body) or an exception to raise; unknown URLs answer 404. Logs requests."""

    def __init__(self, pages: dict[str, Any] | None = None) -> None:
        self.pages: dict[str, Any] = dict(pages or {})
        self.log: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.log.append(url)
        r = self.pages.get(url, (404, ""))
        if isinstance(r, Exception):
            raise r
        status, body = r
        return httpx.Response(status, text=body, headers={"content-type": "text/html"},
                              request=request)

    def hits(self, url: str) -> int:
        return self.log.count(url)


def fetcher(tmp: Path, web: Web) -> PoliteFetcher:
    client = httpx.Client(transport=httpx.MockTransport(web), follow_redirects=True,
                          headers={"User-Agent": USER_AGENT})
    return PoliteFetcher(tmp / "http", min_delay_s=0.0, max_retries=0, client=client)


def src(sid: str = "pub_a", adapter: str = "generic_listing", **kw: Any) -> SourceConfig:
    host = f"{sid.replace('_', '-')}.test"
    return SourceConfig(id=sid, publisher=f"Publisher {sid[-1].upper()}", channel="test channel",
                        entry_url=f"https://{host}/research", adapter=adapter,
                        reliability="medium", default_article_class="publisher_commentary",
                        min_crawl_delay_s=0.0, link_pattern=rf"^https://{re.escape(host)}/articles/",
                        **kw)


def listing(items: list[tuple[str, str, str | None]]) -> str:
    """(slug, title, card date text or None) → a research listing page."""
    cards = "".join(f'<div class="card"><a href="/articles/{slug}">{title}</a>'
                    + (f"<span>{d}</span>" if d else "") + "</div>" for slug, title, d in items)
    return f"<html><body><main>{cards}</main></body></html>"


PARA = ("Memory makers raised contract prices again this quarter as AI servers absorbed most new "
        "supply, and the analysts expect the tightness to persist while capacity additions lag "
        "the demand that hyperscale buyers keep signalling in their orders and their guidance. ")


def article(title: str = "A real article", *, published: str | None = "2026-10-08",
            author: str | None = "Jane Analyst", paywall: bool = False, broken: bool = False,
            paras: int = 4) -> str:
    meta = ((f'<meta property="article:published_time" content="{published}T08:00:00Z">'
             if published else "") + (f'<meta name="author" content="{author}">' if author
                                      else ""))
    if broken:  # the text is still in the page, but only inside a script the parser never reads
        body = ('<div id="app"></div><script type="application/json">'
                + json.dumps({"body": PARA * 12}) + "</script>" + "<!-- pad -->" * 3000)
    else:
        body = (f"<article><h1>{title}</h1>"
                + "".join(f"<p>Point {i + 1}. {PARA}</p>" for i in range(paras))
                + ("<p>This post is for paid subscribers. Subscribe to continue reading.</p>"
                   if paywall else "") + "</article>")
    return (f"<html><head><title>{title}</title>{meta}</head><body>{body}</body></html>")


def healthy_web(s: SourceConfig, *, dates: tuple[str, str] = ("October 8, 2026",
                                                              "October 3, 2026")) -> Web:
    host = s.entry_url.split("/")[2]
    return Web({
        f"https://{host}/robots.txt": (404, ""),
        s.entry_url: (200, listing([("memory-prices", "Memory prices keep rising", dates[0]),
                                    ("grid-queues", "Grid queues lengthen", dates[1])])),
        f"https://{host}/articles/memory-prices": (200, article("Memory prices keep rising")),
        f"https://{host}/articles/grid-queues": (200, article("Grid queues lengthen")),
    })


def check(store: Store, f: PoliteFetcher, sources: list[SourceConfig], *,
          now: datetime = T0, force: bool = False) -> Any:
    return check_sources(sources, f, store, trigger="manual", window_from=W_FROM,
                         window_to=W_TO, now=now, force=force)


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "registry.db")


# --- H.1 every channel gets a status and a timestamp ----------------------------------------------

def test_every_configured_channel_receives_a_status_and_a_last_checked_time(
        tmp_path: Path, store: Store) -> None:
    """Every ACTIVE channel — six since Bank of America (2026-10-11) and Nomura (2026-10-13)
    were retired: the denominators follow the configuration, never a constant."""
    eight = [replace(s, min_crawl_delay_s=0.0) for s in load_sources()]
    n = len(eight)
    assert n == 6
    web = Web()  # every page of every host: 404, except what is stated below
    web.pages["https://www.goldmansachs.com/robots.txt"] = (403, "")
    web.pages["https://www.morganstanley.com/robots.txt"] = httpx.ConnectError("dropped")
    run = check(store, fetcher(tmp_path, web), eight)
    assert [h.source_id for h in run.checks] == [s.id for s in eight]
    assert all(h.status in HealthStatus and h.checked_at == T0 for h in run.checks)
    assert len(store.latest_health()) == n
    s = summary(run.checks, eight)
    assert s["total"] == n and sum(s["counts"].values()) == n
    assert s["line"].startswith(f"Sources healthy: 0/{n} | Degraded: ")


# --- H.2 a working listing with a broken article parser -------------------------------------------

def test_a_working_listing_with_a_broken_article_parser_is_detected(
        tmp_path: Path, store: Store) -> None:
    s = src()
    web = healthy_web(s)
    f = fetcher(tmp_path, web)
    first = check(store, f, [s]).checks[0]
    assert first.status is HealthStatus.HEALTHY and first.sample_words
    web.pages["https://pub-a.test/articles/memory-prices"] = (
        200, article("Memory prices keep rising", broken=True))
    # a week later (a fresh page cache: the 15-minute reuse window has long passed)
    h = check(store, fetcher(tmp_path / "week2", web), [s], now=T0 + timedelta(days=7)).checks[0]
    assert h.status is HealthStatus.DEGRADED  # the listing still answers 200 with links
    tests = {t.name: t for t in h.tests}
    assert tests["access"].result == "PASS" and tests["discovery"].result == "PASS"
    assert tests["parser_integrity"].result == "FAIL" and "parser failure" in h.reason
    assert any("extraction worked at the last check" in c for c in h.changes)
    assert h.alert == "NEW_FAILURE"
    assert h.last_successful_extraction == first.checked_at  # carried, not overwritten
    assert h.manual_action is not None and h.manual_action.kind == "UPLOAD_REQUIRED"


# --- H.3 HTTP 403 is BLOCKED, and never retried ---------------------------------------------------

def test_http_403_is_blocked_and_never_retried(tmp_path: Path, store: Store) -> None:
    s = src()
    web = Web({"https://pub-a.test/robots.txt": (404, ""), s.entry_url: (403, "denied")})
    f = fetcher(tmp_path, web)
    h = check(store, f, [s]).checks[0]
    assert h.status is HealthStatus.BLOCKED and "HTTP 403" in h.reason
    assert web.hits(s.entry_url) == 1  # one request, no retry
    assert h.manual_action is not None and h.manual_action.kind == "UPLOAD_REQUIRED"
    # a check again within the recheck interval does not knock on the door again …
    again = check(store, f, [s], now=T0 + timedelta(hours=2))
    assert web.hits(s.entry_url) == 1 and "not re-requested" in again.skipped[s.id]
    assert again.checks[0].check_id == h.check_id and len(store.health_checks(s.id)) == 1
    # … unless forced, or once the interval has passed
    check(store, f, [s], now=T0 + timedelta(hours=BLOCKED_RECHECK_HOURS + 1))
    assert web.hits(s.entry_url) == 2


# --- H.4 robots.txt that cannot be read fails closed, visibly -------------------------------------

@pytest.mark.parametrize("robots", [httpx.ConnectError("connection dropped"), (503, "")])
def test_an_unreadable_robots_txt_is_handled_conservatively_and_visibly(
        tmp_path: Path, store: Store, robots: Any) -> None:
    s = src()
    web = healthy_web(s)
    web.pages["https://pub-a.test/robots.txt"] = robots
    h = check(store, fetcher(tmp_path, web), [s]).checks[0]
    assert h.status is HealthStatus.BLOCKED
    assert "robots.txt" in h.reason and "FAIL CLOSED" in h.reason
    assert "cannot safely proceed" in h.reason  # said by the check, before any fetch is tried
    assert web.log == ["https://pub-a.test/robots.txt"]  # nothing else was fetched


# --- H.5 a paywalled preview is DEGRADED, never FULL ----------------------------------------------

def test_a_paywalled_preview_is_degraded_not_full(tmp_path: Path, store: Store) -> None:
    s = src()
    web = healthy_web(s)
    for slug, title in (("memory-prices", "Memory prices keep rising"),
                        ("grid-queues", "Grid queues lengthen")):
        web.pages[f"https://pub-a.test/articles/{slug}"] = (200, article(title, paywall=True))
    h = check(store, fetcher(tmp_path, web), [s]).checks[0]
    assert h.status is HealthStatus.DEGRADED and h.sample_retrieval == "PARTIAL"
    assert {t.name: t.result for t in h.tests}["completeness"] == "WARN"
    assert "paywalled preview" in h.reason
    assert h.last_successful_extraction is None  # a preview is not a full-text extraction
    assert h.manual_upload_recommended


@pytest.mark.parametrize(("policy", "status"), [("fetch", HealthStatus.HEALTHY),
                                                 ("request", HealthStatus.DEGRADED)])
def test_a_page_linking_its_report_degrades_only_where_the_report_is_not_read(
        tmp_path: Path, store: Store, policy: str, status: HealthStatus) -> None:
    """Observed 2026-10-11: Citi read DEGRADED ("that report was not read", upload required)
    although its policy fetches each page's linked report. Under "request" (Nomura) it is."""
    s = src(linked_reports=policy)
    web = healthy_web(s)
    for slug, title in (("memory-prices", "Memory prices keep rising"),
                        ("grid-queues", "Grid queues lengthen")):
        page = article(title).replace(
            "</article>", '<p>Must C: The Report</p><a href="https://pub-a.test/r.pdf">Download '
                          'Here</a></article>')
        web.pages[f"https://pub-a.test/articles/{slug}"] = (200, page)
    h = check(store, fetcher(tmp_path, web), [s]).checks[0]
    tests = {t.name: t for t in h.tests}
    assert h.status is status, h.reason
    if policy == "fetch":
        assert tests["completeness"].result == "PASS" and "the scan READS it" in \
            tests["completeness"].detail
        assert not h.manual_upload_recommended
    else:
        assert tests["completeness"].result == "WARN" and "summarises" in h.reason
        assert h.manual_upload_recommended


# --- H.6 nothing new this week is QUIET, not unhealthy --------------------------------------------

def test_an_accessible_channel_with_no_new_article_is_not_unhealthy(
        tmp_path: Path, store: Store) -> None:
    s = src()
    web = healthy_web(s, dates=("August 20, 2026", "August 4, 2026"))
    web.pages["https://pub-a.test/articles/memory-prices"] = (
        200, article("Memory prices keep rising", published="2026-08-20"))
    h = check(store, fetcher(tmp_path, web), [s]).checks[0]
    assert h.status is HealthStatus.HEALTHY
    assert h.freshness is Freshness.QUIET and h.in_window == 0
    assert "QUIET, not unhealthy" in {t.name: t for t in h.tests}["freshness"].detail


# --- H.7 missing publication dates are a visible metadata problem ---------------------------------

def test_missing_publication_dates_create_a_visible_metadata_problem(
        tmp_path: Path, store: Store) -> None:
    s = src()
    web = healthy_web(s, dates=("", ""))
    for slug in ("memory-prices", "grid-queues"):
        web.pages[f"https://pub-a.test/articles/{slug}"] = (200, article(published=None))
    h = check(store, fetcher(tmp_path, web), [s]).checks[0]
    assert h.status is HealthStatus.DEGRADED and "metadata problem" in h.reason
    assert h.manual_action is not None and h.manual_action.kind == "MANUAL_REVIEW"
    att = summary([h], [s])["attention"]
    assert [r["source_id"] for r in att] == ["pub_a"] and "metadata problem" in att[0]["reason"]
    # the same at the next check is said to persist
    h2 = check(store, fetcher(tmp_path, web), [s], now=T0 + timedelta(days=7)).checks[0]
    assert any("publication dates missing at 2 consecutive checks" in c for c in h2.changes)


# --- H.8 a working channel becoming blocked is a health-change event ------------------------------

def test_a_previously_working_channel_becoming_blocked_raises_a_change(
        tmp_path: Path, store: Store) -> None:
    s = src()
    web = healthy_web(s)
    f = fetcher(tmp_path, web)
    assert check(store, f, [s]).checks[0].status is HealthStatus.HEALTHY
    web.pages[s.entry_url] = (403, "")
    t1 = T0 + timedelta(days=7)
    h = check(store, f, [s], now=t1).checks[0]
    assert h.status is HealthStatus.BLOCKED and "HEALTHY → BLOCKED" in h.changes
    assert h.alert == "NEW_FAILURE" and h.consecutive_failed_checks == 1
    assert h.status_since == t1


# --- H.9 a blocked channel becoming accessible is detected ----------------------------------------

def test_a_blocked_channel_becoming_accessible_is_detected(tmp_path: Path, store: Store) -> None:
    s = src()
    web = healthy_web(s)
    web.pages[s.entry_url] = (403, "")
    f = fetcher(tmp_path, web)
    blocked = check(store, f, [s]).checks[0]
    assert blocked.status is HealthStatus.BLOCKED and blocked.manual_upload_recommended
    web.pages[s.entry_url] = healthy_web(s).pages[s.entry_url]
    h = check(store, f, [s], now=T0 + timedelta(days=7)).checks[0]
    assert h.status is HealthStatus.HEALTHY and h.alert == "RECOVERED"
    assert any("accessible again" in c for c in h.changes)
    assert h.manual_action is None  # the upload requirement is lifted for FUTURE articles


# --- H.10 manual ingestion goes on while the channel is BLOCKED -----------------------------------

def test_manual_ingestion_continues_while_the_publisher_is_blocked(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    gs = next(s for s in pipe.sources.values() if s.id == "gs_research")
    web = Web({"https://www.goldmansachs.com/robots.txt": (404, ""),
               gs.entry_url: (403, "Access Denied")})
    blocked = check_sources([replace(gs, min_crawl_delay_s=0.0)], fetcher(tmp_path, web),
                            pipe.store, trigger="manual", window_from=W_FROM, window_to=W_TO,
                            now=T0).checks[0]
    assert blocked.status is HealthStatus.BLOCKED
    url = "https://www.goldmansachs.com/insights/articles/hypothetical-upload"
    text = PARA.strip().rstrip(".")
    run, res = pipe.run_article(
        url, as_of=date(2026, 10, 9), source_id="gs_research", html=article(
            "[HYPOTHETICAL TEST FIXTURE] An uploaded note", published="2026-10-08"),
        fixture=extraction([claim("c1", "b001", text, "contract prices rose", kind="assertion",
                                  epistemic="opinion")],
                           [hyp("h1", "AI memory tightness", node="ai_infrastructure.memory",
                                mechanism="pricing_cycle", supporting=["c1"])]),
        html_note="operator-supplied copy — a MANUAL UPLOAD of an authorized document")
    assert res.status in ("PROCESSED", "PARTIAL_PROCESSED") and res.article_id
    assert run.status is not RunStatus.FAILED
    av = pipe.store.article_versions(res.article_id)[-1]
    assert "MANUAL UPLOAD" in av.retrieval_note
    # one uploaded document is not proof of coverage: the channel stays BLOCKED, upload required
    after = pipe.store.latest_health()["gs_research"]
    assert after.check_id == blocked.check_id and after.status is HealthStatus.BLOCKED
    assert after.manual_upload_recommended


# --- H.11 one channel's failure cannot stop the others --------------------------------------------

def test_one_channel_failing_never_stops_the_others(tmp_path: Path, store: Store,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    import vinci.theme_intelligence.health as health_mod

    a, b, c, d = (src("pub_a"), src("pub_b"), src("pub_c", adapter="broken_adapter"),
                  src("pub_d"))

    def broken(*_: Any, **__: Any) -> Any:
        raise ValueError("adapter bug")

    real_parse = health_mod.parse_document

    def parse(html: str, url: str, final: str | None = None) -> Any:
        if url.startswith("https://pub-d.test/"):  # the CHECK itself crashes, past the adapter
            raise KeyError("parser bug")
        return real_parse(html, url, final)

    monkeypatch.setitem(health_mod.ADAPTERS, "broken_adapter", broken)
    monkeypatch.setattr(health_mod, "parse_document", parse)
    web = healthy_web(a)
    web.pages.update(healthy_web(c).pages)
    web.pages.update(healthy_web(d).pages)
    web.pages.update({"https://pub-b.test/robots.txt": (404, ""), b.entry_url: (403, "")})
    run = check(store, fetcher(tmp_path, web), [d, c, b, a])
    st = {h.source_id: h.status for h in run.checks}
    assert st == {"pub_d": HealthStatus.ERROR, "pub_c": HealthStatus.ERROR,
                  "pub_b": HealthStatus.BLOCKED, "pub_a": HealthStatus.HEALTHY}
    crashed = next(h for h in run.checks if h.source_id == "pub_d")
    assert "the health check itself failed (KeyError)" in crashed.reason
    assert "Traceback" not in crashed.reason


def test_a_scan_checks_health_first_and_never_asks_a_refusing_channel_twice(
        tmp_path: Path) -> None:
    from vinci.theme_intelligence.config import load_taxonomy
    from vinci.theme_intelligence.pipeline import Pipeline

    a, b = src("pub_a"), src("pub_b")
    web = healthy_web(a)
    web.pages.update({"https://pub-b.test/robots.txt": (404, ""), b.entry_url: (403, "")})
    pipe = Pipeline(tmp_path / "ti", sources=(a, b), taxonomy=load_taxonomy(), client=None,
                    fetcher=fetcher(tmp_path, web), review=False)
    run = pipe.run_scan(window_from=W_FROM, window_to=W_TO, as_of=W_TO, max_articles=0)
    cov = {c.source_id: c for c in run.sources}
    assert cov["pub_b"].status == "BLOCKED" and "HTTP 403" in cov["pub_b"].errors[0]
    assert cov["pub_a"].status == "OK" and cov["pub_a"].discovered == 2  # the other scanned on
    assert web.hits(b.entry_url) == 1  # the health check's request — discovery never re-asked
    assert web.hits(a.entry_url) == 1  # the live health fetch was reused by discovery
    checked = {h.source_id: h for h in pipe.store.health_checks(run_id=run.run_id)}
    assert set(checked) == {"pub_a", "pub_b"} and checked["pub_b"].trigger == "scan"
    assert run.status is RunStatus.PARTIAL  # a failing channel is never a quiet week


# --- H.12 health checks never call the LLM --------------------------------------------------------

def test_health_checks_import_and_call_nothing_of_the_llm_pipeline() -> None:
    root = Path(__file__).parents[1] / "vinci" / "theme_intelligence"
    forbidden = {"vinci.graph.llm", "vinci.theme_intelligence.extract",
                 "vinci.theme_intelligence.engine", "vinci.theme_intelligence.completeness",
                 "vinci.theme_intelligence.pipeline"}
    seen: set[str] = set()
    todo = ["vinci.theme_intelligence.health"]
    while todo:  # the TRANSITIVE import closure of the health module, within vinci
        mod = todo.pop()
        if mod in seen or not mod.startswith("vinci."):
            continue
        seen.add(mod)
        path = root.parent.parent / (mod.replace(".", "/") + ".py")
        if not path.exists():
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                todo.append(node.module)
            elif isinstance(node, ast.Import):
                todo += [a.name for a in node.names]
    assert not seen & forbidden, seen & forbidden


def test_the_health_cli_runs_without_an_llm_key(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    import vinci.theme_intelligence.__main__ as cli

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    web = Web()  # every host 404: each channel is checked and recorded, none is reachable
    monkeypatch.setattr(cli, "_health_fetcher", lambda paths: fetcher(tmp_path, web))
    monkeypatch.setattr(cli, "load_sources", lambda: tuple(
        replace(s, min_crawl_delay_s=0.0) for s in load_sources()))
    assert cli.main(["--data-dir", str(tmp_path / "ti"), "sources", "--check-health",
                     "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["total"] == len(load_sources()) == len(out["sources"]) == 6
    assert out["summary"].startswith("Sources healthy: ")
    assert all(r["checked_at"] and r["status"] in HealthStatus.__members__ for r in out["sources"])


# --- H.13 status and history survive a restart (export → import) --------------------------------

def test_a_recorded_health_check_can_never_be_rewritten(tmp_path: Path, store: Store) -> None:
    """The store's parametrised append-only test skips a table its fixture leaves empty — and
    its fixture runs no health check — so the triggers are pinned here."""
    import sqlite3

    s = src()
    check(store, fetcher(tmp_path, healthy_web(s)), [s])
    for sql in ("DELETE FROM source_health", "UPDATE source_health SET payload = payload"):
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            store.conn.execute(sql)
    assert len(store.health_checks(s.id)) == 1


def test_health_history_survives_a_scheduled_restart(tmp_path: Path) -> None:
    s = src()
    web = Web({"https://pub-a.test/robots.txt": (404, ""), s.entry_url: (403, "")})
    one = Store(tmp_path / "one.db")
    first = check(one, fetcher(tmp_path, web), [s]).checks[0]
    one.export_jsonl(tmp_path / "state")  # what the scheduled run commits to its state branch
    two = Store.import_jsonl(tmp_path / "state", tmp_path / "two.db")
    assert [h.check_id for h in two.health_checks(s.id)] == [first.check_id]
    h = check(two, fetcher(tmp_path, web), [s], now=T0 + timedelta(days=7)).checks[0]
    assert h.consecutive_failed_checks == 2 and h.status_since == first.checked_at
    assert len(two.health_checks(s.id)) == 2


# --- expect_blocked never conceals, alerts never repeat -------------------------------------------

def test_expect_blocked_never_conceals_a_blocked_channel(tmp_path: Path, store: Store) -> None:
    s = src(expect_blocked=True)
    web = Web({"https://pub-a.test/robots.txt": (404, ""), s.entry_url: (403, "")})
    f = fetcher(tmp_path, web)
    h = check(store, f, [s]).checks[0]
    assert h.status is HealthStatus.BLOCKED and h.alert == "KNOWN_RESTRICTION"
    sm = summary([h], [s])
    assert sm["counts"]["BLOCKED"] == 1 and sm["attention"][0]["status"] == "BLOCKED"
    h2 = check(store, f, [s], now=T0 + timedelta(days=7)).checks[0]
    assert h2.status is HealthStatus.BLOCKED and h2.alert == ""  # shown, not re-alerted


def test_alerts_go_to_the_hook_once_per_change(tmp_path: Path, store: Store,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    sink = tmp_path / "alerts.jsonl"
    hook = tmp_path / "hook.py"
    hook.write_text("import sys\nopen(sys.argv[1], 'a').write(sys.stdin.read().replace("
                    "'\\n', ' ') + '\\n')\n")
    monkeypatch.setenv(HOOK_ENV, f"{Path(__import__('sys').executable)} {hook} {sink}")
    s = src()
    web = healthy_web(s)
    f = fetcher(tmp_path, web)
    check(store, f, [s])  # HEALTHY: nothing to say
    web.pages[s.entry_url] = (500, "")
    sent = []
    for day in range(1, 5):  # ERROR on four consecutive checks
        h = check(store, f, [s], now=T0 + timedelta(days=day)).checks[0]
        sent.append(h.alert)
    assert sent == ["NEW_FAILURE", "", "PERSISTENT_FAILURE", ""]
    lines = sink.read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])[0]["alert"] == "NEW_FAILURE"


def test_the_dashboard_shows_the_health_block_without_stack_traces(
        tmp_path: Path, store: Store) -> None:
    from vinci.theme_intelligence.report import _health_html

    a, b = src("pub_a"), src("pub_b")
    web = healthy_web(a)
    web.pages.update({"https://pub-b.test/robots.txt": (404, ""), b.entry_url: (403, "")})
    run = check(store, fetcher(tmp_path, web), [a, b])
    html = _health_html(summary(run.checks, [a, b]), print_mode=False)
    assert "Sources healthy: 1/2 | Degraded: 0 | Blocked: 1 | Errors: 0" in html
    attention = html.split("<details")[0]
    assert "Publisher B" in attention and "Publisher A" not in attention  # only who needs it
    assert "All 2 publishers" in html and "Publisher A" in html.split("<details")[1]
    assert "Traceback" not in html and 'File "' not in html
    assert to_json(run, [a, b])["counts"]["BLOCKED"] == 1


# --- the live run of 2026-10-11: one sample hid what most pages do --------------------------------

@pytest.mark.parametrize(("shape", "newest", "older", "says"), [
    ("Bank of America: the newest page is dated, the others state no date",
     {"published": "2026-10-08"}, {"published": None}, "metadata problem"),
    ("SemiAnalysis: the newest post is free, the others are paid previews",
     {}, {"paywall": True}, "paywalled previews"),
])
def test_a_channel_is_judged_on_several_articles_not_one(
        tmp_path: Path, store: Store, shape: str, newest: dict[str, Any], older: dict[str, Any],
        says: str) -> None:
    s = src()
    host = "pub-a.test"
    web = Web({f"https://{host}/robots.txt": (404, ""), s.entry_url: (200, listing(
        [("newest", "The newest note", "October 9, 2026"), ("second", "A second note", None),
         ("third", "A third note", None)])),
        f"https://{host}/articles/newest": (200, article("The newest note", **newest)),
        f"https://{host}/articles/second": (200, article("A second note", **older)),
        f"https://{host}/articles/third": (200, article("A third note", **older))})
    h = check(store, fetcher(tmp_path, web), [s]).checks[0]
    assert h.status is HealthStatus.DEGRADED and says in h.reason, shape
    assert len(h.samples) == 3 and "2 of 3" in h.reason, shape


def _undated_listing_shape(s: SourceConfig) -> Web:
    """The live Bank of America shape (2026-10-11): an undated listing whose FIRST entries are
    one dated series, the pages further down stating no date."""
    host = s.entry_url.split("/")[2]
    slugs = [f"note-{i}" for i in range(9)]
    web = Web({f"https://{host}/robots.txt": (404, ""), s.entry_url: (200, listing(
        [(x, f"Insight note number {i}", None) for i, x in enumerate(slugs)]))})
    for i, x in enumerate(slugs):
        web.pages[f"https://{host}/articles/{x}"] = (200, article(
            f"Insight note number {i}", published="2026-06-25" if i < 3 else None))
    return web


def test_the_sample_is_spread_across_the_listing_not_its_top(
        tmp_path: Path, store: Store) -> None:
    s = src()
    h = check(store, fetcher(tmp_path, _undated_listing_shape(s)), [s]).checks[0]
    assert [x.split(" — ")[0].rsplit("/", 1)[1] for x in h.samples] == [
        "note-0", "note-4", "note-8"]
    assert h.status is HealthStatus.DEGRADED and "metadata problem" in h.reason


def test_the_latest_scans_undated_share_is_date_evidence(tmp_path: Path, store: Store) -> None:
    """A scan reads EVERY candidate's page; three samples can miss what it saw."""
    from vinci.theme_intelligence.schemas import SourceCoverage, WeeklyRun

    s = src()
    store.upsert_run(WeeklyRun(
        run_id="R-prior-scan", mode="scan", window_from=W_FROM, window_to=W_TO, as_of=W_TO,
        started_at=T0 - timedelta(days=1), finished_at=T0 - timedelta(days=1),
        status=RunStatus.SUCCEEDED, llm_provider="x", llm_model="x", extract_prompt_version="x",
        review_prompt_version="x", parser_version="x", engine_version="x", db_schema_version=3,
        sources=[SourceCoverage(source_id=s.id, publisher=s.publisher, channel=s.channel,
                                method="x", status="OK", discovered=16, undated=12)]))
    h = check(store, fetcher(tmp_path, healthy_web(s)), [s]).checks[0]  # every SAMPLE is dated
    assert h.status is HealthStatus.DEGRADED
    assert "the latest scan found 12 of 16" in h.reason and h.last_scan_undated == 12


def _one_article_web(s: SourceConfig, slug: str, paras: int) -> Web:
    host = s.entry_url.split("/")[2]
    return Web({f"https://{host}/robots.txt": (404, ""), s.entry_url: (200, listing(
        [(slug, f"The {slug} note", "October 8, 2026")])),
        f"https://{host}/articles/{slug}": (200, article(f"The {slug} note", paras=paras))})


def test_a_short_article_is_never_judged_against_a_different_long_one(
        tmp_path: Path, store: Store) -> None:
    """Observed in the live re-check of 2026-10-11: Citi's 96-word teasers were flagged as a
    parser failure against a 570-word article read at the previous check."""
    s = src()
    check(store, fetcher(tmp_path, _one_article_web(s, "long-report", 12)), [s])
    h = check(store, fetcher(tmp_path / "later", _one_article_web(s, "short-teaser", 2)), [s],
              now=T0 + timedelta(days=7)).checks[0]
    assert {t.name: t.result for t in h.tests}["parser_integrity"] == "PASS"
    assert "parser failure" not in h.reason  # a short page is partial, not a broken parser


def test_the_same_page_read_far_shorter_than_before_is_a_parser_failure(
        tmp_path: Path, store: Store) -> None:
    s = src()
    first = check(store, fetcher(tmp_path, _one_article_web(s, "report", 12)), [s]).checks[0]
    assert first.sample_words_by_url and first.sample_words_by_url[0][1] >= 300
    h = check(store, fetcher(tmp_path / "later", _one_article_web(s, "report", 1)), [s],
              now=T0 + timedelta(days=7)).checks[0]
    assert h.status is HealthStatus.DEGRADED and "extraction collapsed" in h.reason
    assert any("parser failure suspected" in c for c in h.changes)


# --- the seven-source live check, 2026-10-11 ------------------------------------------------

def test_an_upload_request_names_the_page_that_was_partial_not_the_first_sample(
        tmp_path: Path, store: Store) -> None:
    """Observed 2026-10-11 (live check): Citi's next action asked for an upload of its LatAm
    page — whose linked report the scan READS ("fetch") — while the partial page was a 96-word
    teaser. The page linking its report is sampled first here; the teaser second."""
    s = src(linked_reports="fetch")
    web = healthy_web(s)
    web.pages["https://pub-a.test/articles/memory-prices"] = (200, article(
        "Memory prices keep rising").replace(
        "</article>", '<p>Must C: The Report</p><a href="https://pub-a.test/r.pdf">Download '
                      'Here</a></article>'))
    web.pages["https://pub-a.test/articles/grid-queues"] = (200, article("Grid queues lengthen",
                                                                         paras=2))
    h = check(store, fetcher(tmp_path, web), [s]).checks[0]
    assert h.status is HealthStatus.DEGRADED and "short body" in h.reason
    assert h.manual_action is not None
    assert [a.split(" — ")[0] for a in h.manual_action.affected] == [
        "https://pub-a.test/articles/grid-queues"]


def test_a_persistent_failure_says_what_persists_and_a_cut_list_says_it_is_cut(
        tmp_path: Path, store: Store) -> None:
    """Observed 2026-10-11 (live check): "[PERSISTENT_FAILURE] Citi: " printed with nothing
    after it — a persistent failure changes nothing, so its changes list is empty."""
    s = src()
    web = healthy_web(s)
    f = fetcher(tmp_path, web)
    check(store, f, [s])
    web.pages[s.entry_url] = (403, "")  # access refused from now on
    for i in range(12):  # twelve known articles the channel could not serve
        store.upsert_candidate(f"https://pub-a.test/articles/x{i:02d}", s.id, "INACCESSIBLE",
                               {"source_id": s.id, "title": f"Article {i}"})
    runs = [check(store, f, [s], now=T0 + timedelta(days=d), force=True) for d in (1, 2, 3)]
    text = render_text(runs[-1], [s])
    alerts = [h.alert for r in runs for h in r.checks]
    assert "PERSISTENT_FAILURE" in alerts, alerts
    persistent = runs[alerts.index("PERSISTENT_FAILURE")]
    line = next(x for x in render_text(persistent, [s]).splitlines() if "[PERSISTENT_FAILURE]" in x)
    assert line.split(": ", 1)[1].startswith("still BLOCKED after"), line
    h = runs[-1].checks[0]
    assert h.manual_action is not None
    assert h.manual_action.affected[-1].startswith("… and ")  # the record states its cut
    assert "(showing 10 of" in h.manual_action.affected[-1]
    assert "(showing 3 of" in text  # and so does the printed report
