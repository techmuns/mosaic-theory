"""Open review findings fixed (docs/records/2026-10-14-theme-intelligence-open-review-findings.md):
O1-O7, O13, O14, O19-O21. Each pin fails without its fix; each carries its negative.

HYPOTHETICAL articles (invented text, `.test` domain) through the REAL pipeline, extractions in
the real type; the authentic frozen SEC subset; the corpus checks are in the build record.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
    mention,
)
from vinci.theme_intelligence.parse import parse_document, parse_text_date
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import RunStatus

AS_OF = date(2026, 10, 14)
MEMORY = "ai_infrastructure.memory"
ROOT = Path(__file__).resolve().parents[1]
BODY = "".join(f"<p>Paragraph {i}: DRAM contract prices rose in the quarter as hyperscalers "
               f"kept buying memory for AI servers, and makers held back capacity.</p>"
               for i in range(1, 8))


def _page(inner: str, *, head: str = "") -> str:
    return (f"<html><head><title>Memory note</title>{head}</head><body><main><article>"
            f"<h1>Memory note</h1>{inner}</article></main></body></html>")


# --- O1 / O2 / O3: the page's own date and its whole body ----------------------------------------

def test_a_september_date_written_in_full_is_read() -> None:
    """`raw.replace("Sept", "Sep")` turned "September" into "Sepember": every full September text
    date was UNKNOWN. NEGATIVE pins: "Sept 30" and "Sept. 30" still read."""
    for raw in ("September 30, 2026", "Sept 30, 2026", "Sept. 30, 2026", "Sep 30, 2026"):
        assert parse_text_date(raw) == datetime(2026, 9, 30, tzinfo=UTC), raw
    d = parse_document(_page("<p>Published September 30, 2026</p>" + BODY),
                       "https://dates.test/a", None)
    assert d.published_at == datetime(2026, 9, 30, tzinfo=UTC)
    assert d.published_status.value == "KNOWN"


def test_a_related_articles_date_never_dates_the_page() -> None:
    """With no structured date, the whole page was searched for "Published <date>": a "You may
    also like" card, or a related-articles sidebar, dated the page it sat on. NEGATIVE pin: the
    article's own "Published <date>" line still dates it."""
    card = ('<h2>You may also like</h2><div><a href="/b">Another note</a>'
            "<p>Published Oct 2, 2026</p></div>")
    d = parse_document(_page(BODY + card), "https://dates.test/a", None)
    assert d.published_at is None
    side = ('<aside class="related-articles"><p>Published Oct 2, 2026</p></aside>')
    d = parse_document(_page(BODY + side), "https://dates.test/b", None)
    assert d.published_at is None
    own = parse_document(_page("<p>Published Sep 28, 2026</p>" + BODY + card),
                         "https://dates.test/c", None)
    assert own.published_at == datetime(2026, 9, 28, tzinfo=UTC)


def test_a_body_heading_that_begins_like_related_content_never_cuts_the_article() -> None:
    """The stop-heading pattern matched a PREFIX: "Recommended positioning for 2027" cut the
    article and it stayed FULL. NEGATIVE pins: the real related-content headings (the corpus's
    "You may also like", "Explore more of our thought leadership", "More from <Name>") still
    end the body."""
    for heading in ("Recommended positioning for 2027", "More from the data centre build-out",
                    "Read more into the guidance"):
        paras = BODY.split("</p>")
        mid = "</p>".join(paras[:3]) + f"</p><h2>{heading}</h2>" + "</p>".join(paras[3:])
        d = parse_document(_page(mid), "https://cut.test/a", None)
        assert not [n for n in d.notes if n.startswith("body truncated")], heading
        assert sum(b.text.startswith("Paragraph") for b in d.blocks) == 7, heading
    for heading in ("You may also like", "Explore more of our thought leadership",
                    "More from J.P. Morgan"):
        d = parse_document(_page(BODY + f"<h2>{heading}</h2><p>Paragraph 9: another note's "
                                        f"summary.</p>"), "https://cut.test/b", None)
        assert any(n.startswith("body truncated") for n in d.notes), heading
        assert not any(b.text.startswith("Paragraph 9") for b in d.blocks), heading


