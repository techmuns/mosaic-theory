"""Tests for the CIQ balance-sheet extraction (vinci.dossier.ciq_balance) and the D&A vintage rule.

Fixtures are SYNTHETIC workbook shapes. The canonical CIQ workbooks are licensed and never
committed, so a test that read one could not run in CI and would leak vendor data into the repo if
it did. What the fixtures reproduce is the SHAPE — the row labels, the header row, the column
layout — because that is what the parser binds to.

Every monetary pin uses NON-ZERO values and binds by MAGNITUDE. Three separate 1e6 defects have
shipped here (the anchor's net debt into a $M guard, the R2 engine's equity over a raw share count,
and the original diluted-shares trap), and two of them survived a green test because the fixture's
value was zero or the assertion only checked not-None.
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.dossier import ciq_balance as cb


# --- unit scale ---------------------------------------------------------------------------------
def test_scale_accepts_a_plausible_millions_sheet() -> None:
    """Cash of $126M against revenue of $372M is an ordinary balance sheet."""
    assert cb._assert_scale("cash", 126.1, 371.6) is None
    assert cb._assert_scale("total_debt", 326.0, 371.6) is None


def test_scale_rejects_whole_dollars() -> None:
    """The failure mode that matters: a sheet in DOLLARS beside a revenue figure in millions. The
    number is not absurd on its face — 126,100,000 looks like a real balance — which is exactly why
    it has to be caught by ratio rather than by eye."""
    bad = cb._assert_scale("cash", 126_100_000.0, 371.6)
    assert bad is not None and "UNIT error" in bad


def test_scale_rejects_billions() -> None:
    bad = cb._assert_scale("total_debt", 0.000326, 371.6)
    assert bad is not None and "UNIT error" in bad


def test_scale_skips_what_it_cannot_judge() -> None:
    """No revenue reference, or a genuinely zero line, is not a scale failure."""
    assert cb._assert_scale("cash", 126.1, None) is None
    assert cb._assert_scale("cash", 126.1, 0.0) is None
    assert cb._assert_scale("finance_leases", 0.0, 371.6) is None


def test_scale_bounds_are_wide_enough_for_a_real_balance_sheet() -> None:
    """A cash-rich pre-revenue name and a heavily levered one must both pass — the bound is a unit
    check, not a leverage opinion."""
    assert cb._assert_scale("cash", 900.0, 10.0) is None        # 90x revenue: odd, not a unit bug
    assert cb._assert_scale("total_debt", 0.05, 371.6) is None  # tiny but real


# --- net-debt cross-read -------------------------------------------------------------------------
def _facts(net_debt: float) -> cb.CiqFacts:
    return cb.CiqFacts(ticker="X", as_of=None, source_file="f.xls", source_sha256="abc",
                       facts={"net_debt": cb.CiqFact(value=net_debt, unit="$M", basis="b",
                                                     source="s")})


def test_net_debt_cross_read_passes_when_the_two_reads_agree() -> None:
    """TEV (12x x 100 EBITDA = 1,200) less a 1,000 market cap implies 200 of net debt; the balance
    sheet says 202.4. Two independent routes to the same number."""
    assert cb.net_debt_cross_read(_facts(202.4), market_cap=1000.0, current_multiple=12.0,
                                  ltm_ebitda=100.0) is None


def test_net_debt_cross_read_trips_on_a_structural_disagreement() -> None:
    """The VITL lesson in its net-debt form: the traded multiple implies a balance sheet the filer
    does not have. 12x x 100 - 1,000 = 200 implied against 900 recorded."""
    bad = cb.net_debt_cross_read(_facts(900.0), market_cap=1000.0, current_multiple=12.0,
                                 ltm_ebitda=100.0)
    assert bad is not None and "NET DEBT" in bad and "900" in bad


def test_net_debt_cross_read_handles_net_cash_without_tripping() -> None:
    """A negative net debt is net cash — ordinary, and the ratio must not blow up on the sign."""
    assert cb.net_debt_cross_read(_facts(-150.0), market_cap=1350.0, current_multiple=12.0,
                                  ltm_ebitda=100.0) is None


@pytest.mark.parametrize("kw", [
    {"market_cap": None, "current_multiple": 12.0, "ltm_ebitda": 100.0},
    {"market_cap": 1000.0, "current_multiple": None, "ltm_ebitda": 100.0},
    {"market_cap": 1000.0, "current_multiple": 12.0, "ltm_ebitda": None},
])
def test_net_debt_cross_read_skips_on_missing_inputs(kw: dict) -> None:
    """Absence leaves the check unrun; it never manufactures a pass or a failure."""
    assert cb.net_debt_cross_read(_facts(202.4), **kw) is None


# --- the D&A vintage rule (the queued defect, closed) --------------------------------------------
def _pt(tag: str, end: str, val: float, fy: int) -> dict:
    return {"start": f"{int(end[:4]) - 1}-12-31", "end": end, "val": val,
            "filed": f"{fy + 1}-02-01", "fy": fy, "fp": "FY", "form": "10-K", "accn": "x"}


def _facts_us(**tags: list[dict]) -> dict:
    return {"facts": {"us-gaap": {t: {"units": {"USD": pts}} for t, pts in tags.items()}}}


def test_dep_amort_prefers_the_freshest_tag_not_the_first_alias() -> None:
    """THE FUBO SHAPE, and the reason the defect existed. ``extract_points`` resolves aliases by
    ORDER — first-with-any-data wins — which is correct for breadth and wrong for vintage: an
    abandoned tag keeps its last value forever and still sorts first.

    Here the first alias last reported $0.003M in FY2014 and the third reports $38.5M in FY2024.
    Name-preference picks the twelve-year-old number; vintage-preference picks the current one."""
    from vinci.dossier.anchor import _latest_dep_amort
    f = _facts_us(
        DepreciationDepletionAndAmortization=[_pt("a", "2014-12-31", 3_000.0, 2014)],
        DepreciationAndAmortization=[_pt("b", "2024-12-31", 38_500_000.0, 2024)])
    got = _latest_dep_amort(f)
    assert got is not None
    value, source = got
    assert value == pytest.approx(38_500_000.0), "picked the stale alias"
    assert "DepreciationAndAmortization" in source
    assert "CHOSEN BY VINTAGE" in source and "10y behind" in source


def test_dep_amort_keeps_the_combined_tag_when_it_is_current() -> None:
    """No churn on the healthy case: a filer whose combined tag is up to date keeps it, and the
    source stamp carries no vintage note because nothing was overridden."""
    from vinci.dossier.anchor import _latest_dep_amort
    f = _facts_us(
        DepreciationDepletionAndAmortization=[_pt("a", "2025-12-31", 200_309_000.0, 2025)])
    value, source = _latest_dep_amort(f)  # type: ignore[misc]
    assert value == pytest.approx(200_309_000.0)
    assert "CHOSEN BY VINTAGE" not in source


def test_dep_amort_takes_a_fresher_split_over_a_stale_combined() -> None:
    """The split pair wins when it is newer — the CNXC shape crossed with the FUBO one."""
    from vinci.dossier.anchor import _latest_dep_amort
    f = _facts_us(
        DepreciationDepletionAndAmortization=[_pt("a", "2020-12-31", 10_000_000.0, 2020)],
        Depreciation=[_pt("d", "2025-12-31", 53_100_000.0, 2025)],
        AmortizationOfIntangibleAssets=[_pt("m", "2025-12-31", 71_367_000.0, 2025)])
    value, source = _latest_dep_amort(f)  # type: ignore[misc]
    assert value == pytest.approx(124_467_000.0)
    assert "split" in source and "CHOSEN BY VINTAGE" in source


def test_dep_amort_refuses_a_misaligned_split() -> None:
    """Summing an FY2025 depreciation into an FY2024 amortisation fabricates a year that never
    existed — the split is dropped, and the stale combined tag is all that is left."""
    from vinci.dossier.anchor import _latest_dep_amort
    f = _facts_us(
        DepreciationDepletionAndAmortization=[_pt("a", "2020-12-31", 10_000_000.0, 2020)],
        Depreciation=[_pt("d", "2025-12-31", 53_100_000.0, 2025)],
        AmortizationOfIntangibleAssets=[_pt("m", "2024-12-31", 71_367_000.0, 2024)])
    value, _source = _latest_dep_amort(f)  # type: ignore[misc]
    assert value == pytest.approx(10_000_000.0), "a misaligned split must not be summed"


def test_dep_amort_absent_everywhere_is_none_not_zero() -> None:
    """MVST's shape: no depreciation tag at all. UNKNOWN is flagged upstream; a zero would silently
    inflate every EBITDA-basis number downstream."""
    from vinci.dossier.anchor import _latest_dep_amort
    assert _latest_dep_amort(_facts_us(Revenues=[_pt("r", "2025-12-31", 1.0, 2025)])) is None


def test_dep_amort_magnitude_survives_the_dollars_to_millions_boundary() -> None:
    """MAGNITUDE PIN. The resolver returns DOLLARS; the anchor divides by 1e6 at its call site.
    Pinning the raw return keeps the two halves of that contract honest — a fixture in millions
    would pass either way and catch nothing."""
    from vinci.dossier.anchor import _latest_dep_amort
    f = _facts_us(DepreciationAndAmortization=[_pt("b", "2025-12-31", 124_811_000.0, 2025)])
    value, _ = _latest_dep_amort(f)  # type: ignore[misc]
    assert 1e8 < value < 1e9, f"{value} is not a dollar figure for a $125M D&A"
    assert value / 1e6 == pytest.approx(124.811)


def test_vintage_note_names_how_stale_the_loser_was() -> None:
    """The source stamp has to say WHY it overrode, or the next reader re-derives the argument."""
    from vinci.dossier.anchor import _latest_dep_amort
    f = _facts_us(
        DepreciationDepletionAndAmortization=[_pt("a", "2019-12-31", 45_317_000.0, 2019)],
        DepreciationAndAmortization=[_pt("b", "2025-12-31", 124_811_000.0, 2025)])
    _value, source = _latest_dep_amort(f)  # type: ignore[misc]
    assert "FY2019" in source and "6y behind" in source


# --- the extracted-facts container ---------------------------------------------------------------
def test_ciq_facts_ok_is_false_when_any_check_trips() -> None:
    """A sheet that contradicts itself has NOT been shown to be right in the parts that happen to
    look reasonable — the caller must refuse the whole bundle, not pick survivors."""
    f = cb.CiqFacts(ticker="X", as_of=None, source_file="f.xls", source_sha256="abc",
                    facts={"cash": cb.CiqFact(value=1.0, unit="$M", basis="b", source="s")},
                    failures=["SCALE: something is 1e6 out"])
    assert f.ok is False
    assert f.value("cash") == 1.0
    assert f.value("total_debt") is None


def test_ciq_facts_ok_when_clean() -> None:
    assert cb.CiqFacts(ticker="X", as_of=None, source_file=None, source_sha256=None).ok is True
    assert isinstance(date.today(), date)
