"""Item 29 — every figure in a synthesis point is footnoted (operator ruling 2026-11-04,
"1 + 4").

(1) A point carries `figures`: one entry per figure of its claim, citing the ONE fact that
    states it, or naming an operation (difference / sum / ratio / premium / growth) on two inputs
    of the same claim, each with its own entry. A cited figure is traced to ITS fact by the
    per-fact rule (`_num_traces`, audit G-D6); a computed one is recomputed from its inputs as
    written. A figure with no entry is traced to the point's own ref exactly as before.
(4) The blocks the assembler builds carry a `source_ref`, so a point can cite their figures; a
    block that states numbers with no ref anywhere above it reddens here unless it is on the
    not-a-fact list with its reason.

Value pins sit on the FROZEN SMPL page (and a frozen copy of LLY's quality block for the prompt's
literal example); the committed corpus gets phrasing-free invariants only.
"""

from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
import types
import typing
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from vinci.dossier import flags as dflags
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.dossier.extraction_version import EXTRACTION_VERSIONS

ROOT = Path(__file__).resolve().parents[1]
_FROZEN_SMPL = ROOT / "tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json"
_LLY_QUALITY = ROOT / "tests/fixtures/item29/lly_quality_a439eabe.json"
_COMMITTED = sorted((ROOT / "data/dossiers").glob("*/dossier.json"))
_THIS_VERSION = "2026-11-04.footnote-every-figure"


def _frozen() -> ds.MechanicalLayer:
    return ds.MechanicalLayer.model_validate(json.loads(_FROZEN_SMPL.read_text())["mechanical"])


def _point(claim: str, ref: str, figures: list[dict[str, Any]] | None = None) -> ds.SourcedPoint:
    return ds.SourcedPoint.model_validate(
        {"claim": claim, "source_ref": ref, "figures": figures or []})


def _flags(mech: ds.MechanicalLayer, *points: ds.SourcedPoint) -> list[str]:
    synth = ds.Synthesis(
        evidence_balance="mixed — test", bull_points=list(points), bear_points=[],
        twin_reference_cases=[], key_unknowns=[],
        decisive_question=ds.DecisiveQuestion(question="q?", evidence_for=[],
                                              evidence_against=[]))
    return syn._validate(synth, mech, ticker="SMPL", name="Simply Good Foods")[1]


def _flagged(mech: ds.MechanicalLayer, point: ds.SourcedPoint) -> list[str]:
    """The figure each hard caveat names — UNTRACEABLE (cited or not) and UNDERIVED."""
    return [f.split("'")[1] for f in _flags(mech, point)
            if f.startswith(("UNTRACEABLE", "UNDERIVED"))]


def _refs() -> tuple[str, str, str]:
    iv = _frozen().idiosyncratic_vs_shared
    name, market, rel = (iv.name_180d_return.source_ref, iv.market_180d_return.source_ref,
                         iv.rel_vs_market.source_ref)
    assert name and market and rel
    return name, market, rel


_GD6_CLAIM = ("The de-rate is idiosyncratic, not cyclical: SMPL fell -29% over 180d while its "
              "small-cap benchmark rose +16%, a -45pt relative gap concentrated on the two "
              "April-2026 earnings gap-downs.")


# --- the shape -----------------------------------------------------------------------------------

def test_a_figure_cites_exactly_one_of_a_fact_or_an_operation() -> None:
    ok = ds.FigureCite(figure="15.1x", source_ref="R")
    assert ok.derived is None and ok.inputs == []
    assert ds.FigureCite(figure="$19,661M", derived="difference", inputs=["$1M", "$2M"]).derived
    for bad in ({"figure": "1"}, {"figure": "1", "source_ref": "R", "derived": "sum",
                                  "inputs": ["1", "2"]},
                {"figure": "1", "derived": "sum", "inputs": ["1"]},
                {"figure": "1", "source_ref": "R", "inputs": ["1", "2"]},
                {"figure": "1", "derived": "median", "inputs": ["1", "2"]}):
        with pytest.raises(ValidationError):
            ds.FigureCite.model_validate(bad)


def test_the_footnote_carries_no_verdict_and_the_operations_are_closed() -> None:
    assert set(ds.FigureCite.model_fields) == {"figure", "source_ref", "derived", "inputs"}
    assert ds.FIGURE_OPERATIONS == ("difference", "sum", "ratio", "premium", "growth")
    assert not any("verdict" in k for k in ds.Synthesis.model_fields)
    item = syn.SYNTHESIS_TOOL["input_schema"]["properties"]["bull_points"]["items"]
    assert item["required"] == ["claim", "source_ref", "figures"]
    fig = item["properties"]["figures"]["items"]
    assert fig["properties"]["derived"]["enum"] == list(ds.FIGURE_OPERATIONS)
    assert set(fig["properties"]) == {"figure", "source_ref", "derived", "inputs"}


