"""THE RELEASE SOURCE for the data-quality scorecard (`vinci.quality.core`): "are the figures the
pages read out of 8-K text credible?" — the earnings releases' actuals and guides (the deterministic
parser, `vinci.edgar.release_parse`) and the rate components quoted from credit agreements.

WHY (2026-10-27). The parser had produced wrong numbers that reached the card a reader sees: VRRM's
"$380 million to $385 million" sat there as an adjusted EBITDA of $38.0M for 104 days
(`docs/records/2026-10-22-release-actuals-at-their-scale.md`), and nCino's and Uber's quarterly
guides still sit on their pages under annual labels. Its results were checked where they were used
— CIQ's revenue guide against the release (`ciq.guide_vs_release`) — and never on their own.

WHAT IT READS. The committed pages (`data/dossiers/*/dossier.json`): each page's stored releases
(`mechanical.primary_source.releases`) and covenant rows. Beside them, each filer's XBRL
`companyfacts` from the SEC cache (`data/cache/sec`), read from the cache ONLY — this source never
fetches, so what it judges is what the cache holds, and the boundary names when that was fetched. A
page whose facts the cache lacks runs the quote check alone; its XBRL checks are not run, by name.

``independent`` here means another DOCUMENT from the same filer: the 10-Q/10-K's XBRL against the
8-K release, or EDGAR's own filing date. Same filer, so it cannot catch a filer that misstates its
own numbers twice — it catches this repo reading them wrong. ``internal`` means the stored figure
against its OWN stored quote.

STRUCTURED VALUES ONLY: every figure tested is the page's stored number (`value`, `low`, `high`,
`amount`, `margin_pct`, …), never a rendered string. A quote is read for the figures IT states
through the parser's own reader (`release_parse.quoted_figures`).

COUNTS AND STATUSES ONLY. The repo is public: no figure, quote or period reaches the snapshot.
"""
from __future__ import annotations

import functools
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from vinci.dossier.mechanical import _period_key
from vinci.dossier.statement_recon import DIFFERENT_FLOOR, DIFFERENT_SHARE
from vinci.edgar.concepts import CONCEPT_ALIASES, ConceptPoint, points_for_tag
from vinci.edgar.primary_source import period_scope
from vinci.edgar.release_parse import VERBATIM_CAP, quoted_figures
from vinci.netcache import CachedHttp
from vinci.quality.core import (
    CONFIRMED,
    DIFFERS_STATED,
    DIFFERS_UNEXPLAINED,
    INDEPENDENT,
    INTERNAL,
    SINGLE_SOURCE,
    UNCHECKED,
    Check,
    Corpus,
    Family,
    ItemResult,
    Source,
)

#: A guide's midpoint against the same-scope period a year earlier, either way up. Face validity: a
#: quarterly guide filed as a year reads ~0.25 of the year, and billions read as millions ~0.001; a
#: real guide inside a factor of two covers a business doubling or halving. A name growing faster
#: than that differs here for a true reason — the population line says so.
SCALE_BAND = 2.0
#: A release states a gross margin to one decimal; the XBRL ratio is exact. A tenth of a point is
#: the rounding of both a margin and the revenue under it.
MARGIN_TOL_PTS = 0.1
#: Two figures are the same figure — the parser multiplies a stated number by its scale.
_SAME = 1e-6
_SAME_END_DAYS = 7
_QUARTER_DAYS = (80, 100)
#: The covenant note the extractor writes (`covenant_extract._extract_from_exhibit`, `f"verbatim:
#: “{quote}”"`) — the quote, as stored.
_NOTE_OPEN, _NOTE_CLOSE = "verbatim: “", "”"
#: The structured rate components a covenant row carries, and the unit each is stated in.
_RATE_UNITS = {"margin_pct": "%", "margin_bps": "bps", "floor_pct": "%", "pik_pct": "%"}
_REVENUE_GUIDES = frozenset({"revenue", "net sales", "total revenue", "total revenues"})
READS = "data/dossiers/*/dossier.json + data/cache/sec companyfacts (cache only)"


