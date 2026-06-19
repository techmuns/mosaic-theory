"""The MECHANICAL layer — deterministic, no LLM, every field a source-bound ``{value, source_ref}``.

Facts come from the screen's data-record (already EDGAR/EOD-bound), fresh EDGAR pulls (the 8-K
behind each gap-down; the share-count trend), EOD bars (the name's and IWM's window returns), the
graph (the exposed cross-section, a research INPUT — never a predictor), and the manual CIQ bundle.
Anything not found is UNKNOWN (looked for, absent) or MISSING (whole source absent, e.g. CIQ
un-pulled) — never
a fabricated number. This layer is the ONLY input the synthesis LLM is later given.
"""

from __future__ import annotations

import statistics
from datetime import date, timedelta

from mosaic.dossier.ciq import CiqBundle, CiqParseError, read_sheets, read_text
from mosaic.dossier.schemas import (
    CohortMember,
    Concentration,
    ConsensusContext,
    DrawdownCause,
    FilingRef,
    IdiosyncraticVsShared,
    MechanicalLayer,
    Quality,
    Sourced,
    Valuation,
)
from mosaic.edgar.client import EdgarClient
from mosaic.edgar.concepts import extract_points
from mosaic.graph.exposure import ExposureGraph
from mosaic.graph.filings import html_to_text
from mosaic.netcache import CachedHttp, HttpError
from mosaic.resolver import EntityResolver, ResolutionError
from mosaic.resolver.index import pad_cik
from mosaic.schemas.data_record import DataRecord
from mosaic.schemas.envelope import DataField
from mosaic.schemas.market import PriceBar
from mosaic.store import Store

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_DECLINE_WINDOW_DAYS = 180  # the G2 decline window — keep the cohort comparison on the same window


def _sourced(field: DataField[float] | DataField[int], *, source_ref: str) -> Sourced[float]:
    """Lift a screen data-record :class:`DataField` into a source-bound dossier fact."""
    if field.is_known and field.value is not None:
        return Sourced.present(float(field.value), source_ref=source_ref, note=field.note)
    return Sourced.unknown(note=field.note or "UNKNOWN in the screen data-record")


def _close_on_or_before(bars: list[PriceBar], ref: date) -> float | None:
    elig = [b for b in bars if b.bar_date <= ref]
    return max(elig, key=lambda b: b.bar_date).close if elig else None


def _window_return(bars: list[PriceBar], ref: date, days: int) -> float | None:
    then = _close_on_or_before(bars, ref - timedelta(days=days))
    now = _close_on_or_before(bars, ref)
    return (now / then - 1.0) if (then and now and then > 0) else None


# --- drawdown cause (EDGAR 8-K around the gap-downs) -------------------------------------------


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
        url, excerpt = "", "(no primary document)"
        if f.primary_doc:
            url = _ARCHIVE.format(
                cik=int(pad_cik(f.cik)), acc=f.accession.replace("-", ""), doc=f.primary_doc
            )
            try:
                excerpt = html_to_text(http.get_text(url, ttl_seconds=None))[:700]
            except HttpError:
                excerpt = "(filing body could not be fetched)"
        refs.append(
            FilingRef(
                filing_date=f.filing_date.isoformat(), form=f.form, items=list(f.items),
                accession=f.accession, url=url, excerpt=excerpt,
            )
        )
    return refs


