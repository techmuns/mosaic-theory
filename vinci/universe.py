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
from vinci.edgar.client import SHARES_TAG_WAVG
from vinci.eod import EodClient, PolygonEodClient
from vinci.resolver import EntityResolver
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import DataField, SourceTier
from vinci.store import NO_ROW_DROP_TABLES, Store

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

#: The same export set for the PARALLEL THEME BAND (operator ruling 2026-08-31): the entity master
#: is SHARED and accumulate-only (a megacap identity is a fact about the world, not about a band),
#: while membership lands in the band's own point-in-time table. Deriving this from the primary
#: tuple keeps the two in step if the export set ever grows.
BUILD_THEME_UNIVERSE_TABLES: tuple[str, ...] = tuple(
    "theme_universe_snapshot" if t == "universe_snapshot" else t for t in BUILD_UNIVERSE_TABLES)

#: band -> (config attribute, store table, stats filename). The BUILDER IS BAND-AGNOSTIC: every
#: gate below reads `band`, so the theme band gets the identical operating-company /
#: tradeability / instrument-type discipline, differing ONLY in the cap bounds it was given.
UNIVERSE_BANDS: dict[str, tuple[str, str, str]] = {
    "primary": ("universe", "universe_snapshot", "universe_stats.json"),
    "theme": ("theme_universe", "theme_universe_snapshot", "theme_universe_stats.json"),
}

#: The subset of :data:`BUILD_UNIVERSE_TABLES` that may never SHRINK, DERIVED from the store's own
#: declaration rather than re-listed here — a hand-copied list is one edit away from silently
#: missing a table the day another accumulate-only one joins the export.
BUILD_UNIVERSE_SEED_TABLES: tuple[str, ...] = tuple(
    t for t in BUILD_UNIVERSE_TABLES if t in NO_ROW_DROP_TABLES)


#: EVERY drop this builder can make, in funnel order. Enumerated rather than described, because a
#: stage missing from the thin grain is a stage with no evidence trail — which just MOVES the blind
#: spot instead of closing it. Each is emitted with the one input that decided it.
DROP_STAGES: tuple[str, ...] = (
    "no_price", "no_shares", "out_of_band", "below_adv_floor",
    "unknown_sic", "non_operating", "unknown_type", "non_common_equity",
)


