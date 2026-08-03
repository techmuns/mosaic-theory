"""INSIDER ACTIVITY — the window is stated, the sides are never netted, absence carries its horizon.

THE INCIDENT. SMPL's page read `Open-market buys 2 · sells 0 (net +90.0K sh)`. Every part of that is
true of 182 days and the line said so nowhere. Measured over 24 months: **16 sales, 6 people,
$24.72M**, all discretionary (`aff10b5One` = '0' on all thirteen sale filings, no footnote plan) —
against $1.11M of buying. **The omission ran in the flattering direction: the page showed the buying
and hid the selling.**

AND "REPORT THE LAST OCCURRENCE" ALONE REPRODUCED IT, which the first real run caught. SMPL's most
recent sale is $0.11M nine months back; printing only that states a trivial last sale and implies it
is all there is. The largest is reported beside it.

Fixtures are real `Form4Line`s, per the house rule — never a hand-rolled stub with the attributes
the assertion wants.
"""
from __future__ import annotations

from datetime import date

from vinci.dossier.mechanical import (
    _INSIDER_SCAN_DAYS,
    _INSIDER_WINDOW_DAYS,
    Form4Line,
    compose_insider_line,
)

REF = date(2026, 7, 30)
LAST_FILING = date(2026, 7, 24)


def line(code: str, on: date, shares: float, price: float, who: str, role: str = "director"):
    return Form4Line(code=code, shares=shares, price=price, on=on, who=who, role=role)


#: SMPL's real shape, reduced: two buys inside the window, the selling episode 21 months out.
SMPL = [
    line("P", date(2026, 5, 14), 10_000, 11.78, "cikA"),
    line("P", date(2026, 4, 23), 80_000, 12.39, "cikB"),
    line("S", date(2025, 11, 11), 3_000, 36.00, "cikC", "VP, Controller and CAO"),
    line("S", date(2024, 11, 7), 225_912, 35.67, "cikD"),
    line("F", date(2026, 6, 1), 5_000, 12.00, "cikA"),
]


def compose(rows):
    return compose_insider_line(rows, reference_date=REF, last_filing=LAST_FILING)


def test_the_window_is_stated_on_the_face_of_the_count() -> None:
    """`sells 0` and `sells 0 in the last 182 days` are different claims; only the second is
    actionable. THE RED: drop the window clause and this is the sentence that shipped."""
    out = compose(SMPL)
    assert f"— in the last {_INSIDER_WINDOW_DAYS} days" in out
    assert "sells 0" in out


def test_the_sides_are_never_netted() -> None:
    """$1.1M of buying against $12.4M of selling nets to −$11.3M, which is LESS informative than the
    $1.1M alone. The old line printed exactly that net; it was latent rather than live only because
    no sale fell inside the window. No net may reappear in any form."""
    out = compose(SMPL)
    assert "net " not in out and "net+" not in out and "net-" not in out
    assert "buys 2" in out and "sells 0" in out            # two sides, reported separately


def test_counts_carry_people_and_dollars() -> None:
    """One insider selling $12M is a different fact from six selling $2M, and a share count cannot
    tell them apart."""
    out = compose(SMPL)
    assert "buys 2 (2 insiders, $1.11M)" in out


def test_the_largest_is_reported_when_it_is_not_the_last() -> None:
    """THE FIRST REAL RUN'S FINDING. Reporting only the most recent sale ($0.11M, 9mo) hides the
    $8.06M episode 21 months back — a smaller number in the same flattering direction as the count
    it replaced."""
    out = compose(SMPL)
    assert "last sale $0.11M, VP, Controller and CAO, 2025-11-11 (~9mo ago)" in out
    assert "largest sale $8.06M, director, 2024-11-07 (~21mo ago)" in out


def test_the_largest_is_suppressed_when_it_renders_identically() -> None:
    """NEGATIVE PIN. AORT's two largest buys differ by cents and both print `$0.26M`; repeating a
    number the reader cannot tell apart is noise dressed as a finding. Compared at the precision
    SHOWN, not the underlying float — so a sub-cent difference must NOT produce a second clause."""
    rows = [line("P", date(2026, 3, 1), 10_000, 26.0001, "cikA"),
            line("P", date(2025, 3, 1), 10_000, 26.0002, "cikB")]
    out = compose(rows)
    assert "last purchase $0.26M" in out
    assert "largest purchase" not in out


def test_absence_carries_its_horizon() -> None:
    """A bare "none" would break the visible-absence rule inside the fix written to honour it: this
    scan is BOUNDED, so an unqualified absence over-claims."""
    out = compose([line("P", date(2026, 5, 14), 10_000, 11.78, "cikA")])
    assert f"no sale in the {_INSIDER_SCAN_DAYS // 365}y scanned" in out


def test_tax_withholding_is_never_a_sale() -> None:
    """`F` is shares withheld on vesting — a withholding event with no decision in it. Measured on
    SMPL it is $1.24M against $24.72M of real sales. The fixture carries an F inside the window; it
    must not move the sell side, and must survive under `other`."""
    out = compose(SMPL)
    assert "sells 0" in out
    assert "F×1" in out


def test_the_other_segment_stays_last() -> None:
    """`render._fmt_insider` matches `other X×n` with a `$`-ANCHORED regex and silently leaves raw
    machine dialect on the page if anything follows it. Structural, so a later clause appended to
    the end of this line argues with a test instead of sliding past review."""
    assert compose(SMPL).rstrip().endswith("F×1")


def test_a_priced_gift_never_reports_as_a_dollar_sale() -> None:
    """A `G`/`A` line carries shares at NO price; multiplying by a defaulted 0.0 would report a real
    transfer as a $0 event, which reads as *nothing happened*."""
    assert Form4Line("G", 1_000, 0.0, date(2026, 1, 1), "cikA", "director").usd is None
    assert Form4Line("S", 1_000, 10.0, date(2026, 1, 1), "cikA", "director").usd == 10_000
