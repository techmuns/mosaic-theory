"""Assemble a data-record (contract A) for Screen 2 from stored prices + EDGAR + a benchmark.

Also computes the two derived inputs the gates need beyond the raw price features: G2's
relative-return-vs-benchmark, and G3's **P/E percentile vs trailing range** using *point-in-time*
annual EPS — so the multiple history varies with both price *and* earnings, rather than degenerating
into the drawdown. EV/EBITDA percentile is deferred (needs a share/net-debt history); G3 falls back
to P/E. Negative/absent EPS → the percentile defers to UNKNOWN (depth's job).
"""

from __future__ import annotations

from datetime import date, timedelta

from mosaic.edgar.client import EdgarClient
from mosaic.edgar.concepts import ConceptPoint, extract_points
from mosaic.eod.features import _close_on_or_before, compute_price_features, relative_return
from mosaic.schemas.data_record import (
    CoverageTier,
    DataRecord,
    EventType,
    Fundamentals,
    Identity,
    StressSignals,
    TypedEvent,
)
from mosaic.schemas.envelope import DataField, SourceTier
from mosaic.schemas.market import PriceBar

_GAP_DOWN = -0.10  # a single-day close-to-close drop this steep is a de-rating event marker
_PE_WINDOW_DAYS = 1825  # ~5y multiple range (Polygon Starter gives 5y history) — the spec's 3-5y
# "Multiple at/near floor of its OWN trailing range" needs a real range to judge against. The spec
# wants 3-5y; the free 2y feed caps us, so we require ≈the full ~2y (~450 trading days) before G3
# returns PASS/FAIL. With less, G3 → UNKNOWN→defer (depth judges cheapness) — never a short-window
# FAIL that would wrongly reject a clean de-rating. Face-validity, never forward-return tuning.
_PE_MIN_POINTS = 450


def annual_eps_as_of(points: list[ConceptPoint], d: date) -> float | None:
    """Latest *positive* annual diluted EPS known on/before ``d`` (point-in-time); None if none."""
    cand = [p for p in points if p.is_annual and p.filed <= d and p.value > 0]
    if not cand:
        return None
    return max(cand, key=lambda p: (p.period_end, p.filed)).value


def pe_current_and_percentile(
    price_bars: list[PriceBar],
    annual_eps: list[ConceptPoint],
    *,
    reference_date: date,
    min_points: int = _PE_MIN_POINTS,
) -> tuple[DataField[float], DataField[float]]:
    """(current P/E, percentile of current P/E within its trailing range). Each may be UNKNOWN.

    The percentile defers to UNKNOWN unless ≥ ``min_points`` P/E observations exist in the trailing
    window — a too-short range cannot reliably establish "at floor"."""
    bars = sorted(price_bars, key=lambda b: b.bar_date)
    cur_eps = annual_eps_as_of(annual_eps, reference_date)
    cur_price = _close_on_or_before(bars, reference_date)
    if cur_eps is None or cur_price is None:
        u: DataField[float] = DataField.unknown(
            source="EDGAR", tier=SourceTier.DERIVED, note="no positive EPS/price"
        )
        return u, u
    cur_pe = cur_price / cur_eps
    pe_df = DataField.present(cur_pe, as_of=reference_date, source="EDGAR", tier=SourceTier.DERIVED)

    start = reference_date - timedelta(days=_PE_WINDOW_DAYS)
    hist: list[float] = []
    for b in bars:
        if start <= b.bar_date <= reference_date:
            e = annual_eps_as_of(annual_eps, b.bar_date)
            if e:
                hist.append(b.close / e)
    if len(hist) < min_points:
        pctile_u: DataField[float] = DataField.unknown(
            source="EDGAR",
            tier=SourceTier.DERIVED,
            note=f"only {len(hist)} P/E points (< {min_points}) — too short to judge floor",
        )
        return pe_df, pctile_u
    pctile = sum(1 for x in hist if x <= cur_pe) / len(hist)
    pctile_df = DataField.present(
        pctile, as_of=reference_date, source="EDGAR", tier=SourceTier.DERIVED
    )
    return pe_df, pctile_df


def detect_gap_downs(
    bars: list[PriceBar], *, since: date, threshold: float = _GAP_DOWN
) -> list[date]:
    """Dates of single-day close-to-close drops ≤ ``threshold`` on/after ``since``."""
    bars = sorted(bars, key=lambda b: b.bar_date)
    out: list[date] = []
    for prev, cur in zip(bars, bars[1:], strict=False):
        if cur.bar_date >= since and prev.close > 0 and (cur.close / prev.close - 1.0) <= threshold:
            out.append(cur.bar_date)
    return out


