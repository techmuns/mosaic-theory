"""THE GAP TEST (fix 4a) — each missing item the synthesis prompt's rule 8 governs, sorted into one
of four types (operator ruling 2026-11-07, verbatim: "Yes, use the test"):

1. "our gap" — our pipeline did not read it. Never a signal about the company.
2. "does not apply" — the item has no meaning here (a single-segment filer has no segment profit).
3. "company's normal practice" — the filer has not disclosed it in anything we read.
4. "change or deviation" — disclosed before and absent now. The only type the prompt lets be raised
   as a risk, and only with its evidence: what was disclosed, where, and when it stopped.

A type the structured values cannot decide is "type not determined", which the prompt treats as an
unknown. NO RULE GUESSES: each reads statuses, lists, dates and table cells the layer already
carries — never a note, and never a figure out of a display string (CLAUDE.md). It does match
LABELS as keys: CIQ's own metric names on its Guidance sheet ("EPS Normalized", "EBITDA", "DPS"),
the annual table's row labels ("FCF ($M)") and its "LTM" column, so a renamed label changes a
type, which the pins on the 28 pages would show. A value it needs and cannot read leaves the entry
"type not determined".

TWO READS BEFORE A COMPANY TYPE. The release parser misses guides companies give: on the 28 frozen
pages (freeze bcda7ce3) it reads no guide from any release of MCK, ROST or V, on whose newest
release CIQ records one. So "no guide in any release we read" cannot by itself tell our gap from
the company's practice. CIQ's Guidance sheet (`catalyst_path.guidance_bridge_rows`, the latest guide
CIQ records per metric and its date) is the second read, and "company's normal practice" needs the
two reads to agree over a span CIQ's export reaches (its freshest row's date).

NO PATH EMITS TYPE 4 TODAY (coordinator review of #927, F5, measured 2026-11-08). The only change
the layer could show is a guide stated in one release and absent from those since, with CIQ silent
after it. Neither half is evidence:
- the release parser's blanks are mostly misses (MCK, ROST and V above);
- CIQ keeps one latest date per metric, and a guide reaffirmed unchanged is shown re-dated once on
  the corpus (AORT's 2026 revenue, 2026-05-07 → 08-06) and never shown otherwise.
So that pattern reads "type not determined", saying why. A false type 4 is a false risk, the worst
direction. The schema, the prompt's rule 8 and this module's ladder keep the type for the day a
second read whose silence is evidence exists.

AS OF THE PAGE'S PRICE DATE (F12): a release filed, or a CIQ guide dated, after the page's price
date (`stock_info.as_of`, else the drawdown window's end) is not read here. Since STATE row 57 the
assembly cuts both where it builds them, through the same rule (`vinci.edgar.asof.within_cut`,
`releases_by_cut` below), so on a page built since, these cuts find nothing; they still hold the
line on a page built before it (ORKA's, at the panel's freeze, holds a release filed 2026-10-26
beside its 2026-10-23 price date).

NOT BUILT, stated rather than implied:
- the PEER half of type 4 ("something peers disclose that this filer does not"): the layer carries
  peers' multiples, never their disclosures;
- a change in a FILING (a segment recast, a dropped KPI, a late filing): the layer reads one 10-K's
  segment instance and holds no KPI history;
- a release's 8-K item codes: the releases are the EX-99.1s of the 10 newest 8-Ks carrying item
  2.02 or 8.01 (`mechanical._primary_source`), so an outlook furnished under 7.01 is never read,
  and a non-results 8-K after a guided one is told apart only by time (`FULL_QUARTER`).
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
from vinci.edgar.asof import within_cut

OUR, NA, PRACTICE, CHANGE, UNDETERMINED = GAP_TYPES
PRESENT = SourceStatus.PRESENT

#: CIQ dates a guide on its announcement; the 8-K can follow by a day or two.
NEAR = timedelta(days=3)
#: A guide is "absent" only after releases spanning a full reporting quarter since it: a non-results
#: 8-K a month after a guided one is no stop.
FULL_QUARTER = timedelta(days=75)
#: THE COORDINATOR'S DEFAULT (review of #927, F10, 2026-11-08; within the ruling, the operator's to
#: overrule): a guide CIQ last records more than four quarters before the page's price date stopped
#: long enough ago to be the company's practice now, its stop date stated; one inside four quarters
#: would be a change, which nothing here can evidence (see NO PATH EMITS TYPE 4).
FOUR_QUARTERS = timedelta(days=365)

#: Where the second read lives, named in a basis as a field path, never its long source_ref.
CIQ_GUIDES = "catalyst_path.guidance_bridge_rows"

#: The annual-table rows the survival items read. The filed tiebreak rewrites LTM cells AFTER the
#: assembly types the gaps (`assemble._settle_ltm_refusals`); a pin keeps its rows disjoint from
#: these, so the entries it would leave stale cannot exist (review of #927, F8).
ANNUAL_ROWS_READ: tuple[str, ...] = ("FCF ($M)", "CFO ($M)", "Capex ($M)", "EBITDA ($M)")


def _missing(s: Sourced[Any] | None) -> bool:
    return s is not None and s.status is not PRESENT


# ------------------------------------------------------------------------------- the two reads

def price_date(mech: MechanicalLayer) -> date | None:
    """The page's price date: the stock box's close, else the drawdown window's end."""
    si = mech.stock_info
    if si is not None and si.as_of is not None:
        return si.as_of
    end = mech.drawdown_cause.gap_window_end
    try:
        return date.fromisoformat(end) if end else None
    except ValueError:
        return None


