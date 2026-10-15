"""The enrichment step's CONDITION and BASIS (operator, 2026-10-15: "how do you know if Atlassian,
Twilio will be hurt or benefited?" — "do both options as one PR").

- THE CONDITION: a proposal rests on one of the card's steps; a step that is not a fact (the
  source's opinion, a forecast, our inference) makes its direction a condition — shown as
  "exposed — would be hurt IF this holds: …", never under "Could be hurt".
- THE BASIS: the model states how the company earns from the exposed line; it is checked against
  the company's OWN latest annual report on or before the as-of — its revenue-source sentences.

The thesis is HYPOTHETICAL; the SEC data is the authentic frozen J.P. Morgan subset; the filing
sentences below are VERBATIM from the real 10-Ks named beside them (read 2026-10-15). The model is
a stand-in returning the real tool's shape.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.test_theme_intelligence_enrichment import LINES, StandIn
from tests.theme_intelligence_support import (
    JPM_AS_OF,
    JPM_DIR,
    FrozenSecHttp,
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    mention,
)
from vinci.theme_intelligence.budget import GuardedClient
from vinci.theme_intelligence.cards import enrichment_lines, proposal_reading, set_card
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.enrich import (
    BASIS_MODELS,
    TOOL,
    check_basis,
    revenue_sources,
    step_labels,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import card_context, write_run_outputs
from vinci.theme_intelligence.schemas import Provenance, RunStatus
from vinci.theme_intelligence.securities import ARCHIVE_DOC, AnnualReport, SecResolver

MEM = "ai_infrastructure.memory"

# --- real filing sentences (verbatim) -----------------------------------------------------------
#: NVIDIA 10-K filed 2025-02-26 (0001045810-25-000023), Revenue Recognition
NVDA_SOURCE = ("We derive our revenue from product sales, including hardware and systems, license "
               "and development arrangements, software licensing, and cloud services.")
#: Twilio 10-K filed 2025-02-26 (0001447669-25-000035)
TWLO_SOURCE = ("Our revenue is primarily derived from usage-based fees, which can lead to "
               "variability in our results of operations and at times create differences between "
               "our forecasts and actual results.")
#: Salesforce 10-K filed 2025-03-05 (0001108524-25-000006), with the section title the text
#: layer glues before it
CRM_SOURCE = ("Sources of Revenues We derive our revenues from two sources: (1) subscription and "
              "support revenues and (2) professional services and other revenues.")
#: ServiceNow 10-K filed 2026-01-29 (0001373715-26-000007): WHO pays, not how
NOW_WHO = "A growing portion of our revenue is generated from sales to government customers."
#: Amazon 10-K filed 2026-02-06 (0001018724-26-000004): a model word outside any revenue-source
#: sentence
AMZN_ASIDE = "Revenue from such arrangements is recognized over the subscription period."


def _report(*sentences: str) -> AnnualReport:
    return AnnualReport("10-K", date(2025, 2, 26), "0000000000-25-000001",
                        "https://www.sec.gov/Archives/edgar/data/1/1/x.htm", " ".join(sentences))


# --- the basis check, on real sentences --------------------------------------------------------

def test_the_basis_is_read_in_the_filings_own_revenue_source_sentence() -> None:
    """POSITIVE: Twilio stated usage-based, and its 10-K's revenue-source sentence says so."""
    status, quote, src, note = check_basis(_report(TWLO_SOURCE), "", "usage_based")
    assert status == "IN_FILING" and quote == (TWLO_SOURCE,)
    assert src == "10-K filed 2025-02-26 (0000000000-25-000001)" and "usage-based" in note


def test_a_basis_the_filing_does_not_name_says_what_it_names() -> None:
    """NEGATIVE: Salesforce stated usage-based; its sentence names subscription and services."""
    status, quote, _src, note = check_basis(_report(CRM_SOURCE), "", "usage_based")
    assert status == "FILING_NAMES_OTHER"
    assert note.startswith("its revenue-source sentences name services, subscription — not "
                           "usage-based")
    # the quote starts at the filing's own words: the glued section title is left out
    assert quote == (CRM_SOURCE.removeprefix("Sources of Revenues "),)


