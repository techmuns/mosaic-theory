"""THE GAP TEST (fix 4a) — each missing item the synthesis prompt's rule 8 governs, sorted into one
of four types (operator ruling 2026-11-07, verbatim: "Yes, use the test"):

1. "our gap" — our pipeline did not read it. Never a signal about the company.
2. "does not apply" — the item has no meaning here (a single-segment filer has no segment profit).
3. "company's normal practice" — the filer has not disclosed it in anything we read.
4. "change or deviation" — disclosed before and absent now. The only type the prompt lets be raised
   as a risk, and only with its evidence: what was disclosed, where, and when it stopped.

A type the structured values cannot decide is "type not determined", which the prompt treats as an
unknown. NO RULE DEFAULTS TO TYPE 4 AND NONE GUESSES: each reads statuses, lists, dates and table
cells the layer already carries — never a note, and never a figure out of a display string
(CLAUDE.md). It does match LABELS as keys: CIQ's own metric names on its Guidance sheet ("EPS
Normalized", "EBITDA", "DPS"), the annual table's row labels ("FCF ($M)") and its "LTM" column, so
a renamed label changes a type, which the pins on the 28 pages would show. A value it needs and
cannot read leaves the entry "type not determined".

TWO READS BEFORE A COMPANY TYPE. The release parser misses guides companies give: on the 28 frozen
pages (freeze bcda7ce3) it reads no guide from any release of MCK, ROST or V, on whose newest
release CIQ records one. So "no guide in any release we read" cannot by itself tell our gap from
the company's practice. CIQ's Guidance sheet (`catalyst_path.guidance_bridge_rows`, the latest guide
CIQ records per metric and its date) is the second read, and both company types (3 and 4) need the
two reads to agree over a span CIQ's export reaches (its freshest row's date).

NOT BUILT, stated rather than implied:
- the PEER half of type 4 ("something peers disclose that this filer does not"): the layer carries
  peers' multiples, never their disclosures;
- a change in a FILING (a segment recast, a dropped KPI, a late filing): the layer reads one 10-K's
  segment instance and holds no KPI history;
- a release's 8-K item codes, which `ReleaseExtract` does not store, so a non-results 8-K read after
  a guided one is told apart only by time (`FULL_QUARTER`).
The registry covers the subjects rule 8 named (a segment breakout, cash-runway visibility, a forward
guide, a survival leg); the prompt reads every other UNKNOWN as "type not determined".
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from vinci.dossier.schemas import (
    GAP_TYPES,
    Concentration,
    DisclosureGap,
    FilingRef,
    FinTable,
    GapType,
    GuidanceItem,
    MechanicalLayer,
    ReleaseExtract,
    Sourced,
    SourceStatus,
)

OUR, NA, PRACTICE, CHANGE, UNDETERMINED = GAP_TYPES
PRESENT = SourceStatus.PRESENT

#: CIQ dates a guide on its announcement; the 8-K can follow by a day or two.
NEAR = timedelta(days=3)
#: A guide is "absent now" only after releases spanning a full reporting quarter since it: the
#: release list holds every EX-99.1, and a non-results 8-K a month after a guided one is no stop.
FULL_QUARTER = timedelta(days=75)

#: Where the second read lives, named in a basis as a field path, never its long source_ref.
CIQ_GUIDES = "catalyst_path.guidance_bridge_rows"


def _missing(s: Sourced[Any] | None) -> bool:
    return s is not None and s.status is not PRESENT


# ------------------------------------------------------------------------------- the two reads

@dataclass(frozen=True)
class _Ciq:
    """CIQ's Guidance sheet as (metric, date) pairs, and how far its export reaches."""

    rows: tuple[tuple[str, date], ...]
    reach: date

    def dated(self, family: Callable[[str], bool]) -> list[tuple[str, date]]:
        return [(m, d) for m, d in self.rows if family(m)]


