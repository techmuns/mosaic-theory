"""Discovery, scan orchestration and the weekly dashboard.

Listing HTML here follows the SHAPES the live adapters met on 2026-10-09/10 (JPM's dated cards,
TrendForce's dated URLs, a feed's pubDate) — the live scan is the corpus check; these pin the
behaviour that must not regress: a failed source is reported (never a silent zero), a budget cap
queues (and says so), an interrupted scan resumes, and the dashboard never hides a category.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
)
from vinci.theme_intelligence import pipeline as pipeline_mod
from vinci.theme_intelligence.config import load_sources
from vinci.theme_intelligence.discovery import (
    Candidate,
    Discovery,
    canon,
    card_links,
    date_in_text,
    discover_source,
)
from vinci.theme_intelligence.fetch import FetchResult, FetchStats
from vinci.theme_intelligence.pipeline import ArticleResult, Pipeline
from vinci.theme_intelligence.report import build_dashboard, render_dashboard_html, write_cards
from vinci.theme_intelligence.schemas import RetrievalState, RunStatus, SourceCoverage

WINDOW = (date(2026, 10, 1), date(2026, 10, 10))


class LiveNetworkError(BaseException):
    """A BaseException on purpose: the scan's broad `except Exception` must not swallow it."""


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test here may reach a real host. Observed 2026-10-11: the scan's new source-health pass
    went to the LIVE publishers from these offline tests (minutes of crawl delays) because
    `_fake_scan` stubbed discovery but not the health check."""
    import httpx

    def refuse(self: Any, request: Any) -> Any:
        raise LiveNetworkError(f"live network request in an offline test: {request.url}")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


class FakeFetcher:
    def __init__(self, pages: dict[str, str | None]) -> None:
        self.pages = pages
        self.stats = FetchStats()
        self.calls: list[str] = []

    def set_host_floor(self, url: str, seconds: float) -> None:
        pass

    def fetch(self, url: str, *, ttl_s: float | None = None) -> FetchResult:
        self.calls.append(url)
        now = datetime.now(tz=UTC)
        body = self.pages.get(url)
        if body is None:
            return FetchResult(url, None, 403, RetrievalState.BLOCKED, "HTTP 403", None, None,
                               now, None, None, False, 0.0)
        raw = body.encode()
        return FetchResult(url, url, 200, RetrievalState.FULL, "fetched", raw, "text/html", now,
                           hashlib.sha256(raw).hexdigest(), None, False, 0.0)


def _src(sid: str) -> Any:
    return next(s for s in load_sources() if s.id == sid)


JPM_LIST = """<html><body><nav><a href="/apac/en/insights/markets-and-investing/tmt/nav-item">
Nav item Oct 9, 2026</a></nav><main>
<div class="card"><a href="/apac/en/insights/markets-and-investing/tmt/a-calm-index">A calm
index, a restless market</a><span>Oct 2, 2026</span></div>
<div class="card"><a href="/apac/en/insights/markets-and-investing/tmt/one-economy">One economy,
two markets</a><span>Sep 25, 2026</span></div>
<div class="card"><a href="/apac/en/insights/markets-and-investing/tmt/no-date-here">An undated
card</a></div></main></body></html>"""
JPM_BASE = "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt"


def test_helpers_read_dates_and_canonical_urls() -> None:
    assert date_in_text("published Oct 2, 2026 ·") == date(2026, 10, 2)
    assert date_in_text("8 October 2026") == date(2026, 10, 8)
    assert date_in_text("2026-09-14") == date(2026, 9, 14)
    assert date_in_text("no date") is None
    assert canon("https://Example.test/a/?utm_source=x#top") == "https://example.test/a"


def test_card_dates_come_from_the_link_s_own_card_only() -> None:
    import re

    from bs4 import BeautifulSoup
    links = card_links(BeautifulSoup(JPM_LIST, "html.parser"), JPM_BASE,
                       re.compile("^" + re.escape(JPM_BASE) + r"/[^/]+$"))
    by = {u.rsplit("/", 1)[1]: d for u, _, d in links}
    assert by == {"a-calm-index": date(2026, 10, 2), "one-economy": date(2026, 9, 25),
                  "no-date-here": None}  # nav chrome excluded; no neighbour's date borrowed


def test_window_known_and_undated_accounting(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    undated_page = ("<html><body><article>" + "<p>Text without any date. " * 60
                    + "</p></article></body></html>")
    f = FakeFetcher({JPM_BASE: JPM_LIST, f"{JPM_BASE}/no-date-here": undated_page})
    d = discover_source(_src("jpm_tmt"), f, pipe.store,
                        window_from=WINDOW[0], window_to=WINDOW[1])
    cov = d.coverage
    assert (cov.discovered, cov.in_window, cov.new, cov.skipped_out_of_window, cov.undated) == \
        (3, 1, 1, 1, 1)
    assert cov.status == "OK" and cov.warnings  # undated is reported, never placed in a window
    assert [c.url.rsplit("/", 1)[1] for c in d.selected] == ["a-calm-index"]


def test_a_blocked_source_is_reported_not_a_quiet_zero(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    d = discover_source(_src("gs_research"), FakeFetcher({}), pipe.store,
                        window_from=WINDOW[0], window_to=WINDOW[1])
    assert d.coverage.status == "BLOCKED" and "403" in d.coverage.errors[0]
    assert any("standing access limitation" in w for w in d.coverage.warnings)
    # a channel NOT documented as blocked that fails is a plain failure
    jpm = replace(_src("jpm_tmt"), expect_blocked=False)
    d2 = discover_source(jpm, FakeFetcher({}), pipe.store,
                         window_from=WINDOW[0], window_to=WINDOW[1])
    assert d2.coverage.status == "BLOCKED" and not d2.coverage.warnings


def test_a_broken_adapter_is_an_error_row(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    d = discover_source(_src("citi_must_c"), FakeFetcher({_src("citi_must_c").entry_url:
                                                          "<html>no page data</html>"}),
                        pipe.store, window_from=WINDOW[0], window_to=WINDOW[1])
    assert d.coverage.status == "ERROR" and "__NEXT_DATA__" in d.coverage.errors[0]


# --- scan orchestration --------------------------------------------------------------------------

def _fake_scan(monkeypatch: pytest.MonkeyPatch, pipe: Pipeline, urls: list[str],
               failing_source: bool = False, interrupt_on: str | None = None) -> list[str]:
    srcs = list(pipe.sources.values())

    def discover(src: Any, f: Any, store: Any, *, window_from: date,
                 window_to: date) -> Discovery:
        cov = SourceCoverage(source_id=src.id, publisher=src.publisher, channel=src.channel,
                             method="test", status="OK")
        cands = []
        if src is srcs[0]:
            for u in urls:
                cands.append(Candidate(url=u, source_id=src.id, listed_date=date(2026, 10, 2),
                                       date_basis="listing card date", status="IN_WINDOW"))
            cov.discovered = cov.in_window = cov.new = len(urls)
        if failing_source and src is srcs[1]:
            cov.status, cov.errors = "BLOCKED", ["HTTP 403"]
        return Discovery(cov, cands)

    processed: list[str] = []

    def process_url(self: Pipeline, url: str, *, source_id: str, as_of: date,
                    **kw: Any) -> ArticleResult:
        if url == interrupt_on:
            raise KeyboardInterrupt
        processed.append(url)
        art = Hypo(slug=url.rsplit("/", 1)[1], publisher="Hypo", published=date(2026, 10, 2),
                   blocks=[("paragraph", f"Optical shipments rose {len(processed) + 10}% in "
                                         f"3Q26 at {url}.")])
        n = len(processed) + 10
        x = extraction([claim("c1", "b001", f"Optical shipments rose {n}% in 3Q26",
                              f"Optical shipments +{n}%", metric="optical shipments",
                              value=n, value_text=f"{n}%", unit="%", period="3Q26")],
                       [hyp("h1", "Optics ramp", node="ai_infrastructure.optical_networking",
                            mechanism="demand_volume_shift", supporting=["c1"])])
        return ingest(self, art.doc(), x, as_of=as_of)

    def health(sources: Any, f: Any, store: Any, *, trigger: str, window_from: date,
               window_to: date, run_id: str | None = None, **_: Any) -> Any:
        """The scan's source-health pass, offline: one UNKNOWN row per channel (the check itself
        is exercised against a scripted web in test_theme_intelligence_source_health.py)."""
        from vinci.theme_intelligence.health import HealthRun
        from vinci.theme_intelligence.schemas import HealthStatus, SourceHealthCheck

        rows = [SourceHealthCheck(
            check_id=f"SH-test-{run_id}-{s.id}", source_id=s.id, publisher=s.publisher,
            checked_at=datetime.now(tz=UTC), trigger=trigger, run_id=run_id,
            status=HealthStatus.UNKNOWN, reason="not checked (no network in tests)",
            next_action="—") for s in sources]
        for h in rows:
            store.add_health_check(h)
        return HealthRun(checks=rows)

    monkeypatch.setattr(pipeline_mod, "discover_source", discover)
    monkeypatch.setattr(pipeline_mod, "check_sources", health)
    monkeypatch.setattr(Pipeline, "process_url", process_url)
    return processed


def test_a_budget_cap_queues_the_rest_and_says_so(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = make_pipeline(tmp_path)
    urls = [f"https://example.test/hypothetical/a{i}" for i in range(4)]
    done = _fake_scan(monkeypatch, pipe, urls)
    run = pipe.run_scan(window_from=WINDOW[0], window_to=WINDOW[1], as_of=WINDOW[1],
                        max_articles=2)
    assert len(done) == 2 and run.counts["articles_queued"] == 2
    assert any("processed 2 of 4" in w for w in run.warnings)
    queued = [u for u, _, _ in pipe.store.candidates("QUEUED")]
    assert len(queued) == 2
    # a run that re-discovers them and dies before reading them must not lose the queue
    _fake_scan(monkeypatch, pipe, urls, interrupt_on=sorted(queued)[0])
    with pytest.raises(KeyboardInterrupt):
        pipe.run_scan(window_from=WINDOW[0], window_to=WINDOW[1], as_of=WINDOW[1],
                      max_articles=2)
    assert sorted(u for u, _, _ in pipe.store.candidates("QUEUED")) == sorted(queued)
    # the next run offers the queued items FIRST, ahead of what it discovers itself
    done = _fake_scan(monkeypatch, pipe, [f"https://example.test/hypothetical/b{i}"
                                          for i in range(3)])
    pipe.run_scan(window_from=WINDOW[0], window_to=WINDOW[1], as_of=WINDOW[1], max_articles=2)
    assert set(done) == set(queued)
    assert len(pipe.store.candidates("QUEUED")) == 3  # this run's own three now wait in turn


def test_a_candidate_later_ruled_out_of_the_window_leaves_the_review_list(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Observed 2026-10-11 (on Bank of America's pages, a channel since retired): 12 pages
    stayed UNDATED on the review list after a scan had bounded them out of the window by their
    last modification — an OUT_OF_WINDOW result was never written back over the stale row. A
    processed row is never touched."""
    pipe = make_pipeline(tmp_path)
    _fake_scan(monkeypatch, pipe, [])
    undated, done = "https://example.test/hypothetical/undated", "https://example.test/hypothetical/done"
    sid = list(pipe.sources)[0]
    pipe.store.upsert_candidate(undated, sid, "UNDATED", {"note": "old"})
    pipe.store.upsert_candidate(done, sid, "PROCESSED", {"note": "read"})
    srcs = list(pipe.sources.values())

    def discover(src: Any, f: Any, store: Any, *, window_from: date,
                 window_to: date) -> Discovery:
        cov = SourceCoverage(source_id=src.id, publisher=src.publisher, channel=src.channel,
                             method="test", status="OK")
        cands = [Candidate(url=u, source_id=src.id, status="OUT_OF_WINDOW",
                           note="last modified 2025-09-26 — before the window")
                 for u in (undated, done)] if src is srcs[0] else []
        return Discovery(cov, cands)

    monkeypatch.setattr(pipeline_mod, "discover_source", discover)
    pipe.run_scan(window_from=WINDOW[0], window_to=WINDOW[1], as_of=WINDOW[1], max_articles=2)
    assert pipe.store.candidate(undated)[0] == "OUT_OF_WINDOW"  # type: ignore[index]
    assert pipe.store.candidate(done)[0] == "PROCESSED"  # type: ignore[index]
    assert pipe.store.candidates("UNDATED") == []


