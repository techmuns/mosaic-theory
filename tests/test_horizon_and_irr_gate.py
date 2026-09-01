"""The second test: nominal 2:1 **AND** a base-case IRR floor **AND** a stated horizon.

WHY. The bar was one test on a NOMINAL asymmetry, and it did not ask when the thesis realises. R1
never read `years_to_terminal` and never refused it, so a record could carry `years_to_terminal:
4.0` beside `result.per_scenario.base.years: null` — self-contradictory on disk. Nothing computed a
return, so an 18-month double and a five-year double graded identically.

BOTH TESTS, AND IRR NEVER REPLACES ASYMMETRY. A 40% IRR on a 1.2:1 spread is a levered bet, not a
cheap one, and the bar exists to refuse exactly that — so `gate` is the CONJUNCTION and `pass_fail`
keeps its old meaning (the ratio test alone), unchanged, so no committed record is reclassified by
a field changing under it.
"""
from __future__ import annotations

import json
import pathlib

import pytest

import vinci.scenarios as sc

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: SMPL's adjudicated 2026-08-05 underwrite — bear 1,200/13.0%/5.5x, base 1,340/15.5%/9.0x,
#: bull 1,410/17.0%/12.0x, 18 months, spot 11.32. A FROZEN fixture: these are value pins and the
#: TEST-LAYER RULE keeps value pins off the re-drawn artifact.
_LEGS = {"bear": (1200.0, 0.130, 5.5), "base": (1340.0, 0.155, 9.0), "bull": (1410.0, 0.170, 12.0)}


def _smpl_at(spot: float = 11.32, years: float | None = 1.5) -> sc.ScenarioRecord:
    r = sc.read_record("SMPL", root=ROOT)
    return r.model_copy(update={
        "spot": spot,
        "scenarios": {k: r.scenarios[k].model_copy(update={
            "revenue": v[0], "margin": v[1], "multiple": v[2],
            "years_to_terminal": years if k == "base" else None})
            for k, v in _LEGS.items()}})


def test_the_adjudicated_smpl_underwrite_reproduces_end_to_end() -> None:
    """THE ACCEPTANCE CASE. Three numbers were settled by hand across three independent
    underwrites — 2.10:1, IRR 44.4%, entry limit $11.46 — and the engine must produce all three
    from the legs alone. Reproducing an independently-derived number is the only evidence that the
    arithmetic here is the arithmetic that was adjudicated."""
    res = sc.run_recipe(_smpl_at()).result
    assert res.ratio == pytest.approx(2.1030, abs=5e-4), res.ratio
    assert res.pass_fail == "PASS"
    assert res.irr == pytest.approx(0.4440, abs=5e-4), res.irr
    assert res.irr_pass_fail == "PASS"
    assert res.gate == "PASS"
    assert res.horizon_years == 1.5
    # the price at which the ratio decays to the bar — the operator's stated $11.46
    b = res.per_scenario["base"].value_per_share
    be = res.per_scenario["bear"].value_per_share
    assert (b + res.bar * be) / (1 + res.bar) == pytest.approx(11.46, abs=5e-3)


def test_r1_now_stores_the_horizon_it_was_given() -> None:
    """THE SELF-CONTRADICTION, closed. `years_to_terminal` sat on the SHARED `ScenarioInput` and R1
    read it nowhere, so a stated horizon and a null `years` could coexist in one record."""
    out = sc.run_recipe(_smpl_at())
    assert out.result.per_scenario["base"].years == 1.5, "R1 still does not carry the horizon"


def test_the_irr_is_taken_on_the_nominal_value_never_the_discounted_one() -> None:
    """THE DOUBLE-DISCOUNT DEFECT, pinned on a real R2 record.

    R2's `value_per_share` is ALREADY a PV discounted at `HURDLE`. Feeding it to the IRR would
    report a return net of the very charge the IRR exists to measure against — and it would be
    invisible, because a smaller-but-plausible rate looks like a result rather than a bug. The
    pin is a COMPARISON, not a constant: the computed IRR must match the one taken on
    `value_terminal` and must NOT match the one taken on the PV."""
    rec = sc.read_record("AORT", root=ROOT)
    res = sc.run_recipe(rec).result
    base = res.per_scenario["base"]
    assert base.value_terminal is not None and base.years, "AORT is no longer an R2 fixture"
    nominal, _ = sc.annualised_irr(base.value_terminal, rec.spot, base.years)
    discounted, _ = sc.annualised_irr(base.value_per_share, rec.spot, base.years)
    assert nominal is not None and discounted is not None
    assert res.irr == pytest.approx(nominal), "the IRR is not on the terminal (nominal) value"
    assert res.irr != pytest.approx(discounted), (
        "the IRR equals the rate taken on the PV — it is discounting twice, reporting a return "
        "already net of the 15% hurdle")


