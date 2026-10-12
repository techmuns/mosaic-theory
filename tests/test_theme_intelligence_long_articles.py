"""Long articles, malformed model answers, and the publisher of a feed-host URL — failures of the
2026-10-10 live runs.

1. One mention came back typed "other" (not an allowed entity type) and the whole-answer check
   discarded a paid extraction: the contradiction run FAILED. Now each ITEM is validated; a
   malformed one is dropped and NAMED (never coerced into a guessed value), the rest is kept.
2. The completeness pass over a ~3,000-word SemiAnalysis post (124 open figures + 91 open
   paragraphs) overran the output cap, so the article's gaps stayed unreviewed. Now the gaps are
   reviewed in PARTS, each part seeing what the earlier parts added; a part that overruns is split
   once, and the discarded call is recorded with its cost.
3. `article --url https://newsletter.semianalysis.com/p/…` was filed "UNKNOWN publisher": the
   channel was matched on its entry page's host only, and SemiAnalysis posts live on its feed's.

Fake LLM clients only: no network, no spend. The article is HYPOTHETICAL and labelled as such.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.theme_intelligence_support import (
    JPM_DIR,
    FrozenSecHttp,
    Hypo,
    claim,
    extraction,
    fetched,
    hyp,
    mention,
)
from vinci.graph.llm import LlmError
from vinci.theme_intelligence import completeness as completeness_mod
from vinci.theme_intelligence.__main__ import main, source_for_url
from vinci.theme_intelligence.completeness import run_completeness, scan_article
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.extract import (
    Extraction,
    InvalidAnswerError,
    run_extraction,
    validate_items,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import IssueSeverity
from vinci.theme_intelligence.securities import SecResolver
from vinci.theme_intelligence.store import Store

TRUNCATED = ("model claude-opus-4-8 truncated at max_tokens=21333 — tool call incomplete; raise "
             "the cap or shrink the prompt")
SEGMENTS = ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel")
AS_OF = date(2026, 9, 10)


def _paragraph(i: int, seg: str) -> str:
    who = "the operator Acme Corp" if i == 0 else "the operator"
    tail = "while Hyperscalers grew orders" if i == 0 else "while costs grew"
    return (f"In the {seg} segment {who} reported that unit revenue rose {i + 2}% {tail} at a "
            f"slower pace this year.")


LONG = Hypo(slug="long-article", publisher="Hypo Research A", published=AS_OF,
            blocks=[("paragraph", _paragraph(i, s)) for i, s in enumerate(SEGMENTS)])


def _pass1(*, bad_items: bool) -> dict[str, Any]:
    """Pass 1 captures the first paragraph only; with `bad_items`, it also carries the observed
    malformed shape (a mention typed "other") and an affected mention with an unknown role."""
    affected = [("Acme Corp", "potential_beneficiary")]
    mentions = [mention("Acme Corp", "b001", "Acme Corp")]
    if bad_items:
        affected.append(("Hyperscalers", "bystander"))
        mentions.append(mention("Hyperscalers", "b001", "Hyperscalers", entity_type="other"))
    ans = extraction(
        [claim("c1", "b001", "unit revenue rose 2%", "Alpha unit revenue +2%", value=2,
               value_text="2%", unit="%", period="2026")],
        [hyp("h1", "Unit revenue up-cycle", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"], affected=affected)],
        mentions=mentions)
    ans["attributed_authors"] = []
    return ans


def _listed(user: str) -> set[str]:
    """The gaps a completeness message ASKS about: open figures and unanchored paragraphs."""
    figs = re.findall(r"^- (\S+) \[b\d+\] .* — NOT CAPTURED — ", user, re.M)
    return set(figs) | set(re.findall(r"^- (b\d+): UNANCHORED$", user, re.M))


class FakeLlm:
    """Answers pass 1 with a fixed extraction and pass 1b by accounting for every listed gap
    (immaterial, with a reason). Part 1 also ADDS two claims — one for its own gap and one for a
    gap that belongs to part 2 — and gives a verdict on a gap it was never shown."""

    model = "claude-opus-4-8"

    def __init__(self, pass1: dict[str, Any] | list[dict[str, Any]], *,
                 truncate: frozenset[str] = frozenset(),
                 invalid: frozenset[str] = frozenset()) -> None:
        self.pass1 = pass1 if isinstance(pass1, list) else [pass1]
        self.truncate = truncate
        self.invalid = invalid  # parts ("" = the single call) answered with a broken top level
        self.calls: list[str] = []
        self.users: dict[str, str] = {}
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.last_usage = {"input_tokens": 1000, "output_tokens": 400}
        if tool["name"] == "record_article_evidence":
            self.calls.append("extract")
            return self.pass1.pop(0) if len(self.pass1) > 1 else self.pass1[0]
        m = re.search(r"This is part (\w+):", user)
        label = m.group(1) if m else ""
        self.calls.append("complete" + (f"-{label}" if label else ""))
        self.users[label] = user
        if label in self.truncate:
            self.last_usage = {"input_tokens": 1000, "output_tokens": 21333}
            raise LlmError(TRUNCATED)
        if label in self.invalid:
            return {"figure_reviews": "not a list", "block_reviews": [], "added_claims": [],
                    "added_mentions": [], "hypothesis_additions": [], "added_hypotheses": [],
                    "added_risks": []}
        gaps = _listed(user)
        out: dict[str, Any] = {
            "figure_reviews": [{"figure_id": g, "verdict": "immaterial", "claim_ids": [],
                                "reason": "test: restates the segment pattern"}
                               for g in sorted(gaps) if "#" in g],
            "block_reviews": [{"block_id": g, "verdict": "immaterial", "hypothesis_ids": [],
                               "claim_ids": [], "reason": "test: restates the segment pattern"}
                              for g in sorted(gaps) if "#" not in g],
            "added_claims": [], "added_mentions": [], "hypothesis_additions": [],
            "added_hypotheses": [], "added_risks": []}
        if label in ("1", ""):
            out["added_claims"] = [
                claim("k1_1", "b002", "unit revenue rose 3%", "Bravo unit revenue +3%", value=3,
                      value_text="3%", unit="%", period="2026"),
                claim("k1_2", "b005", "unit revenue rose 6%", "Echo unit revenue +6%", value=6,
                      value_text="6%", unit="%", period="2026")]
            out["hypothesis_additions"] = [{
                "hypothesis_id": "h1", "supporting_claim_ids": ["k1_1", "k1_2"],
                "dislocation_claim_ids": [], "counter_claim_ids": [], "catalyst_claim_ids": [],
                "affected_mentions": [], "sector_exposures": []}]
            out["figure_reviews"] = [r for r in out["figure_reviews"]
                                     if r["figure_id"] != "b002#3%"] + [
                {"figure_id": "b002#3%", "verdict": "captured_by_added_claim",
                 "claim_ids": ["k1_1"], "reason": ""},
                {"figure_id": "b008#9%", "verdict": "immaterial", "claim_ids": [],
                 "reason": "a verdict on a gap this part was not shown"}]
        return out


# --- 1. item-level validation ---------------------------------------------------------------

def test_a_malformed_item_is_dropped_and_named_and_every_valid_item_kept() -> None:
    parsed, dropped = validate_items(Extraction, _pass1(bad_items=True))
    assert [m.name_as_written for m in parsed.mentions] == ["Acme Corp"]
    assert [a.name_as_written for a in parsed.hypotheses[0].affected_mentions] == ["Acme Corp"]
    assert len(parsed.claims) == 1 and len(parsed.hypotheses) == 1  # the rest is kept
    assert len(dropped) == 2, dropped
    assert dropped[0].startswith("mentions[1] dropped — entity_type") and "'other'" in dropped[0]
    assert dropped[1].startswith("hypotheses[0].affected_mentions[1] dropped — role")
    assert "'bystander'" in dropped[1]


def test_a_clean_answer_drops_nothing_and_a_malformed_top_level_still_fails_loud() -> None:
    parsed, dropped = validate_items(Extraction, _pass1(bad_items=False))
    assert dropped == [] and len(parsed.mentions) == 1
    broken = _pass1(bad_items=False)
    broken["claims"] = "c1"  # not a list: nothing item-level to keep — the answer is refused
    with pytest.raises(ValidationError):
        validate_items(Extraction, broken)


def _broken_like_live() -> dict[str, Any]:
    """The live failure's shape (2026-10-10, a SemiAnalysis extraction): `hypotheses` came back as
    TEXT — and broken JSON at that (a stray "{" where a property name belongs), so nothing can
    decode it without guessing."""
    ans = _pass1(bad_items=False)
    ans["hypotheses"] = ('[{"local_id": "h1", "bottom_line_fact": {"text": "t", "claim_ids": '
                         '["c1"]}, {"bottom_line_inference": {"text": "i"}}]')
    return ans


def test_an_answer_failing_at_the_top_level_is_set_aside_and_asked_once_more(
        tmp_path: Path) -> None:
    fake = FakeLlm([_broken_like_live(), _pass1(bad_items=False)])
    got = run_extraction(LONG.doc(), publisher="P", as_of=AS_OF.isoformat(),
                         taxonomy=load_taxonomy(), client=fake, cache_dir=tmp_path)
    assert fake.calls == ["extract", "extract"] and not got.cached
    assert len(got.extraction.hypotheses) == 1  # the re-ask's answer, never a repaired one
    assert len(got.set_aside) == 1
    note, usage = got.set_aside[0]
    assert "set aside as" in note and "asked once more" in note and usage is not None
    kept = sorted(x.name for x in (tmp_path / "extract").iterdir())
    assert len(kept) == 2 and any(".invalid-1.json" in k for k in kept)  # kept for the record
    again = FakeLlm(_broken_like_live())  # a replay reads the good answer: nothing re-paid
    replay = run_extraction(LONG.doc(), publisher="P", as_of=AS_OF.isoformat(),
                            taxonomy=load_taxonomy(), client=again, cache_dir=tmp_path)
    assert again.calls == [] and replay.cached and replay.set_aside == []


def test_a_second_failure_fails_loud_with_both_calls_costed(tmp_path: Path) -> None:
    fake = FakeLlm(_broken_like_live())
    with pytest.raises(InvalidAnswerError) as err:
        run_extraction(LONG.doc(), publisher="P", as_of=AS_OF.isoformat(),
                       taxonomy=load_taxonomy(), client=fake, cache_dir=tmp_path)
    assert fake.calls == ["extract", "extract"]  # asked once more, never a third time
    assert len(err.value.usages) == 2 and all(u for u in err.value.usages)
    assert len(list((tmp_path / "extract").glob("*.invalid-*.json"))) == 2


def test_a_cached_invalid_answer_is_set_aside_and_asked_again(tmp_path: Path) -> None:
    """An answer cached by a run before this fix (written before validation) must not fail the
    article on every replay: it is set aside — paid earlier, so no cost this run — and asked
    again; with no model client the refusal is loud."""
    fake = FakeLlm(_broken_like_live())
    with pytest.raises(InvalidAnswerError):
        run_extraction(LONG.doc(), publisher="P", as_of=AS_OF.isoformat(),
                       taxonomy=load_taxonomy(), client=fake, cache_dir=tmp_path)
    for f in (tmp_path / "extract").glob("*.invalid-2.json"):  # restore one as a plain cache entry
        f.rename(f.with_name(f.name.replace(".invalid-2.json", ".json")))
    with pytest.raises(InvalidAnswerError) as no_client:
        run_extraction(LONG.doc(), publisher="P", as_of=AS_OF.isoformat(),
                       taxonomy=load_taxonomy(), client=None, cache_dir=tmp_path)
    assert no_client.value.usages == []
    good = FakeLlm(_pass1(bad_items=False))
    got = run_extraction(LONG.doc(), publisher="P", as_of=AS_OF.isoformat(),
                         taxonomy=load_taxonomy(), client=good, cache_dir=tmp_path)
    assert good.calls == ["extract"] and len(got.extraction.hypotheses) == 1
    assert [u for _, u in got.set_aside] == [None]  # paid by the earlier run


# --- 2. the completeness pass in parts --------------------------------------------------------

def test_a_long_articles_gaps_are_reviewed_in_parts_and_an_overrun_part_is_split_once(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc, tax = LONG.doc(), load_taxonomy()
    x = Extraction.model_validate(_pass1(bad_items=False))
    ledger = scan_article(doc)
    assert len(ledger.figures) == 8 and len(ledger.argument_blocks) == 8  # 14 open after pass 1
    fake = FakeLlm(_pass1(bad_items=False), truncate=frozenset({"2"}))
    res = run_completeness(doc, x, ledger, publisher="P", as_of=AS_OF.isoformat(), taxonomy=tax,
                           client=fake, cache_dir=tmp_path)
    assert fake.calls == ["complete-1", "complete-2", "complete-2a", "complete-2b", "complete-3"]
    assert [(c.label, c.truncated) for c in res.calls] == [
        ("1", False), ("2", True), ("2a", False), ("2b", False), ("3", False)]
    assert (res.calls[1].cost_usd or 0) > 0  # the discarded call is costed, never hidden
    assert (res.cost_usd or 0) > sum(c.cost_usd or 0 for c in res.calls if not c.truncated)
    # a later part is SHOWN what earlier parts added, and is not asked about what they cover
    assert "b1.k1_2" in fake.users["2a"]
    assert _listed(fake.users["2a"]) == {"b006#7%"}
    assert _listed(fake.users["2b"]) == {"b006", "b007#8%", "b007"}
    assert {c.local_id for c in res.output.added_claims} == {"b1.k1_1", "b1.k1_2"}
    assert [a.supporting_claim_ids for a in res.output.hypothesis_additions] == [
        ["b1.k1_1", "b1.k1_2"]]
    # a verdict on a gap the part was not shown is ignored — and said so
    assert [d for d in res.dropped if "b008#9%" in d] == [
        "part 1: figure_reviews: b008#9% is not a gap of this part — verdict ignored"]
    assert len(res.notes) == 2 and "reviewed in 3 parts" in res.notes[0]
    assert "split once" in res.notes[1]
    # a replay re-pays nothing: the overrun is remembered, every answer is cached
    again = FakeLlm(_pass1(bad_items=False))
    replay = run_completeness(doc, x, ledger, publisher="P", as_of=AS_OF.isoformat(),
                              taxonomy=tax, client=again, cache_dir=tmp_path)
    assert again.calls == [] and replay.cached and replay.output == res.output
    assert [c.label for c in replay.calls] == ["1", "2a", "2b", "3"]


def test_a_half_that_overruns_again_fails_loud(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc = LONG.doc()
    x = Extraction.model_validate(_pass1(bad_items=False))
    fake = FakeLlm(_pass1(bad_items=False), truncate=frozenset({"2", "2a"}))
    with pytest.raises(LlmError):
        run_completeness(doc, x, scan_article(doc), publisher="P", as_of=AS_OF.isoformat(),
                         taxonomy=load_taxonomy(), client=fake, cache_dir=tmp_path)
    assert fake.calls == ["complete-1", "complete-2", "complete-2a"]  # split once, never again


def test_a_short_article_is_one_call_over_the_full_ledger(tmp_path: Path) -> None:
    doc = LONG.doc()
    x = Extraction.model_validate(_pass1(bad_items=False))
    fake = FakeLlm(_pass1(bad_items=False))
    res = run_completeness(doc, x, scan_article(doc), publisher="P", as_of=AS_OF.isoformat(),
                           taxonomy=load_taxonomy(), client=fake, cache_dir=tmp_path)
    assert fake.calls == ["complete"] and res.notes == []
    assert "<batch>" not in fake.users[""]
    assert "b001#2%" in fake.users[""]  # the full ledger, captured figures included
    assert {c.local_id for c in res.output.added_claims} == {"k1_1", "k1_2"}  # ids untouched


# --- 3. end to end: both live failures in one article, through the pipeline -----------------

def test_the_long_malformed_article_runs_end_to_end_with_every_gap_accounted_for(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    fake = FakeLlm(_pass1(bad_items=True), truncate=frozenset({"2"}))
    resolver = SecResolver(tmp_path / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]
    pipe = Pipeline(tmp_path / "ti", sources=load_sources(), taxonomy=load_taxonomy(),
                    client=fake, resolver=resolver, review=False)  # type: ignore[arg-type]
    run = pipe.start_run("article", as_of=AS_OF)
    doc = LONG.doc()
    pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="manual",
                          as_of=AS_OF, publisher_override=LONG.publisher)
    assert len(pipe.store.theses()) == 1
    version = pipe.store.article_versions(pipe.store.articles()[0].article_id)[0]
    rep = pipe.store.completeness(version.version_id)[0]
    assert rep.pass_ran
    by = {f.figure: f.status for f in rep.figures}
    assert by["2%"] == "captured"
    assert by["3%"] == by["6%"] == "added_by_completeness_pass"
    assert {f.status for f in rep.figures} <= {"captured", "added_by_completeness_pass",
                                               "immaterial"}
    assert {b.status for b in rep.blocks} <= {"anchored", "immaterial"}
    issues = pipe.store.issues(run_id=run.run_id)
    dropped = [i.detail for i in issues if i.code == "MALFORMED_ITEM_DROPPED"]
    assert any(d.startswith("extraction: mentions[1] dropped") for d in dropped), dropped
    assert any(d.startswith("extraction: hypotheses[0].affected_mentions[1] dropped")
               for d in dropped), dropped
    assert all(i.severity is IssueSeverity.WARN for i in issues
               if i.code == "MALFORMED_ITEM_DROPPED")
    assert len([i for i in issues if i.code == "COMPLETENESS_IN_PARTS"]) == 2
    calls = pipe.store.llm_calls(run.run_id)
    assert sorted(c["purpose"] for c in calls) == sorted(
        ["extract", "complete-1", "complete-2-truncated", "complete-2a", "complete-2b",
         "complete-3"])
    trunc = next(c for c in calls if c["purpose"] == "complete-2-truncated")
    assert trunc["cost_usd"] > 0 and trunc["usage"]["output_tokens"] == 21333


# --- 4. the publisher of an article on a channel's feed host --------------------------------

@pytest.mark.parametrize(("url", "source_id"), [
    ("https://newsletter.semianalysis.com/p/sparse-savings-persistent-demand-inside-glm53",
     "semianalysis"),
    ("https://semianalysis.com/p/an-entry-host-post", "semianalysis"),
    ("https://www.trendforce.com/presscenter/news/20260930-13258.html", "trendforce"),
    ("https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/"
     "a-calm-index-a-restless-market", "jpm_tmt"),
    ("https://www.citigroup.com/global/insights/overcoming-gridlock-2-0-solving-power-"
     "bottlenecks-to-drive-ai-energy-security", "citi_must_c"),
    ("https://newsletter.semianalysis.com.example.test/p/lookalike", "manual"),  # exact host
    ("https://example.test/hypothetical/elsewhere", "manual"),
])
def test_a_url_is_its_channels_by_any_configured_host(url: str, source_id: str) -> None:
    assert source_for_url(url, load_sources()) == source_id


def test_a_feed_host_article_is_filed_under_its_channels_publisher_end_to_end(
        tmp_path: Path) -> None:
    """The CLI path the live run took (`article --url`), on saved HTML and a frozen extraction:
    the stored article, its version's source line and its card name SemiAnalysis."""
    url = "https://newsletter.semianalysis.com/p/hypothetical-feed-host-post"
    html = tmp_path / "page.html"
    html.write_text(
        "<!doctype html><html><head><title>[HYPOTHETICAL TEST FIXTURE] feed host</title>"
        "<meta name='author' content='Test Author'></head><body><article><p>DRAM contract "
        "prices rose 9% in the quarter as AI server demand absorbed supply across every "
        "vendor.</p><p>Suppliers kept capacity additions modest, so inventories at module "
        "makers fell again while buyers locked in longer contracts with the major vendors."
        "</p><p>This hypothetical page exists only to test that a post on a channel's feed "
        "host is filed under that channel's publisher.</p></article></body></html>")
    fx = tmp_path / "extraction.json"
    ans = extraction(
        [claim("c1", "b001", "DRAM contract prices rose 9% in the quarter", "DRAM +9%",
               value=9, value_text="9%", unit="%", period="the quarter")],
        [hyp("h1", "DRAM contract price up-cycle", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"])])
    ans["attributed_authors"] = []
    fx.write_text(json.dumps(ans))
    data = tmp_path / "ti"
    rc = main(["--data-dir", str(data), "article", "--url", url, "--as-of", "2026-09-10",
               "--html", str(html), "--fixture", str(fx), "--cache-only", "--no-review"])
    assert rc in (0, 2)
    store = Store(data / "registry.db")
    art = store.articles()[0]
    assert (art.source_id, art.publisher) == ("semianalysis", "SemiAnalysis")
    card = next((data / "runs").rglob("cards/TH-*.json"))
    assert "UNKNOWN publisher" not in card.read_text()
    assert "SemiAnalysis" in card.read_text()


# --- 5. end to end: a set-aside answer is costed and the article processed ---------------------

def _pipe_with(tmp_path: Path, fake: FakeLlm) -> Pipeline:
    resolver = SecResolver(tmp_path / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]
    return Pipeline(tmp_path / "ti", sources=load_sources(), taxonomy=load_taxonomy(),
                    client=fake, resolver=resolver, review=False)  # type: ignore[arg-type]


def test_a_set_aside_answer_is_costed_and_the_article_processed_end_to_end(
        tmp_path: Path) -> None:
    pipe = _pipe_with(tmp_path, FakeLlm([_broken_like_live(), _pass1(bad_items=False)]))
    run = pipe.start_run("article", as_of=AS_OF)
    doc = LONG.doc()
    pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="manual",
                          as_of=AS_OF, publisher_override=LONG.publisher)
    assert len(pipe.store.theses()) == 1
    issues = [i for i in pipe.store.issues(run_id=run.run_id) if i.code == "ANSWER_SET_ASIDE"]
    assert len(issues) == 1 and issues[0].severity is IssueSeverity.WARN
    calls = pipe.store.llm_calls(run.run_id)
    assert sorted(c["purpose"] for c in calls) == ["complete", "extract", "extract-invalid"]
    assert next(c for c in calls if c["purpose"] == "extract-invalid")["cost_usd"] > 0


def test_an_unusable_paid_answer_fails_loud_with_its_cost_recorded(tmp_path: Path) -> None:
    pipe = _pipe_with(tmp_path, FakeLlm(_broken_like_live()))
    run = pipe.start_run("article", as_of=AS_OF)
    doc = LONG.doc()
    with pytest.raises(InvalidAnswerError):
        pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="manual",
                              as_of=AS_OF, publisher_override=LONG.publisher)
    calls = pipe.store.llm_calls(run.run_id)
    assert [c["purpose"] for c in calls] == ["extract-invalid", "extract-invalid"]
    assert all(c["cost_usd"] > 0 and not c["cached"] for c in calls)


def test_a_malformed_field_costs_that_field_never_the_completeness_pass(
        tmp_path: Path) -> None:
    """Field by field since 2026-10-12: one malformed field no longer leaves the pass not run."""
    pipe = _pipe_with(tmp_path, FakeLlm(_pass1(bad_items=False), invalid=frozenset({""})))
    run = pipe.start_run("article", as_of=AS_OF)
    doc = LONG.doc()
    pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="manual",
                          as_of=AS_OF, publisher_override=LONG.publisher)
    calls = {c["purpose"]: c for c in pipe.store.llm_calls(run.run_id)}
    assert set(calls) == {"extract", "complete"} and calls["complete"]["cost_usd"] > 0
    codes = [i.code for i in pipe.store.issues(run_id=run.run_id)]
    assert "COMPLETENESS_PASS_NOT_RUN" not in codes
    dropped = [i.detail for i in pipe.store.issues(run_id=run.run_id)
               if i.code == "MALFORMED_ITEM_DROPPED"]
    assert any("figure_reviews: the whole field discarded" in d for d in dropped)


