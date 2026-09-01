"""(A2b persistence) THE FORM, AS IT LANDS IN THE WRITTEN ARTIFACT.

TESTED THROUGH `mech.ev_gap` ON THE COMMITTED JSON, NOT THROUGH THE FUNCTIONS. Six pure functions
had no production caller, and #316's positional swap — `multiple-dominant` silently becoming
`earnings` — survived precisely because unit tests hand a function the same wrong order a caller
would. These read what the refresh actually wrote.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.dossier.ev_gap import Route, build_ev_gap

ROOT = Path(__file__).resolve().parents[1]
NAMES = sorted(d.name for d in (ROOT / "data" / "dossiers").iterdir()
               if (d / "dossier.json").exists())
ROUTES = {Route.FULL, Route.TWO_RATIO, Route.PRICE_IMPLIED_ONLY}


def gap(ticker: str) -> dict | None:
    doc = json.loads((ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    return (doc.get("mechanical") or {}).get("ev_gap")


WRITTEN = [t for t in NAMES if gap(t) is not None]


#: SEALED names are exempt BY NAME, never by silence. A `known_wrong.json` sidecar states that the
#: record stays untouched until a re-assembly exists, and `refresh_dossier` now refuses them — so
#: their `ev_gap` is legitimately absent. Derived from the sidecar rather than hardcoded, so a name
#: that clears rejoins the population automatically instead of staying quietly exempt.
SEALED = [t for t in NAMES if (ROOT / "data" / "dossiers" / t / "known_wrong.json").exists()]


def test_the_refresh_reached_every_unsealed_name() -> None:
    """A NAME THE PASS SKIPPED IS INVISIBLE OTHERWISE. `None` means not-yet-refreshed and a written
    `status` means the refresh ran — so a partial pass looks identical to a name that legitimately
    cannot compute, unless the population is asserted."""
    expected = [t for t in NAMES if t not in SEALED]
    assert expected == WRITTEN, f"ev_gap missing on {sorted(set(expected) - set(WRITTEN))}"


def test_a_sealed_record_did_not_receive_the_form() -> None:
    """THE OTHER DIRECTION, and it is the one that actually failed. The A2b pass wrote `ev_gap`
    into FUBO's sealed `dossier.json`; the seal test caught it. Asserting the absence here means a
    future pass that writes through the seal reddens in A2b's own file too, next to the change that
    would cause it."""
    for t in SEALED:
        assert gap(t) is None, f"{t} is sealed by known_wrong.json but carries an ev_gap"


@pytest.mark.parametrize("ticker", WRITTEN)
def test_every_written_form_states_a_status_and_both_vintages(ticker: str) -> None:
    """BOTH VINTAGES ON EVERY NAME, computed or not. The TEV comes off the comps workbook and the
    consensus off the estimates workbook; one stamp over both would be the `financial_summary.as_of`
    defect — a block date over columns of two vintages."""
    g = gap(ticker)
    assert g is not None
    assert g["status"] in ("computed", "not-computed")
    assert set(g["vintages"]) == {"tev_as_of", "consensus_as_of"}


@pytest.mark.parametrize("ticker", WRITTEN)
def test_a_not_computed_form_always_says_why(ticker: str) -> None:
    """AN EMPTY BLOCK IS NOT AN ANSWER. The render ships before the refresh reaches every name, so
    a form without a reason would leave a page showing nothing with nothing saying why — the
    two-speed defect the insider horizon taught."""
    g = gap(ticker)
    assert g is not None
    if g["status"] == "not-computed":
        assert g.get("reason"), f"{ticker}: not-computed with no reason"


@pytest.mark.parametrize("ticker", WRITTEN)
def test_a_computed_form_carries_its_ratios_and_both_shape_labels(ticker: str) -> None:
    """The three ratios and BOTH labels. Structural only — the VALUES live on frozen fixtures, not
    on a living artifact that re-renders (the test-layer rule)."""
    g = gap(ticker)
    assert g is not None
    if g["status"] != "computed":
        return
    # TWO COMPUTED SHAPES SINCE THE R2 REVISION. A decomposed name carries all four ratios and a
    # label; a suppressed one carries the TOTAL ONLY and NO label — the total needs no consensus,
    # and a label would rank three ratios that were never struck.
    if (g.get("decomposition") or {}).get("status") == "suppressed":
        assert set(g["ratios"]) == {"ev_gap"}
        assert g["shape"] is None
        return
    assert set(g["ratios"]) == {"revenue_ratio", "margin_ratio", "multiple_ratio", "ev_gap"}
    shape = g["shape"]
    assert shape["anchor"], "a computed form with no anchor label"
    # AGREE IS TRISTATE. None means there was no adjacent year to check against — absent evidence,
    # not confirming evidence. Collapsing it to False would read as "the labels disagree".
    assert shape["agree"] in (True, False, None)
    if shape["adjacent"] is None:
        assert shape["agree"] is None, f"{g['shape']}: no adjacent year but agree is not None"


@pytest.mark.parametrize("ticker", WRITTEN)
def test_the_form_is_one_of_the_three_routes_whenever_an_anchor_exists(ticker: str) -> None:
    g = gap(ticker)
    assert g is not None
    if g.get("anchor_fy"):
        assert g["form"] in ROUTES, f"{ticker}: form {g['form']!r} is not a Route"


@pytest.mark.parametrize("ticker", WRITTEN)
def test_the_identity_holds_in_the_written_artifact(ticker: str) -> None:
    """THE PRODUCT IS THE GAP — re-checked on what was WRITTEN, not on what was computed. A
    serialization that dropped precision, or a transform that wrote one year's ratios beside
    another year's gap, would show up here and nowhere else."""
    g = gap(ticker)
    assert g is not None
    if g["status"] != "computed":
        return
    r = g["ratios"]
    if set(r) == {"ev_gap"}:          # suppressed: a total with no factors to multiply
        return
    product = r["revenue_ratio"] * r["margin_ratio"] * r["multiple_ratio"]
    assert product == pytest.approx(r["ev_gap"], rel=1e-9)