def test_a_sentence_naming_several_ways_says_so() -> None:
    status, _q, _s, note = check_basis(_report(NVDA_SOURCE), "", "product_sales")
    assert status == "IN_FILING"
    assert note == ("its revenue-source sentence names product sales — and also licences and "
                    "maintenance")


def test_only_revenue_source_sentences_are_read() -> None:
    """NEGATIVE: a sentence about who pays, and a model word in any other sentence, prove
    nothing — the whole-filing phrase search this replaces "confirmed" nearly every model."""
    assert revenue_sources(f"{NOW_WHO} {AMZN_ASIDE}") == ()
    status, quote, _s, note = check_basis(_report(NOW_WHO, AMZN_ASIDE), "", "subscription")
    assert status == "NOT_DESCRIBED" and quote == () and "not found is not wrong" in note


def test_a_basis_is_unchecked_when_nothing_can_be_read() -> None:
    assert check_basis(None, "no annual report on file", "subscription")[::3] == (
        "UNCHECKED", "no annual report on file")
    assert check_basis(_report(TWLO_SOURCE), "", "")[0] == "UNCHECKED"  # none stated
    assert check_basis(_report(TWLO_SOURCE), "", "other")[0] == "UNCHECKED"  # nothing to look for


def test_the_tool_asks_for_the_basis() -> None:
    item = TOOL["input_schema"]["properties"]["companies"]["items"]
    assert {"revenue_line", "revenue_model"} <= set(item["required"])
    assert item["properties"]["revenue_model"]["enum"] == [*BASIS_MODELS, "other"]


# --- the annual report, point in time ----------------------------------------------------------

class Filings(FrozenSecHttp):
    """The frozen subset, plus annual-report text by URL (real sentences only). A document that
    is also the frozen cover page (a 10-K the listing check reads) keeps that cover page, with
    the text after it."""

    def __init__(self, docs: dict[str, str]) -> None:
        super().__init__(JPM_DIR)
        self.docs = docs
        self.read: list[str] = []

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        if url not in self.docs:
            return super().get_text(url, ttl_seconds)
        self.read.append(url)
        cover = super().get_text(url, ttl_seconds) if url in self.covers else ""
        return cover + self.docs[url]


NVDA_10K_2025 = ARCHIVE_DOC.format(cik=1045810, acc="000104581025000023", doc="nvda-20250126.htm")
AMZN_10K_2026 = ARCHIVE_DOC.format(cik=1018724, acc="000101872426000004", doc="amzn-20251231.htm")
AMZN_10K_2025 = ARCHIVE_DOC.format(cik=1018724, acc="000101872425000004", doc="amzn-20241231.htm")


def test_the_annual_report_read_is_the_latest_on_or_before_the_as_of(tmp_path: Path) -> None:
    """POSITIVE: Amazon's 10-K filed 2026-02-06 is read as of 2026-02-09. NEGATIVE: as of
    2026-02-05 it was not yet filed — the 2025 one is read, never the later."""
    http = Filings({AMZN_10K_2026: f"<p>{AMZN_ASIDE}</p>", AMZN_10K_2025: "<p>older</p>"})
    r = SecResolver(tmp_path, http=http)  # type: ignore[arg-type]
    late, _ = r.annual_report("0001018724", date(2026, 2, 9))
    early, _ = r.annual_report("0001018724", date(2026, 2, 5))
    assert late is not None and late.filed == date(2026, 2, 6) and late.text.endswith(AMZN_ASIDE)
    assert early is not None and early.filed == date(2025, 2, 7) and early.url == AMZN_10K_2025


# --- the condition, and both through the pipeline ----------------------------------------------

STEPS = [{"step": "industry_shift", "text": "Memory makers ship more HBM as AI servers ramp",
          "provenance": "source_stated", "claim_ids": ["c1"]},
         {"step": "pricing", "text": "HBM contract pricing rises",
          "provenance": "model_inference"}]
