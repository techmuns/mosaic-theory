"""The two lease checks compare like with like (wave 2, 2026-10-27) — each pinned on the real case.

Measured before any pin (main 56500bb1, BEFORE `data/snapshots/data_quality/ciq/2026-10-27.json`):
`rent_vs_edgar_lease_cost` 2 differs-unexplained (NKE, WLK), `lease_rows_vs_edgar` 5 (UBER 4,
WERN 1). Each was a different quantity on the two sides, except WERN's:

* NKE tags no `LeaseCost`; CIQ's $1,146M rent was set against its OPERATING lease cost alone
  ($693M). Its operating ($693M) and variable ($453M) lease cost are $1,146M to the dollar.
* WLK's CIQ rent ($128M) IS its `ShortTermLeaseCost` ($128M) — one part of a $306M total.
* UBER tags its finance leases complete (current + noncurrent) only at year-end; carried onto a
  quarter-end, the year-end figure misses EDGAR's operating leases by 2.0–2.1%.
* WERN's 2019-12-31: CIQ's lease rows are NOTHING against EDGAR's $11.736M — no finance figure
  explains rows SHORT of the operating leases. It stays a difference.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from vinci.dossier import lease_basis as lbm


def _facts(points: dict[str, list[tuple[str | None, str, float, str]]]) -> dict[str, Any]:
    """companyfacts shape from (start, end, $M, filed) rows — start None for an instant."""
    return {"facts": {"us-gaap": {tag: {"units": {"USD": [
        {**({"start": s} if s else {}), "end": e, "val": v * 1e6, "filed": f, "form": "10-K",
         "accn": "x"} for s, e, v, f in rows]}} for tag, rows in points.items()}}}


# --- rent: the total against the total ------------------------------------------------------------

#: NKE's FY to 2026-05-31, as filed in its 10-K of 2026-07-15 ($M)
_NKE = {"OperatingLeaseCost": [("2025-06-01", "2026-05-31", 693.0, "2026-07-15")],
        "VariableLeaseCost": [("2025-06-01", "2026-05-31", 453.0, "2026-07-15")]}
#: WLK's FY to 2025-12-31, as filed in its 10-K of 2026-02-26 ($M)
_WLK = {"LeaseCost": [("2025-01-01", "2025-12-31", 306.0, "2026-02-26")],
        "OperatingLeaseCost": [("2025-01-01", "2025-12-31", 178.0, "2026-02-26")],
        "ShortTermLeaseCost": [("2025-01-01", "2025-12-31", 128.0, "2026-02-26")]}


def test_nke_total_lease_cost_is_its_tagged_parts() -> None:
    """Before: (693.0, 'OperatingLeaseCost') — 1.65x from CIQ's 1,146, 'disagree'. Now the parts
    NKE tags, summed and named; CIQ's rent agrees with them to the dollar."""
    got = lbm.edgar_lease_cost(_facts(_NKE), date(2026, 5, 31))
    assert got == pytest.approx((1146.0, "OperatingLeaseCost + VariableLeaseCost"))
    assert lbm.rent_disagrees(1146.0, got[0]) is False


def test_lease_cost_itself_still_wins_and_sublease_income_nets() -> None:
    """Negative pins: a tagged `LeaseCost` is the total (WLK's parts are never summed over it); a
    sublease income is netted, as ASC 842 nets it."""
    assert lbm.edgar_lease_cost(_facts(_WLK), date(2025, 12, 31)) == (306.0, "LeaseCost")
    sub = {**_NKE, "SubleaseIncome": [("2025-06-01", "2026-05-31", 46.0, "2026-07-15")]}
    assert lbm.edgar_lease_cost(_facts(sub), date(2026, 5, 31)) == pytest.approx(
        (1100.0, "OperatingLeaseCost + VariableLeaseCost − SubleaseIncome"))


def test_wlk_rent_is_its_short_term_lease_cost() -> None:
    """CIQ's $128M against WLK's $306M total disagrees by 2.4x — because it is the $128M
    short-term part. Named on the page, and never compared."""
    f = _facts(_WLK)
    assert lbm.rent_component(f, date(2025, 12, 31), 128.0, 306.0) == "ShortTermLeaseCost"
    line = lbm._cross_check(lbm.Rent(128.0, 834.0, date(2025, 12, 31)), (306.0, "LeaseCost"),
                            "ShortTermLeaseCost")
    assert "ShortTermLeaseCost" in line and "DISAGREE" not in line


