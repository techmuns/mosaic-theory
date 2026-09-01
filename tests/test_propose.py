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


# --- the template + the create path --------------------------------------------------------------


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_template_prefills_three_and_leaves_six_empty_with_their_reasons() -> None:
    from vinci.dossier.propose import build_template, legs_from_template
    tpl = build_template(_doc("BRBR"))
    legs = legs_from_template(tpl)
    filled = [(lg, ax) for lg in LEGS for ax in AXES if legs[lg][ax] is not None]
    assert sorted(filled) == sorted((lg, ax) for ax, lg in ANCHORED), filled
    for ax, lg in ANCHORED:
        assert tpl["scenarios"][lg][f"_{ax}_anchor"].strip(), (ax, lg)
    for lg in LEGS:
        for ax in AXES:
            if (ax, lg) not in set(ANCHORED):
                assert tpl["scenarios"][lg][f"_{ax}_why_no_anchor"] == UNPROPOSED_REASON[(ax, lg)]
    # commentary is stripped before validation, so a '_' key can never be read as an input
    assert not any(k.startswith("_") for cell in legs.values() for k in cell)


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_template_carries_the_peer_row_beside_the_own_history_band() -> None:
    """THE MISTAKE THIS BLOCK EXISTS TO PREVENT (operator, working BellRing by hand): anchoring on
    own history, taking a haircut, calling it conservative — while the name trades at a PREMIUM to
    the peer median. BRBR is the live case: LTM TEV/EBITDA 8.8 against a peer median of 6.9."""
    from vinci.dossier.propose import build_template
    mult = build_template(_doc("BRBR"))["_evidence"]["multiple"]
    assert any("own history" in x for x in mult)
    peer = next(x for x in mult if "PEER CROSS-SECTION" in x)
    assert "TEV/EBITDA" in peer and "NTM TEV/EBITDA" in peer, peer
    assert "Median" in peer and "Low" in peer and "High" in peer, peer


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_own_history_line_names_a_rank_not_a_percentile_level() -> None:
    """`own_history.percentile` is WHERE CURRENT SITS (BRBR: 0.037 → 3.7th), not a 25th-percentile
    LEVEL. The first cut printed it as `p25`, putting a 0.037 rank where a multiple belongs."""
    from vinci.dossier.propose import build_template
    line = build_template(_doc("BRBR"))["_evidence"]["multiple"][0]
    assert "pctile of its own range" in line and "p25 0.03" not in line, line


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_no_evidence_line_is_empty() -> None:
    """`startswith("revenue")` also matched "Revenue YoY" and emitted a blank arc — evidence nobody
    can read is noise in a block whose only purpose is to be read."""
    from vinci.dossier.propose import build_template
    for axis, lines in build_template(_doc("BRBR"))["_evidence"].items():
        for line in lines:
            assert line.strip() and not line.rstrip().endswith(":"), (axis, line)


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_shares_denominator_is_taken_stated_and_refused_on_disagreement() -> None:
    """ITEM 24: the denominator is diluted outstanding AT THE VALUATION DATE, and NEITHER dossier
    field is that — one is diluted-but-averaged, the other at-a-date-but-basic. The create path
    takes the point-in-time count, SAYS what it is and is not, and refuses a structural gap."""
    from vinci.dossier.propose import SHARE_DISAGREEMENT_TOL, resolve_shares
    val, basis, source = resolve_shares(_doc("BRBR"))
    # FROZEN LITERALS, per this file's stated convention — the oracle must not come from the same
    # artifact as the subject, or a corrupted dossier value would satisfy the check that reads it.
    # They moved when BRBR was re-assembled 2026-08-10 against a newer filing (diluted 117,500,000
    # → 116,600,000, so the point-in-time gap narrowed 1.05% → 0.28%), and they were re-pinned in
    # THAT PR alongside the regenerated companyfacts fixture — which is the workflow the fixture's
    # own error message prescribes, and the reason a literal here is a deliberate edit rather than
    # a rot: nothing moves these numbers except a re-assembly someone chose to make.
    assert abs(val - 116.278194) < 1e-5, val         # MILLIONS, the ScenarioRecord.facts unit
    assert "point-in-time" in basis and "BASIC" in basis and "do not assume it" in basis
    assert "116,600,000" in basis and "0.28%" in basis, basis

    far = {"ticker": "X", "mechanical": {"stock_info": {"shares_out": {"value": 100e6}}},
           "anchor": {"diluted_shares": {"value": 100e6 * (1 + SHARE_DISAGREEMENT_TOL + 0.01)}}}
    with pytest.raises(ProposalRefusedError, match="disagree"):
        resolve_shares(far)
    with pytest.raises(ProposalRefusedError, match="absent or non-positive"):
        resolve_shares({"ticker": "X", "mechanical": {"stock_info": {"shares_out": {"value": 0}}}})


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_anchors_reach_the_record_as_sourced_vintaged_references() -> None:
    """THE LEAK THIS CLOSES, caught in self-review of #334. `Anchor.as_refpoint()` had ZERO
    production callers — defined, never called — and the create path built no `assumptions` at all,
    so every anchor's source and vintage, and every adjustment/derivation the analyst stated, was
    validated and then dropped on the floor.

    (`ScenarioRecord` refuses a 1.4 record whose assumptions miss an axis, so the path was BROKEN
    rather than silently lossy — but a create path that cannot write is not a create path.)"""
    from vinci.dossier.propose import assumptions_from, build_template, legs_from_template
    doc = _doc("BRBR")
    legs = legs_from_template(build_template(doc))
    asm = assumptions_from(doc, legs)
    assert set(asm) == set(AXES)
    for axis, a in asm.items():
        assert a["method"].strip(), axis
        refs = a["references"]
        assert len(refs) == 1, (axis, refs)               # one anchored (base) cell per axis
        r = refs[0]
        assert r["source"].strip() and r["vintage"] and r["leg"] == "base", (axis, r)
        assert r["role"] in {"median", "consensus"}, r


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_composed_method_names_the_statistic_not_the_house_label() -> None:
    """The prose linter flags "anchor" as a house token — *state the claim, not the house label* —
    and it is right. Analyst words are never edited; this sentence is the MACHINE's, so it is the
    machine's to get right."""
    from vinci.dossier.propose import assumptions_from, build_template, legs_from_template
    doc = _doc("BRBR")
    asm = assumptions_from(doc, legs_from_template(build_template(doc)))
    for axis, a in asm.items():
        assert "computed anchor" not in a["method"], (axis, a["method"])
        assert "median" in a["method"], (axis, a["method"])


