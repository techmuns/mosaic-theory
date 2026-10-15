"""Group 5 of the review leads — WRITES A WRONG FACT OR LOSES ONE (U5, U6, U7, U10, U12, U25,
U55). Verified on main d304ea16
(`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`); the real runs on
copies of the pilot are in the build record.

End to end through the REAL engine on HYPOTHETICAL articles (invented text on the reserved `.test`
domain), extractions in the REAL type. No network, no model call.
"""

from __future__ import annotations

import dataclasses
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.engine import classify_claim
from vinci.theme_intelligence.pipeline import CHANNEL_DEFAULT, Pipeline
from vinci.theme_intelligence.schemas import (
    ArticleClass,
    ChangeClass,
    Claim,
    ClaimKind,
    Confidence,
    Epistemic,
    IssueSeverity,
    LinkRole,
    ResearchAction,
    RunStatus,
    ThesisClaimLink,
    ThesisStatus,
    VerificationIssue,
)

AS_OF = date(2026, 10, 14)
MEM = "ai_infrastructure.memory"


def _x(line: str, title: str, node: str, metric: str, **kw: Any) -> dict[str, Any]:
    return extraction([claim("c1", "b001", line.rstrip("."), title, metric=metric, value=9,
                             value_text="9%", unit="%", period=kw.pop("period", "2026"))],
                      [hyp("h1", title, node=node, mechanism=kw.pop("mechanism",
                                                                    "demand_volume_shift"),
                           supporting=["c1"], **kw)])


def _action(pipe: Pipeline, tid: str) -> ResearchAction:
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    return v.priority.research_action


# --- U5: a new claim is read against the right held reading, whatever the claim ids ---------------

def _c(cid: str, origin: str, *, period: str | None = None, value: float | None = None,
       event: bool = False) -> Claim:
    key = "event||plant opening" if event else "|memory price|q3 2026|%"
    return Claim(claim_id=cid, article_id=f"A-{origin}", article_version_id=f"AV-{origin}",
                 block_id="b001", char_start=0, char_end=4, quote="text", statement="text",
                 kind=ClaimKind.EVENT if event else ClaimKind.METRIC,
                 epistemic=Epistemic.FORECAST, period=period, value=value,
                 value_text=None if value is None else f"{value:g}%", confidence=Confidence.HIGH,
                 span_verified=True, number_verified=True, measure_key=key,
                 fingerprint=f"{key}|{period or value}|{origin}", extraction_id="X-1",
                 origin_id=f"O-{origin}")


@pytest.mark.parametrize("ids", [("C-a", "C-b"), ("C-b", "C-a")])
def test_a_third_origin_confirming_a_moved_date_is_a_confirmation_in_any_id_order(
        ids: tuple[str, str]) -> None:
    """X dates the plant 1Q27; Y moves it to 2Q27 (a timing change); Z says 2Q27 — a confirmation
    of the latest date, never a "timing change" from 1Q27 (claim-id order chose either held claim:
    2 of 6 text variants misclassified). NEGATIVE pin: a date no one held moves the LATEST one."""
    first = _c(ids[0], "x", period="1Q27", event=True)
    moved = _c(ids[1], "y", period="2Q27", event=True)
    cls, _note = classify_claim(_c("C-new", "z", period="2Q27", event=True), LinkRole.SUPPORTS,
                                [first, moved])
    assert cls is ChangeClass.INDEPENDENT_CONFIRMATION
    cls, note = classify_claim(_c("C-new", "z", period="3Q27", event=True), LinkRole.SUPPORTS,
                               [first, moved])
    assert cls is ChangeClass.TIMING_CHANGE and "2Q27 → 3Q27" in note


