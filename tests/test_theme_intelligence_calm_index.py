"""Acceptance: J.P. Morgan "A calm index, a restless market" (published 2026-10-02, as of
2026-10-10) — the article the first build reduced to a single utilities thesis.

Runs the REAL engine on the AUTHENTIC fixture (an excerpt of the retrieved page, the frozen pass-1
and pass-1b outputs, the real SEC data). Pins are phrasing-independent: record kinds and keys,
verbatim source spans, structured figures, verification records — never LLM-composed text.

What the review requires of this article, and what each test pins:
- the utilities thesis is preserved;
- the central equity-DISPERSION argument is preserved as a MARKET-REGIME record — no stock named,
  no buy thesis forced, not dropped for naming no stock — carrying ~43% of constituents above
  their 200-day average, 75% in mid-August, a 3-month implied correlation of 11.2 against a
  long-run average of 41, and the source's implication for sector / thematic selection;
- every material reported figure is captured (the frozen FULL-article ledger) — see
  test_theme_intelligence_corrections for the ledger pins;
- both authors: Kriti Gupta (JSON-LD + byline) and Nick Roberts (byline microdata), with the
  metadata disagreement recorded.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.theme_intelligence_support import CALM_AS_OF, CALM_DIR, ingest_calm, make_pipeline
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import (
    Direction,
    LinkRole,
    RunStatus,
    Thesis,
    ThesisKind,
    ThesisVersion,
)
from vinci.theme_intelligence.verify import EARNINGS_STEPS, is_market_reaction


@pytest.fixture(scope="module")
def calm(tmp_path_factory: pytest.TempPathFactory) -> Pipeline:
    pipe = make_pipeline(tmp_path_factory.mktemp("calm"), sec_dirs=(CALM_DIR,))
    pipe.start_run("article", as_of=CALM_AS_OF, window_from=CALM_AS_OF, window_to=CALM_AS_OF)
    res = ingest_calm(pipe)
    assert res.status == "PROCESSED", res.note
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


def _records(pipe: Pipeline) -> list[tuple[Thesis, ThesisVersion]]:
    out = []
    for t in pipe.store.theses():
        v = pipe.store.thesis_version(t.thesis_id, t.current_version)
        assert v is not None
        out.append((t, v))
    return out


def _regime(pipe: Pipeline) -> tuple[Thesis, ThesisVersion]:
    rs = [(t, v) for t, v in _records(pipe) if t.kind is ThesisKind.MARKET_REGIME]
    assert len(rs) == 1, [t.title for t, _ in rs]
    return rs[0]


def _utilities(pipe: Pipeline) -> tuple[Thesis, ThesisVersion]:
    us = [(t, v) for t, v in _records(pipe) if t.kind is ThesisKind.INVESTMENT_THESIS
          and any("utilit" in s.name.lower() for s in v.content.s05_affected.sector_exposures)]
    assert len(us) == 1, [t.title for t, _ in _records(pipe)]
    return us[0]


def _linked_figures(pipe: Pipeline, tid: str) -> set[str]:
    return {(c.value_text or "").lstrip("~").replace("about ", "")
            for lk in pipe.store.links(tid) if lk.role in (LinkRole.SUPPORTS,
                                                          LinkRole.DISLOCATION,
                                                          LinkRole.CATALYST)
            if (c := pipe.store.claim(lk.claim_id)) is not None and c.span_verified}


def test_both_arguments_survive_as_two_records(calm: Pipeline) -> None:
    recs = _records(calm)
    assert len(recs) == 2
    t, _ = _utilities(calm)
    assert t.key_direction is Direction.NEGATIVE
    r, _ = _regime(calm)
    assert (r.key_node, r.key_mechanism) == ("macro_market", "dispersion_selection")


def test_the_dispersion_record_carries_the_breadth_and_correlation_figures(
        calm: Pipeline) -> None:
    r, v = _regime(calm)
    figs = _linked_figures(calm, r.thesis_id)
    for want in ("43%", "75%", "11.2", "41"):
        assert want in figs, (want, sorted(figs))
    # no stock is named for it and none is invented — the exposure is the source's own words
    assert v.content.s05_affected.companies == ()
    quotes = " ".join(s.quote.lower() for s in v.content.s05_affected.sector_exposures)
    assert "sector" in quotes and "thematic" in quotes


def test_the_dispersion_record_is_not_forced_into_an_earnings_thesis(calm: Pipeline) -> None:
    _, v = _regime(calm)
    f4 = next(f for f in v.priority.factors if f.factor_id == "F4_profit_transmission")
    assert f4.value.startswith("n/a")
    earnings = [s for s in v.content.s03_transmission if s.step == "listed_earnings"]
    assert earnings and earnings[0].text.startswith("NOT APPLICABLE")


def test_the_utilities_price_fall_is_a_market_reaction_not_a_mechanism(calm: Pipeline) -> None:
    _, v = _utilities(calm)
    steps = v.content.s03_transmission
    assert any(s.step == "market_reaction" for s in steps)
    assert not [s for s in steps if s.step in EARNINGS_STEPS and is_market_reaction(s.text)]
    f4 = next(f for f in v.priority.factors if f.factor_id == "F4_profit_transmission")
    assert "market-reaction step(s) NOT counted" in f4.note


def test_both_authors_are_credited_and_the_disagreement_recorded(calm: Pipeline) -> None:
    art = calm.store.article(_records(calm)[0][1].content.s09_sources[0].article_id)
    assert art is not None
    assert [a.name for a in art.authors][:2] == ["Kriti Gupta", "Nick Roberts"]
    issues = [i for i in calm.store.issues() if i.code == "AUTHOR_METADATA_DISCREPANCY"]
    assert issues and "Nick Roberts" in issues[0].detail


def test_article_date_and_first_detected_are_apart(calm: Pipeline, tmp_path: Path) -> None:
    _, v = _utilities(calm)
    assert v.content.header.latest_article_date is not None
    assert v.content.header.latest_article_date.isoformat() == "2026-10-02"
    assert v.content.header.first_detected == CALM_AS_OF
    out = write_run_outputs(calm.store, calm.store.runs()[-1].run_id, tmp_path / "out")
    html = (tmp_path / "out" / "dashboard.html").read_text()
    assert "Article date 2026-10-02" in html and "first detected by the registry 2026-10-10" in html
    assert "not necessarily new to the market" in html
    assert len(out["cards"]) == 2


def test_the_card_opens_on_a_compact_decision_view_without_engine_codes(
        calm: Pipeline) -> None:
    """Review of PR #703, P2.12 / P2.14: the nine sections stay, in order; the first view is the
    header and 01 / 02 / 06 / 08 in plain words — thesis ids, claim ids, change classes and the
    rule trace only behind the audit toggle — and print carries every field."""
    from bs4 import BeautifulSoup

    from vinci.theme_intelligence.cards import render_html
    from vinci.theme_intelligence.report import card_context

    t, v = _utilities(calm)
    rc = card_context(calm.store, t, v, generated="t")
    web, prn = render_html(v.content, rc), render_html(v.content, rc, print_mode=True)
    soup = BeautifulSoup(web, "html.parser")
    for el in soup.select(".aud, .auditbar, script, input, details.sec"):
        el.decompose()
    first = soup.get_text(" ", strip=True)
    assert "Article date 2026-10-02" in first
    assert "first detected by the registry 2026-10-10" in first
    assert "SOURCE OPINION" in first and "MODEL INFERENCE" in first  # labels stay visible
    for code in (t.thesis_id, "C-", "novelty_unverified", "WATCH (RESEARCH NOW unmet", "NOW all",
                 "F5_", "F7_"):
        assert code not in first, code
    for fid in ("s01_bottom_line", "s02_what_changed", "s06_why_now", "s08_decision"):
        assert f'<section class="sec" data-field="{fid}">' in web
    # print: everything open, the audit content included
    assert v.priority.rules_fired[0][:60] in prn and t.thesis_id in prn
    assert "<details>" not in prn


def test_a_figure_prints_its_unit_once(calm: Pipeline, tmp_path: Path) -> None:
    """Observed 2026-10-10: the regime card's evidence table printed "~43% %" and "75% %" — the
    unit appended to a written value that already carried it. Rendered end to end (HTML, print,
    Markdown); the stored card still keeps value and unit as separate fields."""
    out = write_run_outputs(calm.store, calm.store.runs()[-1].run_id, tmp_path / "out")
    texts = [p.read_text() for p in (tmp_path / "out" / "cards").iterdir()
             if p.suffix in (".md", ".html")]
    assert out["cards"] and texts
    joined = "\n".join(texts)
    assert "% %" not in joined and "%</b> %" not in joined
    rows = [r for _, v2 in _records(calm) for r in v2.content.s04_key_evidence
            if r.value_text and "%" in r.value_text]
    assert rows and all(r.unit for r in rows)  # the structured unit is kept
    assert any(r.value_text in joined for r in rows)


def test_the_excerpt_ledger_has_no_open_figure(calm: Pipeline) -> None:
    av = calm.store.article_versions(_records(calm)[0][1].content.s09_sources[0].article_id)[-1]
    reps = calm.store.completeness(av.version_id)
    assert reps and reps[-1].pass_ran
    assert reps[-1].uncaptured == ()
    assert reps[-1].unaccounted_blocks == ()
