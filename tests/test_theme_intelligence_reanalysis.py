"""RE-ANALYSIS (`Pipeline.run_reanalyse`, `reanalyse`): articles already held, analysed again under
the current taxonomy, the thesis an earlier one merged RETIRED (operator, 2026-10-14 — the pilot's
Alzheimer thesis had absorbed a cash-pay article, both keyed `healthcare`).

Offline: HYPOTHETICAL articles (invented text on the reserved `.test` domain); the first analysis
and the re-analysis are extractions in the REAL type. The real run is in the build record.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import RunStatus, ThesisStatus

AS_OF = date(2026, 10, 14)
ALZ = ("Alzheimer's drug sales could grow 26% in 2026.",)
CASH = ("Direct-to-consumer cash-pay drug sales rose 26% in 2026.",)


def _x(line: str, title: str, node: str, metric: str, extra: list[dict[str, Any]] | None = None
       ) -> dict[str, Any]:
    return extraction([claim("c1", "b001", line.rstrip("."), title, metric=metric, value=26,
                             value_text="26%", unit="%", period="2026")],
                      [hyp("h1", title, node=node, mechanism="demand_volume_shift",
                           supporting=["c1"]), *(extra or [])])


def _merged(tmp_path: Path) -> tuple[Pipeline, dict[str, str], str]:
    """The pilot's shape before healthcare had children: two articles, one key, one thesis."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    ids: dict[str, str] = {}
    for slug, lines, title, metric in (
            ("alz", ALZ, "Alzheimer's drug innovation opens a large market", "Alzheimer sales"),
            ("cash", CASH, "Healthcare demand rises", "cash-pay sales")):
        art = Hypo(slug, "Test Publisher", date(2026, 9, 14 if slug == "alz" else 29),
                   [("paragraph", t) for t in lines])
        r = ingest(pipe, art.doc(), _x(lines[0], title, "healthcare", metric), as_of=AS_OF,
                   publisher=art.publisher)
        assert r.article_id is not None
        ids[slug] = r.article_id
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    assert t.current_version == 2  # one key: the cash-pay article merged into the Alzheimer one
    return pipe, ids, t.thesis_id


#: the re-analysis under healthcare's children and pharma's segments — the Alzheimer claim is
#: the SAME content as first recorded (its id is), plus a broad root-level hypothesis whose key is
#: the retired thesis's own
def _again(ids: dict[str, str]) -> dict[str, dict[str, Any]]:
    return {
        ids["alz"]: _x(ALZ[0], "Alzheimer's drug innovation opens a large market",
                       "healthcare.pharma_biotech", "Alzheimer sales",
                       [hyp("h2", "Alzheimer's gains ripple across healthcare", node="healthcare",
                            mechanism="demand_volume_shift", supporting=["c1"])]),
        ids["cash"]: _x(CASH[0], "Direct-to-consumer cash-pay access widens drug sales",
                        "healthcare.pharma_biotech", "cash-pay sales"),
    }


def test_reanalysis_splits_a_merged_thesis_and_retires_it_for_good(tmp_path: Path) -> None:
    """POSITIVE: the merged thesis is RETIRED (archived, its key tagged with the run, a RETIRED
    event, its versions kept); the re-analysis makes the Alzheimer thesis (neurology) from the
    Alzheimer article only and the cash-pay thesis (direct-to-consumer) from the cash-pay article
    only. NEGATIVE: a re-analysed hypothesis on the retired thesis's own key makes a NEW thesis
    with a NEW id — the retired one is never updated, reactivated or overwritten; and a claim
    whose content was already stored is kept, not refused as an id with two meanings."""
    pipe, ids, old = _merged(tmp_path)
    old_key = pipe.store.thesis(old).identity  # type: ignore[union-attr]
    run, results = pipe.run_reanalyse(article_ids=[ids["cash"], ids["alz"]], retire=[old],
                                      reason="healthcare sub-categories", as_of=AS_OF,
                                      fixtures=_again(ids))
    assert run.status is RunStatus.SUCCEEDED, [r.status for r in results]
    t0 = pipe.store.thesis(old)
    assert t0 is not None and t0.status is ThesisStatus.ARCHIVED and t0.retired == run.run_id
    assert t0.current_version == 2 and len(pipe.store.thesis_versions(old)) == 2
    assert any(e.event_type == "RETIRED" for e in pipe.store.events(thesis_id=old))
    # every surface reads it as archived, as of this run — the first real run left the desk
    # listing the retired thesis active, at Research Now (the readers knew only ARCHIVED)
    from bs4 import BeautifulSoup

    from vinci.theme_intelligence.report import theses_as_of_run, write_run_outputs

    assert theses_as_of_run(pipe.store, run)[old][0].status is ThesisStatus.ARCHIVED
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    page = BeautifulSoup((out / "theses" / f"{old}.html").read_text(), "html.parser")
    assert "retired — its articles were analysed again" in page.select_one("header").get_text(" ")
    themes = BeautifulSoup((out / "themes.html").read_text(), "html.parser").get_text(" ")
    assert "3 active · 1 archived" in themes
    live = {t.key_segment or t.key_node: t for t in pipe.store.theses() if not t.retired}
    assert set(live) == {"neurology", "direct_to_consumer", "healthcare"}

    def sources(tid: str) -> set[str]:
        return {c.article_id for lk in pipe.store.links(tid)
                if (c := pipe.store.claim(lk.claim_id)) is not None}

    assert sources(live["neurology"].thesis_id) == {ids["alz"]}
    assert sources(live["direct_to_consumer"].thesis_id) == {ids["cash"]}
    # the root-level hypothesis took the retired thesis's bare key: a new thesis, a new id
    root = live["healthcare"]
    assert root.identity == old_key and root.thesis_id != old
    assert old not in [k for k, _t in pipe._registry_context()]  # noqa: SLF001


