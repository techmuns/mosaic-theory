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
    product = r["revenue_ratio"] * r["margin_ratio"] * r["multiple_ratio"]
    assert product == pytest.approx(r["ev_gap"], rel=1e-9)


def test_a_ratio_recipe_refuses_by_naming_the_convention_not_the_absence() -> None:
    """THE R2 CASE, and the message matters as much as the refusal. AORT/MVST/NCNO store D&A as a
    RATIO OF REVENUE; converting it at the anchor is the reserved analyst decision (operator,
    2026-07-30: "it moves committed numbers and is a decision, not a build"). "No D&A available"
    would send a reader looking for a number that is already in the record."""
    ratio_recipes = [t for t in WRITTEN
                     # A dict `.get` DEFAULT never fires when the key exists carrying None, and
                     # `d_and_a_convention` is written as None for every name without a record.
                     if str((gap(t) or {}).get("d_and_a_convention") or "").startswith("ratio")]
    if not ratio_recipes:
        pytest.skip("no committed R2 record in the corpus")
    for t in ratio_recipes:
        g = gap(t)
        assert g is not None and g["status"] == "not-computed"
        assert "RATIO OF REVENUE" in g["reason"], f"{t}: refusal does not name the convention"
        assert "analyst decision" in g["reason"]


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