def test_a_point_without_footnotes_and_a_block_without_a_ref_write_nothing_new() -> None:
    """ABSENT, never null: every page drawn before item 29 round-trips byte for byte."""
    assert "figures" not in _point("a 3.3x figure", "R").model_dump()
    assert "figures" in _point("a 3.3x figure", "R",
                               [{"figure": "3.3x", "source_ref": "R"}]).model_dump()
    assert "source_ref" not in ds.ConsensusLevel(fy="2026", median=1.0, high=2.0,
                                                 low=0.5).model_dump()
    for f in _COMMITTED:
        text = f.read_text()
        page = json.loads(text)
        if isinstance(page.get("anchor"), dict) and "band_checks" in page["anchor"]:
            continue  # rewritten on purpose by its own pin (test_band_checks)
        assert ds.dossier_json(ds.Dossier.model_validate_json(text)) == text, f.parent.name


# --- (1) the check, on the frozen page -----------------------------------------------------------

def test_the_gd6_point_footnoted_to_each_fact_traces() -> None:
    """The frozen point G-D6 pins (`test_a_real_point_citing_one_fact_for_another_facts_figures_is_
    flagged`: ["-29", "16"]) — each figure footnoted to the fact that states it."""
    mech = _frozen()
    name, market, rel = _refs()
    assert _flagged(mech, _point(_GD6_CLAIM, rel)) == ["-29", "16"]
    good = _point(_GD6_CLAIM, rel, [{"figure": "-29%", "source_ref": name},
                                    {"figure": "+16%", "source_ref": market},
                                    {"figure": "-45pt", "source_ref": rel}])
    assert _flagged(mech, good) == []


def test_a_figure_footnoted_to_a_fact_that_does_not_state_it_is_flagged_naming_that_fact() -> None:
    mech = _frozen()
    name, market, rel = _refs()
    wrong = _point(_GD6_CLAIM, rel, [{"figure": "-29%", "source_ref": rel},
                                     {"figure": "+16%", "source_ref": market}])
    flags = _flags(mech, wrong)
    assert [f.split("'")[1] for f in flags if f.startswith("UNTRACEABLE")] == ["-29"]
    caveats, _ = dflags.partition(flags)
    assert any(c.startswith("Untraceable figure -29 (a bull point) — footnoted to ") and rel in c
               for c in caveats), caveats
    unknown = _point(_GD6_CLAIM, rel, [{"figure": "-29%", "source_ref": "NOT A REF OF THE PAGE"}])
    assert _flagged(mech, unknown)[:1] == ["-29"]


def test_a_computed_figure_recomputes_from_its_cited_inputs_as_written() -> None:
    mech = _frozen()
    name, market, rel = _refs()
    figs = [{"figure": "-29%", "source_ref": name}, {"figure": "+16%", "source_ref": market}]
    good = _point(_GD6_CLAIM, rel, [*figs, {"figure": "-45pt", "derived": "difference",
                                            "inputs": ["-29%", "+16%"]}])
    assert _flagged(mech, good) == []
    wrong = _point(_GD6_CLAIM.replace("-45pt", "-40pt"), rel,
                   [*figs, {"figure": "-40pt", "derived": "difference",
                            "inputs": ["-29%", "+16%"]}])
    flags = _flags(mech, wrong)
    assert [f.split("'")[1] for f in flags if f.startswith("UNDERIVED")] == ["-40"]
    caveats, _ = dflags.partition(flags)
    assert any(c.startswith("Unverified computed figure -40 (a bull point) — ") for c in caveats)


def test_a_computed_figure_with_an_input_that_does_not_trace_is_underived() -> None:
    mech = _frozen()
    name, market, rel = _refs()
    bad_input = _point(_GD6_CLAIM, rel, [{"figure": "-29%", "source_ref": market},
                                         {"figure": "+16%", "source_ref": market},
                                         {"figure": "-45pt", "derived": "difference",
                                          "inputs": ["-29%", "+16%"]}])
    assert sorted(_flagged(mech, bad_input)) == ["-29", "-45"]
    no_entry = _point(_GD6_CLAIM, rel, [{"figure": "+16%", "source_ref": market},
                                        {"figure": "-45pt", "derived": "difference",
                                         "inputs": ["-29%", "+16%"]}])
    assert "-45" in _flagged(mech, no_entry)


@pytest.mark.parametrize(("claim", "fig", "op", "inputs"), [
    ("a 15.1x multiple at the 3rd percentile, 5.0x apart", "5.0x", "ratio", ["15.1x", "3rd"]),
    ("a 15.1x multiple against 2.6%, 12.5% apart", "12.5%", "difference", ["15.1x", "2.6%"]),
    ("15.1x against 9.2x is a 64% premium written as 64x", "64x", "premium", ["15.1x", "9.2x"]),
])
def test_an_operation_on_mismatched_units_is_refused(
        claim: str, fig: str, op: str, inputs: list[str]) -> None:
    """Units must agree, and a percentile rank is never an operand — so "15.1x = 49.0x ÷ 3rd", one
    of the coincidences a derivation SEARCH found, cannot be declared either."""
    mech = _frozen()
    _, _, rel = _refs()
    ents = [{"figure": i, "source_ref": rel} for i in inputs]
    p = _point(claim, rel, [*ents, {"figure": fig, "derived": op, "inputs": inputs}])
    assert any(f.startswith("UNDERIVED") and f"'{syn._claim_figures(fig)[0]:g}'" in f
               for f in _flags(mech, p))


