"""CIQ's revenue guide is checked against the release OF ITS OWN DATE (2026-10-27, VRRM).

THE DEFECT. The guide check set CIQ's latest revenue guide against the NEWEST release's, whatever
either was dated. VRRM's committed page (main 47d8ca27) reads "CIQ 985.0–995.0 vs release
945.0–965.0 → MISMATCH flag", and the data-quality scorecard counts it differs-unexplained. CIQ's
guide row is dated 2026-05-26 — the day of the release that states $985–995M — and the release it
was compared with was filed 2026-08-05, after CIQ's export (2026-07-30), when management cut the
guide to $945–965M. The two sources agree; they were read at different vintages.

MEASURED FIRST (2026-10-27, the 27 committed pages): in every page with both dates, CIQ's guide
date equals a release's filing date to the day (16 of 16). Comparing against the newest
guide-bearing release filed on or before CIQ's date moves ONE page's outcome, VRRM's
(differ → agree); every other page compares the same release as before.

THE FIXTURES are VRRM's committed rows, frozen at main 47d8ca27: its four releases' revenue
guidance verbatim, and CIQ's revenue guide row from the guidance bridge.
"""
from __future__ import annotations

from datetime import date, timedelta

from vinci.dossier import mechanical as dm
from vinci.dossier.ciq_sheets import revenue_guide_from_rows
from vinci.dossier.schemas import CHECK_AGREE, CHECK_DIFFER, GuidanceRow, ReleaseExtract
from vinci.edgar.primary_source import GuideVerification


def _release(filed: str, acc: str, low: float, high: float, period: str,
             verbatim: str) -> ReleaseExtract:
    src = f"8-K {acc} EX-99.1"
    return ReleaseExtract.model_validate({
        "filed": filed, "source_ref": src,
        "guidance": [{"metric": "revenue", "period": period, "low": low, "high": high,
                      "unit": "$M", "basis": "level", "qualitative": False,
                      "verbatim": verbatim, "source_ref": src}]})


#: VRRM's releases, most recent first, as the committed page stores them
_VRRM_RELEASES = [
    _release("2026-08-05", "0001193125-26-335111", 945.0, 965.0, "2026",
             "Total Revenue of $945 million to $965 million"),
    _release("2026-05-26", "0001193125-26-239351", 985.0, 995.0, "2026",
             "Total Revenue of $985 million to $995 million"),
    _release("2026-05-06", "0001193125-26-209031", 1020.0, 1030.0, "2026",
             "Total Revenue of $1,020 million to $1,030 million"),
    _release("2026-02-24", "0001193125-26-067015", 1020.0, 1030.0, "next-fy",
             "Total Revenue of $1,020 million to $1,030 million"),
]
#: CIQ's revenue guide row on VRRM's committed page (the guidance bridge)
_VRRM_CIQ_ROW = GuidanceRow(metric="Revenue", latest_guide="'985.00 - 995.00'", period="FY 2026",
                            dated="2026-05-26", age="80d (stale)",
                            record="actual ≥ floor 7/8 · 2 at-guide (±0.5% of a point, "
                                   "not adjudicated)", most_recent="FY 2025 MET")


def _check(ciq_dated: date | None, lo: float = 985.0,
           hi: float = 995.0) -> GuideVerification:
    return dm._guide_verification(_VRRM_RELEASES, ciq_lo=lo, ciq_hi=hi, ciq_period="FY 2026",
                                  ciq_dated=ciq_dated)


def test_vrrm_ciq_guide_agrees_with_the_release_of_its_own_date() -> None:
    """THE RED, on VRRM's committed rows. The page's CIQ row carries its date, the guide is set
    against the release filed that day, and it agrees; the later cut is named, never hidden."""
    lo, hi, period, dated = revenue_guide_from_rows([_VRRM_CIQ_ROW])
    assert (lo, hi, period, dated) == (985.0, 995.0, "FY 2026", date(2026, 5, 26))
    got = dm._guide_verification(_VRRM_RELEASES, ciq_lo=lo, ciq_hi=hi, ciq_period=period,
                                 ciq_dated=dated)
    assert got.check == CHECK_AGREE
    assert got.line == (
        "guide verification (revenue): CIQ 985.0–995.0 vs release 985.0–995.0 → cross-source "
        "VERIFIED; a later release (filed 2026-08-05, 2026) guides 945.0–965.0 — CIQ's guide "
        "predates it")


def test_a_vendor_misread_at_the_same_vintage_still_differs() -> None:
    """(−) The check still catches CIQ. A guide dated 2026-08-05 that read $985–995M against the
    release of that day ($945–965M) is a MISMATCH, with no later release to name."""
    got = _check(date(2026, 8, 5))
    assert got.check == CHECK_DIFFER
    assert got.line == ("guide verification (revenue): CIQ 985.0–995.0 vs release 945.0–965.0 → "
                        "MISMATCH flag")


def test_a_release_filed_inside_the_filing_lag_is_the_same_vintage() -> None:
    """An 8-K accepted after EDGAR's 5:30 pm cutoff is dated the next business day, so a release
    filed up to `_GUIDE_FILING_LAG_DAYS` after CIQ's date is CIQ's vintage (a Friday release filed
    Monday); one filed a day later is not."""
    filed = date(2026, 8, 5)
    inside = _check(filed - timedelta(days=dm._GUIDE_FILING_LAG_DAYS), 945.0, 965.0)
    assert inside.check == CHECK_AGREE
    outside = _check(filed - timedelta(days=dm._GUIDE_FILING_LAG_DAYS + 1), 945.0, 965.0)
    assert outside.check == CHECK_DIFFER
    assert "a later release (filed 2026-08-05, 2026) guides 945.0–965.0" in outside.line


def test_a_guide_with_no_date_is_set_against_the_newest_release() -> None:
    """A CIQ guide that carries no date keeps the old comparison — the newest guide-bearing
    release — and names no later release, since none can be later than an undated guide."""
    got = _check(None)
    assert got.check == CHECK_DIFFER
    assert "later release" not in got.line


def test_a_later_release_restating_the_same_guide_is_not_named() -> None:
    """VITL's shape: CIQ dated the May guide and the August release restates it. CIQ's guide is
    still the one in force, so nothing predates anything."""
    same = [_release("2026-08-06", "0000000000-26-000002", 985.0, 995.0, "2026", "x"),
            *_VRRM_RELEASES[1:]]
    got = dm._guide_verification(same, ciq_lo=985.0, ciq_hi=995.0, ciq_period="FY 2026",
                                 ciq_dated=date(2026, 5, 26))
    assert got.check == CHECK_AGREE
    assert "later release" not in got.line
