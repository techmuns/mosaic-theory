"""``mosaic`` command-line entrypoint.

Grown one subcommand per build step. Today: ``resolve`` (step 1). Later: ``refresh`` (steps 3–4),
``screen`` (step 5), ``log-verdict`` (step 6), ``score`` (step 7).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from datetime import date, datetime

from mosaic.config import get_config
from mosaic.edgar import EdgarClient
from mosaic.eod import PolygonEodClient, compute_price_features, ingest_prices
from mosaic.ledger import LedgerError, log_verdict
from mosaic.resolver import EntityResolver, ResolutionError
from mosaic.schemas.data_record import Identity
from mosaic.schemas.ledger import Confidence, Verdict
from mosaic.scoring import score_ledger
from mosaic.screens import (
    Screen2Thresholds,
    build_data_record,
    evaluate_screen2,
    gate_g1_drawdown,
    gate_g2_idiosyncratic,
    gate_g3_multiple_floor,
)
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
        ("last close", f.last),
        ("52w high", f.high_52w),
        ("52w low", f.low_52w),
        ("drawdown from high", f.drawdown_from_high),
        ("dist from low", f.dist_from_low),
        ("return 3m", f.ret_3m),
        ("return 6m", f.ret_6m),
        ("return 12m", f.ret_12m),
        ("90d ADV (sh)", f.adv_90d_shares),
        ("90d ADV ($)", f.adv_90d_usd),
        ("volume spike", f.volume_spike),
    ]:
        v = f"{field.value:,.4g}" if isinstance(field.value, (int, float)) else "—"
        print(f"  {label:<20} {field.coverage_status.value:<8} {v}")
    return 0


def _benchmark_identity(symbol: str) -> Identity:
    """A synthetic identity for a benchmark ETF (not a SEC issuer, so not resolver-resolved)."""
    return Identity(
        internal_id=f"IDX-{symbol}",
        issuer_id="IDX",
        cik="",
        ticker=symbol,
        mic="ARCX",
        exchange="ETF",
        eod_symbol=symbol,
        name=f"{symbol} (benchmark)",
    )


def _cmd_screen(args: argparse.Namespace) -> int:
    """Run Screen 2 across the stored universe; print the gate matrix and candidates."""
    cfg = get_config()
    cfg.ensure_dirs()
    edgar = EdgarClient.from_config(cfg)
    client = PolygonEodClient.from_config(cfg)
    th = Screen2Thresholds()
    bench = _benchmark_identity(args.benchmark)
    with Store(cfg.db_path) as store:
        rng = store._conn.execute(
            "SELECT MIN(bar_date) a, MAX(bar_date) b FROM prices WHERE internal_id NOT LIKE 'IDX-%'"
        ).fetchone()
        if not rng or not rng["a"]:
            print("no prices stored; run `mosaic refresh` first")
            return 1
        start, end = date.fromisoformat(rng["a"]), date.fromisoformat(rng["b"])
        ref = date.fromisoformat(args.ref) if args.ref else end

        store.upsert_security(bench)
        if not store.get_price_history(bench.internal_id):
            ingest_prices(client, store, [bench], start=start, end=end)  # cache hits → instant
        bench_bars = store.get_price_history(bench.internal_id)

        secs = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
        print(f"=== Screen 2 · {len(secs)} names · ref {ref} · benchmark {args.benchmark} ===")
        print(f"{'TICKER':<7}{'G1_dd':<8}{'G2_idio':<9}{'G3_mult':<9}verdict")
        admitted = []
        run_at = datetime.combine(ref, datetime.min.time())
        for s in secs:
            rec = build_data_record(
                s,
                price_bars=store.get_price_history(s.internal_id),
                benchmark_bars=bench_bars,
                edgar=edgar,
                reference_date=ref,
                staleness_days=cfg.price_staleness_days,
            )
            g1, g2, g3 = (
                gate_g1_drawdown(rec, th)[0],
                gate_g2_idiosyncratic(rec, th)[0],
                gate_g3_multiple_floor(rec, th)[0],
            )
            cand = evaluate_screen2(rec, screen_run_at=run_at, thresholds=th)
            verdict = "CANDIDATE" if cand else "reject"
            print(f"{s.ticker:<7}{g1.value:<8}{g2.value:<9}{g3.value:<9}{verdict}")
            if cand:
                admitted.append(cand)
                store.save_candidate(cand)
        print(f"\n{len(admitted)} candidate(s) emitted to the store:")
        for c in admitted:
            d = c.data_record
            print(
                f"  • {d.identity.ticker} [band {c.triage_band.value}]  drawdown "
                f"{d.prices.drawdown_from_high.value:.0%}"
            )
            print(f"      trigger: {c.trigger_reason}")
            print(f"      twin: {c.twin_to_rule_out} | depth tasks: {c.unknown_gates_for_depth}")
    return 0


def _cmd_log_verdict(args: argparse.Namespace) -> int:
    """Record a manual BUY/AVOID-terminal verdict for a candidate, freezing the entry price."""
    cfg = get_config()
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    with Store(cfg.db_path) as store:
        try:
            entry = log_verdict(
                store, candidate_id=args.candidate_id, verdict=Verdict(args.verdict),
                twin_call=args.twin, thesis=args.thesis, kill_criteria=args.kill,
                horizon_days=args.horizon_days, confidence=Confidence(args.confidence),
                decided_at=datetime.now(), reference_date=ref,
                staleness_days=cfg.price_staleness_days, benchmark=args.benchmark,
            )
        except LedgerError as exc:
            print(f"could not log verdict: {exc}")
            return 1
        except sqlite3.IntegrityError:
            print(f"a verdict is already logged for {args.candidate_id} (ledger is append-only)")
            return 1
    print(
        f"logged {entry.verdict.value} for {entry.ticker}: frozen entry "
        f"{entry.entry_price:.2f} as_of {entry.entry_price_as_of}, horizon {entry.horizon_days}d"
    )
    return 0


def _cmd_ledger(args: argparse.Namespace) -> int:
    """List all recorded paper verdicts (BUY and AVOID alike)."""
    cfg = get_config()
    with Store(cfg.db_path) as store:
        entries = list(store.iter_ledger())
    if not entries:
        print("decision ledger is empty")
        return 0
    print(f"{'TICKER':<7}{'VERDICT':<16}{'ENTRY':>9}{'AS_OF':>13}{'HORIZON':>9}  DECIDED")
    for e in entries:
        print(
            f"{e.ticker:<7}{e.verdict.value:<16}{e.entry_price:>9.2f}"
            f"{str(e.entry_price_as_of):>13}{e.horizon_days:>8}d  {e.decided_at:%Y-%m-%d}"
        )
    return 0


def _cmd_score(args: argparse.Namespace) -> int:
    """Score the decision ledger and print the BUY−AVOID-spread report."""
    import json

    cfg = get_config()
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    with Store(cfg.db_path) as store:
        _scores, report = score_ledger(
            store, as_of=ref, cost_bps=args.cost_bps,
            benchmark_internal_id=f"IDX-{args.benchmark}",
        )
    print(report.to_markdown())
    if args.json:
        cfg.ensure_dirs()
        path = cfg.snapshots_dir / "scoring_report.json"
        path.write_text(json.dumps(report.to_dict(), indent=2, default=str))
        print(f"\nwrote {path}")
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

    p_screen = sub.add_parser("screen", help="run Screen 2 across the stored universe")
    p_screen.add_argument("--benchmark", default="IWM", help="benchmark ETF for G2 (default: IWM)")
    p_screen.add_argument("--ref", help="reference date YYYY-MM-DD (default: latest stored bar)")
    p_screen.set_defaults(func=_cmd_screen)

    p_log = sub.add_parser("log-verdict", help="record a manual BUY/AVOID verdict for a candidate")
    p_log.add_argument("candidate_id", help="candidate id from `mosaic screen`")
    p_log.add_argument("--verdict", required=True, choices=[v.value for v in Verdict])
    p_log.add_argument("--twin", required=True, help="how the terminal-decline twin was ruled out")
    p_log.add_argument("--thesis", required=True, help="short thesis / rationale")
    p_log.add_argument("--kill", required=True, help="kill-criteria that would falsify the thesis")
    p_log.add_argument("--horizon-days", type=int, required=True, dest="horizon_days")
    p_log.add_argument("--confidence", required=True, choices=[c.value for c in Confidence])
    p_log.add_argument("--benchmark", default="IWM", help="scoring benchmark (default: IWM)")
    p_log.add_argument("--ref", help="decision/entry-price date YYYY-MM-DD (default: today)")
    p_log.set_defaults(func=_cmd_log_verdict)

    p_ledger = sub.add_parser("ledger", help="list recorded paper verdicts")
    p_ledger.set_defaults(func=_cmd_ledger)

    p_score = sub.add_parser("score", help="score the ledger (BUY−AVOID spread + metrics)")
    p_score.add_argument("--benchmark", default="IWM", help="benchmark ETF (default: IWM)")
    p_score.add_argument("--cost-bps", type=float, default=25.0, dest="cost_bps")
    p_score.add_argument("--ref", help="as-of date YYYY-MM-DD (default: today)")
    p_score.add_argument("--json", action="store_true", help="also write the report JSON")
    p_score.set_defaults(func=_cmd_score)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
