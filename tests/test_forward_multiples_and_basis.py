"""A multiple must name the denominator it is struck on.

BOTH fixes answer one measured failure. A real BURL underwrite, built on this dossier, reported
ZERO multiple change between entry and exit while its entry multiple sat on FY+1 and its exit on
FY+2. Rebuilt on one basis the same return is roughly half denominator roll and half re-rating:
the Base price is unchanged, its explanation is not.

WHY THE DOSSIER WAS COMPLICIT. It published only TRAILING multiples — `P/LTM EPS`,
`EV/EBITDA (TEV/LTM)` — while every underwrite runs on forward earnings, so the analyst sourced
"~22.1x forward P/E" externally, with no stated denominator. At the dossier's own price that number
is P/FY27E (GAAP) 22.37x, and P/FY28E is 18.78x — a three-turn gap reported as zero.

AND THE SECOND, SEPARATE BASIS: the EV/EBITDA series implies a 19.3% EBITDA margin against 11%
reported. That is not corrupt data — the ~$991M gap on $12.2B of revenue is the order of annual
rent, i.e. the series is struck on something like EBITDAR — which is exactly why this DISCLOSES
rather than disqualifies. VITL, whose 5.01x really is incoherent, already fails the coherence
guard and never reaches here.
"""

from __future__ import annotations

import json
import pathlib

from vinci.dossier import render as rend
from vinci.dossier.ciq_sheets import forward_multiples
from vinci.dossier.schemas import Dossier, FinRow, FinTable, SourceStatus

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = pathlib.Path("/Users/work/Documents/GitHub/mosaic-theory-ta/data/dossiers")


def _table(**over: object) -> FinTable:
    base: dict[str, object] = {
        "columns": ["FY25", "LTM", "FY27E", "FY28E"],
        "is_estimate": [False, False, True, True],
        "rows": [FinRow(label="EPS (Normalized)", cells=["6.73", "8.95", "11.80", "13.68"],
                        values=[6.73, 8.95, 11.8, 13.68]),
                 FinRow(label="EPS (GAAP, dil.)", cells=["7.80", "11.13", "11.48", "13.40"],
                        values=[7.80, 11.13, 11.48, 13.40])]}
    base.update(over)
    return FinTable(**base)  # type: ignore[arg-type]


# --- fix 1: forward multiples name their denominator -------------------------------------------

def test_a_forward_multiple_names_the_cell_it_came_from() -> None:
    """(+) THE WHOLE POINT. Column and EPS row travel with the number, so two multiples can never
    be silently compared across different periods."""
    got = forward_multiples(_table(), price=256.85, price_as_of="2026-09-22")
    assert got.status is SourceStatus.PRESENT
    by = {fm.label: fm for fm in got.value or []}
    assert set(by) == {"P/FY27E (normalized)", "P/FY27E (GAAP)",
                       "P/FY28E (normalized)", "P/FY28E (GAAP)"}
    fy27 = by["P/FY27E (normalized)"]
    assert fy27.column == "FY27E" and fy27.eps_basis == "EPS (Normalized)"
    assert round(fy27.multiple, 2) == 21.77 and fy27.eps == 11.8
    assert fy27.price == 256.85 and fy27.price_as_of == "2026-09-22"


def test_the_gap_that_was_reported_as_zero_is_now_visible() -> None:
    """(+) The external "~22.1x forward" the underwrite used is P/FY+1; P/FY+2 is three turns
    lower. Publishing both is what makes the difference impossible to miss."""
    by = {fm.label: fm.multiple for fm in
          (forward_multiples(_table(), price=256.85).value or [])}
    assert round(by["P/FY27E (GAAP)"], 1) == 22.4, "this is the number sourced externally"
    assert round(by["P/FY28E (normalized)"], 1) == 18.8
    assert by["P/FY27E (GAAP)"] - by["P/FY28E (normalized)"] > 3.0


