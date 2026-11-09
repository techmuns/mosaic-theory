"""A point guide is the range [low, low] (TeamNostra fix request 2, RE1-D16).

`primary_source.guide_verification_read` compared highs as `(ciq_high or 0.0) - (release_high or
0.0)`, so a guide with no high read as one whose high is zero. TeamNostra's case: CIQ guides a
point of -0.05 (no high) and the release guides -0.05 to 0.00 — and the check read "cross-source
VERIFIED", where -0.05 to 0.10 read "differ". A check that passes on a failure. The same
expression failed the other way too: a point CIQ states as a range of one (11,800–11,800) against
the release's point 11,800 read MISMATCH, its high set against a zero.

On the 28 pages frozen at `bcda7ce3` every VERIFIED line compares two full ranges, so no committed
page carries the defect (each page's line read, 2026-11-10); these pins are the reproduction.
"""

from __future__ import annotations

import pytest

from vinci.edgar import primary_source as ps
from vinci.edgar.primary_source import CHECK_AGREE, CHECK_DIFFER


def test_a_point_guide_against_a_range_ending_at_zero_is_a_mismatch() -> None:
    """⊖ TeamNostra's reproduction: −0.05..None against −0.05..0.00 read VERIFIED."""
    r = ps.guide_verification_read("eps", -0.05, None, release_low=-0.05, release_high=0.0)
    assert r.check == CHECK_DIFFER and "MISMATCH" in r.line


def test_a_range_against_a_point_at_its_low_is_a_mismatch() -> None:
    """⊖ the mirror: CIQ guides −0.05..0.00 and the release states the point −0.05."""
    r = ps.guide_verification_read("eps", -0.05, 0.0, release_low=-0.05, release_high=None)
    assert r.check == CHECK_DIFFER


@pytest.mark.parametrize(("ciq", "release"), [
    ((-0.05, None), (-0.05, None)),          # a point against the same point
    ((11_800.0, 11_800.0), (11_800.0, None)),  # a range of one: read MISMATCH before
    ((240_000.0, 247_000.0), (240_000.0, 247_000.0)),  # a range against the same range
])
def test_a_point_or_a_range_that_agrees_still_verifies(
        ciq: tuple[float, float | None], release: tuple[float, float | None]) -> None:
    """⊕ the negative pins: agreement reads VERIFIED as before."""
    r = ps.guide_verification_read("revenue", ciq[0], ciq[1],
                                   release_low=release[0], release_high=release[1])
    assert r.check == CHECK_AGREE and "VERIFIED" in r.line


def test_a_range_against_a_wider_one_is_still_a_mismatch() -> None:
    """⊕ unchanged: −0.05..None against −0.05..0.10 differed before and differs now."""
    r = ps.guide_verification_read("eps", -0.05, None, release_low=-0.05, release_high=0.1)
    assert r.check == CHECK_DIFFER
