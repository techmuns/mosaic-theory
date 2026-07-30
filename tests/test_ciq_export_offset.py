"""CIQ'S ``As-Of`` IS THE EXPORT DATE; THE DATA IS THE PRIOR CLOSE.

MEASURED 11 OF 11, not inferred from one name. CIQ's printed ``Day Close Price Latest`` was compared
against the Polygon store for every committed dossier:

    name   CIQ px   As-Of        close ON    close PRIOR
    SMPL    10.28   2026-07-24      10.22          10.28   <- PRIOR
    EPAM   100.40   2026-07-29     106.89         100.40   <- PRIOR
    CNXC    25.41   2026-07-29      26.56          25.41   <- PRIOR
    …all eleven matched PRIOR, none matched ON.

So every CIQ-derived as-of in the system read one trading day too NEW: panel ages understated, the
45-day ceiling passing a day early, fleet-wide.

WHY THE PRIOR *BAR*, NEVER ``date - 1`` (operator). Two stamps land on a Monday — NCNO's 2026-07-20
and VITL's 2026-06-29 — where the correction is THREE calendar days. A calendar-day version is right
on nine names, wrong on those two, and wrong again on every market holiday. Reading the store's own
prior bar handles weekends and holidays without a calendar.
"""
from __future__ import annotations

import datetime as dt

from vinci.dossier.freshness import corrected_ciq_as_of


class _Bar:
    def __init__(self, d: str) -> None:
        self.bar_date = d


# A real trading week: Fri 07-17, then Mon 07-20 … Fri 07-24, Mon 07-27 … Wed 07-29.
WEEK = [_Bar(d) for d in ("2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22",
                          "2026-07-23", "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29")]


def test_a_weekday_stamp_moves_back_one_trading_day() -> None:
    """The ordinary case, nine of eleven. SMPL's 07-24 stamp is the 07-23 close."""
    assert corrected_ciq_as_of("2026-07-24", WEEK) == "2026-07-23"
    assert corrected_ciq_as_of("2026-07-29", WEEK) == "2026-07-28"


def test_a_monday_stamp_moves_back_three_calendar_days() -> None:
    """THE RED, and the reason this reads the store instead of subtracting. NCNO's As-Of is
    2026-07-20, a Monday, so the data is the FRIDAY 07-17 close — three calendar days, not one.
    A `date - 1` version returns 07-19, a Sunday, on which no bar exists.

    VITL's 2026-06-29 is the second instance. The operator's first framing called NCNO the only
    Monday in the fleet; measuring found two, which is exactly why the calendar is not hardcoded."""
    assert corrected_ciq_as_of("2026-07-20", WEEK) == "2026-07-17"
    assert dt.date.fromisoformat("2026-07-20").weekday() == 0
    naive = dt.date.fromisoformat("2026-07-20") - dt.timedelta(days=1)
    assert naive.weekday() == 6, "the naive version lands on a Sunday"
    assert str(naive) not in {b.bar_date for b in WEEK}


def test_a_holiday_gap_is_handled_without_a_calendar() -> None:
    """No holiday table anywhere. A four-day gap in the bars resolves to the last real session,
    which is what makes this correct in October without anyone updating a list."""
    bars = [_Bar("2026-11-25"), _Bar("2026-11-30")]  # Thanksgiving week
    assert corrected_ciq_as_of("2026-11-30", bars) == "2026-11-25"


def test_an_empty_store_returns_the_stamp_unchanged() -> None:
    """FAIL-SAFE, and the direction is deliberate. With no bar before the stamp there is nothing to
    resolve from, and INVENTING a date is the fabrication this repo refuses. An uncorrected age is
    one day too NEW — the gate reads it as fresher, which is the miss — but it is recoverable by
    refreshing the store, whereas a fabricated date is not recoverable at all.

    An empty store is a KNOWN worktree state here, so this path is live, not theoretical."""
    assert corrected_ciq_as_of("2026-07-24", []) == "2026-07-24"


def test_a_stamp_older_than_every_bar_is_unchanged() -> None:
    """The other end of the same fail-safe: a stamp predating the store's history has no prior bar
    either, and must not silently resolve forward to the earliest one."""
    assert corrected_ciq_as_of("2020-01-02", WEEK) == "2020-01-02"


def test_the_correction_never_moves_a_stamp_forward() -> None:
    """The invariant that keeps this honest: correcting a stamp may only make a build look OLDER,
    never fresher. A forward move would mean the gate started passing something it used to refuse,
    which is the opposite of the defect being fixed."""
    for stamp in ("2026-07-17", "2026-07-20", "2026-07-24", "2026-07-29", "2026-08-15"):
        assert corrected_ciq_as_of(stamp, WEEK) <= stamp


def test_it_is_wired_into_the_tev_stamp() -> None:
    """A correction nobody calls is not a correction. Matches the EXACT call — a comment naming the
    function would satisfy a bare-name search while the stamp stayed uncorrected."""
    import inspect

    import vinci.dossier.mechanical as dm

    src = inspect.getsource(dm._implied_expectations)
    assert "corrected_ciq_as_of(stated_as_of, price_bars)" in src, (
        "the TEV stamp is not being corrected — every CIQ as-of stays a day too new")
    caller = inspect.getsource(dm.assemble_mechanical)
    assert "store.get_price_history(record.identity.internal_id)" in caller, (
        "the bars never reach _implied_expectations, so the correction cannot fire")