def _ciq(mech: MechanicalLayer) -> _Ciq | None:
    """None when there is no second read: no sheet, no rows, or a row whose date does not parse
    (an unreadable row could be the one that refutes a type, so none is skipped)."""
    cp = mech.catalyst_path
    rows = cp.guidance_bridge_rows if cp is not None else None
    if rows is None or rows.status is not PRESENT or not rows.value:
        return None
    out: list[tuple[str, date]] = []
    for r in rows.value:
        try:
            out.append((r.metric, date.fromisoformat(r.dated)))
        except ValueError:
            return None
    return _Ciq(tuple(out), max(d for _, d in out))


def _releases(mech: MechanicalLayer) -> list[ReleaseExtract] | None:
    """The releases read, oldest first; None when any carries no filing date (they cannot be
    ordered, and a change is an order)."""
    ps = mech.primary_source
    rels = list(ps.releases) if ps is not None else []
    if any(r.filed is None for r in rels):
        return None
    return sorted(rels, key=lambda r: (r.filed, r.source_ref))


def _filed(r: ReleaseExtract) -> date:
    assert r.filed is not None  # `_releases` returns only dated releases
    return r.filed


# CIQ's metric labels, as its Guidance sheet writes them
def _ciq_eps(metric: str) -> bool:
    return metric.startswith("EPS")


def _ciq_ebitda(metric: str) -> bool:
    return metric == "EBITDA"


def _ciq_any(metric: str) -> bool:
    return metric != "DPS"   # a declared dividend is not an outlook


# the release parser's own metric vocabulary (`GuidanceItem.metric`)
def _adj_eps(g: GuidanceItem) -> bool:
    return g.metric == "adjusted eps"


def _adj_ebitda(g: GuidanceItem) -> bool:
    return g.metric == "adjusted ebitda"


def _adj_ebitda_level(g: GuidanceItem) -> bool:
    """What `mechanical._adjusted_facts` can divide by: a dollar range, not a rate."""
    return (_adj_ebitda(g) and not g.qualitative and g.unit == "$M" and g.basis == "level"
            and g.low is not None)


def _any_item(g: GuidanceItem) -> bool:
    return True


@dataclass(frozen=True)
class _Guide:
    """One guide item: the release dates the field reads, the release items that would have
    filled it (``fills``; None where the field would then be PRESENT), the release items that show
    the company guides it at all (``guides``), and CIQ's metrics for the same thing."""

    item: str
    fields: list[str]
    read_at: list[date]
    fills: Callable[[GuidanceItem], bool] | None
    guides: Callable[[GuidanceItem], bool]
    family: Callable[[str], bool]
    noun: str


def _guide_gap(g: _Guide, rels: list[ReleaseExtract] | None, ciq: _Ciq | None) -> DisclosureGap:
    def gap(kind: GapType, basis: str, **kw: str) -> DisclosureGap:
        return DisclosureGap(item=g.item, fields=g.fields, type=kind, basis=basis, **kw)

    if rels is None:
        return gap(UNDETERMINED, "a release read carries no filing date, so the releases cannot "
                                 "be ordered")
    # newest first: the evidence a type cites is the latest that decides it
    at = {d: [r for r in rels if r.filed == d] for d in sorted(set(g.read_at), reverse=True)}
    # (1a) the release parser read it from the filing this field reads, and the field did not
    if g.fills is not None:
        for d, rs in at.items():
            hit = next((r for r in rs if any(g.fills(x) for x in r.guidance)), None)
            if hit is not None:
                return gap(OUR, f"the release parser read {g.noun} from the release filed "
                                f"{d.isoformat()}; this field did not take it",
                           source_ref=hit.source_ref)
    # (1b) CIQ records one at a release this field reads, from which the parser read no guide
    if ciq is not None:
        for d, rs in at.items():
            if any(r.guidance for r in rs):
                continue
            row = next(((m, c) for m, c in ciq.dated(g.family) if abs(c - d) <= NEAR), None)
            if row is not None:
                where = (f"the release filed {d.isoformat()}, from which the release parser read "
                         "no guide" if rs else
                         f"the 8-K filed {d.isoformat()}, whose release the parser did not read")
                return gap(OUR, f"CIQ records {row[0]} guidance dated {row[1].isoformat()} "
                                f"({CIQ_GUIDES}), at {where}")
    guided = [r for r in rels if any(g.guides(x) for x in r.guidance)]
    # (4) stated, then absent from every release read for a full quarter since, and CIQ agrees
    if guided and ciq is not None:
        last = guided[-1]
        later = [r for r in rels if _filed(r) > _filed(last)]
        item = next(x for x in last.guidance if g.guides(x))
        if (later and _filed(later[-1]) - _filed(last) >= FULL_QUARTER
                and ciq.reach >= _filed(later[-1]) - NEAR
                and not any(c > _filed(last) + NEAR for _, c in ciq.dated(g.family))):
            return gap(CHANGE, f"the release filed {_filed(last).isoformat()} states it; none of "
                               f"the {len(later)} release(s) read since does, and {CIQ_GUIDES}, "
                               f"which reaches {ciq.reach.isoformat()}, records none after it",
                       disclosed=f"{item.metric} guide for {item.period}",
                       source_ref=last.source_ref, stopped=_filed(later[0]).isoformat(),
                       stopped_ref=later[0].source_ref)
    # (3) no release read states one, and CIQ, reaching the newest, records none since the oldest
    if len(rels) >= 2 and not guided and ciq is not None:
        oldest, newest = _filed(rels[0]), _filed(rels[-1])
        if (ciq.reach >= newest - NEAR
                and not any(c >= oldest - NEAR for _, c in ciq.dated(g.family))):
            return gap(PRACTICE, f"none of the {len(rels)} releases read ({oldest.isoformat()} to "
                                 f"{newest.isoformat()}) states {g.noun}, and {CIQ_GUIDES}, which "
                                 f"reaches {ciq.reach.isoformat()}, records none since "
                                 f"{oldest.isoformat()}")
    return gap(UNDETERMINED, _why_undetermined(g, rels, ciq, guided))


