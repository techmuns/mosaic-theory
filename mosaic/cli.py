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
from mosaic.orchestrator import run_monthly, run_weekly
from mosaic.resolver import EntityResolver, ResolutionError
from mosaic.schemas.ledger import Confidence, Verdict
from mosaic.scoring import score_ledger
from mosaic.screens import screen_universe
from mosaic.store import Store
from mosaic.universe import build_universe


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


def _cmd_build_universe(args: argparse.Namespace) -> int:
    """Build + snapshot the cap-band universe (market cap = close × XBRL shares)."""
    cfg = get_config()
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    stats = build_universe(reference_date=ref)
    band = cfg.universe
    lo, hi = band.market_cap_min_usd / 1e6, band.market_cap_max_usd / 1e9
    print(f"universe @ {ref} [${lo:.0f}M–${hi:.0f}B, {'/'.join(band.exchanges)}]: {stats}")
    return 0


def _cmd_screen(args: argparse.Namespace) -> int:
    """Run Screen 2 (lazily) across the cap-band universe; print the candidate list."""
    cfg = get_config()
    cfg.ensure_dirs()
    eod = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    with Store(cfg.db_path) as store:
        cands, stats = screen_universe(
            store, eod, edgar, reference_date=ref, lookback_days=args.lookback_days,
            staleness_days=cfg.price_staleness_days, benchmark=args.benchmark,
        )
        store.export_snapshots(cfg.snapshots_dir)
    print(f"=== Screen 2 · {stats['universe']} names · ref {ref} · benchmark {args.benchmark} ===")
    print(
        f"price-gate survivors (G1 pass, G2 not-fail): {stats['g1_g2_survivors']} · "
        f"candidates: {stats['candidates']}"
    )
    for c in sorted(cands, key=lambda c: c.data_record.prices.drawdown_from_high.value or 0):
        d = c.data_record
        print(
            f"  • {d.identity.ticker:<6} [{c.triage_band.value}] "
            f"dd {d.prices.drawdown_from_high.value:.0%}  {d.identity.name[:42]}"
        )
        print(f"      trigger: {c.trigger_reason}")
        print(f"      twin: {c.twin_to_rule_out} | depth: {c.unknown_gates_for_depth}")
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


def _cmd_run_weekly(args: argparse.Namespace) -> int:
    """Scheduled weekly job: refresh the universe + run the screen + export snapshots."""
    end = date.fromisoformat(args.end) if args.end else date.today()
    print(f"weekly run: {run_weekly(end=end, benchmark=args.benchmark)}")
    return 0


def _cmd_run_monthly(args: argparse.Namespace) -> int:
    """Scheduled monthly job: score the ledger + write the report + export snapshots."""
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    report = run_monthly(as_of=as_of, benchmark=args.benchmark, cost_bps=args.cost_bps)
    print(f"monthly run: spread={report['buy_avoid_spread']} pending={report['n_pending']}")
    return 0


def _cmd_graph_test0(args: argparse.Namespace) -> int:
    """Score the EDGAR who-names-whom graph against the CIQ ground truth (graph-track Test 0)."""
    import json
    from pathlib import Path

    from mosaic.ciq import LocalFolderManualStore, load_ciq_edges
    from mosaic.graph import AnthropicLlmClient
    from mosaic.graph.test0 import score_test0

    cfg = get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    llm = AnthropicLlmClient(model=args.model or cfg.graph_llm_model)
    ciq_dir = Path(args.ciq_dir) if args.ciq_dir else cfg.data_dir / "manual" / "ciq"
    ciq_edges, _ = load_ciq_edges(LocalFolderManualStore(ciq_dir), resolver)

    report = score_test0(edgar, resolver, llm, ciq_edges, max_focals=args.max_focals)
    print(
        f"=== Graph Test 0 · model {report['model']} · "
        f"{report['focals_scored']} focals vs CIQ ground truth ==="
    )
    print(
        f"precision {report['precision']:.0%} · recall {report['recall']:.0%} (coverage-limited) · "
        f"resolution-rate {report['resolution_rate']:.0%} · "
        f"TP {report['true_positives']} / spurious {report['spurious']} / missed {report['missed']}"
    )
    for f in report["per_focal"]:
        print(
            f"  • {f['focal']:<6} {f['status']:<8} extracted {f['edges_extracted']:>2} "
            f"(resolved {f['edges_resolved']:>2}) · CIQ {f['ciq_truth']:>3} · "
            f"matched {len(f['matched']):>2} · spurious {len(f['spurious']):>2}"
        )
    if args.json:
        dump = {k: v for k, v in report.items() if k != "edges"}
        dump["edges"] = [e.model_dump() for e in report["edges"]]
        # NOT into snapshots/: the per-focal CIK lists are derived from the licensed CIQ ground
        # truth, so this artifact stays in the git-ignored data root, never committed.
        out = cfg.data_dir / "graph_test0.json"
        out.write_text(json.dumps(dump, indent=2))
        print(f"wrote {out} (git-ignored — contains CIQ-derived comparison)")
    return 0