def build_universe(
    config: Config | None = None, *, reference_date: date, share_periods: list[str] | None = None,
    retain_run_id: str | None = None, retain_dir: Path | None = None, band_name: str = "primary",
) -> dict[str, int]:
    """Build + snapshot a cap-band universe as of ``reference_date``. Returns a stats summary.

    ``band_name`` selects WHICH population is built: ``"primary"`` (the forward-validation
    population every decision-path consumer reads) or ``"theme"`` (the parallel larger band read
    only at the theme altitude — operator ruling 2026-08-31). The two never share a table, so a
    theme build cannot add a row to the population the spread is accumulating against.

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
    if band_name not in UNIVERSE_BANDS:
        raise ValueError(f"unknown universe band {band_name!r} — expected one of "
                         f"{sorted(UNIVERSE_BANDS)}")
    band_attr, _band_table, stats_filename = UNIVERSE_BANDS[band_name]
    band = getattr(cfg, band_attr)
    export_tables = (BUILD_UNIVERSE_TABLES if band_name == "primary"
                     else BUILD_THEME_UNIVERSE_TABLES)

    closes, adv = latest_close_and_adv(eod, reference_date)
    sec_types = eod.security_types()  # instrument-type axis (one cached bulk reference pull)
    periods = share_periods or recent_share_periods(reference_date)
    # PERIOD-AVERAGE TIER ON, here only (2026-08-31): the cap band is a COARSE gate, and a filer
    # publishing no instant count was being dropped entirely — 142 operating equities above $100M
    # ADV, 104 recoverable this way (META among them). Every value carries its tag so the row it
    # stamps says which kind of number it is.
    shares, share_tag = edgar.shares_outstanding_with_provenance(
        periods, include_period_average=True)

    # IMPORTED HERE, NOT AT MODULE SCOPE. `vinci.screens.__init__` imports `run`, which imports
    # `vinci.universe` — so a module-scope import of anything under `vinci.screens` makes importing
    # `vinci.universe` FIRST a circular-import crash. It only fires on that import order, which is
    # why the suite stayed green and a real `build_universe` run did not.
    from vinci.screens.retention import StampedInput, UniverseRow, append_rows

    stats: Counter[str] = Counter()
    dropped: list[UniverseRow] = []

    def _drop(ticker: str, stage: str, reason: str, inp: StampedInput) -> None:
        stats[stage] += 1
        if retain_run_id is not None:
            dropped.append(UniverseRow(
                ticker=ticker, run_id=retain_run_id, reference_date=reference_date,
                stage=stage, reason=reason, deciding_input=inp))

    with Store(cfg.db_path) as store:
        # SEED THE ACCUMULATE-ONLY MASTER BEFORE TOUCHING IT (2026-08-24). `data/vinci.db` is
        # git-ignored, so on any fresh checkout — every CI run — this store starts EMPTY. The loop
        # below upserts only what THIS fetch admits, and the export at the end then writes that
        # subset over `issuers.jsonl` / `securities.jsonl`, which are accumulate-only: an identity
        # is never pruned, because the entity master has to resolve a ledgered name after it leaves
        # the universe. The no-row-drop guard therefore REFUSED the write, and the weekly screen
        # failed four consecutive weeks (2026-08-03 through 08-24) with the served queue frozen:
        #
        #   ROW-DROP on issuers.jsonl: writing 1810 row(s) over 2304 on disk
        #   would drop 503 existing row(s) by PK.
        #
        # It passed on a laptop the whole time, because a dev store already holds the accumulation
        # — the "green everywhere except where it matters" shape. `run_weekly` does seed the store,
        # but at its own line AFTER this function has already exported; the seed has to happen
        # HERE, inside the context that writes.
        #
        # SEEDS ONLY THE TABLES THAT MUST NOT SHRINK. `universe_snapshot` is POINT-IN-TIME — the
        # committed file holds exactly one `as_of` — so loading it back would make it accumulate
        # dates it was never meant to keep, turning a fix for one table into a silent semantic
        # change in another.
        store.rebuild_from_snapshots(cfg.snapshots_dir, tables=BUILD_UNIVERSE_SEED_TABLES)
        # FULL replace, THIS BAND ONLY — a rebuild is a clean snapshot, not an accretion
        store.clear_universe(band=band_name)
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
                      StampedInput(value=None,
                                   source="EDGAR share frames (instant tiers + period average)"))
                continue
            market_cap = close * sh
            # WHICH KIND OF SHARE COUNT DECIDED THIS NAME — computed BEFORE the band test, because
            # the drop path needs it too (review 2026-08-31): the period-average tier newly sizes
            # names that then fall OUT of band, and a retention row claiming a filed EDGAR count
            # as its deciding input would misattribute an exclusion the approximation made.
            tag = share_tag.get(ident.cik, "")
            approximate = tag == SHARES_TAG_WAVG
            shares_source = (f"Polygon close x EDGAR {tag}"
                             + (" (PERIOD AVERAGE - approximate share count)"
                                if approximate else ""))
            if not (band.market_cap_min_usd <= market_cap <= band.market_cap_max_usd):
                if approximate:
                    stats["out_of_band_period_average"] += 1
                _drop(ident.eod_symbol, "out_of_band",
                      f"market cap {market_cap / 1e6:,.1f}M outside "
                      f"[{band.market_cap_min_usd / 1e6:,.0f}M, "
                      f"{band.market_cap_max_usd / 1e6:,.0f}M]",
                      StampedInput(value=market_cap, as_of=reference_date,
                                   source=shares_source))
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
            # Stamped on the admitted row and counted in the run's health numbers, so an
            # approximate cap never blends in silently. (`shares_source` was derived above, where
            # the out-of-band drop path needs the same provenance.)
            if approximate:
                stats["shares_period_average"] += 1
            cap_source = shares_source
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
                    market_cap, as_of=reference_date, source=cap_source, tier=SourceTier.DERIVED
                ),
                band=band_name,
            )
        store.export_snapshots(cfg.snapshots_dir, tables=export_tables)
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
    payload["band"] = band_name   # the population this count describes — never inferred
    (cfg.snapshots_dir / stats_filename).write_text(json.dumps(payload, indent=2) + "\n")
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
