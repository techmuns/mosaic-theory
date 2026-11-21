"""Two guides for DIFFERENT FISCAL YEARS are not cross-checked — never a MISMATCH across years.

WHY (BRBR, the $0 pre-spend check of its FY26 rebuild, 2026-11-21). The page would have printed
``guide verification (revenue): CIQ 2320.0–2420.0 vs release 2335.0–2375.0 → MISMATCH flag``.
CIQ's guide is **FY 2027** (dated 2026-11-18, the day of the Q4 release) and the release guide the
check read is **2026** (the 2026-08-04 8-K): the 11-18 release carries no guide the parser reads,
so the newest one that does is a year older. Two years' guides cannot agree or disagree, and the
check reported them as contradicting — the same false MISMATCH the cross-SCOPE refusal (quarter vs
year, `test_guide_period_alignment.py`) already stops, one level down: both labels name a YEAR,
just not the same one.

THE RULE. When BOTH labels state a fiscal year and the years differ, refuse (NOT CROSS-CHECKED).
A label that states no year (``Q3``, ``next-fy``) decides nothing and the check runs as before —
inventing a year would manufacture the refusal, exactly as `period_scope` declines to invent a
scope.

WHAT IT DOES NOT DO (coordinator A, 2026-11-21, half (b), waiting on #1157): say that the newer
releases carry no parsed guide. LLY's live MISMATCH is that case — CIQ FY 2026 91,000–92,000
(dated 2026-10-29) against the 2026-02-04 release's 2026 80,000–83,000 — a SAME-year pair, so this
guard leaves it alone (pinned below), and the release dates that would explain it live in
`mechanical._guide_verification`, not here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.schemas import CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN
from vinci.edgar.primary_source import guide_verification_read, period_fiscal_year

_FIXTURE = Path(__file__).parent / "fixtures" / "guide_years_brbr.json"


def _brbr() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return data


def test_brbr_fy27_ciq_guide_against_its_fy26_release_guide_is_refused() -> None:
    """THE REGRESSION, on BRBR's real pair. The old check compared the numbers and returned
    MISMATCH; it must refuse, name both years, and record that the check did not run."""
    f = _brbr()
    ciq, rel = f["ciq"], f["release"]
    out = guide_verification_read(
        "revenue", ciq["low"], ciq["high"], release_low=rel["low"], release_high=rel["high"],
        release_basis=rel["basis"], ciq_period=ciq["period"], release_period=rel["period"])
    assert "MISMATCH" not in out.line
    assert "NOT CROSS-CHECKED, different fiscal years" in out.line
    assert ciq["period"] in out.line and rel["period"] in out.line
    assert "2320.0" in out.line and "2335.0" in out.line  # both sides' numbers stay checkable
    assert out.check == CHECK_NOT_RUN


def test_the_shipped_line_is_reproduced_without_the_periods() -> None:
    """THE BEFORE, in one place: withholding the period labels reproduces the line main
    `4b7f804d` built for this pair, so the defect is demonstrated, not merely described."""
    f = _brbr()
    ciq, rel = f["ciq"], f["release"]
    shipped = guide_verification_read(
        "revenue", ciq["low"], ciq["high"], release_low=rel["low"], release_high=rel["high"])
    assert shipped.line == f["line_at_4b7f804d"]
    assert shipped.check == CHECK_DIFFER


def test_a_same_year_mismatch_still_flags_and_a_same_year_match_still_verifies() -> None:
    """THE NEGATIVE PIN. The year guard must not swallow the check it guards: BRBR's labels with
    the year made the SAME — CIQ "FY 2026" against the release's "2026" — and different numbers
    still read MISMATCH; equal numbers still read VERIFIED."""
    rel = _brbr()["release"]
    mismatch = guide_verification_read(
        "revenue", 2320.0, 2420.0, release_low=rel["low"], release_high=rel["high"],
        ciq_period="FY 2026", release_period=rel["period"])
    assert "MISMATCH flag" in mismatch.line
    assert "different fiscal years" not in mismatch.line
    assert mismatch.check == CHECK_DIFFER

    verified = guide_verification_read(
        "revenue", rel["low"], rel["high"], release_low=rel["low"], release_high=rel["high"],
        ciq_period="FY 2026", release_period=rel["period"])
    assert "cross-source VERIFIED" in verified.line
    assert verified.check == CHECK_AGREE


def test_lly_same_year_pair_is_not_decided_by_the_year_guard() -> None:
    """LLY's committed pair (`data/dossiers/LLY/dossier.json` at 4b7f804d): CIQ FY 2026
    91,000–92,000 against the release's 2026 80,000–83,000. One year on both sides, so this guard
    does not touch it — half (b) owns that page's line. Asserted as the guard's ABSENCE, so (b)
    landing does not red it."""
    out = guide_verification_read(
        "revenue", 91_000.0, 92_000.0, release_low=80_000.0, release_high=83_000.0,
        ciq_period="FY 2026", release_period="2026")
    assert "different fiscal years" not in out.line


def test_a_label_without_a_year_leaves_the_check_as_it_was() -> None:
    """``next-fy`` and a bare ``Q3`` state no year, so the pair is compared exactly as before —
    the refusal is never manufactured from a label that decides nothing."""
    for rel_period in ("next-fy", "Q3"):
        ciq_period = "FY 2027" if rel_period == "next-fy" else "FQ3 2026"
        out = guide_verification_read(
            "revenue", 2320.0, 2420.0, release_low=2335.0, release_high=2375.0,
            ciq_period=ciq_period, release_period=rel_period)
        assert "different fiscal years" not in out.line
        assert "MISMATCH flag" in out.line


def test_two_quarters_of_different_years_are_refused_too() -> None:
    """Same scope, different year: FQ3 2026 against Q3 2025 is a different period, and the year
    each label states decides it."""
    out = guide_verification_read(
        "revenue", 600.0, 610.0, release_low=560.0, release_high=570.0,
        ciq_period="FQ3 2026", release_period="Q3 2025")
    assert "NOT CROSS-CHECKED, different fiscal years" in out.line
    assert "MISMATCH" not in out.line


@pytest.mark.parametrize(("label", "year"), [
    # every label shape the corpus hands the check (the CIQ side `FQ*`/`FY*`; the release side
    # `2024`/`2026`/`Fiscal 2028`/`Q1`–`Q4`/`next-fy`, per `primary_source._HALF_PERIOD`'s census)
    ("FY 2027", 2027), ("FQ3 2026", 2026), ("2026", 2026), ("2024", 2024),
    ("Fiscal 2028", 2028), ("Q3", None), ("next-fy", None), (None, None), ("", None),
    # two different years name no one year: undecidable, never the first or the last
    ("FY 2026/2027", None),
])
def test_period_fiscal_year(label: str | None, year: int | None) -> None:
    assert period_fiscal_year(label) == year
