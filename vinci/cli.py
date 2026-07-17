"""``vinci`` command-line entrypoint.

Grown one subcommand per build step. Today: ``resolve`` (step 1). Later: ``refresh`` (steps 3–4),
``screen`` (step 5), ``log-verdict`` (step 6), ``score`` (step 7).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.config import Config, get_config, load_local_env
from vinci.dossier.verdict import derive_proposal
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
from vinci.themes.assay import PriceCloseFn
from vinci.themes.assay_candidates import CANDIDATE_SPECS, PLACEBO_KEY
from vinci.themes.assay_schemas import AssayCard, CandidateSpec
from vinci.themes.drivers import DRIVER_SPECS
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
    # Attach a DERIVED SECTOR + finer sub-INDUSTRY per name (SIC → sectors.*) HERE in the writer,
    # never in the scorer — vinci.rank / vinci.screens stay pure (an AST fence test asserts it).
    # Assemble/inform ONLY: they feed the human cluster roll-up; never a gate/weight/sort.
    from vinci.sectors import industry_for_sic, sector_for_sic

    sic_by_id = {c.candidate_id: c.data_record.identity.sic for c in cands}
    ranked = [
        r.model_copy(update={
            "sector": sector_for_sic(sic_by_id.get(r.candidate_id)),
            "industry": industry_for_sic(sic_by_id.get(r.candidate_id)),
        })
        for r in ranked
    ]
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

    # --show-proposal: an explicit PEEK at the sealed machine proposal for --ticker. The committed
    # brief HIDES it (anti-anchoring); this re-renders the COMMITTED artifact to stdout with the
    # proposal revealed, WITHOUT re-assembling or overwriting anything. If the operator peeks before
    # logging, self-report via `log-verdict --saw-proposal` (stamps revealed_pre_verdict).
    if getattr(args, "show_proposal", False):
        if not args.ticker:
            print("--show-proposal requires --ticker")
            return 1
        from vinci.dossier.render import render_markdown
        from vinci.dossier.schemas import Dossier

        path = get_config().data_dir / "dossiers" / args.ticker.upper() / "dossier.json"
        if not path.exists():
            print(f"no committed dossier for {args.ticker} — assemble it first")
            return 1
        print(render_markdown(Dossier.model_validate_json(path.read_text()), show_proposal=True))
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
    # (mid-cycle) single --ticker with --peers/--scenario → compute + attach the mid-cycle block
    if args.ticker and (getattr(args, "peers", None) or getattr(args, "scenario", None)):
        reasons = {n: getattr(args, f"reason_{n}") for n in ("bear", "base", "bull")
                   if getattr(args, f"reason_{n}", None)}
        peers = [p.strip().upper() for p in (args.peers or "").split(",") if p.strip()]
        rc = _attach_midcycle(cfg, args.ticker, peers=peers,
                              scenario_specs=args.scenario or [], reasons=reasons)
        if rc != 0:
            return rc
    return 0


def _parse_scenario(spec: str) -> tuple[str, dict[str, float]]:
    """'bear:rev=3000,margin=0.03,multiple=5' → ('bear', {'rev':…, 'margin':…, 'multiple':…})."""
    name, _, rest = spec.partition(":")
    kv: dict[str, float] = {}
    for part in rest.split(","):
        if part.strip():
            k, _, v = part.partition("=")
            kv[k.strip()] = float(v)
    return name.strip().lower(), kv


def _attach_midcycle(cfg: Config, ticker: str, *, peers: list[str],
                     scenario_specs: list[str], reasons: dict[str, str]) -> int:
    """Compute the mid-cycle block for one --ticker and persist it into the committed dossier
    .json/.md (re-render only — mechanical/synthesis layers untouched). Deterministic, no LLM."""
    from vinci.dossier import midcycle as mc
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver

    ddir = cfg.data_dir / "dossiers" / ticker.upper()
    path = ddir / "dossier.json"
    if not path.exists():
        print(f"  midcycle: no committed dossier for {ticker} — assemble it first")
        return 1
    d = Dossier.model_validate_json(path.read_text())
    resolver, edgar = EntityResolver.from_config(cfg), EdgarClient.from_config(cfg)

    def series(t: str) -> tuple[mc.AnnualSeries, mc.AnnualSeries]:
        f = edgar.companyfacts(resolver.resolve_ticker(t).cik)
        return mc.annual_series(f, "revenue"), mc.annual_series(f, "operating_income")

    rev, oi = series(ticker)
    facts = edgar.companyfacts(resolver.resolve_ticker(ticker).cik)
    margin = mc.margin_anchor(rev, oi)
    fuel = mc.fuel_split(facts, rev, oi)
    per: dict[str, mc.MarginAnchor] = {}
    for p in peers:
        try:
            pr, po = series(p)
            per[p] = mc.margin_anchor(pr, po)
        except Exception as exc:  # noqa: BLE001 — a peer that won't resolve is EXCLUDED, named
            per[p] = mc.MarginAnchor(by_year={}, revenue_tag=None, opinc_tag=None,
                                     note=f"fetch error: {type(exc).__name__}")
    peer_band = mc.peer_anchor(per)
    bundle = CiqBundle.from_files(ticker, LocalFolderStore.from_config(cfg).files(ticker))
    mult = mc.multiple_anchor(bundle)

    scenarios: list[mc.Scenario] = []
    try:
        for spec in scenario_specs:
            name, kv = _parse_scenario(spec)
            r_musd = kv.get("rev")
            multiple = kv.get("multiple", mult.median if mult.available else None)
            if r_musd is None or multiple is None:
                print(f"  scenario {name!r}: needs rev= and multiple= "
                      "(multiple may default to the D-anchor only when CIQ is present)")
                return 2
            scenarios.append(mc.build_scenario(
                name, revenue=r_musd, multiple=multiple, anchor_margin=margin.median,
                margin=kv.get("margin"), reason=reasons.get(name)))
    except mc.ScenarioError as exc:
        print(f"  REFUSED — {exc}")
        return 2

    si = d.mechanical.stock_info
    spot = si.price.value if si else None
    shares = si.shares_out.value if si else None
    # Net debt ($M) from the CIQ TEV->equity bridge (the existing capital-structure block):
    # net debt = total debt - cash (net cash -> negative, a legitimate value, so guard on None).
    iv = d.mechanical.implied_valuation
    net_debt = (
        iv.bridge_debt - iv.bridge_cash
        if iv is not None and iv.bridge_debt is not None and iv.bridge_cash is not None
        else None
    )
    # A scenario grid needs spot + positive shares + net debt. Supplied-but-unpriceable is said
    # LOUDLY and renders anchors only — the analyst's scenarios are never silently dropped.
    priced = (bool(scenarios) and spot is not None and shares is not None
              and shares > 0 and net_debt is not None)
    if scenarios and not priced:
        missing = ", ".join(
            n for n, ok in (("spot", spot is not None),
                            ("shares>0", shares is not None and shares > 0),
                            ("net-debt (CIQ TEV→equity bridge)", net_debt is not None)) if not ok)
        print(f"  scenarios supplied but NOT priced — missing/invalid: {missing}; anchors only")
    block = mc.assemble_midcycle(margin=margin, fuel=fuel, peers=peer_band, mult=mult,
                                 scenarios=scenarios or None, spot=spot, net_debt_musd=net_debt,
                                 shares=shares)
    d2 = d.model_copy(update={"midcycle": block})
    path.write_text(d2.model_dump_json(indent=2))
    (ddir / "dossier.md").write_text(render_markdown(d2))
    print(f"  midcycle attached → {ddir} (anchors"
          f"{' + scenario grid + ratio' if priced else ' only'})")
    return 0


def _sealed_proposal(
    cfg: Config, ticker: str
) -> tuple[Verdict | None, str | None, datetime | None]:
    """The machine proposal for ``ticker``, SEALED from the COMMITTED dossier artifact at log time
    (the 2026-07-13 pivot) — never recomputed from live data (as-of discipline). A missing artifact
    logs with no proposal (fail-honest — pre-Brief names decide cold); a PRESENT but unreadable one
    fails LOUD, never silently logging no-proposal when a proposal may exist."""
    path = cfg.data_dir / "dossiers" / ticker / "dossier.json"
    if not path.exists():
        print(f"no committed dossier for {ticker} — logging with no machine proposal")
        return None, None, None
    try:
        doc = json.loads(path.read_text())
        synth = doc.get("synthesis") or {}
        prop = derive_proposal(synth.get("evidence_balance"))
        stamp = doc.get("assembled_at")
        assembled = datetime.fromisoformat(stamp) if stamp else None
    except (ValueError, OSError) as exc:  # corrupt/unreadable artifact → loud, actionable
        raise LedgerError(f"committed dossier for {ticker} is unreadable: {exc}") from exc
    if prop.action is None:
        print(f"machine proposal for {ticker}: none — {prop.note}")
    return prop.action, prop.lean, assembled


def _cmd_log_verdict(args: argparse.Namespace) -> int:
    """Record a manual BUY/AVOID-terminal verdict for a candidate, freezing the entry price and
    sealing the machine's proposal (from the committed dossier) + the confirm/override disposition
    beside it — the human's verdict is the verdict of record."""
    cfg = get_config()
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    resolver = EntityResolver.from_config(cfg)  # sources the name's EDGAR SIC → sector at log time
    with Store(cfg.db_path) as store:
        try:
            cand = store.get_candidate(args.candidate_id)
            if cand is None:
                raise LedgerError(
                    f"no candidate {args.candidate_id!r} in the store (run the screen first)"
                )
            mp, ml, stamp = _sealed_proposal(cfg, cand.data_record.identity.ticker)
            entry = log_verdict(
                store, resolver=resolver, candidate_id=args.candidate_id,
                verdict=Verdict(args.verdict),
                twin_call=args.twin, thesis=args.thesis, kill_criteria=args.kill,
                horizon_days=args.horizon_days, confidence=Confidence(args.confidence),
                decided_at=datetime.now(), reference_date=ref,
                staleness_days=cfg.price_staleness_days, benchmark=args.benchmark,
                machine_proposal=mp, machine_lean=ml, proposal_assembled_at=stamp,
                revealed_pre_verdict=getattr(args, "saw_proposal", False),
            )
        except LedgerError as exc:
            print(f"could not log verdict: {exc}")
            return 1
        except sqlite3.IntegrityError:
            print(f"a verdict is already logged for {args.candidate_id} (ledger is append-only)")
            return 1
    prop_note = (
        f"machine proposed {entry.machine_proposal.value}" if entry.machine_proposal is not None
        else "no machine proposal"
    )
    disp = entry.disposition.value if entry.disposition is not None else "n/a"
    print(
        f"logged {entry.verdict.value} for {entry.ticker} [sector: {entry.sector}]: frozen entry "
        f"{entry.entry_price:.2f} as_of {entry.entry_price_as_of}, horizon {entry.horizon_days}d "
        f"· {prop_note} → disposition {disp}"
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
    dumped = [t.model_dump(mode="json") for t in result.candidate_themes]  # ONE dump — the "latest"
    # pointer and the scan-history snapshot share these bytes (mirrors exposure's --out ≡ snapshot).
    if not args.no_write:
        out = cfg.snapshots_dir / "candidate_themes.jsonl"  # "latest" pointer (same bytes)
        out.write_text("\n".join(json.dumps(r) for r in dumped))
        print(f"\nwrote {out} ({len(dumped)} admissible candidate themes)")
    if not args.no_scan_history:  # ALWAYS-ON timestamped archive — a monthly sweep must never
        # clobber the prior harvest; the delta/monitor diffs against these immutable snapshots.
        import subprocess

        from vinci.themes.scan_history import record_snapshot

        try:  # sha is manifest metadata — unavailable is a logged None, not a failure
            git_sha: str | None = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, check=True, timeout=5,
            ).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            git_sha = None
        history_root = args.scan_history_dir or Path("data/scan_history")
        desc = (f"Component A co-movement; basis={args.basis}, window={args.window_days}d, "
                f"ref={args.ref or 'snapshot as_of'}, min_breadth={args.min_breadth}")
        snap_path = record_snapshot(
            dumped, driver_slug="component-a", driver_desc=desc, history_root=history_root,
            now=datetime.now(UTC), git_sha=git_sha, n_scanned=result.stats.names_with_coverage,
            tier_field=None)
        print(f"scan-history snapshot → {snap_path}")
        print(f"manifest + {(history_root / 'manifest.jsonl').read_text().splitlines()[-1]}")
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