def _why_undetermined(g: _Guide, rels: list[ReleaseExtract], ciq: _Ciq | None,
                      guided: list[ReleaseExtract]) -> str:
    if ciq is None:
        return f"there is no second read: {CIQ_GUIDES} is absent or undated"
    if not rels:
        return "no release was read"
    newest = _filed(rels[-1])
    if ciq.reach < newest - NEAR:
        return (f"{CIQ_GUIDES} reaches {ciq.reach.isoformat()}, before the newest release read "
                f"({newest.isoformat()})")
    if guided and _filed(guided[-1]) == newest:
        return f"the newest release read ({newest.isoformat()}) states {g.noun}"
    if guided:
        return (f"the release filed {_filed(guided[-1]).isoformat()} states {g.noun}; the "
                "releases since do not span a full quarter, or CIQ records one after it")
    if len(rels) < 2:
        return "one release was read"
    return (f"the release parser read {g.noun} from none of the {len(rels)} releases, while "
            f"{CIQ_GUIDES} records one since {_filed(rels[0]).isoformat()}")


# ------------------------------------------------------------------------------------- items

def _segment_gap(c: Concentration, segment_count: int | None) -> DisclosureGap | None:
    """Segment profit. A filer reporting more than one segment discloses a profit measure for
    each (ASC 280-10-50-22; IFRS 8.23 likewise), so a multi-segment filer whose profit the page
    lacks is a read we did not make."""
    sp, se = c.segment_profit, c.segment_ebitda
    if sp is not None and sp.status is PRESENT:
        if not _missing(se) or sp.value is None:
            return None
        return DisclosureGap(
            item="segment EBITDA", fields=["concentration.segment_ebitda"], type=PRACTICE,
            basis=f"the filer's segment measure is its {sp.value.measure_kind} "
                  "(concentration.segment_profit), not EBITDA")
    fields = [f for f, s in (("concentration.segment_profit", sp),
                             ("concentration.segment_ebitda", se)) if _missing(s)]
    if se.status is PRESENT:
        if not fields:
            return None
        return DisclosureGap(
            item="segment profit from the 10-K", fields=fields, type=OUR,
            basis="the 10-K XBRL read of a segment profit failed; CIQ's segment EBITDA "
                  "(concentration.segment_ebitda) is on the page")
    if not fields:
        return None
    if segment_count is None:
        return DisclosureGap(item="segment profit by segment", fields=fields, type=UNDETERMINED,
                             basis="CIQ's segment revenue roster cannot be read, so the segment "
                                   "count is not known")
    if segment_count == 1:
        if sp is not None:   # the XBRL read found two or more segments where CIQ reads one
            return DisclosureGap(item="segment profit by segment", fields=fields,
                                 type=UNDETERMINED,
                                 basis="CIQ's Segments sheet reads one segment, while the 10-K "
                                       "XBRL read found segment contexts")
        return DisclosureGap(item="segment profit by segment", fields=fields, type=NA,
                             basis="CIQ's Segments sheet reads one segment, and the 10-K XBRL "
                                   "instance tags fewer than two; there is no breakout to give")
    # None is also no CIK or no annual report yet: say what is on the page, never a read not made
    how = ("failed" if sp is not None else "states no segment profit")
    return DisclosureGap(item="segment profit by segment", fields=fields, type=OUR,
                         basis=f"CIQ's Segments sheet splits revenue into {segment_count} lines, "
                               "and a filer reporting more than one segment discloses a profit "
                               f"measure for each; the 10-K XBRL read {how}")


