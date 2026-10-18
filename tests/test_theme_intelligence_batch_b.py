"""Batch B of the verified review leads (`docs/records/2026-10-14-theme-intelligence-unverified-
leads-verified.md`) — the checks and the duplicated rules:

- U27 QA's "nine sections in order" compared the CLASS's fields, never the stored version;
- U53 the weekly report's "why this action" regex-read the rule trace and named a WATCH held by
  counter-evidence, while the reasons beside it (`cards.why_reasons`, read from the stored factor
  values) had no such branch;
- U56 the partial-awaiting-full rule was coded twice, in two orders: a preview-only channel's
  article with unreadable pages was a visual check on the desk and missing from the report;
- U58 the research-action vocabulary is held in seven maps;
- U41 one render derived each version's review findings up to five times, and the as-of view
  three times;
- U28 the spend bound priced every call as a cache write at 2.5 characters per token, which left
  a cache write no margin for a request that tokenises finer;
- U60b `.nav-tog` repeated `.theme-tog` rule for rule.

The articles are HYPOTHETICAL and labelled; the PDF is a SYNTHETIC fixture.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_overlap import DRAM_DOWN, DRAM_UP, Q4_AS_OF, _memory_case
from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    ingest_jpm,
    make_pipeline,
)
from vinci.theme_intelligence import budget as budget_mod
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.priority import F8_CONTESTED, F8_OUTWEIGHS, counter_verdict
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import (
    SECTION_IDS,
    ResearchAction,
    RunStatus,
    ThesisVersion,
)

ROOT = Path(__file__).resolve().parents[1]


def _current(pipe: Pipeline, tid: str) -> ThesisVersion:
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    return v


# --- U27: the nine sections, as STORED ------------------------------------------------------------

def _qa_section_check(pipe: Pipeline, run_id: str) -> Any:
    from vinci.theme_intelligence.qa import run_qa

    return next(c for c in run_qa(pipe.store, run_id).checks
                if c.name == "cards keep the nine sections in order")


def _jpm_run(tmp_path: Path) -> tuple[Pipeline, str]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=dt.date(2026, 2, 9))
    ingest_jpm(pipe)
    return pipe, pipe.finish_run(RunStatus.SUCCEEDED).run_id


def test_qa_reads_the_stored_versions_sections_in_order(tmp_path: Path) -> None:
    """POSITIVE: a real run's versions hold the nine sections in the fixed order, read from the
    stored payload."""
    from vinci.theme_intelligence.qa import _stored_sections

    pipe, rid = _jpm_run(tmp_path)
    theses = pipe.store.theses()
    assert len(theses) > 1
    for th in theses:
        assert _stored_sections(pipe.store, th.thesis_id, 1) == [f for f, _ in SECTION_IDS]
    check = _qa_section_check(pipe, rid)
    assert check.ok and f"{len(theses)} version(s) created by this run" in check.detail


@pytest.mark.parametrize("reorder", [
    lambda keys: list(reversed(keys)),                       # the lead's reversed order
    lambda keys: keys[:3] + [keys[4], keys[3]] + keys[5:],   # s04 and s05 swapped
])
def test_a_stored_version_with_its_sections_out_of_order_fails_qa(tmp_path: Path,
                                                                  reorder: Any) -> None:
    """NEGATIVE: a stored version whose payload holds the sections out of order — main passed it,
    comparing the class's fields with themselves."""
    pipe, rid = _jpm_run(tmp_path)
    th = pipe.store.theses()[0]
    row = pipe.store.conn.execute("SELECT as_of, payload FROM thesis_versions WHERE thesis_id=? "
                                  "AND version=1", (th.thesis_id,)).fetchone()
    payload = json.loads(row[1])
    content = payload["content"]
    sections = reorder([k for k in content if k != "header"])
    payload["content"] = {"header": content["header"], **{k: content[k] for k in sections}}
    payload["version"] = 2
    pipe.store.conn.execute("INSERT INTO thesis_versions (thesis_id, version, as_of, payload) "
                            "VALUES (?, 2, ?, ?)", (th.thesis_id, row[0], json.dumps(payload)))
    assert pipe.store.thesis_version(th.thesis_id, 2) is not None  # it still parses
    check = _qa_section_check(pipe, rid)
    assert not check.ok
    assert f"{th.thesis_id} v2: {sections}" in check.detail and f"{th.thesis_id} v1" not in \
        check.detail


