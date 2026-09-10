"""(monitoring plan item 2) The "built but not running" ratio, pinned on the real 10-Q.

OFFLINE. The fixture is Alphabet's Q2 2026 10-Q (acc 0001652044-26-000071) as filed — its
`FilingSummary.xml` and the `R64.htm` it indexes, byte-for-byte.
"""
from __future__ import annotations

import pathlib
import re

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
    # `absent_means` is REQUIRED of every non-segment topic — this call previously relied on the
    # hole that made it optional, and the guard that closed it caught this line first.
    fname, short = _pick_report(summary, topic=_PPE_REPORT, refine=_ANY,
                                absent_means="an operating company always holds fixed assets")
    assert fname == "R64.htm", f"resolved {fname}"
    assert re.search(r"property and equipment", short, re.I)
    # ...and the number genuinely differs from the 10-K's, which is the whole point
    assert fname != "R70.htm"


KACC = "0001652044-26-000018"          # the FY2025 10-K — the 38.6% leg, and a DIFFERENT R-number


class _FrozenK:
    def get_text(self, url: str, *, ttl_seconds: float | None = None,
                 params: dict[str, object] | None = None) -> str:
        return (FIX / f"GOOGL-{KACC}-{url.rsplit('/', 1)[-1]}").read_text()


def test_the_10k_leg_agrees_with_the_10q_on_the_period_they_share() -> None:
    """TWO FILINGS, ONE PERIOD, INDEPENDENTLY — the strongest check available offline.

    The 10-Q states Dec-31-2025 as its comparative; the 10-K states it as its current year. Nothing
    makes them agree except the parser reading both correctly, and the report NUMBER differs
    between them (R64 vs R70), so this also exercises name-resolution end to end.

    The earlier commit claimed this leg verified while committing only the 10-Q fixture — the claim
    was true of a live run and unpinned, which is how a verification quietly becomes a memory.
    """
    q = {c.period: c for c in commissioning(_Frozen(), "0001652044", ACC)}       # type: ignore[arg-type]
    k = {c.period: c for c in commissioning(_FrozenK(), "0001652044", KACC)}     # type: ignore[arg-type]

    shared = "Dec. 31, 2025"
    assert shared in q and shared in k, "the two filings no longer overlap on a period"
    assert q[shared].not_yet_in_service == k[shared].not_yet_in_service == 78_592.0
    assert q[shared].in_service == k[shared].in_service == 203_679.0
    assert round(k[shared].ratio * 100, 1) == 38.6

    # ...and the 10-K reaches a year the 10-Q does not, giving the plan's full move
    assert round(k["Dec. 31, 2024"].ratio * 100, 1) == 35.7
    assert round(q["Jun. 30, 2026"].ratio * 100, 1) == 49.7


def test_the_two_ratios_are_both_reported_and_differ() -> None:
    """The plan's ratio and the like-for-like one are DIFFERENT NUMBERS, and both are stated.

    `assets not yet in service` is one member spanning every asset type; `technical infrastructure`
    is one of three in-service members. The plan's 49.7% therefore divides a whole by a part. That
    is kept, because it is the operator's tracked series — but the coherent comparison is carried
    beside it rather than left implied, and this pin is what stops the two being conflated again.
    """
    cur = {c.period: c for c in commissioning(_Frozen(), "0001652044", ACC)}["Jun. 30, 2026"]  # type: ignore[arg-type]
    assert round(cur.ratio * 100, 1) == 49.7
    assert cur.like_for_like is not None
    assert round(cur.like_for_like * 100, 1) == 40.4
    # the denominator of the like-for-like is the filing's OWN stated total, not a local sum
    assert cur.in_service_total == 304_310.0


