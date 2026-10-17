"""The reading page's decision panel, and three surface bugs (desk review, 2026-10-17).

Operator: "are the details displayed as per what the team of investment experts will need?" The
panel stated what fell short in the rule's words and never what would change it; the conditions
met and the "when to raise or lower" list were folded below the timing. It now reads as a decision
box: the label and what it means → what is missing, with the evidence behind it → what would
clear it → what would raise or lower it → the next step → the conditions met and the timing.

The bugs: 02 WHAT CHANGED's closing note read "showing 6 of 17 pieces of evidence from — the rest
are in 04 KEY EVIDENCE" (its article id is audit-only); the dated-evidence lines read identically
(their periods were audit-only); Uploads still said "push before Monday 03:00 UTC" (the weekly run
is started by hand since #729).

The committed J.P. Morgan fixtures (frozen model output), rendered end to end.
"""

from __future__ import annotations

import dataclasses
import re
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import (
    CALM_AS_OF,
    CALM_DIR,
    JPM_AS_OF,
    ingest_calm,
    ingest_jpm,
    make_pipeline,
)
from vinci.theme_intelligence import desk
from vinci.theme_intelligence.config import CURRENT_OBSERVATION_DAYS
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.priority import _fundamental_change
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import RunStatus, ThesisVersion
from vinci.theme_intelligence.timewindow import observation_date


def _build(root: Path, kind: str) -> tuple[Pipeline, Path]:
    if kind == "jpm":
        pipe = make_pipeline(root)
        pipe.start_run("fixture", as_of=JPM_AS_OF)
        ingest_jpm(pipe)
    else:
        pipe = make_pipeline(root, sec_dirs=(CALM_DIR,))
        pipe.start_run("article", as_of=CALM_AS_OF, window_from=CALM_AS_OF, window_to=CALM_AS_OF)
        ingest_calm(pipe)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe, Path(write_run_outputs(pipe.store, run.run_id, root / "out")["dir"])


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> dict[str, tuple[Pipeline, Path]]:
    return {k: _build(tmp_path_factory.mktemp(k), k) for k in ("jpm", "calm")}


def _current(pipe: Pipeline, tid: str) -> ThesisVersion:
    t = next(x for x in pipe.store.theses() if x.thesis_id == tid)
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    return v


def _page(out: Path, tid: str) -> BeautifulSoup:
    s = BeautifulSoup((out / "theses" / f"{tid}.html").read_text(), "html.parser")
    for x in s.select(".aud"):  # the default view: the audit layer is hidden
        x.decompose()
    return s


def _heads(s: BeautifulSoup) -> list[str]:
    a = s.select_one("aside.decide")
    assert a is not None
    return [x.get_text(" ", strip=True) for x in a.find_all(["h2", "h3", "summary"])
            if x.name != "summary" or "conditions met" in x.get_text()]


