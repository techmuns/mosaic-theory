"""RECIPE 3b (W25, 2026-11-17) — one time basis, the horizon owed by a call of record, the EPS line.

(1) A new or superseded R2 record strikes its ratio on NOMINAL `value_terminal`, under a NEW formula
    version (`R2_NOMINAL_RATIO_LINE`); a record stamped with today's chain computes as it did.
(2) A missing horizon refuses at `scenario-create` / `scenario-supersede` only on a `confirmed` or
    `overridden` record (operator 2026-11-16: "yes, exempt watch"); `log-verdict`'s refusal is
    #1004 item 5's, pinned in `tests/test_ledger_safeguards.py` against a temp store.
(3) Every R3 leg states its `eps_line`; the bear bound compares like with like (operator
    2026-11-17: "Yes, add the field").

Built from the REAL committed types — NCNO's, IT's, WERN's and GOOGL's records and pages — in a temp
directory wherever a command writes; no committed record and no ledger is written.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import warnings
from datetime import date
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier import terminal_margin as tm
from vinci.dossier.propose import ntm_consensus_eps

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _rec(t: str) -> sc.ScenarioRecord:
    return sc.read_record(t, root=ROOT)


def _run(rec: sc.ScenarioRecord) -> sc.ScenarioRecord:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return sc.run_recipe(rec.model_copy(deep=True))


# --- (1) R2 on nominal values --------------------------------------------------------------------


def test_ncno_recomputes_byte_identical_under_its_own_stamp(tmp_path: pathlib.Path) -> None:
    """(+) NCNO — the one live R2 record — carries today's chain, so it keeps its PV ratio: the
    recompute equals the committed result and the write is byte-identical."""
    rec = _rec("NCNO")
    assert rec.recipe_formula == list(tm.formula_for(rec.multiple_basis))
    again = _run(rec)
    assert again.result == rec.result and again.recipe_formula == rec.recipe_formula
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        path = sc.write_record(again, root=tmp_path)
    assert path.read_text() == (ROOT / "scenarios" / "NCNO.json").read_text()


def test_the_same_legs_under_the_new_version_strike_the_ratio_on_value_terminal() -> None:
    """(−) NCNO's legs with the stamp cleared — a first compute, as a supersede now makes it — are
    struck NOMINAL: the ratio is (base value_T − spot) ÷ (spot − bear value_T), it moves off the
    PV ratio, the ceiling follows it, and the PV stays on every leg as `value_per_share`."""
    old = _rec("NCNO")
    new = _run(old.model_copy(update={"recipe_formula": []}))
    assert new.recipe_formula == list(sc.r2_formula(old.multiple_basis, nominal=True))
    assert new.recipe_formula[-1] == sc.R2_NOMINAL_RATIO_LINE
    per = new.result.per_scenario
    b, r = per["base"], per["bear"]
    assert b.value_terminal is not None and r.value_terminal is not None
    want = (b.value_terminal - old.spot) / (old.spot - r.value_terminal)
    assert new.result.ratio == pytest.approx(want)
    assert old.result.ratio is not None and new.result.ratio is not None
    assert new.result.ratio != pytest.approx(old.result.ratio), "the ratio did not move"
    for leg in ("bear", "base", "bull"):                  # the PV, recorded, not the ratio's input
        assert per[leg].value_per_share == old.result.per_scenario[leg].value_per_share
    assert new.result.ceiling2to1 == pytest.approx(
        (b.value_terminal + new.result.bar * r.value_terminal) / (1 + new.result.bar))
    assert new.result.irr == old.result.irr               # the IRR was nominal already


def test_a_misstated_r2_stamp_is_still_refused() -> None:
    """(regression) Neither chain: refused, never silently restamped."""
    bad = _rec("NCNO").model_copy(update={"recipe_formula": ["PV = something else"]})
    with pytest.raises(ValueError, match="does not match"):
        _run(bad)


# --- staging a temp root for a dry-run supersede -------------------------------------------------


def _stage(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, t: str,
           payload: dict[str, Any]) -> argparse.Namespace:
    (tmp_path / "scenarios").mkdir()
    shutil.copy(ROOT / "scenarios" / f"{t}.json", tmp_path / "scenarios" / f"{t}.json")
    doss = ROOT / "data" / "dossiers" / t
    if doss.is_dir():
        shutil.copytree(doss, tmp_path / "data" / "dossiers" / t)
    p = tmp_path / "payload.json"
    p.write_text(json.dumps(payload))
    monkeypatch.chdir(tmp_path)
    return argparse.Namespace(ticker=t, payload=str(p), dry_run=True)


def _supersede(args: argparse.Namespace, capsys: pytest.CaptureFixture[str]) -> str:
    from vinci.cli import _cmd_scenario_supersede

    capsys.readouterr()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _cmd_scenario_supersede(args)
    return capsys.readouterr().out


def test_a_superseded_r2_payload_is_struck_nominal(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(−) A supersede payload copied from NCNO's live record carries today's stamp; the reissue
    is struck nominal, and the command says so before anything else it decides."""
    payload = json.loads((ROOT / "scenarios" / "NCNO.json").read_text())
    out = _supersede(_stage(tmp_path, monkeypatch, "NCNO", payload), capsys)
    assert "the reissue is struck NOMINAL" in out and "drop it" in out, out
    assert (tmp_path / "scenarios" / "NCNO.json").read_text() == (
        ROOT / "scenarios" / "NCNO.json").read_text(), "a dry run wrote"