def test_an_entry_that_names_no_figure_of_the_claim_is_a_mismatch_and_loosens_nothing() -> None:
    mech = _frozen()
    name, market, rel = _refs()
    p = _point(_GD6_CLAIM, rel, [{"figure": "April-2026", "source_ref": name},
                                 {"figure": "77.7%", "source_ref": name}])
    flags = _flags(mech, p)
    assert sum(f.startswith("MISMATCH") for f in flags) == 2
    assert all(dflags.is_qa(f) for f in flags if f.startswith("MISMATCH"))
    assert [f.split("'")[1] for f in flags if f.startswith("UNTRACEABLE")] == ["-29", "16"]


def test_a_malformed_footnote_from_the_model_is_dropped_and_named() -> None:
    notes: list[str] = []
    raw = {"evidence_balance": "mixed — x", "bull_points": [{
        "claim": "a 3.3x figure", "source_ref": "R", "figures": [
            {"figure": "3.3x", "source_ref": "R"},
            {"figure": "3.3x", "source_ref": "R", "derived": "sum", "inputs": ["1", "2"]},
            {"figure": "3.3x", "derived": "median", "inputs": ["1", "2"]}, "not a dict"]}],
        "bear_points": [], "twin_reference_cases": [], "key_unknowns": [],
        "decisive_question": {"question": "q", "evidence_for": [], "evidence_against": []}}
    s = syn._parse(raw, notes)
    assert [f.figure for f in s.bull_points[0].figures] == ["3.3x"]
    assert len(notes) == 2 and all(n.startswith("MISMATCH figures:") for n in notes)


def test_the_gd6_draw_is_caught_the_same_with_each_figure_footnoted() -> None:
    """The made-up-figure draw G-D6 pins (seed 20261029, 199 figures in [100, 1000) at 1 dp, cited
    to the relative return): 195 of 199 flagged with no footnote, and the same 195 with each figure
    footnoted to that fact — a footnote names the universe; it never widens it."""
    mech = _frozen()
    _, _, rel = _refs()
    random.seed(20261029)
    figs = sorted({round(random.uniform(100, 1000), 1) for _ in range(200)})
    bare = {f for f in figs if _flagged(mech, _point(f"the figure is {f:,.1f}", rel))}
    noted = {f for f in figs if _flagged(mech, _point(
        f"the figure is {f:,.1f}", rel, [{"figure": f"{f:,.1f}", "source_ref": rel}]))}
    assert len(figs) == 199 and len(bare) == 195 and noted == bare


def test_a_made_up_computed_figure_from_real_inputs_is_flagged() -> None:
    """The new door, shut: a made-up figure declared as a computation of two real, traced inputs
    is refused unless the arithmetic gives it."""
    mech = _frozen()
    name, market, rel = _refs()
    random.seed(20261104)
    caught = 0
    for _ in range(200):
        made = round(random.uniform(50, 1000), 1)
        claim = f"SMPL fell -29% while IWM rose +16%, a {made:,.1f}pt gap"
        p = _point(claim, rel, [{"figure": "-29%", "source_ref": name},
                                {"figure": "+16%", "source_ref": market},
                                {"figure": f"{made:,.1f}pt", "derived": "difference",
                                 "inputs": ["-29%", "+16%"]}])
        caught += bool(_flagged(mech, p))
    assert caught == 200


# --- every committed page: footnoting with the point's own ref changes nothing -------------------

def _points(raw: dict[str, Any]) -> list[tuple[str, ds.SourcedPoint]]:
    s = ds.Synthesis.model_validate(raw["synthesis"])
    return ([("bull_point", p) for p in s.bull_points] + [("bear_point", p) for p in s.bear_points]
            + [("decisive.for", p) for p in s.decisive_question.evidence_for]
            + [("decisive.against", p) for p in s.decisive_question.evidence_against])


def _figure_literals(claim: str) -> list[str]:
    """Each figure of the claim as written — the span `_claim_figures` reads, with its sign."""
    out = []
    for v in syn._claim_figures(claim):
        m = re.search(rf"(?<![\d.,])-?{re.escape(f'{abs(v):,.10g}'.rstrip('.'))}(?![\d])", claim)
        if m:
            out.append(m.group())
    return out


