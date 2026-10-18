"""Batch A of the verified review leads (`docs/records/2026-10-14-theme-intelligence-unverified-
leads-verified.md`) — what the product does wrong, in companies, publishers, operations and replay:

- U11 a company proposed for a thesis was refused as "already named" because its name STARTS like
  one the source names ("Meta" / "Meta Materials");
- U60a the desk's own name rule split "AT&T" into "at", "t" (hiding "AT"), and a name with no ASCII
  letters hid every later name;
- U51 only Citi's house names were excused, so "(J.P. Morgan, Oct 2)" was an unrecorded
  organisation;
- U31a a channel going ERROR → DEGRADED alerted "RECOVERED"; U31c the weekly runner exited 2 for a
  PARTIAL scan whose QA failed (its header says 1); U31d a JPM listing with no card fell back to the
  sitemap and blamed "no dates";
- U37 an unpriced paid call printed "$0, every model answer from the cache";
- U57 the run's spend limit was set after the run started, and a CLI failure kept no traceback;
- U33 a replay read the operator's same-as / duplicate / new decision back out of a sentence, and
  a card finding attaches by its message text.

Articles and pages are HYPOTHETICAL and labelled; records are the REAL types.
"""

from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.test_theme_intelligence_enrichment import StandIn
from tests.test_theme_intelligence_enrichment import _memory_thesis as _thesis
from tests.test_theme_intelligence_group5 import SKIP_LINE, _skip_x
from tests.test_theme_intelligence_source_health import (
    Web,
    article,
    check,
    fetcher,
    healthy_web,
    src,
)
from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import enrich, state
from vinci.theme_intelligence.config import load_sources
from vinci.theme_intelligence.desk import exposure_html
from vinci.theme_intelligence.discovery import jpm_tmt
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.ingest import (
    SAID_DUPLICATE,
    SAID_NEW,
    SAID_SAME_AS,
    ingest_file,
    operator_decision,
)
from vinci.theme_intelligence.schemas import (
    AffectedCompany,
    AffectedView,
    Direction,
    HealthStatus,
    Listing,
    MentionRole,
    RecommendationStatus,
    ResolutionStatus,
    RunStatus,
    SecurityResolution,
    SourceCoverage,
)
from vinci.theme_intelligence.verify import distinct_listings, same_company

AS_OF = date(2026, 10, 16)
REPO = Path(__file__).resolve().parents[1]


# --- U11: a name that starts like a named company, and the SEC verifies apart -----------------

class Sec:
    """A resolver double: verifies the tickers it knows (ticker -> registrant), refuses the rest."""

    def __init__(self, known: dict[str, str]) -> None:
        self.known = known

    def resolve(self, m: Any, *, as_of: date) -> SecurityResolution:
        reg = self.known.get(m.ticker_hint or "")
        return SecurityResolution(
            resolution_id="SR-test", normalized_name=m.normalized_name,
            status=ResolutionStatus.LISTED_EQUITY if reg else ResolutionStatus.UNRESOLVED,
            listings=(Listing(ticker=m.ticker_hint, exchange="NYSE"),) if reg else (),
            cik="0000000001" if reg else None, registrant=reg, method="test double",
            source_ref="test double", resolved_at=datetime.now(tz=UTC))

    def is_foreign_private_issuer(self, cik: str, *, as_of: date) -> bool:
        return False


def _row(name: str, ticker: str, direction: str = "benefit", step: str = "s03.0") -> dict[str, Any]:
    return {"name": name, "ticker": ticker, "exchange": "NYSE", "direction": direction,
            "step_id": step, "business": "an invented business for this test",
            "exposure": "[HYPOTHETICAL] the thesis's step reaches its earnings."}


def _enrich(tmp_path: Path, rows: list[dict[str, Any]], known: dict[str, str]) -> Any:
    pipe, tid = _thesis(tmp_path)
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    res = enrich.enrich_thesis(v.content, version=v.version, area="Technology", groups=[],
                               client=StandIn({"companies": rows}), cache_dir=tmp_path / "llm",
                               resolver=Sec(known),  # type: ignore[arg-type]
                               as_of=AS_OF, run_id="R-test")
    assert res.enrichment is not None
    return res.enrichment