def _cmd_graph_coverage(args: argparse.Namespace) -> int:
    """Build + measure the 1-hop graph on the small/mid screen universe (moat-readiness read)."""
    import json

    from mosaic.graph import AnthropicLlmClient
    from mosaic.graph.coverage import graph_coverage

    cfg = get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    llm = AnthropicLlmClient(model=args.model or cfg.graph_llm_model)
    with Store(cfg.db_path) as store:
        if args.sic:  # a SIC slice of the universe (e.g. semis/electronics → foreign hubs)
            prefixes = tuple(args.sic.split(","))
            ref = date.fromisoformat(args.ref) if args.ref else date.today()
            label = f"SIC {args.sic}"
            focals = []
            for iid in store.latest_universe(ref):
                s = store.get_security(iid)
                if s is None:
                    continue
                sic = resolver.sic_for(s.cik)[0]
                if sic and sic.startswith(prefixes):
                    focals.append(s)
        else:
            label = f"{args.band or 'all'}-band"
            ids = store.candidate_internal_ids(band=args.band)
            focals = [s for iid in ids if (s := store.get_security(iid)) is not None]
    if args.max_names:
        focals = focals[: args.max_names]

    sc_degree = args.super_connector_degree or cfg.graph_super_connector_degree
    rep = graph_coverage(edgar, resolver, llm, focals, super_connector_degree=sc_degree)
    print(f"=== Graph coverage · {rep['model']} · {rep['n_names']} {label} small/mid names ===")
    print(
        f"edges {rep['total_edges']} ({rep['names_with_edges']} names w/ edges) · density "
        f"{rep['edges_per_name']}/name · real {rep['real_edges_per_name']}/name"
    )
    print(
        f"evidence-precision {rep['evidence_precision']:.0%} ({rep['real_edges']} real = "
        f"{rep['real_us_listed']} US-listed + {rep['real_global']} global) · {rep['by_class']}"
    )
    sc = rep["super_connectors"]
    if sc:
        print(f"super-connectors excluded ({len(sc)}, named ≥{sc_degree} hubs): {', '.join(sc)}")
    shared = rep["shared_nodes"]
    print(f"\n--- shared nodes (2+ INDEPENDENT names) — the Test-1 (a) set: {len(shared)} ---")
    for s in shared:
        kind = "US" if s["node_kind"] == "us_listed" else "global"
        tag = s["ticker"] or s["node_id"].split(":", 1)[-1][:18]
        print(f"  {s['degree']}x  {s['name'][:30]:<30} [{kind}:{tag}]  <- {', '.join(s['focals'])}")
    if args.json:
        out = cfg.data_dir / "graph_coverage.json"
        out.write_text(json.dumps(rep, indent=2))
        print(f"wrote {out} (git-ignored)")
    return 0


