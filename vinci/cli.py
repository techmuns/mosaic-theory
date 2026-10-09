"""``vinci`` command-line entrypoint.

Grown one subcommand per build step. Today: ``resolve`` (step 1). Later: ``refresh`` (steps 3–4),
``screen`` (step 5), ``log-verdict`` (step 6), ``score`` (step 7).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from vinci.config import Config, get_config, load_local_env
from vinci.dossier.verdict import derive_proposal
from vinci.edgar import EdgarClient
from vinci.edge_basis import EDGE_BASES, EdgeBasisError, require_edge_basis
from vinci.eod import (
    PolygonEodClient,
    compute_price_features,
    ingest_prices,
    ingest_prices_per_symbol,
    last_completed_session,
)
from vinci.ledger import LedgerError, log_verdict
from vinci.monitor import BENCHMARK_LARGE, BENCHMARK_MID, BENCHMARK_SMALL
from vinci.orchestrator import (
    QUEUE_ADV_FLOOR,
    QUEUE_MD_TOP,
    carry_forward_assessment,
    rank_from_snapshots,
    run_monthly,
    run_weekly,
    write_queue_snapshots,
)
from vinci.progress import stderr_reporter
from vinci.rank import (
    load_candidates_from_snapshot,
    load_cause_annotations,
    render_profile_block,
)
from vinci.resolver import EntityResolver, ResolutionError
from vinci.schemas.data_record import Identity
from vinci.schemas.ledger import (
    EVENT_CLOSE,
    ORIGIN_FOLLOWED,
    ORIGIN_SCREEN,
    Confidence,
    LedgerEntry,
    Verdict,
    origin_of,
    sleeve_of,
)
from vinci.scoring import score_ledger
from vinci.scoring.baseline import resolve_baskets
from vinci.screens import screen_universe
from vinci.sleeves import DEFAULT_SLEEVE
from vinci.store import Store
from vinci.themes.assay import PriceCloseFn
from vinci.themes.assay_candidates import CANDIDATE_SPECS, PLACEBO_KEY
from vinci.themes.assay_schemas import AssayCard, CandidateSpec
from vinci.themes.drivers import DRIVER_SPECS
from vinci.universe import UNIVERSE_BANDS, benchmark_identity, build_universe


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


def _resolve_for_refresh(resolver: EntityResolver, ticker: str, *,
                         sic_failures: list[str] | None = None) -> Identity | None:
    """One ticker for a price backfill: STRICT on the identity, BEST-EFFORT on the SIC.

    WHY `refresh` ENRICHES AT ALL (closes STATE.md §5.0 row 7). This command is how a name that is
    NOT in the cap band enters the entity master — the ledgered-but-out-of-universe class, which
    `build_universe` never comes back to enrich because it never admits it. Resolving without the
    SIC left such a name with a PERMANENT hole: NFLX has sat SIC-less since it arrived exactly this
    way, and Gartner (#523) was the same class. Fetching it here fills the hole at the point of
    entry instead of leaving it for a later sweep.

    WHY THE SIC IS TOLERATED AND THE IDENTITY IS NOT. An unknown/ambiguous ticker still FAILS LOUD
    — mis-resolution is the system's worst failure and the resolver exists to refuse it. But a SIC
    is an ADORNMENT on a price backfill, and `resolve_ticker(enrich=True)` propagates the raw HTTP
    error when data.sec.gov is slow, rate-limiting or 500ing. Every ticker is resolved BEFORE any
    bars are fetched, so an un-caught SEC failure would abort the whole backfill before it started
    — a price job refusing to run because the SEC was flaky, for data the job does not need. So the
    SIC is best-effort and SAYS SO OUT LOUD; the bars are the job.

    SAFE ONLY BECAUSE OF #523. `upsert_security` now COALESCEs `sic`, so writing UNKNOWN can no
    longer erase a stored value. Before that fix this degradation would have been the clobber.

    AND THE TOLERANCE LIVES HERE, NOT IN THE RESOLVER — a soft mode on `EntityResolver` would let
    every other caller degrade silently, including the universe gate that deliberately fails CLOSED
    on a missing SIC (`unknown_sic`).
    """
    try:
        ident = resolver.resolve_ticker(ticker)
    except ResolutionError as exc:
        print(f"skip {ticker}: {exc}")
        return None
    try:
        sic, sic_desc = resolver.sic_for(ident.cik)
    except Exception as exc:  # noqa: BLE001 — reported, never guessed; the bars are the job
        print(f"{ticker}: SIC lookup FAILED ({type(exc).__name__}: {exc}) — refreshing prices with "
              f"SIC UNKNOWN. Bars are unaffected, and any stored SIC is preserved.")
        if sic_failures is not None:
            sic_failures.append(ticker)
        return ident
    if sic is None:
        # ABSENT, not broken — the distinction #523/#525 exist to keep visible.
        print(f"{ticker}: EDGAR publishes no SIC for this issuer (routine for BDCs and funds) — "
              f"stored as UNKNOWN, never inferred.")
    # `or None` is BELT-AND-BRACES, not the primary guard: `sic_for` normalises EDGAR's `""`
    # description at the source (pinned in `tests/test_resolver.py`). It is kept because this is
    # the last line before a DURABLE write to the entity master, and `upsert_security` COALESCEs
    # `sic_description` — SQL COALESCE treats '' as PRESENT, so a blank here would overwrite a
    # stored description rather than defer to it.
    return ident.model_copy(update={"sic": sic, "sic_description": sic_desc or None})


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Backfill/refresh Polygon EOD bars for the given tickers into the store."""
    cfg = get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    client = PolygonEodClient.from_config(cfg)
    secs = []
    sic_failures: list[str] = []
    attempted = 0
    for t in args.tickers:
        if t.upper() in {BENCHMARK_SMALL, BENCHMARK_MID, BENCHMARK_LARGE}:
            # benchmark ETFs are synthetic identities (IDX-*), not SEC issuers — resolver-exempt
            secs.append(benchmark_identity(t.upper()))
            continue
        attempted += 1
        if (ident := _resolve_for_refresh(resolver, t, sic_failures=sic_failures)) is not None:
            secs.append(ident)
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    mode = "per-symbol aggs" if args.aggs else "grouped-daily"
    print(f"refreshing {len(secs)} names {start}..{end} via {mode} "
          f"(Polygon free tier ≈ 5/min; be patient)…")
    with Store(cfg.db_path) as store:
        for s in secs:
            # STAMP `first_seen` — `build_universe` always has (`first_seen=reference_date`) and
            # this path never did, so every identity `refresh` INTRODUCED carries NULL (QQQ, TSM, V
            # in the committed master). That is not cosmetic: `identities_first_seen_after` is the
            # #442 failed-forward-run guard, and its `first_seen > ?` never matches NULL — so a
            # name this command introduced is INVISIBLE to it, and a backdated `run-weekly` would
            # admit a name it could not have known, which is the exact leak the guard exists to
            # stop. `upsert_security` COALESCEs `first_seen`, so this only ever stamps a NEW row;
            # an identity already in the store keeps the date it was really first seen.
            store.upsert_security(s, first_seen=date.today())
        if args.aggs:  # ONE call per symbol — for backfilling a NEW name's history (NCNO-class)
            summary = ingest_prices_per_symbol(
                client, store, secs, start=start, end=end, progress=stderr_reporter)
        else:  # whole-market grouped-daily — the ongoing universe refresh
            summary = ingest_prices(
                client, store, secs, start=start, end=end, progress=stderr_reporter)
    print(f"done: {summary}")
    if sic_failures:
        # SAID ONCE, AT THE END, AND AS A TALLY (review of #528). Per-name lines alone are not a
        # signal: on a long refresh during an SEC outage — or after a change that breaks `sic_for`,
        # since `except Exception` catches an AttributeError just as readily — every name degrades
        # to SIC UNKNOWN, the individual lines scroll past inside Polygon's progress output, and
        # the run still ends `done:` with exit 0. The operator then reasonably reads it as a clean
        # refresh while the exact hole this command exists to stop being dug is re-dug wholesale.
        print(f"WARNING: {len(sic_failures)}/{attempted} SIC lookup(s) FAILED — "
              f"{', '.join(sic_failures)} stored with SIC UNKNOWN (bars are unaffected, and no "
              f"stored SIC was overwritten). Re-run `scripts/backfill_entity_master_sic.py` once "
              f"EDGAR is healthy to fill them.")
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
    """Build + snapshot a cap-band universe (market cap = close × XBRL shares).

    ``--band theme`` builds the PARALLEL theme-altitude population into its own snapshot; the
    default builds the primary forward-validation population exactly as before."""
    cfg = get_config()
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    band_name = getattr(args, "band", "primary")
    stats = build_universe(reference_date=ref, band_name=band_name)
    band = getattr(cfg, UNIVERSE_BANDS[band_name][0])
    lo, hi = band.market_cap_min_usd / 1e6, band.market_cap_max_usd / 1e9
    print(f"universe[{band_name}] @ {ref} [${lo:.0f}M–${hi:.0f}B, "
          f"{'/'.join(band.exchanges)}]: {stats}")
    if band_name == "theme":
        print("  → theme-altitude population only: scans read it, screens/ranker/ledger never do")
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

    Reads the committed snapshots (no DB, no network unless ``--structural``):
    ``candidate_records.jsonl`` for the screen output and ``universe_snapshot.jsonl`` for size.
    The ranking itself goes through ``orchestrator.rank_from_snapshots`` — the SAME path the weekly
    job takes, so a hand-built queue and a CI-built one are the same object and cannot drift.
    Orders, never decides — see ``vinci.rank``.
    """
    from pathlib import Path

    cfg = get_config()
    snaps = cfg.snapshots_dir
    annotations = load_cause_annotations(Path(args.cause_file)) if args.cause_file else {}

    # CARRY FORWARD WHAT THE OPERATOR ALREADY ESTABLISHED (found while wiring the cohort split).
    #
    # `carry_forward_assessment` was added in #420 so a scheduled refresh could not silently un-sink
    # a name an 8-K disqualifier had capped — but it was wired into `run_weekly` ONLY. A hand-run
    # `vinci rank` therefore passed NO flags and wiped every one of them: measured on the committed
    # queue, a plain re-rank restored 58 structurally-disqualified names, and SOC — carrying a
    # "going-concern / substantial doubt" 8-K, capped at 0.05 and sunk to rank 212 — came back at
    # RANK 7. The manual path is the one an operator reaches for precisely when they are working
    # the queue by hand, which is the worst moment to lose it.
    #
    # Safe in the only direction that matters: the structural channel is DEMOTE-ONLY, so a carried
    # flag can only keep a name down. `--structural` still overrides with a fresh scan, and that
    # scan self-clears a signal that no longer fires.
    structural_flags, carried_causes = carry_forward_assessment(cfg)
    # `if not args.cause_file`, NOT `annotations or carried_causes`: an operator who passes a cause
    # file that annotates NOTHING is clearing the annotations, and a truthiness fallback would
    # silently resurrect the carried set underneath them — the supplied file having no effect and
    # saying nothing about it. Explicit file wins, empty or not.
    if not args.cause_file:
        annotations = carried_causes
    if args.structural:
        from vinci.edgar.client import EdgarClient
        from vinci.rank import scan_structural
        from vinci.sec import build_sec_http

        # loaded here only to feed the scan; rank_from_snapshots re-reads them as its own input
        cands = load_candidates_from_snapshot(snaps / "candidate_records.jsonl")
        if cands:
            print(
                f"scanning {len(cands)} candidates for structural disqualifiers "
                f"(EDGAR 8-K text + shares; DEMOTE-ONLY)…"
            )
            # `.flags` only, and it REPLACES the carried set outright: a manual scan is the
            # operator asking for this scan's verdict, so a stale flag must not be resurrected
            # underneath a name that now comes back clean. Coverage matters on the SCHEDULED path,
            # which must not read an unscanned name as clean (orchestrator).
            structural_flags = scan_structural(
                cands, edgar=EdgarClient.from_config(cfg), http=build_sec_http(cfg)
            ).flags

    ranked = rank_from_snapshots(
        cfg, annotations=annotations, structural_flags=structural_flags or None,
        deep_work_adv_floor=args.deep_work_adv_floor,
    )
    if not ranked:
        print(f"no candidates in {snaps / 'candidate_records.jsonl'} — run `vinci screen` first")
        return 1
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
        jsonl, md = write_queue_snapshots(cfg, ranked, md_top=args.md_top)
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
    # MIRROR WHAT WAS WRITTEN. Assembly is a DELIVERY PATH and it did not mirror — demonstrated on
    # this very command: SMPL's 2026-08-03 re-assembly wrote `data/dossiers/SMPL/` while the served
    # `frontend/dossiers/SMPL.md` stayed the older page. That is FUBO's missing-banner shape, which
    # #319 byte-pinned so it goes RED rather than silently serving stale — but red-after-the-fact is
    # a worse guarantee than not needing the pin.
    #
    # THE MIRROR IS A WHOLE-TREE REBUILD, AND THAT IS CORRECT — corrected claim (review of #325).
    # The first cut gated this on `if dossiers:` and said the gate stopped "publishing the OLD page
    # as though it were fresh". It does no such thing in a MIXED cohort: one name assembling and
    # another refusing still rebuilds the entire tree. The gate only skips a pointless rebuild when
    # NOTHING was written; claiming more of it was the declared-vs-enforced class again.
    #
    # NEITHER PARTIAL NOR SKIPPED MIRRORING IS THE FIX, and #319's own invariant is why: it asserts
    # EVERY `frontend/dossiers/<T>.md` is byte-identical to its source, so copying only the
    # successful names — or skipping on any error — strands whichever page had drifted, which is
    # the FUBO defect this call exists to prevent. And a refusal WRITES NOTHING, so a refused
    # name's mirror copy is byte-identical to what it already served (verified: matching sha256 on
    # data/ vs frontend/ for every committed name). The republish is a no-op, not a stale publish.
    #
    # WHAT WAS ACTUALLY MISSING is below: a partial failure must not exit 0.
    if dossiers:
        from vinci.dossier.refresh import mirror_to_frontend

        mirror_to_frontend()
    # (mid-cycle) single --ticker with --peers/--scenario → compute + attach the mid-cycle block
    if args.ticker and (getattr(args, "peers", None) or getattr(args, "scenario", None)):
        reasons = {n: getattr(args, f"reason_{n}") for n in ("bear", "base", "bull")
                   if getattr(args, f"reason_{n}", None)}
        peers = [p.strip().upper() for p in (args.peers or "").split(",") if p.strip()]
        rc = _attach_midcycle(cfg, args.ticker, peers=peers,
                              scenario_specs=args.scenario or [], reasons=reasons)
        if rc != 0:
            return rc
    # A PARTIAL FAILURE MUST NOT EXIT 0. This printed `errors` and returned success, so any caller
    # keying on the exit status read a refused assembly as a completed one — and it bit immediately:
    # the reroll harness written for THIS task read exit 0 as convergence and stopped after a single
    # refused build. D16's shape at the process boundary.
    # The per-name report stays: a batch still tells you WHICH names failed rather than dying on the
    # first. What changes is that the process no longer claims success while reporting failure.
    return 1 if errors else 0


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
            dna = kv.get("dna")
            if r_musd is None or multiple is None:
                print(f"  scenario {name!r}: needs rev= and multiple= "
                      "(multiple may default to the D-anchor only when CIQ is present)")
                return 2
            if dna is None:
                # The multiple is an EV/EBITDA turn; without D&A we would price off EBIT and
                # silently understate a capital-heavy name. Refuse rather than assume zero.
                print(f"  scenario {name!r}: needs dna=<$M> — `multiple` is an "
                      f"{mc.MULTIPLE_BASIS} turn, so D&A is required (pass dna=0 to mean zero)")
                return 2
            scenarios.append(mc.build_scenario(
                name, revenue=r_musd, multiple=multiple, anchor_margin=margin.median,
                d_and_a=dna, margin=kv.get("margin"), reason=reasons.get(name)))
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
    from vinci.scenarios import read_record as _read_rec
    try:  # ABSENT record = not underwritten (normal); a record that won't parse propagates LOUD
        _card = _read_rec(d2.ticker)
    except FileNotFoundError:
        _card = None
    (ddir / "dossier.md").write_text(
        render_markdown(d2, card=_card, dossiers_root=ddir.parent))
    print(f"  midcycle attached → {ddir} (anchors"
          f"{' + scenario grid + ratio' if priced else ' only'})")
    return 0




def _fs_value_drift(committed: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    """Committed financial-summary cells that the re-extraction would CHANGE.

    Widening only PREPENDS earlier periods, so the committed series must be the exact tail of the
    fresh one. A cell that was '—' purely because nothing preceded it is exempt: it is a derivation
    that has become computable, not a restatement. Compared POSITIONALLY from the end — several
    names carry duplicate period labels (BRBR's quarterly columns read FY24, FY24, FY24), so a
    label lookup silently compares the wrong column.
    """
    out: list[str] = []
    for tbl in ("annual", "quarterly"):
        cv = ((committed.get(tbl) or {}).get("value")) or {}
        fv = ((fresh.get(tbl) or {}).get("value")) or {}
        cols, fcols = cv.get("columns") or [], fv.get("columns") or []
        if not cols or not fcols:
            continue
        n = len(cols)
        if fcols[-n:] != cols:
            out.append(f"{tbl}: column tail differs")
            continue
        crows = {r["label"]: r["cells"] for r in cv.get("rows") or []}
        for r in fv.get("rows") or []:
            old = crows.get(r["label"])
            if old is None:
                continue
            tail = (r.get("cells") or [])[-n:]
            for i, (o, nw) in enumerate(zip(old, tail, strict=False)):
                if str(o) != str(nw) and not str(o).startswith("—"):
                    out.append(f"{tbl}/{r['label']}/{cols[i]}: {o!r}→{nw!r}")
    return out


def _cmd_financials_backfill(args: argparse.Namespace) -> int:
    """Re-extract financial_summary from the on-disk CIQ export into committed dossiers.

    The FINANCIALS-ONLY writer, modelled on ``anchor-backfill``: no re-assembly, no LLM, no other
    field touched. Written as a DICT-LEVEL patch because the committed files round-trip
    byte-identically under ``json.dumps(indent=2, ensure_ascii=False)`` (asserted per file before
    writing) while the pydantic model does NOT — it materialises absent optionals as explicit
    nulls, which would rewrite fields this command has no business touching.

    Why it exists: the extractor used to window the series at EXTRACTION (``fy[-4:]``,
    quarterly ``[-8:]``), so five-plus fiscal years and up to 33 quarters never entered
    dossier.json and were unrecoverable without the licensed workbook. Widening the extractor only
    helps names re-assembled afterwards; this backfills the ones already committed.
    """
    import json as _json

    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import financial_summary_annual, financial_summary_quarterly

    root = Path("data/dossiers")
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    rc = 0
    for t in tickers:
        jp = root / t / "dossier.json"
        if not jp.exists():
            print(f"{t}: no committed dossier.json — skipped")
            continue
        raw = jp.read_text()
        doc = _json.loads(raw)
        # PRE-EDIT ASSERTION: refuse to write unless the serialiser reproduces this file exactly,
        # so every untouched byte is provably preserved.
        if _json.dumps(doc, indent=2, ensure_ascii=False) != raw:
            print(f"{t}: REFUSING — serialiser does not reproduce the committed bytes")
            rc = 1
            continue
        paths = sorted((Path("data/manual/ciq") / t).glob("*.xls"))
        if not paths:
            print(f"{t}: no CIQ workbook on disk — skipped (re-extraction needs the export)")
            continue
        try:
            bundle = CiqBundle.from_files(t, paths)
            ann = financial_summary_annual(bundle)
            qtr = financial_summary_quarterly(bundle)
        except CiqUnavailableError as exc:
            print(f"{t}: CIQ unavailable ({exc}) — skipped")
            rc = 1
            continue
        fs = (doc.get("mechanical") or {}).get("financial_summary")
        if fs is None:
            print(f"{t}: no committed financial_summary block — skipped")
            continue
        before = (len((fs.get("annual") or {}).get("value", {}).get("columns", []) or []),
                  len((fs.get("quarterly") or {}).get("value", {}).get("columns", []) or []))
        new_ann = _json.loads(ann.model_dump_json())
        new_qtr = _json.loads(qtr.model_dump_json())
        after = (len((new_ann.get("value") or {}).get("columns", []) or []),
                 len((new_qtr.get("value") or {}).get("columns", []) or []))
        # VINTAGE GUARD. This command widens a WINDOW; it must never silently refresh VALUES.
        # The committed series has to be the exact tail of the re-extracted one — same columns,
        # same cells. When it is not, the on-disk workbook is a NEWER export than the one this
        # dossier was assembled from (CIQ stamps no export date, and the '≥' as-of is a floor, so
        # nothing else detects it). Refreshing numbers under a synthesis written against the old
        # ones is how a dossier starts citing figures it no longer contains — so: refuse, report,
        # and let a full re-assembly handle that name.
        drift = _fs_value_drift(fs, {"annual": new_ann, "quarterly": new_qtr})
        if drift:
            print(f"{t}: REFUSED — the on-disk CIQ export is NEWER than this dossier's assembly "
                  f"({len(drift)} committed value(s) would change, e.g. {drift[0]}). "
                  f"Re-assemble {t} instead so its synthesis matches its numbers.")
            rc = 1
            continue
        if args.dry_run:
            print(f"{t}: annual {before[0]}→{after[0]} cols · quarterly {before[1]}→{after[1]} "
                  f"(dry-run, nothing written)")
            continue
        fs["annual"], fs["quarterly"] = new_ann, new_qtr
        jp.write_text(_json.dumps(doc, indent=2, ensure_ascii=False))
        print(f"{t}: annual {before[0]}→{after[0]} cols · quarterly {before[1]}→{after[1]} → {jp}")
    return rc


def _peerset_drift(committed: str, fresh: str) -> str | None:
    """VINTAGE GUARD for the peer_set writer: the fresh roster may only LENGTHEN each business
    descriptor — same peer count, same per-peer 'Name $CAP' prefix (order included), same
    name-cap tail, and every committed descriptor a PREFIX of its fresh twin (the old capture
    was a word-boundary clip of the same underlying text). Anything else means the on-disk
    workbook is a different export than this dossier was assembled from → refuse (the
    financials-backfill precedent). Composer-output vs composer-output byte comparison — no
    display string is parsed back into values."""
    def parts(s: str) -> tuple[str, list[str], str] | None:
        m = re.match(r"^(\d+ peers) — (.*?)(\s\|\sthe name:.*)?$", s, re.DOTALL)
        if not m:
            return None
        return m.group(1), m.group(2).split("; "), m.group(3) or ""

    pc, pf = parts(committed), parts(fresh)
    if pc is None or pf is None:
        return "unparseable roster line"
    if pc[0] != pf[0]:
        return f"peer count changed ({pc[0]} → {pf[0]})"
    if pc[2] != pf[2]:
        return f"name-cap tail changed ({pc[2]!r} → {pf[2]!r})"
    if len(pc[1]) != len(pf[1]):
        return "segment count changed"
    for seg_c, seg_f in zip(pc[1], pf[1], strict=True):  # lengths equal — checked above
        head_c = seg_c.split(" — ", 1)[0]
        head_f = seg_f.split(" — ", 1)[0]
        if head_c != head_f:
            return f"peer/cap changed ({head_c!r} → {head_f!r})"
        desc_c = seg_c.split(" — ", 1)[1] if " — " in seg_c else ""
        desc_f = seg_f.split(" — ", 1)[1] if " — " in seg_f else ""
        # strip the shared " (HQ)" suffix; the widened text must extend the committed clip
        hq = re.search(r" \([^()]*\)$", desc_c)
        core_c = desc_c[: hq.start()] if hq else desc_c
        hq_f = re.search(r" \([^()]*\)$", desc_f)
        core_f = desc_f[: hq_f.start()] if hq_f else desc_f
        if (hq.group(0) if hq else "") != (hq_f.group(0) if hq_f else ""):
            return f"HQ suffix changed for {head_c!r}"
        # same underlying text proves itself by a prefix relation in EITHER direction: the widened
        # capture extends the old clip — or trims it, where the old [:55] ran PAST the sentence
        # end and grabbed spill from sentence two ("…worldwide. The company"). Only a text with
        # neither relation is a different export.
        if not (core_f.startswith(core_c.rstrip()) or core_c.startswith(core_f.rstrip())):
            return f"description text changed for {head_c!r} (newer export)"
    return None


def _cmd_peerset_backfill(args: argparse.Namespace) -> int:
    """Re-extract the peer_set roster from the on-disk CIQ export into committed dossiers.

    The PEER_SET-ONLY writer, modelled on ``financials-backfill``: a dict-level patch (the
    committed files round-trip byte-identically under ``json.dumps(indent=2,
    ensure_ascii=False)``, asserted per file) that touches ONLY
    ``mechanical.peer_comps.peer_set.value``. Why it exists: the extractor used to clip each
    business descriptor at a hard 55 chars mid-clause ("…risk assessment firm in the");
    widening the capture only helps names re-assembled afterwards — this backfills the ones
    already committed, refusing any name whose workbook is a newer export (``_peerset_drift``)."""
    import json as _json

    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import peer_comps

    root = Path("data/dossiers")
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    rc = 0
    for t in tickers:
        jp = root / t / "dossier.json"
        if not jp.exists():
            print(f"{t}: no committed dossier.json — skipped")
            continue
        raw = jp.read_text()
        doc = _json.loads(raw)
        if _json.dumps(doc, indent=2, ensure_ascii=False) != raw:
            print(f"{t}: REFUSING — serialiser does not reproduce the committed bytes")
            rc = 1
            continue
        paths = sorted((Path("data/manual/ciq") / t).glob("*.xls"))
        if not paths:
            print(f"{t}: no CIQ workbook on disk — skipped (re-extraction needs the export)")
            continue
        try:
            fresh = peer_comps(CiqBundle.from_files(t, paths)).peer_set
        except CiqUnavailableError as exc:
            print(f"{t}: CIQ unavailable ({exc}) — skipped")
            rc = 1
            continue
        ps = ((doc.get("mechanical") or {}).get("peer_comps") or {}).get("peer_set")
        if ps is None or ps.get("status") != "present" or not ps.get("value"):
            print(f"{t}: no committed present peer_set — skipped")
            continue
        if fresh.status.value != "present" or not fresh.value:
            print(f"{t}: fresh extraction returned {fresh.status.value} — skipped")
            rc = 1
            continue
        if fresh.source_ref != ps.get("source_ref"):
            print(f"{t}: REFUSED — source_ref changed ({ps.get('source_ref')!r} → "
                  f"{fresh.source_ref!r})")
            rc = 1
            continue
        drift = _peerset_drift(str(ps["value"]), str(fresh.value))
        if drift:
            print(f"{t}: REFUSED — {drift}. The on-disk export is not the one this dossier was "
                  f"assembled from; re-assemble {t} instead.")
            rc = 1
            continue
        old_len, new_len = len(str(ps["value"])), len(str(fresh.value))
        if ps["value"] == fresh.value:
            print(f"{t}: already at the widened capture — nothing to write")
            continue
        if args.dry_run:
            print(f"{t}: peer_set {old_len}→{new_len} chars (dry-run, nothing written)")
            continue
        ps["value"] = fresh.value
        jp.write_text(_json.dumps(doc, indent=2, ensure_ascii=False))
        print(f"{t}: peer_set {old_len}→{new_len} chars → {jp}")
    return rc


def _cmd_anchor_backfill(args: argparse.Namespace) -> int:
    """Backfill the committed R1 anchor block into existing dossiers — the anchor-ONLY writer.

    Computes the anchor from the committed mechanical layer + EDGAR (no CIQ workbook, no LLM, no
    re-assembly) and writes ONLY the ``anchor`` block into dossier.json: the model round-trips, so
    re-dumping reproduces the committed bytes plus the new field, leaving every other field
    byte-identical. dossier.md is then RE-RENDERED from that record: the anchor is not data-only —
    the page prints its base value and its reason, so leaving the markdown alone published the
    previous anchor beside the new one (review of #534)."""
    from vinci.dossier.anchor import (
        Anchor,
        anchor_changed,
        compute_anchor,
        preserve_operator_tag,
        replace_anchor_block,
    )
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.refresh import _rerender_only
    from vinci.dossier.schemas import Dossier
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver

    cfg = get_config()
    resolver, edgar = EntityResolver.from_config(cfg), EdgarClient.from_config(cfg)
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    done: list[tuple[str, Anchor, float | None, bool]] = []
    for t in tickers:
        path = cfg.data_dir / "dossiers" / t / "dossier.json"
        if not path.exists():
            print(f"  {t}: no committed dossier — skip")
            continue
        original = path.read_text()
        d = Dossier.model_validate_json(original)
        try:
            facts = edgar.companyfacts(resolver.resolve_ticker(t).cik)
        except Exception as exc:  # noqa: BLE001 — a name that won't fetch is skipped, never guessed
            print(f"  {t}: EDGAR fetch failed ({type(exc).__name__}) — skip, not written")
            continue
        # DEPTH-STAGE FALLBACK: the CIQ workbook fills a hole EDGAR left, never overrides it.
        # Extraction is cross-checked before it is offered; a sheet that failed a coherence check
        # is not handed on at all (ciq_balance refuses rather than degrades).
        ciq = None
        try:
            from vinci.dossier.ciq_balance import extract as _ciq_extract
            from vinci.dossier.manual_store import LocalFolderStore as _Store
            bundle = CiqBundle.from_files(t, _Store.from_config(cfg).files(t))
            ciq = _ciq_extract(bundle, t)
            if not ciq.ok:
                print(f"  {t}: CIQ extraction REFUSED — {'; '.join(ciq.failures)}")
                ciq = None
            elif ciq.facts:
                print(f"  {t}: CIQ bridge available ({len(ciq.facts)} facts, "
                      f"{len(ciq.checks)} checks passed)")
        except Exception as exc:  # noqa: BLE001 — no workbook is normal; EDGAR-only then
            print(f"  {t}: no CIQ bridge ({type(exc).__name__})")
        anchor = compute_anchor(d.mechanical.model_dump(mode="json"), facts=facts,
                                computed_at=datetime.now(UTC), ciq=ciq)
        # An operator's hand re-tag outranks the machine's fresh proposal — the recipe is preserved
        # and the divergence reported, never silently overwritten (the queued 2026-07-21 defect).
        anchor, notes = preserve_operator_tag(d.anchor, anchor)
        for n in notes:
            print(f"  {t}: {n}")
        old_base = d.anchor.anchor_base_value_per_share if d.anchor else None
        moved = anchor_changed(d.anchor, anchor)
        if args.dry_run:
            print(f"  {t}: DRY-RUN — {'CHANGED' if moved else 'unchanged'}")
        elif not moved:
            print(f"  {t}: anchor unchanged — not rewritten (artifact left byte-identical)")
        else:
            # byte-preserving replace/insert (a model round-trip drifts older-schema fields)
            path.write_text(replace_anchor_block(original, anchor))
            # AND THE PAGE, because the UI does NOT ignore the anchor (review of #534). This wrote
            # only dossier.json on the claim that the block is data-only; the renderer prints both
            # the base and the reason, so every backfill left the page asserting the PREVIOUS
            # anchor — GOOGL's read "$706.41" against a record saying 699.65, and later a refusal
            # sentence under an applicable one. Two committed artifacts disagreeing is the exact
            # failure `refresh_dossier` was written about; it recurred here because this command
            # writes its own. `_rerender_only` re-renders FROM the stored record: no recompute, no
            # LLM, no re-assembly — the page catches up to the JSON and nothing else moves.
            # GUARDED LIKE EVERY OTHER PER-TICKER STEP (review of #536). An unguarded raise here
            # kills the batch AFTER this name's JSON is written — leaving exactly the stale-page
            # state this call exists to prevent, and stranding every later name too. A page that
            # cannot be re-rendered is reported and the run continues: the JSON is already correct,
            # and the corpus invariant reds on the stale page rather than the batch dying quietly.
            try:
                if _rerender_only(path):
                    print(f"  {t}: dossier.md re-rendered to match the new anchor")
            except Exception as exc:  # noqa: BLE001 — one page must not strand the rest
                print(f"  {t}: WARNING — dossier.json written but dossier.md could NOT be "
                      f"re-rendered ({exc}); the page is stale until it is", file=sys.stderr)
        done.append((t, anchor, old_base, moved))
    n_moved = sum(1 for _t, _a, _o, mv in done if mv)
    mode = "DRY-RUN (nothing written)" if args.dry_run else "written"
    print(f"\n=== anchor backfill: {len(done)} name(s) processed · {n_moved} changed · {mode} ===")
    print(f"{'ticker':7}{'margin (yrs)':>18}{'multiple (qtrs)':>18}{'old base':>10}"
          f"{'new base':>10}{'move':>9}{'conf':>7}  data_quality")
    for t, a, old_base, moved in done:
        if (a.applicable and a.margin and a.margin.value is not None and a.multiple
                and a.multiple.value is not None and a.anchor_base_value_per_share is not None):
            m = f"{a.margin.value * 100:.1f}% ({a.margin.anchor_years}y {a.margin.confidence})"
            x = f"{a.multiple.value:.1f}x ({a.multiple.history_quarters}q {a.multiple.confidence})"
            new = a.anchor_base_value_per_share
            mv = (f"{(new - old_base) / old_base * 100:+.0f}%"
                  if old_base is not None and old_base != 0 else "NEW")
            print(f"{t:7}{m:>18}{x:>18}{(f'{old_base:.2f}' if old_base else '—'):>10}"
                  f"{new:>10.2f}{mv:>9}{a.overall_confidence or '—':>7}  {a.data_quality or ''}"
                  f"{' *' if moved else ''}")
        else:
            print(f"{t:7}  {a.recipe_hint} · applicable={a.applicable} — {a.reason}"
                  f"{' *' if moved else ''}")
    if n_moved:
        print("  (* = changed)")
    return 0


def sync_canonical_ciq(canonical: Path, local: Path, tickers: list[str]) -> list[str]:
    """Sync each ticker's CIQ folder FROM the canonical location, ALWAYS overwriting.

    There is no skip-if-present. SMPL's band was refreshed from a stale same-named copy precisely
    because a 'already present, skip' shortcut left an older export in place while the canonical one
    had moved on — the artifact then recorded a 4.98y window that did not exist. A missing canonical
    folder FAILS LOUD rather than falling back to whatever is lying in the worktree: reading
    an unknown-vintage file is the failure being prevented, not an acceptable degrade."""
    import shutil

    out: list[str] = []
    for t in tickers:
        src, dst = canonical / t, local / t
        if not src.is_dir() or not any(p.is_file() for p in src.iterdir()):
            raise FileNotFoundError(
                f"canonical CIQ folder missing/empty for {t}: {src} — refusing to refresh from "
                f"whatever copy is in the worktree (unknown vintage)")
        dst.mkdir(parents=True, exist_ok=True)
        for p in src.iterdir():
            if p.is_file() and not p.name.startswith("."):
                shutil.copy2(p, dst / p.name)          # ALWAYS overwrite — never skip-if-present
        out.append(f"{t}: synced {src}")
    return out


def _cmd_own_history_refresh(args: argparse.Namespace) -> int:
    """Refresh committed ``valuation.own_history`` from the CURRENT on-disk CIQ export (the
    2026-07-21 window-staleness fix), stamping periodicity/span/source_file metadata.

    Recomputes the band via the SHARED loader (own_history_bands — no re-impl), then writes
    ONLY that nested value byte-preserving (all other fields byte-identical). Prints old-vs-new
    median/span/n and the periodicity verdict; flags any name whose on-disk band is annual-spaced.
    A name with no CIQ file on disk is 'awaiting corrected export' — left untouched, listed. Does
    NOT touch the anchor block — run ``anchor-backfill`` after to re-derive the multiple leg."""
    from vinci.dossier import ciq_sheets as cs
    from vinci.dossier.anchor import replace_valuation_fields
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.mechanical import TRAILING_ONLY_NOTE
    from vinci.dossier.schemas import SourceStatus

    cfg = get_config()
    store = LocalFolderStore.from_config(cfg)
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if args.canonical_ciq:
        synced = sync_canonical_ciq(Path(args.canonical_ciq), cfg.data_dir / "manual" / "ciq",
                                    tickers)
        for line in synced:
            print(f"  sync: {line}")
    print(f"{'ticker':7}{'old med/n/yrs':>20}{'new med/n/yrs':>20}{'period':>11}  status")
    for t in tickers:
        path = cfg.data_dir / "dossiers" / t / "dossier.json"
        if not path.exists():
            print(f"{t:7}  no committed dossier — skip")
            continue
        original = path.read_text()
        doc = json.loads(original)
        oh_old = next((b for b in (((doc.get("mechanical") or {}).get("valuation") or {})
                                   .get("own_history") or {}).get("value") or []
                       if "EBITDA" in str(b.get("metric", ""))), None)
        if not store.available(t):
            print(f"{t:7}  AWAITING CORRECTED EXPORT — no CIQ file on disk; committed band kept")
            continue
        bundle = CiqBundle.from_files(t, store.files(t))
        band = cs.own_history_bands(bundle)
        if band.status != SourceStatus.PRESENT or not band.value:
            print(f"{t:7}  no own-history band from export ({band.note or 'unknown'}) — skip")
            continue
        new_val = [b.model_dump(mode="json") for b in band.value]
        oh_new = next((b for b in new_val if "EBITDA" in str(b.get("metric", ""))), None)
        # THE WHOLE multiples-derived CLUSTER, recomputed together. own_history, range_position,
        # ev_ebitda and (when CIQ-sourced) ev_ebitda_percentile_5y all read the SAME close series;
        # refreshing the band alone left a 35-close band beside a string still saying "over 20
        # closes" — the drift the shared loader exists to prevent. Recompute or don't touch it.
        val_old = ((doc.get("mechanical") or {}).get("valuation") or {})
        updates: dict[str, Any] = {"own_history": band.model_dump(mode="json")}
        updates["range_position"] = cs.range_position(bundle).model_dump(mode="json")
        ev = cs.ev_ebitda_current(bundle)
        if ev.status is SourceStatus.PRESENT and (
                (val_old.get("ev_ebitda_adjusted_fwd") or {}).get("status") != "present"):
            # mechanical._valuation's trailing-only blind-flag (no forward counterpart), IMPORTED
            # rather than mirrored: this line used to carry a byte-copy of the string, which is how
            # one book's vocabulary sat in two places at once and got fixed in neither.
            ev = ev.model_copy(update={"note": TRAILING_ONLY_NOTE})
        updates["ev_ebitda"] = ev.model_dump(mode="json")
        # percentile is EDGAR-screen-sourced when the screen knew it; only the CIQ path is ours
        pct_old = val_old.get("ev_ebitda_percentile_5y") or {}
        if "CIQ" in str(pct_old.get("source_ref") or ""):
            updates["ev_ebitda_percentile_5y"] = cs.ev_ebitda_percentile(bundle).model_dump(
                mode="json")

        def fmt(b: dict[str, Any] | None) -> str:
            if not b:
                return "—"
            return (f"{(b.get('median') or 0):.1f}/{b.get('n_closes')}/"
                    f"{b.get('window_span_years') or '?'}y")
        per = (oh_new or {}).get("periodicity") or "?"
        dq = (oh_new or {}).get("data_quality")
        changed = any(json.dumps(val_old.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
                      for k, v in updates.items())
        # print the flag VERBATIM — a band now carries more than one kind (periodicity_mismatch,
        # band_incoherent, or both joined by "+"), and a hardcoded label would misname the defect
        status = (f"{str(dq).upper()} ✗" if dq else
                  ("refreshed *" if changed and not args.dry_run else
                   ("would refresh (dry-run)" if changed else "unchanged (0/0)")))
        print(f"{t:7}{fmt(oh_old):>20}{fmt(oh_new):>20}{per:>11}  {status}"
              f"{'' if not changed else '  [' + ', '.join(sorted(updates)) + ']'}")
        if changed and not args.dry_run:
            path.write_text(replace_valuation_fields(original, updates))
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
        # THE BOOK COMES FROM THE ARTIFACT, never from a flag: the proposal must be derived under
        # the same framing the synthesis was written under, and the dossier is what records it.
        # THE GATE TRAVELS WITH THE ARTIFACT. A dossier whose draws disagreed must not seal a
        # proposal into the ledger that a re-assembly would not reproduce; `None` (a single-draw
        # artifact) means not measured and keeps the pre-2026-09-26 behaviour.
        _agree = (synth.get("draw_agreement") or {}).get("unanimous")
        prop = derive_proposal(synth.get("evidence_balance"),
                               sleeve=str(doc.get("sleeve") or DEFAULT_SLEEVE),
                               draws_unanimous=_agree if isinstance(_agree, bool) else None)
        stamp = doc.get("assembled_at")
        assembled = datetime.fromisoformat(stamp) if stamp else None
    except (ValueError, OSError) as exc:  # corrupt/unreadable artifact → loud, actionable
        raise LedgerError(f"committed dossier for {ticker} is unreadable: {exc}") from exc
    if prop.action is None:
        print(f"machine proposal for {ticker}: none — {prop.note}")
    return prop.action, prop.lean, assembled


def _committed_limit(ticker: str) -> Any:
    """The STATED limit off the committed scenario record, or None when there is no record.

    NO RECORD AND AN UNREADABLE RECORD ARE DIFFERENT FACTS, and the first draft of this collapsed
    them: a bare `except Exception` returned None for both, so a corrupt or schema-invalid
    `scenarios/<T>.json` SILENTLY DISABLED THE GATE and a BUY above a stated limit went through.
    Its docstring even argued for it — "a read failure must never block a write" — which is the
    wrong reasoning for a guard, where the reassuring answer (unenforced, proceed) is exactly the
    dangerous one. #362's rule, applied to a safety check rather than to a rendered fact.

    So: a MISSING record is None and unenforced, because most names have no record and never will.
    Anything else propagates and refuses the write loudly — a commitment we cannot read is not a
    commitment that is absent.
    """
    import vinci.scenarios as _sc
    try:
        return _sc.read_record(ticker.upper(), root=Path.cwd()).limit
    except FileNotFoundError:
        return None                        # no record for this name — unenforced, and that is true


def _committed_ev_gap(cfg: Config, ticker: str) -> Any:
    """The COMMITTED dossier's persisted EV gap, or None.

    READS THE ARTIFACT, NEVER RECOMPUTES. The gate asks what the human could point at when they
    decided; a fresh extraction would answer a different question and could pass a verdict the
    evidence on the page did not support. Absent/unreadable is a normal state (most names have no
    dossier) and degrades to None, which the gate turns into a NAMED refusal for option 1 and
    leaves irrelevant for the other five.
    """
    path = cfg.data_dir / "dossiers" / ticker.upper() / "dossier.json"
    try:
        return (json.loads(path.read_text()).get("mechanical") or {}).get("ev_gap")
    except (OSError, ValueError):
        return None


def _followed_identity(
    cfg: Config, resolver: EntityResolver, ticker: str
) -> tuple[Any | None, str | None]:
    """``(identity, sleeve)`` for a FOLLOWED ticker, or ``(None, None)`` if it is not followed.

    THE FOLLOW FILE IS THE ONLY ADMISSION KEY, and it is read through the SAME parser assembly uses
    (`_follow_entry`) — a second reader of that file is how the two would drift on the day one of
    them learned about a new field. A name absent from it gets no identity here, so the ledger door
    stays shut for everything except a name the operator has deliberately written down WITH its
    reason and its sleeve.

    The SLEEVE comes from the follow entry, not from a CLI flag: the operator states the strategy
    once, where the follow decision itself is recorded, and every artifact derives it from there.
    A flag would let the ledger row and the dossier disagree about what question was being asked.
    """
    from vinci.dossier.assemble import _follow_entry

    entry = _follow_entry(cfg, ticker.upper())
    if entry is None:
        return None, None
    return resolver.resolve_ticker(ticker.upper()), entry.sleeve


def _screen_id_book_conflict(cfg: Config, ticker: str) -> str | None:
    """Why a verdict logged by SCREEN CANDIDATE ID must be refused for ``ticker`` — or None.

    THE LEDGER TWIN OF `_finalist`'s TWO-ROUTES CHECK. A candidate id seals a screen-origin row
    with no sleeve, which reads as overshoot and counts in the PRIMARY spread. When the operator
    follows the same name under ANOTHER book (WLK: ruled into `ultra_short_term` while the screen
    still ranks it), that row would put the verdict into the fund's proof metric under a book the
    name is not judged in — and the ledger is append-only, so it could not be taken back out. The
    page's copy-paste command names the candidate id, so this is the likely path, not a contrived
    one. Logging by TICKER takes the followed route and carries the follow entry's book."""
    from vinci.dossier.assemble import _follow_entry

    entry = _follow_entry(cfg, ticker.upper())
    if entry is None or entry.sleeve == DEFAULT_SLEEVE:
        return None
    return (
        f"{ticker.upper()} is FOLLOWED under the {entry.sleeve!r} book, so a verdict logged by its "
        f"screen candidate id would be sealed as a screen-origin {DEFAULT_SLEEVE!r} verdict and "
        f"counted in the primary spread — a book this name is not judged in. Log it by ticker "
        f"(`log-verdict {ticker.upper()} …`) so the row carries the {entry.sleeve!r} book, or "
        f"remove the follow entry if the screen should own the name.")


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
            if cand is not None and (
                clash := _screen_id_book_conflict(cfg, cand.data_record.identity.ticker)
            ):
                raise LedgerError(clash)
            # THE FOLLOWED ROUTE. A followed name has NO candidate record by construction, so the
            # positional argument is its TICKER. Resolved here rather than inside `log_verdict`
            # because establishing that a name is genuinely followed is a dossier-layer question
            # (`followed.json`), and the ledger package must not import the dossier package.
            identity, origin, sleeve = None, ORIGIN_SCREEN, None
            if cand is None:
                identity, sleeve = _followed_identity(cfg, resolver, args.candidate_id)
                if identity is None:
                    raise LedgerError(
                        f"{args.candidate_id!r} is neither a candidate in the store nor a FOLLOWED "
                        f"ticker in data/followed.json — run the screen first, or add the follow "
                        f"entry (with its reason and sleeve) if this name is covered out of band.")
                origin = ORIGIN_FOLLOWED
            # (A4) THE EDGE-BASIS GATE, BEFORE the ledger write. The ledger is APPEND-ONLY, so a
            # verdict that reaches it cannot be un-logged — the gate has to refuse here or not at
            # all. It reads the COMMITTED dossier's persisted gap rather than recomputing: the
            # question is what the human could point at when they decided, not what a fresh
            # extraction would say afterwards.
            # THE GATE IS ORIGIN-BLIND: a followed name states its edge basis on exactly the same
            # terms as a screen name. The sleeve says WHICH BOOK; the edge basis says WHICH CLAIM.
            ticker = (cand.data_record.identity.ticker if cand is not None
                      else str(getattr(identity, "ticker", "")))
            edge_line = require_edge_basis(
                getattr(args, "edge_basis", None),
                ev_gap=_committed_ev_gap(cfg, ticker),
                note=getattr(args, "edge_note", None))
            mp, ml, stamp = _sealed_proposal(cfg, ticker)
            entry = log_verdict(
                store, resolver=resolver, candidate_id=args.candidate_id,
                identity=identity, origin=origin, sleeve=sleeve,
                verdict=Verdict(args.verdict),
                twin_call=args.twin,
                # SEALED INTO THE THESIS because the ledger row is append-only and has no field for
                # it yet. Prefixed so it is machine-findable later without parsing prose, and so a
                # reader meets the edge claim BEFORE the argument for it.
                thesis=f"[edge: {edge_line}] {args.thesis}", kill_criteria=args.kill,
                horizon_days=args.horizon_days, confidence=Confidence(args.confidence),
                decided_at=datetime.now(), reference_date=ref,
                staleness_days=cfg.price_staleness_days, benchmark=args.benchmark,
                # THE COMMITTED RECORD'S limit, read here and passed in — the gate itself must not
                # reach for a file. A name with no record, or a record with no limit, passes None
                # and is unenforced, which is every name today.
                stated_limit=_committed_limit(ticker),
                machine_proposal=mp, machine_lean=ml, proposal_assembled_at=stamp,
                revealed_pre_verdict=getattr(args, "saw_proposal", False),
            )
        except EdgeBasisError as exc:
            print(f"REFUSED — no verdict without a stated edge basis:\n{exc}")
            return 1
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
    _export_ledger(cfg, "log-verdict")
    return 0


def _export_ledger(cfg: Config, what: str) -> None:
    """Flush the working DB's ledger to the COMMITTED snapshot, and say where it landed.

    WHY EVERY LEDGER WRITE ENDS HERE. `log_verdict` wrote to the working SQLite DB and stopped, but
    the DB is a CACHE — the durable record is `data/snapshots/decision_ledger.jsonl`, and it is what
    `vinci monitor`, the frontend mirror and any fresh clone actually read (`_cmd_monitor` says so
    in its own docstring). So a verdict logged today reached no reader until somebody happened to
    run the weekly screen or the monthly score, both of which export as a side effect of doing
    something else. Measured on a copy of the committed tree: after a ledger write the DB held 7
    rows and the snapshot still held 6, byte-identical.

    Exporting the LEDGER TABLE ONLY, deliberately. A blanket export would also rewrite the
    universe/candidate snapshots from whatever half-populated state this operator's DB happens to
    be in, which is a much larger diff than the one decision the command was asked to record.
    """
    with Store(cfg.db_path) as store:
        store.export_snapshots(cfg.snapshots_dir, tables=["decision_ledger"])
    path = cfg.snapshots_dir / "decision_ledger.jsonl"
    n = len([ln for ln in path.read_text().splitlines() if ln.strip()])
    print(f"{what}: committed ledger now {n} row(s) → {path}")
    print("  the frontend mirror is NOT rebuilt by this command — run `python frontend/build.py` "
          "and commit, or CI's mirror-sync gate will fail the PR.")


def _cmd_close_position(args: argparse.Namespace) -> int:
    """Append the CLOSE row for a decision, then flush the committed ledger.

    THE COMMAND THAT DID NOT EXIST. The close-row schema, readers, display and id helper all
    shipped in `4f34c11`; the writer did not. Both committed closes were therefore hand-authored
    JSON — a row reaching an append-only record without passing one guard. This is that writer,
    with the guards the hand path never had: no unknown candidate, no second close, no exit before
    entry, and a stated reason (the schema's own rule, enforced where the operator can read it).
    """
    from vinci.ledger import close_position

    cfg = get_config()
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    reason = (args.reason or "").strip()
    if not reason:
        print("REFUSED: --reason is required — a position closes for a stated reason, or the "
              "record cannot be reviewed later.")
        return 1
    try:
        with Store(cfg.db_path) as store:
            close = close_position(
                store, candidate_id=args.candidate_id, exit_price=args.exit_price,
                exit_price_as_of=as_of, reason=reason,
                closed_at=datetime.now(UTC).replace(tzinfo=None))
    except LedgerError as exc:
        print(f"could not close: {exc}")
        return 1
    realized = close.exit_price / close.entry_price - 1.0 if close.exit_price else 0.0
    print(
        f"closed {close.ticker} [{close.verdict.value}] — entry {close.entry_price:.2f} "
        f"{close.entry_price_as_of} → exit {close.exit_price:.2f} {close.exit_price_as_of} "
        f"= {realized:+.2%} realized")
    print(f"  {close.entry_id} closes {close.closes_entry_id}. The DECISION keeps running to its "
          f"horizon — a close is a portfolio action, not a retraction of the call.")
    _export_ledger(cfg, "close-position")
    return 0


def _dossier_doc(ticker: str) -> dict[str, object]:
    path = get_config().data_dir / "dossiers" / ticker.upper() / "dossier.json"
    if not path.exists():
        raise FileNotFoundError(f"no committed dossier for {ticker.upper()} — assemble it first")
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _cmd_scenario_propose(args: argparse.Namespace) -> int:
    """Emit the underwrite template — anchors pre-filled, refusals carrying their evidence.

    A FILE rather than a prompt flow, because a reviewable, diffable artifact is what a handful of
    underwrites a quarter needs. This command NEVER writes a record; it writes a draft the analyst
    fills in and `scenario-create` validates."""
    from vinci.dossier.propose import ProposalRefusedError, build_template

    t = args.ticker.upper()
    try:
        doc = _dossier_doc(t)
        tpl = build_template(doc)
    except (FileNotFoundError, ProposalRefusedError) as exc:
        print(f"REFUSED: {exc}")
        return 1
    out = Path(args.out) if args.out else Path(f"{t}-underwrite.json")
    out.write_text(json.dumps(tpl, indent=2, ensure_ascii=False) + "\n")
    scen: dict[str, Any] = tpl["scenarios"]
    # THE CELLS THE TEMPLATE'S OWN RECIPE READS: an R4 template carries `ebit` and `multiple` and no
    # revenue or margin, so counting R1's trio would report "0 of 9" against six real cells.
    import vinci.scenarios as sc
    from vinci.dossier.propose import AXIS_LEG_FIELD
    axes = (sc.axes_for(sc.RECIPE_R4, tpl.get("multiple_basis")) or ()
            if tpl.get("recipe_id") == sc.RECIPE_R4 else ("revenue", "margin", "multiple"))
    fields = [AXIS_LEG_FIELD.get(a, a) for a in axes]
    total = len(fields) * len(scen)
    filled = sum(1 for c in scen.values() for f in fields if c.get(f) is not None)
    print(f"=== scenario-propose {t} -> {out} ===")
    print(f"  {filled} of {total} pre-filled from computed anchors; {total - filled} required "
          "from you")
    print(f"  recipe: {tpl['recipe_id']}   spot: {tpl['spot']}")
    print("  every empty cell states why it has no anchor; `_evidence` carries the dossier's own "
          "frame for each axis")
    return 0


def _cmd_scenario_create(args: argparse.Namespace) -> int:
    """Validate a filled template and WRITE the record — the create path that did not exist.

    `validate_legs` -> `run_recipe` -> `write_record`. Every guard already pinned applies: an
    anchored cell moved without a stated adjustment is refused, an unanchored cell with no stated
    derivation is refused, a missing leg is refused rather than defaulted, and a dossier/record
    recipe disagreement stops the write."""
    import vinci.scenarios as sc
    from vinci.dossier.propose import (
        ProposalRefusedError,
        assumptions_from,
        check_tier_agreement,
        legs_from_template,
        propose_anchors,
        validate_legs,
    )

    t = args.ticker.upper()
    src = Path(args.from_file)
    if not src.exists():
        print(f"no template at {src}")
        return 1
    tpl = json.loads(src.read_text())
    if str(tpl.get("ticker", "")).upper() != t:
        print(f"REFUSED: template is for {tpl.get('ticker')!r}, not {t}")
        return 1
    # CREATE NEVER OVERWRITES. `write_record` is an unconditional `path.write_text`, so without
    # this a create on a name that already has a record would DESTROY it and bypass
    # archive-and-reissue entirely — the supersession chain (`_amendment_index`, the archived
    # `<TICKER>-<date>`) is the record of what a verdict replaced, and it cannot be reconstructed.
    # REFUSE, DO NOT ROUTE: a create that silently becomes a supersede is a surprise on a
    # destructive path, and `scenario-propose` emits a template that LOOKS like it feeds this
    # command. Name the other command and its requirement so the refusal is actionable.
    if (sc.records_dir() / f"{t}.json").exists():
        print(f"REFUSED: {t} already has a committed record. `scenario-create` never overwrites — "
              "that would destroy it and skip archive-and-reissue. Use `scenario-supersede "
              f"{t} --payload <full-record.json>`, which archives the outgoing record and links "
              "the two. Note its payload is a COMPLETE ScenarioRecord, not this template.")
        return 1
    try:
        doc = _dossier_doc(t)
        check_tier_agreement(doc, str(tpl.get("recipe_id") or ""))
    except (FileNotFoundError, ProposalRefusedError) as exc:
        print(f"REFUSED: {exc}")
        return 1

    # AXES AND BASIS FROM THE RECIPE, never the module default: R3 models earnings and multiple
    # and reads no revenue or margin, so the R1 trio would demand two numbers its arithmetic never
    # touches and refuse a well-formed record — a create path that cannot create.
    _rid = str(tpl.get("recipe_id") or "")
    _basis = str(tpl.get("multiple_basis") or "") or None
    problems = validate_legs(legs_from_template(tpl), propose_anchors(doc),
                             axes=sc.axes_for(_rid, _basis), basis=_basis)
    # THE HORIZON, checked on the TEMPLATE rather than after construction: `ScenarioInput` accepts
    # `years_to_terminal=None` (R2 legacy records need it nullable), so a record built first would
    # validate and only fail later — the analyst deserves it in the same refusal list as everything
    # else, on one pass rather than round the loop again.
    _base = (legs_from_template(tpl).get("base") or {})
    if _base.get("years_to_terminal") is None:
        problems = problems + [
            "base.years_to_terminal is required — the house convention is nominal 2:1 AND a "
            "base-case IRR floor AND a stated horizon, and without a realisation date no IRR "
            "exists to test. State it in years (1.5 = 18 months); it is never defaulted, because "
            "a guessed horizon sets the return the record is then graded on."]
    # THE LEG-YEAR GUARD ON THIS PATH TOO. It was wired into `scenario-supersede` only, which left
    # the field unreachable from the path that CREATES records: no template cell, never read, never
    # enforced — so a created record could only ever read "unstated". Declared and readable but not
    # writable from its own writer is the same class as a helper nothing calls.
    _mech = doc.get("mechanical")
    _gap = (_mech.get("ev_gap") if isinstance(_mech, dict) else None) or {}
    _anchor_fy = _gap.get("anchor_fy") if isinstance(_gap, dict) else None
    # REVENUE IS NOT REQUIRED TO ASK FOR THE YEAR. The gate used to require BOTH `revenue` and
    # `multiple`, and R3 (forward-P/E) legs carry `eps` and no revenue — GOOGL's own recipe — so
    # the whole leg-year requirement was skipped on exactly the recipe the entry-window work was
    # motivated by. `ScenarioInput.revenue` is optional; only `multiple` is not.
    if _base.get("multiple") is not None and str(_base.get("reason") or "").strip():
        _base_leg = sc.ScenarioInput(
            revenue=(float(_base["revenue"]) if _base.get("revenue") is not None else None),
            margin=_base.get("margin"),
            multiple=float(_base["multiple"]), reason=str(_base.get("reason") or ""),
            leg_fy=(str(_base["leg_fy"]) if _base.get("leg_fy") else None))
        problems = problems + sc.leg_fy_problems(_base_leg, _anchor_fy, require_stated=True)
        # ...and the entry window, on the path that CREATES records. Without this the field is
        # unreachable from its own writer: `scenario-supersede` requires it, so every record the
        # create path produced would be refused by the very next supersede.
        problems = problems + sc.entry_basis_problems(
            (str(tpl.get("entry_basis")) if tpl.get("entry_basis") else None), _base_leg,
            entry_denominator=(float(tpl["entry_denominator"])
                               if tpl.get("entry_denominator") else None),
            require_stated=True)
    if problems:
        print(f"=== scenario-create {t}: REFUSED ({len(problems)}) ===")
        for p in problems:
            print(f"  - {p}")
        return 1

    legs = legs_from_template(tpl)
    try:
        rec = sc.ScenarioRecord(
            ticker=t, recipe_id=str(tpl["recipe_id"]), recipe_desc=str(tpl.get("recipe_desc") or
                                                                       tpl["recipe_id"]),
            multiple_basis=str(tpl["multiple_basis"]),
            # THE ENTRY WINDOW, carried from the template like every other stated field. Refused
            # above when blank, so a created record can never read "unstated" — the state the
            # field exists to end.
            entry_basis=(str(tpl["entry_basis"]).strip().upper().replace(" ", "")
                         if tpl.get("entry_basis") else None),
            entry_denominator=(float(tpl["entry_denominator"])
                               if tpl.get("entry_denominator") else None),
            underwrite_date=str(tpl["underwrite_date"]), analyst=str(tpl["analyst"]),
            spot=float(tpl["spot"]), spot_source=str(tpl["spot_source"]),
        # (PR-7) carried through from the template; `write_record` refuses without it from
        # schema 1.5, and a create that silently dropped it would make the gate
        # unsatisfiable from the one path that is supposed to satisfy it.
        spot_as_of=(date.fromisoformat(str(tpl["spot_as_of"])[:10])
                    if tpl.get("spot_as_of") else None),
            facts={k: sc.Fact(**v) for k, v in (tpl.get("facts") or {}).items()},
            scenarios={leg: sc.ScenarioInput(
                # BOTH CONDITIONAL (review of #542). `margin` was unconditional, so a template
                # edited for R3 — which refuses a margin, because EPS already contains it — could
                # not be built at all: the `eps` plumbing below was unreachable, a capability that
                # cannot fire. `revenue` follows for the same reason, one recipe later.
                revenue=(float(c["revenue"]) if c.get("revenue") is not None else None),
                margin=(float(c["margin"]) if c.get("margin") is not None else None),
                multiple=float(c["multiple"]), reason=str(c.get("reason") or ""),
                # carried from the template, never defaulted — `horizon_problems` refuses below if
                # the analyst left it empty
                years_to_terminal=(float(c["years_to_terminal"])
                                   if c.get("years_to_terminal") is not None else None),
                # carried from the template, which pre-fills it with the gap's anchor year —
                # the year `propose_anchors` actually struck the revenue at
                leg_fy=(str(c["leg_fy"]) if c.get("leg_fy") else None),
                # (R3) the P/E recipe's only driver. Carried from the template like every other
                # leg field, never defaulted: `_run_r3` refuses a leg without one rather than
                # assuming a number, and a field the template cannot set is a field a created
                # record can never carry.
                eps=(float(c["eps"]) if c.get("eps") is not None else None),
                # (R4) the EV/NTM EBIT recipe's leg driver — carried for the same reason as `eps`:
                # `_run_r4` refuses a leg without one, so a template that cannot set it is a
                # recipe the create path cannot reach (found by a real create on AMZN, 2026-10-08)
                ebit=(float(c["ebit"]) if c.get("ebit") is not None else None),
                bear_basis=(c.get("bear_basis") or None),
                margin_basis=(c.get("margin_basis") or None)) for leg, c in legs.items()},
            # PASSED AT CONSTRUCTION, not patched in after: ScenarioRecord itself refuses a
            # schema-1.4 record whose assumptions do not cover all three axes, so a create path
            # that built the record first could never write at all.
            assumptions={ax: sc.AssumptionDerivation(
                method=a["method"],
                references=[sc.RefPoint(**r) for r in a["references"]])
                for ax, a in assumptions_from(doc, legs, axes=sc.axes_for(_rid, _basis),
                                              basis=_basis).items()},
        )
        rec = sc.run_recipe(rec)
        path = sc.write_record(rec)
    except (ValueError, KeyError, TypeError) as exc:
        print(f"REFUSED: {type(exc).__name__}: {exc}")
        return 1
    print(f"=== scenario-create {t} -> {path} ===")
    r = rec.result
    for leg in ("bear", "base", "bull"):
        o = r.per_scenario.get(leg)
        if o:
            print(f"  {leg:5} value/share ${o.value_per_share:,.2f}")
    print(f"  reward {r.reward} · risk {r.risk} · ratio {r.ratio} · bar {r.bar} -> {r.pass_fail}")
    return 0


def _cmd_scenario_refresh(args: argparse.Namespace) -> int:
    """THE path for changing a record's MACHINE inputs (record legibility, 2026-07-27).

    Before this existed, `write_record()` had zero programmatic callers and every record edit was
    hand-edited JSON — which is how a machine refresh ended up narrated inside a SEALED rationale.
    Refreshes now land in the structured `refresh_log`, and `machine`-class amendment tags are
    refused from the rationale outright (vinci/seal.py). Hand-editing remains physically possible;
    it is now the exception, not the norm."""
    from datetime import date as _date

    import vinci.scenarios as sc

    # THE QUANTITY A REFRESH SUPPLIES, declared (2026-08-21). Until now this command could only
    # send a bare float, which is precisely why the diluted_shares hazard had no door to close:
    # the value moved while the basis kept naming a quantity the number no longer was. For a
    # QUANTITY_SENSITIVE fact the engine now REFUSES an undeclared refresh, so the operator needs
    # a way to say which one — and saying it is the point, not a formality.
    kinds: dict[str, str] = {}
    for kv in (args.fact_kind or []):
        if "=" not in kv:
            print(f"--fact-kind expects KEY=KIND, got {kv!r}")
            return 2
        k, _, v = kv.partition("=")
        kind = v.strip()
        # CHECKED HERE, not at `Fact(...)` (review fix): the model validator raises a pydantic
        # ValidationError, which no caller catches — a mistyped kind (`oustanding`) exited the CLI
        # on a raw traceback while every other malformed argument on this command prints one line
        # and returns 2. An EMPTY kind was worse than loud: it fell through to a bare float and the
        # refusal told the operator to pass `--fact-kind`, which is what they had just passed.
        if kind not in sc.QUANTITY_KINDS:
            print(f"--fact-kind {k.strip()}: {kind!r} is not one of "
                  f"{sorted(sc.QUANTITY_KINDS)}")
            return 2
        kinds[k.strip()] = kind

    facts: dict[str, float | sc.Fact] = {}
    parsed: dict[str, float] = {}
    for kv in args.fact:
        if "=" not in kv:
            print(f"--fact expects KEY=VALUE, got {kv!r}")
            return 2
        k, _, v = kv.partition("=")
        try:
            parsed[k.strip()] = float(v)
        except ValueError:
            print(f"--fact {k.strip()!r}: {v!r} is not a number")
            return 2
    unknown = sorted(set(kinds) - set(parsed))
    if unknown:
        print(f"--fact-kind names {unknown} which no --fact supplies")
        return 2
    try:
        rec = sc.read_record(args.ticker.upper())
    except FileNotFoundError:
        print(f"no committed record for {args.ticker.upper()}")
        return 1
    # A DECLARED kind rides on a Fact carrying the record's OWN basis/source/unit: the operator is
    # declaring WHICH QUANTITY the new number is, not rewriting the provenance prose. If the two
    # disagree the engine refuses — that refusal is the whole point of the flag.
    for k, val in parsed.items():
        kind = kinds.get(k)
        cur = rec.facts.get(k)
        if kind and cur is not None:
            facts[k] = sc.Fact(value=val, unit=cur.unit, basis=cur.basis, source=cur.source,
                               quantity_kind=kind)
        else:
            facts[k] = val
    on_date = args.as_of or _date.today().isoformat()
    try:
        out = sc.refresh_record(rec, spot=args.spot, facts=facts or None,
                                source=args.source, on_date=on_date)
    except sc.RefreshRefusedError as exc:
        print(f"REFUSED: {exc}")
        return 1
    new_entries = out.refresh_log[len(rec.refresh_log):]
    if not new_entries:
        print(f"{rec.ticker}: nothing to refresh — every supplied value already matches the record")
        return 0
    print(f"=== scenario-refresh {rec.ticker} ({on_date}) ===")
    for e in new_entries:
        print(f"  {e.field:22} {e.old} → {e.new}")
    print(f"  source: {args.source}")
    print(f"  ratio {rec.result.ratio and round(rec.result.ratio, 4)} → "
          f"{out.result.ratio and round(out.result.ratio, 4)}  ({out.result.pass_fail})")
    print("  legs / assumptions / verdict / rationale: UNTOUCHED (asserted)")
    if args.dry_run:
        print("  --dry-run: nothing written")
        return 0
    print(f"  written: {sc.write_record(out)}")
    return 0


#: The `result` fields a supersede compares. THE DECISION-BEARING ONES ONLY, named explicitly
#: rather than diffing the whole model: `per_scenario` carries floats that differ in the last bit
#: on a re-run, and a whole-object comparison would refuse legitimate payloads over noise no
#: reader could act on. These six are what the gate, the card headline and the spread are struck
#: from — if any of them moves, the record says something different.
_RESULT_COMPARED: tuple[str, ...] = ("reward", "risk", "ratio", "pass_fail", "irr", "gate")


def _result_mismatch(stated: Any, computed: Any) -> str | None:
    """A human-readable diff of the decision-bearing result fields, or None when they agree.

    Floats compare with a relative tolerance: the recipe is deterministic, but a payload that
    round-tripped through JSON at lower precision is a formatting artefact and not a disagreement
    about the arithmetic. 1e-6 is far below any figure a reader acts on and far above repr noise.
    """
    out: list[str] = []
    for f in _RESULT_COMPARED:
        a, b = getattr(stated, f, None), getattr(computed, f, None)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if abs(a - b) > max(1e-6, abs(b) * 1e-6):
                out.append(f"{f}: stated {a:.6g}, legs give {b:.6g}")
        elif a != b:
            out.append(f"{f}: stated {a!r}, legs give {b!r}")
    return "; ".join(out) or None


def _result_is_stated(result: Any) -> bool:
    """True when the payload actually STATES a result, i.e. it is not the schema's virgin block.

    `ScenarioRecord.result` is `Field(default_factory=Result)`, so a payload that omits `result`
    (or carries `"result": {}`) arrives as an ALL-DEFAULT `Result()`, not as `None`. That is the
    analyst declining to state a number — the same posture `scenario-create` starts from — and it
    must be DERIVED, never refused: every compared field reads `stated None, legs give <x>`, so
    without this the refusal message's own advice ("drop the stated result and let the recipe
    compute it") is unfollowable, and the archive-and-reissue that stamps a record under the
    tiered ladder has no payload shape that works — a stated result freezes the ladder, and an
    unstated one was refused.
    """
    import vinci.scenarios as sc

    return bool(result is not None and result != sc.Result())


def _cmd_scenario_criterion(args: argparse.Namespace) -> int:
    """Attach a STRUCTURED criterion to a record, beside the analyst's prose — never parsed from it.

    THE WRITE PATH THAT DID NOT EXIST. `MeasuredTrigger` shipped with the evaluator (#552), the
    sustain history (#556) and the three-state card, and NOTHING could put one on a record: zero
    committed records carry a single structured criterion, so the whole chain evaluated an empty
    list on every run. Sixth instance of the built-and-unreachable shape in this repo, and the
    plan's stated next step — "criteria gain a structured form written BESIDE the prose"
    (`docs/records/2026-08-31-phase-rulings.md`).

    IT REFUSES A METRIC THAT DOES NOT RESOLVE, and that refusal is the point. A criterion naming a
    path this name's dossier does not carry evaluates to UNKNOWN on every run, which on the
    dashboard is indistinguishable from a working criterion that has not fired — the
    absent-vs-broken collapse, on the surface built to keep three states apart. Caught at write
    time, when the analyst is present to fix it, the failure costs a sentence; caught never, it
    costs a falsifier nobody notices is dead. SMPL's own "Quest revenue growth" is the live
    example: real arithmetic, but a BRAND figure read from a transcript and LLM-fenced by the
    covenant discipline, so no anchored path carries it.

    THE THRESHOLD, THE COMPARATOR AND THE SENTENCE ARE THE ANALYST'S. This command types what they
    dictate and refuses what cannot be read; it never chooses a number.
    """
    from pydantic import ValidationError

    import vinci.scenarios as sc
    from vinci.triggers import UNKNOWN, evaluate, resolvable_metrics, resolve_metric

    t = args.ticker.upper()
    root = Path.cwd()
    path = root / "scenarios" / f"{t}.json"
    if not path.is_file():
        print(f"REFUSED: no committed record for {t} — a criterion attaches to an underwrite.")
        return 1
    doc_path = root / "data" / "dossiers" / t / "dossier.json"
    if not doc_path.is_file():
        print(f"REFUSED: no committed dossier for {t}, so no metric can be resolved or refused. "
              f"A criterion written blind is one nobody can evaluate.")
        return 1

    rec = sc.ScenarioRecord.model_validate(json.loads(path.read_text()))
    mech = (json.loads(doc_path.read_text()).get("mechanical") or {})

    # RESOLVE BEFORE WRITING, through the evaluator's own resolver — not a second opinion about
    # what "resolvable" means, which would drift from the thing that actually reads it.
    node, source = resolve_metric(mech, args.metric)
    value = node.get("value") if isinstance(node, dict) else None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        menu = resolvable_metrics(mech)
        print(f"REFUSED: {t} carries no numeric value at {args.metric!r}. A criterion on a path "
              f"this dossier does not hold reads UNKNOWN on every run, which looks exactly like a "
              f"criterion that has not fired.")
        if menu:
            print(f"\n  {len(menu)} paths on {t} that CAN be evaluated:")
            for mpath, mval, _src in menu:
                print(f"    {mpath:52s} {mval:,.4g}")
        else:
            print(f"  {t}'s dossier carries no numeric, source-bound path at all.")
        return 1

    try:
        trig = sc.MeasuredTrigger(
            trigger=args.trigger, metric=args.metric, comparator=args.comparator,
            threshold=args.threshold, unit=args.unit, sustain=args.sustain,
            basis=args.basis or (source or ""))
    except ValidationError as exc:
        # THE MODEL'S OWN REFUSALS REACH THE ANALYST AS REFUSALS. `--sustain 0` and a blank
        # `--trigger` are both typing mistakes at the keyboard, and a raw pydantic traceback in
        # the middle of a command whose every other refusal is one printed line reads as a crash
        # in the tool rather than a correction to the input.
        print(f"REFUSED: that is not a well-formed criterion — {exc.error_count()} problem(s):")
        for err in exc.errors():
            print(f"    {'.'.join(str(x) for x in err['loc']) or '(record)'}: {err['msg']}")
        return 1

    existing = list(rec.verdict.measured_triggers)
    if any(x.metric == trig.metric and x.comparator == trig.comparator
           and x.threshold == trig.threshold and x.sustain == trig.sustain for x in existing):
        print(f"REFUSED: {t} already carries this exact criterion — a duplicate would be counted "
              f"twice by the monitor and read as two independent falsifiers.")
        return 1

    # WHAT IT READS TODAY, printed before the write. A criterion that is ALREADY firing at the
    # moment it is written is a fact the analyst should see now, not discover on the next run.
    state = evaluate(trig, mech)
    print(f"=== scenario-criterion {t} ===")
    print(f"  trigger    {trig.trigger}")
    print(f"  measures   {trig.metric} {trig.comparator} {trig.threshold:g} {trig.unit}"
          f"{f', sustained {trig.sustain} readings' if trig.sustain > 1 else ''}")
    print(f"  resolves   {value:,.6g}  [{source or 'no source_ref'}]")
    # THE UNIT IS ASSERTED, NOT CHECKED — say so, every time, because the evaluator cannot.
    # `evaluate` refuses only a node that STATES a disagreeing unit, and across the committed
    # corpus ZERO of 479 resolvable paths state one, so that refusal has never fired and cannot.
    # A mis-stated unit therefore produces a CONFIDENT WRONG ANSWER rather than an UNKNOWN: a $M
    # value read against a $bn threshold reports `551.974 $bn > 1 $bn holds` — FIRED, on a kill
    # criterion, when $551.974M is $0.55bn and the truth is NOT_FIRED. A false FIRED is worse than
    # a false UNKNOWN, and the analyst is the only one who can catch it, so the check is put in
    # front of them beside the number and its source — which usually names the scale itself.
    if not (isinstance(node, dict) and node.get("unit")):
        print(f"  ⚠ UNIT UNCHECKED — this reading states no unit of its own, so {args.unit!r} is "
              f"taken on trust. Confirm {value:,.6g} is in {args.unit} against the source above; a "
              f"wrong unit here reads as a confident FIRED, not an error.")
    print(f"  reads      {state.state} — {state.reason}")
    if args.dry_run:
        print("  --dry-run: nothing written")
        return 0
    if state.state == UNKNOWN and state.satisfied is None:
        # THE NUMERIC CHECK ABOVE IS WEAKER THAN THE EVALUATOR, and only the evaluator's own
        # verdict settles whether this criterion can be read. A node recorded with a
        # non-`present` status, a non-finite reading, or a unit that disagrees with the
        # threshold's all resolve to a number and all come back UNKNOWN — armed, they are
        # indistinguishable on the card from a criterion that is working and quiet, which is the
        # exact collapse this command exists to refuse. `satisfied is None` IS that test: the
        # comparison was never made. A sustain criterion whose comparison DID hold but which has
        # no history yet carries `satisfied=True` and is armed normally — a brand-new criterion
        # has no history by definition, and refusing it would refuse the whole sustain feature.
        print(f"REFUSED (nothing armed): the evaluator cannot read this criterion today, so armed "
              f"it would read UNKNOWN on every run — {state.reason}")
        return 1

    out = rec.model_copy(update={"verdict": rec.verdict.model_copy(
        update={"measured_triggers": [*existing, trig]})})
    # `write_record` takes the REPO root and appends `scenarios/` itself. Passing the scenarios
    # directory wrote `scenarios/scenarios/SMPL.json` while this line reported the path it had
    # MEANT to write — a success message for a file that was never touched.
    written = sc.write_record(out, root=root)

    # READ BACK WHAT LANDED, and refuse to claim otherwise: a command that printed "written"
    # regardless would tell the analyst their falsifier is armed when the file does not carry it,
    # and that is the failure the first run of this command actually produced (it reported a path
    # it had only MEANT to write). The check costs one read.
    #
    # IT DOES NOT NAME A CAUSE, because it cannot know one. An earlier draft blamed
    # version-scoping — "this record's schema has no `measured_triggers` field" — which is not
    # what `_version_scoped` does: it drops the key only when the list is EMPTY (absent-vs-empty),
    # never by schema version, so every committed record (all schema 1.3) keeps an appended
    # criterion. Naming a cause the check cannot establish sends the analyst to
    # `scenario-supersede` for a condition that does not exist.
    landed = ((json.loads(written.read_text()).get("verdict") or {})
              .get("measured_triggers") or [])
    if len(landed) != len(existing) + 1:
        print(f"REFUSED (nothing armed): {written} was written but carries {len(landed)} measured "
              f"criteria where {len(existing) + 1} were expected — the criterion did not land, so "
              f"do not treat this falsifier as armed. Inspect the record before retrying.")
        return 1
    print(f"  written    {written}  ({len(landed)} measured criteria; the prose is untouched)")
    return 0


def _cmd_scenario_supersede(args: argparse.Namespace) -> int:
    """ARCHIVE-AND-REISSUE — the ONLY path that supersedes a record (scenario-refresh precedent).

    The outgoing record is archived intact and both records point at each other; the incoming one
    is supplied by the analyst as a full record payload. Nothing is deleted and no sealed word is
    edited — a reader can always walk live → archived → live again."""
    import json as _json

    import vinci.scenarios as sc
    import vinci.seal as seal
    from vinci import monitor as mon

    root = Path.cwd()
    try:
        outgoing = sc.read_record(args.ticker.upper(), root=root)
    except FileNotFoundError:
        print(f"no live record for {args.ticker.upper()}")
        return 1
    try:
        incoming = sc.ScenarioRecord.model_validate_json(Path(args.payload).read_text())
    except (OSError, ValueError) as exc:
        print(f"payload unreadable / invalid against the schema: {exc}")
        return 2

    # THE ANCHOR/DERIVATION GUARDS, WHICH THIS PATH DID NOT RUN (2026-08-05). Until now supersede
    # did schema validation and NOTHING else — no anchors, no deviation reasons, no tier check —
    # while every one of those guards sat on `scenario-create`, which by definition has no live
    # record to fix. So the §D defect (a bare averaged number whose derivation is unstated) was
    # reintroducible through the one path an analyst actually uses on a live name.
    #
    # ANCHORS MAY LEGITIMATELY BE UNAVAILABLE, and that is NOT forced into a refusal: a record can
    # outlive its dossier (WERN is the live case — a committed record with no `data/dossiers/WERN`),
    # and a closed record amending history is exactly the shape that has no current dossier to
    # anchor against. In that case the anchored checks CANNOT run, so they are skipped and SAID SO
    # LOUDLY rather than silently passing — the derivation requirement still binds, because it is
    # a property of the record and needs no dossier at all.
    from vinci.dossier.propose import (
        ProposalRefusedError,
        check_tier_agreement,
        propose_anchors,
        record_legs_for_validation,
        validate_legs,
    )

    t_up = incoming.ticker.upper()
    anchors: list[Any] = []
    doc: dict[str, Any] | None = None
    try:
        doc = _dossier_doc(t_up)
        check_tier_agreement(doc, incoming.recipe_id)
        anchors = propose_anchors(doc)
    except FileNotFoundError:
        print(f"  ⚠ no committed dossier for {t_up} — anchor + deviation checks NOT RUN. The "
              "derivation requirement still applies; the numbers themselves are unchecked against "
              "any anchor.")
    except ProposalRefusedError as exc:
        print(f"REFUSED: {exc}")
        return 2
    _axes = sc.axes_for(incoming.recipe_id, incoming.multiple_basis)
    problems = validate_legs(record_legs_for_validation(incoming, axes=_axes), anchors,
                             axes=_axes, basis=incoming.multiple_basis)
    problems += sc.horizon_problems(incoming)     # no new record lands without a realisation date
    # ...and none lands struck at a year the decomposition does not use, unexplained. `doc` is
    # None when the name has no committed dossier (WERN), and `leg_fy_problems` treats a missing
    # anchor as nothing-to-check rather than a refusal — same non-forcing rule as the anchors above.
    _anchor_fy = ((doc or {}).get("mechanical") or {}).get("ev_gap") or {}
    problems += sc.leg_fy_problems(
        (incoming.scenarios or {}).get("base"), _anchor_fy.get("anchor_fy"), require_stated=True)
    # ...and the entry window must be stated and period-equivalent to the leg it is compared with.
    problems += sc.basis_problems(incoming, require_stated=True)
    if problems:
        print(f"=== scenario-supersede {t_up}: REFUSED ({len(problems)}) ===")
        for p in problems:
            print(f"  - {p}")
        return 2
    # THE LIMIT NOTES PRINT AND DO NOT REFUSE. `limit > ceiling` says the legs moved under a
    # commitment that did not, which is the analyst's judgment to resolve — so it is surfaced
    # beside the write rather than blocking it. Kept OUT of `problems` on purpose.
    for note in sc.limit_notes(incoming):
        print(f"  ⚠ limit: {note}")
    # THE SPOT NOTES PRINT AND DO NOT REFUSE either, and that is measured rather than cautious:
    # run from this worktree a refusal would block BRBR and EPAM — both correct, both struck at a
    # date past this store's frontier. `vinci audit spot` sweeps the committed corpus; this catches
    # a record at the moment it is written, while the analyst is still holding it.
    try:
        _cfg = get_config()
        with Store(_cfg.db_path) as _store:
            _iid = EntityResolver.from_config(_cfg).resolve_ticker(
                incoming.ticker).internal_id
            _spot_notes = sc.spot_notes(
                incoming, store=f"`{_cfg.db_path.absolute().parent.parent.name}`",
                name_frontier=_store.price_frontier_for(_iid),
                bar_close=(_store.close_on(_iid, incoming.spot_as_of)
                           if incoming.spot_as_of else None))
    except Exception as exc:  # noqa: BLE001 — deliberate, and the asymmetry is the point
        # A NOTE-ONLY CHECK MUST NOT BLOCK A WRITE — the exact OPPOSITE of the rule for
        # `_committed_limit`, whose bare `except` silently disabled a REFUSAL and let a BUY past a
        # stated limit. Swallowing here costs a note; swallowing there cost a gate. The failure is
        # printed rather than hidden, so a check that stopped working still says so.
        _spot_notes = [f"could not be checked — {type(exc).__name__}: {exc}"]
    for note in _spot_notes:
        print(f"  ⚠ spot: {note}")

    # A LIVE position is never superseded. Derived from the LEDGER, not asserted by the caller:
    # a confirmed verdict whose decision row carries no close row is an open position.
    led = root / "data" / "snapshots" / "decision_ledger.jsonl"
    rows = [_json.loads(x) for x in led.read_text().splitlines() if x.strip()] if led.is_file() \
        else []
    closed = {str(mon.entry_of(r).get("closes_entry_id")) for r in mon.close_rows(rows)}
    mine = [mon.entry_of(r) for r in mon.decision_rows(rows)
            if mon.entry_of(r).get("ticker", "").upper() == outgoing.ticker.upper()]
    open_position = bool(mine) and any(e["entry_id"] not in closed for e in mine)

    # THE INCOMING `result` IS RECOMPUTED FROM ITS OWN LEGS, AND A DISAGREEMENT IS REFUSED.
    # `scenario-create` runs `validate_legs -> run_recipe -> write_record`; supersede ran the
    # validator and then wrote whatever `result` the payload happened to carry. A hand-typed
    # ratio that disagrees with the legs above it is the machine CONCLUDING from a number nobody
    # derived — the one thing this repo's records exist not to do — and the spread is accumulated
    # from exactly these figures.
    #
    # REFUSED, NOT SILENTLY OVERWRITTEN: a supplied number that disagrees is either a stale paste
    # or a real disagreement about the arithmetic, and both deserve the analyst's eyes rather than
    # a quiet correction they never see. Measured before shipping: all nine committed records
    # recompute to their stored ratio exactly, so this refuses nothing that exists today.
    try:
        _recomputed = sc.run_recipe(incoming.model_copy(deep=True))
    except (ValueError, KeyError, TypeError) as exc:
        print(f"REFUSED: the incoming payload's legs do not compute — {exc}")
        return 1
    #
    # A PAYLOAD THAT STATES NOTHING IS DERIVED, NOT REFUSED. `result` defaults to a virgin
    # `Result()`, so a payload that omits it disagrees with the legs on every compared field
    # (`stated None, legs give 1.6919…`) — which made the refusal's own advice impossible to
    # follow and left archive-and-reissue with no working payload shape: a stated result freezes
    # the tiered ladder (`_with_irr_gate` only stamps a record that was never computed), and an
    # unstated one was refused. Nothing is silently corrected here — there is no stated number to
    # correct — and the derivation is PRINTED so it is never a quiet substitution.
    if _result_is_stated(incoming.result):
        _mismatch = _result_mismatch(incoming.result, _recomputed.result)
        if _mismatch:
            print(f"REFUSED: {incoming.ticker}: the payload's stated result disagrees with its "
                  f"own legs — {_mismatch}. Fix the legs or drop the stated result and let the "
                  f"recipe compute it; a record whose headline number is not derivable from the "
                  f"rows above it cannot be re-checked.")
            return 1
    else:
        print("  ⚠ payload states no result — DERIVED from its own legs "
              f"(ratio {_recomputed.result.ratio and round(_recomputed.result.ratio, 4)}, "
              f"gate {_recomputed.result.gate}, regime {_recomputed.result.gate_regime})")
    incoming = _recomputed

    try:
        archived, live = sc.supersede_record(
            outgoing, incoming,
            closed_entry_ids={e["entry_id"] for e in mine if e["entry_id"] in closed},
            live_confirmed_open=(outgoing.verdict.status == "confirmed" and open_position))
    except sc.SupersedeRefusedError as exc:
        print(f"REFUSED: {exc}")
        return 1

    # SEAL, before anything is written. The archived record keeps its OWN entry under the archive
    # key; the live ticker key is RE-SEALED at the new rationale. Re-sealing is exactly the
    # "deliberate, reviewable act" vinci/seal.py names — it happens here, once, or not at all.
    man = seal.load_manifest(root)
    man[sc.archive_key(archived)] = man.get(
        outgoing.ticker.upper(), seal.seal_entry(archived.verdict.rationale or ""))
    if seal.is_sealed(live.verdict.status):
        man[live.ticker.upper()] = seal.seal_entry(live.verdict.rationale or "")
    probe = {sc.archive_key(archived): _json.loads(archived.model_dump_json()),
             live.ticker.upper(): _json.loads(live.model_dump_json())}
    if viol := seal.check_all(probe, man):
        print("REFUSED: the reissued pair does not pass the seal:")
        for v in viol:
            print(f"  {v}")
        return 1

    print(f"=== scenario-supersede {outgoing.ticker} ===")
    print(f"  archived : {sc.archive_key(archived)}  (superseded_by {archived.superseded_by})")
    print(f"  live     : {live.ticker} underwritten {live.underwrite_date} "
          f"(supersedes {live.supersedes})")
    print(f"  ratio    : {outgoing.result.ratio and round(outgoing.result.ratio, 4)} → "
          f"{live.result.ratio and round(live.result.ratio, 4)}")
    if args.dry_run:
        print("  --dry-run: nothing written")
        return 0
    # PRE-CHECK BEFORE EITHER WRITE. The archive lands first, so a refusal on the live
    # record used to leave an orphan archive — a superseded record with no successor and an
    # un-updated seal manifest. Validating here makes the pair atomic in the only way that
    # matters: nothing is written unless both can be.
    try:
        sc.validate_for_write(live)
    except ValueError as exc:
        print(f"=== scenario-supersede {t_up}: REFUSED ===\n  {exc}")
        return 2
    ap = sc.write_archived(archived, root=root)
    lp = sc.write_record(live, root=root)
    (root / "scenarios" / seal.SEAL_FILE).write_text(_json.dumps(man, indent=2, sort_keys=True)
                                                     + "\n")
    print(f"  written  : {ap}\n             {lp}\n             seal manifest updated")
    return 0


def _cmd_monitor(args: argparse.Namespace) -> int:
    """MANUAL cadence (no scheduler): mark the committed ledger to the latest close against each
    leg's ASSIGNED benchmark, print the book + the BUY−AVOID diagnostic + the freshness panel,
    and write a dated snapshot as the auditable book history.

    Reads the COMMITTED `decision_ledger.jsonl` — the durable record — not the working DB (which
    a fresh clone has never populated). Benchmarks come from the committed assignment artifact,
    which SUPERSEDES the ledger row's own field; a leg with no assignment fails LOUD rather than
    being measured against a yardstick nobody chose."""
    from vinci import monitor as mon

    cfg = get_config()
    root = Path.cwd()
    ref = date.fromisoformat(args.ref) if args.ref else date.today()
    ledger_path = cfg.data_dir / "snapshots" / "decision_ledger.jsonl"
    if not ledger_path.exists():
        print(f"no committed ledger at {ledger_path}")
        return 1
    ledger_all = [json.loads(ln) for ln in ledger_path.read_text().splitlines() if ln.strip()]
    if not ledger_all:
        print("decision ledger is empty — nothing to monitor")
        return 0
    # POSITIONS ONLY. A close row carries the original verdict for provenance, so feeding the raw
    # ledger to the spread would count a closed name a SECOND time on its own original side.
    # `pair_closes` refuses loud on an unpairable or duplicated close, so a malformed realized book
    # stops the run rather than rendering wrong.
    rows_raw = mon.decision_rows(ledger_all)
    assignments = mon.read_assignments(root)
    missing = sorted({r["ticker"] for r in rows_raw} - set(assignments))
    if missing:
        print(f"no benchmark assignment for {missing} — refusing to measure against an "
              f"unassigned yardstick (write data/monitor/benchmark_assignments.json first)")
        return 1

    # SIC per ticker → the sector is RE-RESOLVED here, at the display/report layer. The frozen
    # ledger row keeps whatever it logged (IT logged "Other" before the 87xx family fix); the
    # correction is forward-only — an append-only row is never rewritten to look better.
    sic_by_ticker: dict[str, str | None] = {}
    cik_by_ticker: dict[str, str | None] = {}
    sec_path = cfg.data_dir / "snapshots" / "securities.jsonl"
    if sec_path.exists():
        for ln in sec_path.read_text().splitlines():
            if ln.strip():
                rec = json.loads(ln)
                sic_by_ticker[rec.get("ticker")] = rec.get("sic")
                cik_by_ticker[rec.get("ticker")] = rec.get("cik")

    eod = PolygonEodClient.from_config(cfg)
    cache: dict[date, dict[str, Any]] = {}

    def bars_on_or_before(day: date) -> tuple[date, dict[str, Any]]:
        # only an EMPTY day steps back; a failed fetch stops the run (`session_on_or_before`)
        return mon.session_on_or_before(eod.grouped_daily, day, cache)

    now_date, now_bars = bars_on_or_before(ref)
    # THE BOOK'S CLOSURE STATE IS READ AS OF THE SNAPSHOT DATE, not as of "whatever the ledger holds
    # now" (review P1 on #418). Anchored on `now_date` rather than `ref` because `now_date` is what
    # the snapshot claims to BE — a close falling between the last trading bar and a non-trading
    # `ref` has not happened yet in the book this file describes. Without this, `monitor --ref
    # <past date>` marked positions closed and printed realized P&L for exits that had not occurred,
    # so a historical snapshot was not reproducible — while the price path beside it was carefully
    # refusing future bars.
    realized = mon.pair_closes(ledger_all, as_of=now_date)
    closed_entry_ids = mon.closed_decision_ids(ledger_all, as_of=now_date)
    notes: list[str] = []
    # AND THE DECISIONS THEMSELVES ARE POINT-IN-TIME. The review flagged the CLOSE half; the same
    # defect sat on the entry half and was louder — re-running `--ref 2026-07-20` marked SMPL's
    # 2026-08-04 re-entry into that day's book with `days_elapsed: -15`, a position that did not
    # exist yet. Both halves now read the ledger as of the snapshot date.
    asof_rows = mon.decisions_as_of(ledger_all, as_of=now_date)
    if len(asof_rows) != len(rows_raw):
        notes.append(
            f"{len(rows_raw) - len(asof_rows)} decision(s) entered after {now_date} are excluded "
            f"— this book is the state as of that date, not today's ledger re-marked backwards")
    rows: list[mon.PositionRow] = []
    for r in asof_rows:
        payload = json.loads(r["payload"])
        # Re-validated ONCE rather than dict-read: the absent-means-screen/overshoot fallbacks live
        # on the model's helpers, and reading the raw dict here would be a second definition of
        # them that could drift from the scoring path's.
        led_entry = LedgerEntry.model_validate(payload)
        tkr, asg = r["ticker"], assignments[r["ticker"]]
        entry_day, entry_bars = bars_on_or_before(date.fromisoformat(r["entry_price_as_of"]))
        for need, where in ((tkr, "position"), (asg.benchmark, "benchmark")):
            if need not in entry_bars or need not in now_bars:
                raise RuntimeError(f"{tkr}: no {where} bar for {need} "
                                   f"({entry_day} / {now_date}) — refusing to guess a price")
        live_sic = sic_by_ticker.get(tkr)
        live_sector = mon.sector_for_display(live_sic)
        if (note := mon.sector_note(
                ticker=tkr, sic=live_sic, frozen_sector=payload.get("sector"))):
            notes.append(note)
        rows.append(mon.position_row(
            ticker=tkr, verdict=r["verdict"], sector=live_sector,
            origin=origin_of(led_entry), sleeve=sleeve_of(led_entry),
            entry_price=r["entry_price"], entry_date=date.fromisoformat(r["entry_price_as_of"]),
            current_price=now_bars[tkr].close, current_date=now_date,
            benchmark=asg.benchmark, benchmark_entry=entry_bars[asg.benchmark].close,
            benchmark_now=now_bars[asg.benchmark].close, horizon_days=r["horizon_days"],
            # Is the POSITION still held? Read from the close rows, which name the decision they
            # close — never inferred from the ticker, since a name can be re-entered (SMPL is, and
            # its two decisions are on opposite sides of this flag).
            closed=r["entry_id"] in closed_entry_ids))
        if payload.get("benchmark") and payload["benchmark"] != asg.benchmark:
            notes.append(f"{tkr}: benchmark {asg.benchmark} (cap band) SUPERSEDES the ledger "
                         f"row's {payload['benchmark']} — the row itself is never mutated")

    fresh: list[mon.FreshnessRow] = []
    # PRIOR MONITOR DAYS ARE THE OBSERVATION HISTORY (step 2). They are dated, committed and
    # append-only, and each already records what every measured criterion read — so a separate
    # store would be a second copy of a fact this repo keeps, free to drift from it.
    #
    # STRICTLY EARLIER THAN THE DAY BEING BUILT, newest first. A re-run of TODAY must not read its
    # own previous output as a prior observation: that would let running the monitor twice extend a
    # streak, which is the exact defect the source_ref de-duplication exists to prevent, reached by
    # a different door.
    _mon_dir = root / "data" / "monitor"
    prior_days: list[dict[str, Any]] = []
    if _mon_dir.is_dir():
        for _p in sorted(_mon_dir.glob("*.json"), reverse=True):
            # A DAY IS A DATED FILENAME — the same test `mon.write_snapshot` already applies to
            # this directory (`_SNAPSHOT_DAY`), rather than a second ad-hoc rule naming the one
            # non-day file we happen to know about. `benchmark_assignments.json` is excluded by
            # not being a date, and so is the next artifact that lands beside it.
            if not mon._SNAPSHOT_DAY.fullmatch(_p.stem) or _p.stem >= ref.isoformat():
                continue
            prior_days.append(json.loads(_p.read_text()))
    edgar = EdgarClient.from_config(cfg)
    for name in sorted({r["ticker"] for r in rows_raw} | _watch_tickers(root)):
        rec_path = root / "scenarios" / f"{name}.json"
        if not rec_path.exists():
            continue
        record = json.loads(rec_path.read_text())
        cik = cik_by_ticker.get(name)
        filings: list[tuple[str, date, str]] = []
        if cik:
            for f in edgar.recent_filings(cik, forms=("8-K", "10-Q", "10-K"),
                                          since=ref - timedelta(days=760)):
                filings.append((f.form, f.filing_date, f.accession))
        v = record.get("verdict") or {}
        note = (f"WATCH (not a position) — avoid-priced: {v.get('avoid_priced_note')}"
                if v.get("avoid_priced") else None)
        logged = next((r["verdict"] for r in rows_raw if r["ticker"] == name), None)
        status = str(v.get("status") or "—")
        # THE DOSSIER IS RESOLVED HERE, not inside the monitor (ruling 3). `freshness_row` takes
        # the mechanical layer as a parameter for the same reason the scoring package takes its
        # baskets: that module resolves neither config nor paths, so a reader that had to FIND a
        # dossier would put file layout inside a pure function. Absent — a name with no committed
        # dossier — the measured criteria report UNKNOWN with that as their stated cause, which is
        # the honest reading and not a quiet page.
        dpath = root / "data" / "dossiers" / name / "dossier.json"
        mech = (json.loads(dpath.read_text()).get("mechanical")
                if dpath.is_file() else None)
        fresh.append(mon.freshness_row(
            ticker=name, verdict=logged or _STATUS_LABEL.get(status, status),
            record=record, filings=filings, today=ref, watch_note=note, mechanical=mech,
            prior_days=prior_days))

    # DUAL MEASUREMENT (ratified §7, 2026-07-22). The CALL is scored at its horizon regardless of
    # whether the position was exited — an exit is a capital decision, not a retraction, and
    # dropping exited names from calibration would let the discriminator's hit-rate be curated by
    # sell timing. REALIZED P&L (entry→exit) is a SEPARATE, labelled view. Both are shown; neither
    # is allowed to stand in for the other.
    # TYPED FIRST, PROSE RENDERED FROM IT. The note text used to be composed here from raw dicts,
    # which made the free-text line the ONLY carrier of the realized book. Now the rows are the
    # carrier and `RealizedRow.note()` renders them, so display cannot drift from the data.
    realized_rows = [mon.RealizedRow.model_validate(r) for r in realized]
    notes.extend(r.note() for r in realized_rows)
    # THEME FALSIFIER SWEEP (brief Item 2): every declared thesis card's dated triggers, flagged
    # when the deadline has passed — beside the scenario dated_triggers rows above, same doctrine
    # (the machine flags the closed window; whether it FIRED is the human's read).
    from vinci.themes.thesis import load_all_theses
    cards, card_problems = load_all_theses(data_dir=cfg.data_dir)
    # today=now_date, NOT ref (review 2026-08-31): the snapshot is stamped as_of=now_date (last
    # trading day), and every other as-of computation in this function anchors there. Sweeping on
    # the calendar ref let a weekend run commit deadline_passed=true into a day file dated BEFORE
    # the deadline — an immutable artifact asserting a window closed after its own as_of.
    theme_rows = mon.theme_falsifier_rows(cards, today=now_date)
    # AN UNREADABLE CARD IS A WATCH THAT IS NOT HAPPENING, so it is surfaced in the run's own
    # notes rather than raising: one hand-edited theme file must not take the book's marks and
    # spread down with it, and it must not pass silently either.
    notes.extend(f"THEME CARD {p}" for p in card_problems)
    # THE PANEL GRID (phase 6) — the consumer phases 2-4 were built for. Every panel decision and
    # its STRUCTURED values land in the artifact; the frontend mirrors the file and renders it.
    #
    # A FAILURE HERE MUST NOT TAKE THE BOOK DOWN. The marks and the spread are the artifact's
    # reason to exist; the grid is an addition to it. A hand-edited `followed.json` that names an
    # unregistered panel raises by design (loud at read, per phase 4), and that must surface as a
    # note rather than as a monitor run that writes nothing at all — the same doctrine as the theme
    # cards above. It is NOT silent: the run prints it and the snapshot carries it.
    panel_rows: list[Any] = []
    try:
        import json as _pj

        from vinci.panels_emit import emit_panels

        def _dossier_for(t: str) -> dict[str, Any] | None:
            f = cfg.data_dir / "dossiers" / t / "dossier.json"
            return _pj.loads(f.read_text()) if f.is_file() else None

        def _record_for(t: str) -> dict[str, Any] | None:
            f = root / "scenarios" / f"{t}.json"
            return _pj.loads(f.read_text()) if f.is_file() else None

        # THEME PANELS attach to the DRIVER, not the ticker, so they are emitted from the driver
        # set and the sweep rows computed just above — never re-derived from the cards, which would
        # be the rival computation `ThemeFalsifierRow` explicitly reserves against.
        from vinci.panels_emit import theme_panel_rows

        tracked = sorted({p.stem for p in (cfg.data_dir / "themes" / "baskets").glob("*.json")}
                         | {p.stem for p in (cfg.data_dir / "themes" / "economics").glob("*.json")})
        # THE ASSIGNMENT IS ATOMIC, and that is the whole point of building into a local first.
        # Seeding `panel_rows` with the theme tier and then `+=`-ing the rest meant a failure in
        # `emit_panels` — the documented unregistered-panel case — left a THEME-ONLY block on the
        # snapshot. The renderer shows its "grid unavailable" notice only when the block is EMPTY,
        # so a broken run would have rendered as a complete six-tile grid with the failure note
        # buried in `notes`: a partial page that looks whole, which is the absent-vs-broken class
        # wearing the one disguise this whole build exists to strip off.
        _theme = theme_panel_rows(
            driver_keys=tracked, declared_cards={c.driver_key for c in cards},
            theme_falsifiers=[r.model_dump(mode="json") for r in theme_rows], today=now_date)
        _named = emit_panels(
            rows=[r.model_dump(mode="json") for r in rows],
            freshness=[f.model_dump(mode="json") for f in fresh],
            dossier_for=_dossier_for, record_for=_record_for, root=root,
        )
        panel_rows = [*_theme, *_named]
    except Exception as exc:  # noqa: BLE001 — surfaced as a note; see the comment above
        notes.append(f"PANEL GRID UNAVAILABLE ({type(exc).__name__}): {exc}")
    snap = mon.MonitorSnapshot(as_of=now_date, rows=rows, spread=mon.compute_spread(rows),
                               freshness=fresh, notes=notes, realized=realized_rows,
                               theme_falsifiers=theme_rows, panels=panel_rows)
    print(mon.render_table(snap))
    # The CLI never rewrites a SUPERSEDED day: re-running the front of the book is routine, while
    # replacing a day that later snapshots sit on top of would overwrite what the book recorded
    # then. `write_snapshot` decides which case this is.
    path = mon.write_snapshot(snap, root=root)
    print(f"\nsnapshot written: {path}")
    return 0


# --- calls tape ---------------------------------------------------------------
def _cmd_calls_accounts(args: argparse.Namespace) -> int:
    """Rebuild data/calls/accounts.json from each account's own meta.json (derived, idempotent)."""
    from vinci.calls.accounts import rebuild_accounts
    idx = rebuild_accounts(default=getattr(args, "default", None))
    print(f"default: {idx.default}")
    for a in idx.accounts:
        print(f"  {a.display:<22} {a.first}..{a.last}  posts={a.n_posts:>6}  "
              f"tracked={a.n_tracked:>4}  hand={a.n_hand_labels:>4}  "
              f"machine={a.n_machine_labels:>6}")
    return 0


def _cmd_calls_bars(args: argparse.Namespace) -> int:
    """Fetch each tracked ticker's Polygon window into data/calls/<handle>/bars/.

    SERVER-SIDE ONLY. The key is read from the environment and never leaves this process; the
    browser reads the committed files, never Polygon.
    """
    from vinci.calls.accounts import load_accounts
    from vinci.calls.bars import fetch_account_bars
    handle = load_accounts().get(args.account).handle
    only = set(args.only.split(",")) if args.only else None

    def _prog(i: int, tot: int, sym: str, n: int) -> None:
        print(f"  {i:>4}/{tot}  {sym:<8} {n:>5} bars", flush=True)

    counts = fetch_account_bars(handle, only=only, on_progress=_prog)
    empty = sorted(t for t, c in counts.items() if c == 0)
    print(f"{handle}: {len(counts)} tickers, {sum(counts.values()):,} bars")
    if empty:
        print(f"  no bars (delisted / renamed / index): {', '.join(empty)}")
    return 0


def _cmd_calls_score(args: argparse.Namespace) -> int:
    """Score an account's directional calls against the committed bars.

    The printed counts are an OPERATOR RUN SUMMARY, not a published aggregate — see
    vinci/calls/run.py on why no hit-rate reaches the dashboard until the hand set is large.
    """
    import collections

    from vinci.calls.accounts import load_accounts
    from vinci.calls.run import score_account, write_results
    handle = load_accounts().get(args.account).handle
    res = score_account(handle, only_hand=args.hand_only)
    out = write_results(handle, res, hand_only=args.hand_only)
    by = collections.Counter(r.status for r in res)
    print(f"{handle}: scored {len(res)} directional calls -> {out}")
    for k in ("CLOSED", "OPEN", "NO_PRICE_DATA", "NO_ENTRY_BAR", "BAD_HORIZON"):
        if by.get(k):
            print(f"  {k:<14} {by[k]:>5}")
    tgt = collections.Counter(r.target_status for r in res if r.target_status)
    print("  target: " + "  ".join(f"{k}={v}" for k, v in sorted(tgt.items())))
    return 0


def _cmd_calls_import(args: argparse.Namespace) -> int:
    """Merge an exported labelling session back into the account's corpus.

    The dashboard cannot write — it is a static mirror — so landing a session is this deliberate,
    reviewable step, where the change appears in `git diff` like any other. Does NOT re-score;
    run `vinci calls score` after.
    """
    from vinci.calls.accounts import load_accounts
    from vinci.calls.ingest import import_labels
    handle = load_accounts().get(args.account).handle
    r = import_labels(handle, Path(args.path), dry_run=args.dry_run)
    verb = "would merge" if args.dry_run else "merged"
    print(f"{handle}: {verb} {r['rows']} row(s) from {args.path}")
    print(f"  new                {r['new']:>5}")
    print(f"  updated (hand)     {r['updated']:>5}")
    print(f"  replaced a guess   {r['replaced_machine']:>5}")
    if not args.dry_run:
        print(f"  hand labels now    {r['hand_total']:>5}")
        print(f"  calendar days recounted {r['days_recounted']:>5}")
        print("  scores are NOT updated — run `vinci calls score` to re-score,")
        print("  and `vinci calls accounts` to refresh the index the dashboard's count reads.")
    return 0


def _cmd_audit_spot(args: argparse.Namespace) -> int:
    """SPOT audit — every committed record's spot against the bar it claims to be. READ-ONLY.

    WHY A FLEET SWEEP AND NOT ONLY A WRITE-PATH CHECK. A gate on `scenario-create` /
    `scenario-supersede` never looks at a record again after it lands, and all eight committed
    records predate the field — so a write-path seat alone would leave the corpus permanently
    unexamined. This is the seat that can actually run against it (CORPUS BEFORE SYNTHETIC).

    IT PRINTS AND NEVER REFUSES, and the corpus is why. Run from this worktree, a
    refuse-on-mismatch rule would block BRBR and EPAM — both CORRECT, both struck at 2026-08-07,
    both resolving only in the `-sl` store while this one reaches 2026-08-04. Every spot is
    auditable somewhere and none is auditable everywhere, so the exit code stays 0 on a note.
    """
    import vinci.scenarios as sc
    from vinci.store.store import Store

    root = Path.cwd()
    cfg = get_config()
    resolver = EntityResolver.from_config(cfg)
    recs = sorted(sc.records_dir(root).glob("*.json"))
    recs = [p for p in recs if not p.stem.startswith("_")]
    if not recs:
        print("no committed scenario records — nothing to audit")
        return 0

    with Store(cfg.db_path) as store:
        # ABSOLUTE BEFORE NAMED: `cfg.db_path` is relative ("data/vinci.db"), so naming the
        # worktree off it directly yields an empty string. `.absolute()` keeps the symlink
        # (which worktree DECLARED it); `.resolve()` follows it (whose bytes these are).
        declared, real = cfg.db_path.absolute(), cfg.db_path.resolve()
        label = f"`{declared.parent.parent.name}`"
        via = ("" if declared == real
               else f" → `{real.parent.parent.name}` (symlinked)")
        print(f"=== spot audit: {len(recs)} record(s) vs {label}{via}, "
              f"frontier {store.price_frontier()} ===")
        clean = notes_total = 0
        for p in recs:
            rec = sc.ScenarioRecord.model_validate_json(p.read_text())
            iid = resolver.resolve_ticker(rec.ticker).internal_id
            bar = (store.close_on(iid, rec.spot_as_of) if rec.spot_as_of else None)
            notes = sc.spot_notes(rec, bar_close=bar, store=label,
                                  name_frontier=store.price_frontier_for(iid))
            if not notes:
                clean += 1
                print(f"  {rec.ticker:6} ${rec.spot:<10,.4g} {rec.spot_as_of}  ✓ matches this "
                      f"store's bar exactly")
                continue
            notes_total += len(notes)
            print(f"  {rec.ticker:6} ${rec.spot:<10,.4g} {rec.spot_as_of or 'unstated':10}")
            for n in notes:
                print(f"         ⚠ {n}")
    print(f"\n{clean} clean · {notes_total} note(s) — notes never change the exit code")
    return 0


def _cmd_audit_r1(args: argparse.Namespace) -> int:
    """R1 applicability audit — READ-ONLY over committed artifacts.

    Reads dossiers + scenario records and prints the seven-check matrix. It writes nothing unless
    ``--out`` is given, and it never changes an exit code on a flag: flags PRINT (the linter
    model). A check that refused to proceed would be routed around exactly when it mattered."""
    from datetime import date as _date

    from vinci import audit_r1 as ar

    root = Path.cwd()
    audits = ar.load_and_audit(root)
    if not audits:
        print("no committed dossier carries an anchor — nothing to audit")
        return 0
    report = ar.render(audits, as_of=args.as_of or _date.today().isoformat())
    print(report)
    if getattr(args, "out", None):
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report + "\n")
        print(f"\nreport written: {args.out}")
    loud = sum(1 for a in audits for f in a.flags if f.severity == "flag")
    print(f"\n{len(audits)} name(s) audited · {loud} flag(s) · "
          f"{sum(1 for a in audits if a.disposition == 'clean')} clean")
    return 0


# Scenario statuses that are NOT ledger positions but must still be watched for staleness:
#   watch            — a standing re-underwrite trigger (WERN)
#   pending_analyst  — the underwrite is RUN and the verdict is outstanding (EPAM). A record
#                      awaiting a human decision is exactly the one that must not go stale
#                      unnoticed: the next print can move the decision before it is ever made.
_FRESHNESS_STATUSES = ("watch", "pending_analyst")
_STATUS_LABEL = {"pending_analyst": "verdict pending"}


def _watch_tickers(root: Path) -> set[str]:
    """Scenario records that are NOT ledger positions but must appear in the freshness panel —
    standing-trigger `watch` names and `pending_analyst` records whose verdict is still owed."""
    out: set[str] = set()
    d = root / "scenarios"
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        rec = json.loads(p.read_text())
        if (rec.get("verdict") or {}).get("status") in _FRESHNESS_STATUSES:
            out.add(str(rec["ticker"]))
    return out


def _cmd_ledger(args: argparse.Namespace) -> int:
    """List every recorded ledger row — the decisions, and the closes that followed them.

    CLOSES ARE SHOWN AND MARKED — never hidden, never bare. This is the append-only record, so
    dropping close rows would misrepresent it; but a close carries the ORIGINAL verdict for
    provenance, so printing one unmarked under a VERDICT header shows the same name twice, both
    reading BUY, with nothing to tell them apart. That is how a reader miscounts the book by hand,
    and it is the display half of the double-count `score_ledger` was just fixed for.

    Matches the web decision log's rule (2026-07-27): the decision keeps its verdict word, and the
    close says it is a close beside it.
    """
    cfg = get_config()
    with Store(cfg.db_path) as store:
        entries = list(store.iter_ledger())
    if not entries:
        print("decision ledger is empty")
        return 0
    print(f"{'TICKER':<7}{'VERDICT':<16}{'ENTRY':>9}{'AS_OF':>13}{'HORIZON':>9}  DECIDED")
    for e in entries:
        close_mark = (
            f"  ← CLOSE @ {e.exit_price:.2f} on {e.exit_price_as_of}"
            if e.event == EVENT_CLOSE and e.exit_price is not None
            else ""
        )
        print(
            f"{e.ticker:<7}{e.verdict.value:<16}{e.entry_price:>9.2f}"
            f"{str(e.entry_price_as_of):>13}{e.horizon_days:>8}d  {e.decided_at:%Y-%m-%d}"
            f"{close_mark}"
        )
    n_close = sum(1 for e in entries if e.event == EVENT_CLOSE)
    if n_close:
        print(f"\n{len(entries) - n_close} decision(s) · {n_close} close(s) — a close is not a "
              f"second verdict; the spread counts decisions only.")
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
            # THE PASSIVE COMPARATOR each sleeve's kill test names. Wired at BOTH default paths
            # (here and `run_monthly`) deliberately: #378's lesson was that a per-book number
            # reachable from only one of them is invisible to every reader of the other.
            baskets=resolve_baskets(
                cfg.data_dir / "followed.json", store.iter_securities()),
        )
    print(report.to_markdown())
    if args.json:
        cfg.ensure_dirs()
        path = cfg.snapshots_dir / "scoring_report.json"
        path.write_text(json.dumps(report.to_dict(), indent=2, default=str))
        print(f"\nwrote {path}")
    return 0


def _cmd_run_weekly(args: argparse.Namespace) -> int:
    """Scheduled weekly job: rebuild the universe, screen it, rank it, export the lot.

    No flags — every stage is unconditional. A cron with opt-in pieces is how the ranker and the
    structural scan both came to be silently missing from the weekly run (STATE.md §5).

    THE DATE COMES FROM THE DATA, NOT THE CLOCK. This defaulted to `date.today()`, which stamped the
    universe as-of, the `reference_date` and every relative-return window with the moment the JOB
    RAN rather than a moment the prices reach. Fired 07:04 UTC on Monday 2026-08-24 — before the US
    market opened — it produced a queue dated 2026-08-24 whose newest possible bar was Friday's.
    The gate caught it every week from 2026-08-03 on, so the weekly run had been structurally
    unable to go green; those four "failures" were the guard refusing a corrupted queue, not four
    bad weeks. `--end` still overrides, and an explicit one skips the probe entirely (no network is
    spent dating a run whose date you gave).
    """
    if args.end:
        end = date.fromisoformat(args.end)
    else:
        # The EOD source is the calendar: `grouped_daily` is empty on a non-trading day, so
        # weekends and holidays answer themselves. See `last_completed_session` for why it starts
        # at yesterday rather than today.
        end = last_completed_session(PolygonEodClient.from_config(get_config()),
                                     today=date.today())
        print(f"weekly run: dating from the data — last completed session {end}", file=sys.stderr)
    result = run_weekly(end=end, benchmark=args.benchmark, progress=stderr_reporter)
    print(f"weekly run: {result}")
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
    #
    # ARCHIVE FIRST, POINTER SECOND (2026-07-31). The order was the other way round, so the
    # "latest" pointer — the ONLY committed cluster file — was overwritten BEFORE the immutable
    # snapshot was secured. A failing archive write, or `--no-scan-history`, left the prior harvest
    # destroyed and nothing keeping it: the "must never clobber" comment described an intent the
    # sequence did not implement. Overwriting the pointer without an archive is now REFUSED.
    if not args.no_write and args.no_scan_history:
        raise SystemExit(
            "REFUSED: --no-scan-history would overwrite candidate_themes.jsonl — the only "
            "committed cluster file — with no immutable snapshot kept. Pass --no-write to print "
            "only, or allow the archive.")
    snap_path = None
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
    # POINTER LAST — only once the immutable snapshot is on disk. `record_snapshot` propagates any
    # write error loudly, so reaching here means the prior harvest is preserved.
    if not args.no_write:
        out = cfg.snapshots_dir / "candidate_themes.jsonl"  # "latest" pointer (same bytes)
        out.write_text("\n".join(json.dumps(r) for r in dumped))
        print(f"\nwrote {out} ({len(dumped)} admissible candidate themes)")
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
        control_pair_coverage,
        grade_driving_fact,
        is_real_exposure,
        provenance_tag_of,
        provenance_tags_of,
        scan_driver_exposure,
    )
    from vinci.themes.schemas import ExposureBasis

    spec = DRIVER_SPECS[args.driver]  # --driver is REQUIRED + choices-gated; fail-loud, no default
    print(f"driver={spec.key}")
    _layers = spec.provenance_tags  # theme's by-tag provenance map (chain layers here)

    def _tags(fact_text: str) -> tuple[str, ...]:
        """All applicable tags when the SPEC declares its tags non-exclusive, else the first match.

        GATED ON `spec.multi_tag` (review of #488): multi-match defeats the most-specific-first
        ordering three of the four drivers depend on — "less-than-truckload carrier" resolves to
        ('ltl', 'asset-based-tl') under truckload's directional tags, putting a headwind name in
        the tailwind bucket."""
        return (provenance_tags_of(fact_text, _layers) if spec.multi_tag
                else (provenance_tag_of(fact_text, _layers),))

    cfg = get_config()
    cfg.ensure_dirs()
    # THE ONE OPT-IN CALL SITE for the parallel band: an exposure scan reads each name's filings
    # independently, so a wider population adds names without changing the names already there.
    # Component A / stage-2 detection deliberately does NOT opt in — its factors are
    # cross-sectional, so a wider population would move every existing name's residual.
    universe, snap = det.load_detection_universe(cfg, include_theme_band=True)
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
    # SAY WHICH POPULATION WAS ACTUALLY SCANNED — computed AFTER --only-tickers/--max-names have
    # narrowed it (review 2026-08-31: printed before, the line described a scan that did not
    # happen; the theme rows sort last, so any --max-names below the primary count scanned zero
    # of them while announcing 810). The theme band's own vintage prints beside the count,
    # because the two bands are built by separate runs and a silently ageing population is the
    # stale-input class this repo keeps closing.
    n_theme = sum(1 for n in universe if n.band == "theme")
    if n_theme:
        tv = det.theme_band_as_of(cfg)
        print(f"universe: {len(universe) - n_theme} primary + {n_theme} theme-band "
              f"(as-of {tv or 'unknown'}; scannable, not tradeable)")
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
    # A zero-pair control check must never print as a clean bill (see control_pair_coverage).
    print(control_pair_coverage(results))
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
    # BY TAG, not by name: a two-sided name counts under BOTH sides, so the totals here can
    # exceed the surfaced count. That is the point — the column answers 'how much exposure
    # of each kind', not 'how many companies'.
    layers = Counter(tag for a in surfaced if (f := grade_driving_fact(a))
                     for tag in _tags(f.fact))
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
    # BY TAG, and the header says so when tags can overlap — with `multi_tag` a two-sided name
    # counts under both sides, so the column deliberately does not sum to the surfaced count.
    _basis = ("tag mentions across" if spec.multi_tag else "of the")
    print(f"\nVOLUME by chain layer — {_basis} {len(surfaced)} surfaced:")
    for layer, n in layers.most_common():
        print(f"  {layer:22} {n}")
    real = [a for a in surfaced if is_real_exposure(a)]
    committed = [a for a in surfaced if a.exposure_basis is ExposureBasis.COMMITTED_CAPACITY]
    print(f"\nREAL — binding/quantified ({len(real)}); contract-type flags are the NOISY tier "
          "(weight for review), revenue-type verified more cleanly:")
    for a in sorted(real, key=lambda x: x.exposure_basis.value):
        f = grade_driving_fact(a)
        if f:
            print(f"  {a.ticker:6} [{a.exposure_basis.value}] <{'+'.join(_tags(f.fact))}> "
                  f"{f.driver_tie.value}: {f.fact[:120]}")
            print(f"         source: {f.source_ref}")
    print(f"\nCOMMITTED-capacity — borderline, capex/MW toward the driver ({len(committed)}):")
    for a in sorted(committed, key=lambda x: x.ticker):
        f = grade_driving_fact(a)
        if f:
            print(f"  {a.ticker:6} <{'+'.join(_tags(f.fact))}> "
                  f"{f.driver_tie.value}: {f.fact[:105]}")
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


def _cmd_theme_thesis_declare(args: argparse.Namespace) -> int:
    """Declare a driver's thesis card — operator-typed JSON, validated, stamped, written.

    The card is the theme thesis gate's input (brief Item 1): mechanism (closed enum), the
    market's mistake stated as a mechanism, the null thesis, and DatedTrigger falsifiers. The
    machine stamps ``mirror_slug`` from the registry and validates shape; it drafts nothing."""
    from pydantic import ValidationError

    from vinci.themes import thesis as th

    cfg = get_config()
    raw = Path(args.file).read_text()
    try:
        card = th.ThemeThesis.model_validate_json(raw)
    except ValidationError as exc:
        print(f"REFUSED: the card does not validate —\n{exc}")
        return 1
    if card.driver_key != args.driver:
        print(f"REFUSED: the file declares driver_key {card.driver_key!r} but the command names "
              f"{args.driver!r} — declaring one driver's card under another is the mis-binding "
              f"the positional argument exists to catch. NOTHING was written.")
        return 1
    card = th.stamped(card)  # the registry's mirror_slug — machine-stamped, never operator-typed
    # WHETHER A PRIOR CARD EXISTED, read BEFORE the write — the success line below claims an
    # archive was made, and `--supersede` on a driver with no card archives NOTHING. Printing the
    # claim off the FLAG rather than the fact told the operator a previous version was recoverable
    # when none was written; the flag says what was asked for, this says what happened.
    superseded = th.thesis_path(card.driver_key, data_dir=cfg.data_dir).exists()
    try:
        path = th.write_thesis(card, data_dir=cfg.data_dir, supersede=args.supersede)
    except (FileExistsError, ValueError) as exc:
        print(f"REFUSED: {exc}")
        return 1
    print(f"OK — card written: {path}"
          f"{' (prior card archived under themes/thesis/archive/)' if superseded else ''}")
    print(f"  mechanism: {card.mechanism.value} · falsifiers: {len(card.falsifiers)} dated · "
          f"first-confirming due {card.first_confirming.deadline}")
    print("  consumers armed: theme page (after build) · monitor sweep (Item 2, pending) · "
          "panel routing (planned)")
    return 0


def _cmd_theme_economics(args: argparse.Namespace) -> int:
    """Assemble one driver's inform-only economics roll-up from committed artifacts (no
    composite — brief Item 4, ruling R5) and write ``data/themes/economics/<driver>.json``."""
    from vinci.themes import rollup as ru

    cfg = get_config()
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    r = ru.build_rollup(args.driver, data_dir=cfg.data_dir, scenarios_root=Path.cwd(),
                        dossiers_dir=cfg.data_dir / "dossiers", as_of=as_of)
    path = ru.write_rollup(r, data_dir=cfg.data_dir)
    print(f"theme economics roll-up written: {path}")
    print(f"  {r.n_members} members · {r.n_underwritten} underwritten — {r.membership_note}")
    if not r.rows:
        print("  (empty roll-up — the artifact carries the reason so the page can say it)")
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
    # THE FREEZE PATH IS A PAIR, and it is checked BEFORE the either/or so a half-specified pair
    # gets its own message. `--worksheet` alone used to satisfy the either/or below (worksheet OR
    # ledger reads as "a freeze was requested"), fall through, and die on `Path(None)` with an
    # unrelated TypeError — review P2 on #412. The ledger-only case was symmetric.
    # --ledger WITHOUT --worksheet is still meaningless (nothing to append); the reverse is not,
    # because the ledger now defaults to its committed home. Reversing this check rather than
    # deleting it: a bare --ledger used to die on `Path(None)` (review P2 on #412) and still would.
    if args.ledger and not args.worksheet:
        raise SystemExit(
            "--ledger was given without --worksheet — the ledger is where the worksheet's "
            "dispositions are appended, so there is nothing to write. To re-measure an "
            "already-frozen theme, use --from-baskets (or --from-mirror).")
    sources = [bool(args.worksheet), bool(args.from_mirror), bool(args.from_baskets)]
    if sum(sources) != 1:
        raise SystemExit(
            "give EXACTLY ONE source: --worksheet + --ledger (freeze from the analyst's "
            "dispositions), --from-baskets (re-measure from the COMMITTED frozen basket, the "
            "durable record the freeze wrote), or --from-mirror (recover a basket from the "
            "published summary — hold-none freezes only).")

    if args.from_baskets:
        # THE PREFERRED RE-MEASURE PATH now that baskets are committed. Unlike --from-mirror this
        # reads what the FREEZE wrote, so it carries the BUY leg and its per-name entry dates —
        # the thing a mirror cannot supply and the reason a reconstruction refuses one.
        baskets = fwd.load_baskets(Path(args.from_baskets))
        # THE ARTIFACT KNOWS ITS OWN DRIVER, so unlike the mirror path this is CHECKABLE rather
        # than a printed warning (review P2 on #422): passing the defense basket with
        # --driver ai-datacenter produced an AI-datacenter-labelled re-measurement of 108 defense
        # names. The mirror carries only a human label and cannot be bound; this can, so it is.
        if baskets.driver != driver:
            print(f"REFUSED: {args.from_baskets} is the {baskets.driver!r} basket, not "
                  f"{driver!r}. The re-measurement would be labelled with one driver and computed "
                  f"over another's names.")
            return 1
        watchlist = list(baskets.watchlist)
        print(f"\n=== Stage-4 forward RE-MEASURE (committed basket) · {driver} ===")
        print(f"basket {args.from_baskets} · frozen {baskets.freeze_timestamp}")
        unstated = "(unstated — written before provenance was recorded)"
        print(f"provenance: {baskets.provenance or unstated}")
        print(f"REBUILT: {len(baskets.ratified)} RATIFIED (BUY) · {len(baskets.passed)} PASSED "
              f"(AVOID) · {len(baskets.all_committed)} equal-weight naive baseline (§3b-i)")
        if not args.measure:
            print("\n(no --measure: basket loaded only)")
            return 0
        return _themes_forward_measure(args, fwd, baskets, watchlist)

    if args.from_mirror:
        # THE RE-MEASURE PATH. No worksheet, no ledger write, no re-freeze: the baskets are
        # reconstructed from the committed mirror so an accrual that has been sitting unmeasured
        # since the freeze can finally be computed. Nothing here logs a disposition.
        mirror = json.loads(Path(args.from_mirror).read_text())
        baskets = fwd.baskets_from_mirror(mirror, driver=driver)
        watchlist = list(baskets.watchlist)
        print(f"\n=== Stage-4 forward RE-MEASURE (from mirror) · {driver} ===")
        # THE BINDING IS NOW MACHINE-CHECKED, so this line reports rather than asks. The mirror
        # carries no registry key of its own (its `driver` field is a human label and its `slug` is
        # not the key either), so `DriverSpec.mirror_slug` holds the mapping and
        # `baskets_from_mirror` refuses a mismatch before anything is measured.
        print(f"mirror {args.from_mirror} · frozen {baskets.freeze_timestamp} · "
              f"slug={mirror.get('slug')!r} bound to driver {driver!r} via "
              f"DriverSpec.mirror_slug (verified)")
        print(f"REBUILT: {len(baskets.ratified)} RATIFIED (BUY) · {len(baskets.passed)} PASSED "
              f"(AVOID) · {len(baskets.all_committed)} equal-weight naive baseline (§3b-i)")
        if baskets.watchlist:
            print(f"WATCHLIST (re-underwrite cohort): {list(baskets.watchlist)}")
        if baskets.avoid_controls:
            print("AVOID-CONTROLS (near-miss control, within PASSED): "
                  f"{list(baskets.avoid_controls)}")
        if not args.measure:
            print("\n(no --measure: baskets rebuilt only)")
            return 0
        return _themes_forward_measure(args, fwd, baskets, watchlist)

    # THE LEDGER DEFAULTS TO ITS COMMITTED HOME, so a freeze cannot land the analyst's
    # dispositions somewhere that is never kept — which is how the three July 2026 ledgers were
    # lost. An explicit --ledger still wins, for ad-hoc runs.
    ws = Path(args.worksheet)
    ledger = (Path(args.ledger) if args.ledger
              else fwd.ledger_path(driver, data_dir=get_config().data_dir))
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ws) as fh:
        rows = list(csv.DictReader(fh))
    all_committed = [r["ticker"] for r in rows]
    # schema-flexible: the AI-datacenter worksheet has a 'chain_layer' column; a demand-shaped one
    # (e.g. defense) has 'category' — either populates the neutral substructure tag
    layer_of = {r["ticker"]: (r.get("chain_layer") or r.get("category", "")) for r in rows}
    ratify_date = date.fromisoformat(args.ratify_date) if args.ratify_date else date.today()
    records, pending = fwd.records_from_worksheet(ws, driver=driver, ratification_date=ratify_date)
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
    # THE DURABLE RECORD, written every freeze rather than only when someone remembers a flag.
    # `--baskets-out` predates this and stays as an extra copy for ad-hoc use; the canonical file is
    # committed, because the Stage-4 accrual is a calendar-time number whose input previously
    # existed on exactly one machine (operator decision 2026-08-12).
    baskets = baskets.model_copy(update={"provenance": (
        f"written by the freeze from {ws} on {freeze_ts[:10]} — the analyst's dispositioned "
        f"worksheet, appended to the ratification ledger at {ledger}")})
    # PREFLIGHT BEFORE ANY WRITE (review P1 on #424). The ledger append used to run FIRST, so a
    # refused re-freeze left the now-COMMITTED ledger holding dispositions for a basket that was
    # never frozen, and the retry appended the same judgment again — 1 row, then 2, then 3.
    # Everything that can fail is checked here; the ledger and the basket then land together as ONE
    # successful freeze. (`records_from_worksheet` and `freeze_baskets` above are already pure —
    # they parse and validate without writing, which is what makes this ordering possible.)
    # THE THESIS GATE (brief Item 1, rulings 2026-08-28): no Stage-4 freeze without the driver's
    # thesis card — "no verdict without saying what the edge IS", at theme level. First in the
    # preflight cluster: the cheapest check, and NOTHING is written on refusal. The three baskets
    # frozen before this gate existed stay frozen (ruling R2 — the surface stamps them
    # THESIS UNSTATED; only a NEW freeze is gated).
    from vinci.themes import thesis as _thesis
    try:
        _thesis.require_thesis_card(driver, data_dir=get_config().data_dir)
    except (FileNotFoundError, ValueError) as exc:   # absent card, or one that will not load
        print(f"REFUSED: {exc}\n  NOTHING was written — the ledger is untouched.")
        return 1
    try:
        fwd.assert_basket_writable(driver, data_dir=get_config().data_dir,
                                   supersede=args.supersede_basket)
    except FileExistsError as exc:
        print(f"REFUSED: {exc}\n  Re-run with --supersede-basket to archive the existing basket "
              f"under data/themes/baskets/archive/ and freeze again. NOTHING was written — the "
              f"ledger is untouched.")
        return 1
    for rec in records:  # append-only: log each dispositioned row (a correction is a new row)
        fwd.append_record(ledger, rec)
    canonical = fwd.write_baskets(baskets, data_dir=get_config().data_dir,
                                  supersede=args.supersede_basket)
    print(f"frozen basket written: {canonical}")
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
    return _themes_forward_measure(args, fwd, baskets, watchlist)