def test_a_figure_is_read_against_its_own_origin_first_then_one_it_agrees_with() -> None:
    held = [_c("C-b", "x", value=10), _c("C-a", "y", value=12)]
    assert classify_claim(_c("C-n", "z", value=12), LinkRole.SUPPORTS, held)[0] \
        is ChangeClass.INDEPENDENT_CONFIRMATION
    assert classify_claim(_c("C-n", "x", value=11), LinkRole.SUPPORTS, held)[0] \
        is ChangeClass.CORRECTION  # its own origin's reading, revised
    assert classify_claim(_c("C-n", "z", value=20), LinkRole.SUPPORTS, held)[0] \
        is ChangeClass.CONTRADICTORY  # NEGATIVE: agrees with no one


@pytest.mark.parametrize("variant", range(6))
def test_end_to_end_a_moved_date_is_read_against_the_latest_reading(variant: int,
                                                                   tmp_path: Path) -> None:
    """Three publishers date one event: 1Q27, then 2Q27, then 3Q27. The third is a timing change
    FROM 2Q27 — the reading the thesis took last — for every wording (claim ids differ by text)."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    for n, (pub, period) in enumerate((("Publisher X", "1Q27"), ("Publisher Y", "2Q27"),
                                       ("Publisher Z", "3Q27"))):
        line = f"The new fab is expected to open in {period} (note {variant}-{n})."
        art = Hypo(f"fab-{variant}-{n}", pub, date(2026, 10, 1 + n), [("paragraph", line)])
        x = extraction([claim("c1", "b001", line.rstrip("."), f"Fab opens {period}",
                              kind="event", epistemic="forecast", metric="fab opening",
                              period=period)],
                       [hyp("h1", "Memory supply arrives later", node=MEM,
                            mechanism="supply_constraint", supporting=["c1"])])
        ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=pub)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    last = max(pipe.store.links(t.thesis_id), key=lambda lk: lk.first_version)
    assert last.change_class is ChangeClass.TIMING_CHANGE
    moved = [lk for lk in pipe.store.links(t.thesis_id)
             if lk.change_class is ChangeClass.TIMING_CHANGE]
    assert len(moved) == 2
    said = " ".join(it.text for v in pipe.store.thesis_versions(t.thesis_id)
                    for it in v.content.s02_what_changed.items)
    assert "2Q27 → 3Q27" in said and "1Q27 → 3Q27" not in said


# --- U6: a re-read version that changes nothing leaves nothing behind -----------------------------

def test_a_discarded_reread_version_leaves_no_link_and_no_review_record() -> None:
    """The orphan re-read (the earlier thesis re-verified, nothing new) whose review re-anchors one
    line: the version changes nothing and is DISCARDED — main still stored the re-anchor's
    CONTEXT link (for a version that never existed) and the review's record."""
    from tests.test_theme_intelligence_glyph_quarantine import (
        Aligning,
        _ingest,
        _pipe,
        _unguarded,
    )
    from vinci.theme_intelligence.schemas import SOURCE_LABELS
    from vinci.theme_intelligence.verify import ReviewOutcome, card_sentences

    pipe = _pipe(Path(tempfile.mkdtemp()), Aligning(orphan=True))
    mp = pytest.MonkeyPatch()
    _unguarded(mp)
    _ingest(pipe)
    mp.undo()
    before = {t.thesis_id: t.current_version for t in pipe.store.theses()}
    src = {p.value for p in SOURCE_LABELS}
    asked: dict[str, tuple[str, str]] = {}

    def reviewer(card: Any, claims: dict[str, Claim]) -> ReviewOutcome:
        sents = card_sentences(card)
        tid = card.header.thesis_id
        if tid in asked and asked[tid][1] in sents.get(asked[tid][0], ("", "", ()))[2]:
            return ReviewOutcome([])  # the re-review: the re-anchored line stands
        cited = {c for _t, _p, cids in sents.values() for c in cids}
        other = [cid for cid, c in claims.items() if cid not in cited and c.span_verified
                 and c.number_verified is not False]
        sid = next((s for s, (_t, p, c) in sents.items() if p in src and c), None)
        if sid is None or not other:
            return ReviewOutcome([])
        asked[tid] = (sid, other[0])
        assert pipe.run is not None
        return ReviewOutcome([VerificationIssue(
            issue_id=f"VI-stub-{tid}", run_id=pipe.run.run_id, scope="card_sentence",
            ref_id=f"{tid}:{sid}", severity=IssueSeverity.BLOCK, code="REVIEW_UNSUPPORTED",
            detail=f"{sid}: UNSUPPORTED — stub", created_at=datetime.now(tz=UTC))],
            {sid: other[:1]})

    pipe.engine.reviewer = reviewer  # type: ignore[assignment]
    _ingest(pipe, reread=True)
    rid = pipe.store.runs()[-1].run_id
    [rep] = pipe.store.completeness_for_run(rid)
    assert rep.coverage is not None and rep.coverage.reverified
    for tid in rep.coverage.reverified:
        t = pipe.store.thesis(tid)
        assert t is not None and t.current_version == before[tid]  # discarded
        assert asked.get(tid)  # the review DID re-anchor a line of the discarded card
        assert not [lk for lk in pipe.store.links(tid) if lk.first_version > t.current_version]
        assert not [i for i in pipe.store.issues(run_id=rid) if i.ref_id.startswith(tid + ":")]