@pytest.mark.skipif(not (DOSS / "BRBR").is_dir(), reason="no committed BRBR")
def test_the_shares_fact_labels_its_unit_as_millions() -> None:
    """`resolve_shares` returns MILLIONS and the first cut labelled the fact "shares" — a unit
    label disagreeing with its own value, which is `percentile`-as-`p25` one field over. SMPL's
    committed record says "M shares" for exactly this reason."""
    from vinci.dossier.propose import build_template
    f = build_template(_doc("BRBR"))["facts"]["diluted_shares"]
    assert f["unit"] == "M shares" and 100 < f["value"] < 200, f


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_template_carries_the_operating_drivers_under_every_axis() -> None:
    """THE ROWS THE ANALYST SETS SIX NUMBERS AGAINST. Until 2026-08-04 the cap deleted them from the
    artifact; recovering them put them on the PAGE, but the page having them is not the analyst
    having them at the judgment. The template is where the judgment happens.

    UNSPLIT, and that is the finding rather than laziness: `kind` states what KIND of claim a row
    is, not which axis it informs. Measured — `attribution` rows are all EXPENSE lines (margin, not
    revenue), `pricing_action` moves revenue AND margin together, and `leading_indicator` is a
    unit/KPI run-rate that is revenue-shaped on SMPL but was `adjusted gross margin` on BRBR. No
    mapping is derivable, so none was invented; the full set goes under each axis.
    """
    from vinci.dossier.propose import build_template
    doc = _doc("SMPL")
    ev = build_template(doc)["_evidence"]
    rows = ((doc["mechanical"].get("operating_drivers") or {}).get("rows")) or []
    assert rows, "SMPL has no driver rows — re-pin this"
    for axis in AXES:
        head = [ln for ln in ev[axis] if ln.startswith("OPERATING DRIVERS")]
        assert head, f"{axis} carries no driver block"
        assert f"{len(rows)} rows" in head[0], head[0]
        assert "no axis mapping is derivable" in head[0]
        emitted = [ln for ln in ev[axis] if ln.startswith("  [")]
        assert len(emitted) == len(rows), (axis, len(emitted), len(rows))


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_forward_peer_leg_is_in_the_template_whatever_a_roll_cites() -> None:
    """THE REROLL DEMONSTRATED THE NEED. SMPL's 2026-08-04 re-assembly dropped the FORWARD peer
    comparison from its synthesis (NTM TEV/EBITDA 5.65 vs 8.72, NTM P/E 6.12 vs 13.08 all vanished)
    and argued from trailing 5.3x — the very basis the PREVIOUS roll had warned 'cannot itself
    distinguish cheap-overshoot from cheap-terminal'. The data never left the page; the ARGUMENT
    did. The template carries both bases so the analyst does not depend on what a roll cited."""
    from vinci.dossier.propose import build_template
    mult = " ".join(build_template(_doc("SMPL"))["_evidence"]["multiple"])
    assert "NTM TEV/EBITDA" in mult and "NTM P/E" in mult, mult[:300]
    assert "TEV/EBITDA:" in mult, "the LTM peer row is gone"
    assert "disagree in SIGN" in mult, "the LTM-vs-NTM warning is gone"


