"""`forward_consensus.pe_eps_basis` — which consensus EPS line CIQ strikes the forward P/E on.

CIQ picks the line per company and the sheet never says which: AMZN's P/E is struck on GAAP EPS
and GOOGL's on normalized. An R3 underwrite multiplying normalized EPS by a GAAP-struck multiple
mixes two bases (AMZN FY2028: GAAP $14.11 against normalized $13.27). The test needs no price — P/E
× EPS IS the price, so on the struck line it is one number in every FY row.

The pins run on frozen DERIVED values (`tests/fixtures/pe_eps_basis_cases.json`: each case's P/E
rows and Current consensus per line, the figures every page already commits), so they gate in CI
without the workbooks. The reader pin compares the live read against them where the export is on
disk.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES: dict[str, dict[str, Any]] = json.loads(
    (ROOT / "tests" / "fixtures" / "pe_eps_basis_cases.json").read_text())["cases"]


def _run(case: dict[str, Any], **override: Any) -> Any:
    args = {"pe": case["pe"], "eps": case["eps"], "fy_periods": case["fy_periods"],
            "quarters": case["quarters"], **override}
    pe = args.pop("pe")
    eps = args.pop("eps")
    return cs.pe_eps_basis(pe, eps, **args)


# --- every outcome, on real exports ------------------------------------------------------------

@pytest.mark.parametrize("ticker", sorted(CASES))
def test_each_case_names_what_its_export_shows(ticker: str) -> None:
    case = CASES[ticker]
    got = _run(case)
    assert got is not None
    assert (got.fiscal_years, got.ntm) == (case["expected"]["fiscal_years"],
                                           case["expected"]["ntm"]), f"{ticker}: {case['why']}"


@pytest.mark.parametrize("ticker", sorted(CASES))
def test_a_named_basis_obeys_the_rule_it_states(ticker: str) -> None:
    """Structure, not values: whatever is named must clear the stated thresholds on its evidence."""
    got = _run(CASES[ticker])
    fits = {f.line: f for f in got.fits}
    lines = dict(cs._PE_EPS_LINES)
    if got.fiscal_years in lines:
        named, rival = fits[lines[got.fiscal_years]], next(
            f for f in got.fits if f.line != lines[got.fiscal_years])
        assert named.spread is not None and rival.spread is not None
        assert rival.spread >= max(cs.PE_BASIS_SEPARATION * named.spread, cs.PE_BASIS_RIVAL_FLOOR)
    else:
        assert got.ntm not in lines, "an NTM row is never named without an FY price"


def test_amzn_is_struck_on_gaap_to_the_cent() -> None:
    """AMZN: P/E × GAAP EPS is $256.24 / $256.37 / $256.23 across FY26–28 — the price; × normalized
    it is $165.20 / $254.90 / $240.98. The NTM row's implied EPS is the GAAP sum of the next four
    quarters (9.39), not the normalized one (9.10)."""
    got = _run(CASES["AMZN"])
    gaap, norm = got.fits
    assert gaap.line == "EPS (GAAP)" and gaap.spread is not None and gaap.spread < 0.001
    assert norm.spread is not None and norm.spread > 0.30
    assert got.ntm_quarters == ["FQ3 2026", "FQ4 2026", "FQ1 2027", "FQ2 2027"]
    assert gaap.ntm_quarter_sum == pytest.approx(9.39)
    assert norm.ntm_quarter_sum == pytest.approx(9.10)
    assert gaap.ntm_gap is not None and gaap.ntm_gap < 0.002


# --- the negatives: what must NOT be named --------------------------------------------------

def test_lines_that_move_together_are_indistinguishable_not_a_coin_flip() -> None:
    """NFLX's two lines are under 0.5% apart, so a 0.24% GAAP spread beside a 0.06% normalized one
    is not evidence — the rival floor holds it at `indistinguishable`."""
    got = _run(CASES["NFLX"])
    assert got.fiscal_years == "indistinguishable"
    assert got.ntm == "undetermined" and got.ntm_implied_eps is None
    assert "establish no price" in (got.note or "")


def test_an_ntm_row_that_fits_the_other_line_is_not_named() -> None:
    """CONSTRUCTED from AMZN's real values — no committed export shows this shape. The NTM P/E is
    set to the multiple the NORMALIZED quarters would imply, so the NTM row fits normalized while
    the FY rows are GAAP. That contradiction is `undetermined`, never a silent flip."""
    case = CASES["AMZN"]
    base = _run(case)
    price = sorted(base.fits[0].implied_prices)[1]
    norm_sum = base.fits[1].ntm_quarter_sum
    got = _run(case, pe={**case["pe"], "NTM": price / norm_sum})
    assert got.fiscal_years == "gaap" and got.ntm == "undetermined"
    assert "NTM fits normalized while the FY rows are gaap" in (got.note or "")


def test_an_ntm_row_off_both_lines_is_not_named() -> None:
    """LLY: the FY rows are normalized to 0.05%, but the NTM row's implied EPS is 1.6% off the
    normalized quarters and 8.2% off GAAP — no line reproduces it, so nothing is named."""
    got = _run(CASES["LLY"])
    assert got.fiscal_years == "normalized" and got.ntm == "undetermined"
    assert all(f.ntm_gap is not None and f.ntm_gap > cs.PE_BASIS_SPREAD_MAX for f in got.fits)


def test_one_testable_row_names_nothing() -> None:
    got = _run(CASES["FUBO"])
    assert (got.fiscal_years, got.ntm) == ("undetermined", "undetermined")
    assert len(got.periods) < 2


def test_no_pe_on_the_ladder_writes_no_field() -> None:
    assert cs.pe_eps_basis({"NTM": 20.0}, CASES["AMZN"]["eps"], fy_periods=["FY 2026"],
                           quarters=[]) is None


# --- the reader, where the export is on disk --------------------------------------------------

@pytest.mark.parametrize("ticker", sorted(CASES))
def test_the_live_read_matches_the_frozen_case(ticker: str) -> None:
    """Pins `_trends_current` and `_pe_eps_basis` — the bundle side — against the frozen values,
    on the SAME export (by hash). Skips where the workbook is not on this machine (CI)."""
    from vinci.dossier.ciq import CiqBundle

    folder = ROOT / "data" / "manual" / "ciq" / ticker
    if not folder.is_dir():
        pytest.skip("no CIQ export on this machine")
    bundle = CiqBundle.from_files(ticker, sorted(p for p in folder.iterdir() if p.is_file()))
    wb = bundle.workbook("estimates")
    case = CASES[ticker]
    if wb is None or cs.file_provenance(wb.path)[0] != case["sha256"]:
        pytest.skip("the on-disk Estimates export is not the frozen one")
    fc = cs.forward_consensus(bundle)
    assert fc is not None and fc.pe_eps_basis is not None
    assert fc.pe_eps_basis == _run(case)


# --- absent until built ------------------------------------------------------------------------

def test_a_page_without_the_field_writes_no_null() -> None:
    """ABSENT, never null, until a page is rebuilt with it (`TOP_DROP_WHEN_NONE`). Built in the
    test from a committed page with the key removed, so this does not lapse once pages carry it."""
    doc = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    doc["forward_consensus"].pop("pe_eps_basis", None)
    out = dossier_json(Dossier.model_validate(doc))
    assert '"pe_eps_basis"' not in out
    assert json.loads(out) == doc