# --- (2) the horizon, owed by a call of record ----------------------------------------------------

HORIZON_LINE = "base.years_to_terminal is required on a"


def test_a_confirmed_copy_of_it_without_a_horizon_is_refused(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(−) IT's real record, its status set to `confirmed` in a TEMP copy, no horizon: refused,
    naming the field. `scenarios/IT.json` is never touched."""
    payload = json.loads((ROOT / "scenarios" / "IT.json").read_text())
    assert payload["scenarios"]["base"].get("years_to_terminal") is None
    payload["verdict"]["status"] = "confirmed"
    out = _supersede(_stage(tmp_path, monkeypatch, "IT", payload), capsys)
    assert f"{HORIZON_LINE} confirmed record" in out, out


def test_its_watch_as_it_stands_is_not_refused_for_a_missing_horizon(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(+) THE EXEMPTION: IT's committed record (`watch`, operator 2026-11-16 option (a)) and no
    horizon is not refused for one. Other supersede guards may still speak; this one does not."""
    payload = json.loads((ROOT / "scenarios" / "IT.json").read_text())
    assert payload["verdict"]["status"] == "watch"
    out = _supersede(_stage(tmp_path, monkeypatch, "IT", payload), capsys)
    assert HORIZON_LINE not in out and "years_to_terminal is required" not in out, out


@pytest.mark.parametrize("status", ["watch", "passed", "pending_analyst"])
def test_no_position_owes_no_horizon(status: str) -> None:
    """(+) The three statuses that hold no position owe none; the two calls of record do."""
    rec = _rec("IT")
    held = rec.model_copy(update={"verdict": rec.verdict.model_copy(update={"status": status})})
    assert sc.horizon_problems(held) == []
    for call in sorted(sc.HORIZON_OWED_BY):
        c = rec.model_copy(update={"verdict": rec.verdict.model_copy(update={"status": call})})
        assert sc.horizon_problems(c), call


@pytest.mark.parametrize("t", ["IT", "WERN"])
def test_it_and_wern_load_run_and_write_byte_identical(t: str, tmp_path: pathlib.Path) -> None:
    """(+) The two records without a horizon load, run and write as they did; the committed page
    prints the UNDEFINED line rather than omitting it."""
    rec = _rec(t)
    assert rec.scenarios["base"].years_to_terminal is None
    again = _run(rec)
    assert again.result == rec.result
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        path = sc.write_record(again, root=tmp_path)
    assert path.read_text() == (ROOT / "scenarios" / f"{t}.json").read_text()
    assert rec.result.irr is None and rec.result.irr_undefined
    page = ROOT / "data" / "dossiers" / t / "dossier.md"
    if page.is_file():
        assert "**Base IRR** UNDEFINED" in page.read_text()


# --- (3) the EPS line ----------------------------------------------------------------------------


def _googl_new(line: str | None, *, stamp_line: str | None = None,
               miss: dict[str, Any] | None = None) -> sc.ScenarioRecord:
    """GOOGL's committed legs as a NEW record: today's page stamp at the page's spot date, every leg
    on ``line``; ``stamp_line`` overrides the stamp's line (a real stamp, one field changed)."""
    doc = json.loads((ROOT / "data" / "dossiers" / "GOOGL" / "dossier.json").read_text())
    stamp, _ = ntm_consensus_eps(doc)
    assert stamp is not None
    if stamp_line is not None:
        stamp = {**stamp, "line": stamp_line}
    rec = _rec("GOOGL")
    legs = {k: v.model_copy(update={"eps_line": line}) for k, v in rec.scenarios.items()}
    if miss is not None:
        legs["bear"] = legs["bear"].model_copy(update={"miss_case": sc.MissCase(**miss)})
    return rec.model_copy(update={
        "ntm_consensus_eps": sc.ConsensusEps(**stamp), "scenarios": legs,
        "spot_as_of": date.fromisoformat(doc["mechanical"]["stock_info"]["as_of"])})


def _miss(line: str, eps: float = 18.12) -> dict[str, Any]:
    return {"consensus_eps": eps, "line": line, "period": "FY2028",
            "source": "TEST value — a FY2028 consensus on this line", "reason": "TEST value"}


def test_googls_stamp_is_on_the_gaap_line_and_its_legs_are_normalized() -> None:
    """The real observed shape: the page's NTM P/E is struck on GAAP EPS; the committed legs read
    'Normalized EPS $15.388' — which no code parses; the pins below state the line as a field."""
    doc = json.loads((ROOT / "data" / "dossiers" / "GOOGL" / "dossier.json").read_text())
    assert doc["forward_consensus"]["pe_eps_basis"]["ntm"] == "gaap"
    assert "Normalized EPS" in _rec("GOOGL").scenarios["bear"].reason


def test_a_googl_shaped_create_on_unlike_lines_is_refused_naming_both() -> None:
    """(−) Normalized legs against a GAAP stamp, no miss case: refused, naming both lines — and
    even a bear BELOW the stamp is, since the two numbers are not one quantity."""
    probs = sc.bear_consensus_problems(_googl_new("normalized"))
    line = next(p for p in probs if "cannot bound it" in p)
    assert "normalized line" in line and "gaap line" in line, probs
    low = _googl_new("normalized")
    low = low.model_copy(update={"scenarios": {**low.scenarios, "bear": low.scenarios[
        "bear"].model_copy(update={"eps": 10.0})}})
    assert any("cannot bound it" in p for p in sc.bear_consensus_problems(low))


def test_a_matching_line_takes_the_bound() -> None:
    """(+) GAAP legs on a GAAP stamp read #1093's bound: refused above it, passing at it."""
    rec = _googl_new("gaap")
    assert any("is ABOVE the NTM consensus EPS" in p for p in sc.bear_consensus_problems(rec))
    assert rec.ntm_consensus_eps is not None
    at = rec.model_copy(update={"scenarios": {**rec.scenarios, "bear": rec.scenarios[
        "bear"].model_copy(update={"eps": rec.ntm_consensus_eps.value})}})
    assert sc.bear_consensus_problems(at) == []


@pytest.mark.parametrize("line", ["gaap", "normalized"])
def test_an_indistinguishable_stamp_matches_either_line(line: str) -> None:
    """(+) Both lines fit CIQ's P/E, so either leg line is compared — and passes at the stamp."""
    rec = _googl_new(line, stamp_line=sc.STAMP_LINE_EITHER)
    assert rec.ntm_consensus_eps is not None
    at = rec.model_copy(update={"scenarios": {**rec.scenarios, "bear": rec.scenarios[
        "bear"].model_copy(update={"eps": rec.ntm_consensus_eps.value})}})
    assert sc.bear_consensus_problems(at) == []


def test_unlike_lines_pass_on_a_miss_case_stated_on_the_legs_own_line() -> None:
    """(+) Normalized legs, a normalized miss case the bear misses: the stamp is not compared."""
    assert sc.bear_consensus_problems(_googl_new("normalized", miss=_miss("normalized"))) == []


def test_a_miss_case_on_the_wrong_line_is_refused() -> None:
    """(−) A GAAP miss case for a normalized bear measures the miss on another line."""
    probs = sc.bear_consensus_problems(_googl_new("normalized", miss=_miss("gaap")))
    assert any("bear.miss_case is on the gaap line" in p for p in probs), probs


def test_an_undetermined_stamp_assumes_no_line() -> None:
    """(−/+) SETTLED IN WRITING (the record): `undetermined` means the page cannot say which line
    CIQ's NTM P/E is struck on, so it is unlike EVERY leg line — refused with that reason, and
    passing only on a miss case stated on the leg's own line."""
    for line in ("gaap", "normalized"):
        probs = sc.bear_consensus_problems(_googl_new(line, stamp_line="undetermined"))
        assert any("`undetermined`), so no line is assumed" in p for p in probs), probs
        assert sc.bear_consensus_problems(
            _googl_new(line, stamp_line="undetermined", miss=_miss(line))) == []


def test_every_r3_leg_states_its_line_and_no_other_record_carries_one() -> None:
    """(−) An R3 leg without `eps_line` is named, leg by leg; a non-R3 leg with one is refused;
    a value outside the page's two lines is refused by the model."""
    probs = sc.bear_consensus_problems(_googl_new(None))
    assert sorted(p.split(".")[0] for p in probs if ".eps_line is required" in p) == [
        "base", "bear", "bull"], probs
    smpl = _rec("SMPL")
    tagged = smpl.model_copy(update={"scenarios": {**smpl.scenarios, "base": smpl.scenarios[
        "base"].model_copy(update={"eps_line": "gaap"})}})
    assert any(p.startswith("base.eps_line is read only on an R3 leg")
               for p in sc.bear_consensus_problems(tagged))
    with pytest.raises(ValueError, match="is not one of"):
        sc.ScenarioInput(multiple=20.0, eps=1.0, reason="r", eps_line="undetermined")


def test_the_r3_template_asks_for_the_line_and_names_the_pages() -> None:
    """(+) The R3 template carries an empty `eps_line` cell per leg — never proposed: R3 fills no
    EPS — and names the line the page's NTM P/E is struck on."""
    from vinci.dossier.propose import build_template

    doc = json.loads((ROOT / "data" / "dossiers" / "GOOGL" / "dossier.json").read_text())
    tpl = build_template(doc)
    for leg in ("bear", "base", "bull"):
        cell = tpl["scenarios"][leg]
        assert cell["eps_line"] is None
        assert "struck on gaap" in cell["_eps_line_why"]


def test_legs_on_two_lines_are_refused() -> None:
    """(−, review round 0) A bear on one line and a base on another moves the unlike comparison
    into the ratio itself; the legs strike on one line."""
    rec = _googl_new("gaap")
    mixed = rec.model_copy(update={"scenarios": {**rec.scenarios, "bear": rec.scenarios[
        "bear"].model_copy(update={"eps_line": "normalized"})}})
    assert any(p.startswith("the legs state different EPS lines")
               for p in sc.bear_consensus_problems(mixed))
    assert not any(p.startswith("the legs state different EPS lines")
                   for p in sc.bear_consensus_problems(rec))
