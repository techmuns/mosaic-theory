"""The ENRICHMENT step (enrich.py): the listed companies a thesis's own steps imply, proposed by
the model as EXTERNAL HYPOTHESES, every name checked against the SEC, stored apart from the thesis
and never read by a priority rule.

Offline: the article is HYPOTHETICAL (invented text on the reserved `.test` domain); the SEC data
is the AUTHENTIC frozen subset of the J.P. Morgan fixture; the model is a stand-in that returns an
answer in the REAL tool's shape (`enrich.TOOL`). The real run is in the build record.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import (
    JPM_AS_OF,
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
    mention,
)
from vinci.theme_intelligence import enrich
from vinci.theme_intelligence.budget import GuardedClient
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import Direction, ResolutionStatus, RunStatus

LINES = ("Micron's HBM revenue rose 40% in the quarter as AI servers ramped.",
         "Microsoft could see cloud margins squeezed as memory costs climb.")


class StandIn:
    """A model stand-in: records each request, answers with a fixed tool input."""

    model = "claude-opus-4-8"

    def __init__(self, answer: dict[str, Any]) -> None:
        self.answer = answer
        self.users: list[str] = []
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_kw: Any) -> dict[str, Any]:
        assert tool["name"] == "record_enrichment"
        self.users.append(user)
        self.last_usage = {"input_tokens": 900, "output_tokens": 300}
        return self.answer


def _memory_thesis(tmp_path: Path, *, steps: bool = True) -> tuple[Pipeline, str]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=JPM_AS_OF)
    art = Hypo("enrich", "Test Publisher", JPM_AS_OF, [("paragraph", t) for t in LINES])
    x = extraction(
        [claim("c1", "b001", LINES[0].rstrip("."), "Micron HBM revenue up 40%",
               metric="HBM revenue growth", value=40, value_text="40%", unit="%",
               period="the quarter")],
        [hyp("h1", "HBM demand lifts memory makers", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"], steps=steps,
             affected=[("Micron", "potential_beneficiary"), ("Microsoft", "potentially_harmed")])],
        mentions=[mention("Micron", "b001", "Micron's HBM revenue rose 40%", ticker="MU"),
                  mention("Microsoft", "b002", "Microsoft could see cloud margins squeezed",
                          role="potentially_harmed", direction="negative", ticker="MSFT")])
    ingest(pipe, art.doc(), x, as_of=JPM_AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    return pipe, t.thesis_id


#: the shape the real tool records (enrich.TOOL), with what validation must refuse
ANSWER = {"companies": [
    {"name": "Amazon", "ticker": "AMZN", "exchange": "Nasdaq", "direction": "hurt",
     "step_id": "s03.1", "business": "cloud computing and online retail",
     "exposure": "AWS buys memory for its servers; higher HBM prices raise its capex per rack."},
    {"name": "ASML Holding", "ticker": "ASML", "exchange": "Nasdaq", "direction": "benefit",
     "step_id": "s03.0", "business": "lithography equipment for chip makers (semiconductors)",
     "exposure": "Memory makers expanding capacity buy more of its lithography tools."},
    {"name": "Micron Technology", "ticker": "MU", "exchange": "Nasdaq", "direction": "benefit",
     "step_id": "s03.1", "business": "memory chip maker", "exposure": "Named already."},
    {"name": "Invented Widgets", "ticker": "IWX", "exchange": "NYSE", "direction": "benefit",
     "step_id": "s03.7", "business": "widgets", "exposure": "No such step."},
]}


def _enriched(tmp_path: Path) -> tuple[Pipeline, str, StandIn]:
    pipe, tid = _memory_thesis(tmp_path)
    model = StandIn(ANSWER)
    pipe.client = GuardedClient(model, pipe.guard)
    run, done = pipe.run_enrich(as_of=JPM_AS_OF)
    assert run.status is RunStatus.SUCCEEDED, done
    return pipe, tid, model


def test_enrichment_proposes_through_the_theses_steps_and_checks_every_name(
        tmp_path: Path) -> None:
    """POSITIVE: a proposal resting on one of the card's steps is kept, its name resolved the
    same way as a source-named company — Amazon to AMZN, verified point in time; ASML, a 20-F
    filer, kept as a foreign filer's US line. NEGATIVE: a company the source already names
    (Micron) and a step the card does not hold are set aside, each with why."""
    pipe, tid, model = _enriched(tmp_path)
    (es,) = pipe.store.enrichments(tid)
    by = {c.name: c for c in es.candidates}
    assert set(by) == {"Amazon", "ASML Holding"}
    assert [x.ticker for x in by["Amazon"].listings] == ["AMZN"]
    assert by["Amazon"].direction is Direction.NEGATIVE and by["Amazon"].step_id == "s03.1"
    assert not by["ASML Holding"].listings and by["ASML Holding"].foreign_filer
    assert by["ASML Holding"].resolution_status is ResolutionStatus.UNRESOLVED
    assert any(r.startswith("Micron Technology: the source already names it") for r in es.refused)
    assert any(r.startswith("Invented Widgets: cites s03.7") for r in es.refused)
    # the request carries the thesis's lines, never the article's text
    (user,) = model.users
    assert "[s03.0]" in user and "HBM demand lifts memory makers" in user
    assert "Micron; Microsoft" in user  # what the source names, so it is not proposed again
    assert not any(line in user for line in LINES)


def test_enrichment_is_shown_as_our_hypothesis_never_in_the_source_lists(tmp_path: Path) -> None:
    """The desk boxes the proposals apart ("our hypothesis"), with the SEC-verified ticker or "not
    verified"; the source's own groups and the card's stock-exposure table never hold them."""
    pipe, tid, _model = _enriched(tmp_path)
    out = Path(write_run_outputs(pipe.store, pipe.store.runs()[-1].run_id,
                                 tmp_path / "out")["dir"])
    page = BeautifulSoup((out / "theses" / f"{tid}.html").read_text(), "html.parser")
    hypo = page.select_one(".expo .hypo")
    assert hypo is not None and "our hypothesis" in hypo.get_text(" ")
    text = hypo.get_text(" ")
    assert "Amazon" in text and "AMZN" in text
    assert "ASML — the US line of a foreign filer, not checked point-in-time" in text
    source_side = [ul.get_text(" ") for ul in page.select(".expo > ul.who")]
    assert source_side and not any("Amazon" in x or "ASML" in x for x in source_side)
    card = BeautifulSoup((out / "cards" / f"{tid}.html").read_text(), "html.parser")
    s05 = card.select_one('[data-field="s05_affected"]')
    assert s05 is not None
    subs = s05.select(".sub")
    stock = next(s for s in subs if s.get_text().startswith("Stock exposures"))
    assert "Amazon" not in stock.find_next_sibling().get_text(" ")
    enr = next(s for s in subs if s.get_text().startswith("Enrichment"))
    after = "".join(x.get_text(" ") for x in enr.find_next_siblings())
    # the step it rests on ("pricing moves") is our inference, not a fact: a condition, never
    # a bare "could be hurt" (2026-10-15)
    assert "Amazon (AMZN) — exposed — would be hurt IF this holds: “pricing moves”" in after