@dataclass(frozen=True)
class _Ciq:
    """CIQ's Guidance sheet as (metric, date) pairs, and how far its export reaches."""

    rows: tuple[tuple[str, date], ...]
    reach: date

    def dated(self, family: Callable[[str], bool]) -> list[tuple[str, date]]:
        """The family's rows, newest first."""
        return sorted(((m, d) for m, d in self.rows if family(m)), key=lambda r: r[1],
                      reverse=True)


def _ciq(mech: MechanicalLayer, cut: date | None) -> _Ciq | None:
    """None when there is no second read: no sheet, no rows, a row whose date does not parse (an
    unreadable row could be the one that refutes a type, so none is skipped), or no row dated on
    or before the page's price date."""
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
    out = [(m, d) for m, d in out if within_cut(d, cut)]
    if not out:
        return None
    return _Ciq(tuple(out), max(d for _, d in out))


def releases_by_cut(releases: Sequence[ReleaseExtract], cut: date | None,
                    ) -> tuple[list[ReleaseExtract], list[ReleaseExtract]]:
    """THE RELEASE CUT (STATE row 57): (the releases filed on or before the page's price date,
    those filed after it), each in its given order. The gap test reads the first; the assembly
    keeps only the first in `primary_source.releases` and states the second
    (`mechanical._primary_source`). Raises on a release with no filing date while a cut applies:
    it cannot be placed on either side, and every release an assembly parses carries its 8-K's
    date, so only a page built before that field could hold one (`releases_read` reads it as
    no read)."""
    if cut is not None and any(r.filed is None for r in releases):
        raise ValueError("a release carries no filing date, so it cannot be cut at the page's "
                         "price date")
    kept: list[ReleaseExtract] = []
    after: list[ReleaseExtract] = []
    for r in releases:
        (kept if r.filed is None or within_cut(r.filed, cut) else after).append(r)
    return kept, after


def releases_read(mech: MechanicalLayer) -> list[ReleaseExtract] | None:
    """The releases the gap test reads: oldest first, filed on or before the page's price date.
    None when any carries no filing date (they cannot be ordered or cut)."""
    ps = mech.primary_source
    rels = list(ps.releases) if ps is not None else []
    if any(r.filed is None for r in rels):
        return None
    kept, _after = releases_by_cut(rels, price_date(mech))
    return sorted(kept, key=lambda r: (_filed(r), r.source_ref))


def _filed(r: ReleaseExtract) -> date:
    assert r.filed is not None  # `releases_read` returns only dated releases
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


def _any_item(g: GuidanceItem) -> bool:
    return True


@dataclass(frozen=True)
class _Guide:
    """One guide item: the release dates the field reads (``read_at``); the release items that
    would have filled it from those filings (``fills``, None where the field would then be
    PRESENT); the release items that show the company guides it at all (``guides``); CIQ's
    metrics for the same thing; and, where the field reads less than the company guides
    (``scope``), what it reads — a guide stated anywhere we read then makes the gap ours."""

    item: str
    fields: list[str]
    read_at: list[date]
    fills: Callable[[GuidanceItem], bool] | None
    guides: Callable[[GuidanceItem], bool]
    family: Callable[[str], bool]
    noun: str
    scope: str | None = None


