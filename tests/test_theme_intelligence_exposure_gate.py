"""The exposure gate and what WATCH waits for (operator, 2026-10-16: "the three themes generated out
of [J.P. Morgan's Software Shock] were all marked as WATCH which doesn't mean anything").

- A named listed company resolved before point-in-time verification existed stayed "not verified"
  for good; it is resolved again as of the date (`Engine.relist`), and a later naming's verified
  listing is no longer shadowed by an earlier stale one (`affected_from`).
- An ETF, index or cited basket the source attaches to a thesis is its exposure — the form a
  sector view is expressed through (`cards.counted_exposures`, one definition for every path and
  surface).
- A WATCH carries its unmet conditions as values: MISSING DATA (the record could not establish
  it) or a SUBSTANTIVE HOLD (the evidence falls short), so the label reads "Watch · needs data" or
  "Watch · on hold" — derived from the stored factor values for a version stored before.

The real article is the committed `jpm_software_shock` fixture (frozen model output and SEC
subset); constructed records use the REAL types.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import (
    CALM_AS_OF,
    CALM_DIR,
    JPM_AS_OF,
    JPM_DIR,
    FrozenSecHttp,
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    ingest_calm,
    ingest_jpm,
    make_pipeline,
    mention,
)
from vinci.netcache import HttpError
from vinci.theme_intelligence.cards import (
    BROAD_INSTRUMENTS,
    INDICATOR_INSTRUMENTS,
    INSTRUMENT_EXPOSURES,
    NAMED_INSTRUMENTS,
    NOT_SECTORS,
    affected_from,
    broad_market_instruments,
    counted_exposures,
    exposure_instruments,
    is_broad_market,
    is_market_indicator,
    market_indicators,
    not_a_sector,
    watch_of,
    why_reasons,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.priority import (
    ThesisState,
    compute_priority,
    exposures_counted,
    watch_label,
    watch_reasons_of,
)
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import (
    AffectedCompany,
    AffectedView,
    Claim,
    ClaimKind,
    Confidence,
    Direction,
    EntityType,
    Epistemic,
    EvidenceDirection,
    Horizon,
    Listing,
    Mention,
    MentionRole,
    PitStatus,
    PriorityFactor,
    Provenance,
    RecommendationStatus,
    ResearchAction,
    ResolutionStatus,
    RetrievalState,
    RunStatus,
    SectorExposure,
    SecurityResolution,
    StanceInSource,
    TransmissionStep,
)
from vinci.theme_intelligence.securities import SecResolver

AS_OF = date(2026, 10, 11)


def _co(name: str, role: MentionRole, status: ResolutionStatus, *tickers: str,
        verified: bool = True) -> AffectedCompany:
    pit = PitStatus.VERIFIED if verified else PitStatus.UNVERIFIED
    return AffectedCompany(
        mention_id=f"M-{name}", name_as_written=name, resolution_status=status,
        listings=tuple(Listing(ticker=t, exchange="NYSE", pit_status=pit) for t in tickers),
        cik=None, role=role, role_detail="", direction=Direction.POSITIVE,
        recommendation_status=RecommendationStatus.NOT_A_RECOMMENDATION, article_id="A-x",
        quote="[HYPOTHETICAL]")


def _view(**kw: Any) -> AffectedView:
    return AffectedView(**{"companies": (), "instruments": (), "sectors": (), "baskets": (),
                           "private_or_unlisted": (), **kw})


# --- one definition of a counted exposure ----------------------------------------------------

def test_an_etf_index_or_basket_the_source_attaches_is_an_exposure() -> None:
    igv = _co("iShares Expanded Tech-Software Sector ETF (IGV)", MentionRole.MARKET_INSTRUMENT,
              ResolutionStatus.FUND, "IGV")
    idx = _co("S&P 500 Software Index", MentionRole.CITED_BASKET, ResolutionStatus.INDEX)
    basket = _co("AI Usage basket", MentionRole.CITED_BASKET, ResolutionStatus.NOT_A_SECURITY)
    ce = counted_exposures(_view(instruments=(igv, idx), not_securities=(basket,)))
    assert ce.instruments == ("iShares Expanded Tech-Software Sector ETF (IGV)",
                              "S&P 500 Software Index", "AI Usage basket")  # IGV printed once


def test_an_instrument_named_only_as_context_or_never_attached_is_not() -> None:
    """NEGATIVE: the S&P 500 as context, an ETF merely named in the article (also_named), and a
    product that is not a security."""
    spx = _co("S&P 500", MentionRole.CONTEXT, ResolutionStatus.INDEX)
    igv = _co("IGV", MentionRole.MARKET_INSTRUMENT, ResolutionStatus.FUND, "IGV")
    product = _co("Claude Code", MentionRole.DISRUPTOR, ResolutionStatus.NOT_A_SECURITY)
    ce = counted_exposures(_view(instruments=(spx,), also_named=(igv,), not_securities=(product,)))
    assert ce.instruments == ()


def test_a_listing_not_verified_as_of_the_date_is_never_counted_but_is_named() -> None:
    meta = _co("Meta", MentionRole.SPENDING_CUSTOMER, ResolutionStatus.LISTED_EQUITY, "META",
               verified=False)
    msft = _co("Microsoft", MentionRole.SPENDING_CUSTOMER, ResolutionStatus.LISTED_EQUITY, "MSFT")
    ce = counted_exposures(_view(companies=(meta, msft)))
    assert ce.listed == (("Microsoft", "MSFT"),) and ce.unverified == ("Meta",)


META_CIK = "0001326801"
_LATER = Mention(mention_id="M-new", article_id="A-y", article_version_id="AV-y",
                 name_as_written="Meta Platforms", normalized_name="meta platforms",
                 entity_type=EntityType.COMPANY, role=MentionRole.SPENDING_CUSTOMER,
                 role_detail="", direction=Direction.POSITIVE,
                 recommendation_status=RecommendationStatus.NOT_A_RECOMMENDATION,
                 block_id="b001", quote="[HYPOTHETICAL] Meta Platforms raised capex",
                 ticker_hint="META")


def _resolution(verified: bool) -> SecurityResolution:
    """The resolver's two real shapes: a verified common-equity line, or none — the line kept
    unverified for the audit (securities.SecResolver.resolve)."""
    line = Listing(ticker="META", exchange="Nasdaq",
                   pit_status=PitStatus.VERIFIED if verified else PitStatus.UNVERIFIED)
    return SecurityResolution(
        resolution_id=f"SR-{verified}", normalized_name="meta platforms",
        status=ResolutionStatus.LISTED_EQUITY, cik=META_CIK, method="test", source_ref="test",
        listings=(line,) if verified else (), other_securities=() if verified else (line,),
        resolved_at=datetime.now(tz=UTC))


def _named_later(first: AffectedCompany, *, verified: bool) -> AffectedCompany:
    av = affected_from(mention_ids=[("M-new", "")], mentions={"M-new": _LATER},
                       resolutions={"M-new": _resolution(verified)}, sectors=[], baskets=[],
                       prev=_view(companies=(first,)))
    (c,) = av.companies  # one entity (its CIK) across the two namings
    return c


def test_a_later_verified_naming_replaces_a_stale_listing_and_keeps_the_first_naming() -> None:
    """A stale "not verified" from an earlier article shadowed the verified listing a later one
    resolved: now the first naming (its article, quote) is kept with the VERIFIED listing."""
    stale = _co("Meta", MentionRole.SPENDING_CUSTOMER, ResolutionStatus.LISTED_EQUITY, "META",
                verified=False).model_copy(update={"cik": META_CIK})
    c = _named_later(stale, verified=True)
    assert (c.mention_id, c.quote) == (stale.mention_id, stale.quote)
    assert [(x.ticker, x.pit_status) for x in c.listings] == [("META", PitStatus.VERIFIED)]


def test_a_later_unverified_naming_replaces_nothing() -> None:
    """NEGATIVE: a later naming whose listing is NOT verified leaves the earlier record exactly as
    it was — verified or not."""
    for verified in (True, False):
        first = _co("Meta", MentionRole.SPENDING_CUSTOMER, ResolutionStatus.LISTED_EQUITY,
                    "META", verified=verified).model_copy(update={"cik": META_CIK})
        assert _named_later(first, verified=False) == first


# --- WATCH says what it waits for ------------------------------------------------------------

def _claim(cid: str, quote: str, *, kind: ClaimKind = ClaimKind.METRIC,
           epistemic: Epistemic = Epistemic.ACTUAL, period: str = "Q3 2026") -> Claim:
    return Claim(claim_id=cid, article_id="A-x", article_version_id="AV-x", block_id="b001",
                 char_start=0, char_end=len(quote), quote=quote, statement=quote, kind=kind,
                 epistemic=epistemic, period=period, value=9.0, value_text="9%",
                 confidence=Confidence.HIGH, span_verified=True, number_verified=True,
                 measure_key=f"k|{cid}", fingerprint=f"f|{cid}", extraction_id="X-1",
                 measured_as_of=date(2026, 9, 30))


def _state(**kw: Any) -> ThesisState:
    step = TransmissionStep(step="pricing", text="contract prices rise",
                            provenance=Provenance.MEASURED_OBSERVATION, claim_ids=("c1",))
    base: dict[str, Any] = {
        "reliability": "medium", "counter": (), "catalyst": (), "listed_exposures": (),
        "supporting": (_claim("c1", "Memory contract prices rose 9% in Q3 2026"),),
        "dislocation": (_claim("d1", "The memory index fell 30% in Q3 2026"),),
        "instrument_exposures": (), "transmission": (step,),
        "horizon": Horizon.NEXT_2_4_QUARTERS, "stance": StanceInSource.ASSERTED,
        "verification_hold": False, "hold_reasons": (), "retrieval": RetrievalState.FULL,
        "sector_exposures": (), "as_of": AS_OF}
    return ThesisState(**{**base, **kw})


@pytest.mark.parametrize(("kw", "action", "codes", "label"), [
    ({"instrument_exposures": ("IGV",)}, ResearchAction.RESEARCH_NOW, [], ""),
    ({"unverified_listings": ("Meta",)}, ResearchAction.WATCH, ["listing_unverified"],
     "needs data"),
    ({"sector_exposures": ("Memory",), "retrieval": RetrievalState.PARTIAL},
     ResearchAction.WATCH, ["partial_text"], "needs data"),
    ({"sector_exposures": ("Memory",), "stance": StanceInSource.CONDITIONAL},
     ResearchAction.WATCH, ["premise_conditional"], "on hold"),
    ({}, ResearchAction.WATCH, ["no_exposure"], "on hold"),
    ({"unverified_listings": ("Meta",), "stance": StanceInSource.CONDITIONAL},
     ResearchAction.WATCH, ["listing_unverified", "premise_conditional"], "on hold"),
])
def test_a_watch_states_whether_it_needs_data_or_is_held(
        kw: dict[str, Any], action: ResearchAction, codes: list[str], label: str) -> None:
    pr = compute_priority(_state(**kw), previous=None, evidence_direction=EvidenceDirection.NEW)
    assert pr.research_action is action
    assert [r.code for r in pr.watch_reasons] == codes
    assert watch_label(pr.watch_reasons) == label


@pytest.mark.parametrize("kw", [
    {"unverified_listings": ("Meta",)}, {"sector_exposures": ("Memory",),
                                          "retrieval": RetrievalState.PARTIAL},
    {"sector_exposures": ("Memory",), "stance": StanceInSource.SPECULATIVE},
    {}, {"sector_exposures": ("Memory",), "dislocation": (), "verification_hold": True,
         "hold_reasons": ("c1 failed span verification",)},
    {"sector_exposures": ("Memory",), "reliability": "low"},
])
def test_a_version_stored_before_the_reasons_derives_the_same_ones(kw: dict[str, Any]) -> None:
    """The derivation from the stored factor VALUES (an older version) agrees, code for code and
    kind for kind, with what the rule now stores."""
    st = _state(**kw)
    pr = compute_priority(st, previous=None, evidence_direction=EvidenceDirection.NEW)
    old = pr.model_copy(update={"watch_reasons": ()})
    derived = watch_reasons_of(old, st.unverified_listings)
    assert [(r.code, r.kind) for r in derived] == [(r.code, r.kind) for r in pr.watch_reasons]


def test_the_stored_exposure_count_reads_both_value_shapes() -> None:
    def pr(value: str) -> Any:
        base = compute_priority(_state(), previous=None, evidence_direction=EvidenceDirection.NEW)
        return base.model_copy(update={"factors": (PriorityFactor(
            factor_id="F6_recognizable_exposures", value=value, note=""),)})

    assert exposures_counted(pr("0 listed · 0 sector")) == 0  # stored before 2026-10-16
    assert exposures_counted(pr("2 listed · 1 sector")) == 3
    assert exposures_counted(pr("0 listed · 0 sector · 2 instrument")) == 2


# --- the real article ----------------------------------------------------------------------------

def _jpm(tmp_path: Path) -> Pipeline:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    return pipe


def test_the_software_shock_theses_say_why_they_are_watch(tmp_path: Path) -> None:
    """J.P. Morgan's Software Shock (committed fixture): three WATCH theses that "didn't mean
    anything". Each is now ON HOLD with its reason — the evidence falls short, not the data: two
    have no verified mispricing or dated catalyst, the software one a conditional premise. The
    software thesis's ETF and index COUNT as its exposure."""
    pipe = _jpm(tmp_path)
    got = {}
    for t in pipe.store.theses():
        v = pipe.store.thesis_version(t.thesis_id, t.current_version)
        assert v is not None
        ce = counted_exposures(v.content.s05_affected)
        got[t.thesis_id] = (v.priority.research_action,
                            watch_of(v.priority, v.content.s05_affected),
                            [r.code for r in v.priority.watch_reasons], ce)
    assert {a for a, _w, _c, _e in got.values()} == {ResearchAction.WATCH}
    assert all(w == "on hold" for _a, w, _c, _e in got.values())
    assert sorted(c for _a, _w, c, _e in got.values()) == [
        ["no_catalyst"], ["no_catalyst"], ["premise_conditional"]]  # the frozen model output
    software = next(x for x in got.values() if "premise_conditional" in x[2])
    assert any("IGV" in i for i in software[3].instruments)  # its ETF is its exposure
    assert "no_exposure" not in software[2]


