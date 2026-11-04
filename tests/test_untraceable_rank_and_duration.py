"""Two false UNTRACEABLE figures the per-fact trace (audit G-D6) printed on real pages, closed
without widening what a figure may trace to (2026-11-04).

1. A PERCENTILE IS WRITTEN AS ITS RANK. `ev_ebitda_percentile_5y` stores 0.026 and the point says
   "the 3rd percentile": 2.6 against 3 is outside the 2% tolerance, so the figure was flagged while
   the cited fact stated it. A 0..1 field named for a percentile (`synthesis._PERCENTILE_FIELDS`)
   now also states its whole-number rank, traced only as that rank — as a date states its year.
2. A DURATION IS A LABEL HOWEVER IT IS WRITTEN. "5 years" was skipped and "a 5-year window",
   "the 52-week low", "over ~2y" were figures. In the claim trace only: `driver_extract`'s row
   check keeps reading them as figures a row's quote must state.

NARROWED by the cross-review of #890 (posted after merge): the rank traced in ANY context
("2.0x", "2 turns", "fell 2%" cited to a percentile all passed), and every decimal duration was
skipped (NCNO's "2.3y" is its band's span — a fact the point must cite — so "7.3y" passed too). A
rank now traces only when WRITTEN as one (an ordinal, or before "percentile" / "pctile" / "%ile"),
and only a WHOLE-NUMBER duration is a label.

Measured over the 30 committed syntheses (27 pages at 9e996d7f + PR #886's three rebuilt pages):
5 rank figures and 7 duration figures of 373 UNTRACEABLE. NOT done, because it would let real
misbindings through: a general "rounds to the figure's written precision" rule — of the 12 figures
it would clear, 7 are another fact's figures that merely round from a value of the cited fact
(CNXC's margins and growth rates cited to its trading multiples).

Value-level pins sit on the FROZEN SMPL page; the committed corpus gets phrasing-free invariants.
"""

from __future__ import annotations

import json
import random
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import driver_extract as dx
from vinci.dossier import flags as dflags
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.verbatim import comparison_key

ROOT = Path(__file__).resolve().parents[1]
_FROZEN_SMPL = ROOT / "tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json"
_COMMITTED = sorted((ROOT / "data/dossiers").glob("*/dossier.json"))
#: a duration's label form, as `synthesis._DURATION_AFTER` reads it after a WHOLE number
_DURATION_AFTER = re.compile(r"^(?:-(?:days?|weeks?|months?|quarters?|qtrs?|years?)\b|y\b)",
                             re.IGNORECASE)
#: a figure written as a percentile rank, as `synthesis._RANK_AFTER` reads it after the number
_RANK_AFTER = re.compile(
    r"^(?:st|nd|rd|th)?[\s-]*(?:percentile|pctile|%ile)\b(?![\s-]*(?:pts?|points?)\b)",
    re.IGNORECASE)


def _frozen() -> ds.MechanicalLayer:
    return ds.MechanicalLayer.model_validate(json.loads(_FROZEN_SMPL.read_text())["mechanical"])


def _flagged(mech: ds.MechanicalLayer, claim: str, ref: str, *, ticker: str = "SMPL",
             name: str = "Simply Good Foods") -> list[str]:
    """The figures a one-point synthesis citing ``ref`` is flagged for, read from the CAVEATS the
    page prints (`flags.partition`), not from the validator's internal string."""
    point = ds.SourcedPoint(claim=claim, source_ref=ref)
    synth = ds.Synthesis(
        evidence_balance="mixed — test", bull_points=[point], bear_points=[],
        twin_reference_cases=[], key_unknowns=[],
        decisive_question=ds.DecisiveQuestion(question="q?", evidence_for=[],
                                              evidence_against=[]))
    _, flags = syn._validate(synth, mech, ticker=ticker, name=name)
    caveats, _ = dflags.partition(flags)
    return [m.group(1) for c in caveats
            if (m := re.match(r"Untraceable figure (\S+) \(", c))]


def _ordinal(n: int) -> str:
    return f"{n}" + ("th" if n % 100 in (11, 12, 13) else {1: "st", 2: "nd", 3: "rd"}.get(
        n % 10, "th"))


# --- 1. a percentile traces as its rank ----------------------------------------------------------