def test_enrichment_never_changes_the_thesis_or_its_research_action(tmp_path: Path) -> None:
    """No new thesis version, the same action; no priority module reads the step (source pin).
    A second pass over the same version asks nothing (NEGATIVE: --refresh asks again)."""
    pipe, tid = _memory_thesis(tmp_path)
    before = [(v.version, v.priority.research_action) for v in pipe.store.thesis_versions(tid)]
    model = StandIn(ANSWER)
    pipe.client = GuardedClient(model, pipe.guard)
    pipe.run_enrich(as_of=JPM_AS_OF)
    after = [(v.version, v.priority.research_action) for v in pipe.store.thesis_versions(tid)]
    assert before == after
    root = Path(enrich.__file__).parent
    for mod in ("engine.py", "priority.py"):
        assert "enrich" not in (root / mod).read_text().lower(), mod
    _run, done = pipe.run_enrich(as_of=JPM_AS_OF)
    assert len(model.users) == 1 and "already proposed for version" in done[0][1]
    pipe.run_enrich(as_of=JPM_AS_OF, refresh=True)
    assert len(model.users) == 1  # the same request again: answered from the cache, unpaid
    assert len(pipe.store.enrichments(tid)) == 2


def test_a_thesis_with_no_stated_step_to_earnings_is_not_sent(tmp_path: Path) -> None:
    """Nothing for a company to be exposed THROUGH: no call, and the run says why."""
    pipe, tid = _memory_thesis(tmp_path, steps=False)
    model = StandIn(ANSWER)
    pipe.client = GuardedClient(model, pipe.guard)
    _run, done = pipe.run_enrich(as_of=JPM_AS_OF)
    assert model.users == [] and pipe.store.enrichments(tid) == []
    assert "no stated step to company earnings" in done[0][1]