def _resolve_only_tickers(args: argparse.Namespace) -> set[str] | None:
    """Parse ``--only-tickers`` / ``--only-file`` into an uppercased ticker set (None if neither is
    given). At most one source; fail loud if a source is supplied but yields no tickers. This is the
    monitor's delta-scan primitive — restrict a scan to a named subset with NO new code path."""
    only_tickers: str | None = args.only_tickers
    only_file: Path | None = args.only_file
    if only_tickers and only_file:
        raise SystemExit("error: pass at most one of --only-tickers / --only-file")
    raw = only_tickers if only_tickers else (only_file.read_text() if only_file else None)
    if raw is None:
        return None
    toks = {t.strip().upper() for t in raw.replace(",", "\n").split() if t.strip()}
    if not toks:
        raise SystemExit("error: --only-tickers/--only-file supplied but no tickers parsed from it")
    return toks


def _partition_only(requested: set[str], universe_tickers: set[str]) -> tuple[set[str], list[str]]:
    """Split ``requested`` (uppercased) against the universe: (kept, missing-sorted). Fail loud on
    an EMPTY intersection — a typo'd/stale delta-scan must ERROR, not silently scan nothing (which
    would read as 'no exposure')."""
    kept = requested & universe_tickers
    missing = sorted(requested - universe_tickers)
    if not kept:
        raise SystemExit(
            f"error: none of the {len(requested)} requested tickers are in the universe "
            f"(e.g. {', '.join(sorted(requested)[:8])}) — refusing to scan nothing")
    return kept, missing


