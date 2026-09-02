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


def _by_segment() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for r in segment_rows(_FrozenHttp(), "0001652044", ACC):  # type: ignore[arg-type]
        if r.period == PERIOD:
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

    Both sides are pinned. REVENUE catches a dropped or double-counted row. OPERATING INCOME also
    catches the sign, because the hedging line is a parenthesised negative — read as positive it
    breaks this sum by twice its own size, and nothing else in the table would notice.
    """
    by = _by_segment()
    tot = by["(consolidated)"]

    seg_rev = sum(m["Revenue from contract with customers"] for s, m in by.items()
                  if "Revenue from contract with customers" in m and s != "(consolidated)"
                  and "|" not in s)
    assert seg_rev + tot["Hedging gains (losses)"] == tot["Total revenues"], (
        f"segment revenue {seg_rev} + hedging {tot['Hedging gains (losses)']} != "
        f"{tot['Total revenues']}")

    # TWO PRESENTATIONS IN ONE TABLE: Services and Cloud state revenue AND costs (income is the
    # difference); Other Bets and the reconciling items state income directly, under a dimensional
    # heading. Reading only one shape loses half the table and the sum stops closing.
    derived = sum(by[s]["Revenue from contract with customers"] - by[s]["Total costs and expenses"]
                  for s in ("Google Services", "Google Cloud"))
    stated = (by["Operating Segments | Other Bets"]["Total income from operations"]
              + by["Reconciling items"]["Total income from operations"])
    assert derived + stated == tot["Total income from operations"], (
        f"{derived} + {stated} != {tot['Total income from operations']}")


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