@dataclass(frozen=True)
class Page:
    """One committed page as this source reads it: its stored releases and covenant rows, and the
    filer's XBRL facts — or why there are none."""

    ticker: str
    releases: list[dict[str, Any]]
    covenants: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] | str | None = None

    @functools.cached_property
    def calendar(self) -> dict[tuple[str, int], date]:
        """The filer's fiscal calendar, built ONCE per page for every check that places a label."""
        return _calendar(self.facts) if isinstance(self.facts, dict) else {}


# --- the filer's XBRL: its fiscal calendar and its figures ---------------------------------------


def _calendar(facts: dict[str, Any]) -> dict[tuple[str, int], date]:
    """(fiscal period, fiscal year) → the period's end, as each 10-Q/10-K states its OWN period: the
    latest period end it carries, under the fiscal year and period its XBRL names. A fourth quarter
    ends with its fiscal year, so ``("FY", y)`` serves both."""
    by_acc: dict[str, tuple[str, int, date, date]] = {}
    for tag in (*CONCEPT_ALIASES["revenue"], *CONCEPT_ALIASES["net_income"],
                *CONCEPT_ALIASES["eps_diluted"]):
        for p in points_for_tag(facts, tag):
            form = (p.form or "").upper()
            if (p.period_start is None or not p.accession or p.fy is None or not p.fp
                    or not form.startswith(("10-Q", "10-K"))):
                continue
            seen = by_acc.get(p.accession)
            if seen is None or p.period_end > seen[2]:
                by_acc[p.accession] = (p.fp.upper(), int(p.fy), p.period_end, p.filed)
    cal: dict[tuple[str, int], tuple[date, date]] = {}
    for fp, fy, end, filed in by_acc.values():
        if fp in ("Q1", "Q2", "Q3", "FY") and ((fp, fy) not in cal or filed < cal[(fp, fy)][1]):
            cal[(fp, fy)] = (end, filed)            # the ORIGINAL filing names the period
    return {k: v[0] for k, v in cal.items()}


def _label(period: str) -> tuple[str, int | None] | None:
    """A stored period label → (fiscal period, year or None), through the page's own helpers
    (`period_scope`, `mechanical._period_key`); None when the label decides no quarter or year."""
    scope = period_scope(period)
    year, q = _period_key(period)
    if scope == "quarter" and q:
        return ("FY" if q == 4 else f"Q{q}"), (year or None)
    if scope == "annual":
        return "FY", (year or None)
    return None


def _period_end(cal: dict[tuple[str, int], date], fp: str, year: int) -> date | None:
    """Where the filer's calendar places (fp, year): reported, or a year after the same period of
    the year before (a forward period no filing has reported yet)."""
    if (fp, year) in cal:
        return cal[(fp, year)]
    prior = cal.get((fp, year - 1))
    return prior + timedelta(days=364) if prior is not None else None


def _days(p: ConceptPoint) -> int:
    return (p.period_end - p.period_start).days if p.period_start is not None else -1


def _near(a: date, b: date) -> bool:
    return abs((a - b).days) <= _SAME_END_DAYS


def _figures(pts: list[ConceptPoint], start: date, end: date) -> list[tuple[date, float]]:
    """Every figure the filer's filings give [start, end]: (filed, $M) — the discrete fact, or a
    longer one from the same start less the shorter one before it (a 10-Q tags year-to-date, a
    fourth quarter is its year less nine months)."""
    span = (end - start).days
    exact = [(p.filed, p.value / 1e6) for p in pts
             if p.period_start is not None and _near(p.period_end, end)
             and abs(_days(p) - span) <= 10]
    if exact:
        return exact
    out = []
    for p in pts:
        if p.period_start is None or not _near(p.period_end, end) or _days(p) <= span + 10:
            continue
        for q in pts:
            if (q.period_start == p.period_start and q.filed <= p.filed
                    and _near(q.period_end, start - timedelta(days=1))):
                out.append((p.filed, (p.value - q.value) / 1e6))
    return out


def _by_tag(facts: dict[str, Any], tags: tuple[str, ...] | list[str], start: date,
            end: date) -> list[list[tuple[date, float]]]:
    """The period's figures on each alias that reports it, aliases in their order of meaning."""
    out = []
    for tag in tags:
        figs = _figures([p for p in points_for_tag(facts, tag) if p.unit == "USD"], start, end)
        if figs:
            out.append(figs)
    return out