# --- U7: a class the page stated survives re-analysis ---------------------------------------------

def test_a_page_stated_class_survives_reanalysis_and_a_channel_default_stays_one(
        tmp_path: Path) -> None:
    """Pilot A-b4589733a42a: "page states it 'should not be regarded as a research report'" became
    "channel default for jpm_tmt" when re-analysed. NEGATIVE pin: a channel default is not turned
    into a page statement."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    lines = ("Biopharma volumes rose 9% in 2026.", "Device orders rose 4% in 2026.")
    ids = []
    for i, line in enumerate(lines):
        art = Hypo(f"cls-{i}", "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
        doc = art.doc()
        if i == 0:
            doc.article_class_hint = ArticleClass.PUBLISHER_COMMENTARY
            doc.article_class_basis = "b001: page states it is commentary, not research"
        node = "healthcare.pharma_biotech" if i == 0 else "healthcare.medtech"
        r = ingest(pipe, doc, _x(line, f"Thesis {i}", node, f"metric {i}"), as_of=AS_OF,
                   publisher=art.publisher)
        assert r.article_id is not None
        ids.append(r.article_id)
    pipe.finish_run(RunStatus.SUCCEEDED)
    stated, default = (pipe.store.article(a) for a in ids)
    assert stated is not None and stated.article_class is ArticleClass.PUBLISHER_COMMENTARY
    assert default is not None and default.article_class_basis.startswith(CHANNEL_DEFAULT)
    pipe.run_reanalyse(article_ids=ids, retire=[], reason="test", as_of=AS_OF, fixtures={
        ids[0]: _x(lines[0], "Thesis 0", "healthcare.pharma_biotech", "metric 0"),
        ids[1]: _x(lines[1], "Thesis 1", "healthcare.medtech", "metric 1")})
    after_stated, after_default = (pipe.store.article(a) for a in ids)
    assert after_stated == stated  # the class and the page's own words, kept
    assert after_default is not None and after_default.article_class is default.article_class
    assert after_default.article_class_basis == default.article_class_basis


# --- U10: a thesis named twice is retired once ----------------------------------------------------

def test_a_thesis_named_twice_for_retirement_is_retired_once(tmp_path: Path) -> None:
    """`--retire T --retire T` failed the run on the second RETIRED event, with T retired and no
    replacement written. (A thesis holding evidence the run does not re-analyse is still refused:
    tests/test_theme_intelligence_reanalysis.py.)"""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Alzheimer's drug sales could grow 26% in 2026."
    art = Hypo("alz", "Test Publisher", date(2026, 9, 14), [("paragraph", line)])
    r = ingest(pipe, art.doc(), _x(line, "Alzheimer's market grows", "healthcare", "sales"),
               as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert r.article_id is not None
    (old,) = [t.thesis_id for t in pipe.store.theses()]
    run, _res = pipe.run_reanalyse(
        article_ids=[r.article_id], retire=[old, old], reason="test", as_of=AS_OF,
        fixtures={r.article_id: _x(line, "Alzheimer's market grows",
                                   "healthcare.pharma_biotech", "sales")})
    assert run.status is RunStatus.SUCCEEDED
    assert [e.event_type for e in pipe.store.events(thesis_id=old)].count("RETIRED") == 1
    assert pipe.store.thesis(old).retired == run.run_id  # type: ignore[union-attr]


# --- U12: a SKIP thesis leaves the active list at the end of EVERY run that changes theses --------

SKIP_LINE = "We think biopharma demand will broaden over time."
WATCH_LINE = "Memory contract prices rose 9% in Q3 2026."


def _skip_x() -> dict[str, Any]:
    """An opinion with no figure: no verified material evidence (SKIP-1)."""
    return extraction([claim("c1", "b001", SKIP_LINE.rstrip("."), "Biopharma demand broadens",
                             kind="assertion", epistemic="opinion")],
                      [hyp("h1", "skip thesis", node="healthcare.pharma_biotech",
                           mechanism="demand_volume_shift", supporting=["c1"])])


def _watch_x() -> dict[str, Any]:
    return _x(WATCH_LINE, "watch thesis", MEM, "memory price", period="Q3 2026",
              mechanism="pricing_cycle", geography="Global")


def _two(pipe: Pipeline) -> tuple[str, str]:
    """A SKIP thesis and one that is not, left ACTIVE by an ingest run's plain finish."""
    pipe.start_run("ingest", as_of=AS_OF)
    out = []
    for slug, line, x in (("skip", SKIP_LINE, _skip_x()), ("watch", WATCH_LINE, _watch_x())):
        art = Hypo(slug, "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
        ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
        (t,) = [y for y in pipe.store.theses() if y.title == f"{slug} thesis"]
        out.append(t.thesis_id)
    return out[0], out[1]


def test_an_ingest_run_ends_with_the_archive_pass(tmp_path: Path) -> None:
    """The pilot's SKIP theses stayed ACTIVE after uploads (7 of 19), and the next enrichment paid
    for three of them. NEGATIVE pin: a thesis that is not SKIP stays active."""
    pipe = make_pipeline(tmp_path)
    skip, watch = _two(pipe)
    assert _action(pipe, skip) is ResearchAction.SKIP
    assert _action(pipe, watch) is not ResearchAction.SKIP
    assert pipe.store.thesis(skip).status is ThesisStatus.ACTIVE  # type: ignore[union-attr]
    pipe.finish_ingest(RunStatus.SUCCEEDED)
    assert pipe.store.thesis(skip).status is ThesisStatus.ARCHIVED  # type: ignore[union-attr]
    assert pipe.store.thesis(watch).status is ThesisStatus.ACTIVE  # type: ignore[union-attr]


def test_a_reanalysis_archives_skip_theses_before_it_enriches(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = make_pipeline(tmp_path)
    skip, watch = _two(pipe)
    pipe.finish_run(RunStatus.SUCCEEDED)  # the state an upload left before the fix: SKIP active
    asked: list[list[str]] = []
    monkeypatch.setattr(pipe, "_scan_enrichment",
                        lambda as_of, targets=None: asked.append(list(targets or [])))
    aids = sorted({c.article_id for c in pipe.store.contributions()})
    fixtures = {aid: (_skip_x() if "biopharma" in pipe.store.article_versions(aid)[-1]
                      .blocks[0].text else _watch_x()) for aid in aids}
    pipe.run_reanalyse(article_ids=aids, retire=[], reason="test", as_of=AS_OF,
                       fixtures=fixtures)
    assert asked and skip not in asked[0] and watch in asked[0]


# --- U25: what an earlier run verified survives a fetch that cannot restate it --------------------

URL = "https://example.test/hypothetical/undated-note"
PARA = "Memory contract prices rose 9% in Q3 2026 as AI servers absorbed new supply."


FILLER = ("Suppliers kept capacity additions modest while hyperscalers extended long-term "
          "agreements, and buyers reported that allocation rather than price set the pace of "
          "deliveries through the quarter.")


def _page(published: str | None = None) -> str:
    meta = (f'<meta property="article:published_time" content="{published}T08:00:00Z">'
            if published else "")
    return (f"<html><head><title>[HYPOTHETICAL TEST FIXTURE] Undated note</title>{meta}</head>"
            f"<body><article><h1>Undated note</h1><p>{PARA}</p>"
            f"<p>Research led by Jane Analyst, memory team.</p>"
            + "".join(f"<p>Point {i}. {FILLER}</p>" for i in range(4))
            + "</article></body></html>")


def _fixture() -> dict[str, Any]:
    x = _x(PARA, "Memory prices climb", MEM, "memory price", period="Q3 2026",
           mechanism="pricing_cycle", geography="Global")
    x["claims"][0].update(quote=PARA.rstrip("."), block_id="b002")
    x["attributed_authors"] = [{"name": "Jane Analyst", "block_id": "b003",
                                "quote": "Research led by Jane Analyst"}]
    return x


def test_an_operator_verified_date_and_a_text_credited_author_survive_a_rerun(
        tmp_path: Path) -> None:
    """Re-running `article --url` on a registered URL without --published was ALREADY_INGESTED,
    but wiped the operator-verified date and the author the text credits. NEGATIVE pin: a date the
    page now states is the page's."""
    pipe = make_pipeline(tmp_path)
    _run, first = pipe.run_article(URL, as_of=AS_OF, html=_page(), fixture=_fixture(),
                                   published=date(2026, 10, 1))
    assert first.article_id is not None
    a1 = pipe.store.article(first.article_id)
    assert a1 is not None and a1.published_at is not None
    assert "operator-verified" in (a1.published_source or "")
    assert [x.name for x in a1.authors] == ["Jane Analyst"]
    _run, again = pipe.run_article(URL, as_of=AS_OF, html=_page(), fixture=_fixture())
    assert again.status == "ALREADY_INGESTED"
    a2 = pipe.store.article(first.article_id)
    assert a2 is not None
    assert (a2.published_at, a2.published_source) == (a1.published_at, a1.published_source)
    assert [x.name for x in a2.authors] == ["Jane Analyst"]
    _run, dated = pipe.run_article(URL, as_of=AS_OF, html=_page("2026-10-05"),
                                   fixture=_fixture())
    a3 = pipe.store.article(first.article_id)
    assert a3 is not None and a3.published_at is not None
    assert a3.published_at.date() == date(2026, 10, 5)


# --- U55: a reassess derives its holds and reads the current source tier --------------------------

def _f10(pipe: Pipeline, tid: str) -> tuple[str, str]:
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    f = next(x for x in v.priority.factors if x.factor_id == "F10_verification_hold")
    return f.value, f.note


def test_a_reassess_never_doubles_a_hold_reason(tmp_path: Path) -> None:
    """The reassess re-joined the previous note to the reasons it had just recomputed: a failed
    span reason read twice after two reassesses. Its claim is written through the store, as a
    span check stored before this code would have left it."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 9% in Q3 2026."
    art = Hypo("m", "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
    ingest(pipe, art.doc(), _x(line, "Memory prices climb", MEM, "memory price",
                               period="Q3 2026", mechanism="pricing_cycle", geography="Global"),
           as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    good = pipe.store.claim(pipe.store.links(t.thesis_id)[0].claim_id)
    assert good is not None
    bad = good.model_copy(update={"claim_id": "C-unverified00001", "span_verified": False,
                                  "fingerprint": "f|unverified", "measure_key": "k|unverified"})
    pipe.store.add_claim(bad)
    pipe.store.add_link(ThesisClaimLink(thesis_id=t.thesis_id, claim_id=bad.claim_id,
                                        role=LinkRole.SUPPORTS, first_version=1,
                                        change_class=ChangeClass.NEW,
                                        independence_group="O-x"))
    for d in (15, 16, 17):
        pipe.run_reassess(as_of=date(2026, 10, d))
    value, note = _f10(pipe, t.thesis_id)
    assert value == "HOLD" and note.count("C-unverified00001 failed span verification") == 1


def test_an_identity_hold_clears_on_reassess_once_the_identity_is_resolved(
        tmp_path: Path) -> None:
    """A HOLD never cleared on reassess: the old note was carried whatever had changed. NEGATIVE
    pin: while the identity is still under review, the hold stands."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    l1 = "DRAM contract prices rose 12% in Q3 2026."
    v1 = Hypo("sib", "Test Publisher", date(2026, 10, 1), [("paragraph", l1)])
    c1 = claim("c1", "b001", l1.rstrip("."), "DRAM +12% Q3 2026", metric="DRAM price change",
               value=12, value_text="12%", unit="%", period="Q3 2026")
    ingest(pipe, v1.doc(), extraction([c1], [hyp(
        "h1", "DRAM pricing keeps rising", node=MEM, mechanism="pricing_cycle",
        geography="Global", supporting=["c1"])]), as_of=AS_OF, publisher=v1.publisher)
    v2 = Hypo("sib", "Test Publisher", date(2026, 10, 1),
              [("paragraph", l1), ("paragraph", "Analysts expect DRAM prices to fall.")])
    ingest(pipe, v2.doc(), extraction([c1], [hyp(
        "h2", "DRAM pricing set to fall", node=MEM, mechanism="pricing_cycle",
        direction="negative", geography="Global", supporting=["c1"])]),
        as_of=AS_OF, publisher=v2.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (sib,) = [t for t in pipe.store.theses() if t.status is ThesisStatus.REVIEW_NEEDED]
    assert "identity under review" in _f10(pipe, sib.thesis_id)[1]
    pipe.run_reassess(as_of=date(2026, 10, 15), thesis_ids=[sib.thesis_id])
    assert "identity under review" in _f10(pipe, sib.thesis_id)[1]  # NEGATIVE: still held
    pipe.store.upsert_thesis(sib.model_copy(update={"status": ThesisStatus.ACTIVE}))
    pipe.run_reassess(as_of=date(2026, 10, 16), thesis_ids=[sib.thesis_id])
    assert "identity under review" not in _f10(pipe, sib.thesis_id)[1]


def test_a_reassess_reads_the_source_tier_the_sources_now_give(tmp_path: Path) -> None:
    """A reassess kept the tier its previous version recorded: a change in sources.toml never
    reached it. NEGATIVE pin: an engine built without the pipeline's sources keeps the recorded
    tier, and says nothing it cannot know."""
    pipe = make_pipeline(tmp_path)
    src = next(s for s in pipe.sources.values() if s.reliability == "high")
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 9% in Q3 2026."
    art = Hypo("tier", src.publisher, date(2026, 10, 1), [("paragraph", line)])
    ingest(pipe, art.doc(), _x(line, "Memory prices climb", MEM, "memory price",
                               period="Q3 2026", mechanism="pricing_cycle", geography="Global"),
           as_of=AS_OF, source_id=src.id, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()

    def tier() -> str:
        cur = pipe.store.thesis(t.thesis_id)
        assert cur is not None
        v = pipe.store.thesis_version(t.thesis_id, cur.current_version)
        assert v is not None
        return next(f.value for f in v.priority.factors
                    if f.factor_id == "F1_source_reliability")

    assert tier() == "high"
    pipe.sources[src.id] = dataclasses.replace(src, reliability="low")
    pipe.run_reassess(as_of=date(2026, 10, 15), thesis_ids=[t.thesis_id])
    assert tier() == "low"
    pipe.engine.reliability_of = None
    pipe.sources[src.id] = src
    pipe.run_reassess(as_of=date(2026, 10, 16), thesis_ids=[t.thesis_id])
    assert tier() == "low"  # NEGATIVE: no lookup, the recorded tier stands
