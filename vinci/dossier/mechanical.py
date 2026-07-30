"""The MECHANICAL layer — deterministic, no LLM, every field a source-bound ``{value, source_ref}``.

Facts come from the screen's data-record (already EDGAR/EOD-bound), fresh EDGAR pulls (the 8-K
behind each gap-down; the share-count trend), EOD bars (the name's and IWM's window returns), the
graph (the exposed cross-section, a research INPUT — never a predictor), and the manual CIQ bundle.
Anything not found is UNKNOWN (looked for, absent) or MISSING (whole source absent, e.g. CIQ
un-pulled) — never
a fabricated number. This layer is the ONLY input the synthesis LLM is later given.
"""

from __future__ import annotations

import re
import statistics
import time
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any, TypeVar

from vinci.config import get_config
from vinci.dossier import ciq_sheets, edgar_fundamentals
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import (
    CapitalInstrument,
    CapitalStructure,
    CatalystCalendar,
    CatalystPath,
    CatalystRow,
    CohortMember,
    Concentration,
    ConsensusContext,
    CovenantPointer,
    DrawdownCause,
    FilingRef,
    FilingSectionExtract,
    FinancialSummary,
    IdiosyncraticVsShared,
    ImpliedExpectationRow,
    ImpliedExpectations,
    ImpliedValuation,
    LeverageSurvival,
    MechanicalLayer,
    OperatingDriver,
    OperatingDriversExtract,
    PeerComps,
    PerfPoint,
    PrimarySource,
    Quality,
    ReconciliationValue,
    ReleaseExtract,
    Sourced,
    SourceStatus,
    StockInfo,
    StockPerformance,
    Valuation,
)
from vinci.edgar import filing_sections, primary_source, release_parse
from vinci.edgar.client import EdgarClient
from vinci.edgar.concepts import extract_points, latest_instant
from vinci.edgar.release_parse import GUIDANCE_REFUSAL_PREFIX
from vinci.eod import compute_price_features
from vinci.finra import FinraLayoutError, short_interest_points
from vinci.graph.exposure import ExposureGraph
from vinci.graph.filings import html_to_text, normalize_text
from vinci.monitor import benchmark_for_cap
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver import EntityResolver, ResolutionError
from vinci.resolver.index import pad_cik
from vinci.schemas.data_record import DataRecord, Identity
from vinci.schemas.envelope import CoverageStatus, DataField
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import DECLINE_WINDOW_DAYS, GAP_DOWN_THRESHOLD
from vinci.store import Store
from vinci.universe import benchmark_identity

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_DECLINE_WINDOW_DAYS = 180  # the G2 decline window — keep the cohort comparison on the same window


def _sourced(field: DataField[float] | DataField[int], *, source_ref: str) -> Sourced[float]:
    """Lift a screen data-record :class:`DataField` into a source-bound dossier fact."""
    if field.is_known and field.value is not None:
        return Sourced.present(float(field.value), source_ref=source_ref, note=field.note)
    return Sourced.unknown(note=field.note or "UNKNOWN in the screen data-record")


_S = TypeVar("_S")


def _prefer_ciq(ciq: Sourced[_S], edgar: Sourced[_S] | None) -> Sourced[_S]:
    """CIQ stays PRIMARY: keep the CIQ field whenever it is PRESENT; otherwise fall to the EDGAR
    fallback (itself PRESENT or fail-loud UNKNOWN). Never overrides a populated CIQ field."""
    if ciq.status is SourceStatus.PRESENT or edgar is None:
        return ciq
    return edgar


def _companyfacts_or_none(edgar: EdgarClient, cik: str | None) -> dict[str, Any] | None:
    """EDGAR companyfacts for the fallback, or None (no CIK / fetch failed) — never raises into the
    assembler; a None just leaves the CIQ field UNKNOWN (no fabrication)."""
    if not cik:
        return None
    try:
        return edgar.companyfacts(cik)
    except (HttpError, KeyError, ValueError):  # ValueError: pad_cik int() on a non-numeric CIK
        return None


def _close_on_or_before(bars: list[PriceBar], ref: date) -> float | None:
    elig = [b for b in bars if b.bar_date <= ref]
    return max(elig, key=lambda b: b.bar_date).close if elig else None


def _window_return(bars: list[PriceBar], ref: date, days: int) -> float | None:
    then = _close_on_or_before(bars, ref - timedelta(days=days))
    now = _close_on_or_before(bars, ref)
    return (now / then - 1.0) if (then and now and then > 0) else None


# --- drawdown cause: label by 8-K item codes + parse the catalyst from the filing TEXT --------

# 8-K item codes → standard titles (cause is read from the codes, never blanket "earnings").
_ITEM_TITLES: dict[str, str] = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "2.02": "Results of Operations and Financial Condition",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy a Listing Rule",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.02": "Departure/Election of Directors or Certain Officers",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}
# short per-code cause label for the per-gap summary (9.01 exhibits carry no event, omitted).
_CAUSE_BY_ITEM: dict[str, str] = {
    "1.01": "material agreement (1.01)", "1.02": "agreement termination (1.02)",
    "2.02": "earnings (2.02)", "2.05": "restructuring (2.05)", "2.06": "impairment (2.06)",
    "3.01": "delisting notice (3.01)", "4.02": "restatement (4.02)",
    "5.02": "management change (5.02)", "7.01": "Reg-FD (7.01)", "8.01": "other event (8.01)",
}


def item_labels(items: list[str]) -> list[str]:
    """Map 8-K item codes to "code title" so the cause is read from the codes, not guessed."""
    return [f"{c} {_ITEM_TITLES.get(c, 'Item ' + c)}" for c in items]


# The 8-K items that can actually MOVE a price (= the keys of _CAUSE_BY_ITEM). An 8-K carrying only
# items OUTSIDE this set is administrative — a routine annual-meeting vote (5.07), bylaw amendment
# (5.03), etc. — and does not explain a gap-down. 5.02 (management change) stays IN: a CEO departure
# genuinely moves a stock.
_EXPLANATORY_ITEMS = frozenset(_CAUSE_BY_ITEM)


def _is_explanatory(items: list[str]) -> bool:
    """Does this 8-K carry any item that could plausibly cause a gap-down?"""
    return bool(set(items) & _EXPLANATORY_ITEMS)


def _admin_label(items: list[str]) -> str:
    """Plain-English label for an administrative-only 8-K — no list repr, no house jargon."""
    if "5.07" in items:
        return "no earnings/guidance filing (annual-meeting 8-K only)"
    codes = ", ".join(c for c in items if c not in _EXPLANATORY_ITEMS) or "—"
    return f"no earnings/guidance filing (administrative 8-K only · items {codes})"


# (8.01 refinement) ANCHORED patterns on the parsed 8.01 body — a bare "other event" hides the one
# cause class 8.01 routinely carries: a securities offering. Deterministic two-step: an OFFERING
# CONTEXT anchor must fire first, then the instrument decides the label (notes → debt, stock →
# equity, neither → the honest generic). No context anchor → the label stays "other event".
_OFFERING_CTX = re.compile(r"underwriting agreement|public offering|to issue and sell", re.I)
_OFFERING_DEBT = re.compile(r"\bnotes?\b|debentures|principal amount", re.I)
_OFFERING_EQUITY = re.compile(r"common stock|ordinary shares|\bshares\b", re.I)


def _refine_801(label: str, events: list[str] | None) -> str:
    """Refine the 8.01 "other event" label from the filing's own parsed body — never a guess."""
    body = " ".join(e for e in (events or []) if e.startswith("8.01"))
    if not body or not _OFFERING_CTX.search(body):
        return label
    if _OFFERING_DEBT.search(body):
        return "debt offering (8.01)"
    if _OFFERING_EQUITY.search(body):
        return "equity offering (8.01)"
    return "securities offering (8.01)"


def _gap_label(items: list[str], events: list[str] | None = None) -> str:
    """A short cause label for one gap-down from its 8-K items. Never "earnings" without 2.02;
    an administrative-only 8-K (5.07 annual-meeting vote, etc.) is NOT a cause — it reads as no
    earnings/guidance filing, matching the 'no company filing' treatment of a gap with no 8-K.
    An 8.01 refines to its offering class when the parsed body anchors one (_refine_801)."""
    labels = [
        _refine_801(_CAUSE_BY_ITEM[c], events) if c == "8.01" else _CAUSE_BY_ITEM[c]
        for c in items
        if c in _CAUSE_BY_ITEM
    ]
    return " + ".join(labels) if labels else _admin_label(items)


def parse_8k_events(text: str, items: list[str], accession: str) -> list[str]:
    """Source-bound per-item catalyst summaries from the 8-K body — the customer/contract/executive
    action, not just the code. Fail loud (UNKNOWN — read by hand) when a body can't be parsed; never
    fabricate. Pure: the filing's own words in, capped summaries out."""
    out: list[str] = []
    for code in items:
        if code == "9.01":  # exhibits — no narrative event
            continue
        title = _ITEM_TITLES.get(code, f"Item {code}")
        m = re.search(rf"Item\s+{re.escape(code)}\b", text, re.IGNORECASE)
        body = ""
        if m:
            seg = text[m.end() : m.end() + 1400]
            nxt = re.search(r"Item\s+\d\.\d\d\b|\bSIGNATURES?\b", seg, re.IGNORECASE)
            seg = seg[: nxt.start()] if nxt else seg
            body = re.sub(r"\s+", " ", seg).strip(" .:;-—").strip()
        if len(body) >= 40:
            out.append(f"{code} {title}: {body[:400]}")
        else:
            out.append(f"{code} {title}: UNKNOWN narrative — read filing {accession} by hand")
    if not out:
        codes = ", ".join(items) or "—"
        out.append(f"only non-narrative items ({codes}) — read filing {accession} by hand")
    return out


def _drawdown_filings(
    edgar: EdgarClient, http: CachedHttp, cik: str, gap_dates: list[date]
) -> list[FilingRef]:
    if not gap_dates:
        return []
    filings = edgar.recent_filings(cik, forms=("8-K",), since=min(gap_dates) - timedelta(days=7))
    refs: list[FilingRef] = []
    for gd in gap_dates:
        lo, hi = gd - timedelta(days=1), gd + timedelta(days=4)
        near = sorted(
            (f for f in filings if lo <= f.filing_date <= hi), key=lambda f: f.filing_date
        )
        if not near:
            continue
        f = near[0]
        url, events = "", [f"UNKNOWN — no primary document for {f.accession}; read by hand"]
        if f.primary_doc:
            url = _ARCHIVE.format(
                cik=int(pad_cik(f.cik)), acc=f.accession.replace("-", ""), doc=f.primary_doc
            )
            try:
                events = parse_8k_events(
                    html_to_text(http.get_text(url, ttl_seconds=None)), list(f.items), f.accession
                )
            except HttpError:
                events = [f"UNKNOWN — could not fetch filing {f.accession}; read by hand"]
        refs.append(
            FilingRef(
                gap_date=gd.isoformat(), filing_date=f.filing_date.isoformat(), form=f.form,
                items=list(f.items), item_types=item_labels(list(f.items)),
                accession=f.accession, url=url, events=events,
                explanatory=_is_explanatory(list(f.items)),
            )
        )
    return refs


_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
_GUIDANCE_ANCHOR = re.compile(
    r"(?:revis|updat)\w*[^.]{0,80}?(?:full[- ]year|outlook|guidance)", re.I)
_MONEY = re.compile(r"\$\s?\d")
_METRIC = re.compile(r"\b(revenue|ebitda|eps|free cash flow|earnings per share)\b", re.I)


def _exhibit_991_url(http: CachedHttp, cik: str, accession: str) -> str | None:
    """The furnished Exhibit 99.1 (press release) URL, or None if the filing furnishes none.

    ONE detector, shared with the primary-source fetch: this module used to carry its own copy of
    the filename regex, and the two DRIFTED — the copy here never learned the '_' separator class,
    so it missed 'ex99_1.htm' that the other matched. The rule now lives once, in
    release_parse.exhibit_991_urls (EDGAR's SGML exhibit TYPE, filename match as fallback)."""
    urls = release_parse.exhibit_991_urls(http, cik, accession)
    return urls[0] if urls else None


def _extract_revised_guidance(text: str) -> str | None:
    """The REVISED full-year outlook block (figures verbatim) from a 99.1 press release. Anchored on
    'revis…/updat…(full-year|outlook|guidance)' so it surfaces a *changed* outlook, not an initial
    one ('updat' is load-bearing: SMPL's 2026-04-09 exhibit said 'Updating Fiscal Year 2026
    Outlook' — no 'revis…' verb anywhere — and the revis-only anchor read it as no-outlook while
    the gap-card parser extracted the same figures from the same exhibit).
    Verbatim — the figures are read from the primary source, never parsed into numbers here (no
    mis-extraction). Returns None when no revised-outlook section exists (→ UNKNOWN upstream).

    Among figures-bearing windows, an anchor that INTRODUCES a list (a ':' within 40 chars of the
    anchor) wins over a bare headline: SMPL's top headline ('Updates Fiscal Year 2026 Outlook
    Denver, CO …') passes the money+metric test on the RESULTS lede behind it, while the actual
    outlook bullets sit under the later 'Updating Fiscal Year 2026 Outlook:' heading. The first
    figures-bearing window stays as the fallback when no colon-introduced anchor exists."""
    fallback: str | None = None
    for m in _GUIDANCE_ANCHOR.finditer(text):  # skip the lede; take the anchor whose window has the
        window = " ".join(text[m.start() : m.start() + 800].split())  # the figures window
        if len(_MONEY.findall(window)) >= 2 and _METRIC.search(window):
            if ":" in text[m.start() : m.end() + 40]:
                return window
            if fallback is None:
                fallback = window
    return fallback


def _revised_guidance(http: CachedHttp, cik: str, filings: list[FilingRef]) -> Sourced[str]:
    """Follow the furnished 99.1 exhibit on the drawdown 8-Ks (the body only *points* to it) and
    surface the company's revised full-year guidance — the verdict-relevant number. Source-bound to
    the exhibit; fail loud UNKNOWN naming the accession(s). The UNKNOWN note distinguishes 'a 99.1
    WAS parsed but no revised-outlook block matched' from 'no 99.1 located' — it never claims the
    exhibit wasn't parsed when it was (SMPL: the gap card extracted this very exhibit's figures
    while this note said 'no … exhibit parsed' — an internal contradiction in one dossier)."""
    tried: list[str] = []
    parsed: list[str] = []
    for f in filings:
        if not ({"2.02", "7.01", "8.01"} & set(f.items)):  # press releases live under these items
            continue
        if f.accession in tried:  # two gap-downs can share ONE filing — list it once
            continue
        tried.append(f.accession)
        url = _exhibit_991_url(http, cik, f.accession)
        if url is None:
            continue
        try:
            text = html_to_text(http.get_text(url, ttl_seconds=None))
        except HttpError:
            continue
        parsed.append(f.accession)
        block = _extract_revised_guidance(text)
        if block:
            ref = f"EDGAR 8-K {f.accession} Ex-99.1 — {url}"
            return Sourced.present(block, source_ref=ref)
    if parsed:
        return Sourced.unknown(
            note=f"no revised-outlook block matched in the parsed 99.1 for 8-Ks {parsed}")
    if tried:
        # located/fetched: an accession lands here when no 99.1 URL was found OR the fetch
        # errored — the exhibit may exist unretrieved; never claim more precision than we have.
        # The "for 8-Ks ['…']" tail is the shape _clean_note/cleanNote singularize — keep it.
        return Sourced.unknown(note=f"no 99.1 exhibit located/fetched for 8-Ks {tried}")
    return Sourced.unknown(note="no results/Reg-FD/other-event 8-K at the gap-downs with a 99.1")


def _drawdown_cause(record: DataRecord, edgar: EdgarClient, http: CachedHttp) -> DrawdownCause:
    gaps = sorted(e.event_date for e in record.events if e.event_type.value == "earnings_gap_down")
    cik = record.identity.cik
    filings = _drawdown_filings(edgar, http, cik, gaps) if cik else []
    by_gap = {f.gap_date: f for f in filings}
    if gaps:
        parts = [
            f"{gd.isoformat()} "
            f"{_gap_label(by_gap[gd.isoformat()].items, by_gap[gd.isoformat()].events)}"
            if gd.isoformat() in by_gap
            # state the WORLD, not our process: a hard fall on a day the company filed nothing is
            # itself a finding (it points away from company news), not a tooling miss.
            else f"{gd.isoformat()} no company filing"
            for gd in gaps
        ]
        shape = Sourced.present(
            "discrete gap-downs — " + "; ".join(parts),
            source_ref="EDGAR 8-K item codes at the gap-down dates (not blanket-labelled earnings)",
        )
    else:
        shape = Sourced.present(
            "gradual bleed — no discrete gap-down detected",
            source_ref="EOD gap-down detector (screen events): none",
        )
    dates_field: Sourced[list[str]] = (
        Sourced.present(
            [g.isoformat() for g in gaps], source_ref="EOD gap-down detector (screen events)"
        )
        if gaps
        else Sourced.unknown(note="no gap-down events on the data-record")
    )
    return DrawdownCause(
        shape=shape,
        gap_down_dates=dates_field,
        filings=filings,
        revised_guidance=(
            _revised_guidance(http, cik, filings)
            if cik and filings
            else Sourced.unknown(note="no catalyst 8-K to follow for a revised-guidance exhibit")
        ),
        # the detector's own params, copied from the screen constants (ONE source of truth) so the
        # renderers can mark coverage honestly (window boundary + pre-window drops).
        gap_threshold=GAP_DOWN_THRESHOLD,
        gap_window_days=DECLINE_WINDOW_DAYS,
    )


# --- (B1) informative drawdown: join each gap-down's 8-K to its parsed EX-99.1 drivers -----------
_DRIVER_METRICS = ("adjusted ebitda", "adjusted operating income", "adjusted net income",
                   "adjusted eps")
_METRIC_SHORT = {
    "adjusted ebitda": "adj EBITDA",
    "adjusted operating income": "adj operating income",  # pre interest/tax — never "net income"
    "adjusted net income": "adj net income",
    "adjusted eps": "adj EPS",
}


def _acc_of(source_ref: str) -> str | None:
    """The EDGAR accession embedded in a release source_ref ('8-K 0001628280-26-033601 EX-99.1')."""
    m = re.search(r"(\d{10}-\d{2}-\d{6})", source_ref)
    return m.group(1) if m else None


