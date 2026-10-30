"""Phase 2 C2 — the share readers outside the dossier read a count tagged after its filing by the
rule #871 shipped (audit X1(a), operator ruling 2026-10-30 "Yes, cross-check").

The screen's share change, the rank's dilution demote and the theme desk's basis check each took a
count at its tagged date. REPX's 2024 count, tagged 2029, became the newest point and anchored a
window with nothing else in it, so the screen read UNKNOWN where REPX's real 2026 counts show a
change; THM's 2023 count, tagged 2033, did the same. None of these readers is assembling one name,
so none may fetch a cover: such a count is dated at its filing day, an upper bound printed
"filed <date>", and still cross-checked against its filing's other counts
(`vinci.edgar.cover_count.share_series`, the one reader they share).

Fixtures are real: the share tags of AAL's, REPX's and THM's companyfacts
(`tests/fixtures/cover_count`) and VRRM's committed companyfacts subset."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.edgar.client import EdgarClient
from vinci.edgar.concepts import extract_points
from vinci.rank.structural import _shares_for
from vinci.schemas.envelope import CoverageStatus
from vinci.screens.assemble import share_change_field
from vinci.theme_intelligence.market import desk_points

_ROOT = Path(__file__).resolve().parent.parent
_FIX = _ROOT / "tests" / "fixtures" / "cover_count"


def _facts(name: str) -> dict[str, Any]:
    path = _FIX / f"{name}.json" if name != "VRRM" else (
        _ROOT / "tests" / "fixtures" / "companyfacts" / "VRRM.json")
    return cast(dict[str, Any], json.loads(path.read_text()))


class _Edgar:
    def __init__(self, facts: dict[str, Any]) -> None:
        self.facts = facts

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts


def _vrrm_newest_scaled(k: float) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads(json.dumps(_facts("VRRM")))
    for r in facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]:
        if r["accn"] == "0001193125-26-335490":
            r["val"] = round(r["val"] * k)
    return facts


# ─── the screen's share change ────────────────────────────────────────────────────────────────

def test_the_screen_reads_repx_real_newest_count() -> None:
    """REPX's 2029 tag (a 2024 count) anchored the window and left it one point wide: UNKNOWN."""
    f = share_change_field(_facts("REPX"))
    assert f.coverage_status is CoverageStatus.PRESENT
    assert f.as_of == date(2026, 8, 3) and "22,153,785 (2026-08-03)" in (f.note or "")


def test_the_screen_prints_a_filing_day_bound_as_one() -> None:
    """AAL's count tagged 2027-07-17 in a 10-Q filed 2026-07-23 ends the window at its filing day,
    printed as "filed", never as the count's own date."""
    f = share_change_field(_facts("AAL"))
    assert f.coverage_status is CoverageStatus.PRESENT
    assert f.as_of == date(2026, 7, 23)
    assert "661,969,951 (filed 2026-07-23)" in (f.note or "") and "2027" not in (f.note or "")


def test_a_correctly_dated_series_reads_as_before() -> None:
    """The negative pin: VRRM's correctly-dated counts keep their dates; its future-dated ones
    (no cover fetched here) read at their filing days."""
    f = share_change_field(_facts("VRRM"))
    assert f.coverage_status is CoverageStatus.PRESENT and "filed 2026-08-05" in (f.note or "")


def test_a_refused_count_in_the_window_makes_the_screen_change_unknown() -> None:
    """VRRM's newest count mutated 20% high disagrees with its 10-Q's diluted average past 10%:
    the change across it is UNKNOWN, naming the refusal — never measured around it."""
    f = share_change_field(_vrrm_newest_scaled(1.2))
    assert f.coverage_status is CoverageStatus.UNKNOWN
    assert "UNKNOWN" in (f.note or "") and "0001193125-26-335490" in (f.note or "")


# ─── the rank's dilution demote ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("name", "newest"), [
    ("REPX", date(2026, 8, 3)), ("THM", date(2026, 5, 1)), ("AAL", date(2026, 7, 23))])
def test_the_rank_series_ends_at_a_date_its_filing_could_state(name: str, newest: date) -> None:
    series = _shares_for(cast(EdgarClient, _Edgar(_facts(name))), "x")
    assert series is not None and max(d for d, _ in series) == newest


def test_a_refused_count_in_the_window_leaves_the_rank_no_series() -> None:
    """Demote-only: a change across an UNKNOWN count is not evaluated, so no dilution flag can
    rest on a count its own filing contradicts."""
    assert _shares_for(cast(EdgarClient, _Edgar(_vrrm_newest_scaled(1.2))), "x") == []
    assert _shares_for(cast(EdgarClient, _Edgar(_facts("VRRM"))), "x")  # the negative pin


# ─── the theme desk's basis check ─────────────────────────────────────────────────────────────

def test_the_desk_reads_no_share_count_after_its_filing() -> None:
    """THM's 2033 tag sorted last and would pair with nothing real; it reads at its 2023 filing
    day. The EPS points are untouched."""
    facts = _facts("THM")
    pts = desk_points(facts, None)
    shares = [p for p in pts if p.concept == "shares"]
    assert shares and all(p.period_end <= p.filed for p in shares)
    raw = [p for p in extract_points(facts, "shares") if p.value]
    assert any(p.period_end > p.filed for p in raw)  # the slip is in the fixture
    assert len(shares) == len(raw)  # nothing refused, nothing dropped


def test_a_series_refused_entire_names_its_refusal() -> None:
    """Review round 1: with every count in reach refused, the window had no kept point to open
    from, so the note read "fewer than 2 usable XBRL share points" and named no refusal. VRRM kept
    to its five counts tagged after their filing, each scaled 1.5x against its filing's own
    counts."""
    facts: dict[str, Any] = json.loads(json.dumps(_facts("VRRM")))
    rows = facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    late = [r for r in rows if r["end"] > r["filed"]]
    assert len(late) == 5
    for r in late:
        r["val"] = round(r["val"] * 1.5)
    facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"] = late
    f = share_change_field(facts)
    assert f.coverage_status is CoverageStatus.UNKNOWN
    assert "UNKNOWN" in (f.note or "") and "fewer than 2" not in (f.note or "")