def build_price_record(
    identity: Identity,
    *,
    price_bars: list[PriceBar],
    benchmark_bars: list[PriceBar],
    reference_date: date,
    staleness_days: int,
    decline_window_days: int = 180,
    market_cap: DataField[float] | None = None,
) -> DataRecord:
    """The **cheap** price-only data-record — enough to evaluate G1/G2 without any EDGAR call.

    Fundamentals are left UNKNOWN; the full-universe screen enriches with EDGAR only for the names
    that survive the price gates (see :func:`enrich_with_fundamentals`)."""
    prices = compute_price_features(
        price_bars, reference_date=reference_date, staleness_days=staleness_days
    )
    rel = relative_return(
        price_bars, benchmark_bars, reference_date=reference_date, lookback_days=decline_window_days
    )
    prices = prices.model_copy(update={"rel_ret_vs_sector": rel})

    uf: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.DERIVED, note="deferred until price gates pass"
    )
    ui: DataField[int] = DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note="deferred")
    fundamentals = Fundamentals(
        ev_ebitda=uf, ev_ebitda_pctile_vs_history=uf, pe=uf, pe_pctile_vs_history=uf,
        fcf_sign=ui, op_income_sign=ui, net_leverage=uf,
    )
    gap_since = reference_date - timedelta(days=decline_window_days)
    events = [
        TypedEvent(event_type=EventType.EARNINGS_GAP_DOWN, event_date=d, source="EOD gap-down")
        for d in detect_gap_downs(price_bars, since=gap_since)
    ]
    return DataRecord(
        identity=identity,
        market_cap=market_cap
        or DataField.unknown(source="DERIVED", tier=SourceTier.DERIVED, note="needs shares"),
        prices=prices,
        fundamentals=fundamentals,
        stress=_no_stress(),
        events=events,
        overall_coverage_tier=CoverageTier.US_FULL,
        as_of=reference_date,
    )


def enrich_with_fundamentals(
    rec: DataRecord, *, edgar: EdgarClient, price_bars: list[PriceBar], reference_date: date
) -> DataRecord:
    """Fetch EDGAR and fill the fundamentals (G3 multiple-at-floor + non-distress signals)."""
    cik = rec.identity.cik
    snap = edgar.fundamental_snapshot(cik)
    facts = edgar.companyfacts(cik) if cik else {}
    annual_eps = [p for p in extract_points(facts, "eps_diluted") if p.is_annual] if facts else []
    pe, pe_pctile = pe_current_and_percentile(price_bars, annual_eps, reference_date=reference_date)
    ev_unknown: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.DERIVED, note="EV/EBITDA history deferred (needs net-debt)"
    )
    fundamentals = Fundamentals(
        ev_ebitda=snap.ebitda_annual,
        ev_ebitda_pctile_vs_history=ev_unknown,
        pe=pe,
        pe_pctile_vs_history=pe_pctile,
        fcf_sign=snap.fcf_sign,
        op_income_sign=snap.op_income_sign,
        net_leverage=snap.net_leverage,
    )
    return rec.model_copy(update={"fundamentals": fundamentals})


def build_data_record(
    identity: Identity,
    *,
    price_bars: list[PriceBar],
    benchmark_bars: list[PriceBar],
    edgar: EdgarClient,
    reference_date: date,
    staleness_days: int,
    decline_window_days: int = 180,
) -> DataRecord:
    """Assemble the full data-record (price + EDGAR fundamentals). The eager path used off the
    hot loop (orchestrator/tests); the screen uses the lazy price→enrich split."""
    rec = build_price_record(
        identity, price_bars=price_bars, benchmark_bars=benchmark_bars,
        reference_date=reference_date, staleness_days=staleness_days,
        decline_window_days=decline_window_days,
    )
    return enrich_with_fundamentals(
        rec, edgar=edgar, price_bars=price_bars, reference_date=reference_date
    )


def _no_stress() -> StressSignals:
    """Stress signals (IBKR options/short-interest) are shortlist-only and deferred in Loop 1."""
    u: DataField[float] = DataField.unknown(source="IBKR", tier=SourceTier.IBKR, note="deferred")
    return StressSignals(iv_pctile=u, short_interest=u)