def test_a_negative_base_has_no_rate_and_says_so_rather_than_returning_zero() -> None:
    """FAIL LOUD. A fractional power of a negative number is not real, and a negative base IS a
    genuine state on this fleet. Never 0.0, never a complex number — a stated reason."""
    irr, why = sc.annualised_irr(-3.0, 10.0, 2.0)
    assert irr is None and "not positive" in why, why
    irr, why = sc.annualised_irr(20.0, 10.0, 0.0)
    assert irr is None and "horizon" in why, why


@pytest.mark.parametrize(
    ("ratio_pf", "irr_ok", "want"),
    [("PASS", True, "PASS"), ("PASS", False, "FAIL"), ("FAIL", True, "FAIL"),
     ("FAIL", False, "FAIL"), ("UNDEFINED", True, "UNDEFINED"),
     # THE MIRROR CASE (2026-08-06). A determinate IRR FAIL beside an unknown ratio is still a
     # determinate FAIL — the same truth as the asymmetry side, and the row that would be missing
     # if the rule had been written to special-case asymmetry alone. 0 committed records sit here,
     # so this row is the only thing that exercises it.
     ("UNDEFINED", False, "FAIL")])
def test_the_gate_is_the_conjunction_and_undefined_is_contagious(
        ratio_pf: str, irr_ok: bool, want: str) -> None:
    """BOTH TESTS. The `PASS/False -> FAIL` row is the one that matters: it is the case where a
    high IRR would otherwise buy a pass on a thin spread, which is what the bar exists to refuse.
    UNDEFINED propagates because a gate reading PASS while half of it could not be computed is
    worse than one that admits it does not know."""
    # a 30% IRR clears the floor; 2% does not — chosen either side, not near it
    years, spot = 1.0, 10.0
    base = spot * (1.30 if irr_ok else 1.02)
    rec = _smpl_at()
    res = sc.Result(per_scenario={"base": sc.ScenarioOutcome(
        value_per_share=base, op_income=0.0, ebitda=0.0, ev=0.0, equity=0.0)},
        pass_fail=ratio_pf)  # type: ignore[arg-type]
    rec = rec.model_copy(update={"spot": spot, "scenarios": {
        **rec.scenarios,
        "base": rec.scenarios["base"].model_copy(update={"years_to_terminal": years})}})
    assert sc._with_irr_gate(res, rec).gate == want


def test_a_failing_asymmetry_decides_the_gate_without_the_irr() -> None:
    """THE SEPARATION (2026-08-06). BOTH DIRECTIONS, because only one of them changed.

    * **Failing asymmetry + no horizon → FAIL.** The gate is an AND and an AND with a determinate
      False is False. Contagion here was reporting DECIDED records as pending work: WERN's reward
      is −10.33 (its base case sits BELOW spot) and its ratio −0.35 against a 2.0 bar, yet it read
      UNDEFINED for want of a horizon that could not have rescued it — stating one adds an IRR
      negative for the same reason. It sat in queues as an underwrite awaiting a field.
    * **PASSING asymmetry + no horizon → still UNDEFINED.** That is where the answer genuinely IS
      unknown, and it is the half that must NOT move. EPAM is the live instance: its committed
      record passes asymmetry at 6.34, so its gate is correctly UNDEFINED, not FAIL.

    COMPLETENESS IS NOT THE GATE'S ANSWER, and must survive the separation: the missing horizon
    stays flagged through `irr_undefined` and `irr_pass_fail`, which is what the page renders."""
    failing = _smpl_at(years=None).model_copy(update={"spot": 1_000.0})   # base far below spot
    res = sc.run_recipe(failing).result
    assert res.pass_fail == "FAIL" and res.irr_pass_fail == "UNDEFINED"
    assert res.gate == "FAIL", (
        "a record whose asymmetry already failed reads UNDEFINED — a decided record presented as "
        "pending work, which is what this separation exists to stop")
    # …and the deficiency is STILL flagged, just not as the gate's answer
    assert res.irr is None and res.irr_undefined and "realisation date" in res.irr_undefined, (
        "the missing horizon stopped being reported — the gate was short-circuited rather than "
        "separated from completeness")

    # the half that must NOT move
    passing = sc.run_recipe(_smpl_at(years=None)).result
    assert passing.pass_fail == "PASS" and passing.gate == "UNDEFINED", (
        "a PASSING asymmetry with no horizon must stay UNDEFINED — that is genuine ignorance "
        "about the decision, not a completeness gap")