def test_a_spacer_cell_in_the_header_does_not_relabel_every_figure() -> None:
    """THE COLUMN SHIFT, CONSTRUCTED — because the real note has no spacer that exposes it.

    Period headers were collected with blanks dropped while value rows keep them, so a single
    spacer cell pairs the two lists one place out: the June figures come back stamped December and
    the June column disappears. Both lists still zip, so nothing complains. This is the same defect
    the segment parser carried, reappearing in the module written to avoid it — which is why it is
    pinned here rather than trusted to the fix.
    """
    real = (FIX / f"GOOGL-{ACC}-R64.htm").read_text()
    # one empty cell inserted between the caption and the first date, nothing else touched
    spacer = '</th>\n<th class="th"></th>\n<th class="th">'
    holed = real.replace('</th>\n<th class="th">', spacer, 1)
    assert holed != real, "the spacer was not introduced"

    class _Spaced:
        def get_text(self, url: str, *, ttl_seconds: float | None = None,
                     params: dict[str, object] | None = None) -> str:
            name = url.rsplit("/", 1)[-1]
            return holed if name == "R64.htm" else (FIX / f"GOOGL-{ACC}-{name}").read_text()

    with pytest.raises(CommissioningUnavailableError, match="do not line up"):
        commissioning(_Spaced(), "0001652044", ACC)  # type: ignore[arg-type]


def test_a_missing_ppe_note_is_not_explained_with_the_segment_notes_story() -> None:
    """A refusal must tell the reader THIS note's story, not another note's.

    `_pick_report` is shared with the segment route, and its "why nothing is here" clause was
    hardcoded to segments while `what` was parameterised — so a filing with no property note
    refused with "a single-segment filer discloses none, and that is an answer rather than a
    failure". For segments that clause is true and useful: a single-segment filer really does
    disclose none. For fixed assets it is FALSE — every operating company holds them, so absence
    is a presentation choice, and the balances may sit under a note named for the asset itself.
    Observed live on WERN (a trucking filer, no property-named report) and LLY, 2026-09-03.

    Pinned as the CLAIM, not as wording: the new text mentions single-segment filers in order to
    deny the analogy, so a token scan would pass on the very message it is meant to reject.
    """
    class _NoPpeReport:
        def get_text(self, url: str, *, ttl_seconds: float | None = None,
                     params: dict[str, object] | None = None) -> str:
            text = (FIX / f"GOOGL-{ACC}-{url.rsplit('/', 1)[-1]}").read_text()
            if url.endswith("FilingSummary.xml"):
                return re.sub(r"Property and [Ee]quipment", "Widgets", text)
            return text

    with pytest.raises(CommissioningUnavailableError) as got:
        commissioning(_NoPpeReport(), "0001652044", ACC)  # type: ignore[arg-type]
    msg = str(got.value)
    assert "indexes no report naming a property-and-equipment" in msg
    # The segment note's conclusion must NOT be asserted of this one.
    assert "a single-segment filer discloses none, and that is an answer" not in msg
    assert "always holds fixed assets" in msg


def test_the_segment_route_keeps_its_own_absence_meaning() -> None:
    """The sibling call site: parameterising the clause must not blank it for segments.

    A default that silently became empty would strip the segment route's explanation while every
    commissioning test stayed green — the sibling-call-site class.
    """
    from vinci.edgar.segments import SegmentReportUnavailableError, _pick_report

    with pytest.raises(SegmentReportUnavailableError) as got:
        _pick_report("<FilingSummary></FilingSummary>")
    assert "a single-segment filer discloses none, and that is an answer" in str(got.value)


def test_a_third_topic_cannot_inherit_the_segment_absence_story_by_forgetting_a_keyword() -> None:
    """The defect class, closed rather than fixed once.

    Parameterising the clause fixed the PP&E route; leaving the SEGMENT sentence as the default
    left the next topic one forgotten keyword away from telling the wrong note's story again —
    and `what=` is already easy to remember because the message is visibly wrong without it,
    while an inherited absence clause reads perfectly and is false. So every topic but segments
    must state its own, and forgetting raises before any fetch. The segment route's own
    no-keyword call is pinned by the test above, so this one only shows every OTHER topic refused.
    """
    from vinci.edgar.segments import _pick_report

    with pytest.raises(ValueError, match="must state what ABSENCE means"):
        _pick_report("<FilingSummary></FilingSummary>",
                     topic=re.compile("goodwill", re.I), what="goodwill")