def test_a_thesis_holding_evidence_from_another_article_is_never_retired(tmp_path: Path) -> None:
    """Retiring a thesis drops nothing only if every article it was built from is analysed
    again. NEGATIVE pin: re-analysing one of its two articles is refused, and nothing changes."""
    pipe, ids, old = _merged(tmp_path)
    with pytest.raises(ValueError, match="holds evidence from"):
        pipe.run_reanalyse(article_ids=[ids["alz"]], retire=[old], reason="test", as_of=AS_OF,
                           fixtures=_again(ids))
    t = pipe.store.thesis(old)
    assert t is not None and not t.retired and t.status is ThesisStatus.ACTIVE
    assert len(pipe.store.theses()) == 1


# --- failures after a retirement (code review of PR #703, 2026-10-14) ---------------------------

def test_an_article_without_its_text_is_refused_before_anything_is_retired(
        tmp_path: Path) -> None:
    """A pulled or exported registry blanks article text: that passed the existence check, the
    theses were retired, THEN "holds no text" was raised — retired with no replacement. Now the
    text is read first. NEGATIVE pin: nothing is retired."""
    from vinci.theme_intelligence.store import Store

    src, ids, old = _merged(tmp_path / "a")
    src.store.export_jsonl(tmp_path / "export")  # the real path: an export blanks the text
    (tmp_path / "b" / "ti").mkdir(parents=True)
    Store.import_jsonl(tmp_path / "export", tmp_path / "b" / "ti" / "registry.db").close()
    pipe = make_pipeline(tmp_path / "b")
    with pytest.raises(ValueError, match="holds no text"):
        pipe.run_reanalyse(article_ids=[ids["cash"], ids["alz"]], retire=[old], reason="test",
                           as_of=AS_OF, fixtures=_again(ids))
    t = pipe.store.thesis(old)
    assert t is not None and not t.retired and t.status is ThesisStatus.ACTIVE