def _period_key(period: str) -> tuple[int, int]:
    """Sort key for a period: (year, quarter) — 'Q1 2026' → (2026, 1), '2025' → (2025, 0)."""
    ym = re.search(r"(\d{4})", period)
    qm = re.search(r"Q(\d)", period)
    return (int(ym.group(1)) if ym else 0, int(qm.group(1)) if qm else 0)


def _fmt_driver(metric: str, value: float) -> str:
    """$M for EBITDA/NI, $/sh for EPS; sign-aware ('-$5.5M', '$44.7M', '-$0.04')."""
    if "eps" in metric:
        return f"-${abs(value):.2f}" if value < 0 else f"${value:.2f}"
    return f"-${abs(value):,.1f}M" if value < 0 else f"${value:,.1f}M"


def guidance_refusal_flags(releases: Sequence[ReleaseExtract]) -> list[str]:
    """(item 22) Lift GUIDANCE REFUSALS off the releases so they reach the READER.

    ``qa_flags`` is the machine tier by design (``render.py``: "dev/JSON only"), and a release's
    own flags roll up nowhere — so a refused guidance sentence was invisible on every surface, the
    absent-and-silent shape the visible-absence rule prohibits. ``flags.partition`` routes anything
    off the QA hide-list to the human caveat channel, which is where "your guidance picture is
    incomplete, and here is the sentence" belongs.

    ONLY the refusals. The sibling ``no anchored pattern matched`` flags say a release stated no
    guidance at all — ordinary across the fleet, and promoting those would drown the channel and
    make the real refusals harder to see, not easier.

    A named function rather than an inline comprehension so the routing has a behavioural pin:
    inlined, the only available test was a source-text assertion."""
    return [f for r in releases for f in r.qa_flags
            if f.startswith(GUIDANCE_REFUSAL_PREFIX)]


def _fmt_guide_range(low: float | None, high: float | None, unit: str) -> str:
    """A guidance range, formatted from its OWN unit and at a precision that keeps the range a
    range. TWO defects, one root, and fixing either alone still prints a wrong number.

    UNIT. The old formatter had one branch for "%" and assumed "$M" for everything else, so VRRM's
    adjusted-EPS guide of $1.19–$1.25 **per share** printed as "$1.2–$1.2M" — wrong by 1e6. The
    unit was unexpressible upstream (``GuidanceItem.unit`` had no ``$/sh``), which is why the
    default was never questioned: every new metric inherits it.

    PRECISION. ``.1f`` collapsed 1.19–1.25 to "$1.2–$1.2" — a ZERO-WIDTH range, which reads as a
    point estimate the company never gave. Decimals are widened until the two bounds are actually
    distinguishable, so the printed range is the recorded one.
    """
    if low is None or high is None:
        return "stated, no number given"

    def pair(dp: int) -> tuple[str, str]:
        return f"{low:,.{dp}f}", f"{high:,.{dp}f}"

    base = {"$M": 1, "$/sh": 2, "%": 1}.get(unit, 1)
    dp = base
    while dp < 4 and low != high and pair(dp)[0] == pair(dp)[1]:
        dp += 1
    lo, hi = pair(dp)
    if unit == "%":
        return f"{lo}–{hi}% growth"
    if unit == "$/sh":
        return f"${lo}–${hi}/sh"
    return f"${lo}–${hi}M"


def _compose_gap_drivers(release: ReleaseExtract) -> Sourced[str] | None:
    """WHAT the results showed — the latest-period adjusted EBITDA / net income / EPS (with the
    prior-period contrast), one-off charges, and the forward outlook — from an already-parsed
    EX-99.1, source-bound to the exhibit. None when the exhibit parsed no drivers. Deterministic
    formatting of STORED values (no new number, no conclusion)."""
    parts: list[str] = []
    by_metric: dict[str, list[ReconciliationValue]] = {}
    for rc in release.reconciliation:
        by_metric.setdefault(rc.metric, []).append(rc)
    for metric in _DRIVER_METRICS:
        items = sorted(by_metric.get(metric, []), key=lambda x: _period_key(x.period), reverse=True)
        if not items:
            continue
        latest = items[0]
        s = f"{_METRIC_SHORT[metric]} {latest.period} {_fmt_driver(metric, latest.value)}"
        # the DIRECTION the release stated beside the level — a gap-down is about the delta
        if latest.change:
            s += f" ({latest.change})"
        # the prior contrast must match the period TYPE (annual vs quarterly) — an FY result pairs
        # with the prior FY, a quarter with the prior-year quarter, never FY vs Q4.
        latest_q = "Q" in latest.period.upper()
        prior = next(
            (i for i in items[1:]
             if i.period != latest.period and ("Q" in i.period.upper()) == latest_q),
            None,
        )
        if prior is not None:
            s += f" (vs {_fmt_driver(metric, prior.value)} {prior.period})"
        parts.append(s)
    for o in release.one_offs:
        # Trim at a CLAUSE boundary, not a character count: the old 48-char cut left dangling
        # connectives ("…charge associated with a", "…expenses in the"), which read as a
        # truncation artefact rather than a fact. Prefer the shortest complete noun phrase.
        desc = re.split(r"\s+(?:associated|related\s+to|in\s+the|for\s+the|due\s+to|which)\b",
                        o.description, maxsplit=1)[0].strip(" ,;")
        parts.append(f"${o.amount:,.1f}M {desc}")
    for g in release.guidance:
        if g.qualitative:
            outlook = "stated, no number given"  # honest: the company spoke, without a figure
        else:
            outlook = _fmt_guide_range(g.low, g.high, getattr(g, "unit", "$M"))
        parts.append(f"{g.period} {g.metric} outlook: {outlook}")
    if not parts:
        return None
    # DEDUP, order-preserving: a release that states the same one-off twice (IT's $150.0M Digital
    # impairment appeared in both the headline and the detail paragraph) must not read as a stutter
    # — identical segments carry no second fact.
    parts = list(dict.fromkeys(parts))
    return Sourced.present("; ".join(parts), source_ref=release.source_ref)


def _enrich_drawdown_drivers(mech: MechanicalLayer, primary: PrimarySource) -> MechanicalLayer:
    """(B1) Join each gap-down's 8-K accession to its parsed EX-99.1 release, attaching the driver
    summary to the FilingRef — the informative cause that replaces item-code boilerplate. Assemble/
    inform: it re-presents already-parsed facts, source-bound; renders no new conclusion."""
    dc = mech.drawdown_cause
    if not dc.filings:
        return mech
    rel_by_acc: dict[str, ReleaseExtract] = {}
    for r in primary.releases:
        acc = _acc_of(r.source_ref)
        if acc is not None:
            rel_by_acc[acc] = r
    new_filings = [
        f.model_copy(update={"drivers": _compose_gap_drivers(rel_by_acc[f.accession])})
        if f.accession in rel_by_acc else f
        for f in dc.filings
    ]
    if new_filings == list(dc.filings):
        return mech
    new_dc = dc.model_copy(update={"filings": new_filings})
    return mech.model_copy(update={"drawdown_cause": new_dc})


# --- idiosyncratic vs shared (graph cohort + EOD window returns) -------------------------------


def _cohort(
    graph: ExposureGraph, resolver: EntityResolver, store: Store, ticker: str, ref: date
) -> Sourced[list[CohortMember]]:
    node = graph.resolve(ticker, resolver)
    if node is None:
        return Sourced.unknown(
            note=f"{ticker} not in graph_coverage.json — no exposed cross-section to compare"
        )
    members: list[CohortMember] = []
    for x in graph.exposed_within(node, hops=2):
        if not x.ticker:
            continue
        try:
            bars = store.get_price_history(resolver.resolve_ticker(x.ticker).internal_id)
        except (ResolutionError, LookupError):
            bars = []
        members.append(
            CohortMember(
                ticker=x.ticker, hops=x.hops,
                ret_180d=_window_return(bars, ref, _DECLINE_WINDOW_DAYS) if bars else None,
                via=(" · ".join(x.path))[:200],
            )
        )
    if not members:
        return Sourced.unknown(note=f"{ticker} in graph but no US-listed exposed names to price")
    return Sourced.present(
        members, source_ref=f"graph_coverage.json node={node}; EOD {_DECLINE_WINDOW_DAYS}d ret"
    )


def _idio_read(name_180d: Sourced[float], cohort: Sourced[list[CohortMember]]) -> Sourced[str]:
    if cohort.status.value != "present" or not cohort.value or name_180d.value is None:
        return Sourced.unknown(
            note="no graph cohort to compare — see rel_vs_market for the name-vs-market read"
        )
    rets = [m.ret_180d for m in cohort.value if m.ret_180d is not None]
    if not rets:
        return Sourced.unknown(note="cohort names have no price history over the window")
    med = statistics.median(rets)
    gap = name_180d.value - med
    if gap <= -0.15:
        read = f"fell ALONE (idiosyncratic): name {name_180d.value:.0%} vs cohort median {med:.0%}"
    elif med <= -0.20:
        read = f"fell WITH cohort (shared/thematic): name {name_180d.value:.0%} vs median {med:.0%}"
    else:
        read = f"mixed: name {name_180d.value:.0%} vs cohort median {med:.0%} (cohort steady)"
    return Sourced.present(read, source_ref=f"derived from {len(rets)} cohort names; face-validity")


def _resolve_benchmark(
    market_cap_musd: Sourced[float], ref: date, *, screen_cap_usd: float | None = None
) -> tuple[Identity, str]:
    """The dossier surface's benchmark = the SAME cap-band policy the monitor freezes at entry
    (``vinci.monitor.benchmark_for_cap``), applied to the CIQ cap ($M) at the reference date.
    One policy, two instants — the monitor's assignment stays frozen for scoring; this one gives
    the analytical context (exhibit + 180d relative) the right yardstick.

    Cap fallback order: CIQ cap → the SCREEN-TIME EOD×XBRL cap the ranker already froze at entry
    (``screen_cap_usd``, threaded from the ranked-queue row) → the small-cap IWM default. The
    ranker fallback exists because the CIQ cap is environment-sensitive (absent when re-assembling
    in an incomplete store), which silently flipped a mid-cap's benchmark to IWM (the IT MDY→IWM
    drift); the ranker's screen-time cap is present regardless and can't reselect on re-assembly.
    Every branch states its basis loudly — never a silent guess."""
    cap_m = market_cap_musd.value if market_cap_musd.status is SourceStatus.PRESENT else None
    if cap_m is not None and cap_m > 0:
        cap_usd = cap_m * 1e6  # CIQ panel is $M; the policy takes USD
        sym, band = benchmark_for_cap(cap_usd)
        basis = f"cap-band: ${cap_usd / 1e9:.1f}B @ {ref} → {band} → {sym}"
    elif screen_cap_usd is not None and screen_cap_usd > 0:
        sym, band = benchmark_for_cap(screen_cap_usd)
        basis = f"cap-band: ${screen_cap_usd / 1e9:.1f}B (screen-time, ranker) → {band} → {sym}"
    else:
        sym, basis = "IWM", "cap-band: cap UNKNOWN → small-cap default IWM"
    return benchmark_identity(sym), basis


def _idiosyncratic_vs_shared(
    record: DataRecord, store: Store, graph: ExposureGraph, resolver: EntityResolver, ref: date,
    *, bench: Identity, bench_basis: str,
) -> IdiosyncraticVsShared:
    sym = record.identity.eod_symbol
    bsym = bench.eod_symbol
    bars = store.get_price_history(record.identity.internal_id)
    name_ret = _window_return(bars, ref, _DECLINE_WINDOW_DAYS) if bars else None
    name_180d = (
        Sourced.present(
            name_ret, source_ref=f"EOD {sym} {_DECLINE_WINDOW_DAYS}d to {ref}"
        )
        if name_ret is not None
        else Sourced.unknown(note="name has no bars over the window")
    )
    bench_bars = store.get_price_history(bench.internal_id)
    mkt_ret = _window_return(bench_bars, ref, _DECLINE_WINDOW_DAYS) if bench_bars else None
    market_180d = (
        Sourced.present(
            mkt_ret, source_ref=f"EOD {bsym} {_DECLINE_WINDOW_DAYS}d to {ref} ({bench_basis})"
        )
        if mkt_ret is not None
        else Sourced.unknown(note=f"{bsym} benchmark bars unavailable — run `vinci refresh {bsym}`")
    )
    # rel is RECOMPUTED here on the same yardstick as market_180d. The screen record's G2 rel
    # (name−IWM, the universe-wide gate) stays in the record — mixing the two would put a
    # small-cap denominator under a mid/large-cap read.
    rel = (
        Sourced.present(
            name_ret - mkt_ret,
            source_ref=f"EOD {sym}−{bsym} {_DECLINE_WINDOW_DAYS}d to {ref} (assembly, cap-band)",
        )
        if (name_ret is not None and mkt_ret is not None)
        else Sourced.unknown(
            note=f"name−{bsym} needs both legs; "
                 f"missing {'name' if name_ret is None else bsym} bars"
        )
    )
    cohort = _cohort(graph, resolver, store, record.identity.ticker, ref)
    return IdiosyncraticVsShared(
        name_180d_return=name_180d, market_180d_return=market_180d, rel_vs_market=rel,
        cohort=cohort, read=_idio_read(name_180d, cohort),
        benchmark_symbol=bsym, benchmark_basis=bench_basis,
    )


_PERF_WINDOW_DAYS = 364  # 52 weeks — the Brief stock-performance exhibit window
# DAILY resolution (a 52-wk window holds ~251 trading days; the cap only guards a pathological
# store). Weekly-ish downsampling (the old cap of 60) SMOOTHED AWAY the very one-day gap-downs the
# What-broke chart marks (CNXC's -11.2% Jun-30 drop was invisible), and made the true 1-day gap %
# unrecoverable from the committed series (a weekly proxy misstated -12.7% as -21.7%). Daily points
# let the renderers derive each gap's exact close-to-close move — the detector's own formula on the
# same closes — instead of fabricating from a downsample. Cost: ~12KB/name of committed JSON.
_PERF_MAX_POINTS = 400