class NoCovers(FrozenSecHttp):
    """The frozen SEC subset with every filing's cover page unreachable: the REAL resolver then
    records each listing "not point-in-time verified", in its real shape (no listing; the line
    kept unverified for the audit)."""

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        raise HttpError(f"cover page unreachable in this test: {url}")


def _resolver(tmp_path: Path, name: str, http: FrozenSecHttp) -> SecResolver:
    return SecResolver(tmp_path / name, http=http)  # type: ignore[arg-type]


def _stale_registry(tmp_path: Path) -> tuple[Pipeline, str]:
    """The real article ingested while no cover page could be read — every listing stored "not
    verified", as in the 2026-10-11 registries — then a fresh resolver, as the next process has.
    Returns the pipeline and the hyperscalers' thesis id."""
    pipe = make_pipeline(tmp_path)
    pipe.resolver = _resolver(tmp_path, "sec-down", NoCovers(JPM_DIR))
    pipe.start_run("fixture", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.resolver = _resolver(tmp_path, "sec-up", FrozenSecHttp(JPM_DIR))
    (hyper,) = [t.thesis_id for t in pipe.store.theses()
                if any(c.name_as_written == "Meta" for c in _current(pipe, t.thesis_id)
                       .content.s05_affected.companies)]
    return pipe, hyper


def _current(pipe: Pipeline, tid: str) -> Any:
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    return v


def test_a_stale_listing_is_verified_again_when_the_thesis_is_reassessed(tmp_path: Path) -> None:
    """The four hyperscalers' listings stored "not verified" (the 2026-10-11 registries) count
    for nothing. A reassess resolves them again as of the date: each verifies from its own
    filing, and they count (F6: 2 sectors -> 4 listed + 2 sectors)."""
    pipe, hyper = _stale_registry(tmp_path)
    v = _current(pipe, hyper)
    before = counted_exposures(v.content.s05_affected)
    assert before.listed == () and {"Meta", "Amazon", "Microsoft"} <= set(before.unverified)
    assert exposures_counted(v.priority) == len(before.sectors) == 2
    pipe.run_reassess(as_of=JPM_AS_OF, thesis_ids=[hyper])
    v = _current(pipe, hyper)
    after = counted_exposures(v.content.s05_affected)
    assert {"Meta", "Amazon", "Alphabet", "Microsoft"} <= {n for n, _ in after.listed}
    assert after.unverified == () and exposures_counted(v.priority) == len(after.listed) + 2


def test_with_no_resolver_hook_a_reassess_keeps_the_stored_listing(tmp_path: Path) -> None:
    """NEGATIVE: with no re-check the stored "not verified" listing stands, and is never
    counted."""
    pipe, hyper = _stale_registry(tmp_path)
    pipe.engine.relist = None
    pipe.run_reassess(as_of=JPM_AS_OF, thesis_ids=[hyper])
    assert counted_exposures(_current(pipe, hyper).content.s05_affected).listed == ()


def test_a_listing_that_still_cannot_be_verified_changes_nothing(tmp_path: Path) -> None:
    """NEGATIVE: re-resolved and STILL not verified — the record stays as it was (no version)."""
    pipe, hyper = _stale_registry(tmp_path)
    pipe.resolver = _resolver(tmp_path, "sec-down-again", NoCovers(JPM_DIR))
    n = pipe.store.thesis(hyper).current_version  # type: ignore[union-attr]
    pipe.run_reassess(as_of=JPM_AS_OF, thesis_ids=[hyper])
    assert pipe.store.thesis(hyper).current_version == n  # type: ignore[union-attr]


def test_a_failed_re_check_returns_the_stored_record_unchanged(tmp_path: Path) -> None:
    """NEGATIVE, at the hook: a re-resolution that still verifies nothing returns the company as
    stored — in either stored shape (a pre-2026-10-11 record carried its unverified line AS its
    listing) — never the new resolution's shape (that would be a version that changes nothing)."""
    pipe, hyper = _stale_registry(tmp_path)
    pipe.resolver = _resolver(tmp_path, "sec-down-again", NoCovers(JPM_DIR))
    meta = next(c for c in _current(pipe, hyper).content.s05_affected.companies
                if c.name_as_written == "Meta")
    old_shape = meta.model_copy(update={"listings": meta.other_securities[:1],
                                        "other_securities": ()})
    assert old_shape.listings and not meta.listings  # the two shapes, really
    for c in (meta, old_shape):
        assert pipe._relist(c, JPM_AS_OF) == c


# --- the surfaces ---------------------------------------------------------------------------------

def test_the_card_and_the_desk_name_what_a_watch_waits_for(tmp_path: Path) -> None:
    """End to end: the card's header and decision, and the desk's thesis page, Themes table and
    This week, print "Watch · on hold" for the real article's theses."""
    pipe = _jpm(tmp_path)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    assert _text(out / "themes.html").count("Watch · on hold") == 3
    for p in (out / "theses").glob("TH-*.html"):
        page = _text(p)
        assert "Watch · on hold" in page and "Why Watch · on hold" in page
    for p in (out / "cards").glob("TH-*.html"):
        assert _text(p).count("Watch · on hold") >= 2  # the header and the decision


def _rows_under(card: BeautifulSoup, heading: str) -> list[Any]:
    """The card's table rows under one section-05 heading (none when it reads "None named.")."""
    sub = card.find("div", class_="sub", string=heading)
    assert sub is not None, heading
    box = sub.find_next_sibling()
    assert box is not None, heading
    return [tr for tr in box.select("tr") if tr.td is not None]


def _names_under(card: BeautifulSoup, heading: str) -> list[str]:
    return [tr.td.get_text() for tr in _rows_under(card, heading)]


def _text(p: Path) -> str:
    return re.sub(r"\s+", " ", BeautifulSoup(p.read_text(), "html.parser").get_text(" "))


def test_every_surface_lists_the_instruments_the_count_takes(tmp_path: Path) -> None:
    """The count, the desk's Who is exposed, the card's section 05 (HTML and Markdown) and the
    dashboard row name the SAME instruments as the thesis's exposure. On 2026-10-16 the count
    took J.P. Morgan's software ETF and index while the card and the desk still listed them as
    "named, not exposures" — the page contradicted its own Watch box. NEGATIVE: an instrument
    the thesis does not attach stays a mention. And a WHOLE-MARKET index the thesis attaches (J.P.
    Morgan's "S&P 500", operator ruling 2026-10-16) is named on every surface under its own words
    and never among the exposures."""
    pipe = _jpm(tmp_path)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    res = write_run_outputs(pipe.store, run.run_id, tmp_path / "out")
    out = Path(res["dir"])
    rows = {r.thesis_id: r for rs in res["dashboard"].categories.values() for r in rs}
    taken = whole = 0
    for t in pipe.store.theses():
        av = _current(pipe, t.thesis_id).content.s05_affected
        inst = [c.name_as_written for c in exposure_instruments(av)]
        broad = [c.name_as_written for c in broad_market_instruments(av)]
        loose = [c.name_as_written for c in av.instruments
                 if c.name_as_written not in inst and c.name_as_written not in broad]
        taken += len(inst)
        whole += len(broad)
        page = BeautifulSoup((out / "theses" / f"{t.thesis_id}.html").read_text(), "html.parser")
        who = next(x for x in page.select("section.panel")
                   if x.h2 is not None and x.h2.get_text() == "Who is exposed")
        listed = [li.b.get_text() for li in who.select("ul.who li") if li.b is not None]
        also = " ".join(x.get_text(" ") for x in who.select("p")
                        if x.get_text().startswith("Also named"))
        card = BeautifulSoup((out / "cards" / f"{t.thesis_id}.html").read_text(), "html.parser")
        md = (out / "cards" / f"{t.thesis_id}.md").read_text().split("## 05")[1]
        md_attached = md.split(f"**{INSTRUMENT_EXPOSURES}:**")[1].split(
            f"**{NAMED_INSTRUMENTS}:**")[0]
        md_counted = md_attached.split(f"**{BROAD_INSTRUMENTS}:**")[0]
        for n in inst:
            assert n in listed and f"{n} (" not in also, (t.thesis_id, n)
            assert n in _names_under(card, INSTRUMENT_EXPOSURES), (t.thesis_id, n)
            assert f"- {n} — " in md_counted, (t.thesis_id, n)
            assert any(x.startswith(f"{n} [") for x in rows[t.thesis_id].named_instruments)
        for n in broad:
            assert n not in listed and f"{n} (broad market index — not counted)" in also
            assert n in _names_under(card, BROAD_INSTRUMENTS)
            assert n not in _names_under(card, INSTRUMENT_EXPOSURES)
            assert n not in _names_under(card, NAMED_INSTRUMENTS)  # attached, never "not attached"
            assert f"- {n} — " in md_attached.split(f"**{BROAD_INSTRUMENTS}:**")[1]
            assert f"- {n} — " not in md_counted
            row = rows[t.thesis_id]  # named ONCE, labelled — never "not attached" (REVIEW)
            assert not any(x.startswith(f"{n} [") for x in row.named_instruments)
            assert [x for x in row.other_named if x.startswith(f"{n} [")] == [
                f"{n} [broad market index — not counted]"]
        assert loose == []  # the fixture attaches every instrument it names: see the next pin
    assert taken >= 2  # the software thesis's ETF and index, at least
    assert whole == 1  # the market-regime thesis's S&P 500



# --- the whole market is no thesis's exposure (operator ruling 2026-10-16) ----------------------

@pytest.mark.parametrize(("name", "status", "tickers", "broad"), [
    # the whole-market instruments attached across 152 local registry copies (2026-10-16)
    ("S&P 500", ResolutionStatus.INDEX, (), True),
    ("Ibovespa", ResolutionStatus.INDEX, (), True),
    ("IPC", ResolutionStatus.INDEX, (), True),
    ("Colcap", ResolutionStatus.INDEX, (), True),
    ("BVL", ResolutionStatus.INDEX, (), True),
    # constructed: the same index written another way, and a fund that tracks it
    ("The S&P 500 Index", ResolutionStatus.INDEX, (), True),
    ("SPDR S&P 500 ETF Trust", ResolutionStatus.FUND, ("SPY",), True),
    # NEGATIVE — the sector and theme instruments attached in the same copies: matched on the
    # WHOLE name, so an index named after the S&P 500 is still a sector index
    ("S&P 500 Software Index", ResolutionStatus.INDEX, (), False),
    ("S&P 500 Utilities", ResolutionStatus.INDEX, (), False),
    ("S&P 500 AI Usage", ResolutionStatus.NOT_A_SECURITY, (), False),
    ("Magnificent 7", ResolutionStatus.NOT_A_SECURITY, (), False),
    ("iShares Expanded Tech-Software Sector ETF (IGV)", ResolutionStatus.FUND, ("IGV",), False),
])
def test_a_whole_market_index_is_told_from_a_sector_one(
        name: str, status: ResolutionStatus, tickers: tuple[str, ...], broad: bool) -> None:
    assert is_broad_market(_co(name, MentionRole.MARKET_INSTRUMENT, status, *tickers)) is broad


def test_the_whole_market_is_named_and_never_counted() -> None:
    spx = _co("S&P 500", MentionRole.MARKET_INSTRUMENT, ResolutionStatus.INDEX)
    igv = _co("iShares Expanded Tech-Software Sector ETF (IGV)", MentionRole.MARKET_INSTRUMENT,
              ResolutionStatus.FUND, "IGV")
    ce = counted_exposures(_view(instruments=(spx, igv)))
    assert ce.instruments == ("iShares Expanded Tech-Software Sector ETF (IGV)",)
    assert ce.broad == ("S&P 500",)


def test_a_thesis_whose_only_instrument_is_the_whole_market_counts_no_exposure(
        tmp_path: Path) -> None:
    """End to end on the real fixture: J.P. Morgan's market-regime thesis attaches the S&P 500
    and names one sector. Its stored rule counts the sector and NOT the index ("0 instrument");
    with the sector gone — the real shape of TH-5C3B51DF57 in a local registry copy, "0 listed ·
    0 sector · 1 instrument" before the ruling — the gate says why there is no exposure."""
    from vinci.theme_intelligence.desk import NearTerm, gates

    pipe = _jpm(tmp_path)
    pipe.finish_run(RunStatus.SUCCEEDED)
    current = [_current(pipe, t.thesis_id) for t in pipe.store.theses()]
    (v,) = [v for v in current if [c.name_as_written for c in broad_market_instruments(
        v.content.s05_affected)] == ["S&P 500"]]
    f = {x.factor_id: x.value for x in v.priority.factors}  # type: ignore[union-attr]
    assert f["F6_recognizable_exposures"] == "0 listed · 1 sector · 0 instrument"
    av = v.content.s05_affected.model_copy(update={"sector_exposures": ()})
    f6 = PriorityFactor(factor_id="F6_recognizable_exposures",
                        value="0 listed · 0 sector · 0 instrument", note="")
    kept = tuple(x for x in v.priority.factors  # type: ignore[union-attr]
                 if not x.factor_id.startswith("F6")) + (f6,)
    alone = v.model_copy(update={
        "content": v.content.model_copy(update={"s05_affected": av}),
        "priority": v.priority.model_copy(update={"factors": kept})})  # type: ignore[union-attr]
    nt = NearTerm(stored="yes", framing="", claims=(), recomputed="yes", note="")
    g = next(x for x in gates(alone, [], nt) if x.name == "An exposure the source names")
    assert not g.ok and "S&P 500" in g.detail and "whole market" in g.detail
    why = " ".join(why_reasons(alone.content, alone.priority))
    assert "Exposure — only a broad market index (S&P 500)" in why


@pytest.mark.parametrize(("name", "status", "tickers", "indicator"), [
    # attached in 33 current versions of the local registry copies (2026-10-16): Cboe's estimate,
    # from option prices, of how closely the largest S&P 500 stocks will move together
    ("Cboe 3-month implied correlation index", ResolutionStatus.INDEX, (), True),
    # constructed: the volatility family, as an index and as a fund of its futures
    ("Cboe Volatility Index (VIX)", ResolutionStatus.INDEX, (), True),
    ("ProShares VIX Short-Term Futures ETF", ResolutionStatus.FUND, ("VIXY",), True),
    # NEGATIVE — an index or fund that SELECTS stocks by volatility holds stocks
    ("S&P 500 Low Volatility Index", ResolutionStatus.INDEX, (), False),
    ("MSCI USA Minimum Volatility Index", ResolutionStatus.INDEX, (), False),
    ("Invesco S&P 500 Low Volatility ETF", ResolutionStatus.FUND, ("SPLV",), False),
    # REVIEW of #736: the hyphenated spellings are the same stock-holding indices
    ("S&P 500 Low-Volatility Index", ResolutionStatus.INDEX, (), False),
    ("MSCI USA Minimum-Volatility Index", ResolutionStatus.INDEX, (), False),
    # NEGATIVE — the sector instruments attached in the same copies
    ("S&P 500 Software Index", ResolutionStatus.INDEX, (), False),
    ("S&P 500 Utilities", ResolutionStatus.INDEX, (), False),
    ("iShares Expanded Tech-Software Sector ETF (IGV)", ResolutionStatus.FUND, ("IGV",), False),
])
def test_a_market_indicator_is_told_from_a_holding(
        name: str, status: ResolutionStatus, tickers: tuple[str, ...], indicator: bool) -> None:
    c = _co(name, MentionRole.MARKET_INSTRUMENT, status, *tickers)
    assert is_market_indicator(c) is indicator


def test_a_market_indicator_is_named_and_never_counted() -> None:
    cor = _co("Cboe 3-month implied correlation index", MentionRole.MARKET_INSTRUMENT,
              ResolutionStatus.INDEX)
    util = _co("S&P 500 Utilities", MentionRole.SECTOR_EXAMPLE, ResolutionStatus.INDEX)
    ce = counted_exposures(_view(instruments=(cor, util)))
    assert ce.instruments == ("S&P 500 Utilities",) and ce.broad == ()
    assert ce.indicators == ("Cboe 3-month implied correlation index",)


def test_the_calm_index_regime_names_its_index_its_indicator_and_its_non_sector_and_counts_none(
        tmp_path: Path) -> None:
    """End to end on the committed J.P. Morgan "calm index" fixture: the dispersion regime
    attaches the S&P 500 and the Cboe 3-month implied correlation index, and its only "sector" is
    the phrase "at both a sector and thematic level". None of the three is counted — so the
    regime that read Research Now on them is WATCH — and every surface names all three, the gate
    and the why-line giving every reason in one line."""
    from vinci.theme_intelligence.desk import NearTerm, gates

    pipe = make_pipeline(tmp_path / "p", sec_dirs=(CALM_DIR,))
    pipe.start_run("article", as_of=CALM_AS_OF, window_from=CALM_AS_OF, window_to=CALM_AS_OF)
    ingest_calm(pipe)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    res = write_run_outputs(pipe.store, run.run_id, tmp_path / "out")
    out = Path(res["dir"])
    current = [_current(pipe, t.thesis_id) for t in pipe.store.theses()]
    (v,) = [v for v in current if market_indicators(v.content.s05_affected)]
    cor, spx = "Cboe 3-month implied correlation index", "S&P 500"
    phrase = "at both a sector and thematic level"
    assert [s.name for s in v.content.s05_affected.sector_exposures] == [phrase]  # stored as read
    f = {x.factor_id: x.value for x in v.priority.factors}  # type: ignore[union-attr]
    assert f["F6_recognizable_exposures"] == "0 listed · 0 sector · 0 instrument"
    assert v.priority.research_action is ResearchAction.WATCH  # type: ignore[union-attr]
    card = BeautifulSoup((out / "cards" / f"{v.thesis_id}.html").read_text(), "html.parser")
    assert _names_under(card, INDICATOR_INSTRUMENTS) == [cor]
    assert _names_under(card, BROAD_INSTRUMENTS) == [spx]
    assert cor not in _names_under(card, INSTRUMENT_EXPOSURES)
    junk = card.find("div", class_="sub", string=NOT_SECTORS)
    assert junk is not None and phrase in junk.find_next_sibling("div").get_text()
    counted_head = card.find("div", class_="sub",
                             string="Sectors / themes the source names as exposed")
    assert counted_head.find_next_sibling("div").get_text() == "None counted."
    md = (out / "cards" / f"{v.thesis_id}.md").read_text()
    assert f"- {cor} — " in md.split(f"**{INDICATOR_INSTRUMENTS}:**")[1].split("**")[0]
    assert f"- {phrase} — " in md.split(f"**{NOT_SECTORS}:**")[1].split("**")[0]
    counted_md = md.split("**Sectors / themes the source names as exposed:**")[1].split(
        f"**{NOT_SECTORS}:**")[0]
    assert phrase not in counted_md and "- none counted" in counted_md
    page = _text(out / "theses" / f"{v.thesis_id}.html")
    assert f"{cor} (market indicator — not counted)" in page
    assert f"{phrase} (not a sector — not counted)" in page
    soup = BeautifulSoup((out / "theses" / f"{v.thesis_id}.html").read_text(), "html.parser")
    assert phrase not in [b.get_text() for b in soup.select(".expo ul.who li > b")]
    rows = {r.thesis_id: r for rs in res["dashboard"].categories.values() for r in rs}
    row = rows[v.thesis_id]  # named ONCE each, labelled — never among the exposures (REVIEW)
    assert f"{cor} [market indicator — not counted]" in row.other_named
    assert not any(x.startswith(cor) for x in row.named_instruments)
    assert f"{phrase} [not a sector — not counted]" in row.other_named
    assert not any(x.startswith(phrase) for x in row.sector_exposures)
    nt = NearTerm(stored="yes", framing="", claims=(), recomputed="yes", note="")
    g = next(x for x in gates(v, [], nt) if x.name == "An exposure the source names")
    assert not g.ok and f"broad market index ({spx})" in g.detail
    assert f"market indicator ({cor})" in g.detail and phrase in g.detail
    why = " ".join(why_reasons(v.content, v.priority))
    assert f"market indicator ({cor})" in why and phrase in why
    # without its non-sector, the index and the indicator are the whole reason, said as one
    av = v.content.s05_affected.model_copy(update={"sector_exposures": ()})
    two = v.model_copy(update={"content": v.content.model_copy(update={"s05_affected": av})})
    g = next(x for x in gates(two, [], nt) if x.name == "An exposure the source names")
    assert g.detail == (f"only a broad market index ({spx}) and a market indicator ({cor}) — "
                        f"neither the whole market nor a measure is counted as an exposure")



def test_a_thesis_whose_only_sectors_are_not_sectors_counts_no_exposure_and_says_why(
        tmp_path: Path) -> None:
    """The live pilot's shape (TH-2FFD9B58A8, 2026-10-16): its only "sectors" were "Treasurys",
    "US equity" and "USD assets". On the real J.P. Morgan record with those as its only names, the
    gate and the why-line say each is not a sector — no instrument reason stands in for them."""
    from vinci.theme_intelligence.desk import NearTerm, gates

    pipe = _jpm(tmp_path)
    pipe.finish_run(RunStatus.SUCCEEDED)
    v = next(v for v in (_current(pipe, t.thesis_id) for t in pipe.store.theses())
             if v.content.s05_affected.sector_exposures)
    se = v.content.s05_affected.sector_exposures[0]
    av = v.content.s05_affected.model_copy(update={
        "instruments": (), "not_securities": (), "companies": (),
        "sector_exposures": tuple(se.model_copy(update={"name": n})
                                  for n in ("Treasurys", "US equity", "USD assets"))})
    f6 = PriorityFactor(factor_id="F6_recognizable_exposures",
                        value="0 listed · 0 sector · 0 instrument", note="")
    kept = tuple(x for x in v.priority.factors  # type: ignore[union-attr]
                 if not x.factor_id.startswith("F6")) + (f6,)
    alone = v.model_copy(update={
        "content": v.content.model_copy(update={"s05_affected": av}),
        "priority": v.priority.model_copy(update={  # type: ignore[union-attr]
            "factors": kept, "research_action": ResearchAction.WATCH, "watch_reasons": ()})})
    nt = NearTerm(stored="yes", framing="", claims=(), recomputed="yes", note="")
    g = next(x for x in gates(alone, [], nt) if x.name == "An exposure the source names")
    assert not g.ok and "Treasurys — an asset class outside equities" in g.detail
    assert "US equity — the whole market" in g.detail and "market index" not in g.detail
    assert g.detail.startswith("only names read as sectors that are not sectors (")
    why = " ".join(why_reasons(alone.content, alone.priority))
    assert "Treasurys — an asset class outside equities" in why


def test_a_version_that_counted_a_non_sector_says_it_is_no_longer_counted(
        tmp_path: Path) -> None:
    """REVIEW of #737: a version STORED counting "US equity" as a sector keeps its action until it
    is re-graded; its gate says the name is no longer counted and that a re-grade applies it."""
    from vinci.theme_intelligence.desk import NearTerm, gates

    pipe = _jpm(tmp_path)
    pipe.finish_run(RunStatus.SUCCEEDED)
    v = next(v for v in (_current(pipe, t.thesis_id) for t in pipe.store.theses())
             if v.content.s05_affected.sector_exposures)
    se = v.content.s05_affected.sector_exposures[0]
    av = v.content.s05_affected.model_copy(update={
        "instruments": (), "not_securities": (), "companies": (),
        "sector_exposures": (se.model_copy(update={"name": "US equity"}),)})
    f6 = PriorityFactor(factor_id="F6_recognizable_exposures",
                        value="0 listed · 1 sector · 0 instrument", note="")
    kept = tuple(x for x in v.priority.factors  # type: ignore[union-attr]
                 if not x.factor_id.startswith("F6")) + (f6,)
    old = v.model_copy(update={
        "content": v.content.model_copy(update={"s05_affected": av}),
        "priority": v.priority.model_copy(update={"factors": kept})})  # type: ignore[union-attr]
    nt = NearTerm(stored="yes", framing="", claims=(), recomputed="yes", note="")
    g = next(x for x in gates(old, [], nt) if x.name == "An exposure the source names")
    assert g.ok and g.detail == (
        "counted 1 exposure when the thesis was assessed; today's rules do not count a name read "
        "as a sector that is not one (US equity — the whole market, not a sector) — a re-grade "
        "($0) applies them")


def test_the_enrichment_prompt_names_only_the_sectors_that_are_sectors(tmp_path: Path) -> None:
    """REVIEW of #737: the paid enrichment call was told "Treasurys; US equity; USD assets" were
    the sectors the source names as exposed. On the real J.P. Morgan card, a name that is not a
    sector stays out of that line and a real one stays in."""
    from vinci.theme_intelligence.enrich import user_message

    pipe = _jpm(tmp_path)
    pipe.finish_run(RunStatus.SUCCEEDED)
    v = next(v for v in (_current(pipe, t.thesis_id) for t in pipe.store.theses())
             if v.content.s05_affected.sector_exposures)
    se = v.content.s05_affected.sector_exposures[0]
    card = v.content.model_copy(update={"s05_affected": v.content.s05_affected.model_copy(
        update={"sector_exposures": (se.model_copy(update={"name": "Treasurys"}),
                                     se.model_copy(update={"name": "utilities"}))})})
    line = next(x for x in user_message(card, version=v.version, area="x", groups=[]).splitlines()
                if x.startswith("Sectors the source names as exposed:"))
    assert "utilities" in line and "Treasurys" not in line

@pytest.mark.parametrize(("name", "refused"), [
    # read as sector exposures in the local registry copies (2026-10-16), and not sectors
    ("at both a sector and thematic level", True),
    ("both a sector and thematic level", True),
    ("seven sectors", True),
    ("broader set of sectors and industries", True),
    ("equities market itself", True),
    ("US equity", True),
    ("Domestic Equity", True),
    ("Latin American equities", True),
    ("large-cap leaders", True),
    ("Treasurys", True),
    ("USD assets", True),
    ("Fixed Income", True),
    ("LatAm FX", True),
    ("LatAm credit", True),
    ("LA5 general government debt", True),
    # constructed: the whole market and an asset class together
    ("US equity and credit markets", True),
    # REVIEW of #737: a sentence-final full stop is punctuation, and "U.S." is still a region
    ("US equities.", True),
    ("U.S. equity", True),
    ("Treasurys.", True),
    # NEGATIVE — sectors read in the same copies: a population is named beside the generic word
    ("information technology sector", False),
    ("midstream sector", False),
    ("the software sector", False),
    ("ETF industry", False),
    ("Registered Investment Adviser (RIA) sub-industry", False),
    ("U.S. natural gas", False),
    ("behind-the-meter power market in Australia", False),
    ("large-cap productivity gains", False),
    ("Tech", False),
    ("AI demand", False),  # a demand driver: left counted for an operator ruling
    # constructed: a credit or bank population is a sector
    ("consumer credit", False),
    ("US regional banks", False),
])
def test_a_name_read_as_a_sector_is_told_from_a_sector(name: str, refused: bool) -> None:
    assert (not_a_sector(name) is not None) is refused


def test_a_name_that_is_not_a_sector_is_named_and_never_counted() -> None:
    def sec(n: str) -> SectorExposure:
        return SectorExposure(name=n, direction=Direction.UNCLEAR,
                              provenance=Provenance.SOURCE_OPINION, quote="[HYPOTHETICAL]",
                              article_id="A-x")
    ce = counted_exposures(_view(sector_exposures=(sec("Treasurys"), sec("utilities"))))
    assert ce.sectors == ("utilities",)
    assert ce.not_sectors == (("Treasurys", "an asset class outside equities, not a sector"),)



def test_a_version_counted_before_the_ruling_says_what_is_no_longer_counted(
        tmp_path: Path) -> None:
    """REVIEW of #736: a version STORED counting the S&P 500 (TH-5C3B51DF57's shape, "0 listed ·
    0 sector · 1 instrument") keeps its action until it is re-graded — and its gate passed with
    "not point-in-time verified" as the reason, which was false. It now says what today's rules
    no longer count, on the gate and on the why-line, whatever the action. NEGATIVE: a version
    whose stored count matches today's says nothing of the kind."""
    from vinci.theme_intelligence.desk import NearTerm, gates

    pipe = _jpm(tmp_path)
    pipe.finish_run(RunStatus.SUCCEEDED)
    current = [_current(pipe, t.thesis_id) for t in pipe.store.theses()]
    (v,) = [v for v in current if [c.name_as_written for c in broad_market_instruments(
        v.content.s05_affected)] == ["S&P 500"]]
    nt = NearTerm(stored="yes", framing="", claims=(), recomputed="yes", note="")
    fresh = next(x for x in gates(v, [], nt) if x.name == "An exposure the source names")
    assert "re-grade" not in fresh.detail  # stored "0 listed · 1 sector · 0 instrument" = today
    assert not any("re-grade" in x for x in why_reasons(v.content, v.priority))
    av = v.content.s05_affected.model_copy(update={"sector_exposures": ()})
    f6 = PriorityFactor(factor_id="F6_recognizable_exposures",
                        value="0 listed · 0 sector · 1 instrument", note="")
    kept = tuple(x for x in v.priority.factors  # type: ignore[union-attr]
                 if not x.factor_id.startswith("F6")) + (f6,)
    old = v.model_copy(update={
        "content": v.content.model_copy(update={"s05_affected": av}),
        "priority": v.priority.model_copy(update={  # type: ignore[union-attr]
            "factors": kept, "research_action": ResearchAction.RESEARCH_NOW})})
    g = next(x for x in gates(old, [], nt) if x.name == "An exposure the source names")
    assert g.ok and "not point-in-time verified" not in g.detail
    assert g.detail == ("counted 1 exposure when the thesis was assessed; today's rules do not "
                        "count a broad market index (S&P 500) — a re-grade ($0) applies them")
    why = why_reasons(old.content, old.priority)
    assert why[0].startswith("Research Now") and why[-1] == f"Exposure — {g.detail}."
    # a stored count nothing on today's card accounts for says only that — never "not verified"
    bare = old.model_copy(update={"content": old.content.model_copy(update={
        "s05_affected": av.model_copy(update={"instruments": ()})})})
    g = next(x for x in gates(bare, [], nt) if x.name == "An exposure the source names")
    assert g.ok and g.detail == "counted when the thesis was assessed: 1 exposure"

def test_an_instrument_named_only_as_a_comparator_stays_a_mention(tmp_path: Path) -> None:
    """NEGATIVE, through the store: an index the source names as a COMPARATOR is not an exposure
    — on the desk, the card and the dashboard row. The real shape: in the current versions of 148
    local registry copies (2026-10-16), 69 instrument entries sit outside the attaching roles, on
    7 distinct theses; 39 of them the S&P 500 as comparator. POSITIVE beside it: the ETF and the
    basket the thesis attaches are. HYPOTHETICAL article; the authentic frozen SEC subset
    resolves the ETF."""
    lines = ("The iShares Expanded Tech-Software Sector ETF (IGV) fell 25% in the quarter as "
             "software stocks sold off.",
             "Software lagged the S&P 500, which rose 4% over the same quarter.",
             "Our AI-disrupted software basket fell 30% in the quarter.")
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=JPM_AS_OF)
    igv, spx = "iShares Expanded Tech-Software Sector ETF (IGV)", "S&P 500"
    basket = "AI-disrupted software basket"
    x = extraction(
        [claim("c1", "b001", lines[0].rstrip("."), "IGV fell 25% in the quarter",
               metric="IGV price change", value=-25, value_text="25%", unit="%",
               period="the quarter"),
         claim("c2", "b002", lines[1].rstrip("."), "S&P 500 rose 4%",
               metric="S&P 500 price change", value=4, value_text="4%", unit="%",
               period="the quarter")],
        [hyp("h1", "Software sell-off overshoots", node="software.saas",
             mechanism="valuation_reset", supporting=["c1"],
             affected=[(igv, "market_instrument"), (spx, "comparator"),
                       (basket, "cited_basket")])],
        mentions=[mention(igv, "b001", lines[0].rstrip("."), entity_type="etf_or_fund",
                          role="market_instrument", ticker="IGV"),
                  mention(spx, "b002", lines[1].rstrip("."), entity_type="index",
                          role="comparator", direction="neutral"),
                  mention(basket, "b003", lines[2].rstrip("."), entity_type="basket",
                          role="cited_basket", direction="negative")])
    ingest(pipe, Hypo("comparator", "Test Publisher", date(2026, 2, 2),
                      [("paragraph", t) for t in lines]).doc(), x, as_of=JPM_AS_OF)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    av = _current(pipe, t.thesis_id).content.s05_affected
    assert {c.name_as_written for c in av.instruments} == {igv, spx}
    assert counted_exposures(av).instruments == (igv, basket)
    res = write_run_outputs(pipe.store, run.run_id, tmp_path / "out")
    out = Path(res["dir"])
    page = BeautifulSoup((out / "theses" / f"{t.thesis_id}.html").read_text(), "html.parser")
    who = next(x for x in page.select("section.panel")
               if x.h2 is not None and x.h2.get_text() == "Who is exposed")
    listed = {li.b.get_text(): li.get_text(" ") for li in who.select("ul.who li")
              if li.b is not None}
    assert set(listed) == {igv, basket} and "not a security" in listed[basket]
    assert f"{spx} (comparator)" in who.get_text(" ")
    card = BeautifulSoup((out / "cards" / f"{t.thesis_id}.html").read_text(), "html.parser")
    assert _names_under(card, INSTRUMENT_EXPOSURES) == [igv, basket]
    assert _names_under(card, NAMED_INSTRUMENTS) == [spx]
    # the thesis's reading: a styled label, then a space, then the reading — the label once ran
    # into it ("MODEL INFERENCEcited basket")
    for tr in _rows_under(card, INSTRUMENT_EXPOSURES):
        cell = tr.select("td")[3]
        assert cell.span is not None and "lab" in cell.span["class"]
        assert cell.get_text().startswith(cell.span.get_text() + " ")
    (row,) = [r for rs in res["dashboard"].categories.values() for r in rs]
    assert [n.split(" [")[0] for n in row.named_instruments] == [igv, basket]
    assert any(n.startswith(f"{spx} [") for n in row.other_named)