def _guide_gap(g: _Guide, rels: list[ReleaseExtract] | None, ciq: _Ciq | None,
               cut: date | None) -> DisclosureGap:
    def gap(kind: GapType, basis: str, **kw: str) -> DisclosureGap:
        return DisclosureGap(item=g.item, fields=g.fields, type=kind, basis=basis, **kw)

    if rels is None:
        return gap(UNDETERMINED, "a release read carries no filing date, so the releases cannot "
                                 "be ordered")
    # (1a) the company guides it in what we read, and the field reads less than that
    if g.scope is not None:
        hit = next(((r, x) for r in reversed(rels) for x in r.guidance if g.guides(x)), None)
        if hit is not None:
            r, x = hit
            return gap(OUR, f"the release filed {_filed(r).isoformat()} states an {x.metric} "
                            f"guide for {x.period}; this field reads only {g.scope}",
                       source_ref=r.source_ref)
        if ciq is not None and rels:
            row = next(((m, c) for m, c in ciq.dated(g.family) if c >= _filed(rels[0]) - NEAR),
                       None)
            if row is not None:
                return gap(OUR, f"CIQ records {row[0]} guidance dated {row[1].isoformat()} "
                                f"({CIQ_GUIDES}); this field reads only {g.scope}")
    # newest first: the evidence a type cites is the latest that decides it
    at = {d: [r for r in rels if r.filed == d] for d in sorted(set(g.read_at), reverse=True)}
    # (1b) the release parser read it from the filing this field reads, and the field did not
    if g.fills is not None:
        for d, rs in at.items():
            got = next((r for r in rs if any(g.fills(x) for x in r.guidance)), None)
            if got is not None:
                return gap(OUR, f"the release parser read {g.noun} from the release filed "
                                f"{d.isoformat()}; this field did not take it",
                           source_ref=got.source_ref)
    # (1c) CIQ records one at a filing this field reads, from which the parser read no guide
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
    # (2) stated, then absent from every release read for a full quarter since, CIQ silent after
    # it: the shape a change would leave, and no evidence of one (module docstring, F5)
    if guided and ciq is not None:
        last = guided[-1]
        later = [r for r in rels if _filed(r) > _filed(last)]
        if (later and _filed(later[-1]) - _filed(last) >= FULL_QUARTER
                and ciq.reach >= _filed(later[-1]) - NEAR
                and not any(c > _filed(last) + NEAR for _, c in ciq.dated(g.family))):
            return gap(UNDETERMINED, f"the release filed {_filed(last).isoformat()} states "
                                     f"{g.noun}; none of the {len(later)} release(s) read since "
                                     f"does and {CIQ_GUIDES} records none after it, but the "
                                     "parser's blanks are mostly misses and CIQ is not shown to "
                                     "re-date a guide reaffirmed unchanged, so this is no evidence "
                                     "of a stop")
    # (3) no release read states one, and CIQ, reaching the newest, records none since the oldest
    if len(rels) >= 2 and not guided and ciq is not None:
        oldest, newest = _filed(rels[0]), _filed(rels[-1])
        if (ciq.reach >= newest - NEAR
                and not any(c >= oldest - NEAR for _, c in ciq.dated(g.family))):
            past = ciq.dated(g.family)
            span = (f"none of the {len(rels)} releases read ({oldest.isoformat()} to "
                    f"{newest.isoformat()}) states {g.noun}, and {CIQ_GUIDES}, which reaches "
                    f"{ciq.reach.isoformat()}, records none since {oldest.isoformat()}")
            if not past:
                return gap(PRACTICE, span)
            stop = past[0][1]
            if cut is None:
                return gap(UNDETERMINED, f"{span}; CIQ's last such guide is dated "
                                         f"{stop.isoformat()}, and the page states no price "
                                         "date to age that stop by")
            if cut - stop <= FOUR_QUARTERS:
                return gap(UNDETERMINED, f"{span}; CIQ's last such guide is dated "
                                         f"{stop.isoformat()}, within four quarters of the "
                                         f"page's price date ({cut.isoformat()}): a stop that "
                                         "recent would be a change, and one read cannot show it")
            return gap(PRACTICE, f"{span}; CIQ's last such guide is dated {stop.isoformat()}, "
                                 "more than four quarters before the page's price date "
                                 f"({cut.isoformat()})")
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
    lacks is a read we did not make. ``segment_profit`` None is a single-segment instance, no CIK
    or no annual report alike, and UNKNOWN is any failed read, so neither is stated as more."""
    sp, se = c.segment_profit, c.segment_ebitda
    if sp is not None and sp.status is PRESENT:
        if not _missing(se) or sp.value is None:
            return None
        # ONE read (F3): the instance read tries its measures in a fixed order, so "operating
        # income" may only be the tag tried first; nothing read says no segment EBITDA exists
        return DisclosureGap(
            item="segment EBITDA", fields=["concentration.segment_ebitda"], type=UNDETERMINED,
            basis=f"the 10-K's segments carry the filer's {sp.value.measure_kind} "
                  "(concentration.segment_profit); one read cannot show it discloses no segment "
                  "EBITDA")
    fields = [f for f, s in (("concentration.segment_profit", sp),
                             ("concentration.segment_ebitda", se)) if _missing(s)]
    if se.status is PRESENT:
        if not fields:
            return None
        return DisclosureGap(
            item="segment profit from the 10-K", fields=fields, type=OUR,
            basis="the 10-K segment-profit read is UNKNOWN; CIQ's segment EBITDA "
                  "(concentration.segment_ebitda) is on the page")
    if not fields:
        return None
    if segment_count is None:
        return DisclosureGap(item="segment profit by segment", fields=fields, type=UNDETERMINED,
                             basis="CIQ's segment revenue roster cannot be read, so the segment "
                                   "count is not known")
    tenk = ("the 10-K segment-profit read is UNKNOWN (concentration.segment_profit)"
            if sp is not None else "the page states no segment profit from the 10-K")
    if segment_count == 1:
        if sp is not None:
            return DisclosureGap(item="segment profit by segment", fields=fields,
                                 type=UNDETERMINED,
                                 basis=f"CIQ's Segments sheet reads one segment, while {tenk}")
        return DisclosureGap(item="segment profit by segment", fields=fields, type=NA,
                             basis=f"CIQ's Segments sheet reads one segment, and {tenk}; there "
                                   "is no breakout to give")
    return DisclosureGap(item="segment profit by segment", fields=fields, type=OUR,
                         basis=f"CIQ's Segments sheet splits revenue across {segment_count} "
                               "segments, and a filer reporting more than one discloses a profit "
                               f"measure for each; {tenk}")


def _windows(mech: MechanicalLayer) -> list[tuple[str, list[FilingRef], Sourced[str],
                                                  Sourced[str]]]:
    dc = mech.drawdown_cause
    out = [("drawdown_cause", dc.filings, dc.revised_guidance, dc.shape)]
    if dc.anchor is not None:
        a = dc.anchor.at_anchor
        out.append(("drawdown_cause.anchor.at_anchor", a.filings, a.revised_guidance, a.shape))
        if (s := dc.anchor.since) is not None:
            out.append(("drawdown_cause.anchor.since", s.filings, s.revised_guidance, s.shape))
    return out


def _filing_dates(filings: Sequence[FilingRef]) -> list[date] | None:
    try:
        return sorted({date.fromisoformat(f.filing_date) for f in filings})
    except ValueError:
        return None


_OUTLOOK = "the outlook a gap-down's 8-K furnished"


def _drawdown_gaps(mech: MechanicalLayer, rels: list[ReleaseExtract] | None,
                   ciq: _Ciq | None, cut: date | None) -> list[DisclosureGap]:
    out: list[DisclosureGap] = []
    empty: list[str] = []   # windows READ and holding no gap-down 8-K — ONE entry for all of them
    for prefix, filings, guidance, shape in _windows(mech):
        if not _missing(guidance):
            continue
        field = f"{prefix}.revised_guidance"
        if not filings and shape.status is PRESENT:
            empty.append(prefix)
            continue
        if not filings:
            # F1: `filings` is also [] when the filing index could not be read, there was no CIK,
            # or the window itself was not read — the shape is then UNKNOWN, saying which
            out.append(DisclosureGap(
                item=_OUTLOOK, fields=[field], type=OUR,
                basis=f"the window's read is UNKNOWN ({prefix}.shape): its gap-downs' 8-Ks, or "
                      "the window itself, were not read"))
            continue
        dates = _filing_dates(filings)
        if dates is None:
            out.append(DisclosureGap(item=_OUTLOOK, fields=[field], type=UNDETERMINED,
                                     basis=f"a filing date in {prefix}.filings does not parse"))
            continue
        out.append(_guide_gap(_Guide(item=_OUTLOOK, fields=[field], read_at=dates,
                                     fills=_any_item, guides=_any_item, family=_ciq_any,
                                     noun="a guide"), rels, ciq, cut))
    if empty:
        where = ", ".join(f"{p}.filings" for p in empty)
        out.insert(0, DisclosureGap(
            item=_OUTLOOK, fields=[f"{p}.revised_guidance" for p in empty], type=NA,
            basis=f"no gap-down 8-K is in the window{'s' if len(empty) > 1 else ''} ({where} "
                  "empty, each window read), and this reads only the outlook such an 8-K "
                  "furnishes"))
    out += _adjusted_ebitda_gap(mech, rels, ciq, cut)
    return out


def _adjusted_ebitda_gap(mech: MechanicalLayer, rels: list[ReleaseExtract] | None,
                         ciq: _Ciq | None, cut: date | None) -> list[DisclosureGap]:
    """The two company-adjusted figures (F2). They read ONLY the adjusted EBITDA in a gap-down
    8-K's outlook (`mechanical._adjusted_facts`), so where the company guides adjusted EBITDA in
    anything we read, their absence is our scope, never the company's."""
    v, q = mech.valuation, mech.quality
    fields = [f for f, s in (("valuation.ev_ebitda_adjusted_fwd", v.ev_ebitda_adjusted_fwd),
                             ("quality.net_debt_to_ebitda_adjusted",
                              q.net_debt_to_ebitda_adjusted)) if _missing(s)]
    if not fields:
        return []
    item = "a company adjusted-EBITDA guide"
    dates = _filing_dates(mech.drawdown_cause.filings)
    if dates is None:
        return [DisclosureGap(item=item, fields=fields, type=UNDETERMINED,
                              basis="a filing date in drawdown_cause.filings does not parse")]
    return [_guide_gap(_Guide(item=item, fields=fields, read_at=dates, fills=None,
                              guides=_adj_ebitda, family=_ciq_ebitda,
                              noun="an adjusted-EBITDA guide", scope=_OUTLOOK), rels, ciq, cut)]


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
    assert label in ANNUAL_ROWS_READ, label   # the rows the F8 pin keeps the tiebreak away from
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
        # NAMED BY ITS FIELD (fix 3b, #930): the survival line no longer carries an FCF-sign leg,
        # so "the FCF sign behind the survival line's runway leg" described a line that is gone.
        # The frozen M-GAP gold keeps the old words (`vinci/evals/synthesis_gap_types.json`).
        out.append(DisclosureGap(
            item="the FCF sign (quality.fcf_sign)", fields=["quality.fcf_sign"],
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
    cut = price_date(mech)
    rels, ciq = releases_read(mech), _ciq(mech, cut)
    out: list[DisclosureGap] = []
    if (seg := _segment_gap(mech.concentration, segment_count)) is not None:
        out.append(seg)
    out += _drawdown_gaps(mech, rels, ciq, cut)
    newest = [_filed(rels[-1])] if rels else []
    if _missing(mech.valuation.adjusted_eps):
        out.append(_guide_gap(_Guide(
            item="an annual adjusted-EPS guide in the newest release",
            fields=["valuation.adjusted_eps"], read_at=newest, fills=None, guides=_adj_eps,
            family=_ciq_eps, noun="an adjusted-EPS guide"), rels, ciq, cut))
    ps = mech.primary_source
    if ps is not None and _missing(ps.current_guide):
        out.append(_guide_gap(_Guide(
            item="a current guide", fields=["primary_source.current_guide"],
            read_at=sorted({_filed(r) for r in rels}) if rels else [], fills=None,
            guides=_any_item, family=_ciq_any, noun="a guide"), rels, ciq, cut))
    out += _survival_gaps(mech)
    return out
