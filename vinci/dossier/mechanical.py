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
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Any, TypeVar

from vinci.dossier import ciq_sheets, edgar_fundamentals
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import (
    CapitalInstrument,
    CapitalStructure,
    CatalystPath,
    CohortMember,
    Concentration,
    ConsensusContext,
    DrawdownCause,
    FilingRef,
    FinancialSummary,
    IdiosyncraticVsShared,
    ImpliedExpectationRow,
    ImpliedExpectations,
    ImpliedValuation,
    LeverageSurvival,
    MechanicalLayer,
    PeerComps,
    Quality,
    Sourced,
    SourceStatus,
    Valuation,
)
from vinci.edgar.client import EdgarClient
from vinci.edgar.concepts import extract_points
from vinci.finra import FinraLayoutError, short_interest_points
from vinci.graph.exposure import ExposureGraph
from vinci.graph.filings import html_to_text
from vinci.netcache import CachedHttp, HttpError
from vinci.resolver import EntityResolver, ResolutionError
from vinci.resolver.index import pad_cik
from vinci.schemas.data_record import DataRecord
from vinci.schemas.envelope import CoverageStatus, DataField
from vinci.schemas.market import PriceBar
from vinci.store import Store

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


def _gap_label(items: list[str]) -> str:
    """A short cause label for one gap-down from its 8-K items. Never "earnings" without 2.02."""
    labels = [_CAUSE_BY_ITEM[c] for c in items if c in _CAUSE_BY_ITEM]
    return " + ".join(labels) if labels else f"non-narrative items {items}"


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
        out.append(f"only non-narrative items {items} — read filing {accession} by hand")
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
            )
        )
    return refs


_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
_EX991 = re.compile(r"ex\W*99\W*d?\W*1(?!\d)", re.I)  # Ex-99.1: dex991/ex-99.1/ex99d1 (not 99.2)
_GUIDANCE_ANCHOR = re.compile(r"revis\w*[^.]{0,80}?(?:full[- ]year|outlook|guidance)", re.I)
_MONEY = re.compile(r"\$\s?\d")
_METRIC = re.compile(r"\b(revenue|ebitda|eps|free cash flow|earnings per share)\b", re.I)


def _is_ex991(name: str) -> bool:
    low = name.lower()
    return low.endswith((".htm", ".html", ".txt")) and _EX991.search(low) is not None


def _exhibit_991_url(http: CachedHttp, cik: str, accession: str) -> str | None:
    """The furnished Exhibit 99.1 (press release) URL from the filing index, or None if absent."""
    acc = accession.replace("-", "")
    try:
        idx = http.get_json(_INDEX.format(cik=int(pad_cik(cik)), acc=acc), ttl_seconds=None)
    except (HttpError, ValueError):
        return None
    for item in idx.get("directory", {}).get("item", []):
        name = str(item.get("name", ""))
        if _is_ex991(name):
            return _ARCHIVE.format(cik=int(pad_cik(cik)), acc=acc, doc=name)
    return None


def _extract_revised_guidance(text: str) -> str | None:
    """The REVISED full-year outlook block (figures verbatim) from a 99.1 press release. Anchored on
    'revis…(full-year|outlook|guidance)' so it surfaces the *revised* outlook, not an initial one.
    Verbatim — the figures are read from the primary source, never parsed into numbers here (no
    mis-extraction). Returns None when no revised-outlook section exists (→ UNKNOWN upstream)."""
    for m in _GUIDANCE_ANCHOR.finditer(text):  # skip the lede; take the anchor whose window has the
        window = " ".join(text[m.start() : m.start() + 800].split())  # the figures window
        if len(_MONEY.findall(window)) >= 2 and _METRIC.search(window):
            return window
    return None


def _revised_guidance(http: CachedHttp, cik: str, filings: list[FilingRef]) -> Sourced[str]:
    """Follow the furnished 99.1 exhibit on the drawdown 8-Ks (the body only *points* to it) and
    surface the company's revised full-year guidance — the verdict-relevant number. Source-bound to
    the exhibit; fail loud UNKNOWN with the accession(s) when no revised-outlook exhibit parses."""
    tried: list[str] = []
    for f in filings:
        if not ({"2.02", "7.01", "8.01"} & set(f.items)):  # press releases live under these items
            continue
        tried.append(f.accession)
        url = _exhibit_991_url(http, cik, f.accession)
        if url is None:
            continue
        try:
            block = _extract_revised_guidance(html_to_text(http.get_text(url, ttl_seconds=None)))
        except HttpError:
            continue
        if block:
            ref = f"EDGAR 8-K {f.accession} Ex-99.1 — {url}"
            return Sourced.present(block, source_ref=ref)
    if tried:
        return Sourced.unknown(note=f"no revised-outlook 99.1 exhibit parsed for 8-Ks {tried}")
    return Sourced.unknown(note="no results/Reg-FD/other-event 8-K at the gap-downs with a 99.1")


