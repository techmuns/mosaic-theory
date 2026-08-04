"""(`scenario-create`) THE PROPOSER — what it defaults, and everything it refuses.

DRIVEN OFF THE COMMITTED DOSSIERS, not constructed dicts, wherever the assertion is structural: the
recurring defect this session is a test whose subject and whose oracle come from different places.
Value-level pins use frozen literals so a re-assembly cannot rot them.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier.propose import (
    ANCHORED,
    AXES,
    LEGS,
    UNPROPOSED_REASON,
    Anchor,
    ProposalRefusedError,
    check_tier_agreement,
    propose_anchors,
    validate_legs,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"


def _doc(t: str) -> dict:
    return json.loads((DOSS / t / "dossier.json").read_text())


def _legs(**over) -> dict[str, dict]:
    # dict.fromkeys is NOT the substitution ruff suggests here: it would give all three legs the
    # SAME inner dict, so patching one would silently patch the others.
    base: dict[str, dict] = {}
    for leg in LEGS:
        base[leg] = dict.fromkeys(AXES, 1.0)
    for leg, patch in over.items():
        base.setdefault(leg, {}).update(patch)
    return base


# --- what it proposes ---------------------------------------------------------------------------


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_exactly_three_axes_are_proposed_and_all_three_are_medians() -> None:
    """THE COUNT IS THE FINDING, and it is three — not six, which the first cut of the derivability
    read claimed. The safe anchors are exactly the MEDIANS: a median absorbs one bad year, while a
    min/max/band-low IS the statistic one observation defines."""
    ancs = propose_anchors(_doc("SMPL"))
    assert {(a.axis, a.leg) for a in ancs} == set(ANCHORED)
    assert all(a.leg == "base" for a in ancs), "a non-base leg acquired a default"
    assert {a.role for a in ancs} <= {"median", "consensus"}, [a.role for a in ancs]
    assert len(ancs) == 3 and 9 - len(ancs) == 6


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_every_proposal_carries_a_source_and_a_vintage() -> None:
    """SCHEMA 1.4 REQUIRES `vintage`, AND THIS IS WHY IT EXISTS: SMPL's five committed margin
    references are unstamped, so when three of its live references moved (LTM revenue, consensus,
    current multiple) nothing could say whether they were right when struck. A proposal that
    inherits no vintage would reproduce that defect on every record written from here."""
    for a in propose_anchors(_doc("SMPL")):
        rp = a.as_refpoint()
        assert rp.source.strip() and rp.vintage and rp.vintage.strip(), a
        assert rp.leg == "base" and rp.role


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_cohort_partner_proposes_from_its_own_longest_coverage_anchor() -> None:
    """BRBR IS THE ALIAS SHAPE, so this pins the anchor it actually proposes from. Its ASC-606 tag
    holds ONE fiscal year while `Revenues` holds seven; `midcycle` picks longest-coverage, so the
    margin anchor must be sourced to `Revenues` and NOT to the truncated tag. If the shared
    first-hit extractor ever becomes the anchor's source, this goes red."""
    mg = next(a for a in propose_anchors(_doc("BRBR")) if a.axis == "margin")
    assert "Revenues" in mg.source and "OperatingIncomeLoss" in mg.source, mg.source
    assert "RevenueFromContractWithCustomer" not in mg.source, (
        "BRBR's margin anchor is sourced to the ASC-606 tag, which holds ONE year for this filer — "
        "the first-hit truncation reached the anchor")


def test_a_dossier_without_the_inputs_proposes_less_never_invents() -> None:
    assert propose_anchors({}) == []
    assert [a.axis for a in propose_anchors({"anchor": {"margin": {"value": 0.16,
                                                                  "anchor_years": 8,
                                                                  "source": "s"}}})] == ["margin"]


# --- what it refuses ----------------------------------------------------------------------------


