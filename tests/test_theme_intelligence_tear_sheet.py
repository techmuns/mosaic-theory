"""The thesis page as a TEAR SHEET (operator, 2026-10-15: "always consider the whole thesis page, as
our goal is to make the views how an expert would look at").

- The first band holds the thesis, its distinct key figures, what changed and the decision (why
  this action, timing, the next step) — read before anything else.
- Who is exposed: an implied company is ONE ROW, grouped under the step it rests on — the step,
  and so its condition, said once per group, never once per company.
- Open review findings are one line each on the thesis page, opening to the review's words; the
  Review tab keeps the full item.
- Nothing is dropped: every folded line is in the page, one click away.

Registries are the SYNTHETIC stress weeks (`theme_intelligence_stress`) and the hypothetical
enrichment thesis of `test_theme_intelligence_enrichment_basis`; the SEC data is the frozen
J.P. Morgan subset.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

import tests.test_theme_intelligence_enrichment_basis as eb
from tests.theme_intelligence_stress import build_stress_registry
from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import desk
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import RunStatus


def _soup(p: Path) -> BeautifulSoup:
    return BeautifulSoup(p.read_text(), "html.parser")


@pytest.fixture(scope="module")
def stress(tmp_path_factory: pytest.TempPathFactory) -> tuple[Pipeline, Path, Any]:
    root = tmp_path_factory.mktemp("tear")
    pipe, _stats = build_stress_registry(root / "reg", weeks=6)
    run = max((r for r in pipe.store.runs() if r.mode == "scan"), key=lambda r: r.started_at)
    out = Path(write_run_outputs(pipe.store, run.run_id, root / "out")["dir"])
    return pipe, out, run


def test_the_first_band_holds_the_thesis_its_figures_what_changed_and_the_decision(
        stress: tuple[Pipeline, Path, Any]) -> None:
    _pipe, out, _run = stress
    pages = sorted((out / "theses").glob("*.html"))
    assert pages
    for p in pages:
        page = _soup(p)
        first = page.select_one("main section.panel")
        assert first is not None and "sheet" in first.get("class", []), p.name
        assert first.select_one(".sheetmain h2").get_text() == "The thesis"  # type: ignore[union-attr]
        why = first.select_one("aside.decide h2")
        assert why is not None and why.get_text().startswith("Why "), p.name
        assert "What changed" in [h.get_text() for h in first.select("h3")]
        # NEGATIVE: the figures live in the band only — no separate "strongest figures" panel
        assert all(n.find_parent("section", class_="sheet") for n in page.select(".nums"))
        assert "The strongest figures" not in [h.get_text() for h in page.select("h2")]
        assert len(page.select(".sheet .nums .num")) <= 3  # a tear sheet's key figures: three
    assert any(len(_soup(p).select(".sheet .nums .num")) == 3 for p in pages)


def test_review_findings_are_one_line_on_the_thesis_page_and_full_on_review(
        stress: tuple[Pipeline, Path, Any]) -> None:
    pipe, out, run = stress
    d = desk.Desk(pipe.store, run, cards={}, generated="")
    per: dict[str, int] = defaultdict(int)
    for f in d.open:
        per[f.thesis_id] += 1
    assert per
    for tid, n in per.items():
        sec = _soup(out / "theses" / f"{tid}.html").select_one("#review")
        assert sec is not None
        items = sec.select("ul.rvcompact > li.rvi")
        assert len(items) == n
        for li in items:  # one line, opening to the review's words and the record
            body = li.select_one("details")
            assert body is not None and body.select_one("summary") is not None
            assert body.select_one(".said") is not None
            assert body.select_one("a[href*='cards/']") is not None
    # NEGATIVE: the Review tab keeps the full item, unfolded
    full = _soup(out / "review.html").select("#rv li.rvi")
    assert full and all(li.select_one(":scope > .said") is not None for li in full)


def test_key_figures_are_three_distinct_ones(tmp_path: Path) -> None:
    """POSITIVE: one value and label stated twice ("$26 billion · DTC cash-pay market size", at
    peak / at its peak — the pilot, 2026-10-15) is ONE figure on the tear sheet. NEGATIVE: the
    same value under another label stays a figure of its own."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=date(2026, 10, 1))
    lines = ["The DTC cash-pay market could reach $26 billion at peak.",
             "In total the DTC cash-pay market could reach $26 billion at its peak.",
             "Branded GLP-1 sales could reach $26 billion next year."]
    art = Hypo("figures", "Test Publisher", date(2026, 9, 29), [("paragraph", t) for t in lines])
    cs = [claim(f"c{i}", f"b00{i + 1}", t.rstrip("."), t.rstrip("."), kind="forecast",
                epistemic="forecast", metric=m, value=26, value_text="$26 billion", unit="USD bn",
                period=per)
          for i, (t, m, per) in enumerate(zip(lines, (
              "DTC cash-pay market size", "DTC cash-pay market size", "branded GLP-1 sales"),
              ("at peak", "at its peak", "next year"), strict=True))]
    x = extraction(cs, [hyp("h1", "Cash-pay access unlocks biopharma demand",
                            node="healthcare", mechanism="demand_volume_shift",
                            supporting=["c0", "c1", "c2"])])
    ingest(pipe, art.doc(), x, as_of=date(2026, 10, 1), publisher=art.publisher)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    (t,) = pipe.store.theses()
    nums = _soup(out / "theses" / f"{t.thesis_id}.html").select(".sheet .nums .num")
    shown = [(n.select_one("b").get_text(), n.select_one(".lbl").get_text())  # type: ignore[union-attr]
             for n in nums]
    assert len(shown) == len(set(shown)) == 2
    assert {lbl for _v, lbl in shown} == {"DTC cash-pay market size", "branded GLP-1 sales"}


