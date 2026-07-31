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

import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from vinci.config import Config, get_config
from vinci.edgar import EdgarClient
from vinci.eod import EodClient, PolygonEodClient
from vinci.resolver import EntityResolver
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import DataField, SourceTier
from vinci.store import Store

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


# The ONLY snapshot artifacts build_universe writes: upsert_security → issuers + securities,
# record_universe → universe_snapshot. It exports EXACTLY this set so a stale working DB can never
# rewrite candidate_records / decision_ledger via the full dump (the 2026-07-13 ledger-DELETE
# near-miss). Enumerated from the store calls below, not guessed.
BUILD_UNIVERSE_TABLES: tuple[str, ...] = ("issuers", "securities", "universe_snapshot")


#: EVERY drop this builder can make, in funnel order. Enumerated rather than described, because a
#: stage missing from the thin grain is a stage with no evidence trail — which just MOVES the blind
#: spot instead of closing it. Each is emitted with the one input that decided it.
DROP_STAGES: tuple[str, ...] = (
    "no_price", "no_shares", "out_of_band", "below_adv_floor",
    "unknown_sic", "non_operating", "unknown_type", "non_common_equity",
)


def build_universe(
    config: Config | None = None, *, reference_date: date, share_periods: list[str] | None = None,
    retain_run_id: str | None = None, retain_dir: Path | None = None,
) -> dict[str, int]:
    """Build + snapshot the cap-band universe as of ``reference_date``. Returns a stats summary.

    RETENTION (thin grain). Every name this builder DROPS gets a row naming the stage, the reason,
    and the single input that decided it. This is the stage nothing has ever measured: a name
    filtered here never reaches the screen, so it has no gate outcomes and would otherwise leave no
    trace at all — and `universe.py`'s market-cap stamp (STATE S3) is exactly a defect at this
    stage. Admitted names are NOT retained here; the screen records them at the candidate grain.
    """
    if (retain_run_id is None) != (retain_dir is None):
        raise ValueError(
            "retain_run_id and retain_dir must be given together — one without the other builds "
            "retention rows and discards them while reporting them as retained")
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

    # IMPORTED HERE, NOT AT MODULE SCOPE. `vinci.screens.__init__` imports `run`, which imports
    # `vinci.universe` — so a module-scope import of anything under `vinci.screens` makes importing
    # `vinci.universe` FIRST a circular-import crash. It only fires on that import order, which is
    # why the suite stayed green and a real `build_universe` run did not.
    from vinci.screens.retention import Outcome, StampedInput, UniverseRow, append_rows

    stats: Counter[str] = Counter()
    dropped: list[UniverseRow] = []

    def _drop(ticker: str, stage: str, reason: str, inp: StampedInput) -> None:
        stats[stage] += 1
        if retain_run_id is not None:
            dropped.append(UniverseRow(
                ticker=ticker, run_id=retain_run_id, reference_date=reference_date,
                outcome=Outcome.FAIL, stage=stage, reason=reason, deciding_input=inp))

    with Store(cfg.db_path) as store:
        store.clear_universe()  # FULL replace — a rebuild is a clean snapshot, not an accretion
        # (was clear-only-`reference_date`, which left prior as_of generations on a persistent DB)
        for ident in resolver.iter_universe(band.exchanges):
            stats["considered"] += 1
            close = closes.get(ident.eod_symbol)
            sh = shares.get(ident.cik)
            if close is None:
                _drop(ident.eod_symbol, "no_price", "no latest close in the grouped-daily pull",
                      StampedInput(value=None, source="Polygon grouped-daily"))
                continue
            if sh is None:
                _drop(ident.eod_symbol, "no_shares", "no EDGAR XBRL share count for the CIK",
                      StampedInput(value=None, source="EDGAR shares_outstanding_by_cik"))
                continue
            market_cap = close * sh
            if not (band.market_cap_min_usd <= market_cap <= band.market_cap_max_usd):
                _drop(ident.eod_symbol, "out_of_band",
                      f"market cap {market_cap / 1e6:,.1f}M outside "
                      f"[{band.market_cap_min_usd / 1e6:,.0f}M, "
                      f"{band.market_cap_max_usd / 1e6:,.0f}M]",
                      StampedInput(value=market_cap, as_of=reference_date,
                                   source="Polygon close x EDGAR XBRL shares"))
                continue
            if (a := adv.get(ident.eod_symbol, 0.0)) < band.adv_floor_usd:
                _drop(ident.eod_symbol, "below_adv_floor",
                      f"ADV ${a / 1e6:,.2f}M below the ${band.adv_floor_usd / 1e6:,.1f}M floor",
                      StampedInput(value=a, as_of=reference_date, source="Polygon ADV"))
                continue  # tradeability gate
            # Operating-companies-only gate — TWO independent structural axes, both fail-CLOSED on a
            # missing value (exclude what we cannot confirm; never silently admit). SIC is fetched
            # only for names that already clear cap+ADV — the would-be-admitted set.
            #
            # Axis 1 — issuer BUSINESS type (EDGAR SIC). A BLANK/unknown SIC is excluded, not
            # admitted: a blank SIC is exactly how a BDC/fund slips a denylist (`None` is never `in`
            # the exclude set — CION, OTF). Then drop the confirmed fund/shell codes.
            sic, sic_desc = resolver.sic_for(ident.cik)
            if sic is None:
                # cannot confirm operating-co → excluded, not admitted
                _drop(ident.eod_symbol, "unknown_sic", "no SIC on the EDGAR issuer record",
                      StampedInput(value=None, source="EDGAR submissions SIC"))
                continue
            if sic in band.excluded_sic_codes:
                # ETF/ETP/fund/blank-check — a basket, not a business
                _drop(ident.eod_symbol, "non_operating", f"SIC {sic} ({sic_desc or '?'}) excluded",
                      StampedInput(value=str(sic), as_of=reference_date,
                                   source="EDGAR submissions SIC"))
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
                stage = "unknown_type" if ptype is None else "non_common_equity"
                _drop(ident.eod_symbol, stage,
                      f"security type {ptype or 'MISSING'} not in the operating-equity allowlist",
                      StampedInput(value=(ptype if ptype else None), as_of=reference_date,
                                   source="Polygon security reference"))
                continue
            stats["in_universe"] += 1
            # Persist the SIC we ALREADY fetched (above, for the Axis-1 gate) onto the identity so
            # it flows into the committed securities/issuers snapshots — was a dead write (fetched,
            # gated on, then discarded via [0]). The coarse SECTOR is derived downstream
            # (sectors.sector_for_sic); SIC itself is never a screen/rank/verdict input.
            ident = ident.model_copy(update={"sic": sic, "sic_description": sic_desc})
            store.upsert_security(ident, first_seen=reference_date)
            store.record_universe(
                as_of=reference_date,
                internal_id=ident.internal_id,
                in_universe=True,
                market_cap=DataField.present(
                    market_cap, as_of=reference_date, source="DERIVED", tier=SourceTier.DERIVED
                ),
            )
        store.export_snapshots(cfg.snapshots_dir, tables=BUILD_UNIVERSE_TABLES)
    # Persist the fail-closed gate-exclusion counts as a committed health snapshot (the ops
    # dashboard reads these; a wrong count signals a gate bug). Derived counts only — no licensed
    # data. SIC-denylist drops = unknown_sic + non_operating; type-allowlist = unknown_type +
    # non_common_equity.
    stats_out = dict(stats)
    payload = {
        "as_of": reference_date.isoformat(),
        "market_cap_min_usd": band.market_cap_min_usd,
        "market_cap_max_usd": band.market_cap_max_usd,
        "adv_floor_usd": band.adv_floor_usd,
        **stats_out,
    }
    (cfg.snapshots_dir / "universe_stats.json").write_text(json.dumps(payload, indent=2) + "\n")
    if retain_run_id is not None and retain_dir is not None:
        # THE COUNT MUST MATCH THE ROWS, or the thin grain is quietly incomplete. Every stage that
        # increments a stat also appends a row, so a divergence means a drop path was added without
        # its evidence — the exact way a blind spot re-opens after being closed.
        expected = sum(stats_out.get(k, 0) for k in DROP_STAGES)
        if len(dropped) != expected:
            raise ValueError(
                f"retention emitted {len(dropped)} thin rows against {expected} counted drops — a "
                "drop path is not writing its row")
        stats_out["retained_universe_rows"] = append_rows(
            dropped, run_id=retain_run_id, snapshots_dir=retain_dir)
    return stats_out
