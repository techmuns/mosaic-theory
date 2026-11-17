"""RECIPE 3a (W25, 2026-11-17) — R1's base multiple is TODAY'S; an R3 bear is bounded by consensus.

(1) R1's proposed base multiple is the band's CURRENT multiple, with the trailing median printed
    beside it; a band with no usable current proposes NOTHING and says why, never the median.
    Fold-in (STATE §5.0 row 10): an empty R3/R4 multiple's refusal cites its own recipe's reason,
    not R1's band.
(2) An R3 bear's EPS is at or below the NTM consensus EPS stamped on the record from the page, or
    the bear states a miss case whose consensus it sits below — refused at the point of decision,
    FLAGGED on an existing record.

Fixtures are the REAL committed types: SMPL's and GOOGL's pages and GOOGL's record. Where a shape is
not in the corpus (no committed page has ever carried a band without `current` — `git log
-S'"current": null' -- 'data/dossiers/*/dossier.json'` is empty), the pin derives it from the real
page by removing that one field, and says so. Values a re-assembly moves are read off the page,
never typed; the frozen 2026-08-18 SMPL page carries the value-level pin.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import warnings
from datetime import date
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier.propose import (
    LEGS,
    UNPROPOSED_REASON,
    _r1_proposal_band,
    build_template,
    legs_from_template,
    multiple_base_refusal,
    ntm_consensus_eps,
    propose_anchors,
    unproposed_reasons,
    validate_legs,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
FROZEN_SMPL = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"
R3_AXES = sc.AXES_BY_RECIPE[sc.RECIPE_R3]
R4_AXES = sc.AXES_BY_RECIPE[sc.RECIPE_R4]


def _doc(t: str) -> dict[str, Any]:
    return json.loads((DOSS / t / "dossier.json").read_text())


def _base_multiple(doc: dict[str, Any]) -> Any:
    return next((a for a in propose_anchors(doc) if (a.axis, a.leg) == ("multiple", "base")), None)


def _without_current(doc: dict[str, Any], value: Any = "drop") -> dict[str, Any]:
    """The real page with ONE field changed: the selected band's `current` removed (or set)."""
    d = copy.deepcopy(doc)
    band, _ = _r1_proposal_band(d)
    assert band is not None, "the page has no R1 band to derive the shape from"
    if value == "drop":
        band.pop("current")
    else:
        band["current"] = value
    return d


# --- (1) the base multiple is the CURRENT multiple, the median beside it ------------------------


def test_frozen_smpl_proposes_its_current_multiple_with_the_median_beside_it() -> None:
    """(+) VALUE PIN on the FROZEN page (2026-08-18, the page SMPL's record was struck against):
    R1 prices SMPL on the ex-lease band, current 6.593104x, median 17.924621x. The proposal is the
    current; the median is printed beside it in the template and travels into the record as a
    frame-level reference — never as the base leg's anchor."""
    doc = json.loads(FROZEN_SMPL.read_text())
    a = _base_multiple(doc)
    assert a is not None and a.role == "current"
    assert a.schema_value == pytest.approx(6.593104) and a.value == pytest.approx(6.5931)
    cell = build_template(doc)["scenarios"]["base"]
    assert cell["multiple"] == pytest.approx(6.593104)
    assert cell["_multiple_median_beside"].startswith("17.9246x — "), cell
    assert "not the proposal" in cell["_multiple_median_beside"]


@pytest.mark.parametrize("ticker", ["SMPL", "BRBR", "EPAM", "IT", "VRRM"])
def test_the_living_pages_propose_the_band_current_never_its_median(ticker: str) -> None:
    """(+) On the five pages where the median sat 2.4x-3.9x above today's multiple (measured at
    `4889ddba`), the proposal is the selected band's `current` — read off the page, an invariant a
    re-assembly cannot rot (TEST-LAYER rule: no value pin on a living page) — and the median is
    beside it, not in the cell."""
    doc = _doc(ticker)
    band, _ = _r1_proposal_band(doc)
    assert band is not None
    a = _base_multiple(doc)
    assert a is not None and a.schema_value == pytest.approx(float(band["current"]))
    tpl = build_template(doc) if ticker != "SMPL" else None   # living SMPL: STATE row 36 refuses
    if tpl is not None:
        cell = tpl["scenarios"]["base"]
        assert cell["multiple"] == pytest.approx(float(band["current"]))
        assert cell["_multiple_median_beside"].startswith(f"{round(float(band['median']), 4):g}x")