def _cmd_themes_exposure(args: argparse.Namespace) -> int:
    """Stage-3: scan the sub-$10B universe for DISCLOSED exposure to ONE driver — selected by
    ``--driver`` from the DRIVER_SPECS registry — reading each name's recent filing stream through
    the fenced, precision-fixed classifier. WIDE funnel: surfaces every
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
    from vinci.themes.exposure import (
        ScanAbortedError,
        grade_driving_fact,
        is_real_exposure,
        provenance_tag_of,
        scan_driver_exposure,
    )
    from vinci.themes.schemas import ExposureBasis

    spec = DRIVER_SPECS[args.driver]  # --driver is REQUIRED + choices-gated; fail-loud, no default
    print(f"driver={spec.key}")
    _layers = spec.provenance_tags  # theme's by-tag provenance map (chain layers here)

    def _tag(fact_text: str) -> str:
        return provenance_tag_of(fact_text, _layers)

    cfg = get_config()
    cfg.ensure_dirs()
    universe, snap = det.load_detection_universe(cfg)
    only = _resolve_only_tickers(args)
    if only is not None:  # delta-scan primitive: restrict to the intersection with the universe
        kept, missing = _partition_only(only, {n.ticker.upper() for n in universe})
        if missing:  # fail loud on names not in the universe — print, then proceed with the rest
            print(f"!! {len(missing)} requested ticker(s) NOT in universe (skipped): "
                  f"{', '.join(missing)}")
        universe = [n for n in universe if n.ticker.upper() in kept]
        print(f"--only-tickers: scanning {len(universe)} of {len(only)} requested "
              "(intersection with the committed universe)")
    if args.max_names:
        universe = universe[: args.max_names]
    names = [(n.ticker, str(n.cik).zfill(10)) for n in universe if n.cik]
    ref = date.fromisoformat(args.ref) if args.ref else snap
    startdt = (ref - timedelta(days=args.window_days)).isoformat()
    try:
        matched, results = scan_driver_exposure(
            spec, names,
            edgar=EdgarClient.from_config(cfg), sec_http=build_sec_http(cfg),
            efts_http=build_efts_http(cfg), llm=AnthropicLlmClient.from_config(cfg),
            startdt=startdt, enddt=ref.isoformat(), max_workers=args.workers,
            progress=stderr_reporter,
        )
    except ScanAbortedError as abort:  # 3 consecutive 4xx → stop, don't persist a poisoned queue
        print(f"\n!! {abort}")
        shown = ", ".join(abort.remaining[:40]) + (" …" if len(abort.remaining) > 40 else "")
        print(f"   {len(abort.assessed)} assessed before abort; "
              f"un-scanned ({len(abort.remaining)}): {shown}")
        print("   NOT writing --out or scan-history — a poisoned queue is worse than none.")
        return 2
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
        snap_path = record_snapshot(
            dumped, driver_slug=spec.key, driver_desc=spec.description,
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
    _not_surfaced = (ExposureBasis.NONE_DISCLOSED, ExposureBasis.UNASSESSED_ERROR)
    surfaced = [a for a in results if a.exposure_basis not in _not_surfaced]
    layers = Counter(_tag(f.fact) for a in surfaced if (f := grade_driving_fact(a)))
    errs = [a for a in results if any("error:" in fl.lower() for fl in a.flags)]
    print(f"\n=== Stage-3 · {spec.key} exposure scan ===")
    print(f"universe {len(names)} · {len(matched)} mention-candidates · {len(results)} assessed "
          f"· {len(errs)} scan-errors (recall gap, logged)")
    print(f"\nVOLUME by exposure-type — the wide funnel, {len(surfaced)} surfaced:")
    for b in tiers:
        print(f"  {b.value:32} {dist.get(b, 0)}")
    print(f"  {'(no chain exposure disclosed)':32} {dist.get(ExposureBasis.NONE_DISCLOSED, 0)}")
    print(f"  {'(UNASSESSED — scan error, NOT none)':32} "
          f"{dist.get(ExposureBasis.UNASSESSED_ERROR, 0)}")
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


def _load_latest_component_a() -> tuple[Path | None, list[dict[str, Any]], str]:
    """Newest component-a snapshot: (path, clusters, scan-date from the YYYYMMDD filename)."""
    import re

    root = Path("data/scan_history/component-a")
    snaps = sorted(root.glob("*.jsonl")) if root.exists() else []
    if not snaps:
        return None, [], ""
    p = snaps[-1]
    clusters = [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]
    m = re.match(r"(\d{4})(\d{2})(\d{2})", p.name)
    return p, clusters, ("-".join(m.groups()) if m else "")


def _cmd_themes_draft(args: argparse.Namespace) -> int:
    """Draft a name + hypothesis + advisory triage disposition for each UNREVIEWED cluster — ONE LLM
    call each, keyed <scan_date>:<cluster_id>, primed with self-excluded few-shot precedent from
    reviews.json. The machine DRAFTS; the human OWNS (themes-review). Idempotent: reuses drafts
    current for this snapshot AND prompt version (no duplicate spend). --include-reviewed re-drafts
    the clusters reviewed FOR THIS scan (a one-shot face-validity re-check vs the human's own calls;
    prints draft-vs-decision agreement). Any call error → an unassessed-error record (never a
    fabricated draft); 3 consecutive same-4xx aborts early."""
    import subprocess
    from datetime import UTC, datetime

    from vinci.graph.llm import AnthropicLlmClient
    from vinci.themes.drafts import (
        PROMPT_VERSION,
        DraftAbortedError,
        _drafts_current,
        draft_targets,
        draft_unreviewed,
    )
    from vinci.themes.scan_history import record_snapshot

    cfg = get_config()
    cfg.ensure_dirs()
    snap_path, clusters, scan_date = _load_latest_component_a()
    if snap_path is None:
        print("!! no component-a snapshot under data/scan_history/component-a — run `themes` first")
        return 2
    reviews = json.loads(Path("frontend/radar/reviews.json").read_text())["reviews"]
    drafts_out = Path("frontend/radar/drafts.json")
    include_reviewed = getattr(args, "include_reviewed", False)

    # IDEMPOTENT (normal path only) — reuse iff same snapshot AND same prompt version; a version
    # bump or a legacy pointer regenerates. --include-reviewed always runs (it is a re-check).
    if drafts_out.exists() and not args.force and not include_reviewed:
        prev = json.loads(drafts_out.read_text())
        if _drafts_current(prev, snap_path.name, PROMPT_VERSION):
            n_prev = len(prev.get("drafts", []))
            print(f"drafts already current for {snap_path.name} @ v{PROMPT_VERSION} "
                  f"({n_prev} drafts) — reusing, no LLM spend (--force to redraft)")
            return 0

    todo = draft_targets(clusters, reviews, scan_date, include_reviewed=include_reviewed)
    if not todo:
        # --include-reviewed MUST run: an empty target means the check silently didn't happen →
        # FAIL LOUD (rc 2). The normal path with no unreviewed clusters is BENIGN — the inbox is
        # fully triaged; that is a success state, not an error (rc 0, leave the pointer untouched).
        if include_reviewed:
            print(f"!! --include-reviewed: no clusters reviewed for {scan_date} in "
                  f"{snap_path.name} — nothing to re-check")
            return 2
        print(f"no unreviewed clusters in {snap_path.name} — inbox is empty, nothing to draft")
        return 0

    llm = AnthropicLlmClient.from_config(cfg)
    try:
        drafts = draft_unreviewed(clusters, reviews, scan_date, llm, progress=stderr_reporter,
                                  include_reviewed=include_reviewed)
    except DraftAbortedError as abort:
        print(f"\n!! {abort} — NOT writing drafts (a poisoned run is worse than none)")
        return 2

    kind = "face-validity recheck (include-reviewed)" if include_reviewed else "inbox drafts"
    history_root = args.scan_history_dir or Path("data/scan_history")
    try:  # sha is manifest metadata — unavailable is a logged None, not a failure
        git_sha: str | None = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True,
            timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        git_sha = None
    snap = record_snapshot(
        drafts, driver_slug="component-a-drafts",
        driver_desc=f"Component-A drafts v{PROMPT_VERSION} for {snap_path.name} — {kind}",
        history_root=history_root, now=datetime.now(UTC), git_sha=git_sha,
        n_scanned=len(drafts), tier_field=None)
    drafts_out.write_text(json.dumps(
        {"scan_date": scan_date, "source": snap_path.name, "prompt_version": PROMPT_VERSION,
         "drafts": drafts}, indent=1, ensure_ascii=False) + "\n")

    ok = sum(1 for d in drafts if d["status"] == "drafted")
    print(f"\ndrafted {ok}/{len(drafts)} {kind} @ v{PROMPT_VERSION} "
          f"({len(drafts) - ok} unassessed-error) → {drafts_out}")
    print(f"scan-history snapshot → {snap}")
    print(f"manifest + {(history_root / 'manifest.jsonl').read_text().splitlines()[-1]}")
    print("\n=== DRAFTS (review sheet — hypotheses, not facts; suggestion is advisory) ===")
    for d in drafts:
        if d["status"] == "drafted":
            print(f"\n[{d['key']}] {d['draft_name']}  ·  suggested: {d['suggested']}")
            print(f"    hypothesis: {d['hypothesis']}")
            print(f"    reason: {d['reason']}")
        else:
            print(f"\n[{d['key']}] UNASSESSED-ERROR — {d['error']}")
        print(f"    members: {' '.join(str(t) for t in d['members'])}")
    if include_reviewed:
        _print_face_validity(drafts, reviews)
    return 0


def _print_face_validity(drafts: list[dict[str, Any]], reviews: list[dict[str, Any]]) -> None:
    """Face-validity comparison: each new draft suggestion NEXT TO the human's recorded decision for
    the same cluster, with the exact-agreement count and the park-or-reject count. Not tuning — a
    one-shot sanity read of the rubric against the human's own calls."""
    decision = {r["key"]: r.get("decision") for r in reviews}
    drafted = [d for d in drafts if d["status"] == "drafted"]
    agree = pr = 0
    print("\n=== FACE-VALIDITY: new draft suggestion vs the human decision (self-excluded) ===")
    print(f"  {'cluster':26} {'draft':16} {'human':16} match")
    for d in sorted(drafted, key=lambda x: x["key"]):
        human = decision.get(d["key"], "<none>")
        sug = d["suggested"]
        ok = sug == human
        agree += ok
        pr += sug in ("park", "reject")
        name = (d["draft_name"] or "")[:24]
        print(f"  {name:26} {sug:16} {str(human):16} {'✓' if ok else '✗'}")
    n = len(drafted)
    print(f"\nagreement (exact): {agree}/{n} · park-or-reject: {pr}/{n}")
    survivors = [d["key"] for d in drafted if d["suggested"] == "keep-for-checks"]
    if survivors:
        print(f"keep-for-checks survivors (REPORT — do not iterate the prompt further here): "
              f"{', '.join(survivors)}")