def test_a_rent_matching_no_part_still_disagrees() -> None:
    """Negative pins: a rent the total agrees with is never re-labelled; a disagreeing rent that
    equals no part ($200M: 1.53x, and no part is $200M) stays a difference."""
    f = _facts(_WLK)
    assert lbm.rent_component(f, date(2025, 12, 31), 300.0, 306.0) is None
    # a filer whose total IS its one part: a rent equal to both agrees, and is not a narrower cost
    one = _facts({"LeaseCost": [("2025-01-01", "2025-12-31", 178.0, "2026-02-26")],
                  "OperatingLeaseCost": [("2025-01-01", "2025-12-31", 178.0, "2026-02-26")]})
    assert lbm.rent_component(one, date(2025, 12, 31), 178.0, 178.0) is None
    assert lbm.rent_component(f, date(2025, 12, 31), 200.0, 306.0) is None
    assert lbm.rent_disagrees(200.0, 306.0) is True


# --- lease rows: a finance figure for the date, or no finance decomposition -----------------------

#: UBER's finance-lease liability as filed — current tagged quarterly, noncurrent at year-end only
_UBER_FIN = {
    "FinanceLeaseLiabilityCurrent": [(None, "2019-09-30", 130.0, "2019-11-05"),
                                     (None, "2019-12-31", 165.0, "2020-03-02")],
    "FinanceLeaseLiabilityNoncurrent": [(None, "2019-12-31", 143.0, "2021-03-01")],
}
#: (date, CIQ lease rows, EDGAR operating leases) on UBER's committed page ($M)
_UBER_0930 = (date(2019, 9, 30), 1930.0, 1656.0)
_UBER_1231 = (date(2019, 12, 31), 2027.0, 1719.0)


def test_uber_has_a_complete_finance_figure_only_at_year_end() -> None:
    fin = lbm._complete(_facts(_UBER_FIN), *lbm._FINANCE_TAGS)
    assert fin == {date(2019, 12, 31): pytest.approx(308.0)}
    near = lbm._near_dated(fin, date(2019, 9, 30), lbm._FINANCE_NEAR_DAYS)
    assert near is not None and near[0] == date(2019, 12, 31)


def test_only_a_figure_within_a_week_is_the_dates_own() -> None:
    """UBER's complete series: the year-end is its own date's figure, the quarter before is not —
    and a filer tagging no finance lease anywhere has 0 as its figure on every date."""
    fin = lbm._complete(_facts(_UBER_FIN), *lbm._FINANCE_TAGS)
    assert lbm._finance_dated(fin, date(2019, 12, 31)) is True
    assert lbm._finance_dated(fin, date(2019, 9, 30)) is False
    assert lbm._finance_dated(fin, date(2019, 3, 31)) is False   # nothing within reach at all
    assert lbm._finance_dated({}, date(2019, 9, 30)) is True


def test_uber_carried_finance_figure_is_unchecked_not_unreconciled() -> None:
    """2019-09-30: 1,930 − 308 (the 2019-12-31 figure) = 1,622 against EDGAR's 1,656 — a 2.1%
    'miss' that compared two dates. Before: unreconciled (and the band refused on four such).
    Now: unchecked; the year-end itself, with its own figure, still reconciles exactly."""
    d, rows, op = _UBER_0930
    old = lbm._split(rows, 308.0, op, adopted=True, comparative=False, nearest=True)
    assert old.status == "unreconciled"
    new = lbm._split(rows, 308.0, op, adopted=True, comparative=False, nearest=True,
                     fin_dated=False)
    assert new.status == "unchecked" and new.operating == pytest.approx(1622.0)
    d, rows, op = _UBER_1231
    assert lbm._split(rows, 308.0, op, adopted=True, comparative=False, nearest=True,
                      fin_dated=True).status == "reconciled"


def test_a_carried_figure_never_confirms() -> None:
    """2019-06-30 'reconciled' on the same carried 308 (1,736 − 308 = 1,428 against 1,454, 1.8%):
    a comparison of two dates is no confirmation either — unchecked."""
    assert lbm._reconciles(1736.0, 308.0, 1454.0) is True
    assert lbm._reconciles(1736.0, 308.0, 1454.0, fin_dated=False) is None


def test_rows_short_of_the_operating_leases_stay_unreconciled() -> None:
    """Negative pin, WERN's 2019-12-31: CIQ's rows are 0 against EDGAR's $11.736M. A finance
    figure can only explain rows ABOVE the operating leases; this stays a difference."""
    got = lbm._split(0.0, 0.0, 11.736, adopted=True, comparative=False, nearest=True,
                     fin_dated=False)
    assert got.status == "unreconciled"


def test_rows_alone_still_reconcile_without_a_dated_finance_figure() -> None:
    """Negative pin: UBER's 2022 quarters are the operating leases alone (finance filed outside
    the rows) — that decomposition subtracts nothing, so no finance date is needed."""
    assert lbm._split(1890.0, 234.0, 1890.0, adopted=True, comparative=False, nearest=False,
                      fin_dated=False).status == "reconciled"