@pytest.mark.parametrize("current", ["drop", None, "NM", 0.0, -3.2])
def test_a_band_with_no_usable_current_proposes_nothing_and_says_why(current: Any) -> None:
    """(−) FAIL LOUD, NEVER THE MEDIAN. No committed page carries this shape, so it is derived from
    the frozen SMPL page by removing (or NM-ing) the band's `current` alone. The base multiple is
    then unproposed, the cell is EMPTY — not the median — and its reason names the missing
    current; `validate_legs` cites the same reason when the analyst leaves it empty."""
    doc = _without_current(json.loads(FROZEN_SMPL.read_text()), current)
    assert _base_multiple(doc) is None
    why = multiple_base_refusal(doc)
    assert why is not None and "no usable current" in why and "never put in its place" in why
    cell = build_template(doc)["scenarios"]["base"]
    assert cell["multiple"] is None, "the median came back as the silent fallback"
    assert cell["_multiple_why_no_anchor"] == why
    assert "_multiple_median_beside" not in cell
    probs = validate_legs(legs_from_template(build_template(doc)), propose_anchors(doc),
                          reasons=unproposed_reasons(doc=doc))
    assert [p for p in probs if p.startswith("base.multiple is required and absent")
            and "no usable current" in p], probs


def test_the_refusal_and_the_proposal_never_coexist_on_the_corpus() -> None:
    """(+) Across every committed page, exactly one of three holds: no band (no proposal, no
    refusal), a proposal, or a refusal — never both, never a band with neither. At `4889ddba`:
    22 of 26 pages propose, 0 refuse; FUBO, ORKA, TECX and VITL carry no band. An invariant, so
    a page whose band is NM later refuses here without reddening the suite."""
    for p in sorted(DOSS.glob("*/dossier.json")):
        doc = json.loads(p.read_text())
        has_band = _r1_proposal_band(doc)[0] is not None
        proposes, refuses = _base_multiple(doc) is not None, multiple_base_refusal(doc) is not None
        assert (proposes or refuses) == has_band and not (proposes and refuses), p.parent.name


def test_moving_off_the_current_to_the_median_needs_a_stated_adjustment() -> None:
    """(−/+) The deviation rule now measures from the CURRENT: a base struck at the median — the
    old proposal — with no `multiple_adjustment` is refused, and passes once it states why."""
    doc = json.loads(FROZEN_SMPL.read_text())
    ancs = propose_anchors(doc)
    band, _ = _r1_proposal_band(doc)
    assert band is not None
    legs = legs_from_template(build_template(doc))
    legs["base"]["multiple"] = float(band["median"])
    moved = [p for p in validate_legs(legs, ancs) if p.startswith("base.multiple")]
    assert moved and "deviates from its anchor 6.5931x" in moved[0], moved
    legs["base"]["multiple_adjustment"] = "re-rates to its own median over the horizon"
    assert not [p for p in validate_legs(legs, ancs) if p.startswith("base.multiple")]


def test_the_band_low_stays_unproposed() -> None:
    """(regression) The bear multiple is still never proposed — the band LOW is one close."""
    doc = json.loads(FROZEN_SMPL.read_text())
    assert ("multiple", "bear") not in {(a.axis, a.leg) for a in propose_anchors(doc)}
    cell = build_template(doc)["scenarios"]["bear"]
    assert cell["multiple"] is None
    assert cell["_multiple_why_no_anchor"] == UNPROPOSED_REASON[("multiple", "bear")]


# --- (1) fold-in: an R3/R4 refusal cites its own recipe, not R1's band (STATE row 10) ------------