def test_an_interrupted_scan_resumes_where_it_stopped(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = make_pipeline(tmp_path)
    urls = [f"https://example.test/hypothetical/r{i}" for i in range(3)]
    done = _fake_scan(monkeypatch, pipe, urls, interrupt_on=urls[1])
    with pytest.raises(KeyboardInterrupt):
        pipe.run_scan(window_from=WINDOW[0], window_to=WINDOW[1], as_of=WINDOW[1],
                      max_articles=10)
    run = pipe.store.runs()[-1]
    assert run.status is RunStatus.INTERRUPTED and list(run.checkpoint) == [urls[0]]
    assert any("resume" in w for w in run.warnings)
    done = _fake_scan(monkeypatch, pipe, urls)
    resumed = pipe.run_scan(window_from=date(2020, 1, 1), window_to=date(2020, 1, 2),
                            as_of=date(2020, 1, 2), max_articles=10, resume_run_id=run.run_id)
    assert resumed.window_from == WINDOW[0]  # the ORIGINAL window, not the arguments
    assert done == urls[1:]  # nothing processed twice
    assert resumed.status is RunStatus.SUCCEEDED


def test_a_failed_source_makes_the_run_partial_and_the_page_says_so(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = make_pipeline(tmp_path)
    _fake_scan(monkeypatch, pipe, [], failing_source=True)
    run = pipe.run_scan(window_from=WINDOW[0], window_to=WINDOW[1], as_of=WINDOW[1],
                        max_articles=5)
    assert run.status is RunStatus.PARTIAL  # zero articles, but NOT a quiet week
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="t")
    html = render_dashboard_html(d)
    assert "PARTIAL RUN" in html and "not absent" in html


def test_the_kpis_say_it_in_plain_words_and_the_first_view_carries_no_engine_codes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review of PR #703, P2: "Accessible sources: 4 of 5" (the AUTOMATIC channels; the two
    manual-first ones are named on their own), the blocked channels BY NAME,
    articles analysed full vs partial, Research Now / Watch / Skip, new / upgraded / downgraded /
    challenged; thesis ids, change classes, claim ids and rule codes only behind the audit toggle;
    the article date and the registry's first-detected date shown apart."""
    from bs4 import BeautifulSoup

    pipe = make_pipeline(tmp_path)
    _fake_scan(monkeypatch, pipe, [f"https://example.test/hypothetical/k{i}" for i in range(2)],
               failing_source=True)
    run = pipe.run_scan(window_from=WINDOW[0], window_to=WINDOW[1], as_of=WINDOW[1],
                        max_articles=5)
    cards = write_cards(pipe.store, tmp_path / "out", generated="t")
    d = build_dashboard(pipe.store, run.run_id, cards=cards, generated="t")
    html = render_dashboard_html(d)
    blocked = list(pipe.sources.values())[1].publisher
    auto = [s for s in pipe.sources.values() if s.mode == "automatic"]
    # a manual-first channel's automated access is still checked and SAID (observed 2026-10-11:
    # "Blocked sources: none" printed beside a health block counting the manual-first two blocked)
    access = {r["source_id"]: r["status"] for r in d.source_health["rows"]}
    manual_first = ", ".join(f"{s.publisher} [automated access {access[s.id]}]"
                             for s in pipe.sources.values() if s.mode == "manual_first")
    assert all(s.id in access for s in pipe.sources.values() if s.mode == "manual_first")
    for label, value in (("Accessible sources", f"{len(auto) - 1} of {len(auto)}"),
                         ("Blocked automatic channels", blocked),
                         ("Manual-first sources", manual_first),
                         ("Articles analyzed", "2 full · 0 partial"),
                         ("Research Now / Watch / Skip", None),
                         ("New / upgraded / downgraded / challenged theses", None)):
        assert f"<span>{label}</span>" in html, label
        if value:
            assert f"<span>{label}</span><b>{value}</b>" in html, (label, value)
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select(".aud, .auditbar, script, input"):
        el.decompose()
    first = soup.get_text(" ", strip=True)
    assert "Published 2026-10-02" in first and "first ingested by the registry" in first
    assert "first detected by the registry" not in first
    for code in ("TH-", "novelty_unverified", "WATCH (RESEARCH NOW unmet", "SKIP-", "C-",
                 "F5_", "F7_"):
        assert code not in first, code
    # … and all of it is still there for the audit view and the printed record
    assert all(tid in html for rows in d.categories.values() for tid in
               (r.thesis_id for r in rows))