def test_a_record_with_no_horizon_still_computes_and_says_why_it_cannot_be_graded() -> None:
    """THE PLACEMENT DECISION, pinned. The refusal is at the WRITE boundary, NOT in `run_recipe`.

    Refusing on recomputation would break
    `test_every_committed_record_result_matches_its_own_facts` — the invariant that re-runs the
    recipe over every committed record to prove its stored result still matches its own facts,
    shipped after PR #189 where two records had facts amended under an unchanged result and nothing
    was red. Four committed R1 records carry no horizon, so refusing there takes that guard dark on
    4 of 7 records: it would stop detecting silent divergence exactly where divergence has already
    happened once. So recomputation stays possible, and the record says UNDEFINED WITH ITS REASON
    rather than passing quietly."""
    res = sc.run_recipe(_smpl_at(years=None)).result
    assert res.ratio is not None and res.pass_fail == "PASS", "the ratio must still compute"
    assert res.irr is None and res.irr_pass_fail == "UNDEFINED"
    assert res.irr_undefined and "realisation date" in res.irr_undefined
    assert res.gate == "UNDEFINED", "a record that cannot be graded must not read PASS"


def test_the_write_paths_refuse_a_missing_or_nonsensical_horizon() -> None:
    """NO GRANDFATHERING, where it actually binds: nothing NEW lands without a realisation date."""
    assert sc.horizon_problems(_smpl_at()) == []
    absent = sc.horizon_problems(_smpl_at(years=None))
    assert len(absent) == 1 and "years_to_terminal is required" in absent[0]
    assert "never defaulted" in absent[0].lower() or "not defaulted" in absent[0].lower()
    assert sc.horizon_problems(_smpl_at(years=0.0)), (
        "a zero horizon must be refused, not divided by")


def test_every_committed_record_passes_the_supersede_guard_it_will_now_face() -> None:
    """THE REFUSAL CASE THE OPERATOR ASKED FOR, measured rather than predicted.

    `scenario-supersede` now routes through `validate_legs`. Fed a record DIRECTLY it refuses all
    seven committed records on nine phantom "must state where it came from" problems each — the
    template's per-cell `{axis}_derivation` keys do not exist on a `ScenarioRecord` and cannot.
    That is a shape mismatch, not a defect found, and shipping it would have blocked every
    legitimate supersede. `record_legs_for_validation` maps the record's OWN provenance
    (`assumptions[axis].method`, `ScenarioInput.reason`) into the shape the validator reads."""
    from vinci.dossier.propose import (
        propose_anchors,
        record_legs_for_validation,
        validate_legs,
    )
    records = sc.all_records(root=ROOT)
    assert records, "no committed records"
    naive_refusals, adapted_refusals = 0, {}
    for t, r in records.items():
        doss = ROOT / "data" / "dossiers" / t / "dossier.json"
        anchors = propose_anchors(json.loads(doss.read_text())) if doss.is_file() else []
        # THE RECIPE'S AXES, exactly as `scenario-supersede` passes them. Defaulting to the R1
        # trio here would refuse GOOGL's R3 record for a revenue and a margin its arithmetic
        # never reads — the same shape mismatch this test exists to catch, reintroduced by the
        # test itself.
        axes = sc.axes_for(r.recipe_id, r.multiple_basis)
        raw = {leg: {"revenue": s.revenue, "margin": s.margin, "multiple": s.multiple,
                     "reason": s.reason} for leg, s in r.scenarios.items()}
        naive_refusals += bool(validate_legs(raw, anchors, axes=axes,
                                             basis=r.multiple_basis))
        probs = validate_legs(record_legs_for_validation(r, axes=axes), anchors,
                              axes=axes, basis=r.multiple_basis)
        if probs:
            adapted_refusals[t] = probs
    assert naive_refusals == len(records), (
        "the naive routing no longer refuses every record — if the record shape gained "
        "`{axis}_derivation` keys the adapter may be redundant; re-check before deleting it")
    assert not adapted_refusals, (
        f"the adapter refuses committed records, which would block a legitimate supersede: "
        f"{adapted_refusals}")