def _governing_filed(figs: list[tuple[date, float]], filed: date | None) -> tuple[date, float]:
    """(filed, figure) the release's own filing period gives: the first filed on or after the
    release (its 10-Q/10-K, or a later recast), else the latest before."""
    after = sorted(f for f in figs if filed is not None and f[0] >= filed)
    return after[0] if after else max(figs)


def _governing(figs: list[tuple[date, float]], filed: date | None) -> float:
    return _governing_filed(figs, filed)[1]


def _differs(release: float, filing: float, half_unit: float) -> bool:
    """`statement_recon`'s rule for a copied figure, widened to the release's own rounding."""
    gap = abs(release - filing)
    return (gap > max(DIFFERENT_SHARE * abs(filing), half_unit + _SAME)
            and gap >= DIFFERENT_FLOOR)


def _filed(r: dict[str, Any]) -> date | None:
    try:
        return date.fromisoformat(str(r.get("filed")))
    except ValueError:
        return None


_NO_FACTS = "no XBRL facts for the filer in the SEC cache"


def _facts(page: Page) -> dict[str, Any] | ItemResult:
    if isinstance(page.facts, dict):
        return page.facts
    return ItemResult(not_run=page.facts or _NO_FACTS)


def _place(cal: dict[tuple[str, int], date], period: str,
           ) -> tuple[str, int, date, date] | None:
    """A stored label → (fp, year, first day, last day) in the filer's calendar, or None."""
    lab = _label(period)
    if lab is None or lab[1] is None:
        return None
    fp, year = lab[0], lab[1]
    end = _period_end(cal, fp, year)
    if end is None:
        return None
    if period_scope(period) != "quarter":
        return fp, year, end - timedelta(days=364), end
    before = {"Q1": ("FY", year - 1), "Q2": ("Q1", year), "Q3": ("Q2", year),
              "FY": ("Q3", year)}[fp]                     # a fourth quarter follows the third
    prev = _period_end(cal, *before)
    start = prev + timedelta(days=1) if prev else end - timedelta(days=91)
    # A CALENDAR THAT DOES NOT TILE IS NO CALENDAR: fuboTV moved its fiscal year to September, so
    # its fiscal 2025 ends 2025-12-31 and its first quarter of 2026 ends the same day — a quarter
    # of zero days, which read a revenue of $0. A quarter is 80–100 days or it is not placed.
    if not _QUARTER_DAYS[0] <= (end - start).days + 1 <= _QUARTER_DAYS[1]:
        return None
    return fp, year, start, end


# --- the checks ---------------------------------------------------------------------------------


def _quote_value(value: float, units: tuple[str, ...], quote: str) -> float | None:
    """The half-unit of the figure in ``quote`` that IS ``value`` in one of ``units``, or None."""
    for f in quoted_figures(quote):
        if f.unit in units and abs(f.value - abs(value)) <= _SAME * max(1.0, abs(value)):
            return f.half_unit
    return None


def _actual_unit(metric: str) -> str:
    return "$" if "eps" in metric else "%" if "margin" in metric else "$M"


