"""``vinci`` command-line entrypoint.

Grown one subcommand per build step. Today: ``resolve`` (step 1). Later: ``refresh`` (steps 3–4),
``screen`` (step 5), ``log-verdict`` (step 6), ``score`` (step 7).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from vinci.config import get_config, load_local_env
from vinci.edgar import EdgarClient
from vinci.eod import PolygonEodClient, compute_price_features, ingest_prices
from vinci.ledger import LedgerError, log_verdict
from vinci.orchestrator import run_monthly, run_weekly
from vinci.progress import stderr_reporter
from vinci.rank import (
    RankWeights,
    StructuralDisqualifier,
    load_candidates_from_snapshot,
    load_cause_annotations,
    load_market_caps_from_snapshot,
    rank_candidates,
    render_profile_block,
    render_queue_markdown,
)
from vinci.resolver import EntityResolver, ResolutionError
from vinci.schemas.ledger import Confidence, Verdict
from vinci.scoring import score_ledger
from vinci.screens import screen_universe
from vinci.store import Store
from vinci.universe import build_universe


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
        summary = ingest_prices(client, store, secs, start=start, end=end, progress=stderr_reporter)
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
        print(f"no stored bars for {ident.ticker}; run `vinci refresh` first")
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
            progress=stderr_reporter,
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


def _cmd_rank(args: argparse.Namespace) -> int:
    """Order the screen's candidates into a priority queue + print the top-N structural profiles.

    Reads the committed snapshots (no DB, no network): ``candidate_records.jsonl`` for the screen
    output and ``universe_snapshot.jsonl`` for size. Orders, never decides — see ``vinci.rank``.
    """
    from pathlib import Path

    cfg = get_config()
    snaps = cfg.snapshots_dir
    cands = load_candidates_from_snapshot(snaps / "candidate_records.jsonl")
    if not cands:
        print(f"no candidates in {snaps / 'candidate_records.jsonl'} — run `vinci screen` first")
        return 1
    caps = load_market_caps_from_snapshot(snaps / "universe_snapshot.jsonl")
    annotations = load_cause_annotations(Path(args.cause_file)) if args.cause_file else {}

    structural_flags: dict[str, StructuralDisqualifier] = {}
    if args.structural:
        from vinci.edgar.client import EdgarClient
        from vinci.rank import scan_structural
        from vinci.sec import build_sec_http

        print(
            f"scanning {len(cands)} candidates for structural disqualifiers "
            f"(EDGAR 8-K text + shares; DEMOTE-ONLY)…"
        )
        structural_flags = scan_structural(
            cands, edgar=EdgarClient.from_config(cfg), http=build_sec_http(cfg)
        )

    ranked = rank_candidates(
        cands, weights=RankWeights(), annotations=annotations,
        market_caps=caps, deep_work_adv_floor=args.deep_work_adv_floor,
        structural_flags=structural_flags or None,
    )
    n_unknown = sum(1 for r in ranked if r.unknown_axes)
    n_gated = sum(1 for r in ranked if r.tradeability_gated)
    disqualified = [r for r in ranked if r.structurally_disqualified]
    print(
        f"=== Ranked queue · {len(ranked)} candidates · weights "
        f"idio .30 / depth .25 / character .25 / mult .20 "
        f"(face-validity, never returns) ==="
    )
    print(
        f"top {args.top} shown · {n_unknown} carry an UNKNOWN axis (flagged) · "
        f"{n_gated} tradeability-gated · LLM cause annotations: {len(annotations)}\n"
    )
    if args.structural:
        print(
            f"--- structural disqualifiers (Tier-3, DEMOTE-ONLY): {len(disqualified)} of "
            f"{len(ranked)} sunk ---"
        )
        for r in disqualified:
            assert r.structural_flag is not None  # disqualified ⇒ flag present
            print(
                f"  ⛔ {r.ticker:<6} {r.structural_flag.signal}  ·  {r.structural_flag.source}"
            )
        print()
    for r in ranked[: args.top]:
        print(render_profile_block(r))
        print()

    if not args.no_write:
        cfg.ensure_dirs()
        jsonl = snaps / "ranked_queue.jsonl"
        with jsonl.open("w") as f:
            for r in ranked:
                f.write(r.model_dump_json() + "\n")
        md = snaps / "ranked_queue.md"
        md.write_text(render_queue_markdown(ranked, top=args.md_top))
        print(f"wrote {jsonl} ({len(ranked)} rows) and {md} (top {args.md_top})")
    return 0


def _cmd_dossier(args: argparse.Namespace) -> int:
    """Assemble per-finalist dossiers (top N, or one --ticker). Assembles, never concludes.

    The ``requirements`` mode instead prints the canonical manual-CIQ manifest (export checklist, or
    ``--json`` for the upload UI) — the single source the MISSING-manifest path also reads."""
    if getattr(args, "mode", "assemble") == "requirements":
        from vinci.dossier import requirements

        if args.json:
            print(json.dumps(requirements.as_payload(args.ticker), indent=2))
        else:
            print(requirements.render_checklist(args.ticker))
        return 0

    from vinci.dossier.assemble import assemble_cohort, load_finalists

    cfg = get_config()
    cfg.ensure_dirs()
    finalists = load_finalists(cfg, top=args.top, ticker=args.ticker)
    if not finalists:
        print("no finalists — run `vinci screen` then `vinci rank` first")
        return 1
    llm = None
    if not args.no_llm:
        from vinci.graph.llm import AnthropicLlmClient

        try:
            llm = AnthropicLlmClient.from_config(cfg)
        except Exception as exc:  # noqa: BLE001 — degrade to mechanical-only, never crash the CLI
            print(f"LLM unavailable ({exc}) — assembling the mechanical layer only")
    dossiers, errors = assemble_cohort(finalists, cfg=cfg, llm=llm)
    out = cfg.data_dir / "dossiers"
    print(f"=== dossier · {len(dossiers)} done · {len(errors)} error(s) · → {out}/<ticker>/ ===")
    for d in sorted(dossiers, key=lambda d: d.rank or 1_000_000):
        print(f"  {d.ticker:<6} rank {d.rank} · {'synth' if d.synthesis else 'NO-synth'} · "
              f"{len(d.caveats)} caveat(s) · {len(d.qa_flags)} qa")
        for c in d.caveats:
            print(f"      ⚠ {c}")
    for e in errors:
        print(f"  ERROR {e}")
    return 0


def _cmd_log_verdict(args: argparse.Namespace) -> int:
    """Record a manual BUY/AVOID-terminal verdict for a candidate, freezing the entry price."""
    cfg = get_config()
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    resolver = EntityResolver.from_config(cfg)  # sources the name's EDGAR SIC → sector at log time
    with Store(cfg.db_path) as store:
        try:
            entry = log_verdict(
                store, resolver=resolver, candidate_id=args.candidate_id,
                verdict=Verdict(args.verdict),
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
        f"logged {entry.verdict.value} for {entry.ticker} [sector: {entry.sector}]: frozen entry "
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
    print(f"weekly run: {run_weekly(end=end, benchmark=args.benchmark, progress=stderr_reporter)}")
    return 0


def _cmd_run_monthly(args: argparse.Namespace) -> int:
    """Scheduled monthly job: score the ledger + write the report + export snapshots."""
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    report = run_monthly(
        as_of=as_of, benchmark=args.benchmark, cost_bps=args.cost_bps, progress=stderr_reporter
    )
    print(f"monthly run: spread={report['buy_avoid_spread']} pending={report['n_pending']}")
    return 0


def _cmd_graph_test0(args: argparse.Namespace) -> int:
    """Score the EDGAR who-names-whom graph against the CIQ ground truth (graph-track Test 0)."""
    import json
    from pathlib import Path

    from vinci.ciq import LocalFolderManualStore, load_ciq_edges
    from vinci.graph import AnthropicLlmClient
    from vinci.graph.test0 import score_test0

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

    from vinci.graph import AnthropicLlmClient
    from vinci.graph.coverage import graph_coverage

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

    from vinci.graph.exposure import ExposureGraph

    cfg = get_config()
    resolver = EntityResolver.from_config(cfg)
    path = cfg.data_dir / "graph_coverage.json"
    if not path.exists():
        print("no graph yet — run `vinci graph-coverage` first")
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


def _cmd_themes(args: argparse.Namespace) -> int:
    """Component A: residual co-movement theme detection on the broad universe (assembles, never
    concludes).

    PROPOSES candidate clusters + their candidate shared-linkage + §7.1 strength signals for the
    analyst to judge (criterion 1). It does NOT name a driver, rank themes, confirm, or select.
    """
    from vinci.themes import FactorBasis, detect_themes, render_result

    cfg = get_config()
    cfg.ensure_dirs()
    ref = date.fromisoformat(args.ref) if args.ref else None
    basis = FactorBasis.MARKET_SECTOR if args.basis == "r1" else FactorBasis.FULL
    result = detect_themes(
        cfg, reference_date=ref, window_days=args.window_days, basis=basis,
        min_breadth=args.min_breadth, max_names=args.max_names, progress=stderr_reporter,
    )
    print(render_result(result, top=args.top))
    if not args.no_write:
        out = cfg.snapshots_dir / "candidate_themes.jsonl"
        with out.open("w") as f:
            for t in result.candidate_themes:
                f.write(t.model_dump_json() + "\n")
        print(f"\nwrote {out} ({len(result.candidate_themes)} admissible candidate themes)")
    return 0


def _cmd_themes_stage2(args: argparse.Namespace) -> int:
    """Components B+C: theme-type signals + megacap confirmation over A's candidate themes.

    ASSEMBLES and PRESENTS: the candidate >$10B leaders (analyst ratifies), the theme-type signals
    (price-pattern / vol-strip-survival / historical-analog / defer), and the confirmation grid
    (Part-7 thresholds × Finding-2 dual benchmark). It renders no type verdict and fires nothing.
    """
    from vinci.themes.render import render_stage2
    from vinci.themes.stage2 import analyze_stage2

    cfg = get_config()
    cfg.ensure_dirs()
    ref = date.fromisoformat(args.ref) if args.ref else None
    llm = None
    if not args.no_llm:
        from vinci.graph.llm import AnthropicLlmClient

        try:
            llm = AnthropicLlmClient.from_config(cfg)
        except Exception as exc:  # noqa: BLE001 — degrade to no-analog, never crash the CLI
            print(f"LLM unavailable ({exc}) — historical analog skipped")
    results = analyze_stage2(
        cfg, reference_date=ref, window_days=args.window_days, max_names=args.max_names,
        llm=llm, progress=stderr_reporter,
    )
    print(f"=== Theme Stage 2 (B+C) · {len(results)} themes (A untouched; leaders read-only) ===\n")
    shown = results if args.top is None else results[: args.top]
    for s2 in shown:
        print(render_stage2(s2))
        print()
    return 0


def _cmd_themes_exposure(args: argparse.Namespace) -> int:
    """Stage-3 build-2: scan the sub-$10B universe for DISCLOSED exposure to ONE driver — the AI-
    datacenter VALUE CHAIN (chips→HBM→packaging→thermal→power→optical→cloud) — reading each name's
    recent filing stream through the fenced, precision-fixed classifier. WIDE funnel: surfaces every
    name with ANY chain-attributable signal, with legible provenance (grade / driver-tie / layer
    / verbatim fact + source_ref). Never concludes/ranks/selects — NO machine confidence score; the
    human triages. The VOLUME (by type + chain layer) is the first-class output."""
    import json
    from collections import Counter
    from datetime import timedelta
    from pathlib import Path

    from vinci.edgar import EdgarClient
    from vinci.graph.llm import AnthropicLlmClient
    from vinci.sec import build_efts_http, build_sec_http
    from vinci.themes import detection as det
    from vinci.themes.drivers import AI_DATACENTER
    from vinci.themes.exposure import (
        grade_driving_fact,
        is_real_exposure,
        provenance_tag_of,
        scan_driver_exposure,
    )
    from vinci.themes.schemas import ExposureBasis

    _layers = AI_DATACENTER.provenance_tags  # theme's by-tag provenance map (chain layers here)

    def _tag(fact_text: str) -> str:
        return provenance_tag_of(fact_text, _layers)

    cfg = get_config()
    cfg.ensure_dirs()
    universe, snap = det.load_detection_universe(cfg)
    if args.max_names:
        universe = universe[: args.max_names]
    names = [(n.ticker, str(n.cik).zfill(10)) for n in universe if n.cik]
    ref = date.fromisoformat(args.ref) if args.ref else snap
    startdt = (ref - timedelta(days=args.window_days)).isoformat()
    matched, results = scan_driver_exposure(
        AI_DATACENTER, names,
        edgar=EdgarClient.from_config(cfg), sec_http=build_sec_http(cfg),
        efts_http=build_efts_http(cfg), llm=AnthropicLlmClient.from_config(cfg),
        startdt=startdt, enddt=ref.isoformat(), max_workers=args.workers, progress=stderr_reporter,
    )
    dumped = [a.model_dump(mode="json") for a in results]  # ONE dump — --out + history share bytes
    if args.out:  # audit-grade persistence — the full model_dump (facts + source_refs), no re-run
        Path(args.out).write_text("\n".join(json.dumps(r) for r in dumped))
        print(f"wrote {len(results)} full assessments (audit-grade) → {args.out}")
    if not args.no_scan_history:  # ALWAYS-ON history (independent of --out) — a re-scan must never
        # clobber the prior scan; the monitor/delta-scan diffs against these snapshots.
        import subprocess

        from vinci.themes.scan_history import record_snapshot

        try:  # sha is metadata for the manifest — unavailable is a logged None, not a failure
            git_sha: str | None = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, check=True, timeout=5,
            ).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            git_sha = None
        history_root = args.scan_history_dir or Path("data/scan_history")
        # "ai-datacenter" literal mirrors the existing AI_DATACENTER hardcoding above — both get
        # replaced together when themes-exposure grows a --driver param (scanner fork, not here).
        snap_path = record_snapshot(
            dumped, driver_slug="ai-datacenter", driver_desc=AI_DATACENTER.description,
            history_root=history_root, now=datetime.now(UTC), git_sha=git_sha,
            n_scanned=len(names))
        print(f"scan-history snapshot → {snap_path}")
        print(f"manifest + {(history_root / 'manifest.jsonl').read_text().splitlines()[-1]}")

    # THE VOLUME — the first-class deliverable (input to the DOWNSTREAM calibration decision, NOT
    # decided here). WIDE funnel: every name with ANY chain-attributable signal (basis != none) is
    # surfaced; the human triages by reading the legible provenance — NO machine confidence/rank.
    tiers = [ExposureBasis.BINDING_CONTRACTS, ExposureBasis.QUANTIFIED_REVENUE,
             ExposureBasis.COMMITTED_CAPACITY, ExposureBasis.ASPIRATIONAL]
    dist = Counter(a.exposure_basis for a in results)
    surfaced = [a for a in results if a.exposure_basis is not ExposureBasis.NONE_DISCLOSED]
    layers = Counter(_tag(f.fact) for a in surfaced if (f := grade_driving_fact(a)))
    errs = [a for a in results if any("error:" in fl.lower() for fl in a.flags)]
    print("\n=== Stage-3 build-2 · AI-datacenter VALUE-CHAIN universe scan ===")
    print(f"universe {len(names)} · {len(matched)} mention-candidates · {len(results)} assessed "
          f"· {len(errs)} scan-errors (recall gap, logged)")
    print(f"\nVOLUME by exposure-type — the wide funnel, {len(surfaced)} surfaced:")
    for b in tiers:
        print(f"  {b.value:32} {dist.get(b, 0)}")
    print(f"  {'(no chain exposure disclosed)':32} {dist.get(ExposureBasis.NONE_DISCLOSED, 0)}")
    print(f"\nVOLUME by chain layer — of the {len(surfaced)} surfaced:")
    for layer, n in layers.most_common():
        print(f"  {layer:22} {n}")
    real = [a for a in surfaced if is_real_exposure(a)]
    committed = [a for a in surfaced if a.exposure_basis is ExposureBasis.COMMITTED_CAPACITY]
    print(f"\nREAL — binding/quantified ({len(real)}); contract-type flags are the NOISY tier "
          "(weight for review), revenue-type verified more cleanly:")
    for a in sorted(real, key=lambda x: x.exposure_basis.value):
        f = grade_driving_fact(a)
        if f:
            print(f"  {a.ticker:6} [{a.exposure_basis.value}] <{_tag(f.fact)}> "
                  f"{f.driver_tie.value}: {f.fact[:120]}")
            print(f"         source: {f.source_ref}")
    print(f"\nCOMMITTED-capacity — borderline, capex/MW toward the driver ({len(committed)}):")
    for a in sorted(committed, key=lambda x: x.ticker):
        f = grade_driving_fact(a)
        if f:
            print(f"  {a.ticker:6} <{_tag(f.fact)}> {f.driver_tie.value}: {f.fact[:105]}")
    print(f"\n(+ {dist.get(ExposureBasis.ASPIRATIONAL, 0)} at the INTENT tier — surfaced, soft on "
          "their face; full provenance in --out. Volume decides the downstream calibration need.)")
    return 0


def _cmd_themes_forward(args: argparse.Namespace) -> int:
    """Stage-4 forward-validation harness: load the analyst's dispositioned committed-tier worksheet
    into the append-only ratification ledger, report disposition status, and — once EVERY name is
    RATIFIED/PASSED — freeze the baskets and (with --measure) measure the two co-primary spreads
    forward, layer-aware + power-labelled. It LOGS + MEASURES human decisions; it never
    selects/ranks/promotes a grade to a hold (§6 dead-signal firewall). Awaits real dispositions."""
    import csv
    import json
    from collections import Counter
    from datetime import date
    from pathlib import Path

    from vinci.themes import forward as fwd

    def _csv_list(s: str | None) -> list[str]:
        return [t.strip() for t in (s or "").split(",") if t.strip()]

    driver = args.driver
    ws, ledger = Path(args.worksheet), Path(args.ledger)
    with open(ws) as fh:
        rows = list(csv.DictReader(fh))
    all_committed = [r["ticker"] for r in rows]
    # schema-flexible: the AI-datacenter worksheet has a 'chain_layer' column; a demand-shaped one
    # (e.g. defense) has 'category' — either populates the neutral substructure tag
    layer_of = {r["ticker"]: (r.get("chain_layer") or r.get("category", "")) for r in rows}
    ratify_date = date.fromisoformat(args.ratify_date) if args.ratify_date else date.today()
    records, pending = fwd.records_from_worksheet(ws, driver=driver, ratification_date=ratify_date)
    for rec in records:  # append-only: log each dispositioned row (a correction is a new row)
        fwd.append_record(ledger, rec)
    counts = Counter(r.disposition.value for r in records)
    print(f"\n=== Stage-4 forward-validation harness · {driver} ===")
    print(f"worksheet {ws}\nledger {ledger} (append-only)")
    print(f"committed {len(all_committed)} · dispositioned {len(records)} {dict(counts)} · "
          f"PENDING {pending}")
    dig = [r.ticker for r in records if r.disposition is fwd.Disposition.DIG_DEEPER]
    if pending or dig:
        print(f"\nNOT READY — {pending} pending + {len(dig)} DIG-DEEPER; every name must be "
              "RATIFIED/PASSED before freezing. Real logging + measurement await triage.")
        return 0
    freeze_ts = date.today().isoformat() + "T00:00:00"
    # cohorts (a SECOND driver now freezes in one command, no bespoke script): --watchlist is the
    # genuine-exposure re-underwrite cohort (falls back to --exposure-names); it also serves as the
    # exposure-carry (diagnostic-2) cohort. --avoid-controls / --real-tier / --watchlist-triggers
    # (a JSON {ticker: trigger}) are optional.
    watchlist = _csv_list(args.watchlist) or _csv_list(args.exposure_names)
    avoid_controls = _csv_list(args.avoid_controls)
    real_tier = _csv_list(args.real_tier)
    triggers = json.loads(Path(args.watchlist_triggers).read_text()) if args.watchlist_triggers \
        else None
    baskets = fwd.freeze_baskets(
        records, all_committed, driver=driver, freeze_timestamp=freeze_ts, layer_of=layer_of,
        watchlist=watchlist or None, watchlist_triggers=triggers,
        avoid_controls=avoid_controls or None, real_tier=real_tier or None)
    if args.baskets_out:
        Path(args.baskets_out).write_text(baskets.model_dump_json(indent=1))
    print(f"\nFROZEN: {len(baskets.ratified)} RATIFIED (BUY) · {len(baskets.passed)} PASSED "
          f"(AVOID) · {len(baskets.all_committed)} equal-weight naive baseline (§3b-i)")
    if baskets.watchlist:
        print(f"WATCHLIST (re-underwrite cohort): {list(baskets.watchlist)}")
    if baskets.avoid_controls:
        print(f"AVOID-CONTROLS (near-miss control, within PASSED): {list(baskets.avoid_controls)}")
    if baskets.real_tier:
        print(f"REAL-tier secondary: {list(baskets.real_tier)}")
    print(f"deferred control: {baskets.deferred_controls[0]}")
    if not args.measure:
        return 0
    from vinci.eod.client import PolygonEodClient
    price_fn = fwd.eod_close_fn(PolygonEodClient.from_config(get_config()))
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    horizons = [int(h) for h in args.horizons.split(",")]
    if not baskets.ratified:  # EMPTY BUY (zero RATIFIED) — hold-none path, NEVER RATIFIED-dependent
        print("\n" + fwd.HOLD_NONE_HONESTY)
        for h in horizons:
            hn = fwd.measure_hold_none(baskets, exposure_names=watchlist, price_fn=price_fn,
                                       horizon_days=h, as_of=as_of)
            print(f"\n--- @ {hn.horizon_days}d (as_of {hn.as_of}) ---")
            print(f"  UNDEFINED (zero RATIFIED, not computed): "
                  f"{[m for m, _ in hn.undefined_measures]}")
            print(f"  DIAGNOSTIC-1 avoid-discipline: {hn.avoid_discipline.detail}")
            print(f"  DIAGNOSTIC-2 exposure-carry (primary): {hn.exposure_carry.detail}")
            print("  CATEGORY-AWARE naive_by_layer (driver-agnostic):")
            for lr in hn.naive_by_layer:
                val = "pending" if lr.mean_return is None else f"{lr.mean_return:+.1%}"
                print(f"    {lr.layer:20} {val:>8} (n={lr.n})")
        return 0
    for rep in fwd.measure(baskets, price_fn=price_fn, horizons_days=horizons, as_of=as_of):
        print(f"\n--- @ {rep.horizon_days}d (as_of {rep.as_of}) · POWER [{rep.power.label}] "
              f"{rep.power.note} ---")
        for ls in (rep.pooled, *rep.by_layer):
            rmp = "n/a" if ls.ratified_minus_passed is None else f"{ls.ratified_minus_passed:+.1%}"
            rmn = "n/a" if ls.ratified_minus_naive is None else f"{ls.ratified_minus_naive:+.1%}"
            print(f"  {ls.scope:20} RAT-PASSED={rmp:>7} RAT-NAIVE={rmn:>7} [{ls.state}] "
                  f"(n_rat={ls.n_ratified} n_pass={ls.n_passed})")
        print(f"  partial-kill (§3c): {rep.partial_kill_scopes or '() none'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vinci", description=__doc__)
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

    p_rank = sub.add_parser("rank", help="order screen candidates into a priority queue (profiles)")
    p_rank.add_argument("--top", type=int, default=15, help="profiles to print (default: 15)")
    p_rank.add_argument(
        "--md-top", type=int, default=50, dest="md_top",
        help="rows in the committed ranked_queue.md table (default: 50)",
    )
    p_rank.add_argument(
        "--deep-work-adv-floor", type=float, default=3_000_000.0, dest="deep_work_adv_floor",
        help="ADV($) below which a name is tradeability-gated (default: 3e6 = universe floor, a "
        "no-op re-check; raise to push thin names down)",
    )
    p_rank.add_argument(
        "--cause-file", dest="cause_file",
        help="optional JSON {ticker_or_id: mean_revert|structural_break} Tier-3 LLM annotations",
    )
    p_rank.add_argument(
        "--structural", action="store_true",
        help="Tier-3 deterministic structural-disqualifier scan (network: free EDGAR 8-K text + "
        "shares series). DEMOTE-ONLY — a fired going-concern/4.02/4.01/3.01/dilution signal sinks "
        "the name, source-bound to its 8-K; never raises rank. Off by default (no network).",
    )
    p_rank.add_argument(
        "--no-write", action="store_true", dest="no_write",
        help="print only; do not write ranked_queue.jsonl / .md snapshots",
    )
    p_rank.set_defaults(func=_cmd_rank)

    p_dossier = sub.add_parser("dossier", help="assemble per-finalist dossiers (never concludes)")
    p_dossier.add_argument(
        "mode", nargs="?", default="assemble", choices=("assemble", "requirements"),
        help="'assemble' (default) builds dossiers; 'requirements' prints the canonical manual-CIQ "
        "manifest (export checklist; the MISSING-manifest path reads the same definition)",
    )
    p_dossier.add_argument("--top", type=int, default=10, help="top N of the queue (default: 10)")
    p_dossier.add_argument(
        "--ticker", help="assemble (or, with 'requirements', render the checklist for) one name"
    )
    p_dossier.add_argument(
        "--no-llm", action="store_true", dest="no_llm", help="mechanical layer only; skip synthesis"
    )
    p_dossier.add_argument(
        "--json", action="store_true", dest="json",
        help="with 'requirements': emit the manifest as JSON (machine-readable, for the upload UI)",
    )
    p_dossier.set_defaults(func=_cmd_dossier)

    p_log = sub.add_parser("log-verdict", help="record a manual BUY/AVOID verdict for a candidate")
    p_log.add_argument("candidate_id", help="candidate id from `vinci screen`")
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

    p_themes = sub.add_parser(
        "themes",
        help="Component A: residual co-movement theme detection (proposes; never concludes)",
    )
    p_themes.add_argument(
        "--ref", help="reference date YYYY-MM-DD (default: universe snapshot as_of)"
    )
    p_themes.add_argument(
        "--window-days", type=int, default=365, dest="window_days",
        help="trailing detection window in calendar days (default: 365 ≈ 12mo)",
    )
    p_themes.add_argument(
        "--basis", choices=("r1", "r2"), default="r2",
        help=(
            "residualization basis: r1=market+sector, r2=+size+vol "
            "(default; the vol-strip is the lever)"
        ),
    )
    p_themes.add_argument(
        "--min-breadth", type=int, default=3, dest="min_breadth",
        help="cluster-size floor — a basket, not a pair (default: 3, face-validity)",
    )
    p_themes.add_argument(
        "--max-names", type=int, dest="max_names", help="cap the universe (quick dev sample)"
    )
    p_themes.add_argument("--top", type=int, help="limit admissible themes printed (default: all)")
    p_themes.add_argument(
        "--no-write", action="store_true", dest="no_write",
        help="print only; do not write candidate_themes.jsonl",
    )
    p_themes.set_defaults(func=_cmd_themes)

    p_s2 = sub.add_parser(
        "themes-stage2",
        help="Components B+C: theme-type signals + megacap confirmation (proposes; never decides)",
    )
    p_s2.add_argument("--ref", help="reference date YYYY-MM-DD (default: universe snapshot as_of)")
    p_s2.add_argument(
        "--window-days", type=int, default=365, dest="window_days",
        help="trailing window in calendar days (default: 365 ≈ 12mo)",
    )
    p_s2.add_argument("--max-names", type=int, dest="max_names", help="cap the universe (dev)")
    p_s2.add_argument("--top", type=int, help="limit themes printed (default: all)")
    p_s2.add_argument(
        "--no-llm", action="store_true", dest="no_llm",
        help="skip the LLM historical-analog (B); compute everything else",
    )
    p_s2.set_defaults(func=_cmd_themes_stage2)

    p_exp = sub.add_parser(
        "themes-exposure",
        help="Stage-3 build-1: semantic-primary exposure scan for the AI-datacenter driver "
        "(assesses disclosed exposure from filings; never concludes)",
    )
    p_exp.add_argument("--ref", help="reference date YYYY-MM-DD (default: snapshot as_of)")
    p_exp.add_argument(
        "--window-days", type=int, default=290, dest="window_days",
        help="recent disclosure window in days (default: 290 ≈ 9.5mo)",
    )
    p_exp.add_argument("--max-names", type=int, dest="max_names", help="cap the universe (dev)")
    p_exp.add_argument("--workers", type=int, default=6, help="concurrent LLM workers (default: 6)")
    p_exp.add_argument("--out", help="write full model_dump JSONL (audit-grade persistence)")
    p_exp.add_argument(
        "--scan-history-dir", type=Path, dest="scan_history_dir",
        help="scan-history archive root (default: data/scan_history; git-ignored)",
    )
    p_exp.add_argument(
        "--no-scan-history", action="store_true", dest="no_scan_history",
        help="skip the always-on timestamped history snapshot",
    )
    p_exp.set_defaults(func=_cmd_themes_exposure)

    p_fwd = sub.add_parser(
        "themes-forward",
        help="Stage-4 forward-validation: log dispositions, freeze baskets, measure spreads",
    )
    p_fwd.add_argument("--worksheet", required=True,
                       help="committed_review_worksheet.csv (with the analyst's dispositions)")
    p_fwd.add_argument("--ledger", required=True, help="append-only ratification ledger JSONL path")
    p_fwd.add_argument("--ratify-date", dest="ratify_date",
                       help="ratification date YYYY-MM-DD (default: today)")
    p_fwd.add_argument("--baskets-out", dest="baskets_out", help="write frozen baskets JSON")
    p_fwd.add_argument("--measure", action="store_true",
                       help="after freeze, measure the spreads forward (Polygon EOD, read-only)")
    p_fwd.add_argument("--as-of", dest="as_of", help="measurement as-of YYYY-MM-DD (default today)")
    p_fwd.add_argument("--horizons", default="30,90,180,365",
                       help="comma-separated forward horizons in days (default: 30,90,180,365)")
    p_fwd.add_argument("--exposure-names", dest="exposure_names",
                       help="comma tickers: the genuine-exposure watchlist / exposure-carry cohort "
                            "(empty-BUY diagnostic 2). Back-compat alias for --watchlist.")
    p_fwd.add_argument("--driver", default="AI-datacenter value chain",
                       help="driver label to freeze under (default: 'AI-datacenter value chain'; "
                            "e.g. 'defense-demand-shift' for theme #2)")
    p_fwd.add_argument("--watchlist",
                       help="comma tickers: genuine-exposure re-underwrite cohort (also the "
                            "exposure-carry cohort); must be ⊆ the committed tier")
    p_fwd.add_argument("--watchlist-triggers", dest="watchlist_triggers",
                       help="path to a JSON object {ticker: verbatim trigger} for the watchlist")
    p_fwd.add_argument("--avoid-controls", dest="avoid_controls",
                       help="comma tickers: near-miss control cohort; must be ⊆ the PASSED leg")
    p_fwd.add_argument("--real-tier", dest="real_tier",
                       help="comma tickers: looser REAL-tier secondary cohort (clearly labeled)")
    p_fwd.set_defaults(func=_cmd_themes_forward)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_local_env()  # local: read repo-root .env; CI: no-op (injected secrets win)
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