def test_a_record_whose_gate_never_ran_gains_no_gate_keys_on_re_serialisation() -> None:
    """THE ARCHIVE. A frozen pre-gate record re-serialised with `"gate": null` would assert WE
    GRADED THIS AND GOT NOTHING; the truth is it predates the gate. Same defect the axis-level
    version scoping was added to close, one level further down."""
    archive = sorted((ROOT / "scenarios" / "archive").glob("*.json"))
    if not archive:
        pytest.skip("no archived records")
    for p in archive:
        rec = sc.ScenarioRecord.model_validate_json(p.read_text())
        if (rec.result.gate if rec.result else None) is not None:
            continue                      # a post-gate archive legitimately carries them
        out = sc._version_scoped(rec).get("result") or {}
        leaked = [f for f in sc.GATE_FIELDS if f in out]
        assert not leaked, f"{p.name} gained {leaked} — it predates the gate and cannot claim one"


def test_supersede_refuses_a_result_its_own_legs_do_not_produce() -> None:
    """`scenario-supersede` recomputes the incoming `result` and REFUSES a disagreement.

    `scenario-create` runs `validate_legs -> run_recipe -> write_record`; supersede ran the
    validator and then wrote whatever `result` the payload carried. A hand-typed ratio that
    disagrees with the legs above it is the machine concluding from a number nobody derived, and
    the BUY-AVOID spread accumulates from exactly these figures.

    DRIVEN OFF A COMMITTED RECORD, mutated one field at a time — a fixture built to the shape the
    check wants would prove only that the comparator compares.
    """
    import vinci.scenarios as sc
    from vinci.cli import _RESULT_COMPARED, _result_mismatch

    smpl = (ROOT / "scenarios" / "SMPL.json").read_text()
    rec = sc.ScenarioRecord.model_validate(json.loads(smpl))
    computed = sc.run_recipe(rec.model_copy(deep=True))

    # the committed record agrees with its own legs — the guard must not refuse what exists
    assert _result_mismatch(rec.result, computed.result) is None

    # a hand-typed ratio is caught, and the message names BOTH numbers
    tampered = rec.model_copy(deep=True)
    tampered.result.ratio = (rec.result.ratio or 0) + 0.5
    why = _result_mismatch(tampered.result, computed.result)
    assert why and "ratio" in why and "legs give" in why, why

    # so is a flipped verdict field, which carries no float tolerance at all
    flipped = rec.model_copy(deep=True)
    flipped.result.pass_fail = "FAIL" if rec.result.pass_fail == "PASS" else "PASS"
    assert "pass_fail" in (_result_mismatch(flipped.result, computed.result) or "")

    # ...but repr-level noise is NOT a disagreement — it would refuse every JSON round-trip
    noisy = rec.model_copy(deep=True)
    noisy.result.ratio = (rec.result.ratio or 0) + 1e-9
    assert _result_mismatch(noisy.result, computed.result) is None

    assert "gate" in _RESULT_COMPARED and "irr" in _RESULT_COMPARED, (
        "the compared set must cover the gate fields, or a record could supersede with a verdict "
        "its legs do not support")