# --- U53: the counter-evidence verdict, one structured value --------------------------------------

def _contested(tmp_path: Path) -> tuple[Pipeline, str, str, str]:
    """One supporting source, one independent source directly contradicting it: CONTESTED. The
    contradicting thesis is its own (no counter-evidence of its own)."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=Q4_AS_OF)
    _memory_case(pipe, "dram-up", "Hypo Research A", [DRAM_UP], "positive",
                 "DRAM prices rise in 4Q26")
    (inc,) = pipe.store.theses()
    _memory_case(pipe, "dram-down", "Hypo Research B", [DRAM_DOWN], "negative",
                 "DRAM prices fall in 4Q26")
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    other = next(t.thesis_id for t in pipe.store.theses() if t.thesis_id != inc.thesis_id)
    return pipe, run.run_id, inc.thesis_id, other


COUNTER = "Counter-evidence — "


def test_a_contested_watch_says_so_on_the_card_and_in_the_weekly_report(tmp_path: Path) -> None:
    """THE CONSTRUCTED CASE, end to end. A WATCH held by an independent contradiction AND by two
    other conditions: main's report line named the contest (its trace regex) while the reasons
    beside it — the card's and the report's own list — did not. Now the verdict is the F8
    factor's stored VALUE, and the report line is the same reasons."""
    pipe, rid, tid, other = _contested(tmp_path)
    v = _current(pipe, tid)
    assert v.priority.research_action is ResearchAction.WATCH
    f8 = next(f for f in v.priority.factors if f.factor_id == "F8_counterevidence")
    assert f8.value == F8_CONTESTED and f8.note.startswith("1 material counter-claims")
    assert "contested: 1 independent source(s)" in v.priority.rules_fired[0]  # the trace as was
    out = Path(write_run_outputs(pipe.store, rid, tmp_path / "out")["dir"])
    rows = {r["thesis_id"]: r for rs in json.loads((out / "dashboard.json").read_text())[
        "categories"].values() for r in rs}
    row = rows[tid]
    said = [x for x in row["why"] if x.startswith(COUNTER)]
    assert len(said) == 1 and "contradict" in said[0]
    assert row["why_action"] == " ".join(row["why"])  # one reading, never two
    assert len(row["why"]) == 3  # exposure and catalyst too: the counter line is not a fallback
    md = (out / "dashboard.md").read_text()
    assert f"- Why this action: {row['why_action']}" in md
    card = json.loads((out / "cards" / f"{tid}.json").read_text())
    assert any(x.startswith(COUNTER) for x in card["why_action"])
    # NEGATIVE: the contradicting thesis holds no counter-evidence of its own
    assert not [x for x in rows[other]["why"] if x.startswith(COUNTER)]
    assert next(f.value for f in _current(pipe, other).priority.factors
                if f.factor_id == "F8_counterevidence") == "0"


def test_counter_evidence_from_the_supporting_source_itself_outweighs_its_support(
        tmp_path: Path) -> None:
    """The other verdict: the supporting source's own counter-observation, as many as its
    support."""
    from vinci.theme_intelligence.cards import why_reasons

    up = ("Conventional DRAM contract prices are projected to rise 10% QoQ in 4Q26 on server "
          "demand.")
    down = "Conventional DRAM module inventory rose 15% in 3Q26 as buyers slowed orders."
    art = Hypo(slug="dram-two-sided", publisher="Hypo Research A", published=Q4_AS_OF,
               blocks=[("paragraph", up), ("paragraph", down)])
    x = extraction(
        [claim("c1", "b001", up.rstrip("."), "DRAM +10%", kind="forecast", epistemic="forecast",
               metric="DRAM contract price", value=10, value_text="10%", unit="%",
               period="4Q26"),
         claim("c2", "b002", down.rstrip("."), "DRAM inventory +15%", metric="module inventory",
               value=15, value_text="15%", unit="%", period="3Q26")],
        [hyp("h1", "DRAM contract prices rise in 4Q26", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", geography="Global", supporting=["c1"],
             counter=["c2"])])
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=Q4_AS_OF)
    ingest(pipe, art.doc(), x, as_of=Q4_AS_OF, publisher="Hypo Research A")
    (th,) = pipe.store.theses()
    v = _current(pipe, th.thesis_id)
    assert counter_verdict(v.priority) == F8_OUTWEIGHS
    assert "counter-evidence outweighs support" in v.priority.rules_fired[0]
    assert any(r.startswith(COUNTER + "its own sources") for r in why_reasons(v.content,
                                                                             v.priority))