@pytest.mark.parametrize("path", _COMMITTED, ids=lambda p: p.parent.name)
def test_footnoting_each_figure_to_the_points_own_ref_flags_exactly_what_today_flags(
        path: Path) -> None:
    """THE LEGACY PATH IS THE SAME UNIVERSE. For every committed point, each figure footnoted to
    the point's own ref is flagged exactly when the unfootnoted figure is."""
    raw = json.loads(path.read_text())
    mech = ds.MechanicalLayer.model_validate(raw["mechanical"])
    for _, p in _points(raw):
        if syn._TRANSCRIPT_REF.search(p.source_ref) or p.figures != []:
            continue
        lits = [x for x in dict.fromkeys(_figure_literals(p.claim)) if x in p.claim]
        noted = p.model_copy(update={"figures": [ds.FigureCite(figure=x, source_ref=p.source_ref)
                                                 for x in lits]})
        assert sorted(_flagged(mech, noted)) == sorted(_flagged(mech, p)), p.claim


# --- the prompt's literal example, against the frozen facts it cites -----------------------------

def _example() -> dict[str, Any]:
    text = syn.system_for("overshoot")
    i = text.index("one literal example: ") + len("one literal example: ")
    obj: dict[str, Any] = json.JSONDecoder().raw_decode(text[i:])[0]
    return obj


def test_every_sleeve_carries_the_footnote_rule() -> None:
    from vinci import sleeves as sl
    for key in sl.SLEEVES:
        assert "(13) FOOTNOTE EVERY FIGURE" in syn.system_for(key), key


def test_the_prompts_literal_example_checks_clean_against_the_facts_it_cites() -> None:
    """The example is real: LLY's committed bear point at a439eabe, its refs read from that page. On
    LLY's frozen quality block it traces figure by figure, the computed one included."""
    ex = _example()
    p = ds.SourcedPoint.model_validate({**ex, "source_ref": ex["figures"][0]["source_ref"]})
    assert len(p.figures) == 7 and sum(f.derived is not None for f in p.figures) == 1
    quality = json.loads(_LLY_QUALITY.read_text())["quality"]
    mech = _frozen().model_copy(update={"quality": ds.Quality.model_validate(quality)})
    assert [f for f in _flags(mech, p) if f.startswith(("UNTRACEABLE", "UNDERIVED",
                                                         "MISMATCH"))] == []
    unfootnoted = p.model_copy(update={"figures": []})
    assert _flagged(mech, unfootnoted) == ["46489", "121.4", "0.9"]


# --- (4) refs on the blocks the assembler builds -------------------------------------------------

#: The fields of the mechanical layer that state something with no ref above them, ON PURPOSE —
#: each with why it is not a fact a point cites. A new field or block reddens the next test until it
#: carries a ref (`schemas.SourceRefWhenBuilt`) or lands here with its reason.
NOT_A_FACT: dict[str, str] = {
    "CapitalStructure.detail_as_of": "a date label",
    "CatalystCalendar.qa_flags": "machine QA",
    "DilutionPipeline.window_days": "a parameter of the read",
    "DrawdownCause.gap_threshold": "a parameter of the read",
    "DrawdownCause.gap_window_days": "a parameter of the read",
    "IdiosyncraticVsShared.benchmark_basis": "a label (its cap is the market leg's ref)",
    "IdiosyncraticVsShared.benchmark_symbol": "a label",
    "ImpliedValuation.bridge_cash": "the structured twin of `implied_valuation.bridge`",
    "ImpliedValuation.bridge_debt": "the structured twin of `implied_valuation.bridge`",
    "MaturityCheck.bound": "a date label",
    "MaturityCheck.panel_filed": "a date label",
    "MechanicalLayer.ev_gap": ("computed after the synthesis, which never sees it "
                               "(test_synthesis_is_blind_to_the_gap)"),
    "OperatingDriversExtract.qa_flags": "machine QA",
    "OwnershipEvents.window_days": "a parameter of the read",
    "PanelCurrency.panel": "a label",
    "PanelCurrency.stated": "a label",
    "PanelCurrency.where": "a label",
    "PrimarySource.qa_flags": "machine QA",
    "SbcLine.window_end": "a date label",
    "SbcLine.window_start": "a date label",
}
_REF_KEYS = ("source_ref", "accession", "url")


def _leaves(tp: Any) -> list[Any]:
    o = typing.get_origin(tp)
    if o in (typing.Union, types.UnionType):
        return [x for a in typing.get_args(tp) for x in _leaves(a)]
    if o is dict:
        return _leaves(typing.get_args(tp)[1])
    if o in (list, tuple, set, frozenset):
        return [x for a in typing.get_args(tp) if a is not Ellipsis for x in _leaves(a)]
    if o is typing.Literal:
        return []   # a closed set of labels states no figure
    return [tp]