def _cmd_graph_exposure(args: argparse.Namespace) -> int:
    """Given an entity/event, list its N-hop exposed names from the graph (discriminator input)."""
    import json

    from mosaic.graph.exposure import ExposureGraph

    cfg = get_config()
    resolver = EntityResolver.from_config(cfg)
    path = cfg.data_dir / "graph_coverage.json"
    if not path.exists():
        print("no graph yet — run `mosaic graph-coverage` first")
        return 1
    g = ExposureGraph.from_edges(json.loads(path.read_text())["edges"])
    start = g.resolve(args.entity, resolver)
    if start is None:
        print(f"{args.entity!r} is not in the current graph (run coverage on its neighbourhood)")
        return 1
    exposed = g.exposed_within(start, hops=args.hops)
    name0 = g.display.get(start, (args.entity, None))[0]
    print(f"=== exposed to {name0} within {args.hops} hop(s): {len(exposed)} names ===")
    for x in exposed:
        print(f"  [{x.hops}h] {(x.ticker or x.node_id):<8} {x.name[:34]:<34}")
        print(f"        via: {' · '.join(x.path)}")
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

    p_univ = sub.add_parser("build-universe", help="build the cap-band universe")
    p_univ.add_argument("--ref", help="as-of date YYYY-MM-DD (default: today)")
    p_univ.set_defaults(func=_cmd_build_universe)

    p_screen = sub.add_parser("screen", help="run Screen 2 across the cap-band universe")
    p_screen.add_argument("--benchmark", default="IWM", help="benchmark ETF for G2 (default: IWM)")
    p_screen.add_argument("--ref", help="reference date YYYY-MM-DD (default: today)")
    p_screen.add_argument(
        "--lookback-days", type=int, default=1825, dest="lookback_days",
        help="price history to refresh (default: 1825 = 5y, for G3)",
    )
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

    p_weekly = sub.add_parser("run-weekly", help="scheduled: refresh + screen + export snapshots")
    p_weekly.add_argument("--end", help="end date YYYY-MM-DD (default: today)")
    p_weekly.add_argument("--benchmark", default="IWM")
    p_weekly.set_defaults(func=_cmd_run_weekly)

    p_monthly = sub.add_parser("run-monthly", help="scheduled: score the ledger + export report")
    p_monthly.add_argument("--as-of", dest="as_of", help="as-of date YYYY-MM-DD (default: today)")
    p_monthly.add_argument("--benchmark", default="IWM")
    p_monthly.add_argument("--cost-bps", type=float, default=25.0, dest="cost_bps")
    p_monthly.set_defaults(func=_cmd_run_monthly)

    p_t0 = sub.add_parser("graph-test0", help="score the EDGAR graph vs CIQ ground truth (Test 0)")
    p_t0.add_argument("--model", help="LLM model id (default: config; claude-opus-4-8 to diagnose)")
    p_t0.add_argument("--ciq-dir", dest="ciq_dir", help="CIQ exports folder (data/manual/ciq)")
    p_t0.add_argument("--max-focals", type=int, dest="max_focals", help="limit focals (smoke test)")
    p_t0.add_argument("--json", action="store_true", help="write graph_test0.json (git-ignored)")
    p_t0.set_defaults(func=_cmd_graph_test0)

    p_cov = sub.add_parser("graph-coverage", help="build+measure the 1-hop graph on screen names")
    p_cov.add_argument("--band", default="A", help="triage band to build on (default: A)")
    p_cov.add_argument("--sic", help="instead of a band: a universe SIC slice, e.g. 3674,357,367")
    p_cov.add_argument("--ref", help="universe as-of date for --sic (default: today)")
    p_cov.add_argument("--max-names", type=int, dest="max_names", help="limit names (sample)")
    p_cov.add_argument("--model", help="LLM model id (default: config graph_llm_model)")
    p_cov.add_argument("--super-connector-degree", type=int, dest="super_connector_degree",
                       help="override: a focal naming this many hubs is excluded (default 6)")
    p_cov.add_argument("--json", action="store_true", help="write graph_coverage.json (ignored)")
    p_cov.set_defaults(func=_cmd_graph_coverage)

    p_exp = sub.add_parser("graph-exposure", help="given an entity/event, list N-hop exposed names")
    p_exp.add_argument("--entity", required=True, help="ticker or company name of the shocked node")
    p_exp.add_argument("--hops", type=int, default=2, help="reachability radius (default: 2)")
    p_exp.set_defaults(func=_cmd_graph_exposure)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
