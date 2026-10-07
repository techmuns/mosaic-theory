"""GAAP-EPS momentum: a claim citing a GAAP-EPS consensus move that normalized EPS did not make over
the same window is shown to the analyst as a caveat.

THE INCIDENT. AMZN's committed synthesis argues its bull case from "FY26E GAAP EPS +71%"; over the
same 12 months normalized FY26 EPS moved +10%. The gap is a below-the-line gain.

The value-level pins read `tests/fixtures/gaap_eps_momentum_cases.json` — real claims and real
consensus paths FROZEN from the committed pages at bc3954c2, because the live prose re-draws on
every re-assembly and a pin on it would rot. The live-page tests assert only invariants.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import flags as dossier_flags
from vinci.dossier.schemas import (
    ConsensusPath,
    ConsensusPoint,
    DecisiveQuestion,
    ForwardConsensus,
    SourcedPoint,
    Synthesis,
)
from vinci.dossier.synthesis import (
    _GAAP_EPS,
    EPS_MOMENTUM_GAP,
    _eps_move,
    _located_claims,
    _snip,
    gaap_eps_momentum_flags,
)

ROOT = Path(__file__).resolve().parents[1]
CASES: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "gaap_eps_momentum_cases.json").read_text())["cases"]
COMMITTED = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))


def _fc(ticker: str) -> ForwardConsensus:
    case = CASES[ticker]
    return ForwardConsensus(
        periods=case["periods"], spreads=[], revisions=[], source_ref="fixture",
        paths=[ConsensusPath(metric=p["metric"], period=p["period"],
                             points=[ConsensusPoint(**pt) for pt in p["points"]])
               for p in case["paths"]])


def _synth(claims: list[list[str]]) -> Synthesis:
    """A synthesis carrying exactly these claims, each in the field it was found in."""
    pts: dict[str, list[SourcedPoint]] = {
        "bull_point": [], "bear_point": [], "decisive.for": [], "decisive.against": []}
    unknowns: list[str] = []
    balance = ""
    for where, text in claims:
        if where == "key_unknown":
            unknowns.append(text)
        elif where == "evidence_balance":
            balance = text
        else:
            pts[where].append(SourcedPoint(claim=text, source_ref="fixture"))
    return Synthesis(
        evidence_balance=balance, bull_points=pts["bull_point"], bear_points=pts["bear_point"],
        key_unknowns=unknowns, twin_reference_cases=[],
        decisive_question=DecisiveQuestion(question="fixture", evidence_for=pts["decisive.for"],
                                           evidence_against=pts["decisive.against"]))


def _flags(ticker: str) -> list[str]:
    return gaap_eps_momentum_flags(_synth(CASES[ticker]["claims"]), _fc(ticker))


# --- the real cases, frozen -----------------------------------------------------------------------


def test_amzn_s_gaap_eps_bull_point_is_shown_to_the_analyst_with_both_moves() -> None:
    """THE PREVIOUSLY UNFLAGGED CASE: the +71% bull point is caveated, with the normalized move
    beside it, over the window the claim names — and it reaches the HUMAN, not the QA list."""
    flags = _flags("AMZN")
    assert len(flags) == 1
    flag = flags[0]
    assert flag.startswith("GAAP-EPS-MOMENTUM bull_point:")
    assert "12 months" in flag and "+71%" in flag and "+10%" in flag
    assert "7.56 → 12.89" in flag and "7.54 → 8.31" in flag
    caveats, qa = dossier_flags.partition(flags)
    assert qa == [] and len(caveats) == 1
    assert caveats[0].startswith("GAAP-EPS move that normalized EPS did not make (a bull point):")


@pytest.mark.parametrize(("ticker", "gaap", "norm"), [
    ("AORT", "-82%", "-49%"), ("CNXC", "-43%", "-10%"), ("WERN", "-29%", "-8%")])
def test_a_gaap_cut_that_operating_eps_did_not_make_is_caveated_too(
        ticker: str, gaap: str, norm: str) -> None:
    """Direction does not matter: a GAAP cut made mostly of charges overstates deterioration as
    surely as AMZN's gain overstates momentum. Each cites the 12-month move, reported there."""
    flags = _flags(ticker)
    assert sorted(f.split(" ", 2)[1].rstrip(":") for f in flags) == [
        "bear_point", "decisive.against"], "each frozen case cites the move in exactly these two"
    for flag in flags:
        assert "over the 12 months" in flag and gaap in flag and norm in flag


def test_a_gap_below_the_threshold_is_not_caveated() -> None:
    """NEGATIVE: V's GAAP and normalized FY26 moves sit 4 points apart — both describe one thing."""
    move = _eps_move(_fc("V"))
    assert move is not None and abs(move[2] - move[3]) < EPS_MOMENTUM_GAP
    assert _flags("V") == []