def _windows(mech: MechanicalLayer) -> list[tuple[str, list[FilingRef], Sourced[str]]]:
    dc = mech.drawdown_cause
    out = [("drawdown_cause", dc.filings, dc.revised_guidance)]
    if dc.anchor is not None:
        out.append(("drawdown_cause.anchor.at_anchor", dc.anchor.at_anchor.filings,
                    dc.anchor.at_anchor.revised_guidance))
        if dc.anchor.since is not None:
            out.append(("drawdown_cause.anchor.since", dc.anchor.since.filings,
                        dc.anchor.since.revised_guidance))
    return out


def _filing_dates(filings: Sequence[FilingRef]) -> list[date] | None:
    try:
        return sorted({date.fromisoformat(f.filing_date) for f in filings})
    except ValueError:
        return None


_OUTLOOK = "the outlook a gap-down's 8-K furnished"


def _drawdown_gaps(mech: MechanicalLayer, rels: list[ReleaseExtract] | None,
                   ciq: _Ciq | None) -> list[DisclosureGap]:
    v, q = mech.valuation, mech.quality
    adjusted = [f for f, s in (("valuation.ev_ebitda_adjusted_fwd", v.ev_ebitda_adjusted_fwd),
                               ("quality.net_debt_to_ebitda_adjusted",
                                q.net_debt_to_ebitda_adjusted)) if _missing(s)]
    out: list[DisclosureGap] = []
    empty: list[str] = []   # the windows with no gap-down 8-K — ONE entry for all of them
    for prefix, filings, guidance in _windows(mech):
        if not _missing(guidance):
            continue
        field = f"{prefix}.revised_guidance"
        if not filings:
            empty.append(prefix)
            continue
        dates = _filing_dates(filings)
        if dates is None:
            out.append(DisclosureGap(item=_OUTLOOK, fields=[field], type=UNDETERMINED,
                                     basis=f"a filing date in {prefix}.filings does not parse"))
            continue
        out.append(_guide_gap(_Guide(item=_OUTLOOK, fields=[field], read_at=dates,
                                     fills=_any_item, guides=_any_item, family=_ciq_any,
                                     noun="a guide"), rels, ciq))
    current_na = "drawdown_cause" in empty
    if empty:
        where = ", ".join(f"{p}.filings" for p in empty)
        out.insert(0, DisclosureGap(
            item=_OUTLOOK,
            fields=[*(f"{p}.revised_guidance" for p in empty), *(adjusted if current_na else [])],
            type=NA, basis=f"no gap-down 8-K is in the window{'s' if len(empty) > 1 else ''} "
                           f"({where} empty), and these read only the outlook such an 8-K "
                           "furnishes"))
    if adjusted and not current_na:
        item = "a company adjusted-EBITDA guide at the gap-down"
        dates = _filing_dates(mech.drawdown_cause.filings)
        if dates is None:   # as the outlook's entry: a filing that cannot be placed decides nothing
            out.append(DisclosureGap(item=item, fields=adjusted, type=UNDETERMINED,
                                     basis="a filing date in drawdown_cause.filings does not "
                                           "parse"))
        else:
            out.append(_guide_gap(_Guide(
                item=item, fields=adjusted, read_at=dates, fills=_adj_ebitda_level,
                guides=_adj_ebitda, family=_ciq_ebitda, noun="an adjusted-EBITDA guide"),
                rels, ciq))
    return out


