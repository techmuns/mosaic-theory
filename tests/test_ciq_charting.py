"""The CIQ Charting export — an unregistered workbook kind until 2026-09-03, and a sentinel that
looks exactly like a real multiple.

CORPUS-DERIVED, SYNTHETIC FIXTURE. The numbers are facts taken from the operator's 2026-09-03 WST
peers export (header row 35 labelled `Dates`; 42.0 repeated ahead of Fortrea/Stevanato/Avantor's
listings); the layout is rebuilt here so no licensed workbook enters the repo.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from vinci.dossier.ciq import _WORKBOOK_KEYWORDS
from vinci.dossier.ciq_charting import Spike, find_spikes, read_charting

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


# ---------------------------------------------------------------------------
# Single-day round-trips. SHAPES are corpus-observed (the 2026-09-03 WST peers
# export: 45 across 11 series x 2,512 dates, 14 of them inverted); the LEVELS
# here are synthetic, so no licensed value enters the repo.
# ---------------------------------------------------------------------------
_SPIKE_HDR = ["Dates", "Subject", "PeerA", "PeerB"]
#: Each case is walled off by quiet days, so no case can manufacture a spike in its neighbour.
#: (The first draft put the one-sided fall straight after the trend's peak and built a real
#: inverted-V out of the join — a fixture defect that would have read as a detector defect.)
_SPIKE_ROWS: list[list[object]] = [
    _SPIKE_HDR,
    [45000.0, 40.00, 20.00, 30.00],                    # 0  quiet
    [45001.0, 35.00, 20.05, 30.05],                    # 1  V, peers flat  -> name-specific
    [45002.0, 40.20, 20.02, 30.02],
    [45003.0, 40.10, 20.03, 30.03],                    # 3  quiet
    [45004.0, 46.00, 20.04, 30.04],                    # 4  INVERTED V — a V-only test misses it
    [45005.0, 40.50, 20.06, 30.06],
    [45006.0, 40.40, 20.05, 30.05],                    # 6  quiet
    [45007.0, 35.00, 17.00, 25.00],                    # 7  V, peers fall too -> MARKET-WIDE
    [45008.0, 40.00, 20.00, 30.00],
    [45009.0, 40.00, 20.00, 30.00],                    # 9  quiet
    [45010.0, 46.00, 20.00, 30.00],                    # 10 TREND — same direction twice
    [45011.0, 53.00, 20.00, 30.00],                    # 11 …neither day is a round-trip
    [45012.0, 53.10, 20.00, 30.00],
    [45013.0, 53.05, 20.00, 30.00],                    # 13 quiet
    [45014.0, 60.00, 20.00, 30.00],                    # 14 ONE-SIDED — big in, small out
    [45015.0, 59.00, 20.00, 30.00],
]

#: Serial 45000 is this date; the cases are named by it so a shifted fixture fails loudly.
_D0 = date(2023, 3, 15)


def _spikes(**kw: float) -> list[Spike]:
    return find_spikes(read_charting(_SPIKE_ROWS), "Subject", **kw)  # type: ignore[arg-type]


def test_the_detector_is_symmetric_and_catches_the_inverted_v() -> None:
    """THE REGRESSION. The first cut of this rule was written from the V that was noticed first;
    on the live export a V-only test returns 31 of 45 and drops the other 14 in silence — every
    one a day where consensus was cut BEFORE price caught up. Same defect, opposite order."""
    shapes = [s.shape for s in _spikes()]
    assert shapes == ["V", "inverted-V", "V"]
    assert _D0 + timedelta(days=4) in {s.when for s in _spikes()}
    assert shapes.count("inverted-V") == 1, "an inverted-V is the same defect, not a lesser one"


def test_a_trend_and_a_one_sided_move_are_not_round_trips() -> None:
    """NEGATIVE PIN. Rows 7-8 move +15% then +15%, rows 9-10 move +14% then −2%. Neither returns
    to where it started, so neither is a stale-denominator print — flagging them would delete real
    observations from a window."""
    days = {(s.when - _D0).days for s in _spikes()}
    assert 10 not in days and 11 not in days  # the trend's two legs
    assert 14 not in days                     # the one-sided move


def test_market_wide_is_reported_from_the_peers_and_never_applied() -> None:
    """SHAPE IS NOT CAUSE. The corpus case is 2020-03-16: a textbook V in WST, and all 9 series
    live that day fell >5% — the COVID crash, not a stale denominator. The flag is returned so a
    caller can judge; `find_spikes` drops nothing, because dropping is the judgement."""
    got = {(s.when - _D0).days: (s.market_wide, s.peers_moved, s.peers_live) for s in _spikes()}
    assert got[1] == (False, 0, 2)  # the subject moved alone
    assert got[7] == (True, 2, 2)   # the peers came too


def test_a_flat_peer_threshold_does_not_decide_the_verdict() -> None:
    """The 5% peer bar is a parameter, not a fact: raise it past the peers' own move and the
    market-wide day reads name-specific. Recorded so the number is never quoted bare."""
    strict = {(s.when - _D0).days: s.market_wide for s in _spikes(peer_threshold=0.20)}
    assert strict[7] is False
