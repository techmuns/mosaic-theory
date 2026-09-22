"""Per-segment PROFIT from a 10-K's own XBRL instance — the structured source, not a rendered table.

WHY NOT THE R-FILES (`vinci/edgar/segments.py`). That route reads the SEC's RENDERED segment table,
and the rendering is the filer's layout: segments as row headings (AMZN, GOOGL, AORT, UBER) or as
COLUMNS (IT, EPAM, PARR, WERN), nested sub-members (WLK, VRRM), and report titles that name
the right table in a different vocabulary at every filer. Measured on the ten multi-segment names in
the
book (2026-09-21), its title-based pick found the right table for ONE (GOOGL), refused six, and
SILENTLY returned the wrong table for three — WERN's and VRRM's COUNTRY revenue and WLK's
reconciliation-to-pretax lines, each labelled as segment economics. Parsing a rendered view is
parsing a display string; the house rule is structured values.

THE INSTANCE IS THE STRUCTURED SOURCE. Every figure in it carries its segment as a DIMENSION on its
context, so the layout the filer chose for its HTML never reaches this parser. Values are exact, in
the unit their ``unitRef`` names — there is no "$ in Millions" caption to misread.

THE RULES, each read off the ten real filings rather than assumed:

* A SEGMENT CONTEXT carries ``us-gaap:StatementBusinessSegmentsAxis`` — or the GEOGRAPHICAL axis
  beside ``srt:ConsolidationItemsAxis = us-gaap:OperatingSegmentsMember``, and no other axis. The
  second form is EPAM's: its operating segments ARE geographies, and a rule keyed on the
  business-segments axis alone reads its revenue and never its profit. It is named, not "any
  axis": TECX pairs the same qualifier with the income-statement-location axis to itemise its ONE
  segment's expenses, and "any axis" read five expense lines as five segments.
* THE MEASURE is the filer's own: ``OperatingIncomeLoss`` when two or more segments carry it
  (AMZN, GOOGL, WLK, WERN, VRRM, PARR); else a filer-defined segment-profit element (EPAM's
  ``SegmentOperatingProfitLoss``, UBER's adjusted EBITDA); else ``GrossProfit`` (IT, AORT). It is
  NAMED on the output — a gross profit is never presented as an operating income.
* THE SEGMENTS are the members that CARRY the measure. That is what excludes, without a list of
  names, the members that are not segments of profit: AORT's four geographic regions and WERN's
  aggregate members sit on the segment axis carrying revenue only.
* REVENUE is read from the IDENTICAL context as the profit — never joined by member name. EPAM tags
  segment revenue on business-axis members and segment profit on geographic ones; a name join would
  pair them by guesswork.

WHAT IT REFUSES. A filing naming ONE segment or none is a single-segment filer — ``None``, an
answer, not a failure. A filing naming two or more segments where fewer than two carry any profit
measure raises, because "we could not find the profit" is a different fact from "there is none".
A non-USD figure raises: this repo reads US filers, and a currency it did not convert is a scale
defect waiting to be printed.
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from vinci.netcache import CachedHttp

_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
_FILE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{name}"

SEGMENT_AXIS = "us-gaap:StatementBusinessSegmentsAxis"
#: The ONE other axis a filer's operating segments may live on — and only beside the
#: operating-segments qualifier. EPAM's segments ARE geographies. NOT any other axis: TECX pairs the
#: same qualifier with `IncomeStatementLocationAxis` to break its ONE segment's expenses into lines
#: (clinical, CMC, employee costs), and a rule that accepted any axis read those as five segments.
GEOGRAPHIC_AXIS = "srt:StatementGeographicalAxis"
CONSOLIDATION_AXIS = "srt:ConsolidationItemsAxis"
OPERATING_SEGMENTS = "us-gaap:OperatingSegmentsMember"
#: The measure, in the order it is preferred. Operating income is the standard; a filer-defined
#: segment measure is the chief operating decision maker's own and outranks a gross profit.
OPERATING_INCOME = "us-gaap:OperatingIncomeLoss"
GROSS_PROFIT = "us-gaap:GrossProfit"
#: A plain EBIT is a filer-defined measure too. Nike's CODM runs its segments on EBIT and tags it
#: `nke:EarningsBeforeInterestAndTaxes` beside `us-gaap:GrossProfit` on the SAME two segments;
#: with only the ADJUSTED spelling listed here, gross profit won by default and NKE's first page
#: called it "the filer's measure" (2026-09-22). No us-gaap element carries this name, so it can
#: only ever match a filer's own extension.
#: RANKED BELOW every segment-specific spelling (review of #640): the candidates are otherwise
#: tried alphabetically, and a filer tagging both a plain `xyz:EarningsBeforeInterestAndTaxes` and
#: its CODM's `xyz:SegmentProfit` on the same segments would have had "E" beat "S" — the plain EBIT
#: printed as the filer's segment measure over the one the filer names as its segment measure.
_SEGMENT_MEASURE = re.compile(
    r"Segment(?:Operating)?Profit|SegmentAdjusted|AdjustedEarningsBeforeInterest|AdjustedEBITDA|"
    r"Segment(?:Gross)?Contribution", re.I)
_PLAIN_EBIT = re.compile(r"EarningsBeforeInterestAndTaxes", re.I)
_FILER_MEASURE = re.compile(f"{_SEGMENT_MEASURE.pattern}|{_PLAIN_EBIT.pattern}", re.I)
_REVENUE = ("us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax")
_XBRLI = "{http://www.xbrl.org/2003/instance}"
_XBRLDI = "{http://xbrl.org/2006/xbrldi}"
_ISO4217 = "http://www.xbrl.org/2003/iso4217"


class SegmentFactsUnavailableError(RuntimeError):
    """The filing has segment contexts and still yields no usable per-segment profit — stated."""


@dataclass(frozen=True)
class SegmentFigure:
    member: str                  # the XBRL member, verbatim — the key a human can check
    segment: str                 # the member humanised ("parr:RefiningMember" → "Refining")
    profit: float                # USD
    revenue: float | None        # USD, from the IDENTICAL context; None when not tagged there


@dataclass(frozen=True)
class SegmentProfitRead:
    measure: str                 # the element, verbatim
    measure_kind: str            # "operating income" | "gross profit" |
    #                              "filer-defined segment measure"
    period_end: date
    figures: tuple[SegmentFigure, ...]
    segments_total: float | None  # the measure on the operating-segments total context, if tagged
    consolidated: float | None    # the measure on the no-dimension context, if tagged
    accession: str
    instance: str


def humanise(member: str) -> str:
    """``amzn:AmazonWebServicesSegmentMember`` → ``Amazon Web Services``. The filer's own element
    name, made readable — never a vocabulary this module invented."""
    local = member.split(":", 1)[-1]
    local = re.sub(r"(?:Reportable|Operating|Business)?Segments?Member$|Member$", "", local)
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", local).strip()
    return words or local


def _qname(tag: str, prefixes: dict[str, str]) -> str:
    """``{uri}Local`` → ``prefix:Local`` using the instance's own namespace declarations."""
    if tag.startswith("{"):
        uri, local = tag[1:].split("}", 1)
        return f"{prefixes.get(uri, uri)}:{local}"
    return tag


