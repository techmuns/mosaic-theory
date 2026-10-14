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