# --- O4: a period label is checked as a period ---------------------------------------------------

def _card_issues(pipe: Pipeline) -> list[str]:
    assert pipe.run is not None
    return [i.detail for i in pipe.store.issues(run_id=pipe.run.run_id)
            if i.code == "NUMBER_NOT_IN_CITED_CLAIMS"]


def _fact_line(tmp: Path, fact: str) -> Pipeline:
    src = "DRAM contract prices rose 9% in 3Q26, the survey shows."
    pipe = make_pipeline(tmp)
    pipe.start_run("fixture", as_of=AS_OF)
    art = Hypo("quarters", "Hypo Research Q", date(2026, 10, 1), [("paragraph", src)])
    h = hyp("h1", "DRAM contract prices are rising", node=MEMORY, mechanism="pricing_cycle",
            supporting=["c1"])
    h["bottom_line_fact"] = {"text": fact, "provenance": "source_stated", "claim_ids": ["c1"]}
    ingest(pipe, art.doc(), extraction([claim(
        "c1", "b001", "DRAM contract prices rose 9% in 3Q26", "DRAM prices rose 9% in 3Q26",
        value=9, value_text="9%", unit="%", period="3Q26")], [h]), as_of=AS_OF)
    return pipe


def test_a_quarter_label_never_hides_a_figure_or_a_changed_period(tmp_path: Path) -> None:
    """The quarter-label excuse took any two digits after the label — "In Q3 45% of …" never had
    its 45 checked — and a line "rose 9% in 4Q27" citing only "rose 9% in 3Q26" passed every
    check. NEGATIVE pins: the claim's own quarter, written another way ("Q3 2026"), passes."""
    assert any("'45'" in d for d in _card_issues(_fact_line(
        tmp_path / "a", "In Q3 45% of DRAM contract prices rose 9%.")))
    assert any("period '4Q27'" in d for d in _card_issues(_fact_line(
        tmp_path / "b", "DRAM contract prices rose 9% in 4Q27.")))
    for i, ok in enumerate(("DRAM contract prices rose 9% in 3Q26.",
                            "DRAM contract prices rose 9% in Q3 2026.")):
        assert _card_issues(_fact_line(tmp_path / f"ok{i}", ok)) == [], ok


# --- O5: a level is not a change -----------------------------------------------------------------

def _claim(cid: str, quote: str, value: float) -> Any:
    from vinci.theme_intelligence.schemas import Claim, ClaimKind, Confidence, Epistemic
    return Claim(claim_id=cid, article_id="A-1", article_version_id="AV-1", block_id="b001",
                 char_start=0, char_end=len(quote), quote=quote, statement=quote,
                 kind=ClaimKind.METRIC, epistemic=Epistemic.ACTUAL, period="3Q26", value=value,
                 value_text=str(value), confidence=Confidence.HIGH, span_verified=True,
                 number_verified=True, measure_key=f"k|{cid}", fingerprint=f"f|{cid}",
                 extraction_id="X-1")


def test_a_level_statement_is_never_read_as_a_change() -> None:
    """Open stems ("accelerat\\w*", "surg\\w*", "MoM\\w*") read "AI accelerator revenue was $10bn"
    and "surgical procedure volumes were 1.2m" as CHANGES; two of them corroborated each other
    into a RESEARCH NOW inflection route. NEGATIVE pin: a change in words still is one."""
    from vinci.theme_intelligence.priority import _fundamental_change

    for q in ("AI accelerator revenue was $10bn in 3Q26",
              "surgical procedure volumes were 1.2m in 3Q26",
              "procurement momentum lifted DRAM demand to 40% of shipments",
              "over $150B of contracted spending sits in the backlog"):
        assert not _fundamental_change(_claim("c1", q, 10)), q
    for q in ("DRAM contract prices rose 9% in 3Q26", "AI accelerator shipments grew 40% in 3Q26",
              "demand is increasingly strong, with shipments up 12%",
              "revenue contracted 5% in 3Q26"):
        assert _fundamental_change(_claim("c1", q, 9)), q