def _instance_name(http: CachedHttp, cik: str, accession: str) -> str:
    idx = http.get_json(_INDEX.format(cik=int(cik), acc=accession.replace("-", "")),
                        ttl_seconds=None)
    names = [str(i["name"]) for i in idx["directory"]["item"]
             if str(i["name"]).endswith("_htm.xml")]
    if len(names) != 1:
        raise SegmentFactsUnavailableError(
            f"{accession}: expected exactly one extracted XBRL instance (*_htm.xml), found "
            f"{names or 'none'} — not guessed between")
    return names[0]


def _iso(node: ET.Element | None) -> date | None:
    text = (node.text or "").strip() if node is not None else ""
    return date.fromisoformat(text) if text else None


Dims = tuple[tuple[str, str], ...]


def _segment_member(dims: dict[str, str]) -> str | None:
    """The segment a context names, or None. See the module note for the two accepted shapes."""
    rest = dict(dims)
    cons = rest.pop(CONSOLIDATION_AXIS, None)
    if cons is not None and cons != OPERATING_SEGMENTS:
        return None                         # corporate, eliminations, reconciling — not a segment
    if len(rest) != 1:
        return None
    axis, member = next(iter(rest.items()))
    if axis == SEGMENT_AXIS:
        return member
    return member if (axis == GEOGRAPHIC_AXIS and cons == OPERATING_SEGMENTS) else None


def _is_measure_or_revenue(element: str) -> bool:
    return (element in (OPERATING_INCOME, GROSS_PROFIT, *_REVENUE)
            or bool(_FILER_MEASURE.search(element.split(":", 1)[-1])))


