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

TWO PRESENTATIONS IN ONE TABLE, and a consumer must expect both. Alphabet's FY2025 10-K states
Google Services and Google Cloud as revenue AND a costs line (operating income is the difference)
while stating Other Bets and the reconciling items as ``Total income from operations`` directly,
under a dimensional heading the renderer writes as ``Operating Segments | Other Bets``. Reading
only the first shape loses two of the four lines and the total stops reconciling; reading only the
second loses the two that matter most. Both are returned as stated, under the heading each was
filed with.

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
    out: list[str] = []
    for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S):
        text = _html.unescape(re.sub(r"<[^>]+>", " ", cell))
        out.append(re.sub(r"\s+", " ", text).strip())
    return out


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
    if detailed:
        return detailed[0]
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
        cells = [c for c in _cells(tr) if c]
        if not cells:
            continue
        # the caption carries the scale for every number under it ("$ in Millions")
        if not unit and "$ in" in cells[0]:
            m = re.search(r"\$ in (\w+)", cells[0])
            unit = f"${m.group(1)}" if m else ""
            continue
        # the period header — the only row that is entirely dates
        if (not periods and len(cells) > 1
                and all(re.match(r"[A-Z][a-z]{2}\. \d", c) for c in cells)):
            periods = cells
            continue
        head, values = cells[0], [_number(c) for c in cells[1:]]
        if len(cells) == 1:
            # a lone cell is either a segment heading or the line-items separator
            if not head.lower().startswith("segment reporting information"):
                segment = head
            continue
        if not periods or not any(v is not None for v in values):
            continue
        for period, val in zip(periods, values, strict=False):
            if val is not None:
                out.append(SegmentRow(segment=segment or "(consolidated)", metric=head,
                                      period=period, value=val, unit=unit, source_ref=src))
    return out
