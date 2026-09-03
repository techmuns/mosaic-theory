"""(MC2) Per-segment ECONOMICS from a filing's R-files — the one route that actually carries them.

WHY NOT COMPANYFACTS. The SEC's ``companyfacts`` API returns facts with NO dimensional qualifiers:
measured on the committed fixtures, not one row carries a segment member, so a segment's operating
income is simply absent from the source this repo already pulls. Segment economics live in the
filing's own rendered financial-report tables (the ``R<n>.htm`` files indexed by
``FilingSummary.xml``), which is why MC2 named that route and why nothing shorter was tried first.

WHY NOT CIQ. `concentration.segment_ebitda` already reads the CIQ Segments sheet and works — for
the two names whose export happens to carry an EBITDA row (UBER, VRRM). Five multi-segment names
in the committed book (GOOGL, IT, EPAM, AORT, WERN) have segmented REVENUE there and no segment
earnings at all, and megacap theses ARE segments: Google Cloud's economics are the thesis, not a
footnote. This module is the second source for exactly those names, and it never overwrites the
first — the assembler prefers what CIQ carries and reaches here only when CIQ has nothing.

WHAT IT DOES NOT DO. It does not compute a margin, pick a "the" segment, or decide which line is
operating income. It returns the disclosed rows as stated, each bound to the accession and the
report it came from, and leaves the arithmetic to a consumer that can state its own basis. A
segment's operating income is often disclosed as revenue MINUS a costs line rather than directly
(Alphabet: "Revenue from contract with customers" and "Total costs and expenses" per segment), and
deciding that subtraction is the reader's judgment about that issuer's presentation, not this
parser's.

TWO PRESENTATIONS OF ONE SEGMENT, JOINED. Alphabet's 10-K states each operating segment twice: a
plain heading carrying revenue and a costs line, and a dimensional one the renderer writes as
``Operating Segments | Google Cloud`` carrying ``Total income from operations`` directly. Left
unjoined they are two keys for one segment and a consumer cannot compute that segment's margin,
which is the whole reason this module exists — so the axis prefix is stripped and the rows land
under one heading.

CORRECTED 2026-09-02: an earlier draft of this note claimed the dimensional shape "loses the two
that matter most". It does not — it states income for ALL THREE operating segments, and is the
more complete of the two. The overlap is therefore a CROSS-CHECK rather than a hazard: revenue
minus costs equals the stated income for Services and Cloud in all three filed years, pinned, so a
mis-attributed row breaks that equality before it breaks any total.

VERIFIED BY RECONCILIATION, not by inspection (2026-09-02, GOOGL 10-K acc 0001652044-26-000018):
segment revenue 402,963 + hedging (127) = 402,836, the disclosed ``Total revenues`` exactly; and
139,404 + 13,910 - 7,515 - 16,760 = 129,039, the disclosed ``Total income from operations``
exactly. The hedging line is the parenthesised-negative case, so that reconciliation also proves
the sign handling rather than asserting it.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vinci.netcache import CachedHttp

#: The rendered-report index every filing carries. Immutable once filed, so it caches forever.
_FILING_SUMMARY = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/FilingSummary.xml"
_REPORT = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{fname}"

#: A report qualifies when its ShortName names segments AND carries the details table rather than
#: the policy text or the tables-only stub. Alphabet's 10-K has four segment reports and only one
#: holds numbers ("… - Revenue and Operating Income/Loss by Segment (Details)"); matching on
#: "segment" alone would pick the accounting-policy note and find nothing in it.
_SEGMENT_REPORT = re.compile(r"segment", re.I)
_DETAILS = re.compile(r"\(details\)", re.I)
#: ...and which of the DETAILS reports holds ECONOMICS rather than geography or long-lived assets.
#: Named rather than positional — see `_pick_report` for the report this distinguishes it from.
_ECONOMICS = re.compile(r"revenue|income|profit|loss|ebitda", re.I)


class SegmentReportUnavailableError(RuntimeError):
    """No segment DETAILS report in this filing — stated, never guessed around."""


@dataclass(frozen=True)
class SegmentRow:
    """One disclosed number, bound to the segment and period it was stated for.

    ``segment`` is the issuer's own heading, verbatim — "Google Cloud", not a normalised slug. A
    normaliser here would be a second vocabulary for names the filer already chose, and the whole
    point of reading the filing is that its words are the record.
    """

    segment: str
    metric: str          # the row label as stated ("Revenue from contract with customers")
    period: str          # the column header as stated ("Dec. 31, 2025")
    value: float
    unit: str            # from the table's own caption ("$ in Millions")
    source_ref: str


def _cells(row_html: str) -> list[str]:
    """Every cell in the row, EMPTIES KEPT — position is the only thing tying a value to a year.

    Dropping blanks and then zipping against the period header shifts every later value one column
    left: a segment with no FY2025 figure silently reports FY2024's number under FY2025, and the
    row still looks well-formed. Empty `<td>`s already appear in this very table.
    """
    out: list[str] = []
    for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S):
        text = _html.unescape(re.sub(r"<[^>]+>", " ", cell))
        out.append(re.sub(r"\s+", " ", text).strip())
    return out


#: The renderer prefixes a dimensional row with its axis member — "Operating Segments | Google
#: Cloud" is the SAME segment as the plain "Google Cloud" heading, stating its income directly
#: where the plain one states revenue and costs. Left unjoined they are two keys for one segment
#: and a consumer cannot compute that segment's margin, which is the whole reason this module
#: exists. VERIFIED on the fixture: derived (revenue - costs) equals the stated income for
#: Services and Cloud in all three filed years, so joining them is a cross-check, not a guess.
_AXIS_PREFIX = re.compile(r"^[^|]*\|\s*")


def _number(cell: str) -> float | None:
    """A stated figure as a float, or None when the cell is not one.

    PARENTHESES ARE NEGATIVE, which is the whole reason this is not `float(cell)`: a segment that
    lost money renders as "(1,229)" and reading it as positive would invert the sign on exactly the
    lines a reader is looking for. `$`, commas and stray spacing are presentation.
    """
    raw = cell.replace("$", "").replace(",", "").strip()
    neg = raw.startswith("(") and raw.endswith(")")
    if neg:
        raw = raw[1:-1].strip()
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", raw):
        return None
    val = float(raw)
    return -val if neg else val


def _pick_report(summary_xml: str) -> tuple[str, str]:
    """(filename, short name) of the segment DETAILS report — or raise, naming what was there.

    A filing carries several segment reports and only one holds the numbers; the others are the
    accounting policy and a tables-only stub. Preferring "(Details)" is not a heuristic about
    wording — it is the SEC renderer's own suffix for the report that holds the tagged facts.
    """
    candidates: list[tuple[str, str]] = []
    for block in re.findall(r"<Report[^>]*>(.*?)</Report>", summary_xml, re.S):
        fname = re.search(r"<HtmlFileName>(.*?)</HtmlFileName>", block)
        short = re.search(r"<ShortName>(.*?)</ShortName>", block)
        if fname and short and _SEGMENT_REPORT.search(short.group(1)):
            candidates.append((fname.group(1), _html.unescape(short.group(1))))
    detailed = [c for c in candidates if _DETAILS.search(c[1])]
    # DOCUMENT ORDER IS NOT A CONTRACT. GOOGL's 10-K carries TWO "(Details)" reports naming
    # segments — the revenue/income table and "Long-Lived Assets by Geographic Area" — and taking
    # the first returned geography figures labelled as segment economics whenever the renderer
    # happened to emit them in the other order. Only GOOGL's ordering was ever checked; the four
    # other multi-segment names are unverified. So the ECONOMICS report is named, not positioned.
    economics = [c for c in detailed if _ECONOMICS.search(c[1])]
    if len(economics) == 1:
        return economics[0]
    if len(economics) > 1:
        raise SegmentReportUnavailableError(
            "more than one segment report names revenue or income, so which one holds the "
            f"economics is ambiguous and is not guessed: {[c[1] for c in economics]}")
    if detailed:
        raise SegmentReportUnavailableError(
            "this filing's segment (Details) reports name no revenue or income line, so none of "
            f"them carries economics — reading one anyway would file geography or asset figures "
            f"as segment earnings: {[c[1] for c in detailed]}")
    if candidates:
        raise SegmentReportUnavailableError(
            "this filing names segment reports but none is a (Details) table, so it carries the "
            f"note without the numbers: {[c[1] for c in candidates]}")
    raise SegmentReportUnavailableError(
        "this filing indexes no report naming a segment — a single-segment filer discloses none, "
        "and that is an answer rather than a failure")


def segment_rows(http: CachedHttp, cik: str, accession: str) -> list[SegmentRow]:
    """Every disclosed segment figure in one filing, as stated.

    FAILS LOUD AND EMPTY-HANDED, never partially: a filing whose segment report cannot be found
    raises rather than returning [], because "no segment disclosure" and "we could not read it"
    are different facts about the issuer and a caller cannot tell them apart from an empty list.
    """
    cik_n = str(int(cik))                      # the Archives path uses the unpadded CIK
    acc = accession.replace("-", "")
    summary = http.get_text(_FILING_SUMMARY.format(cik=cik_n, acc=acc), ttl_seconds=None)
    fname, short = _pick_report(summary)
    doc = http.get_text(_REPORT.format(cik=cik_n, acc=acc, fname=fname), ttl_seconds=None)

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", doc, re.S)
    src = f"EDGAR {accession} {fname} — {short}"
    unit, segment = "", ""
    periods: list[str] = []
    out: list[SegmentRow] = []
    for tr in rows:
        cells = _cells(tr)
        if not any(cells):
            continue
        # the caption carries the scale for every number under it ("$ in Millions")
        if not unit and "$ in" in cells[0]:
            m = re.search(r"\$ in (\w+)", cells[0])
            unit = f"${m.group(1)}" if m else ""
            continue
        # THE PERIOD HEADER CARRIES NO LABEL CELL, so it is read WHOLE. Slicing `cells[1:]` here
        # — as the value rows correctly do — drops the newest year and relabels every figure one
        # period older: FY2025's revenue arrives stamped FY2024. That is the same column-shift the
        # blank-cell fix above exists to prevent, reintroduced one row higher, and the totals still
        # reconcile because every column moved together.
        dated = [c for c in cells if c]
        if (not periods and dated
                and all(re.match(r"[A-Z][a-z]{2}\. \d", c) for c in dated)):
            periods = dated
            continue
        head, values = cells[0], [_number(c) for c in cells[1:]]
        if len([c for c in cells if c]) == 1:
            # A LONE CELL IS A SEGMENT HEADING ONLY INSIDE THE TABLE BODY. The rendered report
            # ends with an XBRL definition footer whose one-cell rows would otherwise each become
            # a "segment", so any figure that followed would be filed under a footnote's label.
            # The body's own separator marks where headings are meaningful.
            low = head.lower()
            if low.startswith("segment reporting information"):
                segment = segment or ""          # the separator itself names no segment
            elif periods and not low.startswith("("):
                segment = head
            continue
        if not periods or not any(v is not None for v in values):
            continue
        # POSITIONAL, WITH EMPTIES INTACT: `values` and `periods` are both column-aligned because
        # `_cells` kept the blanks, so a missing figure leaves a None in its own column instead of
        # pulling every later year one place left.
        for period, val in zip(periods, values[:len(periods)], strict=False):
            if val is not None:
                out.append(SegmentRow(segment=_AXIS_PREFIX.sub("", segment) or "(consolidated)",
                                      metric=head, period=period, value=val, unit=unit,
                                      source_ref=src))
    if not out:
        raise SegmentReportUnavailableError(
            f"{fname} parsed to no figures — the report was found and could not be read, which is "
            f"a different fact from an issuer that discloses no segments and must not be returned "
            f"as an empty list")
    if not unit:
        raise SegmentReportUnavailableError(
            f"{fname} states no scale in its caption, so every figure in it is unitless — a "
            f"segment income of 402836 that might be thousands, millions or dollars is the scale "
            f"defect this repo has recorded twice, and is refused rather than emitted")
    return out
