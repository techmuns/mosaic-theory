"""The R4 template — `scenario-propose` on an R4-tagged page (2026-10-09).

Before this, an R4-tagged page got the R1-shaped template: a pre-filled revenue, margin and D&A
fact and an `EV/EBITDA` basis, all four of which `_run_r4` REFUSES. An R4 underwrite could only be
written by hand-deleting half the template. Now the page's tag selects the template's shape, the
bridge comes from the page's `ev_bridge` (CIQ's TEV claims less market cap, held to exit by the
operator's rule), and a missing or flagged bridge refuses rather than prefills.

THE PAGES ARE REAL. No committed page carries an R4 tag yet — the AMZN/UBER re-tags are the
operator's, after the R4 card render — so each test copies a committed page and sets the tag in
memory, the re-tag an operator would make (#688's create test does the same). The pages are living
artifacts, so the assertions are INVARIANTS against the page's own fields, never a pinned number.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier.ciq_sheets import EV_BRIDGE_CIQ_TOL
from vinci.dossier.propose import (
    ProposalRefusedError,
    build_r4_template,
    build_template,
    check_tier_agreement,
    legs_from_template,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Every key an R4 leg cell may carry — the recipe's two axes with their derivations, the leg
#: reason, the base leg's horizon and year, the bear basis, and `_`-commentary.
R4_CELL_INPUTS = {"ebit", "ebit_derivation", "multiple", "multiple_derivation", "reason",
                  "years_to_terminal", "leg_fy", "bear_basis"}


def _page(ticker: str, *, tag: str | None = sc.RECIPE_R4) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    if tag is not None:
        doc["anchor"]["recipe_hint"] = tag
    return doc


# --- the shape -----------------------------------------------------------------------------------

@pytest.mark.parametrize("ticker", ["AMZN", "UBER"])
def test_an_r4_page_gets_an_r4_template(ticker: str) -> None:
    """Only the cells the recipe reads: `_run_r4` refuses revenue, margin, EPS and a D&A fact, so
    none is emitted — and every R4 cell arrives EMPTY, because nothing anchors it."""
    tpl = build_template(_page(ticker))
    assert tpl["recipe_id"] == sc.RECIPE_R4 and tpl["multiple_basis"] == sc.BASIS_EV_NTM_EBIT
    assert set(tpl["facts"]) == {"diluted_shares", "net_debt"}, "no D&A fact — R4 refuses one"
    for leg, cell in legs_from_template(tpl).items():
        assert set(cell) <= R4_CELL_INPUTS, f"{leg}: a cell the recipe never reads"
        assert cell["ebit"] is None and cell["multiple"] is None, (
            f"{leg}: an R4 leg driver was pre-filled — nothing is ruled to anchor it")
    assert tpl["scenarios"]["base"]["leg_fy"] is None, (
        "R1 pre-fills the EV-gap year because its revenue anchor sits there; R4 has no anchor")


def test_every_field_the_r4_recipe_reads_is_settable_from_the_template() -> None:
    """The settable-field guard for the R4 shape (its R1 twin lives in test_leg_fiscal_year). A
    field `_run_r4` or `scenario-create` reads, with no template cell, is a recipe the create path
    cannot reach — the class #688 found on `ebit` itself."""
    cells = build_template(_page("AMZN"))["scenarios"]
    settable = {k for c in cells.values() for k in c if not k.startswith("_")}
    assert {"ebit", "multiple", "reason", "years_to_terminal", "leg_fy", "bear_basis",
            "ebit_derivation", "multiple_derivation"} <= settable


@pytest.mark.parametrize("ticker", ["SMPL", "GOOGL"])
def test_a_page_not_tagged_r4_keeps_its_template(ticker: str) -> None:
    """The dispatch keys on the R4 tag alone: an R1 page (SMPL) and an R3 page (GOOGL) keep the
    template they had — measured byte-identical on all 26 committed pages before this shipped."""
    tpl = build_template(_page(ticker, tag=None))
    assert tpl["multiple_basis"] == "EV/EBITDA" and "revenue" in tpl["scenarios"]["base"]


