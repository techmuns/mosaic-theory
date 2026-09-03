"""(MC2) The segment-economics extractor, pinned on a REAL filing frozen as a fixture.

OFFLINE BY CONSTRUCTION. The fixture is Alphabet's FY2025 10-K (acc 0001652044-26-000018) as
filed — `FilingSummary.xml` and the `R90.htm` it indexes, byte-for-byte. A hand-rolled table would
have dictated the parser's shape, which is the fixture defect CLAUDE.md names; this is the document
the parser exists to read.
"""
from __future__ import annotations

import pathlib

import pytest

from vinci.edgar.segments import SegmentReportUnavailableError, _pick_report, segment_rows

FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "segments"
ACC = "0001652044-26-000018"
PERIOD = "Dec. 31, 2025"


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
    for period in ("Dec. 31, 2025", "Dec. 31, 2024", "Dec. 31, 2023"):
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
    for period in ("Dec. 31, 2025", "Dec. 31, 2024", "Dec. 31, 2023"):
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
    assert not any("|" in s for s in _by_segment("Dec. 31, 2025")), (
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
    with pytest.raises(SegmentReportUnavailableError, match="name no revenue or income line"):
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
    assert "Dec. 31, 2025" not in got, (
        f"the emptied year still reports a figure — {got.get('Dec. 31, 2025')} shifted into it")
    assert got.get("Dec. 31, 2024") == 43229.0, (
        f"FY2024 moved out of its own column: {got}")
    assert got.get("Dec. 31, 2023") == 33088.0, f"FY2023 moved: {got}"
