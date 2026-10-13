"""Six active publishers (operator decisions 2026-10-11 and 2026-10-13): Bank of America and
Nomura RETIRED, Morgan Stanley and Goldman Sachs MANUAL-FIRST.

- exactly six active configurations; BofA and Nomura named retired channels, their adapters gone;
- a registry MIGRATED with historical BofA records — an article, a thesis it contributed to, queue
  and undated rows, health checks — keeps them auditable and never reactivates them: no BofA
  request, health check, queue entry or intake line;
- manual-first channels are health-checked but never discovered;
- new BofA material is refused through every supported route (document, inbox, article URL);
- a fresh installation and the dashboard denominators follow the configuration (six);
- Nomura (2026-10-13: its full reports sit on a client portal with no public sign-up): new
  material refused, and a preview it left in the registry is never requested on the desk.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
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
    fetched,
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
    DocumentRecord,
    HealthStatus,
    RunStatus,
    SourceCoverage,
    SourceHealthCheck,
)

SIX = ["citi_must_c", "jpm_tmt", "ms_research", "trendforce", "semianalysis", "gs_research"]
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


def test_exactly_six_active_channels_and_bank_of_america_and_nomura_retired() -> None:
    srcs = load_sources()
    assert [s.id for s in srcs] == SIX
    assert {s.id: s.mode for s in srcs if s.mode == "manual_first"} == {
        "ms_research": "manual_first", "gs_research": "manual_first"}
    retired = {r.id: r for r in load_retired_sources()}
    assert sorted(retired) == ["bofa_institutional", "nomura_connects"]
    bofa, nomura = retired["bofa_institutional"], retired["nomura_connects"]
    assert bofa.publisher == "Bank of America" and bofa.hosts == ("business.bofa.com",)
    assert nomura.publisher == "Nomura" and nomura.retired == "2026-10-13"
    assert nomura.hosts == ("nomuraconnects.com", "nomuranow.com")  # its site and its portal
    assert "bofa_cards" not in ADAPTERS and "nomura_articles" not in ADAPTERS
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
    # a BofA document the old registry still held for a licence check — never asked about again
    pipe.store.upsert_document(DocumentRecord(
        doc_id="D-0123456789abcdef", sha256="0123456789abcdef" * 4, filename="bofa-note.pdf",
        fmt="pdf", size=1, received_at=datetime(2026, 7, 1, tzinfo=UTC),
        source_id="bofa_institutional", publisher="Bank of America", status="HELD",
        match_basis="licence not stated (historical)"))
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
    assert sorted(asked["health"]) == sorted(SIX)
    assert sorted(asked["discover"]) == sorted(set(SIX) - {"ms_research", "gs_research"})
    assert [c.source_id for c in run.sources] == SIX
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
    # the dashboard: six channels, no BofA anywhere it would ask for something
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="t")
    assert d.source_health["total"] == 6
    assert "Bank of America" not in " ".join(r["publisher"] for r in d.source_health["rows"])
    intake = " ".join(x for k, v in d.intake.items() if isinstance(v, dict)
                      for x in v["items"])
    assert "Bank of America" not in intake and "bofa" not in intake.lower()
    assert len(d.intake["coverage"]["items"]) == 6
    assert any(r["thesis_id"] == tid for r in d.archive)  # still searchable


def test_the_health_summary_ignores_a_retired_channels_rows() -> None:
    rows = [SourceHealthCheck(check_id=f"SH-{sid}", source_id=sid, publisher=sid,
                              checked_at=datetime(2026, 10, 11, tzinfo=UTC), trigger="manual",
                              status=HealthStatus.HEALTHY, reason="ok", next_action="—")
            for sid in [*SIX, "bofa_institutional", "nomura_connects"]]
    s = summary(rows, list(load_sources()))
    assert s["total"] == 6 and s["line"].startswith("Sources healthy: 6/6 ")


def test_new_bofa_material_is_refused_through_every_route(tmp_path: Path,
                                                          capsys: pytest.CaptureFixture[str]
                                                          ) -> None:
    from vinci.theme_intelligence.__main__ import main

    pipe = make_pipeline(tmp_path / "a")
    pipe.start_run("ingest", as_of=AS_OF)
    with pytest.raises(InactiveSourceError, match="Bank of America .* retired on 2026-10-11"):
        ingest_file(pipe, MS_PDF, Declared(source_id="bofa_institutional", llm_permitted=True))
    for url in (BOFA_URL, "https://insights.business.bofa.com/en-us/a-subdomain-page"):
        with pytest.raises(InactiveSourceError, match="host of Bank of America"):
            ingest_file(pipe, MS_PDF, Declared(source_id="ms_research", url=url,
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


def test_a_fresh_installation_reports_six_channels(tmp_path: Path,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    from vinci.theme_intelligence.__main__ import main

    assert main(["--data-dir", str(tmp_path / "ti"), "init"]) == 0
    capsys.readouterr()
    assert main(["--data-dir", str(tmp_path / "ti"), "sources"]) == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert [ln.split()[0] for ln in lines] == SIX


NOMURA_PAGE = "https://www.nomuraconnects.com/focused-thinking-posts/faster-slower-then-steady/"


def test_new_nomura_material_is_refused_by_source_and_by_host(tmp_path: Path) -> None:
    """Retired 2026-10-13: a Nomura document, or any document claiming a Nomura address (its site
    or its client portal), is refused before it is read or stored."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    with pytest.raises(InactiveSourceError, match="Nomura .* retired on 2026-10-13"):
        ingest_file(pipe, MS_PDF, Declared(source_id="nomura_connects", llm_permitted=True))
    for url in (NOMURA_PAGE, "https://go.nomuranow.com/research/japi/publication/1"):
        with pytest.raises(InactiveSourceError, match="host of Nomura"):
            ingest_file(pipe, MS_PDF, Declared(source_id="ms_research", url=url,
                                               llm_permitted=True))
    assert pipe.store.documents() == []