def test_a_version_stored_before_the_verdict_was_a_value_is_read_from_its_trace(
        tmp_path: Path) -> None:
    """A version stored by main carries F8 as a COUNT and the verdict only in its WATCH trace
    (20 of 1,050 local stored versions, none in the pilot, 2026-10-16): read once, in
    `counter_verdict`. NEGATIVE: the same trace on a SKIP, or a count with no such trace, is no
    verdict."""
    pipe, _rid, tid, _other = _contested(tmp_path)
    pr = _current(pipe, tid).priority
    legacy = pr.model_copy(update={"factors": tuple(
        f.model_copy(update={"value": "1"}) if f.factor_id == "F8_counterevidence" else f
        for f in pr.factors)})
    assert counter_verdict(legacy) == F8_CONTESTED
    assert counter_verdict(legacy.model_copy(update={
        "rules_fired": ("WATCH (RESEARCH NOW unmet: counter-evidence outweighs support)",)}
    )) == F8_OUTWEIGHS
    assert counter_verdict(legacy.model_copy(update={
        "research_action": ResearchAction.SKIP})) is None
    assert counter_verdict(legacy.model_copy(update={
        "rules_fired": ("WATCH (RESEARCH NOW unmet: retrieval PARTIAL)",)})) is None


# --- U56: one partial-awaiting-full rule --------------------------------------------------------

def _preview_only_unreadable(tmp_path: Path) -> tuple[Pipeline, Any, str]:
    """SemiAnalysis is preview-only by decision; a supplied copy of one of its articles has two
    pages of undecodable glyphs (the SYNTHETIC glyph fixture), so the article stays PARTIAL."""
    from tests.test_theme_intelligence_glyph_quarantine import GLYPH, Model, _pipe
    from vinci.theme_intelligence.documents import Declared
    from vinci.theme_intelligence.ingest import ingest_file

    pipe = _pipe(tmp_path, Model())
    pipe.start_run("ingest", as_of=dt.date(2026, 10, 12))
    res = ingest_file(pipe, GLYPH, Declared(source_id="semianalysis", llm_permitted=True),
                      as_of=dt.date(2026, 10, 12))
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    assert res.status == "INGESTED" and res.article_id
    return pipe, run, res.article_id


def test_a_preview_only_channels_unreadable_pages_are_one_visual_check_on_both_surfaces(
        tmp_path: Path) -> None:
    """THE CONSTRUCTED CASE: main's desk asked for a visual check and main's weekly report did
    not list the article at all (its preview-only skip came first)."""
    from vinci.theme_intelligence.desk import _Registry, upload_items
    from vinci.theme_intelligence.report import research_intake

    pipe, run, aid = _preview_only_unreadable(tmp_path)
    (v,) = pipe.store.article_versions(aid)
    assert v.retrieval_state.value == "PARTIAL"
    intake = research_intake(pipe.store, run, [run], {"rows": [], "attention": []})
    (awaiting,) = [x for x in intake["awaiting_documents"]["items"] if aid in x]
    assert "not a missing document: pages 2–3 could not be read" in awaiting
    asked = [u for u in upload_items(_Registry(pipe.store), {}, [])
             if aid in u.audit and u.kind != "done"]  # "done": the import itself, as on main
    assert [u.kind for u in asked] == ["visual"] and asked[0].detail == ["pages 2, 3"]


