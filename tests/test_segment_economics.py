"""(MC2) The segment-economics extractor, pinned on a REAL filing frozen as a fixture.

OFFLINE BY CONSTRUCTION. The fixture is Alphabet's FY2025 10-K (acc 0001652044-26-000018) as
filed — `FilingSummary.xml` and the `R90.htm` it indexes, byte-for-byte. A hand-rolled table would
have dictated the parser's shape, which is the fixture defect CLAUDE.md names; this is the document
the parser exists to read.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from vinci.edgar.segments import SegmentReportUnavailableError, _pick_report, segment_rows

FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "segments"
ACC = "0001652044-26-000018"
#: a column is named by BOTH header rows: the duration above, the date below
PERIOD = "12 Months Ended Dec. 31, 2025"
YEARS = (PERIOD, "12 Months Ended Dec. 31, 2024", "12 Months Ended Dec. 31, 2023")


class _FrozenHttp:
    """The fixture as an HTTP surface — same two calls, no network."""

    def get_text(self, url: str, *, ttl_seconds: float | None = None,
                 params: dict[str, object] | None = None) -> str:
        name = url.rsplit("/", 1)[-1]
        return (FIX / f"GOOGL-{ACC}-{name}").read_text()


def _by_segment(period: str = PERIOD) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for r in segment_rows(_FrozenHttp(), "0001652044", ACC):  # type: ignore[arg-type]
        if r.period == period:
            out.setdefault(r.segment, {})[r.metric] = r.value
    return out


def test_the_details_report_is_chosen_over_the_policy_note() -> None:
    """Alphabet's 10-K indexes FOUR reports naming segments and only one holds numbers.

    Matching on "segment" alone picks the accounting-policy note and finds nothing in it — which
    would look exactly like an issuer that discloses no segment economics.
    """
    summary = (FIX / f"GOOGL-{ACC}-FilingSummary.xml").read_text()
    fname, short = _pick_report(summary)
    assert fname == "R90.htm", f"picked {fname} ({short})"
    assert "(Details)" in short and "Operating Income" in short


def test_a_filing_with_no_segment_report_says_so_rather_than_returning_empty() -> None:
    """"No segment disclosure" and "we could not read it" are different facts about an issuer, and
    a caller cannot tell them apart from an empty list."""
    with pytest.raises(SegmentReportUnavailableError, match="indexes no report naming a segment"):
        _pick_report("<FilingSummary><Reports></Reports></FilingSummary>")
    with pytest.raises(SegmentReportUnavailableError, match="none is a .Details. table"):
        _pick_report("<Report><HtmlFileName>R25.htm</HtmlFileName>"
                     "<ShortName>Information about Segments</ShortName></Report>")


def test_the_parsed_segments_reconcile_to_the_disclosed_totals() -> None:
    """THE VERIFICATION THAT MATTERS, and the only one that proves the parse rather than sampling
    it: the segments must sum to the totals the filing itself states.

    BOTH SIDES, AND EVERY FILED YEAR. Revenue catches a dropped or double-counted row. Operating
    income also catches the SIGN, because the hedging line is a parenthesised negative — read as
    positive it breaks that sum by twice its own size and nothing else in the table would notice.
    Checking all three years catches a COLUMN SHIFT, which a single-period check cannot see: every
    figure moving one year together still reconciles inside each column.
    """
    for period in YEARS:
        by = _by_segment(period)
        tot = by["(consolidated)"]
        segs = [s for s in by if s != "(consolidated)"]

        seg_rev = sum(by[s]["Revenue from contract with customers"] for s in segs
                      if "Revenue from contract with customers" in by[s])
        assert seg_rev + tot["Hedging gains (losses)"] == tot["Total revenues"], (
            f"{period}: segment revenue {seg_rev} + hedging != {tot['Total revenues']}")

        seg_inc = sum(by[s]["Total income from operations"] for s in segs
                      if "Total income from operations" in by[s])
        assert seg_inc == tot["Total income from operations"], (
            f"{period}: segment income {seg_inc} != {tot['Total income from operations']}")


def test_the_two_presentations_of_one_segment_are_joined_and_agree() -> None:
    """The renderer states the SAME segment twice — a plain heading carrying revenue and costs, and
    a dimensional one ("Operating Segments | Google Cloud") carrying income directly.

    LEFT UNJOINED THEY ARE TWO KEYS FOR ONE SEGMENT, and a consumer cannot compute that segment's
    margin — which is the whole reason this module exists. Joined, the overlap becomes a free
    cross-check: revenue minus costs must equal the income stated for the same segment, and it
    does for every operating segment in every filed year. A parse that mis-attributed a row would
    break this before it broke any total.
    """
    for period in YEARS:
        by = _by_segment(period)
        checked = 0
        for seg in ("Google Services", "Google Cloud"):
            m = by[seg]
            derived = m["Revenue from contract with customers"] - m["Total costs and expenses"]
            assert derived == m["Total income from operations"], (
                f"{period} {seg}: revenue-less-costs {derived} != stated "
                f"{m['Total income from operations']}")
            checked += 1
        assert checked == 2, "both dual-stated segments must be checked, or this proves nothing"
    assert not any("|" in s for s in _by_segment(PERIOD)), (
        "a dimensional heading survived the join — the segment is keyed twice")


def test_every_row_carries_its_scale_and_its_accession() -> None:
    """A number without its unit is the scale defect this repo has recorded twice, and one without
    its accession cannot be re-checked against the filing it came from."""
    rows = segment_rows(_FrozenHttp(), "0001652044", ACC)  # type: ignore[arg-type]
    assert rows, "the fixture parsed to nothing"
    assert all(r.unit == "$Millions" for r in rows), {r.unit for r in rows}
    assert all(ACC in r.source_ref and "R90.htm" in r.source_ref for r in rows)
    # the issuer's OWN headings, never normalised into a house vocabulary
    assert {"Google Services", "Google Cloud", "Other Bets"} <= {r.segment for r in rows}


def test_a_parenthesised_loss_reads_negative() -> None:
    """The sign case, isolated. `(127)` is a LOSS; read as 127 it inverts exactly the lines a
    reader is looking for on a segment that is losing money."""
    from vinci.edgar.segments import _number

    assert _number("(127)") == -127.0
    assert _number("$ (1,229)") == -1229.0
    assert _number("342,721") == 342721.0
    assert _number("operating segments") is None, "prose must not parse as a figure"


def test_a_details_report_that_names_no_economics_is_refused() -> None:
    """Document order is not a contract. GOOGL's filing carries TWO segment "(Details)" reports —
    the revenue/income table and "Long-Lived Assets by Geographic Area" — and taking the first
    returned geography figures labelled as segment economics whenever the renderer emitted them in
    the other order. Only GOOGL's ordering was ever checked; four other multi-segment names are
    unverified, so the economics report is NAMED rather than positioned."""
    geo_only = ("<Report><HtmlFileName>R91.htm</HtmlFileName><ShortName>Information about "
                "Segments - Long-Lived Assets by Geographic Area (Details)</ShortName></Report>")
    with pytest.raises(SegmentReportUnavailableError, match="do not match the refinement"):
        _pick_report(geo_only)

    econ = ("<Report><HtmlFileName>R90.htm</HtmlFileName><ShortName>Information about Segments"
            " - Revenue and Operating Income/Loss (Details)</ShortName></Report>")
    both = geo_only + econ
    fname, _short = _pick_report(both)
    assert fname == "R90.htm", "the economics report must win regardless of document order"


def test_a_report_that_parses_to_nothing_raises_rather_than_returning_empty() -> None:
    """The module's own contract, enforced. A table whose header cannot be read yields no rows, and
    returning [] there says "this issuer discloses no segments" — a claim about the issuer made on
    the strength of a parser failure."""
    class _Broken:
        def get_text(self, url: str, *, ttl_seconds: float | None = None,
                     params: dict[str, object] | None = None) -> str:
            name = url.rsplit("/", 1)[-1]
            text = (FIX / f"GOOGL-{ACC}-{name}").read_text()
            # break only the period header; the rest of the table is untouched
            if not name.endswith(".htm"):
                return text
            return text.replace("Dec. 31, 2025", "12 Months Ended")

    with pytest.raises(SegmentReportUnavailableError, match="parsed to no figures"):
        segment_rows(_Broken(), "0001652044", ACC)  # type: ignore[arg-type]


def test_a_blank_cell_leaves_a_hole_rather_than_shifting_every_later_year() -> None:
    """THE COLUMN-SHIFT CASE, CONSTRUCTED — because the filing has no blank that would expose it.

    Dropping empty cells and then zipping against the period header pairs positionally, so a
    segment missing one year's figure silently reports the NEXT year's number under it and the row
    still looks well-formed. Nothing in the real fixture triggers that, which is precisely why the
    fix went in unguarded: a mutation that reintroduced it reddened not one pin.

    So the blank is introduced into the real document — Google Cloud's newest revenue cell emptied,
    everything else untouched — and the assertion is that FY2024's number does NOT move into
    FY2025's slot. The totals cannot catch this: they are checked within each column, and a value
    that moves columns still sums correctly in the one it lands in.
    """
    import re as _re

    real = (FIX / f"GOOGL-{ACC}-R90.htm").read_text()
    row = _re.search(r"<tr[^>]*>(?:(?!</tr>).)*?Revenue from contract with customers"
                     r"(?:(?!</tr>).)*?58,705(?:(?!</tr>).)*?</tr>", real, _re.S)
    assert row, "the fixture no longer carries Google Cloud's 58,705 revenue row"
    holed = real.replace(row.group(0), row.group(0).replace(">58,705<", "><", 1), 1)
    assert holed != real, "the blank was not introduced"

    class _Holed:
        def get_text(self, url: str, *, ttl_seconds: float | None = None,
                     params: dict[str, object] | None = None) -> str:
            name = url.rsplit("/", 1)[-1]
            return holed if name == "R90.htm" else (FIX / f"GOOGL-{ACC}-{name}").read_text()

    got = {r.period: r.value for r in segment_rows(_Holed(), "0001652044", ACC)  # type: ignore[arg-type]
           if r.segment == "Google Cloud" and r.metric == "Revenue from contract with customers"}
    assert PERIOD not in got, (
        f"the emptied year still reports a figure — {got.get(PERIOD)} shifted into it")
    assert got.get("12 Months Ended Dec. 31, 2024") == 43229.0, (
        f"FY2024 moved out of its own column: {got}")
    assert got.get("12 Months Ended Dec. 31, 2023") == 33088.0, f"FY2023 moved: {got}"


# --- a 10-Q heads its columns with TWO rows (audit E2-D18) ---------------------------------------
#
# Alphabet's Q3 2026 10-Q (acc 0001652044-26-000084, filed 2026-10-29) as filed: `FilingSummary.xml`
# and `R84.htm`, byte-for-byte. R84 heads its four columns "3 Months Ended" ×2 over "9 Months Ended"
# ×2, and every date under them is Sep. 30 — so by date alone the quarter's 127,577 of revenue and
# the nine months' 357,269 share the one period "Sep. 30, 2026".
#
# THE SUMMARY INDEXES TWO segment (Details) reports — "Revenues - Revenue by Segment" and R84 — and
# `_pick_report` refuses the pair as ambiguous, as it does Amazon's Q2 2026 10-Q. Serving R84's own
# `<Report>` entry, cut verbatim from that summary, reaches the table reader this pins; the picker
# is a separate question and is not decided here.

Q3 = "0001652044-26-000084"
Q3_REVENUE = {"3 Months Ended Sep. 30, 2026": 127_577.0, "3 Months Ended Sep. 30, 2025": 102_346.0,
              "9 Months Ended Sep. 30, 2026": 357_269.0, "9 Months Ended Sep. 30, 2025": 289_007.0}


class _Q3Http:
    """The 10-Q as an HTTP surface, its summary cut to R84's entry; ``edit`` alters the report."""

    def __init__(self, edit: tuple[str, str] | None = None) -> None:
        self.edit = edit

    def get_text(self, url: str, *, ttl_seconds: float | None = None,
                 params: dict[str, object] | None = None) -> str:
        import re as _re

        name = url.rsplit("/", 1)[-1]
        text = (FIX / f"GOOGL-{Q3}-{name}").read_text()
        if name == "FilingSummary.xml":
            entry = _re.search(r"<Report\b(?:(?!</Report>).)*?<HtmlFileName>R84\.htm"
                               r"</HtmlFileName>.*?</Report>", text, _re.S)
            assert entry, "the summary no longer indexes R84"
            return f"<FilingSummary><MyReports>{entry.group(0)}</MyReports></FilingSummary>"
        if self.edit:
            assert self.edit[0] in text, f"the report no longer carries {self.edit[0]!r}"
            text = text.replace(self.edit[0], self.edit[1], 1)
        return text