def test_a_preview_nomura_left_in_the_registry_is_never_requested_on_the_desk(
        tmp_path: Path) -> None:
    """The desk's Uploads follows the weekly report's intake: a retired channel's PARTIAL article
    (Nomura's "Faster, Slower, Then Steady" in the real pilot) is history — kept and readable on
    Articles, never asked for. NEGATIVE: an ACTIVE channel's preview is still requested."""
    from vinci.theme_intelligence.desk import _Registry, upload_items
    from vinci.theme_intelligence.schemas import RetrievalState

    pipe = make_pipeline(tmp_path)
    for slug, sid, pub in (("nomura-preview", "nomura_connects", "Nomura"),
                           ("active-preview", "semianalysis", "SemiAnalysis")):
        text = (f"The {pub} page summarises a fuller report it links to; the growth outlook "
                f"slows in 2027 before it steadies, with GDP growth easing to 1.8% next year.")
        art = Hypo(slug=slug, publisher=pub, published=date(2026, 9, 29),
                   blocks=[("paragraph", text)])
        ext = extraction([claim("c1", "b001", text.split(";")[1].strip().rstrip("."),
                                "GDP growth eases to 1.8% in 2027", metric="GDP growth",
                                value=1.8, value_text="1.8%", unit="%", period="2027")],
                         [hyp("h1", "Growth slows before it steadies", node="macro_market",
                              mechanism="market_structure_risk", supporting=["c1"])])
        Extraction.model_validate(ext)
        doc = replace(art.doc(), retrieval_state=RetrievalState.PARTIAL)  # read as a preview
        pipe.start_run("article", as_of=AS_OF)
        pipe.process_document(doc, fetched(doc, state=RetrievalState.PARTIAL),
                              url=doc.canonical_url, source_id=sid, as_of=AS_OF, fixture=ext,
                              publisher_override=pub)
        pipe.finish_run(RunStatus.SUCCEEDED)
    held = {a.publisher: a for a in pipe.store.articles()}
    assert held["Nomura"].source_id == "nomura_connects"  # the history stays
    items = upload_items(_Registry(pipe.store), {}, [])
    assert [u.publisher for u in items if u.kind == "full_report"] == ["SemiAnalysis"]
    assert not [u for u in items if u.source_id == "nomura_connects" or u.publisher == "Nomura"]
    # the rendered desk: the history is listed on Articles, the follow-up says it is not asked for
    from bs4 import BeautifulSoup

    from vinci.theme_intelligence.report import write_run_outputs

    last = max(pipe.store.runs(), key=lambda r: r.started_at)
    out = Path(write_run_outputs(pipe.store, last.run_id, tmp_path / "out")["dir"])
    rows = {tr["data-pub"]: tr for tr in BeautifulSoup((out / "articles.html").read_text(),
                                                       "html.parser").select("#at tr[data-pub]")}
    nomura, active = rows["Nomura"].select("td")[-1], rows["SemiAnalysis"].select("td")[-1]
    assert "Not requested — Nomura retired 13 Oct 2026" in nomura.get_text(" ")
    assert not nomura.select("a[href='uploads.html']")
    assert [a.get_text() for a in active.select("a[href='uploads.html']")] == [
        "Supply the full report"]
