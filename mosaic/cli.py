"""``mosaic`` command-line entrypoint.

Grown one subcommand per build step. Today: ``resolve`` (step 1). Later: ``refresh`` (steps 3–4),
``screen`` (step 5), ``log-verdict`` (step 6), ``score`` (step 7).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date

from mosaic.config import get_config
from mosaic.eod import PolygonEodClient, compute_price_features, ingest_prices
from mosaic.resolver import EntityResolver, ResolutionError
from mosaic.store import Store


def _cmd_resolve(args: argparse.Namespace) -> int:
    """Resolve tickers and print the identity table (face-validity eyeballing)."""
    resolver = EntityResolver.from_config()
    header = f"{'INPUT':<10}{'CIK':<12}{'TICKER':<8}{'EXCH':<14}{'EOD':<8}{'SIC':<6}{'NAME'}"
    print(header)
    print("-" * len(header))
    exit_code = 0
    for raw in args.tickers:
        try:
            ident = resolver.resolve_ticker(raw, enrich=args.enrich)
        except ResolutionError as exc:
            print(f"{raw:<10}FAIL-LOUD: {type(exc).__name__}: {exc}")
            exit_code = 0  # fail-loud is correct behaviour, not a CLI error
            continue
        print(
            f"{raw:<10}{ident.cik:<12}{ident.ticker:<8}{ident.exchange:<14}"
            f"{ident.eod_symbol:<8}{ident.sic or '-':<6}{ident.name}"
        )
    return exit_code


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Backfill/refresh Polygon EOD bars for the given tickers into the store."""
    cfg = get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    client = PolygonEodClient.from_config(cfg)
    secs = []
    for t in args.tickers:
        try:
            secs.append(resolver.resolve_ticker(t))
        except ResolutionError as exc:
            print(f"skip {t}: {exc}")
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    print(f"refreshing {len(secs)} names {start}..{end} (Polygon free tier ≈ 5/min; be patient)…")
    with Store(cfg.db_path) as store:
        for s in secs:
            store.upsert_security(s)
        summary = ingest_prices(client, store, secs, start=start, end=end)
    print(f"done: {summary}")
    return 0


def _cmd_eod(args: argparse.Namespace) -> int:
    """Compute and print Screen-2 price features for a ticker from stored bars (face-validity)."""
    cfg = get_config()
    resolver = EntityResolver.from_config(cfg)
    ident = resolver.resolve_ticker(args.ticker)
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    with Store(cfg.db_path) as store:
        bars = store.get_price_history(ident.internal_id)
    if not bars:
        print(f"no stored bars for {ident.ticker}; run `mosaic refresh` first")
        return 1
    f = compute_price_features(bars, reference_date=ref, staleness_days=cfg.price_staleness_days)
    span = f"{bars[0].bar_date}..{bars[-1].bar_date} ({len(bars)} bars)"
    print(f"=== {ident.ticker} ({ident.name})  features as of {ref}  [{span}] ===")
    for label, field in [
        ("last close", f.last), ("52w high", f.high_52w), ("52w low", f.low_52w),
        ("drawdown from high", f.drawdown_from_high), ("dist from low", f.dist_from_low),
        ("return 3m", f.ret_3m), ("return 6m", f.ret_6m), ("return 12m", f.ret_12m),
        ("90d ADV (sh)", f.adv_90d_shares), ("90d ADV ($)", f.adv_90d_usd),
        ("volume spike", f.volume_spike),
    ]:
        v = f"{field.value:,.4g}" if isinstance(field.value, (int, float)) else "—"
        print(f"  {label:<20} {field.coverage_status.value:<8} {v}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mosaic", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="resolve tickers to the canonical identity")
    p_resolve.add_argument("tickers", nargs="+", help="tickers to resolve (e.g. AAPL BRK.B)")
    p_resolve.add_argument(
        "--enrich", action="store_true", help="also fetch SIC sector from EDGAR submissions"
    )
    p_resolve.set_defaults(func=_cmd_resolve)

    p_refresh = sub.add_parser("refresh", help="backfill/refresh Polygon EOD bars into the store")
    p_refresh.add_argument("tickers", nargs="+", help="tickers to refresh")
    p_refresh.add_argument("--start", required=True, help="start date YYYY-MM-DD")
    p_refresh.add_argument("--end", required=True, help="end date YYYY-MM-DD")
    p_refresh.set_defaults(func=_cmd_refresh)

    p_eod = sub.add_parser("eod", help="show computed Screen-2 price features for a ticker")
    p_eod.add_argument("ticker", help="ticker (e.g. AAPL)")
    p_eod.add_argument("--ref", help="reference date YYYY-MM-DD (default: today)")
    p_eod.set_defaults(func=_cmd_eod)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