def test_a_watch_panel_reads_as_a_decision_box(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """Every WATCH page of both fixtures: the label and what it means first, then what is
    missing, what clears it, the next step, then the conditions met and the timing — in that
    order. What would raise or lower the call sits in the main column under "What would change
    the call", never in the panel (it doubled the panel's height beside a short main column).
    NEGATIVE: a Research Now panel has nothing missing and nothing to clear, and says all its
    conditions are met."""
    watches = raised = 0
    for kind in ("jpm", "calm"):
        pipe, out = built[kind]
        for t in pipe.store.theses():
            v = _current(pipe, t.thesis_id)
            s = _page(out, t.thesis_id)
            heads = _heads(s)
            if v.priority.research_action.value == "RESEARCH NOW":
                assert "What's missing" not in heads and "Clears when" not in heads
                assert re.fullmatch(r"(\d+) of \1 conditions met", next(
                    h for h in heads if h.endswith("conditions met")))
                continue
            watches += 1
            assert heads[0] == "Why Watch · on hold"
            key = s.select_one("aside.decide p.key")
            assert key is not None and key.get_text() == desk._WATCH_KEY["on hold"]
            order = ["What's missing", "Clears when", "Next step"]
            at = [heads.index(h) for h in order]
            met = next(i for i, h in enumerate(heads) if h.endswith("conditions met"))
            assert at == sorted(at) and at[-1] < met < heads.index("Timing")
            assert "Would raise priority" not in heads and "Would lower priority" not in heads
            d = v.content.s08_decision
            if d.raise_priority_if or d.lower_priority_if:
                calls = s.select_one("h3.numh + div.calls")
                assert calls is not None and calls.find_previous("h3").get_text() == (
                    "What would change the call")
                assert calls.find_parent("aside") is None
                h4 = [h.get_text() for h in calls.select("h4")]
                assert h4 and h4 == [x for x in ("Would raise priority", "Would lower priority")
                                     if x in h4]
                raised += 1
    assert watches == 4 and raised


def test_clears_when_names_what_would_clear_each_open_condition(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """The "Clears when" lines are the stored WATCH codes' own (`desk._CLEARS`). The calm-index
    regime's one open condition is its exposure (#736/#737 refuse its index, indicator and
    phrase), so it clears when the source names one."""
    pipe, out = built["calm"]
    v = _current(pipe, "TH-4BC577D53A")
    lines = [li.get_text() for li in _page(out, "TH-4BC577D53A").select("ul.clears li")]
    assert lines == desk.Desk.clears_when(None, v) == [desk._CLEARS["no_exposure"]]  # type: ignore[arg-type]
    # and the line says what an exposure is — not merely whatever the mapping holds
    assert lines[0].startswith("the source names an exposure: a listed company, an ETF")


def test_the_missing_catalyst_says_what_the_evidence_is(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """The panel's evidence lines, under the unmet catalyst condition: J.P. Morgan's AI-adopters
    thesis holds forecasts and two measured observations that are not changes; it says how many
    of each (the forecasts are named under Key figures beside it) — in place of the rule's generic
    detail, which said less."""
    pipe, out = built["jpm"]
    li = next(x for x in _page(out, "TH-A56902FFB6").select("aside.decide li.unmet")
              if x.b.get_text() == desk.CATALYST_GATE)
    assert [(x.get("class"), x.get_text()) for x in li.div.find_all("span")] == [
        (["gap"], "The evidence is 3 forecasts; no measured change in a fundamental from the last "
                  "quarter corroborates them."),
        (["gap"], "None of its 2 measured observations from the last quarter (under Timing) states "
                  "a verified change in a fundamental — earnings, revenue, prices, demand, "
                  "margins and the like.")]


class _Swap:
    """The real store, one claim read back with fields changed (the real type, `model_copy`)."""

    def __init__(self, store: Any, cid: str, **update: Any) -> None:
        self._store, self._cid, self._update = store, cid, update

    def claim(self, cid: str) -> Any:
        c = self._store.claim(cid)
        return c.model_copy(update=self._update) if c is not None and cid == self._cid else c

    def __getattr__(self, name: str) -> Any:
        return getattr(self._store, name)


_A_CHANGE = {"quote": "Revenue rose 9% year over year in the quarter.", "value": 9.0,
             "value_text": "9%", "number_verified": True, "metric": "revenue growth",
             "period": "3Q26"}


def test_the_measured_observations_timing_counts_are_said_to_be_no_change(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """TH-2FFD9B58A8 on the pilot: Timing counted "6 measured observations dated within the last
    quarter" beside a catalyst condition reading only "none verified" (7 of 23 pilot pages). The
    panel now says why they do not carry it, in the rule's own test (`_fundamental_change`) and
    with Timing's own count — on both J.P. Morgan theses of that shape (one observation, two).
    NEGATIVE: once one of them IS a measured change in a fundamental, neither line is said."""
    pipe, out = built["jpm"]
    for tid, n in (("TH-04140F1CA8", 1), ("TH-A56902FFB6", 2)):
        page = _page(out, tid)
        timing = page.select_one("aside.decide .timing").get_text(" ", strip=True)
        m = re.search(r"(\d+) measured observations? dated within the last quarter", timing)
        assert m and int(m[1]) == n, tid
        said = [x.get_text() for x in page.select("aside.decide li.unmet .gap")]
        assert said[-1] == (
            ("Its 1 measured observation from the last quarter (under Timing) states no"
             if n == 1 else f"None of its {n} measured observations from the last quarter "
                            f"(under Timing) states a")
            + " verified change in a fundamental — earnings, revenue, prices, demand, margins "
              "and the like."), tid
        v = _current(pipe, tid)
        current = [x.claim for x in desk.near_term_reading(pipe.store, v).claims
                   if x.timing == "current"]
        assert len(current) == n and not any(_fundamental_change(c) for c in current)
        view: Any = type("V", (), {"store": _Swap(pipe.store, current[0].claim_id, **_A_CHANGE)})()
        assert desk.Desk.evidence_gap(view, v) == [], tid
        # NEGATIVE (code review of #740): under a near-term conflict Timing shows the conflict,
        # not this count — the line no longer points there
        nt = desk.near_term_reading(pipe.store, v)
        conflict = dataclasses.replace(nt, recomputed="not shown" if nt.stored == "yes" else "yes")
        plain: Any = type("V", (), {"store": pipe.store})()
        said = desk.Desk.evidence_gap(plain, v, conflict)
        assert conflict.conflict and said[-1].startswith(
            ("Its 1 measured observation from the last quarter states no",
             f"None of its {n} measured observations from the last quarter states a")), tid


def test_a_measured_change_nothing_corroborates_is_never_called_a_forecast(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """TH-16225B12C4 on the pilot: the one change the inflection reading counted is MEASURED
    ("spending on caffeinated beverages has grown at 6% annually") and uncorroborated, and the
    panel called it "a forecast without a corroborating measurement". It is now named as what it
    is. The same real version, its F12 reading set to that shape. NEGATIVE: when the counted
    change is a forecast (TH-FBDC863613's shape), no such line — the forecasts are counted; and a
    change the reading CREDITS ("qualifies") is never called uncorroborated."""
    pipe, _out = built["jpm"]
    v = _current(pipe, "TH-A56902FFB6")
    cid = next(x.claim.claim_id for x in desk.near_term_reading(pipe.store, v).claims
               if x.timing == "current")
    fc = next(r.claim_id for r in v.content.s04_key_evidence if r.epistemic.value == "forecast")

    def reading(claim: str, value: str = "not credible") -> ThesisVersion:
        pr = v.priority.model_copy(update={"factors": [
            x.model_copy(update={"value": value, "claim_ids": (claim,)})
            if x.factor_id == "F12_fundamental_inflection" else x for x in v.priority.factors]})
        return v.model_copy(update={"priority": pr})

    view: Any = type("V", (), {"store": _Swap(pipe.store, cid, **_A_CHANGE)})()
    assert desk.Desk.evidence_gap(view, reading(cid)) == [
        "Its measured change in a fundamental — revenue growth 9% (3Q26) — is not corroborated: "
        "no other figure measured in the last quarter states a change in a fundamental in its own "
        "words, and the source is not the publisher's own data in an industry data report."]
    assert desk.Desk.evidence_gap(view, reading(cid, "qualifies")) == []
    plain: Any = type("V", (), {"store": pipe.store})()
    said = desk.Desk.evidence_gap(plain, reading(fc))
    assert said and said[0].startswith("The evidence is 3 forecasts; ")
    assert not any("is not corroborated" in x for x in said)


def test_an_incomplete_inflection_keeps_the_rules_own_reason(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """NEGATIVE: when a measured change from the last quarter IS there and only its step to
    profits is missing (F12 "incomplete"), "no measured change corroborates them" would be false
    — nothing is said of the forecasts, and the condition keeps the rule's reason ("no stated
    step from the change to profits"). The same real version, its F12 reading alone changed."""
    pipe, _out = built["jpm"]
    v = _current(pipe, "TH-A56902FFB6")
    view: Any = type("V", (), {"store": pipe.store})()
    assert desk.Desk.evidence_gap(view, v)  # the positive case, above
    pr = v.priority.model_copy(update={"factors": [
        x.model_copy(update={"value": "incomplete"})
        if x.factor_id == "F12_fundamental_inflection" else x for x in v.priority.factors]})
    incomplete = v.model_copy(update={"priority": pr})
    assert desk.Desk.evidence_gap(view, incomplete) == []
    gate = next(g for g in desk.gates(incomplete, [], desk.near_term_reading(pipe.store, v))
                if g.name == desk.CATALYST_GATE)
    assert not gate.ok and gate.detail == "no stated step from the change to profits"


def test_a_measured_figure_outside_the_last_quarter_is_said_with_the_rules_own_age(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """The pilot's shape (TH-FBDC863613: a 2Q26 figure 104 days before the as-of, the window 92):
    J.P. Morgan's software thesis holds measured figures; read as of 200 days later, its latest is
    named with its age, dated exactly as the rule dates it (`observation_date`). NEGATIVE: as of
    its own date the figures are inside the window, and nothing is said of their age."""
    pipe, _out = built["jpm"]
    v = _current(pipe, "TH-8DA46A49DB")
    view: Any = type("V", (), {"store": pipe.store})()
    assert "days before the as-of" not in " ".join(desk.Desk.evidence_gap(view, v))
    later = v.model_copy(update={"as_of": v.as_of + timedelta(days=200)})
    pub = {s.article_id: s.published_at.date() if s.published_at else None
           for s in v.content.s09_sources}
    dates = [d for r in v.content.s04_key_evidence
             if r.value_text and r.epistemic.value == "actual"
             and (c := pipe.store.claim(r.claim_id)) is not None
             and (d := observation_date(c, later.as_of, pub.get(r.article_id))) is not None]
    age = (later.as_of - max(dates)).days
    assert age > CURRENT_OBSERVATION_DAYS
    assert (f"{age} days before the as-of, outside the last quarter "
            f"({CURRENT_OBSERVATION_DAYS} days).") in desk.Desk.evidence_gap(view, later)[-1]
    # NEGATIVE (code review of #740): a figure the rule reads as a STALE SERIES is never the
    # latest measured figure, however recent its date — the rule ages it as historical; dated
    # inside the window it would have silenced the line
    latest = max((r for r in v.content.s04_key_evidence if r.value_text
                  and r.epistemic.value == "actual"),
                 key=lambda r: observation_date(pipe.store.claim(r.claim_id), later.as_of,  # type: ignore[arg-type]
                                                pub.get(r.article_id)) or later.as_of)
    stale: Any = type("V", (), {"store": _Swap(
        pipe.store, latest.claim_id, measured_as_of=later.as_of - timedelta(days=10),
        qualifiers=("stale series — the source's figure is a year old",))})()
    said = desk.Desk.evidence_gap(stale, later)
    assert said and "days before the as-of, outside the last quarter" in said[-1]


def test_an_exposure_is_named_with_its_direction(built: dict[str, tuple[Pipeline, Path]]) -> None:
    _pipe, out = built["jpm"]
    gate = next(li.get_text(" ", strip=True) for li in
                _page(out, "TH-8DA46A49DB").select("aside.decide li.ok")
                if "An exposure the source names" in li.get_text())
    assert "S&P 500 Software Index (could be hurt)" in gate


def test_each_dated_line_says_its_period(built: dict[str, tuple[Pipeline, Path]]) -> None:
    """The three AI-adopters lines read alike once their periods were audit-only."""
    pipe, out = built["jpm"]
    v = _current(pipe, "TH-A56902FFB6")
    nt = desk.near_term_reading(pipe.store, v)
    rows = [li.get_text(" ", strip=True) for li in
            _page(out, "TH-A56902FFB6").select("aside.decide .timing details li")]
    periods = [x.claim.period for x in nt.claims[:8] if x.claim.period]
    assert periods and all(f"· {p}" in r for p, r in zip(periods, rows, strict=False))


def test_what_changed_names_the_source_of_its_closing_note(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """The closing "showing N of M" note: on the desk under the list (never counted as one more
    change), naming its publisher and the page's Evidence tab; on the card naming its publisher
    beside the card's own section 04. NEGATIVE: neither reads "from —"."""
    _pipe, out = built["calm"]
    page = _page(out, "TH-4BC577D53A")
    note = next(p.get_text() for p in page.select("p.small.muted")
                if p.get_text().startswith("showing "))
    assert re.fullmatch(r"showing 6 of 10 pieces of evidence from J\.P\. Morgan Private Bank, "
                        r"2026-10-02 — the rest are in the Evidence tab below", note)
    assert not any(li.get_text().startswith("showing ") for li in page.select("ul.changed li"))
    card = BeautifulSoup((out / "cards" / "TH-4BC577D53A.html").read_text(), "html.parser")
    for x in card.select(".aud"):
        x.decompose()
    text = re.sub(r"\s+", " ", card.get_text(" "))
    assert "from J.P. Morgan Private Bank, 2026-10-02 — the rest are in 04 KEY EVIDENCE" in text
    assert "from —" not in text and "from —" not in page.get_text(" ")
    md = (out / "cards" / "TH-4BC577D53A.md").read_text()  # the markdown card too (review, #740)
    assert "from J.P. Morgan Private Bank, 2026-10-02 — the rest are in 04 KEY EVIDENCE" in md


def test_uploads_names_no_monday_deadline(built: dict[str, tuple[Pipeline, Path]]) -> None:
    _pipe, out = built["jpm"]
    text = (out / "uploads.html").read_text()
    assert "Monday 03:00" not in text and "Run workflow" in text


def test_a_research_now_under_review_is_never_missing_anything(
        built: dict[str, tuple[Pipeline, Path]]) -> None:
    """Code review of #740: a Research Now whose near-term reading is in conflict (its stored
    reading no longer matches its claims re-dated today) reads that condition unmet until it is
    reassessed. It is under review — never "Missing:" on This week or Themes, never "Not yet
    Research Now", never "What's missing" in its panel. NEGATIVE: a Watch still names what it
    is missing."""
    pipe, _out = built["calm"]
    d = desk.Desk(pipe.store, pipe.store.runs()[-1], cards={}, generated="")
    rn = next(tid for tid, (_t, v) in d.asof.items()
              if v.priority.research_action.value == "RESEARCH NOW")
    nt = d.near[rn]
    d.near[rn] = dataclasses.replace(nt, recomputed="not shown" if nt.stored == "yes" else "yes")
    assert d.unmet(rn)  # the conflict reads unmet …
    assert d.missing(rn) == ""  # … and is never "Missing:"
    s = BeautifulSoup(d.thesis_page(rn), "html.parser")
    heads = [h.get_text() for h in s.select("aside.decide h3")]
    assert "Under review" in heads and "What's missing" not in heads
    watch = next(tid for tid, (_t, v) in d.asof.items()
                 if v.priority.research_action.value == "WATCH" and d.unmet(tid))
    assert d.missing(watch).startswith('<span class="miss" title="Not yet Research Now: ')