def _revenue_vs_xbrl(page: Page) -> ItemResult:
    rows = [(r, x) for r in page.releases for x in r.get("reconciliation") or []
            if x.get("metric") == "revenue"]
    if not rows:
        return ItemResult(not_applicable="no revenue actual on the page")
    facts = _facts(page)
    if isinstance(facts, ItemResult):
        return facts
    cal = page.calendar
    c: Counter[str] = Counter()
    for r, x in rows:
        placed = _place(cal, str(x.get("period") or ""))
        if placed is None:
            c[UNCHECKED] += 1
            continue
        _fp, _y, start, end = placed
        tagged = _by_tag(facts, CONCEPT_ALIASES["revenue"], start, end)
        if not tagged:
            c[UNCHECKED] += 1
            continue
        gov = _governing(tagged[0], _filed(r))
        others = [v for figs in tagged for _f, v in figs]
        value = float(x["value"])
        half = _quote_value(value, ("$M",), str(x.get("verbatim") or "")) or 0.0
        if not _differs(value, gov, half):
            c[CONFIRMED] += 1
        elif any(not _differs(value, o, half) for o in others):
            c[DIFFERS_STATED] += 1
        else:
            c[DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


def _gross_margin_vs_xbrl(page: Page) -> ItemResult:
    rows = [(r, x) for r in page.releases for x in r.get("reconciliation") or []
            if x.get("metric") == "gross margin"]
    if not rows:
        return ItemResult(not_applicable="no gross-margin actual on the page")
    facts = _facts(page)
    if isinstance(facts, ItemResult):
        return facts
    cal = page.calendar
    c: Counter[str] = Counter()
    for r, x in rows:
        placed = _place(cal, str(x.get("period") or ""))
        if placed is None:
            c[UNCHECKED] += 1
            continue
        _fp, _y, start, end = placed
        gp = _by_tag(facts, ("GrossProfit",), start, end)
        rev = _by_tag(facts, CONCEPT_ALIASES["revenue"], start, end)
        # ONE FILING'S RATIO: gross profit over the revenue THAT filing states for the period —
        # never one filing's gross profit over another's recast revenue
        gross = _governing_filed(gp[0], _filed(r)) if gp else None
        base = next((v for f, v in rev[0] if gross and f == gross[0]), None) if rev else None
        if gross is None or not base:
            c[UNCHECKED] += 1
            continue
        gap = abs(float(x["value"]) - 100.0 * gross[1] / base)
        c[CONFIRMED if gap <= MARGIN_TOL_PTS + _SAME else DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


def _level_guides(page: Page) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(r, g) for r in page.releases for g in r.get("guidance") or []
            if not g.get("qualitative") and g.get("low") is not None
            and g.get("high") is not None]


def _guide_scale_vs_xbrl(page: Page) -> ItemResult:
    guides = [(r, g) for r, g in _level_guides(page)
              if g.get("metric") in _REVENUE_GUIDES and g.get("unit") == "$M"
              and g.get("basis", "level") == "level"]
    if not guides:
        return ItemResult(not_applicable="no revenue level guide on the page")
    facts = _facts(page)
    if isinstance(facts, ItemResult):
        return facts
    cal = page.calendar
    c: Counter[str] = Counter()
    for r, g in guides:
        filed, lab = _filed(r), _label(str(g.get("period") or ""))
        if filed is None or lab is None:
            c[UNCHECKED] += 1
            continue
        # the SAME scope a year earlier: the latest such period ending before the filing, as filed
        # by then — a quarterly guide against a quarter, an annual one against a fiscal year
        fp, quarterly = lab[0], period_scope(str(g.get("period"))) == "quarter"
        before = sorted((e, y) for (p, y), e in cal.items() if p == fp and e < filed)
        placed = (_place(cal, f"Q{4 if fp == 'FY' else fp[1]} {before[-1][1]}" if quarterly
                         else f"FY {before[-1][1]}") if before else None)
        tagged = _by_tag(facts, CONCEPT_ALIASES["revenue"], placed[2], placed[3]) if placed else []
        known = [f for f in tagged[0] if f[0] <= filed] if tagged else []
        base = max(known)[1] if known else None
        if not base or base <= 0:
            c[UNCHECKED] += 1
            continue
        ratio = (float(g["low"]) + float(g["high"])) / 2.0 / base
        c[CONFIRMED if 1.0 / SCALE_BAND <= ratio <= SCALE_BAND else DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


def _guide_period_forward(page: Page) -> ItemResult:
    guides = [(r, g) for r in page.releases for g in r.get("guidance") or []
              if not g.get("qualitative")]
    if not guides:
        return ItemResult(not_applicable="no numeric guide on the page")
    facts = _facts(page)
    if isinstance(facts, ItemResult):
        return facts
    cal = page.calendar
    c: Counter[str] = Counter()
    for r, g in guides:
        filed, lab = _filed(r), _label(str(g.get("period") or ""))
        if filed is None or lab is None or lab[1] is None:
            c[UNCHECKED] += 1            # no year read (`next-fy`, "Q2", "FY"): nothing to place
            continue
        end = _period_end(cal, lab[0], lab[1])
        if end is None:
            c[UNCHECKED] += 1
        else:
            c[CONFIRMED if end > filed else DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


def _stored_figures(page: Page) -> list[tuple[float, tuple[str, ...], str, bool]]:
    """(value, the units it may be stated in, its quote, whether the quote is a release's — cut at
    `VERBATIM_CAP`) for every structured figure the page stores beside a quote."""
    out: list[tuple[float, tuple[str, ...], str, bool]] = []
    for r in page.releases:
        for x in r.get("reconciliation") or []:
            out.append((float(x["value"]), (_actual_unit(str(x.get("metric"))),),
                        str(x.get("verbatim") or ""), True))
        for g in r.get("guidance") or []:
            if g.get("qualitative"):
                continue
            unit = {"$/sh": "$"}.get(str(g.get("unit")), str(g.get("unit")))
            for k in ("low", "high"):
                if g.get(k) is not None:
                    out.append((float(g[k]), (unit,), str(g.get("verbatim") or ""), True))
        for o in r.get("one_offs") or []:
            out.append((float(o["amount"]), ("$M",), str(o.get("verbatim") or ""), True))
        for e in r.get("event_impacts") or []:
            # an impact stated per share is stored unscaled in the same field (#778)
            for k in ("low", "high"):
                if e.get(k) is not None:
                    out.append((float(e[k]), ("$M", "$"), str(e.get("verbatim") or ""), True))
    for row in page.covenants:
        note = str((row.get("value") or {}).get("note") or "")
        if not (note.startswith(_NOTE_OPEN) and note.endswith(_NOTE_CLOSE)):
            continue
        quote = note[len(_NOTE_OPEN):-len(_NOTE_CLOSE)]
        for k, unit in _RATE_UNITS.items():
            if row.get(k) is not None:
                out.append((float(row[k]), (unit,), quote, False))
    return out


def _figure_in_own_quote(page: Page) -> ItemResult:
    figs = _stored_figures(page)
    if not figs:
        return ItemResult(not_applicable="no figure stored beside a quote on the page")
    c: Counter[str] = Counter()
    for value, units, quote, release in figs:
        if _quote_value(value, units, quote) is not None:
            c[CONFIRMED] += 1
        elif release and len(quote) >= VERBATIM_CAP - 1:
            c[DIFFERS_STATED] += 1       # the quote is cut at its cap before the figure
        else:
            c[DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


_XBRL_SECOND = ("EDGAR XBRL from the filer's 10-Q/10-K (`companyfacts`, the SEC cache) for the "
                "fiscal period the row's label names in the filer's own calendar")
CHECKS: tuple[Check, ...] = (
    Check("revenue_vs_xbrl", "A release's reported revenue vs the same fiscal period in XBRL",
          "8-K EX-99.1 revenue actual (primary_source.releases[].reconciliation, metric revenue)",
          f"{_XBRL_SECOND}: the first revenue alias reporting it (CONCEPT_ALIASES['revenue']) — "
          "the discrete fact, else year-to-date less the prior year-to-date (a fourth quarter is "
          "its year less nine months); the filing on or after the release governs",
          INDEPENDENT, "row",
          f"differs beyond {DIFFERENT_SHARE:.1%} of the XBRL figure AND by at least "
          f"${DIFFERENT_FLOOR:g}M (statement_recon.DIFFERENT_SHARE / DIFFERENT_FLOOR), the share "
          "widened to half a unit of the release's own stated figure ('$1.5 billion' ±$50M)",
          "every revenue actual on a committed page whose filer's facts are cached; a label the "
          "filer's calendar cannot place, or a period no 10-Q/10-K has reported yet, is unchecked",
          "another revenue alias or another filing carries the release's figure for the period "
          "(a recast)", None,
          ("wrong_cell", "wrong_unit", "wrong_period", "different_definition"),
          _revenue_vs_xbrl),
    Check("gross_margin_vs_xbrl", "A release's gross margin vs XBRL gross profit ÷ revenue",
          "8-K EX-99.1 gross-margin actual, percent (reconciliation, metric gross margin)",
          f"{_XBRL_SECOND}: GrossProfit ÷ revenue, both on the governing filing", INDEPENDENT,
          "row", f"within {MARGIN_TOL_PTS:g} percentage point (release.MARGIN_TOL_PTS)",
          "every gross-margin actual on a committed page; a filer that tags no GrossProfit is "
          "unchecked — and a release's 'gross margin' can be its own, non-GAAP measure",
          None, None, ("wrong_cell", "wrong_period", "different_definition"),
          _gross_margin_vs_xbrl),
    Check("guide_scale_vs_xbrl",
          "A revenue guide's level vs the filer's revenue for the same scope a year earlier",
          "8-K EX-99.1 revenue level guide ($M), its midpoint, at the scope its label states "
          "(period_scope: a quarter, or annual — `next-fy` reads annual)",
          "EDGAR XBRL revenue for the latest period of that scope (the same quarter, or the fiscal "
          "year) ending before the release was filed, as filed by then", INDEPENDENT, "guide",
          f"the midpoint within {SCALE_BAND:g}x either way (release.SCALE_BAND): a quarterly "
          "guide filed as a year reads ~0.25 and billions read as millions ~0.001",
          "every revenue level guide on a committed page; a name more than doubling or halving "
          "its revenue differs here for a true reason", None, None,
          ("wrong_unit", "wrong_period"), _guide_scale_vs_xbrl),
    Check("guide_period_forward", "A guide's labelled period ends after its release was filed",
          "every numeric guide's period label (primary_source.releases[].guidance)",
          "EDGAR: the release's filing date, and where the filer's own 10-Q/10-K calendar places "
          "the label (a period not yet reported a year after the same period before)",
          INDEPENDENT, "guide",
          "exact: the labelled period ends after the filing date — a guide wearing a period the "
          "filer had already closed differs",
          "every numeric guide on a committed page; a label with no year (`next-fy`, 'Q2', 'FY') "
          "or one the calendar cannot place is unchecked", None, None, ("wrong_period",),
          _guide_period_forward),
    Check("figure_in_own_quote", "Each stored figure is stated in its own quote, at its scale",
          "every structured figure stored beside a quote: release actuals (value), guide bounds "
          "(low, high), one-offs (amount), event impacts (low, high), and covenant rate "
          "components (margin_pct, margin_bps, floor_pct, pik_pct)",
          "the figure's own stored quote (`verbatim`; a covenant row's note), read through "
          "release_parse.quoted_figures", INTERNAL, "figure",
          "exact at the quote's stated scale: the value is one figure the quote states — $M where "
          "the quote states a scale word, a bare dollar figure per share, %, basis points (a "
          "range's unit-less low side takes the high side's unit; 'zero' is 0). A quote PROVES "
          "presence (vinci.verbatim); this asks whether it SUPPORTS the value",
          "every committed page", f"the release quote is cut at its {VERBATIM_CAP}-character cap "
          "(release_parse._verbatim) before the figure", None, ("wrong_cell", "wrong_unit"),
          _figure_in_own_quote),
)
CHECK_IDS = tuple(c.id for c in CHECKS)


# --- the coverage map ---------------------------------------------------------------------------

FAMILIES: tuple[Family, ...] = (
    Family("release.revenue", "8-K EX-99.1", ("8-K <accession> EX-99.1",),
           "the revenue a release reports, per period",
           checks=("revenue_vs_xbrl", "figure_in_own_quote")),
    Family("release.gross_margin", "8-K EX-99.1", ("8-K <accession> EX-99.1",),
           "the gross margin a release reports", checks=("gross_margin_vs_xbrl",
                                                          "figure_in_own_quote")),
    Family("release.non_gaap_actuals", "8-K EX-99.1", ("8-K <accession> EX-99.1",),
           "adjusted EBITDA, adjusted EPS, adjusted net and operating income",
           checks=("figure_in_own_quote",), fallback=SINGLE_SOURCE,
           note="internal on the quote alone: a non-GAAP figure is the filer's own and no XBRL "
                "tag carries it; CIQ's EBITDA is CIQ's normalisation, not the filer's. GAAP "
                "DILUTED EPS is not read as an actual by the parser (no row on any page), so the "
                "XBRL EPS figure has nothing to be set against"),
    Family("release.guidance", "8-K EX-99.1", ("8-K <accession> EX-99.1",),
           "guidance ranges: level and change, every metric",
           checks=("guide_scale_vs_xbrl", "guide_period_forward", "figure_in_own_quote"),
           unscored=("ciq.guide_vs_release — CIQ's revenue guide against the release's, scored "
                     "in the ciq source",),
           note="the level check runs on revenue guides only; a guide of another metric has its "
                "period and its quote checked, not its size"),
    Family("release.one_offs_and_impacts", "8-K EX-99.1", ("8-K <accession> EX-99.1",),
           "one-off charges and event-impact ranges", checks=("figure_in_own_quote",),
           fallback=SINGLE_SOURCE),
    Family("filings.covenant_rates", "8-K EX-10.x", ("8-K <accession> · <exhibit>",),
           "a credit agreement's rate components (margin, floor, PIK)",
           checks=("figure_in_own_quote",),
           note="internal on the quote alone; the quote's presence in the exhibit is checked at "
                "assembly (vinci.verbatim). CIQ's capital-structure panel carries coupons and is "
                "not set against these"),
)


# --- what it reads ------------------------------------------------------------------------------

_COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def _cache(root: Path) -> CachedHttp:
    """The SEC cache, read only: every call below is made on a URL the cache already holds, so no
    request is sent and no user agent is needed."""
    return CachedHttp(cache_dir=root / "data" / "cache", user_agent="vinci data-quality (cache)",
                      min_interval_sec=0.0, namespace="sec")


def read(root: Path, *, facts: Any = None) -> Corpus:
    """Every committed page under ``root/data/dossiers`` with the filer's cached facts. ``facts``
    (ticker, CIK → dict | reason) replaces the cache read — the tests' seam."""
    ddir = root / "data" / "dossiers"
    http = _cache(root) if facts is None else None
    items: dict[str, Page] = {}
    h = hashlib.sha256()
    fetched: list[float] = []
    for f in sorted(ddir.glob("*/dossier.json")) if ddir.is_dir() else []:
        t, raw = f.parent.name.upper(), f.read_bytes()
        if t in items:
            raise ValueError(f"two dossier folders for {t} under {ddir}")
        page = json.loads(raw)
        h.update(t.encode() + b"\n" + hashlib.sha256(raw).hexdigest().encode() + b"\n")
        mech = page.get("mechanical") or {}
        rels = (mech.get("primary_source") or {}).get("releases") or []
        cs = mech.get("capital_structure") or {}
        cov = cs.get("covenant_term_rows") or {}
        rows = [r for r in (cov.get("value") or []) if cov.get("status") == "present"
                and (r.get("value") or {}).get("status") == "present"]
        cik = str(page.get("cik") or "")
        fx: dict[str, Any] | str
        if facts is not None:
            fx = facts(t, cik)
        elif not cik:
            fx = "the page names no CIK"
        else:
            url = _COMPANYFACTS.format(cik=cik.zfill(10))
            assert http is not None
            at = http.fetched_at(url)
            if at is None:
                fx = f"{_NO_FACTS} (CIK {cik.zfill(10)})"
            else:
                body = http.get_text(url, ttl_seconds=None)
                fx = json.loads(body)
                fetched.append(at)
                h.update(hashlib.sha256(body.encode()).hexdigest().encode() + b"\n")
        if isinstance(fx, str):
            h.update(fx.encode() + b"\n")
        items[t] = Page(t, rels, rows, fx)
    when = (f"; companyfacts fetched {date.fromtimestamp(min(fetched))} → "
            f"{date.fromtimestamp(max(fetched))}" if fetched else "")
    n_rel = sum(len(p.releases) for p in items.values())
    return Corpus(items=items, reads=f"{READS}: {n_rel} releases{when}", item_noun="page",
                  sha256=h.hexdigest(), tracked=("data/dossiers",))


def load(root: Path) -> Corpus:
    return read(root)


SOURCE = Source(
    id="release", title="8-K text (release parser, quoted terms)",
    reads_note="reads the committed pages and the SEC cache, never the network; the sha256 names "
               "exactly what was read",
    load=load, checks=CHECKS, families=FAMILIES)
