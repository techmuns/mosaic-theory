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
        assert got.ntm in (got.fiscal_years, "indistinguishable", "undetermined"), (
            "an NTM row never names the OTHER line from a named FY basis")
    if got.fiscal_years == "undetermined":
        assert got.ntm == "undetermined", "an NTM row is never named without an FY price"


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
    is not evidence — the rival floor holds the FY rows at `indistinguishable`.

    Both lines' prices hold, so the FY rows establish TWO prices, not none (review of #686: the
    first cut left the NTM row untested with a note saying no price existed). Each line is tested
    at its own price, both fit, and the NTM row is `indistinguishable` too — the choice of line
    does not matter for NFLX's anchor."""
    got = _run(CASES["NFLX"])
    assert (got.fiscal_years, got.ntm) == ("indistinguishable", "indistinguishable")
    gaap, norm = got.fits
    assert gaap.ntm_implied_eps is not None and norm.ntm_implied_eps is not None
    assert gaap.ntm_implied_eps != norm.ntm_implied_eps, "each line at its OWN price"
    assert all(f.ntm_gap is not None and f.ntm_gap <= cs.PE_BASIS_SPREAD_MAX for f in got.fits)


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
    assert "neither line fits" in (got.note or "")


def test_a_line_that_fits_without_separating_says_so() -> None:
    """ROST (review of #686): normalized fits the NTM row (0.91%, inside the 1% cap) and GAAP sits
    at 1.02% — outside its cap but nowhere near 3x away. Not named, and the note must say WHICH
    failed: the first cut said neither line reproduced the row, which was false for normalized."""
    got = _run(CASES["ROST"])
    assert got.ntm == "undetermined"
    note = got.note or ""
    assert "normalized fits" in note and "neither line fits" not in note


def test_one_testable_row_names_nothing() -> None:
    got = _run(CASES["FUBO"])
    assert (got.fiscal_years, got.ntm) == ("undetermined", "undetermined")
    assert len(got.periods) < 2


def test_no_pe_on_the_ladder_writes_no_field() -> None:
    assert cs.pe_eps_basis({"NTM": 20.0}, CASES["AMZN"]["eps"], fy_periods=["FY 2026"],
                           quarters=[]) is None


def test_a_zero_quarter_sum_is_a_figure_not_a_gap() -> None:
    """CONSTRUCTED from AMZN's real values (review of #686): a near-breakeven name can sum to $0.00
    on one line. Its gap is |0 ÷ implied − 1| = 1, a well-defined figure; the first cut read 0.0 as
    missing and stopped the NTM test for BOTH lines while GAAP still fit to 0.12%."""
    case = CASES["AMZN"]
    zeroed = {**case["eps"], "normalized": {**case["eps"]["normalized"],
                                            **dict.fromkeys(case["quarters"], 0.0)}}
    got = _run(case, eps=zeroed)
    assert got.ntm == "gaap"
    assert got.fits[1].ntm_quarter_sum == 0.0 and got.fits[1].ntm_gap == pytest.approx(1.0)


def test_a_negative_pe_row_is_not_tested() -> None:
    """CONSTRUCTED (review of #686): a negative P/E with positive EPS would give a negative price,
    and a spread over a negative median passed the cap — obviously inconsistent rows read
    `indistinguishable`. Only a positive P/E is tested."""
    got = cs.pe_eps_basis({"FY 2026": -20.0, "FY 2027": -10.0},
                          {"gaap": {"FY 2026": 1.0, "FY 2027": 2.0},
                           "normalized": {"FY 2026": 1.5, "FY 2027": 2.0}},
                          fy_periods=["FY 2026", "FY 2027"], quarters=[])
    assert got is not None and got.periods == [] and got.fiscal_years == "undetermined"


def test_a_missing_eps_line_is_an_outcome_not_an_absent_field() -> None:
    """Review of #686: a page whose ladder HAS a P/E but whose Trends sheet lacks a line must say
    `undetermined` — an absent field reads as 'not yet rebuilt', which would be false."""
    case = CASES["AMZN"]
    got = _run(case, eps={"normalized": case["eps"]["normalized"]})
    assert got is not None
    assert (got.fiscal_years, got.ntm) == ("undetermined", "undetermined")
    assert "0 FY row(s)" in (got.note or "")


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
    # ONE READER PER FIGURE (review of #686): the FY EPS behind each implied price is the layer's
    # own committed path, not a second read of the same cells
    pe = {m.period: m.value for m in fc.current_multiples or [] if m.metric == "Price/Earnings"}
    for k, title in cs._PE_EPS_LINES:
        path = {p.period: p.points[-1].value for p in fc.paths if p.metric == title}
        fit = next(f for f in fc.pe_eps_basis.fits if f.line == title)
        assert fit.implied_prices == [round(pe[p] * path[p], 6) for p in fc.pe_eps_basis.periods], k