def test_estimate_columns_come_from_the_flag_not_the_label() -> None:
    """(-) DISPLAY FORMATTING IS NEVER LOAD-BEARING. The 'E' suffix is a rendering convention; the
    structured mask is the fact. A table whose labels lack 'E' must still strike its estimates."""
    got = forward_multiples(_table(columns=["FY25", "LTM", "2027", "2028"]), price=256.85)
    assert got.status is SourceStatus.PRESENT
    assert {fm.column for fm in got.value or []} == {"2027", "2028"}


def test_no_price_is_unknown_and_not_a_guess() -> None:
    """(-) A multiple whose numerator is unstated is the defect, not the fix."""
    for px in (None, 0.0, -1.0):
        got = forward_multiples(_table(), price=px)  # type: ignore[arg-type]
        assert got.status is SourceStatus.UNKNOWN and got.value is None


def test_a_table_with_no_estimate_column_yields_nothing() -> None:
    """(-) Nothing forward to strike — UNKNOWN, never a trailing multiple relabelled as forward."""
    got = forward_multiples(_table(is_estimate=[False] * 4), price=256.85)
    assert got.status is SourceStatus.UNKNOWN and "no estimate column" in (got.note or "")


def test_a_negative_forward_eps_is_skipped_not_published() -> None:
    """(-) A P/E on negative earnings is meaningless; publishing one would be a fabricated level."""
    t = _table(rows=[FinRow(label="EPS (Normalized)", cells=["1", "1", "-2.00", "13.68"],
                            values=[1.0, 1.0, -2.0, 13.68])])
    cols = {fm.column for fm in (forward_multiples(t, price=256.85).value or [])}
    assert cols == {"FY28E"}, "the loss-making estimate column must not produce a multiple"


def test_a_dossier_predating_the_field_renders_unchanged() -> None:
    """(-) Every committed dossier is in that state; the row must simply not appear."""
    assert rend._forward_multiples_md(None) == ""


# --- fix 2: the multiple's own basis, disclosed not disqualified --------------------------------

def _dossier(t: str) -> Dossier:
    return Dossier.model_validate(json.loads((CORPUS / t / "dossier.json").read_text()))


def test_burl_states_that_its_ev_ebitda_is_not_reported_ebitda() -> None:
    """(+) CORPUS, the name the failure was measured on. The line must give BOTH margins and the
    restated level, because "9.0x, 8th percentile, near-floor" is unreadable without them."""
    if not (CORPUS / "BURL").is_dir():
        return
    line = rend._multiple_basis_md(_dossier("BURL").mechanical)
    assert line, "BURL's series implies 19.3% against 11% reported — it must say so"
    assert "19.3%" in line and "11%" in line
    assert "NOT the reported EBITDA" in line
    assert "15.8x" in line, "the restated level is what makes 9.0x readable"


def test_it_is_silent_where_the_two_bases_agree() -> None:
    """(-) NOT A BANNER ON EVERY PAGE. Most names' implied and reported margins differ only by the
    rounding of a whole-percent cell; a line there would be noise that trains the reader to skip
    it — and then it is not there when it matters."""
    if not (CORPUS / "GOOGL").is_dir():
        return
    assert rend._multiple_basis_md(_dossier("GOOGL").mechanical) == ""


def test_it_discloses_rather_than_disqualifies() -> None:
    """(-) THE DESIGN CHOICE, PINNED. BURL's band is coherent — the gap is the order of its annual
    rent, i.e. an EBITDAR-like series — so the anchor must survive. Tightening the coherence bound
    instead would have thrown it away, which is VITL's treatment and wrong here."""
    if not (CORPUS / "BURL").is_dir():
        return
    m = _dossier("BURL").mechanical
    oh = m.valuation.own_history if m.valuation else None
    assert oh is not None and oh.status is SourceStatus.PRESENT
    band = next(b for b in (oh.value or []) if "EBITDA" in str(b.metric))
    assert band.data_quality is None, (
        "the band must stay USABLE — this is a disclosure, not a coherence failure")