def test_a_quarter_and_its_year_to_date_are_two_periods() -> None:
    """THE RED. The four "Total revenues" figures land in four periods, each named by its duration
    and its date. By date alone two keys held four figures, and each kept whichever came last."""
    rows = [r for r in segment_rows(_Q3Http(), "0001652044", Q3)  # type: ignore[arg-type]
            if r.metric == "Total revenues"]
    assert len(rows) == 4 and {r.period: r.value for r in rows} == Q3_REVENUE, [
        (r.period, r.value) for r in rows]


def test_each_period_reconciles_to_its_own_total() -> None:
    """The columns, checked against themselves: in each of the four periods the three segments'
    revenue plus hedging is that period's total (96,302 + 30,709 + 372 + 194 = 127,577 for the
    quarter). A quarter and a year-to-date filed under one period sum to neither."""
    rows = segment_rows(_Q3Http(), "0001652044", Q3)  # type: ignore[arg-type]
    for period, total in Q3_REVENUE.items():
        parts = sum(r.value for r in rows if r.period == period and r.metric in (
            "Revenue from contract with customers", "Hedging gains (losses)"))
        assert parts == total, f"{period}: {parts} != {total}"


def test_a_header_whose_two_rows_disagree_is_refused() -> None:
    """(−) "9 Months Ended" cut to one column: the duration row spans three columns over four
    dates, and which period the fourth covers is not in the header. Refused, never guessed."""
    cut = ('<th class="th" colspan="2">9 Months Ended</th>',
           '<th class="th" colspan="1">9 Months Ended</th>')
    with pytest.raises(SegmentReportUnavailableError,
                       match="spans 3 columns and its date header 4"):
        segment_rows(_Q3Http(cut), "0001652044", Q3)  # type: ignore[arg-type]