def test_a_company_named_like_one_the_source_names_but_verified_apart_is_proposed(
        tmp_path: Path) -> None:
    """The source names Micron (MU, verified). "Micron Widgets" with a ticker the SEC verifies as
    another company is a proposal; main refused it as "the source already names it"."""
    es = _enrich(tmp_path, [_row("Micron Widgets", "MWX")], {"MWX": "Micron Widgets, Inc."})
    (c,) = es.candidates
    assert c.name == "Micron Widgets" and [x.ticker for x in c.listings] == ["MWX"]
    assert "named like Micron" in c.resolution_note


@pytest.mark.parametrize(("rows", "known", "refused"), [
    # NEGATIVE: the same company — the SEC verifies the named company's own ticker
    ([_row("Micron Technology", "MU")], {"MU": "Micron Technology, Inc."},
     "Micron Technology: the source already names it — set aside"),
    # NEGATIVE: a ticker the SEC does not verify proves nothing (the pilot's second "Rockwell"
    # carried DDAIF) — the names decide
    ([_row("Micron Gadgets", "ZZZZ")], {},
     "Micron Gadgets: the source already names it — set aside"),
    # NEGATIVE: one company proposed twice under two spellings, one verified listing
    ([_row("Invented Holdings", "IVH"), _row("Invented", "IVH")], {"IVH": "Invented Holdings"},
     "Invented: proposed twice — set aside"),
])
def test_a_company_the_sec_does_not_verify_apart_is_still_one_company(
        tmp_path: Path, rows: list[dict[str, Any]], known: dict[str, str], refused: str) -> None:
    es = _enrich(tmp_path, rows, known)
    assert refused in es.refused
    assert all(c.name != refused.split(":")[0] for c in es.candidates)


# --- U60a: one name rule for the enrichment and the desk -----------------------------------------

@pytest.mark.parametrize(("a", "b", "same"), [
    ("Micron", "Micron Technology Inc", True), ("The AES Corporation", "AES", True),
    ("Siemens AG", "Siemens", True), ("Zhipu Z.ai", "Zhipu (Z.ai)", True),
    ("Rockwell", "Rockwell Automation", True),
    ("AT&T", "AT", False),  # main's desk: "at", "t" — hid "AT"
    ("株式会社", "Toyota", False),  # main's desk: a name with no ASCII letters hid every name
    ("Siemens AG", "Siemens Energy", False),  # a legal form only ever EQUALS two names
])
def test_one_company_spelt_two_ways_and_two_companies(a: str, b: str, same: bool) -> None:
    assert same_company(a, b) is same and same_company(b, a) is same


def _co(name: str, *tickers: str) -> AffectedCompany:
    return AffectedCompany(
        mention_id=f"M-{name}", name_as_written=name,
        resolution_status=(ResolutionStatus.LISTED_EQUITY if tickers
                           else ResolutionStatus.UNRESOLVED),
        listings=tuple(Listing(ticker=t, exchange="NYSE") for t in tickers), cik=None,
        role=MentionRole.POTENTIAL_BENEFICIARY, role_detail="", direction=Direction.POSITIVE,
        recommendation_status=RecommendationStatus.NOT_A_RECOMMENDATION, article_id="A-test",
        quote="[HYPOTHETICAL]")


@pytest.mark.parametrize(("cos", "listed"), [
    ([_co("The AES Corporation"), _co("AES")], ["The AES Corporation"]),
    ([_co("Zhipu Z.ai"), _co("Zhipu (Z.ai)")], ["Zhipu Z.ai"]),
    ([_co("AT&T"), _co("AT")], ["AT&T", "AT"]),  # main: "AT" hidden
    ([_co("株式会社"), _co("Toyota")], ["株式会社", "Toyota"]),  # main: "Toyota" hidden
    ([_co("Siemens AG"), _co("Siemens Energy")], ["Siemens AG", "Siemens Energy"]),  # 19 stored
    ([_co("Meta", "META"), _co("Meta Materials", "MMAT")], ["Meta", "Meta Materials"]),
])
def test_the_desk_lists_each_company_once_and_never_hides_another(
        cos: list[AffectedCompany], listed: list[str]) -> None:
    av = AffectedView(companies=tuple(cos), instruments=(), sectors=(), baskets=(),
                      private_or_unlisted=())
    shown = re.findall(r"<li><b>(.*?)</b>", exposure_html(av, [], 0))
    assert [html.unescape(x) for x in shown] == listed


