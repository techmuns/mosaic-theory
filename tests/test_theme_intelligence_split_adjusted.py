"""THE DESK READS A SPLIT THE FILER STATED AS ADJUSTED, NOT AS A BREAK — real filings.

Operator, 2026-11-11: "Split-adjust EPS, fund rule". The fund's rule now puts EPS filed before the
filer's restating 10-K on the current basis (`assemble.split_restatement`). The desk ran its own
check on top (`market.basis_breaks`, which caught NVIDIA's split when the fund's rule missed it),
and that check refused AMZN and GOOGL on the very split the rule had adjusted: their ×20 EPS
restatements and their ×20 share-count jumps. A break of the filer's own factor is now explained;
any other break still refuses.

Real filings, committed: `tests/fixtures/companyfacts/AMZN.json` (annual diluted EPS and the
cover-page share counts the desk reads, `market.desk_points`). The prices are HYPOTHETICAL and
flat: the pin is about which basis the EPS is on, not about AMZN's market price.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from vinci.edgar.concepts import ConceptPoint
from vinci.screens.assemble import MAX_EPS_AGE_DAYS, split_restatement
from vinci.theme_intelligence.market import basis_breaks, desk_points, pe_against_history

AS_OF = date(2026, 11, 10)
FACTS = Path(__file__).parent / "fixtures" / "companyfacts" / "AMZN.json"


def _amzn() -> list[ConceptPoint]:
    return desk_points(json.loads(FACTS.read_text()), AS_OF)


def _flat(days: int = 1825) -> list[tuple[date, float]]:
    return [(AS_OF - timedelta(days=n), 100.0) for n in range(days, -1, -1)]


def test_the_premise_amzns_filings_state_a_20_for_1_and_the_desk_saw_it_as_breaks() -> None:
    since = AS_OF - timedelta(days=1825 + MAX_EPS_AGE_DAYS)
    pts = _amzn()
    stated = split_restatement([p for p in pts if p.concept == "eps_diluted"
                                and p.period_end >= since])
    assert stated is not None and abs(stated.factor - 20) < 0.1
    assert stated.restated_from == date(2023, 2, 3)
    kinds = {k for k, _w in basis_breaks(pts, since, AS_OF)}
    assert kinds == {"eps", "shares"}  # the ×20 restatements and the ×20 cover-page jump
    assert basis_breaks(pts, since, AS_OF, explained=stated.factor) == []


def test_amzn_holds_a_five_year_percentile_across_its_split() -> None:
    pe, pct = pe_against_history(_flat(), _amzn(), AS_OF, "AMZN")
    assert pe.value is not None
    assert pct.value is not None, pct.basis
    assert pct.basis.startswith("share of its daily P/Es from 2021-11-11 to 2026-11-10")
    # the adjustment is said where the figure is shown
    assert "EPS filed before 2023-02-03 put on the current share basis by the filer's own ~20.01x" \
        in pct.basis


def test_a_break_of_another_size_still_refuses() -> None:
    """NEGATIVE: a share count that moves ×3 on a cover page after the split — another event, not
    the filer's ×20 — still refuses the range."""
    extra = ConceptPoint(concept="shares", tag="EntityCommonStockSharesOutstanding", unit="shares",
                         value=3 * 10_700_000_000, period_start=None,
                         period_end=date(2025, 10, 20), filed=date(2025, 10, 31), fy=2025,
                         fp="Q3", form="10-Q", accession="0000000000-25-000000")
    _pe, pct = pe_against_history(_flat(), [*_amzn(), extra], AS_OF, "AMZN")
    assert pct.value is None and "per-share basis changes inside the window" in pct.basis


def _eps(end: date, filed: date, value: float) -> ConceptPoint:
    return ConceptPoint(concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares",
                        value=value, period_start=end - timedelta(days=364), period_end=end,
                        filed=filed, fy=end.year, fp="FY", form="10-K", accession="x")


def test_a_restatement_across_zero_of_the_splits_size_is_not_explained_by_it() -> None:
    """NEGATIVE (review): a 2:1 the filer restated (FY2021 4.00 → 2.00, FY2022 4.40 → 2.20), and
    an accounting restatement turning FY2024's 0.60 profit into a 1.20 loss — ×2 in magnitude.
    `split_restatement` skips a period that crosses zero, so the split stands; the desk must not
    then read the ×2 loss as that split and drop it as explained."""
    pts = [_eps(date(2021, 12, 31), date(2022, 2, 15), 4.00),
           _eps(date(2022, 12, 31), date(2023, 2, 15), 4.40),
           _eps(date(2021, 12, 31), date(2024, 2, 15), 2.00),
           _eps(date(2022, 12, 31), date(2024, 2, 15), 2.20),
           _eps(date(2023, 12, 31), date(2024, 2, 15), 2.40),
           _eps(date(2024, 12, 31), date(2025, 2, 15), 0.60),
           _eps(date(2024, 12, 31), date(2026, 2, 15), -1.20),
           _eps(date(2025, 12, 31), date(2026, 2, 15), 1.00)]
    stated = split_restatement(pts)
    assert stated is not None and abs(stated.factor - 2) < 0.01
    left = basis_breaks(pts, date(2021, 1, 1), date(2026, 8, 1), explained=stated.factor)
    assert [w for _k, w in left] == [
        "the year ending 2024-12-31: EPS 0.6 as first filed, 1.2 as filed 2026-02-15 (×2.0)"]
