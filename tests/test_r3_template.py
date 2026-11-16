"""The template matches the page's recipe — `scenario-propose` on an R3 page (§5.0 row 10).

Before this, an R3-tagged page got the R1-shaped template: an `EV/EBITDA` basis `_run_r3` refuses,
a pre-filled revenue and margin (it refuses a margin on a leg), a base multiple pre-filled from
the own-history EV/EBITDA median (a different multiple), and three enterprise facts it refuses.
GOOGL's R3 record (`scenarios/GOOGL.json`, 2026-09-01) was written by hand-correcting the
template. The validator was recipe-aware (`scenarios.axes_for`); the proposer was not.

THE PAGES ARE REAL. GOOGL's committed page carries the operator's R3 tag; the R1 pins run over
every committed page that builds a template. The pages are living artifacts, so the assertions
are INVARIANTS against the code's own constants and the page's own fields, never a pinned number.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier.midcycle import MULTIPLE_BASIS
from vinci.dossier.propose import (
    AXIS_LEG_FIELD,
    LEGS,
    ProposalRefusedError,
    build_template,
    legs_from_template,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Every key an R3 leg cell may carry: the recipe's two axes with their derivations, the reason,
#: the base leg's horizon and year, and the bear basis. No revenue, margin, EBIT or margin basis.
R3_CELL_INPUTS = {"eps", "eps_derivation", "multiple", "multiple_derivation", "reason",
                  "years_to_terminal", "leg_fy", "bear_basis"}

#: Every key an R1 leg cell carries or may carry — main's shape, unchanged by this work.
R1_CELL_INPUTS = {"revenue", "revenue_adjustment", "revenue_derivation", "margin",
                  "margin_adjustment", "margin_derivation", "multiple", "multiple_adjustment",
                  "multiple_derivation", "reason", "years_to_terminal", "leg_fy", "eps", "ebit",
                  "bear_basis", "margin_basis"}


def _page(ticker: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    return doc


def _r3_page() -> dict[str, Any]:
    doc = _page("GOOGL")
    assert doc["anchor"]["recipe_hint"] == sc.RECIPE_R3, (
        "GOOGL's committed page no longer carries the R3 tag — this file's premise moved")
    return doc


# --- (+) the R3 shape ----------------------------------------------------------------------------

def test_an_r3_page_gets_the_p_e_basis_and_the_r3_axes() -> None:
    """(+) The basis is the one `_run_r3` requires, and each leg carries only the cells the recipe
    reads — `eps` and `multiple`, both EMPTY, each with a derivation to state."""
    tpl = build_template(_r3_page())
    assert tpl["recipe_id"] == sc.RECIPE_R3
    assert tpl["multiple_basis"] == sc.BASIS_PE, (
        f"an R3 template wrote basis {tpl['multiple_basis']!r} — `_run_r3` refuses any basis but "
        f"{sc.BASIS_PE!r}")
    axes = sc.axes_for(sc.RECIPE_R3, tpl["multiple_basis"])
    assert axes is not None
    fields = {AXIS_LEG_FIELD.get(a, a) for a in axes}
    for leg, cell in legs_from_template(tpl).items():
        assert set(cell) <= R3_CELL_INPUTS, f"{leg}: {sorted(set(cell) - R3_CELL_INPUTS)}"
        for f in fields:
            assert f in cell and cell[f] is None, f"{leg}.{f}: missing, or pre-filled"
            assert cell[f"{f}_derivation"] == "", f"{leg}.{f}: no derivation cell to state"
    assert sorted(tpl["_evidence"]) == sorted(axes), (
        "the evidence is keyed by axes the recipe does not model")


def test_an_r3_template_carries_no_fact_the_recipe_refuses() -> None:
    """(+) `_run_r3` refuses a `net_debt`, `d_and_a` or `diluted_shares` fact — a P/E already
    values equity per share. GOOGL's committed R3 record carries none."""
    tpl = build_template(_r3_page())
    assert tpl["facts"] == {}, sorted(tpl["facts"])
    assert json.loads((ROOT / "scenarios" / "GOOGL.json").read_text())["facts"] == {}


