"""Seven active publishers (operator decision 2026-10-11): Bank of America RETIRED, Morgan Stanley
and Goldman Sachs MANUAL-FIRST.

- exactly seven active configurations; BofA a named retired channel, its adapter gone;
- a registry MIGRATED with historical BofA records — an article, a thesis it contributed to, queue
  and undated rows, health checks — keeps them auditable and never reactivates them: no BofA
  request, health check, queue entry or intake line;
- manual-first channels are health-checked but never discovered;
- new BofA material is refused through every supported route (document, inbox, article URL);
- a fresh installation and the dashboard denominators follow the configuration (seven).
"""

from __future__ import annotations

import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

import vinci.theme_intelligence.pipeline as pipeline_mod
from tests.theme_intelligence_support import (
    FIXTURES,
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
)
from vinci.theme_intelligence.config import load_retired_sources, load_sources
from vinci.theme_intelligence.discovery import ADAPTERS, Discovery
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.health import HealthRun, summary
from vinci.theme_intelligence.ingest import InactiveSourceError, ingest_file
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import build_dashboard, card_context
from vinci.theme_intelligence.schemas import (
    HealthStatus,
    RunStatus,
    SourceCoverage,
    SourceHealthCheck,
)

SEVEN = ["citi_must_c", "jpm_tmt", "ms_research", "nomura_connects", "trendforce",
         "semianalysis", "gs_research"]
AS_OF = date(2026, 10, 11)
MS_PDF = FIXTURES / "synthetic_documents" / "ms_report_synthetic.pdf"
BOFA_URL = "https://business.bofa.com/en-us/content/breakthrough-technology/ai-gets-physical.html"


class LiveNetworkError(BaseException):
    """A BaseException on purpose: a broad `except Exception` must not swallow it."""


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def refuse(self: Any, request: Any) -> Any:
        raise LiveNetworkError(f"live network request in an offline test: {request.url}")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


def _stub_scan(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """Discovery and health offline; records which channels each was asked about."""
    asked: dict[str, list[str]] = {"discover": [], "health": []}

    def discover(src: Any, f: Any, store: Any, *, window_from: date,
                 window_to: date) -> Discovery:
        asked["discover"].append(src.id)
        return Discovery(SourceCoverage(source_id=src.id, publisher=src.publisher,
                                        channel=src.channel, method="test", status="OK"), [])

    def health(sources: Any, f: Any, store: Any, *, trigger: str, window_from: date,
               window_to: date, run_id: str | None = None, **_: Any) -> HealthRun:
        rows = []
        for s in sources:
            asked["health"].append(s.id)
            h = SourceHealthCheck(
                check_id=f"SH-t-{run_id}-{s.id}", source_id=s.id, publisher=s.publisher,
                checked_at=datetime.now(tz=UTC), trigger=trigger, run_id=run_id,
                status=HealthStatus.BLOCKED if s.mode == "manual_first" else HealthStatus.HEALTHY,
                reason="test", next_action="—", expect_blocked=s.expect_blocked)
            store.add_health_check(h)
            rows.append(h)
        return HealthRun(checks=rows)

    monkeypatch.setattr(pipeline_mod, "discover_source", discover)
    monkeypatch.setattr(pipeline_mod, "check_sources", health)
    return asked


def test_exactly_seven_active_channels_and_bank_of_america_retired() -> None:
    srcs = load_sources()
    assert [s.id for s in srcs] == SEVEN
    assert {s.id: s.mode for s in srcs if s.mode == "manual_first"} == {
        "ms_research": "manual_first", "gs_research": "manual_first"}
    [bofa] = load_retired_sources()
    assert bofa.id == "bofa_institutional" and bofa.publisher == "Bank of America"
    assert bofa.hosts == ("business.bofa.com",)
    assert "bofa_cards" not in ADAPTERS
    assert all(s.adapter in ADAPTERS for s in srcs)


def _historical_bofa(pipe: Pipeline) -> tuple[str, str]:
    """Records an eight-source registry carried: a BofA article and the thesis it created, a
    QUEUED and an UNDATED BofA candidate, and BofA health checks."""
    text = "Industrial robot orders rose 12% in 2026 as factories automated with AI."
    art = Hypo(slug="historical-bofa", publisher="Bank of America", published=date(2026, 6, 25),
               blocks=[("paragraph", text)])
    ext = extraction([claim("c1", "b001", text.rstrip("."), "Robot orders +12% in 2026",
                            metric="industrial robot orders", value=12, value_text="12%",
                            unit="%", period="2026")],
                     [hyp("h1", "AI pushes factory automation", node="industrials",
                          mechanism="demand_volume_shift", supporting=["c1"])])
    Extraction.model_validate(ext)
    pipe.start_run("article", as_of=date(2026, 7, 1))
    res = ingest(pipe, art.doc(), ext, as_of=date(2026, 7, 1), source_id="bofa_institutional",
                 publisher="Bank of America")
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.store.upsert_candidate(BOFA_URL, "bofa_institutional", "QUEUED",
                                {"source_id": "bofa_institutional", "run_id": "R-old"})
    pipe.store.upsert_candidate(BOFA_URL + "?u", "bofa_institutional", "UNDATED",
                                {"source_id": "bofa_institutional", "title": "Undated BofA page"})
    pipe.store.add_health_check(SourceHealthCheck(
        check_id="SH-old-bofa", source_id="bofa_institutional", publisher="Bank of America",
        checked_at=datetime(2026, 10, 11, 8, 30, tzinfo=UTC), trigger="scan",
        status=HealthStatus.DEGRADED, reason="metadata problem (historical)", next_action="—"))
    [t] = [t for t in pipe.store.theses() if t.key_node == "industrials"]
    return res.article_id or "", t.thesis_id


def test_a_migrated_registry_keeps_bofa_history_and_never_reactivates_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = make_pipeline(tmp_path)
    aid, tid = _historical_bofa(pipe)
    asked = _stub_scan(monkeypatch)
    run = pipe.run_scan(window_from=date(2026, 10, 2), window_to=AS_OF, as_of=AS_OF,
                        max_articles=5)
    # no BofA request, health check or queue processing; manual-first channels: health only
    assert "bofa_institutional" not in asked["discover"] + asked["health"]
    assert sorted(asked["health"]) == sorted(SEVEN)
    assert sorted(asked["discover"]) == sorted(set(SEVEN) - {"ms_research", "gs_research"})
    assert [c.source_id for c in run.sources] == SEVEN
    assert {c.source_id: c.status for c in run.sources}["ms_research"] == "MANUAL_FIRST"
    assert BOFA_URL not in run.checkpoint
    assert pipe.store.candidate(BOFA_URL)[0] == "SOURCE_INACTIVE"  # type: ignore[index]
    # the history is untouched and auditable
    art = pipe.store.article(aid)
    assert art is not None and art.publisher == "Bank of America"
    assert len(pipe.store.thesis_versions(tid)) == 1
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_versions(tid)[-1]
    assert "Bank of America" in str(card_context(pipe.store, t, v, generated="t").__dict__)
    # the dashboard: seven channels, no BofA anywhere it would ask for something
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="t")
    assert d.source_health["total"] == 7
    assert "Bank of America" not in " ".join(r["publisher"] for r in d.source_health["rows"])
    intake = " ".join(x for k, v in d.intake.items() if isinstance(v, dict)
                      for x in v["items"])
    assert "Bank of America" not in intake and "bofa" not in intake.lower()
    assert len(d.intake["coverage"]["items"]) == 7
    assert any(r["thesis_id"] == tid for r in d.archive)  # still searchable