def _rule_case(tmp_path: Path) -> tuple[Any, Any, Any, Any]:
    from vinci.theme_intelligence.config import load_sources
    from vinci.theme_intelligence.report import unread_documents

    pipe, _run, aid = _preview_only_unreadable(tmp_path)
    art = pipe.store.article(aid)
    unread = unread_documents(pipe.store.documents(), set())[aid]
    src = {s.id: s for s in load_sources()}["semianalysis"]
    return art, pipe.store.article_versions(aid), unread, src


def test_the_shared_rule_asks_for_nothing_where_nothing_is_to_be_asked(tmp_path: Path) -> None:
    """NEGATIVE pins of the one rule both surfaces call: a preview-only channel's preview with
    no unreadable pages and no linked report, a retired channel's article, an article read in
    full, and unreadable pages that are back matter only. POSITIVE: a linked report to upload is
    awaited; the unreadable pages ask for a visual check."""
    from vinci.theme_intelligence.report import partial_ask
    from vinci.theme_intelligence.schemas import RetrievalState

    art, versions, unread, src = _rule_case(tmp_path)

    def ask(vs: Any = versions, **kw: Any) -> str | None:
        got = partial_ask(art, vs, **{"unread": unread, "source": src, "linked_upload": False,
                                      "retired": set(), **kw})
        return got[0] if got else None

    assert ask() == "visual"
    assert ask(unread=None) is None  # the preview, by decision
    assert ask(unread=None, linked_upload=True) == "full_report"
    assert ask(retired={"semianalysis"}) is None
    full = [v.model_copy(update={"retrieval_state": RetrievalState.FULL}) for v in versions]
    assert ask(full) is None
    back = unread.model_copy(update={"quarantined": tuple(
        q.model_copy(update={"kind": "back_matter"}) for q in unread.quarantined)})
    assert ask(unread=back) is None


def test_a_retired_channels_document_is_never_read_as_an_unreadable_page_to_check(
        tmp_path: Path) -> None:
    """The report left a RETIRED channel's documents out; the desk read them (U56). One helper:
    left out on both."""
    from vinci.theme_intelligence.report import unread_documents

    pipe, _run, aid = _preview_only_unreadable(tmp_path)
    docs = pipe.store.documents()
    assert aid in unread_documents(docs, set())
    assert unread_documents(docs, {"semianalysis"}) == {}


# --- U58: the research-action vocabulary --------------------------------------------------------

def _action_maps() -> dict[str, dict[str, Any]]:
    """Every map of the research-action vocabulary, keyed by the action's value, each read as its
    call sites read it (report's pill map falls back to "skip", as `_thesis_html` does)."""
    from vinci.theme_intelligence import cards, desk, report
    from vinci.theme_intelligence.schemas import ACTION_RANK

    acts = [a.value for a in ResearchAction]
    return {
        "word cards._ACTION_WORD": {a: cards._ACTION_WORD.get(a) for a in acts},
        "word desk._ACTION": {a: desk._ACTION.get(a, (None,))[0] for a in acts},
        "word report._ACTION_WORDS": {a.value: w for a, w in report._ACTION_WORDS.items()},
        "class cards._PILL": {a: cards._PILL.get(a) for a in acts},
        "class desk._ACTION": {a: desk._ACTION.get(a, (None, None))[1] for a in acts},
        "class report._PILL_CLS": {a: report._PILL_CLS.get(a, "skip") for a in acts},
        "rank schemas.ACTION_RANK": {a.value: r for a, r in ACTION_RANK.items()},
        "rank desk._RANK (ascending)": {a: -desk._RANK[a] if a in desk._RANK else None
                                        for a in acts},
        "rank report._RANK": {a: report._RANK.get(a) for a in acts},
    }


def _disagreements(maps: dict[str, dict[str, Any]]) -> list[str]:
    """Each map against the first of its kind: the same words and pill classes for every action,
    and the same ORDER of the actions (the rank maps run opposite ways by design)."""
    out: list[str] = []
    acts = [a.value for a in ResearchAction]
    first: dict[str, tuple[str, dict[str, Any]]] = {}
    for name, m in maps.items():
        kind = name.split()[0]
        if set(m) != set(acts) or any(v is None for v in m.values()):
            out.append(f"{name} does not cover every action: {m}")
            continue
        seen = (sorted(acts, key=lambda a: m[a]) if kind == "rank" else m)
        if kind not in first:
            first[kind] = (name, seen)
        elif seen != first[kind][1]:
            out.append(f"{name} disagrees with {first[kind][0]}: {seen} vs {first[kind][1]}")
    return out


