"""Cap-band universe builder — the start of the real validation clock.

Market cap = latest EOD close × XBRL shares outstanding, filtered to the configured small/mid band
(US exchanges only). It uses the **breadth tools** so it never makes thousands of per-name calls:
one Polygon grouped-daily call (cached) for every close, and a handful of EDGAR ``frames`` calls for
every filer's shares. Membership is snapshotted with an ``as_of`` so future backtests aren't
survivorship-biased.

Coarse-band caveat: market cap uses the issuer's *total* shares against each security's price, so a
non-primary dual-class line is approximate — fine for a coarse band, not a valuation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from mosaic.config import Config, get_config
from mosaic.edgar import EdgarClient
from mosaic.eod import EodClient, PolygonEodClient
from mosaic.resolver import EntityResolver
from mosaic.schemas.data_record import Identity
from mosaic.schemas.envelope import DataField, SourceTier
from mosaic.store import Store

_QUARTER_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))
_FILING_LAG_DAYS = 40  # don't ask for a quarter's shares frame until it's plausibly filed


def benchmark_identity(symbol: str) -> Identity:
    """Synthetic identity for a benchmark ETF (not a SEC issuer → not resolver-resolved)."""
    return Identity(
        internal_id=f"IDX-{symbol}", issuer_id="IDX", cik="", ticker=symbol, mic="ARCX",
        exchange="ETF", eod_symbol=symbol, name=f"{symbol} (benchmark)",
    )


def recent_share_periods(reference_date: date, *, n: int = 5) -> list[str]:
    """The ``n`` most recent quarter-instant frame keys (e.g. ``CY2026Q1I``), oldest→newest."""
    keys: list[tuple[date, str]] = []
    for yy in range(reference_date.year - 2, reference_date.year + 2):
        for q, (m, d) in enumerate(_QUARTER_ENDS, start=1):
            qe = date(yy, m, d)
            if qe <= reference_date - timedelta(days=_FILING_LAG_DAYS):
                keys.append((qe, f"CY{yy}Q{q}I"))
    keys.sort()
    return [k for _, k in keys[-n:]]


def latest_close_and_adv(
    eod: EodClient, reference_date: date, *, lookback_days: int = 90
) -> tuple[dict[str, float], dict[str, float]]:
    """({ticker: latest close}, {ticker: 90d avg daily $-volume}) from cached grouped-daily bars."""
    closes: dict[str, float] = {}
    dollar_vol: dict[str, float] = defaultdict(float)
    n_days: dict[str, int] = defaultdict(int)
    d = reference_date
    horizon = reference_date - timedelta(days=lookback_days)
    while d >= horizon:
        for t, b in eod.grouped_daily(d).items():
            closes.setdefault(t, b.close)  # most-recent close wins
            dollar_vol[t] += b.close * b.volume
            n_days[t] += 1
        d -= timedelta(days=1)
    adv = {t: dollar_vol[t] / n_days[t] for t in dollar_vol if n_days[t] > 0}
    return closes, adv


def admit_security_type(ptype: str | None, allowed: tuple[str, ...]) -> bool:
    """Instrument-type ALLOWLIST test (Axis 2). Admit ONLY listed operating-co equity types.

    Fail-closed: a blank/unknown/missing ``ptype`` (``None``) is never in the allowlist, so it is
    excluded — never silently admitted (the same rule as a blank SIC). An allowlist, not a denylist:
    a structured-product type we have not enumerated defaults to *excluded*.
    """
    return ptype in allowed


def build_universe(
    config: Config | None = None, *, reference_date: date, share_periods: list[str] | None = None
) -> dict[str, int]:
    """Build + snapshot the cap-band universe as of ``reference_date``. Returns a stats summary."""
    cfg = config or get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    eod = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    band = cfg.universe

    closes, adv = latest_close_and_adv(eod, reference_date)
    sec_types = eod.security_types()  # instrument-type axis (one cached bulk reference pull)
    periods = share_periods or recent_share_periods(reference_date)
    shares = edgar.shares_outstanding_by_cik(periods)

    stats: Counter[str] = Counter()
    with Store(cfg.db_path) as store:
        store.clear_universe(reference_date)  # a rebuild is a clean snapshot, not an accretion
        for ident in resolver.iter_universe(band.exchanges):
            stats["considered"] += 1
            close = closes.get(ident.eod_symbol)
            sh = shares.get(ident.cik)
            if close is None:
                stats["no_price"] += 1
                continue
            if sh is None:
                stats["no_shares"] += 1
                continue
            market_cap = close * sh
            if not (band.market_cap_min_usd <= market_cap <= band.market_cap_max_usd):
                stats["out_of_band"] += 1
                continue
            if adv.get(ident.eod_symbol, 0.0) < band.adv_floor_usd:
                stats["below_adv_floor"] += 1  # tradeability gate
                continue
            # Operating-companies-only gate — TWO independent structural axes, both fail-CLOSED on a
            # missing value (exclude what we cannot confirm; never silently admit). SIC is fetched
            # only for names that already clear cap+ADV — the would-be-admitted set.
            #
            # Axis 1 — issuer BUSINESS type (EDGAR SIC). A BLANK/unknown SIC is excluded, not
            # admitted: a blank SIC is exactly how a BDC/fund slips a denylist (`None` is never `in`
            # the exclude set — CION, OTF). Then drop the confirmed fund/shell codes.
            sic = resolver.sic_for(ident.cik)[0]
            if sic is None:
                stats["unknown_sic"] += 1  # cannot confirm operating-co → excluded, not admitted
                continue
            if sic in band.excluded_sic_codes:
                stats["non_operating"] += 1  # ETF/ETP/fund/blank-check — a basket, not a business
                continue
            # Axis 2 — security INSTRUMENT type (Polygon). An ALLOWLIST of operating-company common
            # equity, fail-CLOSED, with the two exclusion reasons counted separately:
            #   • a CONFIRMED non-equity type (ETN/ETF/ETV/ETS/FUND/SP/PFD/RIGHT/WARRANT/UNIT) — a
            #     basket/derivative. This catches an ETN spliced onto its bank issuer (SHNY=ETS →
            #     Bank of Montreal: ticker→CIK is correct, just not common equity).
            #   • a MISSING type — absent from Polygon's current reference, i.e. recently delisted
            #     (these carry stale bars the 90-day price gate still admitted); flagged, excluded.
            ptype = sec_types.get(ident.eod_symbol)
            if not admit_security_type(ptype, band.allowed_security_types):
                stats["unknown_type" if ptype is None else "non_common_equity"] += 1
                continue
            stats["in_universe"] += 1
            store.upsert_security(ident, first_seen=reference_date)
            store.record_universe(
                as_of=reference_date,
                internal_id=ident.internal_id,
                in_universe=True,
                market_cap=DataField.present(
                    market_cap, as_of=reference_date, source="DERIVED", tier=SourceTier.DERIVED
                ),
            )
        store.export_snapshots(cfg.snapshots_dir)
    return dict(stats)