def _themes_forward_measure(
    args: argparse.Namespace, fwd: Any, baskets: Any, watchlist: list[str],
) -> int:
    """The forward measurement, shared by the FREEZE path and the RE-MEASURE path.

    Extracted rather than copied: two printers of one measurement is how a re-measure comes to
    disagree with the freeze it is supposed to continue, and this report is the fund's only forward
    read on a theme.
    """
    from datetime import date

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
    # the comparator choices come from the MODEL, never a copy of them here: a second list would
    # accept a comparator the validator refuses, and the user would meet the refusal after typing
    # the whole criterion rather than in the usage line.
    from vinci.scenarios import COMPARATORS

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
    p_refresh.add_argument("--aggs", action="store_true",
                           help="per-symbol aggregates (ONE call/name) — backfill a NEW name's "
                                "history; default grouped-daily is the whole-universe refresh")
    p_refresh.set_defaults(func=_cmd_refresh)

    p_eod = sub.add_parser("eod", help="show computed Screen-2 price features for a ticker")
    p_eod.add_argument("ticker", help="ticker (e.g. AAPL)")
    p_eod.add_argument("--ref", help="reference date YYYY-MM-DD (default: today)")
    p_eod.set_defaults(func=_cmd_eod)

    p_univ = sub.add_parser("build-universe", help="build the cap-band universe")
    p_univ.add_argument("--ref", help="as-of date YYYY-MM-DD (default: today)")
    p_univ.add_argument("--band", choices=sorted(UNIVERSE_BANDS), default="primary",
                        help="which population to build: primary (the forward-validation band, "
                             "default) or theme (the parallel larger band read only by theme "
                             "scans)")
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
        "--md-top", type=int, default=QUEUE_MD_TOP, dest="md_top",
        help="rows in the committed ranked_queue.md table (default: 50)",
    )
    p_rank.add_argument(
        "--deep-work-adv-floor", type=float, default=QUEUE_ADV_FLOOR,
        dest="deep_work_adv_floor",
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
                           help="a mid-cycle scenario "
                           "'name:rev=<$M>,margin=<frac>,multiple=<x>,dna=<$M>' (bear/base/bull; "
                           "multiple is an EV/EBITDA turn so dna= is required; omit margin → "
                           "anchor default). Repeatable.")
    for _sc in ("bear", "base", "bull"):
        p_dossier.add_argument(f"--reason-{_sc}", dest=f"reason_{_sc}",
                               help=f"why the {_sc} scenario deviates from the anchor "
                               "(REQUIRED for a deviated margin; refused otherwise)")
    p_dossier.set_defaults(func=_cmd_dossier)

    p_anchor = sub.add_parser(
        "anchor-backfill",
        help="backfill the committed R1 anchor block into dossiers (anchor-only writer — no "
        "re-assembly, no LLM, EDGAR-only; every other field stays byte-identical)")
    p_anchor.add_argument("--tickers", required=True,
                          help="comma-separated tickers, e.g. AORT,BRBR,CNXC")
    p_anchor.add_argument("--dry-run", action="store_true", dest="dry_run",
                          help="DIAGNOSTIC: recompute and report old-vs-new without writing "
                               "anything (the re-validation pass)")
    p_anchor.set_defaults(func=_cmd_anchor_backfill)

    p_fin = sub.add_parser(
        "financials-backfill",
        help="re-extract financial_summary from the on-disk CIQ export into committed dossiers "
        "(financials-only writer — no re-assembly, no LLM; every other field byte-identical)")
    p_fin.add_argument("--tickers", required=True,
                       help="comma-separated tickers, e.g. AORT,BRBR,CNXC")
    p_fin.add_argument("--dry-run", action="store_true", dest="dry_run",
                       help="DIAGNOSTIC: report old-vs-new column counts without writing")
    p_fin.set_defaults(func=_cmd_financials_backfill)

    p_peer = sub.add_parser(
        "peerset-backfill",
        help="re-extract the peer_set roster line from the on-disk CIQ export into committed "
        "dossiers (peer_set-only writer — no re-assembly, no LLM; every other field "
        "byte-identical; refuses on a newer-vintage workbook)")
    p_peer.add_argument("--tickers", required=True,
                        help="comma-separated tickers, e.g. AORT,BRBR,IT")
    p_peer.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="DIAGNOSTIC: report old-vs-new without writing")
    p_peer.set_defaults(func=_cmd_peerset_backfill)

    p_ohr = sub.add_parser(
        "own-history-refresh",
        help="recompute committed valuation.own_history from the CURRENT on-disk CIQ export, stamp "
        "periodicity/span metadata (byte-preserving; own_history value only). Then anchor-backfill "
        "after to re-derive the multiple leg.")
    p_ohr.add_argument("--tickers", required=True, help="comma-separated tickers")
    p_ohr.add_argument("--dry-run", action="store_true", dest="dry_run",
                       help="DIAGNOSTIC: report old-vs-new bands without writing")
    p_ohr.add_argument("--canonical-ciq", dest="canonical_ciq",
                       help="sync each ticker's CIQ folder FROM this canonical root before reading "
                            "(ALWAYS overwrites — no skip-if-present; missing canonical is fatal). "
                            "Use when running outside the primary worktree.")
    p_ohr.set_defaults(func=_cmd_own_history_refresh)

    p_close = sub.add_parser(
        "close-position",
        help="append the CLOSE row for a logged decision (the realized-P&L half)")
    p_close.add_argument("candidate_id", help="candidate id of the decision being closed")
    p_close.add_argument("--exit-price", dest="exit_price", type=float, required=True,
                         help="the price the position actually exited at")
    p_close.add_argument("--as-of", dest="as_of",
                         help="exit date YYYY-MM-DD (default: today). Must not precede the "
                              "frozen entry date.")
    p_close.add_argument("--reason", required=True,
                         help="why the position was closed — the schema refuses a close without "
                              "one, because an unexplained exit cannot be reviewed later")
    p_close.set_defaults(func=_cmd_close_position)

    p_log = sub.add_parser("log-verdict", help="record a manual BUY/AVOID verdict for a candidate")
    p_log.add_argument("candidate_id", help="candidate id from `vinci screen`")
    p_log.add_argument("--verdict", required=True, choices=[v.value for v in Verdict])
    # BOOK-NEUTRAL ON PURPOSE. Each sleeve names its OWN twin (overshoot's is terminal decline,
    # quality's is fully-priced), but argparse builds this help before any ticker — and therefore
    # any sleeve — is known, so it cannot be per-book. Naming one book's twin here asked a quality
    # verdict to rule out terminal decline, the exact false framing the registry exists to remove.
    # The per-book wording lives in `Sleeve.twin_help` and reaches the analyst where the book IS
    # known: the dossier page prints this name's own log-verdict command.
    p_log.add_argument("--twin", required=True,
                       help="how this book's twin case was ruled out (the dossier page prints the "
                            "wording for this name's book)")
    p_log.add_argument("--thesis", required=True, help="short thesis / rationale")
    p_log.add_argument("--kill", required=True, help="kill-criteria that would falsify the thesis")
    p_log.add_argument("--horizon-days", type=int, required=True, dest="horizon_days")
    p_log.add_argument("--confidence", required=True, choices=[c.value for c in Confidence])
    p_log.add_argument("--benchmark", default="IWM", help="scoring benchmark (default: IWM)")
    p_log.add_argument("--ref", help="decision/entry-price date YYYY-MM-DD (default: today)")
    p_log.add_argument(
        "--edge-basis", dest="edge_basis", choices=[b.key for b in EDGE_BASES],
        help="(A4, REQUIRED) what the edge IS. Silence is refused; AGREEMENT IS ALLOWED — five of "
             "the six say 'no variant' out loud and are fully valid verdicts. Not `required=True` "
             "so the refusal can EXPLAIN itself: argparse would print a bare usage line, and the "
             "whole point is that the human sees the five honest alternatives.",
    )
    p_log.add_argument(
        "--edge-note", dest="edge_note",
        help="what the chosen basis requires (the tail, the trigger and its date, the observation "
             "being waited for, the cross-sectional claim). Sealed beside the basis.",
    )
    p_log.add_argument(
        "--saw-proposal", action="store_true", dest="saw_proposal",
        help="self-report: you peeked at the machine proposal (dossier --show-proposal) BEFORE "
        "deciding. Stamps revealed_pre_verdict=True so the anchored disposition is down-weighted.",
    )
    p_log.set_defaults(func=_cmd_log_verdict)

    p_mon = sub.add_parser("monitor", help="mark the book to market vs benchmarks (manual)")
    p_mon.add_argument("--ref", help="as-of date YYYY-MM-DD (default: today)")
    p_mon.set_defaults(func=_cmd_monitor)

    p_sr = sub.add_parser(
        "scenario-refresh",
        help="refresh a record's MACHINE inputs (spot / facts) — never its legs, verdict or "
             "rationale; every change lands in the record's refresh_log")
    p_sr.add_argument("ticker")
    p_sr.add_argument("--spot", type=float, help="new spot; omit to leave unchanged")
    p_sr.add_argument("--fact", action="append", default=[], metavar="KEY=VALUE",
                      help="refresh one machine fact (repeatable); see the refreshable set")
    p_sr.add_argument("--fact-kind", action="append", metavar="KEY=KIND",
                      help="declare WHICH QUANTITY a --fact supplies (e.g. "
                           "diluted_shares=outstanding). Required where two quantities share a "
                           "unit — the engine refuses an undeclared refresh of those")
    p_sr.add_argument("--source", required=True,
                      help="WHERE the new values came from — required; an unattributable refresh "
                           "is an untraceable edit")
    p_sr.add_argument("--as-of", dest="as_of", help="date stamp (default: today)")
    p_sr.add_argument("--dry-run", action="store_true", dest="dry_run",
                      help="print what would change and write nothing")
    p_sr.set_defaults(func=_cmd_scenario_refresh)

    p_sp = sub.add_parser(
        "scenario-propose",
        help="emit an underwrite template: 3 anchors pre-filled, 6 refused with their evidence")
    p_sp.add_argument("ticker")
    p_sp.add_argument("--out", help="output path (default <TICKER>-underwrite.json)")
    p_sp.set_defaults(func=_cmd_scenario_propose)

    p_sc = sub.add_parser(
        "scenario-create",
        help="validate a filled template and write the record (validate -> run_recipe -> write)")
    p_sc.add_argument("ticker")
    p_sc.add_argument("--from", dest="from_file", required=True, help="the filled template")
    p_sc.set_defaults(func=_cmd_scenario_create)


    p_ss = sub.add_parser(
        "scenario-supersede",
        help="archive the live record and reissue a new one — the ONLY supersession path; a LIVE "
             "position is refused (it is amended, never superseded)")
    p_ss.add_argument("ticker")
    p_ss.add_argument("--payload", required=True, type=Path,
                      help="path to the NEW record as JSON (validated against the schema)")
    p_ss.add_argument("--dry-run", action="store_true", dest="dry_run",
                      help="print the pair and write nothing")
    p_ss.set_defaults(func=_cmd_scenario_supersede)

    p_crit = sub.add_parser(
        "scenario-criterion",
        help="attach a STRUCTURED re-underwrite criterion beside the prose — refuses a metric the "
             "name's dossier cannot resolve")
    p_crit.add_argument("ticker")
    p_crit.add_argument("--trigger", required=True,
                        help="the falsifier in YOUR words — kept verbatim, never superseded")
    p_crit.add_argument("--metric", required=True,
                        help="dotted path into the dossier's mechanical layer "
                             "(e.g. quality.net_debt_to_ebitda)")
    p_crit.add_argument("--comparator", required=True,
                        choices=list(COMPARATORS))
    p_crit.add_argument("--threshold", required=True, type=float)
    p_crit.add_argument("--unit", required=True,
                        help="the THRESHOLD's unit — checked against the value's own at evaluation")
    p_crit.add_argument("--sustain", type=int, default=1,
                        help="consecutive readings required (default 1)")
    p_crit.add_argument("--basis", default="",
                        help="where the metric is read and why that series "
                             "(default: its source_ref)")
    p_crit.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="resolve, evaluate and print — write nothing")
    p_crit.set_defaults(func=_cmd_scenario_criterion)

    p_audit = sub.add_parser("audit", help="standing read-only audits over committed artifacts")
    audit_sub = p_audit.add_subparsers(dest="audit_what", required=True)
    p_r1 = audit_sub.add_parser(
        "r1", help="R1 applicability — the seven checks (read-only; flags print, never block)")
    p_r1.add_argument("--as-of", dest="as_of", help="date stamp for the report (default: today)")
    p_r1.add_argument("--out", type=Path, help="write the report here as well as printing it")
    p_r1.set_defaults(func=_cmd_audit_r1)
    p_spot = audit_sub.add_parser(
        "spot", help="every record's spot against the bar it claims to be (read-only; notes print)")
    p_spot.set_defaults(func=_cmd_audit_spot)

    p_calls = sub.add_parser("calls", help="the calls tape — score a public account's stated calls")
    calls_sub = p_calls.add_subparsers(dest="calls_what", required=True)
    p_ca = calls_sub.add_parser("accounts", help="rebuild the account index from each meta.json")
    p_ca.add_argument("--default", help="handle that opens by default")
    p_ca.set_defaults(func=_cmd_calls_accounts)
    p_cb = calls_sub.add_parser("fetch-bars", help="fetch Polygon daily bars for tracked tickers")
    p_cb.add_argument("--account", help="handle (default: the index's default)")
    p_cb.add_argument("--only", help="comma-separated tickers, instead of all tracked")
    p_cb.set_defaults(func=_cmd_calls_bars)
    p_cs = calls_sub.add_parser("score", help="score labelled calls against the committed bars")
    p_cs.add_argument("--account", help="handle (default: the index's default)")
    p_cs.add_argument("--hand-only", action="store_true", dest="hand_only",
                      help="score only human-labelled rows")
    p_cs.set_defaults(func=_cmd_calls_score)
    p_ci = calls_sub.add_parser("import-labels",
                                help="merge an exported labelling session back into the corpus")
    p_ci.add_argument("path", help="the JSONL exported from the tape")
    p_ci.add_argument("--account", help="handle (default: the index's default)")
    p_ci.add_argument("--dry-run", action="store_true", dest="dry_run",
                      help="report what would change and write nothing")
    p_ci.set_defaults(func=_cmd_calls_import)

    p_ledger = sub.add_parser("ledger", help="list recorded paper verdicts")
    p_ledger.set_defaults(func=_cmd_ledger)

    p_score = sub.add_parser("score", help="score the ledger (BUY−AVOID spread + metrics)")
    p_score.add_argument("--benchmark", default="IWM", help="benchmark ETF (default: IWM)")
    p_score.add_argument("--cost-bps", type=float, default=25.0, dest="cost_bps")
    p_score.add_argument("--ref", help="as-of date YYYY-MM-DD (default: today)")
    p_score.add_argument("--json", action="store_true", help="also write the report JSON")
    p_score.set_defaults(func=_cmd_score)

    p_weekly = sub.add_parser("run-weekly", help="scheduled: refresh + screen + export snapshots")
    p_weekly.add_argument("--end", help="end date YYYY-MM-DD "
                          "(default: the last completed session, asked of the EOD source)")
    p_weekly.add_argument("--benchmark", default="IWM")
    p_weekly.set_defaults(func=_cmd_run_weekly)

    p_monthly = sub.add_parser("run-monthly", help="scheduled: score the ledger + export report")
    p_monthly.add_argument("--as-of", dest="as_of", help="as-of date YYYY-MM-DD (default: today)")
    p_monthly.add_argument("--benchmark", default="IWM")
    p_monthly.add_argument("--cost-bps", type=float, default=25.0, dest="cost_bps")
    p_monthly.set_defaults(func=_cmd_run_monthly)

    p_t0 = sub.add_parser("graph-test0", help="score the EDGAR graph vs CIQ ground truth (Test 0)")
    p_t0.add_argument("--model", help="LLM model id (default: config, claude-opus-5; pass "
                                      "claude-opus-4-8 to compare vs the benchmarked baseline)")
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
    # --worksheet/--ledger are the FREEZE path. --from-mirror is the RE-MEASURE path: the ledger and
    # baskets are git-ignored local-only artifacts, so on any machine that did not run the freeze
    # the accrual has no input — and the accrual is the whole point of Stage 4. Exactly one of the
    # two must be given; the parser enforces it rather than discovering it mid-run.
    p_fwd.add_argument("--worksheet",
                       help="committed_review_worksheet.csv (with the analyst's dispositions)")
    p_fwd.add_argument("--ledger",
                       help="append-only ratification ledger JSONL path. Defaults to the COMMITTED "
                            "home, data/themes/ledgers/<driver>.jsonl — the record the basket is "
                            "derived from, kept because the basket says which names are in which "
                            "cohort while the ledger says why, in the analyst's own words.")
    p_fwd.add_argument("--supersede-basket", dest="supersede_basket", action="store_true",
                       help="deliberately re-freeze a driver that already has a committed basket: "
                            "archives the existing one under baskets/archive/ first. Without this "
                            "a second freeze REFUSES rather than silently moving the entry dates "
                            "the forward accrual is measured from.")
    p_fwd.add_argument("--from-baskets", dest="from_baskets",
                       help="re-measure from a COMMITTED frozen basket "
                            "(data/themes/baskets/<driver>.json) — the durable input written by "
                            "the freeze. Preferred over --from-mirror, which recovers a basket "
                            "from a published summary and only works for hold-none freezes.")
    p_fwd.add_argument("--from-mirror", dest="from_mirror",
                       help="re-measure an ALREADY-FROZEN theme from its committed "
                            "frontend/themes/<slug>.json instead of re-freezing. Hold-none "
                            "(zero-RATIFIED) freezes only — the mirror carries no per-name "
                            "ratification date, so a BUY leg cannot be re-dated from it.")
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

    p_tt = sub.add_parser(
        "theme-thesis",
        help="the driver's thesis card — the theme thesis gate's input (operator-typed only)")
    tt_sub = p_tt.add_subparsers(dest="tt_cmd", required=True)
    p_ttd = tt_sub.add_parser(
        "declare", help="validate + stamp + write data/themes/thesis/<driver>.json")
    p_ttd.add_argument("driver", choices=sorted(DRIVER_SPECS),
                       help="driver key (registry-gated, like themes-forward)")
    p_ttd.add_argument("--file", required=True,
                       help="the operator-typed card JSON (ThemeThesis shape; mirror_slug is "
                            "machine-stamped — do not type it)")
    p_ttd.add_argument("--supersede", action="store_true",
                       help="archive the existing card under themes/thesis/archive/ and "
                            "re-declare (never an in-place edit)")
    p_ttd.set_defaults(func=_cmd_theme_thesis_declare)

    p_te = sub.add_parser(
        "theme-economics",
        help="inform-only per-member economics roll-up for one driver (assembles committed "
             "records; NO composite)")
    p_te.add_argument("--driver", required=True, choices=sorted(DRIVER_SPECS))
    p_te.add_argument("--as-of", dest="as_of",
                      help="assembly date YYYY-MM-DD (default: today)")
    p_te.set_defaults(func=_cmd_theme_economics)

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