# --- O6: one company written two ways ------------------------------------------------------------

def test_one_company_written_two_ways_is_one_exposure(tmp_path: Path) -> None:
    """"Alphabet" and "Alphabet Inc." with one role share a mention id; the second skipped the
    name index, so a hypothesis naming "Alphabet Inc." was refused with a false BLOCK
    (UNSUPPORTED_ENTITY) and dropped off the thesis — and a hypothesis writing a mention another
    way ("Caterpillar (CAT)" for "Caterpillar": 22 such refusals in the local corpus) was too.
    NEGATIVE pin: a name the article never writes is still refused."""
    text = ("Alphabet raised its DRAM purchases 9% in 3Q26; Alphabet Inc. expects to buy more, "
            "and Micron Technology is adding capacity.")
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=AS_OF)
    art = Hypo("alias", "Hypo Research A", date(2026, 10, 1), [("paragraph", text)])
    h = hyp("h1", "Hyperscalers buy more DRAM", node=MEMORY, mechanism="pricing_cycle",
            supporting=["c1"], affected=[("Alphabet Inc.", "potential_beneficiary"),
                                         ("Micron Technology (MU)", "potential_beneficiary"),
                                         ("Contoso", "potential_beneficiary")])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", "Alphabet raised its DRAM purchases 9% in 3Q26",
               "Alphabet DRAM purchases +9%", value=9, value_text="9%", unit="%",
               period="3Q26")], [h],
        mentions=[mention("Alphabet", "b001", "Alphabet raised its DRAM purchases"),
                  mention("Alphabet Inc.", "b001", "Alphabet Inc. expects to buy more"),
                  mention("Micron Technology", "b001", "Micron Technology is adding capacity")]),
        as_of=AS_OF)
    assert pipe.run is not None
    refused = [i.detail for i in pipe.store.issues(run_id=pipe.run.run_id)
               if i.code == "UNSUPPORTED_ENTITY"]
    assert not [d for d in refused if "Alphabet" in d or "Micron" in d]
    assert [d for d in refused if "Contoso" in d]
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    assert sorted(c.name_as_written for c in v.content.s05_affected.companies) == [
        "Alphabet", "Micron Technology"]


# --- O7: a retired thesis carries nothing --------------------------------------------------------

