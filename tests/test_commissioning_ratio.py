"""(monitoring plan item 2) The "built but not running" ratio, pinned on the real 10-Q.

OFFLINE. The fixture is Alphabet's Q2 2026 10-Q (acc 0001652044-26-000071) as filed — its
`FilingSummary.xml` and the `R64.htm` it indexes, byte-for-byte.
"""
from __future__ import annotations

import pathlib

import pytest

from vinci.edgar.commissioning import (
    CommissioningUnavailableError,
    commissioning,
)

FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "commissioning"
ACC = "0001652044-26-000071"


class _Frozen:
    def get_text(self, url: str, *, ttl_seconds: float | None = None,
                 params: dict[str, object] | None = None) -> str:
        return (FIX / f"GOOGL-{ACC}-{url.rsplit('/', 1)[-1]}").read_text()


def _rows() -> dict[str, object]:
    return {c.period: c for c in commissioning(_Frozen(), "0001652044", ACC)}  # type: ignore[arg-type]


def test_the_ratio_reproduces_the_figures_the_plan_was_written_from() -> None:
    """THE VERIFICATION: the parser must land on the numbers the monitoring plan cites, to the
    dollar, or it is reading a different note than the one the position rests on.

    The plan states the move as "38.6% -> 49.7% in six months". Both periods come from THIS single
    filing — a 10-Q states the current period and the prior year-end — so one fetch is the whole
    claim, level and move together.
    """
    rows = _rows()
    cur, prior = rows["Jun. 30, 2026"], rows["Dec. 31, 2025"]

    assert cur.not_yet_in_service == 122_814.0        # type: ignore[attr-defined]
    assert cur.in_service == 247_177.0                # type: ignore[attr-defined]
    assert round(cur.ratio * 100, 1) == 49.7          # type: ignore[attr-defined]

    assert prior.not_yet_in_service == 78_592.0       # type: ignore[attr-defined]
    assert prior.in_service == 203_679.0              # type: ignore[attr-defined]
    assert round(prior.ratio * 100, 1) == 38.6        # type: ignore[attr-defined]


def test_the_denominator_is_the_member_line_not_the_in_service_total() -> None:
    """"Property and equipment, in service" also contains the words "in service", and its total
    (304,310) is about a third larger than the technical-infrastructure member (247,177).

    Matching that heading by substring would silently understate the ratio — 40.4% instead of
    49.7% — and nothing else in the table would disagree. The headings are matched WHOLE.
    """
    cur = _rows()["Jun. 30, 2026"]
    assert cur.in_service == 247_177.0, "the denominator is not the member line"  # type: ignore[attr-defined]
    assert cur.in_service != 304_310.0, "the in-service TOTAL was read as the denominator"  # type: ignore[attr-defined]


def test_a_note_missing_either_line_yields_nothing_rather_than_a_half_ratio() -> None:
    """Both sides must come from the same note on the same date. A ratio struck against a
    substituted denominator is not this metric, and returning one would be worse than returning
    none — it would read as the plan's number."""
    class _Stripped:
        def get_text(self, url: str, *, ttl_seconds: float | None = None,
                     params: dict[str, object] | None = None) -> str:
            name = url.rsplit("/", 1)[-1]
            text = (FIX / f"GOOGL-{ACC}-{name}").read_text()
            if not name.endswith(".htm"):
                return text
            return text.replace("Assets not yet in service", "Some other member")

    with pytest.raises(CommissioningUnavailableError, match="no period stating BOTH"):
        commissioning(_Stripped(), "0001652044", ACC)  # type: ignore[arg-type]


def test_the_report_is_resolved_by_name_because_its_number_moves() -> None:
    """THE PLAN'S PART 7 TRAP 2, pinned: "Alphabet's property note sat at R64, R64, R70 and R62
    across its last four filings. Hardcode the number and the parser silently reads a different
    note."

    Observed directly across the two filings this build read: the note is R70 in the FY2025 10-K
    and R64 in this 10-Q. Resolution is by ShortName; this asserts the resolver still finds it
    when the number is not the one anyone remembers.
    """
    import re

    from vinci.edgar.commissioning import _ANY, _PPE_REPORT
    from vinci.edgar.segments import _pick_report

    summary = (FIX / f"GOOGL-{ACC}-FilingSummary.xml").read_text()
    fname, short = _pick_report(summary, topic=_PPE_REPORT, refine=_ANY)
    assert fname == "R64.htm", f"resolved {fname}"
    assert re.search(r"property and equipment", short, re.I)
    # ...and the number genuinely differs from the 10-K's, which is the whole point
    assert fname != "R70.htm"