def _drawdown_cause(record: DataRecord, edgar: EdgarClient, http: CachedHttp) -> DrawdownCause:
    gaps = [e.event_date for e in record.events if e.event_type.value == "earnings_gap_down"]
    if gaps:
        shape = Sourced.present(
            f"discrete event(s) — {len(gaps)} earnings gap-down(s)",
            source_ref="EOD gap-down detector (screen events)",
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
    cik = record.identity.cik
    filings = _drawdown_filings(edgar, http, cik, gaps) if cik else []
    return DrawdownCause(shape=shape, gap_down_dates=dates_field, filings=filings)


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


# --- share-count trend (EDGAR XBRL shares) ----------------------------------------------------


def _share_count_trend(edgar: EdgarClient, cik: str) -> Sourced[str]:
    try:
        pts = [p for p in extract_points(edgar.companyfacts(cik), "shares") if p.value]
    except (HttpError, KeyError):
        return Sourced.unknown(note="EDGAR companyfacts shares unavailable")
    if len(pts) < 2:
        return Sourced.unknown(note="insufficient XBRL shares history for a dilution trend")
    pts.sort(key=lambda p: p.period_end)
    first, last = pts[0], pts[-1]
    pct = (last.value / first.value - 1.0) if first.value else 0.0
    word = "diluting" if pct > 0.02 else "buying back" if pct < -0.02 else "flat"
    return Sourced.present(
        f"{word}: shares {first.value:,.0f} ({first.period_end}) → {last.value:,.0f} "
        f"({last.period_end}), {pct:+.1%}",
        source_ref=f"EDGAR XBRL shares (companyfacts), {first.period_end}..{last.period_end}",
    )


# --- CIQ-sourced fields (fail-loud MISSING when the export is absent) --------------------------


def _ciq_missing(bundle: CiqBundle, module: str, location: str) -> Sourced[str]:
    return Sourced.missing(
        note=f"CIQ {module} not found for {bundle.ticker} — pull into {location} and re-run"
    )


def _ciq_text_summary(bundle: CiqBundle, module: str, location: str, label: str) -> Sourced[str]:
    """Surface a CIQ module's primary data, source-bound. Present-file read; MISSING when absent.

    Deliberately a source-bound *surfacing* of the primary cells/rows (not a derived metric we can't
    verify): the human reads the cited file. Fail-loud UNKNOWN if the present file can't be parsed
    here (e.g. an OLE-disguised transcript needs LibreOffice)."""
    cfiles = bundle.for_module(module)
    if not cfiles:
        return _ciq_missing(bundle, label, location)
    cf = cfiles[0]
    try:
        if cf.fmt.value in ("rtf_text", "mime_doc", "html", "pdf"):
            text = read_text(cf.path, cf.fmt)
            return Sourced.present(text[:1200], source_ref=f"CIQ {cf.path.name} ({cf.fmt.value})")
        sheets = read_sheets(cf.path, cf.fmt)
        preview = "; ".join(f"{name}[{len(rows)}r]" for name, rows in list(sheets.items())[:6])
        return Sourced.present(
            f"sheets: {preview}", source_ref=f"CIQ {cf.path.name} ({cf.fmt.value})"
        )
    except CiqParseError as exc:
        return Sourced.unknown(note=str(exc))


def _valuation(record: DataRecord, bundle: CiqBundle, location: str) -> Valuation:
    f = record.fundamentals
    return Valuation(
        pe=_sourced(f.pe, source_ref="EDGAR XBRL eps_diluted × EOD price (screen data-record, G3)"),
        pe_percentile_5y=_sourced(
            f.pe_pctile_vs_history, source_ref="EDGAR/EOD P/E pctile vs ~5y (screen data-record)"
        ),
        ev_ebitda=_sourced(f.ev_ebitda, source_ref="EDGAR XBRL (screen data-record)"),
        ev_ebitda_percentile_5y=(
            _sourced(f.ev_ebitda_pctile_vs_history, source_ref="EDGAR (screen data-record)")
            if f.ev_ebitda_pctile_vs_history.is_known
            else _ciq_missing(bundle, "Financials→Multiples (EV/EBITDA percentile)", location)
        ),
        range_position=_ciq_text_summary(bundle, "multiples", location, "Financials→Multiples"),
    )


def _quality(record: DataRecord, edgar: EdgarClient, bundle: CiqBundle, location: str) -> Quality:
    f = record.fundamentals
    return Quality(
        fcf_sign=_sourced(f.fcf_sign, source_ref="EDGAR XBRL FCF sign (screen data-record)"),
        free_cash_flow=_ciq_missing(bundle, "Financials→Cash Flow (FCF value)", location),
        margin_trend=_ciq_text_summary(bundle, "financials", location, "Financials→Income Stmt"),
        net_debt_to_ebitda=_sourced(
            f.net_leverage, source_ref="EDGAR XBRL net-debt/EBITDA (screen data-record)"
        ),
        interest_coverage=_ciq_missing(bundle, "Financials (interest coverage)", location),
        share_count_trend=(
            _share_count_trend(edgar, record.identity.cik)
            if record.identity.cik
            else Sourced.unknown(note="no CIK")
        ),
        liquidity_covenant_flags=_ciq_missing(
            bundle, "Capital Structure Details (covenants/liquidity)", location
        ),
    )


def _concentration(bundle: CiqBundle, location: str) -> Concentration:
    return Concentration(
        segments=_ciq_text_summary(bundle, "segments", location, "Segments"),
        customers=_ciq_text_summary(bundle, "customers", location, "Customers & Suppliers"),
        geographic=_ciq_text_summary(bundle, "segments", location, "Segments (geographic)"),
    )


def _consensus(bundle: CiqBundle, location: str) -> ConsensusContext:
    return ConsensusContext(
        eps_trend=_ciq_text_summary(bundle, "estimates", location, "Estimates→Consensus (EPS)"),
        revenue_trend=_ciq_text_summary(bundle, "estimates", location, "Estimates→Consensus (Rev)"),
        revision_history=_ciq_text_summary(bundle, "estimates", location, "Estimates→Revisions"),
    )


def assemble_mechanical(
    record: DataRecord,
    *,
    store: Store,
    edgar: EdgarClient,
    http: CachedHttp,
    graph: ExposureGraph,
    resolver: EntityResolver,
    bundle: CiqBundle,
    ciq_location: str,
    reference_date: date,
) -> MechanicalLayer:
    """Assemble the full source-bound mechanical layer for one finalist. No LLM, no conclusions."""
    return MechanicalLayer(
        valuation=_valuation(record, bundle, ciq_location),
        quality=_quality(record, edgar, bundle, ciq_location),
        concentration=_concentration(bundle, ciq_location),
        drawdown_cause=_drawdown_cause(record, edgar, http),
        idiosyncratic_vs_shared=_idiosyncratic_vs_shared(
            record, store, graph, resolver, reference_date
        ),
        consensus_context=_consensus(bundle, ciq_location),
    )