def test_every_map_of_the_research_action_vocabulary_agrees() -> None:
    """POSITIVE (U58): seven maps in cards / desk / report, and the rank in schemas, say the same
    thing — words, pill classes and order."""
    maps = _action_maps()
    assert len(maps) == 9
    assert _disagreements(maps) == []


def test_a_map_that_drifts_is_named() -> None:
    """NEGATIVE: a renamed word, a missing action and an inverted rank are each caught."""
    maps = _action_maps()
    word = dict(maps, **{"word desk._ACTION": {**maps["word desk._ACTION"], "WATCH": "Monitor"}})
    assert _disagreements(word) == [
        "word desk._ACTION disagrees with word cards._ACTION_WORD: {'RESEARCH NOW': 'Research "
        "Now', 'WATCH': 'Monitor', 'SKIP': 'Skip'} vs {'RESEARCH NOW': 'Research Now', 'WATCH': "
        "'Watch', 'SKIP': 'Skip'}"]
    gone = {k: v for k, v in maps["class cards._PILL"].items() if k != "SKIP"}
    assert _disagreements(dict(maps, **{"class cards._PILL": gone}))[0].startswith(
        "class cards._PILL does not cover every action")
    flipped = {a: -r for a, r in maps["rank report._RANK"].items()}
    assert _disagreements(dict(maps, **{"rank report._RANK": flipped}))[0].startswith(
        "rank report._RANK disagrees with rank schemas.ACTION_RANK")


# --- U41: each view derived once per render -----------------------------------------------------

