"""Assemble a data-record (contract A) for Screen 2 from stored prices + EDGAR + a benchmark.

Also computes the two derived inputs the gates need beyond the raw price features: G2's
relative-return-vs-benchmark, and G3's **P/E percentile vs trailing range** using *point-in-time*
annual EPS — so the multiple history varies with both price *and* earnings, rather than degenerating
into the drawdown. EV/EBITDA percentile is deferred (needs a share/net-debt history); G3 falls back
to P/E. Negative/absent EPS → the percentile defers to UNKNOWN (depth's job).
"""

from __future__ import annotations

from datetime import date, timedelta

from vinci.edgar.client import EdgarClient
from vinci.edgar.concepts import ConceptPoint, extract_points
from vinci.eod.features import _close_on_or_before, compute_price_features, relative_return
from vinci.schemas.data_record import (
    CoverageTier,
    DataRecord,
    EventType,
    Fundamentals,
    Identity,
    StressSignals,
    TypedEvent,
)
from vinci.schemas.envelope import DataField, SourceTier
from vinci.schemas.market import PriceBar

# PUBLIC detector params — the dossier's DrawdownCause carries them so the frontend can mark the
# detector's coverage honestly (boundary + pre-window drops) without duplicating a magic number.
GAP_DOWN_THRESHOLD = -0.10  # a single-day close-to-close drop this steep marks a de-rating event
DECLINE_WINDOW_DAYS = 180  # the detector scans this many days back from the reference date
_PE_WINDOW_DAYS = 1825  # ~5y multiple range (Polygon Starter gives 5y history) — the spec's 3-5y
# "Multiple at/near floor of its OWN trailing range" needs a real range to judge against. The spec
# wants 3-5y; the free 2y feed caps us, so we require ≈the full ~2y (~450 trading days) before G3
# returns PASS/FAIL. With less, G3 → UNKNOWN→defer (depth judges cheapness) — never a short-window
# FAIL that would wrongly reject a clean de-rating. Face-validity, never forward-return tuning.
_PE_MIN_POINTS = 450

# G3's REASONS FOR NOT VALUING A NAME — distinct because their causes are distinct and a reader
# acts differently on each: nothing tagged is a DATA gap, negative-throughout is a real ANSWER
# about the business, a short history is a TIMING state that resolves by waiting, and no price is
# an infrastructure failure.
#
# COUNTS CORRECTED AT REVIEW. The first pass reported 48 / 85 / 49, measured on a WIDER definition
# than the code uses — it counted a name as "nothing tagged" only when BOTH EPS and the EBITDA
# components were absent, while the code (rightly, since EV/EBITDA cannot gate) tests EPS alone.
# The label's text and the code agreed; the NUMBER described a different set. Measured on the
# code's own definition across the 412 names reaching G3 on the 2026-07-29 run:
#   G3_NO_INPUT 54 · G3_NEGATIVE_ECONOMICS 94 · G3_SHORT_HISTORY 34 · G3_NO_PRICE 0 · resolves 230
G3_NO_INPUT = "no valuation input tagged — no diluted EPS in the filing history"
G3_NEGATIVE_ECONOMICS = (
    "inputs tagged but economics negative throughout — never a positive annual EPS. This is an "
    "answer about the business, not a gap in the data")
G3_SHORT_HISTORY = "history below the floor — too short to judge a trailing range"
#: SEPARATE from G3_NEGATIVE_ECONOMICS: that name has never earned anything, this one HAS but the
#: last positive year is too far back to describe the business now. Separate because they resolve
#: differently — one needs a different valuation basis, the other needs the company to file again.
G3_EPS_TOO_OLD = (
    "the last positive annual EPS is older than one filing cycle — a more recent annual figure "
    "exists and is negative, so valuing on the older one prices a business that no longer reports "
    "those earnings")
#: Zero names on the 2026-07-29 run and structurally near-unreachable (a name reaching G3 cleared
#: G1 and G2 on price), but NAMED rather than left an inline literal: an un-named reason is one the
#: taxonomy does not know about, so it escapes both the exhaustiveness pin and the population count.
G3_NO_PRICE = "no price at the reference date"

#: Every reason G3 can emit. The pin asserts the emitted set is exactly this — a fourth reason
#: added inline (as `G3_NO_PRICE` was) is a cause with no count and no label anyone reads.
G3_REASONS = (G3_NO_INPUT, G3_NEGATIVE_ECONOMICS, G3_SHORT_HISTORY, G3_NO_PRICE, G3_EPS_TOO_OLD)