def test_the_template_never_truncates_a_driver_value() -> None:
    """A BOUND THAT BUYS NOTHING STILL DROPS THINGS — the row cap's argument one scale down. The
    template's driver block once truncated values at 130 chars, copied from the LLM digest where the
    cap bounds *input*. A template is a file the ANALYST reads: no token budget, so the cap bought
    nothing. Measured across the fleet before removal: 11 of 242 values exceeded it and TWO carried
    a figure in the tail the kept head did not."""
    import json as _json
    import pathlib as _pl

    from vinci.dossier.propose import build_template
    for folder in sorted((DOSS).glob("*/dossier.json")):
        doc = _json.loads(_pl.Path(folder).read_text())
        rows = ((doc.get("mechanical") or {}).get("operating_drivers") or {}).get("rows") or []
        if not rows:
            continue
        try:
            ev = build_template(doc)["_evidence"]
        except Exception:                       # a name the proposer refuses is out of scope here
            continue
        blob = "\n".join(ev["revenue"])
        for r in rows:
            val = str(r.get("value") or "")
            if val:
                assert val in blob, (
                    f"{folder.parent.name}: driver value truncated in the template — {val[:60]!r}")
        assert "…" not in blob, f"{folder.parent.name}: an ellipsis means a value was cut"


def test_scenario_create_refuses_a_name_that_already_has_a_record(tmp_path, monkeypatch) -> None:
    """A CREATE MUST NEVER OVERWRITE. `write_record` is an unconditional `path.write_text`, so
    without this guard `scenario-create SMPL` would DESTROY the live record and skip
    archive-and-reissue — and the supersession chain (`_amendment_index`, the archived
    `<TICKER>-<date>`) is the record of what a verdict replaced, unreconstructable once gone.

    REFUSES rather than routing: a create that silently becomes a supersede is a surprise on a
    destructive path, and `scenario-propose` emits a template that LOOKS like it feeds this command.
    BOTH DIRECTIONS pinned — refuses when a record exists, proceeds past this check when none does.
    """
    import argparse
    import json as _json

    import vinci.scenarios as sc
    from vinci.cli import _cmd_scenario_create

    recs = tmp_path / "scenarios"
    recs.mkdir()
    monkeypatch.setattr(sc, "records_dir", lambda root=None: recs)
    tpl = tmp_path / "t.json"
    tpl.write_text(_json.dumps({"ticker": "ZZZZ", "recipe_id": "R1_midcycle_margin_evebitda"}))
    args = argparse.Namespace(ticker="ZZZZ", from_file=str(tpl))

    # NEGATIVE — a record exists: refused, and the refusal names the other command.
    (recs / "ZZZZ.json").write_text("{}")
    out: list[str] = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: out.append(" ".join(map(str, a))))
    assert _cmd_scenario_create(args) == 1
    msg = " ".join(out)
    assert "already has a committed record" in msg and "scenario-supersede" in msg, msg
    assert "--payload" in msg, "the refusal does not state what supersede needs"
    assert (recs / "ZZZZ.json").read_text() == "{}", "the existing record was touched"

    # POSITIVE — no record: the guard lets it through (it then fails later, on the absent dossier,
    # which is a DIFFERENT refusal and proves this check is not what stopped it).
    (recs / "ZZZZ.json").unlink()
    out.clear()
    assert _cmd_scenario_create(args) == 1
    assert "already has a committed record" not in " ".join(out), out


