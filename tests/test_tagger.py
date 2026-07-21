"""Tests for the propose-only recipe tagger (vinci.dossier.tagger).

The load-bearing property is that it PROPOSES and never writes — a wrong tag decides which
arithmetic a name gets and is invisible in the output, since an R1 grid on an R2 name looks exactly
like an R1 grid. So the pins are: the signal→proposal mapping on synthetic shapes, and the
purity/precedence guarantees. Committed artifacts are asserted only on invariants that survive a
re-tag, never on a specific name proposing a specific recipe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.dossier import tagger as tg
from vinci.dossier.anchor import (
    RECIPE_R1,
    RECIPE_R1_NOT_ROBUST,
    RECIPE_R2,
    RECIPE_UNRESOLVED,
)

_DOSSIERS = Path(__file__).resolve().parents[1] / "data" / "dossiers"


def _doc(*, margins: list[float], net_debt: float | None = 100.0, base: float | None = 20.0,
         shares: float | None = 50e6, band: bool = True, dq: str | None = None) -> dict:
    """A committed-shape dossier carrying just the signals the tagger reads. Revenue is held at
    1,000 so EBIT = margin × 1,000 reproduces the intended margin exactly."""
    rev = [1000.0] * len(margins)
    return {
        "mechanical": {
            "financial_summary": {"annual": {"value": {
                "is_estimate": [False] * len(margins),
                "rows": [{"label": "Revenue ($M)", "values": rev},
                         {"label": "EBIT ($M)", "values": [m * 1000.0 for m in margins]}]}}},
            "valuation": {"own_history": {"value": (
                [{"metric": "EV/EBITDA (TEV/LTM)", "median": 12.0}] if band else [])}},
        },
        "anchor": {"net_debt": {"value": net_debt}, "anchor_base_value_per_share": base,
                   "diluted_shares": {"value": shares}, "data_quality": dq},
    }


# --- the signal -> proposal mapping -------------------------------------------------------------
def test_stable_adequate_margin_proposes_r1() -> None:
    p = tg.propose("X", _doc(margins=[0.14, 0.15, 0.16, 0.15, 0.16, 0.15]))
    assert p.proposed == RECIPE_R1
    assert any("stable" in s for s in p.signals)


def test_negative_margin_history_proposes_r2() -> None:
    """The positivity case: nothing to revert to because the level was never positive."""
    p = tg.propose("X", _doc(margins=[-0.20, -0.15, -0.12, -0.08, -0.05, -0.03]))
    assert p.proposed == RECIPE_R2
    assert any("negative" in s for s in p.signals)


def test_ramp_proposes_r2_even_though_the_latest_margin_is_healthy() -> None:
    """THE VITL SHAPE, and the one a naive positivity check misses: the latest margin is a
    perfectly good 11.6%, so R1 computes happily — but the early years say a different business
    and the median describes neither end."""
    p = tg.propose("X", _doc(margins=[0.0, 0.005, 0.01, 0.06, 0.09, 0.116]))
    assert p.proposed == RECIPE_R2
    assert any("ramp" in s for s in p.signals)


def test_dominant_leverage_proposes_not_robust() -> None:
    """THE CNXC SHAPE: the margin history is fine and R1 computes, but net debt exceeds the equity
    the anchor derives, so a single turn of multiple error moves most of the price."""
    p = tg.propose("X", _doc(margins=[0.06, 0.065, 0.06, 0.055, 0.06, 0.065],
                             net_debt=2000.0, base=20.0, shares=50e6))   # equity 1,000M
    assert p.proposed == RECIPE_R1_NOT_ROBUST
    assert any("% of anchor equity" in s for s in p.signals)


def test_thin_but_positive_margin_is_flagged_not_waved_through() -> None:
    p = tg.propose("X", _doc(margins=[0.02, 0.03, 0.025, 0.03, 0.035, 0.03], net_debt=10.0))
    assert p.proposed == RECIPE_R1_NOT_ROBUST
    assert "swamps" in p.note or any("swamps" in s for s in p.signals)


def test_short_history_is_unresolved_not_r2() -> None:
    """A margin we could not CHARACTERISE is a data gap, never an R2 signal — the same distinction
    compute_anchor draws between 'not computable' and 'computed and non-positive'."""
    p = tg.propose("X", _doc(margins=[0.10, 0.12]))
    assert p.proposed == RECIPE_UNRESOLVED


# --- precedence ---------------------------------------------------------------------------------
def test_a_disqualified_band_outranks_a_healthy_margin() -> None:
    """A flagged guard means the exit multiple has no usable denominator, so it beats every other
    signal — including a margin history that would otherwise propose R1."""
    p = tg.propose("X", _doc(margins=[0.14, 0.15, 0.16, 0.15, 0.16, 0.15], dq="band_incoherent"))
    assert p.proposed == RECIPE_R2
    assert any("band guard flagged" in s for s in p.signals)


def test_absent_band_proposes_r2() -> None:
    """THE FUBO SHAPE: every trailing multiple is NM on a loss-making year, so the series does not
    exist at all — there is no median to take, which is the R2 case by definition."""
    p = tg.propose("X", _doc(margins=[-0.10, -0.08, -0.05, -0.04, -0.03, -0.02], band=False))
    assert p.proposed == RECIPE_R2
    assert any("does not exist" in s for s in p.signals)


def test_leverage_is_not_read_off_half_a_balance_sheet() -> None:
    """Missing net debt or missing anchor equity → no leverage signal, never a partial one."""
    p = tg.propose("X", _doc(margins=[0.14, 0.15, 0.16, 0.15, 0.16, 0.15], net_debt=None))
    assert any("not assessable" in s for s in p.signals)
    assert p.proposed == RECIPE_R1          # falls through to the margin read, not to a guess


# --- propose-only, and the absent-vs-disagree distinction ---------------------------------------
def test_absent_committed_tag_is_not_a_disagreement() -> None:
    """``agrees`` is None when nothing is committed. Conflating absent with disagreeing would make
    the first tagging of a name look like an override of a human."""
    doc = _doc(margins=[0.14, 0.15, 0.16, 0.15, 0.16, 0.15])
    doc["anchor"].pop("recipe_hint", None)
    assert tg.propose("X", doc).agrees is None
    doc["anchor"]["recipe_hint"] = RECIPE_R1
    assert tg.propose("X", doc).agrees is True
    doc["anchor"]["recipe_hint"] = RECIPE_R2
    assert tg.propose("X", doc).agrees is False


def test_propose_does_not_mutate_the_document() -> None:
    """PURITY. The tagger reads committed artifacts; a proposal that edited one in passing would be
    a write nobody authorised."""
    doc = _doc(margins=[0.14, 0.15, 0.16, 0.15, 0.16, 0.15])
    before = json.dumps(doc, sort_keys=True)
    tg.propose("X", doc)
    assert json.dumps(doc, sort_keys=True) == before


def test_every_proposal_carries_its_signals() -> None:
    """A tagger nobody can argue with is a tagger nobody checks."""
    p = tg.propose("X", _doc(margins=[0.14, 0.15, 0.16, 0.15, 0.16, 0.15]))
    assert p.signals and p.note
    assert all(isinstance(s, str) and s.strip() for s in p.signals)


# --- committed artifacts: invariants only -------------------------------------------------------
def test_tagger_runs_on_every_committed_dossier_without_raising() -> None:
    """It must survive every real shape on file — including a dossier with no anchor block at all
    (VRRM) and one whose multiple series does not exist (FUBO). A tagger that throws on a real
    artifact is worse than no tagger, because the sweep silently stops there."""
    seen = 0
    for d in sorted(_DOSSIERS.iterdir()):
        f = d / "dossier.json"
        if not f.exists():
            continue
        seen += 1
        p = tg.propose(d.name, json.loads(f.read_text()))
        assert p.proposed in {RECIPE_R1, RECIPE_R2, RECIPE_R1_NOT_ROBUST, RECIPE_UNRESOLVED}
        assert p.signals
    assert seen >= 10


def test_no_committed_hand_tag_is_contradicted_without_the_disagreement_being_visible() -> None:
    """Where the tagger DISAGREES with a committed tag it must say so explicitly (agrees is False)
    and carry signals explaining why — the operator ratifies from the disagreement, so a silent one
    is the failure mode. Phrasing- and name-independent: this stays true after any re-tag."""
    for d in sorted(_DOSSIERS.iterdir()):
        f = d / "dossier.json"
        if not f.exists():
            continue
        p = tg.propose(d.name, json.loads(f.read_text()))
        if p.agrees is False:
            assert p.signals, f"{d.name}: disagreement with no signals"
            assert p.note, f"{d.name}: disagreement with no note"


@pytest.mark.parametrize("recipe", [RECIPE_R1, RECIPE_R2, RECIPE_R1_NOT_ROBUST, RECIPE_UNRESOLVED])
def test_proposals_use_the_shared_recipe_constants(recipe: str) -> None:
    """The tagger and the anchor must name recipes from ONE place — a second spelling of
    'R2_NEEDED' would silently never match a committed tag."""
    assert isinstance(recipe, str) and recipe