def test_a_percentage_from_another_window_or_year_is_not_read_as_the_move() -> None:
    """NEGATIVE, from the first real run: SMPL's claim cites GAAP-EPS SURPRISES (-36%, -9%, -42%),
    and -9% equals a FY2028 six-month consensus move. Only the current-FY move the synthesis was
    shown is compared, so the coincidence does not fire."""
    fc = _fc("SMPL")
    fy28 = {p.period: p for p in fc.paths if p.metric == "EPS (GAAP)"}
    assert "FY 2028" in fy28, "the coincidence's other half is gone from the fixture"
    assert _flags("SMPL") == []


def test_an_unqualified_eps_figure_is_not_a_gaap_claim() -> None:
    """NEGATIVE: NCNO's "FY27 EPS revised net +34%" is the NORMALIZED move — CIQ's unqualified
    figure — and its GAAP base is 0.01, so the GAAP move is +3,400%. Only a claim naming GAAP EPS
    is read."""
    assert not any(_GAAP_EPS.search(text) for _, text in CASES["NCNO"]["claims"])
    assert _flags("NCNO") == []


def test_a_loss_making_base_has_no_percentage_move() -> None:
    """NEGATIVE: ORKA's GAAP and normalized paths are negative, so there is no rate to compare and
    nothing fires — even for a claim that names GAAP EPS and a percentage (a stand-in, on the
    real paths)."""
    assert _eps_move(_fc("ORKA")) is None
    synth = _synth([["bear_point", "FY26 GAAP EPS consensus worsened -6% over 12 months"]])
    assert gaap_eps_momentum_flags(synth, _fc("ORKA")) == []
    assert gaap_eps_momentum_flags(synth, None) == []


def test_a_figure_of_the_opposite_sign_is_not_the_move() -> None:
    """NEGATIVE: a signed figure must carry the move's sign. On AMZN's real paths (+71%), a claim
    stating "-71%" is about something else and does not fire; the unsigned "71%" does."""
    fc = _fc("AMZN")
    assert gaap_eps_momentum_flags(
        _synth([["bear_point", "FY26 GAAP EPS consensus fell -71% on the year"]]), fc) == []
    assert gaap_eps_momentum_flags(
        _synth([["bull_point", "FY26 GAAP EPS consensus rose 71% on the year"]]), fc)


def test_the_comparison_shares_one_window() -> None:
    """The normalized move is over the GAAP move's window or nothing: drop the normalized path's
    12-month point and the 12-month GAAP move has no partner — no comparison, no flag."""
    fc = _fc("AMZN")
    paths = [p if not (p.metric == "EPS Normalized" and p.period == fc.periods[0]) else
             p.model_copy(update={"points": [pt for pt in p.points if pt.months_ago != 12]})
             for p in fc.paths]
    assert _eps_move(fc.model_copy(update={"paths": paths})) is None


# --- the live pages: invariants only --------------------------------------------------------------


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_caveat_sits_on_a_gaap_eps_claim_and_a_real_gap(ticker: str) -> None:
    """ACROSS THE COMMITTED PAGES: whatever the prose says today, a caveat only ever lands on a
    claim that names GAAP EPS, on a page whose current-FY GAAP and normalized moves differ by the
    threshold over one window."""
    doc = json.loads((ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    if not doc.get("synthesis") or not doc.get("forward_consensus"):
        pytest.skip(f"{ticker}: no synthesis or no forward consensus on the page")
    synth = Synthesis.model_validate(doc["synthesis"])
    fc = ForwardConsensus.model_validate(doc["forward_consensus"])
    flags = gaap_eps_momentum_flags(synth, fc)
    if not flags:
        return
    move = _eps_move(fc)
    assert move is not None and abs(move[2] - move[3]) >= EPS_MOMENTUM_GAP
    located = _located_claims(synth)
    for flag in flags:
        assert any(flag.startswith(f"GAAP-EPS-MOMENTUM {where}: '{_snip(text, 120)}'")
                   and _GAAP_EPS.search(text) for where, text in located), flag


def test_assembly_runs_the_check_on_the_layer_the_page_carries() -> None:
    """A SOURCE PIN, AND ITS LIMIT STATED: assembly needs the network and an LLM, so this asserts
    the call is written, against the ONE forward-consensus object the page is given."""
    from vinci.dossier import assemble as asm

    src = inspect.getsource(asm.assemble_one)
    assert "flags += gaap_eps_momentum_flags(synthesis, forward_consensus)" in src
    assert src.count("ciq_sheets.forward_consensus(bundle)") == 1