@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), reason="no committed SMPL")
def test_the_margin_trend_is_labelled_ebitda_against_an_ebit_leg() -> None:
    """THE ONE EBITDA FIGURE IN AN EBIT BLOCK. The anchor is `OperatingIncomeLoss / Revenue`, the
    raw series is EBIT, and R1's leg is an operating margin — but the CIQ trend is an EBITDA series.
    With SMPL's D&A at ~2.7% of revenue, 16% EBITDA LTM sits deceptively close to a 15.4481% EBIT
    anchor. This is the axis §D happened on, and an unlabelled basis is how two numbers get averaged
    into one."""
    from vinci.dossier.propose import build_template
    line = next(x for x in build_template(_doc("SMPL"))["_evidence"]["margin"]
                if x.startswith("margin trend"))
    assert "EBITDA basis" in line and "NOT the EBIT margin" in line, line


# --- the R2_NEEDED crash: a template must never be shaped for a recipe the dossier refused --------


def _inapplicable(hint: str, reason: str) -> dict:
    """A dossier whose anchor refused — the shape NCNO/UBER/MVST carry live."""
    return {"ticker": "ZZZZ",
            "anchor": {"applicable": False, "recipe_hint": hint, "reason": reason}}


def test_an_inapplicable_anchor_refuses_instead_of_raising_keyerror() -> None:
    """THE REGRESSION PIN, and it fails on the pre-fix code with the exact production error.

    NCNO and UBER both carry `applicable=False` / `recipe_hint="R2_NEEDED"`, so `propose_anchors`
    returns no `("margin","base")` anchor — revenue and multiple still resolve, margin alone does
    not. `build_template` then indexed `UNPROPOSED_REASON[("margin","base")]`, a table holding only
    bear/bull entries, and raised `KeyError: ('margin', 'base')`. `_cmd_scenario_propose` catches
    `FileNotFoundError` and `ProposalRefusedError`; KeyError is neither, so it reached the user as a
    traceback on an UNDERWRITTEN name."""
    from vinci.dossier.propose import build_template

    with pytest.raises(ProposalRefusedError, match="applicable=False"):
        build_template(_inapplicable("R2_NEEDED", "no positive operating margin over history"))