def test_a_row_wider_than_its_header_is_refused() -> None:
    """(−) One figure cell too many on the "Total revenues" row. Cut to the header's width, its
    first four figures would still read — under whichever periods they happened to sit beside."""
    wide = ('<td class="nump">289,007<span></span>',
            '<td class="nump">1</td><td class="nump">289,007<span></span>')
    with pytest.raises(SegmentReportUnavailableError,
                       match="has 5 figure columns under a header of 4"):
        segment_rows(_Q3Http(wide), "0001652044", Q3)  # type: ignore[arg-type]


def test_a_duration_header_without_its_title_cell_mark_is_refused() -> None:
    """(−, review round 0) The caption cell stripped of ``class="tl"``: the duration row then reads
    as a caption beside two durations, and dropping it would label every column by its date alone
    — the defect this fixes, silently back. Refused instead."""
    bare = ('<th class="tl" colspan="1" rowspan="2">', '<th colspan="1" rowspan="2">')
    with pytest.raises(SegmentReportUnavailableError, match="duration header"):
        segment_rows(_Q3Http(bare), "0001652044", Q3)  # type: ignore[arg-type]


# --- moved here from the panel tests retired in #910 (2026-11-05) ------------------------------
#
# The commissioning ratio (`vinci/edgar/commissioning.py`) was this picker's one other topic, and
# its tests and the panel registry's held the only pins on the picker's ABSENCE guard and on its
# refusal of an ambiguous filing. The picker stays, so the pins do: the first four verbatim, the
# fifth cut to its half that reads this module's default route.