def test_a_percentile_traces_as_its_rank_on_the_frozen_page() -> None:
    """FAILED on 9e996d7f: SMPL's P/E percentile is 0.0183 and "the 2nd percentile" was flagged
    (1.83 vs 2 is outside max(0.05, 2%))."""
    mech = _frozen()
    fact = mech.valuation.pe_percentile_5y if mech.valuation else None
    assert fact is not None and fact.source_ref and fact.value == pytest.approx(0.018327, abs=1e-6)
    assert _flagged(mech, "the P/E sits at the 2nd percentile of its 5y range",
                    fact.source_ref) == []


def test_only_the_rank_itself_is_admitted_and_only_to_its_own_fact() -> None:
    """The negative half. Of every rank 0..100 cited to the percentile fact, the ones that trace
    are its own rank (2) and the three that traced before through its other numbers — 0 (any value
    x1e-2 is within the 0.05 floor of 0), 5 (its ref's "~5y") and 18 (0.0183 x1e3) — so the rule
    admits ONE number per percentile. The same 0.0183
    stored in a field that is not a percentile admits no rank, and the rank cited to another fact
    stays flagged."""
    mech = _frozen()
    assert mech.valuation is not None
    fact = mech.valuation.pe_percentile_5y
    assert fact.source_ref
    traced = {n for n in range(101)
              if not _flagged(mech, f"it sits at the {_ordinal(n)} percentile", fact.source_ref)}
    assert traced == {0, 2, 5, 18}
    other = mech.idiosyncratic_vs_shared.rel_vs_market.source_ref
    assert other
    assert _flagged(mech, "it sits at the 2nd percentile", other) == ["2"]
    not_a_percentile = ds.Sourced[float].present(fact.value or 0.0, source_ref="TEST not-a-pctile")
    moved = mech.model_copy(update={"valuation": mech.valuation.model_copy(update={
        "ev_ebitda": not_a_percentile})})
    assert _flagged(moved, "it sits at the 2nd percentile", "TEST not-a-pctile") == ["2"]


@pytest.mark.parametrize("claim", ["it de-rated to 2.0x", "it trades at 2 turns",
                                   "the stock fell 2%", "2 straight quarters of decline",
                                   "the 2nd straight quarter of decline",
                                   "its 2nd-largest customer",
                                   "the multiple rose 2 percentile points",
                                   "a 2 percentile-point drop"])
def test_the_rank_is_no_figure_written_as_anything_but_a_rank(claim: str) -> None:
    """Cross-review of #890: each TRACED on a439eabe, cited to SMPL's 0.0183 P/E percentile, because
    the rank 2 was admitted whatever the "2" stated. Now only a figure written as a rank traces as
    one."""
    mech = _frozen()
    ref = mech.valuation.pe_percentile_5y.source_ref if mech.valuation else None
    assert ref
    assert _flagged(mech, claim, ref) == ["2"]


@pytest.mark.parametrize("claim", ["the P/E sits at the 2nd percentile",
                                   "a 2 percentile reading", "the 2 pctile of its range",
                                   "near its 2%ile", "a 2nd-percentile multiple"])
def test_a_figure_written_as_a_rank_traces_as_the_rank(claim: str) -> None:
    mech = _frozen()
    ref = mech.valuation.pe_percentile_5y.source_ref if mech.valuation else None
    assert ref
    assert _flagged(mech, claim, ref) == []


def test_only_a_fraction_in_0_to_1_states_a_rank() -> None:
    """The 0..1 guard, pinned where it acts (cross-review of #890: dropping it failed no test).
    Through the trace it is unobservable — a percentile field above 1 already traces its x100 value
    within tolerance, and a negative rank is never a figure's magnitude — so it is pinned on the
    numbers the fact states."""
    for value, ranks in ((0.026, {3.0}), (0.0, {0.0}), (1.0, {100.0}), (-0.026, set()),
                         (1.5, set()), (26.0, set())):
        nums = syn._FactNumbers()
        syn._stated_numbers({"value": value, "source_ref": "R"}, nums, "pe_percentile_5y")
        assert nums.ranks == ranks, value


def test_a_band_percentile_traces_as_its_rank() -> None:
    """The own-history band's `percentile` is the same field by schema. The frozen band reads 0.0,
    and 0 traces through the 0.05 floor anyway, so the band is given AMZN's committed 0.0263 (its
    EV/EBITDA band on 2026-11-02): "the 3rd percentile" then traces and "the 2nd" does not. (The
    band's 35-close series already traces many whole numbers, 4 among them, so the negative is one
    it does not.) FAILED on 9e996d7f (the 3rd was flagged)."""
    mech = _frozen()
    v = mech.valuation
    oh = v.own_history if v else None
    assert v is not None and oh is not None and oh.source_ref and oh.value
    assert [b.percentile for b in oh.value] == [0.0]
    band = oh.value[0].model_copy(update={"percentile": 0.02631578947368421})
    moved = mech.model_copy(update={"valuation": v.model_copy(update={
        "own_history": oh.model_copy(update={"value": [band]})})})
    assert _flagged(moved, "the multiple is at the 3rd percentile", oh.source_ref) == []
    assert _flagged(moved, "the multiple is at the 2nd percentile", oh.source_ref) == ["2"]