def test_the_refusal_points_at_ev_revenue_only_when_that_is_the_cause() -> None:
    """THE REMEDY IS PER CAUSE. Three live shapes refuse here and only one is about the missing
    revenue-basis path: MVST/NCNO/UBER hint `R2_NEEDED`; FUBO's anchor refused on a missing
    own-history multiple (hint `unknown`); VITL's on a coherence guard while still hinting R1.
    Telling FUBO and VITL to resolve an EV/Revenue recipe sends them to fix something unrelated."""
    from vinci.dossier.propose import build_template

    with pytest.raises(ProposalRefusedError, match="EV/Revenue basis exists"):
        build_template(_inapplicable("R2_NEEDED", "no positive operating margin"))
    for hint in ("unknown", "R1_midcycle_margin_evebitda"):
        with pytest.raises(ProposalRefusedError) as exc:
            build_template(_inapplicable(hint, "own-history multiple missing"))
        assert "EV/Revenue" not in str(exc.value), (hint, str(exc.value))


def test_the_refusal_quotes_the_dossiers_own_reason_and_hint() -> None:
    """NOT RE-WORDED HERE. The dossier already states why the anchor refused; a second author for
    one fact is how the two drift."""
    from vinci.dossier.propose import build_template

    with pytest.raises(ProposalRefusedError) as exc:
        build_template(_inapplicable("R2_NEEDED", "no positive operating margin over history"))
    assert "no positive operating margin over history" in str(exc.value)
    assert "'R2_NEEDED'" in str(exc.value)


def test_an_applicable_anchor_is_untouched_by_the_new_refusal() -> None:
    """THE NEGATIVE PIN. A guard that refuses everything is a freeze — an anchor that APPLIES must
    pass through, and `applicable` ABSENT (pre-field artifacts) must not read as False."""
    from vinci.dossier.propose import _refuse_if_recipe_unresolved

    _refuse_if_recipe_unresolved({"anchor": {"applicable": True}}, "ZZZZ")
    _refuse_if_recipe_unresolved({"anchor": {}}, "ZZZZ")
    _refuse_if_recipe_unresolved({}, "ZZZZ")


def test_a_missing_base_axis_no_longer_crashes_the_cell_builder() -> None:
    """DEFENCE IN DEPTH, one layer under the refusal. The refusal catches the KNOWN cause; this
    covers a base axis going missing for some other reason, where a crash is never the right
    answer. `UNPROPOSED_REASON` still has no base entries by design — base anchors are supposed to
    exist — so the fallback names the axis and demands a derivation."""
    from vinci.dossier.propose import UNPROPOSED_REASON

    assert not [k for k in UNPROPOSED_REASON if k[1] == "base"], (
        "a base entry appeared in UNPROPOSED_REASON — if base axes are now legitimately "
        "unproposable, this test and the fallback both need rethinking")
    assert UNPROPOSED_REASON.get(("margin", "base")) is None


@pytest.mark.skipif(not DOSS.is_dir(), reason="no committed dossiers")
def test_no_committed_name_crashes_the_template_builder() -> None:
    """CORPUS BEFORE SYNTHETIC. The pins above run on constructed docs; this one runs on every
    committed dossier, because the defect reached production on names that were already in the
    fleet. Any outcome is acceptable EXCEPT an exception that is not a stated refusal."""
    from vinci.dossier.propose import build_template

    built, refused = [], []
    for p in sorted(DOSS.glob("*/dossier.json")):
        try:
            build_template(json.loads(p.read_text()))
            built.append(p.parent.name)
        except ProposalRefusedError:
            refused.append(p.parent.name)
        except Exception as exc:  # noqa: BLE001 — that is the whole point of this pin
            pytest.fail(f"{p.parent.name}: {type(exc).__name__}: {exc} — every failure here must "
                        f"be a stated ProposalRefusedError, never a raw exception")
    assert built, f"no committed name builds a template — refused={refused}"
    assert refused, "no committed name refuses — the refusal path has gone vacuous"