def test_a_new_topic_must_state_its_own_absence_meaning_or_fail_loudly() -> None:
    """The guard reads the TOPIC PATTERN, not the `what` LABEL.

    Keyed on `what`, the guard made a DISPLAY STRING load-bearing — the rule this repo holds
    because display text drifts — and failed open in the way that matters: a caller passing a new
    `topic` and forgetting BOTH keywords inherited the segment clause AND had its note mislabelled
    "segment", so
    the refusal was wrong twice and silent about both. Observed: a `goodwill` topic returned
    *"no report naming a segment — a single-segment filer discloses none"*.

    Moved here from `tests/test_panels.py` (retired in #910).
    """
    import re as _re

    from vinci.edgar.segments import _pick_report

    with pytest.raises(ValueError, match="must state what ABSENCE means"):
        _pick_report("<FilingSummary></FilingSummary>", topic=_re.compile("goodwill"))
    # The segment route still needs no keyword — it is the one topic the default clause is true of.
    from vinci.edgar.segments import SegmentReportUnavailableError
    with pytest.raises(SegmentReportUnavailableError):
        _pick_report("<FilingSummary></FilingSummary>")


def test_a_blank_absence_clause_is_the_same_hole_as_a_missing_one() -> None:
    """`absent_means=""` passed a None-only check and shipped a refusal explaining nothing.

    Moved here from `tests/test_panels.py` (retired in #910)."""
    import re as _re

    from vinci.edgar.segments import _pick_report

    for blank in ("", "   "):
        with pytest.raises(ValueError, match="may not be blank"):
            _pick_report("<FilingSummary></FilingSummary>", topic=_re.compile("goodwill"),
                         what="goodwill note", absent_means=blank)


