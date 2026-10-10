"""Review of PR #703, round 3 — FIX 1 (false contradictions), FIX 2 (over-broad confirmation) and
FIX 3 (a narrow RESEARCH NOW route for a near-term fundamental inflection).

The hypothetical articles are labelled as such and built from the REAL extraction types; the
real-article pins replay the FROZEN model outputs of the 2026-10-10 acceptance runs.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import (
    FIXTURES,
    Hypo,
    claim,
    extraction,
    frozen_output,
    hyp,
    ingest,
    load_document,
    make_pipeline,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import (
    Direction,
    LinkRole,
    RelationType,
    ResearchAction,
    RunStatus,
    Thesis,
)

AS_OF = date(2026, 9, 30)  # 4Q26 is the next quarter; 3Q26 the one just measured

#: AUTHENTIC fixtures frozen from the 2026-10-10 acceptance runs (registries contradiction-15 and
#: overlap-15). Each second article is the extraction the run made WITH the first article's
#: theses in the registry (its alignment candidates are part of the request).
SA_MORA = FIXTURES / "semianalysis_moratoriums"
CALM_AFTER = FIXTURES / "jpm_calm_index_after_semianalysis"
SA_GLM = FIXTURES / "semianalysis_glm53"
TF_AFTER = FIXTURES / "trendforce_4q26_after_semianalysis"


def _replay_pair(tmp_path: Path, first: tuple[Path, date, str],
                 second: tuple[Path, date, str]) -> tuple[Pipeline, str, str]:
    """Two runs, as the acceptance case ran them: the first article, then the second a later
    week. Returns the pipeline and the two article ids."""
    pipe = make_pipeline(tmp_path, sec_dirs=(first[0], second[0]))
    ids = []
    for n, (d, as_of, channel) in enumerate((first, second), 1):
        pipe.start_run("fixture", as_of=as_of, run_id=f"R-{n}-fixture")
        res = ingest(pipe, load_document(d), frozen_output(d, "extraction.json"), as_of=as_of,
                     source_id=channel, completeness=frozen_output(d, "completeness.json"))
        pipe.finish_run(RunStatus.SUCCEEDED)
        assert res.article_id is not None, res.status
        ids.append(res.article_id)
    return pipe, ids[0], ids[1]


def _from(pipe: Pipeline, article_id: str, node: str) -> list[Thesis]:
    return [t for t in pipe.store.theses() if t.key_node == node
            and {c.article_id for c in pipe.store.contributions(thesis_id=t.thesis_id)}
            == {article_id}]


# --- FIX 1: the real behind-the-meter / utilities regression -----------------------------------

def test_semianalysis_behind_the_meter_vs_jpm_utilities_is_related_never_a_contradiction(
        tmp_path: Path) -> None:
    """Observed 2026-10-10 (round 2): SemiAnalysis's behind-the-meter thesis (power_grid |
    demand_volume_shift | positive) was CHALLENGED by J.P. Morgan's utilities thesis (power_grid |
    policy_regulation | negative) — same node, opposite directions — and re-versioned WEAKER. A fall
    in utility share prices does not contradict rising demand for on-site generation: RELATED, no
    CONTRADICTS evidence, no new version, no downgrade."""
    pipe, sa, jpm = _replay_pair(tmp_path, (SA_MORA, date(2026, 9, 15), "semianalysis"),
                                 (CALM_AFTER, date(2026, 10, 2), "jpm_tmt"))
    node = "ai_infrastructure.power_grid"
    (btm,) = _from(pipe, sa, node)
    assert btm.key_direction is Direction.POSITIVE and "onsite_generation" in btm.key_segment
    utilities = _from(pipe, jpm, node)
    assert utilities and all(u.key_direction is Direction.NEGATIVE for u in utilities)
    assert all("grid_utilities" in u.key_segment for u in utilities)
    # the incumbent is untouched: one version, its own links only, no challenge event
    assert btm.current_version == 1
    assert {lk.first_version for lk in pipe.store.links(btm.thesis_id)} == {1}
    assert not [lk for lk in pipe.store.links(btm.thesis_id) if lk.role is LinkRole.CONTRADICTS]
    assert not [e for e in pipe.store.events(thesis_id=btm.thesis_id)
                if e.event_type in ("CHALLENGED", "DOWNGRADED")]
    pair = [r for r in pipe.store.relations(btm.thesis_id)
            if {r.from_thesis, r.to_thesis} & {u.thesis_id for u in utilities}]
    assert pair and all((r.relation, r.evidence_role) == (RelationType.RELATED, "RELATED")
                        for r in pair)
    assert all("a different mechanism" in r.reason and "a different segment" in r.reason
               for r in pair)
    assert not [r for r in pipe.store.relations() if r.relation is RelationType.COMPETING]


# --- FIX 2: the real SemiAnalysis / TrendForce memory pair -------------------------------------

def test_semianalysis_sparse_attention_and_trendforce_memory_stay_separate_as_adjacent(
        tmp_path: Path) -> None:
    """Round 2 merged TrendForce's enterprise-SSD / NAND pricing evidence into SemiAnalysis's
    sparse-attention DRAM / HBM thesis as a confirmation. They reinforce a broad AI-memory view
    without confirming each other: separate theses (the SEGMENT is part of identity), linked as
    ADJACENT SUPPORT, no TrendForce evidence on the SemiAnalysis thesis."""
    pipe, sa, tf = _replay_pair(tmp_path, (SA_GLM, date(2026, 9, 28), "semianalysis"),
                                (TF_AFTER, date(2026, 9, 30), "trendforce"))
    node = "ai_infrastructure.memory"
    (sa_mem,) = _from(pipe, sa, node)
    tf_mem = _from(pipe, tf, node)
    assert sa_mem.key_segment == "dram_hbm"
    assert tf_mem and all("nand_ssd" in t.key_segment for t in tf_mem)
    assert sa_mem.current_version == 1  # never versioned by the other publisher's evidence
    for t in tf_mem:
        (r,) = [r for r in pipe.store.relations(sa_mem.thesis_id)
                if {r.from_thesis, r.to_thesis} == {sa_mem.thesis_id, t.thesis_id}]
        assert (r.relation, r.evidence_role) == (RelationType.SIBLING, "ADJACENT_SUPPORT")


# --- FIX 3: the real TrendForce 4Q26 article -----------------------------------------------------

def test_the_real_trendforce_4q26_pricing_forecast_takes_the_inflection_route(
        tmp_path: Path) -> None:
    """TrendForce (an industry data report: a price tracker forecasting the price it tracks)
    projects 4Q26 contract prices to rise, states the pricing step itself and names the sectors
    exposed — RESEARCH NOW by the inflection route, with no dislocation or dated catalyst. The
    SemiAnalysis memory thesis beside it does NOT qualify: its changing figure is a workload
    metric (prompt-token reuse), not a fundamental."""
    pipe, sa, tf = _replay_pair(tmp_path, (SA_GLM, date(2026, 9, 28), "semianalysis"),
                                (TF_AFTER, date(2026, 9, 30), "trendforce"))
    node = "ai_infrastructure.memory"
    pricing = [t for t in _from(pipe, tf, node) if t.key_mechanism == "pricing_cycle"]
    assert len(pricing) == 1
    v = pipe.store.thesis_version(pricing[0].thesis_id, 1)
    assert v is not None
    f12 = next(f for f in v.priority.factors if f.factor_id == "F12_fundamental_inflection")
    assert f12.value == "qualifies"
    assert v.priority.research_action is ResearchAction.RESEARCH_NOW
    assert "near-term fundamental inflection" in v.priority.rules_fired[0]
    disl = next(f for f in v.priority.factors if f.factor_id == "F7_dislocation_or_catalyst")
    assert disl.claim_ids == ()  # no dislocation / catalyst counted: the route did the work
    credible = [pipe.store.claim(c) for c in f12.claim_ids]
    assert credible and all(c is not None and c.period == "4Q26"
                            and c.epistemic.value == "forecast"
                            and c.attributed_source_text == "publisher_own" for c in credible)
    (sa_mem,) = _from(pipe, sa, node)
    sv = pipe.store.thesis_version(sa_mem.thesis_id, 1)
    assert sv is not None
    assert next(f for f in sv.priority.factors
                if f.factor_id == "F12_fundamental_inflection").value == "absent"
    # the dashboard's FIRST VIEW says why, in plain words: the route and its research question
    import re

    from bs4 import BeautifulSoup

    from vinci.theme_intelligence.report import build_dashboard, render_dashboard_html

    d = build_dashboard(pipe.store, "R-2-fixture", cards={}, generated="t")
    row = next(r for rs in d.categories.values() for r in rs
               if r.thesis_id == pricing[0].thesis_id)
    assert "a credible near-term change in a fundamental" in row.why_action
    assert "already reflect" in row.why_action and "4Q26" in row.why_action
    soup = BeautifulSoup(render_dashboard_html(d), "html.parser")
    for el in soup.select(".aud, .auditbar, script, input"):
        el.decompose()
    first = soup.get_text(" ", strip=True)
    assert row.why_action in first
    assert not re.search(r"\bC-[0-9a-f]{6,}", first)


# --- FIX 3: the near-term fundamental inflection route -----------------------------------------

FORECAST = ("Our contract price tracker projects conventional DRAM contract prices to rise "
            "10–15% QoQ in 4Q26 as AI servers absorb supply.")
MEASURED = "DRAM contract prices rose 18% QoQ in 3Q26 on server demand."
#: a measured fundamental that states NO change — "contract" here is the noun, never a contraction
UNCHANGED = "DRAM contract prices stood at $3.10 per gigabit in 3Q26."
TECHNICAL = ("When concurrency increases from 8 to 16 requests, the share of prompt tokens "
             "reused from GPU memory falls from 90.3% to 54.8% in 4Q26.")
LONG = "Our tracker projects DRAM contract prices to rise 40% by 2030 as AI servers absorb supply."


def _forecast_claim(cid: str = "c1", quote: str = FORECAST, *, source: str | None = None,
                    period: str = "4Q26", value: float = 10, value_text: str = "10–15%",
                    epistemic: str = "forecast", kind: str = "forecast") -> dict[str, Any]:
    return claim(cid, "b001", quote.rstrip("."), f"DRAM contract prices {value_text} {period}",
                 kind=kind, epistemic=epistemic, metric="conventional DRAM contract price change",
                 value=value, value_text=value_text, unit="% QoQ", period=period,
                 scope="conventional DRAM", source=source)


def _priced(claims: list[dict[str, Any]], *, source_steps: bool = True,
            support: list[str] | None = None) -> dict[str, Any]:
    steps = [{"step": "pricing", "text": "contract prices rise", "provenance": "source_stated",
              "claim_ids": ["c1"]}] if source_steps else [
        {"step": "pricing", "text": "prices may rise", "provenance": "model_inference"}]
    x = extraction(claims, [hyp(
        "h1", "AI servers lift DRAM contract prices", node="ai_infrastructure.memory",
        mechanism="pricing_cycle", geography="Global",
        supporting=support or [c["local_id"] for c in claims], step_list=steps,
        sectors=[("DRAM", "b001", "DRAM contract prices")])])
    return x


#: the ARTICLE CLASS comes from the channel's configuration (or the page), never from the model:
#: TrendForce's channel is an industry data report; a manual URL is not
DATA_REPORT, COMMENTARY = "trendforce", "manual"


def _f12(tmp_path: Path, blocks: list[str], x: dict[str, Any],
         channel: str) -> tuple[str, str, str]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=AS_OF)
    art = Hypo(slug="inflection", publisher="Hypo Research A", published=AS_OF,
               blocks=[("paragraph", b) for b in blocks])
    ingest(pipe, art.doc(), x, as_of=AS_OF, source_id=channel)
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    f = next(f for f in v.priority.factors if f.factor_id == "F12_fundamental_inflection")
    return f.value, v.priority.research_action.value, " ".join(v.priority.rules_fired)


def test_a_price_trackers_own_near_term_forecast_with_stated_economics_qualifies(
        tmp_path: Path) -> None:
    value, action, trace = _f12(tmp_path, [FORECAST], _priced([_forecast_claim()]),
                                DATA_REPORT)
    assert value == "qualifies"
    assert action == ResearchAction.RESEARCH_NOW.value
    assert "near-term fundamental inflection" in trace
    # the research question is composed from structured fields — one unit, never "% %"
    assert ("already reflect conventional DRAM contract price change of 10–15% QoQ in 4Q26?"
            in trace)


@pytest.mark.parametrize(("why", "blocks", "x", "channel", "want"), [
    ("a commentator's forecast alone",
     [FORECAST], _priced([_forecast_claim(source="TrendForce")]), COMMENTARY, "not credible"),
    ("the tracker's own forecast outside a data-report channel",
     [FORECAST], _priced([_forecast_claim()]), COMMENTARY, "not credible"),
    ("no source-stated economics",
     [FORECAST], _priced([_forecast_claim()], source_steps=False), DATA_REPORT, "incomplete"),
    ("long-range, not 2-4 quarters",
     [LONG], _priced([_forecast_claim(quote=LONG, period="2030", value=40, value_text="40%")]),
     DATA_REPORT, "absent"),
    ("a technical metric, not a fundamental (observed 2026-10-10, SemiAnalysis)",
     [TECHNICAL], _priced([_forecast_claim(quote=TECHNICAL, value=54.8,
                                           value_text="90.3% to 54.8%", epistemic="actual",
                                           kind="metric")]), DATA_REPORT, "absent"),
    ("corroborated only by a measured fact that states no change",
     [FORECAST, UNCHANGED],
     _priced([_forecast_claim(source="TrendForce"),
              claim("c2", "b002", UNCHANGED.rstrip("."), "DRAM $3.10/Gb", value=3.1,
                    value_text="$3.10", unit="USD per gigabit", period="3Q26")]),
     COMMENTARY, "not credible"),
])
def test_the_inflection_route_refuses(tmp_path: Path, why: str, blocks: list[str],
                                      x: dict[str, Any], channel: str, want: str) -> None:
    value, action, trace = _f12(tmp_path, blocks, x, channel)
    assert value == want, why
    assert action != ResearchAction.RESEARCH_NOW.value, why


def test_a_commentators_forecast_corroborated_by_a_measured_change_qualifies(
        tmp_path: Path) -> None:
    x = _priced([_forecast_claim(source="TrendForce"),
                 claim("c2", "b002", MEASURED.rstrip("."), "DRAM +18% QoQ 3Q26", value=18,
                       value_text="18%", unit="% QoQ", period="3Q26")])
    value, action, trace = _f12(tmp_path, [FORECAST, MEASURED], x, COMMENTARY)
    assert value == "qualifies" and "corroborated by a measured observation" in trace


# --- FIX 1: what separates a direct contradiction from a related claim, one dimension at a time --

DRAM_UP = "DRAM contract prices rose 15% in 1Q26 in the US as AI servers absorbed supply."


def _memory_hyp(text: str, *, direction: str, geography: str = "US", period: str = "1Q26",
                node: str = "ai_infrastructure.memory",
                mechanism: str = "pricing_cycle") -> tuple[Hypo, dict[str, Any]]:
    art = Hypo(slug=f"mem-{direction}-{geography}-{period}-{node[-6:]}".lower().replace(" ", ""),
               publisher="Hypo Research A", published=date(2026, 3, 2),
               blocks=[("paragraph", text)])
    x = extraction([claim("c1", "b001", text.rstrip("."), "memory price change", value=15,
                          value_text="15%", unit="%", period=period)],
                   [hyp("h1", f"memory pricing {direction}", node=node, mechanism=mechanism,
                        direction=direction, geography=geography, supporting=["c1"])])
    return art, x


@pytest.mark.parametrize(("why", "text", "kw", "want", "says"), [
    ("the same claim predicted the opposite way",
     "DRAM contract prices fell 15% in 1Q26 in the US as hyperscalers paused orders.", {},
     RelationType.COMPETING, "a direct contradiction"),
    ("a different geography",
     "DRAM contract prices fell 15% in 1Q26 in Europe as hyperscalers paused orders.",
     {"geography": "Europe"}, RelationType.RELATED, "a different geography"),
    ("no overlapping timeframe",
     "DRAM contract prices will fall 15% in 2028 in the US as new fabs come online.",
     {"period": "2028"}, RelationType.RELATED, "no overlapping timeframe"),
    ("a different segment",
     "NAND flash contract prices fell 15% in 1Q26 in the US as hyperscalers paused orders.", {},
     RelationType.RELATED, "a different segment"),
])
def test_only_the_same_claim_predicted_the_opposite_way_is_a_contradiction(
        tmp_path: Path, why: str, text: str, kw: dict[str, str], want: RelationType | None,
        says: str) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=date(2026, 3, 2))
    a, xa = _memory_hyp(DRAM_UP, direction="positive")
    ingest(pipe, a.doc(), xa, as_of=date(2026, 3, 2), publisher=a.publisher)
    (inc,) = pipe.store.theses()
    b, xb = _memory_hyp(text, direction="negative", **kw)
    ingest(pipe, b.doc(), xb, as_of=date(2026, 3, 2), publisher="Hypo Research B")
    rels = pipe.store.relations(inc.thesis_id)
    after = pipe.store.thesis(inc.thesis_id)
    assert after is not None
    if want is RelationType.COMPETING:
        assert [(r.relation, r.evidence_role) for r in rels] == [
            (RelationType.COMPETING, "CONTRADICTION")], why
        assert after.current_version == 2, why
    else:
        assert [(r.relation, r.evidence_role) for r in rels] == [(want, "RELATED")], why
        assert after.current_version == 1, why  # never re-versioned WEAKER
    assert all(says in r.reason for r in rels), why


def test_two_unclassified_theses_are_never_a_contradiction_by_key(tmp_path: Path) -> None:
    """`other` | `other` theses share a key shape but not a claim: opposite directions on them
    are RELATED, never a challenge."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=date(2026, 3, 2))
    a, xa = _memory_hyp(DRAM_UP, direction="positive", node="other", mechanism="other")
    ingest(pipe, a.doc(), xa, as_of=date(2026, 3, 2), publisher=a.publisher)
    (inc,) = pipe.store.theses()
    b, xb = _memory_hyp("DRAM contract prices fell 15% in 1Q26 in the US as hyperscalers paused "
                        "orders.", direction="negative", node="other", mechanism="other")
    ingest(pipe, b.doc(), xb, as_of=date(2026, 3, 2), publisher="Hypo Research B")
    rels = pipe.store.relations(inc.thesis_id)
    assert not [r for r in rels if r.relation is RelationType.COMPETING]
    after = pipe.store.thesis(inc.thesis_id)
    assert after is not None and after.current_version == 1