# ---------------------------------------------------------------------------------------------
# R3 — a recipe whose axes are NOT the R1 trio. The create path validated legs, composed
# assumptions, and serialized them all against a module-level `AXES = (revenue, margin,
# multiple)`. Every one of those three refused or corrupted a well-formed forward-P/E record:
# it demanded two numbers R3's arithmetic never reads, compared a P/E turn against an EV/EBITDA
# median, and would have composed provenance over the axes the record does not use.
# Driven off the REAL committed GOOGL dossier and the REAL committed record — the recipe was
# unreachable through the sanctioned path, so a synthetic fixture would only have re-pinned the
# shape the bug already had.
# ---------------------------------------------------------------------------------------------

R3_AXES = ("earnings", "multiple")


def _r3_legs(**over) -> dict[str, dict]:
    """Three legs shaped as an R3 template writes them — `eps`, never `revenue`/`margin`."""
    out = {leg: {"eps": 16.0, "multiple": 24.0,
                 "eps_derivation": "stated", "multiple_derivation": "stated"} for leg in LEGS}
    for leg, patch in over.items():
        out[leg].update(patch)
    return out


def test_r3_axes_are_not_asked_for_revenue_or_margin():
    """The refusal that made R3 uncreatable: nine problems, six of them for axes it never reads."""
    ancs = propose_anchors(_doc("GOOGL"))
    trio = validate_legs(_r3_legs(), ancs)                       # today's default — the R1 shape
    assert [p for p in trio if ".revenue" in p or ".margin" in p], (
        "guard is inert: the R1 default must still demand revenue/margin, or this test proves "
        "nothing about the recipe-aware path below")
    r3 = validate_legs(_r3_legs(), ancs, axes=R3_AXES, basis="P/E")
    assert not [p for p in r3 if ".revenue" in p or ".margin" in p], r3


def test_r3_multiple_is_not_anchored_to_the_ev_ebitda_band():
    """A P/E turn compared against an own-history EV/EBITDA median is a category error.

    Dropping that anchor does not weaken the check — it makes it STRICTER: the leg becomes
    unanchored, so it must state its `multiple_derivation` or be refused.
    """
    ancs = propose_anchors(_doc("GOOGL"))
    mult = [a for a in ancs if a.axis == "multiple"]
    assert mult and mult[0].basis and "EBITDA" in mult[0].basis.upper(), (
        f"GOOGL's committed multiple anchor is no longer an EV/EBITDA statistic ({mult}) — this "
        "test's premise moved, not the code")
    far = _r3_legs(base={"multiple": 24.5, "multiple_derivation": ""})
    assert not [p for p in validate_legs(far, ancs, axes=R3_AXES, basis="P/E")
                if "deviates from its anchor" in p]
    assert [p for p in validate_legs(far, ancs, axes=R3_AXES, basis="P/E")
            if p.startswith("base.multiple has no anchor")], "unanchored must still demand a why"
    # ...and the SAME anchor still binds a record that IS on its basis
    assert [p for p in validate_legs(_legs(base={"multiple": 99.0}), ancs, basis=mult[0].basis)
            if p.startswith("base.multiple") and "deviates" in p]


def test_r3_earnings_axis_reads_the_eps_leg_field():
    """`earnings` states itself in `eps_derivation`, beside the `eps` it explains.

    The sibling defect: `validate_legs` reading the leg field while `assumptions_from` read the
    axis name would validate the analyst's words and then drop them out of the record.
    """
    from vinci.dossier.propose import assumptions_from

    doc = _doc("GOOGL")
    bare = validate_legs(_r3_legs(bear={"eps": None}), propose_anchors(doc),
                         axes=R3_AXES, basis="P/E")
    assert [p for p in bare if p.startswith("bear.eps is required")], bare
    got = assumptions_from(doc, _r3_legs(base={"eps_derivation": "FY27 normalized, memo §4"}),
                           axes=R3_AXES, basis="P/E")
    assert sorted(got) == ["earnings", "multiple"], sorted(got)
    assert "FY27 normalized, memo §4" in got["earnings"]["method"], got["earnings"]["method"]