@pytest.mark.parametrize("ticker", ["AMZN", "UBER"])
def test_the_pages_tagged_r4_get_the_r4_template_as_committed(ticker: str) -> None:
    """The committed re-tags (2026-10-09), unmodified: the page's OWN tag selects the R4 shape."""
    doc = _page(ticker, tag=None)
    assert doc["anchor"]["recipe_hint"] == sc.RECIPE_R4
    tpl = build_template(doc)
    assert tpl["recipe_id"] == sc.RECIPE_R4 and tpl["multiple_basis"] == sc.BASIS_EV_NTM_EBIT


# --- the bridge ----------------------------------------------------------------------------------

@pytest.mark.parametrize("ticker", ["AMZN", "UBER"])
def test_the_bridge_fact_is_the_pages_ciq_tev_claims(ticker: str) -> None:
    """The fact is the page's held exit claims, which ARE CIQ's TEV less market cap — Net Debt plus
    preferred plus minority. UBER is the case where the last two matter ($1,083M of minority)."""
    doc = _page(ticker)
    eb = doc["ev_bridge"]
    fact = build_template(doc)["facts"]["net_debt"]
    assert fact["value"] == pytest.approx(eb["claims"])
    assert abs(fact["value"] - eb["ciq_tev_claims"]) <= EV_BRIDGE_CIQ_TOL
    lines = {ln["label"]: ln["value"] for ln in eb["lines"]}
    assert fact["value"] == pytest.approx(
        eb["net_debt"] + lines["Total Pref. Equity"] + lines["Total Minority Interest"])
    assert {x["value"] for x in eb["exit_claims"]} == {fact["value"]}
    assert eb["source_sha256"] in fact["source"] and eb["estimates_sha256"] in fact["source"]


def _refused(doc: dict[str, Any], match: str) -> None:
    with pytest.raises(ProposalRefusedError, match=match):
        build_r4_template(doc)


def test_a_page_without_a_bridge_is_refused() -> None:
    """FUBO is the real shape: no `ev_bridge` on its page (its Financials export is unstamped)."""
    _refused(_page("FUBO"), "carries no `ev_bridge`")


def test_an_unchecked_bridge_is_refused() -> None:
    doc = _page("AMZN")
    doc["ev_bridge"]["ciq_tev_claims"] = None
    _refused(doc, "never checked against CIQ")


def test_a_flagged_bridge_is_refused_and_one_inside_the_tolerance_is_not() -> None:
    """The template must not prefill from a flagged bridge (#689's record). Both sides of the
    tolerance, which is ONE constant shared with the bridge's own DISAGREES note."""
    doc = _page("AMZN")
    doc["ev_bridge"]["ciq_tev_claims"] = doc["ev_bridge"]["claims"] + 2 * EV_BRIDGE_CIQ_TOL
    _refused(doc, "disagrees with CIQ's own TEV")
    ok = _page("AMZN")
    ok["ev_bridge"]["ciq_tev_claims"] = ok["ev_bridge"]["claims"] + 0.8 * EV_BRIDGE_CIQ_TOL
    build_r4_template(ok)


def test_a_bridge_from_another_estimates_pull_is_refused() -> None:
    """The bridge and today's multiple must come from one Estimates export."""
    doc = _page("AMZN")
    doc["forward_consensus"]["source_sha256"] = "0000000000"
    _refused(doc, "two pulls")


def test_exit_claims_that_differ_by_year_are_refused() -> None:
    """CONSTRUCTED — every committed exit is held today. A consensus exit would vary by year, and
    the template cannot choose the record's exit year."""
    doc = _page("AMZN")
    doc["ev_bridge"]["exit_claims"][-1] = dict(doc["ev_bridge"]["exit_claims"][-1],
                                               value=1.0, method="consensus")
    _refused(doc, "differ by fiscal year")
    doc["ev_bridge"]["exit_claims"] = []
    _refused(doc, "no complete exit claims")


# --- the multiple's empty cell says why, from the page's own band ---------------------------------

def test_the_multiple_says_what_an_unruled_median_would_propose() -> None:
    """Outside its own band, the reason states the ratio a median default would impose (AMZN on
    2026-10-09: 22.59x under a 23.22x low, median 52.56x); inside it, it does not."""
    doc = _page("AMZN")
    series = next(s for s in doc["forward_multiple_history"]["series"]
                  if s["metric"] == "EV/NTM EBIT")
    series["band"].update(current=10.0, low=20.0, high=40.0, median=30.0)
    why = build_r4_template(copy.deepcopy(doc))["scenarios"]["base"]["_multiple_why_no_anchor"]
    assert "OUTSIDE" in why and "3.0×" in why
    series["band"].update(current=25.0)
    why = build_r4_template(doc)["scenarios"]["base"]["_multiple_why_no_anchor"]
    assert "OUTSIDE" not in why