def test_one_render_derives_each_versions_findings_once_and_the_as_of_view_once(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Measured on main: a 52-week render asked for review findings 1,726 times for 913 versions,
    and built the as-of view three times. Counted here on a contested registry: each
    (thesis, version) computed ONCE, whoever asks."""
    from vinci.theme_intelligence import desk, report

    pipe, rid, _tid, _other = _contested(tmp_path)
    computed: list[tuple[str, int]] = []
    real = report._resolved_by_relabel  # called once by each computation, never by a memo hit

    def counting(store: Any, thesis_id: str, v: ThesisVersion, *a: Any) -> Any:
        computed.append((thesis_id, v.version))
        return real(store, thesis_id, v, *a)

    built: list[str] = []
    real_asof = report.theses_as_of_run

    def asof(store: Any, run: Any) -> Any:
        built.append(run.run_id)
        return real_asof(store, run)

    monkeypatch.setattr(report, "_resolved_by_relabel", counting)
    monkeypatch.setattr(report, "theses_as_of_run", asof)
    monkeypatch.setattr(desk, "theses_as_of_run", asof)
    write_run_outputs(pipe.store, rid, tmp_path / "out")
    assert computed and len(computed) == len(set(computed))
    assert built == [rid]


def test_the_derived_memo_lives_only_inside_a_read_pass_and_dies_with_any_append(
        tmp_path: Path) -> None:
    """Safety: outside `reading()` there is no memo; an append inside one drops it (as it drops
    the article versions read) — a finding derived before a write is never served after it."""
    from vinci.theme_intelligence.schemas import IssueSeverity, VerificationIssue

    pipe = make_pipeline(tmp_path)
    assert pipe.store.derived() is None
    with pipe.store.reading():
        memo = pipe.store.derived()
        assert memo is not None
        memo["probe"] = 1
        assert pipe.store.derived() == {"probe": 1}
        pipe.store.add_issue(VerificationIssue(
            issue_id="VI-batch-b-probe", run_id="R-probe", scope="run", ref_id="R-probe",
            severity=IssueSeverity.WARN, code="PROBE", detail="a write inside a read pass",
            created_at=dt.datetime(2026, 10, 16, tzinfo=dt.UTC)))
        assert pipe.store.derived() == {}
        memo["after"] = 2
    assert pipe.store.derived() is None
    with pipe.store.reading():
        assert pipe.store.derived() == {}  # a new pass starts empty


# --- U28: the bound holds at the measured floor, cache write included ---------------------------

#: the lowest request characters per billed input token of 104 distinct real paid calls
#: (2026-10-16): an enrichment call, 4,110 request characters for 1,959 input tokens
FLOOR_CHARS, FLOOR_TOKENS = 4_110, 1_959


def _cost_at_cap(*, cache_write: bool) -> float:
    from vinci.theme_intelligence.config import LLM_MAX_TOKENS
    from vinci.theme_intelligence.extract import cost_of

    usage = ({"cache_creation_input_tokens": FLOOR_TOKENS} if cache_write
             else {"input_tokens": FLOOR_TOKENS})
    cost = cost_of("claude-opus-4-8", {**usage, "output_tokens": LLM_MAX_TOKENS})
    assert cost is not None
    return cost


def test_the_densest_measured_request_is_bounded_with_its_output_at_the_cap() -> None:
    """POSITIVE: at the lowest measured ratio, the output at its cap, uncached and as a cache
    write, the bound covers the bill."""
    user = "u" * (FLOOR_CHARS - 2)  # + "{}": the tool schema
    assert budget_mod.call_bound("claude-opus-4-8", "", user, {}) >= _cost_at_cap(
        cache_write=False)
    assert budget_mod.call_bound("claude-opus-4-8", "", user, {}, cache_write=True) >= \
        _cost_at_cap(cache_write=True)


def test_the_bound_before_u28_left_a_cache_write_under_its_bill(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: main's bound — 2.5 characters per token, every call priced as a cache write — is
    below the bill of the same request as a cache write. Uncached, main's bound and this one are
    the same number."""
    user = "u" * (FLOOR_CHARS - 2)
    now_uncached = budget_mod.call_bound("claude-opus-4-8", "", user, {})
    monkeypatch.setattr(budget_mod, "CHARS_PER_TOKEN_BOUND", 2.5)
    main = budget_mod.call_bound("claude-opus-4-8", "", user, {}, cache_write=True)
    assert main < _cost_at_cap(cache_write=True)
    assert main == pytest.approx(now_uncached, abs=1e-12)


def test_the_guard_bounds_a_cache_writing_call_as_one() -> None:
    """The guard reads the call's own `cache` flag (a completeness part under
    PROMPT_CACHE_PARTS): its input bound is 1.25x the same call's uncached."""
    from vinci.theme_intelligence.budget import GuardedClient, SpendGuard

    class Fake:
        model = "claude-opus-4-8"
        last_usage = {"input_tokens": 10, "output_tokens": 10}

        def extract(self, **_kw: Any) -> dict[str, Any]:
            return {}

    from vinci.theme_intelligence.config import LLM_MAX_TOKENS

    tool = {"name": "record_completeness"}
    chars = len("s") + 40_000 + len(json.dumps(tool))
    for cache, rate in ((False, 1.0), (True, 1.25)):
        guard = SpendGuard(run_limit=100.0)
        GuardedClient(Fake(), guard).extract(system="s", user="u" * 40_000, tool=tool,
                                            cache=cache)
        assert guard.calls[0]["bound_usd"] == pytest.approx(
            (chars / 2.0 * 5.0 * rate + LLM_MAX_TOKENS * 25.0) / 1e6, abs=1e-4), cache


# --- U60b: the two toggles share one rule --------------------------------------------------------

def test_the_two_brand_toggles_share_one_rule_each() -> None:
    """`.nav-tog` repeated `.theme-tog` rule for rule; now each rule names both. The rendered
    styles are compared in a browser in the record (0 of 25,872 computed values differ)."""
    css = (ROOT / "frontend" / "assets" / "styles.css").read_text()
    for part in ("", ":hover", ":focus-visible", " svg"):
        assert css.count(f".theme-tog{part}, .nav-tog{part} {{") == 1, part
        assert f"\n.nav-tog{part} {{" not in css and f"\n.theme-tog{part} {{" not in css, part