def test_verified_listings_tell_two_companies_apart_only_when_both_are_verified() -> None:
    meta, mmat = (Listing(ticker="META", exchange="Nasdaq"),), (Listing(ticker="MMAT",
                                                                        exchange="Nasdaq"),)
    assert distinct_listings(meta, mmat)
    assert not distinct_listings(meta, meta) and not distinct_listings(meta, ())


# --- U51: a research house the text cites is a source ---------------------------------------------

def test_a_cited_research_house_is_a_source_and_another_organisation_is_still_said(
        tmp_path: Path) -> None:
    line = ("[HYPOTHETICAL] Memory contract prices rose 9% in Q3 2026 (J.P. Morgan, Oct 2), and "
            "the invented maker agreed (Acme Widgets, Oct 3), as did lenders such as Goldman "
            "Sachs and Test Publisher Research.")
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("cited-houses", "Test Publisher", date(2026, 10, 5), [("paragraph", line)])
    x = extraction([claim("c1", "b001", "Memory contract prices rose 9% in Q3 2026",
                          "Memory prices +9%", metric="memory price", value=9, value_text="9%",
                          unit="%", period="Q3 2026")],
                   [hyp("h1", "Memory prices climb", node="ai_infrastructure.memory",
                        mechanism="pricing_cycle", supporting=["c1"])])
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    said = [i.detail for i in pipe.store.issues() if i.code == "NAMED_NOT_RECORDED"]
    assert any(d.startswith("Acme Widgets") for d in said)  # NEGATIVE: still said
    assert any(d.startswith("Goldman Sachs") for d in said)  # NEGATIVE: a publisher in a LIST
    assert not any("J.P. Morgan" in d for d in said), said  # main: an unrecorded organisation
    assert not any("Test Publisher" in d for d in said), said  # the article's own house name


# --- U31a / U31d: health alerts, a listing with no card -----------------------------------------

def test_error_then_degraded_is_a_changed_failure_and_only_healthy_is_recovered(
        tmp_path: Path) -> None:
    from vinci.theme_intelligence.store import Store

    store = Store(tmp_path / "registry.db")
    s = src()
    web = healthy_web(s)
    f = fetcher(tmp_path, web)
    assert check(store, f, [s]).checks[0].status is HealthStatus.HEALTHY
    web.pages[s.entry_url] = httpx.ConnectTimeout("timed out (test)")
    h = check(store, f, [s], now=datetime(2026, 10, 12, 6, tzinfo=UTC)).checks[0]
    assert h.status is HealthStatus.ERROR
    host = s.entry_url.split("/")[2]
    web.pages[s.entry_url] = healthy_web(s).pages[s.entry_url]
    for slug, title in (("memory-prices", "Memory prices keep rising"),
                        ("grid-queues", "Grid queues lengthen")):
        web.pages[f"https://{host}/articles/{slug}"] = (200, article(title, paywall=True))
    h = check(store, fetcher(tmp_path / "3", web), [s],  # a fresh page cache each check
              now=datetime(2026, 10, 13, 6, tzinfo=UTC)).checks[0]
    assert h.status is HealthStatus.DEGRADED and h.alert != "RECOVERED"  # main: RECOVERED
    web.pages.update(healthy_web(s).pages)
    h = check(store, fetcher(tmp_path / "4", web), [s],
              now=datetime(2026, 10, 14, 6, tzinfo=UTC)).checks[0]
    assert h.status is HealthStatus.HEALTHY and h.alert == "RECOVERED"  # POSITIVE


