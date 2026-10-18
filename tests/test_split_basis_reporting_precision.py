"""A split restated on CENTS is still a split (2026-10-16).

`share_basis_change` reads a split from the filer's own restatement: two periods restated by the
SAME factor. "The same" was 2% — and EPS is filed to the cent, so a small restated figure carries
more error than that on rounding alone:

  NVIDIA 2024 10-for-1:   FY2023 1.74 → 0.17 (×10.24) · FY2024 11.93 → 1.19 (×10.03) — 2.05% apart
  Pegasystems 2025 2-for-1: FY2023 0.73 → 0.37 (×1.97) · FY2024 1.11 → 0.55 (×2.02) — 2.2% apart

Both went undetected, so the P/E percentile divided split-adjusted prices by pre-split EPS. PEGA
reached the screen: on the 2026-09-22 run it PASSED G3 ("P/E at 11%ile of trailing range") and
ranked 44 of 289 on that percentile. Two factors now agree when they are within 2% OR the ranges
their stated figures allow overlap — never both stacked (that read SMPL's 2021 accounting
restatement as a split), never across a sign change, never from a ratio of cents too coarse to
state a factor; and with two splits in a series the LATEST is reported (the current basis).

Real filings, frozen: `tests/fixtures/split_basis/eps_restated_on_cents.json` (NVDA, PEGA) and the
committed companyfacts fleet (NFLX, SMPL).
"""

from __future__ import annotations

import json
import pathlib
from datetime import date, timedelta

import pytest