def test_a_ratio_recipe_states_its_total_and_suppresses_only_the_decomposition() -> None:
    """REVISED 2026-08-03 (operator). This test previously asserted a REFUSAL, and the refusal was
    over-broad: `our_EV / TEV` uses our leg and the market's price, so the TOTAL needs no consensus
    and was computable the whole time. Only the MARGIN comparison is horizon-mixed.

    Suppressing both withheld a clean statement because a different one was unavailable — and a
    test asserting the refusal held that in place, the same way #321's pin held the fabricated
    blend."""
    ratio_recipes = [t for t in WRITTEN
                     if str((gap(t) or {}).get("d_and_a_convention") or "").startswith("ratio")]
    if not ratio_recipes:
        pytest.skip("no committed R2 record in the corpus")
    for t in ratio_recipes:
        g = gap(t)
        assert g is not None and g["status"] == "computed", f"{t}: the total gap is withheld"
        assert isinstance(g["ratios"]["ev_gap"], float)
        d = g["decomposition"]
        assert d["status"] == "suppressed" and d["reason"]
        # THE MARGINS AS FIGURES, never a ratio — the ratio is the thing being refused.
        assert isinstance((d["margins"] or {})["ours"], float)
        assert "margin_ratio" not in g["ratios"]


def test_the_builder_always_returns_a_status_even_with_nothing_to_work_with() -> None:
    """NEGATIVE, at the builder. Every early return must still be a stated answer — an exception or
    a bare `{}` here becomes the empty block the render must never show."""
    out = build_ev_gap(None, None, tev=None, net_debt=None, shares=None,
                       tev_as_of=None, consensus_as_of=None)
    assert out["status"] == "not-computed" and out["reason"]
    assert set(out["vintages"]) == {"tev_as_of", "consensus_as_of"}


def test_a_floor_dated_consensus_vintage_is_carried_verbatim() -> None:
    """SMPL's estimates export has no As-Of header, so its date is a FLOOR (`≥`). Flattening that
    to a plain date would manufacture precision the workbook does not have — and the operator's
    own brief said "consensus from the 07-30 export", which the artifact cannot attest."""
    def cons(t: str) -> str:
        return str((gap(t) or {}).get("vintages", {}).get("consensus_as_of") or "")

    floors = [t for t in WRITTEN if cons(t).startswith("≥")]
    assert floors, "no floor-dated consensus vintage survived the write — the ≥ was flattened"


# --- THE TOTAL IS NEVER GATED ON CONSENSUS (review of #323) ------------------------------------

R2_LEG = {"revenue": 1000.0, "margin": 0.10, "margin_basis": "operating", "multiple": 10.0,
          "multiple_basis": "EV/EBITDA", "d_and_a": None, "d_and_a_ratio": 0.05,
          "d_and_a_convention": "ratio of revenue (R2, terminal)"}
R1_LEG = {**R2_LEG, "d_and_a": 50.0, "d_and_a_ratio": None,
          "d_and_a_convention": "fixed $M anchor (R1, mid-cycle)"}
#: Revenue at FY2026, EBITDA at FY2028 — both present, NO year in common, so no anchor exists.
NO_COMMON_ANCHOR = {
    "Revenue": [{"fy": "2026", "median": 900.0, "high": 950.0, "low": 880.0, "estimates": "8/8"}],
    "EBITDA": [{"fy": "2028", "median": 140.0, "high": 150.0, "low": 130.0, "estimates": "8/8"}]}