def _jpm(tmp_path: Path, page: str) -> tuple[Any, Any, SourceCoverage]:
    s = replace(next(x for x in load_sources() if x.id == "jpm_tmt"), min_crawl_delay_s=0.0)
    host = s.entry_url.split("/")[2]
    web = Web({f"https://{host}/robots.txt": (404, ""), s.entry_url: (200, page),
               str(s.sitemap_url): (200, '<?xml version="1.0"?><urlset xmlns="http://www.'
                                         'sitemaps.org/schemas/sitemap/0.9"><url><loc>'
                                         f'{s.entry_url}/a-sitemap-only-note</loc></url>'
                                         '</urlset>')})
    cov = SourceCoverage(source_id=s.id, publisher=s.publisher, channel=s.channel, method="test")
    return s, fetcher(tmp_path, web), cov


def test_a_listing_with_no_card_is_a_layout_change_never_a_sitemap_fallback(
        tmp_path: Path) -> None:
    s, f, cov = _jpm(tmp_path, "<html><body><main><p>[HYPOTHETICAL] no cards</p></main></body>"
                               "</html>")
    with pytest.raises(RuntimeError, match="no article card"):  # main: 1 sitemap URL, "no dates"
        jpm_tmt(s, f, cov)


def test_undated_cards_still_fall_back_to_the_sitemap(tmp_path: Path) -> None:
    """NEGATIVE: the fallback's stated purpose — cards that carry no date — is unchanged."""
    base = "/apac/en/insights/markets-and-investing/tmt"
    page = (f'<html><body><main><div class="card"><a href="{base}/an-undated-card">An undated '
            f'card</a></div></main></body></html>')
    s, f, cov = _jpm(tmp_path, page)
    urls = [c.url for c in jpm_tmt(s, f, cov)]
    assert any(u.endswith("/a-sitemap-only-note") for u in urls)
    assert "listing cards carried no dates — falling back to the sitemap" in cov.warnings


# --- U31c: the weekly runner's exit status --------------------------------------------------------

@pytest.mark.parametrize(("scan", "qa", "want"), [(2, 1, 1), (0, 1, 1), (2, 0, 2), (0, 0, 0),
                                                  (1, 0, 1)])
def test_the_weekly_runner_exits_as_its_header_says(tmp_path: Path, scan: int, qa: int,
                                                    want: int) -> None:
    """0 SUCCEEDED · 2 PARTIAL · 1 FAILED or QA did not pass (main: a PARTIAL scan whose QA failed
    exited 2). The script runs in a scratch repository with a stand-in for python."""
    repo = tmp_path / "repo"
    (repo / "bin").mkdir(parents=True)
    shutil.copy(REPO / "bin" / "theme-intelligence-weekly", repo / "bin")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    fake = tmp_path / "fake-python"
    fake.write_text('#!/usr/bin/env bash\ncase "$3" in scan) exit "$SCAN_EXIT";; qa) exit '
                    '"$QA_EXIT";; *) exit 0;; esac\n')
    fake.chmod(0o755)
    out = subprocess.run(["bash", str(repo / "bin" / "theme-intelligence-weekly")], cwd=repo,
                         env={**os.environ, "PY": str(fake), "SCAN_EXIT": str(scan),
                              "QA_EXIT": str(qa)}, capture_output=True, text=True)
    assert out.returncode == want, out.stderr


# --- U37: an unpriced paid call is UNKNOWN, never $0 ----------------------------------------------

class NoUsage(StandIn):
    """A priced model that reports no usage: its answer is a paid call with no cost."""

    def __init__(self) -> None:
        super().__init__({})

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_kw: Any) -> dict[str, Any]:
        self.last_usage = None
        if tool["name"] == "record_article_evidence":
            return _skip_x()
        return {"figure_reviews": [], "block_reviews": [], "added_claims": [],
                "added_mentions": [], "hypothesis_additions": [], "added_hypotheses": [],
                "added_risks": [], "verdicts": []}


