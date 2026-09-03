"""The CIQ Charting export — an unregistered workbook kind until 2026-09-03, and a sentinel that
looks exactly like a real multiple.

CORPUS-DERIVED, SYNTHETIC FIXTURE. The numbers are facts taken from the operator's 2026-09-03 WST
peers export (header row 35 labelled `Dates`; 42.0 repeated ahead of Fortrea/Stevanato/Avantor's
listings); the layout is rebuilt here so no licensed workbook enters the repo.
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.dossier.ciq import _WORKBOOK_KEYWORDS
from vinci.dossier.ciq_charting import read_charting

# `Dates` — NOT the documented `Pricing Date`/`Date`, which is why the notes' scan rule missed it.
_HDR = ["Dates", "West Pharmaceutical", "Stevanato Group", "Agilent Technologies"]
_ROWS: list[list[object]] = [
    [""] * 4, ["chart metadata"] + [""] * 3, _HDR,
    # Excel serials; Stevanato carries the 42.0 sentinel until it lists.
    [44000.0, 34.43, 42.0, 22.34],
    [44001.0, 34.41, 42.0, 22.41],
    [44002.0, 34.02, 42.0, 22.37],
    [44003.0, 33.06, 31.20, 21.35],
    [44004.0, 33.95, 30.80, 21.76],
]


def test_charting_is_a_registered_kind() -> None:
    """It was NOT, so `CiqBundle.from_files` dropped a charting export silently — no kind matched
    the filename and the loader's `continue` skipped it without a word."""
    name = "WST_Peers_Charting Excel Export - Sep 3rd 2026 2_30_56 pm.xls".lower()
    kinds = [k for k, kws in _WORKBOOK_KEYWORDS.items() if any(w in name for w in kws)]
    assert kinds == ["charting"]


def test_header_is_scanned_and_accepts_the_dates_label() -> None:
    s = read_charting(_ROWS)
    assert (s.header_row, s.date_label) == (2, "Dates")   # scanned, never hardcoded
    assert s.dates[0] == date(2020, 6, 18)


def test_a_leading_sentinel_run_is_dropped_and_counted() -> None:
    """POSITIVE PIN — the real shape: 42.0 repeated before a peer lists, then real data. It must
    become None, and the count must be reported, because a mean over it is silently corrupted."""
    s = read_charting(_ROWS)
    assert s.values["Stevanato Group"][:3] == (None, None, None)
    assert s.values["Stevanato Group"][3] == pytest.approx(31.20)
    val, n, first_real = s.sentinels["Stevanato Group"]
    assert (val, n, first_real) == (42.0, 3, date(2020, 6, 21))
    assert s.dropped == 3
    assert "DROPPED 3 sentinel cells" in s.report()   # never silent


def test_a_name_with_full_history_is_untouched() -> None:
    """NEGATIVE PIN — no leading run, so nothing is dropped. A value-based `== 42.0` filter would
    also pass here; the shape rule is what keeps a genuine 42.0 multiple readable."""
    s = read_charting(_ROWS)
    assert None not in s.values["West Pharmaceutical"]
    assert "West Pharmaceutical" not in s.sentinels


def test_a_single_leading_point_is_not_a_sentinel() -> None:
    """NEGATIVE PIN — the bug this test found. Agilent's first value differs from its second, and a
    first cut flagged that one cell as a sentinel run. A run must REPEAT."""
    s = read_charting(_ROWS)
    assert "Agilent Technologies" not in s.sentinels
    assert s.dropped == 3


def test_a_flat_series_is_not_mistaken_for_a_sentinel() -> None:
    """NEGATIVE PIN, and the one a value-based filter gets wrong: a column that never varies is a
    FLAT SERIES, not a pre-listing run. Dropping it would delete real data."""
    rows = [_HDR, [44000.0, 5.0, 42.0, 1.0], [44001.0, 5.0, 42.0, 1.0]]
    s = read_charting(rows)
    assert s.sentinels == {}
    assert s.values["Stevanato Group"] == (42.0, 42.0)


def test_peer_set_drift_is_reportable() -> None:
    """The median's constituents CHANGE over the window, so a spread must say which set."""
    s = read_charting(_ROWS)
    assert s.live_at(date(2020, 6, 18)) == 2     # Stevanato not yet listed
    assert s.live_at(date(2020, 6, 21)) == 3


def test_a_missing_header_fails_loud() -> None:
    with pytest.raises(ValueError, match="label set has widened"):
        read_charting([["something else", "a"], [1.0, 2.0]])