def test_every_field_the_r3_recipe_reads_is_settable_from_the_template() -> None:
    """The settable-field guard for the R3 shape (R4's twin is in `test_r4_template`). A field
    `_run_r3` or `scenario-create` reads, with no template cell, is a recipe the create path
    cannot reach."""
    cells = build_template(_r3_page())["scenarios"]
    for leg in LEGS:
        assert {"eps", "multiple", "reason"} <= set(cells[leg]), leg
    assert {"years_to_terminal", "leg_fy"} <= set(cells["base"])
    assert "bear_basis" in cells["bear"]
    assert cells["base"]["leg_fy"] is None, (
        "R1 pre-fills the EV-gap year because its revenue anchor sits there; R3 has no anchor")


def test_an_r3_page_whose_r1_bit_is_false_is_still_refused() -> None:
    """(-) SCOPE PIN — the R3 template is dispatched AFTER the applicable refusal, so the coupling
    §5.0 row 10 records (R1's `applicable` bit read as an R3 page's) is unchanged here, on the
    propose side as `test_r4_template` pins it on the create side. Widening R4's exception to R3
    is a separate call."""
    doc = _r3_page()
    doc["anchor"]["applicable"] = False
    with pytest.raises(ProposalRefusedError, match="applicable=False"):
        build_template(doc)


