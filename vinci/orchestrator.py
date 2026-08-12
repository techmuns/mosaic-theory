"""Configure-once orchestration for the scheduled jobs (GitHub Actions cron).

Each run is self-contained and idempotent: **rebuild** the working DB from the committed JSONL
snapshots, **refresh** EOD prices for the stored universe (the immutable per-day grouped-daily
responses are cached, so only new days hit the network), run the **screen** (weekly) or the
**scoring** (monthly), then **export** the snapshots back for the workflow to commit. Bulk prices
are not snapshotted (re-pullable + cached); the durable state is the entity master, universe,
candidates, ledger, and as-reported fundamentals.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from vinci.config import Config, get_config
from vinci.edgar import EdgarClient
from vinci.eod import PolygonEodClient, ingest_prices
from vinci.labels import resolve_label
from vinci.progress import ProgressFn
from vinci.rank import (
    CauseClass,
    RankedCandidate,
    RankWeights,
    StructuralDisqualifier,
    load_candidates_from_snapshot,
    load_market_caps_from_snapshot,
    rank_candidates,
    render_queue_markdown,
    scan_structural,
)
from vinci.scoring import score_ledger
from vinci.scoring.baseline import resolve_baskets
from vinci.screens import screen_universe
from vinci.sec import build_sec_http
from vinci.store import Store
from vinci.universe import benchmark_identity

# ~5y: enough history for the 52w drawdown AND the G3 multiple-at-floor range (Polygon Starter).
_SCREEN_LOOKBACK_DAYS = 1825
# Monthly scoring refreshes ~2y so verdicts in that window have forward prices to score against.
_SCORE_LOOKBACK_DAYS = 730
# Queue-writing defaults, shared by the weekly job and the `vinci rank` CLI so the two cannot drift.
QUEUE_MD_TOP = 50
QUEUE_ADV_FLOOR = 3_000_000.0  # = the universe ADV floor; mirrors vinci.rank's own default


def rank_from_snapshots(
    cfg: Config,
    *,
    annotations: dict[str, CauseClass] | None = None,
    structural_flags: dict[str, StructuralDisqualifier] | None = None,
    deep_work_adv_floor: float = QUEUE_ADV_FLOOR,
) -> list[RankedCandidate]:
    """Rank the committed screen output, with the resolved sector/industry labels attached.

    THE ONE RANKING PATH — `vinci rank` and the weekly job both come through here, so a queue built
    by CI is the same object as one built by hand. Reads the committed snapshots only (no DB, no
    network): ``candidate_records.jsonl`` for the screen output, ``universe_snapshot.jsonl`` for
    size. Returns [] when the screen produced nothing, so a caller can skip the write.
    """
    snaps = cfg.snapshots_dir
    records = snaps / "candidate_records.jsonl"
    # ABSENT is a legitimate state (a fresh checkout, or the very first run) and means "nothing has
    # been screened", not "invent something" — so it returns empty and the caller skips the write,
    # leaving any existing queue untouched. Only the missing FILE is tolerated; a malformed one
    # still raises. run_weekly reports `ranked` in its result dict, so a screen that found
    # candidates while the rank found none is visible in the job output rather than silent.
    if not records.exists():
        return []
    cands = load_candidates_from_snapshot(records)
    if not cands:
        return []
    ranked = rank_candidates(
        cands,
        weights=RankWeights(),
        annotations=annotations,
        market_caps=load_market_caps_from_snapshot(snaps / "universe_snapshot.jsonl"),
        structural_flags=structural_flags or None,
        deep_work_adv_floor=deep_work_adv_floor,
    )
    # The RESOLVED labels are attached HERE, in the writer, never in the scorer — vinci.rank and
    # vinci.screens stay label-free and an AST fence test asserts it. Assemble/inform ONLY: they
    # feed the human cluster roll-up, never a gate/weight/sort. gics=None at universe scale: the
    # CIQ-GICS overlay joins at the frontend build from the committed dossier index, so a dossier
    # landing between rank runs upgrades its name without a re-rank.
    sic_by_id = {c.candidate_id: c.data_record.identity.sic for c in cands}
    return [
        r.model_copy(update={
            "sector": (lbl := resolve_label(sic_by_id.get(r.candidate_id))).sector,
            "industry": lbl.industry,
        })
        for r in ranked
    ]


def carry_forward_assessment(
    cfg: Config,
) -> tuple[dict[str, StructuralDisqualifier], dict[str, CauseClass]]:
    """The last EXPLICIT operator assessment, recovered from the queue about to be replaced.

    `vinci rank --structural` / `--cause-file` write `structural_flag` and `cause_class` into
    `ranked_queue.jsonl` ONLY — nothing durable upstream holds them. A scheduled refresh that
    supplied neither would therefore wipe them, and **a name capped at 0.05 by an 8-K disqualifier
    would climb back to the top of the queue on Monday with no operator action** (review, #420).

    Carrying them is safe in the one direction that matters: the structural channel is DEMOTE-ONLY,
    so a stale flag can only keep a name down, never lift one. An 8-K does not un-happen, so the
    flag stays factually true; it is `source_ref`-bound to its accession either way. What this does
    NOT do is DISCOVER new signals — that still needs an explicit `--structural` run. And it
    self-clears: if an operator re-scans and the signal no longer fires, the queue they write has no
    flag, and the next carry-forward reads that absence.

    Keyed by ticker, which is what `rank_candidates` falls back to and what survives a re-screen.
    """
    prior = cfg.snapshots_dir / "ranked_queue.jsonl"
    flags: dict[str, StructuralDisqualifier] = {}
    causes: dict[str, CauseClass] = {}
    if not prior.exists():
        return flags, causes
    for line in prior.read_text().splitlines():
        if not line.strip():
            continue
        r = RankedCandidate.model_validate_json(line)
        if r.structural_flag is not None:
            flags[r.ticker] = r.structural_flag
        if r.cause_class != CauseClass.UNCLASSIFIED:
            causes[r.ticker] = r.cause_class
    return flags, causes


def write_queue_snapshots(
    cfg: Config, ranked: list[RankedCandidate], *, md_top: int = QUEUE_MD_TOP
) -> tuple[Path, Path]:
    """Write ranked_queue.jsonl + .md. Returns both paths so a caller can report what it wrote."""
    cfg.ensure_dirs()
    snaps = cfg.snapshots_dir
    jsonl = snaps / "ranked_queue.jsonl"
    with jsonl.open("w") as f:
        for r in ranked:
            f.write(r.model_dump_json() + "\n")
    md = snaps / "ranked_queue.md"
    md.write_text(render_queue_markdown(ranked, top=md_top))
    return jsonl, md


def refresh_queue(cfg: Config, *, structural: bool = False) -> dict[str, int]:
    """Rank the screen's committed output and REPLACE the queue. The weekly job's tail.

    Extracted from :func:`run_weekly` so its dangerous cases are testable without the network —
    they were review findings on #420, and none is reachable through a function that builds
    Polygon and EDGAR clients from config.

    ``structural=True`` runs the deterministic 8-K disqualifier scan (network). A LIVE SCAN IS
    AUTHORITATIVE AND REPLACES THE CARRY-FORWARD outright — it re-checks all five signals against
    current filings, so a name that no longer fires must come back clean rather than have a stale
    flag resurrected underneath it. The carry-forward exists for the runs that DON'T scan.
    """
    flags, causes = carry_forward_assessment(cfg)
    if structural:
        records = cfg.snapshots_dir / "candidate_records.jsonl"
        cands = load_candidates_from_snapshot(records) if records.exists() else []
        if cands:
            flags = scan_structural(
                cands, edgar=EdgarClient.from_config(cfg), http=build_sec_http(cfg)
            )
    ranked = rank_from_snapshots(cfg, annotations=causes or None, structural_flags=flags or None)
    # WRITE EVEN WHEN EMPTY. The screen has completed by this point, so no candidates is an ANSWER —
    # the latest screen rejected everything — not a failure to produce one. Skipping the write left
    # the previous week's names served as current, and the staleness banner could not catch it
    # either: the retained queue is only seven days old, so it reads as fresh (review, #420).
    #
    # The two cases are told apart on the INPUT, never on the output being empty: a MISSING
    # candidate_records.jsonl means nothing has been screened (fresh checkout) and must not clobber
    # an existing queue; a PRESENT-but-empty one is a real screen result and must replace it.
    if (cfg.snapshots_dir / "candidate_records.jsonl").exists():
        write_queue_snapshots(cfg, ranked)
    return {"ranked": len(ranked),
            "carried_structural": len(flags), "carried_cause": len(causes)}


def run_weekly(
    config: Config | None = None,
    *,
    end: date,
    benchmark: str = "IWM",
    lookback_days: int = _SCREEN_LOOKBACK_DAYS,
    structural: bool = False,
    progress: ProgressFn | None = None,
) -> dict[str, object]:
    """Weekly: refresh the universe's prices and lazily run Screen 2; persist candidates."""
    cfg = config or get_config()
    cfg.ensure_dirs()
    eod = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
        if not any(not s.internal_id.startswith("IDX-") for s in store.iter_securities()):
            return {"status": "no universe in snapshots — run build-universe first"}
        _cands, stats = screen_universe(
            store, eod, edgar, reference_date=end, lookback_days=lookback_days,
            staleness_days=cfg.price_staleness_days, benchmark=benchmark, progress=progress,
        )
        store.export_snapshots(cfg.snapshots_dir)
    # ...then RANK, from the snapshot the screen just exported, through the same path `vinci rank`
    # uses. Until 2026-08-12 this job stopped at the screen: candidate_records advanced every week
    # while ranked_queue.jsonl only moved when a human remembered to run the ranker, and the served
    # queue had drifted 12 days and 95 names behind the screen that fed it (STATE.md §5).
    #
    # NO --structural here: it is a network 8-K scan, off by default in the CLI too, and it SINKS
    # names — putting a demote channel on a cron is a decision-path change and stays a human act.
    # But the last explicit assessment IS carried forward, because the flags live nowhere but the
    # artifact this is about to overwrite (see carry_forward_assessment).
    return {**stats, "ref": end.isoformat(), **refresh_queue(cfg, structural=structural)}


def run_monthly(
    config: Config | None = None,
    *,
    as_of: date,
    benchmark: str = "IWM",
    cost_bps: float = 25.0,
    lookback_days: int = _SCORE_LOOKBACK_DAYS,
    progress: ProgressFn | None = None,
) -> dict[str, object]:
    """Monthly: refresh prices, score the decision ledger, and write the report to snapshots.

    Prices are not snapshotted (re-pullable), so we refresh them before scoring — else a fresh CI
    checkout would have no forward prices to score against. The grouped-daily cache keeps this fast.
    """
    cfg = config or get_config()
    cfg.ensure_dirs()
    client = PolygonEodClient.from_config(cfg)
    bench = benchmark_identity(benchmark)
    start = as_of - timedelta(days=lookback_days)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
        universe = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
        if universe:
            ingest_prices(client, store, universe, start=start, end=as_of, progress=progress)
            store.upsert_security(bench)
            ingest_prices(client, store, [bench], start=start, end=as_of)
        _scores, report = score_ledger(
            store, as_of=as_of, cost_bps=cost_bps, benchmark_internal_id=f"IDX-{benchmark}",
            # Wired here as well as in `vinci score` — see that call site's note.
            # `scoring_report.md` is the artifact most readers open, so a kill test missing
            # from it is missing.
            baskets=resolve_baskets(cfg.data_dir / "followed.json", store.iter_securities()),
        )
        store.export_snapshots(cfg.snapshots_dir)
    (cfg.snapshots_dir / "scoring_report.md").write_text(report.to_markdown())
    return report.to_dict()