def test_a_replay_that_paid_an_unpriced_call_says_its_cost_is_unknown(tmp_path: Path) -> None:
    note = tmp_path / "note.txt"
    filler = ("[HYPOTHETICAL] An invented paragraph standing in for the body of an uploaded "
              "note, long enough to be read as text by the document reader. ") * 3
    note.write_text(f"{SKIP_LINE}\n\n{filler}\n\n{filler}\n")
    laptop = make_pipeline(tmp_path / "laptop")
    laptop.start_run("ingest", as_of=AS_OF)
    ingest_file(laptop, note, Declared(source_id="ms_research", llm_permitted=True), as_of=AS_OF,
                fixture=_skip_x())
    laptop.finish_ingest(RunStatus.SUCCEEDED)
    docs = laptop.store.documents()
    runs = {r.run_id: r for r in laptop.store.runs()}

    def fresh() -> Any:
        p = make_pipeline(tmp_path / "pulled")
        p.client = NoUsage()  # no fixture, no cache: the replay asks the model again
        return p

    lines, _ = state._replay(laptop.paths, docs, runs, fresh, {})
    head = next(ln for ln in lines if ln.startswith("replay run"))
    assert "cost is UNKNOWN" in head and "$0" not in head  # main: "every model answer … $0"


def test_a_carried_run_counts_its_unpriced_calls_apart(tmp_path: Path) -> None:
    run = make_pipeline(tmp_path / "a").start_run("scan", as_of=AS_OF)
    rows = [("LC-1", "extract", {"cost_usd": 0.25, "cached": False}),
            ("LC-2", "review", {"cost_usd": None, "cached": False}),
            ("LC-3", "extract", {"cost_usd": None, "cached": True})]
    lines = state._carry(make_pipeline(tmp_path / "b").store, [(run, rows)], set())
    assert lines[1].endswith("2 paid call(s), $0.2500 + 1 UNPRICED (cost UNKNOWN)")


# --- U57: the spend limit at the run's start; a CLI failure keeps its traceback -----------------