def test_googl_r3_template_refusals_cite_r3_not_r1s_band() -> None:
    """(−) GOOGL's REAL R3 template, empty as proposed: its bear and bull multiples are refused
    (right) and the reason was R1's own-history band-low and p75 (wrong — a P/E is not that band).
    Pinned on the default path and on the CLI's doc-aware path."""
    doc = _doc("GOOGL")
    tpl = build_template(doc)
    assert tpl["recipe_id"] == sc.RECIPE_R3
    for reasons in (None, unproposed_reasons(axes=R3_AXES, doc=doc)):
        probs = validate_legs(legs_from_template(tpl), propose_anchors(doc), axes=R3_AXES,
                              basis=sc.BASIS_PE, reasons=reasons)
        for leg in ("bear", "bull"):
            line = next(p for p in probs if p.startswith(f"{leg}.multiple is required"))
            assert "forward P/E" in line, line
            assert UNPROPOSED_REASON[("multiple", leg)] not in line, line


def test_r4_axes_cite_r4s_reasons() -> None:
    """(−) The same text defect on R4 since #691: an empty EV/EBIT multiple cited R1's band."""
    table = unproposed_reasons(axes=R4_AXES, doc=_doc("AMZN"))
    for leg in LEGS:
        assert "EV/EBIT" in table[("multiple", leg)]
        assert table[("multiple", leg)] not in UNPROPOSED_REASON.values()


# --- (2) the R3 bear bound -----------------------------------------------------------------------


def test_googl_page_states_one_ntm_consensus_eps() -> None:
    """(+) THE SUPPLYING LAYER: `forward_consensus.pe_eps_basis.fits[].ntm_implied_eps`, one value
    across the fitted lines (the `valuation_basis` rule), with its line, source and date."""
    doc = _doc("GOOGL")
    stamp, why = ntm_consensus_eps(doc)
    assert why is None and stamp is not None
    pb = doc["forward_consensus"]["pe_eps_basis"]
    assert {round(f["ntm_implied_eps"], 6) for f in pb["fits"]} == {stamp["value"]}
    assert stamp["line"] == pb["ntm"] and stamp["as_of"] == doc["forward_consensus"]["as_of"]
    assert "ntm_implied_eps" in stamp["source_ref"]


def test_a_page_with_no_or_two_consensus_values_states_none() -> None:
    """(−) No `pe_eps_basis`, or two different implied values: no stamp, and the reason says why —
    the write never picks between two consensus figures."""
    doc = _doc("GOOGL")
    gone = copy.deepcopy(doc)
    gone["forward_consensus"].pop("pe_eps_basis")
    assert ntm_consensus_eps(gone)[0] is None and "no forward_consensus.pe_eps_basis" in str(
        ntm_consensus_eps(gone)[1])
    two = copy.deepcopy(doc)
    two["forward_consensus"]["pe_eps_basis"]["fits"][1]["ntm_implied_eps"] = 14.5
    stamp, why = ntm_consensus_eps(two)
    assert stamp is None and "2 NTM implied EPS values" in str(why)


def _googl() -> sc.ScenarioRecord:
    return sc.read_record("GOOGL", root=ROOT)


def _stamped(rec: sc.ScenarioRecord) -> sc.ScenarioRecord:
    """The record as a NEW one would be written today: the page's stamp, at the page's spot date
    (the template pre-fills `spot_as_of` from `stock_info.as_of`)."""
    doc = _doc("GOOGL")
    stamp, _ = ntm_consensus_eps(doc)
    assert stamp is not None
    return rec.model_copy(update={
        "ntm_consensus_eps": sc.ConsensusEps(**stamp),
        "spot_as_of": date.fromisoformat(doc["mechanical"]["stock_info"]["as_of"])})