def _stock_performance(
    identity: Identity, store: Store, ref: date, *, bench: Identity
) -> StockPerformance | None:
    """52-week rebased price path — the name vs its cap-band benchmark, both indexed to 100 at the
    window start. Reads the SAME EOD closes the idio comparison uses (assemble/visualize, never
    conclude). Returns None (exhibit absent) when the name has <2 window bars — fail-loud, never a
    fabricated series. The benchmark is aligned to the name's trading days via as-of closes; a
    point's ``benchmark`` is None only when the index has no bar on/before that day (the name path
    still renders)."""
    sym = identity.eod_symbol
    lo = ref - timedelta(days=_PERF_WINDOW_DAYS)
    name_win = [b for b in store.get_price_history(identity.internal_id) if lo <= b.bar_date <= ref]
    if len(name_win) < 2:
        return None
    base_name = name_win[0].close
    if base_name <= 0:
        return None
    bench_bars = store.get_price_history(bench.internal_id)
    base_bench = _close_on_or_before(bench_bars, name_win[0].bar_date)

    def _rebased_bench(d: date) -> float | None:
        c = _close_on_or_before(bench_bars, d)
        return round(c / base_bench * 100.0, 2) if (c and base_bench) else None

    step = max(1, len(name_win) // _PERF_MAX_POINTS)
    idxs = list(range(0, len(name_win), step))
    if idxs[-1] != len(name_win) - 1:
        idxs.append(len(name_win) - 1)  # always pin the current (right-edge) point
    points = [
        PerfPoint(
            date=name_win[i].bar_date.isoformat(),
            name=round(name_win[i].close / base_name * 100.0, 2),
            benchmark=_rebased_bench(name_win[i].bar_date),
        )
        for i in idxs
    ]
    last_bench = _close_on_or_before(bench_bars, name_win[-1].bar_date)
    return StockPerformance(
        points=points,
        name_symbol=sym,
        benchmark_symbol=bench.eod_symbol,
        as_of=name_win[-1].bar_date,
        window_days=_PERF_WINDOW_DAYS,
        name_return=name_win[-1].close / base_name - 1.0,
        benchmark_return=(last_bench / base_bench - 1.0) if (last_bench and base_bench) else None,
        source_ref=(
            f"EOD {sym} vs {bench.eod_symbol} rebased to 100, "
            f"{name_win[0].bar_date}..{name_win[-1].bar_date}"
        ),
    )


# --- share-count trend + P/E-basis sanity (EDGAR XBRL) ----------------------------------------

_SHARES_WINDOW_DAYS = 730  # trailing ~2y — current capital-allocation posture, not a stale 7y delta


def _share_count_trend(edgar: EdgarClient, cik: str, reference_date: date) -> Sourced[str]:
    """Recent (trailing ~2y) share-count trend — a 7y endpoint delta hides the current posture."""
    try:
        pts = [p for p in extract_points(edgar.companyfacts(cik), "shares") if p.value]
    except (HttpError, KeyError):
        return Sourced.unknown(note="EDGAR companyfacts shares unavailable")
    pts.sort(key=lambda p: p.period_end)
    recent = [p for p in pts if (reference_date - p.period_end).days <= _SHARES_WINDOW_DAYS]
    if len(recent) < 2:
        return Sourced.unknown(
            note=f"<2 XBRL shares points in the trailing ~2y ({len(pts)} total) — no current trend"
        )
    first, last = recent[0], recent[-1]
    pct = (last.value / first.value - 1.0) if first.value else 0.0
    word = "diluting" if pct > 0.02 else "buying back" if pct < -0.02 else "flat"
    span = (last.period_end - first.period_end).days / 365.0
    return Sourced.present(
        f"{word} (trailing ~{span:.1f}y): {first.value:,.0f} ({first.period_end}) → "
        f"{last.value:,.0f} ({last.period_end}), {pct:+.1%}",
        source_ref=f"EDGAR XBRL shares, trailing {first.period_end}..{last.period_end}",
    )


def _pe_reconciliation(
    record: DataRecord, edgar: EdgarClient, bundle: CiqBundle, revised_guidance: Sourced[str]
) -> tuple[str, str] | None:
    """Whether the trailing GAAP P/E is meaningful. Returns ``(flag, pe_note)`` or None — ``flag``
    is the full human-review line; ``pe_note`` is a SHORT caveat to carry ON the P/E field itself so
    the multiple never renders 'naked' as cheap (closes the gap where a distorted P/E showed clean).
    When the forward adjusted EPS is now in the dossier (99.1), RESOLVE the old 'verify against
    forward EPS' flag into a reconciliation — the trailing GAAP P/E is one-time-distorted and the
    clean read is the forward adjusted guide (this also subsumes the EDGAR-vs-CIQ P/E conflict).
    When the adjusted EPS isn't available the original open flag stands. None when trailing EPS is
    in line with recent history (no distortion)."""
    pe = record.fundamentals.pe
    if not pe.is_known or pe.value is None or not record.identity.cik:
        return None
    try:
        eps = sorted(
            (p for p in extract_points(edgar.companyfacts(record.identity.cik), "eps_diluted")
             if p.is_annual and p.value is not None),
            key=lambda p: p.period_end,
        )
    except (HttpError, KeyError):
        return None
    if len(eps) < 3:
        return None
    latest, prior = eps[-1].value, [p.value for p in eps[:-1]][-4:]
    med = statistics.median(prior)
    if med == 0 or latest is None:
        return None
    if not ((latest > 0) != (med > 0) or latest / med > 2.5 or latest / med < 0.4):
        return None  # trailing EPS is in line with recent history — no distortion
    eps_m = _ADJ_EPS.search(revised_guidance.value or "")
    price = record.prices.last.value if record.prices.last.is_known else None
    ciq_pe = ciq_sheets.pe_ltm_current(bundle)
    if eps_m and price:  # RESOLVED — the forward adjusted EPS is now sourced
        lo, hi = float(eps_m.group(1)), float(eps_m.group(2))
        ciq_tail = (
            f"; CIQ P/LTM {ciq_pe.value:.1f}x uses a different (lower) trailing EPS basis"
            if ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value else ""
        )
        flag = (
            f"RESOLVED (P/E basis) — trailing GAAP P/E {pe.value:.1f}x is one-time-distorted: "
            f"latest GAAP EPS {latest:.2f} is ~{latest / med:.1f}× the recent median {med:.2f}, so "
            f"{pe.value:.1f}x is not a meaningful 'cheap' read. Clean read: forward adjusted guide "
            f"${lo:.2f}–${hi:.2f} → ~{price / ((lo + hi) / 2):.1f}x at the current price{ciq_tail}."
        )
        return flag, "one-time-distorted EPS — not a clean multiple; see the P/E-basis flag"
    flag = (  # adjusted EPS not available — the original open flag stands
        f"P/E may be distorted by non-recurring EPS — latest annual EPS {latest:.2f} vs "
        f"recent median {med:.2f}; verify against normalized/forward EPS (CIQ)"
    )
    note = (
        f"distorted — P/E rests on a non-current positive EPS; latest annual EPS is negative "
        f"({latest:.2f}). Not a meaningful multiple — see the P/E-basis flag"
        if latest < 0 else
        f"distorted — trailing EPS {latest:.2f} is anomalous vs the recent median {med:.2f}; "
        f"not a clean multiple — see the P/E-basis flag"
    )
    return flag, note


def _ltm_gaap_eps(fs: FinancialSummary | None) -> float | None:
    """The LTM GAAP DILUTED EPS as a STRUCTURED value from the financial-summary annual table —
    the 'EPS (GAAP, dil.)' row's ``values`` at the 'LTM' column. None when the summary, the table,
    the row, the LTM column, or the structured value is absent. Reads ``values`` (structured),
    NEVER ``cells`` (display) — the parsers-consume-structured-values rule; a display '(2.08)'/'—'
    is never parsed here."""
    if fs is None:
        return None
    annual = fs.annual
    if annual.status is not SourceStatus.PRESENT or annual.value is None:
        return None
    tbl = annual.value
    # PREFIX-match the LTM header — it can carry a Reclassified '(R)' suffix ('LTM (R)', ciq_sheets
    # tags every period column), exactly like the renderer's own LTM detection
    # (render.py startswith('LTM')). Exact '== "LTM"' would return None on a reclassified twin and
    # silently reintroduce the claim-#7 blind spot for it.
    i = next((k for k, c in enumerate(tbl.columns) if str(c).upper().startswith("LTM")), None)
    if i is None:
        return None
    for row in tbl.rows:
        if row.label == "EPS (GAAP, dil.)" and len(row.values) > i:
            return row.values[i]
    return None


def _eps_caveat_flags(
    record: DataRecord, bundle: CiqBundle, *, eps_resolved: bool,
    ltm_gaap_eps: float | None = None,
) -> list[str]:
    """Flag (a) that earnings power (company-adjusted, non-GAAP EPS) is not shown — UNLESS it now is
    (``eps_resolved``: the 99.1 adjusted EPS surfaced it, so the caveat is a resolved fact, not a
    warning); (b) when the EDGAR P/E conflicts ~Nx with CIQ P/LTM EPS, that the EDGAR trailing
    EPS is one-time-inflated and the synthesis must not anchor on it as 'cheap' — kept UNLESS the
    LTM GAAP EPS is a known LOSS, where (d) owns it (an 'inflated' EPS framing is wrong when GAAP
    trailing is negative, and stacking (b)+(d) is flag noise);
    (d) when a displayed trailing P/E multiple (EDGAR and/or CIQ) rests on NORMALIZED earnings
    while the LTM GAAP diluted EPS is a LOSS — SMPL showed EDGAR P/E 10.9x + CIQ P/LTM 16.0x beside
    an LTM GAAP dil EPS of −2.08 (LTM net income −$199M, the $249M impairment inside the window)
    with no basis label; (b) needs the two multiples ~2x apart, ``_pe_reconciliation`` checks the
    ANNUAL EPS (FY25 +1.02, in line) — both are blind to the LTM sign, the signal that is actually
    wrong; and (c) the ``ltm_gaap_eps``-UNAVAILABLE fallback of (d): CIQ prints a finite P/LTM
    while EDGAR shows no trailing P/E and the GAAP LTM sign can't be read."""
    pe = record.fundamentals.pe
    ciq_pe = ciq_sheets.pe_ltm_current(bundle)
    if not pe.is_known and ciq_pe.status is not SourceStatus.PRESENT:
        return []  # no EPS-based multiple shown at all — nothing to caveat
    out: list[str] = []
    # The bare 'GAAP EPS understates earnings power; adjusted not shown' caveat was DROPPED (2026-06
    # flag-noise audit): pure boilerplate that fired on 8/10 names — its only fact (adjusted EPS
    # UNAVAILABLE) already rides in a synthesis key_unknown, and asserting non-GAAP > GAAP with no
    # non-GAAP figure in hand is itself a mild assemble-not-conclude violation. The substantive,
    # source-bound EDGAR-vs-CIQ P/E conflict below stays.
    # the EDGAR-vs-CIQ P/E conflict: an open flag only while unresolved; when the adjusted EPS is
    # shown it folds into the resolved P/E reconciliation (_pe_reconciliation), not repeated here.
    if (
        not eps_resolved and pe.is_known and pe.value
        and ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value
        and not (ltm_gaap_eps is not None and ltm_gaap_eps < 0)  # a GAAP LTM loss → (d) owns it
    ):
        ratio = max(pe.value, ciq_pe.value) / min(pe.value, ciq_pe.value)
        if ratio >= 2:
            out.append(
                f"EDGAR P/E ({pe.value:.1f}x) conflicts ~{ratio:.0f}x with CIQ P/LTM EPS "
                f"({ciq_pe.value:.1f}x) — EDGAR trailing EPS is one-time-inflated; the "
                f"synthesis must not anchor on {pe.value:.1f}x as 'cheap'."
            )
    # (d) The real basis mismatch, keyed on the LTM GAAP EPS SIGN (the signal (b)/(c)/_pe_recon
    # miss). A displayed positive trailing P/E multiple — EDGAR and/or CIQ — while GAAP LTM diluted
    # EPS is a LOSS. What that PROVES is a NEGATIVE: the denominator is not the LTM GAAP EPS. Which
    # denominator it IS the inputs do not say, so the caveat must not pick one (item 19a): the
    # earlier text asserted "rest on normalized/adjusted earnings", while ``_pe_distortion_note``
    # concluded the OTHER candidate — "P/E rests on a non-current positive EPS" — from a real
    # comparison against the latest annual EPS. Both shipped on CNXC and FUBO, in one dossier, about
    # one number, with the note pointing the reader AT the contradicting flag ("see the P/E-basis
    # flag"). Naming both candidates and declaring the basis unstated is the only claim the inputs
    # support. Names both multiples that are shown.
    if ltm_gaap_eps is not None and ltm_gaap_eps < 0:
        shown: list[str] = []
        if pe.is_known and pe.value and pe.value > 0:
            shown.append(f"EDGAR P/E {pe.value:.1f}x")
        if ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value and ciq_pe.value > 0:
            shown.append(f"CIQ P/LTM EPS {ciq_pe.value:.1f}x")
        if shown:
            # ONE plurality decision feeding every agreeing word. The verb was hardcoded `rest`
            # while the pronoun switched on `len(shown)` — two agreement calls from one fact, so
            # the singular case read "EDGAR P/E 6.0x rest … do not read it" on all three live
            # names (CNXC, FUBO, SMPL), every one of them single-multiple.
            plural = len(shown) > 1
            out.append(
                f"{' and '.join(shown)} {'do' if plural else 'does'} not rest on LTM GAAP "
                f"earnings — LTM GAAP diluted EPS is NEGATIVE ({ltm_gaap_eps:.2f}), so a positive "
                f"multiple must use some other denominator (an EPS from a non-current period, or "
                f"a normalized/adjusted figure — the displayed basis does not say which). Do not "
                f"read {'them' if plural else 'it'} as a GAAP trailing multiple."
            )
    # (c) FALLBACK, only when the LTM GAAP EPS sign is UNAVAILABLE: CIQ prints a finite trailing P/E
    # while EDGAR shows none (an absent EDGAR P/E is itself the negative-GAAP tell). With the sign
    # in hand (d) supersedes this, so gate on ltm_gaap_eps is None to avoid a double caveat.
    elif ltm_gaap_eps is None and not pe.is_known and (
        ciq_pe.status is SourceStatus.PRESENT and ciq_pe.value
    ):
        out.append(
            f"CIQ P/LTM EPS prints {ciq_pe.value:.1f}x while no GAAP trailing P/E is shown "
            f"(trailing GAAP EPS negative or unavailable) — the CIQ multiple rests on a "
            f"different earnings definition; do not read {ciq_pe.value:.1f}x as a GAAP "
            f"trailing P/E."
        )
    return out


def _leverage_basis_flag(net_lev: Sourced[float]) -> str | None:
    """The SHOWN net-debt/EBITDA (CIQ-reported or EDGAR GAAP EBITDA) is not the covenant
    basis: management and credit covenants typically define leverage on ADJUSTED EBITDA (a larger
    denominator → a lower ratio); that non-GAAP reconciliation lives in the earnings
    release/transcript (UNAVAILABLE). Flag the basis so the human doesn't read the reported ratio as
    the covenant ratio. Reads the RESOLVED ratio (the value the dossier actually shows), not the raw
    EDGAR record — so the flagged number can never disagree with the net-debt/EBITDA field.
    Gated on magnitude: below ~1.5x (incl. NET CASH) the reported ratio is already modest and the
    reported-vs-covenant-basis caveat — which only pushes the ratio LOWER — is immaterial review
    noise; it earns its place only when the reported ratio is large enough to look levered. (A 1.3x
    name reads as 'modest' on its own; the caveat changes no judgment there.)"""
    if net_lev.status is not SourceStatus.PRESENT or net_lev.value is None:
        return None
    if net_lev.value < 1.5:
        return None
    return (
        f"Net debt/EBITDA ({net_lev.value:.1f}x) is on REPORTED EBITDA (CIQ / consolidated GAAP), "
        f"not the covenant basis; management and credit covenants typically define leverage on "
        f"adjusted EBITDA (a larger denominator → a lower ratio), reconciled in the earnings "
        f"release/transcript (currently UNAVAILABLE) — do not read {net_lev.value:.1f}x as the "
        f"covenant-basis leverage."
    )


# max/min ratio above which the two CIQ EV/EBITDA sheets are flagged as materially disagreeing
# (~25% apart) — a multiple gap that changes the read. Below it the gap isn't decision-relevant.
_EV_EBITDA_CONFLICT_RATIO = 1.25
# days the Financials→Multiples latest Close may trail the assembly reference date before its
# "current" multiple (and the own-history range/percentile built on it) is treated as STALE. A live
# pull carries an intra-quarter Close within days of the reference; a wider gap means the latest
# column is a clean prior quarter-end that predates any subsequent re-rate (VRRM: 2026-03-31 close,
# 8.5x, vs a post-drawdown comps read of 4.7x). Half a quarter ≈ 45d cleanly separates the two.
_STALE_CLOSE_DAYS = 45


def _ev_ebitda_integrity_flag(bundle: CiqBundle, reference_date: date) -> str | None:
    """CIQ reports the name's current EV/EBITDA on TWO sheets — Financials→Multiples (TEV/LTM,
    ``ev_ebitda_current``, the own-history-range basis) and Comparable-Analysis Trading-Multiples
    (``comps_ev_ebitda``, the cross-sectional lead). A material disagreement is a DATA-INTEGRITY
    signal, not a stable 'basis difference': the usual causes are (1) a STALE Financials Close — its
    last dated column predates the reference date and a since-then re-rate (VRRM), or (2) the two
    sheets priced the name on different dates. Flag the specific cause when detectable, else a plain
    cross-sheet gap; route to the human caveat tier so the operator verifies rather than trusting it
    silently. (After the subject-by-ticker fix, the old MVST 10.0x-vs-38.4x 'conflict' — a comps row
    mis-read as Samsung SDI — no longer fires; the correct Microvast comps read agrees.)

    Staleness is only flagged when it MATTERS: if a present current comps figure AGREES with the
    stale Financials multiple, the staleness is immaterial (the price didn't move) and the inline
    as-of date on the range line already discloses it, so the bottom caveat is suppressed as noise
    (MVST: stale 10.0x vs current comps 11.1x). It fires when comps DISAGREES (VRRM — the read
    changes) or when comps is ABSENT (no way to confirm the stale price is still current)."""
    fin = ciq_sheets.ev_ebitda_current(bundle)
    comp = ciq_sheets.comps_ev_ebitda(bundle)
    fin_date = ciq_sheets.ev_ebitda_asof(bundle)
    stale_days = (reference_date - fin_date).days if fin_date is not None else None
    stale = stale_days is not None and stale_days > _STALE_CLOSE_DAYS

    comps_present = comp.status is SourceStatus.PRESENT
    disagree = False
    if fin.status is SourceStatus.PRESENT and comps_present:
        assert fin.value is not None and comp.value is not None
        lo, hi = sorted((fin.value, comp.value))
        disagree = lo > 0 and hi / lo >= _EV_EBITDA_CONFLICT_RATIO
    # a stale Close whose staleness a present, agreeing comps confirms immaterial adds nothing
    # beyond the inline as-of date — suppress it; keep it when comps disagrees or is absent.
    material_stale = stale and not (comps_present and not disagree)
    if not material_stale and not disagree:
        return None

    if material_stale:
        assert fin_date is not None and stale_days is not None
        head = (
            f"EV/EBITDA stale-price caveat — CIQ's Financials→Multiples current TEV/LTM "
            f"{_fmt_mult(fin)} is priced at its last Close {fin_date.isoformat()}, {stale_days}d "
            f"before the {reference_date.isoformat()} reference; for a since-re-rated name this "
            "'current' multiple AND the own-history range/percentile built on it are stale"
        )
        if disagree:
            head += (
                f". The Comparable-Analysis sheet reads {_fmt_mult(comp)} on a current price — "
                "prefer that figure and re-pull the Financials multiple."
            )
        else:
            head += " — read it as-of that date, not as today's multiple."
        return head
    return (
        f"EV/EBITDA cross-sheet gap — CIQ's Financials→Multiples reads {_fmt_mult(fin)} and its "
        f"Comparable-Analysis sheet reads {_fmt_mult(comp)} on the same concept; verify which the "
        "verdict should use (a stale Close, a different pricing date, or an EBITDA basis) before "
        "reading either."
    )


def _fmt_mult(s: Sourced[float]) -> str:
    """A Sourced EV/EBITDA multiple → 'N.Nx', or '?' when it isn't a present number."""
    return f"{s.value:.1f}x" if s.status is SourceStatus.PRESENT and s.value is not None else "?"


# --- adjusted-basis multiples + leverage (from the 99.1 guide + EDGAR net-debt/shares + EOD) ----

_NUM = r"(\d+(?:\.\d+)?)"  # a plain number — never swallow trailing punctuation (e.g. '1.25.')
_ADJ_EBITDA = re.compile(rf"Adjusted EBITDA of \$?{_NUM}\s*million to \$?{_NUM}\s*million", re.I)
_ADJ_EPS = re.compile(rf"Adjusted EPS of \$?{_NUM} to \$?{_NUM}", re.I)


def _adjusted_facts(
    record: DataRecord, edgar: EdgarClient, revised_guidance: Sourced[str]
) -> tuple[Sourced[str], Sourced[str], Sourced[str]]:
    """Surface the adjusted (non-GAAP) figures the GAAP caveats called UNAVAILABLE — the 99.1
    revised guidance is in the dossier: adjusted EPS, forward EV/adj-EBITDA, and covenant-basis
    net-debt/adj-EBITDA. Each is UNKNOWN if its inputs aren't present — never fabricated (the GAAP
    caveat stays a flag whenever its adjusted counterpart can't be shown). Returns
    (adjusted_eps, ev_ebitda_adjusted_fwd, net_debt_to_ebitda_adjusted)."""
    src = revised_guidance.source_ref or "EDGAR 8-K Ex-99.1"
    text = revised_guidance.value or ""
    eb, eps = _ADJ_EBITDA.search(text), _ADJ_EPS.search(text)
    unk: Sourced[str] = Sourced.unknown(note="adjusted figure not in the 99.1 revised guidance")
    price = record.prices.last.value if record.prices.last.is_known else None

    adj_eps = unk
    if eps:
        lo, hi = float(eps.group(1)), float(eps.group(2))
        tail = f"; adj P/E ~{price / ((lo + hi) / 2):.1f}x at ${price:.2f}" if price else ""
        adj_eps = Sourced.present(
            f"FY26 guide ${lo:.2f}–${hi:.2f}{tail} — earnings power above the GAAP basis",
            source_ref=src,
        )

    cik = record.identity.cik
    try:
        snap = edgar.fundamental_snapshot(cik) if cik else None
        share_pts = (
            [p for p in extract_points(edgar.companyfacts(cik), "shares") if p.value] if cik else []
        )
    except (HttpError, KeyError):
        snap, share_pts = None, []
    net_debt = snap.net_debt.value if snap and snap.net_debt.is_known else None
    shares = max(share_pts, key=lambda p: p.period_end).value if share_pts else None

    ev_adj, nd_adj = unk, unk
    if eb:
        eb_lo, eb_hi = float(eb.group(1)), float(eb.group(2))
        eb_mid = (eb_lo + eb_hi) / 2 * 1e6  # $ (the guide is in $M)
        band = f"FY26 adj-EBITDA ${eb_lo:.0f}–${eb_hi:.0f}M"
        if net_debt is not None:
            nd_adj = Sourced.present(
                f"~{net_debt / eb_mid:.1f}x fwd-adj (net debt ${net_debt / 1e6:,.0f}M / {band})",
                source_ref=f"{src} (adj-EBITDA) + EDGAR net debt",
            )
            if price and shares:
                ev = price * shares + net_debt
                ev_adj = Sourced.present(
                    f"~{ev / eb_mid:.1f}x (fwd, at current ${price:.2f}; EV ${ev / 1e6:,.0f}M "
                    f"/ {band})",
                    source_ref=f"{src} (adj-EBITDA) + EDGAR net debt + EOD price × shares",
                )
    return adj_eps, ev_adj, nd_adj


# --- CIQ-sourced fields (workbook-addressed; the extractors fail loud MISSING/UNKNOWN) ---------


def _valuation(
    record: DataRecord, bundle: CiqBundle, adj_eps: Sourced[str], adj_ev: Sourced[str],
    *, pe_note: str | None = None,
) -> Valuation:
    f = record.fundamentals
    pe = _sourced(f.pe, source_ref="EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)")
    if pe_note and pe.status is SourceStatus.PRESENT:
        pe = pe.model_copy(update={"note": pe_note})  # carry the distortion caveat ON the value
    # trailing-only blind-flag: a trailing multiple with NO forward counterpart can't tell
    # cheap-overshoot from cheap-terminal — force the synthesis to declare it's flying blind rather
    # than imply trailing-cheap = overshoot.
    ev = ciq_sheets.ev_ebitda_current(bundle)
    if ev.status is SourceStatus.PRESENT and adj_ev.status is not SourceStatus.PRESENT:
        ev = ev.model_copy(update={
            "note": "trailing only — no forward basis; cannot distinguish cheap-overshoot from "
            "cheap-terminal"
        })
    return Valuation(
        cross_sectional=ciq_sheets.cross_sectional_valuation(bundle),
        pe=pe,
        pe_percentile_5y=_sourced(
            f.pe_pctile_vs_history, source_ref="EDGAR/EOD P/E pctile vs ~5y (screen data-record)"
        ),
        # The EDGAR screen field `f.ev_ebitda` carries EBITDA *dollars* (screens/assemble.py
        # populates it from ebitda_annual), not the multiple — so the dossier's EV/EBITDA is the
        # authoritative CIQ TEV/LTM multiple, never the EDGAR scalar (never a dollar figure here).
        ev_ebitda=ev,
        ev_ebitda_percentile_5y=(
            _sourced(f.ev_ebitda_pctile_vs_history, source_ref="EDGAR (screen data-record)")
            if f.ev_ebitda_pctile_vs_history.is_known
            else ciq_sheets.ev_ebitda_percentile(bundle)
        ),
        ev_ebitda_adjusted_fwd=adj_ev,
        adjusted_eps=adj_eps,
        range_position=ciq_sheets.range_position(bundle),
        own_history=ciq_sheets.own_history_bands(bundle),  # (P3) structured bands for the chart
    )


def _net_debt_to_ebitda(
    bundle: CiqBundle, edgar_net_lev: Sourced[float]
) -> tuple[Sourced[float], Sourced[float]]:
    """Net-debt/EBITDA via a DETERMINISTIC source hierarchy — no judge, no manual reconciliation.
    CIQ is the depth-stage authority: its Balance Sheet classifies the scattered instrument debt
    (convertible / notes / short-term / subordinated) that EDGAR XBRL under-captures, so CIQ Net
    Debt ÷ CIQ LTM EBITDA wins outright when present. Else the EDGAR XBRL screen figure as a clearly
    LABELLED breadth fallback (itself fail-loud when its inputs are missing/inconsistent). Returns
    ``(net_debt_to_ebitda, ciq_net_debt)`` — the latter feeds the survival readout."""
    ciq_nd = ciq_sheets.net_debt(bundle)
    ciq_eb = ciq_sheets.ltm_ebitda(bundle)
    if ciq_nd.status is SourceStatus.PRESENT and ciq_eb.status is SourceStatus.PRESENT:
        assert ciq_nd.value is not None and ciq_eb.value is not None
        if ciq_eb.value <= 0:
            return Sourced.unknown(
                note=f"CIQ EBITDA ${ciq_eb.value:,.0f}M <= 0 — ratio meaningless"
            ), ciq_nd
        # bind BOTH periods (the bracket shows whether EBITDA is the LTM column or a stale FY, and
        # whether net debt is the same period) — never a bare 'LTM' label the value may not have.
        nd_p = (ciq_nd.source_ref or "").split("[")[-1].rstrip("]")
        eb_p = (ciq_eb.source_ref or "").split("[")[-1].rstrip("]")
        return Sourced.present(
            round(ciq_nd.value / ciq_eb.value, 1),
            source_ref=(
                f"CIQ Net Debt ${ciq_nd.value:,.0f}M [{nd_p}] ÷ "
                f"CIQ EBITDA ${ciq_eb.value:,.0f}M [{eb_p}]"
            ),
        ), ciq_nd
    if edgar_net_lev.status is SourceStatus.PRESENT:
        # carry the caveat in the SOURCE_REF (shown on a PRESENT fact) — the note is dropped
        # by the renderer for PRESENT, so a note-only caveat would vanish from the dossier.
        caveat = "breadth estimate — may under-capture scattered debt; pull CIQ"
        return edgar_net_lev.model_copy(update={
            "source_ref": f"{edgar_net_lev.source_ref}; {caveat}",
            "note": f"EDGAR XBRL {caveat}",
        }), ciq_nd
    return Sourced.unknown(
        note=f"no CIQ Net Debt/EBITDA; EDGAR {edgar_net_lev.note or 'UNKNOWN'} — pull CIQ"
    ), ciq_nd


def _net_debt_to_ocf(
    ciq_nd: Sourced[float], ciq_ocf: Sourced[float], edgar_net_ocf: Sourced[float]
) -> Sourced[float]:
    """Net-debt/OCF on the SAME CIQ net-debt basis as net-debt/EBITDA (so the two reads can't
    disagree on whether net debt exists): CIQ Net Debt ÷ CIQ operating cash flow when both present,
    else the EDGAR XBRL screen figure as a labelled breadth fallback, else UNKNOWN/'pull CIQ'."""
    if ciq_nd.status is SourceStatus.PRESENT and ciq_ocf.status is SourceStatus.PRESENT:
        assert ciq_nd.value is not None and ciq_ocf.value is not None
        if ciq_ocf.value <= 0:
            return Sourced.unknown(note=f"CIQ OCF ${ciq_ocf.value:,.0f}M <= 0 — ratio meaningless")
        nd_p = (ciq_nd.source_ref or "").split("[")[-1].rstrip("]")
        ocf_p = (ciq_ocf.source_ref or "").split("[")[-1].rstrip("]")
        return Sourced.present(
            round(ciq_nd.value / ciq_ocf.value, 1),
            source_ref=(
                f"CIQ Net Debt ${ciq_nd.value:,.0f}M [{nd_p}] ÷ "
                f"CIQ OCF ${ciq_ocf.value:,.0f}M [{ocf_p}]"
            ),
        )
    if edgar_net_ocf.status is SourceStatus.PRESENT:
        caveat = "breadth estimate — may under-capture scattered debt; pull CIQ"
        return edgar_net_ocf.model_copy(update={
            "source_ref": f"{edgar_net_ocf.source_ref}; {caveat}",
            "note": f"EDGAR XBRL {caveat}",
        })
    return Sourced.unknown(
        note=f"no CIQ Net Debt/OCF; EDGAR {edgar_net_ocf.note or 'UNKNOWN'} — pull CIQ"
    )


def _survival_capacity(
    net_lev: Sourced[float], adj_lev: Sourced[str], fcf_sign: Sourced[float],
    *, net_debt: Sourced[float] | None = None,
) -> Sourced[str]:
    """Solvency as ONE block — net leverage + self-funding (FCF sign). Each leg is present or
    fail-loud UNKNOWN (itself a risk). ``net_debt`` (CIQ, $M) lets a non-formable ratio still report
    the known balance-sheet position — a net-cash name is not a 'solvency risk'. No new data source.
    (H3) The nearest-maturity year is retired here — the month-precision E2 maturity wall (rendered
    in the survival super-section) supersedes the coarse 'nearest maturity wall: YYYY' line."""
    present = SourceStatus.PRESENT
    parts: list[str] = []
    if net_lev.status is present and net_lev.value is not None:
        basis = "CIQ" if "CIQ" in (net_lev.source_ref or "") else "GAAP"
        lev = f"net-debt/EBITDA {net_lev.value:.1f}x ({basis})"
        if net_lev.value < 0:
            lev += " → net cash"
        if adj_lev.status is present and adj_lev.value:
            lev += f"; {adj_lev.value}"
        parts.append(lev)
    elif net_debt is not None and net_debt.status is present and net_debt.value is not None:
        # ratio not formable, but the CIQ balance-sheet position IS known — show it rather than a
        # bare 'solvency risk', which a net-cash name is not.
        nd = net_debt.value
        pos = f"net cash ${-nd:,.0f}M" if nd < 0 else f"net debt ${nd:,.0f}M"
        parts.append(f"{pos} (CIQ); net-debt/EBITDA N/A ({net_lev.note or 'not derivable'})")
    else:
        parts.append(
            f"net-debt/EBITDA UNKNOWN ({net_lev.note or 'not derivable'}) — solvency risk"
        )
    if fcf_sign.status is present and fcf_sign.value is not None:
        parts.append(
            "FCF-positive → self-funding" if fcf_sign.value > 0
            else "FCF-negative → burning cash (cash not derived — a risk)"
        )
    else:
        parts.append("FCF sign UNKNOWN — runway not assessable (a risk)")
    return Sourced.present(
        " | ".join(parts),
        source_ref="CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign "
        "(survival capacity)",
    )


def _quality(
    record: DataRecord, edgar: EdgarClient, bundle: CiqBundle, reference_date: date,
    adj_leverage: Sourced[str], *, fcf: Sourced[float], margin: Sourced[str],
    trajectory: Sourced[str],
) -> Quality:
    """``fcf`` / ``margin`` / ``trajectory`` arrive already resolved against the EDGAR fallback (CIQ
    primary; EDGAR fills only an empty CIQ field) — assembled in :func:`assemble_mechanical`."""
    f = record.fundamentals
    edgar_net_lev = _sourced(
        f.net_leverage, source_ref="EDGAR XBRL net-debt/EBITDA (screen data-record)"
    )
    # CIQ-primary deterministic hierarchy: CIQ Net Debt ÷ CIQ LTM EBITDA wins; EDGAR is the labelled
    # breadth fallback. ``ciq_nd`` (CIQ Net Debt) also feeds the survival readout when a ratio can't
    # form. EDGAR net-debt under-captures scattered debt (the MVST case) — never the shown figure.
    net_lev, ciq_nd = _net_debt_to_ebitda(bundle, edgar_net_lev)
    edgar_net_ocf = _sourced(
        f.net_debt_to_ocf,
        source_ref="EDGAR XBRL net-debt/OCF (screen data-record) — OCF basis, not EBITDA",
    )
    # net-debt/OCF on the SAME CIQ net-debt basis as net-debt/EBITDA, so the two leverage rows can't
    # disagree on whether net debt exists (EDGAR figure is the labelled breadth fallback).
    net_ocf = _net_debt_to_ocf(ciq_nd, ciq_sheets.ltm_ocf(bundle), edgar_net_ocf)
    fcf_sign = _sourced(f.fcf_sign, source_ref="EDGAR XBRL FCF sign (screen data-record)")
    liquidity = ciq_sheets.liquidity_covenant_flags(bundle)
    return Quality(
        fcf_sign=fcf_sign,
        free_cash_flow=fcf,
        margin_trend=margin,
        net_debt_to_ebitda=net_lev,
        net_debt_to_ocf=net_ocf,
        net_debt_to_ebitda_adjusted=adj_leverage,
        survival_capacity=_survival_capacity(
            net_lev, adj_leverage, fcf_sign, net_debt=ciq_nd
        ),
        interest_coverage=ciq_sheets.interest_coverage(bundle),
        share_count_trend=(
            _share_count_trend(edgar, record.identity.cik, reference_date)
            if record.identity.cik
            else Sourced.unknown(note="no CIK")
        ),
        liquidity_covenant_flags=liquidity,
        multi_year_trajectory=trajectory,
        roic_trend=ciq_sheets.roic_trend(bundle),  # (P3) structured ROIC series for the chart
    )


def _concentration(bundle: CiqBundle) -> Concentration:
    return Concentration(
        segments=ciq_sheets.segments(bundle),
        segment_ebitda=ciq_sheets.segment_ebitda(bundle),
        customers=ciq_sheets.customers(bundle),
        geographic=ciq_sheets.geographic(bundle),
    )


def _consensus(bundle: CiqBundle) -> ConsensusContext:
    return ConsensusContext(
        eps_trend=ciq_sheets.eps_revisions(bundle),
        revenue_trend=ciq_sheets.revenue_revisions(bundle),
        revision_history=ciq_sheets.consensus_view(bundle),
        surprise_history=ciq_sheets.surprise_history(bundle),
    )


def _parse_money(s: str | None) -> float | None:
    """The ONE money-string → float parser (comma/$/M-aware, (paren)-negative). Preferred path is
    ALWAYS a structured schema float; this is the SINGLE sanctioned fallback when a rendered string
    must be parsed (DESIGN RULE). The comma-blind regex truncated '$1,101.80M' → 1."""
    if not s:
        return None
    t = s.strip()
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "").replace("$", "").rstrip("Mm ").strip()
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _bs_bridge_coherence(bundle: CiqBundle, implied: ImpliedValuation) -> Sourced[str]:
    """(C3 coherence gate) The Balance-Sheet cash & total debt must reconcile with the
    implied-valuation bridge (a DIFFERENT CIQ sheet). On disagreement, render BOTH with sources + a
    soft caveat — never silently prefer one."""
    bs_cash = ciq_sheets._bs_latest(bundle, "Total Cash & ST Investments")
    bs_debt = ciq_sheets._bs_latest(bundle, "Total Debt")
    # LOAD-BEARING: the STRUCTURED bridge floats (DESIGN RULE — never re-parse the display string).
    # The fallback parses the render string via the shared _parse_money() only for a legacy bridge
    # predating the structured fields (bridge_cash/debt None but the string carries a figure).
    br = implied.bridge.value if implied.bridge.status is SourceStatus.PRESENT else ""

    def _leg(structured: float | None, label: str) -> float | None:
        if structured is not None:
            return structured
        m = re.search(rf"{label} \$([\d,.]+)", br or "")
        return _parse_money(m.group(1)) if m else None

    bc = _leg(implied.bridge_cash, "cash")
    bd = _leg(implied.bridge_debt, "debt")
    src = "CIQ Financials→Balance Sheet vs Comparable Analysis→Implied Valuation"

    def close(a: float | None, b: float | None) -> bool:
        return a is not None and b is not None and abs(a - b) <= max(1.0, abs(b) * 0.05)

    def money(v: float | None) -> str:  # an ABSENT figure is UNKNOWN — never a fabricated $0
        return f"${v:,.0f}M" if v is not None else "UNKNOWN"

    # Each leg (cash / debt) is cross-checkable ONLY when both its figures are present. An absent
    # figure is UNKNOWN — it is never coerced to $0 and never read as a disagreement (fail loud):
    # real CIQ bridges omit a row routinely; "$0" would fabricate a number the source never gave.
    legs = (("cash", bs_cash.value, bc), ("debt", bs_debt.value, bd))
    checkable = [(n, a, b) for n, a, b in legs if a is not None and b is not None]
    if not checkable:
        return Sourced.unknown(note="coherence: BS & bridge cash/debt absent — not cross-checked")
    absent = [n for n, a, b in legs if a is None or b is None]
    tail = f" ({'/'.join(absent)} not cross-checked — absent, not zero)" if absent else ""
    if any(not close(a, b) for _n, a, b in checkable):
        pairs = "; ".join(f"{n} BS {money(a)} vs bridge {money(b)}" for n, a, b in legs)
        return Sourced.present(
            f"CAVEAT — the two CIQ sources DISAGREE: {pairs}; verify which the verdict should "
            "use — neither is silently preferred.",
            source_ref=src,
        )
    pairs = "; ".join(f"{n} BS {money(a)} / bridge {money(b)}" for n, a, b in checkable)
    return Sourced.present(
        f"{pairs} — reconcile with the implied-valuation bridge{tail}.",
        source_ref=src,
    )


