"""The ACTUAL and ESTIMATE EBITDA rows do not share a basis, and now the page says so.

THE SEVENTH SIGHTING of the basis-mistranslation class, and the first measured fleet-wide instead
of caught on one name. The annual financial summary fuses CIQ Financials ACTUALS with Estimates
CONSENSUS into ONE table, so `EBITDA ($M)` reads left-to-right across a boundary where the
definition changes and nothing said so.

UBER IS THE PROVING CASE, verified against the primary source rather than assumed: the actual row
equals EDGAR `OperatingIncomeLoss + DepreciationDepletionAndAmortization` to the dollar for FY21-25
(-2,932 / -885 / 1,933 / 3,510 / 6,284 against CIQ's -2,932 / -885 / 1,933 / 3,536 / 6,312), so it
is GAAP EBITDA with SBC expensed. The consensus row implies 2,874 of D&A against ~747 in the
actuals — a gap that is Uber's ~1,826 of stock-based compensation. A growth read across that
boundary is part arithmetic and part definition.

IT IS NOT A UBER QUIRK. Measured across the committed fleet when written: VITL 5.38x, UBER 4.01x,
MVST 2.93x, AORT 2.65x flagged high, NCNO 0.25x flagged low (its estimates add back LESS), against
CNXC/EPAM/SMPL/VRRM consistent. Seven of eleven names carry a step; four do not.
"""
from __future__ import annotations

import json
import pathlib
import statistics

import pytest

from vinci.dossier.ebitda_basis import FLAG_HIGH, FLAG_LOW, read_basis
from vinci.dossier.schemas import FinRow, FinTable

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _table(ebitda: list[float | None], ebit: list[float | None],
           is_estimate: list[bool]) -> FinTable:
    """A minimal annual table built from the REAL type, never a hand-rolled stand-in — a fixture
    shaped to what the test needs would dictate the production signature (#305)."""
    return FinTable(
        columns=[f"C{i}" for i in range(len(is_estimate))],
        rows=[FinRow(label="EBITDA ($M)", cells=[], values=ebitda),
              FinRow(label="EBIT ($M)", cells=[], values=ebit)],
        is_estimate=is_estimate,
    )


# ---------------------------------------------------------------- the divergent case


def test_an_sbc_addback_in_the_estimates_is_caught() -> None:
    """UBER'S SHAPE, in round numbers: actuals imply ~750 of D&A, estimates imply ~2,850 because
    the consensus EBITDA adds SBC back and the consensus EBIT does not."""
    b = read_basis(_table(ebitda=[6312.0, 7474.0, 11396.0],
                          ebit=[5565.0, 6727.0, 8522.0],
                          is_estimate=[False, False, True]))
    assert b.divergent, b.note
    assert b.actual_implied_dna == pytest.approx(747.0)
    assert b.estimate_implied_dna == pytest.approx(2874.0)
    assert b.ratio == pytest.approx(2874.0 / 747.0)
    assert "NOT the same basis" in b.note
    assert "trailing multiple" in b.note, (
        "the note states the arithmetic but not the consequence — a reader has to be told not to "
        "compare a trailing multiple off one row with a forward multiple off the other")


def test_the_inverse_case_is_caught_too() -> None:
    """NCNO'S SHAPE — the estimates add back LESS than the actuals. A one-sided test would report
    it as agreement, which is the `ratio >= 2` mistake #253 already paid for once."""
    b = read_basis(_table(ebitda=[122.0, 175.0], ebit=[100.0, 169.0], is_estimate=[False, True]))
    assert b.ratio is not None and b.ratio < FLAG_LOW
    assert b.divergent and "LESS" in b.note


def test_a_consistent_name_is_not_flagged() -> None:
    """THE NEGATIVE PIN. SMPL/CNXC's shape: implied D&A barely moves, so both rows read as the same
    basis and nothing is printed. A guard that fires on everything is a freeze."""
    b = read_basis(_table(ebitda=[319.0, 245.0], ebit=[300.0, 223.0], is_estimate=[False, True]))
    assert not b.divergent
    assert b.ratio is not None and FLAG_LOW < b.ratio < FLAG_HIGH
    assert "consistent" in b.note


@pytest.mark.parametrize("ratio", [FLAG_HIGH, FLAG_LOW])
def test_the_threshold_is_a_boundary_not_a_range(ratio: float) -> None:
    """Exactly AT the bound flags — `>=` / `<=`, pinned so a silent flip to a strict comparison
    cannot quietly stop reporting the boundary names."""
    b = read_basis(_table(ebitda=[1100.0, 1000.0 + 100.0 * ratio],
                          ebit=[1000.0, 1000.0], is_estimate=[False, True]))
    assert b.ratio == pytest.approx(ratio)
    assert b.divergent