def test_propose_counts_the_cells_the_r3_recipe_reads(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(+) The command's own summary counts R3's six cells, not R1's nine."""
    from vinci.cli import _cmd_scenario_propose

    _stage(tmp_path, monkeypatch)
    out = tmp_path / "tpl.json"
    assert _cmd_scenario_propose(argparse.Namespace(ticker="GOOGL", out=str(out))) == 0
    assert "0 of 6 pre-filled" in capsys.readouterr().out


# --- (+) create, through the CLI -----------------------------------------------------------------

def _stage(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """GOOGL's committed page in a scratch tree with an EMPTY `scenarios/` — so create runs into
    the scratch directory and never near the committed record."""
    doc = _r3_page()
    (tmp_path / "data" / "dossiers" / "GOOGL").mkdir(parents=True)
    (tmp_path / "data" / "dossiers" / "GOOGL" / "dossier.json").write_text(json.dumps(doc))
    (tmp_path / "scenarios").mkdir()
    monkeypatch.chdir(tmp_path)
    return doc


def test_create_on_the_empty_r3_template_refuses_only_the_empty_cells(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(+) The template as proposed, untouched: every refusal is an EMPTY-BY-DESIGN cell — the six
    leg cells and the horizon — and none names a basis, a revenue, a margin or an anchor. On the
    R1 shape the base multiple sat 'anchored' to an EV/EBITDA median, which a P/E is not."""
    from vinci.cli import _cmd_scenario_create, _cmd_scenario_propose

    _stage(tmp_path, monkeypatch)
    out = tmp_path / "tpl.json"
    assert _cmd_scenario_propose(argparse.Namespace(ticker="GOOGL", out=str(out))) == 0
    capsys.readouterr()
    assert _cmd_scenario_create(argparse.Namespace(ticker="GOOGL", from_file=str(out))) == 1
    lines = [ln.strip()[2:] for ln in capsys.readouterr().out.splitlines()
             if ln.strip().startswith("- ")]
    absent = {ln.split(" is required and absent")[0] for ln in lines
              if " is required and absent" in ln}
    assert absent == {f"{leg}.{f}" for leg in LEGS for f in ("eps", "multiple")}, lines
    horizon = [ln for ln in lines if ln.startswith("base.years_to_terminal is required")]
    assert len(horizon) == 1, lines
    assert len(lines) == len(absent) + len(horizon), (
        f"a refusal that is not an empty-by-design cell: {lines}")
    assert not list((tmp_path / "scenarios").glob("GOOGL.json")), "a refusal wrote a record"


def test_propose_then_create_writes_the_r3_record_with_no_hand_edit(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """(+) THE HAND-CORRECTION ROW 10 RECORDS, GONE. The template's empty cells are filled with
    the COMMITTED GOOGL record's own analyst inputs (its EPS, P/E, horizon, bear basis, reasons
    and derivations), and nothing else in the template is touched: create writes the record and
    each leg values at EPS × P/E — the committed record's own per-leg values.

    The one cell the committed record does not state is its entry window (it predates the field,
    #658), so the fill names the base leg's own year, a TEST value labelled as one."""
    from vinci.cli import _cmd_scenario_create, _cmd_scenario_propose

    _stage(tmp_path, monkeypatch)
    committed = json.loads((ROOT / "scenarios" / "GOOGL.json").read_text())
    assert committed["recipe_id"] == sc.RECIPE_R3
    out = tmp_path / "tpl.json"
    assert _cmd_scenario_propose(argparse.Namespace(ticker="GOOGL", out=str(out))) == 0
    tpl = json.loads(out.read_text())
    methods = {ax: committed["assumptions"][ax]["method"] for ax in ("earnings", "multiple")}
    for leg in LEGS:
        src = committed["scenarios"][leg]
        tpl["scenarios"][leg].update(
            eps=src["eps"], multiple=src["multiple"], reason=src["reason"],
            eps_derivation=methods["earnings"], multiple_derivation=methods["multiple"])
    base = committed["scenarios"]["base"]
    tpl["scenarios"]["base"].update(years_to_terminal=base["years_to_terminal"],
                                    leg_fy=base["leg_fy"])
    tpl["scenarios"]["bear"]["bear_basis"] = committed["scenarios"]["bear"]["bear_basis"]
    assert tpl["spot_as_of"], "the page carries no spot date to strike the legs on"
    tpl.update(entry_basis=f"FY{base['leg_fy']}", underwrite_date=tpl["spot_as_of"],
               analyst="test")
    out.write_text(json.dumps(tpl))
    capsys.readouterr()
    rc = _cmd_scenario_create(argparse.Namespace(ticker="GOOGL", from_file=str(out)))
    assert rc == 0, capsys.readouterr().out

    rec = json.loads((tmp_path / "scenarios" / "GOOGL.json").read_text())
    assert rec["recipe_id"] == sc.RECIPE_R3 and rec["multiple_basis"] == sc.BASIS_PE
    assert rec["facts"] == {} and sorted(rec["assumptions"]) == ["earnings", "multiple"]
    for leg in LEGS:
        got = rec["result"]["per_scenario"][leg]["value_per_share"]
        src = committed["scenarios"][leg]
        assert got == pytest.approx(src["eps"] * src["multiple"], abs=1e-3), leg
        assert got == pytest.approx(
            committed["result"]["per_scenario"][leg]["value_per_share"], abs=1e-3), leg


# --- R1 and R4 are unchanged ---------------------------------------------------------------------

def _built() -> list[tuple[str, dict[str, Any]]]:
    out = []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        doc = json.loads(p.read_text())
        try:
            out.append((str(doc["anchor"]["recipe_hint"]), build_template(doc)))
        except ProposalRefusedError:
            continue
    return out


def test_r1_and_r4_templates_keep_their_shape_across_the_corpus() -> None:
    """Every committed page that builds a template and is not R3-tagged keeps main's shape: an
    R1-shaped page writes R1's basis — the validator's constant, `midcycle.MULTIPLE_BASIS` — with
    R1's cells and facts, and an R4 page writes R4's. Measured byte-identical on 25 of the 26
    pages before this shipped (GOOGL, the R3 page, is the one that moved)."""
    built = _built()
    seen = {"r1": 0, "r4": 0}
    for hint, tpl in built:
        if hint == sc.RECIPE_R3:
            continue
        if hint == sc.RECIPE_R4:
            assert tpl["multiple_basis"] == sc.BASIS_EV_NTM_EBIT, tpl["ticker"]
            seen["r4"] += 1
            continue
        assert tpl["recipe_id"] == hint, tpl["ticker"]
        assert tpl["multiple_basis"] == MULTIPLE_BASIS, tpl["ticker"]
        assert set(tpl["facts"]) <= {"diluted_shares", "d_and_a", "net_debt"}, tpl["ticker"]
        assert "diluted_shares" in tpl["facts"], tpl["ticker"]
        for leg, cell in legs_from_template(tpl).items():
            assert set(cell) <= R1_CELL_INPUTS, (tpl["ticker"], leg, sorted(cell))
            assert {"revenue", "margin", "multiple", "eps", "ebit", "margin_basis"} <= set(cell)
        seen["r1"] += 1
    assert seen["r1"] >= 5 and seen["r4"] >= 1, (
        f"the corpus check ran over {seen} — it is not exercising both shapes")