def test_the_six_unproposed_cells_each_state_why_they_are_unproposed() -> None:
    """A guard that says only "missing" is an obstacle; one that says WHY is a guard. Every cell
    with no proposal carries its reason, and the reasons are the two distinct classes —
    UNANCHORED (no statistic) and CONTAMINABLE (the wrong kind of statistic)."""
    unproposed = {(ax, lg) for ax in AXES for lg in LEGS} - set(ANCHORED)
    assert set(UNPROPOSED_REASON) == unproposed and len(unproposed) == 6
    assert all(v.strip() for v in UNPROPOSED_REASON.values())


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_committed_smpl_base_margin_is_refused_which_is_the_whole_point() -> None:
    """§D, MADE STRUCTURALLY IMPOSSIBLE. SMPL's record states a base margin of 14.0% derived by
    averaging a cited anchor against a figure that exists nowhere but prose. Against the computed
    anchor of 15.4481% that is a −1.45pp deviation, and the writer now refuses it unless the
    adjustment is stated. The ruling moved into the write path, where it binds every author."""
    ancs = propose_anchors(_doc("SMPL"))
    # SCHEMA UNITS — ScenarioInput.margin is a decimal fraction, so the committed 14.0% is 0.14.
    problems = validate_legs(_legs(base={"revenue": 1330.0, "margin": 0.14, "multiple": 12.5}),
                             ancs)
    hit = [p for p in problems if p.startswith("base.margin")]
    assert hit and "15.4481" in hit[0] and "-0.014481" in hit[0], problems
    assert "§D" in hit[0]


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_stating_the_adjustment_clears_it_and_matching_the_anchor_needs_nothing() -> None:
    """THE POSITIVE HALF. The guard demands a stated derivation, not a particular number — an
    analyst who says why may sit anywhere, and one who takes the anchor states nothing."""
    ancs = propose_anchors(_doc("SMPL"))
    m = next(a for a in ancs if a.axis == "margin")
    stated = _legs(base={"revenue": 1330.0, "margin": 0.14, "multiple": 12.5,
                         "margin_adjustment": "−1.45pp: this year's gross-margin reset treated as "
                                              "partly structural"})
    assert not [p for p in validate_legs(stated, ancs) if p.startswith("base.margin")]
    at_anchor = _legs(base={"revenue": 1351.7, "margin": m.schema_value,
                            "multiple": 17.8514})
    assert not [p for p in validate_legs(at_anchor, ancs) if p.startswith("base.")]


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_an_unanchored_leg_must_state_a_basis_and_a_missing_leg_is_never_defaulted() -> None:
    ancs = propose_anchors(_doc("SMPL"))
    bare = validate_legs(_legs(), ancs)
    assert any(p.startswith("bear.revenue") and "revenue_derivation" in p
               for p in bare), bare
    with_basis = _legs(bear={"revenue_derivation": "b", "margin_derivation": "d",
                             "multiple_derivation": "m"})
    assert not [p for p in validate_legs(with_basis, ancs) if p.startswith("bear.")]

    dropped = _legs()
    del dropped["bear"]
    assert any("leg 'bear' is missing" in p and "refusing to default" in p
               for p in validate_legs(dropped, ancs))


def test_a_supplied_none_is_refused_with_the_reason_it_was_not_proposed() -> None:
    """ABSENT is not zero and not "use the anchor" — it is refused, and the refusal repeats why the
    cell has no proposal so the analyst is not sent to look it up."""
    ancs = [Anchor("margin", "base", 15.0, "%", 0.15, "median", "l", "s", "v")]
    out = validate_legs(_legs(bear={"margin": None}), ancs)
    assert any(p.startswith("bear.margin is required and absent") and "judgment" in p
               for p in out), out


# --- the recipe/tier disagreement, which has a live case ----------------------------------------