def _refless_fields() -> set[str]:
    seen: set[type] = set()
    out: set[str] = set()

    def walk(cls: type[BaseModel]) -> None:
        if cls in seen:
            return
        seen.add(cls)
        if any(k in cls.model_fields for k in _REF_KEYS):
            return   # a ref-carrying class covers its subtree
        for name, f in cls.model_fields.items():
            if name in syn._ID_KEYS or name.endswith("_id"):
                continue
            for t in _leaves(f.annotation):
                if isinstance(t, type) and issubclass(t, BaseModel):
                    walk(t)
                elif t in (int, float, str) or t is Any:
                    out.add(f"{cls.__name__}.{name}")

    walk(ds.MechanicalLayer)
    return out


def test_every_block_of_the_layer_carries_a_ref_or_says_why_it_is_not_a_fact() -> None:
    """THE GUARD, on the schema: no field that can state a figure sits under no ref, unless it is a
    label, a parameter, machine QA or a twin of a cited fact — named in NOT_A_FACT with why."""
    assert _refless_fields() == set(NOT_A_FACT)


#: The blocks this change gives a ref — absent on a page assembled before it, required after.
_NOW_REFFED = ("ConsensusLevel", "PeerCapitalRow", "PeerCapitalIntensity", "MaturityCheckRow",
               "EvEbitdaBasis", "EvEbitdaAtPrice", "EbitdaBasis", "ImpliedExpectations",
               "ImpliedExpectationRow", "FiledLtmFigure")


def _before_this_version(raw: dict[str, Any]) -> bool:
    order = [v for v, _ in EXTRACTION_VERSIONS]
    v = raw.get("extraction_version")
    return v not in order or order.index(v) < order.index(_THIS_VERSION)


@pytest.mark.parametrize("path", _COMMITTED, ids=lambda p: p.parent.name)
def test_no_committed_page_states_a_figure_no_point_could_cite(path: Path) -> None:
    """THE GUARD, on the pages: every number with no ref above it is a not-a-fact field, the note of
    a fact that came back UNKNOWN, or — on a page assembled before this change — one of the blocks
    that now carry a ref and gain it at the page's next assembly."""
    raw = json.loads(path.read_text())
    legacy = _before_this_version(raw)
    bad: set[str] = set()

    def rec(o: Any, owner: str, field: str, reffed: bool, unknown: bool, pending: bool) -> None:
        if isinstance(o, BaseModel):
            here = reffed or any(getattr(o, k, None) for k in _REF_KEYS)
            unk = unknown or getattr(o, "status", None) in (ds.SourceStatus.UNKNOWN,
                                                            ds.SourceStatus.MISSING)
            pend = pending or (legacy and type(o).__name__ in _NOW_REFFED)
            for k in type(o).model_fields:
                if k not in syn._ID_KEYS and not k.endswith("_id"):
                    rec(getattr(o, k), type(o).__name__, k, here, unk, pend)
        elif isinstance(o, dict):
            here = reffed or any(o.get(k) for k in _REF_KEYS)
            for v in o.values():
                rec(v, owner, field, here, unknown, pending)
        elif isinstance(o, (list, tuple)):
            for v in o:
                rec(v, owner, field, reffed, unknown, pending)
        elif not reffed and o is not None and not isinstance(o, bool):
            nums = syn._FactNumbers()
            syn._stated_numbers(o, nums)
            key = f"{owner}.{field}"
            if nums.values and key not in NOT_A_FACT and not unknown and not pending:
                bad.add(key)

    rec(ds.MechanicalLayer.model_validate(raw["mechanical"]), "MechanicalLayer", "", False, False,
        False)
    assert not bad, f"{path.parent.name}: numbers no point can cite — {sorted(bad)}"


def test_the_ebitda_bases_and_the_ex_lease_multiple_carry_their_computation_ref() -> None:
    from tests.test_net_debt_as_of import _page
    from vinci.dossier.ebitda_basis import EBITDA_BASIS_REF, read_basis
    from vinci.dossier.ev_ebitda_basis import ex_lease_at_price, headline_basis

    raw = json.loads((ROOT / "data/dossiers/GOOGL/dossier.json").read_text())
    mech = ds.MechanicalLayer.model_validate(raw["mechanical"])
    hb = headline_basis(mech)
    assert hb is not None and hb.source_ref and hb.source_ref.startswith("Assembler: ")
    assert read_basis(mech.financial_summary.annual.value).source_ref == EBITDA_BASIS_REF
    assert read_basis(None).source_ref == EBITDA_BASIS_REF
    page, facts, _ref, _cut = _page("NCNO")
    at = ex_lease_at_price(ds.MechanicalLayer.model_validate(page), facts)
    assert at is not None and at.source_ref and at.source_ref.startswith("Assembler: ")
    # the committed pages, assembled before this change, carry none — absent, not null
    assert "source_ref" not in (raw["mechanical"]["valuation"].get("ev_ebitda_basis") or {})