def test_committed_r3_record_is_shaped_by_its_recipe():
    """END-TO-END on the committed record: no null axis its arithmetic never reads.

    A `"revenue": null` on a P/E underwrite asserts someone looked for a revenue and found none.
    Absent is the true statement, and `LEG_FIELDS_DROPPED_WHEN_NONE` is how the record says it.
    """
    rec = json.loads((ROOT / "scenarios" / "GOOGL.json").read_text())
    assert rec["recipe_id"] == "R3_forward_pe" and rec["multiple_basis"] == "P/E"
    assert sorted(rec["assumptions"]) == ["earnings", "multiple"]
    for leg, cell in rec["scenarios"].items():
        assert "revenue" not in cell and "margin" not in cell, (leg, sorted(cell))
        assert isinstance(cell["eps"], float) and isinstance(cell["multiple"], float)
    for axis in ("earnings", "multiple"):
        # PHRASING-INDEPENDENT: the method is composed from analyst prose that will be reworded on
        # any re-underwrite. What must hold is that each leg contributed its own words.
        method = rec["assumptions"][axis]["method"]
        assert all(f"{leg}:" in method for leg in LEGS), (axis, method)


def test_r1_records_keep_their_axes_when_the_drop_list_grew():
    """`revenue`/`margin` drop ONLY when None, and on an R1 record they are never None.

    The mechanism exists to leave the committed corpus byte-identical; this is that claim, asserted
    against the corpus rather than trusted.
    """
    import vinci.scenarios as sc

    assert {"revenue", "margin"} <= set(sc.LEG_FIELDS_DROPPED_WHEN_NONE)
    seen = 0
    for path in sorted((ROOT / "scenarios").glob("*.json")):
        rec = json.loads(path.read_text())
        if rec.get("recipe_id") == "R3_forward_pe" or "scenarios" not in rec:
            continue
        for leg, cell in rec["scenarios"].items():
            assert cell.get("revenue") is not None, (path.name, leg)
            assert cell.get("margin") is not None, (path.name, leg)
            seen += 1
    assert seen >= 3, f"corpus check ran over {seen} legs — it is not exercising anything"


def test_an_anchor_is_dropped_only_when_it_names_a_different_multiple():
    """The basis filter, both directions — it must REFUSE a mismatch and KEEP everything else.

    A filter that drops too eagerly is worse than none: it would silently un-anchor a legitimate
    R1 multiple, turning a real deviation check into a derivation sentence nobody re-reads. So
    uncertainty leaves the check ON — an unknown basis on either side keeps the anchor, and a
    qualified spelling (`EV/EBITDA (NTM)`) still anchors its plain form.
    """
    from vinci.dossier.propose import _anchors_on_basis

    def anc(basis):
        return Anchor("multiple", "base", 17.4, "x", 17.4, "median", "lbl", "src", "2026-08",
                      basis=basis)

    kept = lambda rec, a: bool(_anchors_on_basis([anc(a)], rec))  # noqa: E731
    # NEGATIVE — the one case the filter exists for
    assert not kept("P/E", "EV/EBITDA")
    assert not kept("EV/EBITDA", "P/E")
    # POSITIVE — every other combination survives
    assert kept("EV/EBITDA", "EV/EBITDA")
    assert kept("EV/EBITDA", "EV/EBITDA (NTM)")
    assert kept("EV/EBITDA (NTM)", "EV/EBITDA")
    assert kept("P/E", "P/E")
    assert kept("p/e", " P/E ")                      # case and padding are not a basis difference
    assert kept("P/E", None), "an anchor with no stated basis is not evidence of a mismatch"
    assert kept(None, "EV/EBITDA"), "a record with no stated basis keeps every anchor it had"