def test_a_failure_after_the_retirement_says_so_and_names_the_run_that_finishes_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An article failing AFTER the retirement left the theses retired while the CLI printed
    "refused:". Now it is ReanalysisIncompleteError naming the run that finishes it — the same
    articles WITHOUT --retire — and that run builds the replacements. Each article is re-analysed
    with no per-document limit (the run budget bounds it): a document first released above the
    $30 default came back BUDGET_HELD."""
    from vinci.theme_intelligence.pipeline import ReanalysisIncompleteError

    pipe, ids, old = _merged(tmp_path)
    real, seen = pipe.process_document, []

    def flaky(*a: Any, **kw: Any) -> Any:
        seen.append(kw.get("cost_limit"))
        if len(seen) == 2:
            raise RuntimeError("API outage")
        return real(*a, **kw)

    monkeypatch.setattr(pipe, "process_document", flaky)
    with pytest.raises(ReanalysisIncompleteError, match="WITHOUT --retire") as exc:
        pipe.run_reanalyse(article_ids=[ids["cash"], ids["alz"]], retire=[old], reason="test",
                           as_of=AS_OF, fixtures=_again(ids))
    assert ids["alz"] in str(exc.value) and ids["cash"] in str(exc.value)
    assert seen == [float("inf"), float("inf")]
    t = pipe.store.thesis(old)
    assert t is not None and t.retired  # retired: said, and finishable
    monkeypatch.setattr(pipe, "process_document", real)
    run, _res = pipe.run_reanalyse(article_ids=[ids["cash"], ids["alz"]], retire=[],
                                   reason="finish", as_of=AS_OF, fixtures=_again(ids))
    assert run.status is RunStatus.SUCCEEDED
    live = {t.key_segment or t.key_node for t in pipe.store.theses() if not t.retired}
    assert {"neurology", "direct_to_consumer"} <= live


def test_a_passage_re_anchored_by_an_earlier_run_is_kept_never_a_clash(tmp_path: Path) -> None:
    """A card line the review finds unsupported is re-anchored to a verbatim passage, minted as a
    claim whose id hashes its content but whose record carries `REANCHOR-<run>`. Re-analysing
    the same version re-anchored the same line and raised StoreIntegrityError AFTER the
    retirement. Now the claim first written is kept. NEGATIVE pin: the first run still mints
    it."""
    from datetime import UTC, datetime

    from vinci.theme_intelligence.schemas import IssueSeverity, VerificationIssue

    lines = ("Imaging scanner shipments rose 26% in 2026.",
             "Hospital outpatient demand for imaging rises sharply this year.")
    title = "Hospital outpatient demand for imaging rises sharply"

    def x() -> dict[str, Any]:
        return extraction([claim("c1", "b001", lines[0].rstrip("."), "Imaging shipments rose 26%",
                                 metric="shipments", value=26, value_text="26%", unit="%",
                                 period="2026")],
                          [hyp("h1", title, node="healthcare", mechanism="demand_volume_shift",
                               supporting=["c1"])])
    pipe = make_pipeline(tmp_path)
    base = pipe._review  # noqa: SLF001

    def flags_bottom_line(card: Any, claims: Any) -> Any:
        out = base(card, claims)
        tid = card.header.thesis_id
        assert pipe.run is not None
        out.issues.append(VerificationIssue(
            issue_id=f"VI-test-{tid}-{len(claims)}-{pipe.run.run_id}", run_id=pipe.run.run_id,
            scope="card_sentence", ref_id=f"{tid}:s01.0", severity=IssueSeverity.BLOCK,
            code="REVIEW_UNSUPPORTED", detail="s01.0: UNSUPPORTED — test",
            created_at=datetime.now(tz=UTC)))
        return out

    pipe.engine.reviewer = flags_bottom_line
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("img", "Test Publisher", date(2026, 10, 1), [("paragraph", t) for t in lines])
    r = ingest(pipe, art.doc(), x(), as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert r.article_id is not None
    minted = [c for c in pipe.store.claims_for_article(r.article_id)
              if c.extraction_id.startswith("REANCHOR-")]
    assert minted
    (t,) = pipe.store.theses()
    run, _res = pipe.run_reanalyse(article_ids=[r.article_id], retire=[t.thesis_id],
                                   reason="test", as_of=AS_OF, fixtures={r.article_id: x()})
    assert run.status is RunStatus.SUCCEEDED
    assert [z for z in pipe.store.theses() if not z.retired]  # a live replacement
    kept = pipe.store.claim(minted[0].claim_id)
    assert kept is not None and kept.extraction_id == minted[0].extraction_id


def test_a_retired_thesis_is_never_re_graded_and_never_counted_as_a_live_action(
        tmp_path: Path) -> None:
    """`reassess` had no retired guard: a later re-read of one of its articles (a version recorded
    FULL now read PARTIAL), or `reassess --thesis`, gave the retired thesis a new version and a
    DOWNGRADED event that the run reported. And the weekly brief counted it — the real re-analysis
    run's dashboard read "1 Research Now" and ranked the retired thesis first. NEGATIVE pin: the
    live theses are still counted and ranked, and the retired one is still in its run's report."""
    from vinci.theme_intelligence.report import _active_rows, build_dashboard

    pipe, ids, old = _merged(tmp_path)
    run, _res = pipe.run_reanalyse(article_ids=[ids["cash"], ids["alz"]], retire=[old],
                                   reason="healthcare sub-categories", as_of=AS_OF,
                                   fixtures=_again(ids))
    t0 = pipe.store.thesis(old)
    assert t0 is not None and t0.retired
    before = len(pipe.store.thesis_versions(old))
    assert pipe.engine.reassess(old, run_id=run.run_id, as_of=AS_OF) is None
    # an analyst correction always writes a version — never on a retired thesis
    from vinci.theme_intelligence.engine import SentenceCorrection

    fix = SentenceCorrection(thesis_id=old, sentence_id="s01.0",
                             text="Alzheimer's drugs could open a large market.", claim_ids=(),
                             reason="test")
    assert pipe.engine.reassess(old, run_id=run.run_id, as_of=AS_OF, corrections=[fix]) is None
    r2, outcomes = pipe.run_reassess(as_of=AS_OF, thesis_ids=[old])
    assert len(pipe.store.thesis_versions(old)) == before and outcomes == []
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="test")
    rows = [r for rs in d.categories.values() for r in rs]
    retired = [r for r in rows if r.thesis_id == old]
    assert retired and retired[0].retired  # still in its run's report, as history
    live = [r for r in rows if not r.retired]
    assert d.kpi["retired"] == 1
    assert d.kpi["research_now"] + d.kpi["watch"] + d.kpi["skip"] == len(live)
    ranked = [r.thesis_id for r in _active_rows(d)]
    assert old not in ranked and set(ranked) == {r.thesis_id for r in live}
    # the desk's This week lists it after every live thesis of its area, with no open-conditions
    # badge (it read first, at Research Now, under a header saying "0 at Research Now")
    from bs4 import BeautifulSoup

    from vinci.theme_intelligence.report import write_run_outputs

    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    page = BeautifulSoup((out / "index.html").read_text(), "html.parser")
    area = next(a for a in page.select("div.area")
                if a.find("a", href=f"theses/{old}.html") is not None)
    order = [x["href"] for x in area.select('a[href^="theses/"]')]
    assert order[-1] == f"theses/{old}.html" and len(order) > 1