def test_the_segment_route_keeps_its_own_absence_meaning() -> None:
    """The sibling call site: parameterising the clause must not blank it for segments.

    A default that silently became empty would strip the segment route's explanation while every
    commissioning test stayed green — the sibling-call-site class.

    Moved here from `tests/test_commissioning_ratio.py` (retired in #910).
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

    Moved here from `tests/test_commissioning_ratio.py` (retired in #910).
    """
    from vinci.edgar.segments import _pick_report

    with pytest.raises(ValueError, match="must state what ABSENCE means"):
        _pick_report("<FilingSummary></FilingSummary>",
                     topic=re.compile("goodwill", re.I), what="goodwill")


def test_the_repo_wide_pattern_refuses_a_filing_with_two_economics_reports() -> None:
    """GOOGL's Q2 2026 10-Q (acc 0001652044-26-000071) carries TWO economics-matching segment
    (Details) reports, so the repo-wide pattern rightly refuses as ambiguous — choosing would file
    geography or revenue-only figures as segment economics.

    Moved here from `tests/test_cohort_five.py::
    test_the_declared_note_name_resolves_what_the_repo_wide_pattern_cannot` (retired in #910),
    with the summary it read: its first half, which pins this module's default route. Its second
    half resolved the report through the panel declarations in `data/followed.json`, which retired
    with the panels.
    """
    summary = (FIX / "GOOGL-0001652044-26-000071-FilingSummary.xml").read_text()
    with pytest.raises(SegmentReportUnavailableError, match="more than one segment report"):
        _pick_report(summary)