def _cmd_themes_review(args: argparse.Namespace) -> int:
    """Record the analyst's disposition for a drafted cluster → append to reviews.json (the single
    record). Validates the key against the latest snapshot; refuses an existing key without --amend;
    attributes by:"analyst", or "analyst (ratified advisor draft)" when decision+reason match.
    `reviewed` is the DATE OF REVIEW (today), not the scan date — the scan date already lives in the
    key. An --amend PRESERVES any extra fields on the existing entry (e.g. map_ref)."""
    from datetime import UTC, datetime

    snap_path, clusters, scan_date = _load_latest_component_a()
    if snap_path is None:
        print("!! no component-a snapshot — run `themes` first")
        return 2
    key = args.cluster
    valid = {f"{scan_date}:{c['cluster_id']}": c for c in clusters}
    if key not in valid:
        print(f"!! key {key!r} not a cluster in the latest snapshot ({scan_date}). "
              f"Valid: {', '.join(sorted(valid))}")
        return 2
    members = [m["ticker"] for m in valid[key].get("members", [])]

    reviews_path = Path("frontend/radar/reviews.json")
    doc = json.loads(reviews_path.read_text())
    existing = next((r for r in doc["reviews"] if r["key"] == key), None)
    if existing and not args.amend:
        print(f"!! {key} already reviewed (decision={existing['decision']}). --amend to overwrite.")
        return 2

    draft = None
    drafts_path = Path("frontend/radar/drafts.json")
    if drafts_path.exists():
        draft = next((d for d in json.loads(drafts_path.read_text()).get("drafts", [])
                      if d["key"] == key), None)
    ratified = bool(draft and draft.get("status") == "drafted"
                    and draft.get("suggested") == args.decision
                    and (draft.get("reason") or "").strip() == args.reason.strip())
    by = "analyst (ratified advisor draft)" if ratified else "analyst"
    draft_name = draft.get("draft_name") if draft and draft.get("draft_name") else None
    name = (args.name or draft_name or (existing.get("display_name") if existing else None)
            or " ".join(members[:3]))
    # {**existing, …} PRESERVES extra fields (map_ref) on --amend; a fresh review starts from {}.
    entry = {**(existing or {}), "key": key, "display_name": name, "decision": args.decision,
             "reviewed": datetime.now(UTC).date().isoformat(), "by": by, "reason": args.reason,
             "members": members}
    doc["reviews"] = [r for r in doc["reviews"] if r["key"] != key] + [entry]
    reviews_path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote review → {json.dumps(entry, ensure_ascii=False)}")
    return 0


def _pc_fmt(x: float | None) -> str:
    return "  n/a  " if x is None else f"{x * 100:+7.1f}%"


def _pc_fetch(members: list[str], benches: list[str], start: date, asof: date,
              client: Any) -> tuple[dict[str, dict[str, float]], list[str]]:
    """Split-adjusted daily closes for members + benches over [start, asof] via the repo Polygon
    client's per-symbol aggregates (`daily_bars`, adjusted=true — one cached call each; the
    single-basket analogue of the ad-hoc grouped-daily warm, same adjusted closes). The trading-day
    calendar is the union of the fetched dates (liquid names ⇒ the market calendar)."""
    needed = sorted(set(members) | set(benches))
    bars: dict[str, dict[str, float]] = {t: {} for t in needed}
    all_dates: set[str] = set()
    for t in needed:
        for d, bar in client.daily_bars(t, start, asof):
            if bar.close > 0:
                iso = d.isoformat()
                bars[t][iso] = bar.close
                all_dates.add(iso)
    return bars, sorted(all_dates)


def _pc_valuation(members: list[str], bars: dict[str, dict[str, float]],
                  asof: date) -> dict[str, Any]:
    """P/E percentile of own ~5y history (repo `pe_current_and_percentile`), basket median. The ONLY
    non-Polygon read — cached EDGAR companyfacts; absent/unresolvable → UNKNOWN, disclosed, never
    substituted. Reproduces the ad-hoc valuation_percentile verbatim."""
    import statistics as st
    from datetime import date

    from vinci.edgar.client import EdgarClient
    from vinci.edgar.concepts import extract_points
    from vinci.resolver import EntityResolver, ResolutionError, UnknownSymbolError
    from vinci.schemas.market import PriceBar
    from vinci.screens.assemble import pe_current_and_percentile

    resolver = EntityResolver.from_config()
    edgar = EdgarClient.from_config()
    per: dict[str, tuple[str, Any]] = {}
    for t in members:
        series = bars.get(t, {})
        if not series:
            per[t] = ("UNKNOWN", "no price bars")
            continue
        try:
            cik = resolver.resolve_ticker(t).cik
        except (UnknownSymbolError, ResolutionError) as e:
            per[t] = ("UNKNOWN", f"resolve: {type(e).__name__}")
            continue
        try:
            facts = edgar.companyfacts(cik)
        except Exception as e:  # noqa: BLE001 — absent XBRL → UNKNOWN, disclosed
            per[t] = ("UNKNOWN", f"companyfacts: {type(e).__name__}")
            continue
        annual_eps = [p for p in extract_points(facts, "eps_diluted") if p.is_annual]
        pbars = [PriceBar(internal_id=t, bar_date=date.fromisoformat(iso), open=c, high=c, low=c,
                          close=c, volume=0.0, source="polygon-grouped")
                 for iso, c in series.items() if c > 0]
        _pe, pctile = pe_current_and_percentile(pbars, annual_eps, reference_date=asof)
        per[t] = ("PCTILE", pctile.value) if pctile.value is not None else \
            ("UNKNOWN", pctile.note or "unknown")
    vals = [v for s, v in per.values() if s == "PCTILE"]
    return {"per": {t: list(v) for t, v in per.items()},
            "median": st.median(vals) if vals else None, "n": len(vals)}