def _drawdown_cause(record: DataRecord, edgar: EdgarClient, http: CachedHttp) -> DrawdownCause:
    gaps = sorted(e.event_date for e in record.events if e.event_type.value == "earnings_gap_down")
    cik = record.identity.cik
    filings = _drawdown_filings(edgar, http, cik, gaps) if cik else []
    by_gap = {f.gap_date: f for f in filings}
    if gaps:
        parts = [
            f"{gd.isoformat()} {_gap_label(by_gap[gd.isoformat()].items)}"
            if gd.isoformat() in by_gap
            else f"{gd.isoformat()} no 8-K matched"
            for gd in gaps
        ]
        shape = Sourced.present(
            "discrete gap-downs by 8-K item code — " + "; ".join(parts),
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
    )


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


def _idiosyncratic_vs_shared(
    record: DataRecord, store: Store, graph: ExposureGraph, resolver: EntityResolver, ref: date
) -> IdiosyncraticVsShared:
    sym = record.identity.eod_symbol
    bars = store.get_price_history(record.identity.internal_id)
    name_ret = _window_return(bars, ref, _DECLINE_WINDOW_DAYS) if bars else None
    name_180d = (
        Sourced.present(
            name_ret, source_ref=f"EOD {sym} {_DECLINE_WINDOW_DAYS}d to {ref}"
        )
        if name_ret is not None
        else Sourced.unknown(note="name has no bars over the window")
    )
    bench_bars = store.get_price_history("IDX-IWM")
    mkt_ret = _window_return(bench_bars, ref, _DECLINE_WINDOW_DAYS) if bench_bars else None
    market_180d = (
        Sourced.present(mkt_ret, source_ref=f"EOD IWM {_DECLINE_WINDOW_DAYS}d to {ref}")
        if mkt_ret is not None
        else Sourced.unknown(note="IWM benchmark bars unavailable")
    )
    rel = _sourced(
        record.prices.rel_ret_vs_market, source_ref="EOD name−IWM 180d (screen data-record, G2)"
    )
    cohort = _cohort(graph, resolver, store, record.identity.ticker, ref)
    return IdiosyncraticVsShared(
        name_180d_return=name_180d, market_180d_return=market_180d, rel_vs_market=rel,
        cohort=cohort, read=_idio_read(name_180d, cohort),
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


def _eps_caveat_flags(record: DataRecord, bundle: CiqBundle, *, eps_resolved: bool) -> list[str]:
    """Flag (a) that earnings power (company-adjusted, non-GAAP EPS) is not shown — UNLESS it now is
    (``eps_resolved``: the 99.1 adjusted EPS surfaced it, so the caveat is a resolved fact, not a
    warning); and (b) when the EDGAR P/E conflicts ~Nx with CIQ P/LTM EPS, that the EDGAR trailing
    EPS is one-time-inflated and the synthesis must not anchor on it as 'cheap' (always kept)."""
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
    ):
        ratio = max(pe.value, ciq_pe.value) / min(pe.value, ciq_pe.value)
        if ratio >= 2:
            out.append(
                f"EDGAR P/E ({pe.value:.1f}x) conflicts ~{ratio:.0f}x with CIQ P/LTM EPS "
                f"({ciq_pe.value:.1f}x) — EDGAR trailing EPS is one-time-inflated; the "
                f"synthesis must not anchor on {pe.value:.1f}x as 'cheap'."
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
    )