def test_an_enrichment_set_is_never_edited_and_travels_with_the_registry(tmp_path: Path) -> None:
    """Append-only like every history table (the store's generic pin has no enrichment rows to
    test), and carried by the state branch's export / import."""
    from vinci.theme_intelligence.store import Store

    pipe, tid, _model = _enriched(tmp_path)
    for sql in ("UPDATE enrichments SET thesis_version = 9", "DELETE FROM enrichments"):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            pipe.store.conn.execute(sql)
    counts = pipe.store.export_jsonl(tmp_path / "jsonl")
    assert counts["enrichments"] == 1
    back = Store.import_jsonl(tmp_path / "jsonl", tmp_path / "back.db")
    assert back.enrichments(tid) == pipe.store.enrichments(tid)


class MerckSec:
    """Merck & Co.'s REAL SEC record (ticker map, SIC 2834 Pharmaceutical Preparations, one 10-K)
    — an industry code the identity check can veto against, which the frozen subset lacks."""

    CIK = "0000310158"

    def fetched_at(self, url: str, **_kw: Any) -> float | None:
        return None  # a double records no fetch time

    def get_json(self, url: str, ttl_seconds: float | None = None) -> Any:
        from vinci.netcache import HttpError
        from vinci.theme_intelligence.securities import SUBMISSIONS, TICKERS_EXCHANGE, TICKERS_MF

        if url == TICKERS_EXCHANGE:
            return {"fields": ["cik", "name", "ticker", "exchange"],
                    "data": [[310158, "Merck & Co., Inc.", "MRK", "NYSE"]]}
        if url == TICKERS_MF:
            return {"fields": ["cik", "seriesId", "classId", "symbol"], "data": []}
        if url == SUBMISSIONS.format(cik=self.CIK):
            return {"sic": "2834", "sicDescription": "Pharmaceutical Preparations",
                    "filings": {"recent": {"form": ["10-K"], "filingDate": ["2026-02-25"],
                                           "accessionNumber": [f"{self.CIK}-26-000001"],
                                           "primaryDocument": ["k.htm"]}}, "files": []}
        raise HttpError(f"not in the double: {url}")

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        from tests.theme_intelligence_support import cover_html
        from vinci.netcache import HttpError
        from vinci.theme_intelligence.securities import ARCHIVE_DOC

        if url == ARCHIVE_DOC.format(cik=310158, acc=f"{self.CIK}26000001", doc="k.htm"):
            return cover_html([{"title": "Common Stock", "symbol": "MRK", "exchange": "NYSE"}])
        raise HttpError(f"not in the double: {url}")