def _print_priced_check(res: dict[str, Any], val: dict[str, Any], label: str) -> None:
    from vinci.themes import priced_check as pc

    members = res["members"]
    print("=" * 92)
    print(f"PRICED-CHECK — basket '{label}'  ({len(members)} members)   assemble numbers; conclude "
          "nothing")
    print(f"latest close = {res['latest']}   |   members: {' '.join(members)}")
    print("returns = adjusted-close cumulative (Polygon grouped-daily, adjusted=true; "
          "split-adjusted)")
    print("MECHANICAL TAG (12mo): excess vs BOTH SPY & IWM > +20% → PRICED ; both <= +20% → "
          "NOT-PRICED ; else MIXED")
    print("DISCLOSURES: price returns are DIVIDEND-BLIND; thin-n medians are weak; stale/delisted "
          "members (last bar > 7d old) are flagged and excluded from 'now'.")
    print("=" * 92)

    print("\nBENCHMARK cumulative returns (reference):")
    print(f"  {'window':8s} {'SPY':>9s} {'IWM':>9s}")
    for w in pc.WINDOWS:
        b = res["benchmarks"][w]
        print(f"  {str(w) + 'mo':8s} {_pc_fmt(b['spy'])} {_pc_fmt(b['iwm'])}")

    print(f"\nCOVERAGE over 18mo [{res['anchors'][18]} .. {res['latest']}] (bars found / gaps):")
    cells = [f"{t}:{f}/{g}" for t, (f, g) in res["coverage"].items()]
    for k in range(0, len(cells), 6):
        print("  " + "   ".join(cells[k:k + 6]))

    print("\n1) PRICED READ  (basket MEDIAN cumulative return; excess vs index; n = priced)")
    print(f"   {'window':7s} {'med ret':>9s} {'exSPY':>9s} {'exIWM':>9s} {'n':>4s}")
    for w in pc.WINDOWS:
        r = res["priced"][w]
        if "undef" in r:
            print(f"   {str(w) + 'mo':7s}  UNDEFINED — {r['undef']}  (n={r['n']})")
        else:
            print(f"   {str(w) + 'mo':7s} {_pc_fmt(r['med'])} {_pc_fmt(r['ex_spy'])} "
                  f"{_pc_fmt(r['ex_iwm'])} {r['n']:>4d}")

    print("\n2) TRAJECTORY  (quarter-by-quarter basket-median EXCESS vs IWM; oldest→newest)")
    for row in res["trajectory"]:
        lab = f"Q{row['q']}[{row['a']}->{row['b']}]"
        if row.get("undef"):
            print(f"   {lab}=UNDEF(n={row['n']})")
        else:
            print(f"   {lab}={row['ex_iwm'] * 100:+.1f}%(n={row['n']})")

    print("\n3) VALUATION — P/E percentile of own ~5y history (repo pe_current_and_percentile; "
          "point-in-time)")
    if val["median"] is not None:
        print(f"   basket MEDIAN P/E percentile = {val['median'] * 100:.0f}%ile   "
              f"(n={val['n']} of {len(members)} with a defined percentile)")
    else:
        print("   basket MEDIAN P/E percentile = UNDEFINED (0 members with a defined percentile)")
    defined = [f"{t}={v * 100:.0f}%" for t, (s, v) in val["per"].items() if s == "PCTILE"]
    unknown = [f"{t}({v})" for t, (s, v) in val["per"].items() if s == "UNKNOWN"]
    if defined:
        print("   defined:", "  ".join(defined))
    if unknown:
        print("   UNKNOWN:", "  ".join(unknown))

    print("\n4) DISPERSION — median pairwise corr of market-model RESIDUAL returns, trailing 6mo")
    dsp = res["dispersion"]
    if "undef" in dsp:
        print(f"   UNDEFINED — {dsp['undef']}")
    else:
        print(f"   median pairwise residual corr = {dsp['median']:+.2f}   "
              f"(members used={dsp['n_members']}, pairs={dsp['n_pairs']})")
    print(f"\nTAG: {res['tag']}")


def _cmd_themes_priced_check(args: argparse.Namespace) -> int:
    """Assemble the PRICE AXIS of a basket (the survivor price gate): split-adjusted basket-median
    6/12/18mo return, excess vs SPY/IWM, quarterly trajectory, residual dispersion, valuation
    percentile, and a MECHANICAL tag — no recommendation, no thesis. Polygon (cached) + one cached
    EDGAR read for the percentile. Snapshots each run so reads are dated + immutable."""
    import re
    import subprocess
    from datetime import timedelta

    from vinci.eod.client import PolygonEodClient
    from vinci.themes import priced_check as pc
    from vinci.themes.scan_history import record_snapshot

    cfg = get_config()
    cfg.ensure_dirs()
    members = [t.strip().upper() for t in args.basket.split(",") if t.strip()]
    if not members:
        print("!! --basket is empty")
        return 2
    label = args.label.strip()
    asof = date.fromisoformat(args.asof) if args.asof else date.today()
    start = asof - timedelta(days=1855)  # covers pe_current_and_percentile's 1825d window + pad

    print(f"fetching {len(members)} members + SPY/IWM over [{start} .. {asof}] "
          "(repo Polygon client, cache-first) …")
    client = PolygonEodClient.from_config()
    bars, trading = _pc_fetch(members, ["SPY", "IWM"], start, asof, client)
    ctx = pc.PriceCtx(bars, trading, asof)
    res = pc.compute(ctx, members)
    val = _pc_valuation(members, bars, asof)
    _print_priced_check(res, val, label)

    # dated + immutable snapshot: one record with the full price axis + valuation (json-safe)
    record = {
        "label": label, "asof": asof.isoformat(), "members": members, "tag": res["tag"],
        "priced": {str(w): res["priced"][w] for w in pc.WINDOWS},
        "trajectory": [{**r, "a": r["a"].isoformat(), "b": r["b"].isoformat()}
                       for r in res["trajectory"]],
        "dispersion": res["dispersion"],
        "coverage": {t: list(res["coverage"][t]) for t in members},
        "benchmarks": {str(w): res["benchmarks"][w] for w in pc.WINDOWS},
        "valuation": val, "trading_days": len(trading),
    }
    history_root = args.scan_history_dir or Path("data/scan_history")
    try:
        git_sha: str | None = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True,
            timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        git_sha = None
    slug = "priced-check-" + re.sub(r"[^a-z0-9-]+", "-", label.lower()).strip("-")
    snap = record_snapshot(
        [record], driver_slug=slug, driver_desc=f"Priced-check '{label}' asof {asof}",
        history_root=history_root, now=datetime.now(UTC), git_sha=git_sha, n_scanned=len(members),
        tier_field=None)
    print(f"\nscan-history snapshot → {snap}")
    if args.out:
        Path(args.out).write_text(json.dumps(record, indent=1) + "\n")
        print(f"operator export → {args.out}")
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