def test_a_claim_only_a_retired_thesis_carried_is_never_counted_as_carried(
        tmp_path: Path) -> None:
    """After a re-analysis, a verified material claim that only the RETIRED thesis linked read as
    "carried", so the coverage check raised no alert (the pilot's re-analysis: a 2-claim alert
    suppressed). NEGATIVE pin: a claim a live thesis links still counts as carried."""
    lines = ["Alzheimer's drug sales could grow 26% in 2026, and diagnostic test volumes rose "
             "18% while infusion center visits rose 12% in 2026."]
    first = extraction(
        [claim("c1", "b001", "Alzheimer's drug sales could grow 26% in 2026", "Sales +26%",
               metric="Alzheimer sales", value=26, value_text="26%", unit="%", period="2026"),
         claim("c2", "b001", "diagnostic test volumes rose 18%", "Test volumes +18%",
               metric="diagnostic test volumes", value=18, value_text="18%", unit="%",
               period="2026"),
         claim("c3", "b001", "infusion center visits rose 12% in 2026", "Infusion visits +12%",
               metric="infusion visits", value=12, value_text="12%", unit="%", period="2026")],
        [hyp("h1", "Alzheimer's drugs open a large market", node="healthcare",
             mechanism="demand_volume_shift", supporting=["c1", "c2", "c3"])])
    again = extraction(first["claims"], [hyp(
        "h1", "Alzheimer's drug innovation opens a large market",
        node="healthcare.pharma_biotech", mechanism="demand_volume_shift", supporting=["c1"])])
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("alz", "Test Publisher", date(2026, 9, 14), [("paragraph", t) for t in lines])
    r = ingest(pipe, art.doc(), first, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert r.article_id is not None
    (old,) = pipe.store.theses()
    run, _res = pipe.run_reanalyse(article_ids=[r.article_id], retire=[old.thesis_id],
                                   reason="test", as_of=AS_OF, fixtures={r.article_id: again})
    ids = {c.metric: c.claim_id for c in pipe.store.claims_for_article(r.article_id)}
    linked = pipe.store.linked_claim_ids(list(ids.values()))
    assert ids["Alzheimer sales"] in linked  # a live thesis carries it
    assert ids["diagnostic test volumes"] not in linked
    assert ids["infusion visits"] not in linked
    alerts = [i.detail for i in pipe.store.issues(run_id=run.run_id)
              if i.code == "MECHANISM_COVERAGE"]
    assert alerts, "the two claims only the retired thesis carried raise a coverage alert"


# --- O13: a retry after a crash ------------------------------------------------------------------

def test_a_retry_after_a_crash_mid_article_keeps_the_records_already_written(
        tmp_path: Path) -> None:
    """A run that died after the engine wrote an article's claims, but before marking it applied,
    re-extracted it under a changed registry context (a different extraction id): the same
    content-addressed claim id with another payload raised StoreIntegrityError on every retry.
    Now the record first written is kept. NEGATIVE pin: the retry completes and the claim is
    stored once."""
    line = "Imaging scanner shipments rose 26% in 2026."

    def x(title: str) -> dict[str, Any]:
        return extraction([claim("c1", "b001", line.rstrip("."), "Imaging shipments rose 26%",
                                 metric="shipments", value=26, value_text="26%", unit="%",
                                 period="2026")],
                          [hyp("h1", title, node="healthcare", mechanism="demand_volume_shift",
                               supporting=["c1"])])
    pipe = make_pipeline(tmp_path)
    art = Hypo("img", "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
    pipe.start_run("ingest", as_of=AS_OF)
    real = pipe.store.add_extraction

    def dies(*_a: Any, **_k: Any) -> None:  # the process dies before the 'applied' marker
        raise KeyboardInterrupt

    pipe.store.add_extraction = dies  # type: ignore[method-assign]
    with pytest.raises(KeyboardInterrupt):
        ingest(pipe, art.doc(), x("Imaging demand rises"), as_of=AS_OF, publisher=art.publisher)
    pipe.store.add_extraction = real  # type: ignore[method-assign]
    pipe.finish_run(RunStatus.INTERRUPTED)
    pipe.start_run("ingest", as_of=AS_OF)
    res = ingest(pipe, art.doc(), x("Imaging scanner demand rises"), as_of=AS_OF,
                 publisher=art.publisher)
    assert res.status == "PROCESSED"
    assert res.article_id is not None and len(pipe.store.claims_for_article(res.article_id)) == 1


# --- O14: enrichment never fails a finished scan -------------------------------------------------

def test_an_api_outage_in_enrichment_is_a_warning_never_the_runs_status(tmp_path: Path) -> None:
    """The post-scan enrichment caught only RuntimeError; the Anthropic SDK's connection and
    status errors are not RuntimeErrors, so an outage there marked a completed weekly scan
    FAILED. NEGATIVE pin: the failure is said, as a run warning."""
    class APIConnectionError(Exception):  # the SDK's shape: an Exception, not a RuntimeError
        pass

    pipe = make_pipeline(tmp_path)
    pipe.start_run("scan", as_of=AS_OF, window_from=AS_OF, window_to=AS_OF)

    def outage(*_a: Any, **_k: Any) -> Any:
        raise APIConnectionError("Connection error.")

    pipe._enrich_theses = outage  # type: ignore[method-assign]  # noqa: SLF001
    pipe._scan_enrichment(AS_OF)  # noqa: SLF001
    assert pipe.run is not None
    assert any("enrichment not run: APIConnectionError" in w for w in pipe.run.warnings)
    assert pipe.finish_run(RunStatus.SUCCEEDED).status is RunStatus.SUCCEEDED


# --- O19 / O20 / O21: the app and the rendered pages ---------------------------------------------

def test_the_app_awaits_a_view_so_its_failure_is_shown() -> None:
    """`return mod.render(...)` inside the router's try returned the promise unawaited, so a
    view's failure skipped the catch: a blank or stale screen, no message."""
    src = (ROOT / "frontend" / "app.js").read_text()
    assert "return await mod.render(root, params, { item, frame });" in src
    assert "return mod.render(" not in src


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_a_page_the_host_does_not_hold_says_so_never_a_blank_screen(tmp_path: Path) -> None:
    """Cloudflare Pages answers a missing file with the app's own index (HTTP 200): the view found
    no desk page and threw, and the router swallowed it. Now a missing desk says "not published",
    and a missing page of a published desk says so with a link home."""
    view = (ROOT / "frontend" / "views" / "intel" / "desk.js").resolve().as_uri()
    js = f"""
globalThis.fetch = async () => ({{ ok: true, status: 200,
  text: async () => '<html><body><main class="main" id="main"></main></body></html>' }});
globalThis.DOMParser = class {{ parseFromString() {{ return {{ querySelector: () => null }}; }} }};
const {{ render }} = await import({json.dumps(view)});
const frame = (_item, o) => o.bodyHtml;
const home = {{ innerHTML: "" }}, page = {{ innerHTML: "" }};
await render(home, [], {{ item: {{}}, frame }});
await render(page, ["themes", "TH-ABC123"], {{ item: {{}}, frame }});
console.log(JSON.stringify([home.innerHTML, page.innerHTML]));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    home, page = json.loads(out.stdout.strip().splitlines()[-1])
    assert "No theme-intelligence run is published yet" in home
    assert "This page is not in the published research" in page and "theses/TH-ABC123" in page


def _one_thesis(tmp: Path, node: str = MEMORY, url: str | None = None) -> tuple[Pipeline, Path]:
    pipe = make_pipeline(tmp)
    run = pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("render", "Hypo Research R", date(2026, 10, 1),
               [("paragraph", "DRAM contract prices rose 9% in 3Q26, the survey shows.")])
    doc = art.doc()
    if url is not None:
        doc.canonical_url = url  # the page's own <link rel="canonical">
    ingest(pipe, doc, extraction([claim(
        "c1", "b001", "DRAM contract prices rose 9% in 3Q26", "DRAM prices rose 9%", value=9,
        value_text="9%", unit="%", period="3Q26")], [hyp(
            "h1", "DRAM contract prices are rising", node=node, mechanism="pricing_cycle",
            supporting=["c1"])]), as_of=AS_OF)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe, Path(write_run_outputs(pipe.store, run.run_id, tmp / "out")["dir"])


def test_a_source_link_is_only_ever_a_web_address(tmp_path: Path) -> None:
    """The card put the article's canonical URL — taken from the page itself — into `href`
    unchecked: a `javascript:` canonical became a clickable link on the app's origin. NEGATIVE
    pin: a web address is still a link."""
    pipe, out = _one_thesis(tmp_path / "js", url="javascript:alert(document.domain)")
    (t,) = pipe.store.theses()
    card = (out / "cards" / f"{t.thesis_id}.html").read_text()
    assert 'href="javascript:' not in card
    pipe2, out2 = _one_thesis(tmp_path / "web")
    (t2,) = pipe2.store.theses()
    soup = BeautifulSoup((out2 / "cards" / f"{t2.thesis_id}.html").read_text(), "html.parser")
    assert any(a["href"].startswith("https://") for a in soup.select("a[href]"))


def test_an_area_link_carries_its_whole_name(tmp_path: Path) -> None:
    """Area names were HTML-escaped but not URL-encoded: "Healthcare · Pharma & biotech" split
    the query at "&" and Themes opened unfiltered. NEGATIVE pin: a name without "&" reads the
    same."""
    from vinci.theme_intelligence.desk import area_name

    _pipe, out = _one_thesis(tmp_path, node="healthcare.pharma_biotech")
    page = BeautifulSoup((out / "index.html").read_text(), "html.parser")
    areas = {parse_qs(urlparse(a["href"]).query)["area"][0]
             for a in page.select('a[href^="themes.html?area="]')}
    assert area_name("healthcare.pharma_biotech") in areas
    assert "&" in area_name("healthcare.pharma_biotech")