#: How far past its period end an annual EPS may be and still describe the CURRENT business.
#:
#: DERIVED FROM THE FILING CADENCE, not from the population — the population is a continuous tail
#: (p50 210d, p90 1,763d, max 6,054d across the 412 names reaching G3) with no separation to read a
#: bound off. The cadence has one:
#:
#:     365d  the annual reporting period itself (measured p50 gap between annual points: 365d)
#:   +  90d  the latest statutory 10-K deadline (non-accelerated filers; 60d large-accelerated,
#:           75d accelerated — measured p50 57d, p90 78d, p95 89d on periods ending >= 2022, which
#:           matches the SEC schedule exactly)
#:   +  15d  the NT 10-K extension a late filer is entitled to
#:   = 470d
#:
#: The NEXT-OLDER annual figure sits at least one more period back — 730d — so the bound has 260
#: days of margin and cannot be reached by a filer who is merely late. Past it, the reader has
#: skipped a more recent annual figure, and the only reason to skip one is that it was NEGATIVE:
#: this function takes the latest POSITIVE point, so an unbounded reach-back values a company on
#: pre-loss earnings. Measured before the bound: p90 4.8 years, max 16.6 years.
MAX_EPS_AGE_DAYS = 470


def annual_eps_as_of(points: list[ConceptPoint], d: date,
                     *, max_age_days: int | None = MAX_EPS_AGE_DAYS) -> float | None:
    """Latest *positive* annual diluted EPS known on/before ``d``, within ``max_age_days`` of its
    period end. None if none qualifies.

    THE BOUND LIVES HERE, IN THE SHARED READER, not at the gate. There are two consumers —
    `enrich_with_fundamentals` (G3) and `cli.py`'s `_pc_valuation` peer-cohort command — and both
    reach `annual_eps_as_of` through `pe_current_and_percentile`. Bounding at the gate alone would
    have left the peer-cohort command valuing names on sixteen-year-old earnings, so the default is
    applied at the source and neither caller can opt out by omission.
    """
    # ``None`` means UNBOUNDED, and it is spelled that way on purpose (review finding). The first
    # cut used ``max_age_days=10**6`` as the sentinel — a magic number a reader has to decode, and
    # one a pin then hard-matched as source text. The only caller that wants it is the cause-split
    # probe below, asking "did a positive figure exist AT ALL", which is a different question from
    # "is one current"; naming that distinction is worth more than saving a branch.
    cand = [p for p in points
            if p.is_annual and p.filed <= d and p.value > 0
            and (max_age_days is None or (d - p.period_end).days <= max_age_days)]
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
        # THE CAUSE, NOT JUST THE ABSENCE. "no positive EPS/price" collapsed two states G3 must
        # tell apart: a filer that has NEVER tagged diluted EPS (nothing to value with) and one
        # that tags it every year and has simply never earned a positive number (a real answer
        # about the business, not a gap in our data). Measured on the 412 reaching G3: 54 vs 94.
        if not annual_eps:
            why = G3_NO_INPUT
        elif cur_price is None:
            why = G3_NO_PRICE
        elif annual_eps_as_of(annual_eps, reference_date, max_age_days=None) is not None:
            # a positive figure EXISTS but is out of range — distinct from never having earned one
            why = G3_EPS_TOO_OLD
        else:
            why = G3_NEGATIVE_ECONOMICS
        u: DataField[float] = DataField.unknown(
            source="EDGAR", tier=SourceTier.DERIVED, note=why
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
            note=f"{G3_SHORT_HISTORY}: only {len(hist)} P/E points (< {min_points})",
        )
        return pe_df, pctile_u
    pctile = sum(1 for x in hist if x <= cur_pe) / len(hist)
    pctile_df = DataField.present(
        pctile, as_of=reference_date, source="EDGAR", tier=SourceTier.DERIVED
    )
    return pe_df, pctile_df


def detect_gap_downs(
    bars: list[PriceBar], *, since: date, threshold: float = GAP_DOWN_THRESHOLD
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
    decline_window_days: int = DECLINE_WINDOW_DAYS,
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
    prices = prices.model_copy(update={"rel_ret_vs_market": rel})

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
    # EV/EBITDA — the multiple and its trailing-range percentile are both DEFERRED (need net-debt).
    # The multiple stays UNKNOWN: do NOT write EBITDA *dollars* (``snap.ebitda_annual``) into a
    # field named for a multiple — that mislabel traps any reader (the dossier sources it from CIQ).
    ev_unknown: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.DERIVED, note="EV/EBITDA deferred — needs net-debt/EV"
    )
    fundamentals = Fundamentals(
        ev_ebitda=ev_unknown,
        ev_ebitda_pctile_vs_history=ev_unknown,
        pe=pe,
        pe_pctile_vs_history=pe_pctile,
        fcf_sign=snap.fcf_sign,
        op_income_sign=snap.op_income_sign,
        net_leverage=snap.net_leverage,
        net_debt_to_ocf=snap.net_debt_to_ocf,
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
    decline_window_days: int = DECLINE_WINDOW_DAYS,
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