ANSWER = {"companies": [
    {"name": "NVIDIA", "ticker": "NVDA", "exchange": "Nasdaq", "direction": "benefit",
     "step_id": "s03.0", "business": "GPU and AI systems maker (semiconductors)",
     "exposure": "More HBM supply lets it ship more AI accelerators.",
     "revenue_line": "data-centre GPUs and systems", "revenue_model": "product_sales"},
    {"name": "Amazon", "ticker": "AMZN", "exchange": "Nasdaq", "direction": "hurt",
     "step_id": "s03.1", "business": "cloud computing and online retail",
     "exposure": "AWS buys memory for its servers; higher HBM prices raise its capex per rack.",
     "revenue_line": "AWS cloud services", "revenue_model": "usage_based"}]}


def _pipe(tmp_path: Path, steps: list[dict[str, Any]] = STEPS) -> tuple[Pipeline, str, Filings]:
    http = Filings({NVDA_10K_2025: f"<p>Revenue Recognition {NVDA_SOURCE}</p>",
                    AMZN_10K_2026: f"<p>{AMZN_ASIDE}</p>"})
    resolver = SecResolver(tmp_path / "sec", http=http)  # type: ignore[arg-type]
    pipe = Pipeline(tmp_path / "ti", sources=load_sources(), taxonomy=load_taxonomy(),
                    client=None, resolver=resolver, review=False)
    pipe.start_run("ingest", as_of=JPM_AS_OF)
    art = Hypo("enrich-basis", "Test Publisher", JPM_AS_OF, [("paragraph", t) for t in LINES])
    x = extraction(
        [claim("c1", "b001", LINES[0].rstrip("."), "Micron HBM revenue up 40%",
               metric="HBM revenue growth", value=40, value_text="40%", unit="%",
               period="the quarter")],
        [hyp("h1", "HBM demand lifts memory makers", node=MEM, mechanism="pricing_cycle",
             supporting=["c1"], step_list=steps,
             affected=[("Micron", "potential_beneficiary"), ("Microsoft", "potentially_harmed")])],
        mentions=[mention("Micron", "b001", "Micron's HBM revenue rose 40%", ticker="MU"),
                  mention("Microsoft", "b002", "Microsoft could see cloud margins squeezed",
                          role="potentially_harmed", direction="negative", ticker="MSFT")])
    ingest(pipe, art.doc(), x, as_of=JPM_AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    model = StandIn(ANSWER)
    pipe.client = GuardedClient(model, pipe.guard)
    run, done = pipe.run_enrich(as_of=JPM_AS_OF)
    assert run.status is RunStatus.SUCCEEDED, done
    return pipe, t.thesis_id, http


def test_each_proposal_records_its_steps_label_and_its_checked_basis(tmp_path: Path) -> None:
    pipe, tid, http = _pipe(tmp_path)
    (es,) = pipe.store.enrichments(tid)
    by = {c.name: c for c in es.candidates}
    nvda, amzn = by["NVIDIA"], by["Amazon"]
    assert nvda.step_label is Provenance.MEASURED_OBSERVATION  # a fact: the claim it cites
    assert amzn.step_label is Provenance.MODEL_INFERENCE  # our own inference
    assert (nvda.revenue_model, nvda.basis_check) == ("product_sales", "IN_FILING")
    assert nvda.basis_quote == (NVDA_SOURCE,)
    assert nvda.basis_source == "10-K filed 2025-02-26 (0001045810-25-000023)"
    # a model word outside a revenue-source sentence proves nothing
    assert (amzn.revenue_model, amzn.basis_check) == ("usage_based", "NOT_DESCRIBED")
    assert NVDA_10K_2025 in http.read and AMZN_10K_2026 in http.read
    # the set records the LLM model, and the call's cost is known (the basis's own variable once
    # shadowed the model's name: the set said "usage_based", the cost UNKNOWN — 2026-10-15)
    assert es.model == StandIn.model
    (call,) = [c for c in pipe.store.llm_calls(es.run_id) if c["purpose"] == "enrich"]
    assert call["cost_usd"] is not None and call["cost_usd"] > 0


def test_a_direction_on_a_step_that_is_not_a_fact_is_shown_as_a_condition(
        tmp_path: Path) -> None:
    """POSITIVE: Amazon rests on our inference — "Exposed", with its IF and the step's words,
    never under "Could be hurt". NEGATIVE: NVIDIA rests on a measured step — "Could benefit"."""
    pipe, tid, _http = _pipe(tmp_path)
    out = Path(write_run_outputs(pipe.store, pipe.store.runs()[-1].run_id,
                                 tmp_path / "out")["dir"])
    page = BeautifulSoup((out / "theses" / f"{tid}.html").read_text(), "html.parser")
    hypo = page.select_one(".expo .hypo")
    assert hypo is not None
    groups = {h.get_text(" ", strip=True): h.find_next_sibling("ul").get_text(" ")
              for h in hypo.select("h4")}
    assert set(groups) == {"Could benefit",
                           "Exposed — the direction holds only if its step does"}
    assert "NVIDIA" in groups["Could benefit"] and "Amazon" not in groups["Could benefit"]
    exposed = groups["Exposed — the direction holds only if its step does"]
    assert "Amazon" in exposed and "would be hurt IF this holds" in exposed
    assert "HBM contract pricing rises" in exposed and "(model inference)" in exposed
    # the basis beside it, the filing's sentence on demand
    assert "basis (the model's): product sales" in groups["Could benefit"]
    filing = hypo.select_one("details.filing")
    assert filing is not None and NVDA_SOURCE in filing.get_text(" ")
    # the card (and so its print) carries the same reading and the filing's own words
    card = (out / "cards" / f"{tid}.html").read_text()
    assert "would be hurt IF this holds" in card and NVDA_SOURCE in card


def test_a_conditional_line_cited_to_a_measurement_is_still_a_condition(
        tmp_path: Path) -> None:
    """A step that says what COULD happen is at most the source's opinion, whatever it cites
    (cards.capped_label): NVIDIA's step cites a measured claim but says "could" — a condition."""
    steps = [{**STEPS[0], "text": "Memory makers could ship more HBM as AI servers ramp"},
             STEPS[1]]
    pipe, tid, _http = _pipe(tmp_path, steps)
    (es,) = pipe.store.enrichments(tid)
    nvda = next(c for c in es.candidates if c.name == "NVIDIA")
    assert nvda.step_label is Provenance.SOURCE_OPINION
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None and step_labels(v.content)["s03.0"] is Provenance.SOURCE_OPINION
    _head, rows = enrichment_lines(es, 1, {}, v.content)
    assert any(r.startswith("NVIDIA (NVDA) — exposed — would benefit IF this holds") for r in rows)


def test_a_set_proposed_before_the_label_was_recorded_reads_it_from_its_card(
        tmp_path: Path) -> None:
    """A stored set (2026-10-14) has no step label: it is read from the card version the set
    rests on — and when that card's step is not the recorded one, it is never guessed."""
    pipe, tid, _http = _pipe(tmp_path)
    (es,) = pipe.store.enrichments(tid)
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    rc = card_context(pipe.store, t, v, generated="test")
    card = set_card(es, rc.history)
    steps = {f"s03.{i}": st.step for i, st in enumerate(card.s03_transmission)} if card else {}
    old = {c.name: c.model_copy(update={"step_label": None}) for c in es.candidates}
    assert proposal_reading(old["NVIDIA"], steps, card)[0] is False  # the card: a fact
    assert proposal_reading(old["Amazon"], steps, card)[0] is True
    moved = old["NVIDIA"].model_copy(update={"evidence": "s03.0: another line"})
    cond, how = proposal_reading(moved, steps, card)
    assert cond and "its support was not recorded" in how
    # a set proposed before the basis was asked for shows no basis line
    head, rows = enrichment_lines(es.model_copy(update={"candidates": tuple(
        c.model_copy(update={"revenue_model": ""}) for c in es.candidates)}), 1, steps, card)
    assert head and not any("basis (the model's)" in r for r in rows)


def test_a_company_the_identity_check_refuses_has_no_filing_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: a registrant the identity check refused (UNRESOLVED, no listing, not a foreign
    filer) may be another company — its filing is never read for the basis. Forced here: the
    resolver's own result for NVIDIA, with its listing refused."""
    from vinci.theme_intelligence.schemas import ResolutionStatus

    real = SecResolver.resolve

    def refused(self: SecResolver, m: Any, **kw: Any) -> Any:
        r = real(self, m, **kw)
        if m.name_as_written != "NVIDIA":
            return r
        return r.model_copy(update={"status": ResolutionStatus.UNRESOLVED, "listings": (),
                                    "note": "identity refused (test)"})

    monkeypatch.setattr(SecResolver, "resolve", refused)
    pipe, tid, http = _pipe(tmp_path)
    (es,) = pipe.store.enrichments(tid)
    nvda = next(c for c in es.candidates if c.name == "NVIDIA")
    assert not nvda.listings and not nvda.foreign_filer
    assert nvda.basis_check == "UNCHECKED" and NVDA_10K_2025 not in http.read


def test_a_card_stored_before_lines_were_capped_is_capped_when_read(tmp_path: Path) -> None:
    """A card stored before conditional lines were capped (cards.capped_conditionals, 2026-10-12)
    can label "Memory makers could ship more HBM" a measured observation: read, it is the
    source's opinion — its proposals stay conditions."""
    pipe, tid, _http = _pipe(tmp_path)
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    s0 = v.content.s03_transmission[0]
    old = v.content.model_copy(update={"s03_transmission": (
        s0.model_copy(update={"text": "Memory makers could ship more HBM",
                              "provenance": Provenance.MEASURED_OBSERVATION}),
        *v.content.s03_transmission[1:])})
    assert step_labels(old)["s03.0"] is Provenance.SOURCE_OPINION


def test_an_annual_report_on_an_older_submissions_page_is_found(tmp_path: Path) -> None:
    """Review of #718: the shared walk stops at the first periodic filing — a 10-Q on the recent
    page; a heavy filer's last 10-K on an older page was then "no annual report"."""
    from vinci.netcache import HttpError
    from vinci.theme_intelligence.securities import SUBMISSIONS, SUBMISSIONS_PAGE

    cik = "0000000001"
    tenk = ARCHIVE_DOC.format(cik=1, acc="000000000125000001", doc="x-10k.htm")

    class Pages:
        def get_json(self, url: str, ttl_seconds: float | None = None) -> Any:
            if url == SUBMISSIONS.format(cik=cik):
                return {"filings": {"recent": {
                    "form": ["10-Q"], "filingDate": ["2025-11-01"],
                    "accessionNumber": ["0000000001-25-000002"], "primaryDocument": ["x-q.htm"]},
                    "files": [{"name": "CIK0000000001-submissions-001.json",
                               "filingFrom": "2024-01-01"}]}}
            if url == SUBMISSIONS_PAGE.format(name="CIK0000000001-submissions-001.json"):
                return {"form": ["10-K"], "filingDate": ["2025-02-26"],
                        "accessionNumber": ["0000000001-25-000001"],
                        "primaryDocument": ["x-10k.htm"]}
            raise HttpError(url)

        def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
            if url == tenk:
                return f"<p>{TWLO_SOURCE}</p>"
            raise HttpError(url)

    r = SecResolver(tmp_path, http=Pages())  # type: ignore[arg-type]
    rep, why = r.annual_report(cik, date(2026, 2, 9))
    assert rep is not None, why
    assert rep.form == "10-K" and rep.filed == date(2025, 2, 26) and rep.text == TWLO_SOURCE