# --- review of #730: versions stored with the factor's earlier id -------------------------------

def _legacy(pr: Any, value: str | None) -> Any:
    """The priority with its F6 factor as an earlier version stored it: the id
    "F6_recognizable_listed_exposures" with a bare count — or no F6 at all (value None)."""
    kept = tuple(f for f in pr.factors if not f.factor_id.startswith("F6"))
    if value is not None:
        kept += (PriorityFactor(factor_id="F6_recognizable_listed_exposures", value=value,
                                note="source-named, SEC-resolved listed companies"),)
    return pr.model_copy(update={"factors": kept, "watch_reasons": ()})


def test_the_earlier_factor_id_is_read_as_its_count_and_none_is_never_zero() -> None:
    """8 current versions in the registry copies carried the earlier id (2026-10-16), one of them
    RESEARCH NOW on "4": read as 0, its desk gate said "no exposure". An unreadable count is
    None — unknown, never "no exposure"."""
    pr = compute_priority(_state(sector_exposures=("Memory",)), previous=None,
                          evidence_direction=EvidenceDirection.NEW)
    assert exposures_counted(_legacy(pr, "4")) == 4
    assert exposures_counted(_legacy(pr, "0")) == 0
    assert exposures_counted(_legacy(pr, None)) is None
    watch = _legacy(pr, None).model_copy(update={"research_action": ResearchAction.WATCH})
    assert "no_exposure" not in [r.code for r in watch_reasons_of(watch)]


