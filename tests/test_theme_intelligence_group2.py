"""Group 2 of the verified review leads — money (`docs/records/2026-10-14-theme-intelligence-
unverified-leads-verified.md`, U23a-c; U23d was fixed with company matching, #711):

- U23a: `reask-part --max-cost 1.00` refused a $0.90 call — one re-asked part was held to a
  retry's 85% share of the limit the operator set for that one call.
- U23b: `enrich --refresh` "asks again", and made no model call — the paid answer is reused, by
  the repo's rule for paid answers; the flag now says so.
- U23c: a truncation marker written at a 16,384-token cap still forced COMPACT after the cap was
  raised to 64,000 — a marker holds at the cap it was written at.

The model is a stand-in returning the REAL tools' shapes; documents are the synthetic MS fixture,
the hypothetical long article, or the authentic J.P. Morgan fixture.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_budget import MS_PDF, _pipe
from tests.test_theme_intelligence_enrichment import ANSWER, StandIn
from tests.test_theme_intelligence_enrichment import _memory_thesis as _enrichable
from tests.test_theme_intelligence_long_articles import LONG, FakeLlm, _pass1
from tests.theme_intelligence_support import JPM_AS_OF, jpm_document, jpm_extraction
from vinci.theme_intelligence import completeness as completeness_mod
from vinci.theme_intelligence.__main__ import main
from vinci.theme_intelligence.budget import BudgetExceeded, GuardedClient, SpendGuard
from vinci.theme_intelligence.completeness import run_completeness, scan_article
from vinci.theme_intelligence.config import (
    DOC_RETRY_COMPLETENESS_SHARE,
    EXTRACT_PROMPT_VERSION,
    LLM_MODEL,
    load_taxonomy,
)
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.extract import (
    Extraction,
    cache_key,
    run_extraction,
    system_prompt,
    tool_schema,
    user_message,
)
from vinci.theme_intelligence.ingest import ingest_file, reask_part
from vinci.theme_intelligence.llm import ThemeLlmClient

# --- U23a: one re-asked part may take the whole limit set for it -------------------------------


def _ingested(tmp_path: Path) -> tuple[Any, FakeLlm, str, float]:
    """A supplied report analysed through the real pipeline, its one completeness answer broken
    as a whole (what `reask-part` is for); that call's bound. The re-asked answer is valid."""
    fake = FakeLlm(_pass1(bad_items=False), invalid=frozenset({""}))
    pipe = _pipe(tmp_path, fake)
    pipe.start_run("ingest", as_of=date(2026, 10, 11))
    res = ingest_file(pipe, MS_PDF, Declared(source_id="ms_research", llm_permitted=True),
                      as_of=date(2026, 10, 11))
    assert res.status == "INGESTED"
    (bound,) = [c["bound_usd"] for c in pipe.guard.calls if c["kind"] == "completeness"]
    fake.invalid = frozenset()
    return pipe, fake, res.doc_id, bound


def test_a_reask_may_take_the_whole_limit_set_for_it(tmp_path: Path) -> None:
    """POSITIVE: --max-cost sized so the call takes 90% of it — above a retry's 85% share, which
    main applied, refusing it. The one call is sent."""
    pipe, fake, doc_id, bound = _ingested(tmp_path)
    assert bound / 0.9 * DOC_RETRY_COMPLETENESS_SHARE < bound  # main's share would refuse it
    before = len(fake.calls)
    reask_part(pipe, doc_id, "", max_cost=bound / 0.9)
    assert fake.calls[before:] == ["complete"]


def test_a_reask_over_its_limit_is_still_refused(tmp_path: Path) -> None:
    """NEGATIVE: a call bounded above the whole limit is never sent."""
    pipe, fake, doc_id, bound = _ingested(tmp_path)
    before = len(fake.calls)
    with pytest.raises(BudgetExceeded, match="does not fit"):
        reask_part(pipe, doc_id, "", max_cost=bound * 0.95)
    assert len(fake.calls) == before


def test_a_documents_completeness_still_takes_only_its_share() -> None:
    """NEGATIVE: an ordinary document's completeness pass keeps its share of the limit."""
    g = SpendGuard(run_limit=100.0)
    g.begin_document("A-1", 1.0)
    with pytest.raises(BudgetExceeded, match="retry / completeness limit"):
        g.check(0.9, "completeness")
    g.begin_document("D-1 part 4", 1.0, retry_share=1.0)
    g.check(0.9, "completeness")  # one re-asked part: the whole limit


# --- U23b: --refresh says what it does ---------------------------------------------------------