def _financial_summary(bundle: CiqBundle, implied: ImpliedValuation) -> FinancialSummary:
    """(C) The Financial-Summary appendix — annual actuals+estimates (C1/C4), trailing-8-Q (C2), the
    balance-sheet posture (C3), and the BS↔bridge coherence gate. Estimate columns inherit the
    catalyst as-of (header > sidecar > floor)."""
    asof = ciq_sheets.estimates_as_of(bundle)
    return FinancialSummary(
        annual=ciq_sheets.financial_summary_annual(bundle, as_of=asof.value),
        quarterly=ciq_sheets.financial_summary_quarterly(bundle),
        balance_sheet=ciq_sheets.balance_sheet_posture(bundle),
        coherence=_bs_bridge_coherence(bundle, implied),
        as_of=asof,
    )


def _leverage_survival(quality: Quality, bundle: CiqBundle) -> LeverageSurvival:
    """(B2) One unified leverage & survival block: the name's CIQ NET-debt/EBITDA + the comps
    TOTAL-debt/EBITDA (name vs peer median) side by side, each basis LABELED — no net-vs-total
    mixing; interest coverage + the survival line reused from Quality (moved, not duplicated); the
    S&P-MI credit-health scores. The old Quality leverage lines render from HERE; a pre-B2
    dossier.json falls back to the Quality lines."""
    return LeverageSurvival(
        net_debt_to_ebitda=quality.net_debt_to_ebitda,
        total_debt_to_ebitda=ciq_sheets.comps_total_debt_ebitda(bundle),
        interest_coverage=quality.interest_coverage,
        survival=quality.survival_capacity,
        credit_health=ciq_sheets.credit_health(bundle),
    )


