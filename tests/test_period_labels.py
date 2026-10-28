"""An EDGAR-derived figure is labelled with its OWN fiscal year, never the filing's.

companyfacts stamps every fact with `fy`, the fiscal year of the FILING that reported it, so a
comparative carried a later year: Climb Global's FCF for the year to 2019-12-31 printed "[FY2020]"
(#817's record, item 3), and the CIQ-empty fallback's series repeated a year where a 10-K's three
comparative columns all carried its own stamp. `concepts.fiscal_year_of` names a period by the year
of the annual report that states it as its own, and refuses — the end date is printed instead — a
stamp that names two periods or is no year at all
(`docs/records/2026-10-28-a-label-names-its-own-year-and-a-rate-its-own-quote.md`).

Every pin runs on a FROZEN real filer (`tests/fixtures/stale_annual/CLMB.json`,
`tests/fixtures/fiscal_calendar/`, READMEs there); the values pinned are what those files hold.
"""
from __future__ import annotations

import json
import pathlib
import re
from datetime import date
from typing import Any

from vinci.dossier import anchor
from vinci.dossier.edgar_fundamentals import EdgarFundamentals, _period_label
from vinci.edgar.concepts import (
    ConceptPoint,
    annual_by_period,
    extract_points,
    fiscal_year_ends,
    fiscal_year_of,
    points_for_tag,
)

_ROOT = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def _facts(path: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((_ROOT / path).read_text())
    return facts


CLMB = "stale_annual/CLMB.json"


def _ocf(facts: dict[str, Any], end: str) -> ConceptPoint:
    """The point the readers serve for the year to ``end``: the latest FILED (a comparative)."""
    return annual_by_period(extract_points(facts, "operating_cash_flow"))[date.fromisoformat(end)]


def _series(text: str, name: str) -> list[str]:
    """The labels of one ``Name: L v → L v`` series of a fallback string, in order."""
    body = text.split(f"{name}: ", 1)[1].split(";", 1)[0].split("  [", 1)[0]
    return [part.rsplit(" ", 1)[0] for part in body.split(" → ")]


# --- POSITIVE: a comparative is labelled with its own year ----------------------------------------


def test_climbs_2019_fcf_is_labelled_fy2019_not_the_filings_fy2020() -> None:
    """#817's case: the point served for 2019 is the FY2020 10-K's comparative, stamped 2020."""
    facts = _facts(CLMB)
    point = _ocf(facts, "2019-12-31")
    assert point.fy == 2020 and point.form == "10-K"          # the stamp the label used to read
    ends = fiscal_year_ends(facts)
    assert fiscal_year_of(ends, point) == 2019
    assert _period_label(point, ends) == "FY2019"
    assert anchor._period_label(point, facts) == ("FY2019", False)


def test_the_fallbacks_fcf_series_names_each_year_once_and_in_order() -> None:
    """The series the page prints: main read "FY2017 8 → FY2018 -2 → FY2018 -2 → FY2019 14 →
    FY2020 3", each comparative under the year of the 10-K that last carried it."""
    traj = EdgarFundamentals(_facts(CLMB)).multi_year_trajectory().value
    assert traj is not None
    assert _series(traj, "FCF") == ["FY2015", "FY2016", "FY2017", "FY2018", "FY2019"]
    assert "FY2019 3" in traj
    revenue = [lb for lb in _series(traj, "Revenue") if lb.startswith("FY")]
    assert revenue == sorted(set(revenue))                     # no year twice, never backwards


# --- NEGATIVE: the year a 10-K states as its own keeps its label ---------------------------------


def test_a_current_year_from_its_own_10k_keeps_its_label() -> None:
    facts = _facts(CLMB)
    point = _ocf(facts, "2025-12-31")
    assert point.fy == 2025                                    # its own 10-K: the stamp was right
    assert _period_label(point, fiscal_year_ends(facts)) == "FY2025"
    assert anchor._period_label(point, facts) == ("FY2025", False)


def test_a_20f_filers_year_is_read_from_its_20f() -> None:
    """TAT Technologies files 20-Fs: no 10-K states any of its years, and the year stays named."""
    got = anchor._latest_fcf(_facts("fiscal_calendar/TATT.json"))
    assert not isinstance(got, str)
    assert got[1] == "latest FY2025 (not LTM)"


# --- REFUSED: a stamp that cannot name the year prints the end date -------------------------------


def test_a_stamp_naming_two_periods_names_neither() -> None:
    """Wolverine stamps the 10-Ks for the years to 2024-12-28 and 2026-01-03 both 2024; main
    labelled its anchor FCF for the year to 2026-01-03 "latest FY2024"."""
    facts = _facts("fiscal_calendar/WWW.json")
    assert fiscal_year_ends(facts)[2024] == (date(2024, 12, 28), date(2026, 1, 3))
    got = anchor._latest_fcf(facts)
    assert not isinstance(got, str)
    assert got[1] == "latest year to 2026-01-03 (not LTM)"
    assert "FY" not in got[2]
    earlier = _ocf(facts, "2024-12-28")
    assert fiscal_year_of(fiscal_year_ends(facts), earlier) is None


def test_a_stamp_that_is_no_year_is_refused() -> None:
    """Priority Technology stamps two 10-Ks 43465 and 43830; main printed "FY43465 344"."""
    traj = EdgarFundamentals(_facts("fiscal_calendar/CIK1653558.json")).multi_year_trajectory()
    assert traj.value is not None
    labels = _series(traj.value, "Revenue")
    assert labels[:4] == ["FY2016", "FY2017", "2018-12-31", "2019-12-31"]
    assert not any(re.fullmatch(r"FY\d{5,}", lb) for lb in labels)


def test_a_quarter_ending_on_a_fiscal_year_end_is_no_fiscal_year() -> None:
    """Climb's FY2018 10-K tags its fourth quarter (2018-10-01 → 2018-12-31) `fp="FY"`, ending
    with the fiscal year; a quarter is not that year."""
    facts = _facts(CLMB)
    q4 = [p for p in points_for_tag(facts, "RevenueFromContractWithCustomerExcludingAssessedTax")
          if p.period_end == date(2018, 12, 31) and p.period_start == date(2018, 10, 1)]
    assert q4 and all(p.fp == "FY" and p.form == "10-K" for p in q4)
    assert all(fiscal_year_of(fiscal_year_ends(facts), p) is None for p in q4)