def test_the_health_summary_ignores_a_retired_channels_rows() -> None:
    rows = [SourceHealthCheck(check_id=f"SH-{sid}", source_id=sid, publisher=sid,
                              checked_at=datetime(2026, 10, 11, tzinfo=UTC), trigger="manual",
                              status=HealthStatus.HEALTHY, reason="ok", next_action="—")
            for sid in [*SEVEN, "bofa_institutional"]]
    s = summary(rows, list(load_sources()))
    assert s["total"] == 7 and s["line"].startswith("Sources healthy: 7/7 ")


def test_new_bofa_material_is_refused_through_every_route(tmp_path: Path,
                                                          capsys: pytest.CaptureFixture[str]
                                                          ) -> None:
    from vinci.theme_intelligence.__main__ import main

    pipe = make_pipeline(tmp_path / "a")
    pipe.start_run("ingest", as_of=AS_OF)
    with pytest.raises(InactiveSourceError, match="Bank of America .* retired on 2026-10-11"):
        ingest_file(pipe, MS_PDF, Declared(source_id="bofa_institutional", llm_permitted=True))
    with pytest.raises(InactiveSourceError, match="host of Bank of America"):
        ingest_file(pipe, MS_PDF, Declared(source_id="ms_research", url=BOFA_URL,
                                           llm_permitted=True))
    with pytest.raises(InactiveSourceError, match="not an active channel"):
        ingest_file(pipe, MS_PDF, Declared(source_id="some_other_bank", llm_permitted=True))
    assert pipe.store.documents() == []  # nothing stored, nothing recorded
    data = tmp_path / "cli"
    assert main(["--data-dir", str(data), "article", "--url", BOFA_URL, "--as-of",
                 AS_OF.isoformat(), "--cache-only"]) == 1
    assert "refused: Bank of America was retired" in capsys.readouterr().out
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    shutil.copyfile(MS_PDF, inbox / "bofa.pdf")
    (inbox / "bofa.pdf.meta.json").write_text('{"source": "bofa_institutional"}')
    main(["--data-dir", str(data), "ingest-inbox", "--inbox", str(inbox), "--as-of",
          AS_OF.isoformat(), "--cache-only"])
    assert (inbox / "rejected" / "bofa.pdf").exists()


def test_a_fresh_installation_reports_seven_channels(tmp_path: Path,
                                                     capsys: pytest.CaptureFixture[str]) -> None:
    from vinci.theme_intelligence.__main__ import main

    assert main(["--data-dir", str(tmp_path / "ti"), "init"]) == 0
    capsys.readouterr()
    assert main(["--data-dir", str(tmp_path / "ti"), "sources"]) == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert [ln.split()[0] for ln in lines] == SEVEN