from vinci.edgar.concepts import ConceptPoint, extract_points
from vinci.schemas.envelope import CoverageStatus
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import (
    _SPLIT_TOL,
    G3_SPLIT_BASIS,
    MAX_EPS_AGE_DAYS,
    _factor_range,
    _half_unit,
    pe_current_and_percentile,
    share_basis_change,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
FROZEN = json.loads((ROOT / "tests" / "fixtures" / "split_basis"
                     / "eps_restated_on_cents.json").read_text())
FLEET = ROOT / "tests" / "fixtures" / "companyfacts"


def _points(ticker: str) -> list[ConceptPoint]:
    return [ConceptPoint.model_validate(p) for p in FROZEN[ticker]]


def _fleet(ticker: str) -> list[ConceptPoint]:
    return [p for p in extract_points(json.loads((FLEET / f"{ticker}.json").read_text()),
                                      "eps_diluted") if p.is_annual]


def _window(points: list[ConceptPoint], ref: date) -> list[ConceptPoint]:
    """The G3 call site's window: the range plus the EPS reach-back."""
    start = ref - timedelta(days=1825 + MAX_EPS_AGE_DAYS)
    return [p for p in points if p.period_end >= start]


@pytest.mark.parametrize(("ticker", "ref", "factor"), [
    ("NVDA", date(2026, 10, 14), 10.0),
    ("PEGA", date(2026, 9, 22), 2.0),     # the screen run that admitted it on the percentile
])
def test_a_split_restated_on_cents_is_detected(ticker: str, ref: date, factor: float) -> None:
    got = share_basis_change(_window(_points(ticker), ref))
    assert got == pytest.approx(factor, rel=0.03), got


def test_the_two_factors_really_differ_by_more_than_the_old_tolerance() -> None:
    """The premise, measured: the fixture still exercises the bug (rounding, not the factor)."""
    for (a1, b1), (a2, b2) in (((1.74, 0.17), (11.93, 1.19)), ((0.73, 0.37), (1.11, 0.55))):
        f, g = a1 / b1, a2 / b2
        assert abs(g - f) / max(f, g) > _SPLIT_TOL


def test_the_percentile_g3_reads_is_refused_for_pega() -> None:
    """THE ARTIFACT LAYER: the field the G3 gate and the ranker's multiple axis read — on the
    2026-09-22 run a PRESENT 11th percentile; now refused with the split as its stated cause."""
    ref = date(2026, 9, 22)
    bars = [PriceBar(internal_id="SEC-PEGA", bar_date=ref - timedelta(days=n), open=40.0,
                     high=41.0, low=39.0, close=40.0, volume=1e6, source="t")
            for n in range(0, 1825, 1)]
    pe, pctile = pe_current_and_percentile(bars, _points("PEGA"), reference_date=ref)
    assert pe.coverage_status is CoverageStatus.PRESENT
    assert pctile.coverage_status is CoverageStatus.UNKNOWN
    assert G3_SPLIT_BASIS in (pctile.note or "")


def test_an_accounting_restatement_is_not_a_split() -> None:
    """NEGATIVE, real filings: SMPL's 2021 restatement (FY2018 0.96 → 0.51; FY2019 0.56 → −0.31)
    — a sign change no split makes, and two factors (×1.88, ×1.81) whose ranges do not overlap."""
    assert share_basis_change(_fleet("SMPL")) is None


def test_with_two_splits_the_latest_is_reported() -> None:
    """NFLX carries its 2015 7-for-1 (×7.12, ×6.97 — also hidden on cents before) and its
    2025 10-for-1: the factor is the latest, the basis today's figures are on."""
    assert share_basis_change(_fleet("NFLX")) == pytest.approx(10.02, abs=0.05)
    older = [p for p in _fleet("NFLX") if p.period_end <= date(2016, 12, 31)]
    assert share_basis_change(older) == pytest.approx(7.0, rel=0.03)


def _pt(end: date, filed: date, value: float) -> ConceptPoint:
    return ConceptPoint(concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares",
                        value=value, period_start=end - timedelta(days=364), period_end=end,
                        filed=filed, fy=end.year, fp="FY", form="10-K", accession="x")


def test_restatements_of_cents_state_no_factor() -> None:
    """NEGATIVE: 0.01 → 0.02 and 0.03 → 0.05 allow anything from 1x to 5x — no split is read
    from them, however their ranges overlap."""
    pts = [_pt(date(2022, 12, 31), date(2023, 2, 1), 0.01),
           _pt(date(2022, 12, 31), date(2024, 2, 1), 0.02),
           _pt(date(2023, 12, 31), date(2024, 2, 1), 0.03),
           _pt(date(2023, 12, 31), date(2025, 2, 1), 0.05)]
    assert _factor_range(0.02, 0.01) is None
    assert share_basis_change(pts) is None


def test_the_precision_is_a_cent_or_the_figures_own() -> None:
    assert _half_unit(0.17) == pytest.approx(0.005)
    assert _half_unit(1.2) == pytest.approx(0.005)       # filed 1.20: a cent, not a dime
    assert _half_unit(0.174) == pytest.approx(0.0005)    # a finer figure states its own


def test_a_restatement_across_zero_is_never_a_split_factor() -> None:
    """NEGATIVE: two periods restated by exactly ×2.0 — one from a profit to a LOSS. A split
    rescales and never crosses zero, so only one factor stands, and one is not a split.
    POSITIVE beside it: the same two periods without the sign change are one."""
    flip = [_pt(date(2022, 12, 31), date(2023, 2, 1), 0.56),
            _pt(date(2022, 12, 31), date(2024, 2, 1), -0.28),
            _pt(date(2023, 12, 31), date(2024, 2, 1), 1.00),
            _pt(date(2023, 12, 31), date(2025, 2, 1), 0.50)]
    assert share_basis_change(flip) is None
    same = [p.model_copy(update={"value": abs(p.value)}) for p in flip]
    assert share_basis_change(same) == pytest.approx(2.0)


def test_two_factors_whose_ranges_only_come_near_are_not_one_split() -> None:
    """NEGATIVE, SMPL's magnitudes without the sign change: ×1.88 (0.96 → 0.51) and ×1.81
    (0.56 → 0.31) — 4% apart, and the ranges their cents allow do not meet ([1.854, 1.911] and
    [1.762, 1.852]). Widening the ranges by the 2% as well would make them one factor."""
    pts = [_pt(date(2018, 8, 25), date(2018, 10, 24), 0.96),
           _pt(date(2018, 8, 25), date(2021, 6, 30), 0.51),
           _pt(date(2019, 8, 31), date(2019, 10, 30), 0.56),
           _pt(date(2019, 8, 31), date(2021, 10, 26), 0.31)]
    assert share_basis_change(pts) is None


def test_a_coarse_factor_still_agrees_within_the_old_tolerance() -> None:
    """REGRESSION (review of #735): the precision gate guards only the range path. A 2-for-1 on
    small EPS — 0.10 → 0.05 (a range too coarse to state) and 0.20 → 0.10 — is two exact ×2.0
    factors, and the old 2% rule read it; it must still."""
    pts = [_pt(date(2022, 12, 31), date(2023, 2, 1), 0.10),
           _pt(date(2022, 12, 31), date(2024, 2, 1), 0.05),
           _pt(date(2023, 12, 31), date(2024, 2, 1), 0.20),
           _pt(date(2023, 12, 31), date(2025, 2, 1), 0.10)]
    assert _factor_range(0.10, 0.05) is None
    assert share_basis_change(pts) == pytest.approx(2.0)