def parse_instance(xml_text: str, *, accession: str = "", instance: str = ""
                   ) -> SegmentProfitRead | None:
    """The per-segment profit read from ONE instance document — pure, no I/O, so it is pinned on
    real filings frozen as fixtures. None = no segment context at all (a single-segment filer)."""
    prefixes: dict[str, str] = {}
    for _event, item in ET.iterparse(io.StringIO(xml_text), events=("start-ns",)):
        ns_prefix, ns_uri = cast(tuple[str, str], item)
        prefixes.setdefault(ns_uri, ns_prefix)
    root = ET.fromstring(xml_text)

    def qn(node: ET.Element) -> str:
        return _qname(node.tag, prefixes)

    contexts: dict[str, tuple[dict[str, str], date | None, date | None]] = {}
    for ctx in root.iter(f"{_XBRLI}context"):
        dims = {m.get("dimension", ""): (m.text or "").strip()
                for m in ctx.iter(f"{_XBRLDI}explicitMember")}
        contexts[ctx.get("id", "")] = (dims,
                                       _iso(ctx.find(f"{_XBRLI}period/{_XBRLI}startDate")),
                                       _iso(ctx.find(f"{_XBRLI}period/{_XBRLI}endDate")))

    pe_node = next((n for n in root if qn(n) == "dei:DocumentPeriodEndDate"), None)
    if _iso(pe_node) is None or pe_node is None:
        raise SegmentFactsUnavailableError(f"{accession}: no dei:DocumentPeriodEndDate")
    # THE PERIOD IS THE REQUIRED CONTEXT'S END, not the dei VALUE. A 52/53-week filer may state
    # its period end as the nominal month-end while every fact's context ends on the actual last
    # Saturday; matched on the value, no fact is a fiscal-year fact, no segment is seen, and a
    # multi-segment filer reads as single-segment — silently. The value is the fallback only.
    period_end = contexts.get(pe_node.get("contextRef", ""), ({}, None, None))[2] or _iso(pe_node)
    assert period_end is not None

    # unit id → its currency (the ISO 4217 code), or None for a non-monetary unit (pure, shares,
    # a ratio). The unitRef is an ID the filer chose ("usd", "U_USD", "U001"); only the unit's own
    # <measure> says what it is — the id is a label, never read as a fact.
    ns_of = {pfx: uri for uri, pfx in prefixes.items()}
    currency: dict[str, str | None] = {}
    for u in root.iter(f"{_XBRLI}unit"):
        ms = [(m.text or "").strip() for m in u.iter(f"{_XBRLI}measure")]
        pfx, _, code = ms[0].partition(":") if len(ms) == 1 else ("", "", "")
        # the ISO 4217 namespace by its URI; the conventional prefix is accepted only when the
        # document does not bind it to something else (a trimmed instance may omit the xmlns)
        iso = ns_of.get(pfx, _ISO4217 if pfx == "iso4217" else "") == _ISO4217
        currency[u.get("id", "")] = code.upper() if code and iso else None

    def fiscal_year(cid: str) -> bool:
        _dims, start, stop = contexts.get(cid, ({}, None, None))
        return bool(start and stop and stop == period_end and 350 <= (stop - start).days <= 380)

    # every FY numeric fact, keyed by (element, frozen dims)
    by_ctx: dict[tuple[str, Dims], float] = {}
    segment_members: set[str] = set()
    for node in root:
        cid = node.get("contextRef")
        if not cid or not fiscal_year(cid) or node.text is None:
            continue
        try:
            val = float(node.text.strip())
        except ValueError:
            continue
        element, dims = qn(node), contexts[cid][0]
        unit_id = node.get("unitRef") or ""
        member_here = _segment_member(dims)
        if member_here is not None:
            segment_members.add(member_here)
        if unit_id not in currency:
            if member_here is not None and _is_measure_or_revenue(element):
                raise SegmentFactsUnavailableError(
                    f"{accession}: {element} names unit {unit_id!r}, which the instance never "
                    f"declares — refused, never assumed to be USD")
            continue
        cur = currency[unit_id]
        if cur is None:
            continue    # a margin %, a share count, a ratio — never a profit or a revenue amount
        if cur != "USD":
            if member_here is not None and _is_measure_or_revenue(element):
                raise SegmentFactsUnavailableError(
                    f"{accession}: {element} is tagged in {cur}, not USD — refused, never "
                    f"printed unconverted")
            continue
        by_ctx[(element, tuple(sorted(dims.items())))] = val
    # ONE SEGMENT IS A SINGLE-SEGMENT FILER, not a failure. Since the 2024 segment-disclosure rule
    # (ASU 2023-07) a one-segment company tags that one segment too — LLY, NFLX, CNXC, NCNO, VITL,
    # FUBO and TECX all do — so "has a segment context" stopped meaning "has segments". Read as
    # multi-segment, seven pages would have carried a note saying their segment profit could not
    # be found, about a breakdown they do not have.
    if len(segment_members) <= 1:
        return None

    def carriers(element: str) -> dict[Dims, float]:
        """ONE context per SEGMENT MEMBER. A filer may state a segment's figure twice — on
        {segment} and on {segment, OperatingSegments} (Alphabet does, for revenue) — and a context
        count would list that segment twice and sum it twice. Equal figures are one segment (the
        qualified context kept); unequal figures for one member are refused, never picked."""
        out: dict[str, tuple[Dims, float]] = {}
        for (el, d), v in by_ctx.items():
            member = _segment_member(dict(d)) if el == element else None
            if member is None:
                continue
            if member in out:
                prev_d, prev_v = out[member]
                if prev_v != v:
                    raise SegmentFactsUnavailableError(
                        f"{accession}: {element} states {member} twice with different figures "
                        f"({prev_v:,.0f} vs {v:,.0f}) — not guessed between")
                if CONSOLIDATION_AXIS in dict(prev_d):
                    continue
            out[member] = (d, v)
        return dict(out.values())

    elements = {el for (el, _d) in by_ctx}
    ordered = ([OPERATING_INCOME]
               + sorted((el for el in elements if _FILER_MEASURE.search(el.split(":", 1)[-1])),
                        key=lambda el: (_SEGMENT_MEASURE.search(el.split(":", 1)[-1]) is None, el))
               + [GROSS_PROFIT])
    measure: str | None = None
    kind = ""
    for candidate in ordered:
        if len(carriers(candidate)) >= 2:
            measure = candidate
            kind = ("operating income" if candidate == OPERATING_INCOME else
                    "gross profit" if candidate == GROSS_PROFIT else
                    "filer-defined segment measure")
            break
    if measure is None:
        raise SegmentFactsUnavailableError(
            f"{accession}: segment contexts exist but no profit measure (operating income, a "
            f"filer-defined segment measure, or gross profit) is tagged on two or more segments")

    figures = []
    for key, profit in sorted(carriers(measure).items(), key=lambda kv: -kv[1]):
        member = _segment_member(dict(key))
        if member is None:                  # carriers() admits only segment contexts
            continue
        revenue = next((by_ctx[(r, key)] for r in _REVENUE if (r, key) in by_ctx), None)
        if revenue is None and dict(key).get(SEGMENT_AXIS) == member:
            # THE QUALIFIER IS A NO-OP ON THE BUSINESS-SEGMENT AXIS, and only there. Alphabet tags
            # Cloud's income on {segment: Cloud, consolidation: OperatingSegments} and its revenue
            # on {segment: Cloud} — one segment, stated twice. On a GEOGRAPHIC axis the unqualified
            # context is the geographic disclosure instead (EPAM's revenue by customer location),
            # a different number, so the fallback never reaches there.
            bare: Dims = ((SEGMENT_AXIS, member),)
            revenue = next((by_ctx[(r, bare)] for r in _REVENUE if (r, bare) in by_ctx), None)
        figures.append(SegmentFigure(member=member, segment=humanise(member), profit=profit,
                                     revenue=revenue))
    return SegmentProfitRead(
        measure=measure, measure_kind=kind, period_end=period_end, figures=tuple(figures),
        segments_total=by_ctx.get((measure, ((CONSOLIDATION_AXIS, OPERATING_SEGMENTS),))),
        consolidated=by_ctx.get((measure, ())), accession=accession, instance=instance)


def segment_profit(http: CachedHttp, cik: str, accession: str) -> SegmentProfitRead | None:
    """Fetch the filing's instance and read it. Immutable once filed, so it caches forever."""
    name = _instance_name(http, cik, accession)
    xml_text = http.get_text(_FILE.format(cik=int(cik), acc=accession.replace("-", ""), name=name),
                             ttl_seconds=None)
    return parse_instance(xml_text, accession=accession, instance=name)