def _nearest_maturity(liquidity: Sourced[str]) -> str:
    """The nearest refinancing wall — the earliest 'Due YYYY' in the instrument table, or fail-loud
    UNKNOWN (itself a solvency-visibility risk per the synthesis's opacity-as-signal rule)."""
    if liquidity.status is not SourceStatus.PRESENT or not liquidity.value:
        return "nearest refinancing wall UNKNOWN (no instrument table — a risk)"
    years = sorted(int(y) for y in re.findall(r"Due\s+(\d{4})(?!\d)", liquidity.value))
    if not years:
        return "nearest refinancing wall UNKNOWN (no maturity dates parsed — a risk)"
    return f"nearest maturity wall: {years[0]}"


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
    liquidity: Sourced[str], *, net_debt: Sourced[float] | None = None,
) -> Sourced[str]:
    """Solvency as ONE block — net leverage + self-funding (FCF sign) + nearest refinancing wall —
    so survival can't be read as one quality metric among many. Each leg is present or fail-loud
    UNKNOWN (itself a risk). ``net_debt`` (CIQ, $M) lets a non-formable ratio still report the known
    balance-sheet position — a net-cash name is not a 'solvency risk'. No new data source."""
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
    parts.append(_nearest_maturity(liquidity))
    return Sourced.present(
        " | ".join(parts),
        source_ref="CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth fallback) + FCF sign "
        "+ CIQ Capital Structure (survival capacity)",
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
            net_lev, adj_leverage, fcf_sign, liquidity, net_debt=ciq_nd
        ),
        interest_coverage=ciq_sheets.interest_coverage(bundle),
        share_count_trend=(
            _share_count_trend(edgar, record.identity.cik, reference_date)
            if record.identity.cik
            else Sourced.unknown(note="no CIK")
        ),
        liquidity_covenant_flags=liquidity,
        multi_year_trajectory=trajectory,
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


def _bs_bridge_coherence(bundle: CiqBundle, implied: ImpliedValuation) -> Sourced[str]:
    """(C3 coherence gate) The Balance-Sheet cash & total debt must reconcile with the
    implied-valuation bridge (a DIFFERENT CIQ sheet). On disagreement, render BOTH with sources + a
    soft caveat — never silently prefer one."""
    bs_cash = ciq_sheets._bs_latest(bundle, "Total Cash & ST Investments")
    bs_debt = ciq_sheets._bs_latest(bundle, "Total Debt")
    br = implied.bridge.value if implied.bridge.status is SourceStatus.PRESENT else ""
    mc = re.search(r"cash \$([\d,.]+)", br or "")
    md = re.search(r"debt \$([\d,.]+)", br or "")
    bc = float(mc.group(1).replace(",", "")) if mc else None
    bd = float(md.group(1).replace(",", "")) if md else None
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
# positioning SIGNAL; A (grant/award) / M (option exercise) / F (tax withholding) are routine comp
# mechanics tallied SEPARATELY; anything else (C conversion, G gift, …) is bucketed as 'other' and
# LABELED — never silently dropped (that would misstate the counts). Counts + dates only.
_OPEN_MARKET_CODES = ("P", "S")
_ROUTINE_CODES = ("A", "M", "F")


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
    line = f"P×{p} / S×{s} · net {net / 1000:+.1f}K sh · last {last.isoformat()}"
    routine = "/".join(f"{c}×{counts[c]}" for c in _ROUTINE_CODES if counts.get(c))
    if routine:
        line += f" · routine {routine}"
    other = "/".join(
        f"{c}×{n}" for c, n in sorted(counts.items())
        if c not in _OPEN_MARKET_CODES and c not in _ROUTINE_CODES and n
    )
    if other:
        line += f" · other {other}"
    return Sourced.present(
        line, source_ref=f"EDGAR Form 4 (latest {filings[0].accession}; {len(filings)} in 6m)")