def test_the_identity_check_reads_what_the_company_does_never_the_mechanisms_words(
        tmp_path: Path) -> None:
    """The first real pass (2026-10-14) refused Merck & Co.: its exposure sentence spoke of a drug
    "pipeline", which the identity check read as oil and gas against Merck's SIC 2834. The check
    now reads the stated BUSINESS only. POSITIVE: the same proposal resolves to MRK. NEGATIVE: a
    business of another industry (an oil pipeline operator) is still refused identity."""
    from datetime import date

    from vinci.theme_intelligence.securities import SecResolver

    pipe, tid = _memory_thesis(tmp_path)
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    resolver = SecResolver(tmp_path / "sec-merck", http=MerckSec())  # type: ignore[arg-type]

    def propose(business: str) -> Any:
        model = StandIn({"companies": [
            {"name": "Merck & Co.", "ticker": "MRK", "exchange": "NYSE", "direction": "benefit",
             "step_id": "s03.0", "business": business,
             "exposure": "Licensing Chinese assets rebuilds its drug pipeline before a patent "
                         "cliff."}]})
        res = enrich.enrich_thesis(v.content, version=v.version, area="Healthcare", groups=[],
                                   client=model, cache_dir=tmp_path / f"llm-{len(business)}",
                                   resolver=resolver, as_of=date(2026, 10, 14), run_id="R-t")
        assert res.enrichment is not None
        (c,) = res.enrichment.candidates
        return c

    pharma = propose("large-cap pharma, oncology and vaccines leader")
    assert [x.ticker for x in pharma.listings] == ["MRK"]
    pipes = propose("oil pipeline operator")
    assert not pipes.listings and "not the same company" in pipes.resolution_note


def test_the_weekly_scan_ends_with_enrichment_in_its_own_run(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Operator 2026-10-14: enrichment is part of the weekly run. A scan (offline, no new article
    this week) enriches every active thesis whose current version has no set — inside the SCAN's
    run, its call on the scan's bill, so the week's report and desk carry it. NEGATIVE: a scan
    with enrichment off (`scan --no-enrich`) asks nothing."""
    from tests.test_theme_intelligence_scan import _fake_scan

    for on in (True, False):
        pipe, tid = _memory_thesis(tmp_path / str(on))
        pipe.enrich_in_scan = on
        model = StandIn(ANSWER)
        pipe.client = GuardedClient(model, pipe.guard)
        _fake_scan(monkeypatch, pipe, [])
        run = pipe.run_scan(window_from=JPM_AS_OF, window_to=JPM_AS_OF, as_of=JPM_AS_OF,
                            max_articles=5)
        sets = pipe.store.enrichments(tid)
        if on:
            (es,) = sets
            assert run.mode == "scan" and es.run_id == run.run_id
            assert run.counts.get("theses_enriched") == 1
            assert [c["purpose"] for c in pipe.store.llm_calls(run.run_id)] == ["enrich"]
        else:
            assert sets == [] and model.users == [] and "theses_enriched" not in run.counts


def test_the_scan_command_enriches_unless_told_not_to(monkeypatch: pytest.MonkeyPatch,
                                                      tmp_path: Path) -> None:
    """The weekly wrappers call `scan`: the command turns the step on; `--no-enrich` off."""
    from vinci.theme_intelligence import __main__ as cli
    from vinci.theme_intelligence import pipeline as pipeline_mod

    seen: list[bool] = []

    class StopError(Exception):
        pass

    def recorder(*_a: Any, enrich: bool = False, **_k: Any) -> Any:
        seen.append(enrich)
        raise StopError

    monkeypatch.setattr(pipeline_mod, "Pipeline", recorder)
    for argv in (["scan", "--cache-only"], ["scan", "--cache-only", "--no-enrich"]):
        with pytest.raises(StopError):
            cli.main(["--data-dir", str(tmp_path), *argv])
    assert seen == [True, False]