# (F1) Form 4 non-derivative transaction codes: open-market P (purchase) / S (sale) are the
# positioning SIGNAL; A (grant/award) is surfaced as 'grants'; every other non-open-market code
# (M option exercise, F tax withholding, C conversion, G gift, …) is bucketed as 'other' and
# LABELED — never silently dropped (that would misstate the counts). Counts + dates only.
_OPEN_MARKET_CODES = ("P", "S")


def _form4_codes(http: CachedHttp, cik: str, accession: str) -> list[tuple[str, float]]:
    """The (code, shares) of every non-derivative transaction in ONE Form 4 — parsed from the raw
    ownership XML (never the xsl-styled view). Returns [] when the filing has no non-deriv table
    or its doc can't be fetched (fail-soft per filing; the block still assembles from the rest)."""
    accn = accession.replace("-", "")
    try:
        idx = http.get_json(_INDEX.format(cik=int(pad_cik(cik)), acc=accn), ttl_seconds=None)
    except (HttpError, ValueError):
        return []
    names = [str(it.get("name", "")) for it in idx.get("directory", {}).get("item", [])]
    xmlname = next(
        (n for n in names if n.lower().endswith(".xml") and "ownership" in n.lower()),
        next((n for n in names if n.lower().endswith(".xml")), None),
    )
    if not xmlname:
        return []
    try:
        raw = http.get_text(
            _ARCHIVE.format(cik=int(pad_cik(cik)), acc=accn, doc=xmlname), ttl_seconds=None)
        root = ET.fromstring(raw)
    except (HttpError, ET.ParseError, ValueError):
        return []
    out: list[tuple[str, float]] = []
    for t in root.findall(".//nonDerivativeTransaction"):
        code = (t.findtext(".//transactionCoding/transactionCode") or "").strip()
        sh = t.findtext(".//transactionAmounts/transactionShares/value")
        if code:
            out.append((code, float(sh) if sh else 0.0))
    return out


def _insider_activity(
    edgar: EdgarClient, http: CachedHttp, cik: str | None, reference_date: date
) -> Sourced[str]:
    """(F1) Trailing-6m insider activity from EDGAR Form 4 — open-market P/S counts + net P−S
    shares, routine comp codes (A/M/F) tallied separately, any other code labeled. Counts and dates
    ONLY (no interpretation), source-bound to the latest Form 4 accession; fail-loud UNKNOWN when
    none are on file."""
    if not cik:
        return Sourced.unknown(note="no CIK for Form 4 lookup")
    try:
        filings = edgar.recent_filings(
            cik, forms=("4",), since=reference_date - timedelta(days=182))
    except HttpError as exc:
        return Sourced.unknown(note=f"EDGAR Form 4 fetch failed: {exc}")
    if not filings:
        return Sourced.unknown(note="no Form 4 filings in the trailing 6m")
    counts: dict[str, int] = {}
    net = 0.0
    for f in filings:
        for code, sh in _form4_codes(http, cik, f.accession):
            counts[code] = counts.get(code, 0) + 1
            if code == "P":
                net += sh
            elif code == "S":
                net -= sh
    p, s = counts.get("P", 0), counts.get("S", 0)
    last = max(f.filing_date for f in filings)
    # (H5) PLAIN LABELS, sign-descriptors only (counts + net + dates) — no interpretive language.
    # 'grants' = the A (award/grant) code; option-exercise (M) / tax-withheld (F) / conversions (C)
    # etc. are preserved compactly under 'other' so nothing is silently dropped.
    line = (f"Open-market buys {p} · sells {s} (net {net / 1000:+.1f}K sh) · "
            f"grants {counts.get('A', 0)} · last {last.isoformat()}")
    other = "/".join(
        f"{c}×{n}" for c, n in sorted(counts.items())
        if c not in _OPEN_MARKET_CODES and c != "A" and n
    )
    if other:
        line += f" · other {other}"
    return Sourced.present(
        line, source_ref=f"EDGAR Form 4 (latest {filings[0].accession}; {len(filings)} in 6m)")


def _short_interest(
    finra: CachedHttp, record: DataRecord, reference_date: date, *, shares_out: float | None = None
) -> Sourced[str]:
    """(F2/H5) Latest FINRA settlement short interest, sign-descriptors only: prior → latest with a
    rising/falling trend + FINRA's own Δ%, the % of shares out (EDGAR XBRL count), days-to-cover vs
    the SCREEN 90d ADV, and the latest-4 settlements as a mini-row. No interpretation — a cross-
    reference for the human, never a conclusion; fail-loud UNKNOWN when no settlement is on file."""
    symbol = record.identity.ticker
    try:
        points = short_interest_points(
            finra, symbol, start=reference_date - timedelta(days=120), end=reference_date)
    except (HttpError, FinraLayoutError) as exc:
        return Sourced.unknown(note=f"FINRA short interest unavailable: {exc}")
    if not points:
        return Sourced.unknown(note="no FINRA short-interest settlement in the trailing window")
    latest = points[0]
    prior = points[1] if len(points) > 1 else None
    # (H5) prior → latest with a rising/falling sign-descriptor (a plain comparison, not a verdict)
    if prior is not None:
        trend = ("rising" if latest.shares_short > prior.shares_short
                 else "falling" if latest.shares_short < prior.shares_short else "flat")
        line = f"{prior.shares_short / 1e6:.1f}M → {latest.shares_short / 1e6:.1f}M sh"
        pct = f"{latest.change_percent:+.1f}%, " if latest.change_percent is not None else ""
        line += f" ({pct}{trend})"
    else:
        line = f"{latest.shares_short / 1e6:.1f}M sh"
        if latest.change_percent is not None:
            line += f" ({latest.change_percent:+.1f}%)"
    if shares_out and shares_out > 0:  # (H5) % of shares out, EDGAR XBRL count (omitted if absent)
        line += f" · {latest.shares_short / shares_out * 100:.1f}% of shares out (EDGAR XBRL)"
    adv = record.prices.adv_90d_shares
    if adv.coverage_status is CoverageStatus.PRESENT and adv.value:
        line += f" · DTC {latest.shares_short / adv.value:.1f}d"
        basis = f"DTC = {latest.shares_short:,} short ÷ {adv.value:,.0f} screen 90d ADV"
    else:
        basis = "screen 90d ADV unavailable — DTC omitted"
    # (H5) latest-4 settlements mini-row (dates + shares) — the recent trend, source-bound
    mini = " · ".join(f"{pt.settlement_date} {pt.shares_short / 1e6:.1f}M" for pt in points[:4])
    return Sourced.present(
        f"Short interest (FINRA, settle {latest.settlement_date}): {line} · recent: {mini}",
        source_ref=f"FINRA consolidated short interest (settle {latest.settlement_date}); {basis}")


def _edgar_shares_outstanding(edgar: EdgarClient, cik: str | None) -> float | None:
    """(H5) Latest EDGAR XBRL shares outstanding (dei cover-page, us-gaap fallback), or None when
    absent — the denominator for short interest as a % of shares out (never faked when missing)."""
    facts = _companyfacts_or_none(edgar, cik)
    if not facts:
        return None
    pt = latest_instant(extract_points(facts, "shares"))
    return pt.value if pt else None


def _catalyst_path(
    bundle: CiqBundle,
    reference_date: date,
    *,
    insider_activity: Sourced[str] | None = None,
    short_interest: Sourced[str] | None = None,
) -> CatalystPath:
    """Assemble the horizon-matched estimates/guidance/revision view from the five new Estimates
    sheets. The workbook as-of (freshest embedded data date) is resolved ONCE and threaded into
    every sub-field's source_ref. Each sub-field independently reads UNKNOWN/MISSING when its sheet
    is absent — a FRESH assembly always builds the block; raggedness lives one level down. The (F)
    positioning inputs are assembled upstream (they need EDGAR/FINRA + the record), slotted in."""
    asof = ciq_sheets.estimates_as_of(bundle)
    aod = asof.value
    return CatalystPath(
        as_of=asof,
        horizon_read=ciq_sheets.horizon_read(bundle, as_of=aod),
        acceleration_read=ciq_sheets.acceleration_read(bundle, as_of=aod),
        cross_name_anchor=ciq_sheets.cross_name_anchor(bundle, as_of=aod),
        guidance_bridge=ciq_sheets.guidance_bridge(
            bundle, as_of=aod, reference_date=reference_date, stale_after_days=_STALE_CLOSE_DAYS
        ),
        guidance_bridge_rows=ciq_sheets.guidance_bridge_rows(
            bundle, reference_date=reference_date, stale_after_days=_STALE_CLOSE_DAYS
        ),
        revision_events=ciq_sheets.revision_events(bundle, as_of=aod),
        consensus_stats=ciq_sheets.consensus_stats(bundle, as_of=aod),
        insider_activity=insider_activity,
        short_interest=short_interest,
    )


# --- (catalyst calendar, ratified 2026-07-24) dated events + what each tests ---------------------
# Face-validity constants (never outcome-tuned): a print rhythm needs ≥4 results 8-Ks to call;
# a sane quarterly gap sits in 60..120d (an irregular filer → REFUSE, never guess); maturities
# make the calendar when they fall within ~24 months of the reference date.
_CAL_MIN_PRINTS = 4
_CAL_GAP_DAYS = (60, 120)
_CAL_MATURITY_HORIZON_DAYS = 730


def _next_print_estimate(print_dates: list[date], ref: date) -> tuple[date, str] | None:
    """CADENCE-ESTIMATE of the next results print from the filer's OWN 2.02-8-K history: the
    median inter-print gap (≥ ``_CAL_MIN_PRINTS`` prints, gap within ``_CAL_GAP_DAYS``) rolled
    forward from the last print past ``ref``. None on any doubt — the caller emits a qa_flag and
    NO row (an estimate is labeled; a guess is forbidden)."""
    prints = sorted(set(print_dates))
    if len(prints) < _CAL_MIN_PRINTS:
        return None
    gaps = [(b - a).days for a, b in zip(prints, prints[1:], strict=False)]
    med = statistics.median(gaps)
    if not (_CAL_GAP_DAYS[0] <= med <= _CAL_GAP_DAYS[1]):
        return None  # irregular rhythm — refuse to call it
    step = timedelta(days=round(med))
    est = prints[-1] + step
    while est <= ref:
        est += step
    basis = (f"median {round(med)}d gap over {len(prints)} results 8-Ks; "
             f"last print {prints[-1].isoformat()}")
    return est, basis


# (source D, ratified 2026-07-24) a FORWARD action verb followed within a clause by a month name —
# "will become effective in September", "launching in Q..January 2028". Tight by design (the K6
# precision lesson): past-tense verbs are excluded by the alternation itself ("completed" is not
# "completes|completing"), and a backward reference ("last September") is rejected post-match.
_CAL_MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ("January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"))}
_CAL_FWD_EVENT = re.compile(
    r"\b(?:effective|launch(?:es|ing)?|open(?:s|ing)?|begin(?:s|ning)?|start(?:s|ing)?|"
    r"roll(?:s|ing)?\s+out|ship(?:s|ping)?|transition(?:s|ing)?|commenc(?:es|ing))\b"
    r"[^.]{0,60}?\b(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\b(?:\s+(\d{4}))?",
    re.IGNORECASE)
_CAL_BACKWARD = re.compile(r"\b(?:last|past|earlier|prior|previous|ago)\b", re.IGNORECASE)


