"""Guides covering different PERIODS are not cross-checked, and a percentile says how long it is.

WHY (NFLX, found by the analyst reading the committed page). The dossier printed
``guide verification (revenue): CIQ 12860.0–12860.0 vs release 50.7–51.7 → MISMATCH flag``. Nothing
about it was true as a verification. CIQ's guide is **FQ3 2026** — one quarter, 12,860.0 — and the
release guides **FY2026**, $50.7–51.7bn. Four quarters at CIQ's own number is 51,440, INSIDE the
annual guide: the two sources corroborate, and the check reported them as contradicting.

THE FAILURE MODE. A MISMATCH on revenue guidance reads as management missing its own number, which
is exactly the evidence an underwriter weighs against a name. Here it was an artefact of comparing
a quarter to a year, and it is not NFLX-specific — any name whose CIQ guide period differs from the
period its release guides gets one.

WHY NOT ANNUALISE. Multiplying the quarter by four to force the comparison would manufacture the
base the check exists to verify (a guide is not four equal quarters), which is precisely what the
CROSS-BASIS refusal beside it already rejects. Refusing loses nothing: an unverifiable pair was
never verification.

THE SECOND PIN. ``ev_ebitda_percentile_5y`` holds every quarterly Close the workbook carries —
NFLX's is 38 of them spanning 9.4 years, not the five the field name implies. The count alone did
not reveal it. The value is unchanged (the full history is the better distribution); the span is
now stated, so the window cannot be assumed from the name.
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.dossier.ciq_sheets import _quarterly_span_label
from vinci.edgar.primary_source import guide_verification, period_scope

# NFLX's real pair, from the committed dossier: CIQ Estimates→Guidance revenue for FQ3 2026, and
# the 2026-04-16 EX-99.1 annual guide. Frozen — filed numbers, so this pin cannot rot.
_NFLX_CIQ_FQ3 = 12_860.0
_NFLX_RELEASE_FY26 = (50_700.0, 51_700.0)


def test_quarter_vs_annual_guide_is_refused_not_flagged_as_mismatch() -> None:
    """THE REGRESSION. The old check compared the two numbers and returned MISMATCH; it must now
    refuse. Asserting the absence of MISMATCH is the discriminating half — a refusal that still
    carried the word would keep reading as a miss to anyone scanning the page."""
    out = guide_verification(
        "revenue", _NFLX_CIQ_FQ3, _NFLX_CIQ_FQ3,
        release_low=_NFLX_RELEASE_FY26[0], release_high=_NFLX_RELEASE_FY26[1],
        ciq_period="FQ3 2026", release_period="2026")
    assert "NOT CROSS-CHECKED" in out
    assert "MISMATCH" not in out
    assert "QUARTER" in out and "YEAR" in out  # names WHICH scopes, so the refusal is checkable
    assert "FQ3 2026" in out and "2026" in out
    assert " a YEAR" in out and " a QUARTER" in out  # reads as English, not "a ANNUAL"


def test_the_broken_case_is_reproducible_without_the_period_and_fixed_with_it() -> None:
    """THE BEFORE/AFTER, in one place. Withholding the period labels reproduces the exact string the
    committed NFLX dossier shipped — so the defect is demonstrated, not merely described — and
    supplying them refuses instead. Without this, the fix is pinned only by its own new symbols."""
    shipped = guide_verification(
        "revenue", _NFLX_CIQ_FQ3, _NFLX_CIQ_FQ3,
        release_low=_NFLX_RELEASE_FY26[0], release_high=_NFLX_RELEASE_FY26[1])
    assert "MISMATCH" in shipped  # the pre-fix behaviour, still reachable when nothing says period

    fixed = guide_verification(
        "revenue", _NFLX_CIQ_FQ3, _NFLX_CIQ_FQ3,
        release_low=_NFLX_RELEASE_FY26[0], release_high=_NFLX_RELEASE_FY26[1],
        ciq_period="FQ3 2026", release_period="2026")
    assert "MISMATCH" not in fixed and "NOT CROSS-CHECKED" in fixed


def test_same_period_still_verifies_and_still_mismatches() -> None:
    """The refusal must not swallow the check it guards. Same scope → the prior behaviour exactly:
    matching ranges VERIFIED, differing ranges MISMATCH."""
    verified = guide_verification(
        "revenue", 50_700.0, 51_700.0, release_low=50_700.0, release_high=51_700.0,
        ciq_period="FY 2026", release_period="2026")
    assert "cross-source VERIFIED" in verified

    mismatch = guide_verification(
        "revenue", 48_000.0, 48_500.0, release_low=50_700.0, release_high=51_700.0,
        ciq_period="FY 2026", release_period="2026")
    assert "MISMATCH" in mismatch  # a REAL disagreement still fires


def test_undecidable_period_leaves_the_prior_behaviour_untouched() -> None:
    """An unrecognised (or absent) label must not manufacture a refusal — inventing a scope would
    silence real mismatches, the opposite failure. Every pre-existing caller passes no period."""
    for ciq_p, rel_p in [(None, None), ("FY 2026", None), (None, "2026"), ("whenever", "2026")]:
        out = guide_verification("revenue", 48_000.0, 48_500.0, release_low=50_700.0,
                                 release_high=51_700.0, ciq_period=ciq_p, release_period=rel_p)
        assert "MISMATCH" in out, f"{ciq_p!r}/{rel_p!r} must not be refused"


@pytest.mark.parametrize(
    ("label", "scope"),
    [
        ("FQ3 2026", "quarter"),   # CIQ quarterly — carries a year, and is still a quarter
        ("FQ4 2002", "quarter"),
        ("Q3", "quarter"),         # release quarterly
        ("FY 2026", "annual"),     # CIQ annual
        ("2026", "annual"),        # release annual (bare year)
        ("Fiscal 2028", "annual"),
        ("next-fy", "annual"),
        ("", None),
        (None, None),
        ("H1 2026", None),         # a half-year decides neither — refuse to guess
    ],
)
def test_period_scope_reads_both_vendors_labels(label: str | None, scope: str | None) -> None:
    """Every period shape the committed dossiers actually contain, on both sides of the check."""
    assert period_scope(label) == scope


def test_percentile_window_states_its_span_in_years() -> None:
    """THE SECOND REGRESSION. A count of quarters does not say how long the window is; NFLX's 38
    closes span 9.4 years under a field named ``_5y``. The span must be stated, and it must be the
    series' own — not a constant."""
    nflx = [date(2017, 3, 31), date(2020, 6, 30), date(2026, 5, 29)]
    label = _quarterly_span_label(nflx)
    assert "spanning 2017-03-31..2026-05-29" in label
    assert "(9.2y)" in label  # measured from the dates themselves
    assert "5y" not in label.replace("2026-05-29", "")  # never asserts the field name's window

    short = _quarterly_span_label([date(2024, 3, 31), date(2025, 3, 31)])
    assert "(1.0y)" in short


def test_percentile_span_is_omitted_rather_than_guessed() -> None:
    """Unparseable headers → no span. An omitted window is honest; a guessed one would put a
    fabricated window on the label whose whole job is to stop a window being assumed."""
    assert _quarterly_span_label(["not-a-date", None, 42]) == ""
    assert _quarterly_span_label([date(2024, 3, 31)]) == ""  # one date spans nothing