def test_peer_rows_and_the_intensity_block_carry_their_refs() -> None:
    from vinci.dossier.capital_allocation import PEER_INTENSITY_REF, build_peer_capital_intensity

    grid = [types.SimpleNamespace(ticker="AAA", market_cap=1000.0, is_name=True),
            types.SimpleNamespace(ticker="BBB", market_cap=2000.0),
            types.SimpleNamespace(ticker="CCC", market_cap=3000.0)]

    def resolve(t: str) -> Any:
        if t == "CCC":
            raise LookupError(t)
        return types.SimpleNamespace(cik=t)

    def companyfacts(cik: str) -> Any:
        if cik == "BBB":
            raise OSError("unreachable")
        return {"facts": {}}

    pc = build_peer_capital_intensity(grid, resolve=resolve, companyfacts=companyfacts)
    assert pc.source_ref == PEER_INTENSITY_REF
    refs = {r.ticker: r.source_ref for r in pc.rows}
    assert set(refs) == {"AAA", "BBB", "CCC"} and all(refs.values())
    assert refs["AAA"].startswith("EDGAR companyfacts AAA")
    assert refs["BBB"] == refs["CCC"].replace("CCC", "BBB")   # grid-only rows name the grid


def test_checked_maturities_carry_the_panel_line_and_the_filing() -> None:
    from tests.test_debt_maturities import VRRM_8K, VRRM_10Q, _check

    mc = _check("VRRM", [VRRM_10Q, VRRM_8K])
    assert mc.rows and all(r.source_ref for r in mc.rows)
    for r in mc.rows:
        assert r.source_ref is not None and r.description in r.source_ref
        assert (r.source or "not checked") in r.source_ref


def test_implied_expectations_and_each_row_carry_a_ref() -> None:
    from tests.test_dossier import _ie_inputs
    from vinci.dossier import mechanical as dm

    ie = dm._implied_expectations(*_ie_inputs())
    assert ie is not None and ie.source_ref and ie.source_ref.startswith("Assembler: ")
    assert ie.rows and all(r.source_ref and r.multiple_source in r.source_ref for r in ie.rows)


def test_a_filed_ltm_figures_two_ciq_readings_carry_a_ref_a_point_can_cite() -> None:
    """#891's filed-LTM block states CIQ's two readings (the annual export's LTM cell, which the
    page's table no longer shows, and the quarterly export's quarters summed) beside the filed
    figure. They sat under no ref of their own; on CELH's and NFLX's real fixture rows each figure
    now names them, and a point footnoting them to that ref traces, while one footnoting them to a
    quarter's filing, or to the ref on a block built before it, does not. (The filed figure's own
    ref also traces them, but only by the trace's 2% tolerance: the tiebreak admits a reading
    within 2% of the filing, so that is a coincidence of bands, never a citation.)"""
    from tests.test_filed_tiebreak import MERGER, OUI, _decide
    from vinci.dossier import filed_tiebreak as ft

    for name, label in (("CELH", OUI), ("NFLX", MERGER)):
        d = _decide(name, label)
        assert d.figure is not None and d.figure.source_ref == ft.ciq_readings_ref(d.row)
        assert label in d.figure.source_ref and d.figure.ltm_end in d.figure.source_ref
    f = _decide("CELH", OUI).figure
    assert f is not None and f.source_ref and f.value.source_ref
    assert (f.ciq_annual, f.ciq_quarterly) == (-418.8, -405.027)
    base = _frozen()
    assert base.financial_summary is not None
    mech = base.model_copy(update={"financial_summary": base.financial_summary.model_copy(
        update={"filed_ltm": [f]})})
    claim = ("CIQ disagrees with itself on the LTM: the annual export reads -418.8 while the "
             "quarterly export sums to -405.0.")

    def cited(ref: str) -> ds.SourcedPoint:
        return _point(claim, f.source_ref or "", [{"figure": "-418.8", "source_ref": ref},
                                                   {"figure": "-405.0", "source_ref": ref}])

    assert _flagged(mech, cited(f.source_ref)) == []
    assert f.quarters[0].source_ref
    assert _flagged(mech, cited(f.quarters[0].source_ref)) == ["-418.8", "-405"]
    bare = base.model_copy(update={"financial_summary": base.financial_summary.model_copy(
        update={"filed_ltm": [f.model_copy(update={"source_ref": None})]})})
    assert _flagged(bare, cited(f.source_ref)) == ["-418.8", "-405"]


def test_both_consensus_level_builders_name_a_row_alike(monkeypatch: pytest.MonkeyPatch) -> None:
    import inspect

    from vinci.dossier import ciq_sheets as cs
    from vinci.dossier import mechanical as dm
    from vinci.dossier import refresh as rf

    cell = cs.ConsensusCell(fy="2027", median=10.0, high=12.0, low=8.0, std_dev=1.0,
                            estimates="9/10", is_forward=True)
    monkeypatch.setattr(cs, "consensus_levels", lambda _b: {"EBITDA": [cell]})
    for name in ("eps_revisions", "revenue_revisions", "consensus_view", "surprise_history"):
        monkeypatch.setattr(cs, name, lambda _b: ds.Sourced[str].unknown(note="stub"))
    cc = dm._consensus(typing.cast(Any, None))
    assert cc.consensus_levels is not None
    assert cc.consensus_levels["EBITDA"][0].source_ref == cs.consensus_level_ref("EBITDA", "2027")
    assert "consensus_level_ref(m, c.fy)" in inspect.getsource(rf)