def _dated_operating_events(
    od: OperatingDriversExtract | None, reference_date: date,
) -> list[CatalystRow]:
    """(source D) MANAGEMENT-STATED dated operating events mined from the already-extracted
    driver verbatims — a price increase 'effective in September', a launch, a plant opening.
    Month-granular dates render as YYYY-MM (never a fabricated day). Year resolution when
    unstated: the NEXT occurrence of that month on/after the reference month (a stated month is
    forward-looking by construction of the pattern). Past-resolved events are dropped — a
    calendar lists what is ahead. No match → no row, silently (no event stated is a normal
    state, unlike an unreadable DATE, which flags)."""
    if od is None:
        return []
    rows: list[CatalystRow] = []
    seen: set[tuple[str, str]] = set()
    for r in od.rows:
        text = r.verbatim or ""
        for m in _CAL_FWD_EVENT.finditer(text):
            if _CAL_BACKWARD.search(text[max(0, m.start() - 24):m.end()]):
                continue  # "last September" — a backward reference, not a calendar event
            month = _CAL_MONTHS[m.group(1).lower()]
            if m.group(2):
                year = int(m.group(2))
            else:
                year = reference_date.year + (1 if month < reference_date.month else 0)
            stamp = f"{year:04d}-{month:02d}"
            if stamp < reference_date.strftime("%Y-%m"):
                continue  # resolved to the past — not a calendar row
            # the event text: the CLAUSE carrying the match — from the last comma/semicolon
            # before the match (a long sentence's lead-in is throat-clearing, and a blind
            # 120-char cap was cutting the event itself) to the sentence end, condensed
            lo = text.rfind(". ", 0, m.start())
            lo = lo + 2 if lo != -1 else 0
            hi = text.find(". ", m.end())
            hi = hi if hi != -1 else len(text)
            cl = max(text.rfind(",", lo, m.start()), text.rfind(";", lo, m.start()))
            start = cl + 1 if cl != -1 else lo
            clause = " ".join(text[start:hi].split()).lstrip(",; ")
            event = clause if len(clause) <= 120 else clause[:117].rstrip() + "…"
            key = (stamp, clause[:60].lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append(CatalystRow(
                event=event, expected_date=stamp, date_basis="stated",
                tests_what="a management-stated dated operating action — the thesis mechanism "
                           "on a timetable; the following print reads its result",
                source_ref=r.source_ref))
    return rows


def _catalyst_calendar(
    edgar: EdgarClient, cik: str, reference_date: date, mech: MechanicalLayer,
) -> CatalystCalendar:
    """Assemble the DATED catalyst rows — deterministic, source-bound, never weighted:
    A. the next results print (cadence-estimate from the filer's own 2.02 history);
    B. the committed revised-guidance checkpoint enriches the print row (the print TESTS the guide);
    C. in-horizon debt maturities from the capital-structure panel (stated ISO dates).
    Every miss is a loud qa_flag; an empty calendar is an honest outcome."""
    rows: list[CatalystRow] = []
    qa: list[str] = []
    # A + B — the next print, and what it tests
    try:
        filings = edgar.recent_filings(cik, forms=("8-K",))
        prints = [f.filing_date for f in filings if "2.02" in f.items]
    except Exception as exc:  # noqa: BLE001 — a feed miss is a loud flag, never an abort
        prints = []
        qa.append(f"catalyst: submissions feed unavailable ({type(exc).__name__}) — no print row")
    if prints:
        est = _next_print_estimate(prints, reference_date)
        if est is None:
            qa.append(f"catalyst: print cadence unreadable ({len(prints)} results 8-Ks / "
                      "irregular gaps) — no estimated print row (never guessed)")
        else:
            est_date, basis = est
            rg = mech.drawdown_cause.revised_guidance
            if rg.status is SourceStatus.PRESENT and rg.value:
                tests = ("the committed revised outlook (see Revised guidance — the print is the "
                         "checkpoint that confirms or refutes it)")
                src = f"cadence: EDGAR submissions ({basis}) · guide: {rg.source_ref}"
            else:
                tests = "the next reported quarter against the committed trajectory"
                src = f"cadence: EDGAR submissions ({basis})"
            rows.append(CatalystRow(
                event="Next results print", expected_date=est_date.isoformat(),
                date_basis="cadence-estimate", tests_what=tests, source_ref=src))
    # C — in-horizon maturities (stated dates from the capital-structure panel). ``instruments``
    # is Sourced[list[...]] — read the value only when PRESENT (absent panel = no rows, no guess).
    cs = mech.capital_structure
    if (cs is not None and cs.instruments.status is SourceStatus.PRESENT
            and cs.instruments.value):
        horizon = reference_date + timedelta(days=_CAL_MATURITY_HORIZON_DAYS)
        for inst in cs.instruments.value:
            if not inst.maturity_date:
                continue
            try:
                mat = date.fromisoformat(inst.maturity_date)
            except ValueError:
                qa.append(f"catalyst: unparseable maturity {inst.maturity_date!r} "
                          f"on {inst.description!r} — row skipped")
                continue
            if reference_date < mat <= horizon:
                amt = (f"${inst.principal_musd:,.1f}M " if inst.principal_musd is not None else "")
                rows.append(CatalystRow(
                    event=f"{inst.description} {amt}matures".replace("  ", " "),
                    expected_date=mat.isoformat(), date_basis="stated",
                    tests_what="refinance / repay / convert before the wall — the survival read",
                    source_ref="CIQ capital-structure panel (maturity_date)"))
    # D — management-stated dated operating events from the driver verbatims (source D,
    # ratified 2026-07-24; surfaced by SMPL's September price increase)
    rows.extend(_dated_operating_events(mech.operating_drivers, reference_date))
    rows.sort(key=lambda r: r.expected_date)
    return CatalystCalendar(rows=rows, qa_flags=qa)


def _catalyst_stale_flag(catalyst: CatalystPath, reference_date: date) -> str | None:
    """Fire the SHARED staleness caveat (same 45d knob as the EV/EBITDA stale-Close check) when the
    Estimates export's as-of trails the reference date by more than the constant — the revision
    breadth / guidance / consensus below may predate a since-then re-rate. UNKNOWN as-of → no fire
    (fail-quiet on absence; the sub-fields already read MISSING)."""
    aod = catalyst.as_of.value
    if not aod:
        return None
    if "operator-attested" in (catalyst.as_of.note or ""):  # R1: attested date trusted — no caveat
        return None
    if aod.startswith("≥"):  # FLOOR basis — a lower bound on the (un-stamped) export date
        # A floor F is a lower bound on the true export date E: an export cannot embed a revision
        # event dated after itself, so E >= F. Hence worst-case staleness (R - E) <= (R - F). When
        # even that worst case is within tolerance the data is PROVABLY fresh — no caveat (a floor
        # at/after the reference means the export post-dates the screen: fresher still). The floor
        # nature is never hidden: each read keeps its "≥F · export date unverified" suffix. The
        # caveat fires ONLY when the bound cannot rule out staleness.
        floor = date.fromisoformat(aod[1:])
        worst_case_stale = (reference_date - floor).days
        if worst_case_stale <= _STALE_CLOSE_DAYS:
            return None
        return (
            f"Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; "
            f"its data is on/after {aod[1:]} (the latest embedded revision event), so it is up to "
            f"{worst_case_stale}d before the {reference_date.isoformat()} reference — beyond the "
            f"{_STALE_CLOSE_DAYS}d tolerance — and the true export date is unknown, so freshness "
            "cannot be confirmed. Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar)."
        )
    stale_days = (reference_date - date.fromisoformat(aod)).days
    if stale_days <= _STALE_CLOSE_DAYS:
        return None
    return (
        f"Catalyst-path staleness caveat — the CIQ Estimates export is as-of {aod}, {stale_days}d "
        f"before the {reference_date.isoformat()} reference; the revision breadth, guidance bridge "
        "and consensus below may predate a since-then re-rate. Re-pull CIQ Estimates before "
        "relying on the horizon/acceleration reads."
    )


def _iso_or_none(stamp: str | None) -> date | None:
    """A clean ISO date, or None for anything else (a floor ``≥…``, a prose note, empty). The
    freshness gate fires only on a parseable as-of, so an odd stamp fails quiet."""
    if not stamp:
        return None
    try:
        return date.fromisoformat(stamp)
    except ValueError:
        return None


def _latest_earnings_print(edgar: EdgarClient, cik: str) -> date | None:
    """The latest EARNINGS print date on EDGAR — the newest 8-K carrying item 2.02 (Results of
    Operations). Fail-quiet: a submissions-feed miss or a name with no 2.02 on file returns None
    (the caller then raises no freshness caveat, never aborts)."""
    try:
        prints = [f.filing_date for f in edgar.recent_filings(cik, forms=("8-K",))
                  if "2.02" in f.items]
    except Exception:  # noqa: BLE001 — a feed miss silences the gate, never aborts the assembly
        return None
    return max(prints) if prints else None


def _panel_freshness_flag(
    ie: ImpliedExpectations | None, latest_print: date | None,
) -> str | None:
    """Fire a loud caveat when a CIQ valuation panel PREDATES the latest earnings print — the guard
    the SMPL 2026-07-24 stale-inputs incident earned (a recorded BUY read panels dated 2026-06-03 /
    2026-06-25 while the FQ3 print had landed 2026-07-09).

    ORTHOGONAL to the reference-date stale checks (``_catalyst_stale_flag`` / the EV/EBITDA
    stale-Close): those compare a panel's as-of to the REFERENCE date within a 45d tolerance, and a
    panel can sit inside that tolerance yet still predate a PRINT that landed after both the panel
    AND the reference (SMPL's panels were within 45d of its 2026-07-06 reference — the reference
    itself predated the print). ANCHORED — EDGAR item-2.02 filing dates + the panels' own CIQ as-of
    stamps; NO tunable knob (`older than the newest print` is a hard fact, not a face-validity
    band). Fail-quiet: no print, no valuation block, or an unparseable as-of → no caveat."""
    if ie is None or latest_print is None:
        return None
    stale = [(label, d) for label, stamp in (("valuation multiples", ie.multiples_as_of),
                                             ("implied-TEV inputs", ie.tev_as_of))
             if (d := _iso_or_none(stamp)) is not None and d < latest_print]
    if not stale:
        return None
    lag = (latest_print - min(d for _, d in stale)).days
    named = "; ".join(f"{label} as-of {d.isoformat()}" for label, d in stale)
    return (
        f"Panel-freshness caveat — {len(stale)} CIQ valuation panel(s) predate the latest earnings "
        f"print ({latest_print.isoformat()}, EDGAR 8-K item 2.02), the oldest by {lag}d: {named}. "
        "The valuation read may rest on a pre-print P&L — re-pull CIQ after the print before "
        "relying on it."
    )


# --- E1/E3/E4: structured capital structure + maturity-anchored 8-Ks + covenant pointers -----
def _maturity_8ks(
    edgar: EdgarClient, cik: str, instruments: list[CapitalInstrument], reference_date: date
) -> Sourced[str]:
    """(E3) 8-Ks filed within ±10d of any instrument maturity in the TRAILING 12m — where a
    recently-matured facility's resolution would be disclosed. POINTERS only ('read for
    resolution'); never an assumption of repayment or default."""
    mats = sorted({
        date.fromisoformat(i.maturity_date)
        for i in instruments
        if i.maturity_date
        and reference_date - timedelta(days=365)
        <= date.fromisoformat(i.maturity_date) <= reference_date
    })
    if not mats or not cik:
        return Sourced.unknown(note="no trailing-12m instrument maturity to anchor an 8-K")
    try:
        filings = edgar.recent_filings(cik, forms=("8-K",), since=min(mats) - timedelta(days=11))
    except HttpError as exc:
        return Sourced.unknown(note=f"EDGAR 8-K fetch failed: {exc}")
    lines: list[str] = []
    seen: set[str] = set()
    for m in mats:
        for f in sorted(filings, key=lambda f: abs((f.filing_date - m).days)):
            if abs((f.filing_date - m).days) > 10 or f.accession in seen:
                continue
            seen.add(f.accession)
            items = ", ".join(item_labels(list(f.items))) or "—"
            lines.append(
                f"8-K at maturity {m.isoformat()}: filed {f.filing_date.isoformat()} "
                f"[{f.accession}] {items} — read for resolution"
            )
    if not lines:
        dates = ", ".join(m.isoformat() for m in mats)
        return Sourced.unknown(note=f"no 8-K within ±10d of a trailing-12m maturity ({dates})")
    return Sourced.present(
        "; ".join(lines), source_ref="EDGAR 8-K submissions (±10d of instrument maturities)")


# (H1) agreement-class whitelist — only an instrument backed by a DISCRETE contract gets a filing
# lookup; a generic balance-sheet aggregate (Notes Payable, a lease) has no single agreement to
# point at and renders an honest "no contract-level filing expected" note.
_COVENANT_CLASS_RE = re.compile(
    r"\b(loan|credit|facilit|indenture|convertible|agreement|bond)\b", re.IGNORECASE)
# an EXECUTION filing carries the agreement as an EXHIBIT — a material-contract ex-10.x or a
# filename naming the contract; a primary 8-K body ('mvst-20240603.htm') matches none of these.
_AGREEMENT_EXHIBIT_RE = re.compile(
    r"ex-?10\d|loan|credit|facilit|indenture|agreement|secur|pledge|guarant|warrant", re.IGNORECASE)


def _covenant_query(desc: str) -> str:
    """The canonical efts phrase for an instrument's agreement class — the CIQ label ('Convertible
    Loan With Shareholder') rarely matches the filing's contract name ('Loan and Security
    Agreement'), so query the class's standard agreement term instead of the raw label."""
    d = desc.lower()
    if "bond" in d and "loan" not in d:
        return "Indenture"
    if "credit" in d:
        return "Credit Agreement"
    if "facilit" in d and "loan" not in d:
        return "Facility Agreement"
    return "Loan Agreement"  # loan / convertible-loan / default


def _exhibit_names(http: CachedHttp, cik: str, accession: str) -> list[str]:
    """The document filenames in one filing's index.json ([] on any fetch/parse failure)."""
    try:
        idx = http.get_json(
            _INDEX.format(cik=int(pad_cik(cik)), acc=accession.replace("-", "")), ttl_seconds=None)
    except (HttpError, ValueError):
        return []
    return [str(it.get("name", "")) for it in idx.get("directory", {}).get("item", [])]


def _covenant_pointers(
    edgar: EdgarClient, http: CachedHttp, cik: str, instruments: list[CapitalInstrument]
) -> Sourced[list[CovenantPointer]]:
    """(H1) Locate the EXECUTION filing (the 8-K/10-K carrying the agreement as an exhibit) for each
    AGREEMENT-CLASS instrument, SCOPED to the subject CIK. efts full-text is queried with ciks=<CIK>
    AND any cross-CIK hit is rejected (the E4 bug: an unscoped 'Convertible Bond' matched AXESSTEL's
    2005 8-K). A generic BS line (Notes Payable, a lease) gets an honest 'no contract-level filing'
    note. Deduped by accession; the located exhibit filenames feed the fenced E5 extraction."""
    if not cik:
        return Sourced.unknown(note="no CIK for covenant-pointer lookup")
    cik10 = pad_cik(cik)
    rows: list[CovenantPointer] = []
    seen: set[str] = set()

    # (1) latest 10-K material-contract exhibits (ex-10.x) — contracts incorporated by reference
    try:
        tenks = edgar.recent_filings(cik, forms=("10-K",))
        if tenks:
            acc = tenks[0].accession
            exs = [n for n in _exhibit_names(http, cik, acc) if re.search(r"ex-?10\d", n, re.I)]
            if exs:
                rows.append(CovenantPointer(
                    family="material contracts (10-K exhibit index)", filing="latest 10-K",
                    filing_date=tenks[0].filing_date.isoformat(), accession=acc, exhibits=exs))
                seen.add(acc)
    except (HttpError, KeyError, ValueError):
        pass

    # (2) per whitelisted family — efts (ciks-scoped) → keep only EXHIBIT-BEARING execution 8-Ks
    queries: dict[str, str] = {}  # family → canonical efts phrase
    generic: list[str] = []
    for i in instruments:
        fam = i.description.split(" With ")[0].split(" - ")[0].strip()
        if _COVENANT_CLASS_RE.search(i.description):
            queries.setdefault(fam, _covenant_query(i.description))
        elif fam not in generic:
            generic.append(fam)
    for fam, phrase in list(queries.items())[:6]:
        try:
            hits = edgar.fulltext_search(phrase, forms="8-K", ciks=cik10)
        except HttpError:
            continue
        added = 0
        for h in hits:
            if added >= 2:
                break
            # (H1a) DEFENSE-IN-DEPTH cross-CIK guard — reject any hit whose filer CIK ≠ the subject
            if h.cik and pad_cik(h.cik) != cik10:
                continue
            if h.accession in seen:
                continue
            exs = [n for n in _exhibit_names(http, cik, h.accession)
                   if _AGREEMENT_EXHIBIT_RE.search(n)
                   and n.lower().endswith((".htm", ".html", ".txt"))]  # .html: some filers use it
            if not exs:  # a mention-only 8-K (no agreement exhibit) is NOT a pointer
                continue
            seen.add(h.accession)
            rows.append(CovenantPointer(
                family=fam, filing="8-K",
                filing_date=h.file_date.isoformat() if h.file_date else "",
                accession=h.accession, exhibits=exs))
            added += 1

    # (3) generic balance-sheet aggregates — honest "no contract-level filing" note (not a pointer)
    for fam in generic[:4]:
        rows.append(CovenantPointer(
            family=fam, filing="—", filing_date="", accession="", exhibits=[],
            note="no contract-level filing expected (aggregate line item)"))

    if not any(r.accession for r in rows):
        return Sourced.unknown(
            note="no CIK-scoped agreement exhibit located across the filing history")
    return Sourced.present(
        rows,
        source_ref="EDGAR 10-K exhibit index + CIK-scoped efts (agreement-class, exhibit-bearing)")


def _covenant_summary(rows_s: Sourced[list[CovenantPointer]]) -> str:
    """A one-line summary of the located pointers (back-compat covenant_pointers string)."""
    if rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return ""
    located = [f"{r.family[:34]} [{r.accession}]" for r in rows_s.value if r.accession]
    return "; ".join(located) if located else "no contract-level filing located"


def _capital_structure(
    record: DataRecord, edgar: EdgarClient, http: CachedHttp, bundle: CiqBundle,
    reference_date: date,
) -> CapitalStructure:
    """(E1+E3+E4) Assemble the structured capital structure: CIQ instruments + summary aggregates,
    the maturity-anchored 8-Ks, and the covenant exhibit pointers. Covenant TERMS (E5, LLM) are
    filled in the synthesis phase; UNKNOWN here."""
    instruments, summary, detail_as_of = ciq_sheets.capital_structure_ciq(bundle)
    insts = (instruments.value
             if instruments.status is SourceStatus.PRESENT and instruments.value else [])
    cik = record.identity.cik
    pointer_rows = _covenant_pointers(edgar, http, cik or "", insts)
    located = (pointer_rows.status is SourceStatus.PRESENT
               and any(r.accession for r in (pointer_rows.value or [])))
    summary_str = _covenant_summary(pointer_rows)
    pointers_str = (Sourced.present(summary_str, source_ref=pointer_rows.source_ref or "efts")
                    if located and summary_str else
                    Sourced.unknown(note=pointer_rows.note or "no CIK-scoped agreement exhibit"))
    # (E5, fenced) covenant TERMS are LLM-extractable ONLY from a located exhibit; the note is
    # opacity-as-signal — it tells the human whether any exhibit exists to read (a Tier-1 pointer
    # present) or whether the facility is wholly undocumented (extraction impossible, itself a
    # fact).
    terms_note = (
        "(E5) named covenant terms extract in the LLM phase from the located exhibit(s) above"
        if located else "(E5) no covenant exhibit located — nothing to extract named terms from")
    return CapitalStructure(
        instruments=instruments, summary=summary, detail_as_of=detail_as_of,
        maturity_filings=_maturity_8ks(edgar, cik or "", insts, reference_date),
        covenant_pointers=pointers_str, covenant_pointer_rows=pointer_rows,
        covenant_terms=Sourced.unknown(note=terms_note),
    )


# --- (G) implied expectations: price-inverted, multiples-space ----------------------------------
# Every input is an ALREADY-ASSEMBLED Sourced field — these parsers read those assembled values,
# NEVER the workbook (no extraction; that would be an extractor change, out of scope). Deterministic
# arithmetic only: implied_level = TEV ÷ multiple. TEV is DERIVED (mcap + net debt) since it's
# not surfaced as a single field; the same two fields feed a vintage-coherence guard.
_IE_TOL = 0.10  # G5 vintage-coherence tolerance AND (condition b) the net-debt reconciliation band

# THE fixed, declared multiple set (no per-name curation). Each: (label, metric, kind, key). kind
# 'ladder' = the name's OWN NTM forward multiple (catalyst cross_name_anchor); 'peer' = the peer
# median (peer_comps trading_multiples). 'key' locates the number inside that assembled string.
_IE_MULTIPLE_SET: tuple[tuple[str, str, str, str], ...] = (
    ("name NTM TEV/EBITDA", "EBITDA", "ladder", "TEV/EBITDA"),
    ("peer-median NTM TEV/EBITDA", "EBITDA", "peer", "NTM TEV/EBITDA"),
    ("peer-median LTM TEV/EBITDA", "EBITDA", "peer", "TEV/EBITDA"),
    ("name NTM TEV/Rev", "Revenue", "ladder", "TEV/REV"),
    ("peer-median NTM TEV/Rev", "Revenue", "peer", "NTM TEV/Rev"),
    ("peer-median LTM TEV/Rev", "Revenue", "peer", "TEV/Rev"),
)


def _ie_ladder(cna: str | None, period: str, key: str) -> float | None:
    """A forward multiple from the cross_name_anchor ladder ('NTM: … TEV/EBITDA 7.54 …')."""
    if not cna:
        return None
    seg = next((s for s in cna.split(" | ") if s.strip().startswith(period)), None)
    if not seg:
        return None
    mo = re.search(rf"{re.escape(key)}\s+(-?\d+(?:\.\d+)?)", seg)
    return float(mo.group(1)) if mo else None


def _ie_peer_median(tm: str | None, label: str) -> float | None:
    """The peer-median multiple for an EXACT trading_multiples segment label ('NM' → None)."""
    if not tm:
        return None
    for seg in tm.split(";"):
        lab, _, rest = seg.partition(":")
        if lab.strip() == label:
            mo = re.search(r"Median\s+(-?\d+(?:\.\d+)?|NM)", rest)
            return float(mo.group(1)) if (mo and mo.group(1) != "NM") else None
    return None


def _ie_consensus_latest(ar: str | None, period: str, metric: str) -> float | None:
    """The latest consensus level for period+metric from the acceleration_read path string."""
    if not ar:
        return None
    seg = next((s for s in ar.split(" | ") if s.strip().startswith(f"{period} {metric}:")), None)
    mo = re.search(r"(-?\d+(?:\.\d+)?)\s*\(latest\)", seg) if seg else None
    return float(mo.group(1)) if mo else None


def _ie_asof(source_ref: str | None) -> str:
    """The '· as-of YYYY-MM-DD' an extractor stamps on its source_ref (else 'UNKNOWN')."""
    mo = re.search(r"as-of\s+(\d{4}-\d{2}-\d{2})", source_ref or "")
    return mo.group(1) if mo else "UNKNOWN"


def _ie_bridge_net_debt(implied: ImpliedValuation) -> float | None:
    """Net debt implied by the cash/debt bridge (total debt − cash) — condition-b probe. Reads the
    STRUCTURED schema floats (DESIGN RULE); the old thousands-blind regex on the display string
    truncated '$1,101.80M' → 1 and fired a FALSE reconcile caveat. Legacy fallback parses the render
    string via the shared _parse_money() only when a structured field is absent."""
    cash, debt = implied.bridge_cash, implied.bridge_debt
    if (cash is None or debt is None) and implied.bridge.status is SourceStatus.PRESENT:
        br = implied.bridge.value or ""
        if cash is None and (m := re.search(r"cash \$([\d,.]+)", br)):
            cash = _parse_money(m.group(1))
        if debt is None and (m := re.search(r"total debt \$([\d,.]+)", br)):
            debt = _parse_money(m.group(1))
    return debt - cash if (cash is not None and debt is not None) else None


def _implied_expectations(
    peer_comps: PeerComps, catalyst: CatalystPath, implied_val: ImpliedValuation, bundle: CiqBundle
) -> ImpliedExpectations | None:
    """(G) Assemble price-inverted expectations from ALREADY-SOURCED fields. TEV = mcap + net debt
    (simple-TEV basis — the cell is not surfaced and carries a stale second pricing vintage,
    so deriving from Latest-mcap is vintage-coherent). implied_level = TEV ÷ multiple for the fixed
    set. (H7) The EBITDA consensus anchors are the DIRECT Estimates→Trends latest levels (the single
    source of truth), NOT TEV ÷ ladder — the ladder-derived FY26 lives ONLY in the vintage-guard
    line; a G5 residual (FY26 probe) certifies the vintages. Returns None when TEV can't be derived
    (mcap / net debt absent) — the block won't render."""
    mc, grid = implied_val.market_cap, peer_comps.peer_grid
    if (mc.status is not SourceStatus.PRESENT or mc.value is None
            or grid is None or grid.status is not SourceStatus.PRESENT):
        return None
    name_row = next((r for r in (grid.value or []) if getattr(r, "is_name", False)), None)
    if name_row is None or name_row.net_debt is None:
        return None
    market_cap, net_debt = float(mc.value), float(name_row.net_debt)
    tev = market_cap + net_debt
    tev_as_of = _ie_asof(mc.source_ref)
    mult_as_of = (
        (catalyst.as_of.value or "UNKNOWN").lstrip("≥")
        if catalyst.as_of.status is SourceStatus.PRESENT else "UNKNOWN")
    cna = (catalyst.cross_name_anchor.value
           if catalyst.cross_name_anchor.status is SourceStatus.PRESENT else None)
    tm = (peer_comps.trading_multiples.value
          if peer_comps.trading_multiples.status is SourceStatus.PRESENT else None)
    cna_src = catalyst.cross_name_anchor.source_ref or "CIQ Estimates→Multiples"
    tm_src = peer_comps.trading_multiples.source_ref or "CIQ Comparable Analysis→Trading Multiples"

    rows: list[ImpliedExpectationRow] = []
    for label, metric, kind, key in _IE_MULTIPLE_SET:
        mult = _ie_ladder(cna, "NTM", key) if kind == "ladder" else _ie_peer_median(tm, key)
        src = cna_src if kind == "ladder" else tm_src
        if mult is None or mult <= 0:  # NM/negative/absent → UNKNOWN row, never a fake multiple
            note = ("multiple NM/non-positive — no fundamental level implied" if mult is not None
                    else "multiple absent from the assembled comps")
            rows.append(ImpliedExpectationRow(
                label=label, metric=metric, multiple=mult, multiple_source=src,
                implied_level=None, is_identity=(kind == "ladder"), note=note))
        else:
            rows.append(ImpliedExpectationRow(
                label=label, metric=metric, multiple=mult, multiple_source=src,
                implied_level=round(tev / mult, 1), is_identity=(kind == "ladder")))

    # (H7/P8) BOTH the EBITDA and REVENUE consensus anchors are the DIRECT Estimates→Trends latest
    # levels (FY26E/FY27E), the SINGLE SOURCE OF TRUTH — NOT TEV ÷ ladder. The ladder FY26 (a26) is
    # kept ONLY for the G5 vintage-guard probe below (the ladder-derived figure now lives ONLY there
    # for both metrics). The TEV/Rev name-row identity still stands in the table (is_identity row).
    def _anchor(period: str, key: str = "TEV/EBITDA") -> float | None:
        mo = _ie_ladder(cna, period, key)
        return (tev / mo) if (mo and mo > 0) else None  # UNROUNDED; 1dp only at display

    def _direct_anchors(metric: str) -> Sourced[str]:
        vals = [(lab, ciq_sheets.trends_fy_level(bundle, metric=metric, fy_label=fy))
                for lab, fy in (("FY26E", "FY 2026"), ("FY27E", "FY 2027"))]
        if all(v is None for _, v in vals):
            return Sourced.unknown(
                note=f"no direct FY26/FY27 {metric} consensus in Estimates→Trends")
        txt = " · ".join(f"{lab} {(f'${v:.1f}M') if v is not None else 'n/a'}" for lab, v in vals)
        return Sourced.present(
            txt + f" (direct consensus {metric} — CIQ Estimates→Trends latest snapshot)",
            source_ref=f"CIQ Estimates→Trends (FY26/FY27 consensus {metric}, latest snapshot)")

    a26 = _anchor("FY 2026")  # LADDER-derived FY26 — kept ONLY for the G5 vintage-guard probe below
    anchors = _direct_anchors("EBITDA")  # (H7) direct Trends, the single source of truth
    rev_anchors = _direct_anchors("Revenue")  # (P8) direct Trends — ladder only in the guard line

    # (G5) vintage-coherence: derived FY26 (TEV ÷ FY26 forward multiple, UNROUNDED) vs the DIRECT
    # FY26 EBITDA consensus (Estimates→Trends latest — SAME source as the anchors). NTM is not a
    # sourced level, so FY26 — the nearest direct consensus — is the probe; shared-TEV ladder certs.
    direct26 = ciq_sheets.trends_fy_level(bundle, metric="EBITDA", fy_label="FY 2026")
    coherent, pct = True, 0.0
    if direct26 and direct26 > 0 and a26 is not None:
        pct = abs(a26 - direct26) / direct26
        coherent = pct <= _IE_TOL
    # the residual is stated as a DECIMAL fraction, never a percentage — the block carries zero '%'
    # tokens (the value-space fence: nothing here is differenced into a percentage gap).
    if direct26 and a26 is not None:
        coherence_note = (
            f"vintage-coherent: derived FY26 ${a26:.1f}M vs direct consensus ${direct26:.1f}M "
            f"(residual {pct:.3f} ≤ {_IE_TOL:.2f} tolerance)" if coherent else
            f"multiple-pricing vintage differs from TEV as-of — re-pull comps (derived FY26 "
            f"${a26:.1f}M vs direct ${direct26:.1f}M, residual {pct:.3f} > {_IE_TOL:.2f})")
    else:
        coherence_note = "vintage-coherence UNKNOWN — no direct FY26 EBITDA consensus to probe"

    # (condition b) net-debt coherence vs the cash/debt bridge — reconcile or soft-caveat (C3).
    bridge_nd = _ie_bridge_net_debt(implied_val)
    nd_ok = bridge_nd is None or abs(bridge_nd - net_debt) <= _IE_TOL * max(1.0, abs(net_debt))
    tev_src = (
        f"TEV = mcap {market_cap:.1f} + net debt {net_debt:.1f} "
        f"(CIQ Comparable Analysis→Financial Data, Latest, as-of {tev_as_of}) — simple-TEV basis"
        + ("" if nd_ok else f"; ⚠ net-debt {net_debt:.1f} vs bridge {bridge_nd:.1f} — reconcile"))
    return ImpliedExpectations(
        rows=rows, tev=Sourced.present(round(tev, 1), source_ref=tev_src), anchors=anchors,
        rev_anchors=rev_anchors, heterogeneity_gate=implied_val.comparability_gate.value or "",
        tev_as_of=tev_as_of, multiples_as_of=mult_as_of, vintage_coherent=coherent,
        coherence_note=coherence_note, net_debt_reconciled=nd_ok)


_PS_TTL = 24 * 3600  # primary-source fetch cache TTL (seconds)


def _ltm_adj_ebitda(releases: list[ReleaseExtract]) -> float | None:
    """LTM adjusted EBITDA = FY + latest-Q − prior-year-Q, from the release recon values (the parser
    captures the prior-year comparison distinctly, period-labeled). None unless all three periods
    are present — never a partial guess (fail-loud)."""
    vals: dict[str, float] = {}
    for r in releases:
        for rv in r.reconciliation:
            if rv.metric == "adjusted ebitda":
                vals.setdefault(rv.period, rv.value)
    quarters = [p for p in vals if re.fullmatch(r"Q[1-4]\s+20\d\d", p)]
    if not quarters:
        return None
    cur = max(quarters, key=lambda p: (int(p[3:7]), int(p[1])))  # latest (year, quarter)
    yr, qn = int(cur[3:7]), int(cur[1])
    prior, fy = f"Q{qn} {yr - 1}", str(yr - 1)  # prior-year same quarter; the completed FY
    if prior not in vals or fy not in vals:
        return None
    if vals[fy] < vals[cur] or vals[fy] < vals[prior]:
        # A FULL-YEAR below one of its own quarters ⇒ a mis-periodized row (SMPL: a prior-year
        # QUARTER stamped with the bare year '2025' composed LTM = 66.2 − 73.9 + 57.0 = $49.3M →
        # a bogus ~6.6x net-debt/EBITDA in basis_triangulation, beside a real ~$220M LTM) or a
        # pathological quarter mix — refuse (→ 'LTM unavailable'), never a quarter-scale LTM.
        return None
    return round(vals[fy] - vals[prior] + vals[cur], 1)


def _latest_quarter_ocf_positive(facts: dict[str, Any] | None) -> bool | None:
    """Sign of the latest SINGLE-QUARTER operating cash flow (EDGAR) — the first self-funding input.
    Single-quarter = duration ≤ ~100 days (excludes 6/9-month YTD durations). None = unavailable."""
    if not facts:
        return None
    pts = [p for p in extract_points(facts, "operating_cash_flow")
           if p.period_start is not None and (p.period_end - p.period_start).days <= 100]
    return max(pts, key=lambda p: (p.period_end, p.filed)).value > 0 if pts else None


def _latest_balance_date(facts: dict[str, Any] | None) -> date | None:
    """The maturity-wall 'as of' — the most recent instant (balance-sheet) period_end in EDGAR."""
    if not facts:
        return None
    instants = [p.period_end for concept in ("long_term_debt", "debt_current")
                for p in extract_points(facts, concept) if p.is_instant]
    return max(instants) if instants else None


def _fy_reconciliation(releases: list[ReleaseExtract]) -> dict[str, float]:
    """The FULL-YEAR (bare 20YY period) recon values keyed by metric — the margin/revenue inputs."""
    out: dict[str, float] = {}
    for r in releases:
        for rv in r.reconciliation:
            if re.fullmatch(r"20\d\d", rv.period):
                out.setdefault(rv.metric, rv.value)
    return out


def _fy_impairment(releases: list[ReleaseExtract]) -> float | None:
    """The FY one-off impairment amount ($M) — the margin cross-check numerator."""
    for r in releases:
        for oo in r.one_offs:
            if "impair" in oo.description.lower():
                return oo.amount
    return None


def _release_revenue_guide(
    releases: list[ReleaseExtract],
) -> tuple[float | None, float | None, bool]:
    """The most-recent release's revenue guide as (low, high, qualitative) — the cross-source
    comparison for guide verification. Releases are most-recent first; the first with a revenue
    guide wins (a QUALITATIVE-only outlook signals a numeric CIQ guide has no corroboration)."""
    for r in releases:
        for g in r.guidance:
            if g.metric == "revenue":
                return (g.low, g.high, g.qualitative)
    return (None, None, False)


#: Display cap for a qualitative guide's verbatim in the MAIN BODY. The stored text is a 200-char
#: raw extract; the whole of it is not a decision value.
_GUIDE_VERBATIM_CAP = 110


def _current_guide(releases: list[ReleaseExtract]) -> Sourced[str]:
    """(item 1 clause (c)) The guide from the LATEST results filing that carries one.

    THE SPLIT. `_revised_guidance` walks the DRAWDOWN 8-Ks and answers "what did management say in
    the filing that caused the gap" — drawdown-vintage by construction, and correct as built. This
    answers the other question its docstring also claimed: "the verdict-relevant number", i.e. the
    guide that GOVERNS today. The two coincide until guidance is revised after the drawdown, and
    then they diverge — SMPL's bear argued April's guide while the base used July's, both in one
    document, neither labelled.

    Selection is by the release's OWN `filed` date, never by list position and never by parsing the
    accession out of `source_ref`. Absence is ATTRIBUTED, never silent."""
    dated = [r for r in releases if r.guidance and r.filed is not None]
    if not dated:
        undated = [r for r in releases if r.guidance]
        if undated:
            return Sourced.unknown(
                note=f"{len(undated)} release(s) carry a guide but none carries a filing date — "
                     "cannot say which governs")
        return Sourced.unknown(
            note=f"no guide in any of the {len(releases)} parsed release(s)" if releases
                 else "no EX-99.1 release parsed")
    latest = max(dated, key=lambda r: r.filed or date.min)
    filed = latest.filed
    assert filed is not None                            # `dated` filtered on it
    parts = []
    for g in latest.guidance:
        # REVIEW FIX (#254). The first cut printed "metric period: — $M" for BOTH a
        # qualitative guide and a high-only range: it read `low`/`high` and ignored the
        # `qualitative` flag and the `verbatim` text the model already carries. Live on 6 rows
        # across 4 names (AORT, IT, MVST, VITL) — every one of them qualitative — so a
        # reaffirmed-outlook statement rendered as an em-dash with a currency unit stuck to it:
        # a missing NUMBER where the filer made a non-numeric statement, which is a different
        # claim and the wrong one.
        if g.qualitative or (g.low is None and g.high is None):
            # the verbatim is a 200-char raw extract and carries page furniture ("Page 2 of 13 …")
            # on real filings, so cap it for a MAIN-BODY slot. Truncation is MARKED, never silent,
            # and the untruncated text stays in the release record.
            said = " ".join((g.verbatim or "").split())
            if len(said) > _GUIDE_VERBATIM_CAP:
                said = said[:_GUIDE_VERBATIM_CAP].rstrip() + "… (full text in the release record)"
            parts.append(f"{g.metric} {g.period}: {said}" if said
                         else f"{g.metric} {g.period}: qualitative guide, no figure given")
            continue
        if g.low is not None and g.high is not None:
            rng = f"{g.low:,.1f}–{g.high:,.1f}"
        elif g.low is not None:
            rng = f"≥ {g.low:,.1f}"          # a floor is not a point estimate; say which it is
        else:
            rng = f"≤ {g.high:,.1f}"         # was silently dropped — the bound is the whole guide
        parts.append(f"{g.metric} {g.period}: {rng} {g.unit}".strip())
    return Sourced.present(
        "; ".join(parts),
        source_ref=f"{latest.source_ref} (filed {filed.isoformat()})")


# ITEM 18 — the key an underwrite record uses for its typed covenant-basis leverage, under 18a's
# `facts` schema. NO committed record carries it today (the seven hold cash_interest, cash_tax_rate,
# d_and_a, d_and_a_ratio, diluted_shares, ltm_revenue, net_debt, share_growth, burn_to_breakeven),
# so every name currently takes the legacy branch. Named here so the typed branch is reachable the
# day an analyst writes one, rather than requiring a code change then.
COVENANT_LEVERAGE_FACT = "covenant_leverage"


def _covenant_basis(card: Any | None) -> str | None:
    """ITEM 18 — NO FALSE UNKNOWN. What the covenant-basis line may honestly say, given the fund's
    own underwrite record.

    > Any field the dossier would render as UNKNOWN must first be checked against the record.

    Three states, and only the middle one is new:

    * **no record** → None, and the historical "UNKNOWN (not disclosed)" stands. Most names are
      never underwritten; with nothing to contradict it, the line is honest.
    * **record, no typed fact** (every committed record today) → the vintage message. The record
      predates 18a's typed fields, so the basis exists only as V-row prose. UNKNOWN is FALSE here —
      that is the SMPL incident exactly.
    * **record with the typed fact** → render it, source-bound.

    NO PROSE IS READ. The legacy branch is chosen by the ABSENCE of a typed fact, never by
    inspecting the thesis text — a prose reader is out of scope by decision, and it would be the
    display-string parse this repo forbids besides."""
    if card is None:
        return None
    fact = (getattr(card, "facts", None) or {}).get(COVENANT_LEVERAGE_FACT)
    if fact is None:
        return primary_source.COVENANT_BASIS_NO_STRUCTURED_SOURCE
    return f"{fact.value:g}{fact.unit} ({fact.basis})"


def _primary_source(
    record: DataRecord, edgar: EdgarClient, http: CachedHttp,
    bundle: CiqBundle, reference_date: date, mech: MechanicalLayer,
    card: Any | None = None,
) -> tuple[PrimarySource, float, OperatingDriversExtract]:
    """(RC-1 C) Fetch the primary-source filings (recent 8-K EX-99.1 releases + the latest 10-Q),
    parse them, and run the four cross-source derivations over them + the CIQ/EDGAR mechanical
    layer. RESILIENT TO SOURCE MISSES: any fetch/parse miss becomes an honest UNKNOWN line + a QA
    flag — a missing source never aborts the assembly.

    **ONE DELIBERATE ABORT (item 18), and it is NOT a source miss.** If the underwrite record holds
    a typed covenant fact and this function would still emit ``covenant basis: UNKNOWN``, it RAISES.
    The resilience rule exists so an ABSENT source degrades to an honest UNKNOWN; it is not licence
    to ship a DISHONEST one. Bare ``ValueError`` on purpose — ``DossierAssemblyError`` lives in
    ``assemble.py``, which imports this module, so raising it here would cycle; ``assemble_cohort``
    collects either as a per-name error and the cohort continues.

    Also assembles the (PR-B) operating-driver rows over the SAME already-fetched text
    (A1 releases + A2 10-Q MD&A) plus CIQ Key Developments (A3) — zero extra I/O. Returns
    (PrimarySource, fetch-latency seconds, OperatingDriversExtract)."""
    t0 = time.perf_counter()
    cik = record.identity.cik
    qa: list[str] = []
    releases: list[ReleaseExtract] = []
    filing: FilingSectionExtract | None = None
    filing_as_of: date | None = None  # the parsed 10-Q's period end — the maturity-wall 'as of'
    # (PR-B) operating-driver rows accumulate over the same fetched text; a per-source miss flags.
    driver_rows: list[OperatingDriver] = []
    driver_qa: list[str] = []
    saw_release = saw_10q = False
    # (1) recent 8-K EX-99.1 earnings/event releases (one failing exhibit never drops the rest) -
    if cik:
        try:
            for f in edgar.recent_filings(cik, forms=("8-K",))[:10]:
                if not (set(f.items) & {"2.02", "8.01"}):
                    continue
                try:
                    urls = release_parse.exhibit_991_urls(http, cik, f.accession)
                    if not urls:
                        # DISCLOSE the empty read. An 8-K carrying item 2.02/8.01 almost always
                        # furnishes a press release, so finding none is a detection miss far more
                        # often than a filing that truly has none — and a silent zero here reads
                        # downstream as "this company said nothing", which is a different claim.
                        qa.append(f"primary-source: 8-K {f.accession} carries "
                                  f"{'/'.join(sorted(set(f.items) & {'2.02', '8.01'}))} but no "
                                  f"EX-99.1 exhibit was found")
                    for url in urls:
                        txt = normalize_text(html_to_text(http.get_text(url, ttl_seconds=_PS_TTL)))
                        src = f"8-K {f.accession} EX-99.1"
                        rel = release_parse.parse_release(txt, source_ref=src)
                        # the filing's own date, so a consumer can pick the FRESHEST guide
                        # without parsing the accession out of source_ref
                        releases.append(rel.model_copy(update={"filed": f.filing_date}))
                        saw_release = True
                        driver_rows += release_parse.operating_drivers(txt, source_ref=src)  # A1
                except Exception as exc:
                    qa.append(f"primary-source: EX-99.1 fetch/parse failed for 8-K {f.accession} "
                              f"({type(exc).__name__})")
        except Exception as exc:
            qa.append(f"primary-source: 8-K enumeration failed ({type(exc).__name__})")
    # (2) latest 10-Q filing sections ------------------------------------------------------------
    if cik:
        try:
            qs = edgar.recent_filings(cik, forms=("10-Q",))
            if qs and qs[0].primary_doc:
                url = filing_sections.filing_url(cik, qs[0].accession, qs[0].primary_doc)
                txt = normalize_text(html_to_text(http.get_text(url, ttl_seconds=_PS_TTL)))
                src = f"10-Q {qs[0].accession}"
                filing = filing_sections.parse_filing_sections(txt, source_ref=src)
                filing_as_of = qs[0].report_date  # the maturity-wall 'as of' — panel window base
                saw_10q = True
                driver_rows += filing_sections.results_attribution(txt, source_ref=src)  # A2
        except Exception as exc:
            qa.append(f"primary-source: latest 10-Q fetch/parse failed ({type(exc).__name__})")
    driver_rows += ciq_sheets.key_development_drivers(bundle)  # A3 (CIQ Key Developments)
    # per-source honest-miss flags (a fetched source that yielded no driver row) — never a fake row
    if saw_release and not any(r.source_ref.startswith("8-K") for r in driver_rows):
        driver_qa.append("operating-drivers: no anchored pattern matched — EX-99.1 pricing/KPI")
    if saw_10q and not any(r.source_ref.startswith("10-Q") for r in driver_rows):
        driver_qa.append("operating-drivers: no anchored pattern matched — 10-Q MD&A attribution")
    if not driver_rows:
        driver_qa.append("operating-drivers: no rows extracted (releases/10-Q/KD all missed)")
    op_drivers = OperatingDriversExtract(rows=driver_rows, qa_flags=driver_qa)
    latency = time.perf_counter() - t0
    facts = _companyfacts_or_none(edgar, cik)
    # (3) derivations over structured inputs (never re-parsing a display string) -----------------
    fcf = ciq_sheets.free_cash_flow(bundle)
    fcf_sign = fcf.value > 0 if fcf.value is not None else None
    self_fund = primary_source.self_funding(_latest_quarter_ocf_positive(facts), fcf_sign)
    # wall coherence — filing ≤12m vs CIQ panel same-window, tranche-matched, exclusive boundary.
    # Balance = the 10-Q's OWN period end (the wall's 'as of'), NOT the latest companyfacts instant
    # (which can be a later 10-K, shifting the window and dropping the 41.7M convertible bond).
    balance = filing_as_of or _latest_balance_date(facts)
    cs_layer = mech.capital_structure
    instruments = (cs_layer.instruments.value
                   if cs_layer is not None and cs_layer.instruments.value is not None else [])
    panel = [primary_source.PanelInstrument(
                i.description, i.principal_musd,
                date.fromisoformat(i.maturity_date) if i.maturity_date else None)
             for i in instruments]
    wall_qa: list[str] = []
    mw = filing.maturity_wall if filing is not None else None
    if balance is not None:
        filing_conv = next((t.amount for t in (mw.tranches if mw else [])
                            if "convert" in t.name.lower()), None)
        wall_line, wall_qa = primary_source.wall_coherence(
            mw.within_12m_total if mw else None, panel, balance=balance,
            filing_convertible=filing_conv,
            panel_convertible_principal=primary_source.panel_convertible_principal(panel, balance))
    else:
        wall_line = "wall coherence: UNKNOWN — no EDGAR balance-sheet date"
    qa += wall_qa
    # basis triangulation — each leverage row basis-labeled; FY margins from the release
    nde = mech.leverage_survival.net_debt_to_ebitda if mech.leverage_survival is not None else None
    tde = ciq_sheets.comps_total_debt_ebitda_value(bundle)
    net_debt = ciq_sheets.net_debt(bundle)
    fy = _fy_reconciliation(releases)
    tri = primary_source.basis_triangulation(
        f"{nde.value}x" if nde is not None and nde.status is SourceStatus.PRESENT else None,
        f"{tde.value}x" if tde.status is SourceStatus.PRESENT else None,
        net_debt.value if net_debt.status is SourceStatus.PRESENT else None,
        _ltm_adj_ebitda(releases),
        gaap_gross_margin=fy.get("gross margin"), impairment=_fy_impairment(releases),
        revenue=fy.get("revenue"), covenant_basis=_covenant_basis(card))
    # ITEM 18's RED, as a coherence assertion rather than a hope. It can only fire if this wiring
    # breaks — a typed fact present while the rendered line still claims ignorance of it. That is
    # the false UNKNOWN, and a build that would print one must fail rather than ship the page.
    if (card is not None
            and (getattr(card, "facts", None) or {}).get(COVENANT_LEVERAGE_FACT) is not None
            and f"covenant basis: {primary_source.COVENANT_BASIS_UNKNOWN}" in tri):
        raise ValueError(
            f"{record.identity.ticker}: the underwrite record holds a typed "
            f"{COVENANT_LEVERAGE_FACT} fact and the dossier would still render "
            f"'covenant basis: {primary_source.COVENANT_BASIS_UNKNOWN}' — a FALSE UNKNOWN "
            "(item 18). Refusing the build: a gap invites a look, an UNKNOWN closes the question.")
    # guide verification — CIQ revenue guide (point OR range) vs the release guide + prior-FY actual
    ciq_lo, ciq_hi = ciq_sheets.revenue_guide_lohi(bundle, reference_date=reference_date)
    rel_lo, rel_hi, rel_qual = _release_revenue_guide(releases)
    guide = primary_source.guide_verification(
        "revenue", ciq_lo, ciq_hi,
        prior_fy_actual=fy.get("revenue"), release_qualitative=rel_qual,
        release_low=rel_lo, release_high=rel_hi)
    ps = PrimarySource(
        releases=releases, filing=filing,
        self_funding=Sourced.present(
            self_fund, source_ref="EDGAR latest-Q OCF sign + CIQ LTM FCF sign"),
        wall_coherence=Sourced.present(
            wall_line, source_ref="10-Q maturity wall vs CIQ capital panel (same window)"),
        basis_triangulation=Sourced.present(
            tri, source_ref="CIQ leverage bases + release LTM adj-EBITDA/margins"),
        guide_verification=Sourced.present(
            guide, source_ref="CIQ revenue guide vs release actual/outlook"),
        current_guide=_current_guide(releases),
        qa_flags=qa)
    return ps, latency, op_drivers


_ASSEMBLY_PRICE_STALE_DAYS = 7  # one weekly refresh cadence + a weekend; older ⇒ refresh was missed


def _price_stale_note(last_close: date | None, today: date) -> str | None:
    """Fail-loud staleness at ASSEMBLY time (vs today, not the reference date): an as-of document
    may legitimately trail the screen date, but a CMP printed from a close older than one refresh
    cadence silently misleads. Returns the caveat text, or None when fresh/unknowable."""
    if last_close is None:
        return None
    gap = (today - last_close).days
    if gap <= _ASSEMBLY_PRICE_STALE_DAYS:
        return None
    return (
        f"PRICE STALE AT ASSEMBLY: last stored close {last_close} is {gap} calendar days before "
        f"assembly — run `vinci refresh` before assembling"
    )


def _stock_info(
    record: DataRecord, store: Store, edgar: EdgarClient, bundle: CiqBundle,
    reference_date: date, market_cap: Sourced[float], *, today: date | None = None,
) -> StockInfo:
    """(Phase-2) The market-data 'stock info' box: CMP + 52-week range (EOD price features), shares
    outstanding (EDGAR XBRL), book value/share + market cap (CIQ). Each value is source-bound; a
    missing source stays UNKNOWN — never fabricated. Assemble/inform only: no gate, no conclusion.
    The 52-week high/low defer to UNKNOWN without ~a year of bars (the price-features rule)."""
    bars = store.get_price_history(record.identity.internal_id)
    cap_val = market_cap.value if market_cap.status is SourceStatus.PRESENT else None
    feats = compute_price_features(
        bars, reference_date=reference_date,
        staleness_days=get_config().price_staleness_days, market_cap=cap_val)
    sym = record.identity.eod_symbol
    shares = _edgar_shares_outstanding(edgar, record.identity.cik)
    price = _sourced(feats.last, source_ref=f"EOD {sym} last close")
    stale = _price_stale_note(feats.last.as_of, today or date.today())
    if stale and price.status is SourceStatus.PRESENT:
        price = price.model_copy(update={"note": stale})
    return StockInfo(
        price=price,
        high_52w=_sourced(feats.high_52w, source_ref=f"EOD {sym} 52-week high"),
        low_52w=_sourced(feats.low_52w, source_ref=f"EOD {sym} 52-week low"),
        shares_out=(
            Sourced.present(float(shares), source_ref="EDGAR XBRL shares outstanding")
            if shares and shares > 0
            else Sourced.unknown(note="no EDGAR XBRL share count")),
        book_value_ps=ciq_sheets.book_value_per_share(bundle),
        market_cap=market_cap,
        as_of=feats.last.as_of,
    )


def assemble_mechanical(
    record: DataRecord,
    *,
    store: Store,
    edgar: EdgarClient,
    http: CachedHttp,
    finra: CachedHttp,
    graph: ExposureGraph,
    resolver: EntityResolver,
    bundle: CiqBundle,
    reference_date: date,
    screen_cap_usd: float | None = None,
    card: Any | None = None,
) -> tuple[MechanicalLayer, list[str]]:
    """Assemble the source-bound mechanical layer (no LLM) + any flags for human review (e.g. a
    distorted-P/E-basis warning). No conclusions. ``screen_cap_usd`` is the ranker's frozen
    screen-time cap — the benchmark-band fallback when the CIQ cap is absent (see below)."""
    # the catalyst 8-K's 99.1 (revised guidance) is fetched first: its adjusted EBITDA/EPS feed the
    # adjusted-basis multiples + leverage, which in turn RESOLVE the GAAP-only caveats below.
    drawdown = _drawdown_cause(record, edgar, http)
    adj_eps, adj_ev, adj_lev = _adjusted_facts(record, edgar, drawdown.revised_guidance)
    pe_recon = _pe_reconciliation(record, edgar, bundle, drawdown.revised_guidance)
    # EDGAR fundamentals fallback: when the CIQ Financials subsheets are present-but-empty while CIQ
    # multiples ARE populated, fill free_cash_flow / margin_trend / multi_year_trajectory from EDGAR
    # XBRL. The "multiples present" signal is Financials→Multiples OR the comps Trading Multiples —
    # either proves the workbook is pulled (both read PRESENT for AORT). CIQ multiples stay primary;
    # a PRESENT CIQ field is never overridden (_prefer_ciq).
    peer_comps = ciq_sheets.peer_comps(bundle)
    key_ratios = ciq_sheets.key_ratios(bundle)  # (Phase-2) CIQ Ratios panel: RoE/RoCE/D:E/dividend
    return_ratios = ciq_sheets.return_ratios(bundle)  # (Phase-4) same panel, per-period
    ciq_fcf = ciq_sheets.free_cash_flow(bundle)
    ciq_margin = ciq_sheets.margin_trend(bundle)
    ciq_traj = ciq_sheets.multi_year_trajectory(bundle)
    edgar_fb = edgar_fundamentals.build_fallback(
        multiples=[ciq_sheets.ev_ebitda_current(bundle), peer_comps.trading_multiples],
        ciq_fundamentals=[ciq_fcf, ciq_margin, ciq_traj],
        facts_fn=lambda: _companyfacts_or_none(edgar, record.identity.cik),
    )
    fcf = _prefer_ciq(ciq_fcf, edgar_fb.free_cash_flow() if edgar_fb else None)
    margin = _prefer_ciq(ciq_margin, edgar_fb.margin_trend() if edgar_fb else None)
    trajectory = _prefer_ciq(ciq_traj, edgar_fb.multi_year_trajectory() if edgar_fb else None)
    # Flag the cross-source comparison ONLY when an EDGAR field reached the dossier (CIQ was
    # empty for it). Keying on the RESOLVED fields — not "EDGAR could supply" — avoids a false basis
    # warning when CIQ won every field. fundamental_deltas only (trading_multiples is CIQ-vs-CIQ).
    edgar_used = any(
        (s.source_ref or "").startswith("EDGAR XBRL companyfacts")
        for s in (fcf, margin, trajectory)
    )
    if edgar_used:
        peer_comps = edgar_fundamentals.flag_deltas_basis(peer_comps)
    quality = _quality(
        record, edgar, bundle, reference_date, adj_lev,
        fcf=fcf, margin=margin, trajectory=trajectory,
    )
    implied_val = ciq_sheets.implied_valuation(bundle, peer_comps.comparability)
    # cap-band benchmark for the dossier surface (exhibit + 180d relative) — the monitor's policy
    # applied at the reference date's CIQ cap; one yardstick across both consumers below.
    bench, bench_basis = _resolve_benchmark(
        implied_val.market_cap, reference_date, screen_cap_usd=screen_cap_usd)
    today = date.today()  # assembly instant — the staleness guard compares the store against NOW
    # (F) positioning inputs slotted into the catalyst path — free DATED feeds: EDGAR Form 4 insider
    # activity + FINRA short interest (DTC vs the screen ADV). Counts/shares/dates only.
    catalyst = _catalyst_path(
        bundle, reference_date,
        insider_activity=_insider_activity(edgar, http, record.identity.cik, reference_date),
        short_interest=_short_interest(
            finra, record, reference_date,
            shares_out=_edgar_shares_outstanding(edgar, record.identity.cik)),
    )
    valuation = _valuation(
        record, bundle, adj_eps, adj_ev, pe_note=pe_recon[1] if pe_recon else None)
    # (G) price-inverted expectations (multiples-space) attach to Valuation. Built from already-
    # assembled fields only (peer multiples + the forward ladder + the derived TEV) — no extraction.
    valuation = valuation.model_copy(
        update={"implied_expectations":
                _implied_expectations(peer_comps, catalyst, implied_val, bundle)})
    mech = MechanicalLayer(
        valuation=valuation,
        quality=quality,
        concentration=_concentration(bundle),
        peer_comps=peer_comps,
        drawdown_cause=drawdown,
        idiosyncratic_vs_shared=_idiosyncratic_vs_shared(
            record, store, graph, resolver, reference_date,
            bench=bench, bench_basis=bench_basis,
        ),
        consensus_context=_consensus(bundle),
        catalyst_path=catalyst,
        # B2 unified leverage & survival (both bases + credit health) + B3 CIQ implied valuation
        # (posed; the comparability gate from peer_comps renders on its header).
        leverage_survival=_leverage_survival(quality, bundle),
        implied_valuation=implied_val,
        # C — Financial-Summary appendix (actuals + consensus), reconciled vs the implied bridge.
        financial_summary=_financial_summary(bundle, implied_val),
        # E — structured capital structure (instruments + summary + maturity 8-Ks + pointers).
        capital_structure=_capital_structure(record, edgar, http, bundle, reference_date),
        management_commentary=ciq_sheets.management_commentary(bundle),
        key_ratios=key_ratios,  # (Phase-2) the Motilal-style CIQ Ratios panel
        return_ratios=return_ratios,  # (Phase-4) per-period return-ratio series (chart + table)
        stock_info=_stock_info(  # (Phase-2) CMP + 52wk range + shares + book value + cap
            record, store, edgar, bundle, reference_date, implied_val.market_cap, today=today),
        # (Brief) 52-week rebased price path — name vs the cap-band benchmark (the idio closes).
        stock_performance=_stock_performance(
            record.identity, store, reference_date, bench=bench),
    )
    # (RC-1 C) primary-source layer — fetch 8-K EX-99.1 releases + the latest 10-Q, parse, and run
    # the four cross-source derivations over them + this mechanical layer. Resilient: a fetch/parse
    # miss becomes an UNKNOWN line + QA flag, never an abort. Attached via model_copy (frozen).
    primary, ps_latency, op_drivers = _primary_source(
        record, edgar, http, bundle, reference_date, mech, card)
    mech = mech.model_copy(update={
        "primary_source": primary, "operating_drivers": op_drivers})  # (PR-B) mechanism tier
    mech = _enrich_drawdown_drivers(mech, primary)  # (B1) gap-downs → parsed EX-99.1 drivers
    # (catalyst calendar) dated events + what each tests — needs drawdown_cause (the guide) and
    # capital_structure (maturities), both on mech by now; its misses ride the QA channel.
    calendar = _catalyst_calendar(edgar, record.identity.cik, reference_date, mech)
    mech = mech.model_copy(update={"catalyst_calendar": calendar})
    flags: list[str] = list(primary.qa_flags)
    flags += guidance_refusal_flags(primary.releases)
    flags += op_drivers.qa_flags  # (PR-B) operating-driver per-source honest-miss flags → QA
    flags += calendar.qa_flags  # (catalyst calendar) cadence/maturity honest-miss flags → QA
    si_asof = mech.stock_info.as_of if mech.stock_info is not None else None
    if (stale := _price_stale_note(si_asof, today)) is not None:
        flags.append(f"stock-info: {stale}")  # loud twin of the CMP-row note — machine-visible
    flags.append(f"primary-source: {len(primary.releases)} EX-99.1 release(s) + "
                 f"{'1' if primary.filing is not None else '0'} 10-Q parsed "
                 f"(+{ps_latency:.1f}s fetch)")
    if pe_recon is not None:
        flags.append(pe_recon[0])
    flags += _eps_caveat_flags(
        record, bundle, eps_resolved=adj_eps.status is SourceStatus.PRESENT,
        ltm_gaap_eps=_ltm_gaap_eps(mech.financial_summary))
    # the reported-leverage caveat is an open warning only while the covenant basis isn't shown;
    # reads the RESOLVED ratio so the flag can't quote a different number than the field shows
    if adj_lev.status is not SourceStatus.PRESENT and (
        lev := _leverage_basis_flag(mech.quality.net_debt_to_ebitda)
    ):
        flags.append(lev)
    # data-integrity check on the name's current EV/EBITDA: a stale Financials Close (predates the
    # reference date, so its "current" multiple + own-history range are stale) and/or a material gap
    # vs the current comps figure — flag so the human verifies rather than trusting one silently.
    if (ev_flag := _ev_ebitda_integrity_flag(bundle, reference_date)) is not None:
        flags.append(ev_flag)
    # catalyst-path staleness: the Estimates export's as-of vs the reference date (shared 45d knob).
    if mech.catalyst_path is not None and (
        cat_flag := _catalyst_stale_flag(mech.catalyst_path, reference_date)
    ):
        flags.append(cat_flag)
    # panel-freshness (the SMPL 2026-07-24 incident guard): a CIQ valuation panel that predates the
    # latest EARNINGS PRINT — orthogonal to the reference-date staleness above (a panel can sit
    # within the 45d reference tolerance yet still predate a print that landed after both).
    if (fresh_flag := _panel_freshness_flag(
        mech.valuation.implied_expectations if mech.valuation is not None else None,
        _latest_earnings_print(edgar, record.identity.cik),
    )) is not None:
        flags.append(fresh_flag)
    return mech, flags