def _short_interest(finra: CachedHttp, record: DataRecord, reference_date: date) -> Sourced[str]:
    """(F2) Latest FINRA settlement short interest — shares short + FINRA's own Δ% + days-to-cover
    computed against the SCREEN data-record ADV (no ADV recompute). Dated as-of (no floor). A cross-
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
    line = f"{latest.shares_short / 1e6:.1f}M sh"
    if latest.change_percent is not None:
        line += f" ({latest.change_percent:+.1f}%)"
    adv = record.prices.adv_90d_shares
    if adv.coverage_status is CoverageStatus.PRESENT and adv.value:
        line += f" · DTC {latest.shares_short / adv.value:.1f}d"
        basis = f"DTC = {latest.shares_short:,} short ÷ {adv.value:,.0f} screen 90d ADV"
    else:
        basis = "screen 90d ADV unavailable — DTC omitted"
    return Sourced.present(
        f"Short interest (FINRA, settle {latest.settlement_date}): {line}",
        source_ref=f"FINRA consolidated short interest (settle {latest.settlement_date}); {basis}")


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
        revision_events=ciq_sheets.revision_events(bundle, as_of=aod),
        consensus_stats=ciq_sheets.consensus_stats(bundle, as_of=aod),
        insider_activity=insider_activity,
        short_interest=short_interest,
    )


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
    if aod.startswith("≥"):  # FLOOR basis — no as-of stamp; freshness can't be evaluated on a bound
        return (
            f"Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; "
            f"its data is on/after {aod[1:]} (the latest embedded revision event), but the true "
            f"export date is unknown, so freshness vs the {reference_date.isoformat()} reference "
            "cannot be confirmed. Re-pull, or corroborate against a dated sibling CIQ export."
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


def _covenant_pointers(
    edgar: EdgarClient, http: CachedHttp, cik: str, instruments: list[CapitalInstrument]
) -> Sourced[str]:
    """(E4) Locate credit/loan/indenture exhibits — filed at EXECUTION and incorporated by reference
    later, so scan the FILING HISTORY: the latest 10-K's exhibit index (material-contract ex-10.x) +
    EDGAR full-text (efts) for the instrument-family descriptions. Accession-bound POINTERS; an
    absence line for undocumented facilities (expected for the China bank loans)."""
    if not cik:
        return Sourced.unknown(note="no CIK")
    pointers: list[str] = []
    try:  # (1) latest 10-K exhibit index — the material-contract exhibits
        tenks = edgar.recent_filings(cik, forms=("10-K",))
        if tenks:
            acc = tenks[0].accession
            idx = http.get_json(
                _INDEX.format(cik=int(pad_cik(cik)), acc=acc.replace("-", "")), ttl_seconds=None)
            names = [str(it.get("name", "")) for it in idx.get("directory", {}).get("item", [])]
            # substring-match 'ex10N' anywhere in the filename — CIQ/EDGAR prefix exhibit files with
            # the ticker+date ('mvst20251231-ex1013.htm'), so a start-anchored match misses them.
            exs = [n for n in names if re.search(r"ex-?10\d", n, re.IGNORECASE)]
            if exs:
                pointers.append(f"latest 10-K [{acc}] material-contract exhibits: {', '.join(exs)}")
    except (HttpError, KeyError, ValueError):
        pass
    families = sorted(
        {i.description.split(" With ")[0].split(" - ")[0].strip() for i in instruments})
    for fam in families[:6]:  # (2) efts on each instrument-family description
        try:
            hits = edgar.fulltext_search(fam, forms="8-K")
        except HttpError:
            continue
        if hits:
            pointers.append(f"'{fam[:34]}' → efts {hits[0].accession} ({hits[0].form})")
    if not pointers:
        return Sourced.unknown(
            note="no credit/loan/indenture exhibit located across filing history "
            "(undocumented facility — expected for the bank term loans)")
    return Sourced.present(
        "; ".join(pointers), source_ref="EDGAR filing-history exhibit index + full-text search")


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
    pointers = _covenant_pointers(edgar, http, cik or "", insts)
    # (E5, fenced) covenant TERMS are LLM-extractable ONLY from a located exhibit; the note is
    # opacity-as-signal — it tells the human whether any exhibit exists to read (a Tier-1 pointer
    # present) or whether the facility is wholly undocumented (extraction impossible, itself a
    # fact).
    terms_note = (
        "(E5) named covenant terms extract in the LLM phase from the located exhibit(s) above"
        if pointers.status is SourceStatus.PRESENT
        else "(E5) no covenant exhibit located — no document to extract named terms from")
    return CapitalStructure(
        instruments=instruments, summary=summary, detail_as_of=detail_as_of,
        maturity_filings=_maturity_8ks(edgar, cik or "", insts, reference_date),
        covenant_pointers=pointers,
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


def _ie_bridge_net_debt(bridge: str | None) -> float | None:
    """Net debt implied by the cash/debt bridge string (total debt − cash) — condition-b probe."""
    if not bridge:
        return None
    cash = re.search(r"cash\s+\$?(-?\d+(?:\.\d+)?)", bridge)
    debt = re.search(r"total debt\s+\$?(-?\d+(?:\.\d+)?)", bridge)
    return float(debt.group(1)) - float(cash.group(1)) if (cash and debt) else None


def _implied_expectations(
    peer_comps: PeerComps, catalyst: CatalystPath, implied_val: ImpliedValuation
) -> ImpliedExpectations | None:
    """(G) Assemble price-inverted expectations from ALREADY-SOURCED fields (no workbook). TEV =
    mcap + net debt (simple-TEV basis, labeled — the cell is not surfaced and carries a stale second
    pricing vintage, so deriving from Latest-mcap is vintage-coherent). implied_level =
    TEV ÷ multiple for the fixed set; consensus anchors are the same TEV ÷ the forward ladder (so
    the NTM anchor IS the name-NTM identity row); a G5 residual (FY26 probe) certifies the vintages.
    Returns None when TEV can't be derived (mcap / net debt absent) — the block won't render."""
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

    # consensus anchors (FY26E/FY27E/NTM EBITDA levels) = the SAME TEV ÷ the forward ladder, so the
    # NTM anchor equals the name-NTM identity row BY CONSTRUCTION. FY26E is ALSO directly sourced
    # (acceleration_read) — that direct value is the independent probe the G5 guard checks against.
    def _anchor(period: str, key: str = "TEV/EBITDA") -> float | None:
        mo = _ie_ladder(cna, period, key)
        return (tev / mo) if (mo and mo > 0) else None  # UNROUNDED; 1dp only at display

    def _anchor_line(key: str, metric: str) -> Sourced[str]:
        vals = [(lab, _anchor(p, key)) for lab, p in
                (("FY26E", "FY 2026"), ("FY27E", "FY 2027"), ("NTM", "NTM"))]
        txt = " · ".join(f"{lab} {(f'${v:.1f}M') if v is not None else 'n/a'}" for lab, v in vals)
        return Sourced.present(
            txt + f" (consensus {metric} = TEV ÷ forward ladder; NTM = the name-NTM identity)",
            source_ref=cna_src)

    # anchors are UNROUNDED here (1dp only at display) so the NTM anchor prints the SAME as the
    # name-NTM identity row (both TEV ÷ 7.54 = 82.6). The parallel REVENUE anchors substantiate the
    # TEV/Rev name-row identity (†) — so it's shown, not merely asserted.
    a26 = _anchor("FY 2026")  # the EBITDA FY26 anchor is kept for the G5 residual probe below
    anchors = _anchor_line("TEV/EBITDA", "EBITDA")
    rev_anchors = _anchor_line("TEV/REV", "Revenue")

    # (G5) vintage-coherence: derived FY26 (TEV ÷ FY26 forward multiple, UNROUNDED) vs the DIRECT
    # FY26 EBITDA consensus (acceleration_read). NTM consensus is not a sourced level, so FY26 — the
    # nearest direct consensus — is the probe; the shared-TEV ladder certifies all horizons.
    direct26 = _ie_consensus_latest(catalyst.acceleration_read.value, "FY 2026", "EBITDA")
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
    bridge_nd = _ie_bridge_net_debt(
        implied_val.bridge.value if implied_val.bridge.status is SourceStatus.PRESENT else None)
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
) -> tuple[MechanicalLayer, list[str]]:
    """Assemble the source-bound mechanical layer (no LLM) + any flags for human review (e.g. a
    distorted-P/E-basis warning). No conclusions."""
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
    # (F) positioning inputs slotted into the catalyst path — free DATED feeds: EDGAR Form 4 insider
    # activity + FINRA short interest (DTC vs the screen ADV). Counts/shares/dates only.
    catalyst = _catalyst_path(
        bundle, reference_date,
        insider_activity=_insider_activity(edgar, http, record.identity.cik, reference_date),
        short_interest=_short_interest(finra, record, reference_date),
    )
    valuation = _valuation(
        record, bundle, adj_eps, adj_ev, pe_note=pe_recon[1] if pe_recon else None)
    # (G) price-inverted expectations (multiples-space) attach to Valuation. Built from already-
    # assembled fields only (peer multiples + the forward ladder + the derived TEV) — no extraction.
    valuation = valuation.model_copy(
        update={"implied_expectations": _implied_expectations(peer_comps, catalyst, implied_val)})
    mech = MechanicalLayer(
        valuation=valuation,
        quality=quality,
        concentration=_concentration(bundle),
        peer_comps=peer_comps,
        drawdown_cause=drawdown,
        idiosyncratic_vs_shared=_idiosyncratic_vs_shared(
            record, store, graph, resolver, reference_date
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
    )
    flags: list[str] = []
    if pe_recon is not None:
        flags.append(pe_recon[0])
    flags += _eps_caveat_flags(record, bundle, eps_resolved=adj_eps.status is SourceStatus.PRESENT)
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
    return mech, flags