def test_every_committed_record_would_survive_the_new_supersede_check() -> None:
    """THE COST OF THE GUARD, measured rather than assumed: it refuses nothing that exists.

    A guard that would block legitimate supersedes of records already on disk is a guard that
    stops the fund working. Asserted over the whole corpus, not a sample.
    """
    import vinci.scenarios as sc
    from vinci.cli import _result_mismatch

    seen = 0
    for f in sorted((ROOT / "scenarios").glob("*.json")):
        if f.name.startswith("_"):
            continue
        rec = sc.ScenarioRecord.model_validate(json.loads(f.read_text()))
        again = sc.run_recipe(rec.model_copy(deep=True)).result
        assert _result_mismatch(rec.result, again) is None, f.name
        seen += 1
    assert seen >= 9, f"corpus check walked {seen} records — it is not exercising anything"


def test_supersede_derives_an_unstated_result_instead_of_refusing_it() -> None:
    """A payload that STATES no result is DERIVED, not refused (review fix, 2026-09-01).

    `ScenarioRecord.result` is `Field(default_factory=Result)`, NOT nullable — so a payload that
    omits `result` arrives as an all-default `Result()` and disagrees with its own legs on every
    compared field. Two things broke on that:

      * the refusal's own advice — "drop the stated result and let the recipe compute it" — was
        unfollowable: doing exactly that produced `reward: stated None, legs give 51.5145; ...`;
      * archive-and-reissue had NO working payload shape for stamping the tiered ladder, because
        `_with_irr_gate` freezes any record that carries a computed result. A stated result froze
        the ladder; an unstated one was refused. GOOGL's reissue — the sequel both PRs name — was
        unreachable either way.

    DRIVEN OFF THE COMMITTED GOOGL RECORD, mutated one field at a time.
    """
    from vinci.cli import _result_is_stated, _result_mismatch

    doc = json.loads((ROOT / "scenarios" / "GOOGL.json").read_text())

    # (a) the virgin block is NOT a stated result, however loudly it disagrees with the legs
    virgin = dict(doc)
    virgin.pop("result", None)
    rec = sc.ScenarioRecord.model_validate(virgin)
    assert _result_is_stated(rec.result) is False
    assert rec.result is not None, "the premise: it is a virgin Result(), never None"
    assert _result_mismatch(rec.result, sc.run_recipe(rec.model_copy(deep=True)).result), (
        "the mismatch report must still FIRE on the virgin block — the fix is that the caller "
        "does not consult it, not that the comparator went blind")

    # ...and an explicit empty object is the same declining posture
    empty = dict(doc)
    empty["result"] = {}
    assert _result_is_stated(sc.ScenarioRecord.model_validate(empty).result) is False

    # (b) deriving it is what makes the record stampable under the ladder — the whole point
    derived = sc.run_recipe(rec.model_copy(deep=True))
    assert derived.result.gate_regime == sc.GATE_REGIME, (
        "an unstated result must reach the engine UNCOMPUTED so the tiers stamp it; if this "
        "reddens, reissue can no longer put a record under the ladder")
    assert derived.result.asymmetry_tier is not None and derived.result.eligible is not None

    # (c) a record that DOES state a result is still compared, and still refused on disagreement
    stated = sc.ScenarioRecord.model_validate(doc)
    assert _result_is_stated(stated.result) is True
    tampered = stated.model_copy(deep=True)
    tampered.result.ratio = (stated.result.ratio or 0) + 0.5
    assert _result_is_stated(tampered.result) is True
    assert "ratio" in (_result_mismatch(
        tampered.result, sc.run_recipe(tampered.model_copy(deep=True)).result) or ""), (
        "widening 'unstated' must not have widened into 'unchecked' — a hand-typed ratio is "
        "still refused, which is the 2026-09-01 ruling")


def test_supersede_consults_the_stated_check_before_refusing() -> None:
    """THE CALL SITE, pinned — a helper-level test stays green when the caller drops it.

    `_result_is_stated` is only worth anything inside `_cmd_scenario_supersede`; guarding the
    helper alone would let a revert delete the branch and stay green.
    """
    src = (ROOT / "vinci" / "cli.py").read_text()
    supersede = src.split("def _cmd_scenario_supersede", 1)[1].split("\ndef _cmd_", 1)[0]
    assert "_result_is_stated" in supersede, (
        "supersede refuses an UNSTATED result again — the payload shape that reissues a record "
        "under the tiered ladder is unreachable, and the refusal message advises the impossible")
    assert "_result_mismatch" in supersede, (
        "supersede no longer refuses a stated disagreement — that is the 2026-09-01 ruling")