@pytest.mark.parametrize("leg", [R2_LEG, R1_LEG], ids=["r2-ratio", "r1-absolute"])
@pytest.mark.parametrize("levels", [None, {}, NO_COMMON_ANCHOR],
                         ids=["no-levels", "empty-levels", "no-common-anchor"])
def test_the_total_survives_an_absent_or_unanchorable_consensus(leg: dict, levels: dict) -> None:
    """THE SAME CONFLATION, ONE LEVEL UP — and the first fix moved it rather than removing it.

    `total_gap` reads OUR leg and TEV and nothing else, so a name whose consensus export is absent
    or has no common anchor still has a computable total. The first cut returned `not-computed`
    before the leg was even looked at, which withheld exactly the statement this design exists to
    state. Both leg shapes, because the defect was in the CONTROL FLOW, not in the R2 branch.
    """
    g = build_ev_gap(levels, leg, tev=1500.0, net_debt=200.0, shares=50.0,
                     tev_as_of="2026-07-24", consensus_as_of="2026-07-21")
    assert g["status"] == "computed", f"the total was withheld: {g.get('reason')!r}"
    assert g["ratios"]["ev_gap"] == pytest.approx(1.0)
    assert set(g["ratios"]) == {"ev_gap"}
    assert g["shape"] is None, "a shape label with no decomposition to rank"
    d = g["decomposition"]
    assert d["status"] == "suppressed"
    assert "the total gap stands on our leg and the market price alone" in d["reason"]


def test_an_absent_consensus_is_a_different_reason_from_thin_coverage() -> None:
    """"Coverage below the floor" implies a consensus was READ and found thin. With no consensus at
    all that sentence is false — a third state, named separately."""
    g = build_ev_gap(None, R2_LEG, tev=1500.0, net_debt=200.0, shares=50.0,
                     tev_as_of=None, consensus_as_of=None)
    why = g["decomposition"]["reason"]
    assert "no consensus levels are persisted" in why
    assert "below the floor" not in why and "TERMINAL" not in why


def test_a_leg_that_cannot_convert_is_still_refused() -> None:
    """NEGATIVE CONTROL. Removing the consensus gate must not make everything computable: a leg
    with NEITHER an absolute D&A nor a ratio cannot produce our EBITDA at all, and that is a real
    refusal rather than a suppression."""
    broken = {**R2_LEG, "d_and_a": None, "d_and_a_ratio": None}
    g = build_ev_gap(None, broken, tev=1500.0, net_debt=200.0, shares=50.0,
                     tev_as_of=None, consensus_as_of=None)
    assert g["status"] == "not-computed"
    assert "neither an absolute nor a ratio" in g["reason"]


def test_no_leg_and_no_consensus_says_so_rather_than_naming_only_one() -> None:
    """Both halves missing is its own state; reporting "the route is known" would be false."""
    g = build_ev_gap(None, None, tev=None, net_debt=None, shares=None,
                     tev_as_of=None, consensus_as_of=None)
    assert g["status"] == "not-computed"
    assert "neither side of the comparison exists" in g["reason"]


def test_a_forward_pe_leg_is_refused_with_a_reason_rather_than_crashing() -> None:
    """REVIEW FIX (R3). `our_ebitda` is revenue × margin; a forward-P/E leg values a share as
    EPS × multiple and carries NEITHER, so `total_gap`'s `float(leg["revenue"])` reached
    `float(None)` and raised TypeError — unhandled inside `ev_gap_transform`, which would take
    down `refresh_dossier` for the whole name. It is masked on GOOGL today only because that
    record states no `diluted_shares` and is refused one line earlier; a share count on any R3
    record un-masks it. Every other missing input here yields a stated `not-computed`, and so
    must this one.
    """
    from vinci.dossier.refresh import _base_leg

    r3 = {**R2_LEG, "revenue": None, "margin": None, "multiple_basis": "P/E"}
    g = build_ev_gap(None, r3, tev=1500.0, net_debt=200.0, shares=50.0,
                     tev_as_of=None, consensus_as_of=None)
    assert g["status"] == "not-computed"
    assert "no revenue and margin" in g["reason"], g["reason"]
    # NOT A SYNTHETIC SHAPE: the committed R3 record really produces it through the same reader
    # `ev_gap_transform` uses. (Skipped if the record is not committed on this checkout.)
    leg = _base_leg("GOOGL")
    if leg is not None:
        assert leg["revenue"] is None and leg["margin"] is None, leg
        live = build_ev_gap(None, leg, tev=1500.0, net_debt=200.0, shares=50.0,
                            tev_as_of=None, consensus_as_of=None)
        assert live["status"] == "not-computed" and "no revenue and margin" in live["reason"]
