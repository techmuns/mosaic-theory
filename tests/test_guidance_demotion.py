"""A twenty-four-year-old number sat in a column headed "Latest guide".

THE DEFECT. NFLX's guidance table opened with `Gross Margin % — '47.00 - 48.00' for FQ4 2002`,
dated **2002-10-17**, with the Age column two places right reading `8686d (stale)`. The eye takes
the figure; the caveat arrives too late. It is not one odd row — the builder picks the newest guide
with a PARSEABLE RANGE, so any company that STOPPED guiding a metric keeps surfacing whatever it
last said:

    NFLX  Gross Margin %       2002-10-17   8686d
    NFLX  EBITDA               2003-06-09   8451d
    EPAM  Capital Expenditure  2016-02-18   3814d
    AORT  EPS Normalized       2019-10-30   2441d
    UBER  Revenue              2020-04-17   2294d
    UBER  Capital Expenditure  2020-05-07   2274d
    V     Capital Expenditure  2020-10-28   2100d

THE TEST IS THE GUIDE'S PERIOD, NOT ITS ISSUE AGE (review finding, #423). Age was the first
criterion and it is WRONG IN BOTH DIRECTIONS, with a counterexample each way in this very corpus:

    VITL  Gross Margin %  dated 2023-11-02  977d  for **FY 2027**  → still ahead of a 2026 as-of
    MVST  Gross Margin %  dated 2025-11-10  238d  for **FY 2025**  → a year already finished

Long-term guidance stays applicable without being reissued, so calling VITL's "none current" is
simply false; and MVST's is recent yet covers a period that closed and was never reguided. The
issue date says nothing about applicability — the guided period says everything. Switching the
criterion keeps all ten true positives, drops the VITL false positive, and CATCHES MVST, which the
age rule missed.

UNPARSEABLE ERRS TOWARD LEAVING IT ALONE: a false demotion actively misleads, a missed one leaves
the Age column still telling the truth.

NOTHING IS DELETED. The figure stays in its cell, reframed as `none current (last: …)`, and
`dossier.json` is untouched — the three-tier rule as written: curated main body, machine-complete
JSON. Verified before choosing that surface: no committed synthesis quotes a figure from any
>1y-stale guide, so the harm was to a human reader and the fix belongs where a human reads.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.dossier.render import _guidance_bridge_lines, _guide_period_year


class _Row:
    def __init__(self, metric: str, guide: str, period: str, dated: str, age: str) -> None:
        self.metric, self.latest_guide, self.period = metric, guide, period
        self.dated, self.age = dated, age
        self.record, self.most_recent = "—", "—"


class _Sourced:
    def __init__(self, value: list[_Row]) -> None:
        from vinci.dossier.schemas import SourceStatus
        self.value, self.status, self.source_ref = value, SourceStatus.PRESENT, "CIQ→Guidance"


class _AsOf:
    def __init__(self, v: str) -> None:
        self.value = v


class _CP:
    def __init__(self, rows: list[_Row], as_of: str = "≥2026-07-21") -> None:
        self.guidance_bridge_rows = _Sourced(rows)
        self.guidance_bridge = None
        self.as_of = _AsOf(as_of)


NFLX_DEAD = _Row("Gross Margin %", "'47.00 - 48.00'", "FQ4 2002", "2002-10-17", "8686d (stale)")
NFLX_LIVE = _Row("Revenue", "12,860.0", "FQ3 2026", "2026-07-16", "fresh")
RECENT_STALE = _Row("EPS Normalized", "1.20", "FQ1 2026", "2025-12-03", "215d (stale)")
#: VITL's REAL row — old issue date, period still ahead. The case age got wrong.
LONG_TERM = _Row("Gross Margin %", "35.0", "FY 2027", "2023-11-02", "977d (stale)")
#: MVST's REAL row — recent issue date, period already closed. The case age also got wrong.
RECENT_DEAD = _Row("Gross Margin %", "22.0", "FY 2025", "2025-11-10", "238d (stale)")


def _cells(rows: list[_Row]) -> str:
    return "\n".join(_guidance_bridge_lines(_CP(rows)))


# ─── the period reader ────────────────────────────────────────────────────────────────────────

def test_the_period_year_is_read_from_the_rows_own_label() -> None:
    """The row states the period it covers; the render reads that rather than inferring one from
    the issue date — which is the whole error this rule was rebuilt to remove."""
    assert _guide_period_year("FQ4 2002") == 2002
    assert _guide_period_year("FY 2027") == 2027
    assert _guide_period_year("") is None and _guide_period_year("—") is None


# ─── the demotion ─────────────────────────────────────────────────────────────────────────────

def test_a_dead_guide_no_longer_leads_with_its_figure() -> None:
    """NFLX'S REAL ROW. The number is still there — nothing is deleted — but it can no longer be
    read as current guidance."""
    out = _cells([NFLX_DEAD])
    assert "none current" in out, out
    assert "'47.00 - 48.00'" in out, "the figure was deleted rather than reframed"
    assert "2002-10-17" in out and "8686d" in out, "the date and age must still be shown"


def test_a_current_guide_is_untouched() -> None:
    """THE NEGATIVE HALF. A demotion that caught live guidance would be worse than the defect."""
    out = _cells([NFLX_LIVE])
    assert "none current" not in out
    assert "12,860.0" in out


def test_a_recently_stale_guide_is_still_current_guidance() -> None:
    """A guide for the CURRENT fiscal year is live guidance even when the export marks it stale —
    FQ1 2026 at a 2026 as-of has not been superseded by anything."""
    out = _cells([RECENT_STALE])
    assert "none current" not in out, "a guide for the CURRENT year was demoted"
    assert "1.20" in out


def test_demoted_rows_sort_below_the_current_ones() -> None:
    """SHEET ORDER PUT THE DEAD GUIDES FIRST — NFLX's 2002 and 2003 rows opened its table. A reader
    should meet current guidance before a superseded one, whatever order the workbook exported."""
    out = _cells([NFLX_DEAD, NFLX_LIVE])
    assert out.index("12,860.0") < out.index("none current"), (
        "a dead guide still precedes live guidance in the rendered table")


def test_long_term_guidance_survives_an_old_issue_date() -> None:
    """REVIEW FINDING (P1, #423) — VITL'S REAL ROW, and the case that killed the age rule. Dated
    2023-11-02 (977d) but FOR FY 2027, still ahead of the 2026 as-of. Multi-year guidance remains
    applicable without being reissued annually; demoting it states something false."""
    out = _cells([LONG_TERM])
    assert "none current" not in out, f"a guide for a FUTURE period was demoted:\n{out}"
    assert "35.0" in out


def test_a_recently_issued_guide_for_a_closed_period_is_demoted() -> None:
    """MVST'S REAL ROW, and the other direction the age rule got wrong: only 238d old, but for
    FY 2025 — a year already finished and never reguided. There IS no current gross-margin guide,
    however recently the last one was issued."""
    out = _cells([RECENT_DEAD])
    assert "none current" in out, f"a guide for a CLOSED period was left as current:\n{out}"
    assert "22.0" in out, "the figure was deleted rather than reframed"


def test_an_unreadable_period_is_left_alone_rather_than_demoted() -> None:
    """The conservative direction, chosen deliberately: a false demotion misleads, a missed one
    leaves the Age column still telling the truth."""
    odd = _Row("EBITDA", "5.0", "n/a", "2015-01-01", "4000d (stale)")
    assert "none current" not in _cells([odd])


# ─── the corpus ───────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_the_json_still_carries_every_guide_figure() -> None:
    """CURATING NEVER DELETES A FACT. The demotion is display-only, so the machine-complete tier
    must still hold each row exactly as the builder produced it — this is what makes the reframing
    a curation rather than a loss."""
    seen = 0
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        cp = (json.loads(p.read_text()).get("mechanical") or {}).get("catalyst_path") or {}
        for r in ((cp.get("guidance_bridge_rows") or {}).get("value") or []):
            seen += 1
            assert "none current" not in str(r.get("latest_guide") or ""), (
                f"{p.parent.name}: the render's wording leaked into the stored record")
    assert seen, "no committed guidance rows — this test checked nothing"


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_no_rendered_page_presents_a_closed_period_guide_as_current() -> None:
    """THE FLEET PIN, and the one that would have caught the original defect. Reads the committed
    pages: a guide whose stated PERIOD closed before the page's own catalyst as-of must never
    appear without its demotion marker.

    Keyed on the period the row itself states — the criterion the render uses — so it cannot drift
    back to the issue-age proxy that was wrong in both directions."""
    import re

    bad: list[str] = []
    for jp in sorted(Path("data/dossiers").glob("*/dossier.json")):
        doc = json.loads(jp.read_text())
        cp = (doc.get("mechanical") or {}).get("catalyst_path") or {}
        a = cp.get("as_of")
        a = a.get("value") if isinstance(a, dict) else a
        am = re.search(r"(20\d\d)-\d\d-\d\d", str(a or ""))
        if am is None:
            continue
        asof_yr = int(am.group(1))
        md = (jp.parent / "dossier.md")
        page = md.read_text() if md.is_file() else ""
        for r in ((cp.get("guidance_bridge_rows") or {}).get("value") or []):
            pm = re.search(r"(20\d\d)", str(r.get("period") or ""))
            if pm is None or int(pm.group(1)) >= asof_yr:
                continue
            for line in page.splitlines():
                same_row = (str(r.get("period")) in line and str(r.get("dated")) in line)
                if same_row and "none current" not in line:
                    bad.append(f"{jp.parent.name}: {r.get('metric')} for "
                               f"{r.get('period')} renders as current")
    assert not bad, "\n  ".join(["closed-period guides presented as current:", *bad])