def _enriched(tmp_path: Path, answer: dict[str, Any]) -> tuple[BeautifulSoup, Any]:
    saved = eb.ANSWER
    eb.ANSWER = answer
    try:
        pipe, tid, _http = eb._pipe(tmp_path)
    finally:
        eb.ANSWER = saved
    out = Path(write_run_outputs(pipe.store, pipe.store.runs()[-1].run_id,
                                 tmp_path / "out")["dir"])
    (es,) = pipe.store.enrichments(tid)
    return _soup(out / "theses" / f"{tid}.html"), es


def test_an_implied_company_is_one_row_and_its_step_is_said_once(tmp_path: Path) -> None:
    """POSITIVE: Amazon and Alphabet rest on ONE step — one header over two rows; NVIDIA on
    another — a header of its own. NEGATIVE: never a header per company."""
    alphabet = {"name": "Alphabet", "ticker": "GOOGL", "exchange": "Nasdaq", "direction": "hurt",
                "step_id": "s03.1", "business": "online advertising and cloud computing",
                "exposure": "Google Cloud buys memory for its servers.",
                "revenue_line": "Google Cloud", "revenue_model": "usage_based"}
    page, es = _enriched(tmp_path, {"companies": [*eb.ANSWER["companies"], alphabet]})
    hypo = page.select_one(".expo .hypo")
    assert hypo is not None
    heads = hypo.select("h4.cond")
    rows = hypo.select("details.hrow")
    assert len(rows) == len(es.candidates) == 3 and len(heads) == 2
    under = {h.get_text(" ", strip=True)[:30]: [r.select_one("summary b").get_text()  # type: ignore[union-attr]
                                                for r in h.find_next_sibling("div").select(
                                                    "details.hrow")] for h in heads}
    assert sorted(map(sorted, under.values())) == [["Alphabet", "Amazon"], ["NVIDIA"]]


def test_nothing_folded_is_dropped(tmp_path: Path) -> None:
    """Every proposal's rationale, listing, basis and the filing's own sentence are in the page,
    one click away — the tear sheet folds, it never deletes."""
    page, es = _enriched(tmp_path, eb.ANSWER)
    text = page.select_one(".expo .hypo").get_text(" ")  # type: ignore[union-attr]
    for c in es.candidates:
        assert c.rationale in text
        for q in c.basis_quote:
            assert q in text
    assert eb.NVDA_SOURCE in text