def test_a_runs_budget_is_set_as_it_starts(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("enrich", as_of=AS_OF, budget=0.5)
    assert pipe.guard.run_limit == 0.5
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.start_run("enrich", as_of=AS_OF)
    assert pipe.guard.run_limit != 0.5  # NEGATIVE: none stated, the mode's default


def test_a_cli_ingest_that_fails_records_its_traceback(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.theme_intelligence import __main__ as cli
    from vinci.theme_intelligence import ingest as ingest_mod

    def boom(*_a: Any, **_k: Any) -> Any:
        raise ValueError("an unexpected failure (test)")

    monkeypatch.setattr(ingest_mod, "ingest_file", boom)  # the CLI imports it when it runs
    note = tmp_path / "note.txt"
    note.write_text("[HYPOTHETICAL] text")
    data = tmp_path / "ti"
    assert cli.main(["--data-dir", str(data), "init"]) == 0
    assert cli.main(["--data-dir", str(data), "ingest-file", "--path", str(note), "--source",
                     "ms_research"]) == 1
    from vinci.theme_intelligence.config import Paths
    from vinci.theme_intelligence.store import Store

    (run,) = Store(Paths(data).db).runs()
    err = "\n".join(run.warnings)
    assert "ValueError: an unexpected failure (test)" in err and "Traceback" in err


# --- U33: the operator's decision is a stored value -----------------------------------------------

def _two_uploads(tmp_path: Path) -> tuple[Any, Path]:
    from tests.test_theme_intelligence_ingestion import MS_PDF, _ms, _ms_extraction

    pipe = make_pipeline(tmp_path / "laptop")
    pipe.start_run("ingest", as_of=AS_OF)
    first = ingest_file(pipe, MS_PDF, _ms(), as_of=AS_OF, fixture=_ms_extraction())
    assert first.status == "INGESTED", first.note
    return pipe, first.article_id


def test_an_operator_decision_is_stored_as_a_value_and_survives_a_reworded_sentence(
        tmp_path: Path) -> None:
    from tests.test_theme_intelligence_ingestion import MS_HTML, _ms, _ms_extraction

    pipe, aid = _two_uploads(tmp_path)
    second = ingest_file(pipe, MS_HTML, _ms(), as_of=AS_OF, same_as=aid,
                         fixture=_ms_extraction())
    rec = next(d for d in pipe.store.documents() if d.doc_id == second.doc_id)
    assert (rec.decision, rec.decision_article) == ("same_as", aid)
    reworded = rec.model_copy(update={"match_basis": "the operator said: same article as " + aid})
    assert operator_decision(reworded) == ("same_as", aid)  # main read the sentence: none


@pytest.mark.parametrize(("basis", "want"), [
    (f"{SAID_SAME_AS}A-0123456789ab", ("same_as", "A-0123456789ab")),
    (f"{SAID_DUPLICATE}A-0123456789ab", ("duplicate_of", "A-0123456789ab")),
    (SAID_NEW, ("new", None)),
    ("no article of this publisher resembles it", (None, None)),  # NEGATIVE: the engine's match
])
def test_a_record_from_before_the_field_is_read_by_the_one_sentence_its_writer_shares(
        tmp_path: Path, basis: str, want: tuple[str | None, str | None]) -> None:
    pipe, _aid = _two_uploads(tmp_path)
    (rec,) = pipe.store.documents()
    legacy = rec.model_copy(update={"match_basis": basis, "decision": None,
                                    "decision_article": None})
    assert operator_decision(legacy) == want


def test_a_card_finding_of_every_producer_attaches_to_its_line(tmp_path: Path) -> None:
    """Findings attach by their message text (`line_findings`), written by six producers in three
    shapes — a reworded producer detaches its findings silently. Each producer, through its own
    code, attaches to the line it names."""
    from tests.test_theme_intelligence_review_carry import FakeReviewer
    from vinci.theme_intelligence.report import line_findings
    from vinci.theme_intelligence.verify import (
        _SOURCE_VALUES,
        card_sentences,
        deterministic_card_checks,
        review_card,
    )

    pipe, tid = _thesis(tmp_path)
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    claims = {c.claim_id: c for a in pipe.store.articles()
              for c in pipe.store.claims_for_article(a.article_id)}
    sents = card_sentences(v.content)
    src_sids = [s for s, (_t, p, c) in sents.items() if c and p in _SOURCE_VALUES]
    model_sids = [s for s, (_t, p, _c) in sents.items() if p == "MODEL INFERENCE"]
    assert len(src_sids) >= 2 and model_sids
    partial, unsupported = src_sids[0], src_sids[1]
    reviewer = FakeReviewer({partial: "the cited span is narrower (test)"})
    real = reviewer.extract

    def answer(**kw: Any) -> dict[str, Any]:
        out = real(**kw)
        for x in out["verdicts"]:
            if x["sentence_id"] in (unsupported, model_sids[0]):
                x["verdict"], x["problem"] = "UNSUPPORTED", "no span says so (test)"
        return out

    reviewer.extract = answer  # type: ignore[method-assign]
    issues = review_card(v.content, claims, client=reviewer, cache_dir=tmp_path / "llm",
                         run_id=v.run_id).issues
    with pipe.store.tx():
        for i in issues:
            pipe.store.add_issue(i)
    withheld, flagged, _corrected, _carried = line_findings(pipe.store, tid, v)
    assert {i.code for i in issues} >= {"REVIEW_PARTIAL", "REVIEW_UNSUPPORTED",
                                         "REVIEW_INFERENCE_UNSUPPORTED"}
    assert flagged[partial] == "the cited span is narrower (test)"
    assert flagged[model_sids[0]] == "no span says so (test)"
    assert "REVIEW_UNSUPPORTED" in withheld[unsupported]
    # the deterministic checks: a source line whose claims are gone (FACT_WITHOUT_CLAIM) — on
    # the PARTIAL line, the one line no blocking review finding holds
    det = [i for i in deterministic_card_checks(v.content, {}, v.run_id)
           if i.ref_id.endswith(f":{partial}")]
    assert [i.code for i in det] == ["FACT_WITHOUT_CLAIM"]
    with pipe.store.tx():
        pipe.store.add_issue(det[0])
    withheld, _f, _c, _r = line_findings(pipe.store, tid, v)
    assert withheld[partial].startswith("FACT_WITHOUT_CLAIM")