# --- the dashboard -------------------------------------------------------------------------------

def test_every_category_prints_with_a_count_and_a_long_one_says_showing_x_of_y(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.theme_intelligence import report
    monkeypatch.setattr(report, "DASHBOARD_ROWS_PER_CATEGORY", 2)
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=date(2026, 3, 2))
    nodes = ["ai_infrastructure.memory", "ai_infrastructure.optical_networking",
             "ai_infrastructure.power_grid"]
    for i, node in enumerate(nodes):
        art = Hypo(slug=f"n{i}", publisher="Hypo", published=date(2026, 3, 2),
                   blocks=[("paragraph", f"Shipments rose {20 + i}% in 1Q26.")])
        ingest(pipe, art.doc(), extraction(
            [claim("c1", "b001", f"Shipments rose {20 + i}% in 1Q26", "x", metric="shipments",
                   value=20 + i, value_text=f"{20 + i}%", unit="%", period="1Q26")],
            [hyp("h1", f"Thesis {i}", node=node, mechanism="demand_volume_shift",
                 supporting=["c1"])]), as_of=date(2026, 3, 2))
    assert pipe.run is not None
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    cards = write_cards(pipe.store, tmp_path / "out", generated="t")
    d = build_dashboard(pipe.store, run.run_id, cards=cards, generated="t")
    html = render_dashboard_html(d)
    assert "showing 2 of 3" in html  # a collapse prints its own truncation
    for cat in ("NEW", "UPGRADED", "DOWNGRADED", "CHALLENGED", "UNCHANGED BUT MATERIAL",
                "ARCHIVED"):
        assert f'<div class="cat">{cat} <small>' in html  # always printed, even when empty
    assert d.totals_active.get("RESEARCH NOW", 0) == 0  # zero RESEARCH NOW is a valid answer
    assert html.count('class="row"') == 3  # nothing dropped: the third row is one click below