def _local_bundle(ticker: str) -> Any:
    from vinci.dossier.ciq import CiqBundle

    folder = ROOT / "data" / "manual" / "ciq" / ticker
    if not folder.is_dir():
        pytest.skip("no CIQ export on this machine")
    return CiqBundle.from_files(ticker, sorted(p for p in folder.iterdir() if p.is_file()))


def test_a_trends_sheet_without_the_gaap_block_still_answers() -> None:
    """Review of #686, on AMZN's REAL sheet with the GAAP block's title renamed: the first cut
    returned None when the GAAP block was absent, which drops the field exactly as an unbuilt page
    does. It must return an outcome, read from the line that is there."""
    bundle = _local_bundle("AMZN")
    fc = cs.forward_consensus(bundle)
    assert fc is not None
    trends = [list(r) for r in bundle.sheet("estimates", "Trends")]
    for r in trends:
        if r and str(r[0]).strip() == "EPS (GAAP)":
            r[0] = "EPS (GAAP) — renamed for the test"
    paths = [p for p in fc.paths if p.metric != "EPS (GAAP)"]
    got = cs._pe_eps_basis(fc.current_multiples, trends, paths, fc.periods)
    assert got is not None and got.fiscal_years == "undetermined"
    assert got.ntm_quarters == []


def test_a_failure_in_the_annotation_does_not_cost_the_layer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Review of #686: the basis is an annotation on `forward_consensus`. A failure in it must leave
    the paths, spreads, revisions and ladder standing, and NAME itself in `withheld`."""
    bundle = _local_bundle("AMZN")

    def boom(*_a: Any, **_k: Any) -> None:
        raise ValueError("an unexpected header")

    monkeypatch.setattr(cs, "_pe_eps_basis", boom)
    fc = cs.forward_consensus(bundle)
    assert fc is not None and fc.paths and fc.current_multiples
    assert fc.pe_eps_basis is None
    assert any("P/E basis: not built (ValueError: an unexpected header)" in w for w in fc.withheld)


# --- absent until built ------------------------------------------------------------------------

def test_a_page_without_the_field_writes_no_null() -> None:
    """ABSENT, never null, until a page is rebuilt with it (`TOP_DROP_WHEN_NONE`). Built in the
    test from a committed page with the key removed, so this does not lapse once pages carry it."""
    doc = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    doc["forward_consensus"].pop("pe_eps_basis", None)
    out = dossier_json(Dossier.model_validate(doc))
    assert '"pe_eps_basis"' not in out
    assert json.loads(out) == doc


def test_the_ntm_cap_is_on_the_base_the_gap_is_measured_against(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Review of #686: the gap is |sum ÷ implied − 1|, relative to the IMPLIED NTM EPS, so four
    quarters' cent-rounding (±$0.02) must be expressed against that same base. The first cut divided
    by each line's own sum, so a rival summing near zero earned a near-infinite cap. On AORT (four
    quarters sum to $0.12) both lines now share one cap, 0.02 ÷ implied."""
    seen: list[dict[str, float]] = []
    real = cs._basis_of

    def spy(dispersion: dict[str, float], cap: dict[str, float]) -> Any:
        seen.append(cap)
        return real(dispersion, cap)

    monkeypatch.setattr(cs, "_basis_of", spy)
    got = _run(CASES["AORT"])
    implied = got.fits[0].ntm_implied_eps
    assert implied is not None and got.ntm == "gaap"
    ntm_cap = seen[-1]
    assert ntm_cap["gaap"] == ntm_cap["normalized"] == pytest.approx(
        max(cs.PE_BASIS_SPREAD_MAX, 4 * cs._EPS_HALF_CENT / implied), rel=1e-4)


def test_a_path_without_its_current_point_leaves_that_row_untested() -> None:
    """A path can END BEFORE Current: 13 of 676 committed paths do (CNXC's cash-flow lines stop at
    six months ago, TECX's EBITDA at twelve). Read off such a path, an EPS would be a stale vintage
    set against TODAY's P/E. Built from AMZN's committed page with one EPS path's Current point
    removed: that row must leave the test, never be filled from an older vintage."""
    from vinci.dossier.schemas import ForwardConsensus

    page = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    fc = ForwardConsensus.model_validate(page["forward_consensus"])
    paths = [p.model_copy(update={"points": [x for x in p.points if x.months_ago != 0]})
             if (p.metric, p.period) == ("EPS (GAAP)", "FY 2026") else p for p in fc.paths]
    got = cs._pe_eps_basis(fc.current_multiples, [], paths, fc.periods)
    assert got is not None
    assert "FY 2026" not in got.periods and len(got.periods) == 2