# ---------------------------------------------------------------- what it must REFUSE to guess


def test_a_missing_ebit_row_says_so_rather_than_reading_as_agreement() -> None:
    """ABSENT IS NOT CONSISTENT. Without EBIT there is no implied D&A, and returning an un-flagged
    result would be indistinguishable from a checked-and-clean name."""
    t = FinTable(columns=["C0", "C1"],
                 rows=[FinRow(label="EBITDA ($M)", cells=[], values=[100.0, 200.0])],
                 is_estimate=[False, True])
    b = read_basis(t)
    assert not b.divergent and b.ratio is None
    assert "EBIT ($M) absent" in b.note


def test_no_estimate_column_says_so() -> None:
    """A table with no consensus columns has no boundary to measure across."""
    b = read_basis(_table(ebitda=[100.0, 110.0], ebit=[90.0, 99.0], is_estimate=[False, False]))
    assert not b.divergent and b.ratio is None
    assert "nothing to compare across the boundary" in b.note


def test_a_table_with_no_estimate_flags_is_not_checkable() -> None:
    """Pre-P3 JSON round-trips with `is_estimate=[]`; that is unknown, not agreement."""
    b = read_basis(_table(ebitda=[100.0], ebit=[90.0], is_estimate=[]))
    assert not b.divergent and "not checkable" in b.note


def test_a_column_missing_one_leg_is_skipped_not_zeroed() -> None:
    """A None EBIT must not read as EBITDA − 0 = all-of-EBITDA-is-D&A, which would drag the median
    and could flip a real divergence into apparent agreement."""
    b = read_basis(_table(ebitda=[1000.0, None, 1000.0], ebit=[900.0, 500.0, None],
                          is_estimate=[False, False, True]))
    assert b.actual_implied_dna == pytest.approx(100.0), "the None-EBITDA column leaked in"
    assert b.ratio is None and "no estimate column" in b.note


def test_a_zero_actual_implied_dna_does_not_divide_by_zero() -> None:
    b = read_basis(_table(ebitda=[100.0, 300.0], ebit=[100.0, 200.0], is_estimate=[False, True]))
    assert b.ratio is None and not b.divergent
    assert "divide by it" in b.note and b.estimate_implied_dna == pytest.approx(100.0)


def test_every_branch_states_a_reason() -> None:
    """NO SILENT BLANK. Each refusal path must say why, because "not flagged" and "not checked"
    are different claims and a blank note cannot distinguish them."""
    for t in (_table([100.0], [90.0], []),
              FinTable(columns=["C0"], rows=[], is_estimate=[False]),
              _table([100.0, 110.0], [90.0, 99.0], [False, False])):
        assert read_basis(t).note.strip(), "a branch returned an empty note"


# ---------------------------------------------------------------- the LIVE committed corpus


def test_the_committed_fleet_splits_into_flagged_and_clean() -> None:
    """CORPUS BEFORE SYNTHETIC. The pins above run on constructed tables; this one runs on every
    committed dossier, so the check is proved able to FIND something and to stay quiet on names
    where there is nothing to find. A check that flags all or none is not measuring."""
    flagged, clean, skipped = [], [], []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        d = json.loads(p.read_text())
        ann = ((d.get("mechanical") or {}).get("financial_summary") or {}).get("annual") or {}
        v = ann.get("value")
        if not isinstance(v, dict) or not v.get("rows"):
            skipped.append(p.parent.name)
            continue
        rows = {r.get("label"): (r.get("values") or []) for r in v["rows"]}
        eb, ei = rows.get("EBITDA ($M)") or [], rows.get("EBIT ($M)") or []
        flags = v.get("is_estimate") or []
        act, est = [], []
        for a, b, e in zip(eb, ei, flags, strict=False):
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                (est if bool(e) else act).append(a - b)
        if not act or not est or statistics.median(act) == 0:
            skipped.append(p.parent.name)
            continue
        r = statistics.median(est) / statistics.median(act)
        (flagged if (r >= FLAG_HIGH or r <= FLAG_LOW) else clean).append(p.parent.name)

    assert flagged, (
        "NO committed name shows an actual-vs-estimate EBITDA basis step. Either every CIQ export "
        "now agrees across the boundary — a real win, re-measure and move this pin to a fixture — "
        "or the rows stopped resolving and this check has gone vacuous.")
    assert clean, (
        f"EVERY committed name is flagged ({flagged}) — a guard that fires on the whole fleet is "
        "not discriminating; check the thresholds against the measured distribution before "
        "trusting any individual flag.")