def test_a_consensus_not_knowable_at_the_spot_is_refused() -> None:
    """(−) Today's stamp (≥2026-11-01) on GOOGL's own spot date (2026-08-31): a lookahead, named."""
    rec = _googl().model_copy(update={"ntm_consensus_eps": _stamped(_googl()).ntm_consensus_eps})
    assert rec.spot_as_of == date(2026, 8, 31)
    probs = sc.bear_consensus_problems(rec)
    assert any("AFTER spot_as_of 2026-08-31" in p for p in probs), probs
    assert not any("AFTER spot_as_of" in p for p in sc.bear_consensus_problems(_stamped(rec)))


@pytest.mark.parametrize("bad", [0.0, -1.0, float("inf"), float("nan")])
def test_a_miss_case_must_state_a_positive_consensus(bad: float) -> None:
    """(−) A bound every bear sits below is no miss: the model refuses it."""
    with pytest.raises(ValueError, match="not a positive EPS"):
        sc.MissCase(consensus_eps=bad, period="FY2028", source="s", reason="r")


def _bear(rec: sc.ScenarioRecord, **upd: Any) -> sc.ScenarioRecord:
    legs = dict(rec.scenarios)
    legs["bear"] = legs["bear"].model_copy(update=upd)
    return rec.model_copy(update={"scenarios": legs})


def test_googls_committed_record_is_flagged_and_still_writes(tmp_path: pathlib.Path) -> None:
    """(−, existing) GOOGL's committed record — bear EPS 15.388, no stamp (it predates the field)
    — is FLAGGED: the bound names it, and a write warns. It is NOT refused and NOT rewritten: the
    write to a scratch root succeeds and the record round-trips byte-identical."""
    rec = _googl()
    assert rec.recipe_id == sc.RECIPE_R3 and rec.scenarios["bear"].eps == pytest.approx(15.388)
    flags = sc.bear_consensus_problems(rec)
    assert len(flags) == 1 and "carries no NTM consensus EPS" in flags[0], flags
    with pytest.warns(sc.AdmissibilityWarning, match="carries no NTM consensus EPS"):
        path = sc.write_record(rec, root=tmp_path)
    assert path.read_text() == (ROOT / "scenarios" / "GOOGL.json").read_text()


def test_the_same_legs_as_a_new_record_are_refused() -> None:
    """(−, new) The same legs, stamped with GOOGL's page consensus as a create or supersede would
    stamp it: 15.388 sits above it with no miss case — refused, naming both numbers."""
    rec = _stamped(_googl())
    assert rec.ntm_consensus_eps is not None
    assert rec.scenarios["bear"].eps > rec.ntm_consensus_eps.value
    probs = sc.bear_consensus_problems(rec)
    assert len(probs) == 1 and "is ABOVE the NTM consensus EPS" in probs[0], probs
    assert "15.388" in probs[0] and f"{rec.ntm_consensus_eps.value:g}" in probs[0]


def test_a_bear_at_or_below_consensus_or_with_a_real_miss_passes() -> None:
    """(+) At the stamp, below it, or above it with a miss case it actually misses: no problem. A
    miss case the bear does not miss is refused."""
    rec = _stamped(_googl())
    assert rec.ntm_consensus_eps is not None
    v = rec.ntm_consensus_eps.value
    assert sc.bear_consensus_problems(_bear(rec, eps=v)) == []
    assert sc.bear_consensus_problems(_bear(rec, eps=v - 1.0)) == []
    miss = {"period": "FY2028", "source": "forward_consensus.spreads EPS Normalized FY 2028",
            "reason": "TEST value"}
    above = _bear(rec, miss_case=sc.MissCase(consensus_eps=18.12, **miss))
    assert sc.bear_consensus_problems(above) == []
    short = _bear(rec, miss_case=sc.MissCase(consensus_eps=15.0, **miss))
    assert "is not below it" in sc.bear_consensus_problems(short)[0]


def test_a_miss_case_off_the_r3_bear_is_refused() -> None:
    """(−) Read on one leg of one recipe: carried anywhere else it bounds nothing."""
    rec = _stamped(_googl())
    legs = dict(rec.scenarios)
    legs["base"] = legs["base"].model_copy(update={"miss_case": sc.MissCase(
        consensus_eps=18.0, period="FY2028", source="s", reason="r")})
    probs = sc.bear_consensus_problems(rec.model_copy(update={"scenarios": legs}))
    assert any(p.startswith("base.miss_case is read only on an R3 bear") for p in probs), probs