def _make_price_fn(eod: PolygonEodClient) -> PriceCloseFn:
    """As-of close lookup over Polygon grouped-daily, backstepping up to 5 days to the nearest
    trading day. None on no data (non-trading OR before the plan history window) - never faked."""
    from datetime import timedelta

    cache: dict[date, dict[str, float]] = {}

    def closes_on(day: date) -> dict[str, float]:
        for back in range(6):
            d = day - timedelta(days=back)
            if d not in cache:
                cache[d] = {t: b.close for t, b in eod.grouped_daily(d).items()}
            if cache[d]:
                return cache[d]
        return {}

    def price_fn(ticker: str, day: date) -> float | None:
        return closes_on(day).get(ticker)

    return price_fn


def _snapshot_assay(card: AssayCard, candidate: CandidateSpec, history_root: Path) -> None:
    """Archive the card's quarters via ``scan_history.record_snapshot`` (reused AS-IS). Each quarter
    is a record tagged ``exposure_basis=<reference-combo quadrant>`` so the manifest tier_counts
    summarize the quadrant distribution (contract requires an ``exposure_basis`` key per record)."""
    import subprocess

    from vinci.themes.assay import _REFERENCE_COMBO
    from vinci.themes.scan_history import record_snapshot

    dumped = [{**qr.model_dump(mode="json"),
               "exposure_basis": qr.quadrant_by_combo.get(_REFERENCE_COMBO, "UNKNOWN")}
              for qr in card.quarters]
    try:
        git_sha: str | None = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        git_sha = None
    record_snapshot(dumped, driver_slug=candidate.key, driver_desc=candidate.note,
                    history_root=history_root, now=datetime.now(UTC), git_sha=git_sha,
                    n_scanned=len(card.quarters))


def _assay_with_retries(
    build: Callable[[], AssayCard], *, label: str, attempts: int = 6
) -> AssayCard:
    """Self-healing wrapper for a cache-first assay build (step 7): retry on a TRANSIENT efts 5xx
    (the harness caches every successful read, so each retry resumes further). Fail LOUD with the
    exact missing read when attempts exhaust — never a silent partial."""
    import time

    from vinci.netcache import HttpError

    backoff, last = 20.0, ""
    for i in range(1, attempts + 1):
        try:
            return build()
        except HttpError as exc:
            last = str(exc)
            pause = "" if i == attempts else f" in {backoff:.0f}s"
            print(f"  [{label}] attempt {i}/{attempts} hit a transient read error; "
                  f"cache-first retry{pause} ...", file=sys.stderr)
            if i < attempts:
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 90.0)
    raise HttpError(
        f"assay '{label}' FAILED after {attempts} cache-first attempts; missing read: {last}")


def _price_and_types(eod: PolygonEodClient) -> tuple[PriceCloseFn, dict[str, str] | None]:
    """(price_fn, security_types) from one Polygon client. security_types is best-effort — on a
    reference-pull failure, warrant detection falls back to ticker-suffix only (logged, never
    silent)."""
    from vinci.netcache import HttpError

    try:
        sec_types: dict[str, str] | None = {t: ty for t, ty in eod.security_types().items() if ty}
    except HttpError as exc:
        print(f"  security_types unavailable ({exc}); warrant detection falls back to suffix-only",
              file=sys.stderr)
        sec_types = None
    return _make_price_fn(eod), sec_types


def _cmd_themes_assay(args: argparse.Namespace) -> int:
    """Earliness assay v1 for ONE candidate at an as-of. Deterministic reads only (EDGAR full-text +
    Polygon); ZERO LLM. Self-healing (cache-first retries on transient efts 5xx). Prints the card +
    JSON path; snapshots the quarters to history."""
    from vinci.sec import build_efts_http, build_sec_http
    from vinci.themes import assay

    cfg = get_config()
    cfg.ensure_dirs()
    candidate = CANDIDATE_SPECS[args.candidate]
    efts, sec_http = build_efts_http(cfg), build_sec_http(cfg)
    edgar = EdgarClient.from_config(cfg)
    price_fn, sec_types = _price_and_types(PolygonEodClient.from_config(cfg))
    cache_root = args.cache_dir or Path("data/assay_cache")
    placebo_terms = None if candidate.is_placebo else CANDIDATE_SPECS[PLACEBO_KEY].terms
    card = _assay_with_retries(
        lambda: assay.assay_candidate(
            candidate, date.fromisoformat(args.as_of), args.quarters, efts=efts, sec_http=sec_http,
            edgar=edgar, price_fn=price_fn, cache_root=cache_root, max_pages=args.max_pages,
            security_types=sec_types, placebo_terms=placebo_terms),
        label=f"{args.candidate}@{args.as_of}")
    jpath = assay.emit(card, args.out_dir or Path("data/assay"))
    _snapshot_assay(card, candidate, args.history_dir or Path("data/assay_history"))
    print(assay.render_markdown(card))
    print(f"card -> {jpath}")
    return 0