def test_a_dossier_record_recipe_disagreement_refuses_and_aort_is_the_live_case() -> None:
    """AORT ON DAY ONE. Its dossier reads `recipe_hint: R1_midcycle_margin_evebitda`,
    `applicable: True`, while its committed record is R2 (`tier: B`). The record governs — but a
    silent disagreement is how a record acquires the wrong arithmetic, so the write stops."""
    if (DOSS / "AORT").is_dir():
        aort = _doc("AORT")
        assert (aort.get("anchor") or {}).get("recipe_hint") == "R1_midcycle_margin_evebitda", (
            "AORT no longer carries the hint this pin was built on — re-check the live case")
        with pytest.raises(ProposalRefusedError, match="disagrees"):
            check_tier_agreement(aort, "R2_terminal_margin")
    check_tier_agreement({"anchor": {"recipe_hint": "R1_midcycle_margin_evebitda"}},
                         "R1_midcycle_margin_evebitda")
    with pytest.raises(ProposalRefusedError, match="R2_NEEDED"):
        check_tier_agreement({"anchor": {"recipe_hint": "R2_NEEDED"}},
                             "R1_midcycle_margin_evebitda")


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_margin_anchor_is_compared_in_schema_units_not_display_units() -> None:
    """TWO UNITS, TWO FIELDS — caught in self-review of this PR. `ScenarioInput.margin` is a DECIMAL
    FRACTION (SMPL's committed legs are 0.1 / 0.14 / 0.165) while a `RefPoint` displays a margin as
    `15.4481` + `"%"`. A single field would compare a supplied 0.14 against 15.4481 and report a
    99% deviation on a leg that matches its anchor EXACTLY — display formatting made load-bearing,
    which is the rule this repo already has."""
    m = next(a for a in propose_anchors(_doc("SMPL")) if a.axis == "margin")
    assert m.unit == "%" and abs(m.value - 15.4481) < 1e-4, m       # display
    assert abs(m.schema_value - 0.154481) < 1e-6, m                  # what a leg is compared to
    assert m.as_refpoint().value == m.value

    ancs = [m]
    at_anchor = _legs(base={"margin": m.schema_value})               # schema units == no deviation
    assert not [p for p in validate_legs(at_anchor, ancs) if p.startswith("base.margin")]
    display_units = _legs(base={"margin": m.value})                  # 15.4481 IS a real deviation
    assert [p for p in validate_legs(display_units, ancs) if p.startswith("base.margin")]


def test_a_zero_anchor_does_not_silently_accept_everything() -> None:
    """The relative-drift fallback used to read `0.0` for a zero anchor, so ANY supplied value
    passed. A zero anchor is pathological, and silently accepting is the wrong failure."""
    ancs = [Anchor("margin", "base", 0.0, "%", 0.0, "median", "l", "s", "v")]
    assert [p for p in validate_legs(_legs(base={"margin": 9.9}), ancs)
            if p.startswith("base.margin")]
    assert not [p for p in validate_legs(_legs(base={"margin": 0.0}), ancs)
                if p.startswith("base.margin")]


def test_applicable_false_is_a_disagreement_and_vitl_is_the_second_live_case() -> None:
    """VITL, MISSED BY THE FIRST CUT. It carries `recipe_hint: R1_midcycle_margin_evebitda` with
    `applicable: False` — the dossier declining that recipe for this name (EBITDA dispersion 263.7%,
    so it routes two-ratio). Checking only the hint STRING waved it through."""
    if (DOSS / "VITL").is_dir():
        vitl = _doc("VITL")
        assert (vitl.get("anchor") or {}).get("applicable") is False, (
            "VITL is no longer applicable=False — re-check this live case")
        with pytest.raises(ProposalRefusedError, match="applicable=False"):
            check_tier_agreement(vitl, "R1_midcycle_margin_evebitda")
    check_tier_agreement({"anchor": {"recipe_hint": "R1_midcycle_margin_evebitda",
                                     "applicable": True}}, "R1_midcycle_margin_evebitda")