def test_a_percentile_at_an_exact_half_admits_both_neighbours_and_no_more() -> None:
    """At an exact half the page has no one rank: in binary floats 0.145 x 100 is 14.4999…, so
    `render._pctile` and the web print the 14th while a writer reading "0.145" says the 15th, and
    0.025 is the 2nd to Python's half-even and the 3rd to `Math.round`. Both neighbours trace; the
    next ones out do not. (The first cut, floor(x x 100 + 0.5), admitted only the 14th.)"""
    mech = _frozen()
    v = mech.valuation
    assert v is not None and v.pe_percentile_5y.source_ref
    ref = v.pe_percentile_5y.source_ref
    for value, both, out in ((0.145, ("14th", "15th"), ("13th", "16th")),
                             (0.025, ("2nd", "3rd"), ("1st", "4th"))):
        moved = mech.model_copy(update={"valuation": v.model_copy(update={
            "pe_percentile_5y": v.pe_percentile_5y.model_copy(update={"value": value})})})
        for rank in both:
            assert _flagged(moved, f"it sits at the {rank} percentile", ref) == [], (value, rank)
        for rank in out:
            assert _flagged(moved, f"it sits at the {rank} percentile", ref) == [rank[:-2]], (
                value, rank)
    assert syn._percentile_ranks(0.026) == {3.0}
    assert syn._percentile_ranks(0.0183) == {2.0}
    assert syn._percentile_ranks(0.145) == {14.0, 15.0}