# --- the render: web and Markdown, from committed JSON -------------------------------------------

def _footnoted_smpl() -> dict[str, Any]:
    raw = json.loads(_FROZEN_SMPL.read_text())
    name, market, rel = _refs()
    for p in raw["synthesis"]["bull_points"]:
        if p["claim"] == _GD6_CLAIM:
            p["figures"] = [{"figure": "-29%", "source_ref": name},
                            {"figure": "+16%", "source_ref": market},
                            {"figure": "-45pt", "derived": "difference",
                             "inputs": ["-29%", "+16%"]}]
    return raw


def _node_render(pages: dict[str, dict[str, Any]], tmp: Path) -> dict[str, str]:
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    for t, d in pages.items():
        (tmp / f"{t}.json").write_text(json.dumps(d))
    dj = (ROOT / "frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const out = {{}};
for (const t of {json.dumps(sorted(pages))}) {{
  out[t] = renderDossier(JSON.parse(readFileSync(`{tmp.as_posix()}/${{t}}.json`)), null, null);
}}
console.log(JSON.stringify(out));
"""
    res = subprocess.run(["node", "--input-type=module", "-e", driver], capture_output=True,
                         text=True, check=True, cwd=ROOT)
    out: dict[str, str] = json.loads(res.stdout)
    return out


def test_a_footnoted_point_renders_a_mark_per_figure_and_a_collapsed_sources_block(
        tmp_path: Path) -> None:
    """End to end, frozen page → `renderDossier`: an endnote mark right after each cited figure, ‡
    after the computed one, and "How each figure is sourced" collapsed on screen (it force-opens in
    print with every other <details>, styles.css @media print)."""
    html = _node_render({"SMPL": _footnoted_smpl()}, tmp_path)["SMPL"]
    point = next(seg for seg in html.split('<div class="point bull">')[1:] if "-45pt" in seg)
    assert re.search(r"-29%<sup class=\"cite-n\"[^>]*>\[A\d+\]</sup>", point), point[:400]
    assert re.search(r"\+16%<sup class=\"cite-n\"[^>]*>\[A\d+\]</sup>", point), point[:400]
    assert '-45pt<sup class="cite-d"' in point
    det = point.split('<details class="fig-cites"', 1)[1].split("</details>", 1)[0]
    assert not det.lstrip().startswith("open") and "How each figure is sourced (3)" in det
    assert "-45pt</b> ‡ computed: -29% − +16%" in det
    _, market, _ = _refs()
    assert market.split(" (")[0] in det
    css = (ROOT / "frontend/assets/styles.css").read_text()
    print_css = css[css.index("@media print"):]
    assert "details:not([open]) { display: block !important; }" in print_css


def test_no_committed_page_renders_a_footnote_mark_before_its_next_assembly(
        tmp_path: Path) -> None:
    """Every committed page today carries no `figures`, so none renders a ‡ or a sources block —
    the points render as they did (claim + one cite)."""
    pages = {p.parent.name: json.loads(p.read_text()) for p in _COMMITTED[:9]}
    for t, html in _node_render(pages, tmp_path).items():
        assert 'class="cite-d"' not in html and "fig-cites" not in html, t


def test_the_markdown_render_footnotes_each_figure() -> None:
    from vinci.dossier.render import render_markdown

    md = render_markdown(ds.Dossier.model_validate(_footnoted_smpl()))
    line = next(ln for ln in md.splitlines() if "-45pt" in ln and ln.startswith("- "))
    assert re.search(r"-29%\[\d+\]", line) and re.search(r"\+16%\[\d+\]", line)
    assert "-45pt‡" in line
    assert "How each figure is sourced: -29% [" in md and "-45pt ‡ = -29% − +16%" in md
    plain = render_markdown(ds.Dossier.model_validate(json.loads(_FROZEN_SMPL.read_text())))
    assert "How each figure is sourced" not in plain and "‡" not in plain


# --- review fixes (code-review round 0) ----------------------------------------------------------

def test_a_footnote_to_a_transcript_ref_the_page_does_not_carry_is_a_caveat_not_a_soft_note() -> (
        None):
    """'transcript' in a made-up ref bought the soft, hidden TRANSCRIPT-FIGURE route: a fabricated
    figure footnoted to "CIQ transcript(s): made up" reached the page with no caveat. Only a
    transcript the layer carries is soft."""
    mech = _frozen()
    _, market, rel = _refs()
    fake = _point(_GD6_CLAIM, rel, [{"figure": "-29%", "source_ref": "CIQ transcript(s): made up"},
                                    {"figure": "+16%", "source_ref": market}])
    flags = _flags(mech, fake)
    assert [f.split("'")[1] for f in flags if f.startswith("UNTRACEABLE")] == ["-29"]
    assert not any(f.startswith("TRANSCRIPT-FIGURE") for f in flags)
    caveats, _ = dflags.partition(flags)
    assert any(c.startswith("Untraceable figure -29 (a bull point)") for c in caveats), caveats


def test_a_footnote_covers_its_own_figure_never_another_of_the_same_magnitude() -> None:
    """Entries were keyed by magnitude and re-used once exhausted, so a footnoted "$16M" also
    passed the un-footnoted "16%" beside it — which then escaped the point-ref trace."""
    mech = _frozen()
    _, market, rel = _refs()
    claim = "SMPL fell -29% while the benchmark rose 16%, on $16M of volume"
    assert _flagged(mech, _point(claim, rel)) == ["-29", "16", "16"]
    assert _flagged(mech, _point(claim, rel, [{"figure": "$16M", "source_ref": market}])) == [
        "-29", "16"]
    # a figure the claim writes twice is covered twice by its one footnote
    twice = "the benchmark rose +16% and, again, +16%"
    assert _flagged(mech, _point(twice, rel, [{"figure": "+16%", "source_ref": market}])) == []


def test_a_footnote_is_matched_to_the_occurrence_it_names_not_the_first_of_its_magnitude() -> (
        None):
    """(Codex P2, round 1) Entries were bucketed by magnitude, so a "$16M" footnote was spent on an
    earlier "-16%" and the "$16M" itself fell back to the point's ref: the caveat named "-16" as
    footnoted to the volume's fact. Matched by where its literal is written, the footnote checks
    its own figure and the "-16%" is traced to the point's ref (which states the 16)."""
    mech = _frozen()
    name, market, _ = _refs()
    claim = "SMPL fell -16% while volume ran to $16M"
    flags = _flags(mech, _point(claim, market, [{"figure": "$16M", "source_ref": name}]))
    hard = [f for f in flags if f.startswith("UNTRACEABLE")]
    assert [f.split("'")[1] for f in hard] == ["16"]
    assert f"[cited to {name}]" in hard[0]
    # the same footnote on the "-16%" instead: that figure is the one checked against `name`
    flags = _flags(mech, _point(claim, market, [{"figure": "-16%", "source_ref": name}]))
    assert [f.split("'")[1] for f in flags if f.startswith("UNTRACEABLE")] == ["-16"]


def test_a_signed_computed_figure_must_carry_the_sign_its_operation_gives() -> None:
    """(Codex P1, round 1) The recompute compared magnitudes, so "+45pt" declared as -29% − +16%
    (which gives -45) passed. A figure written with a sign is compared signed; an unsigned one
    ("a 45pt gap", its direction in words) is compared on its size, as the trace compares."""
    mech = _frozen()
    name, market, rel = _refs()
    figs = [{"figure": "-29%", "source_ref": name}, {"figure": "+16%", "source_ref": market}]

    def gap(lit: str) -> list[str]:
        return _flagged(mech, _point(_GD6_CLAIM.replace("-45pt", lit), rel, [
            *figs, {"figure": lit, "derived": "difference", "inputs": ["-29%", "+16%"]}]))

    assert gap("-45pt") == []
    assert gap("45pt") == []
    assert gap("+45pt") == ["45"]
    assert gap("−45pt") == []   # the typographic minus is a sign too


def test_a_footnote_whose_inputs_are_not_a_list_is_dropped_not_a_crash() -> None:
    notes: list[str] = []
    raw = {"evidence_balance": "mixed — x", "bull_points": [{
        "claim": "a 3.3x figure", "source_ref": "R", "figures": [
            {"figure": "3.3x", "derived": "ratio", "inputs": 5},
            {"figure": "3.3x", "derived": "ratio", "inputs": "ab"}]}],
        "bear_points": [], "twin_reference_cases": [], "key_unknowns": [],
        "decisive_question": {"question": "q", "evidence_for": [], "evidence_against": []}}
    s = syn._parse(raw, notes)
    assert s.bull_points[0].figures == [] and len(notes) == 2


def test_a_mark_never_lands_inside_a_longer_decimal() -> None:
    from vinci.dossier.render import _find_figure

    claim = "margin 5.4% across 5 segments"
    assert _find_figure(claim, "5", 0) == claim.index("5 segments")
    assert _find_figure("$1,098M and 98", "98", 0) == len("$1,098M and ")


def test_a_footnoted_markdown_point_keeps_its_tag_before_its_own_cite() -> None:
    """The un-footnoted point prints claim, tag, warning, then its cite; a footnoted one printed
    its cite before the tag — and with no endnote table, the tag after the cite's sub-line."""
    from vinci.dossier.render import _footnoted_claim

    _, market, rel = _refs()
    p = _point("rose +16%", rel, [{"figure": "+16%", "source_ref": market}])
    assert _footnoted_claim(p, " (crux)") == f"rose +16% (crux)\n  - ↳ `{rel}`"