def _cmd_themes_assay_retrocast(args: argparse.Namespace) -> int:
    """Run the four control retrocasts, print each full card, then the pre-committed kill-criterion
    verdict under BOTH velocity definitions (RECORDED window-relative + v1 anchored) side by side.
    Sanctioned network (EDGAR + Polygon only, ZERO LLM). Self-healing (cache-first retries). The
    anchored verdict is printed ALONGSIDE, NEVER adopted; a disagreement is reported LOUD."""
    from functools import partial

    from vinci.sec import build_efts_http, build_sec_http
    from vinci.themes import assay

    cfg = get_config()
    cfg.ensure_dirs()
    efts, sec_http = build_efts_http(cfg), build_sec_http(cfg)
    edgar = EdgarClient.from_config(cfg)
    price_fn, sec_types = _price_and_types(PolygonEodClient.from_config(cfg))
    cache_root = args.cache_dir or Path("data/assay_cache")
    out_dir = args.out_dir or Path("data/assay")
    hist = args.history_dir or Path("data/assay_history")
    placebo_terms = CANDIDATE_SPECS[PLACEBO_KEY].terms
    # 2026 as-ofs approximate the frozen-basket freeze_timestamps (AI-DC 2026-07-02, defense
    # 2026-07-03); those files are git-ignored/off-repo, so these are the DOCUMENTED approximations.
    cases = [
        ("ai-datacenter", "2026-06-01", "PRICED at as-of"),
        ("defense-demand-shift", "2026-06-15", "PRICED at as-of"),
        ("ai-datacenter", "2022-07-01", "EARLY residence in-window"),
        ("defense-demand-shift", "2023-01-01", "EARLY residence in-window"),
    ]
    print("=" * 92)
    print("EARLINESS-ASSAY v2 RETROCAST - CONTRAST axis. Zero LLM; EDGAR + Polygon + subs.")
    print("KILL CRITERION (v0/v1, pre-committed, verbatim):")
    print(f"  {assay.KILL_CRITERION}")
    print("CONTRAST CRITERION (v2, pre-committed, verbatim):")
    print(f"  {assay.CONTRAST_CRITERION}")
    print("FINAL CRITERION (v2.1, pre-committed, verbatim):")
    print(f"  {assay.FINAL_CRITERION}")
    print("=" * 92)
    cards: list[AssayCard] = []
    for key, asof_s, expected in cases:
        candidate = CANDIDATE_SPECS[key]
        print(f"\n----- {key} @ {asof_s}  (expected: {expected}) -----")
        build = partial(
            assay.assay_candidate, candidate, date.fromisoformat(asof_s), args.quarters,
            efts=efts, sec_http=sec_http, edgar=edgar, price_fn=price_fn, cache_root=cache_root,
            max_pages=args.max_pages, security_types=sec_types, placebo_terms=placebo_terms)
        card = _assay_with_retries(build, label=f"{key}@{asof_s}")
        cards.append(card)
        assay.emit(card, out_dir)
        _snapshot_assay(card, candidate, hist)
        print(assay.render_markdown(card))
    v_rec, e_rec = assay.kill_verdict(cards)
    v_anch, e_anch = assay.kill_verdict(cards, anchored=True)
    print("\n" + "=" * 92)
    print("KILL-CRITERION VERDICT (printed evidence; never auto-acted-on)")
    print("\n-- RECORDED (window-relative v0 basis — THE recorded verdict):")
    for e in e_rec or ["(no >=2q EARLY residence under any combo)"]:
        print(f"  + {e}")
    print(f"  >>> {v_rec}")
    print("\n-- ANCHORED (v1 velocity — PENDING SANCTION; printed alongside, NOT adopted):")
    for e in e_anch or ["(no >=2q EARLY residence under any combo)"]:
        print(f"  + {e}")
    print(f"  >>> {v_anch}")
    rec_cls, anch_cls = v_rec.split()[0], v_anch.split()[0]
    print("\n" + "=" * 92)
    if rec_cls == anch_cls:
        print(f"AGREEMENT: RECORDED and ANCHORED verdicts AGREE ({rec_cls}). Anchored adoption "
              "still PENDING OPERATOR SANCTION.")
    else:
        print(f"!!! DISAGREEMENT: RECORDED={rec_cls} vs ANCHORED={anch_cls}. Anchored adoption "
              "STOPPED — operator must sanction; the RECORDED verdict stands.")
    print("=" * 92)

    # --- v2 CONTRAST criterion (pre-committed, mechanical) ---
    card_by = {(c.candidate_key, c.as_of): c for c in cards}
    placebo_incspec: dict[str, int] = {}  # merged placebo incumbent-specific (2018Q2..2023Q1)
    gated_placebo: dict[str, int] = {}  # v2.1 merged GATED placebo incumbent-specific
    for pa in ("2022-01-01", "2023-01-01"):
        pbuild = partial(
            assay.assay_candidate, CANDIDATE_SPECS[PLACEBO_KEY], date.fromisoformat(pa),
            args.quarters,
            efts=efts, sec_http=sec_http, edgar=edgar, price_fn=price_fn, cache_root=cache_root,
            max_pages=args.max_pages, security_types=sec_types)
        for qr in _assay_with_retries(pbuild, label=f"placebo@{pa}").quarters:
            if qr.incumbent is not None:
                placebo_incspec[qr.quarter] = qr.incumbent.incumbent_specific
                gated_placebo[qr.quarter] = qr.incumbent.gated_incumbent_specific
    positives = [("defense-demand-shift", "2023-01-01", "2021Q4"),
                 ("ai-datacenter", "2022-07-01", None)]
    print("\nCONTRAST VERDICT (v2, mechanical; incumbent-specific first-mentions)")
    contrast_any = confounded = False
    for key, asof_s, cutoff in positives:
        card = card_by[key, asof_s]
        theme = [qr.incumbent.incumbent_specific
                 for qr in card.quarters if qr.incumbent is not None]
        pser = [placebo_incspec.get(qr.quarter, -1) for qr in card.quarters]
        win = "through " + cutoff if cutoff else "full window"
        print(f"\n-- {key} @ {asof_s} (pre-re-rate: {win}) --")
        if -1 in pser or len(theme) != len(card.quarters):
            print("  >>> INCONCLUSIVE — placebo incumbent-specific does not cover the window")
            continue
        pre_idx = [i for i, qr in enumerate(card.quarters)
                   if cutoff is None or qr.quarter <= cutoff]
        verdict, ev = assay.contrast_verdict(theme, pser, pre_idx)
        print(f"  theme incumbent-specific:   {theme}")
        print(f"  placebo incumbent-specific: {pser}")
        for e in ev:
            print(f"  + {e}")
        print(f"  >>> {verdict}")
        contrast_any = contrast_any or verdict.startswith("CONTRAST SHOWN")
        confounded = confounded or verdict.startswith("CONFOUNDED")
    print("\n" + "=" * 92)
    if confounded:
        print("CONTRAST OUTCOME: CONFOUNDED — the placebo incumbent-specific itself qualifies; "
              "the machinery cannot support a contrast claim. Revisit tiers/incumbency first.")
    elif contrast_any:
        print("CONTRAST OUTCOME: >=1 positive control shows CONTRAST. Velocity axis -> Phase B "
              "(gate open PENDING ANALYST TIER RATIFICATION).")
    else:
        print("CONTRAST OUTCOME: NO positive control shows contrast. SCOPE-STOP ENGAGED — velocity "
              "axis DEMOTED to a diagnostic, further velocity-axis iteration is BARRED, and "
              "the assay ships reduced (price-axis PRICED-gate + decomposition + human reading).")
    print("=" * 92)

    # --- v2.1 FINAL criterion (filing-continuity-GATED series; pre-committed, mechanical) ---
    print("\nFINAL VERDICT (v2.1, mechanical; filing-continuity-GATED incumbent-specific)")
    gated_any = gated_confounded = False
    for key, asof_s, cutoff in positives:
        card = card_by[key, asof_s]
        gtheme = [qr.incumbent.gated_incumbent_specific
                  for qr in card.quarters if qr.incumbent is not None]
        gpser = [gated_placebo.get(qr.quarter, -1) for qr in card.quarters]
        win = "through " + cutoff if cutoff else "full window"
        print(f"\n-- {key} @ {asof_s} (pre-re-rate: {win}) --")
        if -1 in gpser or len(gtheme) != len(card.quarters):
            print("  >>> INCONCLUSIVE — gated placebo does not cover the window")
            continue
        pre_idx = [i for i, qr in enumerate(card.quarters)
                   if cutoff is None or qr.quarter <= cutoff]
        verdict, ev = assay.contrast_verdict(gtheme, gpser, pre_idx)
        print(f"  gated theme incumbent-specific:   {gtheme}")
        print(f"  gated placebo incumbent-specific: {gpser}")
        for e in ev:
            print(f"  + {e}")
        print(f"  >>> {verdict}")
        gated_any = gated_any or verdict.startswith("CONTRAST SHOWN")
        gated_confounded = gated_confounded or verdict.startswith("CONFOUNDED")
    print("\n" + "=" * 92)
    if gated_confounded or not gated_any:
        why = ("the GATED placebo still self-qualifies (criterion i failed)" if gated_confounded
               else "NO positive control shows contrast on the gated series")
        print("FINAL OUTCOME: SCOPE-STOP EXECUTES FINALLY — " + why + ". Velocity axis DEMOTED "
              "to a printed diagnostic, velocity-axis iteration BARRED; the assay ships reduced "
              "(price-axis PRICED-gate + decomposition + human reading).")
    else:
        print("FINAL OUTCOME: CONTRAST SHOWN on the gated series — velocity axis PROMOTED to "
              "evidential; Phase-B cards carry it (PENDING ANALYST TIER RATIFICATION).")
    print("=" * 92)
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
    p_dossier.add_argument(
        "--show-proposal", action="store_true", dest="show_proposal",
        help="reveal the SEALED machine proposal for --ticker (a peek; the brief hides it so it "
        "can't anchor you). If you peek before logging, pass log-verdict --saw-proposal.",
    )
    # (mid-cycle) the cyclical-underwriting block — computed for a single --ticker
    p_dossier.add_argument("--peers", help="comma-separated peer tickers for the mid-cycle margin "
                           "band (Anchor B), e.g. MRTN,HTLD; peers under 10y history excluded")
    p_dossier.add_argument("--scenario", action="append", default=[],
                           help="a mid-cycle scenario 'name:rev=<$M>,margin=<frac>,multiple=<x>' "
                           "(bear/base/bull; omit margin → anchor default). Repeatable.")
    for _sc in ("bear", "base", "bull"):
        p_dossier.add_argument(f"--reason-{_sc}", dest=f"reason_{_sc}",
                               help=f"why the {_sc} scenario deviates from the anchor "
                               "(REQUIRED for a deviated margin; refused otherwise)")
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
    p_log.add_argument(
        "--saw-proposal", action="store_true", dest="saw_proposal",
        help="self-report: you peeked at the machine proposal (dossier --show-proposal) BEFORE "
        "deciding. Stamps revealed_pre_verdict=True so the anchored disposition is down-weighted.",
    )
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
    p_themes.add_argument(
        "--scan-history-dir", type=Path, dest="scan_history_dir",
        help="scan-history archive root (default: data/scan_history; git-ignored)",
    )
    p_themes.add_argument(
        "--no-scan-history", action="store_true", dest="no_scan_history",
        help="skip the always-on timestamped history snapshot",
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
        help="Stage-3: semantic-primary exposure scan for a theme driver (--driver; assesses "
        "disclosed exposure from filings; never concludes)",
    )
    p_exp.add_argument(
        "--driver", required=True, choices=sorted(DRIVER_SPECS),
        help="theme driver to scan (from the DRIVER_SPECS registry; REQUIRED — no default)",
    )
    p_exp.add_argument("--ref", help="reference date YYYY-MM-DD (default: snapshot as_of)")
    p_exp.add_argument(
        "--window-days", type=int, default=290, dest="window_days",
        help="recent disclosure window in days (default: 290 ≈ 9.5mo)",
    )
    p_exp.add_argument("--max-names", type=int, dest="max_names", help="cap the universe (dev)")
    p_exp.add_argument(
        "--only-tickers", dest="only_tickers",
        help="restrict the scan to these comma-separated tickers, intersected with the universe "
        "(the monitor's delta-scan primitive); unknown names are printed and skipped, an empty "
        "intersection errors rather than scanning nothing",
    )
    p_exp.add_argument(
        "--only-file", type=Path, dest="only_file",
        help="like --only-tickers but read the tickers from a file (comma/newline-separated)",
    )
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

    p_draft = sub.add_parser(
        "themes-draft",
        help="Draft a name + hypothesis + advisory disposition for each UNREVIEWED cluster (1 LLM "
        "call each; the machine drafts, the human owns via themes-review)",
    )
    p_draft.add_argument("--force", action="store_true",
                         help="redraft even if drafts are current for this snapshot+version")
    p_draft.add_argument("--include-reviewed", action="store_true", dest="include_reviewed",
                         help="re-draft clusters reviewed FOR THIS scan (one-shot face-validity "
                              "check vs the human's calls); prints agreement")
    p_draft.add_argument("--scan-history-dir", type=Path, dest="scan_history_dir",
                         help="scan-history archive root (default: data/scan_history; git-ignored)")
    p_draft.set_defaults(func=_cmd_themes_draft)

    p_rev = sub.add_parser(
        "themes-review",
        help="Record the analyst's disposition for a drafted cluster → reviews.json",
    )
    p_rev.add_argument("--cluster", required=True, help="cluster key '<scan-date>:<cluster_id>'")
    p_rev.add_argument("--decision", required=True, choices=("keep-for-checks", "park", "reject"),
                       help="the analyst's disposition (draft vocabulary; ratification is a match)")
    p_rev.add_argument("--reason", required=True, help="one-line reason (verbatim to reviews.json)")
    p_rev.add_argument("--name", help="display name (default: the draft name, else top-3 tickers)")
    p_rev.add_argument("--amend", action="store_true", help="overwrite an existing review")
    p_rev.set_defaults(func=_cmd_themes_review)

    p_pc = sub.add_parser(
        "themes-priced-check",
        help="assemble a basket's PRICE AXIS (median 6/12/18mo return, excess vs SPY/IWM, "
        "trajectory, dispersion, valuation, mechanical tag) — the survivor price gate",
    )
    p_pc.add_argument("--basket", required=True,
                      help="comma-separated tickers, e.g. WERN,MRTN,HTLD")
    p_pc.add_argument("--label", required=True, help="basket name (snapshot slug + display)")
    p_pc.add_argument("--asof", help="latest-close date YYYY-MM-DD (default: today)")
    p_pc.add_argument("--out", help="optional operator export path (JSON record)")
    p_pc.add_argument("--scan-history-dir", type=Path, dest="scan_history_dir",
                      help="scan-history archive root (default: data/scan_history; git-ignored)")
    p_pc.set_defaults(func=_cmd_themes_priced_check)

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
    p_fwd.add_argument("--driver", required=True, choices=sorted(DRIVER_SPECS),
                       help="driver to freeze under (from the DRIVER_SPECS registry; REQUIRED — no "
                            "default, the same fail-loud gate as themes-exposure)")
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

    p_assay = sub.add_parser(
        "themes-assay",
        help="Earliness assay v0: velocity x price quadrant retrocast for ONE candidate (zero LLM)")
    p_assay.add_argument("--candidate", required=True, choices=sorted(CANDIDATE_SPECS),
                         help="candidate theme key (from the CANDIDATE_SPECS registry)")
    p_assay.add_argument("--as-of", dest="as_of", required=True, help="as-of date YYYY-MM-DD")
    p_assay.add_argument("--quarters", type=int, default=16, help="lookback quarters (default: 16)")
    p_assay.add_argument("--max-pages", type=int, default=8, dest="max_pages",
                         help="efts page cap per term-quarter (default: 8; cap => loud degrade)")
    p_assay.add_argument("--out-dir", type=Path, dest="out_dir",
                         help="card output dir (default: data/assay)")
    p_assay.add_argument("--cache-dir", type=Path, dest="cache_dir",
                         help="efts velocity cache dir (default: data/assay_cache)")
    p_assay.add_argument("--history-dir", type=Path, dest="history_dir",
                         help="scan-history archive root (default: data/assay_history)")
    p_assay.set_defaults(func=_cmd_themes_assay)

    p_retro = sub.add_parser(
        "themes-assay-retrocast",
        help="Run the four control retrocasts + print the pre-committed kill-criterion verdict")
    p_retro.add_argument("--quarters", type=int, default=16, help="lookback quarters (default: 16)")
    p_retro.add_argument("--max-pages", type=int, default=8, dest="max_pages",
                         help="efts page cap per term-quarter (default: 8)")
    p_retro.add_argument("--out-dir", type=Path, dest="out_dir",
                         help="card output dir (default: data/assay)")
    p_retro.add_argument("--cache-dir", type=Path, dest="cache_dir",
                         help="efts velocity cache dir (default: data/assay_cache)")
    p_retro.add_argument("--history-dir", type=Path, dest="history_dir",
                         help="scan-history archive root (default: data/assay_history)")
    p_retro.set_defaults(func=_cmd_themes_assay_retrocast)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_local_env()  # local: read repo-root .env; CI: no-op (injected secrets win)
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
