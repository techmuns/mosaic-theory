"""Seven verified review leads that fail a run or write a wrong fact
(`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`, group 1):

- U8: a re-keyed thesis at a retired key's salted id — every later bare-key article failed with
  StoreIntegrityError.
- U1: a second hypothesis of one article version reaching the same thesis by another route was
  dropped as ALREADY_INGESTED — its claims linked to nothing, with no warning.
- U2: a thesis archived while held for review came back ACTIVE — its identity hold gone for good.
- U38: an undated document took the run's as-of as its publication date — an old report read as
  current, and reset a thesis's stale clock.
- U18: "supply will fall short" against "demand will rise" was a CONTRADICTION — the same reading.
- U14: on a pulled registry (no article text), a retitled copy of a held report was analysed, and
  paid for, a second time.
- U31e: an empty SEC_USER_AGENT (an unset GitHub secret) broke the package at import.

Articles are HYPOTHETICAL (`.test` domain) or the synthetic MS fixture; SEC data is the frozen
J.P. Morgan subset; no model is called.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_ingestion import AS_OF as MS_AS_OF
from tests.test_theme_intelligence_ingestion import MS_HTML, MS_PDF, _ms, _ms_extraction
from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.config import sec_user_agent
from vinci.theme_intelligence.config import load_taxonomy
from vinci.theme_intelligence.contradiction import AMBIGUOUS, COMPATIBLE, CONTRADICTS, compare
from vinci.theme_intelligence.documents import read_document
from vinci.theme_intelligence.engine import thesis_id_for
from vinci.theme_intelligence.ingest import NEW, identify, ingest_file
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import (
    Claim,
    ClaimKind,
    Confidence,
    Epistemic,
    RunStatus,
    ThesisStatus,
)
from vinci.theme_intelligence.store import Store

AS_OF = date(2026, 10, 14)
MEM = "ai_infrastructure.memory"
ROOT = Path(__file__).resolve().parent.parent


def _mem(line: str, title: str, n: int, period: str = "Q3 2026") -> dict[str, Any]:
    return extraction([claim("c1", "b001", line.rstrip("."), f"Memory contract prices +{n}%",
                             metric="memory contract price change", value=n, value_text=f"{n}%",
                             unit="%", period=period)],
                      [hyp("h1", title, node=MEM, mechanism="pricing_cycle", geography="Global",
                           supporting=["c1"])])


def _issues(pipe: Pipeline, code: str) -> list[str]:
    return [i.detail for i in pipe.store.issues() if i.code == code]


# --- U8: the former key follows the chain of retired ids --------------------------------------

def _retired_then_rekeyed(tmp_path: Path) -> tuple[Pipeline, str, str]:
    """R (bare key K) retired by re-analysis; S created at the salted id with K; S re-keyed."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 12% in Q3 2026."
    a1 = Hypo("bare-a", "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
    r1 = ingest(pipe, a1.doc(), _mem(line, "Memory pricing keeps rising", 12), as_of=AS_OF,
                publisher=a1.publisher)
    (r,) = pipe.store.theses()
    key = r.identity
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.run_reanalyse(article_ids=[r1.article_id or ""], retire=[r.thesis_id], reason="test",
                       as_of=AS_OF, fixtures={r1.article_id or "": _mem(
                           line, "Memory pricing keeps rising", 12)})
    s = next(t for t in pipe.store.theses() if not t.retired)
    assert s.thesis_id == thesis_id_for(f"{key}|after:{r.thesis_id}")
    pipe.store.rekey_thesis(s.model_copy(update={"key_segment": "nand"}))
    return pipe, key, s.thesis_id


def test_a_bare_key_article_finds_the_thesis_created_with_it_past_a_retired_one(
        tmp_path: Path) -> None:
    """POSITIVE: main raised StoreIntegrityError (`thesis_versions` id [S, 1]) here, and again
    on every later article with this key. The former key finds its thesis, as it does without a
    retirement in between."""
    pipe, key, sid = _retired_then_rekeyed(tmp_path)
    assert pipe.engine._by_key(key) is not None  # noqa: SLF001
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices climbed 15% in October 2026, according to our checks."
    a2 = Hypo("bare-b", "Other Publisher", date(2026, 10, 10), [("paragraph", line)])
    res = ingest(pipe, a2.doc(), _mem(line, "Memory prices climb again", 15, "October 2026"),
                 as_of=AS_OF, publisher=a2.publisher)
    assert res.status == "PROCESSED" and [o.thesis_id for o in res.outcomes] == [sid]
    assert len([t for t in pipe.store.theses() if not t.retired]) == 1


def test_a_retired_key_with_no_successor_is_never_matched(tmp_path: Path) -> None:
    """NEGATIVE: a retired thesis is never matched again — its key's lookup finds nothing."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 12% in Q3 2026."
    a1 = Hypo("bare-a", "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
    ingest(pipe, a1.doc(), _mem(line, "Memory pricing keeps rising", 12), as_of=AS_OF,
           publisher=a1.publisher)
    (r,) = pipe.store.theses()
    pipe.store.retire_thesis(r.model_copy(update={"retired": "R-test"}))
    assert pipe.engine._by_key(r.identity) is None  # noqa: SLF001
    gone = pipe.store.thesis(r.thesis_id)
    assert gone is not None and gone.identity != r.identity  # its key carries the retirement …
    assert pipe.engine._by_key(gone.identity) is None  # noqa: SLF001 — … and still never matches


# --- U1: a second route to one thesis is a second contribution ---------------------------------

L_DRAM = "DRAM contract prices rose 12% in Q3 2026."
L_SSD = "SSD contract prices rose 8% in Q3 2026 as NAND supply tightened."


def _dram() -> dict[str, Any]:
    return claim("c1", "b001", L_DRAM.rstrip("."), "DRAM contract prices +12% in Q3 2026",
                 metric="DRAM contract price change", value=12, value_text="12%", unit="%",
                 period="Q3 2026")


def _first_version(tmp_path: Path) -> tuple[Pipeline, str]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    v1 = Hypo("mem", "Test Publisher", date(2026, 10, 1), [("paragraph", L_DRAM)])
    ingest(pipe, v1.doc(), extraction([_dram()], [hyp(
        "h1", "DRAM pricing keeps rising", node=MEM, mechanism="pricing_cycle",
        geography="Global", supporting=["c1"])]), as_of=AS_OF, publisher=v1.publisher)
    (t,) = pipe.store.theses()
    return pipe, t.thesis_id


def test_a_second_hypothesis_reaching_one_thesis_by_another_route_is_applied(
        tmp_path: Path) -> None:
    """POSITIVE: a later version keys h1 exactly and h2 (DRAM + NAND) by another segment; the
    same-article route sends h2 to the same thesis. Main: ALREADY_INGESTED, the SSD claim linked
    to nothing, no warning."""
    pipe, tid = _first_version(tmp_path)
    before = len(pipe.store.contributions(tid))
    v2 = Hypo("mem", "Test Publisher", date(2026, 10, 1),
              [("paragraph", L_DRAM), ("paragraph", L_SSD)])
    ssd = claim("c2", "b002", "SSD contract prices rose 8% in Q3 2026",
                "SSD contract prices +8% in Q3 2026", metric="SSD contract price change",
                value=8, value_text="8%", unit="%", period="Q3 2026")
    r2 = ingest(pipe, v2.doc(), extraction([_dram(), ssd], [
        hyp("h1", "DRAM pricing keeps rising", node=MEM, mechanism="pricing_cycle",
            geography="Global", supporting=["c1"]),
        hyp("h2", "DRAM and NAND SSD pricing keep rising", node=MEM, mechanism="pricing_cycle",
            geography="Global", supporting=["c1", "c2"])]), as_of=AS_OF, publisher=v2.publisher)
    assert [o.thesis_id for o in r2.outcomes] == [tid, tid]
    assert "ALREADY_INGESTED" not in {e for o in r2.outcomes for e in o.events}
    (c2,) = [c for c in pipe.store.claims_for_article(r2.article_id or "")
             if c.quote.startswith("SSD")]
    assert pipe.store.linked_claim_ids([c2.claim_id]) == {c2.claim_id}
    assert len(pipe.store.contributions(tid)) == before + 2  # one per route
    (warn,) = _issues(pipe, "SAME_THESIS_IN_ARTICLE")
    assert tid in warn and "DRAM and NAND SSD" in warn


def test_one_hypothesis_per_thesis_is_one_contribution(tmp_path: Path) -> None:
    """NEGATIVE: a later version whose one hypothesis reaches the thesis — one contribution, no
    warning."""
    pipe, tid = _first_version(tmp_path)
    before = len(pipe.store.contributions(tid))
    v2 = Hypo("mem", "Test Publisher", date(2026, 10, 1),
              [("paragraph", L_DRAM), ("paragraph", L_SSD)])
    r2 = ingest(pipe, v2.doc(), extraction([_dram()], [hyp(
        "h1", "DRAM pricing keeps rising", node=MEM, mechanism="pricing_cycle",
        geography="Global", supporting=["c1"])]), as_of=AS_OF, publisher=v2.publisher)
    assert [o.thesis_id for o in r2.outcomes] == [tid]
    assert len(pipe.store.contributions(tid)) == before + 1
    assert _issues(pipe, "SAME_THESIS_IN_ARTICLE") == []


# --- U2: archiving never takes a thesis out of review --------------------------------------------

def _hold(pipe: Pipeline, tid: str) -> list[str]:
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    return [f.note for f in v.priority.factors
            if f.factor_id == "F10_verification_hold" and f.value == "HOLD"]


def test_an_archived_sibling_comes_back_held_for_review(tmp_path: Path) -> None:
    """POSITIVE: a same-article SIBLING (REVIEW_NEEDED, identity hold) archived as stale, then
    updated by material evidence. Main: ACTIVE, the hold gone."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    v1 = Hypo("sib", "Test Publisher", date(2026, 10, 1), [("paragraph", L_DRAM)])
    ingest(pipe, v1.doc(), extraction([_dram()], [hyp(
        "h1", "DRAM pricing keeps rising", node=MEM, mechanism="pricing_cycle",
        geography="Global", supporting=["c1"])]), as_of=AS_OF, publisher=v1.publisher)
    v2 = Hypo("sib", "Test Publisher", date(2026, 10, 1),
              [("paragraph", L_DRAM), ("paragraph", "Analysts expect DRAM prices to fall.")])
    ingest(pipe, v2.doc(), extraction([_dram()], [hyp(
        "h2", "DRAM pricing set to fall", node=MEM, mechanism="pricing_cycle",
        direction="negative", geography="Global", supporting=["c1"])]),
        as_of=AS_OF, publisher=v2.publisher)
    (sib,) = [t for t in pipe.store.theses() if t.status is ThesisStatus.REVIEW_NEEDED]
    assert _hold(pipe, sib.thesis_id)
    late = date(2027, 2, 15)
    pipe.engine.archive_pass(run_id=pipe.run.run_id, as_of=late)  # type: ignore[union-attr]
    assert pipe.store.thesis(sib.thesis_id).status is ThesisStatus.ARCHIVED  # type: ignore[union-attr]
    a3 = Hypo("other-src", "Other Publisher", date(2027, 2, 10),
              [("paragraph", "DRAM spot prices fell 9% in January 2027.")])
    r3 = ingest(pipe, a3.doc(), extraction(
        [claim("c1", "b001", "DRAM spot prices fell 9% in January 2027",
               "DRAM spot prices -9% in January 2027", metric="DRAM spot price", value=-9,
               value_text="9%", unit="%", period="January 2027")],
        [hyp("h1", "DRAM pricing set to fall", node=MEM, mechanism="pricing_cycle",
             direction="negative", geography="Global", supporting=["c1"])]),
        as_of=late, publisher=a3.publisher)
    assert "REACTIVATED" in r3.outcomes[0].events
    assert pipe.store.thesis(sib.thesis_id).status is ThesisStatus.REVIEW_NEEDED  # type: ignore[union-attr]
    assert _hold(pipe, sib.thesis_id)  # the identity hold is on the new version too


def _archive_and_reactivate(tmp_path: Path, *, node: str, mechanism: str) -> ThesisStatus:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    title = "Unclassified widget demand rises"
    a1 = Hypo("op", "Test Publisher", date(2026, 10, 1),
              [("paragraph", "We think demand for test widgets will be strong.")])
    ingest(pipe, a1.doc(), extraction(
        [claim("c1", "b001", "We think demand for test widgets will be strong",
               "Demand for test widgets will be strong", kind="opinion", epistemic="opinion")],
        [hyp("h1", title, node=node, mechanism=mechanism, supporting=["c1"])]),
        as_of=AS_OF, publisher=a1.publisher)
    (t,) = pipe.store.theses()
    late = date(2027, 2, 15)  # stale, whatever its action
    pipe.engine.archive_pass(run_id=pipe.run.run_id, as_of=late)  # type: ignore[union-attr]
    assert pipe.store.thesis(t.thesis_id).status is ThesisStatus.ARCHIVED  # type: ignore[union-attr]
    a2 = Hypo("metric", "Other Publisher", date(2027, 2, 10),
              [("paragraph", "Test widget shipments rose 40% in January 2027.")])
    ingest(pipe, a2.doc(), extraction(
        [claim("c1", "b001", "Test widget shipments rose 40% in January 2027",
               "Test widget shipments +40% in January 2027", metric="shipments", value=40,
               value_text="40%", unit="%", period="January 2027")],
        [hyp("h1", title, node=node, mechanism=mechanism, supporting=["c1"])]),
        as_of=late, publisher=a2.publisher)
    out = pipe.store.thesis(t.thesis_id)
    assert out is not None and "REACTIVATED" in {
        e.event_type for e in pipe.store.events(thesis_id=t.thesis_id)}
    return out.status


def test_an_archived_unclassified_thesis_comes_back_for_review(tmp_path: Path) -> None:
    """POSITIVE: an `other` thesis (a human must classify it) archived, then reactivated — main
    brought it back ACTIVE."""
    assert _archive_and_reactivate(tmp_path, node="other",
                                   mechanism="other") is ThesisStatus.REVIEW_NEEDED


def test_an_archived_ordinary_thesis_comes_back_active(tmp_path: Path) -> None:
    """NEGATIVE: a thesis never held for review comes back ACTIVE, as before."""
    assert _archive_and_reactivate(tmp_path, node="ai_infrastructure.compute_semis",
                                   mechanism="demand_volume_shift") is ThesisStatus.ACTIVE


# --- U38: an undated source never takes the run's date -----------------------------------------

def test_undated_evidence_never_resets_a_theses_stale_clock(tmp_path: Path) -> None:
    """POSITIVE: an undated article updates a thesis — its last-evidence date is kept, the change
    item carries no date, and the run says why (main: the run's as-of as both)."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 12% in Q3 2026."
    a1 = Hypo("dated", "Test Publisher", date(2026, 9, 1), [("paragraph", line)])
    ingest(pipe, a1.doc(), _mem(line, "Memory pricing keeps rising", 12), as_of=AS_OF,
           publisher=a1.publisher)
    (t,) = pipe.store.theses()
    assert t.last_material_update == date(2026, 9, 1)
    line2 = "Memory contract prices rose a further 9% in October 2026."
    a2 = Hypo("undated", "Other Publisher", None, [("paragraph", line2)])
    res = ingest(pipe, a2.doc(), _mem(line2, "Memory pricing keeps rising", 9, "October 2026"),
                 as_of=AS_OF, publisher=a2.publisher)
    after = pipe.store.thesis(t.thesis_id)
    assert after is not None and after.current_version == 2
    assert after.last_material_update == date(2026, 9, 1)  # main: 2026-10-14, the run's as-of
    v = pipe.store.thesis_version(t.thesis_id, 2)
    assert v is not None
    dates = {i.original_date for i in v.content.s02_what_changed.items
             if i.article_id == res.article_id}
    assert dates == {None}
    (warn,) = _issues(pipe, "UNDATED_SOURCE")
    assert res.article_id in warn and "keeps its own last-evidence date" in warn


def test_an_undated_source_creating_a_thesis_says_so(tmp_path: Path) -> None:
    """The clock of a thesis an undated source creates starts at the run's as-of — the only date
    the registry has — and the card says the source is undated."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 12% in Q3 2026."
    a1 = Hypo("undated", "Test Publisher", None, [("paragraph", line)])
    ingest(pipe, a1.doc(), _mem(line, "Memory pricing keeps rising", 12), as_of=AS_OF,
           publisher=a1.publisher)
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None and t.last_material_update == AS_OF
    assert "UNDATED source" in v.content.s02_what_changed.vs_prior
    assert {i.original_date for i in v.content.s02_what_changed.items} == {None}


def test_a_dated_source_is_dated_by_its_publication(tmp_path: Path) -> None:
    """NEGATIVE: a dated source moves the clock to its own date and raises no warning."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 12% in Q3 2026."
    a1 = Hypo("dated", "Test Publisher", date(2026, 10, 2), [("paragraph", line)])
    ingest(pipe, a1.doc(), _mem(line, "Memory pricing keeps rising", 12), as_of=AS_OF,
           publisher=a1.publisher)
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None and t.last_material_update == date(2026, 10, 2)
    assert "a source published 2026-10-02" in v.content.s02_what_changed.vs_prior
    assert _issues(pipe, "UNDATED_SOURCE") == []


@pytest.mark.parametrize(("published", "basis"), [
    (None, "before this run's as-of (the source states no publication date)"),
    (date(2026, 10, 1), "before publication")])
def test_a_stale_series_names_what_it_is_measured_against(
        tmp_path: Path, published: date | None, basis: str) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("stale", "Hypo Research A", published, [
        ("paragraph", "Server shipments grew 12% according to the survey."),
        ("chart_source", "Source: Hypo Survey. Data as of June 30, 2024.")])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", "Server shipments grew 12%", "Server shipments +12%",
               metric="server shipment growth", value=12, value_text="12%", unit="%",
               measured_as_of="2024-06-30", as_of_block="b002", source="Hypo Survey")],
        [hyp("h1", "Server demand", node="ai_infrastructure.compute_semis",
             mechanism="demand_volume_shift", supporting=["c1"])]),
        as_of=AS_OF, publisher=art.publisher)
    (c,) = pipe.store.claims_for_article(pipe.store.articles()[0].article_id)
    (q,) = [q for q in c.qualifiers if q.startswith("stale series")]
    assert q.endswith(basis)


# --- U18: demand and supply are two variables -------------------------------------------------

PRODUCTS = list(load_taxonomy().products_of(MEM))


def _c(cid: str, quote: str) -> Claim:
    return Claim(claim_id=cid, article_id="A" + cid, article_version_id="AV", block_id="b",
                 char_start=0, char_end=1, quote=quote, statement=quote, kind=ClaimKind.FORECAST,
                 epistemic=Epistemic.FORECAST, period="2027", confidence=Confidence.HIGH,
                 span_verified=True, number_verified=True, measure_key="k" + cid,
                 fingerprint="f" + cid, extraction_id="X", origin_id="O" + cid)


def _verdict(a: str, b: str) -> str:
    return compare(_c("1", a), _c("2", b), products=PRODUCTS, ref=AS_OF,
                   overlap_geo=lambda x, y: True, geo_ch="Global", geo_inc="Global").kind


@pytest.mark.parametrize(("challenger", "incumbent", "kind"), [
    # POSITIVE — the verifier's pair, both ways: one bullish reading, never a contradiction
    ("HBM supply will fall short in 2027", "HBM demand is expected to rise 50% in 2027",
     COMPATIBLE),
    ("HBM demand is expected to rise 50% in 2027", "HBM supply will fall short in 2027",
     COMPATIBLE),
    # a claim naming both: its one direction is supply's — unclear against demand
    ("HBM supply will fall short of demand in 2027", "HBM demand is expected to rise 50% in 2027",
     AMBIGUOUS),
    # a shipped volume is neither side alone: unclear, never "different variables"
    ("HBM shipments will fall in 2027", "HBM demand is expected to rise 50% in 2027", AMBIGUOUS),
    # NEGATIVE — one variable, opposite directions: still a contradiction
    ("HBM demand will fall 20% in 2027", "HBM demand is expected to rise 50% in 2027",
     CONTRADICTS),
    ("HBM supply will fall in 2027", "HBM supply will rise in 2027", CONTRADICTS),
    ("HBM shipments will fall in 2027", "HBM shipments will rise in 2027", CONTRADICTS),
])
def test_demand_and_supply_are_two_variables(challenger: str, incumbent: str, kind: str) -> None:
    assert _verdict(challenger, incumbent) == kind


# --- U14: a pulled registry compares block hashes ---------------------------------------------

NEW_TITLE = "Synthetic Note: Operators Move Power Generation On-Site"


def _pulled(tmp_path: Path) -> tuple[Pipeline, str]:
    a = make_pipeline(tmp_path / "a")
    a.start_run("ingest", as_of=MS_AS_OF)
    first = ingest_file(a, MS_PDF, _ms(), as_of=MS_AS_OF, fixture=_ms_extraction())
    a.store.export_jsonl(tmp_path / "branch")
    (tmp_path / "b" / "ti").mkdir(parents=True)
    Store.import_jsonl(tmp_path / "branch", tmp_path / "b" / "ti" / "registry.db").close()
    b = make_pipeline(tmp_path / "b")
    b.start_run("ingest", as_of=MS_AS_OF)
    return b, first.article_id or ""


def test_a_retitled_copy_on_a_pulled_registry_goes_to_review(tmp_path: Path) -> None:
    """POSITIVE: the held report's text is not on this machine; a copy under another title (27%
    title overlap) was a NEW, paid article on main. Its argument blocks hash the same: REVIEW."""
    b, held = _pulled(tmp_path)
    html = MS_HTML.read_text()
    html = (html.replace("<title>Synthetic Utilities Note: AI Power Demand</title>",
                         f"<title>{NEW_TITLE}</title>")
            .replace("<h1>Synthetic Utilities Note: AI Power Demand Moves On-Site</h1>",
                     f"<h1>{NEW_TITLE}</h1>"))
    copy = tmp_path / "ms_retitled.html"
    copy.write_text(html)
    assert read_document(copy, _ms()).doc.title == NEW_TITLE
    res = ingest_file(b, copy, _ms(), as_of=MS_AS_OF, fixture=_ms_extraction())
    assert res.status == "REVIEW" and res.article_id == held
    assert "word(s) of identical argument blocks" in res.note
    assert b.store.conn.execute("SELECT count(*) FROM articles").fetchone() == (1,)


def test_another_report_on_a_pulled_registry_is_new(tmp_path: Path) -> None:
    """NEGATIVE: a different report of the same publisher shares a date line and a byline with
    the held one, never its argument: NEW."""
    b, _held = _pulled(tmp_path)
    other = tmp_path / "ms_other.html"
    other.write_text(
        "<html><head><title>Synthetic Note: Copper Cathode Premiums</title></head><body>"
        "<h1>Synthetic Note: Copper Cathode Premiums</h1>"
        "<p>Synthetic Strategist, Equity Research</p><p>October 1, 2026</p>"
        "<p>[SYNTHETIC TEST FIXTURE] Copper cathode premiums in Shanghai widened to $120 per "
        "tonne as smelter maintenance tightened refined supply into the fourth quarter, and "
        "fabricators drew down bonded stocks to cover orders from grid and data-centre "
        "customers across the region.</p>"
        "<p>[SYNTHETIC TEST FIXTURE] We expect premiums to ease in the first half of 2027 as "
        "new smelting capacity in Indonesia and the Democratic Republic of Congo ramps, which "
        "would leave the market close to balance by mid-year on our estimates.</p>"
        "</body></html>")
    m = identify(b, read_document(other, _ms()), _ms())
    assert m.kind == NEW, m.basis


DISCLAIMER = ("This material is provided for information only and is not an offer or "
              "solicitation to buy or sell any security. Past performance is not a guide to "
              "future returns. The views expressed are those of the author at the date of "
              "publication and may change without notice. The publisher and its affiliates may "
              "hold positions in the securities discussed, act as market maker or adviser to "
              "issuers named, and receive compensation for such services. Investors should "
              "seek independent advice before acting on anything in this note, which does not "
              "take into account the objectives, financial situation or needs of any reader.")


def test_a_shared_disclaimer_on_a_pulled_registry_is_not_the_same_report(
        tmp_path: Path) -> None:
    """NEGATIVE: every report of a publisher repeats its disclaimer word for word — a long
    block that would outweigh the argument. Only argument blocks are compared: NEW."""
    from vinci.theme_intelligence.documents import Declared, DocumentRead

    a = make_pipeline(tmp_path / "a")
    a.start_run("ingest", as_of=AS_OF)
    held = Hypo("held-dram-price-note", "Test Publisher", date(2026, 10, 1),
                [("paragraph", L_DRAM), ("disclaimer", DISCLAIMER)])
    ingest(a, held.doc(), extraction([_dram()], [hyp(
        "h1", "DRAM pricing keeps rising", node=MEM, mechanism="pricing_cycle",
        geography="Global", supporting=["c1"])]), as_of=AS_OF, publisher=held.publisher)
    a.store.export_jsonl(tmp_path / "branch")
    (tmp_path / "b" / "ti").mkdir(parents=True)
    Store.import_jsonl(tmp_path / "branch", tmp_path / "b" / "ti" / "registry.db").close()
    b = make_pipeline(tmp_path / "b")
    other = Hypo("copper-cathode-premiums-weekly", "Test Publisher", date(2026, 10, 8),
                 [("paragraph", "Copper cathode premiums in Shanghai widened to $120 per tonne "
                                "as smelter maintenance tightened refined supply."),
                  ("disclaimer", DISCLAIMER)])
    read = DocumentRead(path=tmp_path / "other.html", sha256="0" * 64, fmt="html", size=1,
                        doc=other.doc())
    m = identify(b, read, Declared(source_id="manual"))
    assert m.kind == NEW, m.basis


# --- U31e: an unset secret is an unset User-Agent -----------------------------------------------

@pytest.mark.parametrize(("value", "contact"), [
    ("", "tech@muns.io"), ("   ", "tech@muns.io"),  # POSITIVE: main raised IndexError at import
    ("Acme Research ops@acme.test", "ops@acme.test")])  # NEGATIVE: a set value is used
def test_the_package_imports_whatever_the_sec_user_agent(value: str, contact: str) -> None:
    out = subprocess.run(
        [sys.executable, "-c",
         "from vinci.theme_intelligence.config import USER_AGENT; print(USER_AGENT)"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
        env={**os.environ, "SEC_USER_AGENT": value, "PYTHONDONTWRITEBYTECODE": "1"})
    assert out.returncode == 0, out.stderr[-400:]
    assert out.stdout.strip().endswith(f"contact: {contact})")


def test_an_empty_sec_user_agent_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "")
    assert sec_user_agent() == "vinci-research tech@muns.io"
    monkeypatch.setenv("SEC_USER_AGENT", "Acme Research ops@acme.test")
    assert sec_user_agent() == "Acme Research ops@acme.test"


def test_a_thesis_this_version_created_is_reached_again_as_a_second_contribution(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Whatever route brings a second hypothesis to a thesis the SAME version just created, its
    evidence is applied (the creation's contribution id would swallow it). The route is forced
    here: no natural one is known to reach a same-version creation today."""
    from vinci.theme_intelligence.engine import Engine

    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    made: list[str] = []
    real = Engine._create

    def create(self: Engine, *a: Any, **kw: Any) -> Any:
        out = real(self, *a, **kw)
        made.append(out.thesis_id)
        return out

    monkeypatch.setattr(Engine, "_create", create)
    monkeypatch.setattr(Engine, "_same_article_thesis",
                        lambda self, *a, **kw: self.store.thesis(made[0]) if made else None)
    v1 = Hypo("mem", "Test Publisher", date(2026, 10, 1),
              [("paragraph", L_DRAM), ("paragraph", L_SSD)])
    ssd = claim("c2", "b002", "SSD contract prices rose 8% in Q3 2026",
                "SSD contract prices +8% in Q3 2026", metric="SSD contract price change",
                value=8, value_text="8%", unit="%", period="Q3 2026")
    res = ingest(pipe, v1.doc(), extraction([_dram(), ssd], [
        hyp("h1", "DRAM pricing keeps rising", node=MEM, mechanism="pricing_cycle",
            geography="Global", supporting=["c1"]),
        hyp("h2", "DRAM and NAND SSD pricing keep rising", node=MEM, mechanism="pricing_cycle",
            geography="Global", supporting=["c1", "c2"])]), as_of=AS_OF, publisher=v1.publisher)
    assert len(made) == 1 and [o.thesis_id for o in res.outcomes] == [made[0], made[0]]
    assert "ALREADY_INGESTED" not in {e for o in res.outcomes for e in o.events}
    assert len(pipe.store.contributions(made[0])) == 2