class _NotAnObject(FakeLlm):
    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> Any:
        out = super().extract(system=system, user=user, tool=tool, cache=cache)
        return out if tool["name"] == "record_article_evidence" else ["not", "an", "object"]


def test_an_answer_that_is_not_an_object_leaves_the_pass_not_run_and_costed(
        tmp_path: Path) -> None:
    pipe = _pipe_with(tmp_path, _NotAnObject(_pass1(bad_items=False)))
    run = pipe.start_run("article", as_of=AS_OF)
    doc = LONG.doc()
    pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="manual",
                          as_of=AS_OF, publisher_override=LONG.publisher)
    calls = {c["purpose"]: c for c in pipe.store.llm_calls(run.run_id)}
    assert set(calls) == {"extract", "complete-invalid"}
    assert calls["complete-invalid"]["cost_usd"] > 0
    assert [i.code for i in pipe.store.issues(run_id=run.run_id)
            if i.code == "COMPLETENESS_PASS_NOT_RUN"] == ["COMPLETENESS_PASS_NOT_RUN"]


def test_a_malformed_part_keeps_its_valid_fields_and_its_bad_field_stays_open(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc = LONG.doc()
    x = Extraction.model_validate(_pass1(bad_items=False))
    fake = FakeLlm(_pass1(bad_items=False), invalid=frozenset({"3"}))
    res = run_completeness(doc, x, scan_article(doc), publisher="P", as_of=AS_OF.isoformat(),
                           taxonomy=load_taxonomy(), client=fake, cache_dir=tmp_path)
    assert [c.label for c in res.calls] == ["1", "2", "3"]  # the bad part's call is costed
    assert [d for d in res.dropped if d.startswith("part 3:")] == [
        "part 3: the answer failed as a whole (figure_reviews: Input should be a valid list) "
        "— recovered field by field:",
        "part 3: figure_reviews: the whole field discarded — 10 characters of text where a list "
        "belongs, not valid JSON (Expecting value: line 1 column 1, character 0)"]
    reviewed = {r.figure_id for r in res.output.figure_reviews}
    assert "b008#9%" not in reviewed  # part 3's figure keeps no verdict
    assert any(n.startswith("part 3: recovered") for n in res.notes)


# --- a malformed FIELD costs that field (2026-10-12) ------------------------------------------

#: the REAL shape: Citi Gridlock's completeness part 4 of 13 gave `added_hypotheses` as 4,420
#: characters of text that is not valid JSON (an object where a key belonged)
BROKEN_HYPOTHESES = ('[{"local_id": "hx2_1", "title": "Charlie re-rating", "bottom_line_fact": '
                     '{"text": "t", "claim_ids": ["k2_1"]}, {"text": "u"}}]')


class _MalformedPart(FakeLlm):
    """Part 2 answers in the real malformed shape, beside a VALID added claim; `fixed` answers
    the same request well formed (a re-ask)."""

    def __init__(self, *a: Any, fixed: bool = False, **k: Any) -> None:
        super().__init__(*a, **k)
        self.fixed = fixed

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        out = super().extract(system=system, user=user, tool=tool, cache=cache)
        m = re.search(r"This is part (\w+):", user)
        if tool["name"] == "record_article_evidence" or not m or m.group(1) != "2":
            return out
        out["added_claims"] = [claim("k2_1", "b003", "unit revenue rose 4%",
                                     "Charlie unit revenue +4%", value=4, value_text="4%",
                                     unit="%", period="2026")]
        out["added_hypotheses"] = [] if self.fixed else BROKEN_HYPOTHESES
        return out


def _run(doc: Any, client: Any, cache: Path, **kw: Any) -> Any:
    return run_completeness(doc, Extraction.model_validate(_pass1(bad_items=False)),
                            scan_article(doc), publisher="P", as_of=AS_OF.isoformat(),
                            taxonomy=load_taxonomy(), client=client, cache_dir=cache, **kw)


def test_a_recovered_part_keeps_its_content_out_of_later_requests_and_replays_free(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc = LONG.doc()
    fake = _MalformedPart(_pass1(bad_items=False))
    res = _run(doc, fake, tmp_path)
    assert [c.local_id for c in res.output.added_claims if c.local_id.startswith("b2.")] == [
        "b2.k2_1"]  # the valid claim of the malformed answer is kept
    assert [(lbl, it.local_id, it.title) for lbl, it in res.lost] == [
        ("2", "hx2_1", "Charlie re-rating")]
    assert any("added_hypotheses: the whole field discarded" in d and "hx2_1" in d
               for d in res.dropped)
    # later parts are shown what WHOLE answers added (part 1's k1_1), never the recovered part's
    assert "k1_1" in fake.users["3"] and "k2_1" not in fake.users["3"]
    # so a replay sends every request byte-identical: all from the cache, the same result
    again = _run(doc, None, tmp_path)
    assert all(c.cached for c in again.calls) and again.output == res.output


def test_a_reask_sends_only_that_part_and_keeps_the_paid_original(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc = LONG.doc()
    paid = _MalformedPart(_pass1(bad_items=False))
    _run(doc, paid, tmp_path)
    before = {f.name: f.read_bytes() for f in (tmp_path / "complete").glob("*.json")}
    fixed = _MalformedPart(_pass1(bad_items=False), fixed=True)
    res = _run(doc, None, tmp_path, reask="2", reask_client=fixed)
    assert fixed.calls == ["complete-2"] and fixed.users["2"] == paid.users["2"]
    for name, data in before.items():  # every paid answer kept as it was paid
        assert (tmp_path / "complete" / name).read_bytes() == data
    assert len(list((tmp_path / "complete").glob("*.reask-1.json"))) == 1
    assert any("re-asked answer" in n for n in res.notes)
    # the paid answer NAMED hx2_1; the re-asked answer proposed nothing — still accounted for,
    # as lost with why (2026-10-12: Gridlock's regulatory-reform proposition, re-asked away)
    assert [(lbl, it.local_id, it.title) for lbl, it in res.lost] == [
        ("2", "hx2_1", "Charlie re-rating")]
    assert "did not propose it again" in res.lost[0][1].note
    assert [c.label for c in res.calls if not c.cached] == ["2"]


def test_a_reask_that_proposes_a_lost_item_again_does_not_list_it_as_lost(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc = LONG.doc()
    _run(doc, _MalformedPart(_pass1(bad_items=False)), tmp_path)
    again = _MalformedPart(_pass1(bad_items=False), fixed=True)
    good = hyp("hx2_1", "Charlie re-rating", node="ai_infrastructure",
               mechanism="valuation_rerating", supporting=["k2_1"])
    orig = again.extract

    def _with_hyp(**k: Any) -> dict[str, Any]:
        out = orig(**k)
        if k["tool"]["name"] != "record_article_evidence":
            out["added_hypotheses"] = [good]
        return out

    again.extract = _with_hyp  # type: ignore[method-assign]
    res = _run(doc, None, tmp_path, reask="2", reask_client=again)
    assert not [it for _l, it in res.lost if it.local_id == "hx2_1"]


def test_a_whole_answer_is_never_re_asked(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc = LONG.doc()
    _run(doc, FakeLlm(_pass1(bad_items=False)), tmp_path)  # every part well formed
    again = FakeLlm(_pass1(bad_items=False))
    with pytest.raises(RuntimeError, match="valid as a whole — nothing to re-ask"):
        _run(doc, None, tmp_path, reask="2", reask_client=again)
    assert again.calls == []


def test_a_reask_sends_nothing_when_another_part_cannot_be_reproduced(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.theme_intelligence.completeness import (
        COMPLETE_PROMPT_VERSION,
        completeness_system,
        completeness_tool,
    )
    from vinci.theme_intelligence.extract import cache_key

    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 6)
    doc = LONG.doc()
    paid = _MalformedPart(_pass1(bad_items=False))
    _run(doc, paid, tmp_path)
    tax = load_taxonomy()
    key3 = cache_key(paid.model, COMPLETE_PROMPT_VERSION, completeness_tool(tax),
                     completeness_system(tax), paid.users["3"])
    (tmp_path / "complete" / f"{key3}.json").unlink()  # part 3 can no longer be reproduced
    fixed = _MalformedPart(_pass1(bad_items=False), fixed=True)
    with pytest.raises(RuntimeError, match="no cached completeness pass"):
        _run(doc, None, tmp_path, reask="2", reask_client=fixed)
    assert fixed.calls == []  # nothing sent