def _percentile_fields(schema: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(schema, dict):
        for k in schema.get("properties", {}):
            if "percentile" in k.lower():
                out.add(k)
        for v in schema.values():
            out |= _percentile_fields(v)
    elif isinstance(schema, list):
        for v in schema:
            out |= _percentile_fields(v)
    return out


def test_every_percentile_field_of_the_page_schema_is_in_the_closed_set() -> None:
    """The rank is read only from a closed set of field names. A new percentile field on the page
    schema reddens here, so adding one to the set is a decision rather than an omission."""
    found = _percentile_fields(ds.MechanicalLayer.model_json_schema())
    assert found == set(syn._PERCENTILE_FIELDS), found


# --- 2. a duration is a label --------------------------------------------------------------------

@pytest.mark.parametrize("claim", [
    "impairment-free over the 5-year window",
    "the stock is near its 52-week low",
    "shares roughly flat over ~2y",
    "the band spans ~9y",
    "a 180-day return",
])
def test_a_hyphenated_or_abbreviated_duration_is_no_figure(claim: str) -> None:
    """FAILED on 9e996d7f for each: the spaced form ("5 years") was skipped, these were flagged.
    Whole numbers only (cross-review of #890)."""
    mech = _frozen()
    ref = mech.idiosyncratic_vs_shared.rel_vs_market.source_ref
    assert ref
    assert _flagged(mech, claim, ref) == []
    assert syn._claim_figures(claim) == []
    # the transcript-row check is unmoved: there the duration is still a figure its quote must state
    assert dx._figures(claim) != []


@pytest.mark.parametrize(("claim", "figure"), [
    ("the multiple sits low in its own 2.3y range", "2.3"),
    ("the multiple sits low in its own 7.3y range", "7.3"),
    ("a 7.3-year span of closes", "7.3"),
    ("a 7.4-year payback", "7.4"),
])
def test_a_decimal_duration_is_a_figure(claim: str, figure: str) -> None:
    """Cross-review of #890: each TRACED on a439eabe. "2.3y" is NCNO's band span
    (`own_history.value[0].window_span_years`), a fact the point must cite — and "7.3y" or a
    "7.4-year payback" is a figure as surely, whatever unit follows it."""
    mech = _frozen()
    ref = mech.idiosyncratic_vs_shared.rel_vs_market.source_ref
    assert ref
    assert _flagged(mech, claim, ref) == [figure]


@pytest.mark.parametrize(("claim", "figures"), [
    ("a 5-year CAGR of 345.6%", ["345.6"]),
    ("$5-billion of new capacity", ["5"]),
    ("growth of 5-10% a year", ["5", "-10"]),
    ("a 7-yard gain", ["7"]),
])
def test_a_figure_beside_a_duration_or_a_hyphen_is_still_a_figure(
        claim: str, figures: list[str]) -> None:
    """The negative half: only a time unit makes a label — a figure after the duration, a hyphenated
    amount and a range are still traced, and flagged when the cited fact lacks them."""
    mech = _frozen()
    ref = mech.idiosyncratic_vs_shared.rel_vs_market.source_ref
    assert ref
    assert _flagged(mech, claim, ref) == figures


# --- the G-D6 draw is unmoved --------------------------------------------------------------------

def test_the_gd6_draw_flags_the_same_195_of_199() -> None:
    """`test_model_input_checks`'s made-up-figure draw (seed 20261029, 199 figures in [100, 1000)
    at 1 dp, cited to the relative return) flagged 195 of 199 on 9e996d7f and flags the same 195
    here: neither change can reach a 1-dp figure above 25."""
    mech = _frozen()
    ref = mech.idiosyncratic_vs_shared.rel_vs_market.source_ref
    assert ref
    random.seed(20261029)
    figs = sorted({round(random.uniform(100, 1000), 1) for _ in range(200)})
    assert len(figs) == 199
    assert sum(bool(_flagged(mech, f"the figure is {f:,.1f}", ref)) for f in figs) == 195


# --- the committed corpus: phrasing-free invariants ----------------------------------------------

def _points(raw: dict[str, Any]) -> list[ds.SourcedPoint]:
    s = ds.Synthesis.model_validate(raw["synthesis"])
    return [*s.bull_points, *s.bear_points, *s.decisive_question.evidence_for,
            *s.decisive_question.evidence_against]


def _ranks(x: float) -> set[float]:
    """A 0..1 percentile's whole-number rank(s), computed here without the code under test: the
    nearest whole number to x100 on its stored decimal, both neighbours at an exact half."""
    d = Decimal(repr(x)) * 100
    lo = int(d // 1)
    return {float(lo), float(lo + 1)} if d - lo == Decimal("0.5") else {float(round(d))}


def _ranks_by_ref(mech: ds.MechanicalLayer) -> dict[str, set[float]]:
    """The rank of each percentile on the page, keyed by its fact's ref — read from the schema's
    fields directly, not through the code under test."""
    out: dict[str, set[float]] = {}
    v = mech.valuation
    if v is None:
        return out
    for fact in (v.pe_percentile_5y, v.ev_ebitda_percentile_5y):
        if fact.source_ref and fact.value is not None:
            out.setdefault(comparison_key(fact.source_ref), set()).update(_ranks(fact.value))
    if v.own_history is not None and v.own_history.source_ref and v.own_history.value:
        out.setdefault(comparison_key(v.own_history.source_ref), set()).update(
            r for b in v.own_history.value for r in _ranks(b.percentile))
    return out


@pytest.mark.parametrize("path", _COMMITTED, ids=lambda p: p.parent.name)
def test_no_committed_point_is_flagged_for_its_own_percentile_rank_or_a_duration(
        path: Path) -> None:
    """Every committed synthesis point, through `_validate` and the caveat split: no caveat names a
    number WRITTEN as a rank that is the rank of a percentile the point's cited fact states, nor a
    whole number the point writes only as a duration. On 9e996d7f this failed on IT, NFLX, NKE, TJX
    (a rank) and EPAM, LLY, NFLX, WLK (a duration); each page is validated as itself."""
    raw = json.loads(path.read_text())
    mech = ds.MechanicalLayer.model_validate(raw["mechanical"])
    ranks = _ranks_by_ref(mech)
    for p in _points(raw):
        if syn._TRANSCRIPT_REF.search(p.source_ref):
            continue
        flagged = {float(f.replace(",", "")) for f in _flagged(
            mech, p.claim, p.source_ref, ticker=raw["ticker"], name=raw.get("name", ""))}
        own_rank = ranks.get(comparison_key(p.source_ref), set())
        written_as_rank: set[float] = set()
        durations: set[float] = set()
        others: set[float] = set()
        for m in syn._NUM.finditer(p.claim):
            v = abs(float(m.group().replace(",", "")))
            tail = p.claim[m.end():]
            if _RANK_AFTER.match(tail):
                written_as_rank.add(v)
            whole = "." not in m.group()
            (durations if whole and _DURATION_AFTER.match(tail) else others).add(v)
        assert not flagged & own_rank & written_as_rank, (p.claim, flagged & own_rank)
        assert not {abs(f) for f in flagged} & (durations - others), p.claim