# --- the tier gate: R4's own eligibility says R1 cannot anchor -----------------------------------

def test_an_r4_tag_is_not_refused_by_r1s_applicable_bit() -> None:
    """UBER carries `applicable=False` — R1 cannot anchor it, which is R4's eligibility condition 2.
    The gate read that bit as the recipe's and would refuse the name its own rule admits."""
    doc = _page("UBER")
    assert doc["anchor"]["applicable"] is False
    check_tier_agreement(doc, sc.RECIPE_R4)
    build_template(doc)
    with pytest.raises(ProposalRefusedError, match="disagrees with record recipe"):
        check_tier_agreement(doc, sc.RECIPE_R3)


def test_an_r3_tag_keeps_the_applicable_coupling() -> None:
    """NEGATIVE PIN — the exception is R4's alone. R3's eligibility asks nothing of R1, so the
    coupling §5.0 row 10 records (#670) is a separate call and is unchanged here."""
    doc = _page("GOOGL", tag=None)
    doc["anchor"]["applicable"] = False
    with pytest.raises(ProposalRefusedError, match="applicable=False"):
        check_tier_agreement(doc, sc.RECIPE_R3)


# --- end to end: propose → fill → create ---------------------------------------------------------

@pytest.mark.parametrize("ticker", ["AMZN", "UBER"])
def test_propose_then_create_writes_an_r4_record_on_the_pages_bridge(
    ticker: str, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """THE CREATE PATH, run from the template the proposer emits. The analyst's six numbers are
    filled from the page's own figures (FY2028 consensus EBIT, today's NTM EV/EBIT); the bridge and
    shares are the template's, untouched."""
    from vinci.cli import _cmd_scenario_create, _cmd_scenario_propose

    doc = _page(ticker)
    (tmp_path / "data" / "dossiers" / ticker).mkdir(parents=True)
    (tmp_path / "data" / "dossiers" / ticker / "dossier.json").write_text(json.dumps(doc))
    (tmp_path / "scenarios").mkdir()
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "tpl.json"
    assert _cmd_scenario_propose(argparse.Namespace(ticker=ticker, out=str(out))) == 0
    assert "0 of 6 pre-filled" in capsys.readouterr().out

    fc = doc["forward_consensus"]
    ebit = next(s["mean"] for s in fc["spreads"] if s["metric"] == "EBIT" and
                s["period"] == "FY 2028")
    mult = next(m["value"] for m in fc["current_multiples"]
                if m["metric"] == "TEV/EBIT" and m["period"] == "NTM")
    tpl = json.loads(out.read_text())
    for scale, leg in ((0.8, "bear"), (1.0, "base"), (1.1, "bull")):
        c = tpl["scenarios"][leg]
        c.update(ebit=ebit * scale, multiple=round(mult * scale, 4), reason=f"{leg} test leg",
                 ebit_derivation="FY2028 consensus EBIT, scaled for the leg",
                 multiple_derivation="today's NTM EV/EBIT, scaled for the leg")
    tpl["scenarios"]["base"].update(years_to_terminal=1.25, leg_fy="2028")
    tpl["scenarios"]["bear"]["bear_basis"] = "analyst"
    tpl.update(entry_basis="NTM", entry_denominator=round(ebit / 1.5, 1),
               underwrite_date="2026-10-09", analyst="test")
    out.write_text(json.dumps(tpl))
    assert _cmd_scenario_create(argparse.Namespace(ticker=ticker, from_file=str(out))) == 0

    rec = json.loads((tmp_path / "scenarios" / f"{ticker}.json").read_text())
    assert rec["recipe_id"] == sc.RECIPE_R4 and set(rec["assumptions"]) == {"ebit", "multiple"}
    assert rec["facts"]["net_debt"]["value"] == pytest.approx(doc["ev_bridge"]["claims"])
    base = rec["result"]["per_scenario"]["base"]
    assert base["value_per_share"] == pytest.approx(
        (ebit * mult - doc["ev_bridge"]["claims"]) / rec["facts"]["diluted_shares"]["value"],
        abs=1e-2)
