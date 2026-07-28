"""MATERIALITY GUARD (P1, IC audit 2026-07-28) — a one-off too big to go unmentioned.

ACCEPTANCE (operator policy 2026-07-28): every audit-derived build ships a fixture that FAILS on
`2facc5e` and PASSES after. On 2facc5e `vinci.dossier.materiality` does not exist, so every test
here errors at import — the required red. Suite-green-unchanged is not evidence of a fix.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.materiality import (
    MCAP_FRACTION,
    MaterialityError,
    MaterialityUnavailableError,
    check_materiality,
    scan_material_lines,
    unusual_items_block,
)

ROOT = Path(__file__).resolve().parents[1]

# The SMPL shape, reduced to its bones: a curated table that omits the line, an unusual-items block
# that carries it, and a synthesis that never says the number. Market cap 909.4; the writedown at
# -391.9 is 43% of it. A fixture, not the living record — the living one is checked separately by
# an invariant, because analyst re-underwrites legitimately move its numbers.
def _sheet(writedown: float | str) -> list[list[Any]]:
    return [
        ["Fiscal Period", "FY2024", "FY2025", "LTM"],
        ["Revenue", 1401.6, 1450.9, 1392.0],
        ["Cost Of Goods Sold", 900.0, 920.0, 929.0],       # recurring + huge: must NOT fire
        ["EBT Excl. Unusual Items", 175.6, 150.6, 80.1],
        ["Restructuring Charges", "-", "-", -2.4],          # small: must not fire
        ["Asset Writedown", "-", -60.9, writedown],
        ["EBT Incl. Unusual Items", 175.6, 80.8, -311.8],
        ["Filing Date", 46000, 46100, 46212],               # a DATE SERIAL outside the block
    ]

_CURATED = {"Revenue ($M)", "EBITDA ($M)", "EBIT ($M)", "Net income ($M)", "FCF ($M)"}
_LTM_COL = 3


def test_the_audited_defect_raises() -> None:
    """THE ACCEPTANCE FIXTURE. A writedown at 43% of market cap, in neither the curated summary nor
    the synthesis — exactly SMPL's shape on 2026-07-24 — must fail the build loudly."""
    with pytest.raises(MaterialityError, match="material UNUSUAL ITEM"):
        check_materiality(_sheet(-391.9), _LTM_COL, market_cap=909.4, revenue=None,
                          summary_labels=_CURATED,
                          synthesis_text="the bear case cites a $60.9M Atkins impairment",
                          ticker="FIXTURE")


def test_eleven_percent_of_market_cap_is_over_the_line() -> None:
    """The audit's own acceptance test, verbatim: a writedown at 11% of market cap raises; the
    threshold is a floor, not an approximation."""
    over, under = -(909.4 * 0.11), -(909.4 * 0.09)
    with pytest.raises(MaterialityError):
        check_materiality(_sheet(over), _LTM_COL, market_cap=909.4, revenue=None,
                          summary_labels=_CURATED, synthesis_text="", ticker="FIXTURE")
    check_materiality(_sheet(under), _LTM_COL, market_cap=909.4, revenue=None,
                      summary_labels=_CURATED, synthesis_text="", ticker="FIXTURE")
    assert MCAP_FRACTION == 0.10


def test_either_satisfying_route_silences_it() -> None:
    """Two routes reach the reader and either suffices — data or argument. The guard requires
    VISIBILITY, not a particular tier."""
    # (a) surfaced as DATA in the curated summary
    check_materiality(_sheet(-391.9), _LTM_COL, market_cap=909.4, revenue=None,
                      summary_labels={*_CURATED, "Asset Writedown ($M)"},
                      synthesis_text="", ticker="FIXTURE")
    # (b) argued in the synthesis — matched on the MAGNITUDE, since prose names the number, not
    # the sheet's row label
    check_materiality(_sheet(-391.9), _LTM_COL, market_cap=909.4, revenue=None,
                      summary_labels=_CURATED,
                      synthesis_text="management wrote down $391.9M across the brand portfolio",
                      ticker="FIXTURE")


def test_recurring_operating_lines_and_date_serials_never_fire() -> None:
    """THE NEGATIVE PIN, and the reason the audit's stated fix was not implemented literally.
    Scanning every income-statement line fired on TWELVE for SMPL — Cost Of Goods Sold at 102% of
    market cap, share counts compared against dollars, and `Filing Date` 46,212 (an Excel date
    serial) at 5082%. A guard that fires on the filing date is switched off within a week."""
    rows = _sheet(-391.9)
    lo, hi = unusual_items_block(rows)
    scanned = {ln.label for ln in scan_material_lines(rows[lo:hi], _LTM_COL,
                                                      market_cap=909.4, revenue=None)}
    assert scanned == {"Asset Writedown"}, scanned
    assert "Cost Of Goods Sold" not in scanned and "Filing Date" not in scanned


def test_a_sheet_without_the_block_refuses_to_report_a_clean_pass() -> None:
    """Fail loud, never fail quiet: a guard that cannot find its rows must not return 'nothing
    material found' — that is indistinguishable from a clean record and worse than a gap."""
    with pytest.raises(MaterialityUnavailableError, match="cannot run"):
        unusual_items_block([["Fiscal Period", "LTM"], ["Revenue", 1392.0]])


def test_no_denominator_is_a_silent_pass_by_design() -> None:
    """A threshold with no denominator is not a test. Inventing a market cap to have something to
    divide by would be the fabrication the repo refuses; the missing market cap fails loud on its
    own path, and stacking a second failure on one cause buries the first."""
    assert scan_material_lines(_sheet(-391.9), _LTM_COL, market_cap=None, revenue=None) == []


def test_every_committed_bundle_has_a_locatable_block() -> None:
    """The block delimiters are the guard's only structural assumption — pin it against the real
    committed corpus so a CIQ export-format change reddens here, not in a silent skip."""
    from vinci.dossier.ciq import CiqBundle

    man = ROOT / "data" / "manual" / "ciq"
    if not man.is_dir():
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    seen = 0
    for d in sorted(man.iterdir()):
        if not d.is_dir():
            continue
        try:
            inc = CiqBundle.from_files(d.name, sorted(d.glob("*"))).sheet(
                "financials", "Income Statement", freq="annual")
        except Exception:
            continue
        lo, hi = unusual_items_block(inc)      # raises if a bundle lost its delimiters
        assert hi > lo
        seen += 1
    assert seen >= 5, f"expected the committed bundle corpus, saw {seen}"


def test_material_unusual_items_reach_the_committed_record() -> None:
    """E2E on the ARTIFACT, conditional so a re-underwrite cannot redden it: IF a committed
    dossier's annual summary carries an unusual-item row, its value is structured (charts consume
    values, never re-parsed display strings). SMPL and CNXC are the two names the guard fires on;
    both must surface their line as DATA once re-assembled."""
    for t in ("SMPL", "CNXC"):
        f = ROOT / "data" / "dossiers" / t / "dossier.json"
        if not f.exists():
            continue
        ann = (json.loads(f.read_text()).get("mechanical") or {}).get(
            "financial_summary", {}).get("annual") or {}
        rows = (ann.get("value", ann) or {}).get("rows") or []
        for r in rows:
            if any(k in r["label"].lower() for k in ("writedown", "impairment", "restructuring")):
                assert r.get("values"), f"{t}: {r['label']} carries no structured values"