def test_the_gate_names_what_was_counted_when_the_card_cannot_list_it(tmp_path: Path) -> None:
    """A RESEARCH NOW version stored before point-in-time verification: its rule counted 4 listed
    companies whose listings the card does not verify today. The gate passes — the action stands —
    and says what was counted, never an empty line."""
    from vinci.theme_intelligence.desk import NearTerm, gates

    pipe, hyper = _stale_registry(tmp_path)
    v = _current(pipe, hyper)
    av = v.content.s05_affected.model_copy(update={"sector_exposures": ()})
    old = v.model_copy(update={
        "content": v.content.model_copy(update={"s05_affected": av}),
        "priority": _legacy(v.priority, "4").model_copy(
            update={"research_action": ResearchAction.RESEARCH_NOW})})
    nt = NearTerm(stored="yes", framing="", claims=(), recomputed="yes", note="")
    g = next(x for x in gates(old, [], nt) if x.name == "An exposure the source names")
    assert g.ok and "counted when the thesis was assessed: Meta" in g.detail


def test_the_markdown_record_says_what_a_watch_waits_for(tmp_path: Path) -> None:
    pipe = _jpm(tmp_path)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    for p in (out / "cards").glob("TH-*.md"):
        assert p.read_text().splitlines()[2].startswith("**WATCH · on hold**")
    assert (out / "dashboard.md").read_text().count("[WATCH · on hold]") == 3