def _annual(mech: MechanicalLayer) -> tuple[FinTable, int] | None:
    """The annual table and its LTM column, when the page carries both."""
    fs = mech.financial_summary
    ann = fs.annual if fs is not None else None
    if ann is None or ann.status is not PRESENT or ann.value is None:
        return None
    if "LTM" not in ann.value.columns:
        return None
    return ann.value, ann.value.columns.index("LTM")


def _ltm(table: tuple[FinTable, int], label: str) -> float | None:
    t, col = table
    row = next((r for r in t.rows if r.label == label), None)
    if row is None or col >= len(row.values):
        return None
    return row.values[col]


def _survival_gaps(mech: MechanicalLayer) -> list[DisclosureGap]:
    q = mech.quality
    table = _annual(mech)
    out: list[DisclosureGap] = []
    if _missing(q.fcf_sign):
        has = table is not None and (_ltm(table, "FCF ($M)") is not None or (
            _ltm(table, "CFO ($M)") is not None and _ltm(table, "Capex ($M)") is not None))
        out.append(DisclosureGap(
            item="the FCF sign behind the survival line's runway leg", fields=["quality.fcf_sign"],
            type=OUR if has else UNDETERMINED,
            basis=("the FCF-sign read is UNKNOWN while the page's annual table "
                   "(financial_summary.annual) states LTM cash flow" if has else
                   "the FCF-sign read is UNKNOWN, and the annual table states no LTM cash flow")))
    if _missing(q.net_debt_to_ebitda):
        ebitda = _ltm(table, "EBITDA ($M)") if table is not None else None
        fields = ["quality.net_debt_to_ebitda"]
        ls = mech.leverage_survival
        if ls is not None and _missing(ls.net_debt_to_ebitda):
            fields.append("leverage_survival.net_debt_to_ebitda")
        out.append(DisclosureGap(
            item="net debt / EBITDA", fields=fields,
            type=NA if ebitda is not None and ebitda <= 0 else UNDETERMINED,
            basis=("the annual table's LTM EBITDA is not positive, and a ratio to it has no "
                   "meaning" if ebitda is not None and ebitda <= 0 else
                   "the annual table states no non-positive LTM EBITDA that would make the ratio "
                   "inapplicable")))
    return out


def disclosure_gaps(mech: MechanicalLayer, *, segment_count: int | None) -> list[DisclosureGap]:
    """Every gap the registry covers, typed — an empty list when the page has none. Reads the
    layer alone, plus ``segment_count`` (`ciq_sheets.segment_count`: CIQ's segment roster, which
    the layer carries only as a display string). Deterministic: the same layer gives the same
    list, in the same order."""
    rels, ciq = _releases(mech), _ciq(mech)
    out: list[DisclosureGap] = []
    if (seg := _segment_gap(mech.concentration, segment_count)) is not None:
        out.append(seg)
    out += _drawdown_gaps(mech, rels, ciq)
    newest = [_filed(rels[-1])] if rels else []
    if _missing(mech.valuation.adjusted_eps):
        out.append(_guide_gap(_Guide(
            item="an annual adjusted-EPS guide in the newest release",
            fields=["valuation.adjusted_eps"], read_at=newest, fills=None, guides=_adj_eps,
            family=_ciq_eps, noun="an adjusted-EPS guide"), rels, ciq))
    ps = mech.primary_source
    if ps is not None and _missing(ps.current_guide):
        out.append(_guide_gap(_Guide(
            item="a current guide", fields=["primary_source.current_guide"],
            read_at=sorted({_filed(r) for r in rels}) if rels else [], fills=None,
            guides=_any_item, family=_ciq_any, noun="a guide"), rels, ciq))
    out += _survival_gaps(mech)
    return out