def test_no_other_committed_record_is_bounded() -> None:
    """(+) R1 and R2 records read no EPS: the bound returns nothing on the six non-R3 records."""
    recs = sc.all_records(root=ROOT)
    assert len(recs) == 7
    for t, rec in recs.items():
        if rec.recipe_id != sc.RECIPE_R3:
            assert sc.bear_consensus_problems(rec) == [], t


def _stage_googl(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    (tmp_path / "data" / "dossiers" / "GOOGL").mkdir(parents=True)
    (tmp_path / "data" / "dossiers" / "GOOGL" / "dossier.json").write_text(
        (DOSS / "GOOGL" / "dossier.json").read_text())
    (tmp_path / "scenarios").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path / "tpl.json"


def test_create_through_the_cli_refuses_the_committed_bear_and_stamps_the_page(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(−/+) END TO END: GOOGL's template filled with its committed legs is REFUSED at create on
    the bound, writing nothing; with the bear EPS at the page's consensus it writes, and the
    record carries the stamp from the page."""
    from vinci.cli import _cmd_scenario_create, _cmd_scenario_propose

    out = _stage_googl(tmp_path, monkeypatch)
    committed = json.loads((ROOT / "scenarios" / "GOOGL.json").read_text())
    assert _cmd_scenario_propose(argparse.Namespace(ticker="GOOGL", out=str(out))) == 0
    tpl = json.loads(out.read_text())
    for leg in LEGS:
        src = committed["scenarios"][leg]
        tpl["scenarios"][leg].update(eps=src["eps"], multiple=src["multiple"],
                                     reason=src["reason"], eps_derivation="stated",
                                     multiple_derivation="stated")
    base = committed["scenarios"]["base"]
    tpl["scenarios"]["base"].update(years_to_terminal=base["years_to_terminal"],
                                    leg_fy=base["leg_fy"])
    tpl["scenarios"]["bear"]["bear_basis"] = committed["scenarios"]["bear"]["bear_basis"]
    tpl.update(entry_basis=f"FY{base['leg_fy']}", underwrite_date=tpl["spot_as_of"],
               analyst="test")
    out.write_text(json.dumps(tpl))
    capsys.readouterr()
    assert _cmd_scenario_create(argparse.Namespace(ticker="GOOGL", from_file=str(out))) == 1
    said = capsys.readouterr().out
    assert "is ABOVE the NTM consensus EPS" in said, said
    assert not list((tmp_path / "scenarios").glob("GOOGL.json")), "a refusal wrote a record"

    stamp, _ = ntm_consensus_eps(_doc("GOOGL"))
    assert stamp is not None
    tpl["scenarios"]["bear"]["eps"] = stamp["value"]
    out.write_text(json.dumps(tpl))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rc = _cmd_scenario_create(argparse.Namespace(ticker="GOOGL", from_file=str(out)))
    assert rc == 0, capsys.readouterr().out
    rec = json.loads((tmp_path / "scenarios" / "GOOGL.json").read_text())
    assert rec["ntm_consensus_eps"] == stamp


def test_a_stamp_on_a_non_r3_record_is_refused() -> None:
    """(−, review round 1) The stamp bounds only an R3 bear, as `miss_case` does: an R1 or R2
    record carrying one (a payload copied from an R3 record) is refused, not written carrying a
    bound no rule reads. SMPL's committed R1 record, with GOOGL's page stamp put on it."""
    rec = sc.read_record("SMPL", root=ROOT)
    assert rec.recipe_id != sc.RECIPE_R3
    stamp, _ = ntm_consensus_eps(_doc("GOOGL"))
    assert stamp is not None
    probs = sc.bear_consensus_problems(
        rec.model_copy(update={"ntm_consensus_eps": sc.ConsensusEps(**stamp)}))
    assert any(p.startswith("ntm_consensus_eps is read only on an R3 record") for p in probs), probs
