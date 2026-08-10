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
    """THE NEGATIVE PIN. SMPL/CNXC's shape: implied D&A barely moves, so nothing is flagged. A
    guard that fires on everything is a freeze.

    THE NOTE NO LONGER SAYS "consistent" — see the pin below. Not-detected is not agreement, and
    this function cannot support the stronger claim."""
    b = read_basis(_table(ebitda=[319.0, 245.0], ebit=[300.0, 223.0], is_estimate=[False, True]))
    assert not b.divergent
    assert b.ratio is not None and FLAG_LOW < b.ratio < FLAG_HIGH
    assert "NO DIVERGENCE WAS DETECTED" in b.note


def test_the_unflagged_branch_never_claims_the_rows_share_a_basis() -> None:
    """THE DEFECT BRBR EXPOSED, and it is wording rather than arithmetic. The un-flagged note read
    "consistent, so both EBITDA rows read as the same basis" — an affirmative claim this function
    cannot support: it tests ONE PROXY against ONE THRESHOLD, so a step under the bar is a
    measurement that came back low, never a finding of sameness. Declared-vs-enforced, in the one
    place a reader goes to CHECK basis."""
    b = read_basis(_table(ebitda=[319.0, 245.0], ebit=[300.0, 223.0], is_estimate=[False, True]))
    assert "consistent" not in b.note, b.note
    assert "same basis" not in b.note, b.note
    assert "not a finding that the rows share a basis" in b.note


def test_a_ratio_inside_the_observed_blind_band_says_so_on_the_page() -> None:
    """BRBR'S SHAPE at 1.73x: below the 2.0x flag, and its rows genuinely differ — FY25 EBITDA
    reads 376 against a REPORTED ADJUSTED 481.6, and FY26E 288.1 matches management's ADJUSTED
    guidance of 275-295. The threshold is deliberately NOT lowered (that would be tuning to the
    instance); instead a reader standing in the band is told they are in it."""
    b = read_basis(_table(ebitda=[400.0, 330.0], ebit=[376.0, 289.0], is_estimate=[False, True]))
    assert b.ratio is not None and 1.5 <= b.ratio < FLAG_HIGH, b.ratio
    assert not b.divergent
    assert "BAND WHERE A REAL BASIS CHANGE HAS BEEN OBSERVED" in b.note
    assert "UNRESOLVED" in b.note


def test_a_low_ratio_outside_the_band_is_not_given_the_band_warning() -> None:
    """THE NEGATIVE HALF. SMPL sits at 1.19x and VRRM at 1.32x — under the band, and a warning on
    every un-flagged name is the freeze the threshold exists to avoid."""
    b = read_basis(_table(ebitda=[319.0, 245.0], ebit=[300.0, 223.0], is_estimate=[False, True]))
    assert b.ratio is not None and b.ratio < 1.5
    assert "BAND WHERE" not in b.note, b.note


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


def test_an_absent_annual_table_is_not_checkable() -> None:
    """REVIEW FINDING. `Sourced[FinTable].value` is None whenever the annual table is
    UNKNOWN/MISSING, and a name whose financials did not resolve still gets a dossier — so None is
    an EXPECTED input, not a defensive check. The first cut typed the parameter `Any`, so this case
    was never surfaced and an un-resolved name would have read as "checked, nothing found"."""
    b = read_basis(None)
    assert not b.divergent and b.ratio is None
    assert "no annual table" in b.note


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


def test_the_web_twin_exists_and_emits_only_real_css_classes() -> None:
    """REVIEW FINDING — the markdown twin had a pin and the WEB twin had none, so `ebitdaBasisNote`
    could be deleted and only the printed page would notice.

    A CLASS THAT DOES NOT EXIST FAILS SILENTLY: the block renders unstyled rather than erroring, and
    the markdown preview cannot show it because markdown has no classes. This build nearly shipped
    exactly that — the first cut emitted `ds-caveat`, which has no rule anywhere; it was caught by
    hand, which is precisely the thing a pin exists to stop relying on. Same shape and scope as
    `test_capital_allocation`'s class pin, applied to the function this PR adds."""
    import re

    js = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    css = (ROOT / "frontend" / "assets" / "styles.css").read_text()
    assert "function ebitdaBasisNote(m) {" in js, (
        "the web twin is gone — the printed page would still carry the basis caveat while the "
        "served page silently dropped it, which is the md↔web parity class")
    assert "ebitdaBasisNote(m)" in js[js.index("function financialSnapshot(m) {"):], (
        "ebitdaBasisNote is defined but financialSnapshot no longer calls it — a helper nobody "
        "invokes is the shape a helper-level pin stays green through")

    body = js[js.index("function ebitdaBasisNote(m) {"):]
    body = body[:body.index("\nfunction ")]
    emitted = {c for attr in re.findall(r'class="([^"$]+)"', body) for c in attr.split()}
    assert emitted, "no classes found — the extraction is wrong, not the markup"
    missing = sorted(c for c in emitted if not re.search(rf"\.{re.escape(c)}\b", css))
    assert not missing, (
        f"the web twin emits CSS classes with no rule in styles.css: {missing}. They fail "
        "silently — the block renders unstyled and the markdown preview cannot show it.")


def test_the_web_twin_gates_on_the_structured_flag_not_the_prose() -> None:
    """Both renderers must read `divergent`, never sniff `note` — the display-formatting-is-never-
    load-bearing rule. A twin keyed off the sentence drifts the moment the wording moves."""
    js = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    body = js[js.index("function ebitdaBasisNote(m) {"):]
    body = body[:body.index("\nfunction ")]
    assert "divergent" in body, "the web twin does not read the structured flag"
    assert "ebitda_basis" in body, "the web twin does not read the structured block"


def test_the_transform_writes_the_block_from_the_stored_json_alone() -> None:
    """THE BACK-FILL PATH. Six committed names carry a step and none of their pages said so;
    re-assembling to land a DETERMINISTIC block would reroll six syntheses. This transform reads
    NOTHING outside the artifact — the annual table already holds both rows and the flags."""
    from vinci.dossier.refresh import ebitda_basis_transform

    mech = {"financial_summary": {"annual": {"value": {
        "columns": ["FY25", "FY26E"],
        "rows": [{"label": "EBITDA ($M)", "cells": ["", ""], "values": [6312.0, 11396.0]},
                 {"label": "EBIT ($M)", "cells": ["", ""], "values": [5565.0, 8522.0]}],
        "is_estimate": [False, True]}}}}
    out = ebitda_basis_transform()(mech)

    b = out["financial_summary"]["ebitda_basis"]
    assert b["divergent"] is True and b["ratio"] == pytest.approx(2874.0 / 747.0)
    assert mech["financial_summary"].get("ebitda_basis") is None, (
        "the transform mutated its input — `refresh_dossier` re-reads the original on refusal")


def test_the_transform_always_writes_a_reason_even_when_it_cannot_compute() -> None:
    """ABSENT means NOT YET REFRESHED and must keep that meaning, so a build the check cannot read
    still gets a block that SAYS SO rather than no key at all."""
    from vinci.dossier.refresh import ebitda_basis_transform

    out = ebitda_basis_transform()({"financial_summary": {"annual": {"value": None}}})
    b = out["financial_summary"]["ebitda_basis"]
    assert b["divergent"] is False and b["note"].strip()
    # ...and a build with no appendix at all is left completely alone
    assert ebitda_basis_transform()({"stock_info": {"x": 1}}) == {"stock_info": {"x": 1}}


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