def test_refresh_says_the_paid_answer_comes_from_the_cache(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The behaviour is the repo's rule for paid answers (pinned in the enrichment tests: the
    same request again is answered from the cache, unpaid); the flag, the run's note and the
    docs said "asks again"."""
    with pytest.raises(SystemExit):
        main(["enrich", "--help"])
    shown = " ".join(capsys.readouterr().out.split())
    assert "comes from the cache" in shown and "ask again for a version" not in shown
    pipe, _tid = _enrichable(tmp_path)
    pipe.client = GuardedClient(StandIn(ANSWER), pipe.guard)
    pipe.run_enrich(as_of=JPM_AS_OF)
    _run, done = pipe.run_enrich(as_of=JPM_AS_OF)
    assert "the paid answer comes from the cache" in done[0][1]
    assert "asks again" not in done[0][1]
    doc = (Path(__file__).resolve().parent.parent / "docs" / "theme_intelligence.md").read_text()
    assert "`--refresh` asks again" not in doc


# --- U23c: a truncation marker holds at the cap it was written at ------------------------------

class Capped:
    """A client with an output cap; answers the extraction (compact or not) — records which."""

    model = LLM_MODEL

    def __init__(self, cap: int | None) -> None:
        if cap is not None:
            self.max_tokens = cap
        self.compact: list[bool] = []
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_kw: Any) -> dict[str, Any]:
        self.compact.append("COMPACT MODE" in system)
        self.last_usage = {"input_tokens": 1000, "output_tokens": 400}
        return jpm_extraction()


def _marked(cache: Path, cap: int | None) -> None:
    tax = load_taxonomy()
    key = cache_key(LLM_MODEL, EXTRACT_PROMPT_VERSION, tool_schema(tax), system_prompt(tax),
                    user_message(jpm_document(), publisher="J.P. Morgan", as_of="2026-02-09"))
    m = cache / "extract" / f"{key}.truncated.json"
    m.parent.mkdir(parents=True, exist_ok=True)
    usage: dict[str, int] = {"output_tokens": 16_384}
    if cap is not None:
        usage["max_tokens"] = cap
    m.write_text(json.dumps({"model": LLM_MODEL, "prompt_version": EXTRACT_PROMPT_VERSION,
                             "usage": usage, "error": "truncated"}))


def _extract(cache: Path, client: Any) -> Any:
    return run_extraction(jpm_document(), publisher="J.P. Morgan", as_of="2026-02-09",
                          taxonomy=load_taxonomy(), client=client, cache_dir=cache)


def test_a_raised_cap_asks_the_full_request_again(tmp_path: Path) -> None:
    """POSITIVE: the marker was written at 16,384; the client (behind the spend guard, as in
    production) now has 64,000 — the full request is sent. Main sent the COMPACT one."""
    _marked(tmp_path, 16_384)
    inner = Capped(64_000)
    res = _extract(tmp_path, GuardedClient(inner, SpendGuard(run_limit=100.0)))
    assert inner.compact == [False] and not res.compact


@pytest.mark.parametrize(("marker_cap", "client_cap"), [
    (16_384, 16_384),  # the same cap: no full answer fits — COMPACT, unpaid for the full request
    (21_333, 16_384),  # a LOWER cap: the same
    (None, 64_000),  # a marker stating no cap: it holds, never a paid re-ask on a guess
    (16_384, None),  # a client stating no cap: the same
])
def test_a_marker_holds_unless_the_cap_was_raised(
        tmp_path: Path, marker_cap: int | None, client_cap: int | None) -> None:
    """NEGATIVE."""
    _marked(tmp_path, marker_cap)
    inner = Capped(client_cap)
    res = _extract(tmp_path, GuardedClient(inner, SpendGuard(run_limit=100.0)))
    assert inner.compact == [True] and res.compact


def test_the_real_client_states_its_cap() -> None:
    """The cap is read from the client the CLI builds — a key is needed to construct it, never
    used: no request is made."""
    assert ThemeLlmClient(model=LLM_MODEL, max_tokens=64_000, api_key="sk-test").max_tokens == \
        64_000


class CappedLlm(FakeLlm):
    """`FakeLlm` with a cap: a truncation reports it, as the real client does."""

    def __init__(self, cap: int, **kw: Any) -> None:
        super().__init__(_pass1(bad_items=False), **kw)
        self.max_tokens = cap

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        try:
            return super().extract(system=system, user=user, tool=tool, cache=cache)
        finally:
            if self.last_usage is not None:
                self.last_usage = {**self.last_usage, "max_tokens": self.max_tokens}


def _complete(cache: Path, client: Any) -> Any:
    doc = LONG.doc()
    return run_completeness(doc, Extraction.model_validate(_pass1(bad_items=False)),
                            scan_article(doc), publisher="P", as_of="2026-10-02",
                            taxonomy=load_taxonomy(), client=client, cache_dir=cache)


@pytest.mark.parametrize(("cap", "asked"), [
    (64_000, ["complete"]),  # POSITIVE: a raised cap asks the whole review again (main: split)
    (16_384, []),  # NEGATIVE: the same cap — split, every part from the cache
])
def test_a_completeness_marker_holds_at_its_cap(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cap: int, asked: list[str]) -> None:
    monkeypatch.setattr(completeness_mod, "GAPS_PER_CALL", 1000)  # one whole call
    first = CappedLlm(16_384, truncate=frozenset({""}))
    _complete(tmp_path, first)
    assert first.calls[0] == "complete" and len(first.calls) > 1  # truncated, then split
    again = CappedLlm(cap)
    _complete(tmp_path, again)
    assert again.calls == asked
